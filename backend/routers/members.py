"""Members router: manage group members and guests."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from dependencies import get_current_user
from utils.validation import get_group_or_404, verify_group_membership, get_user_by_email


router = APIRouter(prefix="/groups/{group_id}", tags=["members"])


@router.post("/members", response_model=schemas.GroupMember)
def add_group_member(
    group_id: int, 
    member_add: schemas.GroupMemberAdd, 
    current_user: Annotated[models.User, Depends(get_current_user)], 
    db: Session = Depends(get_db)
):
    get_group_or_404(db, group_id)
    verify_group_membership(db, group_id, current_user.id)

    # Find user by email
    user = get_user_by_email(db, member_add.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already a member
    existing = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this group")

    # Add member
    new_member = models.GroupMember(group_id=group_id, user_id=user.id)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return schemas.GroupMember(
        id=new_member.id,
        user_id=user.id,
        full_name=user.full_name or user.email,
        email=user.email
    )


@router.delete("/members/{user_id}")
def remove_group_member(
    group_id: int, 
    user_id: int, 
    current_user: Annotated[models.User, Depends(get_current_user)], 
    db: Session = Depends(get_db)
):
    group = get_group_or_404(db, group_id)
    verify_group_membership(db, group_id, current_user.id)

    # Owner can remove anyone except themselves
    # Non-owners can only remove themselves
    if current_user.id != group.created_by_id and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only remove yourself from the group")

    if user_id == group.created_by_id:
        raise HTTPException(status_code=400, detail="Group owner cannot be removed. Delete the group instead.")

    member = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this group")

    # Auto-unlink any guests managed by this user
    db.query(models.GuestMember).filter(
        models.GuestMember.group_id == group_id,
        models.GuestMember.managed_by_id == user_id,
        models.GuestMember.managed_by_type == 'user'
    ).update({"managed_by_id": None, "managed_by_type": None})

    # Auto-unlink any members managed by this user
    db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.managed_by_id == user_id,
        models.GroupMember.managed_by_type == 'user'
    ).update({"managed_by_id": None, "managed_by_type": None})

    db.delete(member)
    db.commit()

    return {"message": "Member removed successfully"}


@router.post("/guests", response_model=schemas.GuestMember)
def add_guest(
    group_id: int,
    guest: schemas.GuestMemberCreate,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    get_group_or_404(db, group_id)
    verify_group_membership(db, group_id, current_user.id)

    db_guest = models.GuestMember(
        group_id=group_id,
        name=guest.name,
        created_by_id=current_user.id
    )
    db.add(db_guest)
    db.commit()
    db.refresh(db_guest)
    return db_guest


@router.get("/unknown-guest", response_model=schemas.GuestMember)
def get_or_create_unknown_guest(
    group_id: int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Get or create the special 'Unknown' placeholder guest for a group.

    This allows items to be assigned to an 'Unknown' participant that can
    be claimed later by any group member.
    """
    get_group_or_404(db, group_id)
    verify_group_membership(db, group_id, current_user.id)

    # Check if unknown guest already exists for this group
    unknown_guest = db.query(models.GuestMember).filter(
        models.GuestMember.group_id == group_id,
        models.GuestMember.is_unknown_placeholder == True
    ).first()

    if unknown_guest:
        return unknown_guest

    # Create new unknown guest
    unknown_guest = models.GuestMember(
        group_id=group_id,
        name="Unknown",
        created_by_id=current_user.id,
        is_unknown_placeholder=True
    )
    db.add(unknown_guest)
    db.commit()
    db.refresh(unknown_guest)
    return unknown_guest


@router.delete("/guests/{guest_id}")
def remove_guest(
    group_id: int, 
    guest_id: int, 
    current_user: Annotated[models.User, Depends(get_current_user)], 
    db: Session = Depends(get_db)
):
    get_group_or_404(db, group_id)
    verify_group_membership(db, group_id, current_user.id)

    guest = db.query(models.GuestMember).filter(
        models.GuestMember.id == guest_id,
        models.GuestMember.group_id == group_id
    ).first()

    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found in this group")

    # Delete all expense splits involving this guest
    db.query(models.ExpenseSplit).filter(
        models.ExpenseSplit.user_id == guest_id,
        models.ExpenseSplit.is_guest == True
    ).delete()

    # Delete all expenses where this guest was the payer
    db.query(models.Expense).filter(
        models.Expense.payer_id == guest_id,
        models.Expense.payer_is_guest == True
    ).delete()

    # Now delete the guest
    db.delete(guest)
    db.commit()

    return {"message": "Guest removed successfully"}


@router.post("/guests/{guest_id}/claim")
def claim_guest(
    group_id: int,
    guest_id: int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    get_group_or_404(db, group_id)

    guest = db.query(models.GuestMember).filter(
        models.GuestMember.id == guest_id,
        models.GuestMember.group_id == group_id
    ).first()

    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    if guest.is_unknown_placeholder:
        raise HTTPException(status_code=400, detail="Cannot claim the Unknown placeholder. Use claim-unknown-items to claim specific items.")

    if guest.claimed_by_id:
        raise HTTPException(status_code=400, detail="Guest already claimed")

    # Transfer expenses where guest was payer
    expenses_updated = db.query(models.Expense).filter(
        models.Expense.payer_id == guest_id,
        models.Expense.payer_is_guest == True
    ).update({
        "payer_id": current_user.id,
        "payer_is_guest": False
    })

    # Transfer splits where guest was involved
    splits_updated = db.query(models.ExpenseSplit).filter(
        models.ExpenseSplit.user_id == guest_id,
        models.ExpenseSplit.is_guest == True
    ).update({
        "user_id": current_user.id,
        "is_guest": False
    })

    # Transfer item assignments where guest was assigned
    db.query(models.ExpenseItemAssignment).filter(
        models.ExpenseItemAssignment.user_id == guest_id,
        models.ExpenseItemAssignment.is_guest == True
    ).update({
        "user_id": current_user.id,
        "is_guest": False
    })

    # Update any guests that were managed by this guest to be managed by the new user
    managed_guests_updated = db.query(models.GuestMember).filter(
        models.GuestMember.managed_by_id == guest_id,
        models.GuestMember.managed_by_type == 'guest'
    ).update({
        "managed_by_id": current_user.id,
        "managed_by_type": 'user'
    })

    # Update any members that were managed by this guest to be managed by the new user
    managed_members_updated = db.query(models.GroupMember).filter(
        models.GroupMember.managed_by_id == guest_id,
        models.GroupMember.managed_by_type == 'guest'
    ).update({
        "managed_by_id": current_user.id,
        "managed_by_type": 'user'
    })

    # Mark guest as claimed
    guest.claimed_by_id = current_user.id

    # Add user to group if not already member
    existing_member = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == current_user.id
    ).first()

    if not existing_member:
        new_member = models.GroupMember(group_id=group_id, user_id=current_user.id)

        # If this guest was being managed by another guest, check if that manager has been claimed
        # If so, update the new member to be managed by the manager's new user ID
        if guest.managed_by_id and guest.managed_by_type == 'guest':
            manager_guest = db.query(models.GuestMember).filter(
                models.GuestMember.id == guest.managed_by_id
            ).first()
            if manager_guest and manager_guest.claimed_by_id:
                # Manager guest was claimed, update to point to the user who claimed it
                new_member.managed_by_id = manager_guest.claimed_by_id
                new_member.managed_by_type = 'user'
            else:
                # Manager guest not claimed yet, keep the guest reference
                new_member.managed_by_id = guest.managed_by_id
                new_member.managed_by_type = 'guest'
        elif guest.managed_by_id and guest.managed_by_type == 'user':
            # Already managed by a user, preserve that relationship
            new_member.managed_by_id = guest.managed_by_id
            new_member.managed_by_type = 'user'

        db.add(new_member)

    # Clear the guest's managed_by fields to prevent double-counting in balance calculations
    # The management relationship has been transferred to the GroupMember above
    guest.managed_by_id = None
    guest.managed_by_type = None

    db.commit()

    return {
        "message": "Guest claimed successfully",
        "transferred_expenses": expenses_updated,
        "transferred_splits": splits_updated,
        "managed_guests_updated": managed_guests_updated,
        "managed_members_updated": managed_members_updated
    }


@router.post("/guests/{guest_id}/manage")
def manage_guest(
    group_id: int,
    guest_id: int,
    request: schemas.ManageGuestRequest,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Link a guest to a manager (user or guest) for aggregated balance tracking"""
    get_group_or_404(db, group_id)
    verify_group_membership(db, group_id, current_user.id)

    # Get the guest
    guest = db.query(models.GuestMember).filter(
        models.GuestMember.id == guest_id,
        models.GuestMember.group_id == group_id
    ).first()

    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    # Cannot manage a claimed guest
    if guest.claimed_by_id:
        raise HTTPException(status_code=400, detail="Cannot manage a claimed guest")
    
    # Cannot manage yourself
    if request.is_guest and request.user_id == guest_id:
        raise HTTPException(status_code=400, detail="Guest cannot manage itself")

    # Verify manager exists and is in the group
    if request.is_guest:
        # Manager is a guest - verify it exists and is in this group
        manager_guest = db.query(models.GuestMember).filter(
            models.GuestMember.id == request.user_id,
            models.GuestMember.group_id == group_id,
            models.GuestMember.claimed_by_id == None  # Cannot use claimed guests as managers
        ).first()
        if not manager_guest:
            raise HTTPException(status_code=400, detail="Manager guest not found or already claimed")
        managed_by_name = manager_guest.name
    else:
        # Manager is a user - verify they are a group member
        manager_membership = db.query(models.GroupMember).filter(
            models.GroupMember.group_id == group_id,
            models.GroupMember.user_id == request.user_id
        ).first()
        if not manager_membership:
            raise HTTPException(status_code=400, detail="Manager must be a group member")
        manager = db.query(models.User).filter(models.User.id == request.user_id).first()
        managed_by_name = manager.full_name or manager.email if manager else None

    # Update guest's manager
    guest.managed_by_id = request.user_id
    guest.managed_by_type = 'guest' if request.is_guest else 'user'
    db.commit()
    db.refresh(guest)

    return {
        "message": "Guest manager updated successfully",
        "guest": schemas.GuestMember(
            id=guest.id,
            group_id=guest.group_id,
            name=guest.name,
            created_by_id=guest.created_by_id,
            claimed_by_id=guest.claimed_by_id,
            managed_by_id=guest.managed_by_id,
            managed_by_type=guest.managed_by_type,
            managed_by_name=managed_by_name
        )
    }


@router.delete("/guests/{guest_id}/manage")
def unmanage_guest(
    group_id: int,
    guest_id: int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Remove guest's manager link"""
    get_group_or_404(db, group_id)
    verify_group_membership(db, group_id, current_user.id)

    guest = db.query(models.GuestMember).filter(
        models.GuestMember.id == guest_id,
        models.GuestMember.group_id == group_id
    ).first()

    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    # Remove manager link
    guest.managed_by_id = None
    guest.managed_by_type = None
    db.commit()

    return {"message": "Guest manager removed successfully"}


@router.post("/members/{member_user_id}/manage")
def manage_member(
    group_id: int,
    member_user_id: int,
    request: schemas.ManageGuestRequest,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Link a registered member to a manager (user or guest) for aggregated balance tracking"""
    get_group_or_404(db, group_id)
    verify_group_membership(db, group_id, current_user.id)

    # Get the member
    member = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == member_user_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Cannot manage yourself
    if not request.is_guest and request.user_id == member_user_id:
        raise HTTPException(status_code=400, detail="Member cannot manage themselves")

    # Verify manager exists and is in the group
    if request.is_guest:
        # Manager is a guest - verify it exists and is in this group
        manager_guest = db.query(models.GuestMember).filter(
            models.GuestMember.id == request.user_id,
            models.GuestMember.group_id == group_id,
            models.GuestMember.claimed_by_id == None  # Cannot use claimed guests as managers
        ).first()
        if not manager_guest:
            raise HTTPException(status_code=400, detail="Manager guest not found or already claimed")
        managed_by_name = manager_guest.name
    else:
        # Manager is a user - verify they are a group member
        manager_membership = db.query(models.GroupMember).filter(
            models.GroupMember.group_id == group_id,
            models.GroupMember.user_id == request.user_id
        ).first()
        if not manager_membership:
            raise HTTPException(status_code=400, detail="Manager must be a group member")
        manager = db.query(models.User).filter(models.User.id == request.user_id).first()
        managed_by_name = manager.full_name or manager.email if manager else None

    # Update member's manager
    member.managed_by_id = request.user_id
    member.managed_by_type = 'guest' if request.is_guest else 'user'
    db.commit()
    db.refresh(member)

    # Get user details for response
    user = db.query(models.User).filter(models.User.id == member_user_id).first()

    return {
        "message": "Member manager updated successfully",
        "member": schemas.GroupMember(
            id=member.id,
            user_id=member.user_id,
            full_name=user.full_name or user.email if user else "Unknown",
            email=user.email if user else "",
            managed_by_id=member.managed_by_id,
            managed_by_type=member.managed_by_type,
            managed_by_name=managed_by_name
        )
    }


@router.delete("/members/{member_user_id}/manage")
def unmanage_member(
    group_id: int,
    member_user_id: int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Remove member's manager link"""
    get_group_or_404(db, group_id)
    verify_group_membership(db, group_id, current_user.id)

    member = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == member_user_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Remove manager link
    member.managed_by_id = None
    member.managed_by_type = None
    db.commit()

    return {"message": "Member manager removed successfully"}


@router.post("/claim-unknown-items")
def claim_unknown_items(
    group_id: int,
    request: schemas.ClaimUnknownItemsRequest,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Claim specific item assignments from the Unknown guest.

    Allows users to claim items that were assigned to 'Unknown' when the expense
    was created. The assignments are transferred to the claiming user.
    """
    get_group_or_404(db, group_id)
    verify_group_membership(db, group_id, current_user.id)

    # Get the unknown guest for this group
    unknown_guest = db.query(models.GuestMember).filter(
        models.GuestMember.group_id == group_id,
        models.GuestMember.is_unknown_placeholder == True
    ).first()

    if not unknown_guest:
        raise HTTPException(status_code=404, detail="No Unknown guest found for this group")

    item_assignment_ids = request.item_assignment_ids

    # Get all the item assignments that belong to the Unknown guest
    assignments = db.query(models.ExpenseItemAssignment).filter(
        models.ExpenseItemAssignment.id.in_(item_assignment_ids),
        models.ExpenseItemAssignment.user_id == unknown_guest.id,
        models.ExpenseItemAssignment.is_guest == True
    ).all()

    if len(assignments) != len(item_assignment_ids):
        raise HTTPException(
            status_code=400,
            detail="Some item assignments are not from the Unknown guest or do not exist"
        )

    # Transfer the assignments to the current user
    transferred_count = db.query(models.ExpenseItemAssignment).filter(
        models.ExpenseItemAssignment.id.in_(item_assignment_ids)
    ).update({
        "user_id": current_user.id,
        "is_guest": False
    }, synchronize_session=False)

    # Recalculate splits for the affected expenses
    # Get unique expense IDs from the items
    item_ids = [a.expense_item_id for a in assignments]
    items = db.query(models.ExpenseItem).filter(
        models.ExpenseItem.id.in_(item_ids)
    ).all()
    expense_ids = list(set(item.expense_id for item in items))

    # Recalculate splits for each affected expense
    from utils.splits import calculate_itemized_splits
    for expense_id in expense_ids:
        expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
        if expense and expense.split_type == 'ITEMIZED':
            # Get all items for this expense
            expense_items = db.query(models.ExpenseItem).filter(
                models.ExpenseItem.expense_id == expense_id
            ).all()

            # Get all assignments for these items
            all_item_ids = [item.id for item in expense_items]
            all_assignments = db.query(models.ExpenseItemAssignment).filter(
                models.ExpenseItemAssignment.expense_item_id.in_(all_item_ids)
            ).all()

            # Build items data structure for split calculation
            items_data = []
            for item in expense_items:
                item_assignments = [a for a in all_assignments if a.expense_item_id == item.id]
                items_data.append({
                    "price": item.price,
                    "is_tax_tip": item.is_tax_tip,
                    "assignments": [{"user_id": a.user_id, "is_guest": a.is_guest} for a in item_assignments],
                    "split_type": item.split_type or "EQUAL",
                    "split_details": item.split_details
                })

            # Calculate new splits
            new_splits = calculate_itemized_splits(items_data)

            # Delete old splits
            db.query(models.ExpenseSplit).filter(
                models.ExpenseSplit.expense_id == expense_id
            ).delete(synchronize_session=False)

            # Create new splits
            for user_key, amount in new_splits.items():
                is_guest = user_key.startswith("guest_")
                user_id = int(user_key.split("_")[1])
                db.add(models.ExpenseSplit(
                    expense_id=expense_id,
                    user_id=user_id,
                    is_guest=is_guest,
                    amount_owed=amount
                ))

    db.commit()

    return {
        "message": f"Successfully claimed {transferred_count} item assignment(s)",
        "transferred_count": transferred_count,
        "affected_expenses": expense_ids
    }
