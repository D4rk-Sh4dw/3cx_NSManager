from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User, AuditLog
from schemas import User as UserSchema, UserCreate, UserUpdate, UserSimple
from routers.auth import get_current_user, get_password_hash

router = APIRouter(prefix="/users", tags=["users"])

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker

@router.get("/", response_model=List[UserSchema])
async def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all users (admin only)"""
    return db.query(User).all()

@router.get("/duty-eligible", response_model=List[UserSimple])
async def get_duty_eligible_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get users who can take emergency duty (for plan creation)"""
    return db.query(User).filter(
        User.is_active == True,
        (User.can_take_duty == True) | (User.role == "planner")
    ).all()

@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get single user by ID (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserSchema)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create new user (admin only)"""
    # Check if username or email already exists
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone_number=user_data.phone_number,
        role=user_data.role,
        is_active=user_data.is_active,
        can_take_duty=user_data.can_take_duty
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        target_table="users",
        target_id=new_user.id,
        new_value={"username": new_user.username, "email": new_user.email, "role": new_user.role}
    )
    db.add(audit)
    db.commit()
    
    return new_user

@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_values = {"email": user.email, "role": user.role}
    
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.first_name is not None:
        user.first_name = user_data.first_name
    if user_data.last_name is not None:
        user.last_name = user_data.last_name
    if user_data.phone_number is not None:
        user.phone_number = user_data.phone_number
    if user_data.role is not None:
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.can_take_duty is not None:
        user.can_take_duty = user_data.can_take_duty
    if user_data.password is not None:
        user.password_hash = get_password_hash(user_data.password)
    
    db.commit()
    db.refresh(user)
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        target_table="users",
        target_id=user.id,
        old_value=old_values,
        new_value={"email": user.email, "role": user.role}
    )
    db.add(audit)
    db.commit()
    
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    # Audit log before deletion
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        target_table="users",
        target_id=user.id,
        old_value={"username": user.username, "email": user.email}
    )
    db.add(audit)
    
    db.delete(user)
    db.commit()
    
    return {"status": "deleted"}
