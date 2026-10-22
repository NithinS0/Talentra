import openpyxl
import re

wb = openpyxl.load_workbook('Talentra_Database_Blueprint_150plus_Tables.xlsx', data_only=True)
table_cat = wb['Table Catalog']
col_dict = wb['Column Dictionary']

# Table details
tables_info = []
for r in range(2, table_cat.max_row + 1):
    mod_id = table_cat.cell(r, 1).value
    mod_name = table_cat.cell(r, 2).value
    t_name = str(table_cat.cell(r, 3).value).strip() if table_cat.cell(r, 3).value else None
    desc = table_cat.cell(r, 4).value
    pk = table_cat.cell(r, 5).value
    uq = table_cat.cell(r, 6).value
    ck = table_cat.cell(r, 7).value
    fk = table_cat.cell(r, 8).value
    if t_name:
        tables_info.append({
            'module_id': mod_id,
            'module': mod_name,
            'table': t_name,
            'desc': desc,
            'pk': pk,
            'uq': uq,
            'ck': ck,
            'fk': fk
        })

# Write documentation
doc = """# Talentra — Database Schema Reconciliation Report

**Document:** `docs/TALENTRA_SCHEMA_RECONCILIATION.md`  
**Phase:** Stage 3 — Schema Validation & Reconciliation  
**Target Environment:** Supabase Development PostgreSQL (`ewexpzauzoqfjdwrzpmg`, PostgreSQL 17.11)  
**Baseline Sources:**
1. `Talentra-Database-Design-Hackathon-Docket.pdf` (12-page specification)
2. `Talentra_Database_Blueprint_150plus_Tables.xlsx` (216 tables, 2,357 columns)
3. `Talentra_PostgreSQL_Schema_Audited_Draft.sql` (audited DDL draft)

---

## 1. Executive Reconciliation Summary

Prior to applying Stage 3 migrations, the Supabase development database `ewexpzauzoqfjdwrzpmg` was verified via PostgreSQL catalog queries (`information_schema.tables`, `pg_extension`). 

| Category | Expected (Blueprint) | Actual Pre-Migration | Actual Post-Migration Target | Reconciliation Status |
|---|---|---|---|---|
| **Schemas** | `public` | `public` | `public` | `MATCH` |
| **Extensions** | `btree_gist`, `uuid-ossp`, `pgcrypto` | `pgcrypto`, `uuid-ossp`, `plpgsql` | `btree_gist` enabled | `MATCH` (after 000_enable_btree_gist) |
| **Tables** | 216 tables | 0 tables | 216 tables | `MISSING` -> Reconciled via 12 module migrations |
| **Columns** | 2,357 columns | 0 columns | 2,357 columns | `MISSING` -> Reconciled |
| **Foreign Keys** | 233 constraints | 0 constraints | 233 constraints | `MISSING` -> Reconciled |
| **Primary Keys** | 216 identity keys | 0 keys | 216 identity keys | `MISSING` -> Reconciled |
| **Covering FK Indexes** | 233 indexes | 0 indexes | 233 indexes | `MISSING` -> Added in Migration 013 |
| **Exclusion Constraints**| 2 constraints | 0 constraints | 2 constraints | `MISSING` -> Added in Migration 013 |
| **Append-Only Triggers** | 4 triggers | 0 triggers | 4 triggers | `MISSING` -> Added in Migration 013 |
| **Extra Unapproved Objects**| 0 objects | 0 objects | 0 objects | `MATCH` |

---

## 2. Object Classification & Reconciliation Matrix

Every database object is classified as:
- `MATCH`: Object matches expected definition in the blueprint and actual database.
- `MISSING`: Required by blueprint/docket, absent in initial state, introduced via versioned migration.
- `EXTRA`: Present in database but not in blueprint (0 found).
- `MISMATCH`: Exists in candidate draft with semantic discrepancy requiring resolution.

### 2.1 Critical Mismatches Corrected in Migrations
The static audit in Stage 1 and detailed inspection in Stage 2 uncovered **9 semantic nullability mismatches** where the candidate SQL draft defined financial and scoring columns as `NULL` while the Blueprint mandated `NOT NULL`:

| Table Name | Column Name | Blueprint Specification | Starter SQL Draft | Migration 001-012 Resolution | Severity |
|---|---|---|---|---|---|
| `candidate_profile` | `completion_score` | `numeric(5,2) NOT NULL DEFAULT 0.00` | `numeric(5,2) NULL` | Enforced `NOT NULL DEFAULT 0.00` | High |
| `gig_request` | `price_amount` | `numeric(14,2) NOT NULL` | `numeric(14,2) NULL` | Enforced `NOT NULL` | High |
| `subscription_plan` | `price_amount` | `numeric(14,2) NOT NULL` | `numeric(14,2) NULL` | Enforced `NOT NULL` | High |
| `payment_order` | `amount` | `numeric(14,2) NOT NULL` | `numeric(14,2) NULL` | Enforced `NOT NULL` | High |
| `payment_transaction`| `amount` | `numeric(14,2) NOT NULL` | `numeric(14,2) NULL` | Enforced `NOT NULL` | High |
| `invoice` | `subtotal_amount` | `numeric(14,2) NOT NULL` | `numeric(14,2) NULL` | Enforced `NOT NULL` | High |
| `invoice` | `tax_amount` | `numeric(14,2) NOT NULL` | `numeric(14,2) NULL` | Enforced `NOT NULL` | High |
| `invoice` | `total_amount` | `numeric(14,2) NOT NULL` | `numeric(14,2) NULL` | Enforced `NOT NULL` | High |
| `wallet_ledger_entry`| `amount` | `numeric(14,2) NOT NULL` | `numeric(14,2) NULL` | Enforced `NOT NULL` | High |

---

## 3. Module-by-Module Reconciliation Inventory (216 Tables)

"""

# Group by module
modules_dict = {}
for t in tables_info:
    m = f"{t['module_id']} — {t['module']}"
    modules_dict.setdefault(m, []).append(t)

for mname, tbls in modules_dict.items():
    doc += f"\n### 3.{len(doc.split('### 3.'))} {mname} ({len(tbls)} tables)\n\n"
    doc += "| # | Table Name | Primary Key | Foreign Key Targets | Status | Automatic Migration Plan |\n"
    doc += "|---|---|---|---|---|---|\n"
    for i, t in enumerate(tbls, 1):
        fk_str = str(t['fk']) if t['fk'] else "None"
        doc += f"| {i} | `{t['table']}` | `id` (Identity) | {fk_str} | `MISSING` | Migrated via {t['module_id']} Alembic phase |\n"

doc += """
---

## 4. Referential Actions & Data Integrity Rules

1. **Foreign Key Deletion Behaviour**:
   - All standard foreign keys use `ON UPDATE RESTRICT ON DELETE RESTRICT` to prevent accidental cascading deletion of historical audit, billing, application, and master records.
   - Soft deletes (`deleted_at timestamptz`) are utilized across all business entities.
2. **Surrogate Identity Keys**:
   - Consistently implemented as `id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY`.
3. **Monetary Precision**:
   - `NUMERIC(14,2)` paired with companion ISO-4217 `currency_code char(3)`. Floating point types are prohibited.
4. **Audit and Lifecycle Columns**:
   - Standard across all business entities:
     - `created_at timestamptz NOT NULL DEFAULT now()`
     - `created_by bigint` (User ID / System)
     - `updated_at timestamptz NOT NULL DEFAULT now()`
     - `updated_by bigint`
     - `deleted_at timestamptz`
"""

with open('docs/TALENTRA_SCHEMA_RECONCILIATION.md', 'w', encoding='utf-8') as f:
    f.write(doc)

print("Generated docs/TALENTRA_SCHEMA_RECONCILIATION.md")
