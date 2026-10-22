"""Subscription, Wallet, and Ledger Model Factory."""

import itertools
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.subscription import SubscriptionPlan, Subscription, Wallet, WalletLedgerEntry

_sub_counter = itertools.count(1)


def create_factory_wallet_with_funds(
    db: Session,
    account_id: int,
    initial_balance: Decimal = Decimal("1000.00"),
    currency_code: str = "USD",
) -> Wallet:
    """Create a wallet and seed an initial credit ledger entry."""
    idx = next(_sub_counter)
    wallet = Wallet(
        account_id=account_id,
        currency_code=currency_code,
        status_code_id=1,
    )
    db.add(wallet)
    db.flush()

    if initial_balance > 0:
        db.add(WalletLedgerEntry(
            wallet_id=wallet.id,
            entry_type_code_id=1,  # CREDIT
            amount=initial_balance,
            currency_code=currency_code,
            source_type="FACTORY_SEED",
            source_id=f"FAC_ORDER_{idx}",
            idempotency_key=f"IDEM_FAC_WALLET_{idx}_{int(datetime.now().timestamp())}",
        ))
        db.flush()

    return wallet
