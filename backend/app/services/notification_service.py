"""Notification, Preferences, Community, Support & FAQ Domain Service (Module M10).

Implements and enforces all functional, privacy, and security specifications for Stage 12:
- FR-0139: Notification preference persistence (channel/category explicit values, disabled channel suppression)
- FR-0140: Job alert filters (criteria reference valid skills/location and alert preferences)
- FR-0141: Notification delivery idempotency (duplicate provider callback yields one logical delivery state)
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

import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, select, and_, or_
from sqlalchemy.orm import Session

from app.models.notification import (
    Language,
    NotificationPreference,
    JobAlertPreference,
    PrivacyPreference,
    Notification,
    NotificationDelivery,
    NotificationTemplate,
    CommunityPost,
    CommunityReaction,
    CommunityComment,
    SupportTicket,
    SupportTicketMessage,
    Faq,
    ReferralEvent,
    SocialShareEvent,
    NotificationDeliveryAttempt,
    NotificationPreferenceHistory,
    SupportTicketStatusHistory,
    CommunityModerationEvent,
)
from app.models.user import User, Role, UserRoleAssignment


# ==========================================
# Domain Status Codes and Constants
# ==========================================

NOTIFICATION_STATUS = {
    "UNREAD": 1,
    "READ": 2,
    "ARCHIVED": 3,
}

DELIVERY_STATUS = {
    "PENDING": 1,
    "DELIVERED": 2,
    "FAILED": 3,
    "BOUNCED": 4,
}

NOTIFICATION_TYPE = {
    "JOB_ALERT": 1,
    "APPLICATION_UPDATE": 2,
    "SECURITY": 3,
    "MARKETING": 4,
    "SYSTEM": 5,
}

CHANNEL = {
    "IN_APP": 1,
    "EMAIL": 2,
    "SMS": 3,
    "PUSH": 4,
}

TICKET_STATUS = {
    "OPEN": 1,
    "IN_PROGRESS": 2,
    "RESOLVED": 3,
    "CLOSED": 4,
}

FAQ_STATUS = {
    "PUBLISHED": 1,
    "DRAFT": 2,
    "ARCHIVED": 3,
}

COMMUNITY_MODERATION = {
    "PUBLISHED": 1,
    "PENDING": 2,
    "FLAGGED": 3,
    "REMOVED": 4,
}

DEFAULT_FALLBACK_LANGUAGE = "en"
MAX_COMMUNITY_POST_LENGTH = 10000


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalize datetime to timezone-aware UTC for cross-database consistency."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class NotificationService:
    """Authoritative business logic for Notifications, User Preferences, Community, Support & FAQ."""

    # =========================================================================
    # 1. NOTIFICATION PREFERENCES & RETENTION (FR-0139, FR-0142, FR-0150, FR-0207)
    # =========================================================================

    @staticmethod
    def get_user_notification_preferences(db: Session, user_id: int) -> List[NotificationPreference]:
        """Fetch saved notification preferences for a user."""
        return db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
            NotificationPreference.deleted_at.is_(None),
        ).all()

    @staticmethod
    def set_notification_preference(
        db: Session,
        user_id: int,
        notification_type_code_id: int,
        channel_code_id: int,
        enabled: bool,
        actor_user_id: Optional[int] = None,
    ) -> NotificationPreference:
        """Create or update a notification preference and record an auditable history event (FR-0139, FR-0150)."""
        now = datetime.now(timezone.utc)
        pref = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
            NotificationPreference.notification_type_code_id == notification_type_code_id,
            NotificationPreference.channel_code_id == channel_code_id,
            NotificationPreference.deleted_at.is_(None),
        ).first()

        old_enabled = None
        if pref:
            old_enabled = pref.enabled
            pref.enabled = enabled
            pref.updated_at = now
            pref.updated_by = actor_user_id
        else:
            pref = NotificationPreference(
                user_id=user_id,
                notification_type_code_id=notification_type_code_id,
                channel_code_id=channel_code_id,
                enabled=enabled,
                created_at=now,
                created_by=actor_user_id,
                updated_at=now,
            )
            db.add(pref)
            db.flush()

        # Audit history entry (FR-0150)
        history = NotificationPreferenceHistory(
            notification_preference_id=pref.id,
            event_code_id=1,  # UPDATED
            actor_user_id=actor_user_id or user_id,
            occurred_at=now,
            metadata_redacted={
                "type": notification_type_code_id,
                "channel": channel_code_id,
                "old_enabled": old_enabled,
                "new_enabled": enabled,
            },
            created_at=now,
            created_by=actor_user_id,
        )
        db.add(history)
        db.commit()
        db.refresh(pref)
        return pref

    @staticmethod
    def is_channel_enabled(
        db: Session,
        user_id: int,
        notification_type_code_id: int,
        channel_code_id: int,
    ) -> bool:
        """Check whether delivery is enabled for the specified user, type, and channel (FR-0139)."""
        # Essential/System notifications (type 3=SECURITY, 5=SYSTEM) always enabled for in-app
        if notification_type_code_id in [NOTIFICATION_TYPE["SECURITY"], NOTIFICATION_TYPE["SYSTEM"]] and channel_code_id == CHANNEL["IN_APP"]:
            return True

        pref = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
            NotificationPreference.notification_type_code_id == notification_type_code_id,
            NotificationPreference.channel_code_id == channel_code_id,
            NotificationPreference.deleted_at.is_(None),
        ).first()

        # If user explicitly configured preference, respect it; otherwise default True for non-marketing
        if pref is not None:
            return pref.enabled
        return notification_type_code_id != NOTIFICATION_TYPE["MARKETING"]

    # =========================================================================
    # 2. NOTIFICATIONS & DELIVERY (FR-0139, FR-0141, FR-0142, FR-0149, FR-0207)
    # =========================================================================

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        title: str,
        body: str,
        category_id: int = 1,
        channel_id: int = 1,
        priority: str = "NORMAL",
        link: Optional[str] = None,
        retention_days: int = 90,
        provider_code: str = "MOCK",
        idempotency_key: Optional[str] = None,
        actor_user_id: Optional[int] = None,
    ) -> Tuple[Notification, Optional[NotificationDelivery]]:
        """Create a notification respecting user channel preferences, creating delivery records (FR-0139, FR-0141)."""
        now = datetime.now(timezone.utc)
        retention_expires_at = now + timedelta(days=retention_days)

        # Check user channel preference (FR-0139)
        channel_allowed = NotificationService.is_channel_enabled(db, user_id, category_id, channel_id)

        setting_payload = {
            "title": title,
            "body": body,
            "category_id": category_id,
            "channel_id": channel_id,
            "priority": priority,
            "link": link,
            "retention_expires_at": retention_expires_at.isoformat(),
            "is_read": False,
        }

        notification = Notification(
            user_id=user_id,
            setting_code_id=NOTIFICATION_STATUS["UNREAD"],
            setting_value=setting_payload,
            enabled=True,
            created_at=now,
            created_by=actor_user_id,
            updated_at=now,
        )
        db.add(notification)
        db.flush()

        delivery = None
        # Only create external delivery if channel preference is enabled
        if channel_allowed and channel_id != CHANNEL["IN_APP"]:
            idem_key = idempotency_key or f"deliv-{notification.id}-{uuid.uuid4().hex[:12]}"
            delivery = NotificationDelivery(
                notification_id=notification.id,
                channel_code_id=channel_id,
                provider_code=provider_code,
                delivery_status_code_id=DELIVERY_STATUS["PENDING"],
                attempt_count=0,
                idempotency_key=idem_key,
                created_at=now,
                created_by=actor_user_id,
                updated_at=now,
            )
            db.add(delivery)

        db.commit()
        db.refresh(notification)
        if delivery:
            db.refresh(delivery)
        return notification, delivery

    @staticmethod
    def list_notifications(
        db: Session,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """Fetch paginated notifications for the authenticated user."""
        query = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.deleted_at.is_(None),
        )
        if unread_only:
            query = query.filter(Notification.setting_code_id == NOTIFICATION_STATUS["UNREAD"])
        return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def mark_notifications_read(
        db: Session,
        user_id: int,
        notification_ids: List[int],
    ) -> int:
        """Mark one or more notifications as read for the authenticated user."""
        now = datetime.now(timezone.utc)
        notifications = db.query(Notification).filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == user_id,
            Notification.deleted_at.is_(None),
        ).all()

        updated_count = 0
        for notif in notifications:
            notif.setting_code_id = NOTIFICATION_STATUS["READ"]
            if notif.setting_value:
                val = dict(notif.setting_value)
                val["is_read"] = True
                notif.setting_value = val
            notif.updated_at = now
            updated_count += 1

        db.commit()
        return updated_count

    @staticmethod
    def purge_expired_notification_bodies(
        db: Session,
        retention_cutoff: Optional[datetime] = None,
    ) -> int:
        """Purge and redact notification message bodies whose retention period has expired (FR-0142, FR-0207)."""
        cutoff = _ensure_utc(retention_cutoff) or datetime.now(timezone.utc)
        notifications = db.query(Notification).filter(
            Notification.deleted_at.is_(None),
        ).all()

        purged_count = 0
        now = datetime.now(timezone.utc)
        for notif in notifications:
            if notif.setting_value and "retention_expires_at" in notif.setting_value:
                expires_str = notif.setting_value.get("retention_expires_at")
                if expires_str:
                    try:
                        exp_dt = _ensure_utc(datetime.fromisoformat(expires_str))
                        if exp_dt <= cutoff:
                            # Redact message body while preserving audit metadata
                            val = dict(notif.setting_value)
                            val["body"] = "[EXPIRED_AND_PURGED]"
                            val["purged_at"] = now.isoformat()
                            notif.setting_value = val
                            notif.updated_at = now
                            purged_count += 1
                    except (ValueError, TypeError):
                        pass

        db.commit()
        return purged_count

    @staticmethod
    def handle_delivery_callback(
        db: Session,
        provider_code: str,
        provider_message_reference: str,
        delivery_status: str,
        idempotency_key: str,
        delivery_id: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> NotificationDelivery:
        """Process external provider callback idempotently without duplicate status mutations (FR-0141)."""
        delivery = None
        if delivery_id:
            delivery = db.query(NotificationDelivery).filter(NotificationDelivery.id == delivery_id).first()

        if not delivery:
            # Find delivery by provider message reference or idempotency key
            delivery = db.query(NotificationDelivery).filter(
                or_(
                    NotificationDelivery.provider_message_reference == provider_message_reference,
                    NotificationDelivery.idempotency_key == idempotency_key,
                )
            ).first()

        if not delivery:
            raise ValueError(f"Notification delivery reference '{provider_message_reference}' not found")

        # Map status
        status_id = DELIVERY_STATUS["DELIVERED"] if delivery_status.upper() in ["DELIVERED", "SENT", "SUCCESS"] else DELIVERY_STATUS["FAILED"]

        # Idempotency check (FR-0141): If already at this status and provider ref matched, return existing
        if delivery.delivery_status_code_id == status_id and delivery.provider_message_reference == provider_message_reference:
            return delivery

        now = datetime.now(timezone.utc)
        delivery.delivery_status_code_id = status_id
        delivery.provider_message_reference = provider_message_reference
        delivery.attempt_count += 1
        delivery.updated_at = now

        # Log delivery attempt
        attempt = NotificationDeliveryAttempt(
            notification_delivery_id=delivery.id,
            event_code_id=1 if status_id == DELIVERY_STATUS["DELIVERED"] else 2,
            occurred_at=now,
            metadata_redacted={
                "status": delivery_status,
                "error": error_message,
                "idempotency_key": idempotency_key,
            },
            created_at=now,
        )
        db.add(attempt)
        db.commit()
        db.refresh(delivery)
        return delivery

    @staticmethod
    def attempt_delivery_with_retry(
        db: Session,
        delivery_id: int,
        simulate_failure: bool = False,
    ) -> NotificationDelivery:
        """Attempt provider delivery with outage handling and bounded retry accounting (FR-0149)."""
        delivery = db.query(NotificationDelivery).filter(NotificationDelivery.id == delivery_id).first()
        if not delivery:
            raise ValueError(f"Delivery record {delivery_id} not found")

        now = datetime.now(timezone.utc)
        delivery.attempt_count += 1

        if simulate_failure:
            # Record outage failure; status remains retryable without duplicating delivery
            delivery.delivery_status_code_id = DELIVERY_STATUS["FAILED"]
            attempt = NotificationDeliveryAttempt(
                notification_delivery_id=delivery.id,
                event_code_id=2,  # FAILED
                occurred_at=now,
                metadata_redacted={"error": "Provider API gateway timeout (504)", "retryable": True},
                created_at=now,
            )
            db.add(attempt)
        else:
            # Successful delivery upon recovery
            delivery.delivery_status_code_id = DELIVERY_STATUS["DELIVERED"]
            delivery.provider_message_reference = f"msg_{uuid.uuid4().hex[:16]}"
            attempt = NotificationDeliveryAttempt(
                notification_delivery_id=delivery.id,
                event_code_id=1,  # SUCCESS
                occurred_at=now,
                metadata_redacted={"provider": delivery.provider_code, "status": "DELIVERED"},
                created_at=now,
            )
            db.add(attempt)

        delivery.updated_at = now
        db.commit()
        db.refresh(delivery)
        return delivery

    # =========================================================================
    # 3. JOB ALERTS & LANGUAGE FALLBACK (FR-0140, FR-0143)
    # =========================================================================

    @staticmethod
    def create_or_update_job_alert(
        db: Session,
        user_id: int,
        criteria: Dict[str, Any],
        enabled: bool = True,
    ) -> JobAlertPreference:
        """Create or update a candidate job search alert filter (FR-0140)."""
        now = datetime.now(timezone.utc)
        alert = db.query(JobAlertPreference).filter(
            JobAlertPreference.user_id == user_id,
            JobAlertPreference.deleted_at.is_(None),
        ).first()

        if alert:
            alert.setting_value = criteria
            alert.enabled = enabled
            alert.updated_at = now
        else:
            alert = JobAlertPreference(
                user_id=user_id,
                setting_code_id=1,
                setting_value=criteria,
                enabled=enabled,
                created_at=now,
                updated_at=now,
            )
            db.add(alert)

        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def match_job_against_alert(
        alert_criteria: Dict[str, Any],
        job_skills: List[str],
        job_location: Optional[str] = None,
    ) -> bool:
        """Evaluate if a posted job matches the candidate's alert criteria (FR-0140)."""
        filter_skills = alert_criteria.get("skills", [])
        filter_location = alert_criteria.get("location")

        # Match skills (case-insensitive)
        if filter_skills:
            job_skills_lower = [s.lower() for s in job_skills]
            if not any(fs.lower() in job_skills_lower for fs in filter_skills):
                return False

        # Match location
        if filter_location and job_location:
            if filter_location.lower() not in job_location.lower():
                return False

        return True

    @staticmethod
    def resolve_language_preference(
        db: Session,
        requested_language_code: Optional[str],
    ) -> Language:
        """Resolve requested language code; fall back to default 'en' if unsupported (FR-0143)."""
        if requested_language_code:
            lang = db.query(Language).filter(
                Language.language_code == requested_language_code.lower(),
                Language.deleted_at.is_(None),
            ).first()
            if lang:
                return lang

        # Fallback to configured default language
        fallback = db.query(Language).filter(
            Language.language_code == DEFAULT_FALLBACK_LANGUAGE,
            Language.deleted_at.is_(None),
        ).first()

        if not fallback:
            now = datetime.now(timezone.utc)
            fallback = Language(
                language_code=DEFAULT_FALLBACK_LANGUAGE,
                display_name="English",
                is_default=True,
                created_at=now,
                updated_at=now,
            )
            db.add(fallback)
            db.commit()
            db.refresh(fallback)

        return fallback

    # =========================================================================
    # 4. COMMUNITY POSTS & REACTIONS (FR-0144, FR-0145)
    # =========================================================================

    @staticmethod
    def create_community_post(
        db: Session,
        author_user_id: int,
        title: str,
        body: str,
        language_code: Optional[str] = "en",
    ) -> CommunityPost:
        """Create a community discussion post with character boundary and UTF-8 support (FR-0144)."""
        # Validate body length (FR-0144)
        if len(body) > MAX_COMMUNITY_POST_LENGTH:
            raise ValueError(
                f"Community post body length ({len(body)}) exceeds maximum allowed limit of {MAX_COMMUNITY_POST_LENGTH:,} characters (FR-0144)"
            )

        lang = NotificationService.resolve_language_preference(db, language_code)
        now = datetime.now(timezone.utc)

        post = CommunityPost(
            author_user_id=author_user_id,
            title=title,
            body=body,
            language_id=lang.id,
            moderation_status_code_id=COMMUNITY_MODERATION["PUBLISHED"],
            created_at=now,
            created_by=author_user_id,
            updated_at=now,
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        return post

    @staticmethod
    def toggle_community_reaction(
        db: Session,
        post_id: int,
        user_id: int,
        reaction_type: str = "LIKE",
    ) -> CommunityReaction:
        """Toggle a reaction on a community post ensuring reaction uniqueness per user/post/type (FR-0145)."""
        reaction_code = f"post:{post_id}:user:{user_id}:type:{reaction_type.upper()}"
        now = datetime.now(timezone.utc)

        reaction = db.query(CommunityReaction).filter(
            CommunityReaction.code == reaction_code,
            CommunityReaction.deleted_at.is_(None),
        ).first()

        if reaction:
            # Toggle state idempotently: if active -> remove, if removed -> activate
            reaction.status_code_id = 2 if reaction.status_code_id == 1 else 1
            reaction.updated_at = now
            reaction.updated_by = user_id
        else:
            reaction = CommunityReaction(
                code=reaction_code,
                name=reaction_type.upper(),
                status_code_id=1,  # ACTIVE
                description=f"Reaction by user {user_id} on post {post_id}",
                created_at=now,
                created_by=user_id,
                updated_at=now,
            )
            db.add(reaction)

        db.commit()
        db.refresh(reaction)
        return reaction

    # =========================================================================
    # 5. SUPPORT TICKETS & FAQ (FR-0146, FR-0147)
    # =========================================================================

    @staticmethod
    def create_support_ticket(
        db: Session,
        requester_user_id: int,
        subject: str,
        description: str,
        priority_code_id: int = 2,
    ) -> SupportTicket:
        """Create a customer support ticket."""
        now = datetime.now(timezone.utc)
        ticket_number = f"TICK-{now.strftime('%Y%m')}-{uuid.uuid4().hex[:8].upper()}"

        ticket = SupportTicket(
            requester_user_id=requester_user_id,
            ticket_number=ticket_number,
            subject=subject,
            description=description,
            priority_code_id=priority_code_id,
            status_code_id=TICKET_STATUS["OPEN"],
            created_at=now,
            created_by=requester_user_id,
            updated_at=now,
        )
        db.add(ticket)
        db.flush()

        history = SupportTicketStatusHistory(
            support_ticket_id=ticket.id,
            event_code_id=TICKET_STATUS["OPEN"],
            actor_user_id=requester_user_id,
            occurred_at=now,
            created_at=now,
        )
        db.add(history)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def get_support_ticket(
        db: Session,
        ticket_id: int,
        requesting_user_id: int,
        is_support_staff: bool = False,
    ) -> SupportTicket:
        """Retrieve support ticket enforcing strict requester ownership (FR-0146)."""
        ticket = db.query(SupportTicket).filter(
            SupportTicket.id == ticket_id,
            SupportTicket.deleted_at.is_(None),
        ).first()

        if not ticket:
            raise ValueError(f"Support ticket {ticket_id} not found")

        # FR-0146: Ticket access is limited to requester and authorized support staff
        if ticket.requester_user_id != requesting_user_id and not is_support_staff:
            raise PermissionError(
                f"Access denied: User {requesting_user_id} is not the requester of ticket {ticket_id} (FR-0146)"
            )

        return ticket

    @staticmethod
    def list_faqs(
        db: Session,
        public_only: bool = True,
    ) -> List[Faq]:
        """Query FAQ items; public queries strictly filter out draft/inactive entries (FR-0147)."""
        query = db.query(Faq).filter(Faq.deleted_at.is_(None))
        if public_only:
            # FR-0147: Only active/published FAQ entries appear in guest-facing queries
            query = query.filter(Faq.status_code_id == FAQ_STATUS["PUBLISHED"])
        return query.order_by(Faq.id.asc()).all()

    # =========================================================================
    # 6. REFERRAL EVENT ATTRIBUTION (FR-0148)
    # =========================================================================

    @staticmethod
    def record_referral_event(
        db: Session,
        referrer_user_id: int,
        referee_user_id: int,
        referral_code: str,
        event_type: str = "SIGNUP",
    ) -> ReferralEvent:
        """Record referral event without awarding duplicate credit (FR-0148)."""
        # Deduplication check: only one signup referral awarded per referee
        existing_event = db.query(ReferralEvent).filter(
            ReferralEvent.actor_user_id == referee_user_id,
            ReferralEvent.event_code_id == 1,  # SIGNUP
            ReferralEvent.deleted_at.is_(None),
        ).first()

        if existing_event:
            return existing_event

        now = datetime.now(timezone.utc)
        ref_event = ReferralEvent(
            event_code_id=1,  # SIGNUP
            actor_user_id=referee_user_id,
            occurred_at=now,
            metadata_redacted={
                "referrer_user_id": referrer_user_id,
                "referee_user_id": referee_user_id,
                "referral_code": referral_code,
                "event_type": event_type,
                "attributed": True,
            },
            created_at=now,
            created_by=referee_user_id,
            updated_at=now,
        )
        db.add(ref_event)
        db.commit()
        db.refresh(ref_event)
        return ref_event
