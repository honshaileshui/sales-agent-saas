"""
Authentication Routes - SELF-CONTAINED
======================================
All auth logic is here to avoid circular imports.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

router = APIRouter()

# Config
SECRET_KEY = "salesagent-ai-secret-key-change-in-production-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Helpers
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": user_id, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

# Models
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: Optional[str] = None


# Endpoints
@router.post("/login")
async def login(creds: UserLogin):
    from database import get_db_cursor
    
    with get_db_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM users WHERE email=%s AND is_active=TRUE", (creds.email.lower(),))
        user = cur.fetchone()
    
    if not user or not verify_password(creds.password, dict(user)["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = dict(user)
    with get_db_cursor() as cur:
        cur.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=%s", (user["id"],))
    
    return {"access_token": create_token(str(user["id"])), "token_type": "bearer", "expires_in": 86400}


@router.post("/register", status_code=201)
async def register(data: UserRegister):
    from database import get_db_cursor
    
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    with get_db_cursor(commit=False) as cur:
        cur.execute("SELECT id FROM users WHERE email=%s", (data.email.lower(),))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
    
    with get_db_cursor() as cur:
        cur.execute("""
            INSERT INTO users (email, password_hash, full_name, company_name)
            VALUES (%s, %s, %s, %s) RETURNING *
        """, (data.email.lower(), hash_password(data.password), data.full_name, data.company_name))
        user = dict(cur.fetchone())
    
    return {"id": str(user["id"]), "email": user["email"], "full_name": user["full_name"]}


@router.get("/me")
async def me(creds: HTTPAuthorizationCredentials = Depends(security)):
    from database import get_db_cursor
    
    user_id = decode_token(creds.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    user = dict(user)
    return {"id": str(user["id"]), "email": user["email"], "full_name": user["full_name"]}


@router.post("/change-password")
async def change_pwd(current_password: str, new_password: str, creds: HTTPAuthorizationCredentials = Depends(security)):
    from database import get_db_cursor
    
    user_id = decode_token(creds.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = dict(cur.fetchone())
    
    if not verify_password(current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Wrong password")
    
    with get_db_cursor() as cur:
        cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (hash_password(new_password), user_id))
    
    return {"success": True}


@router.post("/refresh")
async def refresh(creds: HTTPAuthorizationCredentials = Depends(security)):
    user_id = decode_token(creds.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"access_token": create_token(user_id), "token_type": "bearer", "expires_in": 86400}