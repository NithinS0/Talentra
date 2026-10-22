"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Briefcase,
  Building,
  MapPin,
  Clock,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Users,
  Send,
  Loader2,
  GraduationCap,
  FileText,
  Check,
  X,
  HelpCircle,
  ExternalLink,
  ShieldCheck,
  Award,
} from "lucide-react";
import { getJobDetails, updateJobStatus, getJobApplications, getJobEligibility } from "@/lib/api/jobs";
import { applyToJob } from "@/lib/api/applications";
import { getMyCandidateProfile } from "@/lib/api/candidates";
import { JobResponse, JobEligibilityResponse } from "@/types/jobs";
import { ApplicationResponse } from "@/types/applications";
import { CandidateFullProfile } from "@/types/candidate";
import { useAuth } from "@/lib/auth/context";
import { formatDate } from "@/lib/utils";

interface PageProps {
  params: Promise<{ jobId: string }>;
}

export default function JobDetailPage({ params }: PageProps) {
  const router = useRouter();
  const { activeRole } = useAuth();
  const resolvedParams = use(params);
  const jobId = parseInt(resolvedParams.jobId, 10);

  const [job, setJob] = useState<JobResponse | null>(null);
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [eligibility, setEligibility] = useState<JobEligibilityResponse | null>(null);
  const [candidateProfile, setCandidateProfile] = useState<CandidateFullProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Application submission modal state
  const [isApplying, setIsApplying] = useState(false);
  const [coverLetter, setCoverLetter] = useState("");
  const [selectedResumeVersionId, setSelectedResumeVersionId] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedApplication, setSubmittedApplication] = useState<ApplicationResponse | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);

  // Status transition state
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function fetchJobAndRelated() {
      if (isNaN(jobId)) {
        setError("Invalid Job ID");
        setIsLoading(false);
        return;
      }

      try {
        const jobData = await getJobDetails(jobId);
        if (isMounted) setJob(jobData);

        // If candidate, evaluate eligibility and fetch profile resumes
        if (activeRole === "CANDIDATE") {
          try {
            const [eligData, profData] = await Promise.allSettled([
              getJobEligibility(jobId),
              getMyCandidateProfile(),
            ]);

            if (isMounted) {
              if (eligData.status === "fulfilled") {
                setEligibility(eligData.value);
              }
              if (profData.status === "fulfilled") {
                setCandidateProfile(profData.value);
                // Pre-select default resume version if available
                const defaultResume = profData.value.resumes.find((r) => r.is_default && r.versions?.length > 0);
                if (defaultResume && defaultResume.versions?.length > 0) {
                  setSelectedResumeVersionId(defaultResume.versions[0].id);
                } else if (profData.value.resumes.length > 0 && profData.value.resumes[0].versions?.length > 0) {
                  setSelectedResumeVersionId(profData.value.resumes[0].versions[0].id);
                }
              }
            }
          } catch {
            // Non-critical if candidate evaluation fails to load
          }
        }

        // If employer or recruiter, fetch applications
        if (["EMPLOYER", "RECRUITER", "SUPER_ADMIN", "ACCOUNT_ADMIN"].includes(activeRole)) {
          try {
            const appsData = await getJobApplications(jobId);
            if (isMounted) setApplications(appsData.items || []);
          } catch {
            // Non-critical if user lacks org permissions for this specific job
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load job requirement");
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    fetchJobAndRelated();
    return () => {
      isMounted = false;
    };
  }, [jobId, activeRole]);

  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setApplyError(null);

    try {
      const app = await applyToJob(jobId, {
        cover_letter: coverLetter.trim() || undefined,
        resume_version_id: selectedResumeVersionId || undefined,
      });
      setSubmittedApplication(app);
      setIsApplying(false);
    } catch (err: unknown) {
      setApplyError(err instanceof Error ? err.message : "Failed to submit application");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStatusChange = async (targetStatus: string) => {
    setIsUpdatingStatus(true);
    try {
      const updated = await updateJobStatus(jobId, { status: targetStatus });
      setJob(updated);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to update status");
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const isCandidate = activeRole === "CANDIDATE";
  const canManage = ["EMPLOYER", "RECRUITER", "SUPER_ADMIN", "ACCOUNT_ADMIN"].includes(activeRole);

  // Flatten candidate available resume versions for selector
  const availableResumeVersions: {
    versionId: number;
    resumeTitle: string;
    fileName: string;
    versionNumber: number;
    isDefault: boolean;
    uploadedAt: string;
  }[] = [];

  if (candidateProfile?.resumes) {
    for (const res of candidateProfile.resumes) {
      for (const ver of res.versions || []) {
        availableResumeVersions.push({
          versionId: ver.id,
          resumeTitle: res.resume_title,
          fileName: ver.file_name || `Resume v${ver.version_number}.pdf`,
          versionNumber: ver.version_number,
          isDefault: res.is_default,
          uploadedAt: ver.created_at,
        });
      }
    }
  }

  if (isLoading) {
    return (
      <DashboardShell title="Job Details" breadcrumbs={[{ label: "Jobs", href: "/jobs" }, { label: `Job #${jobId}` }]}>
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      </DashboardShell>
    );
  }

  if (error || !job) {
    return (
      <DashboardShell title="Job Details" breadcrumbs={[{ label: "Jobs", href: "/jobs" }, { label: "Error" }]}>
        <Card className="border-red-200 dark:border-red-900/50">
          <CardContent className="pt-6 text-center space-y-4">
            <AlertCircle className="h-10 w-10 text-red-500 mx-auto" />
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Job Requirement Not Found</h2>
            <p className="text-sm text-slate-500">{error || "The requested job does not exist or has been removed."}</p>
            <Button onClick={() => router.push("/jobs")} variant="outline" className="gap-2">
              <ArrowLeft className="h-4 w-4" /> Back to Jobs Directory
            </Button>
          </CardContent>
        </Card>
      </DashboardShell>
    );
  }

  const jobTitle = job.job_title || job.title || "Job Requirement";
  const jobStatus = job.status || job.status_code || "DRAFT";
  const publishState = job.publish_state || job.publish_status_code || "UNPUBLISHED";
  const isJobOpen = jobStatus === "OPEN" && publishState === "PUBLISHED";

  return (
    <DashboardShell
      title={jobTitle}
      breadcrumbs={[
        { label: "Jobs", href: "/jobs" },
        { label: jobTitle },
      ]}
    >
      <div className="space-y-6">
        {/* Navigation & Status Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <Button onClick={() => router.push("/jobs")} variant="outline" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" /> Back to Jobs
          </Button>

          <div className="flex items-center gap-2">
            <Badge variant={jobStatus === "OPEN" ? "default" : "outline"} className={jobStatus === "OPEN" ? "bg-emerald-600 text-white" : ""}>
              {jobStatus}
            </Badge>
            <Badge variant="outline" className="text-xs">{publishState}</Badge>
            {job.positions_count && job.positions_count > 0 && (
              <Badge variant="outline" className="text-xs bg-slate-50 dark:bg-slate-800">
                {job.positions_count} Openings
              </Badge>
            )}
          </div>
        </div>

        {/* Application Success Banner */}
        {submittedApplication && (
          <div className="p-5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 flex items-start gap-3.5 text-emerald-900 dark:text-emerald-200 shadow-xs">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold text-sm">Application submitted successfully! (ID: #{submittedApplication.id})</p>
              <p className="text-xs text-emerald-700 dark:text-emerald-300">
                Submitted with resume snapshot: <span className="font-mono font-medium">{submittedApplication.resume_snapshot_file_name || submittedApplication.resume_snapshot_title || "Standard Resume"}</span>.
                Your profile details have been securely recorded for employer review.
              </p>
            </div>
          </div>
        )}

        {/* Job Primary Card */}
        <Card className="border border-slate-200 dark:border-slate-800 shadow-xs">
          <CardHeader>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <CardTitle className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {jobTitle}
                </CardTitle>
                <CardDescription className="flex items-center gap-2 mt-1.5 text-sm text-slate-600 dark:text-slate-400">
                  <Building className="h-4 w-4 text-slate-400" />
                  <span className="font-medium text-slate-700 dark:text-slate-200">
                    {job.organisation_name || `Organisation #${job.organisation_id}`}
                  </span>
                  {job.location_city && (
                    <>
                      <span>·</span>
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5" />
                        {job.location_city}{job.location_country ? `, ${job.location_country}` : ""}
                      </span>
                    </>
                  )}
                </CardDescription>
              </div>

              {isCandidate && !submittedApplication && (
                <div className="flex flex-col sm:flex-row items-end gap-2">
                  <Button
                    onClick={() => setIsApplying(true)}
                    className="gap-2 bg-[#4169D8] hover:bg-[#3254B8] text-white shadow-xs"
                    size="lg"
                    disabled={!isJobOpen}
                  >
                    <Send className="h-4 w-4" />
                    {isJobOpen ? "Apply to Requirement" : "Applications Closed"}
                  </Button>
                </div>
              )}

              {canManage && (
                <div className="flex items-center gap-2">
                  {jobStatus === "OPEN" ? (
                    <Button
                      onClick={() => handleStatusChange("CLOSED")}
                      variant="outline"
                      size="sm"
                      disabled={isUpdatingStatus}
                    >
                      Close Job
                    </Button>
                  ) : (
                    <Button
                      onClick={() => handleStatusChange("OPEN")}
                      variant="outline"
                      size="sm"
                      disabled={isUpdatingStatus}
                    >
                      Re-open Job
                    </Button>
                  )}
                </div>
              )}
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Meta attributes */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50 dark:bg-[#0E121B] border border-slate-100 dark:border-slate-800 text-sm">
              <div>
                <span className="text-[11px] uppercase tracking-wider text-slate-400 block font-semibold">Work Arrangement</span>
                <span className="font-semibold text-slate-700 dark:text-slate-200">
                  {job.work_type || job.work_type_name || "On-site"}
                </span>
              </div>
              <div>
                <span className="text-[11px] uppercase tracking-wider text-slate-400 block font-semibold">Employment Type</span>
                <span className="font-semibold text-slate-700 dark:text-slate-200">
                  {job.employment_type || job.employment_type_name || "Full-time"}
                </span>
              </div>
              <div>
                <span className="text-[11px] uppercase tracking-wider text-slate-400 block font-semibold">Compensation</span>
                <span className="font-semibold text-slate-700 dark:text-slate-200">
                  {job.salary_min && job.salary_max
                    ? `${job.salary_currency_code || "INR"} ${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}`
                    : "Competitive / Disclosed on Interview"}
                </span>
              </div>
              <div>
                <span className="text-[11px] uppercase tracking-wider text-slate-400 block font-semibold">Application Deadline</span>
                <span className="font-semibold text-slate-700 dark:text-slate-200">
                  {job.application_deadline ? formatDate(job.application_deadline) : "Open Until Filled"}
                </span>
              </div>
            </div>

            {/* Description */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Job Overview & Position Summary
              </h3>
              <div className="prose dark:prose-invert max-w-none text-slate-800 dark:text-slate-200 text-sm whitespace-pre-line leading-relaxed">
                {job.description || job.job_description}
              </div>
            </div>

            {/* Responsibilities */}
            {job.responsibilities && (
              <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Key Responsibilities
                </h3>
                <div className="text-sm text-slate-800 dark:text-slate-200 whitespace-pre-line leading-relaxed">
                  {job.responsibilities}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Structured Placement & Eligibility Criteria Card */}
        <Card className="border border-slate-200 dark:border-slate-800 shadow-xs">
          <CardHeader>
            <div className="flex items-center gap-2">
              <GraduationCap className="h-5 w-5 text-[#4169D8]" />
              <div>
                <CardTitle className="text-lg font-bold">Structured Placement & Eligibility Criteria</CardTitle>
                <CardDescription className="text-xs">
                  Automated shortlisting rules configured by the employer for this campus / corporate drive.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="p-3.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-[#0E121B]">
                <span className="text-[11px] text-slate-500 block font-semibold uppercase">Required Qualifications</span>
                <span className="text-sm font-semibold text-slate-900 dark:text-white">
                  {job.required_qualifications || "Any Graduate / Relevant Degree"}
                </span>
              </div>

              <div className="p-3.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-[#0E121B]">
                <span className="text-[11px] text-slate-500 block font-semibold uppercase">Accepted Branches / Streams</span>
                <span className="text-sm font-semibold text-slate-900 dark:text-white">
                  {job.accepted_branches || "All Engineering & Technical Disciplines"}
                </span>
              </div>

              <div className="p-3.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-[#0E121B]">
                <span className="text-[11px] text-slate-500 block font-semibold uppercase">Academic Cutoff</span>
                <span className="text-sm font-semibold text-slate-900 dark:text-white">
                  {job.min_cgpa ? `Min ${job.min_cgpa.toFixed(2)} CGPA` : ""}
                  {job.min_cgpa && job.min_percentage ? " or " : ""}
                  {job.min_percentage ? `Min ${job.min_percentage.toFixed(1)}% Marks` : ""}
                  {!job.min_cgpa && !job.min_percentage ? "No minimum cutoff specified" : ""}
                </span>
              </div>

              <div className="p-3.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-[#0E121B]">
                <span className="text-[11px] text-slate-500 block font-semibold uppercase">Backlogs / Arrears Policy</span>
                <span className="text-sm font-semibold text-slate-900 dark:text-white">
                  {job.allow_backlogs
                    ? `Allowed (Max ${job.max_active_backlogs ?? 0} active)`
                    : "Zero Active Backlogs Required"}
                </span>
              </div>

              <div className="p-3.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-[#0E121B]">
                <span className="text-[11px] text-slate-500 block font-semibold uppercase">Experience Requirement</span>
                <span className="text-sm font-semibold text-slate-900 dark:text-white">
                  {job.min_experience_years !== null && job.min_experience_years !== undefined
                    ? `${job.min_experience_years} to ${job.max_experience_years ?? "Any"} Years`
                    : "Fresher / Entry-Level Eligible"}
                </span>
              </div>

              <div className="p-3.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-[#0E121B]">
                <span className="text-[11px] text-slate-500 block font-semibold uppercase">Required Documents</span>
                <span className="text-sm font-semibold text-slate-900 dark:text-white">
                  {job.required_documents || "Standard Resume"}
                </span>
              </div>
            </div>

            {/* Skills Tags */}
            {(job.required_skills || job.preferred_skills) && (
              <div className="space-y-3 pt-2">
                {job.required_skills && (
                  <div>
                    <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 block mb-1.5">
                      Mandatory Core Skills:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {job.required_skills.split(",").map((s, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs bg-[#4169D8]/10 text-[#4169D8] border-[#4169D8]/30 font-medium">
                          {s.trim()}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {job.preferred_skills && (
                  <div>
                    <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 block mb-1.5">
                      Preferred / Good-to-Have Skills:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {job.preferred_skills.split(",").map((s, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                          {s.trim()}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Candidate Interactive Eligibility Assessment Card */}
        {isCandidate && (
          <Card className="border border-slate-200 dark:border-slate-800 shadow-xs overflow-hidden">
            <CardHeader className="bg-slate-50/50 dark:bg-slate-900/40 border-b border-slate-100 dark:border-slate-800">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-[#4169D8]" />
                  <div>
                    <CardTitle className="text-lg font-bold">Your Eligibility Assessment</CardTitle>
                    <CardDescription className="text-xs">
                      Evaluated in real-time from your saved profile, academic records, and document vault.
                    </CardDescription>
                  </div>
                </div>

                {eligibility && (
                  <Badge
                    className={
                      eligibility.overall_status === "ELIGIBLE"
                        ? "bg-emerald-600 text-white font-semibold text-xs px-3 py-1"
                        : eligibility.overall_status === "NOT_ELIGIBLE"
                        ? "bg-rose-600 text-white font-semibold text-xs px-3 py-1"
                        : "bg-amber-600 text-white font-semibold text-xs px-3 py-1"
                    }
                  >
                    {eligibility.overall_status === "ELIGIBLE" && "STATUS: ELIGIBLE TO APPLY"}
                    {eligibility.overall_status === "NOT_ELIGIBLE" && "STATUS: NOT ELIGIBLE"}
                    {eligibility.overall_status === "UNABLE_TO_DETERMINE" && "STATUS: UNABLE TO DETERMINE"}
                  </Badge>
                )}
              </div>
            </CardHeader>

            <CardContent className="pt-6 space-y-6">
              {eligibility ? (
                <>
                  {/* Status Banner */}
                  <div
                    className={
                      eligibility.overall_status === "ELIGIBLE"
                        ? "p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 flex items-start gap-3"
                        : eligibility.overall_status === "NOT_ELIGIBLE"
                        ? "p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 flex items-start gap-3"
                        : "p-4 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 flex items-start gap-3"
                    }
                  >
                    {eligibility.overall_status === "ELIGIBLE" && (
                      <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                    )}
                    {eligibility.overall_status === "NOT_ELIGIBLE" && (
                      <AlertCircle className="h-5 w-5 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
                    )}
                    {eligibility.overall_status === "UNABLE_TO_DETERMINE" && (
                      <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                    )}
                    <div className="space-y-1">
                      <p
                        className={
                          eligibility.overall_status === "ELIGIBLE"
                            ? "font-semibold text-sm text-emerald-900 dark:text-emerald-200"
                            : eligibility.overall_status === "NOT_ELIGIBLE"
                            ? "font-semibold text-sm text-rose-900 dark:text-rose-200"
                            : "font-semibold text-sm text-amber-900 dark:text-amber-200"
                        }
                      >
                        {eligibility.overall_status === "ELIGIBLE" && "You meet all configured eligibility criteria for this role."}
                        {eligibility.overall_status === "NOT_ELIGIBLE" && "Your profile does not satisfy one or more mandatory requirements."}
                        {eligibility.overall_status === "UNABLE_TO_DETERMINE" && "Missing profile information prevents automated eligibility verification."}
                      </p>
                      <p className="text-xs text-slate-600 dark:text-slate-400">
                        {eligibility.overall_status === "ELIGIBLE"
                          ? "You can proceed to apply using any of your verified resume versions."
                          : "Review the detailed criteria table below to identify unmet cutoffs or missing academic marks."}
                      </p>
                    </div>
                  </div>

                  {/* Detailed Criteria Table */}
                  <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-slate-50 dark:bg-slate-900">
                          <TableHead className="font-semibold text-xs">Criterion</TableHead>
                          <TableHead className="font-semibold text-xs">Job Cutoff / Requirement</TableHead>
                          <TableHead className="font-semibold text-xs">Your Profile Value</TableHead>
                          <TableHead className="font-semibold text-xs">Status</TableHead>
                          <TableHead className="font-semibold text-xs">Evaluation Note</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {eligibility.criteria.map((crit, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="font-medium text-xs text-slate-900 dark:text-white">
                              {crit.criterion}
                            </TableCell>
                            <TableCell className="text-xs text-slate-700 dark:text-slate-300 font-mono">
                              {crit.required_value}
                            </TableCell>
                            <TableCell className="text-xs text-slate-600 dark:text-slate-400 font-mono">
                              {crit.candidate_value || "—"}
                            </TableCell>
                            <TableCell>
                              {crit.status === "SATISFIED" && (
                                <Badge className="bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30 text-[11px] gap-1 font-medium">
                                  <Check className="h-3 w-3" /> Satisfied
                                </Badge>
                              )}
                              {crit.status === "UNSATISFIED" && (
                                <Badge className="bg-rose-500/15 text-rose-700 dark:text-rose-300 border-rose-500/30 text-[11px] gap-1 font-medium">
                                  <X className="h-3 w-3" /> Unsatisfied
                                </Badge>
                              )}
                              {crit.status === "UNABLE_TO_DETERMINE" && (
                                <Badge className="bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30 text-[11px] gap-1 font-medium">
                                  <HelpCircle className="h-3 w-3" /> Unverified
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell className="text-xs text-slate-500 dark:text-slate-400">
                              {crit.explanation}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  {/* Missing Requirements Guidance */}
                  {eligibility.missing_requirements && eligibility.missing_requirements.length > 0 && (
                    <div className="p-4 rounded-xl border border-amber-200 dark:border-amber-900/60 bg-amber-50/50 dark:bg-amber-950/20 space-y-2">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                        <h4 className="text-xs font-bold text-amber-900 dark:text-amber-300 uppercase tracking-wider">
                          Action Required to Establish Eligibility
                        </h4>
                      </div>
                      <ul className="list-disc list-inside text-xs text-amber-800 dark:text-amber-200 space-y-1">
                        {eligibility.missing_requirements.map((req, idx) => (
                          <li key={idx}>{req}</li>
                        ))}
                      </ul>
                      <div className="pt-2">
                        <Link href="/candidates/me">
                          <Button size="sm" variant="outline" className="text-xs gap-1.5 border-amber-300 dark:border-amber-800 hover:bg-amber-100 dark:hover:bg-amber-900/30">
                            Update Candidate Profile & Documents <ExternalLink className="h-3 w-3" />
                          </Button>
                        </Link>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center justify-center py-6 text-sm text-slate-500">
                  <Loader2 className="h-4 w-4 animate-spin mr-2" /> Evaluating your academic profile against position requirements...
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Application Submission Form / Modal */}
        {isApplying && (
          <Card className="border-2 border-[#4169D8] dark:border-[#4169D8]/80 shadow-lg">
            <CardHeader className="bg-[#4169D8]/5 border-b border-[#4169D8]/20">
              <CardTitle className="text-lg font-bold flex items-center gap-2 text-slate-900 dark:text-white">
                <Send className="h-5 w-5 text-[#4169D8]" />
                Submit Application for {jobTitle}
              </CardTitle>
              <CardDescription className="text-xs">
                Select your verified resume version and attach a tailored cover letter.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleApply}>
              <CardContent className="space-y-5 pt-6">
                {applyError && (
                  <div className="p-3.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-xs text-rose-700 dark:text-rose-300 flex items-start gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                    <span>{applyError}</span>
                  </div>
                )}

                {/* Resume Version Selector */}
                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-2">
                    <FileText className="h-4 w-4 text-[#4169D8]" />
                    Select Authoritative Resume Version <span className="text-rose-500">*</span>
                  </label>

                  {availableResumeVersions.length > 0 ? (
                    <div className="space-y-2">
                      <div className="grid grid-cols-1 gap-2.5">
                        {availableResumeVersions.map((r) => (
                          <label
                            key={r.versionId}
                            className={`flex items-center justify-between p-3 rounded-lg border text-xs cursor-pointer transition-colors ${
                              selectedResumeVersionId === r.versionId
                                ? "border-[#4169D8] bg-[#4169D8]/10 text-slate-900 dark:text-white font-medium"
                                : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900 text-slate-700 dark:text-slate-300"
                            }`}
                          >
                            <div className="flex items-center gap-3">
                              <input
                                type="radio"
                                name="resume_version"
                                value={r.versionId}
                                checked={selectedResumeVersionId === r.versionId}
                                onChange={() => setSelectedResumeVersionId(r.versionId)}
                                className="h-4 w-4 text-[#4169D8] focus:ring-[#4169D8]"
                              />
                              <div>
                                <div className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                  {r.resumeTitle}
                                  {r.isDefault && (
                                    <Badge className="bg-[#4169D8] text-white text-[10px] font-medium py-0 px-1.5">
                                      Default
                                    </Badge>
                                  )}
                                </div>
                                <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                                  {r.fileName} (v{r.versionNumber}) · Uploaded {formatDate(r.uploadedAt)}
                                </div>
                              </div>
                            </div>
                          </label>
                        ))}
                      </div>
                      <p className="text-[11px] text-slate-500">
                        This specific resume version will be frozen and permanently linked to this application snapshot.
                      </p>
                    </div>
                  ) : (
                    <div className="p-4 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 text-xs text-amber-800 dark:text-amber-200 space-y-2">
                      <p className="font-medium">No resume found on your candidate profile.</p>
                      <p className="text-[11px]">You must upload at least one verified resume before submitting campus applications.</p>
                      <Link href="/candidates/me#resumes">
                        <Button size="sm" variant="outline" className="text-xs gap-1 border-amber-300 dark:border-amber-800">
                          Upload Resume in Profile <ExternalLink className="h-3 w-3" />
                        </Button>
                      </Link>
                    </div>
                  )}
                </div>

                {/* Cover Letter */}
                <div className="space-y-1.5">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                    Statement of Suitability / Cover Letter (Optional)
                  </label>
                  <textarea
                    rows={4}
                    value={coverLetter}
                    onChange={(e) => setCoverLetter(e.target.value)}
                    placeholder="Describe how your skills, academic coursework, and projects match this requirement..."
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0E121B] text-xs text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#4169D8]"
                  />
                </div>
              </CardContent>

              <CardFooter className="flex justify-end gap-3 border-t border-slate-100 dark:border-slate-800 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsApplying(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmitting || (availableResumeVersions.length > 0 && !selectedResumeVersionId)}
                  className="gap-2 bg-[#4169D8] hover:bg-[#3254B8] text-white"
                >
                  {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  Confirm & Submit Application
                </Button>
              </CardFooter>
            </form>
          </Card>
        )}

        {/* Employer / Recruiter Candidate Applications Pipeline */}
        {canManage && (
          <Card className="border border-slate-200 dark:border-slate-800 shadow-xs">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg font-bold flex items-center gap-2">
                    <Users className="h-5 w-5 text-[#4169D8]" />
                    Applicant Review Pipeline
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Authoritative candidate submissions for this requirement ({applications.length} total)
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {applications.length === 0 ? (
                <div className="text-center py-10 text-slate-500 text-xs">
                  No candidate applications received yet for this requirement.
                </div>
              ) : (
                <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-slate-50 dark:bg-slate-900">
                        <TableHead className="text-xs">App ID</TableHead>
                        <TableHead className="text-xs">Candidate</TableHead>
                        <TableHead className="text-xs">Submitted Resume Snapshot</TableHead>
                        <TableHead className="text-xs">Eligibility</TableHead>
                        <TableHead className="text-xs">Applied Date</TableHead>
                        <TableHead className="text-xs">Pipeline Stage</TableHead>
                        <TableHead className="text-right text-xs">Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {applications.map((app) => (
                        <TableRow key={app.id}>
                          <TableCell className="font-mono text-xs">#{app.id}</TableCell>
                          <TableCell>
                            <div className="font-medium text-xs text-slate-900 dark:text-white">
                              {app.candidate_name || `Candidate #${app.candidate_profile_id}`}
                            </div>
                            <div className="text-[11px] font-mono text-slate-500">
                              {app.candidate_actor_id}
                            </div>
                          </TableCell>
                          <TableCell className="text-xs font-mono text-slate-600 dark:text-slate-400">
                            {app.resume_snapshot_file_name || app.resume_snapshot_title || "Standard Profile"}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={
                                app.eligibility_status === "ELIGIBLE"
                                  ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/30 text-[10px]"
                                  : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[10px]"
                              }
                            >
                              {app.eligibility_status || "VERIFIED"}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-slate-500 text-xs">
                            {formatDate(app.applied_at || app.created_at)}
                          </TableCell>
                          <TableCell>
                            <Badge variant={app.status === "HIRED" ? "default" : "outline"} className="text-[10px]">
                              {app.status || app.status_code}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <Link href={`/applications/${app.id}`}>
                              <Button variant="outline" size="sm" className="text-xs">
                                Review Candidate
                              </Button>
                            </Link>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
