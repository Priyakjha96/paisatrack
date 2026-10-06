from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import get_current_user

router = APIRouter(prefix="/expenses")


def to_out(e: models.Expense) -> dict:
    return {
        "id": e.id,
        "amount": e.amount_paise / 100,
        "category_id": e.category_id,
        "note": e.note,
        "date": e.date,
    }


def get_own_category(db: Session, user_id: int, category_id: int):
    category = (
        db.query(models.Category)
        .filter(models.Category.id == category_id, models.Category.user_id == user_id)
        .first()
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


def get_own_expense(db: Session, user_id: int, expense_id: int):
    expense = (
        db.query(models.Expense)
        .filter(models.Expense.id == expense_id, models.Expense.user_id == user_id)
        .first()
    )
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.post("", response_model=schemas.ExpenseOut)
def add_expense(
    data: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    get_own_category(db, current_user.id, data.category_id)

    expense = models.Expense(
        user_id=current_user.id,
        category_id=data.category_id,
        amount_paise=round(data.amount * 100),
        note=data.note,
        date=data.date or date.today(),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return to_out(expense)


@router.get("", response_model=list[schemas.ExpenseOut])
def list_expenses(
    month: str | None = None,
    category_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Expense).filter(models.Expense.user_id == current_user.id)

    if category_id is not None:
        query = query.filter(models.Expense.category_id == category_id)

    if month is not None:
        try:
            year, mon = map(int, month.split("-"))
            start = date(year, mon, 1)
        except ValueError:
            raise HTTPException(status_code=400, detail="month must look like 2026-10")
        end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
        query = query.filter(models.Expense.date >= start, models.Expense.date < end)

    expenses = query.order_by(models.Expense.date.desc(), models.Expense.id.desc()).all()
    return [to_out(e) for e in expenses]


@router.put("/{expense_id}", response_model=schemas.ExpenseOut)
def update_expense(
    expense_id: int,
    data: schemas.ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    expense = get_own_expense(db, current_user.id, expense_id)

    if data.category_id is not None:
        get_own_category(db, current_user.id, data.category_id)
        expense.category_id = data.category_id
    if data.amount is not None:
        expense.amount_paise = round(data.amount * 100)
    if data.note is not None:
        expense.note = data.note
    if data.date is not None:
        expense.date = data.date

    db.commit()
    db.refresh(expense)
    return to_out(expense)


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    expense = get_own_expense(db, current_user.id, expense_id)
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted"}