from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from database import get_db, User
from auth import get_current_user, verify_password, get_password_hash
from logging_service import log_action

router = APIRouter(prefix="/users", tags=["Users"])


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)


class UserResponse(BaseModel):
    id: int
    login: str
    full_name: Optional[str]
    company: Optional[str]
    position: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class AdminUserCreate(BaseModel):
    login: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    is_active: bool = True


class LogResponse(BaseModel):
    id: int
    timestamp: str
    user_id: Optional[int]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    details: Optional[str]
    ip_address: Optional[str]

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(lambda: None)):
    """Get current user's profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(lambda: None),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Update current user's profile."""
    update_data = user_data.model_dump(exclude_unset=True)
    
    if 'password' in update_data and update_data['password']:
        update_data['password_hash'] = get_password_hash(update_data.pop('password'))
    
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    
    # Log the action
    log_action(
        db=db,
        action="PROFILE_UPDATED",
        user_id=current_user.id,
        entity_type="user",
        entity_id=current_user.id,
        details=f"Profile updated for user {current_user.login}",
        ip_address=request.client.host if request.client else None
    )
    
    return current_user


@router.get("/", response_model=List[UserResponse])
async def list_all_users(
    current_user: User = Depends(lambda: None),
    db: Session = Depends(get_db)
):
    """List all users (admin functionality)."""
    users = db.query(User).all()
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: AdminUserCreate,
    current_user: User = Depends(lambda: None),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Create a new user (admin functionality)."""
    existing_user = db.query(User).filter(User.login == user_data.login).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        login=user_data.login,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        company=user_data.company,
        position=user_data.position,
        is_active=user_data.is_active
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log the action
    log_action(
        db=db,
        action="USER_CREATED",
        user_id=current_user.id,
        entity_type="user",
        entity_id=new_user.id,
        details=f"User {new_user.login} created by {current_user.login}",
        ip_address=request.client.host if request.client else None
    )
    
    return new_user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(lambda: None),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Update a user's profile (admin functionality)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = user_data.model_dump(exclude_unset=True)
    
    if 'password' in update_data and update_data['password']:
        update_data['password_hash'] = get_password_hash(update_data.pop('password'))
    
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    
    # Log the action
    log_action(
        db=db,
        action="USER_UPDATED",
        user_id=current_user.id,
        entity_type="user",
        entity_id=user_id,
        details=f"User {user.login} updated by {current_user.login}",
        ip_address=request.client.host if request.client else None
    )
    
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(lambda: None),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Delete a user (admin functionality)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_login = user.login
    db.delete(user)
    db.commit()
    
    # Log the action
    log_action(
        db=db,
        action="USER_DELETED",
        user_id=current_user.id,
        entity_type="user",
        entity_id=user_id,
        details=f"User {user_login} deleted by {current_user.login}",
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": "User deleted successfully"}


@router.get("/logs", response_model=List[LogResponse])
async def get_logs(
    current_user: User = Depends(lambda: None),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0
):
    """Get system logs (admin functionality)."""
    from database import Log
    
    logs = db.query(Log).order_by(Log.timestamp.desc()).offset(offset).limit(limit).all()
    return logs
