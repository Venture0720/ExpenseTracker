from auth import app
from main import expense_router
from statistics import stats_router

app.include_router(expense_router)
app.include_router(stats_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)