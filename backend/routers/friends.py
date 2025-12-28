"""Friends router: manage friend relationships."""

from typing import Annotated
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

import models
import schemas
from database import get_db
from dependencies import get_current_user
from utils.validation import get_user_by_email


router = APIRouter(prefix="/friends", tags=["friends"])


def verify_friendship(db: Session, current_user_id: int, friend_id: int) -> models.User:
    """Verify that a friendship exists between current user and friend_id.
    Returns the friend user object if friendship exists, raises 404 otherwise.
    """
    friendship = db.query(models.Friendship).filter(
        or_(
            and_(models.Friendship.user_id1 == current_user_id, models.Friendship.user_id2 == friend_id),
            and_(models.Friendship.user_id1 == friend_id, models.Friendship.user_id2 == current_user_id)
        )
    ).first()

    if not friendship:
        raise HTTPException(status_code=404, detail="Friend not found")

    friend = db.query(models.User).filter(models.User.id == friend_id).first()
    if not friend:
        raise HTTPException(status_code=404, detail="Friend not found")

    return friend


@router.post("", response_model=schemas.Friend)
def add_friend(
    friend_request: schemas.FriendRequest, 
    current_user: Annotated[models.User, Depends(get_current_user)], 
    db: Session = Depends(get_db)
):
    friend_user = get_user_by_email(db, friend_request.email)
    if not friend_user:
        raise HTTPException(status_code=404, detail="User not found")

    if friend_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself as friend")

    # Check if already friends
    existing = db.query(models.Friendship).filter(
        ((models.Friendship.user_id1 == current_user.id) & (models.Friendship.user_id2 == friend_user.id)) |
        ((models.Friendship.user_id1 == friend_user.id) & (models.Friendship.user_id2 == current_user.id))
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already friends")

    new_friendship = models.Friendship(user_id1=current_user.id, user_id2=friend_user.id)
    db.add(new_friendship)
    db.commit()

    return friend_user


@router.get("", response_model=list[schemas.Friend])
def read_friends(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    # Find all friendships involving current_user
    friendships = db.query(models.Friendship).filter(
        (models.Friendship.user_id1 == current_user.id) | (models.Friendship.user_id2 == current_user.id)
    ).all()

    friends = []
    for f in friendships:
        friend_id = f.user_id2 if f.user_id1 == current_user.id else f.user_id1
        friend = db.query(models.User).filter(models.User.id == friend_id).first()
        if friend:
            friends.append(friend)

    return friends


@router.get("/{friend_id}", response_model=schemas.Friend)
def get_friend(
    friend_id: int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Get details of a specific friend."""
    friend = verify_friendship(db, current_user.id, friend_id)
    return friend


@router.get("/{friend_id}/expenses", response_model=list[schemas.FriendExpenseWithSplits])
def get_friend_expenses(
    friend_id: int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Get all expenses shared between current user and a friend.
    Includes both group expenses and direct (non-group) expenses.
    """
    friend = verify_friendship(db, current_user.id, friend_id)

    # Find expenses where BOTH users are participants (via splits or as payer)
    # Subquery for expenses where current user is in splits
    current_user_split_expenses = db.query(models.ExpenseSplit.expense_id).filter(
        models.ExpenseSplit.user_id == current_user.id,
        models.ExpenseSplit.is_guest == False
    ).subquery()

    # Subquery for expenses where friend is in splits
    friend_split_expenses = db.query(models.ExpenseSplit.expense_id).filter(
        models.ExpenseSplit.user_id == friend_id,
        models.ExpenseSplit.is_guest == False
    ).subquery()

    # Find expenses where both are involved (either as payer or in splits)
    expenses = db.query(models.Expense).filter(
        or_(
            # Current user is payer AND friend is in splits
            and_(
                models.Expense.payer_id == current_user.id,
                models.Expense.payer_is_guest == False,
                models.Expense.id.in_(friend_split_expenses)
            ),
            # Friend is payer AND current user is in splits
            and_(
                models.Expense.payer_id == friend_id,
                models.Expense.payer_is_guest == False,
                models.Expense.id.in_(current_user_split_expenses)
            ),
            # Both are in splits of the same expense
            and_(
                models.Expense.id.in_(current_user_split_expenses),
                models.Expense.id.in_(friend_split_expenses)
            )
        )
    ).order_by(models.Expense.date.desc(), models.Expense.id.desc()).all()

    result = []
    for expense in expenses:
        # Get splits with user names
        splits = db.query(models.ExpenseSplit).filter(
            models.ExpenseSplit.expense_id == expense.id
        ).all()

        splits_with_names = []
        for split in splits:
            if split.is_guest:
                guest = db.query(models.GuestMember).filter(models.GuestMember.id == split.user_id).first()
                user_name = guest.name if guest else "Unknown Guest"
            else:
                user = db.query(models.User).filter(models.User.id == split.user_id).first()
                user_name = (user.full_name or user.email) if user else "Unknown User"

            splits_with_names.append(schemas.ExpenseSplitDetail(
                id=split.id,
                expense_id=split.expense_id,
                user_id=split.user_id,
                is_guest=split.is_guest,
                amount_owed=split.amount_owed,
                percentage=split.percentage,
                shares=split.shares,
                user_name=user_name
            ))

        # Get group name if expense is in a group
        group_name = None
        if expense.group_id:
            group = db.query(models.Group).filter(models.Group.id == expense.group_id).first()
            group_name = group.name if group else None

        # Load items for ITEMIZED expenses
        items_data = []
        split_type = expense.split_type or "EQUAL"
        if split_type == "ITEMIZED":
            expense_items = db.query(models.ExpenseItem).filter(
                models.ExpenseItem.expense_id == expense.id
            ).all()

            for item in expense_items:
                assignments = db.query(models.ExpenseItemAssignment).filter(
                    models.ExpenseItemAssignment.expense_item_id == item.id
                ).all()

                assignment_details = []
                for a in assignments:
                    if a.is_guest:
                        guest = db.query(models.GuestMember).filter(
                            models.GuestMember.id == a.user_id
                        ).first()
                        name = guest.name if guest else "Unknown Guest"
                    else:
                        user = db.query(models.User).filter(
                            models.User.id == a.user_id
                        ).first()
                        name = (user.full_name or user.email) if user else "Unknown"

                    assignment_details.append(schemas.ExpenseItemAssignmentDetail(
                        user_id=a.user_id,
                        is_guest=a.is_guest,
                        user_name=name
                    ))

                items_data.append(schemas.ExpenseItemDetail(
                    id=item.id,
                    expense_id=item.expense_id,
                    description=item.description,
                    price=item.price,
                    is_tax_tip=item.is_tax_tip,
                    assignments=assignment_details
                ))

        result.append(schemas.FriendExpenseWithSplits(
            id=expense.id,
            description=expense.description,
            amount=expense.amount,
            currency=expense.currency,
            date=expense.date,
            payer_id=expense.payer_id,
            payer_is_guest=expense.payer_is_guest,
            group_id=expense.group_id,
            created_by_id=expense.created_by_id,
            splits=splits_with_names,
            split_type=split_type,
            items=items_data,
            icon=expense.icon,
            receipt_image_path=expense.receipt_image_path,
            notes=expense.notes,
            group_name=group_name
        ))

    return result


@router.get("/{friend_id}/balance", response_model=list[schemas.FriendBalance])
def get_friend_balance(
    friend_id: int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Calculate the net balance between current user and a friend.
    Positive amount = friend owes you, Negative = you owe friend.
    Returns a list of balances grouped by currency.
    """
    friend = verify_friendship(db, current_user.id, friend_id)

    # Get all expenses shared between the two users
    # Reuse the same query logic from get_friend_expenses
    current_user_split_expenses = db.query(models.ExpenseSplit.expense_id).filter(
        models.ExpenseSplit.user_id == current_user.id,
        models.ExpenseSplit.is_guest == False
    ).subquery()

    friend_split_expenses = db.query(models.ExpenseSplit.expense_id).filter(
        models.ExpenseSplit.user_id == friend_id,
        models.ExpenseSplit.is_guest == False
    ).subquery()

    expenses = db.query(models.Expense).filter(
        or_(
            and_(
                models.Expense.payer_id == current_user.id,
                models.Expense.payer_is_guest == False,
                models.Expense.id.in_(friend_split_expenses)
            ),
            and_(
                models.Expense.payer_id == friend_id,
                models.Expense.payer_is_guest == False,
                models.Expense.id.in_(current_user_split_expenses)
            ),
            and_(
                models.Expense.id.in_(current_user_split_expenses),
                models.Expense.id.in_(friend_split_expenses)
            )
        )
    ).all()

    # Calculate balance per currency
    # Positive = friend owes current user, Negative = current user owes friend
    balances: dict[str, float] = defaultdict(float)

    for expense in expenses:
        currency = expense.currency

        # Get splits for this expense
        splits = db.query(models.ExpenseSplit).filter(
            models.ExpenseSplit.expense_id == expense.id
        ).all()

        # Find what the friend owes in this expense
        friend_split = next(
            (s for s in splits if s.user_id == friend_id and not s.is_guest),
            None
        )
        # Find what current user owes in this expense
        current_user_split = next(
            (s for s in splits if s.user_id == current_user.id and not s.is_guest),
            None
        )

        if expense.payer_id == current_user.id and not expense.payer_is_guest:
            # Current user paid - friend owes their split amount
            if friend_split:
                balances[currency] += friend_split.amount_owed / 100.0

        elif expense.payer_id == friend_id and not expense.payer_is_guest:
            # Friend paid - current user owes their split amount
            if current_user_split:
                balances[currency] -= current_user_split.amount_owed / 100.0

    # Convert to list of FriendBalance objects, excluding zero balances
    result = [
        schemas.FriendBalance(amount=amount, currency=currency)
        for currency, amount in balances.items()
        if abs(amount) > 0.01  # Filter out near-zero balances
    ]

    # Sort by currency for consistent ordering
    result.sort(key=lambda x: x.currency)

    return result
