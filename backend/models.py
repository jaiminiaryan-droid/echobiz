from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Index
from sqlalchemy.sql import func
from database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=False), default=func.now())
    
    __table_args__ = (
        Index('idx_users_username', 'username'),
    )

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    date = Column(String(20), nullable=False, index=True)
    product = Column(String(255))
    quantity = Column(Integer)
    price_per_unit = Column(Float)
    total = Column(Float, nullable=False)
    category = Column(String(255))
    mode = Column(String(50))
    customer = Column(String(255))
    profit_loss = Column(Float)
    created_at = Column(DateTime(timezone=False), default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_transactions_user_date', 'user_id', 'date'),
        Index('idx_transactions_user_created', 'user_id', 'created_at'),
    )

class Inventory(Base):
    __tablename__ = 'inventory'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    product = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    purchase_price = Column(Float, nullable=False)
    updated_at = Column(DateTime(timezone=False), default=func.now())
    
    __table_args__ = (
        Index('idx_inventory_user_product', 'user_id', 'product', unique=True),
    )
