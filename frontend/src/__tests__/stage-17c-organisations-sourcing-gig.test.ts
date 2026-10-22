import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "@/lib/api/client";
import {
  listOrganisations,
  getOrganisationDetails,
  createOrganisation,
  getOrganisationRecruiters,
} from "@/lib/api/organisations";
import {
  listSourcingRequests,
  createSourcingRequest,
  respondToSourcingRequest,
  cancelSourcingRequest,
} from "@/lib/api/sourcing";
import {
  listGigRequests,
  getGigRequestDetails,
  createGigRequest,
  applyToGigRequest,
} from "@/lib/api/gig";
import { OrganisationResponse, OrganisationListResponse } from "@/types/organisations";
import { SourcingRequestResponse, SourcingRequestListResponse } from "@/types/sourcing";
import { GigRequestResponse, GigRequestListResponse, GigApplicationResponse } from "@/types/gig";

describe("Stage 17C: Organisations, Sourcing & Gig Marketplace APIs", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("Organisations & Accounts (/api/v1/organisations)", () => {
    it("lists organisations with search query and pagination", async () => {
      const mockOrgs: OrganisationListResponse = {
        items: [
          {
            id: 1,
            legal_name: "Acme Corporation Technologies Private Limited",
            display_name: "Acme Corporation",
            organisation_type_code_id: 1,
            status_code_id: 1,
            status_code: "ACTIVE",
            primary_country_id: 101,
            primary_country_name: "India",
            created_at: "2026-01-10T00:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
        total_pages: 1,
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockOrgs);

      const res = await listOrganisations({ q: "Acme" });
      expect(res.items.length).toBe(1);
      expect(res.items[0].display_name).toBe("Acme Corporation");
      expect(apiClient.get).toHaveBeenCalledWith("/organisations", {
        params: { q: "Acme" },
      });
    });

    it("retrieves organisation details by ID", async () => {
      const mockOrg: OrganisationResponse = {
        id: 1,
        legal_name: "Acme Corporation Technologies Private Limited",
        display_name: "Acme Corporation",
        organisation_type_code_id: 1,
        status_code_id: 1,
        status_code: "ACTIVE",
        created_at: "2026-01-10T00:00:00Z",
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockOrg);

      const res = await getOrganisationDetails(1);
      expect(res.id).toBe(1);
      expect(apiClient.get).toHaveBeenCalledWith("/organisations/1");
    });

    it("creates a new organisation legal entity", async () => {
      const newOrg = {
        legal_name: "FinPay Escrow Solutions Ltd",
        display_name: "FinPay Escrow",
        primary_country_id: 101,
      };

      const mockCreated: OrganisationResponse = {
        id: 88,
        legal_name: newOrg.legal_name,
        display_name: newOrg.display_name,
        organisation_type_code_id: 1,
        status_code_id: 1,
        status_code: "ACTIVE",
        created_at: "2026-10-20T12:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockCreated);

      const res = await createOrganisation(newOrg);
      expect(res.id).toBe(88);
      expect(apiClient.post).toHaveBeenCalledWith("/organisations", newOrg);
    });

    it("retrieves recruiters mapped to an organisation", async () => {
      const mockRecruiters = [
        {
          id: 1,
          organisation_id: 1,
          recruiter_user_id: 5,
          recruiter_actor_id: "RE00005",
          recruiter_name: "Pooja Recruiter",
          valid_from: "2026-01-01T00:00:00Z",
          valid_until: null,
          assigned_by_user_id: 1,
        },
      ];

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockRecruiters);

      const res = await getOrganisationRecruiters(1);
      expect(res.length).toBe(1);
      expect(res[0].recruiter_actor_id).toBe("RE00005");
      expect(apiClient.get).toHaveBeenCalledWith("/organisations/1/recruiters");
    });
  });

  describe("Sourcing & Consultant Requests (/api/v1/sourcing)", () => {
    it("lists sourcing requests with pagination", async () => {
      const mockSourcing: SourcingRequestListResponse = {
        items: [
          {
            id: 12,
            job_requirement_id: 101,
            job_title: "Staff Next.js Platform Architect",
            organisation_id: 1,
            organisation_name: "Acme Corporation",
            requester_user_id: 2,
            consultant_user_id: 9,
            consultant_name: "Rajesh Consultant",
            status_code_id: 1,
            status: "PENDING",
            requested_at: "2026-10-19T10:00:00Z",
            created_at: "2026-10-19T10:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockSourcing);

      const res = await listSourcingRequests({ page: 1, page_size: 20 });
      expect(res.items.length).toBe(1);
      expect(res.items[0].status).toBe("PENDING");
      expect(apiClient.get).toHaveBeenCalledWith("/sourcing/requests", {
        params: { page: 1, page_size: 20 },
      });
    });

    it("creates sourcing request linked to job requirement", async () => {
      const payload = {
        job_requirement_id: 101,
        consultant_user_id: 9,
      };

      const mockResponse: SourcingRequestResponse = {
        id: 13,
        job_requirement_id: 101,
        job_title: "Staff Next.js Platform Architect",
        organisation_id: 1,
        organisation_name: "Acme Corporation",
        requester_user_id: 2,
        consultant_user_id: 9,
        status_code_id: 1,
        status: "PENDING",
        requested_at: "2026-10-20T10:00:00Z",
        created_at: "2026-10-20T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockResponse);

      const res = await createSourcingRequest(payload);
      expect(res.id).toBe(13);
      expect(apiClient.post).toHaveBeenCalledWith("/sourcing/requests", payload);
    });

    it("consultant accepts a sourcing request", async () => {
      const mockAccepted: SourcingRequestResponse = {
        id: 12,
        job_requirement_id: 101,
        job_title: "Staff Next.js Platform Architect",
        organisation_id: 1,
        organisation_name: "Acme Corporation",
        requester_user_id: 2,
        consultant_user_id: 9,
        status_code_id: 2,
        status: "ACCEPTED",
        requested_at: "2026-10-19T10:00:00Z",
        created_at: "2026-10-19T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockAccepted);

      const res = await respondToSourcingRequest(12, "ACCEPT", "Ready to source talent");
      expect(res.status).toBe("ACCEPTED");
      expect(apiClient.post).toHaveBeenCalledWith("/sourcing/requests/12/respond", {
        decision: "ACCEPT",
        reason: "Ready to source talent",
      });
    });

    it("employer cancels an active sourcing request", async () => {
      const mockCancelled: SourcingRequestResponse = {
        id: 12,
        job_requirement_id: 101,
        job_title: "Staff Next.js Platform Architect",
        organisation_id: 1,
        organisation_name: "Acme Corporation",
        requester_user_id: 2,
        consultant_user_id: 9,
        status_code_id: 4,
        status: "CANCELLED",
        requested_at: "2026-10-19T10:00:00Z",
        created_at: "2026-10-19T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockCancelled);

      const res = await cancelSourcingRequest(12, "Position filled internally");
      expect(res.status).toBe("CANCELLED");
      expect(apiClient.post).toHaveBeenCalledWith("/sourcing/requests/12/cancel", {
        reason: "Position filled internally",
      });
    });
  });

  describe("Gig Marketplace (/api/v1/gig)", () => {
    it("lists open gig requests with pricing and dates", async () => {
      const mockGigs: GigRequestListResponse = {
        items: [
          {
            id: 301,
            requester_organisation_id: 1,
            organisation_name: "Acme Corporation",
            created_by_user_id: 2,
            title: "Build Zero-Knowledge Identity Verification Integration",
            description: "Implement ZK proof client with cryptographic milestone verification.",
            starts_at: "2026-11-01T09:00:00Z",
            ends_at: "2026-11-30T18:00:00Z",
            pricing_type_code_id: 1,
            pricing_type: "FIXED",
            price_amount: 75000,
            currency_code: "INR",
            status_code_id: 1,
            status: "OPEN",
            created_at: "2026-10-20T00:00:00Z",
            updated_at: "2026-10-20T00:00:00Z",
          },
        ],
        total: 1,
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockGigs);

      const res = await listGigRequests({ skip: 0, limit: 50 });
      expect(res.items.length).toBe(1);
      expect(res.items[0].title).toContain("Zero-Knowledge");
      expect(apiClient.get).toHaveBeenCalledWith("/gig/requests", {
        params: { skip: 0, limit: 50 },
      });
    });

    it("retrieves a single gig request details by ID", async () => {
      const mockGigs: GigRequestListResponse = {
        items: [
          {
            id: 301,
            requester_organisation_id: 1,
            organisation_name: "Acme Corporation",
            created_by_user_id: 2,
            title: "Build Zero-Knowledge Identity Verification Integration",
            description: "Implement ZK proof client with cryptographic milestone verification.",
            starts_at: "2026-11-01T09:00:00Z",
            ends_at: "2026-11-30T18:00:00Z",
            pricing_type_code_id: 1,
            pricing_type: "FIXED",
            price_amount: 75000,
            currency_code: "INR",
            status_code_id: 1,
            status: "OPEN",
            created_at: "2026-10-20T00:00:00Z",
            updated_at: "2026-10-20T00:00:00Z",
          },
        ],
        total: 1,
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockGigs);

      const gig = await getGigRequestDetails(301);
      expect(gig).not.toBeNull();
      expect(gig?.id).toBe(301);
    });

    it("creates a new gig request with validated pricing and date window", async () => {
      const payload = {
        requester_organisation_id: 1,
        title: "FastAPI Escrow Ledger Performance Profiling",
        description: "Benchmark SQLAlchemy connection pools and async query execution under load.",
        starts_at: "2026-11-05T09:00:00Z",
        ends_at: "2026-11-20T18:00:00Z",
        pricing_type_code_id: 1,
        price_amount: 45000,
        currency_code: "INR",
      };

      const mockCreated: GigRequestResponse = {
        id: 302,
        created_by_user_id: 2,
        organisation_name: "Acme Corporation",
        status_code_id: 1,
        status: "OPEN",
        pricing_type: "FIXED",
        created_at: "2026-10-20T12:00:00Z",
        updated_at: "2026-10-20T12:00:00Z",
        ...payload,
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockCreated);

      const res = await createGigRequest(payload);
      expect(res.id).toBe(302);
      expect(apiClient.post).toHaveBeenCalledWith("/gig/requests", payload);
    });

    it("candidate submits proposal / application to a gig request", async () => {
      const mockAppResponse: GigApplicationResponse = {
        id: 801,
        gig_request_id: 301,
        gig_request_title: "Build Zero-Knowledge Identity Verification Integration",
        gig_worker_profile_id: 10,
        gig_worker_name: "Rahul Verma",
        applied_at: "2026-10-20T14:00:00Z",
        status_code_id: 1,
        status: "APPLIED",
        created_at: "2026-10-20T14:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockAppResponse);

      const res = await applyToGigRequest(301, {
        notes: "I have implemented Circom / SnarkJS circuits in production.",
      });

      expect(res.id).toBe(801);
      expect(res.status).toBe("APPLIED");
      expect(apiClient.post).toHaveBeenCalledWith("/gig/requests/301/apply", {
        notes: "I have implemented Circom / SnarkJS circuits in production.",
      });
    });
  });
});
