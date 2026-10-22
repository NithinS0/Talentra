import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { formatCurrency, formatDate } from "../lib/utils";

describe("Shared UI Component Library", () => {
  describe("Button", () => {
    it("renders children text accurately", () => {
      render(<Button>Click Action</Button>);
      expect(screen.getByRole("button", { name: /click action/i })).toBeDefined();
    });

    it("triggers onClick callback when clicked", () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Submit</Button>);
      fireEvent.click(screen.getByRole("button", { name: /submit/i }));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it("disables button when disabled prop is provided", () => {
      render(<Button disabled>Disabled Button</Button>);
      const btn = screen.getByRole("button", { name: /disabled button/i });
      expect((btn as HTMLButtonElement).disabled).toBe(true);
    });

    it("shows loading state and disables interaction when isLoading is true", () => {
      render(<Button isLoading>Processing</Button>);
      const btn = screen.getByRole("button");
      expect((btn as HTMLButtonElement).disabled).toBe(true);
      expect(btn.querySelector(".animate-spin")).toBeDefined();
    });
  });

  describe("Badge", () => {
    it("renders default badge variant", () => {
      render(<Badge>Active Status</Badge>);
      expect(screen.getByText("Active Status")).toBeDefined();
    });

    it("renders success and warning variants", () => {
      const { rerender } = render(<Badge variant="success">Completed</Badge>);
      expect(screen.getByText("Completed")).toBeDefined();

      rerender(<Badge variant="warning">Pending Review</Badge>);
      expect(screen.getByText("Pending Review")).toBeDefined();
    });
  });

  describe("Card", () => {
    it("renders card title, description, and content", () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Milestone Escrow</CardTitle>
            <CardDescription>Escrow funds held securely</CardDescription>
          </CardHeader>
          <CardContent>
            <p>Active Balance: $5,000</p>
          </CardContent>
        </Card>
      );
      expect(screen.getByText("Milestone Escrow")).toBeDefined();
      expect(screen.getByText("Escrow funds held securely")).toBeDefined();
      expect(screen.getByText("Active Balance: $5,000")).toBeDefined();
    });
  });

  describe("Input", () => {
    it("renders input field with label and placeholder", () => {
      render(<Input label="Email Address" placeholder="user@talentra.io" />);
      expect(screen.getByLabelText("Email Address")).toBeDefined();
      expect(screen.getByPlaceholderText("user@talentra.io")).toBeDefined();
    });

    it("displays error message when provided", () => {
      render(<Input label="Password" error="Password must be at least 8 characters" />);
      expect(screen.getByText("Password must be at least 8 characters")).toBeDefined();
    });
  });

  describe("Format Utilities", () => {
    it("formats currency correctly into USD currency representation", () => {
      const formatted = formatCurrency(12500);
      expect(formatted).toContain("12,500");
    });

    it("formats dates into readable string", () => {
      const date = new Date(2026, 9, 20); // Oct 20, 2026
      const formatted = formatDate(date);
      expect(formatted).toContain("2026");
      expect(formatted).toContain("Oct");
    });
  });
});
