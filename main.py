#1. Category of expenses 
#2. Sorting by importance and amount (ASC, DESC)
#3. Switch of contents. 
#4. 
from pydantic import BaseModel
from datetime import datetime, timezone
from fastapi import Depends, APIRouter, HTTPException
from auth import app, Post_expense, get_current_user, get_db

expense_router = APIRouter(prefix="/expenses", tags=["expenses"])

@expense_router.post("/create")
async def send_expense(exp: Post_expense, current_user_id: int = Depends(get_current_user), db = Depends(get_db)):
    cursor = db.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO expense (title, price, description, created_at, user_id) VALUES (?, ?, ?, ?, ?)",
        (exp.title, exp.price, exp.description, now, current_user_id),
    )
    db.commit()
    return {"message": "Expense created", "owner_id": current_user_id}

@expense_router.get("/get")
async def get_expense(current_user_id: int = Depends(get_current_user), db = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM expense WHERE user_id = ?", (current_user_id,))
    result = cursor.fetchall()
    return [dict(row) for row in result]

@expense_router.delete("/{expense_id}")
async def delete_expense(expense_id: int, current_user_id: int = Depends(get_current_user), db = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM expense WHERE expense_id = ? AND user_id = ?", (expense_id, current_user_id))
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Successfully deleted"}


class UpdateExpense(BaseModel):
    title: str | None = None 
    price: float | None = None 
    description: str | None = None 

@expense_router.patch("/{expense_id}")
async def update_expense(
    expense_id: int,
    exp: UpdateExpense,
    current_user_id: int = Depends(get_current_user),
    db = Depends(get_db)
):
    cursor = db.cursor()
    updates = []
    params = []
    if exp.title is not None:
        updates.append("title = ?")
        params.append(exp.title)
    if exp.price is not None:
        updates.append("price = ?")
        params.append(exp.price)
    if exp.description is not None:
        updates.append("description = ?")
        params.append(exp.description)

    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")

    params.extend([expense_id, current_user_id])
    cursor.execute(
        f"UPDATE expense SET {', '.join(updates)} WHERE expense_id = ? AND user_id = ?",
        params,
    )
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Updated"}

    


app.include_router(expense_router)
