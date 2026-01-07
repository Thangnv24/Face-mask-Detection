from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from passlib.context import CryptContext
from datetime import timedelta
from app.core.security import create_access_token
import json, os

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

class RegisterIn(BaseModel):
    username: str
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 4:
            raise ValueError('Password must be at least 4 characters')
        if len(v) > 72:
            raise ValueError('Password cannot be longer than 72 characters')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username cannot be longer than 50 characters')
        return v

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=dict)
def register(data: RegisterIn):
    users = load_users()
    if data.username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Truncate password to 72 bytes for bcrypt
    password_bytes = data.password.encode('utf-8')[:72]
    hashed = pwd_context.hash(password_bytes.decode('utf-8'))
    
    users[data.username] = {"password": hashed}
    save_users(users)
    return {"msg": "registered"}

@router.post("/login", response_model=TokenOut)
def login(data: RegisterIn):
    users = load_users()
    if data.username not in users:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Truncate password to 72 bytes for bcrypt
    password_bytes = data.password.encode('utf-8')[:72]
    
    if not pwd_context.verify(password_bytes.decode('utf-8'), users[data.username]["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": data.username}, expires_delta=timedelta(minutes=60))
    return {"access_token": access_token}
