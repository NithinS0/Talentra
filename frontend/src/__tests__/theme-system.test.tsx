import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeToggle } from "../components/layout/theme-toggle";
import { NAV_ITEMS, PORTAL_ITEMS } from "../components/layout/sidebar";

// Mock next-themes
const mockSetTheme = vi.fn();
let mockCurrentTheme = "light";

vi.mock("next-themes", () => ({
  useTheme: () => ({
    theme: mockCurrentTheme,
    resolvedTheme: mockCurrentTheme,
    setTheme: (theme: string) => {
      mockCurrentTheme = theme;
      mockSetTheme(theme);
    },
  }),
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe("Theme System & Role-Based Navigation Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCurrentTheme = "light";
  });

  describe("Theme Toggle Component", () => {
    it("renders with light mode as default and correct accessible aria-label", () => {
      render(<ThemeToggle />);
      const button = screen.getByRole("button", { name: /switch to dark mode/i });
      expect(button).toBeDefined();
    });

    it("triggers theme toggle to dark mode when clicked", () => {
      render(<ThemeToggle />);
      const button = screen.getByRole("button", { name: /switch to dark mode/i });
      fireEvent.click(button);
      expect(mockSetTheme).toHaveBeenCalledWith("dark");
    });

    it("displays 'switch to light mode' label when active theme is dark", () => {
      mockCurrentTheme = "dark";
      render(<ThemeToggle />);
      const button = screen.getByRole("button", { name: /switch to light mode/i });
      expect(button).toBeDefined();
      fireEvent.click(button);
      expect(mockSetTheme).toHaveBeenCalledWith("light");
    });
  });

  describe("Persona Navigation Matrix Filtering", () => {
    it("restricts CANDIDATE from seeing recruiter/admin directories", () => {
      const candidateNav = NAV_ITEMS.filter((item) => !item.roles || item.roles.includes("CANDIDATE"));
      const hrefs = candidateNav.map((i) => i.href);

      // Permitted for Candidate
      expect(hrefs).toContain("/candidates/me");
      expect(hrefs).toContain("/jobs");
      expect(hrefs).toContain("/applications");
      expect(hrefs).toContain("/verification");
      expect(hrefs).toContain("/notifications");
      expect(hrefs).toContain("/support");

      // Strictly Forbidden for Candidate
      expect(hrefs).not.toContain("/candidates");
      expect(hrefs).not.toContain("/organisations");
      expect(hrefs).not.toContain("/sourcing");
      expect(hrefs).not.toContain("/licences");
      expect(hrefs).not.toContain("/administration");
      expect(hrefs).not.toContain("/master-data");
      expect(hrefs).not.toContain("/gigs");
    });

    it("restricts CANDIDATE to only the Candidate portal", () => {
      const candidatePortals = PORTAL_ITEMS.filter((item) => item.roles.includes("CANDIDATE"));
      expect(candidatePortals.length).toBe(1);
      expect(candidatePortals[0].href).toBe("/portal/candidate");
    });

    it("restricts RECRUITER to recruitment modules and blocks admin routes", () => {
      const recruiterNav = NAV_ITEMS.filter((item) => !item.roles || item.roles.includes("RECRUITER"));
      const hrefs = recruiterNav.map((i) => i.href);

      expect(hrefs).toContain("/jobs");
      expect(hrefs).toContain("/applications");
      expect(hrefs).toContain("/candidates");
      expect(hrefs).toContain("/sourcing");

      // Forbidden for Recruiter
      expect(hrefs).not.toContain("/organisations");
      expect(hrefs).not.toContain("/licences");
      expect(hrefs).not.toContain("/administration");
      expect(hrefs).not.toContain("/master-data");
      expect(hrefs).not.toContain("/verification");
    });

    it("allows EMPLOYER to view organization and hiring pipelines but not platform admin", () => {
      const employerNav = NAV_ITEMS.filter((item) => !item.roles || item.roles.includes("EMPLOYER"));
      const hrefs = employerNav.map((i) => i.href);

      expect(hrefs).toContain("/jobs");
      expect(hrefs).toContain("/applications");
      expect(hrefs).toContain("/candidates");
      expect(hrefs).toContain("/organisations");
      expect(hrefs).toContain("/gigs");
      expect(hrefs).toContain("/sourcing");
      expect(hrefs).toContain("/billing");

      // Forbidden for Employer
      expect(hrefs).not.toContain("/licences");
      expect(hrefs).not.toContain("/administration");
      expect(hrefs).not.toContain("/master-data");
    });

    it("allows SUPER_ADMIN access to administration, master data, licences, and all portals", () => {
      const adminNav = NAV_ITEMS.filter((item) => !item.roles || item.roles.includes("SUPER_ADMIN"));
      const hrefs = adminNav.map((i) => i.href);

      expect(hrefs).toContain("/administration");
      expect(hrefs).toContain("/master-data");
      expect(hrefs).toContain("/licences");
      expect(hrefs).toContain("/organisations");

      const adminPortals = PORTAL_ITEMS.filter((item) => item.roles.includes("SUPER_ADMIN"));
      expect(adminPortals.length).toBe(PORTAL_ITEMS.length);
    });

    it("restricts CONSULTANT to gig marketplace and sourcing", () => {
      const consultantNav = NAV_ITEMS.filter((item) => !item.roles || item.roles.includes("CONSULTANT"));
      const hrefs = consultantNav.map((i) => i.href);

      expect(hrefs).toContain("/gigs");
      expect(hrefs).toContain("/sourcing");
      expect(hrefs).toContain("/billing");

      expect(hrefs).not.toContain("/candidates");
      expect(hrefs).not.toContain("/organisations");
      expect(hrefs).not.toContain("/licences");
      expect(hrefs).not.toContain("/administration");
    });

    it("restricts PLACEMENT_OFFICER to jobs, applications, candidate roster, analytics", () => {
      const poNav = NAV_ITEMS.filter((item) => !item.roles || item.roles.includes("PLACEMENT_OFFICER"));
      const hrefs = poNav.map((i) => i.href);

      expect(hrefs).toContain("/jobs");
      expect(hrefs).toContain("/applications");
      expect(hrefs).toContain("/candidates");
      expect(hrefs).toContain("/analytics");

      expect(hrefs).not.toContain("/licences");
      expect(hrefs).not.toContain("/administration");
      expect(hrefs).not.toContain("/master-data");
      expect(hrefs).not.toContain("/gigs");
    });
  });
});
