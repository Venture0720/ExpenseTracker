from pydantic import BaseModel 
from fastapi import Depends, HTTPException, APIRouter
from auth import get_current_user_id, app, get_db
from typing import Optional 
import re
stats_router = APIRouter(prefix = "/statistics", tags = ["statistics"])



@stats_router.get("/summary")
async def get_statistics(
        current_user_id: int = Depends(get_current_user_id),
        db = Depends(get_db),
        month: Optional[str] = None
):
    cursor, conn = db
    if month:
        if not re.match(r'^\d{4}-\d{2}$', month):
            raise HTTPException(status_code = 400, detail = "Incorrect format of insert. Use | YYYY-MM | type of format. ")
        cursor.execute("SELECT SUM(price), COUNT(*), AVG(price) FROM expense WHERE user_id = ? AND strftime('%Y-%m', created_at) = ?", (current_user_id, month))
        
    else:
        cursor.execute("SELECT SUM(price), COUNT(*), AVG(price) FROM expense WHERE user_id = ?", (current_user_id,))

    result = cursor.fetchone()
    return {
        "total_spending": result[0] or 0,
        "expense_count": result[1] or 0,
        "average_spending": result[2] or 0,
        "period": month or "all time"
    }