from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)  # For call routing
    role = Column(String, default="planner")  # admin, planner, buchhaltung
    is_active = Column(Boolean, default=True)
    can_take_duty = Column(Boolean, default=True)  # Eligible for emergency service
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationship to plans (user can be assigned to emergency duty)
    plans = relationship("NotfallPlan", back_populates="user")


class NotfallPlan(Base):
    __tablename__ = "notfallplan"

    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(DateTime, nullable=False)  # Start of shift
    end_date = Column(DateTime, nullable=False)  # End of shift
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Changed from person_id
    confirmed = Column(Boolean, default=False)
    created_by = Column(String, nullable=True)  # Username or ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="plans")  # Changed from person
    calendar_events = relationship("CalendarEvent", back_populates="plan", cascade="all, delete-orphan")

class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    notfallplan_id = Column(Integer, ForeignKey("notfallplan.id"), nullable=False)
    ms_event_id = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    plan = relationship("NotfallPlan", back_populates="calendar_events")

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True) # If user deleted, keep log? Or Set Null.
    username = Column(String, nullable=True) # Capture username at time of action
    action = Column(String, nullable=False) # CREATE, UPDATE, DELETE, CONFIRM
    target_table = Column(String, nullable=False) # persons, notfallplan, etc.
    target_id = Column(Integer, nullable=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
