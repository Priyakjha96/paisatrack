import datetime as dt

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


# NAYA
class ExpenseCreate(BaseModel):
    amount: float = Field(gt=0)
    category_id: int
    note: str = ""
    date: dt.date | None = None


# NAYA
class ExpenseUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    category_id: int | None = None
    note: str | None = None
    date: dt.date | None = None


# NAYA
class ExpenseOut(BaseModel):
    id: int
    amount: float
    category_id: int
    note: str
    date: dt.date

    # NAYA
class BudgetSet(BaseModel):
    category_id: int
    month: str
    limit: float = Field(gt=0)


# NAYA
class BudgetOut(BaseModel):
    id: int
    category_id: int
    month: str
    limit: float


# NAYA
class BudgetStatus(BaseModel):
    category_id: int
    category: str
    month: str
    limit: float
    spent: float
    remaining: float
    percent_used: float
    status: str


    # NAYA
class MonthSummary(BaseModel):
    month: str
    total_spent: float
    total_budget: float
    remaining: float
    expense_count: int


# NAYA
class CategoryTotal(BaseModel):
    category_id: int
    category: str
    total: float
    percent: float