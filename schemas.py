from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime


class UserResponse(BaseModel):
    id: int
    userid: str
    email: EmailStr
    wallet_balance: float
    created_at: datetime

class TopupRequest(BaseModel):
    amount: float

    
class SMSRequest(BaseModel):
    message: str
    recipient: List[str]
    
    @validator('recipient')
    def validate_phone_numbers(cls, v):
        for phone in v:
            if not phone.startswith('+'):
                raise ValueError('Phone numbers must start with +')
            if not phone[1:].isdigit():
                raise ValueError('Phone numbers must contain only digits after +')
            if not (10 <= len(phone) <= 15):
                raise ValueError('Phone numbers must be between 10 and 15 characters')
        return v

class SMSTemplate(BaseModel):
    id:int
    name: Optional[str] = None
    content: str

class SMSResponse(BaseModel):
    id: int
    recipient: str
    message: str
    status: str
    cost: float
    created_at: datetime



class APIKeyResponse(BaseModel):
    id: int
    key: str
    is_active: bool

    class Config:
        from_attributes = True