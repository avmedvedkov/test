from datetime import datetime
from sqlalchemy.orm import Session
from database import Log


def log_action(
    db: Session,
    action: str,
    user_id: int = None,
    entity_type: str = None,
    entity_id: int = None,
    details: str = None,
    ip_address: str = None
):
    """Log an action to the database."""
    log_entry = Log(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
        timestamp=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()
    return log_entry
