from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ----------- Auth -----------

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# ----------- Expense -----------

class ExpenseCreate(BaseModel):
    amount: float
    category: str
    vendor: str
    date: str  # YYYY-MM-DD
    description: Optional[str] = ""
    image_path: Optional[str] = None


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    vendor: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None


class ExpenseOut(BaseModel):
    id: int
    user_id: int
    amount: float
    category: str
    vendor: str
    date: str
    description: str
    image_path: str
    created_at: datetime

    class Config:
        from_attributes = True


# ----------- Analytics -----------

class MonthlyStat(BaseModel):
    month: str
    total: float
    count: int


class CategoryStat(BaseModel):
    category: str
    total: float
    count: int


class DashboardSummary(BaseModel):
    total_spent: float
    this_month: float
    total_transactions: int
    max_month: str
    max_month_amount: float
    top_category: str
    top_category_amount: float
    avg_monthly_spend: float
