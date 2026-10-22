"use client";

import React, { useEffect, useState, useRef } from "react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getMyCandidateProfile,
  updateMyCandidateProfile,
  getMyProfileCompleteness,
  uploadProfilePhoto,
  deleteProfilePhoto,
  addEducation,
  updateEducation,
  deleteEducation,
  uploadEducationDocument,
  addOrUpdateSemester,
  deleteSemester,
  uploadSemesterGradeSheet,
  uploadResume,
  setDefaultResume,
  deleteResume,
  uploadDocument,
  deleteDocument,
  addSkill,
  deleteSkill,
  addProject,
  deleteProject,
  addCertification,
  deleteCertification,
  addWorkExperience,
  deleteWorkExperience,
} from "@/lib/api/candidates";
import {
  CandidateFullProfile,
  ProfileCompleteness,
  EducationRecord,
  SemesterRecord,
  CandidateResumeItem,
  CandidateDocumentItem,
  SkillItem,
  ProjectItem,
  CertificationItem,
  WorkExperienceItem,
  EducationLevel,
  EducationStatus,
  GradingSystem,
  SemesterResultStatus,
} from "@/types/candidate";
import {
  User,
  GraduationCap,
  FileText,
  Briefcase,
  Code,
  FolderGit2,
  Award,
  Upload,
  Trash2,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Camera,
  ExternalLink,
  Plus,
  Loader2,
  Save,
  Check,
  ChevronRight,
  Shield,
  Eye,
  FileCheck,
  Sparkles,
  Download,
  Calendar,
  Layers,
  FileSpreadsheet,
} from "lucide-react";
import { formatDate } from "@/lib/utils";

type ActiveTab =
  | "personal"
  | "academics"
  | "semesters"
  | "resumes"
  | "documents"
  | "skills_projects";

export default function CandidateProfilePage() {
  const [profile, setProfile] = useState<CandidateFullProfile | null>(null);
  const [completeness, setCompleteness] = useState<ProfileCompleteness | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>("personal");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // File upload input references
  const photoInputRef = useRef<HTMLInputElement>(null);
  const resumeInputRef = useRef<HTMLInputElement>(null);
  const documentInputRef = useRef<HTMLInputElement>(null);

  // Modals & form state
  const [showAddEduModal, setShowAddEduModal] = useState(false);
  const [showAddSemModal, setShowAddSemModal] = useState(false);
  const [showAddSkillModal, setShowAddSkillModal] = useState(false);
  const [showAddProjectModal, setShowAddProjectModal] = useState(false);
  const [showAddCertModal, setShowAddCertModal] = useState(false);
  const [showAddExpModal, setShowAddExpModal] = useState(false);
  const [showUploadDocModal, setShowUploadDocModal] = useState(false);

  // Selected education for semester management
  const [selectedEducationId, setSelectedEducationId] = useState<number | null>(null);

  // Fetch full profile and completeness
  const refreshProfileData = async () => {
    try {
      const [fullProf, comp] = await Promise.all([
        getMyCandidateProfile(),
        getMyProfileCompleteness(),
      ]);
      setProfile(fullProf);
      setCompleteness(comp);

      // Auto-select college/undergraduate education for semester view if none selected
      if (!selectedEducationId && fullProf.education_records.length > 0) {
        const ugOrDiploma = fullProf.education_records.find(
          (e) => e.education_level === "UNDERGRADUATE" || e.education_level === "DIPLOMA"
        );
        setSelectedEducationId(ugOrDiploma ? ugOrDiploma.id : fullProf.education_records[0].id);
      }
    } catch (err: unknown) {
      console.error("Failed to load profile:", err);
      setStatusMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to load candidate profile.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    const loadInitialData = async () => {
      try {
        const [fullProf, comp] = await Promise.all([
          getMyCandidateProfile(),
          getMyProfileCompleteness(),
        ]);
        if (!isMounted) return;
        setProfile(fullProf);
        setCompleteness(comp);

        if (!selectedEducationId && fullProf.education_records.length > 0) {
          const ugOrDiploma = fullProf.education_records.find(
            (e) => e.education_level === "UNDERGRADUATE" || e.education_level === "DIPLOMA"
          );
          setSelectedEducationId(ugOrDiploma ? ugOrDiploma.id : fullProf.education_records[0].id);
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        setStatusMessage({
          type: "error",
          text: err instanceof Error ? err.message : "Failed to load candidate profile.",
        });
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    loadInitialData();
    return () => {
      isMounted = false;
    };
  }, [selectedEducationId]);

  const showNotification = (type: "success" | "error", text: string) => {
    setStatusMessage({ type, text });
    setTimeout(() => setStatusMessage(null), 5000);
  };

  // ──────────────────────────────────────────────────────────────────────────
  // 1. Personal & Contact Handlers
  // ──────────────────────────────────────────────────────────────────────────
  const handlePersonalUpdate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!profile) return;
    setIsSaving(true);
    const formData = new FormData(e.currentTarget);

    try {
      const payload: Partial<CandidateFullProfile> = {
        first_name: formData.get("first_name") as string,
        middle_name: (formData.get("middle_name") as string) || undefined,
        last_name: formData.get("last_name") as string,
        headline: (formData.get("headline") as string) || undefined,
        summary: (formData.get("summary") as string) || undefined,
        phone_e164: (formData.get("phone_e164") as string) || undefined,
        email_address: (formData.get("email_address") as string) || undefined,
        current_city: (formData.get("current_city") as string) || undefined,
        current_state: (formData.get("current_state") as string) || undefined,
        linkedin_url: (formData.get("linkedin_url") as string) || undefined,
        github_url: (formData.get("github_url") as string) || undefined,
        portfolio_url: (formData.get("portfolio_url") as string) || undefined,
        preferred_roles: (formData.get("preferred_roles") as string) || undefined,
        preferred_locations: (formData.get("preferred_locations") as string) || undefined,
        is_public_visible: formData.get("is_public_visible") === "on",
        consent_placement_rules: formData.get("consent_placement_rules") === "on",
      };

      const updated = await updateMyCandidateProfile(payload);
      setProfile(updated);
      await refreshProfileData();
      showNotification("success", "Profile details saved successfully.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to save profile.");
    } finally {
      setIsSaving(false);
    }
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsSaving(true);
    try {
      const res = await uploadProfilePhoto(file);
      if (profile) {
        setProfile({ ...profile, profile_photo_url: res.photo_url });
      }
      await refreshProfileData();
      showNotification("success", "Profile photo updated successfully.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to upload photo.");
    } finally {
      setIsSaving(false);
    }
  };

  const handlePhotoDelete = async () => {
    if (!confirm("Are you sure you want to remove your profile photo?")) return;
    setIsSaving(true);
    try {
      await deleteProfilePhoto();
      if (profile) {
        setProfile({ ...profile, profile_photo_url: null });
      }
      await refreshProfileData();
      showNotification("success", "Profile photo removed.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to delete photo.");
    } finally {
      setIsSaving(false);
    }
  };

  // ──────────────────────────────────────────────────────────────────────────
  // 2. Education Handlers
  // ──────────────────────────────────────────────────────────────────────────
  const handleAddEducationSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSaving(true);
    const fd = new FormData(e.currentTarget);

    try {
      const payload: Partial<EducationRecord> = {
        education_level: fd.get("education_level") as EducationLevel,
        institution_name: fd.get("institution_name") as string,
        board_or_university: (fd.get("board_or_university") as string) || undefined,
        field_of_study: (fd.get("field_of_study") as string) || undefined,
        stream_specialization: (fd.get("stream_specialization") as string) || undefined,
        status: (fd.get("status") as EducationStatus) || "COMPLETED",
        start_year: fd.get("start_year") ? Number(fd.get("start_year")) : undefined,
        completion_year: fd.get("completion_year") ? Number(fd.get("completion_year")) : undefined,
        grading_system: (fd.get("grading_system") as GradingSystem) || "PERCENTAGE",
        score_value: fd.get("score_value") ? Number(fd.get("score_value")) : undefined,
        max_score: fd.get("max_score") ? Number(fd.get("max_score")) : undefined,
        percentage: fd.get("percentage") ? Number(fd.get("percentage")) : undefined,
        cgpa: fd.get("cgpa") ? Number(fd.get("cgpa")) : undefined,
        has_backlogs: fd.get("has_backlogs") === "on",
        active_backlogs_count: fd.get("active_backlogs_count")
          ? Number(fd.get("active_backlogs_count"))
          : 0,
      };

      await addEducation(payload);
      await refreshProfileData();
      setShowAddEduModal(false);
      showNotification("success", "Academic record added successfully.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to add academic record.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteEducation = async (id: number) => {
    if (!confirm("Are you sure you want to delete this qualification record?")) return;
    try {
      await deleteEducation(id);
      await refreshProfileData();
      showNotification("success", "Qualification record deleted.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to delete record.");
    }
  };

  const handleEducationDocUpload = async (educationId: number, file: File) => {
    try {
      await uploadEducationDocument(educationId, file);
      await refreshProfileData();
      showNotification("success", "Marksheet uploaded successfully.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to upload marksheet.");
    }
  };

  // ──────────────────────────────────────────────────────────────────────────
  // 3. Semester Handlers
  // ──────────────────────────────────────────────────────────────────────────
  const handleAddSemesterSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedEducationId) return;
    setIsSaving(true);
    const fd = new FormData(e.currentTarget);

    try {
      const payload: Partial<SemesterRecord> = {
        semester_number: Number(fd.get("semester_number")),
        academic_term: (fd.get("academic_term") as string) || undefined,
        result_status: (fd.get("result_status") as SemesterResultStatus) || "PASS",
        sgpa: fd.get("sgpa") ? Number(fd.get("sgpa")) : undefined,
        cgpa: fd.get("cgpa") ? Number(fd.get("cgpa")) : undefined,
        credits_registered: fd.get("credits_registered") ? Number(fd.get("credits_registered")) : undefined,
        credits_earned: fd.get("credits_earned") ? Number(fd.get("credits_earned")) : undefined,
        has_backlog: fd.get("has_backlog") === "on",
        backlog_details: (fd.get("backlog_details") as string) || undefined,
      };

      await addOrUpdateSemester(selectedEducationId, payload);
      await refreshProfileData();
      setShowAddSemModal(false);
      showNotification("success", "Semester gradesheet added successfully.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to add semester.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteSemester = async (semId: number) => {
    if (!selectedEducationId) return;
    if (!confirm("Are you sure you want to delete this semester record?")) return;
    try {
      await deleteSemester(selectedEducationId, semId);
      await refreshProfileData();
      showNotification("success", "Semester record deleted.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to delete semester.");
    }
  };

  const handleSemesterDocUpload = async (semNumber: number, file: File) => {
    if (!selectedEducationId) return;
    try {
      await uploadSemesterGradeSheet(selectedEducationId, semNumber, file);
      await refreshProfileData();
      showNotification("success", "Semester marksheet uploaded.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to upload marksheet.");
    }
  };

  // ──────────────────────────────────────────────────────────────────────────
  // 4. Resume Handlers
  // ──────────────────────────────────────────────────────────────────────────
  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsSaving(true);
    try {
      const title = prompt("Enter a title for this resume (e.g., Software Engineering Resume):", "Primary Resume");
      if (!title) return;
      await uploadResume(file, title, undefined, true);
      await refreshProfileData();
      showNotification("success", "Resume uploaded and set as default.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to upload resume.");
    } finally {
      setIsSaving(false);
      if (resumeInputRef.current) resumeInputRef.current.value = "";
    }
  };

  const handleSetDefaultResume = async (resumeId: number) => {
    try {
      await setDefaultResume(resumeId);
      await refreshProfileData();
      showNotification("success", "Default resume updated.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to set default resume.");
    }
  };

  const handleDeleteResume = async (resumeId: number) => {
    if (!confirm("Are you sure you want to delete this resume? Active application snapshots will remain preserved.")) return;
    try {
      await deleteResume(resumeId);
      await refreshProfileData();
      showNotification("success", "Resume deleted.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to delete resume.");
    }
  };

  // ──────────────────────────────────────────────────────────────────────────
  // 5. Document Vault Handlers
  // ──────────────────────────────────────────────────────────────────────────
  const handleDocumentVaultUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const file = (e.currentTarget.elements.namedItem("doc_file") as HTMLInputElement)?.files?.[0];
    const category = fd.get("category") as string;
    const title = fd.get("title") as string;

    if (!file || !category || !title) {
      showNotification("error", "Please provide a document title, category, and file.");
      return;
    }

    setIsSaving(true);
    try {
      await uploadDocument(file, category, title);
      await refreshProfileData();
      setShowUploadDocModal(false);
      showNotification("success", "Document stored in vault with SHA-256 integrity hash.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to upload document.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteVaultDocument = async (docId: number) => {
    if (!confirm("Are you sure you want to remove this document from your vault?")) return;
    try {
      await deleteDocument(docId);
      await refreshProfileData();
      showNotification("success", "Document removed from vault.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to delete document.");
    }
  };

  // ──────────────────────────────────────────────────────────────────────────
  // 6. Skills, Projects, Experience & Certifications Handlers
  // ──────────────────────────────────────────────────────────────────────────
  const handleAddSkillSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await addSkill({
        skill_name: fd.get("skill_name") as string,
        proficiency_level: (fd.get("proficiency_level") as "BEGINNER" | "INTERMEDIATE" | "EXPERT") || "INTERMEDIATE",
        years_experience: fd.get("years_experience") ? Number(fd.get("years_experience")) : 1,
        is_primary: fd.get("is_primary") === "on",
      });
      await refreshProfileData();
      setShowAddSkillModal(false);
      showNotification("success", "Skill added.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to add skill.");
    }
  };

  const handleAddProjectSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await addProject({
        project_name: fd.get("project_name") as string,
        role_description: (fd.get("role_description") as string) || "Lead Developer",
        technologies: (fd.get("technologies") as string) || undefined,
        project_url: (fd.get("project_url") as string) || undefined,
        description: (fd.get("description") as string) || undefined,
      });
      await refreshProfileData();
      setShowAddProjectModal(false);
      showNotification("success", "Project added.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to add project.");
    }
  };

  const handleAddCertSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await addCertification({
        name: fd.get("name") as string,
        issuing_organisation: fd.get("issuing_organisation") as string,
        credential_id: (fd.get("credential_id") as string) || undefined,
        credential_url: (fd.get("credential_url") as string) || undefined,
      });
      await refreshProfileData();
      setShowAddCertModal(false);
      showNotification("success", "Certification recorded.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to add certification.");
    }
  };

  const handleAddExpSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await addWorkExperience({
        employer_name: fd.get("employer_name") as string,
        job_title: fd.get("job_title") as string,
        start_date: (fd.get("start_date") as string) || "2024-01-01",
        end_date: (fd.get("end_date") as string) || undefined,
        is_current: fd.get("is_current") === "on",
        description: (fd.get("description") as string) || undefined,
      });
      await refreshProfileData();
      setShowAddExpModal(false);
      showNotification("success", "Work experience added.");
    } catch (err: unknown) {
      showNotification("error", err instanceof Error ? err.message : "Failed to add work experience.");
    }
  };

  if (isLoading) {
    return (
      <DashboardShell>
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
          <Loader2 className="w-10 h-10 animate-spin text-[#4169D8]" />
          <p className="text-slate-600 dark:text-slate-400 font-medium">
            Loading candidate records & verification status...
          </p>
        </div>
      </DashboardShell>
    );
  }

  const selectedEducation = profile?.education_records.find((e) => e.id === selectedEducationId);

  return (
    <DashboardShell>
      <div className="space-y-6 max-w-7xl mx-auto pb-16">
        {/* Notification Toast */}
        {statusMessage && (
          <div
            className={`p-4 rounded-xl flex items-center justify-between text-sm font-medium transition-all duration-200 border ${
              statusMessage.type === "success"
                ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-200 border-emerald-200 dark:border-emerald-800/50"
                : "bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-200 border-rose-200 dark:border-rose-800/50"
            }`}
          >
            <div className="flex items-center space-x-2">
              {statusMessage.type === "success" ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0" />
              )}
              <span>{statusMessage.text}</span>
            </div>
            <button
              onClick={() => setStatusMessage(null)}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            >
              ✕
            </button>
          </div>
        )}

        {/* ─── Profile Header & Completeness Card ──────────────────────────────── */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            {/* Candidate Identity Avatar */}
            <div className="flex items-center space-x-5">
              <div className="relative group">
                <div className="w-24 h-24 rounded-2xl bg-gradient-to-tr from-[#4169D8] to-indigo-500 flex items-center justify-center text-white text-3xl font-bold shadow-md overflow-hidden border-2 border-white dark:border-slate-800">
                  {profile?.profile_photo_url ? (
                    <img
                      src={profile.profile_photo_url}
                      alt={profile.display_name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <span>
                      {profile?.first_name?.[0]}
                      {profile?.last_name?.[0]}
                    </span>
                  )}
                </div>
                {/* Photo Actions Overlay */}
                <div className="absolute inset-0 bg-black/60 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2">
                  <button
                    type="button"
                    onClick={() => photoInputRef.current?.click()}
                    title="Upload Photo"
                    className="p-1.5 bg-white/20 hover:bg-white/40 text-white rounded-lg transition"
                  >
                    <Camera className="w-4 h-4" />
                  </button>
                  {profile?.profile_photo_url && (
                    <button
                      type="button"
                      onClick={handlePhotoDelete}
                      title="Remove Photo"
                      className="p-1.5 bg-rose-500/80 hover:bg-rose-600 text-white rounded-lg transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
                <input
                  type="file"
                  ref={photoInputRef}
                  onChange={handlePhotoUpload}
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                />
              </div>

              <div>
                <div className="flex items-center space-x-3">
                  <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                    {profile?.display_name || "Candidate Profile"}
                  </h1>
                  <Badge variant="outline" className="font-mono text-xs">
                    {profile?.actor_id}
                  </Badge>
                  {completeness?.is_placement_eligible ? (
                    <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 flex items-center space-x-1">
                      <Shield className="w-3 h-3 mr-1" /> Placement Eligible
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-amber-600 dark:text-amber-400">
                      Incomplete Profile
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 line-clamp-1">
                  {profile?.headline || "Add a professional headline describing your career focus"}
                </p>
                <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-slate-500 dark:text-slate-400">
                  {profile?.current_city && (
                    <span className="flex items-center">
                      📍 {profile.current_city}, {profile.current_state}
                    </span>
                  )}
                  {profile?.email_address && (
                    <span className="flex items-center">✉️ {profile.email_address}</span>
                  )}
                  {profile?.phone_e164 && (
                    <span className="flex items-center">📞 {profile.phone_e164}</span>
                  )}
                </div>
              </div>
            </div>

            {/* Completeness Score Gauge */}
            <div className="bg-slate-50 dark:bg-slate-800/60 p-4 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col justify-center min-w-[260px]">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Profile Completeness
                </span>
                <span className="text-base font-bold text-[#4169D8]">
                  {completeness?.overall_score ?? 0}%
                </span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-2.5 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 rounded-full ${
                    (completeness?.overall_score ?? 0) >= 80
                      ? "bg-emerald-500"
                      : (completeness?.overall_score ?? 0) >= 50
                      ? "bg-[#4169D8]"
                      : "bg-amber-500"
                  }`}
                  style={{ width: `${completeness?.overall_score ?? 0}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-2">
                {(completeness?.overall_score ?? 0) >= 80
                  ? "✓ Verified for placement drive shortlisting"
                  : "Complete required records to unlock all placement opportunities"}
              </p>
            </div>
          </div>

          {/* Missing Checklist Banner (if incomplete) */}
          {completeness && completeness.checklist_items.filter((i) => !i.is_complete).length > 0 && (
            <div className="mt-6 pt-5 border-t border-slate-100 dark:border-slate-800/80">
              <div className="flex items-center space-x-2 text-xs font-semibold text-amber-700 dark:text-amber-400 mb-2">
                <AlertTriangle className="w-4 h-4" />
                <span>Action Items to Complete Your Placement Profile:</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                {completeness.checklist_items
                  .filter((i) => !i.is_complete)
                  .map((item) => (
                    <div
                      key={item.key}
                      onClick={() => {
                        if (item.section === "personal") setActiveTab("personal");
                        else if (item.section === "academics") setActiveTab("academics");
                        else if (item.section === "resumes") setActiveTab("resumes");
                        else if (item.section === "skills") setActiveTab("skills_projects");
                      }}
                      className="cursor-pointer group flex items-center justify-between p-2.5 rounded-lg bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/30 hover:border-[#4169D8] transition"
                    >
                      <div className="text-xs text-slate-700 dark:text-slate-300">
                        <span className="font-medium group-hover:text-[#4169D8] transition">
                          {item.title}
                        </span>
                        {item.missing_reason && (
                          <p className="text-[10px] text-slate-500 dark:text-slate-400">
                            {item.missing_reason}
                          </p>
                        )}
                      </div>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-[#4169D8] transition shrink-0 ml-2" />
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>

        {/* ─── Navigation Tabs ────────────────────────────────────────────────── */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 overflow-x-auto space-x-2 pb-px scrollbar-none">
          {[
            { id: "personal", label: "Personal & Contact", icon: User },
            { id: "academics", label: "Academic Records", icon: GraduationCap },
            { id: "semesters", label: "Semester Grade Sheets", icon: FileSpreadsheet },
            { id: "resumes", label: "Resume Manager", icon: FileText },
            { id: "documents", label: "Document Vault", icon: Layers },
            { id: "skills_projects", label: "Skills & Projects", icon: Code },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as ActiveTab)}
                className={`flex items-center space-x-2 py-3 px-4 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                  isActive
                    ? "border-[#4169D8] text-[#4169D8] dark:text-[#5B82EE]"
                    : "border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* ─── TAB 1: Personal & Contact Details ──────────────────────────────── */}
        {activeTab === "personal" && profile && (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
            <form onSubmit={handlePersonalUpdate} className="space-y-6">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                    Personal Information & Placement Preferences
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Basic identification, verified contact information, and job matching criteria.
                  </p>
                </div>
                <Button type="submit" disabled={isSaving} className="bg-[#4169D8] hover:bg-[#3355B8]">
                  {isSaving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                  Save Changes
                </Button>
              </div>

              {/* Name Fields */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    First Name <span className="text-rose-500">*</span>
                  </label>
                  <Input name="first_name" defaultValue={profile.first_name} required />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    Middle Name
                  </label>
                  <Input name="middle_name" defaultValue={profile.middle_name || ""} />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    Last Name <span className="text-rose-500">*</span>
                  </label>
                  <Input name="last_name" defaultValue={profile.last_name} required />
                </div>
              </div>

              {/* Headline & Summary */}
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    Professional Headline
                  </label>
                  <Input
                    name="headline"
                    defaultValue={profile.headline || ""}
                    placeholder="e.g. Final Year B.Tech CSE | Backend & Cloud Systems"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    Professional Bio / Summary
                  </label>
                  <textarea
                    name="summary"
                    rows={4}
                    defaultValue={profile.summary || ""}
                    placeholder="Write a concise overview of your technical background, accomplishments, and career aspirations..."
                    className="w-full text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#4169D8] caret-primary"
                  />
                </div>
              </div>

              {/* Contact & Location */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    Email Address
                  </label>
                  <Input name="email_address" defaultValue={profile.email_address || ""} type="email" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    Phone Number (E.164)
                  </label>
                  <Input name="phone_e164" defaultValue={profile.phone_e164 || ""} placeholder="+91 9876543210" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    Current City
                  </label>
                  <Input name="current_city" defaultValue={profile.current_city || ""} />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    Current State
                  </label>
                  <Input name="current_state" defaultValue={profile.current_state || ""} />
                </div>
              </div>

              {/* Social / Portfolio Links */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    LinkedIn Profile URL
                  </label>
                  <Input name="linkedin_url" defaultValue={profile.linkedin_url || ""} placeholder="https://linkedin.com/in/..." />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    GitHub Profile URL
                  </label>
                  <Input name="github_url" defaultValue={profile.github_url || ""} placeholder="https://github.com/..." />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    Portfolio / Website
                  </label>
                  <Input name="portfolio_url" defaultValue={profile.portfolio_url || ""} placeholder="https://yourdomain.com" />
                </div>
              </div>

              {/* Preferences & Privacy */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    Preferred Job Roles (comma separated)
                  </label>
                  <Input name="preferred_roles" defaultValue={profile.preferred_roles || ""} placeholder="Software Engineer, Cloud Developer, Analyst" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    Preferred Job Locations
                  </label>
                  <Input name="preferred_locations" defaultValue={profile.preferred_locations || ""} placeholder="Bengaluru, Hyderabad, Pune, Remote" />
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    id="is_public_visible"
                    name="is_public_visible"
                    defaultChecked={profile.is_public_visible}
                    className="w-4 h-4 rounded text-[#4169D8] focus:ring-[#4169D8]"
                  />
                  <label htmlFor="is_public_visible" className="text-xs font-medium text-slate-700 dark:text-slate-300">
                    Make profile visible to verified hiring partners and campus recruiters
                  </label>
                </div>

                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    id="consent_placement_rules"
                    name="consent_placement_rules"
                    defaultChecked={profile.consent_placement_rules}
                    className="w-4 h-4 rounded text-[#4169D8] focus:ring-[#4169D8]"
                  />
                  <label htmlFor="consent_placement_rules" className="text-xs font-medium text-slate-700 dark:text-slate-300">
                    I acknowledge campus placement drive terms and eligibility guidelines
                  </label>
                </div>
              </div>
            </form>
          </div>
        )}

        {/* ─── TAB 2: Academic Records ────────────────────────────────────────── */}
        {activeTab === "academics" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  Academic History & Qualifications
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Comprehensive academic records covering secondary (10th), higher secondary (12th), diploma, and degree qualifications.
                </p>
              </div>
              <Button
                onClick={() => setShowAddEduModal(true)}
                className="bg-[#4169D8] hover:bg-[#3355B8] shrink-0"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Qualification
              </Button>
            </div>

            {/* List of Education Qualifications */}
            <div className="grid grid-cols-1 gap-4">
              {profile?.education_records.length === 0 ? (
                <div className="text-center py-12 bg-white dark:bg-slate-900 border border-dashed border-slate-300 dark:border-slate-800 rounded-2xl">
                  <GraduationCap className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                  <p className="text-base font-semibold text-slate-700 dark:text-slate-300">
                    No academic records added yet
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto mt-1 mb-4">
                    Add your Class 10, Class 12 / Diploma, and Undergraduate degree qualifications to qualify for campus placement drives.
                  </p>
                  <Button onClick={() => setShowAddEduModal(true)} variant="outline">
                    Add First Record
                  </Button>
                </div>
              ) : (
                profile?.education_records.map((edu) => (
                  <div
                    key={edu.id}
                    className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm hover:border-slate-300 dark:hover:border-slate-700 transition"
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className="font-semibold text-xs text-[#4169D8] border-[#4169D8]/30">
                            {edu.education_level.replace("_", " ")}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {edu.status}
                          </Badge>
                          {edu.has_backlogs ? (
                            <Badge className="bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20 text-xs">
                              {edu.active_backlogs_count} Active Backlogs
                            </Badge>
                          ) : (
                            <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 text-xs">
                              Zero Backlogs
                            </Badge>
                          )}
                        </div>

                        <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-2">
                          {edu.institution_name}
                        </h3>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          {edu.field_of_study || edu.board_or_university || "General"}
                          {edu.stream_specialization && ` • ${edu.stream_specialization}`}
                        </p>

                        <div className="flex flex-wrap items-center gap-4 mt-3 text-xs text-slate-500 dark:text-slate-400 font-medium">
                          {edu.completion_year && <span>Passing Year: {edu.completion_year}</span>}
                          {edu.percentage && <span>Percentage: {edu.percentage}%</span>}
                          {edu.cgpa && <span>CGPA: {edu.cgpa} / 10.0</span>}
                          {edu.grading_system && <span>Grading: {edu.grading_system}</span>}
                        </div>
                      </div>

                      {/* Document & Actions */}
                      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                        {edu.document_storage_key ? (
                          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-xs font-medium">
                            <FileCheck className="w-4 h-4 text-emerald-600" />
                            <span className="truncate max-w-[140px]">{edu.document_name || "Marksheet Attached"}</span>
                          </div>
                        ) : (
                          <label className="cursor-pointer inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-dashed border-slate-300 dark:border-slate-700 hover:border-[#4169D8] text-xs font-medium text-slate-600 dark:text-slate-400 transition">
                            <Upload className="w-3.5 h-3.5" />
                            <span>Upload Marksheet</span>
                            <input
                              type="file"
                              accept=".pdf,.jpg,.jpeg,.png"
                              className="hidden"
                              onChange={(e) => {
                                const f = e.target.files?.[0];
                                if (f) handleEducationDocUpload(edu.id, f);
                              }}
                            />
                          </label>
                        )}

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteEducation(edu.id)}
                          className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/30"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Modal: Add Education */}
            {showAddEduModal && (
              <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-xl max-h-[90vh] overflow-y-auto">
                  <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3 mb-4">
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">
                      Add Academic Qualification
                    </h3>
                    <button
                      onClick={() => setShowAddEduModal(false)}
                      className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                    >
                      ✕
                    </button>
                  </div>

                  <form onSubmit={handleAddEducationSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          Education Level <span className="text-rose-500">*</span>
                        </label>
                        <select
                          name="education_level"
                          required
                          className="w-full text-sm rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-white"
                        >
                          <option value="CLASS_10">Class 10 / Secondary</option>
                          <option value="CLASS_12">Class 12 / Higher Secondary</option>
                          <option value="DIPLOMA">Diploma / Polytechnic</option>
                          <option value="UNDERGRADUATE">Undergraduate (B.Tech, B.Sc, BCA)</option>
                          <option value="POSTGRADUATE">Postgraduate (M.Tech, MCA, MBA)</option>
                          <option value="DOCTORATE">Doctorate / Ph.D</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          Status
                        </label>
                        <select
                          name="status"
                          className="w-full text-sm rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-white"
                        >
                          <option value="COMPLETED">Completed</option>
                          <option value="PURSUING">Pursuing / In Progress</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                        Institution / School / College Name <span className="text-rose-500">*</span>
                      </label>
                      <Input name="institution_name" required placeholder="e.g. National Institute of Technology" />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          Board / University
                        </label>
                        <Input name="board_or_university" placeholder="e.g. CBSE, ICSE, Anna University" />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          Field of Study / Branch
                        </label>
                        <Input name="field_of_study" placeholder="e.g. Computer Science and Engineering" />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          Grading System
                        </label>
                        <select
                          name="grading_system"
                          className="w-full text-sm rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-white"
                        >
                          <option value="PERCENTAGE">Percentage (%)</option>
                          <option value="CGPA_10">CGPA (10 point)</option>
                          <option value="CGPA_4">CGPA (4 point)</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          Percentage (%)
                        </label>
                        <Input name="percentage" type="number" step="0.01" placeholder="85.50" />
                      </div>

                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          CGPA
                        </label>
                        <Input name="cgpa" type="number" step="0.01" placeholder="8.75" />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          Completion / Passing Year
                        </label>
                        <Input name="completion_year" type="number" placeholder="2026" />
                      </div>

                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          Active Backlogs Count
                        </label>
                        <Input name="active_backlogs_count" type="number" defaultValue="0" />
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 pt-2">
                      <input type="checkbox" id="has_backlogs" name="has_backlogs" className="w-4 h-4 rounded text-[#4169D8]" />
                      <label htmlFor="has_backlogs" className="text-xs font-medium text-slate-700 dark:text-slate-300">
                        Candidate has current or historical backlogs in this program
                      </label>
                    </div>

                    <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                      <Button type="button" variant="ghost" onClick={() => setShowAddEduModal(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" disabled={isSaving} className="bg-[#4169D8] hover:bg-[#3355B8]">
                        {isSaving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                        Save Record
                      </Button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ─── TAB 3: Semester Grade Sheets ───────────────────────────────────── */}
        {activeTab === "semesters" && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                    Semester-Wise Grade Sheets & Performance
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Track SGPA, CGPA progression, registered credits, backlog details, and grade sheet documents.
                  </p>
                </div>

                {/* Qualification Selector */}
                {profile && profile.education_records.length > 0 && (
                  <div className="flex items-center space-x-3">
                    <span className="text-xs font-semibold text-slate-500">Degree:</span>
                    <select
                      value={selectedEducationId || ""}
                      onChange={(e) => setSelectedEducationId(Number(e.target.value))}
                      className="text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2 font-medium text-slate-900 dark:text-white"
                    >
                      {profile.education_records.map((e) => (
                        <option key={e.id} value={e.id}>
                          {e.education_level.replace("_", " ")} - {e.institution_name}
                        </option>
                      ))}
                    </select>

                    <Button
                      onClick={() => setShowAddSemModal(true)}
                      size="sm"
                      className="bg-[#4169D8] hover:bg-[#3355B8] shrink-0"
                    >
                      <Plus className="w-3.5 h-3.5 mr-1" /> Add Semester
                    </Button>
                  </div>
                )}
              </div>
            </div>

            {/* Semester Cards Grid */}
            {!selectedEducation ? (
              <div className="text-center py-12 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
                <p className="text-sm text-slate-500">Please add an Undergraduate or Diploma qualification first.</p>
              </div>
            ) : selectedEducation.semesters.length === 0 ? (
              <div className="text-center py-12 bg-white dark:bg-slate-900 border border-dashed border-slate-300 dark:border-slate-800 rounded-2xl">
                <FileSpreadsheet className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                <p className="text-base font-semibold text-slate-700 dark:text-slate-300">
                  No semester records added for {selectedEducation.institution_name}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4">
                  Add semester grade sheets (Semester 1 through 8) to verify your academic criteria for recruiters.
                </p>
                <Button onClick={() => setShowAddSemModal(true)} variant="outline">
                  Add Semester 1
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {selectedEducation.semesters
                  .sort((a, b) => a.semester_number - b.semester_number)
                  .map((sem) => (
                    <div
                      key={sem.id}
                      className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm hover:border-[#4169D8]/50 transition flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold uppercase tracking-wider text-[#4169D8]">
                            Semester {sem.semester_number}
                          </span>
                          <Badge
                            variant={sem.result_status === "PASS" ? "outline" : "destructive"}
                            className="text-[11px]"
                          >
                            {sem.result_status}
                          </Badge>
                        </div>

                        <div className="grid grid-cols-2 gap-3 mt-4 text-center bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl">
                          <div>
                            <span className="text-[10px] text-slate-500 uppercase font-semibold">SGPA</span>
                            <p className="text-lg font-bold text-slate-900 dark:text-white">
                              {sem.sgpa != null ? sem.sgpa : "—"}
                            </p>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-500 uppercase font-semibold">CGPA</span>
                            <p className="text-lg font-bold text-slate-900 dark:text-white">
                              {sem.cgpa != null ? sem.cgpa : "—"}
                            </p>
                          </div>
                        </div>

                        <div className="mt-3 text-xs text-slate-500 space-y-1">
                          {sem.credits_earned != null && (
                            <p>Credits: {sem.credits_earned} / {sem.credits_registered || "—"}</p>
                          )}
                          {sem.has_backlog && (
                            <p className="text-rose-600 dark:text-rose-400 font-medium">
                              ⚠️ Backlog: {sem.backlog_details || "Active backlog"}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Grade sheet file upload / preview */}
                      <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                        {sem.grade_sheet_storage_key ? (
                          <div className="flex items-center space-x-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span className="truncate max-w-[130px]">{sem.grade_sheet_name || "Grade Sheet"}</span>
                          </div>
                        ) : (
                          <label className="cursor-pointer inline-flex items-center space-x-1 text-xs text-[#4169D8] hover:underline font-medium">
                            <Upload className="w-3.5 h-3.5" />
                            <span>Upload PDF</span>
                            <input
                              type="file"
                              accept=".pdf,.jpg,.jpeg,.png"
                              className="hidden"
                              onChange={(e) => {
                                const f = e.target.files?.[0];
                                if (f) handleSemesterDocUpload(sem.semester_number, f);
                              }}
                            />
                          </label>
                        )}

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteSemester(sem.id)}
                          className="text-slate-400 hover:text-rose-600 p-1 h-auto"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))}
              </div>
            )}

            {/* Modal: Add Semester */}
            {showAddSemModal && (
              <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl">
                  <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3 mb-4">
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">
                      Add Semester Grade Record
                    </h3>
                    <button
                      onClick={() => setShowAddSemModal(false)}
                      className="text-slate-400 hover:text-slate-600"
                    >
                      ✕
                    </button>
                  </div>

                  <form onSubmit={handleAddSemesterSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          Semester # (1 - 10) <span className="text-rose-500">*</span>
                        </label>
                        <Input name="semester_number" type="number" min="1" max="10" required defaultValue="1" />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          Result Status
                        </label>
                        <select
                          name="result_status"
                          className="w-full text-sm rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-white"
                        >
                          <option value="PASS">PASS</option>
                          <option value="FAIL">FAIL</option>
                          <option value="AWAITED">AWAITED</option>
                          <option value="ARREAR">ARREAR</option>
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          SGPA
                        </label>
                        <Input name="sgpa" type="number" step="0.01" min="0" max="10" placeholder="8.65" />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          Cumulative CGPA
                        </label>
                        <Input name="cgpa" type="number" step="0.01" min="0" max="10" placeholder="8.70" />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          Credits Registered
                        </label>
                        <Input name="credits_registered" type="number" step="0.5" placeholder="24" />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                          Credits Earned
                        </label>
                        <Input name="credits_earned" type="number" step="0.5" placeholder="24" />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="has_backlog" name="has_backlog" className="w-4 h-4 rounded text-[#4169D8]" />
                        <label htmlFor="has_backlog" className="text-xs font-medium text-slate-700 dark:text-slate-300">
                          Semester has uncleared backlogs
                        </label>
                      </div>
                      <Input name="backlog_details" placeholder="e.g. Data Structures (CS201)" />
                    </div>

                    <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                      <Button type="button" variant="ghost" onClick={() => setShowAddSemModal(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" disabled={isSaving} className="bg-[#4169D8] hover:bg-[#3355B8]">
                        Save Semester
                      </Button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ─── TAB 4: Resume Manager ──────────────────────────────────────────── */}
        {activeTab === "resumes" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  Resume Versioning & Snapshot Manager
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Upload multiple tailored resumes. Job applications capture an immutable snapshot of the submitted version.
                </p>
              </div>

              <div>
                <Button
                  onClick={() => resumeInputRef.current?.click()}
                  className="bg-[#4169D8] hover:bg-[#3355B8]"
                >
                  <Upload className="w-4 h-4 mr-2" /> Upload Resume Version
                </Button>
                <input
                  type="file"
                  ref={resumeInputRef}
                  onChange={handleResumeUpload}
                  accept=".pdf,.doc,.docx"
                  className="hidden"
                />
              </div>
            </div>

            {/* Resumes List */}
            <div className="grid grid-cols-1 gap-4">
              {profile?.resumes.length === 0 ? (
                <div className="text-center py-12 bg-white dark:bg-slate-900 border border-dashed border-slate-300 dark:border-slate-800 rounded-2xl">
                  <FileText className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                  <p className="text-base font-semibold text-slate-700 dark:text-slate-300">
                    No resumes uploaded yet
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4">
                    Upload your primary resume (PDF format recommended, max 10MB) to apply for campus job openings.
                  </p>
                  <Button onClick={() => resumeInputRef.current?.click()} variant="outline">
                    Upload Resume Now
                  </Button>
                </div>
              ) : (
                profile?.resumes.map((res) => (
                  <div
                    key={res.id}
                    className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="flex items-start space-x-4">
                      <div className="w-12 h-12 rounded-xl bg-[#4169D8]/10 text-[#4169D8] flex items-center justify-center shrink-0">
                        <FileText className="w-6 h-6" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="text-base font-bold text-slate-900 dark:text-white">
                            {res.resume_title}
                          </h3>
                          {res.is_default && (
                            <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 text-xs">
                              Default Resume
                            </Badge>
                          )}
                          <Badge variant="outline" className="text-xs">
                            {res.versions.length} {res.versions.length === 1 ? "Version" : "Versions"}
                          </Badge>
                        </div>

                        {/* Latest Version Details */}
                        {res.versions.length > 0 && (
                          <div className="mt-2 text-xs text-slate-500 space-y-1">
                            <p>
                              Latest: <span className="font-medium text-slate-700 dark:text-slate-300">{res.versions[0].file_name}</span> (v{res.versions[0].version_number})
                              {res.versions[0].file_size_bytes && (
                                <span> • {(res.versions[0].file_size_bytes / 1024).toFixed(0)} KB</span>
                              )}
                            </p>
                            <p>Uploaded: {formatDate(res.versions[0].created_at)}</p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      {!res.is_default && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSetDefaultResume(res.id)}
                          className="text-xs"
                        >
                          Set as Default
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteResume(res.id)}
                        className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/30"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* ─── TAB 5: Document Vault ──────────────────────────────────────────── */}
        {activeTab === "documents" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  Candidate Document Vault
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Secure cryptographic document storage with SHA-256 verification (Government ID, Transcripts, Certificates).
                </p>
              </div>

              <Button
                onClick={() => setShowUploadDocModal(true)}
                className="bg-[#4169D8] hover:bg-[#3355B8]"
              >
                <Upload className="w-4 h-4 mr-2" /> Upload to Vault
              </Button>
            </div>

            {/* Documents Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {profile?.documents.length === 0 ? (
                <div className="col-span-full text-center py-12 bg-white dark:bg-slate-900 border border-dashed border-slate-300 dark:border-slate-800 rounded-2xl">
                  <Layers className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                  <p className="text-base font-semibold text-slate-700 dark:text-slate-300">
                    No documents stored in vault
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4">
                    Upload transcripts, caste/income certificates, or ID proofs required by campus recruiters.
                  </p>
                  <Button onClick={() => setShowUploadDocModal(true)} variant="outline">
                    Add Document
                  </Button>
                </div>
              ) : (
                profile?.documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <Badge variant="outline" className="text-xs font-semibold text-[#4169D8]">
                          {doc.document_category.replace(/_/g, " ")}
                        </Badge>
                        {doc.is_verified ? (
                          <span className="text-[11px] text-emerald-600 flex items-center">
                            <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Verified
                          </span>
                        ) : (
                          <span className="text-[11px] text-slate-400">Submitted</span>
                        )}
                      </div>

                      <h4 className="text-sm font-bold text-slate-900 dark:text-white mt-3 truncate">
                        {doc.title}
                      </h4>
                      <p className="text-xs text-slate-500 truncate mt-0.5">{doc.file_name}</p>

                      <div className="mt-3 bg-slate-50 dark:bg-slate-800/40 p-2.5 rounded-lg space-y-1 text-[11px] text-slate-500">
                        <p>Size: {(doc.file_size_bytes / 1024).toFixed(0)} KB</p>
                        <p className="font-mono text-[10px] truncate" title={doc.content_sha256}>
                          SHA: {doc.content_sha256.substring(0, 16)}...
                        </p>
                        <p>Uploaded: {formatDate(doc.created_at)}</p>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteVaultDocument(doc.id)}
                        className="text-rose-600 hover:text-rose-700 hover:bg-rose-50"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Modal: Upload Document */}
            {showUploadDocModal && (
              <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl">
                  <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3 mb-4">
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">
                      Upload Document to Vault
                    </h3>
                    <button onClick={() => setShowUploadDocModal(false)} className="text-slate-400 hover:text-slate-600">
                      ✕
                    </button>
                  </div>

                  <form onSubmit={handleDocumentVaultUpload} className="space-y-4">
                    <div>
                      <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                        Document Category <span className="text-rose-500">*</span>
                      </label>
                      <select
                        name="category"
                        required
                        className="w-full text-sm rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-white"
                      >
                        <option value="TRANSCRIPT">Consolidated Transcript</option>
                        <option value="DEGREE_CERTIFICATE">Provisional / Degree Certificate</option>
                        <option value="CLASS_10_MARKSHEET">Class 10 Marksheet</option>
                        <option value="CLASS_12_MARKSHEET">Class 12 Marksheet</option>
                        <option value="DIPLOMA_CERTIFICATE">Diploma Certificate</option>
                        <option value="CERTIFICATE">Government ID / Extracurricular</option>
                        <option value="OTHER">Other Verification Document</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                        Document Title <span className="text-rose-500">*</span>
                      </label>
                      <Input name="title" required placeholder="e.g. Official B.Tech 6-Semester Transcript" />
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                        File (PDF, PNG, JPG - max 15MB) <span className="text-rose-500">*</span>
                      </label>
                      <Input name="doc_file" type="file" required accept=".pdf,.png,.jpg,.jpeg" />
                    </div>

                    <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                      <Button type="button" variant="ghost" onClick={() => setShowUploadDocModal(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" disabled={isSaving} className="bg-[#4169D8] hover:bg-[#3355B8]">
                        {isSaving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                        Store Document
                      </Button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ─── TAB 6: Skills, Projects, Experience & Certifications ───────────── */}
        {activeTab === "skills_projects" && (
          <div className="space-y-8">
            {/* Section A: Skills */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4 mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center">
                    <Code className="w-4 h-4 mr-2 text-[#4169D8]" /> Technical & Domain Skills
                  </h3>
                  <p className="text-xs text-slate-500">Skills are matched against job requirements during automated shortlisting.</p>
                </div>
                <Button size="sm" onClick={() => setShowAddSkillModal(true)} variant="outline">
                  <Plus className="w-3.5 h-3.5 mr-1" /> Add Skill
                </Button>
              </div>

              <div className="flex flex-wrap gap-2">
                {profile?.skills.length === 0 ? (
                  <p className="text-xs text-slate-500 py-3">No skills listed yet. Add your core technical competencies.</p>
                ) : (
                  profile?.skills.map((s) => (
                    <div
                      key={s.id}
                      className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 text-xs font-medium text-slate-800 dark:text-slate-200"
                    >
                      <span>{s.skill_name}</span>
                      <span className="text-[10px] text-slate-400">({s.proficiency_level})</span>
                      <button
                        onClick={async () => {
                          await deleteSkill(s.id);
                          await refreshProfileData();
                        }}
                        className="text-slate-400 hover:text-rose-500 ml-1"
                      >
                        ✕
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Section B: Projects */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4 mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center">
                    <FolderGit2 className="w-4 h-4 mr-2 text-[#4169D8]" /> Projects & Repositories
                  </h3>
                  <p className="text-xs text-slate-500">Showcase technical systems, open source tools, or engineering projects.</p>
                </div>
                <Button size="sm" onClick={() => setShowAddProjectModal(true)} variant="outline">
                  <Plus className="w-3.5 h-3.5 mr-1" /> Add Project
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {profile?.projects.length === 0 ? (
                  <p className="col-span-full text-xs text-slate-500 py-3">No projects recorded yet.</p>
                ) : (
                  profile?.projects.map((p) => (
                    <div
                      key={p.id}
                      className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-bold text-slate-900 dark:text-white">{p.project_name}</h4>
                          <button
                            onClick={async () => {
                              await deleteProject(p.id);
                              await refreshProfileData();
                            }}
                            className="text-slate-400 hover:text-rose-500"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        {p.role_description && (
                          <p className="text-xs font-medium text-[#4169D8] mt-0.5">{p.role_description}</p>
                        )}
                        {p.description && (
                          <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 line-clamp-3">{p.description}</p>
                        )}
                        {p.technologies && (
                          <p className="text-[11px] text-slate-500 font-mono mt-2">Tech: {p.technologies}</p>
                        )}
                      </div>
                      {p.project_url && (
                        <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800">
                          <a
                            href={p.project_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs text-[#4169D8] hover:underline inline-flex items-center"
                          >
                            View Repository <ExternalLink className="w-3 h-3 ml-1" />
                          </a>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Section C: Work Experience & Internships */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4 mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center">
                    <Briefcase className="w-4 h-4 mr-2 text-[#4169D8]" /> Work Experience & Internships
                  </h3>
                  <p className="text-xs text-slate-500">Industry internships, research assistantships, or professional roles.</p>
                </div>
                <Button size="sm" onClick={() => setShowAddExpModal(true)} variant="outline">
                  <Plus className="w-3.5 h-3.5 mr-1" /> Add Experience
                </Button>
              </div>

              <div className="space-y-4">
                {profile?.work_experiences.length === 0 ? (
                  <p className="text-xs text-slate-500 py-3">No work experience or internships recorded.</p>
                ) : (
                  profile?.work_experiences.map((exp) => (
                    <div
                      key={exp.id}
                      className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 flex justify-between items-start"
                    >
                      <div>
                        <h4 className="text-sm font-bold text-slate-900 dark:text-white">{exp.job_title}</h4>
                        <p className="text-xs font-medium text-slate-600 dark:text-slate-400">
                          {exp.employer_name} • {exp.start_date} to {exp.is_current ? "Present" : exp.end_date || "—"}
                        </p>
                        {exp.description && (
                          <p className="text-xs text-slate-500 mt-2">{exp.description}</p>
                        )}
                      </div>
                      <button
                        onClick={async () => {
                          await deleteWorkExperience(exp.id);
                          await refreshProfileData();
                        }}
                        className="text-slate-400 hover:text-rose-500"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Section D: Certifications */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4 mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center">
                    <Award className="w-4 h-4 mr-2 text-[#4169D8]" /> Professional Certifications
                  </h3>
                  <p className="text-xs text-slate-500">Cloud, security, machine learning, or professional credentials.</p>
                </div>
                <Button size="sm" onClick={() => setShowAddCertModal(true)} variant="outline">
                  <Plus className="w-3.5 h-3.5 mr-1" /> Add Certificate
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {profile?.certifications.length === 0 ? (
                  <p className="col-span-full text-xs text-slate-500 py-3">No certifications listed.</p>
                ) : (
                  profile?.certifications.map((c) => (
                    <div
                      key={c.id}
                      className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 flex justify-between items-start"
                    >
                      <div>
                        <h4 className="text-sm font-bold text-slate-900 dark:text-white">{c.name}</h4>
                        <p className="text-xs text-slate-500">{c.issuing_organisation}</p>
                        {c.credential_id && (
                          <p className="text-[11px] font-mono text-slate-400 mt-1">ID: {c.credential_id}</p>
                        )}
                      </div>
                      <button
                        onClick={async () => {
                          await deleteCertification(c.id);
                          await refreshProfileData();
                        }}
                        className="text-slate-400 hover:text-rose-500"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Modals for Skills, Projects, Experience, Certs */}
            {showAddSkillModal && (
              <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
                <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-sm w-full p-6 shadow-xl border border-slate-200 dark:border-slate-800">
                  <h4 className="text-sm font-bold mb-3">Add Skill</h4>
                  <form onSubmit={handleAddSkillSubmit} className="space-y-3">
                    <Input name="skill_name" required placeholder="e.g. Python, React, PostgreSQL" />
                    <select name="proficiency_level" className="w-full text-sm rounded-lg border p-2">
                      <option value="INTERMEDIATE">Intermediate</option>
                      <option value="EXPERT">Expert</option>
                      <option value="BEGINNER">Beginner</option>
                    </select>
                    <div className="flex justify-end space-x-2 pt-2">
                      <Button type="button" variant="ghost" size="sm" onClick={() => setShowAddSkillModal(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" size="sm" className="bg-[#4169D8]">Add</Button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {showAddProjectModal && (
              <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
                <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 dark:border-slate-800">
                  <h4 className="text-sm font-bold mb-3">Add Engineering Project</h4>
                  <form onSubmit={handleAddProjectSubmit} className="space-y-3">
                    <Input name="project_name" required placeholder="Project Title" />
                    <Input name="role_description" placeholder="Your Role (e.g. Full Stack Developer)" />
                    <Input name="technologies" placeholder="Technologies (e.g. Next.js, FastAPI, PostgreSQL)" />
                    <Input name="project_url" placeholder="Repository or Demo URL" />
                    <textarea name="description" rows={3} placeholder="Project overview..." className="w-full text-sm rounded-lg border p-2" />
                    <div className="flex justify-end space-x-2 pt-2">
                      <Button type="button" variant="ghost" size="sm" onClick={() => setShowAddProjectModal(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" size="sm" className="bg-[#4169D8]">Save Project</Button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {showAddExpModal && (
              <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
                <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 dark:border-slate-800">
                  <h4 className="text-sm font-bold mb-3">Add Work Experience</h4>
                  <form onSubmit={handleAddExpSubmit} className="space-y-3">
                    <Input name="employer_name" required placeholder="Company / Organization Name" />
                    <Input name="job_title" required placeholder="Job Title / Role" />
                    <div className="grid grid-cols-2 gap-2">
                      <Input name="start_date" type="date" required />
                      <Input name="end_date" type="date" />
                    </div>
                    <div className="flex items-center space-x-2">
                      <input type="checkbox" id="is_current" name="is_current" className="rounded" />
                      <label htmlFor="is_current" className="text-xs">Currently working here</label>
                    </div>
                    <textarea name="description" rows={3} placeholder="Key responsibilities and achievements..." className="w-full text-sm rounded-lg border p-2" />
                    <div className="flex justify-end space-x-2 pt-2">
                      <Button type="button" variant="ghost" size="sm" onClick={() => setShowAddExpModal(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" size="sm" className="bg-[#4169D8]">Save</Button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {showAddCertModal && (
              <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
                <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-sm w-full p-6 shadow-xl border border-slate-200 dark:border-slate-800">
                  <h4 className="text-sm font-bold mb-3">Add Certification</h4>
                  <form onSubmit={handleAddCertSubmit} className="space-y-3">
                    <Input name="name" required placeholder="Certification Name" />
                    <Input name="issuing_organisation" required placeholder="Issuer (e.g. AWS, Google)" />
                    <Input name="credential_id" placeholder="Credential ID (optional)" />
                    <Input name="credential_url" placeholder="Verification URL (optional)" />
                    <div className="flex justify-end space-x-2 pt-2">
                      <Button type="button" variant="ghost" size="sm" onClick={() => setShowAddCertModal(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" size="sm" className="bg-[#4169D8]">Save</Button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
