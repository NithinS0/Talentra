import json
import os
import shutil

with open('backend/app/scratch_phase_plan.json', 'r', encoding='utf-8') as f:
    phases = json.load(f)

with open('backend/app/scratch_indexes.json', 'r', encoding='utf-8') as f:
    indexes = json.load(f)

# Ensure target directories exist
vdirs = ['backend/alembic/versions', 'alembic/versions']
for vd in vdirs:
    os.makedirs(vd, exist_ok=True)

prev_rev = None

for p in phases:
    rev = f"{p['rev']}_{p['name']}"
    filename = f"20261018_{p['rev']}0_{rev}.py"
    desc = p['desc']
    tables = p['tables']
    ddls = p['ddls']
    
    # Escape triple quotes in DDL if any
    joined_ddls = "\n\n".join(ddls)
    # Reverse tables for downgrade
    drop_stmts = "\n".join([f'    op.execute(\'DROP TABLE IF EXISTS "{t}" CASCADE;\')' for t in reversed(tables)])
    
    down_rev_str = f"'{prev_rev}'" if prev_rev else "None"
    
    content = f'''"""Migration {rev}: {desc}

Revision ID: {rev}
Revises: {prev_rev}
Create Date: 2026-10-18 14:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '{rev}'
down_revision: Union[str, None] = {down_rev_str}
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schema creation for {desc} ({len(tables)} tables)
    op.execute("""
{joined_ddls}
    """)


def downgrade() -> None:
    # Warning: Destructive rollback. All data in these tables will be removed.
{drop_stmts}
'''
    for vd in vdirs:
        with open(os.path.join(vd, filename), 'w', encoding='utf-8') as f:
            f.write(content)
            
    print(f"Generated migration {filename} ({len(tables)} tables)")
    prev_rev = rev

# Migration 013: Business Constraints, Covering Indexes & Append-Only Triggers
rev_013 = "013_business_constraints_and_indexes"
filename_013 = f"20261018_0130_{rev_013}.py"
joined_indexes = "\n".join(indexes)

content_013 = f'''"""Migration {rev_013}: Business Constraints, Covering Indexes & Append-Only Triggers

Revision ID: {rev_013}
Revises: {prev_rev}
Create Date: 2026-10-18 14:30:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '{rev_013}'
down_revision: Union[str, None] = '{prev_rev}'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable btree_gist extension for exclusion constraints
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    # 2. Add covering indexes for all 233 foreign keys
    op.execute("""
{joined_indexes}
    """)

    # 3. Add exclusion constraints for non-overlapping subscriptions and gig worker availability
    op.execute("""
    ALTER TABLE "subscription" 
    ADD CONSTRAINT "excl_subscription_licence_period" 
    EXCLUDE USING gist (
        "licence_id" WITH =, 
        tstzrange("valid_from", "valid_to") WITH &&
    );

    ALTER TABLE "gig_worker_availability" 
    ADD CONSTRAINT "excl_gig_worker_availability_window" 
    EXCLUDE USING gist (
        "gig_worker_profile_id" WITH =, 
        tstzrange("starts_at", "ends_at") WITH &&
    );
    """)

    # 4. Create trigger function and triggers for immutable audit and ledger tables
    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_immutable_record_modification()
    RETURNS TRIGGER AS $$
    BEGIN
        RAISE EXCEPTION 'Immutable record violation: updates and deletes are prohibited on %', TG_TABLE_NAME;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS trg_immutable_audit_event ON "audit_event";
    CREATE TRIGGER trg_immutable_audit_event
    BEFORE UPDATE OR DELETE ON "audit_event"
    FOR EACH ROW EXECUTE FUNCTION prevent_immutable_record_modification();

    DROP TRIGGER IF EXISTS trg_immutable_wallet_ledger ON "wallet_ledger_entry";
    CREATE TRIGGER trg_immutable_wallet_ledger
    BEFORE UPDATE OR DELETE ON "wallet_ledger_entry"
    FOR EACH ROW EXECUTE FUNCTION prevent_immutable_record_modification();

    DROP TRIGGER IF EXISTS trg_immutable_payment_transaction ON "payment_transaction";
    CREATE TRIGGER trg_immutable_payment_transaction
    BEFORE UPDATE OR DELETE ON "payment_transaction"
    FOR EACH ROW EXECUTE FUNCTION prevent_immutable_record_modification();

    DROP TRIGGER IF EXISTS trg_immutable_profile_download_history ON "profile_download_history";
    CREATE TRIGGER trg_immutable_profile_download_history
    BEFORE UPDATE OR DELETE ON "profile_download_history"
    FOR EACH ROW EXECUTE FUNCTION prevent_immutable_record_modification();
    """)


def downgrade() -> None:
    # Remove triggers and exclusion constraints
    op.execute("""
    DROP TRIGGER IF EXISTS trg_immutable_audit_event ON "audit_event";
    DROP TRIGGER IF EXISTS trg_immutable_wallet_ledger ON "wallet_ledger_entry";
    DROP TRIGGER IF EXISTS trg_immutable_payment_transaction ON "payment_transaction";
    DROP TRIGGER IF EXISTS trg_immutable_profile_download_history ON "profile_download_history";
    DROP FUNCTION IF EXISTS prevent_immutable_record_modification();

    ALTER TABLE "subscription" DROP CONSTRAINT IF EXISTS "excl_subscription_licence_period";
    ALTER TABLE "gig_worker_availability" DROP CONSTRAINT IF EXISTS "excl_gig_worker_availability_window";
    """)
'''

for vd in vdirs:
    with open(os.path.join(vd, filename_013), 'w', encoding='utf-8') as f:
        f.write(content_013)

print(f"Generated migration {filename_013} (Indexes, Exclusions, Append-Only Triggers)")
