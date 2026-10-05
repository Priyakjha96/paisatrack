from fastapi import FastAPI

from app import models
from app.database import Base, engine
from app.routes import auth, categories

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)
app.include_router(categories.router)


@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Namaste {name}"}