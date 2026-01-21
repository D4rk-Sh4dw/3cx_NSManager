import os
import requests
from datetime import datetime
from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient

# Environment Variables
TENANT_ID = os.getenv("MS_TENANT_ID")
CLIENT_ID = os.getenv("MS_CLIENT_ID")
CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
TARGET_FILE_EMAIL = os.getenv("MS_CALENDAR_EMAIL") # The email of the shared mailbox/calendar

def get_graph_client():
    if not (TENANT_ID and CLIENT_ID and CLIENT_SECRET):
        print("MS Graph Credentials missing")
        return None
    
    credential = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    return GraphClient(credential=credential)

def create_event(subject: str, start: datetime, end: datetime, attendee_email: str = None, attendee_name: str = None):
    client = get_graph_client()
    if not client:
        return "MOCK_EVENT_ID_" + str(start.timestamp())

    # Format dates to ISO
    # MS Graph expects: "2023-01-01T12:00:00"
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

    # Post to specific user/calendar or default
    url = f"/users/{TARGET_FILE_EMAIL}/calendar/events" if TARGET_FILE_EMAIL else "/me/calendar/events"
    
    try:
        result = client.post(url, json=event_body)
        if result.status_code == 201:
            return result.json().get("id")
        else:
            print(f"Error creating event: {result.text}")
            return None
    except Exception as e:
        print(f"Exception creating event: {e}")
        return None

def delete_event(event_id: str):
    client = get_graph_client()
    if not client:
        print(f"Mock deleting event {event_id}")
        return True

    url = f"/users/{TARGET_FILE_EMAIL}/calendar/events/{event_id}" if TARGET_FILE_EMAIL else f"/me/calendar/events/{event_id}"
    
    try:
        client.delete(url)
        return True
    except Exception as e:
        print(f"Error deleting event: {e}")
        return False
