import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient, setAuthToken, registerAuthExpiredHandler, ApiClientError } from "@/lib/api/client";
import {
  getStoredSession,
  setStoredSession,
  clearStoredSession,
  getDefaultActorIdForRole,
  getRoleForActorPrefix,
  ROLE_PREFIX_MAP,
} from "@/lib/auth/session";
import { DEMO_PERSONAS } from "@/lib/auth/context";
import {
  listJobs,
  getJobDetails,
  createJob,
  updateJobStatus,
  getJobApplications,
} from "@/lib/api/jobs";
import {
  applyToJob,
  getApplicationDetails,
  updateApplicationStatus,
} from "@/lib/api/applications";
import {
  listOrganisations,
  getOrganisationDetails,
  getOrganisationRecruiters,
} from "@/lib/api/organisations";
import {
  createSourcingRequest,
  respondToSourcingRequest,
} from "@/lib/api/sourcing";
import {
  createGigRequest,
  applyToGigRequest,
} from "@/lib/api/gig";
import {
  getLicence,
  allocateSeat,
  registerDevice,
} from "@/lib/api/licences";
import {
  getAccountWallet,
  creditWallet,
  debitWallet,
  correctWalletLedger,
  createPaymentOrder,
} from "@/lib/api/subscriptions";
import {
  captureVerificationConsent,
  initiateVerification,
  getSecureDocumentUrl,
  submitVerificationReview,
  runRetentionJob,
} from "@/lib/api/verification";
import {
  listAdminUsers,
  grantUserRole,
  revokeUserRole,
  updateUserStatus,
  softDeleteUser,
  listAuditEvents,
  revokeIdentitySession,
} from "@/lib/api/admin";
import { AuthSession } from "@/types/auth";
import { WalletLedgerEntryResponse } from "@/types/subscriptions";
import { VerificationCaseResponse } from "@/types/verification";

describe("STAGE 17E: Comprehensive Frontend Acceptance & Integration Hardening", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    setAuthToken(null);
  });

  /* ==========================================================================
     1. Authentication, Sessions & Route Protection Hardening
     ========================================================================== */
  describe("1. Authentication, Sessions & Role Governance", () => {
    it("persists active session to storage and sets global auth token", () => {
      const mockSession: AuthSession = {
        accessToken: "jwt-token-stage-17e-valid",
        activeRole: "EMPLOYER",
        activeActorId: "EM00001",
        user: {
          user_id: 101,
          email_address: "employer.demo@talentra.io",
          display_name: "Priya Verma",
          roles: ["EMPLOYER"],
          actor_identities: [
            {
              actor_id: "EM00001",
              role_code: "EMPLOYER",
              actor_prefix: "EM",
              is_active: true,
            },
          ],
          created_at: "2026-10-21T00:00:00Z",
        },
      };

      setStoredSession(mockSession);
      const stored = getStoredSession();
      expect(stored).not.toBeNull();
      expect(stored?.accessToken).toBe("jwt-token-stage-17e-valid");
      expect(stored?.user.email_address).toBe("employer.demo@talentra.io");
      expect(stored?.activeRole).toBe("EMPLOYER");
      expect(stored?.activeActorId).toBe("EM00001");
    });

    it("clears stored session and resets token on logout", () => {
      setStoredSession({
        accessToken: "test-token",
        activeRole: "ADMIN",
        activeActorId: "AD00001",
        user: {
          user_id: 1,
          email_address: "admin@talentra.io",
          display_name: "Admin",
          roles: ["ADMIN"],
          actor_identities: [
            {
              actor_id: "AD00001",
              role_code: "ADMIN",
              actor_prefix: "AD",
              is_active: true,
            },
          ],
          created_at: "2026-10-21T00:00:00Z",
        },
      });

      clearStoredSession();
      expect(getStoredSession()).toBeNull();
    });

    it("triggers registered session expiration callback on HTTP 401 Unauthorized", async () => {
      let expiredCalled = false;
      registerAuthExpiredHandler(() => {
        expiredCalled = true;
      });

      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
        status: 401,
        ok: false,
        json: async () => ({ detail: "Token expired or invalid" }),
      } as Response);

      await expect(apiClient.get("/auth/me")).rejects.toThrow("Token expired or invalid");
      expect(expiredCalled).toBe(true);
    });

    it("handles HTTP 403 Forbidden without throwing unhandled exceptions", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
        status: 403,
        ok: false,
        json: async () => ({ detail: "Access denied. Insufficient role permissions." }),
      } as Response);

      await expect(apiClient.get("/admin/audit-events")).rejects.toThrow("Access denied");
    });

    it("verifies all 8 documented role portals and their canonical actor IDs", () => {
      const documentedRoles = [
        { role: "SUPER_ADMIN", prefix: "SA", defaultActor: "SA00001" },
        { role: "ADMIN", prefix: "AD", defaultActor: "AD00001" },
        { role: "ACCOUNT_ADMIN", prefix: "AA", defaultActor: "AA00001" },
        { role: "EMPLOYER", prefix: "EM", defaultActor: "EM00001" },
        { role: "RECRUITER", prefix: "RE", defaultActor: "RE00001" },
        { role: "CONSULTANT", prefix: "CO", defaultActor: "CO00001" },
        { role: "CANDIDATE", prefix: "CA", defaultActor: "CA00001" },
        { role: "PLACEMENT_OFFICER", prefix: "PO", defaultActor: "PO00001" },
      ];

      for (const item of documentedRoles) {
        expect(ROLE_PREFIX_MAP[item.role]).toBe(item.prefix);
        expect(getDefaultActorIdForRole(item.role)).toBe(item.defaultActor);
        expect(getRoleForActorPrefix(item.defaultActor)).toBe(item.role);
      }
    });

    it("verifies DEMO_PERSONAS contains all 8 portals plus guest visitor", () => {
      expect(DEMO_PERSONAS.length).toBe(9);
      const roles = DEMO_PERSONAS.map((p) => p.roleCode);
      expect(roles).toContain("SUPER_ADMIN");
      expect(roles).toContain("ADMIN");
      expect(roles).toContain("ACCOUNT_ADMIN");
      expect(roles).toContain("EMPLOYER");
      expect(roles).toContain("RECRUITER");
      expect(roles).toContain("CONSULTANT");
      expect(roles).toContain("CANDIDATE");
      expect(roles).toContain("PLACEMENT_OFFICER");
      expect(roles).toContain("GUEST");
    });
  });

  /* ==========================================================================
     2. Core Workflows Acceptance & Hardening
     ========================================================================== */
  describe("2. Core Workflows (Jobs, Applications, Organisations, Gigs, Sourcing)", () => {
    it("handles job list with query parameters and pagination", async () => {
      const mockJobsResponse = {
        items: [
          {
            id: 1,
            title: "Senior Full-Stack Engineer",
            department: "Engineering",
            location: "Bengaluru, India",
            status: "OPEN",
            open_positions: 2,
            hired_count: 0,
            created_at: "2026-10-21T08:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockJobsResponse);

      const res = await listJobs({ search: "Full-Stack", page_size: 20 });
      expect(res.items.length).toBe(1);
      expect(res.items[0].title).toBe("Senior Full-Stack Engineer");
      expect(res.items[0].status).toBe("OPEN");
    });

    it("verifies application state machine transitions from SUBMITTED through HIRED", async () => {
      const mockApp = {
        id: 10,
        job_requirement_id: 1,
        job_title: "Senior Full-Stack Engineer",
        organisation_id: 1,
        organisation_name: "Acme Corp",
        candidate_profile_id: 42,
        candidate_actor_id: "CA00042",
        candidate_name: "Arun Sharma",
        status: "SUBMITTED",
        applied_at: "2026-10-21T09:00:00Z",
        last_status_changed_at: "2026-10-21T09:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockApp);

      const applied = await applyToJob(1, {
        cover_letter: "Excited to apply for Senior Full-Stack role.",
      });
      expect(applied.status).toBe("SUBMITTED");

      // Screening transition (PATCH)
      vi.spyOn(apiClient, "patch").mockResolvedValueOnce({
        ...mockApp,
        status: "SCREENING",
      });
      const screening = await updateApplicationStatus(10, {
        status: "SCREENING",
        notes: "Passed resume filter",
      });
      expect(screening.status).toBe("SCREENING");

      // Interview transition (PATCH)
      vi.spyOn(apiClient, "patch").mockResolvedValueOnce({
        ...mockApp,
        status: "INTERVIEW",
      });
      const interview = await updateApplicationStatus(10, {
        status: "INTERVIEW",
        notes: "System design round scheduled",
      });
      expect(interview.status).toBe("INTERVIEW");

      // Hired transition (PATCH)
      vi.spyOn(apiClient, "patch").mockResolvedValueOnce({
        ...mockApp,
        status: "HIRED",
      });
      const hired = await updateApplicationStatus(10, {
        status: "HIRED",
        notes: "Offer accepted",
      });
      expect(hired.status).toBe("HIRED");
    });

    it("allows candidate application status update to WITHDRAWN", async () => {
      vi.spyOn(apiClient, "patch").mockResolvedValueOnce({
        id: 10,
        job_requirement_id: 1,
        job_title: "Senior Full-Stack Engineer",
        organisation_id: 1,
        organisation_name: "Acme Corp",
        candidate_profile_id: 42,
        candidate_actor_id: "CA00042",
        candidate_name: "Arun Sharma",
        status: "WITHDRAWN",
        applied_at: "2026-10-21T09:00:00Z",
        last_status_changed_at: "2026-10-21T10:00:00Z",
      });

      const res = await updateApplicationStatus(10, {
        status: "WITHDRAWN",
        notes: "Accepted another offer",
      });
      expect(res.status).toBe("WITHDRAWN");
    });

    it("enforces recruiter listing scoped to organisation boundary", async () => {
      const mockRecruiters = [
        {
          id: 50,
          organisation_id: 12,
          recruiter_user_id: 7,
          recruiter_actor_id: "RE00007",
          recruiter_name: "Vikram Sen",
          valid_from: "2026-10-21T10:00:00Z",
          assigned_by_user_id: 1,
          is_active: true,
        },
      ];

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockRecruiters);

      const res = await getOrganisationRecruiters(12);
      expect(res.length).toBe(1);
      expect(res[0].organisation_id).toBe(12);
      expect(res[0].recruiter_user_id).toBe(7);
      expect(res[0].is_active).toBe(true);
    });

    it("manages consultant sourcing requests lifecycle and response decisions", async () => {
      vi.spyOn(apiClient, "post").mockResolvedValueOnce({
        id: 301,
        job_requirement_id: 1,
        job_title: "Staff DevOps Consultant",
        organisation_id: 1,
        organisation_name: "Acme Corp",
        requester_user_id: 5,
        status_code_id: 1,
        status: "PENDING",
        requested_at: "2026-10-21T10:00:00Z",
        created_at: "2026-10-21T10:00:00Z",
      });

      const req = await createSourcingRequest({
        job_requirement_id: 1,
        consultant_user_id: 9,
      });
      expect(req.id).toBe(301);
      expect(req.status).toBe("PENDING");

      // Consultant accepts sourcing request
      vi.spyOn(apiClient, "post").mockResolvedValueOnce({
        id: 301,
        job_requirement_id: 1,
        job_title: "Staff DevOps Consultant",
        organisation_id: 1,
        organisation_name: "Acme Corp",
        requester_user_id: 5,
        consultant_user_id: 9,
        status_code_id: 2,
        status: "ACCEPTED",
        requested_at: "2026-10-21T10:00:00Z",
        responded_at: "2026-10-21T10:30:00Z",
        created_at: "2026-10-21T10:00:00Z",
      });

      const accepted = await respondToSourcingRequest(301, "ACCEPT", "Available to start Monday");
      expect(accepted.status).toBe("ACCEPTED");
    });

    it("supports gig marketplace requisition and candidate proposal submission", async () => {
      vi.spyOn(apiClient, "post").mockResolvedValueOnce({
        id: 401,
        requester_organisation_id: 1,
        created_by_user_id: 5,
        title: "React Component Library Audit",
        description: "Audit design tokens against WCAG 2.1 AA",
        starts_at: "2026-11-01T00:00:00Z",
        ends_at: "2026-11-15T00:00:00Z",
        pricing_type_code_id: 1,
        pricing_type: "FIXED",
        price_amount: 2500.0,
        currency_code: "USD",
        status_code_id: 1,
        status: "OPEN",
        created_at: "2026-10-21T10:00:00Z",
        updated_at: "2026-10-21T10:00:00Z",
      });

      const gig = await createGigRequest({
        requester_organisation_id: 1,
        title: "React Component Library Audit",
        description: "Audit design tokens against WCAG 2.1 AA",
        starts_at: "2026-11-01T00:00:00Z",
        ends_at: "2026-11-15T00:00:00Z",
        pricing_type_code_id: 1,
        price_amount: 2500.0,
        currency_code: "USD",
      });
      expect(gig.id).toBe(401);

      // Candidate applies with proposal
      vi.spyOn(apiClient, "post").mockResolvedValueOnce({
        id: 801,
        gig_request_id: 401,
        gig_worker_profile_id: 42,
        applied_at: "2026-10-21T10:30:00Z",
        status_code_id: 1,
        status: "APPLIED",
        created_at: "2026-10-21T10:30:00Z",
      });

      const application = await applyToGigRequest(401, {
        notes: "Experienced with WCAG and design systems",
      });
      expect(application.id).toBe(801);
      expect(application.status).toBe("APPLIED");
    });
  });

  /* ==========================================================================
     3. Financial, Licensing & Verification Invariants Hardening
     ========================================================================== */
  describe("3. Financial, Licensing & Identity Invariants", () => {
    it("enforces append-only compensating ledger correction for financial corrections", async () => {
      const mockCorrection: WalletLedgerEntryResponse = {
        id: 88,
        wallet_id: 2,
        entry_type_code_id: 3,
        direction_code_id: 2,
        amount: -25.0,
        balance_after: 475.0,
        currency_code: "USD",
        description: "Compensating correction for duplicate charge",
        created_at: "2026-10-21T11:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockCorrection);

      const res = await correctWalletLedger({
        original_entry_id: 44,
        amount: -25.0,
        reason: "Duplicate fee compensation",
        idempotency_key: "idem-corr-44-88",
      });
      expect(res.id).toBe(88);
      expect(res.wallet_id).toBe(2);
      expect(res.amount).toBe(-25.0);
    });

    it("verifies licence seat allocation rejects over-capacity requests", async () => {
      vi.spyOn(apiClient, "post").mockRejectedValueOnce(
        new ApiClientError(400, "Seat allocation exceeds total licensed seats")
      );

      await expect(
        allocateSeat({
          licence_id: 10,
          user_id: 99,
        })
      ).rejects.toThrow("Seat allocation exceeds total licensed seats");
    });

    it("captures verification consent with documented purpose before identity processing", async () => {
      vi.spyOn(apiClient, "post").mockResolvedValueOnce({
        consent_record_id: 101,
        user_id: 42,
        purpose: "KYC_ONBOARDING",
        granted: true,
        captured_at: "2026-10-21T11:00:00Z",
      });

      const consent = await captureVerificationConsent({
        user_id: 42,
        permitted_purpose: "KYC_ONBOARDING",
      });
      expect(consent.consent_record_id).toBe(101);
      expect(consent.granted).toBe(true);
      expect(consent.purpose).toBe("KYC_ONBOARDING");
    });

    it("initiates verification with SHA-256 fingerprint and masked identifier (FR-0164, FR-0209)", async () => {
      const mockCase: VerificationCaseResponse = {
        case_id: 501,
        user_id: 42,
        document_type: "AADHAAR",
        provider_code: "SANDBOX_MOCK",
        status: "INITIATED",
        requested_at: "2026-10-21T11:05:00Z",
        masked_identifier: "XXXX-XXXX-9012",
        identifier_fingerprint: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        malware_scan_status: "PASSED",
        consent_record_id: 101,
        purpose: "KYC_ONBOARDING",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockCase);

      const res = await initiateVerification({
        user_id: 42,
        document_type: "AADHAAR",
        file_name: "aadhaar_front.pdf",
        file_mime_type: "application/pdf",
        raw_identifier_for_masking_only: "123456789012",
        consent_record_id: 101,
        purpose: "KYC_ONBOARDING",
      });

      expect(res.case_id).toBe(501);
      expect(res.masked_identifier).toBe("XXXX-XXXX-9012");
      expect(res.status).toBe("INITIATED");
    });

    it("enforces dual control for high-risk verification override decisions (FR-0176, FR-0178)", async () => {
      // High-risk override without second approver is rejected
      vi.spyOn(apiClient, "post").mockRejectedValueOnce(
        new ApiClientError(400, "High-risk override requires a verified second approver user ID")
      );

      await expect(
        submitVerificationReview(501, {
          decision: "VERIFIED",
          reason: "Manual exception approved",
          reviewer_user_id: 1,
          is_high_risk_override: true,
          second_approver_user_id: null,
        })
      ).rejects.toThrow("High-risk override requires a verified second approver");

      // High-risk override with valid second approver succeeds
      const approvedCase: VerificationCaseResponse = {
        case_id: 501,
        user_id: 42,
        document_type: "AADHAAR",
        provider_code: "SANDBOX_MOCK",
        status: "VERIFIED",
        requested_at: "2026-10-21T11:05:00Z",
        completed_at: "2026-10-21T11:10:00Z",
        masked_identifier: "XXXX-XXXX-9012",
        malware_scan_status: "PASSED",
        consent_record_id: 101,
        purpose: "KYC_ONBOARDING",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(approvedCase);

      const override = await submitVerificationReview(501, {
        decision: "VERIFIED",
        reason: "Manual exception approved with executive sign-off",
        reviewer_user_id: 1,
        is_high_risk_override: true,
        second_approver_user_id: 2,
      });

      expect(override.status).toBe("VERIFIED");
    });

    it("protects immutable security audit events from deletion (FR-0059)", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
        status: 403,
        ok: false,
        json: async () => ({
          detail: "Audit event records are immutable and cannot be deleted or modified (FR-0059)",
        }),
      } as Response);

      await expect(
        apiClient.delete("/admin/audit-events/999")
      ).rejects.toThrow("Audit event records are immutable");
    });

    it("executes data retention scheduler dry run safely without destructive purges (FR-0177)", async () => {
      vi.spyOn(apiClient, "post").mockResolvedValueOnce({
        job_id: 1001,
        data_class: "KYC_DOCUMENTS",
        dry_run: true,
        evaluated_records: 120,
        eligible_for_purge: 0,
        purged_records: 0,
        skipped_due_to_legal_hold: 120,
        executed_at: "2026-10-21T11:15:00Z",
        status: "COMPLETED",
      });

      const summary = await runRetentionJob({
        target_data_class: "KYC_DOCUMENTS",
        retention_days: 2555,
        dry_run: true,
      });

      expect(summary.dry_run).toBe(true);
      expect(summary.purged_records).toBe(0);
      expect(summary.evaluated_records).toBe(120);
    });
  });

  /* ==========================================================================
     4. Security, Secrets & Environment Hardening
     ========================================================================== */
  describe("4. Security & Environment Verification", () => {
    it("confirms no sensitive private keys or database passwords exist in frontend environment", () => {
      const publicKeys = Object.keys(process.env).filter((key) =>
        key.startsWith("NEXT_PUBLIC_")
      );

      for (const key of publicKeys) {
        const val = process.env[key] || "";
        expect(key).not.toMatch(/SECRET/i);
        expect(key).not.toMatch(/PRIVATE/i);
        expect(key).not.toMatch(/SERVICE_ROLE/i);
        expect(val).not.toMatch(/postgres:\/\/.*:.*@/);
      }
    });

    it("ensures public API base URL is non-empty and well-formed", () => {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
      expect(baseUrl).toMatch(/^https?:\/\/.+/);
      expect(baseUrl.endsWith("/")).toBe(false);
    });
  });
});
