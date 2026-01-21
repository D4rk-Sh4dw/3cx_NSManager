from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import AuditLog
from pydantic import BaseModel
from datetime import datetime
from routers.auth import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])

class AuditLogSchema(BaseModel):
    id: int
    user_id: int | None
    username: str | None
    action: str
    target_table: str
    target_id: int | None
    timestamp: datetime
    # old_value: dict | None
    # new_value: dict | None # simplifying output for now

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AuditLogSchema])
def read_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): #, current_user = Depends(get_current_user)):
    # Temporarily removed auth depend for easier testing if needed, but for prod uncomment
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs
