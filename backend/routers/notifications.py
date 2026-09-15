from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User, NotificationLog
from routers.users import require_admin
from services.email_service import send_mail, html_wrapper, transport_name, is_configured
from services.notifications import get_admin_emails

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/status")
def notification_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Show which mail transport is active and what was sent recently (admin only)."""
    recent = (
        db.query(NotificationLog)
        .order_by(NotificationLog.sent_at.desc())
        .limit(20)
        .all()
    )
    return {
        "transport": transport_name(),
        "configured": is_configured(),
        "admin_recipients": get_admin_emails(db),
        "recent": [
            {
                "type": n.notification_type,
                "reference": n.reference,
                "recipients": n.recipients,
                "sent_at": n.sent_at,
            }
            for n in recent
        ],
    }


@router.post("/test")
def send_test_mail(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Send a test mail to the calling admin to verify the mail configuration."""
    if not current_user.email:
        raise HTTPException(status_code=400, detail="Your account has no email address")

    text = (
        "Dies ist eine Testnachricht des Notfallservice Managers.\n\n"
        f"Versandweg: {transport_name()}"
    )
    html = html_wrapper(
        "Testnachricht",
        [
            "Dies ist eine Testnachricht des Notfallservice Managers.",
            f"Versandweg: <strong>{transport_name()}</strong>",
        ],
    )

    ok = send_mail([current_user.email], "Notfallservice Manager: Testnachricht", text, html)
    if not ok:
        raise HTTPException(
            status_code=500,
            detail=f"Mail could not be sent (transport: {transport_name()}). Check the backend logs.",
        )
    return {"status": "sent", "to": current_user.email, "transport": transport_name()}
