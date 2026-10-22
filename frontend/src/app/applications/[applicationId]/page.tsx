"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Building,
  User,
  Clock,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Briefcase,
  Loader2,
  Send,
  History,
} from "lucide-react";
import { getApplicationDetails, updateApplicationStatus } from "@/lib/api/applications";
import { ApplicationResponse } from "@/types/applications";
import { useAuth } from "@/lib/auth/context";
import { formatDate } from "@/lib/utils";

interface PageProps {
  params: Promise<{ applicationId: string }>;
}

const ALLOWED_TRANSITIONS = ["SCREENING", "INTERVIEW", "OFFERED", "HIRED", "REJECTED", "WITHDRAWN"];

export default function ApplicationDetailPage({ params }: PageProps) {
  const router = useRouter();
  const { activeRole } = useAuth();
  const resolvedParams = use(params);
  const applicationId = parseInt(resolvedParams.applicationId, 10);

  const [application, setApplication] = useState<ApplicationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Status transition state
  const [targetStatus, setTargetStatus] = useState<string>("SCREENING");
  const [statusNotes, setStatusNotes] = useState<string>("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadApplication() {
      if (isNaN(applicationId)) {
        setError("Invalid Application ID");
        setIsLoading(false);
        return;
      }

      try {
        const data = await getApplicationDetails(applicationId);
        if (isMounted) {
          setApplication(data);
          const nextTarget =
            data.status === "APPLIED"
              ? "SCREENING"
              : data.status === "SCREENING"
              ? "INTERVIEW"
              : data.status === "INTERVIEW"
              ? "OFFERED"
              : "HIRED";
          setTargetStatus(nextTarget);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load application details");
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadApplication();
    return () => {
      isMounted = false;
    };
  }, [applicationId]);

  const handleStatusTransition = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdating(true);
    setUpdateError(null);
    setUpdateSuccess(false);

    try {
      const updated = await updateApplicationStatus(applicationId, {
        status: targetStatus,
        notes: statusNotes || undefined,
      });
      setApplication(updated);
      setUpdateSuccess(true);
      setStatusNotes("");
    } catch (err: unknown) {
      setUpdateError(err instanceof Error ? err.message : "Failed to update application status");
    } finally {
      setIsUpdating(false);
    }
  };

  const canManage = ["EMPLOYER", "RECRUITER", "SUPER_ADMIN", "ACCOUNT_ADMIN"].includes(activeRole);

  const getStatusBadgeVariant = (status: string) => {
    switch (status.toUpperCase()) {
      case "HIRED":
      case "OFFERED":
        return "default";
      case "REJECTED":
      case "WITHDRAWN":
        return "destructive";
      default:
        return "outline";
    }
  };

  if (isLoading) {
    return (
      <DashboardShell
        title="Application Details"
        breadcrumbs={[{ label: "Applications", href: "/applications" }, { label: `#${applicationId}` }]}
      >
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      </DashboardShell>
    );
  }

  if (error || !application) {
    return (
      <DashboardShell
        title="Application Details"
        breadcrumbs={[{ label: "Applications", href: "/applications" }, { label: "Error" }]}
      >
        <Card className="border-red-200 dark:border-red-900/50">
          <CardContent className="pt-6 text-center space-y-4">
            <AlertCircle className="h-10 w-10 text-red-500 mx-auto" />
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Application Record Not Found</h2>
            <p className="text-sm text-slate-500">
              {error || "The requested application does not exist or access was denied."}
            </p>
            <Button onClick={() => router.push("/applications")} variant="outline" className="gap-2">
              <ArrowLeft className="h-4 w-4" /> Back to Applications
            </Button>
          </CardContent>
        </Card>
      </DashboardShell>
    );
  }

  const currentStatus = application.status || application.status_code || "APPLIED";

  return (
    <DashboardShell
      title={`Application #${application.id}`}
      breadcrumbs={[
        { label: "Applications", href: "/applications" },
        { label: `Application #${application.id}` },
      ]}
    >
      <div className="space-y-6">
        {/* Navigation & Status Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <Button onClick={() => router.push("/applications")} variant="outline" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" /> Back to Applications
          </Button>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Pipeline Stage:</span>
            <Badge variant={getStatusBadgeVariant(currentStatus)} className="text-sm px-3 py-1">
              {currentStatus}
            </Badge>
          </div>
        </div>

        {updateSuccess && (
          <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 flex items-center gap-3 text-emerald-800 dark:text-emerald-300">
            <CheckCircle2 className="h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold text-sm">Status transitioned successfully!</p>
              <p className="text-xs text-emerald-600 dark:text-emerald-400">
                The authoritative status audit history record has been committed to the ledger.
              </p>
            </div>
          </div>
        )}

        {/* Application Overview Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="md:col-span-2 space-y-6">
            <CardHeader>
              <CardTitle className="text-xl">Job Requirement & Candidacy</CardTitle>
              <CardDescription>
                Authoritative candidate submission details verified by backend security.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* Job Info Banner */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                    <Briefcase className="h-4 w-4 text-indigo-500" />
                    {application.job_title}
                  </h3>
                  <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
                    <Building className="h-3.5 w-3.5" />
                    {application.organisation_name}
                  </p>
                </div>
                <Link href={`/jobs/${application.job_requirement_id}`}>
                  <Button variant="outline" size="sm">
                    View Requirement
                  </Button>
                </Link>
              </div>

              {/* Candidate Info */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                <div className="p-3 rounded-lg border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-950">
                  <span className="text-xs text-slate-400 block font-medium">Candidate Name</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-1.5 mt-1">
                    <User className="h-4 w-4 text-slate-400" />
                    {application.candidate_name}
                  </span>
                </div>
                <div className="p-3 rounded-lg border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-950">
                  <span className="text-xs text-slate-400 block font-medium">Candidate Actor ID</span>
                  <span className="font-mono text-xs text-indigo-600 dark:text-indigo-400 block mt-1">
                    {application.candidate_actor_id}
                  </span>
                </div>
              </div>

              {/* Cover Letter */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Cover Letter / Statement of Motivation
                </h4>
                <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm text-slate-700 dark:text-slate-300 whitespace-pre-line leading-relaxed">
                  {application.cover_letter || "No statement or cover letter was attached to this application."}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timeline & Metadata Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <History className="h-4 w-4 text-slate-500" />
                  Submission Audit
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div>
                  <span className="text-xs text-slate-400 block font-medium">Applied Timestamp</span>
                  <span className="font-medium text-slate-800 dark:text-slate-200">
                    {formatDate(application.applied_at || application.created_at || "")}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block font-medium">Last Status Change</span>
                  <span className="font-medium text-slate-800 dark:text-slate-200">
                    {formatDate(application.last_status_changed_at || "")}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block font-medium">Application Record ID</span>
                  <span className="font-mono text-xs text-slate-600 dark:text-slate-400">
                    #{application.id}
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Recruiter / Employer Action Panel */}
            {canManage && (
              <Card className="border-indigo-200 dark:border-indigo-900/60">
                <CardHeader>
                  <CardTitle className="text-base">Pipeline Decision</CardTitle>
                  <CardDescription>
                    Transition candidate to next workflow stage.
                  </CardDescription>
                </CardHeader>
                <form onSubmit={handleStatusTransition}>
                  <CardContent className="space-y-3">
                    {updateError && (
                      <div className="p-2.5 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 text-xs text-red-600 dark:text-red-300">
                        {updateError}
                      </div>
                    )}
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                        Target Status Stage
                      </label>
                      <select
                        value={targetStatus}
                        onChange={(e) => setTargetStatus(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        {ALLOWED_TRANSITIONS.map((status) => (
                          <option key={status} value={status}>
                            {status}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                        Audit Notes (Optional)
                      </label>
                      <textarea
                        rows={2}
                        value={statusNotes}
                        onChange={(e) => setStatusNotes(e.target.value)}
                        placeholder="Rationale or interview assessment feedback..."
                        className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </CardContent>
                  <CardFooter>
                    <Button type="submit" disabled={isUpdating} className="w-full gap-2" size="sm">
                      {isUpdating && <Loader2 className="h-4 w-4 animate-spin" />}
                      Transition Status
                    </Button>
                  </CardFooter>
                </form>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
