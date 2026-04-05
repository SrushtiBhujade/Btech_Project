import random
import string
import uuid
from typing import List, Dict
from sqlalchemy.orm import Session
from .. import models, schemas

def generate_join_code(db: Session) -> str:
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        # Check if code already exists
        exists = db.query(models.Group).filter(models.Group.join_code == code).first()
        if not exists:
            return code

def calculate_group_balances(db: Session, group_id: str):
    # 1. Get all members of the group
    members = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.status == "ACCEPTED"
    ).all()
    
    user_map = {m.user_id: m.user.name for m in members}
    user_ids = list(user_map.keys())
    
    # 2. Initialize balances (net amount: positive means someone owes them, negative means they owe)
    # Actually, let's use: positive = "is owed", negative = "owes"
    net_balances = {uid: 0.0 for uid in user_ids}
    
    # 3. Get all group expenses
    expenses = db.query(models.GroupExpense).filter(models.GroupExpense.group_id == group_id).all()
    
    for exp in expenses:
        # Payer is owed the full amount minus their own split
        # Participants owe their split amount
        for split in exp.splits:
            if split.user_id == exp.paid_by:
                # Payer's net change: amount_paid - his_split
                net_balances[exp.paid_by] += (exp.amount - split.amount)
            else:
                # Participant's net change: -his_split
                if split.user_id in net_balances:
                    net_balances[split.user_id] -= split.amount

    # Prepare UserBalance list
    balances = [
        schemas.UserBalance(user_id=uid, user_name=user_map[uid], net_balance=round(net_balances[uid], 2))
        for uid in user_ids
    ]
    
    # 4. Simplify Debts (Greedy Algorithm)
    simplified_debts = simplify_debts(net_balances, user_map)
    
    return schemas.GroupBalanceOut(balances=balances, simplified_debts=simplified_debts)

def simplify_debts(net_balances: Dict[int, float], user_map: Dict[int, str]) -> List[schemas.DebtOut]:
    # Debtors (net negative) and Creditors (net positive)
    debtors = []
    creditors = []
    
    for uid, balance in net_balances.items():
        if balance < -0.01:
            debtors.append({'id': uid, 'amount': -balance})
        elif balance > 0.01:
            creditors.append({'id': uid, 'amount': balance})
    
    # Sort to optimize (optional, but good)
    debtors.sort(key=lambda x: x['amount'], reverse=True)
    creditors.sort(key=lambda x: x['amount'], reverse=True)
    
    debts = []
    i = 0 # debtor index
    j = 0 # creditor index
    
    while i < len(debtors) and j < len(creditors):
        d = debtors[i]
        c = creditors[j]
        
        settle_amount = min(d['amount'], c['amount'])
        
        if settle_amount > 0.01:
            debts.append(schemas.DebtOut(
                from_user_id=d['id'],
                from_user_name=user_map[d['id']],
                to_user_id=c['id'],
                to_user_name=user_map[c['id']],
                amount=round(settle_amount, 2)
            ))
        
        d['amount'] -= settle_amount
        c['amount'] -= settle_amount
        
        if d['amount'] < 0.01:
            i += 1
        if c['amount'] < 0.01:
            j += 1
            
    return debts

def calculate_group_analytics(db: Session, group_id: str) -> schemas.GroupAnalyticsOut:
    # 1. Get all expenses
    expenses = db.query(models.GroupExpense).filter(models.GroupExpense.group_id == group_id).all()
    
    # 2. Get members
    members = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.status == "ACCEPTED"
    ).all()
    user_map = {m.user_id: m.user.name for m in members}
    
    # Init metrics
    category_totals = {}
    member_paid_totals = {uid: 0.0 for uid in user_map.keys()}
    total_spend = 0.0
    
    for exp in expenses:
        total_spend += exp.amount
        
        # Category breakdown
        cat = exp.category or "Other"
        category_totals[cat] = category_totals.get(cat, 0.0) + exp.amount
        
        # Member contributions (total paid)
        if exp.paid_by in member_paid_totals:
            member_paid_totals[exp.paid_by] += exp.amount
            
    # Format category breakdown
    category_breakdown = [
        schemas.CategorySpend(category=cat, amount=round(amt, 2))
        for cat, amt in category_totals.items()
    ]
    
    # Format member contributions
    member_contributions = [
        schemas.UserContribution(user_id=uid, user_name=user_map[uid], total_paid=round(amt, 2))
        for uid, amt in member_paid_totals.items()
    ]
    
    # Sort for "Top" metrics
    top_spender = "None"
    if member_paid_totals:
        top_uid = max(member_paid_totals, key=member_paid_totals.get)
        if member_paid_totals[top_uid] > 0:
            top_spender = user_map.get(top_uid, "Unknown")
            
    top_category = "None"
    if category_totals:
        top_cat = max(category_totals, key=category_totals.get)
        top_category = top_cat

    return schemas.GroupAnalyticsOut(
        category_breakdown=category_breakdown,
        member_contributions=member_contributions,
        total_group_spend=round(total_spend, 2),
        top_spender=top_spender,
        top_category=top_category
    )
