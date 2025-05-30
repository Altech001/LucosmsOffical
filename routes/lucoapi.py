from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import secrets
import string

from database import get_db
from models import APIKeys, Users
import models
from routes.auth import get_current_user
from rate_limiter.rate_limiter import limiter

router = APIRouter(
    prefix="/api_key",
    tags=["LucoSMS API Keys"]
)

def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key"""
    alphabet = string.ascii_letters + string.digits
    random_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f"Luco_{random_key}"

@router.post("/generate", response_model=dict)
# @limiter.limit("10/minute")
def generate_user_api_key(user_session=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Generate a new API key for a user
    """
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    api_key = generate_api_key()
    
    existing_key = db.query(APIKeys).filter(APIKeys.key == api_key).first()
    if existing_key:
        raise HTTPException(status_code=400, detail="API key generation collision occurred")

    new_api_key = APIKeys(
        user_id=user.id,
        key=api_key,
        is_active=True
    )
    
    db.add(new_api_key)
    db.commit()
    db.refresh(new_api_key)
    
    return {
        "api_key": new_api_key.key,
        "message": "API key generated successfully",
    }

@router.get("/list", response_model=list[dict])
# @limiter.limit("10/minute")
def list_api_keys(user_session=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    List all API keys for a user
    """
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    api_keys = db.query(APIKeys).filter(APIKeys.user_id == user.id).all()
    
    return [{
        "id": key.id,
        "key": key.key[-8:],  # Mask key, show last 8 characters
        "full_key": key.key,  # Include full key for copying (securely handled in frontend)
        "is_active": key.is_active,
    } for key in api_keys]

@router.put("/deactivate/{key_id}", response_model=dict)
# @limiter.limit("10/minute")
def deactivate_api_key(key_id: int, user_session=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Deactivate an existing API key
    """
    api_key = db.query(APIKeys).filter(
        APIKeys.id == key_id,
        APIKeys.user_id == db.query(Users.id).filter(Users.clerk_user_id == user_session.user_id).scalar_subquery()
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found or not owned by user")
    
    if not api_key.is_active:
        raise HTTPException(status_code=400, detail="API key already deactivated")
    
    api_key.is_active = False
    db.commit()
    
    return {"message": "API key deactivated successfully"}

@router.delete("/delete/{key_id}", response_model=dict)
# @limiter.limit("10/minute")
def delete_api_key(key_id: int, user_session=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Delete an existing API key
    """
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    api_key = db.query(APIKeys).filter(
        APIKeys.id == key_id,
        APIKeys.user_id == user.id  # Ensure the key belongs to the user
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found or not owned by user")
    
    db.delete(api_key)
    db.commit()
    
    return {"message": "API key deleted successfully"}