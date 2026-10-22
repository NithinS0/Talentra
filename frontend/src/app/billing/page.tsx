"use client";

import { useEffect, useState, useCallback } from "react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  CreditCard,
  Wallet,
  Receipt,
  PlusCircle,
  AlertCircle,
  CheckCircle2,
  Loader2,
  TrendingDown,
  TrendingUp,
  FileText,
  Clock,
  RotateCcw,
} from "lucide-react";
import {
  getSubscriptionPlans,
  getAccountWallet,
  creditWallet,
  debitWallet,
  correctWalletLedger,
  createPaymentOrder,
  createSubscription,
  cancelSubscription,
} from "@/lib/api/subscriptions";
import {
  SubscriptionPlanResponse,
  WalletResponse,
  WalletLedgerEntryResponse,
  PaymentOrderResponse,
  SubscriptionResponse,
} from "@/types/subscriptions";
import { formatDate } from "@/lib/utils";

export default function BillingPage() {
  const [plans, setPlans] = useState<SubscriptionPlanResponse[]>([]);
  const [wallet, setWallet] = useState<WalletResponse | null>(null);
  const [ledgerEntries, setLedgerEntries] = useState<WalletLedgerEntryResponse[]>([]);
  const [recentOrders, setRecentOrders] = useState<PaymentOrderResponse[]>([]);
  const [activeSubscription, setActiveSubscription] = useState<SubscriptionResponse | null>(null);

  const [accountId, setAccountId] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Forms
  const [creditAmount, setCreditAmount] = useState<string>("");
  const [creditDescription, setCreditDescription] = useState<string>("");
  const [isCrediting, setIsCrediting] = useState<boolean>(false);

  const [debitAmount, setDebitAmount] = useState<string>("");
  const [debitPurpose, setDebitPurpose] = useState<string>("");
  const [isDebiting, setIsDebiting] = useState<boolean>(false);

  // Ledger Correction (FR-0138, FR-0206)
  const [correctionEntryId, setCorrectionEntryId] = useState<string>("");
  const [correctionAmount, setCorrectionAmount] = useState<string>("");
  const [correctionReason, setCorrectionReason] = useState<string>("");
  const [isCorrecting, setIsCorrecting] = useState<boolean>(false);

  // Payment Order (FR-0125)
  const [orderAmount, setOrderAmount] = useState<string>("50.00");
  const [orderCurrency, setOrderCurrency] = useState<string>("USD");
  const [isOrdering, setIsOrdering] = useState<boolean>(false);

  // Subscription creation
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [subLicenceId, setSubLicenceId] = useState<string>("1");
  const [isSubscribing, setIsSubscribing] = useState<boolean>(false);

  const loadBillingData = useCallback(async (accId: number) => {
    try {
      setIsLoading(true);
      setError(null);
      const [fetchedPlans, fetchedWallet] = await Promise.all([
        getSubscriptionPlans(),
        getAccountWallet(accId),
      ]);
      setPlans(fetchedPlans || []);
      setWallet(fetchedWallet);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load billing metrics");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function init() {
      try {
        const [fetchedPlans, fetchedWallet] = await Promise.all([
          getSubscriptionPlans(),
          getAccountWallet(accountId),
        ]);
        if (isMounted) {
          setPlans(fetchedPlans || []);
          setWallet(fetchedWallet);
          setIsLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load billing metrics");
          setIsLoading(false);
        }
      }
    }
    init();
    return () => {
      isMounted = false;
    };
  }, [accountId]);

  // Handlers
  const handleCredit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!wallet) return;
    const num = parseFloat(creditAmount);
    if (isNaN(num) || num <= 0) {
      setError("Please specify a valid positive decimal credit amount.");
      return;
    }

    try {
      setIsCrediting(true);
      setError(null);
      const idempotencyKey = `credit-${wallet.id}-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      const entry = await creditWallet(wallet.id, {
        amount: num.toFixed(2),
        currency_code: wallet.currency_code,
        source_reference: "MANUAL_TOPUP",
        description: creditDescription || "Manual credit balance top-up",
        idempotency_key: idempotencyKey,
      });

      setLedgerEntries((prev) => [entry, ...prev]);
      setSuccessMessage(`Successfully credited ${wallet.currency_code} ${num.toFixed(2)} to wallet.`);
      setCreditAmount("");
      setCreditDescription("");
      // Refresh authoritative wallet balance
      const refreshedWallet = await getAccountWallet(wallet.account_id);
      setWallet(refreshedWallet);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Credit transaction rejected");
    } finally {
      setIsCrediting(false);
    }
  };

  const handleDebit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!wallet) return;
    const num = parseFloat(debitAmount);
    if (isNaN(num) || num <= 0) {
      setError("Please specify a valid positive decimal debit amount.");
      return;
    }

    try {
      setIsDebiting(true);
      setError(null);
      const idempotencyKey = `debit-${wallet.id}-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      const entry = await debitWallet(wallet.id, {
        amount: num.toFixed(2),
        currency_code: wallet.currency_code,
        purpose: debitPurpose || "SERVICE_USAGE",
        description: `Service consumption debit: ${debitPurpose || "Standard"}`,
        idempotency_key: idempotencyKey,
      });

      setLedgerEntries((prev) => [entry, ...prev]);
      setSuccessMessage(`Successfully debited ${wallet.currency_code} ${num.toFixed(2)}.`);
      setDebitAmount("");
      setDebitPurpose("");
      const refreshedWallet = await getAccountWallet(wallet.account_id);
      setWallet(refreshedWallet);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Debit rejected (insufficient funds or concurrency conflict)");
    } finally {
      setIsDebiting(false);
    }
  };

  const handleCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    const entryId = parseInt(correctionEntryId, 10);
    const amountNum = parseFloat(correctionAmount);
    if (isNaN(entryId) || isNaN(amountNum) || !correctionReason) {
      setError("Correction requires valid original entry ID, signed adjustment amount, and audit reason.");
      return;
    }

    try {
      setIsCorrecting(true);
      setError(null);
      const idempotencyKey = `corr-${entryId}-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      const entry = await correctWalletLedger({
        original_entry_id: entryId,
        amount: amountNum.toFixed(2),
        reason: correctionReason,
        idempotency_key: idempotencyKey,
      });

      setLedgerEntries((prev) => [entry, ...prev]);
      setSuccessMessage(`Compensating ledger correction posted for Entry #${entryId}. Ledger history preserved.`);
      setCorrectionEntryId("");
      setCorrectionAmount("");
      setCorrectionReason("");
      if (wallet) {
        const refreshedWallet = await getAccountWallet(wallet.account_id);
        setWallet(refreshedWallet);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ledger correction failed");
    } finally {
      setIsCorrecting(false);
    }
  };

  const handleCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    const num = parseFloat(orderAmount);
    if (isNaN(num) || num <= 0) {
      setError("Please specify a valid positive order amount.");
      return;
    }

    try {
      setIsOrdering(true);
      setError(null);
      const idempotencyKey = `ord-${accountId}-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      const order = await createPaymentOrder({
        account_id: accountId,
        amount: num.toFixed(2),
        currency_code: orderCurrency,
        provider_code: "STRIPE",
        idempotency_key: idempotencyKey,
        description: `Deposit ${orderCurrency} ${num.toFixed(2)} to Account #${accountId}`,
      });

      setRecentOrders((prev) => [order, ...prev]);
      setSuccessMessage(`Payment order created: ${order.order_reference} (${orderCurrency} ${num.toFixed(2)}). Status: PENDING.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to initiate payment order");
    } finally {
      setIsOrdering(false);
    }
  };

  const handleSubscribe = async (plan: SubscriptionPlanResponse) => {
    const licId = parseInt(subLicenceId, 10);
    if (isNaN(licId) || licId <= 0) {
      setError("A valid positive licence ID is required to bind subscription entitlements.");
      return;
    }

    try {
      setIsSubscribing(true);
      setError(null);
      const starts = new Date();
      const ends = new Date();
      ends.setMonth(starts.getMonth() + 1);

      const sub = await createSubscription({
        account_id: accountId,
        plan_id: plan.id,
        licence_id: licId,
        starts_at: starts.toISOString(),
        ends_at: ends.toISOString(),
        auto_renew: true,
        seats_allocated: plan.max_seats,
      });

      setActiveSubscription(sub);
      setSelectedPlanId(null);
      setSuccessMessage(`Subscription #${sub.id} activated on plan '${plan.plan_name}'.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create subscription");
    } finally {
      setIsSubscribing(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!activeSubscription) return;
    const reason = window.prompt("Reason for subscription cancellation:", "User request");
    if (!reason) return;

    try {
      setIsLoading(true);
      setError(null);
      const res = await cancelSubscription(activeSubscription.id, { reason });
      setActiveSubscription(res);
      setSuccessMessage(`Subscription #${res.id} cancelled. Payment and ledger history preserved.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to cancel subscription");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <DashboardShell
      title="Subscriptions, Wallet & Payments"
      breadcrumbs={[{ label: "Billing" }]}
    >
      <div className="space-y-6">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Financial Administration & Wallet (Module M09)
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Authoritative append-only financial ledger, atomic wallet balance, and idempotent payment governance.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Account ID:</span>
            <input
              type="number"
              value={accountId}
              onChange={(e) => setAccountId(parseInt(e.target.value, 10) || 1)}
              className="w-20 px-2 py-1 text-xs border border-slate-300 dark:border-slate-700 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
              min="1"
            />
          </div>
        </div>

        {/* Global Notifications */}
        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-lg flex items-center justify-between text-red-700 dark:text-red-400">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium">{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-xs underline">
              Dismiss
            </button>
          </div>
        )}

        {successMessage && (
          <div className="p-4 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 rounded-lg flex items-center justify-between text-emerald-700 dark:text-emerald-400">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium">{successMessage}</span>
            </div>
            <button onClick={() => setSuccessMessage(null)} className="text-xs underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Wallet Balance Hero Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="md:col-span-1 bg-gradient-to-br from-slate-900 to-slate-800 text-white border-0 shadow-lg">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <Wallet className="w-4 h-4 text-emerald-400" />
                  Authoritative Wallet
                </CardTitle>
                <Badge variant="outline" className="text-emerald-400 border-emerald-400">
                  {wallet?.is_locked ? "LOCKED" : "ACTIVE"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider">Available Balance</span>
                <div className="text-3xl font-extrabold tracking-tight mt-1 text-white">
                  {wallet?.currency_code || "USD"} {Number(wallet?.balance_amount || 0).toFixed(2)}
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Algebraic sum of immutable ledger entries (FR-0128)
                </p>
              </div>

              <div className="pt-2 border-t border-slate-700 text-xs flex justify-between text-slate-300">
                <span>Overdraft Limit:</span>
                <span className="font-mono">{wallet?.currency_code || "USD"} {Number(wallet?.overdraft_limit || 0).toFixed(2)}</span>
              </div>
            </CardContent>
          </Card>

          {/* Quick Credit Top-Up */}
          <Card className="md:col-span-1">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-500" />
                Credit Wallet
              </CardTitle>
              <CardDescription>Post append-only credit entry (FR-0127)</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCredit} className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Amount ({wallet?.currency_code || "USD"})
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="100.00"
                    value={creditAmount}
                    onChange={(e) => setCreditAmount(e.target.value)}
                    className="w-full px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Description
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Wire transfer deposit"
                    value={creditDescription}
                    onChange={(e) => setCreditDescription(e.target.value)}
                    className="w-full px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                  />
                </div>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={isCrediting || !wallet}
                  className="w-full h-8 text-xs flex items-center justify-center gap-1.5"
                >
                  {isCrediting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <PlusCircle className="w-3.5 h-3.5" />}
                  Apply Credit
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Quick Debit Consumption */}
          <Card className="md:col-span-1">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-amber-500" />
                Atomic Debit
              </CardTitle>
              <CardDescription>Enforces minimum balance under row lock (FR-0130)</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleDebit} className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Amount ({wallet?.currency_code || "USD"})
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="25.00"
                    value={debitAmount}
                    onChange={(e) => setDebitAmount(e.target.value)}
                    className="w-full px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Purpose
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. CANDIDATE_PROFILE_DOWNLOAD"
                    value={debitPurpose}
                    onChange={(e) => setDebitPurpose(e.target.value)}
                    className="w-full px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                  />
                </div>
                <Button
                  type="submit"
                  variant="outline"
                  disabled={isDebiting || !wallet}
                  className="w-full h-8 text-xs flex items-center justify-center gap-1.5"
                >
                  {isDebiting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <TrendingDown className="w-3.5 h-3.5" />}
                  Execute Debit
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Subscription Plans Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-primary" />
              Available Subscription Plans & Entitlements (FR-0124, FR-0137)
            </CardTitle>
            <CardDescription>
              Authoritative subscription plans returned by the backend with feature entitlement definitions.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {plans.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-sm">
                No subscription plans configured.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {plans.map((p) => (
                  <div
                    key={p.id}
                    className="border border-slate-200 dark:border-slate-800 rounded-lg p-5 flex flex-col justify-between hover:border-primary transition-colors bg-white dark:bg-slate-900"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <h3 className="font-bold text-slate-900 dark:text-white text-base">
                          {p.plan_name}
                        </h3>
                        <Badge variant="purple">{p.plan_code}</Badge>
                      </div>
                      <div className="mt-3">
                        <span className="text-2xl font-black text-slate-900 dark:text-white">
                          {p.currency_code} {Number(p.price_amount).toFixed(2)}
                        </span>
                        <span className="text-xs text-slate-500"> / cycle</span>
                      </div>
                      <div className="mt-4 space-y-2 text-xs text-slate-600 dark:text-slate-300">
                        <div className="flex justify-between">
                          <span>Max Seats:</span>
                          <span className="font-semibold">{p.max_seats}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Candidate Searches:</span>
                          <span className="font-semibold">{p.max_candidates_search || "Unlimited"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Profile Download Quota:</span>
                          <span className="font-semibold">{p.profile_download_quota || 0}</span>
                        </div>
                        {p.entitlements && p.entitlements.length > 0 && (
                          <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                            <span className="font-medium text-slate-700 dark:text-slate-300 block mb-1">Entitlements:</span>
                            <div className="flex flex-wrap gap-1">
                              {p.entitlements.map((e) => (
                                <Badge key={e.id} variant="outline" className="text-[10px]">
                                  {e.feature_key}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800">
                      <Button
                        variant="primary"
                        onClick={() => handleSubscribe(p)}
                        disabled={isSubscribing}
                        className="w-full text-xs"
                      >
                        Subscribe to {p.plan_name}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Active Subscription Banner */}
            {activeSubscription && (
              <div className="mt-6 p-4 border border-indigo-200 dark:border-indigo-900 bg-indigo-50/50 dark:bg-indigo-950/20 rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-900 dark:text-white text-sm">
                      Active Subscription #{activeSubscription.id}
                    </span>
                    <Badge variant={activeSubscription.cancelled_at ? "destructive" : "success"}>
                      {activeSubscription.cancelled_at ? "CANCELLED" : "ACTIVE"}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Valid: {formatDate(activeSubscription.starts_at)} — {formatDate(activeSubscription.ends_at)} • Seats: {activeSubscription.seats_allocated}
                  </p>
                </div>
                {!activeSubscription.cancelled_at && (
                  <Button
                    variant="destructive"
                    onClick={handleCancelSubscription}
                    className="text-xs"
                  >
                    Cancel Subscription (FR-0135)
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Payment Order Initiation & Ledger Compensation */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Payment Order (FR-0125, FR-0126) */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Receipt className="w-4 h-4 text-primary" />
                Initiate Payment Order (FR-0125)
              </CardTitle>
              <CardDescription>
                Idempotent gateway checkout initiation. Zero PAN/CVV storage.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateOrder} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Amount
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={orderAmount}
                      onChange={(e) => setOrderAmount(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                      min="1"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Currency (ISO 4217)
                    </label>
                    <select
                      value={orderCurrency}
                      onChange={(e) => setOrderCurrency(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    >
                      <option value="USD">USD</option>
                      <option value="EUR">EUR</option>
                      <option value="GBP">GBP</option>
                      <option value="INR">INR</option>
                    </select>
                  </div>
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  disabled={isOrdering}
                  className="w-full flex items-center justify-center gap-2"
                >
                  {isOrdering ? <Loader2 className="w-4 h-4 animate-spin" /> : <Receipt className="w-4 h-4" />}
                  Generate Payment Order
                </Button>
              </form>

              {recentOrders.length > 0 && (
                <div className="mt-4 border-t border-slate-200 dark:border-slate-800 pt-4 space-y-2">
                  <span className="text-xs font-medium text-slate-500">Recent Payment Orders:</span>
                  {recentOrders.map((ord) => (
                    <div
                      key={ord.id}
                      className="p-3 border border-slate-100 dark:border-slate-800 rounded-md flex items-center justify-between text-xs"
                    >
                      <div>
                        <span className="font-mono font-medium">{ord.order_reference}</span>
                        <span className="text-slate-400 block text-[11px]">{formatDate(ord.created_at)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold">{ord.currency_code} {Number(ord.amount).toFixed(2)}</span>
                        <Badge variant="warning">PENDING</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Ledger Correction (FR-0138, FR-0206) */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <RotateCcw className="w-4 h-4 text-purple-500" />
                Ledger Correction & Compensating Entry (FR-0138, FR-0206)
              </CardTitle>
              <CardDescription>
                Financial ledgers are append-only. Corrections link to the original entry ID without mutating past history.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCorrection} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Original Entry ID
                    </label>
                    <input
                      type="number"
                      placeholder="e.g. 101"
                      value={correctionEntryId}
                      onChange={(e) => setCorrectionEntryId(e.target.value)}
                      className="w-full px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                      min="1"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Signed Adjustment
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="e.g. -10.00"
                      value={correctionAmount}
                      onChange={(e) => setCorrectionAmount(e.target.value)}
                      className="w-full px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Audit Rationale
                  </label>
                  <input
                    type="text"
                    placeholder="Mandatory explanation for ledger reconciliation"
                    value={correctionReason}
                    onChange={(e) => setCorrectionReason(e.target.value)}
                    className="w-full px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    required
                  />
                </div>

                <Button
                  type="submit"
                  variant="outline"
                  disabled={isCorrecting}
                  className="w-full h-8 text-xs flex items-center justify-center gap-1.5"
                >
                  {isCorrecting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RotateCcw className="w-3.5 h-3.5" />}
                  Post Compensating Entry
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Append-Only Ledger Activity Stream */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" />
              Session Ledger Activity (Append-Only)
            </CardTitle>
            <CardDescription>
              Chronological log of transactions posted in this session. Updates and deletes are prohibited.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {ledgerEntries.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-sm">
                No ledger transactions recorded in this session. Perform a Credit or Debit to view live ledger posting.
              </div>
            ) : (
              <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Entry ID</TableHead>
                      <TableHead>Direction</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Balance After</TableHead>
                      <TableHead>Reference / Correction</TableHead>
                      <TableHead>Timestamp</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {ledgerEntries.map((entry) => (
                      <TableRow key={entry.id}>
                        <TableCell className="font-mono text-xs">#{entry.id}</TableCell>
                        <TableCell>
                          <Badge variant={entry.direction_code_id === 1 ? "success" : "destructive"}>
                            {entry.direction_code_id === 1 ? "CREDIT" : "DEBIT"}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-semibold text-xs">
                          {entry.currency_code} {Number(entry.amount).toFixed(2)}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {entry.currency_code} {Number(entry.balance_after).toFixed(2)}
                        </TableCell>
                        <TableCell className="text-xs text-slate-500">
                          {entry.original_entry_id ? (
                            <span className="text-purple-600 dark:text-purple-400 font-medium">
                              Corrects Entry #{entry.original_entry_id}
                            </span>
                          ) : (
                            entry.description || entry.reference_type || "Standard Ledger Entry"
                          )}
                        </TableCell>
                        <TableCell className="text-xs text-slate-400">
                          {formatDate(entry.created_at)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
