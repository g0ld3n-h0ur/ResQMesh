"""
app/api/v1/notifications.py

Notifications router — framework skeleton.

Manages push notifications, SMS alerts, and in-app alert broadcasting
to citizens, volunteers, and partner organisations during disaster events.

Prefix  : /api/v1/notifications
Tags    : Notifications
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_NOTIFICATIONS

router = APIRouter(
    prefix="/notifications",
    tags=[API_V1_TAG_NOTIFICATIONS],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to future phase
# ---------------------------------------------------------------------------
# GET  /notifications/                  → List notifications for the current user
# POST /notifications/broadcast         → Broadcast an alert to a target group
# POST /notifications/sos-alert        → Send an emergency SOS broadcast
# GET  /notifications/{notification_id} → Retrieve a specific notification
# PUT  /notifications/{notification_id}/read → Mark a notification as read
# DELETE /notifications/{notification_id}   → Delete a notification record
