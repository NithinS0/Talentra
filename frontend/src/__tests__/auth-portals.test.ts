import { describe, it, expect } from "vitest";
import { getPortalPathForRole, getSafeReturnUrl } from "../lib/auth/session";

describe("Stage 17B: Role Portals & Safe Return URL Routing", () => {
  describe("getPortalPathForRole", () => {
    it("resolves Super Admin portal route correctly", () => {
      expect(getPortalPathForRole("SUPER_ADMIN")).toBe("/portal/super-admin");
    });

    it("resolves Platform Admin portal route correctly", () => {
      expect(getPortalPathForRole("ADMIN")).toBe("/portal/admin");
    });

    it("resolves Account Admin portal route correctly", () => {
      expect(getPortalPathForRole("ACCOUNT_ADMIN")).toBe("/portal/account-admin");
    });

    it("resolves Employer portal route correctly", () => {
      expect(getPortalPathForRole("EMPLOYER")).toBe("/portal/employer");
    });

    it("resolves Recruiter portal route correctly", () => {
      expect(getPortalPathForRole("RECRUITER")).toBe("/portal/recruiter");
    });

    it("resolves Consultant portal route correctly", () => {
      expect(getPortalPathForRole("CONSULTANT")).toBe("/portal/consultant");
    });

    it("resolves Candidate portal route correctly", () => {
      expect(getPortalPathForRole("CANDIDATE")).toBe("/portal/candidate");
    });

    it("resolves Placement Officer portal route correctly", () => {
      expect(getPortalPathForRole("PLACEMENT_OFFICER")).toBe("/portal/placement-officer");
    });

    it("resolves unknown or unassigned roles to dashboard fallback", () => {
      expect(getPortalPathForRole("GUEST")).toBe("/dashboard");
      expect(getPortalPathForRole("UNKNOWN")).toBe("/dashboard");
    });
  });

  describe("getSafeReturnUrl", () => {
    it("preserves safe relative paths", () => {
      expect(getSafeReturnUrl("/jobs")).toBe("/jobs");
      expect(getSafeReturnUrl("/portal/candidate?tab=milestones")).toBe(
        "/portal/candidate?tab=milestones"
      );
    });

    it("blocks open redirect attempts using double leading slashes", () => {
      expect(getSafeReturnUrl("//attacker.com")).toBe("/dashboard");
      expect(getSafeReturnUrl("//evil.org/phish")).toBe("/dashboard");
    });

    it("blocks open redirect attempts using absolute protocols", () => {
      expect(getSafeReturnUrl("https://evil.com")).toBe("/dashboard");
      expect(getSafeReturnUrl("http://evil.com")).toBe("/dashboard");
      expect(getSafeReturnUrl("javascript:alert(1)")).toBe("/dashboard");
    });

    it("blocks backslash open redirect vectors", () => {
      expect(getSafeReturnUrl("/\\attacker.com")).toBe("/dashboard");
    });

    it("falls back cleanly on empty or null values", () => {
      expect(getSafeReturnUrl(null)).toBe("/dashboard");
      expect(getSafeReturnUrl(undefined, "/portal/candidate")).toBe("/portal/candidate");
      expect(getSafeReturnUrl("   ")).toBe("/dashboard");
    });
  });
});
