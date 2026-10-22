/**
 * Gig Marketplace types matching backend schemas (backend/app/schemas/gig.py).
 */

export interface GigRequestResponse {
  id: number;
  requester_organisation_id: number;
  organisation_name?: string | null;
  created_by_user_id: number;
  title: string;
  description: string;
  starts_at: string;
  ends_at: string;
  pricing_type_code_id: number;
  pricing_type: string;
  price_amount: number;
  currency_code: string;
  status_code_id: number;
  status: string; // OPEN, ASSIGNED, COMPLETED, CANCELLED
  created_at: string;
  updated_at: string;
}

export interface GigRequestListResponse {
  items: GigRequestResponse[];
  total: number;
}

export interface GigRequestCreate {
  requester_organisation_id: number;
  title: string;
  description: string;
  starts_at: string;
  ends_at: string;
  pricing_type_code_id: number; // 1: FIXED, 2: HOURLY / RATE_BASED
  price_amount: number;
  currency_code: string;
}

export interface GigApplicationCreate {
  notes?: string;
}

export interface GigApplicationResponse {
  id: number;
  gig_request_id: number;
  gig_request_title?: string | null;
  gig_worker_profile_id: number;
  gig_worker_name?: string | null;
  applied_at: string;
  status_code_id: number;
  status: string; // APPLIED, ACCEPTED, REJECTED
  decided_by_user_id?: number | null;
  decided_at?: string | null;
  created_at: string;
}
