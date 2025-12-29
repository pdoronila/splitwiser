# Changelog

All notable changes to the Splitwiser project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added - 2025-12-28

#### Member Management for Registered Users
- Added ability to manage registered users, similar to guest management
- Registered users can now have their balances aggregated with another member or guest
- Visual indicators show "Includes:" breakdown when viewing aggregated balances
- Labels in Group Detail Page distinguish between "Splitwisers" (registered users) and "Guests"

**Backend Changes:**
- `backend/models.py` - Added `managed_by_id` and `managed_by_type` to `GroupMember` model
- `backend/routers/members.py` - New endpoints for managing registered members:
  - `POST /groups/{group_id}/members/{member_id}/manage`
  - `DELETE /groups/{group_id}/members/{member_id}/manage`
- `backend/routers/balances.py` - Updated balance aggregation to include managed members

**Frontend Changes:**
- `frontend/src/ManageMemberModal.tsx` - New component for managing registered members
- `frontend/src/GroupDetailPage.tsx` - Added "Splitwisers" and "Guests" section headers
- Updated balance display to show aggregated balances for managed members

**Database Migration:**
```sql
ALTER TABLE group_members ADD COLUMN managed_by_id INTEGER;
ALTER TABLE group_members ADD COLUMN managed_by_type TEXT;
```

**Migration Scripts:**
- `backend/migrations/add_member_management.py` - Idempotent migration script
- `backend/migrations/migrate.sh` - Helper script for direct installations
- `backend/migrations/migrate-docker.sh` - Helper script for Docker deployments
- See [Migration README](backend/migrations/README.md) for detailed instructions

#### Progressive Web App (PWA) Support
- Added PWA manifest and service worker for installable app experience
- Supports offline functionality with local IndexedDB caching
- Added app icons and maskable icons for Android
- Dark mode theme support for iPhone PWA

**Frontend Changes:**
- `frontend/public/manifest.json` - PWA manifest configuration
- `frontend/src/db/schema.ts` - IndexedDB schema for offline storage
- `frontend/src/services/offlineApi.ts` - Offline API wrapper
- `frontend/src/services/syncManager.ts` - Background sync manager
- Added various icon sizes (192x192, 512x512, maskable)

**Features:**
- Install to home screen on mobile devices
- Offline expense creation and editing
- Automatic sync when connection restored
- Exchange rates cached for offline use

#### Enhanced Receipt Scanner (OCR V2)
- Improved receipt text parsing with spatial layout analysis
- Better handling of multi-line items
- Filters out false matches from receipt metadata (phone numbers, dates, totals)
- Warning message when receipt scanning unavailable offline

**Backend Changes:**
- `backend/ocr/parser_v2.py` - New spatial layout parser
- `backend/ocr/test_parser_comparison.py` - Parser comparison tests
- `backend/routers/receipts.py` - Updated to use V2 parser

**Improvements:**
- More accurate item extraction
- Better price matching
- Reduced false positives
- Handles complex receipt layouts

#### Mobile-Friendly Improvements
- Replaced browser `alert()`, `prompt()`, and `confirm()` dialogs with custom modals
- Fixed iOS keyboard issue for number inputs (shows numeric keypad)
- iOS share support using Web Share API
- Mobile-responsive dialogs and forms

**Frontend Changes:**
- `frontend/src/AddFriendModal.tsx` - Custom friend request modal
- `frontend/src/AddGuestModal.tsx` - Custom guest add modal
- `frontend/src/DeleteGroupConfirm.tsx` - Custom confirmation modal
- Fixed `inputMode="decimal"` for iOS number inputs

#### Currency Enhancements
- Added CNY (Chinese Yuan/RMB) support
- Added HKD (Hong Kong Dollar) support
- Currency flags displayed in selectors
- Recently-used currencies sorted to top of list
- Currency selector now shows flag emojis for better UX

**Backend Changes:**
- `backend/schemas.py` - Updated currency validation to include CNY and HKD
- Exchange rate fetching updated to support new currencies

**Frontend Changes:**
- `frontend/src/AddExpenseModal.tsx` - Currency selector with flags
- Currency preferences stored in localStorage

#### Public Group Sharing
- Allow logged-in users to join public groups via share link
- Redirect logic: if user is already a member, redirect to authenticated view
- Read-only public view for non-members
- Share button copies link to clipboard (Web Share API on mobile)

**Backend Changes:**
- `backend/routers/groups.py` - Updated public group access logic
- Auto-join functionality for logged-in users

**Frontend Changes:**
- `frontend/src/GroupDetailPage.tsx` - Smart redirect for group members
- Share button with native sharing on mobile

#### Visual & UX Enhancements
- Group and expense icons/emojis for personalization
- Improved dashboard look and feel
- Better group display with icons
- Favicon and page titles added
- Friend detail page to view expenses between two friends

**Features:**
- Custom emoji picker for groups
- Icon categories for expenses
- Visual polish across all pages

### Changed - 2025-12-28

#### Claimed Guest Display Fix
- Fixed display names for claimed guests throughout the application
- Claimed guests now show registered user's `full_name` instead of old `guest.name`
- Consistent naming across balance view, expenses, and friend lists

**Backend Changes:**
- `backend/utils/display.py` - New utility functions:
  - `get_guest_display_name()` - Returns claimed user's name if applicable
  - `get_participant_display_name()` - Unified participant naming
- Updated 15+ locations across routers to use helper functions:
  - `backend/routers/auth.py` - Transfer managed_by on claim
  - `backend/routers/balances.py` - Balance breakdown display
  - `backend/routers/groups.py` - 8 locations updated
  - `backend/routers/expenses.py` - 4 locations updated
  - `backend/routers/friends.py` - 2 locations updated

**Migration Scripts:**
- `backend/migrations/fix_management_after_claim.py` - Fixes existing data
- `backend/migrations/fix_claimed_guest_management.py` - Guest claiming fixes

**Documentation:**
- See [BUGFIX_CLAIMED_GUEST_DISPLAY.md](BUGFIX_CLAIMED_GUEST_DISPLAY.md) for detailed analysis

#### Backend Refactoring
- Major refactoring to modular router-based architecture
- Separated monolithic `main.py` into focused routers:
  - `backend/routers/auth.py` - Authentication endpoints
  - `backend/routers/groups.py` - Group management
  - `backend/routers/members.py` - Member and guest management
  - `backend/routers/expenses.py` - Expense CRUD
  - `backend/routers/balances.py` - Balance calculations
  - `backend/routers/friends.py` - Friend management
  - `backend/routers/receipts.py` - OCR receipt scanning
- Improved code organization and maintainability
- Shared dependencies in `backend/dependencies.py`

#### Authentication Improvements
- Fixed auth refresh token issue
- More robust token validation
- Better error handling for expired tokens

#### Date Handling
- Normalized all dates in database to remove time zone issues
- Fixed timezone shifting for expense dates
- Consistent date formatting across frontend and backend

#### Expense Features
- Allow payer to not participate in expense (pay on behalf of others)
- Separate tax and tip fields for itemized expenses
- Helpful breakdown display for itemized expenses
- Receipt image saving and display
- Notes field added to expenses
- Deleting expense now also deletes associated receipt image

**Backend Changes:**
- `backend/models.py` - Added `notes` and `receipt_image_path` fields
- Receipt images stored in `backend/receipts/` directory
- Nginx configuration updated for file serving

#### Guest Management Improvements
- Fixed bug with dropping managed guest users
- Guests can now manage other guests
- Improved UI for guest management
- Fixed claiming issues for managed guests

#### Offline Support
- Exchange rates refresh when expenses added/edited offline
- Better handling of offline state
- Sync queue for pending changes

### Fixed - 2025-12-28

- Fixed exchange rate update when expense date or currency changes
- Fixed participant toggle for current user in expense creation
- Fixed iOS group sharing with Web Share API
- Fixed iOS keyboard showing full keyboard instead of numpad for amounts
- Fixed false price matches from receipt metadata in OCR
- Fixed multi-line receipt item parsing
- Fixed build issues with TypeScript
- Fixed claimed guest name display across all views
- Fixed balance display for claimed users
- Fixed managed member claiming migrations
- Fixed auth refresh token handling
- Fixed timezone issues causing date shifts
- Fixed visual bugs in dashboard and group displays
- Fixed nginx file upload size limits for receipt images

### Added - 2025-12-10

#### Group Default Currency Feature
- Added `default_currency` field to Group model (defaults to USD)
- Currency validation in Pydantic schemas (supports USD, EUR, GBP, JPY, CAD)
- Currency selector dropdown in group creation form
- Edit Group modal now includes currency editor
- Expense creation automatically pre-fills currency from group's default
- Toggle button on Group Detail page to view balances in group's default currency
- Balance grouping by currency with clear section headers

**Backend Changes:**
- `backend/models.py` - Added `default_currency` column to `Group` model
- `backend/schemas.py` - Updated `GroupBase`, `GroupCreate`, `GroupUpdate` with currency field and validation
- `backend/main.py` - Updated group creation/update endpoints to handle `default_currency`

**Frontend Changes:**
- `frontend/src/App.tsx` - Added currency selector to group creation
- `frontend/src/EditGroupModal.tsx` - Added currency editor
- `frontend/src/AddExpenseModal.tsx` - Implemented automatic currency pre-fill from group default
- `frontend/src/GroupDetailPage.tsx` - Added balance grouping by currency and conversion toggle
- Updated Group TypeScript interfaces across all components

**Database Migration:**
```sql
ALTER TABLE groups ADD COLUMN default_currency TEXT DEFAULT 'USD';
```

#### Historical Exchange Rate Caching
- Expenses now cache their historical exchange rate at creation time
- Integration with Frankfurter API (free, no API key required)
- Fallback to static rates if API is unavailable
- `/exchange_rates` endpoint now fetches live rates from Frankfurter API

**Backend Changes:**
- `backend/models.py` - Added `exchange_rate` field to `Expense` model
- `backend/main.py` - Added three new functions:
  - `fetch_historical_exchange_rate()` - Fetches historical rates from Frankfurter API
  - `get_exchange_rate_for_expense()` - Wrapper with fallback logic
  - Updated `get_exchange_rates()` - Now fetches live rates from API
- Expense creation now automatically fetches and caches exchange rate for the expense date

**API Integration:**
- Frankfurter API (`https://api.frankfurter.app/`)
  - Historical rates back to 1999
  - No API key required
  - Maintained using European Central Bank data
  - Free for reasonable usage

**Database Migration:**
```sql
ALTER TABLE expenses ADD COLUMN exchange_rate TEXT;
```

**Benefits:**
- Accurate historical tracking of exchange rates
- Only one API call per expense (minimal API usage)
- Fast balance viewing (uses cached rates)
- Works offline with fallback to static rates

### Changed - 2025-12-10
- Balance display now groups by currency first, then by person
- Exchange rate endpoint now fetches live rates instead of using static values
- Group detail page UI enhanced with currency conversion toggle

### Technical Details

**Files Modified:**
- Backend: `models.py`, `schemas.py`, `main.py`
- Frontend: `App.tsx`, `GroupDetailPage.tsx`, `AddExpenseModal.tsx`, `EditGroupModal.tsx`
- Database: Added columns to `groups` and `expenses` tables

**Dependencies:**
- No new dependencies added (uses existing `requests` library for API calls)

**Testing:**
- Historical rate fetching tested for EUR, GBP on various dates
- Current rate endpoint tested and verified
- Database migrations completed successfully

**Known Limitations:**
- Frankfurter API supports EUR, USD, and other major currencies but not all world currencies
- Historical rates only available from 1999 onwards
- Existing expenses (created before this update) have NULL exchange_rate and will use fallback rates
