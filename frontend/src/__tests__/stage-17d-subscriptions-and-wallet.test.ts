import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "@/lib/api/client";
import {
  getSubscriptionPlans,
  createSubscription,
  cancelSubscription,
  checkEntitlement,
  getAccountWallet,
  creditWallet,
  debitWallet,
  correctWalletLedger,
  createPaymentOrder,
  processRefund,
  downloadCandidateProfile,
} from "@/lib/api/subscriptions";
import {
  SubscriptionPlanResponse,
  SubscriptionResponse,
  WalletResponse,
  WalletLedgerEntryResponse,
  PaymentOrderResponse,
  RefundResponse,
  ProfileDownloadResponse,
} from "@/types/subscriptions";

describe("Stage 17D: Subscriptions, Wallet & Payments (Module M09)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("Subscription Plans & Lifecycle (FR-0124, FR-0135, FR-0137)", () => {
    it("retrieves public subscription plans with feature entitlements", async () => {
      const mockPlans: SubscriptionPlanResponse[] = [
        {
          id: 1,
          plan_code: "GROWTH",
          plan_name: "Growth Plan",
          billing_cycle_code_id: 1,
          price_amount: "49.00",
          currency_code: "USD",
          max_seats: 5,
          is_active: true,
          is_public: true,
          display_order: 1,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          entitlements: [
            {
              id: 10,
              plan_id: 1,
              feature_key: "ADVANCED_SEARCH",
              entitlement_type: "FEATURE",
              is_unlimited: true,
              created_at: "2026-01-01T00:00:00Z",
            },
          ],
        },
      ];

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockPlans);

      const res = await getSubscriptionPlans();
      expect(res).toHaveLength(1);
      expect(res[0].plan_code).toBe("GROWTH");
      expect(res[0].entitlements).toHaveLength(1);
      expect(apiClient.get).toHaveBeenCalledWith("/subscriptions/plans");
    });

    it("creates subscription with period validity", async () => {
      const mockSub: SubscriptionResponse = {
        id: 10,
        account_id: 1,
        plan_id: 1,
        licence_id: 1,
        subscription_status_code_id: 1,
        starts_at: "2026-10-01T00:00:00Z",
        ends_at: "2026-11-01T00:00:00Z",
        auto_renew: true,
        renewal_count: 0,
        seats_allocated: 5,
        created_at: "2026-10-01T00:00:00Z",
        updated_at: "2026-10-01T00:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockSub);

      const res = await createSubscription({
        account_id: 1,
        plan_id: 1,
        licence_id: 1,
        starts_at: "2026-10-01T00:00:00Z",
        ends_at: "2026-11-01T00:00:00Z",
        auto_renew: true,
        seats_allocated: 5,
      });

      expect(res.id).toBe(10);
      expect(res.auto_renew).toBe(true);
      expect(apiClient.post).toHaveBeenCalledWith("/subscriptions", expect.objectContaining({
        account_id: 1,
        plan_id: 1,
      }));
    });

    it("cancels subscription recording cancelled_at and preserving history (FR-0135)", async () => {
      const mockCancelled: SubscriptionResponse = {
        id: 10,
        account_id: 1,
        plan_id: 1,
        licence_id: 1,
        subscription_status_code_id: 3,
        starts_at: "2026-10-01T00:00:00Z",
        ends_at: "2026-11-01T00:00:00Z",
        auto_renew: false,
        renewal_count: 0,
        seats_allocated: 5,
        cancelled_at: "2026-10-21T10:00:00Z",
        created_at: "2026-10-01T00:00:00Z",
        updated_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockCancelled);

      const res = await cancelSubscription(10, { reason: "Budget re-allocation" });
      expect(res.cancelled_at).toBe("2026-10-21T10:00:00Z");
      expect(apiClient.post).toHaveBeenCalledWith("/subscriptions/10/cancel", {
        reason: "Budget re-allocation",
      });
    });

    it("verifies feature entitlement check (FR-0137)", async () => {
      vi.spyOn(apiClient, "get").mockResolvedValueOnce({
        account_id: 1,
        feature_key: "ADVANCED_SEARCH",
        granted: true,
      });

      const res = await checkEntitlement(1, "ADVANCED_SEARCH");
      expect(res.granted).toBe(true);
      expect(apiClient.get).toHaveBeenCalledWith("/subscriptions/entitlements/check", {
        params: { account_id: 1, feature_key: "ADVANCED_SEARCH" },
      });
    });
  });

  describe("Wallet & Immutable Ledger (FR-0128, FR-0129, FR-0130, FR-0138, FR-0206)", () => {
    it("fetches wallet balance calculated as algebraic sum of ledger entries", async () => {
      const mockWallet: WalletResponse = {
        id: 3,
        account_id: 1,
        balance_amount: "250.00",
        currency_code: "USD",
        wallet_status_code_id: 1,
        is_locked: false,
        overdraft_limit: "0.00",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockWallet);

      const res = await getAccountWallet(1);
      expect(res.balance_amount).toBe("250.00");
      expect(apiClient.get).toHaveBeenCalledWith("/wallet/1");
    });

    it("posts append-only credit entry to wallet with idempotency key", async () => {
      const mockEntry: WalletLedgerEntryResponse = {
        id: 101,
        wallet_id: 3,
        entry_type_code_id: 1,
        direction_code_id: 1,
        amount: "50.00",
        balance_after: "300.00",
        currency_code: "USD",
        idempotency_key: "idem-credit-101",
        description: "Invoice payment top-up",
        created_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockEntry);

      const res = await creditWallet(3, {
        amount: "50.00",
        currency_code: "USD",
        idempotency_key: "idem-credit-101",
        description: "Invoice payment top-up",
      });

      expect(res.id).toBe(101);
      expect(res.balance_after).toBe("300.00");
      expect(apiClient.post).toHaveBeenCalledWith("/wallet/3/credit", expect.objectContaining({
        amount: "50.00",
        idempotency_key: "idem-credit-101",
      }));
    });

    it("handles insufficient wallet credit rejection (FR-0130)", async () => {
      vi.spyOn(apiClient, "post").mockRejectedValueOnce({
        status: 400,
        message: "Insufficient wallet credits (FR-0130)",
      });

      await expect(
        debitWallet(3, {
          amount: "9999.00",
          currency_code: "USD",
          idempotency_key: "idem-fail",
        })
      ).rejects.toMatchObject({
        status: 400,
      });
    });

    it("posts compensating ledger correction referencing original entry without modifying it (FR-0138, FR-0206)", async () => {
      const mockCorrection: WalletLedgerEntryResponse = {
        id: 102,
        wallet_id: 3,
        entry_type_code_id: 3,
        direction_code_id: 2,
        amount: "-10.00",
        balance_after: "290.00",
        currency_code: "USD",
        idempotency_key: "idem-corr-102",
        original_entry_id: 101,
        description: "Billing overcharge adjustment",
        created_at: "2026-10-21T10:15:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockCorrection);

      const res = await correctWalletLedger({
        original_entry_id: 101,
        amount: "-10.00",
        reason: "Billing overcharge adjustment",
        idempotency_key: "idem-corr-102",
      });

      expect(res.original_entry_id).toBe(101);
      expect(res.amount).toBe("-10.00");
      expect(apiClient.post).toHaveBeenCalledWith("/wallet/ledger/correction", expect.objectContaining({
        original_entry_id: 101,
        amount: "-10.00",
      }));
    });
  });

  describe("Payments & Profile Downloads (FR-0125, FR-0132, FR-0133)", () => {
    it("creates payment order with durable idempotency key", async () => {
      const mockOrder: PaymentOrderResponse = {
        id: 88,
        order_reference: "ord_88",
        account_id: 1,
        amount: "100.00",
        currency_code: "USD",
        order_status_code_id: 1,
        idempotency_key: "idem-order-88",
        created_at: "2026-10-21T10:00:00Z",
        updated_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockOrder);

      const res = await createPaymentOrder({
        account_id: 1,
        amount: "100.00",
        currency_code: "USD",
        provider_code: "STRIPE",
        idempotency_key: "idem-order-88",
      });

      expect(res.id).toBe(88);
      expect(res.order_reference).toBe("ord_88");
      expect(apiClient.post).toHaveBeenCalledWith("/payments/orders", expect.objectContaining({
        idempotency_key: "idem-order-88",
      }));
    });

    it("issues refund referencing original payment transaction (FR-0133)", async () => {
      const mockRefund: RefundResponse = {
        id: 7,
        payment_transaction_id: 12,
        refund_reference: "ref_7",
        amount: "25.00",
        currency_code: "USD",
        status_code_id: 1,
        idempotency_key: "idem-ref-7",
        created_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockRefund);

      const res = await processRefund({
        payment_transaction_id: 12,
        amount: "25.00",
        reason: "Customer requested cancellation",
        idempotency_key: "idem-ref-7",
      });

      expect(res.id).toBe(7);
      expect(res.payment_transaction_id).toBe(12);
      expect(apiClient.post).toHaveBeenCalledWith("/payments/refund", expect.objectContaining({
        payment_transaction_id: 12,
        amount: "25.00",
      }));
    });

    it("consumes wallet credit and records candidate profile download (FR-0132)", async () => {
      const mockDownload: ProfileDownloadResponse = {
        id: 55,
        account_id: 1,
        user_id: 1,
        candidate_id: 42,
        credits_consumed: 1,
        download_format: "PDF",
        downloaded_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockDownload);

      const res = await downloadCandidateProfile(
        { candidate_id: 42, download_format: "PDF" },
        1,
        1
      );

      expect(res.candidate_id).toBe(42);
      expect(res.credits_consumed).toBe(1);
      expect(apiClient.post).toHaveBeenCalledWith(
        "/wallet/download-profile",
        { candidate_id: 42, download_format: "PDF" },
        { params: { account_id: 1, organisation_id: 1 } }
      );
    });
  });
});
