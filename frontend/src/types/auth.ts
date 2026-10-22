/**
 * Canonical Talentra Roles matching LookupRole and user_role_assignment.
 */
export type RoleCode =
  | "SUPER_ADMIN"
  | "ADMIN"
  | "ACCOUNT_ADMIN"
  | "GUEST"
  | "CANDIDATE"
  | "EMPLOYER"
  | "RECRUITER"
  | "CONSULTANT"
  | "PLACEMENT_OFFICER";

/**
 * Public Actor ID Prefixes (two uppercase letters).
 */
export type ActorPrefix =
  | "SA" // Super Admin
  | "AD" // Admin
  | "AA" // Account Admin
  | "GU" // Guest
  | "CA" // Candidate
  | "EM" // Employer
  | "RE" // Recruiter
  | "CO" // Consultant
  | "PO"; // Placement Officer

/**
 * Actor Identity item matching backend UserActorIdentity model.
 */
export interface ActorIdentityItem {
  role_code: RoleCode | string;
  actor_prefix: ActorPrefix | string;
  actor_id: string; // Format: PPNNNNN (e.g. CA00001)
  organisation_id?: number | null;
  is_active: boolean;
}

/**
 * Authenticated User Profile matching FastAPI UserProfileResponse.
 */
export interface UserProfile {
  user_id: number;
  display_name: string;
  email_address: string;
  phone_e164?: string | null;
  provider_subject?: string | null;
  roles: string[];
  actor_identities: ActorIdentityItem[];
  created_at: string;
}

/**
 * Auth Token credentials stored in session.
 */
export interface AuthSession {
  accessToken: string;
  refreshToken?: string;
  user: UserProfile;
  activeRole: RoleCode;
  activeActorId: string;
}

/**
 * Sign-in request payload.
 */
export interface SignInRequest {
  email: string;
  password?: string;
  role_code?: RoleCode;
}

/**
 * Candidate self-registration request payload matching FastAPI CandidateRegisterRequest.
 */
export interface CandidateRegisterRequest {
  first_name: string;
  middle_name?: string | null;
  last_name: string;
  country_code: string; // ISO 3166-1 alpha-2 e.g. "IN", "US"
  phone_number?: string | null;
  headline?: string | null;
  summary?: string | null;
}

/**
 * Candidate profile response matching FastAPI CandidateProfileResponse.
 */
export interface CandidateProfileResponse {
  user_id: number;
  actor_id: string; // Format: CAxxxxx
  first_name: string;
  middle_name?: string | null;
  last_name: string;
  display_name: string;
  headline?: string | null;
  summary?: string | null;
  email_address?: string | null;
  phone_e164?: string | null;
  country_code?: string | null;
  country_name?: string | null;
  completion_score: number;
  created_at: string;
}

