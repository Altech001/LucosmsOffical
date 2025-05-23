from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Annotated
from typing import List
import hashlib
from sqlalchemy.orm import Session
# from models import  SMSResponse, SMSTemplate
from database import get_db
import time
from fastapi.concurrency import run_in_threadpool
from dotenv import load_dotenv
import os

import models
from routes.auth import get_current_user
from schemas import SMSResponse, SMSTemplate


load_dotenv()



user_router = APIRouter(
    prefix="/api/v1",
    tags=["Luco SMS"]
)

SMS_COST = 32.0

#Injection Dependency =================================================
# dep_db: Annotated[Session, Depends(get_db)] = Depends(get_db)
dep_db  = Annotated[Session, Depends(get_db)]



#==============ACCOUNT ENDPOINTS START =======================================================
# @user_router.post("/topup")
# def topup_wallet(topup: TopupRequest, user_id: int, db: Session = Depends(get_db)):
#     user = db.query(models.Users).filter(models.Users.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not Found")
    
#     user.wallet_balance += topup.amount
#     transaction = models.Transactions(
#         user_id=user_id,
#         amount=topup.amount,
#         transaction_type="topup"
#     )
#     db.add(transaction)
#     db.commit()
#     return {"message": "Wallet topped up successfully", "new_balance": user.wallet_balance}


@user_router.get("/wallet-balance")
def get_wallet_balance(user_id: str, db: Session = Depends(get_db)):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"balance": user.wallet_balance}


@user_router.get("/transaction_history")
def transaction_history(user_id: str, db: dep_db, skip : int,limit: int = 10):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    transactions = db.query(models.Transactions).filter(models.Transactions.user_id == user_id).all()
    transactions = transactions[skip:skip+limit]
    if not transactions:
        raise HTTPException(detail="No transactions found", status_code=404)
    
    return transactions


@user_router.delete("/transcation_delete")
def delete_transaction(transaction_id: int, user_id: str, db: dep_db):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    transaction = db.query(models.Transactions).filter(models.Transactions.id == transaction_id).first()
    if not transaction:
        raise HTTPException(detail="No transaction found", status_code=404)
    db.delete(transaction)
    db.commit()
    return {
        "message": "Transaction deleted successfully"
    }
    
@user_router.delete("/all_transaction")
def delete_all_transactions(user_id: str, db: dep_db):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    transactions = db.query(models.Transactions).filter(models.Transactions.user_id == user_id).all()
    if not transactions:
        raise HTTPException(detail="No transactions found", status_code=404)
    for transaction in transactions:
        db.delete(transaction)
    db.commit()
    return {
        "message": "All transactions deleted successfully"
    }
    


#============= SMS TEMPLATE ENDPOINTS START ===================================================

@user_router.post("/smstemplate")
def sms_template(template: SMSTemplate, user_id: str, db: dep_db):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    sms_template = models.SmsTemplates(
        user_id=user.id,
        name= user.username,
        content=template.content
    )
    # sms_template = SMSTemplate
    db.add(sms_template)
    db.commit()
    db.refresh(sms_template)
    
    return sms_template

@user_router.get("/smstemplate", response_model=List[SMSTemplate])
def fetch_sms_templates(user_id: int, db: dep_db, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    templates = db.query(models.SmsTemplates).filter(models.SmsTemplates.user_id == user_session.user_id).all()
    
    return templates

@user_router.put("/sms_temp_update")
def sms_template_update(user_id: str, new_content: str, db: dep_db, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    template = db.query(models.SmsTemplates).filter(models.SmsTemplates.user_id == user_session.user_id).first()
    if not template:
        raise HTTPException(detail="No template found", status_code=404)
    
    current_content = template.content
    
    template.content = new_content
    db.commit()
    db.refresh(template)
    
    return {
        "message": "Template updated successfully",
        "old_content": current_content,
        "new_content": template.content
    }
    

@user_router.delete("/sms_template")
def delete_sms_template(template_id: int, user_id: str, db: dep_db, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    sms_template = db.query(models.SmsTemplates).filter(models.SmsTemplates.id == template_id).first()
    if not sms_template:
        raise HTTPException(detail="No template found", status_code=404)
    
    db.delete(sms_template)
    db.commit()
    
    return {
        "message": "SMS template deleted successfully"
    }


#============= SMS TEMPLATE ENDPOINTS START ===================================================
@user_router.get("/delivery_report")
def delivery_report(user_id: str, sms_id : int, db: dep_db, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    delivery_reports = db.query(models.SmsDeliveryReports).filter(models.SmsDeliveryReports.sms_id == sms_id).all()
    if not delivery_reports:
        raise HTTPException(detail="No delivery report found", status_code=404)
    
    return {
        "delivery_reports": delivery_reports
    }



@user_router.get("/sms_history", response_model=List[SMSResponse])
def sms_history(user_id: str, db: dep_db, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    message = db.query(models.SmsMessages).filter(models.SmsMessages.user_id == user_session.user_id).all()
    if not message:
        raise HTTPException(detail="No message found", status_code=404)
    
    return message


@user_router.delete("/delivery_report")
def delete_delivery_report(user_id: int, db: dep_db, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    delivery_report = db.query(models.SmsDeliveryReports).all()
    if not delivery_report:
        raise HTTPException(detail="No delivery report found", status_code=404)
    
    db.delete(delivery_report)
    db.commit()
    
    return {
        "message": "Delivery report deleted successfully"
    }
    
@user_router.delete("/sms_history")
def delete_sms_history(message_id: int, user_id: str, db: dep_db, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    sms_message = db.query(models.SmsMessages).filter(models.SmsMessages.id == message_id).first()
    if not sms_message:
        raise HTTPException(detail="No message found", status_code=404)
    
    db.delete(sms_message)
    db.commit()
    
    return {
        "message": "SMS history deleted successfully"
    }
    



