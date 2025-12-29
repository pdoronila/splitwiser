# Bug Fix: Claimed Guest Display Names

## Issue Summary

When guests claimed their accounts and became registered users, their names were still displayed as the old `guest.name` instead of showing their User's `full_name` or email. This caused confusion where the same person appeared under two different names in various parts of the application.

## Root Cause

Throughout the codebase, when displaying guest information, the code was using `guest.name` directly without checking if the guest had been claimed (`guest.claimed_by_id` is set). When a guest is claimed, we should look up the corresponding User record and display their `full_name` or `email` instead.

## Solution

### 1. Created Helper Function

**File:** `backend/utils/display.py` (NEW)

Created two utility functions:
- `get_guest_display_name(guest, db)` - Returns the appropriate display name for a guest (User's full_name if claimed, otherwise guest.name)
- `get_participant_display_name(user_id, is_guest, db)` - Helper for getting any participant's name

### 2. Fixed Display Issues in Multiple Locations

Updated all locations where guest names are displayed to use the helper function:

#### Auth/Registration Flow
- **backend/routers/auth.py** (lines 69-86)
  - Fixed: When guests claim accounts during registration, their `managed_by` relationship is now properly transferred to the `group_members` table

#### Balance Display
- **backend/routers/balances.py** (lines 97-98)
  - Fixed: Managed guest breakdown in balance view now shows User's full_name for claimed guests

#### Group Display
- **backend/routers/groups.py** (multiple locations)
  - Lines 80, 110, 236, 266: Fixed manager name display when manager is a claimed guest
  - Lines 319, 353, 605, 639: Fixed expense split names for claimed guests
  - Lines 476, 519: Fixed balance display for claimed guests

#### Expense Display
- **backend/routers/expenses.py** (multiple locations)
  - Lines 187, 224, 468: Fixed expense split names for claimed guests
  - Fixed itemized expense assignment names for claimed guests

#### Friend Expenses
- **backend/routers/friends.py** (multiple locations)
  - Lines 158, 199: Fixed friend expense split names for claimed guests
  - Fixed itemized expense assignment names in friend view

## Files Changed

### New Files
1. `backend/utils/display.py` - Helper functions for guest display names

### Modified Files
1. `backend/routers/auth.py` - Transfer managed_by relationship on claim
2. `backend/routers/balances.py` - Use helper for balance breakdown
3. `backend/routers/groups.py` - Use helper in 8 locations
4. `backend/routers/expenses.py` - Use helper in 4 locations
5. `backend/routers/friends.py` - Use helper in 2 locations

## Testing

After deployment, verify:

1. **Balance View**: When viewing group balances, managed users who were claimed guests should show their User's full_name (e.g., "Jezmin Pelayo") instead of just the guest name (e.g., "Jezmin")

2. **Expense Details**: Historical expenses involving claimed guests should show the User's current name, not the old guest name

3. **Manager Display**: When a guest is managed by a claimed guest, it should show the manager's User name

## Migration Script

Created `backend/migrations/fix_management_after_claim.py` to fix existing database records where the `managed_by` relationship wasn't transferred when guests claimed their accounts.

Run with:
```bash
python migrations/fix_management_after_claim.py --db-path /path/to/db.sqlite3
```

## Deployment

1. Deploy updated backend code
2. Run migration script (if needed) to fix existing data
3. Restart backend containers
4. Clear browser cache and hard refresh frontend

## Impact

- **User-Facing**: Users will now see consistent names across the application
- **Historical Data**: Old expenses will display the person's current registered name instead of their old guest name
- **Balance Aggregation**: The "Includes:" breakdown in balances will show proper full names
- **Breaking Changes**: None - this is purely a display fix

## Related Issues

This fix addresses the broader issue of claimed guest display across the entire application, not just in the balance view. All locations that display guest information have been updated to handle claimed guests properly.
