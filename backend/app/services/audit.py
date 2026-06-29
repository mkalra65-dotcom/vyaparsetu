from sqlalchemy.orm import Session

from app.models.audit_log import ApplicationAuditLog


def add_application_audit_log(
    db: Session,
    *,
    application_id: int,
    actor_user_id: int,
    action: str,
    old_status: str | None = None,
    new_status: str | None = None,
    note: str | None = None,
) -> ApplicationAuditLog:
    audit_log = ApplicationAuditLog(
        application_id=application_id,
        actor_user_id=actor_user_id,
        action=action,
        old_status=old_status,
        new_status=new_status,
        note=note,
    )
    db.add(audit_log)
    return audit_log
