from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from database import get_db
from models import NotfallPlan, AuditLog, CalendarEvent
import models
from schemas import Plan as PlanSchema, PlanCreate, PlanUpdate
from routers.auth import get_current_user
from services.msgraph import create_event, delete_event
import json

router = APIRouter(prefix="/plans", tags=["plans"])

@router.get("/", response_model=List[PlanSchema])
def read_plans(start: str = None, end: str = None, db: Session = Depends(get_db)):
    # Simple date filter
    query = db.query(NotfallPlan)
    if start:
        query = query.filter(NotfallPlan.end_date >= start) # Overlaps start
    if end:
        query = query.filter(NotfallPlan.start_date <= end) # Overlaps end
    return query.all()

@router.post("/", response_model=PlanSchema)
def create_plan(plan: PlanCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Validation: Overlap check
    # Check if any CONFIRMED plan overlaps. Unconfirmed plans might overlap?
    # User requirement: "Nur eine Person pro Zeitraum eintragbar".
    # Assuming strict non-overlap for valid plans.
    overlap = db.query(NotfallPlan).filter(
        and_(
            NotfallPlan.start_date < plan.end_date,
            NotfallPlan.end_date > plan.start_date
        )
    ).first()
    
    if overlap:
        raise HTTPException(status_code=400, detail="Time slot already occupied")

    db_plan = NotfallPlan(**plan.dict(), created_by=current_user.username)
    db.add(db_plan)
    
    # Audit Log
    log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        target_table="notfallplan",
        new_value=json.loads(db_plan.json()) if hasattr(db_plan, 'json') else str(plan.dict()) 
    )
    db.add(log)
    
    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.put("/{plan_id}", response_model=PlanSchema)
def update_plan(plan_id: int, plan_update: PlanUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_plan = db.query(NotfallPlan).filter(NotfallPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Check if confirmed -> Delete old event
    if db_plan.confirmed:
        # Fetch associated event
        cal_event = db.query(models.CalendarEvent).filter(models.CalendarEvent.notfallplan_id == db_plan.id).first()
        if cal_event:
            delete_event(cal_event.ms_event_id)
            db.delete(cal_event)
            # We don't recreate immediately, we wait for confirm? 
            # Or if it remains confirmed, we recreate?
            # Requirement: "Änderungen... neue Termine erzeugen"
            # If we unconfirm it? No, `confirmed` might still be true in update?
            # Let's assume if we update, we need to Re-Confirm or Auto-Update.
            # If input confirmed=True or stays True, we should recreate.
    
    # Update fields
    for key, value in plan_update.dict(exclude_unset=True).items():
        setattr(db_plan, key, value)
    
    # If it is still confirmed (or newly confirmed), create new event?
    # For now, let's keep it simple: If you change it, it stays confirmed but we need to re-sync.
    # Logic: Delete Old -> Create New
    
    if db_plan.confirmed:
        start = db_plan.start_date
        end = db_plan.end_date
        person = db.query(models.Person).filter(models.Person.id == db_plan.person_id).first()
        if person:
            subject = f"{person.first_name}: IT-Notfallservice"
            # We don't have person email in DB model "Person", so we pass None or assume external logic.
            # We only have external_number.
            # Assuming we just create the event on the public calendar.
            new_id = create_event(subject, start, end)
            if new_id:
                new_cal_event = models.CalendarEvent(notfallplan_id=db_plan.id, ms_event_id=new_id)
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

@router.post("/{plan_id}/confirm")
def confirm_plan(plan_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_plan = db.query(NotfallPlan).filter(NotfallPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    if db_plan.confirmed:
        return {"status": "already_confirmed"}

    db_plan.confirmed = True
    
    # Create MS Graph Event
    person = db.query(models.Person).filter(models.Person.id == db_plan.person_id).first()
    if person:
        subject = f"{person.first_name}: IT-Notfallservice"
        event_id = create_event(subject, db_plan.start_date, db_plan.end_date)
        
        if event_id:
            cal_event = models.CalendarEvent(notfallplan_id=db_plan.id, ms_event_id=event_id)
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
