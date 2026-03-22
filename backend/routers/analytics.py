from collections import defaultdict
from datetime import datetime, date, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Expense, User
from ..schemas import DashboardSummary
from ..routers.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _get_user_expenses(db: Session, user_id: int):
    return db.query(Expense).filter(Expense.user_id == user_id).all()


@router.get("/monthly")
def monthly_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return spending totals grouped by month (YYYY-MM)."""
    expenses = _get_user_expenses(db, current_user.id)
    monthly = defaultdict(lambda: {"total": 0.0, "count": 0})
    for e in expenses:
        key = e.date[:7]  # YYYY-MM
        monthly[key]["total"] += e.amount
        monthly[key]["count"] += 1
    result = sorted(
        [{"month": k, "total": round(v["total"], 2), "count": v["count"]} for k, v in monthly.items()],
        key=lambda x: x["month"]
    )
    return result


@router.get("/weekly")
def weekly_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return spending grouped by ISO week (last 12 weeks)."""
    expenses = _get_user_expenses(db, current_user.id)
    cutoff = (date.today() - timedelta(weeks=12)).isoformat()
    recent = [e for e in expenses if e.date >= cutoff]

    weekly = defaultdict(lambda: {"total": 0.0, "count": 0})
    for e in recent:
        try:
            d = datetime.strptime(e.date, "%Y-%m-%d").date()
            week_key = f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"
        except ValueError:
            week_key = "Unknown"
        weekly[week_key]["total"] += e.amount
        weekly[week_key]["count"] += 1

    result = sorted(
        [{"week": k, "total": round(v["total"], 2), "count": v["count"]} for k, v in weekly.items()],
        key=lambda x: x["week"]
    )
    return result


@router.get("/yearly")
def yearly_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return spending grouped by year."""
    expenses = _get_user_expenses(db, current_user.id)
    yearly = defaultdict(lambda: {"total": 0.0, "count": 0})
    for e in expenses:
        key = e.date[:4]
        yearly[key]["total"] += e.amount
        yearly[key]["count"] += 1
    return sorted(
        [{"year": k, "total": round(v["total"], 2), "count": v["count"]} for k, v in yearly.items()],
        key=lambda x: x["year"]
    )


@router.get("/category")
def category_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return spending grouped by category."""
    expenses = _get_user_expenses(db, current_user.id)
    cats = defaultdict(lambda: {"total": 0.0, "count": 0})
    for e in expenses:
        cats[e.category]["total"] += e.amount
        cats[e.category]["count"] += 1
    return sorted(
        [{"category": k, "total": round(v["total"], 2), "count": v["count"]} for k, v in cats.items()],
        key=lambda x: x["total"],
        reverse=True
    )


@router.get("/vendors")
def vendor_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return top 10 vendors by spending."""
    expenses = _get_user_expenses(db, current_user.id)
    vendors = defaultdict(lambda: {"total": 0.0, "count": 0})
    for e in expenses:
        vendors[e.vendor]["total"] += e.amount
        vendors[e.vendor]["count"] += 1
    sorted_vendors = sorted(vendors.items(), key=lambda x: x[1]["total"], reverse=True)[:10]
    return [{"vendor": k, "total": round(v["total"], 2), "count": v["count"]} for k, v in sorted_vendors]


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return key stats for the dashboard overview cards."""
    expenses = _get_user_expenses(db, current_user.id)

    if not expenses:
        return DashboardSummary(
            total_spent=0, this_month=0, total_transactions=0,
            max_month="N/A", max_month_amount=0,
            top_category="N/A", top_category_amount=0, avg_monthly_spend=0
        )

    total_spent = sum(e.amount for e in expenses)
    current_month = date.today().strftime("%Y-%m")
    this_month = sum(e.amount for e in expenses if e.date.startswith(current_month))

    # Monthly aggregation
    monthly = defaultdict(float)
    for e in expenses:
        monthly[e.date[:7]] += e.amount

    max_month = max(monthly, key=monthly.get) if monthly else "N/A"
    max_month_amount = monthly.get(max_month, 0)
    avg_monthly = total_spent / len(monthly) if monthly else 0

    # Category aggregation
    cats = defaultdict(float)
    for e in expenses:
        cats[e.category] += e.amount

    top_category = max(cats, key=cats.get) if cats else "N/A"
    top_category_amount = cats.get(top_category, 0)

    return DashboardSummary(
        total_spent=round(total_spent, 2),
        this_month=round(this_month, 2),
        total_transactions=len(expenses),
        max_month=max_month,
        max_month_amount=round(max_month_amount, 2),
        top_category=top_category,
        top_category_amount=round(top_category_amount, 2),
        avg_monthly_spend=round(avg_monthly, 2),
    )
