/**
 * Job Requirement and Discovery types matching backend schemas (backend/app/schemas/job.py).
 */

export interface CriterionResult {
  criterion: string;
  required_value: string;
  candidate_value?: string | null;
  status: "SATISFIED" | "UNSATISFIED" | "UNABLE_TO_DETERMINE";
  explanation: string;
}

export interface JobEligibilityResponse {
  job_id: number;
  candidate_id: number;
  overall_status: "ELIGIBLE" | "NOT_ELIGIBLE" | "UNABLE_TO_DETERMINE";
  can_apply: boolean;
  criteria: CriterionResult[];
  missing_requirements: string[];
}

export interface JobResponse {
  id: number;
  organisation_id: number;
  organisation_name: string;
  job_role_id?: number;
  job_role_name?: string;
  title?: string;
  description?: string;
  // Aliases for compatibility
  job_title?: string;
  job_description?: string;
  status_code_id?: number;
  status_code?: string;
  status?: string;
  publish_status_code_id?: number;
  publish_status_code?: string;
  publish_state?: string;
  work_type_name?: string;
  employment_type_name?: string;
  work_type?: string;
  employment_type?: string;
  country_name?: string;
  open_to_consultants?: boolean;
  positions_count?: number;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency_code?: string | null;
  application_deadline?: string | null;
  applications_count?: number;

  // Structured requirements & eligibility criteria
  responsibilities?: string | null;
  required_skills?: string | null;
  preferred_skills?: string | null;
  required_qualifications?: string | null;
  accepted_branches?: string | null;
  min_percentage?: number | null;
  min_cgpa?: number | null;
  allow_backlogs?: boolean;
  max_active_backlogs?: number;
  min_experience_years?: number | null;
  max_experience_years?: number | null;
  location_city?: string | null;
  location_country?: string | null;
  required_documents?: string | null;

  created_at: string;
  updated_at?: string | null;
}

export interface JobListResponse {
  items: JobResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages?: number;
  pages?: number;
}

export interface JobCreateRequest {
  organisation_id: number;
  job_role_id: number;
  title: string;
  description: string;
  employment_type_id: number;
  work_type_id: number;
  positions_count?: number;
  salary_min?: number;
  salary_max?: number;
  salary_currency_code?: string;
  application_deadline?: string;
  open_to_consultants?: boolean;
  publish_now?: boolean;

  // Structured requirements
  responsibilities?: string;
  required_skills?: string;
  preferred_skills?: string;
  required_qualifications?: string;
  accepted_branches?: string;
  min_percentage?: number;
  min_cgpa?: number;
  allow_backlogs?: boolean;
  max_active_backlogs?: number;
  min_experience_years?: number;
  max_experience_years?: number;
  location_city?: string;
  location_country?: string;
  required_documents?: string;

  // Aliases for compatibility
  job_title?: string;
  job_description?: string;
  country_id?: number;
}

export interface JobUpdateRequest {
  title?: string;
  description?: string;
  employment_type_id?: number;
  work_type_id?: number;
  positions_count?: number;
  salary_min?: number;
  salary_max?: number;
  salary_currency_code?: string;
  application_deadline?: string;
  open_to_consultants?: boolean;

  // Structured requirements
  responsibilities?: string;
  required_skills?: string;
  preferred_skills?: string;
  required_qualifications?: string;
  accepted_branches?: string;
  min_percentage?: number;
  min_cgpa?: number;
  allow_backlogs?: boolean;
  max_active_backlogs?: number;
  min_experience_years?: number;
  max_experience_years?: number;
  location_city?: string;
  location_country?: string;
  required_documents?: string;
}

export interface JobStatusUpdateRequest {
  status?: string;
  publish_state?: string;
  status_code?: string;
  publish_status_code?: string;
}
