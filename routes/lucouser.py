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
from pydantic import BaseModel, constr
import models
from routes.auth import get_current_user
from schemas import SMSResponse, SMSTemplate


load_dotenv()



user_router = APIRouter(
    prefix="/api/v1",
    tags=["Luco SMS"]
)



SMS_COST = 32.0

#Injection Dependency =======================================================================
# dep_db: Annotated[Session, Depends(get_db)] = Depends(get_db)
dep_db  = Annotated[Session, Depends(get_db)]


#==============ACCOUNT ENDPOINTS START =======================================================

@user_router.get("/wallet-balance")
def get_wallet_balance(user_session=Depends(get_current_user), db: Session = Depends(get_db)):

    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"balance": user.wallet_balance}


@user_router.get("/transaction_history")
def transaction_history(db: dep_db, skip: int, limit: int = 10, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    transactions = db.query(models.Transactions).filter(models.Transactions.user_id == user.id).all()
    transactions = transactions[skip:skip+limit]
    if not transactions:
        raise HTTPException(detail="No transactions found", status_code=404)
    return transactions


@user_router.delete("/transcation_delete")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db), user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    transaction = db.query(models.Transactions).filter(
        models.Transactions.id == transaction_id,
        models.Transactions.user_id == user.id
    ).first()
    if not transaction:
        raise HTTPException(detail="No transaction found", status_code=404)
    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}
    
@user_router.delete("/all_transaction")
def delete_all_transactions(db: Session = Depends(get_db), user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    transactions = db.query(models.Transactions).filter(models.Transactions.user_id == user.id).all()
    if not transactions:
        raise HTTPException(detail="No transactions found", status_code=404)
    for transaction in transactions:
        db.delete(transaction)
    db.commit()
    return {"message": "All transactions deleted successfully"}
    


#============= SMS TEMPLATE ENDPOINTS START ===================================================

@user_router.post("/smstemplate")
def sms_template(template: SMSTemplate, db: Session = Depends(get_db), user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    sms_template = models.SmsTemplates(
        user_id=user.id,
        name=template.name,
        content=template.cotent
    )
    db.add(sms_template)
    db.commit()
    db.refresh(sms_template)
    return sms_template

@user_router.get("/smstemplate", response_model=List[SMSTemplate])
def fetch_sms_templates(db: dep_db, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    templates = db.query(models.SmsTemplates).filter(models.SmsTemplates.user_id == user.id).all()
    return templates

# @user_router.put("/sms_temp_update")
# def sms_template_update(new_content: str, db: dep_db, user_session=Depends(get_current_user)):
#     user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
#     if not user:
#         raise HTTPException(detail="User not Found", status_code=404)
    
#     template = db.query(models.SmsTemplates).filter(models.SmsTemplates.user_id == user.id).first()
#     if not template:
#         raise HTTPException(detail="No template found", status_code=404)
    
#     current_content = template.content
#     template.content = new_content
#     db.commit()
#     db.refresh(template)
    
#     return {
#         "message": "Template updated successfully",
#         "old_content": current_content,
#         "new_content": template.content
#     }

class UpdateTemplate(BaseModel):
    new_content: constr(min_length=1, max_length=160, strip_whitespace=True) # type: ignore

@user_router.put("/sms_temp_update")
def update_sms_template(
    template_id: int,
    update_data: UpdateTemplate,
    db: Session = Depends(get_db),
    user_session=Depends(get_current_user)
):
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    template = db.query(models.SmsTemplates).filter(
        models.SmsTemplates.id == template_id,
    ).first()
    if not template:
        raise HTTPException(detail="No template found", status_code=404)
    
    current_content = template.content
    template.content = update_data.new_content
    db.commit()
    db.refresh(template)
    
    return {
        "message": "Template updated successfully",
        "old_content": current_content,
        "new_content": template.content
    }

@user_router.delete("/sms_template")
def delete_sms_template(template_id: int, db: dep_db, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
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
def delivery_report( db: dep_db, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    delivery_reports = db.query(models.SmsDeliveryReports).filter(
        # models.SmsDeliveryReports.sms_id == sms_id,
        models.SmsDeliveryReports.id == user.id
    ).all()
    if not delivery_reports:
        raise HTTPException(detail="No delivery report found", status_code=404)
    
    return {"delivery_reports": delivery_reports}

@user_router.delete("/delivery_report")
def delete_delivery_report(db: dep_db, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    delivery_reports = db.query(models.SmsDeliveryReports).filter(
        models.SmsDeliveryReports.user_id == user.id
    ).all()
    if not delivery_reports:
        raise HTTPException(detail="No delivery reports found", status_code=404)
    
    for report in delivery_reports:
        db.delete(report)
    db.commit()
    
    return {"message": "Delivery reports deleted successfully"}


@user_router.get("/sms_history", response_model=List[SMSResponse])
def sms_history(db: dep_db, user_session=Depends(get_current_user)):
    # First get the user using clerk_user_id
    user = db.query(models.Users).filter(
        models.Users.clerk_user_id == user_session.user_id
    ).first()
    
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    # Use the user's internal UUID to query messages
    messages = db.query(models.SmsMessages).filter(
        models.SmsMessages.user_id == user.id  # Using user.id (UUID) instead of user_session.user_id
    ).all()
    
    if not messages:
        raise HTTPException(detail="No message found", status_code=404)
    
    return messages



@user_router.delete("/sms_history/{message_id}")
def delete_sms_history(message_id: int, db: dep_db, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    # First check if the SMS exists and belongs to the user
    sms_message = db.query(models.SmsMessages).filter(
        models.SmsMessages.id == message_id,
        models.SmsMessages.user_id == user.id
    ).first()
    if not sms_message:
        raise HTTPException(detail="No message found", status_code=404)
    
    # Delete related delivery reports first
    db.query(models.SmsDeliveryReports).filter(
        models.SmsDeliveryReports.sms_id == message_id
    ).delete()
    
    # Then delete the SMS message
    db.delete(sms_message)
    db.commit()
    return {"message": "SMS history deleted successfully"}

@user_router.delete("/sms_history/all")
def delete_all_sms_history(db: dep_db, user_session=Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.clerk_user_id == user_session.user_id).first()
    if not user:
        raise HTTPException(detail="User not Found", status_code=404)
    
    # Get all SMS messages for this user
    sms_messages = db.query(models.SmsMessages).filter(
        models.SmsMessages.user_id == user.id
    ).all()
    if not sms_messages:
        raise HTTPException(detail="No messages found", status_code=404)
    
    # Delete all related delivery reports first
    for message in sms_messages:
        db.query(models.SmsDeliveryReports).filter(
            models.SmsDeliveryReports.sms_id == message.id
        ).delete()
    
    # Then delete all SMS messages
    db.query(models.SmsMessages).filter(
        models.SmsMessages.user_id == user.id
    ).delete()
    
    db.commit()
    return {"message": "All SMS history deleted successfully"}

