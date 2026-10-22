-- 1. Covering indexes for all 233 foreign keys
CREATE INDEX IF NOT EXISTS "idx_state_country_id" ON "state" ("country_id");
CREATE INDEX IF NOT EXISTS "idx_city_state_id" ON "city" ("state_id");
CREATE INDEX IF NOT EXISTS "idx_skill_parent_skill_id" ON "skill" ("parent_skill_id");
CREATE INDEX IF NOT EXISTS "idx_industry_parent_industry_id" ON "industry" ("parent_industry_id");
CREATE INDEX IF NOT EXISTS "idx_job_role_industry_id" ON "job_role" ("industry_id");
CREATE INDEX IF NOT EXISTS "idx_reference_code_reference_domain_id" ON "reference_code" ("reference_domain_id");
CREATE INDEX IF NOT EXISTS "idx_reference_code_translation_reference_code_id" ON "reference_code_translation" ("reference_code_id");
CREATE INDEX IF NOT EXISTS "idx_reference_code_translation_language_id" ON "reference_code_translation" ("language_id");
CREATE INDEX IF NOT EXISTS "idx_ui_translation_ui_translation_key_id" ON "ui_translation" ("ui_translation_key_id");
CREATE INDEX IF NOT EXISTS "idx_ui_translation_language_id" ON "ui_translation" ("language_id");
CREATE INDEX IF NOT EXISTS "idx_industry_translation_language_id" ON "industry_translation" ("language_id");
CREATE INDEX IF NOT EXISTS "idx_work_type_translation_language_id" ON "work_type_translation" ("language_id");
CREATE INDEX IF NOT EXISTS "idx_employment_type_translation_language_id" ON "employment_type_translation" ("language_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_profile_user_id" ON "candidate_profile" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_contact_candidate_profile_id" ON "candidate_contact" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_contact_city_id" ON "candidate_contact" ("city_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_education_candidate_profile_id" ON "candidate_education" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_education_qualification_id" ON "candidate_education" ("qualification_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_work_experience_candidate_profile_id" ON "candidate_work_experience" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_work_experience_job_role_id" ON "candidate_work_experience" ("job_role_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_skill_candidate_profile_id" ON "candidate_skill" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_skill_skill_id" ON "candidate_skill" ("skill_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_language_candidate_profile_id" ON "candidate_language" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_language_language_id" ON "candidate_language" ("language_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_project_candidate_profile_id" ON "candidate_project" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_resume_candidate_profile_id" ON "candidate_resume" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_resume_version_candidate_resume_id" ON "resume_version" ("candidate_resume_id");
CREATE INDEX IF NOT EXISTS "idx_resume_version_language_id" ON "resume_version" ("language_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_assessment_candidate_profile_id" ON "candidate_assessment" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_assessment_user_id" ON "candidate_assessment" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_assessment_answer_candidate_profile_id" ON "candidate_assessment_answer" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_assessment_answer_user_id" ON "candidate_assessment_answer" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_assessment_question_candidate_profile_id" ON "assessment_question" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_assessment_question_user_id" ON "assessment_question" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_course_enrolment_candidate_profile_id" ON "candidate_course_enrolment" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_course_enrolment_user_id" ON "candidate_course_enrolment" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_referral_candidate_profile_id" ON "candidate_referral" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_referral_user_id" ON "candidate_referral" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_bookmark_candidate_profile_id" ON "candidate_bookmark" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_bookmark_user_id" ON "candidate_bookmark" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_profile_language_candidate_profile_id" ON "candidate_profile_language" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_profile_language_user_id" ON "candidate_profile_language" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_contact_consent_candidate_profile_id" ON "candidate_contact_consent" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_contact_consent_user_id" ON "candidate_contact_consent" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_project_skill_candidate_profile_id" ON "candidate_project_skill" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_project_skill_user_id" ON "candidate_project_skill" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_referral_attribution_candidate_profile_id" ON "candidate_referral_attribution" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_referral_attribution_user_id" ON "candidate_referral_attribution" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_organisation_id" ON "job_requirement" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_job_role_id" ON "job_requirement" ("job_role_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_employment_type_id" ON "job_requirement" ("employment_type_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_work_type_id" ON "job_requirement" ("work_type_id");
CREATE INDEX IF NOT EXISTS "idx_job_position_job_requirement_id" ON "job_position" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_skill_job_requirement_id" ON "job_requirement_skill" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_skill_job_application_id" ON "job_requirement_skill" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_skill_candidate_profile_id" ON "job_requirement_skill" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_qualification_job_requirement_id" ON "job_requirement_qualification" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_qualification_job_application_id" ON "job_requirement_qualification" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_qualification_candidate_profile_id" ON "job_requirement_qualification" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_location_job_requirement_id" ON "job_requirement_location" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_location_job_application_id" ON "job_requirement_location" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_location_candidate_profile_id" ON "job_requirement_location" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_job_questionnaire_job_requirement_id" ON "job_questionnaire" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_job_questionnaire_job_application_id" ON "job_questionnaire" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_job_questionnaire_candidate_profile_id" ON "job_questionnaire" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_job_questionnaire_question_job_requirement_id" ON "job_questionnaire_question" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_job_questionnaire_question_job_application_id" ON "job_questionnaire_question" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_job_questionnaire_question_candidate_profile_id" ON "job_questionnaire_question" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_job_questionnaire_option_job_requirement_id" ON "job_questionnaire_option" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_job_questionnaire_option_job_application_id" ON "job_questionnaire_option" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_job_questionnaire_option_candidate_profile_id" ON "job_questionnaire_option" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_job_application_job_requirement_id" ON "job_application" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_job_application_candidate_profile_id" ON "job_application" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_job_application_resume_version_id" ON "job_application" ("resume_version_id");
CREATE INDEX IF NOT EXISTS "idx_application_status_history_job_application_id" ON "application_status_history" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_application_answer_job_requirement_id" ON "application_answer" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_application_answer_job_application_id" ON "application_answer" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_application_answer_candidate_profile_id" ON "application_answer" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_application_shortlist_job_requirement_id" ON "application_shortlist" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_application_shortlist_job_application_id" ON "application_shortlist" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_application_shortlist_candidate_profile_id" ON "application_shortlist" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_application_interview_job_requirement_id" ON "application_interview" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_application_interview_job_application_id" ON "application_interview" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_application_interview_candidate_profile_id" ON "application_interview" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_application_interview_feedback_job_requirement_id" ON "application_interview_feedback" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_application_interview_feedback_job_application_id" ON "application_interview_feedback" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_application_interview_feedback_candidate_profile_id" ON "application_interview_feedback" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_application_offer_job_requirement_id" ON "application_offer" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_application_offer_job_application_id" ON "application_offer" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_application_offer_candidate_profile_id" ON "application_offer" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_application_join_record_job_requirement_id" ON "application_join_record" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_application_join_record_job_application_id" ON "application_join_record" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_application_join_record_candidate_profile_id" ON "application_join_record" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_application_rejection_job_requirement_id" ON "application_rejection" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_application_rejection_job_application_id" ON "application_rejection" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_application_rejection_candidate_profile_id" ON "application_rejection" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_job_bookmark_job_requirement_id" ON "job_bookmark" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_job_bookmark_job_application_id" ON "job_bookmark" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_job_bookmark_candidate_profile_id" ON "job_bookmark" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_status_history_job_requirement_id" ON "job_requirement_status_history" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_employment_type_job_requirement_id" ON "job_requirement_employment_type" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_employment_type_job_application_id" ON "job_requirement_employment_type" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_employment_type_candidate_profile_id" ON "job_requirement_employment_type" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_work_type_job_requirement_id" ON "job_requirement_work_type" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_work_type_job_application_id" ON "job_requirement_work_type" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_job_requirement_work_type_candidate_profile_id" ON "job_requirement_work_type" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_application_feedback_job_requirement_id" ON "application_feedback" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_application_feedback_job_application_id" ON "application_feedback" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_application_feedback_candidate_profile_id" ON "application_feedback" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_job_search_saved_filter_job_requirement_id" ON "job_search_saved_filter" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_job_search_saved_filter_job_application_id" ON "job_search_saved_filter" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_job_search_saved_filter_candidate_profile_id" ON "job_search_saved_filter" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_credential_user_id" ON "credential" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_role_permission_role_id" ON "role_permission" ("role_id");
CREATE INDEX IF NOT EXISTS "idx_role_permission_permission_id" ON "role_permission" ("permission_id");
CREATE INDEX IF NOT EXISTS "idx_user_role_assignment_user_id" ON "user_role_assignment" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_user_role_assignment_role_id" ON "user_role_assignment" ("role_id");
CREATE INDEX IF NOT EXISTS "idx_user_role_assignment_organisation_id" ON "user_role_assignment" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_identity_session_user_id" ON "identity_session" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_consent_record_user_id" ON "consent_record" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_account_recovery_request_organisation_id" ON "account_recovery_request" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_account_recovery_request_account_id" ON "account_recovery_request" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_parent_organisation_id" ON "organisation" ("parent_organisation_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_profile_organisation_id" ON "organisation_profile" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_profile_account_id" ON "organisation_profile" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_location_organisation_id" ON "organisation_location" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_location_account_id" ON "organisation_location" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_identifier_organisation_id" ON "organisation_identifier" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_identifier_country_id" ON "organisation_identifier" ("country_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_verification_organisation_id" ON "organisation_verification" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_verification_account_id" ON "organisation_verification" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_recruiter_mapping_organisation_id" ON "organisation_recruiter_mapping" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_account_organisation_organisation_id" ON "account_organisation" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_account_organisation_account_id" ON "account_organisation" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_account_admin_assignment_organisation_id" ON "account_admin_assignment" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_account_admin_assignment_account_id" ON "account_admin_assignment" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_contact_organisation_id" ON "organisation_contact" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_contact_account_id" ON "organisation_contact" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_review_organisation_id" ON "organisation_review" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_review_account_id" ON "organisation_review" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_status_history_organisation_id" ON "organisation_status_history" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_domain_organisation_id" ON "organisation_domain" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_domain_account_id" ON "organisation_domain" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_document_reference_organisation_id" ON "organisation_document_reference" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_document_reference_account_id" ON "organisation_document_reference" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_account_status_history_account_id" ON "account_status_history" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_hierarchy_closure_organisation_id" ON "organisation_hierarchy_closure" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_hierarchy_closure_account_id" ON "organisation_hierarchy_closure" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_organisation_verification_event_organisation_verification_id" ON "organisation_verification_event" ("organisation_verification_id");
CREATE INDEX IF NOT EXISTS "idx_gig_worker_profile_user_id" ON "gig_worker_profile" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_gig_service_offering_gig_request_id" ON "gig_service_offering" ("gig_request_id");
CREATE INDEX IF NOT EXISTS "idx_gig_service_offering_gig_worker_profile_id" ON "gig_service_offering" ("gig_worker_profile_id");
CREATE INDEX IF NOT EXISTS "idx_gig_worker_skill_gig_request_id" ON "gig_worker_skill" ("gig_request_id");
CREATE INDEX IF NOT EXISTS "idx_gig_worker_skill_gig_worker_profile_id" ON "gig_worker_skill" ("gig_worker_profile_id");
CREATE INDEX IF NOT EXISTS "idx_gig_worker_availability_gig_request_id" ON "gig_worker_availability" ("gig_request_id");
CREATE INDEX IF NOT EXISTS "idx_gig_worker_availability_gig_worker_profile_id" ON "gig_worker_availability" ("gig_worker_profile_id");
CREATE INDEX IF NOT EXISTS "idx_gig_application_gig_request_id" ON "gig_application" ("gig_request_id");
CREATE INDEX IF NOT EXISTS "idx_gig_application_gig_worker_profile_id" ON "gig_application" ("gig_worker_profile_id");
CREATE INDEX IF NOT EXISTS "idx_gig_assignment_gig_application_id" ON "gig_assignment" ("gig_application_id");
CREATE INDEX IF NOT EXISTS "idx_gig_assignment_gig_worker_profile_id" ON "gig_assignment" ("gig_worker_profile_id");
CREATE INDEX IF NOT EXISTS "idx_gig_handoff_reference_gig_assignment_id" ON "gig_handoff_reference" ("gig_assignment_id");
CREATE INDEX IF NOT EXISTS "idx_gig_earnings_reconciliation_gig_request_id" ON "gig_earnings_reconciliation" ("gig_request_id");
CREATE INDEX IF NOT EXISTS "idx_gig_earnings_reconciliation_gig_worker_profile_id" ON "gig_earnings_reconciliation" ("gig_worker_profile_id");
CREATE INDEX IF NOT EXISTS "idx_gig_worker_list_entry_gig_request_id" ON "gig_worker_list_entry" ("gig_request_id");
CREATE INDEX IF NOT EXISTS "idx_gig_worker_list_entry_gig_worker_profile_id" ON "gig_worker_list_entry" ("gig_worker_profile_id");
CREATE INDEX IF NOT EXISTS "idx_gig_rating_gig_request_id" ON "gig_rating" ("gig_request_id");
CREATE INDEX IF NOT EXISTS "idx_gig_rating_gig_worker_profile_id" ON "gig_rating" ("gig_worker_profile_id");
CREATE INDEX IF NOT EXISTS "idx_gig_request_status_history_gig_request_id" ON "gig_request_status_history" ("gig_request_id");
CREATE INDEX IF NOT EXISTS "idx_gig_application_status_history_gig_application_id" ON "gig_application_status_history" ("gig_application_id");
CREATE INDEX IF NOT EXISTS "idx_gig_assignment_status_history_gig_assignment_id" ON "gig_assignment_status_history" ("gig_assignment_id");
CREATE INDEX IF NOT EXISTS "idx_licence_account_id" ON "licence" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_licence_seat_allocation_user_id" ON "licence_seat_allocation" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_licence_seat_allocation_licence_id" ON "licence_seat_allocation" ("licence_id");
CREATE INDEX IF NOT EXISTS "idx_registered_device_user_id" ON "registered_device" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_licence_usage_snapshot_user_id" ON "licence_usage_snapshot" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_licence_usage_snapshot_licence_id" ON "licence_usage_snapshot" ("licence_id");
CREATE INDEX IF NOT EXISTS "idx_login_device_decision_user_id" ON "login_device_decision" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_login_device_decision_licence_id" ON "login_device_decision" ("licence_id");
CREATE INDEX IF NOT EXISTS "idx_licence_entitlement_user_id" ON "licence_entitlement" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_licence_entitlement_licence_id" ON "licence_entitlement" ("licence_id");
CREATE INDEX IF NOT EXISTS "idx_licence_status_history_licence_id" ON "licence_status_history" ("licence_id");
CREATE INDEX IF NOT EXISTS "idx_device_login_counter_user_id" ON "device_login_counter" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_device_login_counter_licence_id" ON "device_login_counter" ("licence_id");
CREATE INDEX IF NOT EXISTS "idx_sourcing_request_job_requirement_id" ON "sourcing_request" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_outreach_batch_organisation_id" ON "outreach_batch" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_outreach_batch_job_requirement_id" ON "outreach_batch" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_outreach_recipient_outreach_batch_id" ON "outreach_recipient" ("outreach_batch_id");
CREATE INDEX IF NOT EXISTS "idx_outreach_recipient_candidate_profile_id" ON "outreach_recipient" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_sourcing_shortlist_candidate_profile_id" ON "candidate_sourcing_shortlist" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_sourcing_shortlist_user_id" ON "candidate_sourcing_shortlist" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_sourcing_request_status_history_sourcing_request_id" ON "sourcing_request_status_history" ("sourcing_request_id");
CREATE INDEX IF NOT EXISTS "idx_candidate_contact_attempt_candidate_contact_id" ON "candidate_contact_attempt" ("candidate_contact_id");
CREATE INDEX IF NOT EXISTS "idx_consultant_profile_candidate_profile_id" ON "consultant_profile" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_consultant_profile_user_id" ON "consultant_profile" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_subscription_account_id" ON "subscription" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_subscription_subscription_plan_id" ON "subscription" ("subscription_plan_id");
CREATE INDEX IF NOT EXISTS "idx_subscription_licence_id" ON "subscription" ("licence_id");
CREATE INDEX IF NOT EXISTS "idx_subscription_renewal_account_id" ON "subscription_renewal" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_subscription_cancellation_account_id" ON "subscription_cancellation" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_payment_order_account_id" ON "payment_order" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_payment_transaction_payment_order_id" ON "payment_transaction" ("payment_order_id");
CREATE INDEX IF NOT EXISTS "idx_invoice_account_id" ON "invoice" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_invoice_subscription_id" ON "invoice" ("subscription_id");
CREATE INDEX IF NOT EXISTS "idx_invoice_line_account_id" ON "invoice_line" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_payment_refund_account_id" ON "payment_refund" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_wallet_account_id" ON "wallet" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_wallet_ledger_entry_wallet_id" ON "wallet_ledger_entry" ("wallet_id");
CREATE INDEX IF NOT EXISTS "idx_credit_consumption_account_id" ON "credit_consumption" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_profile_download_history_candidate_profile_id" ON "profile_download_history" ("candidate_profile_id");
CREATE INDEX IF NOT EXISTS "idx_profile_download_history_organisation_id" ON "profile_download_history" ("organisation_id");
CREATE INDEX IF NOT EXISTS "idx_profile_download_history_credit_consumption_id" ON "profile_download_history" ("credit_consumption_id");
CREATE INDEX IF NOT EXISTS "idx_wallet_balance_snapshot_account_id" ON "wallet_balance_snapshot" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_invoice_status_history_invoice_id" ON "invoice_status_history" ("invoice_id");
CREATE INDEX IF NOT EXISTS "idx_payment_reconciliation_run_account_id" ON "payment_reconciliation_run" ("account_id");
CREATE INDEX IF NOT EXISTS "idx_notification_preference_user_id" ON "notification_preference" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_job_alert_preference_user_id" ON "job_alert_preference" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_privacy_preference_user_id" ON "privacy_preference" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_notification_user_id" ON "notification" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_notification_delivery_notification_id" ON "notification_delivery" ("notification_id");
CREATE INDEX IF NOT EXISTS "idx_notification_template_user_id" ON "notification_template" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_community_post_language_id" ON "community_post" ("language_id");
CREATE INDEX IF NOT EXISTS "idx_notification_delivery_attempt_notification_delivery_id" ON "notification_delivery_attempt" ("notification_delivery_id");
CREATE INDEX IF NOT EXISTS "idx_notification_preference_history_notification_preference_id" ON "notification_preference_history" ("notification_preference_id");
CREATE INDEX IF NOT EXISTS "idx_support_ticket_status_history_support_ticket_id" ON "support_ticket_status_history" ("support_ticket_id");
CREATE INDEX IF NOT EXISTS "idx_identity_verification_case_user_id" ON "identity_verification_case" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_identity_verification_case_consent_record_id" ON "identity_verification_case" ("consent_record_id");
CREATE INDEX IF NOT EXISTS "idx_government_document_reference_user_id" ON "government_document_reference" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_verification_review_user_id" ON "verification_review" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_verification_consent_purpose_user_id" ON "verification_consent_purpose" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_verification_retention_job_user_id" ON "verification_retention_job" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_trending_job_snapshot_job_requirement_id" ON "trending_job_snapshot" ("job_requirement_id");
CREATE INDEX IF NOT EXISTS "idx_trending_job_snapshot_job_application_id" ON "trending_job_snapshot" ("job_application_id");
CREATE INDEX IF NOT EXISTS "idx_trending_job_snapshot_candidate_profile_id" ON "trending_job_snapshot" ("candidate_profile_id");

-- 2. Exclusion constraints using btree_gist
ALTER TABLE "subscription" 
ADD CONSTRAINT "excl_subscription_licence_period" 
EXCLUDE USING gist (
    "licence_id" WITH =, 
    tstzrange("starts_at", "ends_at") WITH &&
);

ALTER TABLE "gig_worker_availability" 
ADD CONSTRAINT "excl_gig_worker_availability_window" 
EXCLUDE USING gist (
    "gig_worker_profile_id" WITH =, 
    tstzrange("starts_at", "ends_at") WITH &&
);

-- 3. Append-only trigger function and triggers for immutable tables
CREATE OR REPLACE FUNCTION prevent_immutable_record_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutable record violation: updates and deletes are prohibited on %', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_immutable_audit_event
BEFORE UPDATE OR DELETE ON "audit_event"
FOR EACH ROW EXECUTE FUNCTION prevent_immutable_record_modification();

CREATE TRIGGER trg_immutable_wallet_ledger
BEFORE UPDATE OR DELETE ON "wallet_ledger_entry"
FOR EACH ROW EXECUTE FUNCTION prevent_immutable_record_modification();

CREATE TRIGGER trg_immutable_payment_transaction
BEFORE UPDATE OR DELETE ON "payment_transaction"
FOR EACH ROW EXECUTE FUNCTION prevent_immutable_record_modification();

CREATE TRIGGER trg_immutable_profile_download_history
BEFORE UPDATE OR DELETE ON "profile_download_history"
FOR EACH ROW EXECUTE FUNCTION prevent_immutable_record_modification();