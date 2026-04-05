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
    image_path: Optional[str] = ""
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


# ----------- Group -----------

class GroupCreate(BaseModel):
    name: str


class GroupUpdate(BaseModel):
    name: str


class GroupJoinRequest(BaseModel):
    join_code: str


class GroupMemberOut(BaseModel):
    user_id: int
    user_name: str
    role: str
    status: str

    class Config:
        from_attributes = True


class GroupOut(BaseModel):
    id: str
    name: str
    join_code: str
    created_by: int
    created_at: datetime
    members: list[GroupMemberOut] = []

    class Config:
        from_attributes = True


class GroupMemberAction(BaseModel):
    user_id: int
    action: str  # ACCEPT, REJECT


# ----------- Group Expense -----------

class GroupExpenseCreate(BaseModel):
    title: str
    amount: float
    category: Optional[str] = "Other"
    image_path: Optional[str] = ""
    participants: list[int]  # user_ids


class ExpenseSplitOut(BaseModel):
    user_id: int
    user_name: str
    amount: float

    class Config:
        from_attributes = True


class GroupExpenseOut(BaseModel):
    id: int
    group_id: str
    paid_by: int
    payer_name: str
    title: str
    amount: float
    category: str
    image_path: str
    date: datetime
    splits: list[ExpenseSplitOut]

    class Config:
        from_attributes = True


class DebtOut(BaseModel):
    from_user_id: int
    from_user_name: str
    to_user_id: int
    to_user_name: str
    amount: float


class UserBalance(BaseModel):
    user_id: int
    user_name: str
    net_balance: float  # positive means they are owed, negative means they owe


class GroupBalanceOut(BaseModel):
    balances: list[UserBalance]
    simplified_debts: list[DebtOut]


class CategorySpend(BaseModel):
    category: str
    amount: float


class UserContribution(BaseModel):
    user_id: int
    user_name: str
    total_paid: float


class GroupAnalyticsOut(BaseModel):
    category_breakdown: list[CategorySpend]
    member_contributions: list[UserContribution]
    total_group_spend: float
    top_spender: str
    top_category: str
