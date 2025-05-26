from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from uuid import uuid4


class SMSMessageBase(BaseModel):
    message: str = Field(..., min_length=1, max_length=160)
    recipients: List[str] = Field(..., min_items=1)

    @validator('recipients')
    def validate_phone_numbers(cls, v):
        for phone in v:
            if not phone.startswith('+'):
                raise ValueError('Phone numbers must start with +')
            if not phone[1:].isdigit():
                raise ValueError('Phone numbers must contain only digits after +')
            if not (10 <= len(phone) <= 15):
                raise ValueError('Phone numbers must be between 10 and 15 characters')
        return v

class SMSMessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=160)
    recipients: List[str] = Field(..., min_items=1)

    @validator('recipients')
    def validate_phone_numbers(cls, v):
        for phone in v:
            if not phone.startswith('+'):
                raise ValueError('Phone numbers must start with +')
            if not phone[1:].isdigit():
                raise ValueError('Phone numbers must contain only digits after +')
            if not (10 <= len(phone) <= 15):
                raise ValueError('Phone numbers must be between 10 and 15 characters')
        return v

class SMSMessageResponse(SMSMessageBase):
    id: int
    user_id: int
    status: str
    cost: float
    created_at: datetime

    class Config:
        from_attributes = True

class SMSDeliveryReport(BaseModel):
    # sms_id: str = Field(default_factory=lambda: str(uuid4()))
    sms_id : int
    status: str
    updated_at: datetime

    class Config:
        from_attributes = True

class SMSTemplate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1, max_length=160)
    user_id: Optional[int] = None

    class Config:
        from_attributes = True
        
        
        