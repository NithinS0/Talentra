import json
import os

with open('backend/app/scratch_phase_plan.json', 'r', encoding='utf-8') as f:
    phases = json.load(f)

with open('backend/app/scratch_indexes.json', 'r', encoding='utf-8') as f:
    indexes = json.load(f)

sql_dir = 'backend/migrations_sql'
os.makedirs(sql_dir, exist_ok=True)

for p in phases:
    rev = f"{p['rev']}_{p['name']}"
    filename = f"{rev}.sql"
    sql = "\n\n".join(p['ddls'])
    with open(os.path.join(sql_dir, filename), 'w', encoding='utf-8') as f:
        f.write(sql)
    print(f"Exported {filename} ({len(p['tables'])} tables)")

# Phase 013: Indexes, Exclusions, Append-Only Triggers
sql_013 = f"""
-- 1. Covering indexes for all 233 foreign keys
{chr(10).join(indexes)}

-- 2. Exclusion constraints using btree_gist
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

-- 3. Append-only trigger function and triggers for immutable tables
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
"""

with open(os.path.join(sql_dir, "013_business_constraints_and_indexes.sql"), 'w', encoding='utf-8') as f:
    f.write(sql_013.strip())

print("Exported 013_business_constraints_and_indexes.sql")
