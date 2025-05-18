import time
from typing import Optional
from fastapi import BackgroundTasks, Depends, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from database import get_db
import models
from datetime import datetime, timedelta

auto_delete_router = APIRouter(
    prefix="/api/v1/maintenance",
    tags=["System Maintenance"]
)

async def delete_old_records(db: Session):
    """
    Delete records older than 24 hours
    """
    try:
        # cutoff time (24 hours ago)
        cutoff_time = datetime.now() - timedelta(hours=24)

        old_messages = db.query(models.SmsMessages).filter(
            models.SmsMessages.created_at < cutoff_time
        ).all()
        

        for message in old_messages:
            db.query(models.SmsDeliveryReports).filter(
                models.SmsDeliveryReports.sms_id == message.id
            ).delete()
        

        for message in old_messages:
            db.delete(message)

        old_transactions = db.query(models.Transactions).filter(
            models.Transactions.created_at < cutoff_time
        ).all()
        for transaction in old_transactions:
            db.delete(transaction)


        old_promo_usages = db.query(models.PromoCodeUsage).filter(
            models.PromoCodeUsage.used_at < cutoff_time
        ).all()
        for usage in old_promo_usages:
            if usage.referrer_reward_paid and usage.referred_reward_paid:
                db.delete(usage)

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error during auto-deletion: {str(e)}"
        )

@auto_delete_router.post("/cleanup")
async def trigger_cleanup(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Trigger the cleanup process as a background task
    """
    background_tasks.add_task(delete_old_records, db)
    return JSONResponse(
        content={"message": "Cleanup process started in background"},
        status_code=200
    )

@auto_delete_router.get("/status")
async def cleanup_status(db: Session = Depends(get_db)):
    """
    Get statistics about records that will be cleaned up in next run
    """
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    old_messages_count = db.query(models.SmsMessages).filter(
        models.SmsMessages.created_at < cutoff_time
    ).count()
    
    old_transactions_count = db.query(models.Transactions).filter(
        models.Transactions.created_at < cutoff_time
    ).count()
    
    old_delivery_reports_count = db.query(models.SmsDeliveryReports).filter(
        models.SmsDeliveryReports.updated_at < cutoff_time
    ).count()
    
    old_promo_usages_count = db.query(models.PromoCodeUsage).filter(
        models.PromoCodeUsage.used_at < cutoff_time,
        models.PromoCodeUsage.referrer_reward_paid == True,
        models.PromoCodeUsage.referred_reward_paid == True
    ).count()
    
    return {
        "old_messages": old_messages_count,
        "old_transactions": old_transactions_count,
        "old_delivery_reports": old_delivery_reports_count,
        "old_promo_usages": old_promo_usages_count,
        "cutoff_time": cutoff_time.isoformat()
    }

