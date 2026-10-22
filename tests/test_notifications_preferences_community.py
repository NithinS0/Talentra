"""Automated Functional, Security & Resilience Tests for Talentra Stage 12: Notifications, Preferences & Community.

Maps strictly to approved test cases in Talentra_Final_Test_Cases_All_Modules.xlsx (Sheet: Notifications Preferences & Com):
- FR-0139: Notification preference persistence (channel/category explicit values; disabled channel suppression)
- FR-0140: Job alert filters (criteria reference valid skills/location and alert preferences)
- FR-0141: Notification delivery idempotency (repeated callbacks yield one logical delivery state without duplicates)
- FR-0142: Message retention (expired body purged/redacted while delivery metadata remains)
- FR-0143: Language preference fallback (unsupported preference resolves to configured fallback)
- FR-0144: Community post length (within-limit free text saves; oversized rejected, UTF-8 supported)
- FR-0145: Reaction uniqueness (one reaction per user/post/type toggled idempotently)
- FR-0146: Support ticket ownership (ticket access limited to requester and authorized support staff)
- FR-0147: FAQ publication state (only active/published FAQ entries appear in public queries)
- FR-0148: Referral event attribution (valid referral recorded once without duplicate credit)
- FR-0149: Notification provider outage (failure recorded, retry strategy does not lose or duplicate deliveries)
- FR-0150: Preference change audit (auditable history recording actor, timestamp, before/after values)
- FR-0207: Notification body retention expiry (expired message bodies purged/redacted)
"""

import sys
import os
import uuid
from typing import Tuple, List, Optional, Dict
from datetime import datetime, timedelta, timezone
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_test_supabase_token
from app.models.country import Country
from app.models.user import User, Role, UserRoleAssignment
from app.models.notification import (
    Language,
    NotificationPreference,
    JobAlertPreference,
    PrivacyPreference,
    Notification,
    NotificationDelivery,
    CommunityPost,
    CommunityReaction,
    SupportTicket,
    Faq,
    ReferralEvent,
    NotificationDeliveryAttempt,
    NotificationPreferenceHistory,
)
from app.services.notification_service import (
    NotificationService,
    NOTIFICATION_STATUS,
    DELIVERY_STATUS,
    NOTIFICATION_TYPE,
    CHANNEL,
    TICKET_STATUS,
    FAQ_STATUS,
    DEFAULT_FALLBACK_LANGUAGE,
    MAX_COMMUNITY_POST_LENGTH,
)


@pytest.fixture(scope="session")
def test_engine():
    """Create test SQLite engine with static pool."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def do_connect(dbapi_connection, connection_record):
        dbapi_connection.isolation_level = None

    with engine.begin() as conn:
        Base.metadata.create_all(bind=conn)

    return engine


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Provide transactional database session for tests."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Provide FastAPI test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_roles(db_session):
    """Seed system roles."""
    roles = [
        Role(role_code="SUPER_ADMIN", display_name="Super Administrator", description="Platform Admin", is_system_role=True),
        Role(role_code="ADMIN", display_name="Platform Administrator", description="Admin", is_system_role=True),
        Role(role_code="CANDIDATE", display_name="Candidate", description="Job seeker", is_system_role=False),
        Role(role_code="EMPLOYER", display_name="Employer", description="Hiring org", is_system_role=False),
    ]
    roles_dict = {}
    for r in roles:
        existing = db_session.query(Role).filter(Role.role_code == r.role_code).first()
        if not existing:
            db_session.add(r)
            db_session.flush()
            roles_dict[r.role_code] = r
        else:
            roles_dict[r.role_code] = existing
    db_session.commit()
    return roles_dict


def _create_user(db_session, role_code: str = "CANDIDATE") -> User:
    """Helper to create a test user with assigned role."""
    uid = uuid.uuid4().hex[:8]
    sub = f"auth0|usr_{uid}"
    email = f"user_{uid}@talentra.test"
    now = datetime.now(timezone.utc)

    user = User(
        email_address=email,
        display_name=f"User {uid}",
        provider_subject=sub,
        account_status_code_id=1,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    db_session.flush()

    role = db_session.query(Role).filter(Role.role_code == role_code).first()
    if role:
        db_session.add(UserRoleAssignment(
            user_id=user.id,
            role_id=role.id,
            assigned_by_user_id=user.id,
            valid_from=now,
            created_at=now,
        ))
        db_session.flush()
    db_session.commit()
    return user


def _auth_headers(user: User) -> dict:
    """Helper to generate bearer token headers matching Supabase Auth."""
    token = create_test_supabase_token(sub=user.provider_subject, email=user.email_address)
    return {"Authorization": f"Bearer {token}"}


# =========================================================================
# TEST CASES: FR-0139 through FR-0150, FR-0207
# =========================================================================

def test_fr0139_notification_preference_persistence(db_session, seed_roles):
    """FR-0139: Notification preference persistence - disabled channel receives no non-essential notification."""
    user = _create_user(db_session, "CANDIDATE")

    # 1. User explicitly disables EMAIL for MARKETING
    pref = NotificationService.set_notification_preference(
        db=db_session,
        user_id=user.id,
        notification_type_code_id=NOTIFICATION_TYPE["MARKETING"],
        channel_code_id=CHANNEL["EMAIL"],
        enabled=False,
    )
    assert pref.enabled is False

    # 2. Verify check method confirms channel is disabled
    assert NotificationService.is_channel_enabled(
        db=db_session,
        user_id=user.id,
        notification_type_code_id=NOTIFICATION_TYPE["MARKETING"],
        channel_code_id=CHANNEL["EMAIL"],
    ) is False

    # 3. Create marketing notification with EMAIL channel - delivery is suppressed
    notif, delivery = NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        title="Exclusive Discount",
        body="Get 50% off premium subscription",
        category_id=NOTIFICATION_TYPE["MARKETING"],
        channel_id=CHANNEL["EMAIL"],
    )
    assert notif.id is not None
    # External delivery suppressed because user disabled EMAIL for marketing
    assert delivery is None

    # 4. User enables EMAIL for JOB_ALERT
    NotificationService.set_notification_preference(
        db=db_session,
        user_id=user.id,
        notification_type_code_id=NOTIFICATION_TYPE["JOB_ALERT"],
        channel_code_id=CHANNEL["EMAIL"],
        enabled=True,
    )
    # Create job alert with EMAIL channel - delivery record IS created
    notif2, delivery2 = NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        title="New Python Jobs",
        body="3 matching jobs found",
        category_id=NOTIFICATION_TYPE["JOB_ALERT"],
        channel_id=CHANNEL["EMAIL"],
    )
    assert delivery2 is not None
    assert delivery2.channel_code_id == CHANNEL["EMAIL"]


def test_fr0140_job_alert_filters(db_session, seed_roles):
    """FR-0140: Job alert filters - alert criteria reference valid skills/location and only matching jobs are alerted."""
    user = _create_user(db_session, "CANDIDATE")

    criteria = {
        "keywords": "Backend Engineer",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "location": "San Francisco",
    }

    # 1. Save alert criteria
    alert = NotificationService.create_or_update_job_alert(
        db=db_session,
        user_id=user.id,
        criteria=criteria,
        enabled=True,
    )
    assert alert.id is not None
    assert alert.setting_value["location"] == "San Francisco"

    # 2. Matching job passes filter
    assert NotificationService.match_job_against_alert(
        alert_criteria=criteria,
        job_skills=["Python", "Docker"],
        job_location="San Francisco, CA",
    ) is True

    # 3. Non-matching job (different skills and location) fails filter
    assert NotificationService.match_job_against_alert(
        alert_criteria=criteria,
        job_skills=["Java", "Spring"],
        job_location="London, UK",
    ) is False


def test_fr0141_notification_delivery_idempotency(db_session, seed_roles):
    """FR-0141: Notification delivery idempotency - repeated callbacks yield one logical delivery state without duplicates."""
    user = _create_user(db_session, "CANDIDATE")
    notif, delivery = NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        title="Interview Reminder",
        body="Your interview is tomorrow at 10 AM",
        category_id=NOTIFICATION_TYPE["APPLICATION_UPDATE"],
        channel_id=CHANNEL["EMAIL"],
    )
    assert delivery is not None

    idempotency_key = f"deliv-call-{uuid.uuid4().hex}"
    msg_ref = f"sendgrid-msg-{uuid.uuid4().hex[:12]}"

    # First callback: sets status to DELIVERED
    d1 = NotificationService.handle_delivery_callback(
        db=db_session,
        provider_code="SENDGRID",
        provider_message_reference=msg_ref,
        delivery_status="DELIVERED",
        idempotency_key=idempotency_key,
        delivery_id=delivery.id,
    )
    assert d1.delivery_status_code_id == DELIVERY_STATUS["DELIVERED"]

    # Replay identical callback: idempotently updates without duplicating delivery records
    d2 = NotificationService.handle_delivery_callback(
        db=db_session,
        provider_code="SENDGRID",
        provider_message_reference=msg_ref,
        delivery_status="DELIVERED",
        idempotency_key=idempotency_key,
        delivery_id=delivery.id,
    )
    assert d2.id == d1.id
    assert d2.delivery_status_code_id == DELIVERY_STATUS["DELIVERED"]

    # Total deliveries for this notification remains exactly 1
    total = db_session.query(NotificationDelivery).filter(NotificationDelivery.notification_id == notif.id).count()
    assert total == 1


def test_fr0142_and_fr0207_message_retention_and_expiry(db_session, seed_roles):
    """FR-0142 & FR-0207: Message retention and body expiry - expired message body is purged/redacted while audit metadata remains."""
    user = _create_user(db_session, "CANDIDATE")

    # Create notification with retention expired 10 days ago
    notif, _ = NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        title="Security Alert",
        body="Secret PIN 1234 was used to login",
        category_id=NOTIFICATION_TYPE["SECURITY"],
        channel_id=CHANNEL["IN_APP"],
        retention_days=-10,  # Expired in past
    )

    # Before purge: body is present
    assert notif.setting_value["body"] == "Secret PIN 1234 was used to login"

    # Run retention task
    purged_count = NotificationService.purge_expired_notification_bodies(db=db_session)
    assert purged_count >= 1

    # After purge: body is redacted
    db_session.refresh(notif)
    assert notif.setting_value["body"] == "[EXPIRED_AND_PURGED]"
    assert "purged_at" in notif.setting_value

    # Audit metadata remains intact
    assert notif.id is not None
    assert notif.user_id == user.id
    assert notif.setting_code_id is not None


def test_fr0143_language_preference_fallback(db_session, seed_roles):
    """FR-0143: Language preference fallback - unsupported preference resolves to configured fallback without error."""
    # 1. Resolve valid supported language
    es_lang = Language(
        language_code="es",
        display_name="Spanish",
        is_default=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(es_lang)
    db_session.commit()

    resolved_es = NotificationService.resolve_language_preference(db_session, "es")
    assert resolved_es.language_code == "es"

    # 2. Unsupported language code resolves to default fallback 'en'
    resolved_fallback = NotificationService.resolve_language_preference(db_session, "xx-klingon")
    assert resolved_fallback.language_code == DEFAULT_FALLBACK_LANGUAGE
    assert resolved_fallback.is_default is True


def test_fr0144_community_post_length(db_session, seed_roles):
    """FR-0144: Community post length - free text within limit saves; oversized rejected, UTF-8 supported."""
    user = _create_user(db_session, "CANDIDATE")

    # 1. Valid post within 10,000 chars with UTF-8 characters and emojis
    unicode_body = "Hello Talentra! 🚀 This is an exciting community discussion. Ça va très bien! 日本語もOKです。"
    post = NotificationService.create_community_post(
        db=db_session,
        author_user_id=user.id,
        title="Community Welcome",
        body=unicode_body,
        language_code="en",
    )
    assert post.id is not None
    assert post.body == unicode_body

    # 2. Oversized post exceeding 10,000 characters is rejected
    oversized_body = "A" * (MAX_COMMUNITY_POST_LENGTH + 1)
    with pytest.raises(ValueError, match="exceeds maximum allowed limit of 10,000 characters"):
        NotificationService.create_community_post(
            db=db_session,
            author_user_id=user.id,
            title="Too Long Post",
            body=oversized_body,
        )


def test_fr0145_reaction_uniqueness(db_session, seed_roles):
    """FR-0145: Reaction uniqueness - one reaction per user/post/type toggled idempotently."""
    user = _create_user(db_session, "CANDIDATE")
    post = NotificationService.create_community_post(
        db=db_session,
        author_user_id=user.id,
        title="Post For Reactions",
        body="Discussion content",
    )

    # 1. First reaction: activates reaction (status = 1)
    r1 = NotificationService.toggle_community_reaction(
        db=db_session,
        post_id=post.id,
        user_id=user.id,
        reaction_type="LIKE",
    )
    assert r1.status_code_id == 1

    # 2. Second reaction with same user and type: toggles reaction off (status = 2)
    r2 = NotificationService.toggle_community_reaction(
        db=db_session,
        post_id=post.id,
        user_id=user.id,
        reaction_type="LIKE",
    )
    assert r2.id == r1.id
    assert r2.status_code_id == 2

    # 3. Third reaction toggles back on (status = 1)
    r3 = NotificationService.toggle_community_reaction(
        db=db_session,
        post_id=post.id,
        user_id=user.id,
        reaction_type="LIKE",
    )
    assert r3.status_code_id == 1


def test_fr0146_support_ticket_ownership(db_session, seed_roles):
    """FR-0146: Support ticket ownership - ticket access limited to requester and authorized support staff; cross-user denied."""
    candidate1 = _create_user(db_session, "CANDIDATE")
    candidate2 = _create_user(db_session, "CANDIDATE")
    admin = _create_user(db_session, "ADMIN")

    ticket = NotificationService.create_support_ticket(
        db=db_session,
        requester_user_id=candidate1.id,
        subject="Password Reset Help",
        description="I am unable to reset my password using standard link",
    )

    # 1. Requester can access their own ticket
    t_requester = NotificationService.get_support_ticket(
        db=db_session,
        ticket_id=ticket.id,
        requesting_user_id=candidate1.id,
        is_support_staff=False,
    )
    assert t_requester.id == ticket.id

    # 2. Support staff (Admin) can access any ticket
    t_admin = NotificationService.get_support_ticket(
        db=db_session,
        ticket_id=ticket.id,
        requesting_user_id=admin.id,
        is_support_staff=True,
    )
    assert t_admin.id == ticket.id

    # 3. Unrelated candidate (candidate2) is denied access with PermissionError (403)
    with pytest.raises(PermissionError, match="Access denied"):
        NotificationService.get_support_ticket(
            db=db_session,
            ticket_id=ticket.id,
            requesting_user_id=candidate2.id,
            is_support_staff=False,
        )


def test_fr0147_faq_publication_state(db_session, seed_roles):
    """FR-0147: FAQ publication state - only active/published FAQ entries appear in public queries; draft/inactive excluded."""
    now = datetime.now(timezone.utc)

    # 1. Published FAQ
    faq_published = Faq(
        code="FAQ-001",
        name="How do I apply for jobs?",
        description="Navigate to the Jobs tab and click Apply.",
        status_code_id=FAQ_STATUS["PUBLISHED"],
        created_at=now,
        updated_at=now,
    )
    # 2. Draft FAQ
    faq_draft = Faq(
        code="FAQ-002",
        name="Draft upcoming feature question",
        description="Internal instructions not yet ready for public.",
        status_code_id=FAQ_STATUS["DRAFT"],
        created_at=now,
        updated_at=now,
    )
    db_session.add(faq_published)
    db_session.add(faq_draft)
    db_session.commit()

    # Public query returns only published FAQs
    public_faqs = NotificationService.list_faqs(db=db_session, public_only=True)
    faq_ids = [f.id for f in public_faqs]
    assert faq_published.id in faq_ids
    assert faq_draft.id not in faq_ids


def test_fr0148_referral_event_attribution(db_session, seed_roles):
    """FR-0148: Referral event attribution - valid referral recorded once without duplicate credit."""
    referrer = _create_user(db_session, "CANDIDATE")
    referee = _create_user(db_session, "CANDIDATE")

    # 1. First referral event
    e1 = NotificationService.record_referral_event(
        db=db_session,
        referrer_user_id=referrer.id,
        referee_user_id=referee.id,
        referral_code="REF-ALPHA-99",
        event_type="SIGNUP",
    )
    assert e1.id is not None
    assert e1.metadata_redacted["attributed"] is True

    # 2. Duplicate referral event for same referee: returns existing record without duplicate credit
    e2 = NotificationService.record_referral_event(
        db=db_session,
        referrer_user_id=referrer.id,
        referee_user_id=referee.id,
        referral_code="REF-ALPHA-99",
        event_type="SIGNUP",
    )
    assert e2.id == e1.id

    # Total referral events for referee is 1
    total = db_session.query(ReferralEvent).filter(ReferralEvent.actor_user_id == referee.id).count()
    assert total == 1


def test_fr0149_notification_provider_outage(db_session, seed_roles):
    """FR-0149: Notification provider outage - failure is recorded and retry strategy does not lose or duplicate deliveries."""
    user = _create_user(db_session, "CANDIDATE")
    notif, delivery = NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        title="Application Status Changed",
        body="Your application was shortlisted",
        category_id=NOTIFICATION_TYPE["APPLICATION_UPDATE"],
        channel_id=CHANNEL["EMAIL"],
    )
    assert delivery is not None

    # 1. Simulate provider API outage / 504 gateway timeout
    d_fail = NotificationService.attempt_delivery_with_retry(
        db=db_session,
        delivery_id=delivery.id,
        simulate_failure=True,
    )
    assert d_fail.delivery_status_code_id == DELIVERY_STATUS["FAILED"]
    assert d_fail.attempt_count == 1

    # 2. Delivery is retried upon provider recovery
    d_recovered = NotificationService.attempt_delivery_with_retry(
        db=db_session,
        delivery_id=delivery.id,
        simulate_failure=False,
    )
    assert d_recovered.delivery_status_code_id == DELIVERY_STATUS["DELIVERED"]
    assert d_recovered.attempt_count == 2
    assert d_recovered.provider_message_reference is not None


def test_fr0150_preference_change_audit(db_session, seed_roles):
    """FR-0150: Preference change audit - change event records actor, time, and before/after values safely."""
    user = _create_user(db_session, "CANDIDATE")

    # Update preference
    pref = NotificationService.set_notification_preference(
        db=db_session,
        user_id=user.id,
        notification_type_code_id=NOTIFICATION_TYPE["SECURITY"],
        channel_code_id=CHANNEL["SMS"],
        enabled=True,
        actor_user_id=user.id,
    )

    # Check audit log in notification_preference_history
    history_entry = db_session.query(NotificationPreferenceHistory).filter(
        NotificationPreferenceHistory.notification_preference_id == pref.id,
    ).first()

    assert history_entry is not None
    assert history_entry.actor_user_id == user.id
    assert history_entry.metadata_redacted["new_enabled"] is True


# =========================================================================
# END-TO-END FASTAPI HTTP INTEGRATION TESTS
# =========================================================================

def test_api_notifications_and_community_flow(client, db_session, seed_roles):
    """End-to-end HTTP API flow for notifications, preferences, community, and support tickets."""
    user = _create_user(db_session, "CANDIDATE")
    headers = _auth_headers(user)

    # 1. POST /api/v1/preferences/notifications
    res = client.post(
        "/api/v1/preferences/notifications",
        json={
            "notification_type_code_id": 1,
            "channel_code_id": 2,
            "enabled": True,
        },
        headers=headers,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["enabled"] is True

    # 2. POST /api/v1/notifications
    res = client.post(
        "/api/v1/notifications",
        json={
            "user_id": user.id,
            "title": "Welcome to Talentra",
            "body": "Thank you for joining our talent network!",
            "category_id": 5,
            "channel_id": 1,
        },
        headers=headers,
    )
    assert res.status_code == status.HTTP_201_CREATED
    notif_id = res.json()["id"]

    # 3. GET /api/v1/notifications
    res = client.get("/api/v1/notifications", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    notifications = res.json()
    assert len(notifications) >= 1
    assert any(n["id"] == notif_id for n in notifications)

    # 4. POST /api/v1/notifications/mark-read
    res = client.post(
        "/api/v1/notifications/mark-read",
        json={"notification_ids": [notif_id]},
        headers=headers,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["updated_count"] >= 1

    # 5. POST /api/v1/community/posts
    res = client.post(
        "/api/v1/community/posts",
        json={
            "title": "Welcome Discussion",
            "body": "Let's share insights on modern distributed systems.",
            "language_code": "en",
        },
        headers=headers,
    )
    assert res.status_code == status.HTTP_201_CREATED
    post_id = res.json()["id"]

    # 6. POST /api/v1/community/posts/{id}/react
    res = client.post(
        f"/api/v1/community/posts/{post_id}/react",
        json={"post_id": post_id, "reaction_type": "LIKE"},
        headers=headers,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status_code_id"] == 1

    # 7. POST /api/v1/support/tickets
    res = client.post(
        "/api/v1/support/tickets",
        json={
            "subject": "Platform Feedback",
            "description": "The search filter is working well. Thank you!",
            "priority_code_id": 2,
        },
        headers=headers,
    )
    assert res.status_code == status.HTTP_201_CREATED
    ticket_id = res.json()["id"]

    # 8. GET /api/v1/support/tickets/{id}
    res = client.get(f"/api/v1/support/tickets/{ticket_id}", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["subject"] == "Platform Feedback"

    # 9. GET /api/v1/support/faqs
    res = client.get("/api/v1/support/faqs", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    assert isinstance(res.json(), list)
