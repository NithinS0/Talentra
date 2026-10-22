import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "@/lib/api/client";
import {
  getMyProfileCompleteness,
  addEducation,
  uploadEducationDocument,
  addOrUpdateSemester,
  uploadSemesterGradeSheet,
  uploadResume,
  setDefaultResume,
  deleteResume,
  uploadDocument,
  deleteDocument,
  addSkill,
  addProject,
} from "@/lib/api/candidates";
import { getJobEligibility, createJob } from "@/lib/api/jobs";
import {
  ProfileCompleteness,
  EducationRecord,
  SemesterRecord,
  CandidateResumeItem,
  CandidateDocumentItem,
} from "@/types/candidate";
import { JobEligibilityResponse, JobResponse, JobCreateRequest } from "@/types/jobs";

describe("Candidate Academics, Document Vault & Structured Job Eligibility APIs", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("Dynamic Completeness (/api/v1/candidates/me/completeness)", () => {
    it("retrieves completeness score and checklist items", async () => {
      const mockCompleteness: ProfileCompleteness = {
        overall_score: 85,
        is_placement_eligible: true,
        checklist_items: [
          {
            key: "class_10",
            section: "academics",
            title: "Class 10 / Secondary School",
            is_complete: true,
            weight: 15,
            deep_link: "/candidates/me#academics",
          },
          {
            key: "resume",
            section: "resumes",
            title: "Default Resume Uploaded",
            is_complete: true,
            weight: 20,
            deep_link: "/candidates/me#resumes",
          },
        ],
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockCompleteness);

      const result = await getMyProfileCompleteness();
      expect(result.overall_score).toBe(85);
      expect(result.is_placement_eligible).toBe(true);
      expect(result.checklist_items).toHaveLength(2);
      expect(apiClient.get).toHaveBeenCalledWith("/candidates/me/completeness");
    });
  });

  describe("Academic Records & Marksheets (/api/v1/candidates/me/education)", () => {
    it("adds an academic qualification record", async () => {
      const mockEducation: Partial<EducationRecord> = {
        id: 10,
        education_level: "UNDERGRADUATE",
        institution_name: "National Institute of Technology",
        cgpa: 8.85,
        status: "COMPLETED",
        has_backlogs: false,
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockEducation);

      const payload = {
        education_level: "UNDERGRADUATE" as const,
        institution_name: "National Institute of Technology",
        cgpa: 8.85,
      };

      const result = await addEducation(payload);
      expect(result.institution_name).toBe("National Institute of Technology");
      expect(apiClient.post).toHaveBeenCalledWith("/candidates/me/education", payload);
    });

    it("uploads education marksheet via multipart form data", async () => {
      const mockUpdated: Partial<EducationRecord> = {
        id: 10,
        document_name: "class10_marksheet.pdf",
        document_storage_key: "vault/candidate_1/class10.pdf",
      };

      vi.spyOn(apiClient, "postFormData").mockResolvedValueOnce(mockUpdated);

      const fakeFile = new File(["dummy content"], "class10_marksheet.pdf", {
        type: "application/pdf",
      });

      const result = await uploadEducationDocument(10, fakeFile);
      expect(result.document_name).toBe("class10_marksheet.pdf");
      expect(apiClient.postFormData).toHaveBeenCalled();
    });
  });

  describe("Semester Grade Sheets (/api/v1/candidates/me/education/:id/semesters)", () => {
    it("creates or updates a semester record with SGPA and backlogs info", async () => {
      const mockSemester: Partial<SemesterRecord> = {
        id: 5,
        semester_number: 6,
        sgpa: 9.1,
        cgpa: 8.95,
        result_status: "PASS",
        has_backlog: false,
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockSemester);

      const payload = {
        semester_number: 6,
        sgpa: 9.1,
        cgpa: 8.95,
        result_status: "PASS" as const,
        has_backlog: false,
      };

      const result = await addOrUpdateSemester(10, payload);
      expect(result.semester_number).toBe(6);
      expect(result.sgpa).toBe(9.1);
      expect(apiClient.post).toHaveBeenCalledWith(
        "/candidates/me/education/10/semesters",
        payload
      );
    });

    it("uploads semester gradesheet document", async () => {
      const mockResult: Partial<SemesterRecord> = {
        id: 5,
        semester_number: 6,
        grade_sheet_name: "sem6_gradesheet.pdf",
      };

      vi.spyOn(apiClient, "postFormData").mockResolvedValueOnce(mockResult);

      const fakeFile = new File(["content"], "sem6_gradesheet.pdf", {
        type: "application/pdf",
      });

      const result = await uploadSemesterGradeSheet(10, 6, fakeFile);
      expect(result.grade_sheet_name).toBe("sem6_gradesheet.pdf");
      expect(apiClient.postFormData).toHaveBeenCalled();
    });
  });

  describe("Resume Manager & Versioning (/api/v1/candidates/me/resumes)", () => {
    it("uploads resume version with default flag", async () => {
      const mockResume: Partial<CandidateResumeItem> = {
        id: 2,
        resume_title: "Campus Placement Resume",
        is_default: true,
        versions: [
          {
            id: 1,
            candidate_resume_id: 2,
            version_number: 1,
            storage_object_key: "resumes/resume_v1.pdf",
            file_name: "resume_v1.pdf",
            mime_type: "application/pdf",
            is_archived: false,
            created_at: "2026-03-01T10:00:00Z",
          },
        ],
      };

      vi.spyOn(apiClient, "postFormData").mockResolvedValueOnce(mockResume);

      const fakeFile = new File(["dummy pdf content"], "resume_v1.pdf", {
        type: "application/pdf",
      });

      const result = await uploadResume(fakeFile, "Campus Placement Resume", "SDE", true);
      expect(result.resume_title).toBe("Campus Placement Resume");
      expect(result.is_default).toBe(true);
      expect(apiClient.postFormData).toHaveBeenCalled();
    });

    it("sets default resume", async () => {
      vi.spyOn(apiClient, "put").mockResolvedValueOnce({
        id: 2,
        is_default: true,
      });

      const res = await setDefaultResume(2);
      expect(res.is_default).toBe(true);
      expect(apiClient.put).toHaveBeenCalledWith("/candidates/me/resumes/2/default", {});
    });

    it("deletes a resume", async () => {
      vi.spyOn(apiClient, "delete").mockResolvedValueOnce(undefined);

      await deleteResume(2);
      expect(apiClient.delete).toHaveBeenCalledWith("/candidates/me/resumes/2");
    });
  });

  describe("Document Vault (/api/v1/candidates/me/documents)", () => {
    it("uploads a document to the vault with SHA-256 hash", async () => {
      const mockDoc: Partial<CandidateDocumentItem> = {
        id: 101,
        title: "Official College Transcript",
        document_category: "TRANSCRIPT",
        file_name: "transcript.pdf",
        content_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        is_verified: false,
      };

      vi.spyOn(apiClient, "postFormData").mockResolvedValueOnce(mockDoc);

      const fakeFile = new File(["transcript data"], "transcript.pdf", {
        type: "application/pdf",
      });

      const result = await uploadDocument(fakeFile, "TRANSCRIPT", "Official College Transcript");
      expect(result.content_sha256).toBeDefined();
      expect(result.document_category).toBe("TRANSCRIPT");
      expect(apiClient.postFormData).toHaveBeenCalled();
    });

    it("deletes a document from the vault", async () => {
      vi.spyOn(apiClient, "delete").mockResolvedValueOnce(undefined);

      await deleteDocument(101);
      expect(apiClient.delete).toHaveBeenCalledWith("/candidates/me/documents/101");
    });
  });

  describe("Structured Criteria & Candidate Eligibility Evaluation", () => {
    it("retrieves candidate eligibility evaluation for a job with criterion breakdown", async () => {
      const mockEligibility: JobEligibilityResponse = {
        job_id: 1,
        candidate_id: 42,
        overall_status: "ELIGIBLE",
        can_apply: true,
        criteria: [
          {
            criterion: "qualification",
            required_value: "B.Tech, B.E., MCA",
            candidate_value: "UNDERGRADUATE (B.Tech)",
            status: "SATISFIED",
            explanation: "Candidate qualification meets accepted degrees.",
          },
          {
            criterion: "minimum_cgpa",
            required_value: ">= 7.50",
            candidate_value: "8.85",
            status: "SATISFIED",
            explanation: "Candidate aggregate CGPA meets or exceeds the required cutoff.",
          },
          {
            criterion: "backlogs",
            required_value: "Zero active backlogs allowed",
            candidate_value: "0 active backlogs",
            status: "SATISFIED",
            explanation: "Candidate has 0 active backlogs, satisfying policy.",
          },
        ],
        missing_requirements: [],
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockEligibility);

      const result = await getJobEligibility(1);
      expect(result.overall_status).toBe("ELIGIBLE");
      expect(result.can_apply).toBe(true);
      expect(result.criteria).toHaveLength(3);
      expect(result.criteria[0].status).toBe("SATISFIED");
      expect(apiClient.get).toHaveBeenCalledWith("/jobs/1/eligibility", { params: undefined });
    });

    it("creates job with structured criteria", async () => {
      const mockCreatedJob: Partial<JobResponse> = {
        id: 99,
        job_title: "Campus Systems Engineer",
        required_qualifications: "B.Tech, B.E.",
        accepted_branches: "CSE, IT",
        min_cgpa: 7.5,
        allow_backlogs: false,
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockCreatedJob);

      const payload: JobCreateRequest = {
        organisation_id: 1,
        job_role_id: 1,
        employment_type_id: 1,
        work_type_id: 1,
        title: "Campus Systems Engineer",
        description: "High-scale engineering role.",
        required_qualifications: "B.Tech, B.E.",
        accepted_branches: "CSE, IT",
        min_cgpa: 7.5,
        allow_backlogs: false,
      };

      const result = await createJob(payload);
      expect(result.id).toBe(99);
      expect(result.required_qualifications).toBe("B.Tech, B.E.");
      expect(apiClient.post).toHaveBeenCalledWith("/jobs", payload);
    });
  });
});
