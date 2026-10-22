"""Notifications, User Preferences, Community, Support & FAQ FastAPI Endpoints (Module M10).

Audited against:
- Talentra Database Blueprint 150+ Tables (Module: M10 Notifications, Preferences and Community)
- Talentra Final Test Cases: FR-0139 through FR-0150, FR-0207
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationPreferenceCreate,
    NotificationPreferenceResponse,
    JobAlertPreferenceCreate,
    JobAlertPreferenceResponse,
    PrivacyPreferenceCreate,
    PrivacyPreferenceResponse,
    NotificationCreate,
    NotificationResponse,
    NotificationBulkReadRequest,
    NotificationDeliveryResponse,
    NotificationDeliveryCallback,
    CommunityPostCreate,
    CommunityPostResponse,
    CommunityReactionCreate,
    CommunityReactionResponse,
    CommunityCommentCreate,
    CommunityCommentResponse,
    SupportTicketCreate,
    SupportTicketResponse,
    SupportTicketStatusUpdate,
    FaqCreate,
    FaqResponse,
    ReferralEventCreate,
    ReferralEventResponse,
)
from app.services.notification_service import NotificationService, FAQ_STATUS

router = APIRouter(tags=["Notifications, Preferences & Community"])


# =========================================================================
# 1. Notifications & In-App Alerts (FR-0139, FR-0141, FR-0142, FR-0207)
# =========================================================================

@router.get("/notifications", response_model=List[NotificationResponse])
def get_user_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve notifications for the authenticated user with unread filtering."""
    notifications = NotificationService.list_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    res = []
    for notif in notifications:
        val = notif.setting_value or {}
        res.append(
            NotificationResponse(
                id=notif.id,
                user_id=notif.user_id,
                setting_code_id=notif.setting_code_id,
                setting_value=notif.setting_value,
                enabled=notif.enabled,
                is_read=val.get("is_read", False),
                title=val.get("title"),
                body=val.get("body"),
                created_at=notif.created_at,
                updated_at=notif.updated_at,
            )
        )
    return res


@router.post("/notifications", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a notification respecting user channel preferences (FR-0139)."""
    notif, _ = NotificationService.create_notification(
        db=db,
        user_id=payload.user_id,
        title=payload.title,
        body=payload.body,
        category_id=payload.category_id,
        channel_id=payload.channel_id,
        priority=payload.priority,
        link=payload.link,
        retention_days=payload.retention_days,
        actor_user_id=current_user.id,
    )
    val = notif.setting_value or {}
    return NotificationResponse(
        id=notif.id,
        user_id=notif.user_id,
        setting_code_id=notif.setting_code_id,
        setting_value=notif.setting_value,
        enabled=notif.enabled,
        is_read=val.get("is_read", False),
        title=val.get("title"),
        body=val.get("body"),
        created_at=notif.created_at,
        updated_at=notif.updated_at,
    )


@router.post("/notifications/mark-read")
def mark_notifications_read(
    payload: NotificationBulkReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark notifications as read in bulk for the authenticated user."""
    count = NotificationService.mark_notifications_read(
        db=db,
        user_id=current_user.id,
        notification_ids=payload.notification_ids,
    )
    return {"updated_count": count}


@router.post("/notifications/purge-expired")
def purge_expired_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Purge and redact notification message bodies whose retention period expired (FR-0142, FR-0207)."""
    purged_count = NotificationService.purge_expired_notification_bodies(db=db)
    return {"purged_count": purged_count}


@router.post("/notifications/delivery/callback")
def process_delivery_callback(
    payload: NotificationDeliveryCallback,
    db: Session = Depends(get_db),
):
    """Idempotently process external notification delivery callback (FR-0141)."""
    try:
        delivery = NotificationService.handle_delivery_callback(
            db=db,
            provider_code=payload.provider_code,
            provider_message_reference=payload.provider_message_reference,
            delivery_status=payload.delivery_status,
            idempotency_key=payload.idempotency_key,
            error_message=payload.error_message,
        )
        return {
            "status": "processed",
            "delivery_id": delivery.id,
            "delivery_status_code_id": delivery.delivery_status_code_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =========================================================================
# 2. Preferences (FR-0139, FR-0140, FR-0150)
# =========================================================================

@router.get("/preferences/notifications", response_model=List[NotificationPreferenceResponse])
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get authenticated user's notification preferences."""
    prefs = NotificationService.get_user_notification_preferences(db, current_user.id)
    return prefs


@router.post("/preferences/notifications", response_model=NotificationPreferenceResponse)
def update_notification_preference(
    payload: NotificationPreferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update notification preference and record an auditable history event (FR-0139, FR-0150)."""
    pref = NotificationService.set_notification_preference(
        db=db,
        user_id=current_user.id,
        notification_type_code_id=payload.notification_type_code_id,
        channel_code_id=payload.channel_code_id,
        enabled=payload.enabled,
        actor_user_id=current_user.id,
    )
    return pref


@router.post("/preferences/job-alerts", response_model=JobAlertPreferenceResponse)
def save_job_alert_preference(
    payload: JobAlertPreferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save candidate job alert search criteria (FR-0140)."""
    alert = NotificationService.create_or_update_job_alert(
        db=db,
        user_id=current_user.id,
        criteria=payload.setting_value,
        enabled=payload.enabled,
    )
    return alert


# =========================================================================
# 3. Community (FR-0144, FR-0145)
# =========================================================================

@router.post("/community/posts", response_model=CommunityPostResponse, status_code=status.HTTP_201_CREATED)
def create_community_post(
    payload: CommunityPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0144: Create a community post enforcing 10,000 char maximum boundary with UTF-8 support."""
    try:
        post = NotificationService.create_community_post(
            db=db,
            author_user_id=current_user.id,
            title=payload.title,
            body=payload.body,
            language_code=payload.language_code,
        )
        return post
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/community/posts/{post_id}/react", response_model=CommunityReactionResponse)
def react_to_community_post(
    post_id: int,
    payload: CommunityReactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0145: Toggle reaction on community post ensuring reaction uniqueness per user/post/type."""
    reaction = NotificationService.toggle_community_reaction(
        db=db,
        post_id=post_id,
        user_id=current_user.id,
        reaction_type=payload.reaction_type,
    )
    return reaction


# =========================================================================
# 4. Support Tickets & FAQ (FR-0146, FR-0147)
# =========================================================================

@router.post("/support/tickets", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
def create_support_ticket(
    payload: SupportTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new support ticket."""
    ticket = NotificationService.create_support_ticket(
        db=db,
        requester_user_id=current_user.id,
        subject=payload.subject,
        description=payload.description,
        priority_code_id=payload.priority_code_id,
    )
    return ticket


@router.get("/support/tickets/{ticket_id}", response_model=SupportTicketResponse)
def get_support_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0146: Retrieve support ticket strictly verifying requester ownership or staff privilege."""
    is_staff = any(r.role.role_code in ["ADMIN", "SUPER_ADMIN"] for r in current_user.role_assignments)
    try:
        ticket = NotificationService.get_support_ticket(
            db=db,
            ticket_id=ticket_id,
            requesting_user_id=current_user.id,
            is_support_staff=is_staff,
        )
        return ticket
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/support/faqs", response_model=List[FaqResponse])
def get_faqs(
    public_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """FR-0147: Query FAQs; public queries strictly filter out draft/inactive entries."""
    faqs = NotificationService.list_faqs(db=db, public_only=public_only)
    return faqs


# =========================================================================
# 5. Referrals (FR-0148)
# =========================================================================

@router.post("/referrals", response_model=ReferralEventResponse, status_code=status.HTTP_201_CREATED)
def record_referral(
    payload: ReferralEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0148: Record a referral event without duplicate attribution credit."""
    ref_event = NotificationService.record_referral_event(
        db=db,
        referrer_user_id=payload.referrer_user_id,
        referee_user_id=payload.referee_user_id,
        referral_code=payload.referral_code,
        event_type=payload.event_type,
    )
    return ref_event
