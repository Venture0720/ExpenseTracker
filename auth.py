from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from pydantic.networks import EmailStr
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
import sqlite3
import bcrypt 
from datetime import datetime, timezone, timedelta
import jwt
import os 
from dotenv import load_dotenv

load_dotenv(dotenv_path=".gitignore/.env")

    
app = FastAPI()
security = HTTPBearer() 

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:    
        payload = jwt.decode(
    token,
    os.getenv("secret_key"),
    algorithms=[os.getenv("algorithm")]
)
        user_id: int = payload.get("user_id")
        if user_id is None: 
            raise HTTPException(status_code=401, detail  = "Invalid token") 
        return user_id 
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code = 401, detail = "Token has expired")
    except jwt.InvalidTokenError: 
        raise HTTPException(status_code = 401, detail = "Invalid token")



def get_token(user_id: int):
    secret_key = os.getenv("secret_key")
    algorithm = os.getenv("algorithm")
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        "iat": datetime.now(timezone.utc)
    }

    token = jwt.encode(payload, secret_key, algorithm=algorithm) 
    return token 

DB_PATH = "users.db"


def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS user_table (user_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS expense (expense_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, price REAL, description TEXT, created_at TEXT, user_id INTEGER, FOREIGN KEY (user_id) REFERENCES user_table (user_id))"
        )
        conn.commit()
    finally:
        conn.close()


init_db()


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class Register(BaseModel):
    name: str 
    email: EmailStr
    password: str = Field(min_length = 8)

class Login(BaseModel):
    email: EmailStr
    password: str = Field(min_length = 8)

@app.post("/register")
async def get_registered(reg: Register):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        hashed = bcrypt.hashpw(reg.password.encode(), bcrypt.gensalt())
        cursor.execute("INSERT INTO user_table (name, email, password) VALUES (?, ?, ?)", (reg.name, reg.email, hashed))
        conn.commit()
        user_id = cursor.lastrowid
        token = get_token(user_id=user_id)
        return {"message": "Success", "your_token": token}
    except sqlite3.IntegrityError:
        return {"message": "This email is already registered."}
    finally:
        conn.close()

@app.post("/login")
async def get_login(log: Login):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, password from user_table WHERE email = ?", (log.email,))
        p = cursor.fetchone()
        if p is None:
            raise HTTPException(status_code=400, detail="Create an account first")
        if bcrypt.checkpw(log.password.encode(), p[1]):
            token = get_token(user_id=p[0])
            return {"message": "Login successfull", "your_token": token, "token_type": "bearer"}
        return {"message": "create user first!"}
    finally:
        conn.close()


class Post_expense(BaseModel):
    title: str
    price: float 
    description: str
#Создать новый файл, и там сделать полный круд. 