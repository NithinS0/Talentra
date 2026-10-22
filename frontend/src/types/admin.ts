export interface AdminUserRoleGrantRequest {
  user_id: number;
  role_code: string;
  organisation_id?: number | null;
  valid_from?: string | null;
  valid_until?: string | null;
}

export interface AdminUserRoleRevokeRequest {
  user_id: number;
  role_code: string;
  organisation_id?: number | null;
  reason?: string | null;
}

export interface AdminUserStatusUpdateRequest {
  account_status_code_id: number; // 1=ACTIVE, 2=SUSPENDED, 3=DEACTIVATED/LOCKED
  reason: string;
}

export interface AdminUserResponse {
  id: number;
  email_address?: string | null;
  display_name: string;
  account_status_code_id: number;
  account_status: string;
  roles: string[];
  actor_ids: string[];
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface AdminUserListResponse {
  items: AdminUserResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AuditEventResponse {
  id: number;
  actor_user_id?: number | null;
  action_code: string;
  resource_type: string;
  resource_id?: string | null;
  occurred_at: string;
  request_id?: string | null;
  metadata_redacted?: Record<string, unknown> | null;
}

export interface AuditEventListResponse {
  items: AuditEventResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SessionRevokeRequest {
  session_id: number;
  reason?: string | null;
}

export interface AdminSessionResponse {
  id: number;
  user_id: number;
  started_at: string;
  last_activity_at: string;
  expires_at: string;
  is_revoked: boolean;
}

export interface ConsentWithdrawRequest {
  consent_type_code_id: number;
  reason?: string | null;
}

export interface ConsentRecordResponse {
  id: number;
  user_id: number;
  consent_type_code_id: number;
  policy_version: string;
  granted: boolean;
  captured_at: string;
  withdrawn_at?: string | null;
}

export interface AccessReviewReportResponse {
  generated_at: string;
  reviewer_user_id: number;
  privileged_users_count: number;
  privileged_users: Array<{
    user_id: number;
    email_address: string;
    display_name: string;
    roles: string[];
  }>;
  audit_correlation_id: string;
}

export interface DataClassificationItem {
  table_name: string;
  column_name: string;
  classification: string; // PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED_PII
  data_type: string;
}

export interface DataClassificationResponse {
  total_classified: number;
  unclassified_count: number;
  items: DataClassificationItem[];
}
