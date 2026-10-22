/**
 * Application pipeline types matching backend schemas (backend/app/schemas/application.py).
 */

export interface ApplicationResponse {
  id: number;
  job_requirement_id: number;
  job_title: string;
  organisation_id: number;
  organisation_name: string;
  candidate_profile_id: number;
  candidate_actor_id: string;
  candidate_name: string;
  candidate_headline?: string | null;
  status: string; // APPLIED, SCREENING, INTERVIEW, OFFERED, HIRED, REJECTED, WITHDRAWN
  cover_letter?: string | null;
  applied_at: string;
  last_status_changed_at: string;
  resume_version_id?: number | null;
  resume_snapshot_title?: string | null;
  resume_snapshot_file_name?: string | null;
  eligibility_status?: string | null;
  eligibility_notes?: string | null;
  // Aliases for compatibility
  status_code?: string;
  created_at?: string;
}

export interface ApplicationListResponse {
  items: ApplicationResponse[];
  total: number;
  page: number;
  page_size: number;
  pages?: number;
  total_pages?: number;
}

export interface ApplicationSubmitRequest {
  cover_letter?: string;
  resume_version_id?: number;
  resume_url?: string;
}

export interface ApplicationStatusUpdateRequest {
  status: string; // SCREENING, INTERVIEW, OFFERED, HIRED, REJECTED, WITHDRAWN
  notes?: string;
}
