import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Group, GroupMember, GroupExpense, ExpenseSplit
from ..schemas import (
    GroupCreate, GroupUpdate, GroupOut, GroupJoinRequest, GroupMemberOut, 
    GroupMemberAction, GroupExpenseCreate, GroupExpenseOut, 
    GroupBalanceOut, ExpenseSplitOut, GroupAnalyticsOut
)
from .auth import get_current_user
from ..services import group_service

router = APIRouter(prefix="/groups", tags=["Groups"])

@router.post("/create", response_model=GroupOut)
def create_group(
    group_in: GroupCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    group_id = str(uuid.uuid4())
    join_code = group_service.generate_join_code(db)
    
    group = Group(
        id=group_id,
        name=group_in.name,
        join_code=join_code,
        created_by=current_user.id
    )
    db.add(group)
    
    # Add creator as ADMIN member
    member = GroupMember(
        user_id=current_user.id,
        group_id=group_id,
        role="ADMIN",
        status="ACCEPTED"
    )
    db.add(member)
    
    db.commit()
    db.refresh(group)
    return group

@router.put("/{group_id}", response_model=GroupOut)
def update_group(
    group_id: str,
    group_in: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Only Admin (creator or check role) can update
    # Simple check for now: only creator or ADMIN role
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    if not member or member.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admins can update group.")
    
    group.name = group_in.name
    db.commit()
    db.refresh(group)
    return group

@router.delete("/{group_id}")
def delete_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    if not member or member.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admins can delete group.")
    
    # Delete related splits, expenses, members
    # Since we don't have cascade delete set up in models, we'll do it manually or assume sqlite handles it if configured
    # To be safe, manual delete
    db.query(ExpenseSplit).filter(ExpenseSplit.expense_id.in_(
        db.query(GroupExpense.id).filter(GroupExpense.group_id == group_id)
    )).delete(synchronize_session=False)
    
    db.query(GroupExpense).filter(GroupExpense.group_id == group_id).delete(synchronize_session=False)
    db.query(GroupMember).filter(GroupMember.group_id == group_id).delete(synchronize_session=False)
    db.delete(group)
    db.commit()
    return {"message": "Group deleted successfully"}

@router.get("/me", response_model=List[GroupOut])
def get_my_groups(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Get all groups where user is an ACCEPTED member
    memberships = db.query(GroupMember).filter(
        GroupMember.user_id == current_user.id,
        GroupMember.status == "ACCEPTED"
    ).all()
    
    res = []
    for m in memberships:
        group = m.group
        members_out = [
            GroupMemberOut(
                user_id=gm.user_id,
                user_name=gm.user.name,
                role=gm.role,
                status=gm.status
            ) for gm in group.members
        ]
        res.append(GroupOut(
            id=group.id,
            name=group.name,
            join_code=group.join_code,
            created_by=group.created_by,
            created_at=group.created_at,
            members=members_out
        ))
    return res

@router.post("/join", response_model=GroupMemberOut)
def join_group(
    join_req: GroupJoinRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    group = db.query(Group).filter(Group.join_code == join_req.join_code).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if already a member
    existing = db.query(GroupMember).filter(
        GroupMember.group_id == group.id,
        GroupMember.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already a member or request pending")
    
    member = GroupMember(
        user_id=current_user.id,
        group_id=group.id,
        role="MEMBER",
        status="PENDING"
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return GroupMemberOut(
        user_id=member.user_id,
        user_name=current_user.name,
        role=member.role,
        status=member.status
    )

@router.get("/{group_id}", response_model=GroupOut)
def get_group_details(
    group_id: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if user is a member
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.status == "ACCEPTED"
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    # Map members to include names
    members_out = []
    for m in group.members:
        members_out.append(GroupMemberOut(
            user_id=m.user_id,
            user_name=m.user.name,
            role=m.role,
            status=m.status
        ))
    
    return GroupOut(
        id=group.id,
        name=group.name,
        join_code=group.join_code,
        created_by=group.created_by,
        created_at=group.created_at,
        members=members_out
    )

@router.post("/{group_id}/accept-user", response_model=GroupMemberOut)
def manage_member(
    group_id: str,
    action_in: GroupMemberAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if current user is ADMIN
    admin_member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.role == "ADMIN"
    ).first()
    if not admin_member:
        raise HTTPException(status_code=403, detail="Only admins can manage members")
    
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == action_in.user_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Pending request not found")
    
    if action_in.action == "ACCEPT":
        member.status = "ACCEPTED"
    elif action_in.action == "REJECT":
        member.status = "REJECTED"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    db.commit()
    db.refresh(member)
    
    return GroupMemberOut(
        user_id=member.user_id,
        user_name=member.user.name,
        role=member.role,
        status=member.status
    )

@router.delete("/{group_id}/members/{user_id}")
def remove_member(
    group_id: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if current user is ADMIN or the user being removed
    admin_member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.role == "ADMIN"
    ).first()
    
    if not admin_member and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Only admins can remove members")
    
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Cannot remove the last admin? (Optional safety)
    if member.role == "ADMIN":
        admins_count = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.role == "ADMIN"
        ).count()
        if admins_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last admin of a group")

    db.delete(member)
    db.commit()
    return {"message": "Member removed successfully"}

@router.post("/{group_id}/expenses", response_model=GroupExpenseOut)
def add_group_expense(
    group_id: str,
    expense_in: GroupExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is accepted member
    me = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.status == "ACCEPTED"
    ).first()
    if not me:
        raise HTTPException(status_code=403, detail="Must be an accepted member")
    
    # Calculate split (equal by default)
    n = len(expense_in.participants)
    if n == 0:
        raise HTTPException(status_code=400, detail="Must have at least one participant")
    
    split_amount = expense_in.amount / n
    
    expense = GroupExpense(
        group_id=group_id,
        paid_by=current_user.id,
        title=expense_in.title,
        amount=expense_in.amount,
        category=expense_in.category or "Other",
        image_path=expense_in.image_path or ""
    )
    db.add(expense)
    db.flush() # Get expense id
    
    for uid in expense_in.participants:
        split = ExpenseSplit(
            expense_id=expense.id,
            user_id=uid,
            amount=split_amount
        )
        db.add(split)
    
    db.commit()
    db.refresh(expense)
    
    # Map to Out schema
    splits_out = [
        ExpenseSplitOut(user_id=s.user_id, user_name=s.user.name, amount=s.amount)
        for s in expense.splits
    ]
    
    return GroupExpenseOut(
        id=expense.id,
        group_id=expense.group_id,
        paid_by=expense.paid_by,
        payer_name=current_user.name,
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        image_path=expense.image_path,
        date=expense.date,
        splits=splits_out
    )

@router.get("/{group_id}/expenses", response_model=List[GroupExpenseOut])
def get_group_expenses(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check membership
    me = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.status == "ACCEPTED"
    ).first()
    if not me:
        raise HTTPException(status_code=403, detail="Access denied")
    
    expenses = db.query(models.GroupExpense).filter(
        models.GroupExpense.group_id == group_id
    ).order_by(models.GroupExpense.created_at.desc()).all()
    
    res = []
    for exp in expenses:
        splits_out = [
            ExpenseSplitOut(user_id=s.user_id, user_name=s.user.name, amount=s.amount)
            for s in exp.splits
        ]
        res.append(GroupExpenseOut(
            id=exp.id,
            group_id=exp.group_id,
            paid_by=exp.paid_by,
            payer_name=exp.payer.name,
            title=exp.title,
            amount=exp.amount,
            category=exp.category,
            image_path=exp.image_path,
            date=exp.date,
            splits=splits_out
        ))
    return res

@router.get("/{group_id}/balances", response_model=GroupBalanceOut)
def get_group_balances(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check membership
    me = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.status == "ACCEPTED"
    ).first()
    if not me:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return group_service.calculate_group_balances(db, group_id)

@router.get("/{group_id}/analytics", response_model=GroupAnalyticsOut)
def get_group_analytics(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check membership
    me = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.status == "ACCEPTED"
    ).first()
    if not me:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return group_service.calculate_group_analytics(db, group_id)
