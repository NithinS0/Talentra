export interface NotificationPreferenceResponse {
  id: number;
  user_id: number;
  notification_type_code_id: number;
  channel_code_id: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationPreferencePayload {
  notification_type_code_id: number;
  channel_code_id: number;
  enabled: boolean;
}

export interface JobAlertPreferencePayload {
  setting_code_id?: number;
  setting_value: Record<string, unknown>;
  enabled?: boolean;
}

export interface JobAlertPreferenceResponse {
  id: number;
  user_id: number;
  setting_code_id: number;
  setting_value?: Record<string, unknown> | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationResponse {
  id: number;
  user_id: number;
  setting_code_id: number;
  setting_value?: Record<string, unknown> | null;
  enabled: boolean;
  is_read: boolean;
  title?: string | null;
  body?: string | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationCreatePayload {
  user_id: number;
  title: string;
  body: string;
  category_id?: number;
  channel_id?: number;
  priority?: string;
  link?: string | null;
  retention_days?: number;
}

export interface CommunityPostCreatePayload {
  title: string;
  body: string;
  language_code?: string;
}

export interface CommunityPostResponse {
  id: number;
  author_user_id: number;
  title: string;
  body: string;
  language_id?: number | null;
  moderation_status_code_id: number;
  created_at: string;
  updated_at: string;
}

export interface CommunityReactionPayload {
  post_id: number;
  reaction_type: string; // 'LIKE', 'HELPFUL', 'INSIGHTFUL'
}

export interface CommunityReactionResponse {
  id: number;
  code?: string | null;
  name?: string | null;
  status_code_id: number;
  created_at: string;
}

export interface SupportTicketCreatePayload {
  subject: string;
  description: string;
  priority_code_id?: number;
}

export interface SupportTicketResponse {
  id: number;
  requester_user_id: number;
  ticket_number: string;
  subject: string;
  description: string;
  priority_code_id: number;
  status_code_id: number;
  assigned_to_user_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface FaqResponse {
  id: number;
  code?: string | null;
  name?: string | null;
  status_code_id: number;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReferralEventPayload {
  referrer_user_id: number;
  referee_user_id: number;
  referral_code: string;
  event_type?: string;
}

export interface ReferralEventResponse {
  id: number;
  event_code_id: number;
  actor_user_id?: number | null;
  occurred_at: string;
  metadata_redacted?: Record<string, unknown> | null;
  created_at: string;
}
