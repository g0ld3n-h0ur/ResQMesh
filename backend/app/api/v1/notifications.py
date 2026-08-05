"""
app/api/v1/notifications.py

Notification router — complete production implementation.

Prefix : /api/v1/notifications
Tags   : Notifications

Endpoint map
------------
POST  /                              → Create a notification / broadcast     (Government)
GET   /                              → List notifications for current user    (All authenticated)
GET   /{notification_id}             → Get a specific notification            (All authenticated)
PATCH /{notification_id}/read        → Mark a notification as read            (All authenticated)
DELETE /{notification_id}            → Soft-delete a notification             (Gov + own)

Permissions
-----------
Government : Create + read all + mark read + delete any
Others     : Read own/role-broadcast + mark read + delete own user-specific
"""

from __future__ import annotations

from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import RequireGovernment
from app.dependencies.auth import CurrentUser
from app.database.session import get_db
from app.models.enums import NotificationPriority
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.services import notification_service
from app.utils.constants import (
    API_V1_TAG_NOTIFICATIONS,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from app.utils.response import paginated_response, success_response

router = APIRouter(
    prefix="/notifications",
    tags=[API_V1_TAG_NOTIFICATIONS],
)


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _serialize(notification: Any) -> dict[str, Any]:
    return NotificationResponse.model_validate(notification).model_dump(mode="json")


def _serialize_list(notifications: list[Any]) -> list[dict[str, Any]]:
    return [_serialize(n) for n in notifications]


_SORT_BY_DESCRIPTION = (
    "Sort field. Options: newest (default) | oldest | priority."
)


# ===========================================================================
# GOVERNMENT ONLY — create notifications / broadcasts
# ===========================================================================


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a notification or broadcast",
    description="""
Create a new notification and deliver it to a specific user or an entire
role group.

### Delivery modes
| `recipient_id` | `recipient_role` | Mode |
|---|---|---|
| Set | null | User-specific (only that user sees it) |
| null | Set | Role broadcast (all users with that role see it) |
| Set | Set | User-specific with role context for audit |

At least one of `recipient_id` or `recipient_role` must be provided.

### Priority levels
`low` | `medium` (default) | `high` | `critical`

Requires: **Government** role.
    """,
)
async def create_notification(
    data: Annotated[
        NotificationCreate,
        Body(
            openapi_examples={
                "broadcast_critical": {
                    "summary": "Critical broadcast to all volunteers",
                    "value": {
                        "title": "Immediate Evacuation Required — Zone 4",
                        "message": (
                            "All units must evacuate Zone 4 immediately. "
                            "Heavy flooding reported on Main Road."
                        ),
                        "priority": "critical",
                        "recipient_role": "volunteer",
                    },
                },
                "user_specific": {
                    "summary": "Direct message to a specific user",
                    "value": {
                        "title": "Your assignment has been updated",
                        "message": "You have been reassigned to Shelter Block B.",
                        "priority": "high",
                        "recipient_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    },
                },
                "ngo_broadcast": {
                    "summary": "Resource update to all NGOs",
                    "value": {
                        "title": "Water Supply Replenished at Depot 3",
                        "message": "5000 litres of water now available at Depot 3, Velachery.",
                        "priority": "medium",
                        "recipient_role": "ngo",
                    },
                },
            }
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    notification = notification_service.create_notification(db=db, data=data)
    return success_response(
        data=_serialize(notification),
        message="Notification created and dispatched successfully.",
        status_code=status.HTTP_201_CREATED,
    )


# ===========================================================================
# ALL AUTHENTICATED USERS — inbox operations
# ===========================================================================


@router.get(
    "/",
    summary="List notifications for the current user",
    description="""
Retrieve a paginated, filtered list of notifications visible to the authenticated user.

### Visibility scope
- **Government**: sees all notifications on the platform.
- **Other roles**: sees notifications addressed directly to them **plus**
  all role-based broadcasts targeting their role.

### Filters
- **priority**: `low` | `medium` | `high` | `critical`
- **is_read**: `true` (read) | `false` (unread)
- **search**: Keyword across notification title and message body

### Sorting
- **sort_by**: `newest` (default) | `oldest` | `priority`

Requires: Any authenticated role.
    """,
)
async def list_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
    priority: Optional[NotificationPriority] = Query(
        None, description="Filter by urgency: low | medium | high | critical."
    ),
    is_read: Optional[bool] = Query(
        None, description="Filter by read status: false = unread only, true = read only."
    ),
    search: Optional[str] = Query(
        None, description="Keyword search across title and message."
    ),
    sort_by: str = Query("newest", description=_SORT_BY_DESCRIPTION),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Results per page (max {MAX_PAGE_SIZE}).",
    ),
) -> Any:
    notifications, total = notification_service.list_notifications(
        db=db,
        current_user=current_user,
        priority=priority,
        is_read=is_read,
        search=search,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return paginated_response(
        data=_serialize_list(notifications),
        total=total,
        page=page,
        page_size=page_size,
        message=f"Retrieved {len(notifications)} of {total} notification(s).",
    )


@router.get(
    "/{notification_id}",
    summary="Get a notification by ID",
    description="""
Retrieve a specific notification by UUID.

Visibility is enforced — users can only access notifications addressed
to them or broadcast to their role. **HTTP 403** is returned otherwise.

Requires: Any authenticated role.
    """,
)
async def get_notification(
    notification_id: Annotated[
        UUID, Path(description="UUID of the notification to retrieve.")
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> Any:
    notification = notification_service.get_notification_by_id(
        db=db, notification_id=notification_id, current_user=current_user
    )
    return success_response(
        data=_serialize(notification),
        message="Notification retrieved successfully.",
    )


@router.patch(
    "/{notification_id}/read",
    summary="Mark a notification as read",
    description="""
Set `is_read = true` on the specified notification.

- Idempotent — calling on an already-read notification returns the
  current state without error.
- Visibility enforced — users cannot mark notifications they shouldn't see.

Requires: Any authenticated role.
    """,
)
async def mark_notification_read(
    notification_id: Annotated[
        UUID, Path(description="UUID of the notification to mark as read.")
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> Any:
    notification = notification_service.mark_as_read(
        db=db, notification_id=notification_id, current_user=current_user
    )
    return success_response(
        data=_serialize(notification),
        message="Notification marked as read.",
    )


@router.delete(
    "/{notification_id}",
    summary="Delete a notification",
    description="""
Soft-delete a notification (`is_deleted = true`).

### Permission rules
- **Government**: can delete any notification.
- **Other users**: can only delete notifications addressed **directly to them**
  (`recipient_id` = their UUID). Broadcast notifications cannot be deleted
  by non-government users.

Requires: Any authenticated role (with ownership constraint for non-Government).
    """,
)
async def delete_notification(
    notification_id: Annotated[
        UUID, Path(description="UUID of the notification to delete.")
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
) -> Any:
    notification_service.delete_notification(
        db=db, notification_id=notification_id, current_user=current_user
    )
    return success_response(message="Notification deleted successfully.")
