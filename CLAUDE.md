# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Splitwiser is a Splitwise clone for expense splitting among friends and groups. It features multi-currency support, various split types (equal, exact, percentage, shares), OCR receipt scanning, and debt simplification.

## Architecture

### Backend (FastAPI + SQLAlchemy)
- `backend/main.py` - API endpoints and core business logic (expenses, groups, friends, balances, debt simplification)
- `backend/models.py` - SQLAlchemy models: User, Group, GroupMember, Friendship, Expense, ExpenseSplit
- `backend/schemas.py` - Pydantic schemas for request/response validation
- `backend/auth.py` - JWT authentication with bcrypt password hashing
- `backend/database.py` - SQLite database configuration
- Uses OAuth2 with Bearer tokens; all authenticated endpoints require `Authorization: Bearer <token>` header

### Frontend (React + TypeScript + Vite)
- `frontend/src/App.tsx` - Main app with Dashboard, routing, and protected routes
- `frontend/src/AuthContext.tsx` - Authentication context provider
- `frontend/src/AddExpenseModal.tsx` - Expense creation with split type selection
- `frontend/src/ReceiptScanner.tsx` - OCR receipt scanning using tesseract.js
- `frontend/src/SettleUpModal.tsx` - Settlement modal
- Styling with Tailwind CSS v4

### Key Patterns
- Money stored in cents (integer) to avoid floating-point issues
- Balance calculation: positive = owed to you, negative = you owe
- Debt simplification algorithm converts all currencies to USD for settlement

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

## API Endpoints

- `POST /register` - User registration
- `POST /token` - Login (OAuth2 form: username=email, password)
- `GET /users/me` - Current user info
- `POST /groups`, `GET /groups` - Group CRUD
- `POST /friends`, `GET /friends` - Friend management
- `POST /expenses`, `GET /expenses` - Expense CRUD
- `GET /balances` - User balance summary
- `GET /simplify_debts/{group_id}` - Debt simplification for a group
- `GET /exchange_rates` - Currency exchange rates
