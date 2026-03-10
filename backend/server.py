from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File
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
from sarvamai import SarvamAI
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, engine, Base
from models import User as UserModel, Transaction as TransactionModel, Inventory as InventoryModel

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize Sarvam AI client - 100% Indian AI solution!
sarvam_client = SarvamAI(api_subscription_key=os.environ.get('SARVAM_API_KEY'))

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
    """Parse natural language command using Sarvam AI LLM (Made in India!)"""
    
    system_message = """You are a financial transaction parser for Indian shopkeepers.
Extract structured data from natural language commands in HINDI or ENGLISH.

IMPORTANT: Detect buying vs selling carefully:
- BUYING/PURCHASE: kharido, kharide, kharida, liye, liya, bought, purchase, mangaya
- SELLING: beche, bechi, becha, bechaa, sold, sale, diye (when giving to customer)

HINDI SALE (बेचना - Selling) Examples:
Input: "10 chawal 60 rupaye mein beche"
Output: {"type": "sale", "product": "chawal", "quantity": 10, "price_per_unit": 60, "total": 600}

Input: "Maine 5 sugar 50 rupaye mein bechi"
Output: {"type": "sale", "product": "sugar", "quantity": 5, "price_per_unit": 50, "total": 250}

Input: "5 kilo chawal 60 ke rate pe bech diye"
Output: {"type": "sale", "product": "chawal", "quantity": 5, "price_per_unit": 60, "total": 300}

HINDI PURCHASE (खरीदना - Buying/Inventory) Examples:
Input: "10 kilo chawal 50 ke rate pe kharida"
Output: {"type": "purchase", "product": "chawal", "quantity": 10, "price_per_unit": 50, "total": 500}

Input: "ye chiz 100 ki kharido"
Output: {"type": "purchase", "product": "item", "quantity": 1, "price_per_unit": 100, "total": 100}

Input: "5 sugar 40 rupaye mein liye"
Output: {"type": "purchase", "product": "sugar", "quantity": 5, "price_per_unit": 40, "total": 200}

Input: "maine 10 kg chawal 50 ke rate pe kharide"
Output: {"type": "purchase", "product": "chawal", "quantity": 10, "price_per_unit": 50, "total": 500}

ENGLISH SALE Examples:
Input: "Sold 5 rice for 50 each"
Output: {"type": "sale", "product": "rice", "quantity": 5, "price_per_unit": 50, "total": 250}

ENGLISH PURCHASE Examples:
Input: "Bought 10 rice at 40 each"
Output: {"type": "purchase", "product": "rice", "quantity": 10, "price_per_unit": 40, "total": 400}

HINDI EXPENSE Examples:
Input: "500 rupaye ka kharcha" or "Dukaan ke liye 2000 kharch kiye"
Output: {"type": "expense", "category": "shop", "total": 2000}

ENGLISH EXPENSE Examples:
Input: "Bought shop supplies for 3000"
Output: {"type": "expense", "category": "shop supplies", "total": 3000}

Common Products Translation:
- chawal = rice
- cheeni = sugar
- atta = wheat flour
- tel = oil
- daal = lentils
- namak = salt

Return ONLY valid JSON with no extra text or explanation."""
    
    try:
        # Use Sarvam AI's chat completion
        import asyncio
        loop = asyncio.get_event_loop()
        
        def get_sarvam_response():
            response = sarvam_client.chat.completions(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": command}
                ],
                model="sarvam-105b",  # Using Sarvam's 105B model for better understanding
                temperature=0,
                max_tokens=200
            )
            return response.choices[0].message.content
        
        response_text = await loop.run_in_executor(None, get_sarvam_response)
        
        import json
        # Clean response text - remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        parsed_data = json.loads(response_text)
        return parsed_data
    except Exception as e:
        logger.error(f"Sarvam AI parse error: {str(e)}")
        return {"type": "unknown", "error": "Could not parse command"}

@api_router.post("/voice")
async def process_voice(
    audio: UploadFile = File(...),
    auth: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Convert voice to text using Sarvam AI (optimized for Indian languages) and process command"""
    
    try:
        # Save uploaded audio temporarily
        temp_dir = Path("/tmp")
        temp_dir.mkdir(exist_ok=True)
        audio_path = temp_dir / f"{uuid.uuid4()}.webm"
        
        with open(audio_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Transcribe with Sarvam AI (supports 22 Indian languages + code-mixing)
        # Note: Sarvam SDK is synchronous, so we run it in executor
        import asyncio
        loop = asyncio.get_event_loop()
        
        def transcribe_audio():
            with open(audio_path, "rb") as audio_file:
                response = sarvam_client.speech_to_text.transcribe(
                    file=audio_file,
                    model="saaras:v3",
                    mode="transcribe"
                )
                return response.transcript
        
        transcribed_text = await loop.run_in_executor(None, transcribe_audio)
        logger.info(f"Sarvam AI transcribed: {transcribed_text}")
        
        # Clean up temp file
        audio_path.unlink(missing_ok=True)
        
        # Parse the transcribed command with GPT
        parsed = await parse_command(transcribed_text)
        
        # Process as regular command
        user_id = auth['user_id']
        
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
            
            profit_msg = ""
            if profit_loss > 0:
                profit_msg = f" Profit: ₹{profit_loss:.0f}"
            elif profit_loss < 0:
                profit_msg = f" Loss: ₹{abs(profit_loss):.0f}"
            
            return {
                "text": transcribed_text,
                "message": f"Sale recorded. Total ₹{transaction.total:.0f}.{profit_msg}",
                "success": True
            }
        
        elif parsed.get('type') == 'purchase':
            # Add to inventory when purchasing items
            product = parsed.get('product')
            quantity = parsed.get('quantity', 0)
            purchase_price = parsed.get('price_per_unit', 0)
            
            if product:
                result = await db.execute(
                    select(InventoryModel).where(
                        and_(InventoryModel.user_id == user_id, InventoryModel.product == product)
                    )
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    existing.quantity += quantity
                    existing.purchase_price = purchase_price
                    existing.updated_at = datetime.now()
                else:
                    inventory = InventoryModel(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        product=product,
                        quantity=quantity,
                        purchase_price=purchase_price,
                        updated_at=datetime.now()
                    )
                    db.add(inventory)
                
                await db.commit()
                
                return {
                    "text": transcribed_text,
                    "message": f"Purchase recorded. Added {quantity} {product} to inventory. Total ₹{parsed.get('total'):.0f}.",
                    "success": True
                }
        
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
            
            return {
                "text": transcribed_text,
                "message": f"Expense recorded. ₹{transaction.total:.0f}.",
                "success": True
            }
        
        else:
            return {
                "text": transcribed_text,
                "message": "Command transcribed but not understood. Please try again.",
                "success": False
            }
    
    except Exception as e:
        logger.error(f"Voice processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")

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
    
    elif parsed.get('type') == 'purchase':
        # Add to inventory when purchasing items
        product = parsed.get('product')
        quantity = parsed.get('quantity', 0)
        purchase_price = parsed.get('price_per_unit', 0)
        
        if product:
            result = await db.execute(
                select(InventoryModel).where(
                    and_(InventoryModel.user_id == user_id, InventoryModel.product == product)
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.quantity += quantity
                existing.purchase_price = purchase_price
                existing.updated_at = datetime.now()
            else:
                inventory = InventoryModel(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    product=product,
                    quantity=quantity,
                    purchase_price=purchase_price,
                    updated_at=datetime.now()
                )
                db.add(inventory)
            
            await db.commit()
            
            return CommandResponse(
                message=f"Purchase recorded. Added {quantity} {product} to inventory. Total ₹{parsed.get('total'):.0f}."
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
