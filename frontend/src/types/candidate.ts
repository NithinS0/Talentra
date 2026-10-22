/**
 * Canonical Candidate Profile, Education, Semester, Document, and Resume Types.
 * Aligned with FastAPI Pydantic schemas in backend/app/schemas/candidate.py.
 */

export type EducationLevel =
  | "CLASS_10"
  | "CLASS_12"
  | "DIPLOMA"
  | "UNDERGRADUATE"
  | "POSTGRADUATE"
  | "DOCTORATE";

export type EducationStatus = "COMPLETED" | "PURSUING" | "INCOMPLETE";

export type GradingSystem = "PERCENTAGE" | "CGPA_10" | "CGPA_4" | "MARKS";

export type SemesterResultStatus =
  | "PASS"
  | "FAIL"
  | "AWAITED"
  | "ARREAR"
  | "SUPPLEMENTARY";

export type DocumentCategory =
  | "CLASS_10_MARKSHEET"
  | "CLASS_12_MARKSHEET"
  | "DIPLOMA_CERTIFICATE"
  | "SEMESTER_GRADESHEET"
  | "TRANSCRIPT"
  | "DEGREE_CERTIFICATE"
  | "RESUME"
  | "CERTIFICATE"
  | "OTHER";

export interface SemesterRecord {
  id: number;
  candidate_education_id: number;
  semester_number: number;
  academic_term?: string | null;
  result_status: SemesterResultStatus;
  sgpa?: number | null;
  cgpa?: number | null;
  credits_registered?: number | null;
  credits_earned?: number | null;
  has_backlog: boolean;
  backlog_details?: string | null;
  grade_sheet_storage_key?: string | null;
  grade_sheet_name?: string | null;
  grade_sheet_size_bytes?: number | null;
  grade_sheet_mime_type?: string | null;
  uploaded_at?: string | null;
}

export interface EducationRecord {
  id: number;
  candidate_profile_id: number;
  education_level: EducationLevel;
  institution_name: string;
  board_or_university?: string | null;
  field_of_study?: string | null;
  stream_specialization?: string | null;
  status: EducationStatus;
  start_year?: number | null;
  completion_year?: number | null;
  grading_system: GradingSystem;
  score_value?: number | null;
  max_score?: number | null;
  percentage?: number | null;
  cgpa?: number | null;
  has_backlogs: boolean;
  active_backlogs_count: number;
  historical_backlogs_count: number;
  document_storage_key?: string | null;
  document_name?: string | null;
  document_size_bytes?: number | null;
  document_mime_type?: string | null;
  semesters: SemesterRecord[];
  created_at: string;
  updated_at: string;
}

export interface ResumeVersionItem {
  id: number;
  candidate_resume_id: number;
  version_number: number;
  storage_object_key: string;
  file_name?: string | null;
  file_size_bytes?: number | null;
  mime_type: string;
  target_role?: string | null;
  is_archived: boolean;
  created_at: string;
}

export interface CandidateResumeItem {
  id: number;
  candidate_profile_id: number;
  resume_title: string;
  is_default: boolean;
  versions: ResumeVersionItem[];
  created_at: string;
  updated_at: string;
}

export interface CandidateDocumentItem {
  id: number;
  candidate_profile_id: number;
  document_category: DocumentCategory | string;
  title: string;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  storage_path: string;
  content_sha256: string;
  is_verified: boolean;
  is_archived: boolean;
  linked_entity_type?: string | null;
  linked_entity_id?: number | null;
  created_at: string;
}

export interface SkillItem {
  id: number;
  candidate_profile_id: number;
  skill_name?: string | null;
  proficiency_level: "BEGINNER" | "INTERMEDIATE" | "EXPERT";
  years_experience?: number | null;
  is_primary: boolean;
}

export interface ProjectItem {
  id: number;
  candidate_profile_id: number;
  project_name: string;
  role_description: string;
  technologies?: string | null;
  project_url?: string | null;
  description?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  outcome?: string | null;
}

export interface CertificationItem {
  id: number;
  candidate_profile_id: number;
  name: string;
  issuing_organisation: string;
  issue_date?: string | null;
  expiry_date?: string | null;
  credential_id?: string | null;
  credential_url?: string | null;
  document_storage_key?: string | null;
  document_name?: string | null;
  document_size_bytes?: number | null;
}

export interface WorkExperienceItem {
  id: number;
  candidate_profile_id: number;
  employer_name: string;
  job_title: string;
  start_date: string;
  end_date?: string | null;
  is_current: boolean;
  description?: string | null;
}

export interface CompletenessItem {
  key: string;
  section: string;
  title: string;
  is_complete: boolean;
  weight: number;
  missing_reason?: string | null;
  deep_link: string;
}

export interface ProfileCompleteness {
  overall_score: number;
  is_placement_eligible: boolean;
  checklist_items: CompletenessItem[];
}

export interface CandidateFullProfile {
  id: number;
  user_id: number;
  actor_id: string; // CAxxxxx
  first_name: string;
  middle_name?: string | null;
  last_name: string;
  display_name: string;
  headline?: string | null;
  summary?: string | null;
  profile_photo_url?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
  current_city?: string | null;
  current_state?: string | null;
  email_address?: string | null;
  phone_e164?: string | null;
  country_code?: string | null;
  country_name?: string | null;
  preferred_roles?: string | null;
  preferred_locations?: string | null;
  preferred_employment_types?: string | null;
  expected_graduation_date?: string | null;
  availability_status: string;
  is_public_visible: boolean;
  consent_placement_rules: boolean;
  consent_share_with_employers: boolean;
  completion_score: number;
  education_records: EducationRecord[];
  resumes: CandidateResumeItem[];
  documents: CandidateDocumentItem[];
  skills: SkillItem[];
  projects: ProjectItem[];
  work_experiences: WorkExperienceItem[];
  certifications: CertificationItem[];
  created_at: string;
  updated_at: string;
}
