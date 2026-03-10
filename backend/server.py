from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, engine, Base
from models import User as UserModel, Transaction as TransactionModel, Inventory as InventoryModel

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

JWT_SECRET = os.environ.get('JWT_SECRET', 'echobiz-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    username: str
    created_at: datetime

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    token: str
    username: str

class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)
    id: str
    user_id: str
    type: Literal["sale", "expense", "payment"]
    date: str
    product: Optional[str] = None
    quantity: Optional[int] = None
    price_per_unit: Optional[float] = None
    total: float
    category: Optional[str] = None
    mode: Optional[str] = None
    customer: Optional[str] = None
    profit_loss: Optional[float] = None
    created_at: datetime

class Inventory(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)
    id: str
    user_id: str
    product: str
    quantity: int
    purchase_price: float
    updated_at: datetime

class InventoryAdd(BaseModel):
    product: str
    quantity: int
    purchase_price: float

class CommandInput(BaseModel):
    command: str

class CommandResponse(BaseModel):
    message: str
    transaction: Optional[Transaction] = None

class SummaryResponse(BaseModel):
    sales: float
    expenses: float
    profit: float
    date: str

def create_token(user_id: str, username: str) -> str:
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.now() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@api_router.post("/auth/register", response_model=TokenResponse, status_code=201)
async def register(user_input: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).where(UserModel.username == user_input.username))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    password_hash = bcrypt.hashpw(user_input.password.encode('utf-8'), bcrypt.gensalt())
    user = UserModel(
        id=str(uuid.uuid4()),
        username=user_input.username,
        password_hash=password_hash.decode('utf-8'),
        created_at=datetime.now()
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    token = create_token(user.id, user.username)
    return TokenResponse(token=token, username=user.username)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_input: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).where(UserModel.username == user_input.username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not bcrypt.checkpw(user_input.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user.id, user.username)
    return TokenResponse(token=token, username=user.username)

async def parse_command(command: str) -> dict:
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    system_message = """You are a financial transaction parser for Indian shopkeepers.
Extract structured data from natural language commands.

For SALE commands (sold, becha, sale):
{"type": "sale", "product": "<product_name>", "quantity": <number>, "price_per_unit": <price>, "total": <quantity * price>}

For EXPENSE commands (bought, purchase, spent, kharcha):
{"type": "expense", "category": "<category>", "total": <amount>}

For PAYMENT commands (payment, paid, received, mila):
{"type": "payment", "mode": "<cash/upi/card>", "customer": "<name if mentioned>", "total": <amount>}

For QUERY commands (summary, profit, kitna, status):
{"type": "query", "query_type": "<summary/inventory>"}

Return ONLY valid JSON, no explanation."""
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"parser-{uuid.uuid4()}",
        system_message=system_message
    ).with_model("openai", "gpt-4o")
    
    user_message = UserMessage(text=command)
    response = await chat.send_message(user_message)
    
    import json
    try:
        parsed_data = json.loads(response)
        return parsed_data
    except:
        return {"type": "unknown", "error": "Could not parse command"}

@api_router.post("/command", response_model=CommandResponse)
async def process_command(input: CommandInput, auth: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = auth['user_id']
    command = input.command.strip()
    
    parsed = await parse_command(command)
    
    if parsed.get('type') == 'query':
        query_type = parsed.get('query_type', 'summary')
        if query_type == 'summary':
            return CommandResponse(message="Please check summary section")
        elif query_type == 'inventory':
            return CommandResponse(message="Please check inventory section")
    
    if parsed.get('type') == 'sale':
        product = parsed.get('product')
        quantity = parsed.get('quantity', 0)
        selling_price = parsed.get('price_per_unit', 0)
        
        profit_loss = 0
        if product:
            result = await db.execute(
                select(InventoryModel).where(
                    and_(InventoryModel.user_id == user_id, InventoryModel.product == product)
                )
            )
            inventory_item = result.scalar_one_or_none()
            
            if inventory_item:
                purchase_price = inventory_item.purchase_price
                profit_loss = (selling_price - purchase_price) * quantity
                
                inventory_item.quantity = max(0, inventory_item.quantity - quantity)
                inventory_item.updated_at = datetime.now()
            else:
                inventory = InventoryModel(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    product=product,
                    quantity=0,
                    purchase_price=0,
                    updated_at=datetime.now()
                )
                db.add(inventory)
        
        transaction = TransactionModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="sale",
            date=datetime.now().strftime('%Y-%m-%d'),
            product=product,
            quantity=quantity,
            price_per_unit=selling_price,
            total=parsed.get('total'),
            profit_loss=profit_loss,
            created_at=datetime.now()
        )
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        
        profit_msg = ""
        if profit_loss > 0:
            profit_msg = f" Profit: ₹{profit_loss:.0f}"
        elif profit_loss < 0:
            profit_msg = f" Loss: ₹{abs(profit_loss):.0f}"
        
        return CommandResponse(
            message=f"Sale recorded. Total ₹{transaction.total:.0f}.{profit_msg}",
            transaction=Transaction.model_validate(transaction)
        )
    
    elif parsed.get('type') == 'expense':
        transaction = TransactionModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="expense",
            date=datetime.now().strftime('%Y-%m-%d'),
            category=parsed.get('category', 'General'),
            total=parsed.get('total'),
            created_at=datetime.now()
        )
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        
        return CommandResponse(
            message=f"Expense recorded. ₹{transaction.total:.0f}.",
            transaction=Transaction.model_validate(transaction)
        )
    
    elif parsed.get('type') == 'payment':
        transaction = TransactionModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="payment",
            date=datetime.now().strftime('%Y-%m-%d'),
            mode=parsed.get('mode', 'cash'),
            customer=parsed.get('customer'),
            total=parsed.get('total'),
            created_at=datetime.now()
        )
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        
        return CommandResponse(
            message=f"Payment received. ₹{transaction.total:.0f} recorded.",
            transaction=Transaction.model_validate(transaction)
        )
    
    else:
        return CommandResponse(message="Sorry, I didn't understand that. Please try again.")

@api_router.get("/summary", response_model=SummaryResponse)
async def get_summary(auth: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = auth['user_id']
    today = datetime.now().strftime('%Y-%m-%d')
    
    result = await db.execute(
        select(TransactionModel).where(
            and_(TransactionModel.user_id == user_id, TransactionModel.date == today)
        )
    )
    transactions = result.scalars().all()
    
    sales = sum(t.total for t in transactions if t.type == 'sale')
    expenses = sum(t.total for t in transactions if t.type == 'expense')
    profit = sales - expenses
    
    return SummaryResponse(sales=sales, expenses=expenses, profit=profit, date=today)

@api_router.get("/inventory", response_model=List[Inventory])
async def get_inventory(auth: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = auth['user_id']
    
    result = await db.execute(
        select(InventoryModel).where(InventoryModel.user_id == user_id)
    )
    inventory_items = result.scalars().all()
    
    return [Inventory.model_validate(item) for item in inventory_items]

@api_router.post("/inventory/add")
async def add_inventory(inventory_input: InventoryAdd, auth: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = auth['user_id']
    product = inventory_input.product.lower()
    
    result = await db.execute(
        select(InventoryModel).where(
            and_(InventoryModel.user_id == user_id, InventoryModel.product == product)
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.quantity += inventory_input.quantity
        existing.purchase_price = inventory_input.purchase_price
        existing.updated_at = datetime.now()
        await db.commit()
        return {"message": f"Updated {product}. New stock: {existing.quantity} units", "quantity": existing.quantity}
    else:
        inventory = InventoryModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            product=product,
            quantity=inventory_input.quantity,
            purchase_price=inventory_input.purchase_price,
            updated_at=datetime.now()
        )
        db.add(inventory)
        await db.commit()
        return {"message": f"Added {product} to inventory", "quantity": inventory_input.quantity}

@api_router.post("/inventory/seed")
async def seed_inventory(auth: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = auth['user_id']
    
    initial_stock = [
        {"product": "rice", "quantity": 50, "purchase_price": 40},
        {"product": "wheat flour", "quantity": 30, "purchase_price": 35},
        {"product": "sugar", "quantity": 25, "purchase_price": 45},
        {"product": "cooking oil", "quantity": 20, "purchase_price": 180},
        {"product": "tea", "quantity": 15, "purchase_price": 250},
        {"product": "salt", "quantity": 40, "purchase_price": 20},
        {"product": "milk", "quantity": 10, "purchase_price": 60},
        {"product": "biscuits", "quantity": 50, "purchase_price": 10},
    ]
    
    for item in initial_stock:
        result = await db.execute(
            select(InventoryModel).where(
                and_(InventoryModel.user_id == user_id, InventoryModel.product == item["product"])
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            inventory = InventoryModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                product=item["product"],
                quantity=item["quantity"],
                purchase_price=item["purchase_price"],
                updated_at=datetime.now()
            )
            db.add(inventory)
    
    await db.commit()
    return {"message": "Inventory seeded with basic groceries", "items_added": len(initial_stock)}

@api_router.get("/transactions", response_model=List[Transaction])
async def get_transactions(auth: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    user_id = auth['user_id']
    
    result = await db.execute(
        select(TransactionModel)
        .where(TransactionModel.user_id == user_id)
        .order_by(TransactionModel.created_at.desc())
        .limit(50)
    )
    transactions = result.scalars().all()
    
    return [Transaction.model_validate(t) for t in transactions]

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
