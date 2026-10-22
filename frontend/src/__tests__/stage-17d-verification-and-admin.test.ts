import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "@/lib/api/client";
import {
  captureVerificationConsent,
  initiateVerification,
  getSecureDocumentUrl,
  submitVerificationReview,
  getIntegrationRegister,
  runRetentionJob,
  evaluateFeatureFlag,
} from "@/lib/api/verification";
import {
  listAdminUsers,
  grantUserRole,
  revokeUserRole,
  updateUserStatus,
  softDeleteUser,
  listAuditEvents,
  revokeIdentitySession,
  getAccessReview,
  getDataClassification,
} from "@/lib/api/admin";
import {
  VerificationConsentResponse,
  VerificationCaseResponse,
  DocumentAccessUrlResponse,
  IntegrationBoundaryEntry,
  RetentionJobSummaryResponse,
  FeatureFlagResponse,
} from "@/types/verification";
import {
  AdminUserResponse,
  AdminUserListResponse,
  AuditEventListResponse,
  AdminSessionResponse,
  AccessReviewReportResponse,
  DataClassificationResponse,
} from "@/types/admin";

describe("Stage 17D: Government Verification, Integrations & Administration (Stages 14 & M04)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("Government ID Verification & Integrations (FR-0163, FR-0164, FR-0165, FR-0175, FR-0209)", () => {
    it("captures explicit verification consent with documented purpose (FR-0163)", async () => {
      const mockConsent: VerificationConsentResponse = {
        consent_record_id: 10,
        user_id: 1,
        purpose: "KYC_ONBOARDING",
        granted: true,
        captured_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockConsent);

      const res = await captureVerificationConsent({
        user_id: 1,
        permitted_purpose: "KYC_ONBOARDING",
      });

      expect(res.consent_record_id).toBe(10);
      expect(res.granted).toBe(true);
      expect(apiClient.post).toHaveBeenCalledWith("/verification/consent", expect.objectContaining({
        permitted_purpose: "KYC_ONBOARDING",
      }));
    });

    it("initiates verification case with zero raw PII persistence (FR-0164, FR-0209)", async () => {
      const mockCase: VerificationCaseResponse = {
        case_id: 55,
        user_id: 1,
        document_type: "AADHAAR",
        provider_code: "DIGILOCKER",
        status: "SUBMITTED",
        requested_at: "2026-10-21T10:00:00Z",
        masked_identifier: "XXXX-XXXX-9012",
        malware_scan_status: "PASSED",
        consent_record_id: 10,
        purpose: "KYC_ONBOARDING",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockCase);

      const res = await initiateVerification({
        user_id: 1,
        document_type: "AADHAAR",
        file_name: "aadhaar.pdf",
        file_mime_type: "application/pdf",
        consent_record_id: 10,
        purpose: "KYC_ONBOARDING",
        raw_identifier_for_masking_only: "123456789012",
      });

      expect(res.case_id).toBe(55);
      expect(res.masked_identifier).toBe("XXXX-XXXX-9012");
      expect(res.malware_scan_status).toBe("PASSED");
      expect(apiClient.post).toHaveBeenCalledWith("/verification/initiate", expect.objectContaining({
        document_type: "AADHAAR",
        consent_record_id: 10,
      }));
    });

    it("generates short-lived presigned URL for document access (FR-0165, FR-0181)", async () => {
      const mockUrl: DocumentAccessUrlResponse = {
        case_id: 55,
        presigned_url: "https://storage.talentra.internal/docs/case-55?token=abc123xyz",
        expires_at: "2026-10-21T10:15:00Z",
        access_token: "tok_xyz",
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockUrl);

      const res = await getSecureDocumentUrl(55);
      expect(res.presigned_url).toContain("token=abc123xyz");
      expect(apiClient.get).toHaveBeenCalledWith("/verification/cases/55/access-url");
    });

    it("submits reviewer decision enforcing dual control for high-risk overrides (FR-0175, FR-0178)", async () => {
      const mockReviewedCase: VerificationCaseResponse = {
        case_id: 55,
        user_id: 1,
        document_type: "AADHAAR",
        provider_code: "DIGILOCKER",
        status: "VERIFIED",
        requested_at: "2026-10-21T10:00:00Z",
        completed_at: "2026-10-21T10:05:00Z",
        masked_identifier: "XXXX-XXXX-9012",
        malware_scan_status: "PASSED",
        consent_record_id: 10,
        purpose: "KYC_ONBOARDING",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockReviewedCase);

      const res = await submitVerificationReview(55, {
        decision: "VERIFIED",
        reason: "Valid document matched with official records",
        reviewer_user_id: 1,
        is_high_risk_override: true,
        second_approver_user_id: 2,
      });

      expect(res.status).toBe("VERIFIED");
      expect(apiClient.post).toHaveBeenCalledWith("/verification/cases/55/review", expect.objectContaining({
        decision: "VERIFIED",
        is_high_risk_override: true,
      }));
    });

    it("retrieves external integration boundary register (FR-0183)", async () => {
      const mockRegister: IntegrationBoundaryEntry[] = [
        {
          provider_code: "DIGILOCKER",
          display_name: "DigiLocker India",
          purpose: "Identity Document Verification",
          source_of_truth: "GOVERNMENT_AUTHORITY",
          stored_vs_reference_data: "TOKENIZED_REFERENCE_ONLY",
          timeout_seconds: 30,
          retry_policy: "EXPONENTIAL_BACKOFF_MAX_3",
          idempotency_policy: "DURABLE_IDEMPOTENCY_KEY",
          audit_behavior: "LOG_EVENT_HASH_NO_PII",
          status: "ACTIVE",
        },
      ];

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockRegister);

      const res = await getIntegrationRegister();
      expect(res).toHaveLength(1);
      expect(res[0].provider_code).toBe("DIGILOCKER");
      expect(apiClient.get).toHaveBeenCalledWith("/verification/integrations/register");
    });

    it("evaluates deterministic feature flag rollout (FR-0215, FR-0216)", async () => {
      const mockFlag: FeatureFlagResponse = {
        flag_code: "KYC_AUTOMATION",
        enabled: true,
        subject_key: "tenant-10",
        rollout_percentage: 100,
        evaluation_reason: "PERCENTAGE_ROLLOUT_MATCH",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockFlag);

      const res = await evaluateFeatureFlag({
        flag_code: "KYC_AUTOMATION",
        subject_key: "tenant-10",
      });

      expect(res.enabled).toBe(true);
      expect(apiClient.post).toHaveBeenCalledWith("/verification/feature-flags/evaluate", expect.objectContaining({
        flag_code: "KYC_AUTOMATION",
      }));
    });
  });

  describe("Administration, Role Governance & Audit Immutability (FR-0055, FR-0059, FR-0063, FR-0066, FR-0068)", () => {
    it("lists users for administrative governance", async () => {
      const mockList: AdminUserListResponse = {
        items: [
          {
            id: 1,
            email_address: "admin@talentra.com",
            display_name: "Admin User",
            account_status_code_id: 1,
            account_status: "ACTIVE",
            roles: ["SUPER_ADMIN"],
            actor_ids: ["SA00001"],
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockList);

      const res = await listAdminUsers({ page: 1 });
      expect(res.items).toHaveLength(1);
      expect(res.items[0].display_name).toBe("Admin User");
      expect(apiClient.get).toHaveBeenCalledWith("/admin/users", {
        params: { page: 1 },
      });
    });

    it("grants role to user preventing privilege escalation (FR-0055, FR-0068)", async () => {
      const mockUpdated: AdminUserResponse = {
        id: 2,
        email_address: "recruiter@acme.com",
        display_name: "Recruiter One",
        account_status_code_id: 1,
        account_status: "ACTIVE",
        roles: ["RECRUITER"],
        actor_ids: ["RC00002"],
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockUpdated);

      const res = await grantUserRole({
        user_id: 2,
        role_code: "RECRUITER",
      });

      expect(res.roles).toContain("RECRUITER");
      expect(apiClient.post).toHaveBeenCalledWith("/admin/roles/grant", {
        user_id: 2,
        role_code: "RECRUITER",
      });
    });

    it("updates account status with mandatory audit reason (FR-0060, FR-0201)", async () => {
      const mockSuspended: AdminUserResponse = {
        id: 2,
        email_address: "recruiter@acme.com",
        display_name: "Recruiter One",
        account_status_code_id: 2,
        account_status: "SUSPENDED",
        roles: ["RECRUITER"],
        actor_ids: ["RC00002"],
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "patch").mockResolvedValueOnce(mockSuspended);

      const res = await updateUserStatus(2, {
        account_status_code_id: 2,
        reason: "Compliance suspension",
      });

      expect(res.account_status).toBe("SUSPENDED");
      expect(apiClient.patch).toHaveBeenCalledWith("/admin/users/2/status", {
        account_status_code_id: 2,
        reason: "Compliance suspension",
      });
    });

    it("soft-deletes user account setting deleted_at timestamp (FR-0063)", async () => {
      const mockDeleted: AdminUserResponse = {
        id: 2,
        email_address: "recruiter@acme.com",
        display_name: "Recruiter One",
        account_status_code_id: 3,
        account_status: "DEACTIVATED",
        roles: [],
        actor_ids: ["RC00002"],
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-10-21T10:00:00Z",
        deleted_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "delete").mockResolvedValueOnce(mockDeleted);

      const res = await softDeleteUser(2, "Administrative soft deletion");
      expect(res.deleted_at).toBe("2026-10-21T10:00:00Z");
      expect(apiClient.delete).toHaveBeenCalledWith("/admin/users/2", {
        params: { reason: "Administrative soft deletion" },
      });
    });

    it("retrieves append-only audit events (FR-0059, FR-0064)", async () => {
      const mockEvents: AuditEventListResponse = {
        items: [
          {
            id: 1,
            actor_user_id: 1,
            action_code: "USER_ROLE_GRANTED",
            resource_type: "USER_ROLE",
            resource_id: "2",
            occurred_at: "2026-10-21T10:00:00Z",
            metadata_redacted: { role: "RECRUITER" },
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockEvents);

      const res = await listAuditEvents({ page: 1 });
      expect(res.items).toHaveLength(1);
      expect(res.items[0].action_code).toBe("USER_ROLE_GRANTED");
      expect(apiClient.get).toHaveBeenCalledWith("/admin/audit-events", {
        params: { page: 1 },
      });
    });

    it("revokes active identity session and terminates access (FR-0066)", async () => {
      const mockRevoked: AdminSessionResponse = {
        id: 15,
        user_id: 2,
        started_at: "2026-10-21T09:00:00Z",
        last_activity_at: "2026-10-21T09:30:00Z",
        expires_at: "2026-10-22T09:00:00Z",
        is_revoked: true,
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockRevoked);

      const res = await revokeIdentitySession(15, { session_id: 15, reason: "Security incident" });
      expect(res.is_revoked).toBe(true);
      expect(apiClient.post).toHaveBeenCalledWith("/admin/sessions/15/revoke", {
        session_id: 15,
        reason: "Security incident",
      });
    });

    it("generates privileged access review report (FR-0069)", async () => {
      const mockReview: AccessReviewReportResponse = {
        generated_at: "2026-10-21T10:00:00Z",
        reviewer_user_id: 1,
        privileged_users_count: 2,
        privileged_users: [
          {
            user_id: 1,
            email_address: "admin@talentra.com",
            display_name: "Admin User",
            roles: ["SUPER_ADMIN"],
          },
        ],
        audit_correlation_id: "audit-cor-999",
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockReview);

      const res = await getAccessReview();
      expect(res.privileged_users_count).toBe(2);
      expect(apiClient.get).toHaveBeenCalledWith("/admin/access-review");
    });

    it("retrieves sensitive column data governance classification inventory (FR-0065)", async () => {
      const mockClass: DataClassificationResponse = {
        total_classified: 150,
        unclassified_count: 0,
        items: [
          {
            table_name: "verification_case",
            column_name: "masked_identifier",
            classification: "CONFIDENTIAL",
            data_type: "VARCHAR(80)",
          },
        ],
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockClass);

      const res = await getDataClassification();
      expect(res.total_classified).toBe(150);
      expect(res.items[0].classification).toBe("CONFIDENTIAL");
      expect(apiClient.get).toHaveBeenCalledWith("/admin/data-classification");
    });

    it("runs data retention scheduler with dry run mode (FR-0177, FR-0196)", async () => {
      const mockSummary: RetentionJobSummaryResponse = {
        job_id: 8,
        data_class: "KYC_DOCUMENTS",
        dry_run: true,
        evaluated_records: 200,
        eligible_for_purge: 15,
        purged_records: 0,
        skipped_due_to_legal_hold: 2,
        executed_at: "2026-10-21T10:00:00Z",
        status: "COMPLETED",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockSummary);

      const res = await runRetentionJob({
        dry_run: true,
        target_data_class: "KYC_DOCUMENTS",
        retention_days: 2555,
      });

      expect(res.dry_run).toBe(true);
      expect(res.eligible_for_purge).toBe(15);
      expect(res.purged_records).toBe(0);
      expect(apiClient.post).toHaveBeenCalledWith("/verification/retention/run", expect.objectContaining({
        dry_run: true,
        target_data_class: "KYC_DOCUMENTS",
      }));
    });
  });
});
