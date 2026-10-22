# Talentra — Backup, Disaster Recovery & Migration Rollback Runbook

## 1. Backup Strategy & Objectives

Talentra implements high-availability persistence through Supabase PostgreSQL automated backup pipelines and disaster recovery procedures.

### Operational Recovery Targets
- **Recovery Point Objective (RPO)**: < 5 minutes (via continuous Write-Ahead Log [WAL] archiving).
- **Recovery Time Objective (RTO)**: < 30 minutes for database restoration.

---

## 2. Backup Mechanisms

### 2.1. Automated Physical Backups (PITR)
- **Point-In-Time Recovery**: Active WAL archiving allows restoration to any arbitrary second within the past 7 to 30 days.
- **Daily Full Backups**: Automated snapshot taken every 24 hours during off-peak hours (02:00 UTC).

### 2.2. Logical Schema Dumps
For offline archival and staging synchronization:
```bash
# Export schema-only DDL
pg_dump -h db.[PROJECT-REF].supabase.co -U postgres -d postgres -p 5432 --schema-only -F p -f schema_backup.sql

# Export complete database with data
pg_dump -h db.[PROJECT-REF].supabase.co -U postgres -d postgres -p 5432 -F c -b -v -f talentra_full_backup.dump
```

---

## 3. Alembic Migration Rollback Procedures

When a newly applied migration introduces unforeseen regression, use the following rollback runbook:

### 3.1. Dry-Run Inspection
Always generate and inspect the SQL that will be executed during a downgrade:
```powershell
.\.venv\Scripts\alembic downgrade -1 --sql
```

### 3.2. Executing Downgrades
```powershell
# Rollback exactly one revision
.\.venv\Scripts\alembic downgrade -1

# Rollback to a specific historical revision
.\.venv\Scripts\alembic downgrade <revision_id>
```

> **Warning on Immutability Triggers**:
> If rolling back a migration that modifies tables protected by append-only triggers (`audit_events`, `wallet_ledgers`, `payment_transactions`), the trigger must be temporarily disabled in a single transactional block:
> ```sql
> BEGIN;
> ALTER TABLE audit_events DISABLE TRIGGER trg_immutable_audit_event;
> -- Perform required corrective migration
> ALTER TABLE audit_events ENABLE TRIGGER trg_immutable_audit_event;
> COMMIT;
> ```

---

## 4. Disaster Recovery & Restoration Verification

Following any database restoration or failover event:

1. **Test Liveness & Readiness**:
   ```powershell
   curl -f http://localhost:8000/api/v1/health
   curl -f http://localhost:8000/api/v1/health/db
   ```
2. **Execute Automated Catalog Verification**:
   ```powershell
   .\.venv\Scripts\python.exe backend/app/verify_schema.py
   ```
   Confirm that all 216 base tables, 233 foreign keys, and 489 indexes are present and valid.
3. **Verify Append-Only Trigger Enforcement**:
   Execute a test update on `audit_events` to ensure it is immediately rejected:
   ```sql
   UPDATE audit_events SET action = 'TEST' WHERE event_id = 1;
   -- Expected output: ERROR: Updates are prohibited on immutable audit table.
   ```
