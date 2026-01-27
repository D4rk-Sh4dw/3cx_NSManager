from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
import calendar
from database import get_db
from models import User, NotfallPlan
from routers.auth import get_current_active_user, get_current_user

router = APIRouter(
    prefix="/stats",
    tags=["stats"],
    responses={404: {"description": "Not found"}},
)

def calculate_duration_in_period(plan_start: datetime, plan_end: datetime, period_start: datetime, period_end: datetime) -> int:
    """Calculate overlap in days between plan and period."""
    # Intersection
    start = max(plan_start, period_start)
    end = min(plan_end, period_end)
    
    if start >= end:
        return 0
    
    # Difference + 1? It depends on how we define "days". 
    # If plan is Jan 1 00:00 to Jan 2 00:00, that is 1 day (Jan 1).
    # Diff is 1 day.
    
    delta = end - start
    return max(0, delta.days)

@router.get("/overview", response_model=Dict[str, Any])
def get_stats_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Only Admin and Buchhaltung
    if current_user.role not in ["admin", "buchhaltung"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    now = datetime.now()
    
    # Current Month Scope
    month_start = datetime(now.year, now.month, 1)
    # Last day of month
    _, last_day = calendar.monthrange(now.year, now.month)
    month_end = datetime(now.year, now.month, last_day) + timedelta(days=1) # Start of next month roughly, or just covering full end day.
    # Actually simpler: period_end comparison. 
    # If plan ends at 00:00 of next day, strict inequality works.
    
    # Current Year Scope
    year_start = datetime(now.year, 1, 1)
    year_end = datetime(now.year + 1, 1, 1)
    
    # Helper to Fetch and Aggregate
    def get_aggregated_stats(start_scope: datetime, end_scope: datetime):
        # Fetch confirmed plans intersecting the scope
        plans = db.query(NotfallPlan).filter(
            NotfallPlan.confirmed == True,
            or_(
                and_(NotfallPlan.start_date >= start_scope, NotfallPlan.start_date < end_scope),
                and_(NotfallPlan.end_date > start_scope, NotfallPlan.end_date <= end_scope),
                and_(NotfallPlan.start_date <= start_scope, NotfallPlan.end_date >= end_scope)
            )
        ).all()
        
        user_stats = {}
        
        for plan in plans:
            uid = plan.user_id
            if uid not in user_stats:
                # Pre-fetch user name to avoid N+1 if lazy loading (though eager load preferred)
                u = plan.user
                user_stats[uid] = {
                    "user_id": uid,
                    "first_name": u.first_name if u else "Unknown",
                    "last_name": u.last_name if u else "Unknown",
                    "username": u.username if u else "Unknown",
                    "total_days": 0,
                    "total_entries": 0
                }
            
            days = calculate_duration_in_period(plan.start_date, plan.end_date, start_scope, end_scope)
            user_stats[uid]["total_days"] += days
            user_stats[uid]["total_entries"] += 1
            
        return list(user_stats.values())

    month_stats = get_aggregated_stats(month_start, month_end)
    year_stats = get_aggregated_stats(year_start, year_end)
    
    return {
        "month": {
            "name": now.strftime("%B"),
            "year": now.year,
            "data": month_stats
        },
        "year": {
            "year": now.year,
            "data": year_stats
        }
    }
