import { describe, it, expect, afterEach, vi } from "vitest";
import { registerCandidate } from "../lib/api/auth";
import { CandidateRegisterRequest, CandidateProfileResponse } from "../types/auth";
import { ApiClientError } from "../lib/api/client";

describe("Stage 17B: Candidate Self-Registration API", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  const validPayload: CandidateRegisterRequest = {
    first_name: "Arun",
    middle_name: "Kumar",
    last_name: "Sharma",
    country_code: "IN",
    phone_number: "9876543210",
    headline: "Lead Full-Stack Engineer",
    summary: "Python and Next.js specialist.",
  };

  it("submits candidate registration payload to /auth/register/candidate", async () => {
    const mockSuccessResponse: CandidateProfileResponse = {
      user_id: 101,
      actor_id: "CA00001",
      first_name: "Arun",
      middle_name: "Kumar",
      last_name: "Sharma",
      display_name: "Arun Sharma",
      headline: "Lead Full-Stack Engineer",
      summary: "Python and Next.js specialist.",
      email_address: "arun.sharma@example.com",
      phone_e164: "+919876543210",
      country_code: "IN",
      country_name: "India",
      completion_score: 85.0,
      created_at: "2026-10-20T12:00:00Z",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockSuccessResponse,
    });

    const response = await registerCandidate(validPayload);
    expect(response).toEqual(mockSuccessResponse);
    expect(response.actor_id).toBe("CA00001");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/auth/register/candidate"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(validPayload),
      })
    );
  });

  it("throws ApiClientError with 409 Conflict when candidate profile exists", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({
        detail: "Candidate profile already exists for this account.",
      }),
    });

    await expect(registerCandidate(validPayload)).rejects.toThrow(ApiClientError);
    await expect(registerCandidate(validPayload)).rejects.toMatchObject({
      status: 409,
      message: "Candidate profile already exists for this account.",
    });
  });

  it("throws ApiClientError with 422 Unprocessable Entity on invalid country code", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        detail: "Invalid ISO 3166-1 alpha-2 country code: XX",
      }),
    });

    await expect(
      registerCandidate({ ...validPayload, country_code: "XX" })
    ).rejects.toMatchObject({
      status: 422,
      message: "Invalid ISO 3166-1 alpha-2 country code: XX",
    });
  });
});
