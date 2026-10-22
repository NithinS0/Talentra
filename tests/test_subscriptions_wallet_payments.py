"""Automated Functional, Financial Integrity & Concurrency Tests for Talentra Stage 11: Subscriptions, Wallet & Payments.

Maps strictly to approved test cases in Talentra_Final_Test_Cases_All_Modules.xlsx (Sheet: Subscriptions Wallet Payments &):
- FR-0124: Subscription period validity (end not before start, non-overlapping active periods per licence)
- FR-0125: Payment idempotency (duplicate external events handled idempotently without duplicate charges/credits)
- FR-0126: No card/bank data storage (only transaction references, amounts and masked metadata; zero PAN/CVV)
- FR-0127: Money decimal precision (Numeric(14, 2) + ISO 4217 companion currency code)
- FR-0128: Wallet balance consistency (balance equals algebraic sum of ledger entries)
- FR-0129: Append-only wallet ledger (corrections are new entries referencing original, never updates)
- FR-0130: Insufficient credit deduction (credits cannot be consumed below permitted balance)
- FR-0131: Concurrent wallet deductions (balance check and deduction are atomic under concurrency)
- FR-0132: Profile download history (append-only history linking actor, candidate, timestamp, and credit charge)
- FR-0133: Refund references original payment (cannot exceed refundable amount)
- FR-0134: Invoice totals (invoice lines, tax, and total match rounded decimal rules)
- FR-0135: Subscription cancellation (records cancelled_at effective date and preserves payment history)
- FR-0136: Payment failure recovery (timeout recovery does not duplicate financial impact)
- FR-0137: Entitlement enforcement (features and limits are governed by active subscription entitlements)
- FR-0138: Wallet ledger correction linkage (correction references original transaction via original_entry_id)
- FR-0206: Payment ledger correction never overwrites original (ledger is append-only; original record unchanged)
"""

import sys
import os
import uuid
import threading
from typing import Tuple, List, Optional, Dict
from decimal import Decimal
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_test_supabase_token
from app.models.country import Country
from app.models.user import User, Role, UserRoleAssignment
from app.models.organisation import Organisation, Account, AccountOrganisation, AccountAdminAssignment
from app.models.licence import Licence
from app.models.candidate import CandidateProfile
from app.models.subscription import (
    SubscriptionPlan,
    PlanEntitlement,
    Subscription,
    PaymentOrder,
    PaymentTransaction,
    Invoice,
    Wallet,
    WalletLedgerEntry,
    CreditConsumption,
    ProfileDownloadHistory,
    PaymentRefund,
    PaymentWebhookEvent,
)
from app.services.subscription_service import SubscriptionService, SUBSCRIPTION_STATUS, WALLET_ENTRY_TYPE


@pytest.fixture(scope="session")
def test_engine():
    """Create test SQLite engine with static pool."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def do_connect(dbapi_connection, connection_record):
        dbapi_connection.isolation_level = None

    with engine.begin() as conn:
        Base.metadata.create_all(bind=conn)

    return engine


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Provide transactional database session for tests."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Provide FastAPI test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_roles(db_session):
    """Seed system roles."""
    roles = [
        Role(role_code="SUPER_ADMIN", display_name="Super Administrator", description="Platform Admin", is_system_role=True),
        Role(role_code="ADMIN", display_name="Platform Administrator", description="Admin", is_system_role=True),
        Role(role_code="ACCOUNT_ADMIN", display_name="Account Administrator", description="Account Admin", is_system_role=True),
        Role(role_code="EMPLOYER", display_name="Employer", description="Hiring org", is_system_role=False),
        Role(role_code="RECRUITER", display_name="Recruiter", description="Recruiter", is_system_role=False),
        Role(role_code="CANDIDATE", display_name="Candidate", description="Job seeker", is_system_role=False),
    ]
    roles_dict = {}
    for r in roles:
        existing = db_session.query(Role).filter(Role.role_code == r.role_code).first()
        if not existing:
            db_session.add(r)
            db_session.flush()
            roles_dict[r.role_code] = r
        else:
            roles_dict[r.role_code] = existing
    db_session.commit()
    return roles_dict


def _create_user(db_session, role_code: str = "EMPLOYER") -> User:
    """Helper to create a test user with assigned role."""
    uid = uuid.uuid4().hex[:8]
    sub = f"auth0|usr_{uid}"
    email = f"user_{uid}@talentra.test"
    now = datetime.now(timezone.utc)

    user = User(
        email_address=email,
        display_name=f"User {uid}",
        provider_subject=sub,
        account_status_code_id=1,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    db_session.flush()

    role = db_session.query(Role).filter(Role.role_code == role_code).first()
    if role:
        db_session.add(UserRoleAssignment(
            user_id=user.id,
            role_id=role.id,
            assigned_by_user_id=user.id,
            valid_from=now,
            created_at=now,
        ))
        db_session.flush()
    db_session.commit()
    return user


def _create_account_and_org(db_session, user: User) -> Tuple[Account, Organisation]:
    """Helper to create an account and organisation."""
    uid = uuid.uuid4().hex[:6]
    now = datetime.now(timezone.utc)

    country = db_session.query(Country).filter(Country.alpha3_code == "USA").first()
    if not country:
        country = Country(
            country_code="US",
            alpha3_code="USA",
            numeric_code="840",
            name="United States",
            is_active=True,
        )
        db_session.add(country)
        db_session.flush()

    org = Organisation(
        legal_name=f"Org {uid} Ltd",
        display_name=f"Org {uid}",
        organisation_type_code_id=1,
        primary_country_id=country.id,
        status_code_id=1,
        created_by=user.id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(org)
    db_session.flush()


    account = Account(
        account_code=f"ACC-{uid.upper()}",
        account_name=f"Account {uid}",
        status_code_id=1,
        root_organisation_id=org.id,
        created_by=user.id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(account)
    db_session.flush()

    db_session.add(AccountOrganisation(
        account_id=account.id,
        organisation_id=org.id,
        name="Primary",
        created_by=user.id,
        created_at=now,
    ))
    db_session.commit()
    return account, org



def _auth_headers(user: User) -> dict:
    """Helper to generate bearer token headers matching Supabase Auth."""
    token = create_test_supabase_token(sub=user.provider_subject, email=user.email_address)
    return {"Authorization": f"Bearer {token}"}



def _create_licence(db_session, account_id: int) -> Licence:
    """Helper to create a licence for subscription tests."""
    now = datetime.now(timezone.utc)
    licence = Licence(
        licence_code=f"LIC-{uuid.uuid4().hex[:8].upper()}",
        account_id=account_id,
        max_users=5,
        max_devices_per_user=2,
        valid_from=now - timedelta(days=1),
        valid_until=now + timedelta(days=365),
        status_code_id=1,
        created_at=now,
        updated_at=now,
    )
    db_session.add(licence)
    db_session.commit()
    db_session.refresh(licence)
    return licence


def _create_plan_with_entitlements(db_session, plan_code: str = "ENTERPRISE_PRO") -> SubscriptionPlan:
    """Helper to create a subscription plan with entitlements."""
    now = datetime.now(timezone.utc)
    plan = db_session.query(SubscriptionPlan).filter(SubscriptionPlan.plan_code == plan_code).first()
    if not plan:
        plan = SubscriptionPlan(
            plan_code=plan_code,
            name="Enterprise Pro Plan",
            price_amount=Decimal("499.00"),
            currency_code="USD",
            billing_interval_code_id=1,
            active=True,
            created_at=now,
            updated_at=now,
        )
        db_session.add(plan)
        db_session.flush()

        entitlement = PlanEntitlement(
            subscription_plan_id=plan.id,
            code="candidate_search",
            name="Advanced Candidate Search",
            status_code_id=1,
            created_at=now,
            updated_at=now,
        )
        db_session.add(entitlement)
        db_session.commit()
        db_session.refresh(plan)
    return plan


# =========================================================================
# TEST CASES: FR-0124 through FR-0138, FR-0206
# =========================================================================

def test_fr0124_subscription_period_validity(db_session, seed_roles):
    """FR-0124: Subscription period validity - end must not precede start, and non-overlapping active periods per licence."""
    user = _create_user(db_session, "ACCOUNT_ADMIN")
    account, org = _create_account_and_org(db_session, user)
    licence = _create_licence(db_session, account.id)
    plan = _create_plan_with_entitlements(db_session)

    now = datetime.now(timezone.utc)
    start_time = now
    end_time = now + timedelta(days=30)

    # 1. Reject when end precedes start
    with pytest.raises(ValueError, match="ends_at must not precede starts_at"):
        SubscriptionService.create_subscription(
            db=db_session,
            account_id=account.id,
            plan_id=plan.id,
            starts_at=end_time,
            ends_at=start_time,
            licence_id=licence.id,
        )

    # 2. Successfully create initial active subscription
    sub1 = SubscriptionService.create_subscription(
        db=db_session,
        account_id=account.id,
        plan_id=plan.id,
        starts_at=start_time,
        ends_at=end_time,
        licence_id=licence.id,
    )
    assert sub1.id is not None
    assert sub1.status_code_id == SUBSCRIPTION_STATUS["ACTIVE"]

    # 3. Reject overlapping active subscription period for same licence
    overlapping_start = start_time + timedelta(days=10)
    overlapping_end = end_time + timedelta(days=10)
    with pytest.raises(ValueError, match="overlaps with existing active subscription"):
        SubscriptionService.create_subscription(
            db=db_session,
            account_id=account.id,
            plan_id=plan.id,
            starts_at=overlapping_start,
            ends_at=overlapping_end,
            licence_id=licence.id,
        )

    # 4. Allow adjacent non-overlapping period (starts exactly when sub1 ends)
    adjacent_start = end_time
    adjacent_end = end_time + timedelta(days=30)
    sub2 = SubscriptionService.create_subscription(
        db=db_session,
        account_id=account.id,
        plan_id=plan.id,
        starts_at=adjacent_start,
        ends_at=adjacent_end,
        licence_id=licence.id,
    )
    assert sub2.id is not None
    assert sub2.id != sub1.id


def test_fr0125_payment_idempotency(db_session, seed_roles):
    """FR-0125: Payment idempotency - duplicate external events/orders handled idempotently without duplicate charges/credits."""
    user = _create_user(db_session, "EMPLOYER")
    account, org = _create_account_and_org(db_session, user)

    idempotency_key = f"order-idem-{uuid.uuid4().hex}"
    amount = Decimal("100.00")

    # 1. Create order
    order1 = SubscriptionService.create_payment_order(
        db=db_session,
        account_id=account.id,
        amount=amount,
        currency_code="USD",
        idempotency_key=idempotency_key,
    )

    # 2. Resubmit with same idempotency key - returns same order without creating duplicate
    order2 = SubscriptionService.create_payment_order(
        db=db_session,
        account_id=account.id,
        amount=amount,
        currency_code="USD",
        idempotency_key=idempotency_key,
    )
    assert order1.id == order2.id

    # 3. Duplicate payment webhook event handling
    event_id = f"evt_{uuid.uuid4().hex[:12]}"
    trans1 = SubscriptionService.process_payment_webhook(
        db=db_session,
        event_id=event_id,
        provider_order_reference=order1.provider_order_reference,
        provider_transaction_reference=f"txn_{uuid.uuid4().hex[:12]}",
        status="SUCCEEDED",
        amount=amount,
        currency_code="USD",
        idempotency_key=f"wh-{event_id}",
    )
    assert trans1.id is not None

    wallet = SubscriptionService.get_or_create_wallet(db_session, account.id)
    initial_balance = SubscriptionService.get_wallet_balance(db_session, wallet.id)
    assert initial_balance == Decimal("100.00")

    # Replay identical webhook event: must be idempotently ignored without duplicate wallet credits
    trans2 = SubscriptionService.process_payment_webhook(
        db=db_session,
        event_id=event_id,
        provider_order_reference=order1.provider_order_reference,
        provider_transaction_reference=trans1.provider_transaction_reference,
        status="SUCCEEDED",
        amount=amount,
        currency_code="USD",
        idempotency_key=f"wh-{event_id}",
    )
    assert trans2.id == trans1.id

    # Verify wallet balance remained $100.00, not doubled to $200.00
    rechecked_balance = SubscriptionService.get_wallet_balance(db_session, wallet.id)
    assert rechecked_balance == Decimal("100.00")


def test_fr0126_no_card_bank_data_storage(db_session, seed_roles):
    """FR-0126: No card/bank data storage - platform stores transaction references and masked metadata, zero raw card/bank data."""
    user = _create_user(db_session, "EMPLOYER")
    account, org = _create_account_and_org(db_session, user)

    order = SubscriptionService.create_payment_order(
        db=db_session,
        account_id=account.id,
        amount=Decimal("50.00"),
        currency_code="USD",
        idempotency_key=f"card-test-{uuid.uuid4().hex}",
    )

    # Ingest webhook with simulated payload containing attempts to pass raw card info
    event_id = f"evt_{uuid.uuid4().hex[:12]}"
    raw_payload_with_card = {
        "event_id": event_id,
        "card_number": "4111111111111234",
        "cvv": "123",
        "card_brand": "VISA",
        "masked_card": "**** **** **** 1234",
    }

    trans = SubscriptionService.process_payment_webhook(
        db=db_session,
        event_id=event_id,
        provider_order_reference=order.provider_order_reference,
        provider_transaction_reference=f"txn_{uuid.uuid4().hex[:12]}",
        status="SUCCEEDED",
        amount=Decimal("50.00"),
        currency_code="USD",
        idempotency_key=f"wh-{event_id}",
        raw_metadata=raw_payload_with_card,
    )

    # Scan payment_webhook_event to verify raw PAN & CVV are redacted
    webhook_event = db_session.query(PaymentWebhookEvent).order_by(PaymentWebhookEvent.id.desc()).first()
    assert webhook_event.metadata_redacted.get("card_number") == "[REDACTED]"
    assert webhook_event.metadata_redacted.get("cvv") == "[REDACTED]"

    # Verify model table columns: ensure no column exists for raw PAN, CVV, or banking passwords
    table_columns = [col.name.lower() for col in PaymentTransaction.__table__.columns]
    assert "card_number" not in table_columns
    assert "cvv" not in table_columns
    assert "cvc" not in table_columns
    assert "bank_account_number" not in table_columns


def test_fr0127_money_decimal_precision(db_session, seed_roles):
    """FR-0127: Money decimal precision - fixed 2-decimal precision (Numeric(14,2)) and companion ISO 4217 currency code."""
    user = _create_user(db_session, "EMPLOYER")
    account, org = _create_account_and_org(db_session, user)

    # Order with amount requiring standard rounding
    amount = Decimal("99.994")  # Should quantize to 99.99
    order = SubscriptionService.create_payment_order(
        db=db_session,
        account_id=account.id,
        amount=amount,
        currency_code="USD",
        idempotency_key=f"prec-{uuid.uuid4().hex}",
    )

    assert order.amount == Decimal("99.99")
    assert order.currency_code == "USD"

    # Wallet entry precision
    wallet = SubscriptionService.get_or_create_wallet(db_session, account.id, currency_code="EUR")
    entry = SubscriptionService.credit_wallet(
        db=db_session,
        wallet_id=wallet.id,
        amount=Decimal("123.456"),  # Rounds to 123.46
        idempotency_key=f"prec-w-{uuid.uuid4().hex}",
        currency_code="EUR",
    )
    assert entry.amount == Decimal("123.46")
    assert entry.currency_code == "EUR"


def test_fr0128_wallet_balance_consistency(db_session, seed_roles):
    """FR-0128: Wallet balance consistency - balance equals algebraic sum of ledger entries."""
    user = _create_user(db_session, "EMPLOYER")
    account, org = _create_account_and_org(db_session, user)

    wallet = SubscriptionService.get_or_create_wallet(db_session, account.id)

    # 1. Initial balance is 0.00
    assert SubscriptionService.get_wallet_balance(db_session, wallet.id) == Decimal("0.00")

    # 2. Credits: $150.00 + $50.00 = $200.00
    SubscriptionService.credit_wallet(db_session, wallet.id, Decimal("150.00"), f"c1-{uuid.uuid4().hex}")
    SubscriptionService.credit_wallet(db_session, wallet.id, Decimal("50.00"), f"c2-{uuid.uuid4().hex}")
    assert SubscriptionService.get_wallet_balance(db_session, wallet.id) == Decimal("200.00")

    # 3. Debit: -$75.00 -> $125.00
    SubscriptionService.debit_wallet(db_session, wallet.id, Decimal("75.00"), f"d1-{uuid.uuid4().hex}")
    assert SubscriptionService.get_wallet_balance(db_session, wallet.id) == Decimal("125.00")


def test_fr0129_append_only_wallet_ledger(db_session, seed_roles):
    """FR-0129: Append-only wallet ledger - corrections are new entries referencing original, never updates or deletes."""
    user = _create_user(db_session, "ADMIN")
    account, org = _create_account_and_org(db_session, user)

    wallet = SubscriptionService.get_or_create_wallet(db_session, account.id)
    entry = SubscriptionService.credit_wallet(db_session, wallet.id, Decimal("100.00"), f"entry-{uuid.uuid4().hex}")

    orig_id = entry.id
    orig_amount = entry.amount
    orig_key = entry.idempotency_key

    # Post correction entry
    correction = SubscriptionService.correct_wallet_ledger(
        db=db_session,
        original_entry_id=orig_id,
        adjustment_amount=Decimal("-20.00"),
        idempotency_key=f"corr-{uuid.uuid4().hex}",
        reason="Adjustment for erroneous over-credit",
        actor_user_id=user.id,
    )

    # Verify correction is a distinct new entry
    assert correction.id != orig_id
    assert correction.original_entry_id == orig_id
    assert correction.entry_type_code_id == WALLET_ENTRY_TYPE["CORRECTION"]

    # Verify original entry remains completely untouched
    db_session.refresh(entry)
    assert entry.amount == orig_amount
    assert entry.idempotency_key == orig_key

    # Balance correctly reflects original plus correction ($100 - $20 = $80)
    assert SubscriptionService.get_wallet_balance(db_session, wallet.id) == Decimal("80.00")


def test_fr0130_insufficient_credit_deduction(db_session, seed_roles):
    """FR-0130: Insufficient credit deduction - credits cannot be consumed below permitted balance; atomic failure without balance change."""
    user = _create_user(db_session, "EMPLOYER")
    account, org = _create_account_and_org(db_session, user)

    wallet = SubscriptionService.get_or_create_wallet(db_session, account.id)
    SubscriptionService.credit_wallet(db_session, wallet.id, Decimal("10.00"), f"init-{uuid.uuid4().hex}")

    # Attempt to debit $25.00 when only $10.00 available
    with pytest.raises(ValueError, match="Insufficient wallet credits"):
        SubscriptionService.debit_wallet(
            db=db_session,
            wallet_id=wallet.id,
            amount=Decimal("25.00"),
            idempotency_key=f"fail-debit-{uuid.uuid4().hex}",
        )

    # Assert balance remains strictly unchanged at $10.00
    assert SubscriptionService.get_wallet_balance(db_session, wallet.id) == Decimal("10.00")


def test_fr0131_concurrent_wallet_deductions(test_engine, seed_roles):
    """FR-0131: Concurrent wallet deductions - balance check and deduction are atomic; parallel deductions never produce negative balance."""
    # Create isolated session for setup
    session_factory = sessionmaker(bind=test_engine)
    setup_db = session_factory()

    user = _create_user(setup_db, "EMPLOYER")
    account, org = _create_account_and_org(setup_db, user)
    wallet = SubscriptionService.get_or_create_wallet(setup_db, account.id)

    # Fund wallet with $10.00
    SubscriptionService.credit_wallet(setup_db, wallet.id, Decimal("10.00"), f"fund-{uuid.uuid4().hex}")
    wallet_id = wallet.id
    setup_db.close()


    # Launch two concurrent threads both trying to debit $10.00
    results = {"success": 0, "failed": 0}
    lock = threading.Lock()

    def run_debit():
        db = session_factory()
        try:
            SubscriptionService.debit_wallet(
                db=db,
                wallet_id=wallet_id,
                amount=Decimal("10.00"),
                idempotency_key=f"race-{uuid.uuid4().hex}",
            )
            with lock:
                results["success"] += 1
        except ValueError:
            with lock:
                results["failed"] += 1
        finally:
            db.close()

    t1 = threading.Thread(target=run_debit)
    t2 = threading.Thread(target=run_debit)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exactly one thread succeeds, and the other fails due to insufficient balance
    assert results["success"] == 1
    assert results["failed"] == 1

    # Verify final balance is $0.00, never negative
    check_db = session_factory()
    final_balance = SubscriptionService.get_wallet_balance(check_db, wallet_id)
    assert final_balance == Decimal("0.00")
    check_db.close()


def test_fr0132_profile_download_history(db_session, seed_roles):
    """FR-0132: Profile download history - append-only history linked to credit consumption containing actor, candidate, timestamp, charge."""
    user = _create_user(db_session, "RECRUITER")
    account, org = _create_account_and_org(db_session, user)

    # Create candidate profile
    cand_user = _create_user(db_session, "CANDIDATE")
    cand_profile = CandidateProfile(
        user_id=cand_user.id,
        actor_id=f"CA{uuid.uuid4().hex[:5].upper()}",
        first_name="Jane",
        last_name="Doe",
        headline="Senior Distributed Systems Architect",
        profile_status_code_id=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(cand_profile)
    db_session.commit()


    wallet = SubscriptionService.get_or_create_wallet(db_session, account.id)
    SubscriptionService.credit_wallet(db_session, wallet.id, Decimal("5.00"), f"credits-{uuid.uuid4().hex}")

    history, consumption = SubscriptionService.download_candidate_profile(
        db=db_session,
        account_id=account.id,
        recruiter_user_id=user.id,
        candidate_profile_id=cand_profile.id,
        organisation_id=org.id,
        credits_cost=Decimal("1.00"),
    )

    assert history.id is not None
    assert history.candidate_profile_id == cand_profile.id
    assert history.actor_user_id == user.id
    assert history.credit_consumption_id == consumption.id
    assert consumption.amount == Decimal("1.00")

    # Wallet balance deducted by 1.00 ($5.00 - $1.00 = $4.00)
    assert SubscriptionService.get_wallet_balance(db_session, wallet.id) == Decimal("4.00")


def test_fr0133_refund_references_original_payment(db_session, seed_roles):
    """FR-0133: Refund references original payment - refund references original transaction and cannot exceed refundable amount."""
    user = _create_user(db_session, "ACCOUNT_ADMIN")
    account, org = _create_account_and_org(db_session, user)

    order = SubscriptionService.create_payment_order(
        db=db_session,
        account_id=account.id,
        amount=Decimal("100.00"),
        currency_code="USD",
        idempotency_key=f"ord-ref-{uuid.uuid4().hex}",
    )
    trans = SubscriptionService.process_payment_webhook(
        db=db_session,
        event_id=f"evt_{uuid.uuid4().hex[:12]}",
        provider_order_reference=order.provider_order_reference,
        provider_transaction_reference=f"txn_{uuid.uuid4().hex[:12]}",
        status="SUCCEEDED",
        amount=Decimal("100.00"),
        currency_code="USD",
        idempotency_key=f"wh-ref-{uuid.uuid4().hex}",
    )

    # 1. Partial refund of $40.00 succeeds
    refund1 = SubscriptionService.process_refund(
        db=db_session,
        payment_transaction_id=trans.id,
        refund_amount=Decimal("40.00"),
        idempotency_key=f"ref1-{uuid.uuid4().hex}",
    )
    assert refund1.id is not None
    assert refund1.amount == Decimal("40.00")

    # 2. Attempt to refund $70.00 exceeds remaining $60.00 refundable amount -> rejected
    with pytest.raises(ValueError, match="exceeds remaining refundable amount"):
        SubscriptionService.process_refund(
            db=db_session,
            payment_transaction_id=trans.id,
            refund_amount=Decimal("70.00"),
            idempotency_key=f"ref2-{uuid.uuid4().hex}",
        )

    # 3. Exact remaining refund of $60.00 succeeds
    refund2 = SubscriptionService.process_refund(
        db=db_session,
        payment_transaction_id=trans.id,
        refund_amount=Decimal("60.00"),
        idempotency_key=f"ref3-{uuid.uuid4().hex}",
    )
    assert refund2.id is not None

    # 4. Any further refund rejected as total already fully refunded
    with pytest.raises(ValueError, match="exceeds remaining refundable amount"):
        SubscriptionService.process_refund(
            db=db_session,
            payment_transaction_id=trans.id,
            refund_amount=Decimal("1.00"),
            idempotency_key=f"ref4-{uuid.uuid4().hex}",
        )


def test_fr0134_invoice_totals(db_session, seed_roles):
    """FR-0134: Invoice totals - invoice lines, tax and total use defined rounding and decimal arithmetic rules."""
    user = _create_user(db_session, "ACCOUNT_ADMIN")
    account, org = _create_account_and_org(db_session, user)

    # Subtotal $125.50 with 10% tax = $12.55 tax, total = $138.05
    invoice = SubscriptionService.generate_invoice(
        db=db_session,
        account_id=account.id,
        subtotal=Decimal("125.50"),
        tax_rate=Decimal("0.10"),
        currency_code="USD",
    )

    assert invoice.subtotal_amount == Decimal("125.50")
    assert invoice.tax_amount == Decimal("12.55")
    assert invoice.total_amount == Decimal("138.05")
    assert invoice.total_amount == invoice.subtotal_amount + invoice.tax_amount


def test_fr0135_subscription_cancellation(db_session, seed_roles):
    """FR-0135: Subscription cancellation - cancellation records effective date and does not erase payment history."""
    user = _create_user(db_session, "ACCOUNT_ADMIN")
    account, org = _create_account_and_org(db_session, user)
    plan = _create_plan_with_entitlements(db_session)

    now = datetime.now(timezone.utc)
    sub = SubscriptionService.create_subscription(
        db=db_session,
        account_id=account.id,
        plan_id=plan.id,
        starts_at=now,
        ends_at=now + timedelta(days=30),
    )

    # Create associated payment order
    order = SubscriptionService.create_payment_order(
        db=db_session,
        account_id=account.id,
        amount=plan.price_amount,
        currency_code="USD",
        idempotency_key=f"ord-cancel-{uuid.uuid4().hex}",
    )

    # Cancel subscription
    cancelled_sub = SubscriptionService.cancel_subscription(
        db=db_session,
        subscription_id=sub.id,
        reason="Switching to custom enterprise agreement",
        actor_user_id=user.id,
    )

    assert cancelled_sub.status_code_id == SUBSCRIPTION_STATUS["CANCELLED"]
    assert cancelled_sub.cancelled_at is not None

    # Assert payment history remains completely preserved
    persisted_order = db_session.query(PaymentOrder).filter(PaymentOrder.id == order.id).first()
    assert persisted_order is not None
    assert persisted_order.amount == plan.price_amount


def test_fr0136_payment_failure_recovery(db_session, seed_roles):
    """FR-0136: Payment failure recovery - unknown outcome is reconciled using provider reference/idempotency key without duplicate charges."""
    user = _create_user(db_session, "EMPLOYER")
    account, org = _create_account_and_org(db_session, user)

    idempotency_key = f"recov-{uuid.uuid4().hex}"
    order = SubscriptionService.create_payment_order(
        db=db_session,
        account_id=account.id,
        amount=Decimal("150.00"),
        currency_code="USD",
        idempotency_key=idempotency_key,
    )

    # Ingest FAILED webhook (simulating timeout or card decline)
    event_id = f"evt_{uuid.uuid4().hex[:12]}"
    trans_fail = SubscriptionService.process_payment_webhook(
        db=db_session,
        event_id=event_id,
        provider_order_reference=order.provider_order_reference,
        provider_transaction_reference=f"txn_{uuid.uuid4().hex[:12]}",
        status="FAILED",
        amount=Decimal("150.00"),
        currency_code="USD",
        idempotency_key=f"wh-fail-{idempotency_key}",
    )
    assert trans_fail.status_code_id == 2  # FAILED
    assert order.status_code_id == 3  # FAILED

    wallet = SubscriptionService.get_or_create_wallet(db_session, account.id)
    # Wallet balance was NOT credited on failure
    assert SubscriptionService.get_wallet_balance(db_session, wallet.id) == Decimal("0.00")

    # Reconcile retry with same event: no false credit
    trans_retry = SubscriptionService.process_payment_webhook(
        db=db_session,
        event_id=event_id,
        provider_order_reference=order.provider_order_reference,
        provider_transaction_reference=trans_fail.provider_transaction_reference,
        status="FAILED",
        amount=Decimal("150.00"),
        currency_code="USD",
        idempotency_key=f"wh-fail-{idempotency_key}",
    )
    assert trans_retry.id == trans_fail.id
    assert SubscriptionService.get_wallet_balance(db_session, wallet.id) == Decimal("0.00")


def test_fr0137_entitlement_enforcement(db_session, seed_roles):
    """FR-0137: Entitlement enforcement - features and limits are governed by active subscription entitlements."""
    user = _create_user(db_session, "EMPLOYER")
    account, org = _create_account_and_org(db_session, user)
    plan = _create_plan_with_entitlements(db_session)

    # 1. No subscription -> entitlement denied
    assert SubscriptionService.check_entitlement(db_session, account.id, "candidate_search") is False

    # 2. Active subscription created -> entitlement granted
    now = datetime.now(timezone.utc)
    sub = SubscriptionService.create_subscription(
        db=db_session,
        account_id=account.id,
        plan_id=plan.id,
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=29),
    )
    assert SubscriptionService.check_entitlement(db_session, account.id, "candidate_search") is True

    # 3. Non-existent entitlement code -> denied
    assert SubscriptionService.check_entitlement(db_session, account.id, "unlimited_concierge") is False

    # 4. Cancelled subscription -> entitlement immediately revoked
    SubscriptionService.cancel_subscription(db_session, sub.id, "Plan terminated")
    assert SubscriptionService.check_entitlement(db_session, account.id, "candidate_search") is False


def test_fr0138_wallet_ledger_correction_linkage(db_session, seed_roles):
    """FR-0138: Wallet ledger correction linkage - correction must reference original transaction via original_entry_id and use compensating entry."""
    user = _create_user(db_session, "ADMIN")
    account, org = _create_account_and_org(db_session, user)

    wallet = SubscriptionService.get_or_create_wallet(db_session, account.id)
    entry = SubscriptionService.credit_wallet(db_session, wallet.id, Decimal("250.00"), f"entry-{uuid.uuid4().hex}")

    correction = SubscriptionService.correct_wallet_ledger(
        db=db_session,
        original_entry_id=entry.id,
        adjustment_amount=Decimal("-50.00"),
        idempotency_key=f"corr-{uuid.uuid4().hex}",
        reason="Over-credit reconciliation",
    )

    assert correction.original_entry_id == entry.id
    assert correction.source_type == "CORRECTION"
    assert correction.source_id == str(entry.id)
    assert correction.amount == Decimal("-50.00")


def test_fr0206_payment_ledger_correction_never_overwrites_original(db_session, seed_roles):
    """FR-0206: Payment ledger correction never overwrites original - ledger is append-only; original record remains unmodified."""
    user = _create_user(db_session, "ADMIN")
    account, org = _create_account_and_org(db_session, user)

    wallet = SubscriptionService.get_or_create_wallet(db_session, account.id)
    original_entry = SubscriptionService.credit_wallet(
        db=db_session,
        wallet_id=wallet.id,
        amount=Decimal("300.00"),
        idempotency_key=f"orig-{uuid.uuid4().hex}",
        source_type="PAYMENT_ORDER",
        source_id="ORD-999",
    )

    # Snapshot original record values
    orig_dict = {
        "id": original_entry.id,
        "wallet_id": original_entry.wallet_id,
        "amount": original_entry.amount,
        "entry_type_code_id": original_entry.entry_type_code_id,
        "currency_code": original_entry.currency_code,
        "source_type": original_entry.source_type,
        "source_id": original_entry.source_id,
        "idempotency_key": original_entry.idempotency_key,
    }

    # Post compensating correction
    correction_entry = SubscriptionService.correct_wallet_ledger(
        db=db_session,
        original_entry_id=original_entry.id,
        adjustment_amount=Decimal("-100.00"),
        idempotency_key=f"corr-{uuid.uuid4().hex}",
        reason="Compensating debit for billing adjustment",
    )

    # Assert new row was inserted
    assert correction_entry.id != original_entry.id

    # Verify original row has identical values (zero field mutation)
    db_session.refresh(original_entry)
    for field, val in orig_dict.items():
        assert getattr(original_entry, field) == val, f"Field {field} on original ledger entry was modified!"


# =========================================================================
# END-TO-END FASTAPI HTTP INTEGRATION TESTS
# =========================================================================

def test_api_subscriptions_and_wallet_flow(client, db_session, seed_roles):
    """End-to-end HTTP API flow for plans, subscriptions, wallet balance, and credits."""
    user = _create_user(db_session, "ACCOUNT_ADMIN")
    account, org = _create_account_and_org(db_session, user)
    plan = _create_plan_with_entitlements(db_session)
    headers = _auth_headers(user)

    # 1. GET /api/v1/subscriptions/plans
    res = client.get("/api/v1/subscriptions/plans", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    plans = res.json()
    assert len(plans) >= 1
    assert any(p["plan_code"] == plan.plan_code for p in plans)

    # 2. POST /api/v1/subscriptions
    licence = _create_licence(db_session, account.id)
    now = datetime.now(timezone.utc)
    sub_payload = {
        "account_id": account.id,
        "plan_id": plan.id,
        "licence_id": licence.id,
        "starts_at": now.isoformat(),
        "ends_at": (now + timedelta(days=30)).isoformat(),
        "auto_renew": False,
        "seats_allocated": 1,
    }

    res = client.post("/api/v1/subscriptions", json=sub_payload, headers=headers)
    assert res.status_code == status.HTTP_201_CREATED
    sub_data = res.json()
    assert sub_data["account_id"] == account.id
    sub_id = sub_data["id"]


    # 3. GET /api/v1/subscriptions/entitlements/check
    res = client.get(
        f"/api/v1/subscriptions/entitlements/check?account_id={account.id}&feature_key=candidate_search",
        headers=headers,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["granted"] is True

    # 4. POST /api/v1/subscriptions/{id}/cancel
    res = client.post(
        f"/api/v1/subscriptions/{sub_id}/cancel",
        json={"reason": "Customer cancellation test"},
        headers=headers,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["cancelled_at"] is not None

    # 5. GET /api/v1/wallet/{account_id}
    res = client.get(f"/api/v1/wallet/{account.id}", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    wallet_data = res.json()
    wallet_id = wallet_data["id"]

    # 6. POST /api/v1/wallet/{wallet_id}/credit
    res = client.post(
        f"/api/v1/wallet/{wallet_id}/credit",
        json={
            "amount": "250.00",
            "currency_code": "USD",
            "idempotency_key": f"credit-api-{uuid.uuid4().hex}",
            "description": "API Credit Topup",
        },
        headers=headers,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["balance_after"] == "250.00"

    # 7. POST /api/v1/payments/invoices
    res = client.post(
        f"/api/v1/payments/invoices?account_id={account.id}&subtotal=200.00&tax_rate=0.10",
        headers=headers,
    )
    assert res.status_code == status.HTTP_201_CREATED
    inv_data = res.json()
    assert inv_data["subtotal_amount"] == "200.00"
    assert inv_data["tax_amount"] == "20.00"
    assert inv_data["total_amount"] == "220.00"
