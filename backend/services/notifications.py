"""Notification mails triggered by actions in the backend."""
from datetime import datetime
from typing import List, Optional

from database import SessionLocal
from models import User, NotificationLog
from services.email_service import send_mail, html_wrapper


def get_admin_emails(db) -> List[str]:
    admins = db.query(User).filter(User.role == "admin", User.is_active == True).all()
    return [a.email for a in admins if a.email]


def _record(notification_type: str, reference: str, recipients: List[str]):
    """Store what was sent. Failures here must never break the caller."""
    db = SessionLocal()
    try:
        db.add(NotificationLog(
            notification_type=notification_type,
            reference=reference,
            recipients=recipients,
        ))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[MAIL] Could not record notification {notification_type}/{reference}: {e}")
    finally:
        db.close()


def _fmt(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")


def notify_admins_pending_confirmation(
    recipients: List[str],
    plan_id: int,
    assignee_name: str,
    start_date: datetime,
    end_date: datetime,
    created_by: Optional[str],
):
    """Tell the admins that a new entry is waiting for confirmation.

    Called as a FastAPI BackgroundTask, so it takes plain values instead of
    ORM objects - the request session is already closed at that point.
    """
    if not recipients:
        print("[MAIL] No active admins with an email address, skipping confirmation notice.")
        return

    period = f"{_fmt(start_date)} - {_fmt(end_date)}"
    subject = f"Notfallservice: Eintrag von {assignee_name} bestätigen ({start_date.strftime('%d.%m.%Y')})"

    text = (
        "Ein neuer Eintrag im Notfallservice-Plan wartet auf Bestätigung.\n\n"
        f"Mitarbeiter: {assignee_name}\n"
        f"Zeitraum:    {period}\n"
        f"Eingetragen von: {created_by or 'unbekannt'}\n\n"
        "Bitte im Notfallservice Manager prüfen und bestätigen."
    )
    html = html_wrapper(
        "Eintrag wartet auf Bestätigung",
        [
            "Ein neuer Eintrag im Notfallservice-Plan wartet auf Bestätigung.",
            f"<strong>Mitarbeiter:</strong> {assignee_name}<br>"
            f"<strong>Zeitraum:</strong> {period}<br>"
            f"<strong>Eingetragen von:</strong> {created_by or 'unbekannt'}",
        ],
        link_path="/calendar",
    )

    if send_mail(recipients, subject, text, html):
        _record("plan_needs_confirmation", f"plan:{plan_id}", recipients)
