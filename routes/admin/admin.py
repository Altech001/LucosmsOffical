from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import secrets
import string
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta

from database import get_db
import models

admin_router = APIRouter(
    prefix="/v1/admin",
    tags=["Admin"]
)

# Pydantic models for request/response validation
class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    wallet_balance: float
    clerk_user_id: str
    created_at: datetime

    class Config:
        orm_mode = True

class TransactionResponse(BaseModel):
    id: int
    user_id: str
    amount: float
    transaction_type: str
    created_at: datetime

    class Config:
        orm_mode = True

class SmsMessageResponse(BaseModel):
    id: int
    user_id: str
    recipient: str
    message: str
    status: str
    cost: float
    created_at: datetime

    class Config:
        from_attributes = True

class SmsDeliveryReportResponse(BaseModel):
    id: int
    sms_id: int
    status: str
    updated_at: datetime

    class Config:
        from_attributes = True

class SmsTemplateResponse(BaseModel):
    id: int
    user_id: str
    name: str
    content: str

    class Config:
        from_attributes = True

class APIKeyResponse(BaseModel):
    id: int
    user_id: str
    key: str
    is_active: bool

    class Config:
        from_attributes = True

class UserWalletResponse(BaseModel):
    id: str
    username: str
    wallet_balance: float

    class Config:
        orm_mfrom_attributesode = True

class WalletSummaryResponse(BaseModel):
    wallets: List[UserWalletResponse]
    total_balance: float

class TransactionCreate(BaseModel):
    user_id: str
    amount: float
    transaction_type: str

class SmsMessageCreate(BaseModel):
    user_id: str
    recipient: str
    message: str
    status: str = "pending"
    cost: float = 32.0

class SmsDeliveryReportCreate(BaseModel):
    sms_id: int
    status: str

class SmsTemplateCreate(BaseModel):
    user_id: str
    name: str
    content: str

class APIKeyCreate(BaseModel):
    user_id: str

class WalletTopup(BaseModel):
    amount: float

class BulkMessageCreate(BaseModel):
    message: str
    cost: float = 32.0

# User endpoints
@admin_router.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.Users).all()
    return users

@admin_router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@admin_router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user: UserResponse, db: Session = Depends(get_db)):
    db_user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user.dict().items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

@admin_router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    db_user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return

# Wallet endpoints
@admin_router.get("/wallets", response_model=WalletSummaryResponse)
def get_all_wallets(db: Session = Depends(get_db)):
    users = db.query(models.Users).all()
    total_balance = sum(user.wallet_balance for user in users)
    wallets = [
        UserWalletResponse(id=user.id, username=user.username, wallet_balance=user.wallet_balance)
        for user in users
    ]
    return WalletSummaryResponse(wallets=wallets, total_balance=total_balance)

@admin_router.post("/wallets/{user_id}/topup", response_model=UserResponse)
def topup_wallet(user_id: str, topup: WalletTopup, db: Session = Depends(get_db)):
    if topup.amount <= 0:
        raise HTTPException(status_code=400, detail="Top-up amount must be positive")
    
    db_user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.wallet_balance += topup.amount
    new_transaction = models.Transactions(
        user_id=user_id,
        amount=topup.amount,
        transaction_type="credit"
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(db_user)
    return db_user

@admin_router.post("/wallet/{user_id}/topup", response_model=UserResponse)
def topup_wallet(user_id: str, topup: WalletTopup, db: Session = Depends(get_db)):
    if topup.amount <= 0:
        raise HTTPException(status_code=400, detail="Top-up amount must be positive")
    
    db_user = db.query(models.Users).filter(models.Users.clerk_user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.wallet_balance += topup.amount
    new_transaction = models.Transactions(
        user_id=db_user.id,
        amount=topup.amount,
        transaction_type="credit"
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(db_user)
    return db_user

# Transaction endpoints
@admin_router.get("/transactions", response_model=List[TransactionResponse])
def get_all_transactions(db: Session = Depends(get_db)):
    transactions = db.query(models.Transactions).all()
    return transactions

@admin_router.get("/transactions/user/{user_id}", response_model=List[TransactionResponse])
def get_user_transactions(user_id: str, db: Session = Depends(get_db)):
    transactions = db.query(models.Transactions).filter(models.Transactions.user_id == user_id).all()
    return transactions

# @admin_router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
# def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
#     db_user = db.query(models.Users).filter(models.Users.id == transaction.user_id).first()
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     new_transaction = models.Transactions(**transaction.dict())
#     db.add(new_transaction)
#     db.commit()
#     db.refresh(new_transaction)
#     return new_transaction

# SMS Message endpoints
@admin_router.get("/sms_messages", response_model=List[SmsMessageResponse])
def get_all_sms_messages(db: Session = Depends(get_db)):
    sms_messages = db.query(models.SmsMessages).all()
    return sms_messages

@admin_router.get("/sms_messages/user/{user_id}", response_model=List[SmsMessageResponse])
def get_user_sms_messages(user_id: str, db: Session = Depends(get_db)):
    sms_messages = db.query(models.SmsMessages).filter(models.SmsMessages.user_id == user_id).all()
    return sms_messages


# SMS Delivery Report endpoints
@admin_router.get("/sms_delivery_reports", response_model=List[SmsDeliveryReportResponse])
def get_all_delivery_reports(db: Session = Depends(get_db)):
    reports = db.query(models.SmsDeliveryReports).all()
    return reports

@admin_router.post("/sms_delivery_reports", response_model=SmsDeliveryReportResponse, status_code=status.HTTP_201_CREATED)
def create_delivery_report(report: SmsDeliveryReportCreate, db: Session = Depends(get_db)):
    db_sms = db.query(models.SmsMessages).filter(models.SmsMessages.id == report.sms_id).first()
    if not db_sms:
        raise HTTPException(status_code=404, detail="SMS message not found")
    
    new_report = models.SmsDeliveryReports(**report.dict())
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

# SMS Template endpoints
@admin_router.get("/sms_templates", response_model=List[SmsTemplateResponse])
def get_all_sms_templates(db: Session = Depends(get_db)):
    templates = db.query(models.SmsTemplates).all()
    return templates

@admin_router.get("/sms_templates/user/{user_id}", response_model=List[SmsTemplateResponse])
def get_user_sms_templates(user_id: str, db: Session = Depends(get_db)):
    templates = db.query(models.SmsTemplates).filter(models.SmsTemplates.user_id == user_id).all()
    return templates

@admin_router.post("/sms_templates", response_model=SmsTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_sms_template(template: SmsTemplateCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.Users).filter(models.Users.id == template.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if len(template.content) > 160:
        raise HTTPException(status_code=400, detail="Template content exceeds 160 characters")
    
    new_template = models.SmsTemplates(**template.dict())
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template

# API Key endpoints
@admin_router.get("/api_keys", response_model=List[APIKeyResponse])
def get_all_api_keys(db: Session = Depends(get_db)):
    api_keys = db.query(models.APIKeys).all()
    return api_keys

@admin_router.get("/api_keys/user/{user_id}", response_model=List[APIKeyResponse])
def get_user_api_keys(user_id: str, db: Session = Depends(get_db)):
    api_keys = db.query(models.APIKeys).filter(models.APIKeys.user_id == user_id).all()
    return api_keys

@admin_router.post("/api_keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(api_key: APIKeyCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.Users).filter(models.Users.id == api_key.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate secure API key
    characters = string.ascii_letters + string.digits
    new_key = ''.join(secrets.choice(characters) for _ in range(32))
    
    db_api_key = models.APIKeys(user_id=api_key.user_id, key=new_key)
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    return db_api_key

@admin_router.put("/api_keys/{api_key_id}/toggle", response_model=APIKeyResponse)
def toggle_api_key(api_key_id: int, db: Session = Depends(get_db)):
    db_api_key = db.query(models.APIKeys).filter(models.APIKeys.id == api_key_id).first()
    if not db_api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db_api_key.is_active = not db_api_key.is_active
    db.commit()
    db.refresh(db_api_key)
    return db_api_key

# Maintenance endpoints
@admin_router.post("/maintenance/clean_old_transactions")
def clean_old_transactions(months: int = 6, db: Session = Depends(get_db)):
    cutoff_date = datetime.utcnow() - timedelta(days=months*30)
    deleted_count = db.query(models.Transactions).filter(models.Transactions.created_at < cutoff_date).delete()
    db.commit()
    return {"message": f"Deleted {deleted_count} transactions older than {months} months"}

@admin_router.post("/maintenance/clean_pending_sms")
def clean_pending_sms(db: Session = Depends(get_db)):
    deleted_count = db.query(models.SmsMessages).filter(
        models.SmsMessages.status == "pending",
        models.SmsMessages.created_at < datetime.utcnow() - timedelta(hours=24)
    ).delete()
    db.commit()
    return {"message": f"Deleted {deleted_count} pending SMS messages older than 24 hours"}

@admin_router.get("/maintenance/stats")
def get_system_stats(db: Session = Depends(get_db)):
    stats = {
        "total_users": db.query(models.Users).count(),
        "total_transactions": db.query(models.Transactions).count(),
        "total_sms_messages": db.query(models.SmsMessages).count(),
        "total_templates": db.query(models.SmsTemplates).count(),
        "total_api_keys": db.query(models.APIKeys).count(),
        "active_api_keys": db.query(models.APIKeys).filter(models.APIKeys.is_active == True).count(),
        "pending_sms": db.query(models.SmsMessages).filter(models.SmsMessages.status == "pending").count()
    }
    return stats

# Background task simulation (could be used with a task queue like)
@admin_router.post("/background/recalculate_wallet_balances")
def recalculate_wallet_balances(db: Session = Depends(get_db)):
    users = db.query(models.Users).all()
    updated_count = 0
    
    for user in users:
        total_credits = db.query(func.sum(models.Transactions.amount)).filter(
            models.Transactions.user_id == user.id,
            models.Transactions.transaction_type == "credit"
        ).scalar() or 0.0
        
        total_debits = db.query(func.sum(models.Transactions.amount)).filter(
            models.Transactions.user_id == user.id,
            models.Transactions.transaction_type == "debit"
        ).scalar() or 0.0
        
        new_balance = total_credits - total_debits
        if user.wallet_balance != new_balance:
            user.wallet_balance = new_balance
            updated_count += 1
    
    db.commit()
    return {"message": f"Recalculated balances for {updated_count} users {user.wallet_balance}"}