import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
from pydantic import BaseModel, Field
import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError

# Базы данных (в памяти, для примера)
users_db: dict[str, dict] = {}
ads_db: dict[str, 'Ad'] = {}

# Модели данных
class UserCreate(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: str
    email: str
    password_hash: str

class AdCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)

class Ad(AdCreate):
    id: str
    owner_id: str
    created_at: datetime

# Функции для работы с паролями
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed.encode('utf-8')
    )

SECRET_KEY = "your-very-secret-key-change-in-production"

def create_jwt_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_jwt_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except (DecodeError, ExpiredSignatureError):
        return None
