from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import get_current_user

router = APIRouter(prefix="/budgets")


def month_range(month: str):
    try:
        year, mon = map(int, month.split("-"))
        start = date(year, mon, 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="month must look like 2026-10")
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    return start, end


@router.post("", response_model=schemas.BudgetOut)
def set_budget(
    data: schemas.BudgetSet,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    start, _ = month_range(data.month)
    month_key = start.strftime("%Y-%m")

    category = (
        db.query(models.Category)
        .filter(models.Category.id == data.category_id, models.Category.user_id == current_user.id)
        .first()
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    limit_paise = round(data.limit * 100)

    budget = (
        db.query(models.Budget)
        .filter(
            models.Budget.user_id == current_user.id,
            models.Budget.category_id == data.category_id,
            models.Budget.month == month_key,
        )
        .first()
    )
    if budget:
        budget.limit_paise = limit_paise
    else:
        budget = models.Budget(
            user_id=current_user.id,
            category_id=data.category_id,
            month=month_key,
            limit_paise=limit_paise,
        )
        db.add(budget)

    db.commit()
    db.refresh(budget)
    return {
        "id": budget.id,
        "category_id": budget.category_id,
        "month": budget.month,
        "limit": budget.limit_paise / 100,
    }


@router.get("/status", response_model=list[schemas.BudgetStatus])
def budget_status(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if month is None:
        month = date.today().strftime("%Y-%m")
    start, end = month_range(month)
    month_key = start.strftime("%Y-%m")

    budgets = (
        db.query(models.Budget)
        .filter(models.Budget.user_id == current_user.id, models.Budget.month == month_key)
        .all()
    )
    names = {
        c.id: c.name
        for c in db.query(models.Category).filter(models.Category.user_id == current_user.id).all()
    }

    rows = (
        db.query(models.Expense.category_id, func.sum(models.Expense.amount_paise))
        .filter(
            models.Expense.user_id == current_user.id,
            models.Expense.date >= start,
            models.Expense.date < end,
        )
        .group_by(models.Expense.category_id)
        .all()
    )
    spent_by_category = {category_id: total for category_id, total in rows}

    result = []
    for b in budgets:
        spent = spent_by_category.get(b.category_id, 0)
        percent = round(spent * 100 / b.limit_paise, 1)
        if percent >= 100:
            status = "exceeded"
        elif percent >= 80:
            status = "warning"
        else:
            status = "ok"

        result.append(
            {
                "category_id": b.category_id,
                "category": names.get(b.category_id, "Unknown"),
                "month": month_key,
                "limit": b.limit_paise / 100,
                "spent": spent / 100,
                "remaining": (b.limit_paise - spent) / 100,
                "percent_used": percent,
                "status": status,
            }
        )
    return result