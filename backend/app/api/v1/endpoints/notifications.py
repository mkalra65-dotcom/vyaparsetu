from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.models.notification import Notification
from app.schemas.notification import NotificationRead

router = APIRouter()


@router.get("/my", response_model=list[NotificationRead])
def list_my_notifications(db: DbSession, current_user: CurrentUser) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    notification.is_read = True
    notification.read_at = datetime.now(UTC)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
