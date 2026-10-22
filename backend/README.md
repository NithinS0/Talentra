# Talentra — FastAPI Service Layer (Backend)

The backend service layer for Talentra is a high-performance RESTful API built on **FastAPI (Python 3.11+)**, **SQLAlchemy 2.x**, **Psycopg 3**, and **Alembic**, backed by **Supabase PostgreSQL**.

---

## 1. Quick Start

### 1.1. Prerequisites
- Python 3.11+
- Virtual environment tool (`venv`)
- Active PostgreSQL 15+ database or Supabase project

### 1.2. Virtual Environment Setup (PowerShell on Windows)
```powershell
# In repository root:
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install pinned dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 1.3. Configure Environment Variables
Copy `.env.example` in the root directory to `.env` and configure your credentials:

```ini
APP_ENV=development
APP_DEBUG=true

# Direct Connection on Port 5432 (Mandatory for DDL & Alembic migrations)
DATABASE_URL="postgresql+psycopg://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"

# Connection Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=5
DB_POOL_TIMEOUT=30
DB_CONNECT_TIMEOUT=10
DB_POOL_RECYCLE=1800
DB_ECHO=false
```

### 1.4. Pre-Flight Connectivity Diagnostic
```powershell
.\.venv\Scripts\python.exe backend/app/verify_db.py
```

### 1.5. Run Database Migrations
```powershell
# Dry-run SQL inspection
.\.venv\Scripts\alembic upgrade head --sql

# Apply all migrations to database
.\.venv\Scripts\alembic upgrade head
```

Verify that all 216 tables and 489 indexes are present:
```powershell
.\.venv\Scripts\python.exe backend/app/verify_schema.py
```

### 1.6. Seed Master Reference Data
```powershell
.\.venv\Scripts\python.exe backend/app/seeds/seed_reference_data.py
```

### 1.7. Start the Development Server
```powershell
.\.venv\Scripts\uvicorn backend.app.main:app --reload --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative ReDoc UI: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Liveness Probe: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- Database Readiness Probe: [http://localhost:8000/api/v1/health/db](http://localhost:8000/api/v1/health/db)

---

## 2. Directory Structure

```text
backend/
├── README.md                      # Backend service documentation
├── alembic/                       # Alembic environment and versioned migrations
│   ├── env.py                     # Migration runner context
│   └── versions/                  # Revisions 000 through 014
├── app/
│   ├── main.py                    # FastAPI application initialization & middleware
│   ├── config.py                  # Pydantic Settings v2 configuration
│   ├── database.py                # SQLAlchemy engine & session maker
│   ├── api/                       # API route controllers (/api/v1/*)
│   ├── models/                    # SQLAlchemy ORM model definitions
│   ├── schemas/                   # Pydantic request/response schemas
│   ├── services/                  # Business logic services
│   ├── seeds/                     # Database seeders (seed_reference_data.py)
│   ├── verify_db.py               # Pre-flight database connectivity probe
│   └── verify_schema.py           # Catalog & blueprint reconciliation verifier
└── migrations_sql/                # Pure SQL migration reference scripts
```

---

## 3. Database Migration Directives

- **Direct Connection Rule**: Always run Alembic against the direct connection (Port 5432). Supabase connection poolers (Port 6543) do not support the transaction locks required by migration runners.
- **Rollback Procedure**: To roll back the last migration:
  ```powershell
  .\.venv\Scripts\alembic downgrade -1
  ```
- **Append-Only Triggers**: Tables `audit_events`, `wallet_ledgers`, `payment_transactions`, and `profile_download_history` are protected by database immutability triggers. They cannot be updated or deleted.

---

## 4. Testing

Run Pytest from the repository root:
```powershell
.\.venv\Scripts\pytest -v tests/test_health.py
```
For complete acceptance test guidelines, see [`docs/development/TESTING.md`](../docs/development/TESTING.md).
