export type LicenceStatusCode = 1 | 2 | 3 | 4; // 1=ACTIVE, 2=SUSPENDED, 3=REVOKED, 4=EXPIRED
export type LicenceStatusName = 'ACTIVE' | 'SUSPENDED' | 'REVOKED' | 'EXPIRED' | 'UNKNOWN';

export interface LicenceResponse {
  id: number;
  licence_code: string;
  account_id: number;
  max_users: number;
  max_devices_per_user: number;
  valid_from: string;
  valid_until: string;
  status_code_id: number;
  status: LicenceStatusName | string;
  allocated_seats: number;
  available_seats: number;
  created_at: string;
  updated_at: string;
}

export interface LicenceCreatePayload {
  licence_code: string;
  account_id: number;
  max_users: number;
  max_devices_per_user: number;
  valid_from: string;
  valid_until: string;
}

export interface LicenceStatusUpdatePayload {
  status_code_id: number;
  reason?: string;
}

export interface SeatAllocationCreatePayload {
  licence_id: number;
  user_id: number;
  expires_at?: string | null;
}

export interface SeatAllocationResponse {
  id: number;
  licence_id: number;
  user_id: number;
  status_code_id: number;
  status: string;
  occurred_at?: string | null;
  expires_at?: string | null;
  created_at: string;
}

export interface DeviceRegisterPayload {
  device_fingerprint_hash: string;
  device_label?: string;
}

export interface DeviceRevocationPayload {
  reason: string;
}

export interface DeviceResponse {
  id: number;
  user_id: number;
  device_fingerprint_hash: string;
  device_label?: string | null;
  first_seen_at: string;
  last_seen_at: string;
  revoked_at?: string | null;
  is_active: boolean;
}

export interface SessionCreatePayload {
  device_id?: number;
  device_fingerprint_hash?: string;
  device_label?: string;
  provider_session_reference?: string;
  duration_seconds?: number;
}

export interface SessionRevocationPayload {
  reason: string;
}

export interface SessionResponse {
  id: number;
  user_id: number;
  device_id?: number | null;
  device_label?: string | null;
  provider_session_reference?: string | null;
  started_at: string;
  last_activity_at: string;
  expires_at: string;
  ended_at?: string | null;
  revoked_at?: string | null;
  is_active: boolean;
}

export interface SessionCleanupResponse {
  cleaned_count: number;
  timestamp: string;
  status: string;
}

export interface LicenceUsageResponse {
  licence_id: number;
  licence_code: string;
  account_id: number;
  max_users: number;
  allocated_seats: number;
  available_seats: number;
  max_devices_per_user: number;
  status: string;
}
