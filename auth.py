from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
import sqlite3
import bcrypt 
from datetime import datetime, timezone, timedelta
import jwt
import os 
from dotenv import load_dotenv

load_dotenv()

    
app = FastAPI()
security = HTTPBearer() 

def create_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:    
        payload = jwt.decode(token, os.getenv("secret_key"), algorithm=os.getenv("algorithm"))
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

conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS user_table (user_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT)")
conn.commit()



class Register(BaseModel):
    name: str 
    email: str
    password: str = Field(min_length = 8)

class Login(BaseModel):
    email: str
    password: str = Field(min_length = 8)

@app.post("/register")
async def get_registered(reg: Register):
    hashed = bcrypt.hashpw(reg.password.encode(), bcrypt.gensalt()) 
    try:
        cursor.execute("INSERT INTO user_table (name, email, password) VALUES (?, ?, ?)", (reg.name, reg.email, hashed))
        user_id = cursor.lastrowid
        token = get_token(user_id = user_id)
        return {"message": "Success", "your_token": token}
    except sqlite3.IntegrityError:
        return {"message": "This email is already registered."}

@app.post("/login")
async def get_login(log: Login):
    cursor.execute("SELECT user_id, password from user_table WHERE email = ?", (log.email,))
    p = cursor.fetchone()
    if p is None:
        raise HTTPException(status_code= 400, detail = "Create an account first")
    else:
        if bcrypt.checkpw(log.password.encode(), p[1]):  
            token = get_token(user_id= p[0])
            return {"message": "Login successfull", "your_token": token, "token_type": "bearer"}
        return {"message": "create user first!"}


cursor.execute("CREATE TABLE IF NOT EXISTS expense (expense_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, price REAL, description TEXT, created_at TEXT, user_id INTEGER, FOREIGN KEY (user_id) REFERENCES user_table (user_id))")
conn.commit()
class Post_expense(BaseModel):
    title: str
    price: float 
    description: str

@app.post("/create_expense")
async def send_expense(exp: Post_expense, current_user_id: int = Depends(create_user)):
    now = datetime.now.strftime("%H:%M")
    cursor.execute("INSERT INTO expense (title, price, description, created_at, user_id)", (exp.title, exp.description, now, current_user_id))
    conn.commit()
    return {"message": "Expense created", "owner_id": current_user_id}


#Создать новый файл, и там сделать полный круд. 