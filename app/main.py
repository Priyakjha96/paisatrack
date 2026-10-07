from pathlib import Path  # NAYA

from fastapi import FastAPI
from fastapi.responses import FileResponse  # NAYA

from app import models
from app.database import Base, engine
from app.routes import auth, categories, expenses, budgets, reports

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(expenses.router)
app.include_router(budgets.router)
app.include_router(reports.router)

STATIC_DIR = Path(__file__).parent / "static"  # NAYA


@app.get("/", include_in_schema=False)  # NAYA
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Namaste {name}"}