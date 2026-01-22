import time
import requests
import os
import pytz
from datetime import datetime
from database import SessionLocal
from models import NotfallPlan, User
from sqlalchemy import and_

# Configuration
CHECK_INTERVAL = 60 # Check every 60 seconds
TIMEZONE = pytz.timezone("Europe/Berlin")

# 3CX Configuration
CX_TENANT_URL = os.getenv("CX_TENANT_URL", "https://my-3cx.3cx.eu") # Base URL without /xapi/v1
CX_CLIENT_ID = os.getenv("CX_CLIENT_ID", "")
CX_CLIENT_SECRET = os.getenv("CX_CLIENT_SECRET", "")
CX_DUMMY_EXT = os.getenv("CX_DUMMY_EXT", "999") # The Dummy Extension to update
CENTRAL_NUMBER = os.getenv("CENTRAL_NUMBER", "200") # Fallback to Central if no one on duty

# Cache for 3CX User ID
_cx_user_id = None
_last_token = None
_token_expiry = 0

def get_3cx_token():
    """Authenticates using Client Credentials Flow to get a Bearer Token"""
    global _last_token, _token_expiry
    
    if _last_token and time.time() < _token_expiry - 60:
        return _last_token

    print(f"[3CX] Authenticating against {CX_TENANT_URL}...")
    token_url = f"{CX_TENANT_URL}/connect/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": CX_CLIENT_ID,
        "client_secret": CX_CLIENT_SECRET,
        "scope": "offline_access" # Basic scope
    }
    
    try:
        resp = requests.post(token_url, data=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        _last_token = data["access_token"]
        _token_expiry = time.time() + data.get("expires_in", 3600)
        print("[3CX] Authenticated successfully.")
        return _last_token
    except Exception as e:
        print(f"[3CX] Authentication failed: {e}")
        return None

def get_dummy_user_id(token):
    """Finds the System ID of the Dummy User by Extension Number"""
    global _cx_user_id
    if _cx_user_id: 
        return _cx_user_id

    print(f"[3CX] Looking up User ID for Extension {CX_DUMMY_EXT}...")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    # Adjust endpoint based on XAPI documentation: /xapi/v1/Users
    url = f"{CX_TENANT_URL}/xapi/v1/Users?$filter=Number eq '{CX_DUMMY_EXT}'"
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # XAPI returns list in 'value' or standard OData format
        users = data.get("value", [])
        if users:
            _cx_user_id = users[0]["Id"]
            print(f"[3CX] Found User ID: {_cx_user_id}")
            return _cx_user_id
        else:
            print(f"[3CX] User with extension {CX_DUMMY_EXT} not found.")
            return None
    except Exception as e:
        print(f"[3CX] User lookup failed: {e}")
        return None

def update_3cx_mobile(number: str):
    """Updates the Dummy User's Mobile Number via XAPI"""
    token = get_3cx_token()
    if not token: return

    user_id = get_dummy_user_id(token)
    if not user_id: return

    print(f"[3CX] Updating User {CX_DUMMY_EXT} Mobile Number to: {number}")
    headers = {
        "Authorization": f"Bearer {token}", 
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    url = f"{CX_TENANT_URL}/xapi/v1/Users({user_id})"
    
    # Payload structure for XAPI PATCH
    payload = {
        "Mobile": number
    }

    try:
        resp = requests.patch(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        print("[3CX] Successfully updated mobile number.")
    except Exception as e:
        print(f"[3CX] Update failed: {e}")
        if resp.text:
            print(f"[3CX] Response: {resp.text}")

def get_current_active_user(db):
    """Finds the user currently scheduled and confirmed."""
    now = datetime.now(TIMEZONE).replace(tzinfo=None) # Start simple
    
    plan = db.query(NotfallPlan).filter(
        and_(
            NotfallPlan.start_date <= now,
            NotfallPlan.end_date >= now,
            NotfallPlan.confirmed == True
        )
    ).first()
    
    if plan and plan.user:
        return plan.user
    return None

def main():
    print("Starting Scheduler Service (Push Mode)...")
    
    if not CX_CLIENT_ID or not CX_CLIENT_SECRET:
        print("[WARNING] CX_CLIENT_ID or CX_CLIENT_SECRET not set. 3CX Integration disabled.")
    
    last_number = None

    while True:
        try:
            db = SessionLocal()
            target_number = CENTRAL_NUMBER # Default Fallback

            user = get_current_active_user(db)
            if user:
                if user.phone_number:
                    target_number = user.phone_number
                    print(f"[{datetime.now()}] Active Plan: {user.first_name} {user.last_name} ({target_number})")
                else:
                    print(f"[{datetime.now()}] Active Plan: {user.first_name} {user.last_name} HAS NO NUMBER. Using Fallback.")
            else:
                 print(f"[{datetime.now()}] No Active Plan. Using Fallback: {CENTRAL_NUMBER}")

            # Only update if number changed to reduce API calls
            if target_number != last_number:
                if CX_CLIENT_ID:
                    update_3cx_mobile(target_number)
                last_number = target_number
            else:
                pass # No change

            db.close()
            
        except Exception as e:
            print(f"Error in scheduler loop: {e}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
