from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from database import get_db
from models import NotfallPlan, AuditLog, CalendarEvent, User
from schemas import Plan as PlanSchema, PlanCreate, PlanUpdate
from routers.auth import get_current_user
from services.graph_service import create_event, delete_event
import json

router = APIRouter(prefix="/plans", tags=["plans"])

def require_planner_or_admin(current_user: User = Depends(get_current_user)):
    """Only admin and planner can modify plans"""
    if current_user.role not in ["admin", "planner"]:
        raise HTTPException(
            status_code=403,
            detail="Admin or planner access required"
        )
    return current_user

@router.get("/", response_model=List[PlanSchema])
def read_plans(
    start: str = None, 
    end: str = None, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # All roles can view
):
    """Get plans (all authenticated users can view)"""
    query = db.query(NotfallPlan)
    if start:
        query = query.filter(NotfallPlan.end_date >= start)
    if end:
        query = query.filter(NotfallPlan.start_date <= end)
    return query.all()

@router.post("/", response_model=PlanSchema)
def create_plan(
    plan: PlanCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_planner_or_admin)
):
    """Create plan (admin: anyone, planner: self only)"""
    
    # 1. Permission Check
    target_user_id = plan.user_id
    if current_user.role == "planner":
        if target_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Planners can only schedule themselves")
    
    # Validation: Overlap check
    overlap = db.query(NotfallPlan).filter(
        and_(
            NotfallPlan.start_date < plan.end_date,
            NotfallPlan.end_date > plan.start_date
        )
    ).first()
    
    if overlap:
        raise HTTPException(status_code=400, detail="Time slot already occupied")

    # Verify user_id exists and can take duty
    assigned_user = db.query(User).filter(User.id == target_user_id).first()
    if not assigned_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not assigned_user.can_take_duty:
        raise HTTPException(status_code=400, detail="User cannot take emergency duty")

    db_plan = NotfallPlan(**plan.dict(), created_by=current_user.username)
    db.add(db_plan)
    
    # Audit Log
    log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        target_table="notfallplan",
        new_value=str(plan.dict())
    )
    db.add(log)
    
    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.put("/{plan_id}", response_model=PlanSchema)
def update_plan(
    plan_id: int, 
    plan_update: PlanUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_planner_or_admin)
):
    """Update plan (admin: all, planner: own only)"""
    db_plan = db.query(NotfallPlan).filter(NotfallPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Permission Check
    if current_user.role == "planner":
        if db_plan.user_id != current_user.id:
             raise HTTPException(status_code=403, detail="Planners can only update their own plans")
        # Planner cannot reassign plan to someone else
        if plan_update.user_id and plan_update.user_id != current_user.id:
             raise HTTPException(status_code=403, detail="Planners cannot reassign plans")
    
    # Check if confirmed -> Delete old event
    if db_plan.confirmed:
        cal_event = db.query(CalendarEvent).filter(CalendarEvent.notfallplan_id == db_plan.id).first()
        if cal_event:
            delete_event(cal_event.ms_event_id)
            db.delete(cal_event)
    
    # Update fields
    for key, value in plan_update.dict(exclude_unset=True).items():
        setattr(db_plan, key, value)
    
    # If it is still confirmed, create new event
    if db_plan.confirmed:
        assigned_user = db.query(User).filter(User.id == db_plan.user_id).first()
        if assigned_user:
            subject = f"{assigned_user.first_name} {assigned_user.last_name}: IT-Notfallservice"
            attendee_email = assigned_user.email
            new_id = create_event(subject, db_plan.start_date, db_plan.end_date, attendee_email)
            if new_id:
                new_cal_event = CalendarEvent(notfallplan_id=db_plan.id, ms_event_id=new_id)
                db.add(new_cal_event)

    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        target_table="notfallplan",
        target_id=db_plan.id,
        new_value=str(plan_update.dict())
    ))

    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_planner_or_admin)
):
    """Delete plan (admin: all, planner: own only)"""
    db_plan = db.query(NotfallPlan).filter(NotfallPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Permission Check
    if current_user.role == "planner":
        if db_plan.user_id != current_user.id:
             raise HTTPException(status_code=403, detail="Planners can only delete their own plans")
        if db_plan.confirmed:
             raise HTTPException(status_code=403, detail="Cannot delete confirmed plans")
    
    # Delete associated calendar event
    cal_event = db.query(CalendarEvent).filter(CalendarEvent.notfallplan_id == db_plan.id).first()
    if cal_event:
        delete_event(cal_event.ms_event_id)
        db.delete(cal_event)
    
    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        target_table="notfallplan",
        target_id=db_plan.id
    ))
    
    db.delete(db_plan)
    db.commit()
    return {"status": "deleted"}

@router.post("/{plan_id}/confirm")
def confirm_plan(
    plan_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_planner_or_admin)
):
    """Confirm plan (admin: all, planner: own only)"""
    db_plan = db.query(NotfallPlan).filter(NotfallPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Permission Check
    if current_user.role == "planner":
        if db_plan.user_id != current_user.id:
             raise HTTPException(status_code=403, detail="Planners can only confirm their own plans")

    if db_plan.confirmed:
        return {"status": "already_confirmed"}

    db_plan.confirmed = True
    
    # Create MS Graph Event with attendee
    assigned_user = db.query(User).filter(User.id == db_plan.user_id).first()
    if assigned_user:
        subject = f"{assigned_user.first_name} {assigned_user.last_name}: IT-Notfallservice"
        attendee_email = assigned_user.email
        event_id = create_event(subject, db_plan.start_date, db_plan.end_date, attendee_email)
        
        if event_id:
            cal_event = CalendarEvent(notfallplan_id=db_plan.id, ms_event_id=event_id)
            db.add(cal_event)

    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="CONFIRM",
        target_table="notfallplan",
        target_id=db_plan.id
    ))

    db.commit()
    return {"status": "confirmed"}
