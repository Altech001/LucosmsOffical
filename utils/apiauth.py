from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from database import get_db
from models import APIKeys, Users

api_key_header = APIKeyHeader(name="X-API-Key")

async def get_api_user(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
) -> Users:
    api_key_db = db.query(APIKeys).filter(
        APIKeys.key == api_key,
        APIKeys.is_active == True
    ).first()
    
    if not api_key_db:
        raise HTTPException(
            status_code=401,
            detail="Invalid or Inactive API Key"
        )
    
    user = db.query(Users).filter(Users.id == api_key_db.user_id).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User Not Found"
        )
    
    return user