from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.routes.budgets import month_range
from app.security import get_current_user

router = APIRouter(prefix="/reports")


@router.get("/summary", response_model=schemas.MonthSummary)
def summary(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if month is None:
        month = date.today().strftime("%Y-%m")
    start, end = month_range(month)
    month_key = start.strftime("%Y-%m")

    total_spent, count = (
        db.query(
            func.coalesce(func.sum(models.Expense.amount_paise), 0),
            func.count(models.Expense.id),
        )
        .filter(
            models.Expense.user_id == current_user.id,
            models.Expense.date >= start,
            models.Expense.date < end,
        )
        .one()
    )

    total_budget = (
        db.query(func.coalesce(func.sum(models.Budget.limit_paise), 0))
        .filter(models.Budget.user_id == current_user.id, models.Budget.month == month_key)
        .scalar()
    )

    return {
        "month": month_key,
        "total_spent": total_spent / 100,
        "total_budget": total_budget / 100,
        "remaining": (total_budget - total_spent) / 100,
        "expense_count": count,
    }


@router.get("/by-category", response_model=list[schemas.CategoryTotal])
def by_category(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if month is None:
        month = date.today().strftime("%Y-%m")
    start, end = month_range(month)

    rows = (
        db.query(
            models.Category.id,
            models.Category.name,
            func.sum(models.Expense.amount_paise),
        )
        .join(models.Expense, models.Expense.category_id == models.Category.id)
        .filter(
            models.Expense.user_id == current_user.id,
            models.Expense.date >= start,
            models.Expense.date < end,
        )
        .group_by(models.Category.id, models.Category.name)
        .order_by(func.sum(models.Expense.amount_paise).desc())
        .all()
    )

    grand_total = sum(total for _, _, total in rows)
    if grand_total == 0:
        return []

    return [
        {
            "category_id": category_id,
            "category": name,
            "total": total / 100,
            "percent": round(total * 100 / grand_total, 1),
        }
        for category_id, name, total in rows
    ]