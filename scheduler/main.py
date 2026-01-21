import time
import requests
import os
import pytz
from datetime import datetime, time as dtime
from database import SessionLocal
from models import NotfallPlan, Person
from sqlalchemy import and_

# Configuration
CHECK_INTERVAL = 60 # Check every 60 seconds
BUSINESS_START = dtime(8, 0)
BUSINESS_END = dtime(17, 0)
TIMEZONE = pytz.timezone("Europe/Berlin")

# 3CX Configuration (Dummy / Stub for now)
# In production, these should be env vars
CX_API_BASE = os.getenv("CX_API_BASE", "https://3cx.example.com/api")
CX_API_KEY = os.getenv("CX_API_KEY", "dummy_key")
CX_FORWARDING_DN = os.getenv("CX_FORWARDING_DN", "1000") # The Mock Extension or DID rule ID to update
CENTRAL_NUMBER = "200" # Internal number for Zentrale

def update_3cx_forwarding(number: str):
    """
    Updates the 3CX forwarding rule to the specified number.
    This is a stub implementation.
    """
    print(f"[3CX] Updating forwarding for DN {CX_FORWARDING_DN} to {number}")
    # In a real implementation:
    # 1. Authenticate / Login to 3CX API (if needed)
    # 2. PUT /api/ActiveCalls or /api/Extension/{id}/ForwardingRules
    # payload = {"ForwardTo": number}
    # requests.put(f"{CX_API_BASE}/...", json=payload, headers=...)
    pass

def get_current_active_person(db):
    """
    Finds the person currently scheduled and confirmed.
    """
    now = datetime.now(TIMEZONE).replace(tzinfo=None) # Start simple, assuming DB dates are naive or aligned
    # Depending on how we store dates in DB. If naive, we might need care.
    # For now, let's assume DB stores robust UTC or local.
    
    # We query for a plan that covers NOW and is confirmed
    plan = db.query(NotfallPlan).filter(
        and_(
            NotfallPlan.start_date <= now,
            NotfallPlan.end_date >= now,
            NotfallPlan.confirmed == True
        )
    ).first()
    
    if plan and plan.person:
        return plan.person
    return None

def main():
    print("Starting Scheduler Service...")
    while True:
        try:
            now = datetime.now(TIMEZONE)
            current_time = now.time()
            is_business_hours = BUSINESS_START <= current_time <= BUSINESS_END
            # Weekend check? 
            # if now.weekday() >= 5: is_business_hours = False

            db = SessionLocal()
            target_number = None

            if is_business_hours:
                print(f"[{now}] Business Hours. Forwarding to Zentrale.")
                target_number = CENTRAL_NUMBER
            else:
                person = get_current_active_person(db)
                if person:
                    print(f"[{now}] Off Hours. Active Person: {person.first_name} {person.last_name} ({person.external_number})")
                    target_number = person.external_number
                else:
                    print(f"[{now}] Off Hours. NO ACTIVE PERSON! Fallback?")
                    # Fallback to Zentrale or specific emergency fallback?
                    target_number = CENTRAL_NUMBER # Fallback

            if target_number:
                update_3cx_forwarding(target_number)

            db.close()
            
        except Exception as e:
            print(f"Error in scheduler loop: {e}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
