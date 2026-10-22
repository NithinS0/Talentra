export interface VerificationConsentRequest {
  user_id: number;
  consent_type_code_id?: number;
  policy_version?: string;
  permitted_purpose: string;
  granted?: boolean;
}

export interface VerificationConsentResponse {
  consent_record_id: number;
  user_id: number;
  purpose: string;
  granted: boolean;
  captured_at: string;
}

export interface VerificationInitiateRequest {
  user_id: number;
  document_type: 'AADHAAR' | 'PAN' | 'PASSPORT' | 'VOTER_ID' | string;
  file_name: string;
  file_mime_type: string;
  file_content_base64?: string | null;
  consent_record_id: number;
  purpose?: string;
  raw_identifier_for_masking_only?: string | null;
}

export interface VerificationCaseResponse {
  case_id: number;
  user_id: number;
  document_type: string;
  provider_code: string;
  provider_case_reference?: string | null;
  status: string;
  requested_at: string;
  completed_at?: string | null;
  masked_identifier?: string | null;
  identifier_fingerprint?: string | null;
  name_match_score?: number | null;
  name_match_status?: string | null;
  malware_scan_status: string;
  consent_record_id: number;
  purpose: string;
}

export interface VerificationReviewRequest {
  decision: 'VERIFIED' | 'REJECTED' | 'ESCALATED_FOR_DUAL_CONTROL' | string;
  reason: string;
  reviewer_user_id: number;
  second_approver_user_id?: number | null;
  is_high_risk_override?: boolean;
}

export interface DocumentAccessUrlResponse {
  case_id: number;
  presigned_url: string;
  expires_at: string;
  access_token: string;
}

export interface IntegrationBoundaryEntry {
  provider_code: string;
  display_name: string;
  purpose: string;
  source_of_truth: string;
  stored_vs_reference_data: string;
  timeout_seconds: number;
  retry_policy: string;
  idempotency_policy: string;
  audit_behavior: string;
  status: string;
}

export interface RetentionJobRunRequest {
  dry_run?: boolean;
  target_data_class: 'KYC_DOCUMENTS' | 'INACTIVE_SESSIONS' | 'PROCESSED_WEBHOOKS' | string;
  retention_days?: number;
}

export interface RetentionJobSummaryResponse {
  job_id: number;
  data_class: string;
  dry_run: boolean;
  evaluated_records: number;
  eligible_for_purge: number;
  purged_records: number;
  skipped_due_to_legal_hold: number;
  executed_at: string;
  status: string;
}

export interface FeatureFlagEvaluationRequest {
  flag_code: string;
  subject_key: string;
  tenant_id?: string | null;
  environment?: string;
}

export interface FeatureFlagResponse {
  flag_code: string;
  enabled: boolean;
  subject_key: string;
  rollout_percentage: number;
  evaluation_reason: string;
}
