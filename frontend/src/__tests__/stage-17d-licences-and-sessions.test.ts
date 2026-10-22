import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "@/lib/api/client";
import {
  createLicence,
  getLicence,
  updateLicenceStatus,
  allocateSeat,
  releaseSeat,
  registerDevice,
  revokeDevice,
  createSession,
  heartbeatSession,
  endSession,
  revokeSession,
  cleanupExpiredSessions,
} from "@/lib/api/licences";
import {
  LicenceResponse,
  SeatAllocationResponse,
  DeviceResponse,
  SessionResponse,
  SessionCleanupResponse,
} from "@/types/licences";

describe("Stage 17D: Licences, Seats, Devices & Sessions (Module M07)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("Licence Lifecycle (FR-0098, FR-0099)", () => {
    it("creates licence with positive integer seat and device limits", async () => {
      const mockLicence: LicenceResponse = {
        id: 1,
        licence_code: "TALENTRA-ENT-2026",
        account_id: 1,
        max_users: 10,
        max_devices_per_user: 3,
        valid_from: "2026-01-01T00:00:00Z",
        valid_until: "2027-01-01T00:00:00Z",
        status_code_id: 1,
        status: "ACTIVE",
        allocated_seats: 0,
        available_seats: 10,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockLicence);

      const res = await createLicence({
        licence_code: "TALENTRA-ENT-2026",
        account_id: 1,
        max_users: 10,
        max_devices_per_user: 3,
        valid_from: "2026-01-01T00:00:00Z",
        valid_until: "2027-01-01T00:00:00Z",
      });

      expect(res.id).toBe(1);
      expect(res.max_users).toBe(10);
      expect(res.max_devices_per_user).toBe(3);
      expect(apiClient.post).toHaveBeenCalledWith("/licences", expect.objectContaining({
        licence_code: "TALENTRA-ENT-2026",
        max_users: 10,
      }));
    });

    it("retrieves authoritative licence capacity metrics", async () => {
      const mockLicence: LicenceResponse = {
        id: 1,
        licence_code: "TALENTRA-ENT-2026",
        account_id: 1,
        max_users: 10,
        max_devices_per_user: 3,
        valid_from: "2026-01-01T00:00:00Z",
        valid_until: "2027-01-01T00:00:00Z",
        status_code_id: 1,
        status: "ACTIVE",
        allocated_seats: 4,
        available_seats: 6,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockLicence);

      const res = await getLicence(1);
      expect(res.available_seats).toBe(6);
      expect(res.allocated_seats).toBe(4);
      expect(apiClient.get).toHaveBeenCalledWith("/licences/1");
    });

    it("updates licence lifecycle status with confirmation audit reason", async () => {
      const mockSuspended: LicenceResponse = {
        id: 1,
        licence_code: "TALENTRA-ENT-2026",
        account_id: 1,
        max_users: 10,
        max_devices_per_user: 3,
        valid_from: "2026-01-01T00:00:00Z",
        valid_until: "2027-01-01T00:00:00Z",
        status_code_id: 2,
        status: "SUSPENDED",
        allocated_seats: 4,
        available_seats: 6,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "put").mockResolvedValueOnce(mockSuspended);

      const res = await updateLicenceStatus(1, {
        status_code_id: 2,
        reason: "Compliance audit suspension",
      });

      expect(res.status).toBe("SUSPENDED");
      expect(apiClient.put).toHaveBeenCalledWith("/licences/1/status", {
        status_code_id: 2,
        reason: "Compliance audit suspension",
      });
    });
  });

  describe("Seat Allocation & Release (FR-0100, FR-0110)", () => {
    it("allocates a seat under transactional lock", async () => {
      const mockAlloc: SeatAllocationResponse = {
        id: 99,
        licence_id: 1,
        user_id: 5,
        status_code_id: 1,
        status: "ACTIVE",
        created_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockAlloc);

      const res = await allocateSeat({ licence_id: 1, user_id: 5 });
      expect(res.id).toBe(99);
      expect(res.user_id).toBe(5);
      expect(apiClient.post).toHaveBeenCalledWith("/licences/seats", {
        licence_id: 1,
        user_id: 5,
      });
    });

    it("handles seat capacity exhaustion (400 Bad Request)", async () => {
      vi.spyOn(apiClient, "post").mockRejectedValueOnce({
        status: 400,
        message: "Licence seat capacity exceeded (FR-0100)",
      });

      await expect(allocateSeat({ licence_id: 1, user_id: 99 })).rejects.toMatchObject({
        status: 400,
      });
    });

    it("releases seat and immediately restores licence headroom (FR-0110)", async () => {
      const mockReleased: SeatAllocationResponse = {
        id: 99,
        licence_id: 1,
        user_id: 5,
        status_code_id: 2,
        status: "RELEASED",
        created_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "delete").mockResolvedValueOnce(mockReleased);

      const res = await releaseSeat(99, "Employee offboarding");
      expect(res.status).toBe("RELEASED");
      expect(apiClient.delete).toHaveBeenCalledWith("/licences/seats/99", {
        params: { reason: "Employee offboarding" },
      });
    });
  });

  describe("Device Registration & Revocation (FR-0106, FR-0108)", () => {
    it("registers client device using 64-hex SHA-256 fingerprint hash", async () => {
      const mockDevice: DeviceResponse = {
        id: 42,
        user_id: 1,
        device_fingerprint_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        device_label: "MacBook Pro",
        first_seen_at: "2026-10-21T10:00:00Z",
        last_seen_at: "2026-10-21T10:00:00Z",
        is_active: true,
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockDevice);

      const res = await registerDevice({
        device_fingerprint_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        device_label: "MacBook Pro",
      });

      expect(res.id).toBe(42);
      expect(res.is_active).toBe(true);
      expect(apiClient.post).toHaveBeenCalledWith("/licences/devices", {
        device_fingerprint_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        device_label: "MacBook Pro",
      });
    });

    it("revokes device and terminates linked active sessions (FR-0106)", async () => {
      const mockRevokedDevice: DeviceResponse = {
        id: 42,
        user_id: 1,
        device_fingerprint_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        device_label: "MacBook Pro",
        first_seen_at: "2026-10-21T10:00:00Z",
        last_seen_at: "2026-10-21T10:00:00Z",
        revoked_at: "2026-10-21T11:00:00Z",
        is_active: false,
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockRevokedDevice);

      const res = await revokeDevice(42, { reason: "Lost device" });
      expect(res.is_active).toBe(false);
      expect(apiClient.post).toHaveBeenCalledWith("/licences/devices/42/revoke", {
        reason: "Lost device",
      });
    });
  });

  describe("Session Governance & Cleanup (FR-0101, FR-0104, FR-0204)", () => {
    it("creates authenticated session enforcing concurrency limits", async () => {
      const mockSession: SessionResponse = {
        id: 501,
        user_id: 1,
        started_at: "2026-10-21T10:00:00Z",
        last_activity_at: "2026-10-21T10:00:00Z",
        expires_at: "2026-10-22T10:00:00Z",
        is_active: true,
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockSession);

      const res = await createSession({ duration_seconds: 86400 });
      expect(res.id).toBe(501);
      expect(res.is_active).toBe(true);
      expect(apiClient.post).toHaveBeenCalledWith("/licences/sessions", {
        duration_seconds: 86400,
      });
    });

    it("updates session heartbeat (FR-0104)", async () => {
      const mockHeartbeat: SessionResponse = {
        id: 501,
        user_id: 1,
        started_at: "2026-10-21T10:00:00Z",
        last_activity_at: "2026-10-21T10:30:00Z",
        expires_at: "2026-10-22T10:00:00Z",
        is_active: true,
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockHeartbeat);

      const res = await heartbeatSession(501);
      expect(res.last_activity_at).toBe("2026-10-21T10:30:00Z");
      expect(apiClient.post).toHaveBeenCalledWith("/licences/sessions/501/heartbeat");
    });

    it("ends session and releases active device capacity (FR-0109)", async () => {
      const mockEnded: SessionResponse = {
        id: 501,
        user_id: 1,
        started_at: "2026-10-21T10:00:00Z",
        last_activity_at: "2026-10-21T10:30:00Z",
        expires_at: "2026-10-22T10:00:00Z",
        ended_at: "2026-10-21T10:35:00Z",
        is_active: false,
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockEnded);

      const res = await endSession(501);
      expect(res.is_active).toBe(false);
      expect(apiClient.post).toHaveBeenCalledWith("/licences/sessions/501/end");
    });

    it("idempotently cleans up expired sessions (FR-0204)", async () => {
      const mockCleanup: SessionCleanupResponse = {
        cleaned_count: 7,
        timestamp: "2026-10-21T11:00:00Z",
        status: "COMPLETED",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockCleanup);

      const res = await cleanupExpiredSessions();
      expect(res.cleaned_count).toBe(7);
      expect(res.status).toBe("COMPLETED");
      expect(apiClient.post).toHaveBeenCalledWith("/licences/sessions/cleanup");
    });
  });
});
