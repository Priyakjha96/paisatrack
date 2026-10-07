from fastapi import FastAPI

from app import models
from app.database import Base, engine
from app.routes import auth, categories, expenses, budgets, reports  # NAYA: reports

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(expenses.router)
app.include_router(budgets.router)
app.include_router(reports.router)  # NAYA


@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Namaste {name}"}