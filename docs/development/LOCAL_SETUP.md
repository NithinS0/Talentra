# Talentra — Local Development Setup Runbook

## 1. System Prerequisites

Before starting local development, ensure your workstation has the following tools installed:

- **Node.js**: v18.17.0+ or v20.x LTS
- **Package Manager**: npm v9+ (or pnpm v8+)
- **Python**: Python 3.11+
- **Database Access**: Direct connection to a PostgreSQL 15+ instance or a Supabase project.
- **Operating System**: Windows (PowerShell), macOS, or Linux.

---

## 2. Repository Architecture at a Glance

```text
Talentra/
├── frontend/               # Next.js 16 Web Application (Port 3000)
├── backend/                # FastAPI Application & Alembic migrations (Port 8000)
├── docs/                   # Authoritative Documentation
├── scripts/                # Database and build automation utilities
├── tests/                  # Pytest test suite
├── .env.example            # Environment configuration template
└── requirements.txt        # Backend Python dependencies
```

---

## 3. Backend Setup & Runbook

### 3.1. Virtual Environment & Dependencies
Open a terminal in the project root:

```powershell
# Create Python 3.11 virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# (Alternative for macOS/Linux)
# source .venv/bin/activate

# Upgrade pip and install pinned backend dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3.2. Environment Configuration
Copy the template configuration file:

```powershell
Copy-Item .env.example .env
```

Open `.env` in your editor and configure your database connection string:

```ini
APP_ENV=development
APP_DEBUG=true

# Direct Connection (Port 5432) - REQUIRED for Alembic migrations & DDL
DATABASE_URL="postgresql+psycopg://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"

# Connection Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=5
DB_POOL_TIMEOUT=30
DB_CONNECT_TIMEOUT=10
DB_POOL_RECYCLE=1800
DB_ECHO=false
```

> **Special Characters Alert**: If your database password contains characters like `@`, `#`, `:`, `%`, `?`, `/`, or `$`, they must be percent-encoded (e.g., `@` becomes `%40`, `#` becomes `%23`).

### 3.3. Verify Database Connectivity
Execute the pre-flight verification script:

```powershell
.\.venv\Scripts\python.exe backend/app/verify_db.py
```
This tests:
1. Core dependency package imports.
2. Pydantic Settings loading and safe URL masking.
3. Alembic configuration resolution.
4. Supabase connection (`SELECT 1;`) and session closure.

### 3.4. Apply Database Migrations
Execute Alembic migrations across all 13 modules:

```powershell
# (Optional) Dry-run offline SQL transaction
.\.venv\Scripts\alembic upgrade head --sql

# Apply all migrations to your PostgreSQL/Supabase database
.\.venv\Scripts\alembic upgrade head
```

Verify that the schema has all 216 tables and indexes:

```powershell
.\.venv\Scripts\python.exe backend/app/verify_schema.py
```

### 3.5. Seed Reference Master Data
Populate reference domains, countries, languages, currencies, and roles:

```powershell
.\.venv\Scripts\python.exe backend/app/seeds/seed_reference_data.py
```

### 3.6. Start the FastAPI Backend Server
```powershell
.\.venv\Scripts\uvicorn backend.app.main:app --reload --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Probe: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- Database Probe: [http://localhost:8000/api/v1/health/db](http://localhost:8000/api/v1/health/db)

---

## 4. Frontend Setup & Runbook

### 4.1. Install Dependencies
Open a second terminal window in `frontend/`:

```bash
cd frontend
npm install
```

### 4.2. Run the Development Server
```bash
npm run dev
```
The Next.js development server will start at [http://localhost:3000](http://localhost:3000).

### 4.3. Run Frontend Validation Commands
```bash
# TypeScript type checking
npm run typecheck

# Unit and integration tests (Vitest)
npm run test

# Production build check (Turbopack)
npm run build
```

---

## 5. Troubleshooting Common Issues

| Symptom | Cause | Solution |
|:---|:---|:---|
| `FATAL: password authentication failed` | Password contains unencoded special characters | URL-encode special characters in `DATABASE_URL` (`@` -> `%40`). |
| `Alembic: cannot execute transaction in pooler` | Connecting via Transaction Pooler (Port 6543) | Switch `DATABASE_URL` host to Direct Connection on **Port 5432**. |
| `ModuleNotFoundError: No module named 'backend'` | Running Python without virtualenv activated or wrong working directory | Run from the repository root with `.venv/Scripts/python.exe`. |
| `Port 3000 is already in use` | Another process is holding port 3000 | Terminate the occupying process or run `npm run dev -- -p 3001`. |
