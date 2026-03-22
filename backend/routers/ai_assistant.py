from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import Expense, User
from ..routers.auth import get_current_user
from ..services import ai_service

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []


@router.get("/summarize")
def summarize(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Summarize user's expenses for the past N days."""
    from datetime import date, timedelta
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.date >= cutoff
    ).order_by(Expense.date.desc()).all()

    expense_list = [
        {"date": e.date, "amount": e.amount, "category": e.category,
         "vendor": e.vendor, "description": e.description}
        for e in expenses
    ]
    summary = ai_service.summarize_expenses(expense_list)
    return {"summary": summary, "expense_count": len(expenses), "days": days}


@router.get("/recommend")
def recommend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get personalized saving recommendations."""
    from .analytics import dashboard_summary, category_analytics
    expenses = db.query(Expense).filter(Expense.user_id == current_user.id).all()

    expense_list = [
        {"date": e.date, "amount": e.amount, "category": e.category,
         "vendor": e.vendor, "description": e.description}
        for e in expenses
    ]

    # Build stats
    from collections import defaultdict
    cats = defaultdict(float)
    for e in expenses:
        cats[e.category] += e.amount

    stats = {
        "total_spent": round(sum(e.amount for e in expenses), 2),
        "total_transactions": len(expenses),
        "top_categories": dict(sorted(cats.items(), key=lambda x: x[1], reverse=True)[:5])
    }

    recommendations = ai_service.get_recommendations(expense_list, stats)
    return {"recommendations": recommendations}


@router.post("/chat")
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Free-form chat with AI about expenses."""
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id
    ).order_by(Expense.date.desc()).limit(100).all()

    expense_list = [
        {"date": e.date, "amount": e.amount, "category": e.category,
         "vendor": e.vendor, "description": e.description}
        for e in expenses
    ]

    reply = ai_service.chat_with_expenses(req.message, expense_list, req.history or [])
    return {"reply": reply}
