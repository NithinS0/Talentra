export interface FunnelStageCount {
  stage_name: string;
  status_code_id: number;
  count: number;
  conversion_rate_percent: number;
}

export interface FunnelAggregationResponse {
  organisation_id?: number | null;
  job_requirement_id?: number | null;
  as_of_date: string;
  total_applications: number;
  total_hired: number;
  overall_conversion_rate_percent: number;
  stages: FunnelStageCount[];
}

export interface DailyRefreshRequest {
  organisation_id?: number | null;
  refresh_date?: string | null;
}

export interface DailyRefreshResponse {
  status: string;
  refresh_date: string;
  records_processed: number;
  source_watermark: string;
  run_id: number;
}

export interface WatermarkResponse {
  last_watermark?: string | null;
  last_successful_run_at?: string | null;
  status_code_id: number;
  status_name: string;
  refresh_lag_seconds: number;
}

export interface DataFreshnessResponse {
  watermark_timestamp_utc?: string | null;
  current_timestamp_utc: string;
  lag_seconds: number;
  is_fresh: boolean;
}

export interface KpiDefinitionResponse {
  id: number;
  code?: string | null;
  name?: string | null;
  status_code_id: number;
  description?: string | null;
}

export interface DataQualityIssueResponse {
  id: number;
  code?: string | null;
  name?: string | null;
  status_code_id: number;
  description?: string | null;
  created_at: string;
}

export interface SuperAdminDashboardResponse {
  total_organisations: number;
  total_jobs: number;
  total_applications: number;
  total_gig_assignments: number;
  active_subscriptions_count: number;
  watermark?: string | null;
  refresh_lag_seconds: number;
}

export interface EmployerDashboardResponse {
  organisation_id: number;
  organisation_name: string;
  open_jobs_count: number;
  total_applications_received: number;
  interviews_scheduled: number;
  offers_extended: number;
  hires_count: number;
  funnel: FunnelAggregationResponse;
}

export interface RecruiterDashboardResponse {
  recruiter_user_id: number;
  organisation_id: number;
  assigned_jobs_count: number;
  total_candidates_in_pipeline: number;
  interviews_conducted: number;
  hires_this_month: number;
}

export interface CandidateDashboardResponse {
  candidate_user_id: number;
  applications_submitted: number;
  under_review_count: number;
  interviews_scheduled: number;
  offers_received: number;
  profile_views_count: number;
}

export interface TpoDashboardResponse {
  registered_students_count: number;
  total_applications_sent: number;
  offers_received: number;
  placement_rate_percent: number;
}

export interface CandidatePiiMinimized {
  candidate_id: number;
  masked_name: string;
  masked_email: string;
  current_status: string;
  applications_count: number;
}
