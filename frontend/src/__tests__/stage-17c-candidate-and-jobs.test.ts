import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "@/lib/api/client";
import { getMyCandidateProfile } from "@/lib/api/candidates";
import {
  listJobs,
  getJobDetails,
  createJob,
  updateJob,
  updateJobStatus,
  getJobApplications,
} from "@/lib/api/jobs";
import { JobResponse, JobListResponse } from "@/types/jobs";
import { CandidateProfileResponse } from "@/types/auth";

describe("Stage 17C: Candidate Profile & Jobs Workflow APIs", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("Candidate Profiles (/api/v1/candidates/me)", () => {
    it("successfully retrieves current candidate profile for authenticated CANDIDATE", async () => {
      const mockProfile: CandidateProfileResponse = {
        user_id: 42,
        actor_id: "CA00042",
        first_name: "Rahul",
        middle_name: "Dev",
        last_name: "Verma",
        display_name: "Rahul Verma",
        headline: "Principal Distributed Systems Engineer",
        summary: "Specialist in high-throughput transaction ledger systems.",
        email_address: "rahul.verma@example.com",
        phone_e164: "+919876543210",
        country_code: "IN",
        country_name: "India",
        completion_score: 95.0,
        created_at: "2026-03-01T10:00:00Z",
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockProfile);

      const result = await getMyCandidateProfile();
      expect(result).toEqual(mockProfile);
      expect(apiClient.get).toHaveBeenCalledWith("/candidates/me");
      expect(result.actor_id).toBe("CA00042");
      expect(result.completion_score).toBe(95.0);
    });

    it("handles 403 Forbidden when caller lacks CANDIDATE role", async () => {
      vi.spyOn(apiClient, "get").mockRejectedValueOnce({
        status: 403,
        message: "Forbidden: role 'CANDIDATE' required",
      });

      await expect(getMyCandidateProfile()).rejects.toMatchObject({
        status: 403,
      });
    });

    it("handles 404 when profile record does not yet exist", async () => {
      vi.spyOn(apiClient, "get").mockRejectedValueOnce({
        status: 404,
        message: "Candidate profile record not found.",
      });

      await expect(getMyCandidateProfile()).rejects.toMatchObject({
        status: 404,
      });
    });
  });

  describe("Job Discovery & Management (/api/v1/jobs)", () => {
    it("lists jobs with search query, filters, and pagination parameters", async () => {
      const mockJobs: JobListResponse = {
        items: [
          {
            id: 101,
            organisation_id: 1,
            organisation_name: "Acme Corporation",
            job_title: "Staff Next.js Platform Architect",
            job_description: "Architect high-reliability enterprise frontend applications.",
            status: "OPEN",
            status_code: "OPEN",
            publish_state: "PUBLISHED",
            publish_status_code: "PUBLISHED",
            work_type_name: "Remote",
            employment_type_name: "Full Time",
            country_name: "India",
            created_at: "2026-10-15T09:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockJobs);

      const res = await listJobs({ search: "Next.js", page: 1, page_size: 20 });
      expect(res.total).toBe(1);
      expect(res.items[0].job_title).toBe("Staff Next.js Platform Architect");
      expect(apiClient.get).toHaveBeenCalledWith("/jobs", {
        params: { search: "Next.js", page: 1, page_size: 20 },
      });
    });

    it("retrieves single job details by ID", async () => {
      const mockJob: JobResponse = {
        id: 101,
        organisation_id: 1,
        organisation_name: "Acme Corporation",
        job_title: "Staff Next.js Platform Architect",
        job_description: "Architect high-reliability enterprise frontend applications.",
        status: "OPEN",
        status_code: "OPEN",
        publish_state: "PUBLISHED",
        publish_status_code: "PUBLISHED",
        created_at: "2026-10-15T09:00:00Z",
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockJob);

      const res = await getJobDetails(101);
      expect(res.id).toBe(101);
      expect(apiClient.get).toHaveBeenCalledWith("/jobs/101");
    });

    it("creates job requirement with valid employer authorization", async () => {
      const newJobPayload = {
        organisation_id: 1,
        job_role_id: 1,
        title: "Senior Escrow Smart Contract Auditor",
        description: "Audit high-value transaction escrows and release condition gates.",
        employment_type_id: 1,
        work_type_id: 2,
        publish_now: true,
      };

      const mockCreated: JobResponse = {
        id: 202,
        organisation_id: 1,
        organisation_name: "Acme Corporation",
        job_title: newJobPayload.title,
        job_description: newJobPayload.description,
        status: "OPEN",
        status_code: "OPEN",
        publish_state: "PUBLISHED",
        publish_status_code: "PUBLISHED",
        created_at: "2026-10-20T12:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockCreated);

      const res = await createJob(newJobPayload);
      expect(res.id).toBe(202);
      expect(res.status).toBe("OPEN");
      expect(apiClient.post).toHaveBeenCalledWith("/jobs", newJobPayload);
    });

    it("updates job status from OPEN to CLOSED", async () => {
      const mockUpdated: JobResponse = {
        id: 101,
        organisation_id: 1,
        organisation_name: "Acme Corporation",
        job_title: "Staff Next.js Platform Architect",
        job_description: "Architect high-reliability enterprise frontend applications.",
        status: "CLOSED",
        status_code: "CLOSED",
        publish_state: "PUBLISHED",
        publish_status_code: "PUBLISHED",
        created_at: "2026-10-15T09:00:00Z",
      };

      vi.spyOn(apiClient, "patch").mockResolvedValueOnce(mockUpdated);

      const res = await updateJobStatus(101, { status: "CLOSED" });
      expect(res.status).toBe("CLOSED");
      expect(apiClient.patch).toHaveBeenCalledWith("/jobs/101/status", { status: "CLOSED" });
    });

    it("retrieves candidate applications submitted for a job", async () => {
      const mockApps = {
        items: [
          {
            id: 501,
            job_requirement_id: 101,
            job_title: "Staff Next.js Platform Architect",
            organisation_id: 1,
            organisation_name: "Acme Corporation",
            candidate_profile_id: 42,
            candidate_actor_id: "CA00042",
            candidate_name: "Rahul Verma",
            status: "APPLIED",
            status_code: "APPLIED",
            applied_at: "2026-10-18T14:30:00Z",
            last_status_changed_at: "2026-10-18T14:30:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockApps);

      const res = await getJobApplications(101);
      expect(res.items.length).toBe(1);
      expect(res.items[0].candidate_name).toBe("Rahul Verma");
      expect(apiClient.get).toHaveBeenCalledWith("/jobs/101/applications", { params: undefined });
    });
  });
});
