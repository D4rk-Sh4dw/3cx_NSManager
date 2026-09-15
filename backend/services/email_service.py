"""Email delivery for system notifications.

The transport is picked automatically:
1. SMTP, if SMTP_HOST is set
2. Microsoft Graph sendMail, if MS Graph credentials are set
3. Otherwise the mail is only logged (mock mode, like graph_service)
"""
import os
import smtplib
import requests
from email.message import EmailMessage
from html import escape
from typing import List, Optional
from azure.identity import ClientSecretCredential

# SMTP Configuration
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "true").lower() in ("1", "true", "yes")
SMTP_SSL = os.getenv("SMTP_SSL", "false").lower() in ("1", "true", "yes")

# Microsoft Graph Configuration (shared with the calendar integration)
TENANT_ID = os.getenv("MS_TENANT_ID")
CLIENT_ID = os.getenv("MS_CLIENT_ID")
CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")

# Sender: explicit MAIL_FROM, otherwise the shared calendar mailbox
MAIL_FROM = os.getenv("MAIL_FROM") or os.getenv("MS_CALENDAR_EMAIL")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Notfallservice Manager")
MAIL_LOGO_URL = os.getenv("MAIL_LOGO_URL", "").strip()

# Base URL used for links inside the mails
APP_BASE_URL = os.getenv("APP_BASE_URL", "").rstrip("/")


def _graph_available() -> bool:
    return bool(TENANT_ID and CLIENT_ID and CLIENT_SECRET and MAIL_FROM)


def _get_access_token() -> Optional[str]:
    try:
        credential = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
        return credential.get_token("https://graph.microsoft.com/.default").token
    except Exception as e:
        print(f"[MAIL] Error getting Graph access token: {e}")
        return None


def _send_via_smtp(recipients: List[str], subject: str, body_text: str, body_html: Optional[str]) -> bool:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{MAIL_FROM_NAME} <{MAIL_FROM or SMTP_USER}>"
    msg["To"] = ", ".join(recipients)
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    try:
        if SMTP_SSL:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20)
        with server:
            if SMTP_STARTTLS and not SMTP_SSL:
                server.starttls()
            if SMTP_USER:
                server.login(SMTP_USER, SMTP_PASSWORD or "")
            server.send_message(msg)
        print(f"[MAIL] Sent '{subject}' via SMTP to {len(recipients)} recipient(s).")
        return True
    except Exception as e:
        print(f"[MAIL] SMTP send failed: {e}")
        return False


def _send_via_graph(recipients: List[str], subject: str, body_text: str, body_html: Optional[str]) -> bool:
    token = _get_access_token()
    if not token:
        return False

    payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML" if body_html else "Text",
                "content": body_html or body_text,
            },
            "toRecipients": [{"emailAddress": {"address": r}} for r in recipients],
        },
        "saveToSentItems": False,
    }

    url = f"https://graph.microsoft.com/v1.0/users/{MAIL_FROM}/sendMail"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        if response.status_code in (202, 200):
            print(f"[MAIL] Sent '{subject}' via Graph to {len(recipients)} recipient(s).")
            return True
        print(f"[MAIL] Graph send failed: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        print(f"[MAIL] Graph send exception: {e}")
        return False


def send_mail(recipients: List[str], subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
    """Send one mail to all recipients. Returns True if it was handed to a transport."""
    recipients = [r for r in recipients if r]
    if not recipients:
        print(f"[MAIL] No recipients for '{subject}', skipping.")
        return False

    if SMTP_HOST:
        return _send_via_smtp(recipients, subject, body_text, body_html)

    if _graph_available():
        return _send_via_graph(recipients, subject, body_text, body_html)

    print(f"[MAIL] MOCK (no SMTP_HOST and no Graph credentials/MAIL_FROM) "
          f"-> To: {', '.join(recipients)} | Subject: {subject}\n{body_text}")
    return False


def is_configured() -> bool:
    """True if a real transport is available (used by the config check endpoint)."""
    return bool(SMTP_HOST) or _graph_available()


def transport_name() -> str:
    if SMTP_HOST:
        return "smtp"
    if _graph_available():
        return "graph"
    return "mock"


def html_wrapper(title: str, paragraphs: List[str], link_path: str = "") -> str:
    """Small shared HTML skeleton so all notification mails look the same."""
    body = "".join(f"<p style='margin:0 0 12px 0;'>{p}</p>" for p in paragraphs)
    logo = ""
    if MAIL_LOGO_URL:
        logo = (
            f"<img src='{escape(MAIL_LOGO_URL, quote=True)}' alt='{escape(MAIL_FROM_NAME, quote=True)}' "
            "style='display:block;max-width:200px;max-height:72px;width:auto;height:auto;"
            "margin:0 0 20px 0;'/>"
        )
    button = ""
    if APP_BASE_URL:
        url = f"{APP_BASE_URL}{link_path}"
        button = (
            f"<p style='margin:24px 0 0 0;'>"
            f"<a href='{url}' style='background:#1f2937;color:#ffffff;text-decoration:none;"
            f"padding:10px 18px;border-radius:6px;display:inline-block;'>Zum Notfallplan</a></p>"
        )
    return (
        "<div style=\"font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#111827;"
        "line-height:1.5;\">"
        f"{logo}<h2 style='margin:0 0 16px 0;font-size:18px;'>{title}</h2>"
        f"{body}{button}"
        "<p style='margin:24px 0 0 0;color:#6b7280;font-size:12px;'>"
        "Diese Nachricht wurde automatisch vom Notfallservice Manager versendet.</p>"
        "</div>"
    )
