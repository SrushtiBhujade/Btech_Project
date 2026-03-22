import os
import shutil
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Expense, User
from ..schemas import ExpenseOut, ExpenseCreate, ExpenseUpdate
from ..routers.auth import get_current_user
from ..services.ocr_service import extract_text_from_image
from ..services.extractor import extract_fields_with_ai

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post("/upload", response_model=ExpenseOut)
async def upload_bill(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a bill image, run OCR + AI extraction, save to DB."""
    # Save file to disk
    ext = os.path.splitext(file.filename or "bill.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # OCR
    raw_text = extract_text_from_image(file_path)

    # AI Extraction
    fields = extract_fields_with_ai(raw_text)

    # Return extracted data without saving
    return {
        "id": 0,  # Temp ID since it's not in DB yet
        "user_id": current_user.id,
        "amount": fields["amount"],
        "category": fields["category"],
        "vendor": fields["vendor"],
        "date": fields["date"],
        "description": fields["description"],
        "raw_text": raw_text,
        "image_path": filename,
        "created_at": __import__("datetime").datetime.utcnow()
    }


@router.post("/manual", response_model=ExpenseOut)
def add_manual_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually add an expense (or save a confirmed uploaded bill)."""
    # Note: Using .dict() as .model_dump() isn't standard in older pydantic
    extra_fields = {}
    if hasattr(data, "image_path") and data.image_path:
        extra_fields["image_path"] = data.image_path
        
    expense = Expense(
        user_id=current_user.id,
        amount=data.amount,
        category=data.category,
        vendor=data.vendor,
        date=data.date,
        description=data.description or "",
        **extra_fields
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/", response_model=List[ExpenseOut])
def list_expenses(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all expenses for the current user with optional filters."""
    query = db.query(Expense).filter(Expense.user_id == current_user.id)

    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    if category:
        query = query.filter(Expense.category == category)

    return query.order_by(Expense.date.desc()).all()


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id, Expense.user_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id, Expense.user_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Also remove image file
    if expense.image_path:
        img_path = os.path.join(UPLOAD_DIR, expense.image_path)
        if os.path.exists(img_path):
            os.remove(img_path)

    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}
