/**
 * Sourcing and Consultant Requests types matching backend schemas (backend/app/schemas/sourcing.py).
 */

export interface SourcingRequestResponse {
  id: number;
  job_requirement_id: number;
  job_title: string;
  organisation_id: number;
  organisation_name: string;
  requester_user_id: number;
  consultant_user_id?: number | null;
  consultant_name?: string | null;
  status_code_id: number;
  status: string; // PENDING, ACCEPTED, DECLINED, CANCELLED, COMPLETED
  open_to_consultants_snapshot?: boolean;
  requested_at: string;
  responded_at?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface SourcingRequestListResponse {
  items: SourcingRequestResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SourcingRequestCreate {
  job_requirement_id: number;
  consultant_user_id?: number | null;
}

export interface CandidateShortlistResponse {
  id: number;
  sourcing_request_id?: number | null;
  candidate_profile_id: number;
  title?: string | null;
  description?: string | null;
}
