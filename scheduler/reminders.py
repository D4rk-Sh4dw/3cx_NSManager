"""Weekly reminder: nag everyone if nobody signed up for the coming week."""
import os
from datetime import datetime, timedelta
from typing import List, Tuple

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from models import NotfallPlan, User, NotificationLog
from email_service import send_mail, html_wrapper

NOTIFICATION_TYPE = "weekly_reminder"

REMINDER_ENABLED = os.getenv("REMINDER_ENABLED", "true").lower() in ("1", "true", "yes")
# 0 = Monday ... 6 = Sunday. Default: Thursday, 09:00 - leaves a few days to react.
REMINDER_WEEKDAY = int(os.getenv("REMINDER_WEEKDAY", "3"))
REMINDER_HOUR = int(os.getenv("REMINDER_HOUR", "9"))


def next_week_bounds(now: datetime) -> Tuple[datetime, datetime]:
    """Monday 00:00 of the coming week until the Monday after (exclusive)."""
    monday_this_week = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start = monday_this_week + timedelta(days=7)
    return start, start + timedelta(days=7)


def week_reference(start: datetime) -> str:
    iso_year, iso_week, _ = start.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def get_duty_eligible_emails(db) -> List[str]:
    """Same rule as the /users/duty-eligible endpoint in the backend."""
    users = db.query(User).filter(
        User.is_active == True,
        (User.can_take_duty == True) | (User.role == "planner")
    ).all()
    return [u.email for u in users if u.email]


def week_is_covered(db, start: datetime, end: datetime) -> bool:
    plan = db.query(NotfallPlan).filter(
        and_(
            NotfallPlan.start_date < end,
            NotfallPlan.end_date > start,
        )
    ).first()
    return plan is not None


def already_sent(db, reference: str) -> bool:
    return db.query(NotificationLog).filter(
        NotificationLog.notification_type == NOTIFICATION_TYPE,
        NotificationLog.reference == reference,
    ).first() is not None


def _record(db, reference: str, recipients: List[str]):
    try:
        db.add(NotificationLog(
            notification_type=NOTIFICATION_TYPE,
            reference=reference,
            recipients=recipients,
        ))
        db.commit()
    except IntegrityError:
        # Another run got there first - nothing to do.
        db.rollback()
    except Exception as e:
        db.rollback()
        print(f"[REMINDER] Could not record notification for {reference}: {e}")


def send_weekly_reminder(db, now: datetime, force: bool = False) -> bool:
    """Send the reminder if the coming week has no entry yet. Returns True if sent."""
    start, end = next_week_bounds(now)
    reference = week_reference(start)

    if not force and already_sent(db, reference):
        return False

    if week_is_covered(db, start, end):
        print(f"[REMINDER] Week {reference} is already covered, no reminder needed.")
        return False

    recipients = get_duty_eligible_emails(db)
    if not recipients:
        print("[REMINDER] No duty-eligible users with an email address.")
        return False

    period = f"{start.strftime('%d.%m.%Y')} - {(end - timedelta(days=1)).strftime('%d.%m.%Y')}"
    subject = f"Notfallservice: Für KW {start.isocalendar()[1]} ({period}) ist noch niemand eingetragen"

    text = (
        f"Für die kommende Woche ({period}) hat sich noch niemand für den "
        "Notfallservice eingetragen.\n\n"
        "Bitte im Notfallservice Manager eintragen, damit die Rufumleitung "
        "korrekt gesetzt werden kann."
    )
    html = html_wrapper(
        f"Notfallservice KW {start.isocalendar()[1]} ist unbesetzt",
        [
            f"Für die kommende Woche (<strong>{period}</strong>) hat sich noch niemand "
            "für den Notfallservice eingetragen.",
            "Bitte im Notfallservice Manager eintragen, damit die Rufumleitung korrekt "
            "gesetzt werden kann.",
        ],
        link_path="/calendar",
    )

    if send_mail(recipients, subject, text, html):
        _record(db, reference, recipients)
        return True
    return False


def maybe_send_weekly_reminder(db, now: datetime):
    """Called from the scheduler loop. Fires on the configured weekday/hour only."""
    if not REMINDER_ENABLED:
        return
    if now.weekday() != REMINDER_WEEKDAY:
        return
    # >= so a restart later on the same day still sends the reminder.
    if now.hour < REMINDER_HOUR:
        return
    send_weekly_reminder(db, now)
