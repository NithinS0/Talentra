# Talentra — Production Deployment & Release Runbook

## 1. Production Architecture Overview

Talentra is designed for containerized or serverless deployment across enterprise cloud environments (AWS, GCP, Azure, or Vercel/Supabase).

```text
┌────────────────────────────────────────────────────────┐
│              Cloudflare / Route 53 (DNS)              │
├────────────────────────────────────────────────────────┤
│           Nginx / AWS ALB (TLS 1.3 Termination)        │
├──────────────────────────┬─────────────────────────────┤
│  Frontend Cluster        │  Backend API Cluster        │
│  Next.js 16 (Node/Edge)  │  FastAPI (Uvicorn Workers)  │
│  Port 3000               │  Port 8000                  │
├──────────────────────────┴─────────────────────────────┤
│           Persistence Layer: Supabase PostgreSQL       │
│           Direct Port 5432 (DDL / Migrations)          │
│           Session Pooler Port 6543 (Runtime Traffic)   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Environment Configuration Matrix

The following environment variables must be defined in your production container orchestrator (e.g., Kubernetes Secrets, AWS Secrets Manager, Vercel Environment Variables):

| Variable Name | Required In | Description / Format |
|:---|:---:|:---|
| `APP_ENV` | Backend | Set to `production` |
| `APP_DEBUG` | Backend | Must be `false` |
| `DATABASE_URL` | Backend | Direct connection string to PostgreSQL on **Port 5432** |
| `SUPABASE_URL` | Backend | HTTPS endpoint of the Supabase project |
| `SUPABASE_ANON_KEY` | Backend/FE | Public anon key for client-side storage access |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend | Private key with full administrative access (NEVER expose to FE) |
| `SUPABASE_JWT_SECRET` | Backend | HMAC secret used to verify client JWTs |
| `STRIPE_SECRET_KEY` | Backend | Live Stripe secret key (`sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | Backend | Signing secret for inbound Stripe webhooks |
| `SENDGRID_API_KEY` | Backend | Production SendGrid API key |
| `SUREPASS_API_KEY` | Backend | Production identity verification gateway key |
| `STORAGE_SIGNING_PEPPER` | Backend | High-entropy random secret for document URL signing |
| `NEXT_PUBLIC_API_URL` | Frontend | Public URL of the FastAPI gateway (e.g. `https://api.talentra.com`) |

---

## 3. Pre-Deployment Readiness Checklist

Before promoting a release to production:

- [ ] **Alembic Dry-Run**: Run `alembic upgrade head --sql` to verify DDL transactions without locking active tables.
- [ ] **Migration Direct Port**: Confirm migration jobs connect via **Port 5432** directly to Postgres, not the transaction pooler.
- [ ] **CORS Isolation**: Verify `CORS_ORIGINS` in FastAPI explicitly lists only the approved production frontend domains.
- [ ] **Frontend Build**: Verify `npm run build` succeeds cleanly with all static routes generated.
- [ ] **Test Automation**: Ensure all 154 frontend tests and backend test suites pass with 0 failures.
- [ ] **Security Secret Sanitization**: Verify no `.env` or development credentials exist in Git history or Docker images.

---

## 4. Release Execution Workflow

1. **Step 1: Database Migration**:
   ```bash
   alembic upgrade head
   ```
2. **Step 2: Deploy Backend Workers**:
   Launch FastAPI uvicorn container with multi-worker configuration:
   ```bash
   gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```
3. **Step 3: Verify Backend Probes**:
   - `curl -f https://api.talentra.com/api/v1/health`
   - `curl -f https://api.talentra.com/api/v1/health/db`
4. **Step 4: Deploy Frontend**:
   Deploy Next.js build output (standalone server or Vercel edge deployment).
5. **Step 5: Post-Release Smoke Test**:
   Perform end-to-end verification of portal login, job search, and role switcher.
