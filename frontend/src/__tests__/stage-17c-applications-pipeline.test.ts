import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "@/lib/api/client";
import {
  applyToJob,
  getMyApplications,
  getApplicationDetails,
  updateApplicationStatus,
} from "@/lib/api/applications";
import { ApplicationResponse, ApplicationListResponse } from "@/types/applications";

describe("Stage 17C: Applications & Pipeline Workflow APIs", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("Application Submission (POST /jobs/{id}/apply)", () => {
    it("submits application successfully for candidate", async () => {
      const mockSubmitted: ApplicationResponse = {
        id: 777,
        job_requirement_id: 101,
        job_title: "Staff Next.js Platform Architect",
        organisation_id: 1,
        organisation_name: "Acme Corporation",
        candidate_profile_id: 42,
        candidate_actor_id: "CA00042",
        candidate_name: "Rahul Verma",
        status: "APPLIED",
        cover_letter: "I have 8+ years building enterprise Next.js applications.",
        applied_at: "2026-10-20T15:00:00Z",
        last_status_changed_at: "2026-10-20T15:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockSubmitted);

      const res = await applyToJob(101, {
        cover_letter: "I have 8+ years building enterprise Next.js applications.",
      });

      expect(res.id).toBe(777);
      expect(res.status).toBe("APPLIED");
      expect(apiClient.post).toHaveBeenCalledWith("/jobs/101/apply", {
        cover_letter: "I have 8+ years building enterprise Next.js applications.",
      });
    });

    it("handles 409 Conflict when candidate has already applied to this job", async () => {
      vi.spyOn(apiClient, "post").mockRejectedValueOnce({
        status: 409,
        message: "You have already submitted an active application for this job requirement.",
      });

      await expect(
        applyToJob(101, { cover_letter: "Duplicate apply" })
      ).rejects.toMatchObject({
        status: 409,
      });
    });

    it("handles 422 Unprocessable Entity when job is CLOSED", async () => {
      vi.spyOn(apiClient, "post").mockRejectedValueOnce({
        status: 422,
        message: "Job requirement is not currently open for new candidate applications.",
      });

      await expect(
        applyToJob(101, { cover_letter: "Applying to closed job" })
      ).rejects.toMatchObject({
        status: 422,
      });
    });

    it("handles 403 Forbidden when candidate is blocked from job organisation", async () => {
      vi.spyOn(apiClient, "post").mockRejectedValueOnce({
        status: 403,
        message: "Candidate is blocked from submitting applications to this organisation.",
      });

      await expect(
        applyToJob(101, { cover_letter: "Blocked candidate apply" })
      ).rejects.toMatchObject({
        status: 403,
      });
    });
  });

  describe("Candidate Applications Retrieval (GET /applications/me)", () => {
    it("retrieves paginated list of candidate applications", async () => {
      const mockList: ApplicationListResponse = {
        items: [
          {
            id: 777,
            job_requirement_id: 101,
            job_title: "Staff Next.js Platform Architect",
            organisation_id: 1,
            organisation_name: "Acme Corporation",
            candidate_profile_id: 42,
            candidate_actor_id: "CA00042",
            candidate_name: "Rahul Verma",
            status: "SCREENING",
            applied_at: "2026-10-20T15:00:00Z",
            last_status_changed_at: "2026-10-20T16:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockList);

      const res = await getMyApplications({ page: 1, page_size: 20 });
      expect(res.items.length).toBe(1);
      expect(res.items[0].status).toBe("SCREENING");
      expect(apiClient.get).toHaveBeenCalledWith("/applications/me", {
        params: { page: 1, page_size: 20 },
      });
    });
  });

  describe("Application Status Pipeline (PATCH /applications/{id}/status)", () => {
    it("transitions application from SCREENING to INTERVIEW", async () => {
      const mockTransitioned: ApplicationResponse = {
        id: 777,
        job_requirement_id: 101,
        job_title: "Staff Next.js Platform Architect",
        organisation_id: 1,
        organisation_name: "Acme Corporation",
        candidate_profile_id: 42,
        candidate_actor_id: "CA00042",
        candidate_name: "Rahul Verma",
        status: "INTERVIEW",
        applied_at: "2026-10-20T15:00:00Z",
        last_status_changed_at: "2026-10-20T17:00:00Z",
      };

      vi.spyOn(apiClient, "patch").mockResolvedValueOnce(mockTransitioned);

      const res = await updateApplicationStatus(777, {
        status: "INTERVIEW",
        notes: "Candidate passed screening filter; proceeding to tech loop.",
      });

      expect(res.status).toBe("INTERVIEW");
      expect(apiClient.patch).toHaveBeenCalledWith("/applications/777/status", {
        status: "INTERVIEW",
        notes: "Candidate passed screening filter; proceeding to tech loop.",
      });
    });

    it("retrieves single application details by ID", async () => {
      const mockDetail: ApplicationResponse = {
        id: 777,
        job_requirement_id: 101,
        job_title: "Staff Next.js Platform Architect",
        organisation_id: 1,
        organisation_name: "Acme Corporation",
        candidate_profile_id: 42,
        candidate_actor_id: "CA00042",
        candidate_name: "Rahul Verma",
        status: "OFFERED",
        applied_at: "2026-10-20T15:00:00Z",
        last_status_changed_at: "2026-10-20T18:00:00Z",
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockDetail);

      const res = await getApplicationDetails(777);
      expect(res.id).toBe(777);
      expect(res.status).toBe("OFFERED");
      expect(apiClient.get).toHaveBeenCalledWith("/applications/777");
    });
  });
});
