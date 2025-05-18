from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from database import Base

class Users(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    wallet_balance = Column(Float, default=0.0)
    clerk_user_id = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    

class Transactions(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=func.now())


class SmsMessages(Base):
    __tablename__ = "sms_messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    recipient = Column(String(20), nullable=False)
    message = Column(String(160), nullable=False)
    status = Column(String(20), default="pending")
    cost = Column(Float, default=32.0)
    created_at = Column(DateTime, default=func.now())

class SmsDeliveryReports(Base):
    __tablename__ = "sms_delivery_reports"
    id = Column(Integer, primary_key=True)
    sms_id = Column(Integer, ForeignKey("sms_messages.id"), nullable=False)
    status = Column(String(20), nullable=False)
    updated_at = Column(DateTime, default=func.now())

class SmsTemplates(Base):
    __tablename__ = "sms_templates"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String(50), nullable=False)
    content = Column(String(160), nullable=False)


class APIKeys(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    key = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    