from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    expenses = relationship("Expense", back_populates="owner")
    groups = relationship("GroupMember", back_populates="user")
    paid_expenses = relationship("GroupExpense", back_populates="payer")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Extracted from bill
    amount = Column(Float, nullable=False)
    category = Column(String, default="Other")
    vendor = Column(String, default="Unknown")
    date = Column(String, nullable=False)  # ISO format YYYY-MM-DD
    description = Column(Text, default="")

    # Raw data
    raw_text = Column(Text, default="")
    image_path = Column(String, default="")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="expenses")


class Group(Base):
    __tablename__ = "groups"

    id = Column(String, primary_key=True, index=True)  # UUID string
    name = Column(String, nullable=False)
    join_code = Column(String, unique=True, index=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("GroupMember", back_populates="group")
    expenses = relationship("GroupExpense", back_populates="group")


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    role = Column(String, default="MEMBER")  # ADMIN, MEMBER
    status = Column(String, default="PENDING")  # PENDING, ACCEPTED, REJECTED
    joined_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="groups")
    group = relationship("Group", back_populates="members")


class GroupExpense(Base):
    __tablename__ = "group_expenses"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    paid_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, default="Other")
    image_path = Column(String, default="")
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="expenses")
    payer = relationship("User", back_populates="paid_expenses")
    splits = relationship("ExpenseSplit", back_populates="expense")


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("group_expenses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)  # share of the expense

    expense = relationship("GroupExpense", back_populates="splits")
    user = relationship("User")
