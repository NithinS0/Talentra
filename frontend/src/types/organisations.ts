/**
 * Organisation and Account Management types matching backend schemas (backend/app/schemas/organisation.py).
 */

export interface OrganisationResponse {
  id: number;
  legal_name: string;
  display_name: string;
  organisation_type_code_id: number;
  status_code_id: number;
  status_code: string; // ACTIVE, INACTIVE, DEACTIVATED
  parent_organisation_id?: number | null;
  primary_country_id?: number | null;
  primary_country_name?: string | null;
  created_at: string;
  updated_at?: string | null;
  // Aliases for compatibility
  country_id?: number;
  country_name?: string;
}

export interface OrganisationListResponse {
  items: OrganisationResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface OrganisationCreateRequest {
  legal_name: string;
  display_name: string;
  primary_country_id: number;
  organisation_type_code_id?: number;
  initial_identifier?: string;
  identifier_type_code_id?: number;
}

export interface RecruiterMappingResponse {
  id: number;
  organisation_id: number;
  recruiter_user_id: number;
  recruiter_actor_id?: string | null;
  recruiter_name?: string | null;
  valid_from: string;
  valid_until?: string | null;
  assigned_by_user_id: number;
  // Aliases
  is_active?: boolean;
  assigned_at?: string;
}
