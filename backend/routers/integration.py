from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import get_db
from models import NotfallPlan, User
from datetime import datetime
import os

router = APIRouter(prefix="/integration", tags=["integration"])

# Secure this endpoint with a simple API Key if needed
CX_API_KEY = os.getenv("CX_API_KEY", "secret-cx-key")

@router.get("/routing")
def get_routing_destination(
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """
    Returns the target number for the current time.
    Used by 3CX CFD (Call Flow Designer).
    """
    # Simple security check
    if api_key != CX_API_KEY:
        # For now, we might want to allow open access if inside simple private network, 
        # but let's encourage using a key.
        # pass 
        raise HTTPException(status_code=401, detail="Invalid API Key")

    now = datetime.now()
    
    # Logic:
    # 1. Check for confirmed, active plan
    current_plan = db.query(NotfallPlan).filter(
        and_(
            NotfallPlan.start_date <= now,
            NotfallPlan.end_date >= now,
            NotfallPlan.confirmed == True
        )
    ).first()

    response = {
        "status": "fallback",
        "destination_number": "", # Central/Fallback
        "source": "default",
        "display_name": "Fallback"
    }

    if current_plan:
        user = db.query(User).filter(User.id == current_plan.user_id).first()
        if user and user.phone_number:
            response["status"] = "active_plan"
            response["destination_number"] = user.phone_number
            response["source"] = "plan"
            response["display_name"] = f"{user.first_name} {user.last_name}"
    
    return response
