import { describe, it, expect, beforeEach } from "vitest";
import {
  getStoredSession,
  setStoredSession,
  clearStoredSession,
  getDefaultActorIdForRole,
  getRoleForActorPrefix,
} from "../lib/auth/session";
import { AuthSession } from "../types/auth";

describe("Auth Session Utilities", () => {
  beforeEach(() => {
    clearStoredSession();
  });

  const mockSession: AuthSession = {
    accessToken: "demo-jwt-token-123",
    user: {
      user_id: 1,
      display_name: "Alice Admin",
      email_address: "alice@talentra.io",
      roles: ["SUPER_ADMIN"],
      actor_identities: [
        {
          role_code: "SUPER_ADMIN",
          actor_prefix: "SA",
          actor_id: "SA00001",
          is_active: true,
        },
      ],
      created_at: "2026-01-01T00:00:00Z",
    },
    activeRole: "SUPER_ADMIN",
    activeActorId: "SA00001",
  };

  it("stores and retrieves auth session from localStorage", () => {
    expect(getStoredSession()).toBeNull();

    setStoredSession(mockSession);

    const session = getStoredSession();
    expect(session).not.toBeNull();
    expect(session?.accessToken).toBe("demo-jwt-token-123");
    expect(session?.activeRole).toBe("SUPER_ADMIN");
    expect(session?.activeActorId).toBe("SA00001");
  });

  it("clears stored session properly", () => {
    setStoredSession(mockSession);
    clearStoredSession();
    expect(getStoredSession()).toBeNull();
  });

  it("maps roles to canonical actor ID prefixes correctly", () => {
    expect(getDefaultActorIdForRole("SYSTEM_ADMIN")).toBe("SA00001");
    expect(getDefaultActorIdForRole("SUPER_ADMIN")).toBe("SA00001");
    expect(getDefaultActorIdForRole("ADMIN")).toBe("AD00001");
    expect(getDefaultActorIdForRole("CANDIDATE")).toBe("CA00001");
    expect(getDefaultActorIdForRole("CLIENT")).toBe("CL00001");
    expect(getDefaultActorIdForRole("FREELANCER")).toBe("FL00001");
    expect(getDefaultActorIdForRole("DISPUTE_ARBITRATOR")).toBe("DA00001");
    expect(getDefaultActorIdForRole("PLACEMENT_OFFICER")).toBe("PO00001");
  });

  it("resolves role from actor prefix", () => {
    expect(getRoleForActorPrefix("SA00001")).toBe("SUPER_ADMIN");
    expect(getRoleForActorPrefix("FL00001")).toBe("FREELANCER");
    expect(getRoleForActorPrefix("CL00001")).toBe("CLIENT");
    expect(getRoleForActorPrefix("DA00001")).toBe("DISPUTE_ARBITRATOR");
    expect(getRoleForActorPrefix("XX99999")).toBe("CLIENT"); // Default fallback
  });
});
