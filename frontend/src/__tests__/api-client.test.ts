import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { apiClient, ApiClientError } from "../lib/api/client";

describe("apiClient", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    apiClient.setAuthToken(null);
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("sends standard GET request with default headers", async () => {
    const mockResponse = { data: "test-data" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    });

    const result = await apiClient.get<typeof mockResponse>("/test-endpoint");
    expect(result).toEqual(mockResponse);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/test-endpoint"),
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          Accept: "application/json",
        }),
      })
    );
  });

  it("appends query parameters correctly", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ results: [] }),
    });

    await apiClient.get("/items", { params: { page: 2, limit: 10, active: true } });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/items\?page=2&limit=10&active=true/),
      expect.anything()
    );
  });

  it("includes Authorization header when token is configured", async () => {
    apiClient.setAuthToken("mock-jwt-token-xyz");

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ authenticated: true }),
    });

    await apiClient.get("/auth/me");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer mock-jwt-token-xyz",
        }),
      })
    );
  });

  it("throws ApiClientError with status 401 on Unauthorized response", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Invalid or expired authentication credentials" }),
    });

    await expect(apiClient.get("/protected")).rejects.toThrow(ApiClientError);
    await expect(apiClient.get("/protected")).rejects.toMatchObject({
      status: 401,
      message: "Invalid or expired authentication credentials",
    });
  });

  it("throws ApiClientError with status 403 on Forbidden response", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: "Insufficient privileges for this operation" }),
    });

    await expect(apiClient.get("/admin/users")).rejects.toMatchObject({
      status: 403,
      message: "Insufficient privileges for this operation",
    });
  });

  it("handles network failures cleanly", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("Network connection lost"));

    await expect(apiClient.get("/health")).rejects.toThrow("Network connection lost");
  });
});
