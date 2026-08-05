"""
app/services/notification_service.py

Business logic for the Notification module.

Responsibilities
----------------
- Create individual or broadcast notifications
- List notifications visible to the current user
  (own user-specific + all broadcasts matching their role)
- Get a single notification (with ownership check)
- Mark a notification as read
- Soft-delete a notification (Government can delete any; users delete own)
- Transaction rollback on all write failures

Delivery modes
--------------
1. User-specific  — recipient_id set; appears only in that user's inbox
2. Role broadcast — recipient_role set; visible to all users with that role
3. Both           — user-specific with role context preserved for audit

Filtering (list endpoint)
--------------------------
- priority : exact NotificationPriority match
- is_read  : boolean filter (unread / read)
- search   : keyword across title and message

Sorting
-------
- newest   (created_at DESC, default)
- oldest   (created_at ASC)
- priority (priority ordering: critical > high > medium > low)
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import NotificationPriority, RoleEnum
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationCreate, NotificationUpdate

logger = logging.getLogger("app.services.notification_service")

# Priority ordering for sort (higher = more urgent)
_PRIORITY_ORDER = case(
    (Notification.priority == NotificationPriority.CRITICAL, 4),
    (Notification.priority == NotificationPriority.HIGH, 3),
    (Notification.priority == NotificationPriority.MEDIUM, 2),
    (Notification.priority == NotificationPriority.LOW, 1),
    else_=0,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_or_404(db: Session, notification_id: UUID) -> Notification:
    """Load a non-deleted Notification by UUID, or raise HTTP 404."""
    stmt = (
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.is_deleted.is_(False))
    )
    obj = db.execute(stmt).scalar_one_or_none()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with id '{notification_id}' not found.",
        )
    return obj


def _assert_visible(notification: Notification, current_user: User) -> None:
    """
    Assert that a user is allowed to view/interact with a notification.

    Visibility rules:
    - Government users can access any notification.
    - A user can access any notification addressed to them (recipient_id match).
    - A user can access any broadcast notification targeting their role.
    """
    if current_user.role == RoleEnum.GOVERNMENT:
        return
    is_addressed_to_user = (
        notification.recipient_id is not None
        and notification.recipient_id == current_user.id
    )
    is_role_broadcast = (
        notification.recipient_id is None
        and notification.recipient_role == current_user.role
    )
    if not (is_addressed_to_user or is_role_broadcast):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this notification.",
        )


def _base_visible_stmt(current_user: User):
    """
    Build the base SELECT for notifications visible to the current user.

    Government: all non-deleted notifications.
    Others: user-specific (recipient_id = self) OR role broadcast.
    """
    base = select(Notification).where(Notification.is_deleted.is_(False))
    if current_user.role == RoleEnum.GOVERNMENT:
        return base
    return base.where(
        or_(
            Notification.recipient_id == current_user.id,
            (Notification.recipient_id.is_(None))
            & (Notification.recipient_role == current_user.role),
        )
    )


def _apply_filters(
    stmt,
    priority: Optional[NotificationPriority],
    is_read: Optional[bool],
    search: Optional[str],
):
    if priority:
        stmt = stmt.where(Notification.priority == priority)
    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)
    if search:
        term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Notification.title.ilike(term),
                Notification.message.ilike(term),
            )
        )
    return stmt


def _resolve_sort(sort_by: str):
    _map = {
        "newest": (Notification.created_at.desc(),),
        "oldest": (Notification.created_at.asc(),),
        "priority": (_PRIORITY_ORDER.desc(), Notification.created_at.desc()),
    }
    return _map.get(sort_by, (Notification.created_at.desc(),))


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------


def create_notification(
    db: Session,
    data: NotificationCreate,
) -> Notification:
    """
    Create a new notification (user-specific or broadcast).

    Args:
        db:   Active database session.
        data: Validated NotificationCreate payload.

    Returns:
        The created Notification ORM instance.

    Raises:
        HTTPException 404: recipient_id provided but user not found.
        HTTPException 500: Database write failure.
    """
    # Validate recipient_id exists if provided
    if data.recipient_id is not None:
        exists = db.execute(
            select(func.count())
            .select_from(User)
            .where(User.id == data.recipient_id)
            .where(User.is_deleted.is_(False))
        ).scalar_one()
        if exists == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipient user '{data.recipient_id}' not found.",
            )

    notification = Notification(
        title=data.title,
        message=data.message,
        priority=data.priority,
        recipient_role=data.recipient_role,
        recipient_id=data.recipient_id,
        is_read=False,
    )
    try:
        db.add(notification)
        db.commit()
        db.refresh(notification)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to create notification: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification. Please try again.",
        ) from exc

    logger.info(
        "Notification created: id=%s priority=%s recipient_role=%s recipient_id=%s",
        notification.id,
        notification.priority,
        notification.recipient_role,
        notification.recipient_id,
    )
    return notification


def get_notification_by_id(
    db: Session,
    notification_id: UUID,
    current_user: User,
) -> Notification:
    """
    Retrieve a single notification, enforcing visibility rules.

    Args:
        db:              Active database session.
        notification_id: UUID of the notification to fetch.
        current_user:    Authenticated requesting user.

    Returns:
        The matching Notification ORM instance.

    Raises:
        HTTPException 403: User is not the intended recipient.
        HTTPException 404: Notification not found or soft-deleted.
    """
    notification = _get_or_404(db, notification_id)
    _assert_visible(notification, current_user)
    return notification


def list_notifications(
    db: Session,
    current_user: User,
    priority: Optional[NotificationPriority] = None,
    is_read: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = "newest",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Notification], int]:
    """
    List notifications visible to the current user with filtering and pagination.

    Args:
        db:           Active database session.
        current_user: Authenticated user whose inbox to list.
        priority:     Filter by urgency level.
        is_read:      Filter by read/unread status.
        search:       Keyword search across title and message.
        sort_by:      newest | oldest | priority.
        page:         1-indexed page number.
        page_size:    Results per page.

    Returns:
        (list of Notification ORM objects, total matching count)
    """
    base = _base_visible_stmt(current_user)
    base = _apply_filters(base, priority=priority, is_read=is_read, search=search)

    count_stmt = select(func.count()).select_from(base.subquery())
    total: int = db.execute(count_stmt).scalar_one()

    order_exprs = _resolve_sort(sort_by)
    items_stmt = (
        base.order_by(*order_exprs)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    notifications = list(db.execute(items_stmt).scalars().all())
    return notifications, total


def mark_as_read(
    db: Session,
    notification_id: UUID,
    current_user: User,
) -> Notification:
    """
    Mark a notification as read (is_read = True).

    Enforces visibility — users cannot mark notifications they shouldn't see.

    Args:
        db:              Active database session.
        notification_id: UUID of the notification to mark.
        current_user:    Authenticated user.

    Returns:
        The updated Notification ORM instance.

    Raises:
        HTTPException 403: User is not the intended recipient.
        HTTPException 404: Notification not found.
        HTTPException 500: Database write failure.
    """
    notification = _get_or_404(db, notification_id)
    _assert_visible(notification, current_user)

    if notification.is_read:
        return notification  # Already read — no-op

    notification.is_read = True
    try:
        db.commit()
        db.refresh(notification)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Failed to mark notification %s as read: %s", notification_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read. Please try again.",
        ) from exc

    logger.info("Notification marked as read: id=%s user=%s", notification_id, current_user.id)
    return notification


def delete_notification(
    db: Session,
    notification_id: UUID,
    current_user: User,
) -> None:
    """
    Soft-delete a notification.

    Government can delete any notification.
    Other users can only delete notifications addressed specifically to them
    (recipient_id == current_user.id). Broadcast notifications cannot be
    deleted by regular users.

    Args:
        db:              Active database session.
        notification_id: UUID of the notification to delete.
        current_user:    Authenticated user.

    Raises:
        HTTPException 403: Insufficient permission.
        HTTPException 404: Notification not found.
        HTTPException 500: Database write failure.
    """
    notification = _get_or_404(db, notification_id)

    if current_user.role != RoleEnum.GOVERNMENT:
        # Non-government users may only delete their own user-specific notifications
        if notification.recipient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You can only delete notifications addressed directly to you. "
                    "Broadcast notifications can only be deleted by Government users."
                ),
            )

    notification.is_deleted = True
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Failed to delete notification %s: %s", notification_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification. Please try again.",
        ) from exc

    logger.info("Notification soft-deleted: id=%s", notification_id)
