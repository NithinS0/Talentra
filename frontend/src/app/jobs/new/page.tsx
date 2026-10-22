"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { createJob } from "@/lib/api/jobs";
import { JobCreateRequest } from "@/types/jobs";
import {
  Briefcase,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  GraduationCap,
  FileCheck,
  Building,
  Loader2,
} from "lucide-react";

export default function NewJobPage() {
  const router = useRouter();
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [responsibilities, setResponsibilities] = useState("");
  const [organisationId, setOrganisationId] = useState("1");
  const [employmentTypeId, setEmploymentTypeId] = useState("1");
  const [workTypeId, setWorkTypeId] = useState("1");
  const [locationCity, setLocationCity] = useState("Bengaluru");
  const [locationCountry, setLocationCountry] = useState("India");
  const [applicationDeadline, setApplicationDeadline] = useState("");

  // Structured eligibility criteria
  const [requiredQualifications, setRequiredQualifications] = useState(
    "B.Tech, B.E., M.Tech, MCA"
  );
  const [acceptedBranches, setAcceptedBranches] = useState(
    "Computer Science, Information Technology, Electronics"
  );
  const [minCgpa, setMinCgpa] = useState("7.0");
  const [minPercentage, setMinPercentage] = useState("70");
  const [allowBacklogs, setAllowBacklogs] = useState(false);
  const [maxActiveBacklogs, setMaxActiveBacklogs] = useState("0");
  const [minExpYears, setMinExpYears] = useState("0");
  const [maxExpYears, setMaxExpYears] = useState("2");
  const [requiredSkills, setRequiredSkills] = useState("Python, SQL, Algorithms, Git");
  const [preferredSkills, setPreferredSkills] = useState("FastAPI, React, Docker, AWS");
  const [requiredDocuments, setRequiredDocuments] = useState(
    "Resume, Class 10 Marksheet, Class 12 Marksheet, College Transcript"
  );

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!jobTitle.trim() || jobTitle.length < 3) {
      setError("Job title must be at least 3 characters.");
      return;
    }
    if (!jobDescription.trim() || jobDescription.length < 10) {
      setError("Job description must be at least 10 characters.");
      return;
    }

    const payload: JobCreateRequest = {
      organisation_id: parseInt(organisationId, 10),
      job_role_id: 1, // General Software Engineering
      title: jobTitle.trim(),
      description: jobDescription.trim(),
      responsibilities: responsibilities.trim() || undefined,
      employment_type_id: parseInt(employmentTypeId, 10),
      work_type_id: parseInt(workTypeId, 10),
      location_city: locationCity.trim() || undefined,
      location_country: locationCountry.trim() || undefined,
      application_deadline: applicationDeadline || undefined,
      required_qualifications: requiredQualifications.trim() || undefined,
      accepted_branches: acceptedBranches.trim() || undefined,
      min_cgpa: minCgpa ? parseFloat(minCgpa) : undefined,
      min_percentage: minPercentage ? parseFloat(minPercentage) : undefined,
      allow_backlogs: allowBacklogs,
      max_active_backlogs: allowBacklogs ? parseInt(maxActiveBacklogs, 10) : 0,
      min_experience_years: minExpYears ? parseInt(minExpYears, 10) : undefined,
      max_experience_years: maxExpYears ? parseInt(maxExpYears, 10) : undefined,
      required_skills: requiredSkills.trim() || undefined,
      preferred_skills: preferredSkills.trim() || undefined,
      required_documents: requiredDocuments.trim() || undefined,
      publish_now: true,
    };

    setIsSubmitting(true);
    try {
      const created = await createJob(payload);
      router.push(`/jobs/${created.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create job requirement.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <DashboardShell
      title="Create Job Requirement"
      breadcrumbs={[{ label: "Jobs", href: "/jobs" }, { label: "New Requirement" }]}
    >
      <div className="max-w-4xl space-y-6 mx-auto pb-16">
        <Link
          href="/jobs"
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-[#4169D8] transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Jobs Directory
        </Link>

        <Card className="border border-slate-200 dark:border-slate-800 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl font-bold">
                  Post New Placement / Job Requisition
                </CardTitle>
                <CardDescription className="text-xs">
                  Configure role specifications, eligibility rules, and required verification documents for automated candidate evaluation.
                </CardDescription>
              </div>
              <Badge className="bg-[#4169D8]/10 text-[#4169D8] border-[#4169D8]/20 text-xs">
                Active Requisition
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {error && (
              <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-xs text-rose-700 dark:text-rose-300 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Section 1: Basic Information */}
              <div className="space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center">
                  <Building className="w-3.5 h-3.5 mr-1.5 text-[#4169D8]" /> 1. Requisition & Organization Overview
                </h3>

                <Input
                  label="Job Title *"
                  placeholder="e.g. Graduate Software Engineer (Backend Systems)"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  required
                />

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <Select
                    label="Organisation *"
                    options={[
                      { value: "1", label: "Acme Corporation (#1)" },
                      { value: "2", label: "FinPay Technologies (#2)" },
                    ]}
                    value={organisationId}
                    onChange={(e) => setOrganisationId(e.target.value)}
                    required
                  />
                  <Select
                    label="Employment Type *"
                    options={[
                      { value: "1", label: "Full Time" },
                      { value: "2", label: "Part Time" },
                      { value: "3", label: "Contract" },
                      { value: "4", label: "Internship" },
                    ]}
                    value={employmentTypeId}
                    onChange={(e) => setEmploymentTypeId(e.target.value)}
                    required
                  />
                  <Select
                    label="Work Arrangement *"
                    options={[
                      { value: "1", label: "Remote" },
                      { value: "2", label: "Hybrid" },
                      { value: "3", label: "Onsite" },
                    ]}
                    value={workTypeId}
                    onChange={(e) => setWorkTypeId(e.target.value)}
                    required
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <Input
                    label="City"
                    placeholder="e.g. Bengaluru, Hyderabad, Pune"
                    value={locationCity}
                    onChange={(e) => setLocationCity(e.target.value)}
                  />
                  <Input
                    label="Country"
                    placeholder="e.g. India"
                    value={locationCountry}
                    onChange={(e) => setLocationCountry(e.target.value)}
                  />
                  <Input
                    label="Application Deadline"
                    type="date"
                    value={applicationDeadline}
                    onChange={(e) => setApplicationDeadline(e.target.value)}
                  />
                </div>
              </div>

              {/* Section 2: Detailed Descriptions */}
              <div className="space-y-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center">
                  <Briefcase className="w-3.5 h-3.5 mr-1.5 text-[#4169D8]" /> 2. Responsibilities & Job Description
                </h3>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Job Description & Role Summary *
                  </label>
                  <textarea
                    rows={4}
                    placeholder="Describe the team, mission, project scope, and what the role entails..."
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#4169D8] caret-primary"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Key Responsibilities (optional)
                  </label>
                  <textarea
                    rows={4}
                    placeholder="Detail day-to-day duties, engineering milestones, and collaboration expectations..."
                    value={responsibilities}
                    onChange={(e) => setResponsibilities(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#4169D8] caret-primary"
                  />
                </div>
              </div>

              {/* Section 3: Structured Eligibility Criteria */}
              <div className="space-y-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center">
                  <GraduationCap className="w-3.5 h-3.5 mr-1.5 text-[#4169D8]" /> 3. Candidate Academic & Cutoff Criteria
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Input
                    label="Required Qualifications"
                    placeholder="e.g. B.Tech, B.E., M.Tech, MCA"
                    value={requiredQualifications}
                    onChange={(e) => setRequiredQualifications(e.target.value)}
                  />
                  <Input
                    label="Accepted Branches / Streams"
                    placeholder="e.g. Computer Science, IT, Electronics"
                    value={acceptedBranches}
                    onChange={(e) => setAcceptedBranches(e.target.value)}
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <Input
                    label="Min CGPA (out of 10.0)"
                    type="number"
                    step="0.01"
                    placeholder="e.g. 7.50"
                    value={minCgpa}
                    onChange={(e) => setMinCgpa(e.target.value)}
                  />
                  <Input
                    label="Min Percentage (%)"
                    type="number"
                    step="0.1"
                    placeholder="e.g. 70.0"
                    value={minPercentage}
                    onChange={(e) => setMinPercentage(e.target.value)}
                  />
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                      Backlogs Policy
                    </label>
                    <div className="flex items-center space-x-2 pt-2">
                      <input
                        type="checkbox"
                        id="allow_backlogs"
                        checked={allowBacklogs}
                        onChange={(e) => setAllowBacklogs(e.target.checked)}
                        className="w-4 h-4 rounded text-[#4169D8]"
                      />
                      <label htmlFor="allow_backlogs" className="text-xs text-slate-700 dark:text-slate-300">
                        Allow active backlogs
                      </label>
                    </div>
                  </div>
                </div>

                {allowBacklogs && (
                  <div className="w-full sm:w-1/3">
                    <Input
                      label="Max Allowed Active Backlogs"
                      type="number"
                      min="1"
                      value={maxActiveBacklogs}
                      onChange={(e) => setMaxActiveBacklogs(e.target.value)}
                    />
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Input
                    label="Min Experience (Years)"
                    type="number"
                    min="0"
                    value={minExpYears}
                    onChange={(e) => setMinExpYears(e.target.value)}
                  />
                  <Input
                    label="Max Experience (Years)"
                    type="number"
                    min="0"
                    value={maxExpYears}
                    onChange={(e) => setMaxExpYears(e.target.value)}
                  />
                </div>
              </div>

              {/* Section 4: Skills & Required Documents */}
              <div className="space-y-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center">
                  <FileCheck className="w-3.5 h-3.5 mr-1.5 text-[#4169D8]" /> 4. Technical Skills & Mandatory Documents
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Input
                    label="Required Skills (comma separated)"
                    placeholder="e.g. Python, SQL, REST APIs, Git"
                    value={requiredSkills}
                    onChange={(e) => setRequiredSkills(e.target.value)}
                  />
                  <Input
                    label="Preferred Skills (comma separated)"
                    placeholder="e.g. Docker, Kubernetes, AWS, GraphQL"
                    value={preferredSkills}
                    onChange={(e) => setPreferredSkills(e.target.value)}
                  />
                </div>

                <Input
                  label="Required Candidate Documents"
                  placeholder="e.g. Resume, Class 10 Marksheet, Class 12 Marksheet, College Transcript"
                  value={requiredDocuments}
                  onChange={(e) => setRequiredDocuments(e.target.value)}
                />
              </div>

              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-end gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.push("/jobs")}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-[#4169D8] hover:bg-[#3355B8] gap-2"
                >
                  {isSubmitting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Briefcase className="h-4 w-4" />
                  )}
                  Publish Job Requirement
                </Button>
              </div>
            </form>
          </CardContent>
          <CardFooter className="text-xs text-slate-500 border-t border-slate-100 dark:border-slate-800">
            Eligibility engine automatically checks candidate profiles against these criteria upon application.
          </CardFooter>
        </Card>
      </div>
    </DashboardShell>
  );
}
