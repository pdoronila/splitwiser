# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Splitwiser is a Splitwise clone for expense splitting among friends and groups. It features multi-currency support (USD, EUR, GBP, JPY, CAD, CNY, HKD) with historical exchange rate caching, various split types (equal, exact, percentage, shares, itemized with per-item split methods), two-phase interactive OCR receipt scanning with bounding box editor and 5-minute caching, group-level currency management, debt simplification, guest and member management with balance aggregation, dark mode, refresh token authentication with password reset and email change flows, email notifications via Brevo API (friend requests, password reset, security alerts), Progressive Web App (PWA) with offline support via IndexedDB, and mobile-optimized UI with pinch-to-zoom gestures and Web Share API.

## Architecture

### Backend (FastAPI + SQLAlchemy)

**Main Application:**
- `backend/main.py` - FastAPI app initialization and router registration
- `backend/models.py` - SQLAlchemy models: User, Group, GroupMember, Friendship, Expense, ExpenseSplit, GuestMember, RefreshToken, ExpenseItem, ExpenseItemAssignment
- `backend/schemas.py` - Pydantic schemas for request/response validation
- `backend/auth.py` - JWT token creation and password hashing
- `backend/database.py` - SQLite database configuration
- `backend/dependencies.py` - Shared FastAPI dependencies (auth, database session)

**Routers (Modular API Endpoints):**
- `backend/routers/auth.py` - Authentication (login, register, refresh tokens, logout, password reset, email change)
- `backend/routers/groups.py` - Group CRUD, public share links
- `backend/routers/members.py` - Member and guest management, claiming
- `backend/routers/expenses.py` - Expense CRUD, split calculations
- `backend/routers/balances.py` - Balance calculations, debt simplification
- `backend/routers/friends.py` - Friend management, friend request emails
- `backend/routers/ocr.py` - Two-phase OCR (region detection, text extraction)

**Utilities:**
- `backend/utils/currency.py` - Exchange rate fetching (Frankfurter API), caching
- `backend/utils/validation.py` - Split validation, participant verification
- `backend/utils/splits.py` - Split calculation logic (equal, exact, percentage, shares, itemized)
- `backend/utils/display.py` - Display name helpers for guests and claimed users
- `backend/utils/email.py` - Brevo API email service for transactional emails

**OCR Integration:**
- `backend/ocr/service.py` - Google Cloud Vision API client (singleton)
- `backend/ocr/parser.py` - Receipt text parsing and item extraction (V1)
- `backend/ocr/parser_v2.py` - Enhanced spatial layout parser with improved accuracy
- `backend/ocr/regions.py` - Smart region detection and filtering for two-phase OCR (V3)

**Database Migrations:**
- `backend/migrations/` - Migration scripts with helper tools
- `backend/migrations/migrate.sh` - Helper script for direct installations
- `backend/migrations/migrate-docker.sh` - Helper script for Docker deployments
- `backend/migrations/README.md` - Detailed migration documentation

**Key Database Fields:**
- Group: `default_currency`, `icon`, `share_link_id`, `is_public`
- GroupMember: `managed_by_id`, `managed_by_type` (NEW - for registered user management)
- Expense: `exchange_rate`, `split_type`, `receipt_image_path`, `icon`, `notes`, `payer_is_guest`
- ExpenseSplit: `is_guest`
- GuestMember: `claimed_by_id`, `managed_by_id`, `managed_by_type`
- RefreshToken: `token_hash`, `expires_at`, `revoked`
- ExpenseItem: `description`, `price`, `is_tax_tip`
- ExpenseItemAssignment: `user_id`, `is_guest`

### Frontend (React + TypeScript + Vite)

**Core Components:**
- `frontend/src/App.tsx` - Main app with Dashboard, routing, protected routes
- `frontend/src/AuthContext.tsx` - Authentication with automatic token refresh
- `frontend/src/ThemeContext.tsx` - Dark mode with localStorage persistence
- `frontend/src/GroupDetailPage.tsx` - Group detail, balances, public share links
- `frontend/src/ExpenseDetailModal.tsx` - Expense viewing/editing with notes
- `frontend/src/AddExpenseModal.tsx` - Expense creation (5 split types)

**Services & Types:**
- `frontend/src/services/api.ts` - Centralized API client with auth handling
- `frontend/src/services/offlineApi.ts` - Offline API wrapper using IndexedDB
- `frontend/src/services/syncManager.ts` - Background sync manager for PWA
- `frontend/src/db/schema.ts` - IndexedDB schema for offline storage
- `frontend/src/types/` - TypeScript definitions (group.ts, expense.ts, balance.ts, friend.ts)
- `frontend/src/utils/formatters.ts` - Money, date, and name formatting
- `frontend/src/utils/expenseCalculations.ts` - Frontend split calculations
- `frontend/src/utils/participantHelpers.ts` - Participant data helpers

**Feature Components:**
- `frontend/src/ReceiptScanner.tsx` - Two-phase OCR receipt scanning (V3)
- `frontend/src/components/expense/BoundingBoxEditor.tsx` - Interactive bounding box editor
- `frontend/src/components/expense/ItemPreviewEditor.tsx` - Item review and editing interface
- `frontend/src/components/expense/ReceiptCanvas.tsx` - Canvas rendering for OCR
- `frontend/src/components/expense/ExpenseItemList.tsx` - Itemized expense UI with per-item splits
- `frontend/src/ManageGuestModal.tsx` - Guest management and balance aggregation
- `frontend/src/ManageMemberModal.tsx` - Member management for registered users
- `frontend/src/AddGuestModal.tsx` - Add non-registered users (mobile-friendly)
- `frontend/src/AddMemberModal.tsx` - Add registered members
- `frontend/src/DeleteGroupConfirm.tsx` - Custom confirmation dialogs (replaces browser alerts)
- `frontend/src/hooks/useItemizedExpense.ts` - Itemized expense state management
- `frontend/src/hooks/useBoundingBoxes.ts` - Bounding box state management for OCR
- `frontend/src/utils/imageCompression.ts` - Client-side image compression

**PWA Support:**
- `frontend/public/manifest.json` - PWA manifest for installable app
- `frontend/public/icons/` - App icons (192x192, 512x512, maskable)
- Service worker for offline caching and background sync

### Key Patterns
- Money stored in cents (integer) to avoid floating-point issues
- Balance calculation: positive = owed to you, negative = you owe
- Debt simplification converts all currencies to USD using cached exchange rates
- Historical exchange rates cached at expense creation (Frankfurter API)
- Group-level default currency for expense pre-filling and balance display
- Guest users support claiming (merge history) and management (balance aggregation)
- Registered members can also be managed for balance aggregation (NEW)
- Claimed guests display using registered user's `full_name` via `display.py` helpers
- Refresh tokens stored hashed (SHA-256) in database with server-side revocation
- Public share links allow read-only group viewing without login
- Itemized expenses use proportional tax/tip distribution
- PWA with IndexedDB for offline expense creation and auto-sync
- Mobile-optimized with Web Share API and custom dialogs (no browser alerts)
- Currency flags and recently-used sorting in currency selectors
- Receipt images stored in `backend/receipts/` directory

## Development Commands

### Backend
```bash
cd backend
source venv/bin/activate  # Activate virtual environment
pip install -r requirements.txt  # Install dependencies
uvicorn main:app --reload  # Run dev server on http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install  # Install dependencies
npm run dev  # Run dev server (Vite)
npm run build  # Build for production (tsc + vite build)
npm run lint  # Run ESLint
```

### Testing
```bash
cd backend
pytest tests/test_main.py  # Run backend tests
pytest tests/test_main.py::test_create_user -v  # Run single test
```

### Database Migrations
When schema changes are made, update the SQLite database:
```bash
cd backend
source venv/bin/activate
python -c "from database import Base, engine; import models; Base.metadata.create_all(bind=engine)"
```

For manual column additions (e.g., adding new fields to existing tables):
```bash
sqlite3 db.sqlite3
ALTER TABLE table_name ADD COLUMN column_name TYPE DEFAULT 'value';
```

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /token` - Login (OAuth2 form: username=email, password), returns access_token and refresh_token
- `POST /auth/refresh` - Exchange refresh token for new access token
- `POST /auth/logout` - Revoke refresh token
- `GET /users/me` - Current user info
- `POST /auth/forgot-password` - Request password reset email
- `POST /auth/reset-password` - Reset password with token
- `POST /auth/change-password` - Change password (requires authentication)
- `POST /auth/change-email` - Change email address with verification
- `GET /auth/verify-email/{token}` - Verify new email address

### Groups
- `POST /groups` - Create group (accepts `default_currency` field)
- `GET /groups` - List user's groups
- `GET /groups/{group_id}` - Get group details (includes `default_currency`)
- `PUT /groups/{group_id}` - Update group (can change `default_currency`)
- `DELETE /groups/{group_id}` - Delete group
- `GET /groups/{group_id}/balances` - Get group balances (per currency, includes managed guest aggregation)
- `POST /groups/{group_id}/guests` - Add guest member to group
- `DELETE /groups/{group_id}/guests/{guest_id}` - Remove guest from group
- `POST /groups/{group_id}/guests/{guest_id}/claim` - Claim guest profile (merge to registered user)
- `POST /groups/{group_id}/guests/{guest_id}/manage` - Link guest to manager for balance aggregation
- `DELETE /groups/{group_id}/guests/{guest_id}/manage` - Unlink guest from manager

### Friends & Expenses
- `POST /friends`, `GET /friends` - Friend management
- `POST /friends/request` - Send friend request email notification
- `POST /expenses` - Create expense (supports split_type: EQUAL, EXACT, PERCENTAGE, SHARES, ITEMIZED; caches historical exchange rate)
- `GET /expenses` - List expenses
- `GET /expenses/{expense_id}` - Get expense details (includes items for ITEMIZED type)
- `PUT /expenses/{expense_id}` - Update expense (updates cached exchange rate if date/currency changes)
- `DELETE /expenses/{expense_id}` - Delete expense

### Public Access
- `GET /public/groups/{share_link_id}` - Get group details via public share link (no auth required)
- `GET /public/groups/{share_link_id}/expenses/{expense_id}` - Get expense details via public link

### Balances & Currency
- `GET /balances` - User balance summary across all groups (includes managed guest balances)
- `GET /simplify_debts/{group_id}` - Debt simplification using cached exchange rates
- `GET /exchange_rates` - Current exchange rates (Frankfurter API)

### OCR Receipt Scanning
- `POST /ocr/detect-regions` - Upload receipt, get detected text regions with bounding boxes (Phase 1)
- `POST /ocr/extract-regions` - Extract text from specific regions using provided coordinates (Phase 2)

## Feature Details

### Group Default Currency

Groups can have a default currency that streamlines expense creation and balance viewing.

**Database Schema:**
- `groups.default_currency` (String, default: "USD") - The preferred currency for the group

**Supported Currencies:**
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- JPY (Japanese Yen)
- CAD (Canadian Dollar)

**Validation:**
- Pydantic field validator in `schemas.py` ensures only valid currencies are accepted
- Invalid currencies return 422 Unprocessable Entity error

**Frontend Features:**
1. **Group Creation** - Currency selector dropdown in sidebar (defaults to USD)
2. **Group Editing** - Default currency can be changed via Edit Group modal
3. **Expense Pre-fill** - When creating an expense in a group, currency automatically pre-fills with group's default
4. **Balance Display** - Toggle button to view all balances converted to group's default currency

**Backend Implementation:**
- `POST /groups` - Accepts `default_currency` in request body
- `PUT /groups/{group_id}` - Updates `default_currency` field
- `GET /groups/{group_id}` - Returns group with `default_currency` field

### Historical Exchange Rate Caching

Expenses cache their exchange rate at creation time for accurate historical tracking.

**Problem Solved:**
Exchange rates fluctuate daily. Without caching historical rates, old expenses would be converted using today's rates, leading to inaccurate balance calculations.

**Solution:**
Cache the exchange rate from the expense's currency to USD on the date of the expense.

**Database Schema:**
- `expenses.exchange_rate` (String, nullable) - Exchange rate from expense currency to USD on expense date
- Stored as string for SQLite compatibility
- Example: "1.0945" (means 1 EUR = 1.0945 USD on that date)

**API Used: Frankfurter API**
- URL: `https://api.frankfurter.app/`
- Free, no API key required
- Historical rates back to 1999
- Maintained using European Central Bank data
- No rate limits for reasonable usage

**How It Works:**

1. **On Expense Creation:**
   ```python
   # User creates expense with date "2024-01-15" and currency "EUR"
   exchange_rate = get_exchange_rate_for_expense("2024-01-15", "EUR")
   # Fetches from: https://api.frankfurter.app/2024-01-15?from=EUR&to=USD
   # Returns: 1.0945
   # Stores in expense.exchange_rate = "1.0945"
   ```

2. **On Balance Viewing:**
   - Frontend fetches current rates from `/exchange_rates` endpoint
   - Backend calls Frankfurter API for latest rates
   - Frontend uses current rates for balance conversion display

**Fallback Mechanism:**
If Frankfurter API is unavailable:
- Falls back to hardcoded rates in `EXCHANGE_RATES` dict
- Prints warning to console
- System continues to function normally

**Functions:**
- `fetch_historical_exchange_rate(date, from_currency, to_currency)` - Fetches historical rate from API
- `get_exchange_rate_for_expense(date, currency)` - Wrapper with fallback logic
- `get_exchange_rates()` - Fetches current rates for frontend

**Benefits:**
- ✅ Accurate historical records preserved
- ✅ Only one API call per expense (minimal usage)
- ✅ Fast balance viewing (no API calls needed)
- ✅ Works offline if API fails (fallback rates)
- ✅ No API key required (free service)

### Balance Grouping by Currency

Group balance display intelligently groups and converts between currencies.

**Two Display Modes:**

1. **Grouped by Currency (Default):**
   - Balances organized by currency with section headers
   - Example:
     ```
     USD
       Alice  +$50.00
       Bob    -$30.00

     EUR
       Alice  +€20.00
     ```

2. **Converted to Group Currency (Toggle):**
   - All balances converted to group's default currency
   - Aggregates multi-currency balances per person
   - Example (group default: USD):
     ```
     Alice  +$73.30  (combined $50 + €20)
     Bob    -$30.00
     ```

**Frontend Implementation:**
- Toggle button: "Show in {currency}" / "Show by currency"
- Uses current exchange rates from `/exchange_rates` endpoint
- Client-side conversion for fast, responsive UI
- Filters out near-zero balances after conversion

**Conversion Logic:**
```typescript
// Convert through USD as intermediary
const amountInUSD = amount / exchangeRates[fromCurrency];
const converted = amountInUSD * exchangeRates[toCurrency];
```

## Currency Conversion Flow

```
Expense Created (2024-01-15)
    ↓
Fetch historical rate for 2024-01-15
    ↓ (Frankfurter API)
Cache rate in expense.exchange_rate
    ↓
Store expense with cached rate
    ↓
View Balances Today
    ↓
Fetch current rates
    ↓ (Frankfurter API)
Display with today's conversion rates
```

## Email Notifications

Splitwiser supports transactional emails via Brevo API (optional feature).

### Email Service Architecture

**Email Utility ([backend/utils/email.py](backend/utils/email.py)):**
- Brevo API integration (not SMTP)
- Async email sending with error handling
- HTML and plain text email templates
- Environment-based configuration
- Graceful fallback if not configured

### Email Types

1. **Password Reset**
   - Triggered by "Forgot Password" flow
   - Contains secure reset link (expires in 1 hour)
   - Sent via `send_password_reset_email()`

2. **Password Changed Notification**
   - Sent after successful password change
   - Security notification to alert user
   - Sent via `send_password_changed_notification()`

3. **Email Verification**
   - Sent when user changes email address
   - Contains verification link (expires in 24 hours)
   - Sent via `send_email_verification_email()`

4. **Email Change Notification**
   - Security alert sent to old email address
   - Notifies user of email change
   - Sent via `send_email_change_notification()`

5. **Friend Request Notification**
   - Sent when someone sends you a friend request
   - Contains link to view pending requests
   - Sent via `send_friend_request_email()`

### Configuration

**Environment Variables:**
- `BREVO_API_KEY` - Your Brevo API key
- `FROM_EMAIL` - Verified sender email in Brevo
- `FROM_NAME` - Sender display name (default: "Splitwiser")
- `FRONTEND_URL` - Base URL for email links

**Configuration Check:**
```python
from backend.utils.email import is_email_configured
if is_email_configured():
    # Email service is ready
```

### API Integration

**Brevo API:**
- Endpoint: `https://api.brevo.com/v3/smtp/email`
- Authentication: API key in request headers
- No SMTP configuration needed
- Free tier: 300 emails/day

### Error Handling

- Gracefully handles API failures (logs error, returns False)
- Timeout protection (10 second limit)
- Configuration validation before sending
- Detailed error logging for debugging

### Setup Guide

See [EMAIL_SETUP.md](EMAIL_SETUP.md) for step-by-step configuration instructions.

## OCR Receipt Scanning (Two-Phase Interactive System)

Receipt scanning uses Google Cloud Vision API with an advanced two-phase interactive workflow.

### Architecture

```
backend/ocr/
├── service.py   # Google Cloud Vision client (singleton)
├── parser.py    # Receipt text parsing & item extraction (V1)
├── parser_v2.py # Enhanced spatial layout parser
└── regions.py   # Smart region detection and filtering (Two-Phase OCR)

backend/routers/
└── ocr.py       # OCR endpoints (region detection, extraction)

frontend/src/
├── ReceiptScanner.tsx                    # Main scanner component
├── components/expense/
│   ├── BoundingBoxEditor.tsx             # Interactive region editor
│   ├── ItemPreviewEditor.tsx             # Item review interface
│   └── ReceiptCanvas.tsx                 # Canvas rendering engine
├── hooks/
│   └── useBoundingBoxes.ts               # Bounding box state management
└── utils/
    └── imageCompression.ts               # Client-side compression
```

### Two-Phase OCR System

**Phase 1: Interactive Region Definition**
- Automatic detection of text regions using Vision API paragraph boundaries
- Interactive canvas for adjusting bounding boxes
- Drag to move, resize from corners, double-click to add new boxes
- Click to delete regions
- Pinch-to-zoom with proper centering (mobile touch support)
- Numbered labels for clear identification
- Visual feedback during interaction

**Phase 2: Item Review & Editing**
- Split-view interface showing receipt regions and extracted items
- Inline editing of descriptions and prices
- Tax/tip marking per item
- Bidirectional highlighting (click item → highlights box on receipt)
- Items sorted by Y-coordinate (top-to-bottom on receipt)
- Cropped region preview above each item
- Individual edit buttons (no global edit mode)

### Backend Implementation

**API Endpoints:**
- `POST /ocr/detect-regions` - Upload receipt, get detected text regions with bounding boxes
- `POST /ocr/extract-regions` - Extract text from specific regions (coordinates provided by user)

**Smart Region Detection ([backend/ocr/regions.py](backend/ocr/regions.py)):**
- Uses Vision API paragraph boundaries for line-level detection (not individual words)
- Intelligent filtering removes headers, footers, noise
- Confidence scoring for extracted items
- Enhanced price matching (handles prices with/without dollar signs)
- Initial suggestions with smart defaults

**Response Caching:**
- In-memory caching of Vision API responses (5-minute TTL)
- Single OCR call per receipt minimizes API usage
- Cache key based on image hash
- Reduces costs and improves performance

**File Validation:**
- 10MB maximum file size
- JPEG, PNG, WebP formats supported
- Comprehensive error handling

### Frontend Features

**Client-Side Image Compression ([frontend/src/utils/imageCompression.ts](frontend/src/utils/imageCompression.ts)):**
- Automatically compresses images before upload
- Maximum dimension: 1920px
- Target size: ~1MB
- Preserves image quality while reducing bandwidth

**Interactive Canvas Editor ([frontend/src/components/expense/BoundingBoxEditor.tsx](frontend/src/components/expense/BoundingBoxEditor.tsx)):**
- Full touch support (mobile-friendly)
- Pinch-to-zoom with proper pivot point calculations
- Drag gestures for panning
- Mouse support for desktop
- Visual feedback for selected regions
- Coordinate system transformations (OCR ↔ display)

**Item Preview Editor ([frontend/src/components/expense/ItemPreviewEditor.tsx](frontend/src/components/expense/ItemPreviewEditor.tsx)):**
- Per-item split methods (Equal, Exact, Percentage, Shares)
- Dynamic split detail inputs based on split type
- Visual region preview for each item
- Save/cancel/delete for individual items
- Validation for split totals

### Per-Item Split Methods

**Flexible Splitting:**
Each item in an itemized expense can have its own split method:
- **Equal** - Divide item equally among assignees (default)
- **Exact** - Specify exact dollar amounts per person
- **Percentage** - Split by percentages (must total 100%)
- **Shares** - Split by share ratio (e.g., 2:1)

**Example:**
```
Item: "2 Corona $10.00"
Assignees: Alice, Bob
Split Method: SHARES
Split Details: Alice=2, Bob=1
Result: Alice=$6.67, Bob=$3.33
```

**Backend Validation:**
- EXACT: Validates amounts match item price
- PERCENT: Ensures percentages add to 100%
- SHARES: Validates positive share values
- Comprehensive error messages

### Setup

1. Create Google Cloud project and enable Cloud Vision API
2. Create service account with "Cloud Vision API User" role
3. Download JSON credentials file
4. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
   ```

### Free Tier

- 1,000 pages/month free
- Requires GCP account with billing enabled (won't charge within free tier)
- Caching reduces API calls significantly

## Guest User Management

Non-registered users can participate in expenses and later claim their profiles.

### Database Schema

**GuestMember Model:**
- `id` - Primary key
- `group_id` - Group the guest belongs to
- `name` - Guest's display name
- `created_by_id` - User who added the guest
- `claimed_by_id` - User who claimed this guest (nullable)
- `managed_by_id` - ID of manager (user or guest, nullable)
- `managed_by_type` - Type of manager: 'user' or 'guest' (nullable)

### Features

**1. Guest Creation**
- Any group member can add guests with just a name
- Guests can be payers or participants in expenses
- Endpoint: `POST /groups/{group_id}/guests`

**2. Guest Claiming**
- Registered users can claim guest profiles to merge expense history
- All expenses where guest was payer transfer to claiming user
- All expense splits involving guest transfer to claiming user
- Claiming user automatically added to group if not already member
- Endpoint: `POST /groups/{group_id}/guests/{guest_id}/claim`

**3. Guest Management (Balance Aggregation)**
- Link a guest to a "manager" (registered user OR another guest)
- Guest's balance aggregates with manager's balance in balance view
- Guest still appears separately in expense details
- Prevents circular management (cannot manage self)
- Cannot manage claimed guests
- Auto-unlink when manager leaves group
- Endpoints:
  - `POST /groups/{group_id}/guests/{guest_id}/manage` - Link to manager
  - `DELETE /groups/{group_id}/guests/{guest_id}/manage` - Unlink

### Example Use Case

```
1. Alice adds "Bob's Friend" as guest to group
2. Guest participates in several expenses
3. Bob registers and claims guest profile
4. All guest expenses transfer to Bob
5. Bob is automatically added to the group
```

### Frontend Components
- `ManageGuestModal.tsx` - UI for linking guests to managers
- `AddGuestModal.tsx` - Simple form to add guest by name
- Visual indicators show managed guest relationships in balance view

## Member Management for Registered Users

Similar to guest management, registered users can also be managed for balance aggregation.

### Database Schema

**GroupMember Model Additions:**
- `managed_by_id` - ID of manager (user or guest, nullable)
- `managed_by_type` - Type of manager: 'user' or 'guest' (nullable)

### Features

**1. Member Management**
- Link registered members to a manager (registered user OR guest)
- Member's balance aggregates with manager's balance in balance view
- Member still appears separately in expense details
- Prevents circular management (cannot manage self)
- Auto-unlink when manager leaves group
- Endpoints:
  - `POST /groups/{group_id}/members/{member_id}/manage` - Link to manager
  - `DELETE /groups/{group_id}/members/{member_id}/manage` - Unlink

**2. Visual Separation**
- Group Detail Page shows "Splitwisers" section for registered users
- Separate "Guests" section for non-registered users
- Clear visual distinction between member types

### Example Use Case

```
1. Alice and Bob are both registered users in a group
2. They're a couple and want to see their combined balance
3. Alice links Bob as managed by her
4. Balance view now shows "Alice: $100 (Includes: Bob)"
5. Expense details still show individual transactions
```

### Frontend Components
- `ManageMemberModal.tsx` - UI for linking members to managers
- `GroupDetailPage.tsx` - Section headers distinguish Splitwisers from Guests
- Visual indicators show managed member relationships in balance view

### Migration Scripts
- `backend/migrations/add_member_management.py` - Adds columns to group_members table
- `backend/migrations/migrate.sh` - Helper for direct installations
- `backend/migrations/migrate-docker.sh` - Helper for Docker deployments
- See `backend/migrations/README.md` for detailed instructions

## Claimed Guest Display Names

When guests claim their accounts, they should display using their registered user name.

### Implementation

**Helper Functions ([backend/utils/display.py](backend/utils/display.py)):**
- `get_guest_display_name(guest, db)` - Returns claimed user's `full_name` if applicable, otherwise `guest.name`
- `get_participant_display_name(user_id, is_guest, db)` - Unified helper for any participant

**Updated Locations:**
All locations displaying guest names now use these helpers:
- `backend/routers/auth.py` - Transfer managed_by on claim
- `backend/routers/balances.py` - Balance breakdown display
- `backend/routers/groups.py` - 8 locations updated
- `backend/routers/expenses.py` - 4 locations updated
- `backend/routers/friends.py` - 2 locations updated

**Migration Scripts:**
- `backend/migrations/fix_management_after_claim.py` - Fixes existing data where managed_by wasn't transferred
- `backend/migrations/fix_claimed_guest_management.py` - Guest claiming fixes

**Documentation:**
- See [BUGFIX_CLAIMED_GUEST_DISPLAY.md](BUGFIX_CLAIMED_GUEST_DISPLAY.md) for detailed technical analysis

## Public Share Links

Enable read-only group sharing without requiring authentication.

### Database Schema

**Group Model Additions:**
- `share_link_id` - Unique UUID for the public share link (nullable)
- `is_public` - Boolean flag indicating if public sharing is enabled (default: false)

### How It Works

**Enabling Public Sharing:**
1. Group owner opens group settings
2. Toggles "Enable public sharing"
3. Backend generates unique `share_link_id` (UUID)
4. Frontend displays shareable URL

**Accessing Public Links:**
1. Anyone with the link can view group balances and expenses
2. No login required
3. Read-only access (no modifications allowed)
4. Expense details accessible via modal

### API Endpoints

- `PUT /groups/{group_id}` - Toggle `is_public` flag, generates `share_link_id`
- `GET /public/groups/{share_link_id}` - Get group details (no auth)
- `GET /public/groups/{share_link_id}/expenses/{expense_id}` - Get expense details (no auth)

### Frontend Implementation

- `GroupDetailPage.tsx` - Handles both authenticated and public views
- Uses `isPublicView` prop to toggle between edit/read-only modes
- Share button copies public URL to clipboard
- All edit buttons hidden in public view

## Refresh Token Authentication

Secure authentication with short-lived access tokens and long-lived refresh tokens.

### Architecture

**Token Types:**
1. **Access Token (JWT)**
   - Short-lived (30 minutes)
   - Contains user email and expiry
   - Used for API authentication
   - Transmitted in Authorization header

2. **Refresh Token (Random)**
   - Long-lived (30 days)
   - Cryptographically secure random token (256-bit)
   - Stored hashed (SHA-256) in database
   - Used to obtain new access tokens

### Database Schema

**RefreshToken Model:**
- `id` - Primary key
- `user_id` - Owner of token
- `token_hash` - SHA-256 hash (plaintext never stored)
- `expires_at` - Expiry datetime
- `created_at` - Creation datetime
- `revoked` - Boolean flag for logout

### Authentication Flow

**Login:**
```
1. POST /token with credentials
2. Server validates password
3. Server creates access token (JWT, 30 min)
4. Server creates refresh token (random, 30 days)
5. Server stores HASHED refresh token in database
6. Server returns both tokens to client
7. Client stores both in localStorage
```

**Token Refresh:**
```
1. Access token expires (401 error)
2. Client POST /auth/refresh with refresh token
3. Server validates refresh token hash
4. Server checks not revoked and not expired
5. Server creates new access token
6. Client updates localStorage
7. Client retries original request
```

**Logout:**
```
1. Client POST /auth/logout with refresh token
2. Server marks token as revoked in database
3. Client clears localStorage
```

### Security Benefits
- Access tokens short-lived (minimizes attack window)
- Refresh tokens stored hashed (protects against DB breach)
- Token revocation on logout (prevents reuse)
- Automatic refresh provides seamless UX
- No password storage in client after login

### Frontend Implementation
- `AuthContext.tsx` implements automatic token refresh on 401
- Transparent retry logic for expired access tokens
- All API calls automatically use current access token

### Functions

**Backend ([auth.py](backend/auth.py)):**
- `create_access_token(data)` - Generate JWT with 30 min expiry
- `create_refresh_token()` - Generate secure random token
- `hash_token(token)` - SHA-256 hash for storage
- `verify_access_token(token)` - Validate JWT

**Frontend ([AuthContext.tsx](frontend/src/AuthContext.tsx)):**
- `refreshAccessToken()` - Exchange refresh token for new access token
- `fetchWithRefresh()` - Auto-retry on 401 with token refresh

## Itemized Expense Splitting

Split expenses by individual items with proportional tax/tip distribution (e.g., restaurant bills).

### Database Schema

**ExpenseItem Model:**
- `id` - Primary key
- `expense_id` - Parent expense
- `description` - Item name (e.g., "Burger")
- `price` - Item price in cents
- `is_tax_tip` - Boolean flag for tax/tip items

**ExpenseItemAssignment Model:**
- `id` - Primary key
- `expense_item_id` - Item being assigned
- `user_id` - Person assigned to item
- `is_guest` - Boolean flag for guest users

### Split Calculation Algorithm

**Steps:**
1. Sum each person's assigned items (shared items split equally among assignees)
2. Calculate subtotal for all non-tax/tip items
3. Distribute tax/tip proportionally based on each person's subtotal share
4. Return final splits with total amounts owed

**Tax/Tip Distribution:**
```
Person's tax/tip share = (Person's subtotal / Total subtotal) × Total tax/tip
```

**Rounding Handling:**
- Item splits: First assignee gets remainder cents
- Tax/tip: Last person gets remainder to ensure exact total

### Example

```
Restaurant bill:
├─ Burger ($12.99) → Alice, Bob
├─ Pizza ($15.99) → Bob, Charlie
├─ Salad ($8.99) → Alice
└─ Tax/Tip ($7.50) → Marked as tax/tip

Calculation:
1. Burger: Alice $6.50, Bob $6.49
2. Pizza: Bob $8.00, Charlie $7.99
3. Salad: Alice $8.99
4. Subtotals: Alice $15.49, Bob $14.49, Charlie $7.99 (Total: $37.97)
5. Tax/tip distribution:
   - Alice: ($15.49 / $37.97) × $7.50 = $3.06
   - Bob: ($14.49 / $37.97) × $7.50 = $2.86
   - Charlie: ($7.99 / $37.97) × $7.50 = $1.58
6. Final: Alice $18.55, Bob $17.35, Charlie $9.57
   Total: $45.47 ✓
```

### Frontend Implementation

**Components:**
- `ExpenseItemList.tsx` - Item list with assignment UI
  - Inline buttons for small groups (≤5 participants)
  - Modal selector for large groups
  - Visual validation (red border for unassigned items)
  - Assignment display: "You + 2 others" or specific names

**Custom Hook:**
- `useItemizedExpense.ts` - State management for items and assignments
  - `addManualItem()` - Add item from OCR or manual entry
  - `removeItem()` - Delete item
  - `toggleItemAssignment()` - Assign/unassign person to item
  - `taxTipAmount` - Separate field for tax/tip

### Validation Rules
1. All non-tax/tip items must have at least one assignee
2. Sum of splits must equal expense total (±1 cent tolerance)
3. Expense total auto-calculated from sum of items
4. All participants must exist in database

### API Usage

**Create Itemized Expense:**
```json
POST /expenses
{
  "description": "Restaurant",
  "amount": 4547,
  "currency": "USD",
  "date": "2025-12-26",
  "group_id": 1,
  "payer_id": 1,
  "split_type": "ITEMIZED",
  "items": [
    {
      "description": "Burger",
      "price": 1299,
      "is_tax_tip": false,
      "assignments": [
        {"user_id": 1, "is_guest": false},
        {"user_id": 2, "is_guest": false}
      ]
    },
    {
      "description": "Tax/Tip",
      "price": 750,
      "is_tax_tip": true,
      "assignments": []
    }
  ]
}
```

## Dark Mode

System-wide dark theme with user preference persistence.

### Architecture

**Theme Context ([ThemeContext.tsx](frontend/src/ThemeContext.tsx)):**
- React Context API for global theme state
- Persists preference to localStorage
- Falls back to system preference if no saved preference
- Applies 'dark' class to `<html>` element

### Implementation

**Preference Priority:**
1. User's saved preference in localStorage
2. System preference from `prefers-color-scheme` media query
3. Default: light mode

**Theme Toggle:**
- Button in sidebar footer
- Sun icon (yellow) when in dark mode → click for light
- Moon icon (gray) when in light mode → click for dark

**Styling:**
- Tailwind CSS v4 with `@variant dark (&:where(.dark, .dark *));`
- All components use `dark:` variants for dark mode styles
- Examples:
  - `dark:bg-gray-800` - Dark backgrounds
  - `dark:text-gray-100` - Light text
  - `dark:border-gray-700` - Dark borders
  - `dark:hover:bg-gray-600` - Dark hover states

**Smooth Transitions:**
```css
* {
  transition: background-color 0.2s ease-in-out,
              border-color 0.2s ease-in-out;
}
```

### Coverage
All 20+ frontend components implement dark mode:
- Modals (AddExpense, SettleUp, EditGroup, ManageGuest)
- Forms (Login, Register)
- Lists (Groups, Friends, Expenses, Balances)
- Detail pages (GroupDetail, ExpenseDetail)
- Navigation (Sidebar, Header)

### Storage
```typescript
// Save preference
localStorage.setItem('theme', isDark ? 'dark' : 'light');

// Load preference
const savedTheme = localStorage.getItem('theme');
const prefersDark = savedTheme === 'dark' ||
  window.matchMedia('(prefers-color-scheme: dark)').matches;
```

## Database Schema Changes

### New Tables

```sql
-- Guest user management
CREATE TABLE guest_members (
    id INTEGER PRIMARY KEY,
    group_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_by_id INTEGER NOT NULL,
    claimed_by_id INTEGER,
    managed_by_id INTEGER,
    managed_by_type TEXT
);

-- Refresh token authentication
CREATE TABLE refresh_tokens (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    revoked BOOLEAN DEFAULT FALSE
);

-- Itemized expense items
CREATE TABLE expense_items (
    id INTEGER PRIMARY KEY,
    expense_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    price INTEGER NOT NULL,
    is_tax_tip BOOLEAN DEFAULT FALSE
);

-- Itemized expense assignments
CREATE TABLE expense_item_assignments (
    id INTEGER PRIMARY KEY,
    expense_item_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    is_guest BOOLEAN DEFAULT FALSE
);
```

### Modified Tables

```sql
-- Group default currency
ALTER TABLE groups ADD COLUMN default_currency TEXT DEFAULT 'USD';

-- Historical exchange rate caching
ALTER TABLE expenses ADD COLUMN exchange_rate TEXT;

-- Guest user support in expenses
ALTER TABLE expenses ADD COLUMN payer_is_guest BOOLEAN DEFAULT FALSE;
ALTER TABLE expense_splits ADD COLUMN is_guest BOOLEAN DEFAULT FALSE;

-- Receipt images and notes
ALTER TABLE expenses ADD COLUMN receipt_image_path TEXT;
ALTER TABLE expenses ADD COLUMN icon TEXT;
ALTER TABLE expenses ADD COLUMN notes TEXT;

-- Group icons and public sharing
ALTER TABLE groups ADD COLUMN icon TEXT;
ALTER TABLE groups ADD COLUMN share_link_id TEXT UNIQUE;
ALTER TABLE groups ADD COLUMN is_public BOOLEAN DEFAULT FALSE;

-- Member management for registered users (NEW)
ALTER TABLE group_members ADD COLUMN managed_by_id INTEGER;
ALTER TABLE group_members ADD COLUMN managed_by_type TEXT;
```

## Progressive Web App (PWA)

Splitwiser is installable as a Progressive Web App with offline support.

### Architecture

**PWA Manifest ([frontend/public/manifest.json](frontend/public/manifest.json)):**
- App name, description, and theme colors
- Start URL and display mode (standalone)
- Icon definitions (192x192, 512x512, maskable)
- Dark mode theme support

**Service Worker:**
- Caches static assets for offline use
- Intercepts network requests
- Provides fallback for offline scenarios
- Background sync for pending operations

**IndexedDB Storage ([frontend/src/db/schema.ts](frontend/src/db/schema.ts)):**
- `expenses` table - Offline expense creation
- `groups` table - Cached group data
- `exchange_rates` table - Currency conversion offline
- `sync_queue` table - Pending operations to sync

### Offline API Wrapper ([frontend/src/services/offlineApi.ts](frontend/src/services/offlineApi.ts))

Wraps standard API calls with offline fallback:
- Detects online/offline state
- Stores operations in IndexedDB when offline
- Returns cached data when offline
- Queues mutations for later sync

### Sync Manager ([frontend/src/services/syncManager.ts](frontend/src/services/syncManager.ts))

Background sync for pending operations:
- Monitors online/offline state changes
- Processes sync queue when connection restored
- Retries failed operations
- Handles conflict resolution

### Features

**Offline Capabilities:**
- Create and edit expenses without internet
- View cached groups and balances
- Currency conversion using cached rates
- Queue operations for automatic sync

**Installation:**
- Install to home screen on iOS and Android
- Standalone app experience (no browser chrome)
- App icon on device home screen
- Launch like a native app

**Performance:**
- Fast loading via service worker caching
- Reduced network requests
- Instant UI feedback for offline operations

### Usage

**Exchange Rates Caching:**
```typescript
// Rates cached in IndexedDB for offline use
// Refreshed when online or when adding/editing expenses offline
```

**Offline Expense Creation:**
```typescript
// 1. User creates expense while offline
// 2. Stored in IndexedDB with pending status
// 3. Added to sync_queue
// 4. When online, sync manager processes queue
// 5. Expense created on server
// 6. Local copy updated with server response
```

## Mobile-Friendly Features

### Custom Dialogs

Replaced browser `alert()`, `prompt()`, and `confirm()` with custom modals:
- **AddFriendModal** - Custom friend request dialog
- **AddGuestModal** - Guest addition with validation
- **DeleteGroupConfirm** - Confirmation dialogs with proper styling
- Mobile-responsive with touch-friendly buttons

### iOS Keyboard Fix

Number inputs show numeric keypad on iOS:
```tsx
<input
  type="text"
  inputMode="decimal"
  pattern="[0-9]*"
/>
```

### Web Share API

Native sharing on mobile devices:
```typescript
if (navigator.share) {
  await navigator.share({
    title: 'Group Share',
    url: shareUrl
  });
} else {
  // Fallback to clipboard
  navigator.clipboard.writeText(shareUrl);
}
```

### PWA Theme

iPhone PWA with proper dark mode support:
- `theme-color` meta tag updates based on theme
- Maskable icons for Android adaptive icons
- Splash screen with app branding

## Enhanced Receipt Scanner (OCR V2)

Improved receipt parsing with spatial layout analysis.

### Parser V2 ([backend/ocr/parser_v2.py](backend/ocr/parser_v2.py))

**Improvements:**
- Spatial layout analysis using bounding boxes
- Better multi-line item handling
- Filters false matches (phone numbers, dates, metadata)
- More accurate price matching
- Reduced false positives

**Algorithm:**
1. Extract text with bounding box coordinates from Google Cloud Vision
2. Group text blocks by vertical position (line grouping)
3. Match item descriptions with prices on same line
4. Filter out common false matches:
   - Phone numbers (pattern: XXX-XXX-XXXX)
   - Dates (pattern: MM/DD/YYYY)
   - Total/subtotal lines
   - Receipt metadata
5. Return structured items with prices

**Testing:**
- `backend/ocr/test_parser_comparison.py` - Comparison between V1 and V2 parsers
- Test cases for complex receipts with multi-line items

### Offline Warning

Receipt scanning unavailable offline:
- Warning message displayed when offline
- Scanner disabled in offline mode
- Requires Google Cloud Vision API (network required)

## Performance Optimizations

Splitwiser has been extensively optimized to eliminate N+1 query problems and improve response times.

### Database Optimizations

**Indexes Added:**
- Expense queries indexed for faster lookups
- Group member queries optimized with proper joins
- Balance calculations use efficient SQL queries

**N+1 Query Elimination:**
- Group details endpoint: Uses `joinedload` for members and guests
- Expense listing: Pre-loads related data in single query
- Balance calculations: Aggregates data efficiently
- Public group endpoints: Optimized for anonymous access
- Friend expenses and balances: Batch loading implemented

### Query Optimization Locations

The following endpoints have been optimized:
- `GET /groups` - Group listing with member counts
- `GET /groups/{group_id}` - Group details with all relations
- `GET /groups/{group_id}/balances` - Balance calculations
- `GET /expenses` - Expense listing with participant details
- `GET /public/groups/{share_link_id}` - Public group access
- `GET /friends` - Friend listing with expense data

## Security Features

### Rate Limiting

**Protected Endpoints:**
- Authentication endpoints (`/token`, `/register`) - Prevents brute force attacks
- OCR endpoint (`/ocr/scan-receipt`) - Prevents API abuse (10MB file limit)
- Rate limits enforced using `slowapi` library
- Supports `X-Forwarded-For` header for proxy environments

**Configuration:**
- Default: 5 requests per minute for auth endpoints
- Default: 10 requests per minute for OCR endpoint
- Configurable per-endpoint limits

### Security Headers

**HTTP Security Headers:**
- `Content-Security-Policy` - Restricts resource loading
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - XSS protection

### Input Validation

**Schema Validation:**
- Maximum length enforcement on all text fields
- File upload size limits (10MB for receipts)
- Email format validation
- Currency validation against allowed list

**Information Leakage Prevention:**
- OCR error messages sanitized
- Generic error responses for security-sensitive operations
- No exposure of internal paths or stack traces

## Currency Enhancements

### Additional Currencies

Added support for:
- **CNY** - Chinese Yuan (Renminbi) 🇨🇳
- **HKD** - Hong Kong Dollar 🇭🇰

**Backend Changes:**
- `backend/schemas.py` - Updated currency validation
- Exchange rate fetching includes CNY and HKD

### Currency Flags

Visual currency selector with flag emojis:
- USD 🇺🇸, EUR 🇪🇺, GBP 🇬🇧, JPY 🇯🇵, CAD 🇨🇦, CNY 🇨🇳, HKD 🇭🇰
- Improves UX and visual recognition
- Consistent across all currency selectors

### Recently-Used Sorting

Currency selectors show recently-used currencies first:
- Stored in localStorage
- Top 3 recent currencies sorted to top
- Faster selection for frequently-used currencies

**Implementation:**
```typescript
// Save currency usage
const recentCurrencies = JSON.parse(localStorage.getItem('recentCurrencies') || '[]');
recentCurrencies.unshift(selectedCurrency);
localStorage.setItem('recentCurrencies', JSON.stringify(recentCurrencies.slice(0, 3)));
```
