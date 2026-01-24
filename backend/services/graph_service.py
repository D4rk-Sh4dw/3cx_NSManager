import os
import requests
import uuid
from datetime import datetime
from azure.identity import ClientSecretCredential

# Environment Variables
TENANT_ID = os.getenv("MS_TENANT_ID")
CLIENT_ID = os.getenv("MS_CLIENT_ID")
CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
TARGET_FILE_EMAIL = os.getenv("MS_CALENDAR_EMAIL") # The email of the shared mailbox/calendar

def get_access_token():
    print(f"[GRAPH DEBUG] Checking credentials... Tenant: {TENANT_ID}, ClientID: {CLIENT_ID}")
    
    if not (TENANT_ID and CLIENT_ID and CLIENT_SECRET):
        print("[GRAPH DEBUG] MS Graph Credentials missing in environment variables.")
        return None
    
    try:
        print("[GRAPH DEBUG] Attempting to acquire token via ClientSecretCredential...")
        credential = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
        # Request a token for Graph API
        token = credential.get_token("https://graph.microsoft.com/.default")
        print("[GRAPH DEBUG] Token acquired successfully.")
        return token.token
    except Exception as e:
        print(f"[GRAPH DEBUG] Error getting access token: {e}")
        return None

def create_event(subject: str, start: datetime, end: datetime, attendee_email: str = None, attendee_name: str = None):
    token = get_access_token()
    if not token:
        return f"MOCK_EVENT_ID_{start.timestamp()}_{uuid.uuid4()}"

    # Format dates to ISO
    start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%S")

    event_body = {
        "subject": subject,
        "start": {
            "dateTime": start_str,
            "timeZone": "Europe/Berlin"
        },
        "end": {
            "dateTime": end_str,
            "timeZone": "Europe/Berlin"
        },
        "isOnlineMeeting": False,
    }

    if attendee_email:
        event_body["attendees"] = [
            {
                "emailAddress": {
                    "address": attendee_email,
                    "name": attendee_name or "Notfall Contact"
                },
                "type": "required"
            }
        ]

    # Construct URL
    base_url = "https://graph.microsoft.com/v1.0"
    endpoint = f"/users/{TARGET_FILE_EMAIL}/calendar/events" if TARGET_FILE_EMAIL else "/me/calendar/events"
    url = base_url + endpoint
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=event_body, headers=headers)
        if response.status_code == 201:
            return response.json().get("id")
        else:
            print(f"Error creating event: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception creating event: {e}")
        return None

def delete_event(event_id: str):
    token = get_access_token()
    if not token:
        print(f"Mock deleting event {event_id}")
        return True

    base_url = "https://graph.microsoft.com/v1.0"
    endpoint = f"/users/{TARGET_FILE_EMAIL}/calendar/events/{event_id}" if TARGET_FILE_EMAIL else f"/me/calendar/events/{event_id}"
    url = base_url + endpoint

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            return True
        else:
            print(f"Error deleting event: {response.text}")
            return False
    except Exception as e:
        print(f"Error deleting event: {e}")
        return False
