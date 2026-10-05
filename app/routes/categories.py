from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import get_current_user

router = APIRouter(prefix="/categories")


@router.post("", response_model=schemas.CategoryOut)
def create_category(
    data: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = (
        db.query(models.Category)
        .filter(models.Category.user_id == current_user.id, models.Category.name == data.name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    category = models.Category(user_id=current_user.id, name=data.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("", response_model=list[schemas.CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Category).filter(models.Category.user_id == current_user.id).all()