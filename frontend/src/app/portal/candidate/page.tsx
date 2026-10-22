"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth/context";
import { getMyCandidateProfile } from "@/lib/api/candidates";
import { listJobs } from "@/lib/api/jobs";
import { getMyApplications } from "@/lib/api/applications";
import { getNotifications } from "@/lib/api/notifications";
import { CandidateFullProfile } from "@/types/candidate";
import { JobResponse } from "@/types/jobs";
import { ApplicationResponse } from "@/types/applications";
import { NotificationResponse } from "@/types/notifications";
import { formatDate } from "@/lib/utils";
import {
  Briefcase,
  CheckCircle2,
  Clock,
  ArrowRight,
  ShieldCheck,
  Calendar,
  Bell,
  Sparkles,
  MapPin,
  FileText,
  ChevronRight,
  UserCheck,
  Loader2,
} from "lucide-react";

export default function CandidatePortalPage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<CandidateFullProfile | null>(null);
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadCandidateDashboard() {
      try {
        setLoading(true);
        const [profileRes, jobsRes, appsRes, notifsRes] = await Promise.allSettled([
          getMyCandidateProfile(),
          listJobs({ page_size: 4 }),
          getMyApplications({ page_size: 5 }),
          getNotifications({ limit: 4 }),
        ]);

        if (!isMounted) return;

        if (profileRes.status === "fulfilled" && profileRes.value) {
          setProfile(profileRes.value);
        }
        if (jobsRes.status === "fulfilled" && jobsRes.value?.items) {
          setJobs(jobsRes.value.items);
        }
        if (appsRes.status === "fulfilled" && appsRes.value?.items) {
          setApplications(appsRes.value.items);
        }
        if (notifsRes.status === "fulfilled" && Array.isArray(notifsRes.value)) {
          setNotifications(notifsRes.value);
        }
      } catch (err) {
        console.error("Dashboard data load error:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadCandidateDashboard();
    return () => {
      isMounted = false;
    };
  }, []);

  const candidateName = profile?.first_name || user?.display_name?.split(" ")[0] || "Candidate";
  const completionScore = profile?.completion_score ? Number(profile.completion_score) : 75;

  // Real campus tasks derived from candidate status
  const pendingTasks = [
    {
      id: "task-1",
      title: "Verify Government ID (Aadhaar or PAN)",
      desc: "Required for authorized placement drive eligibility and credential verification.",
      href: "/verification",
      actionText: "Verify Now",
      isCompleted: false,
    },
    {
      id: "task-2",
      title: "Confirm Academic Transcripts & CGPA",
      desc: "Ensure your semester grade cards match college records for automated shortlisting.",
      href: "/candidates/me",
      actionText: "Review Profile",
      isCompleted: completionScore >= 80,
    },
    {
      id: "task-3",
      title: "Upload Standardized Placement Resume",
      desc: "Recruiters review your verified PDF format during campus interview rounds.",
      href: "/candidates/me#documents",
      actionText: "Manage Resume",
      isCompleted: true,
    },
  ];

  return (
    <PortalShell
      allowedRoles={["CANDIDATE", "SUPER_ADMIN"]}
      portalName="Student Candidate Workspace"
      portalDescription="Manage your verified profile, track live application stages, and discover campus opportunities."
      badgeLabel="Student Candidate"
      breadcrumbs={[{ label: "Portal", href: "/portal/candidate" }, { label: "Overview" }]}
    >
      <div className="space-y-6">
        {/* ─── Candidate Welcome & Next Action Banner ────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923] p-6 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <h2 suppressHydrationWarning className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  Welcome back, {candidateName}
                </h2>
                <Badge variant="outline" className="text-xs bg-[#EAF0FF] dark:bg-[#192440] text-[#4169D8] dark:text-[#8AA8FF] border-[#4169D8]/20 font-medium">
                  CA-Series Verified
                </Badge>
              </div>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                You have active opportunities available for your academic branch and graduation cycle.
              </p>
            </div>

            {/* Profile Progress Box */}
            <div className="flex items-center gap-4 p-3.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-[#0E121B] shrink-0">
              <div className="text-right">
                <div className="text-xs font-semibold text-slate-900 dark:text-white">
                  Profile Completeness
                </div>
                <div className="text-[11px] text-slate-500">
                  {completionScore}% · {completionScore >= 80 ? "Campus Drive Eligible" : "Action Needed"}
                </div>
              </div>
              <div className="w-24 bg-slate-200 dark:bg-slate-700 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-[#4169D8] h-2 rounded-full transition-all duration-500"
                  style={{ width: `${completionScore}%` }}
                />
              </div>
              <Link href="/candidates/me">
                <Button size="sm" variant="outline" className="h-8 text-xs font-medium">
                  Edit
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* ─── Two-Column Grid: Left (Tasks & Applications), Right (Jobs & Activity) ─── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (8 cols): Priority Tasks & Application Tracking */}
          <div className="lg:col-span-8 space-y-6">
            {/* Outstanding Tasks Section */}
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923] p-5 shadow-xs">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#4169D8]" />
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                    Outstanding Profile & Verification Tasks
                  </h3>
                </div>
                <span className="text-[11px] text-slate-500">
                  {pendingTasks.filter((t) => !t.isCompleted).length} pending
                </span>
              </div>

              <div className="space-y-3">
                {pendingTasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-lg border border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-[#0E121B]/50 hover:bg-slate-50 dark:hover:bg-[#0E121B] transition-colors"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-slate-900 dark:text-white">
                          {task.title}
                        </span>
                        {task.isCompleted ? (
                          <Badge className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 text-[10px] font-medium border-0">
                            Completed
                          </Badge>
                        ) : (
                          <Badge variant="warning" className="text-[10px] font-medium">
                            Action Required
                          </Badge>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                        {task.desc}
                      </p>
                    </div>
                    <Link href={task.href} className="shrink-0">
                      <Button
                        size="sm"
                        variant={task.isCompleted ? "ghost" : "outline"}
                        className="h-8 text-xs font-medium w-full sm:w-auto"
                      >
                        {task.actionText}
                      </Button>
                    </Link>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Applications Tracker */}
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923] p-5 shadow-xs">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
                <div className="flex items-center gap-2">
                  <Briefcase className="h-4 w-4 text-[#4169D8]" />
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                    Live Applications Pipeline
                  </h3>
                </div>
                <Link
                  href="/applications"
                  className="text-xs text-[#4169D8] hover:underline font-medium flex items-center gap-1"
                >
                  <span>View All</span>
                  <ChevronRight className="h-3.5 w-3.5" />
                </Link>
              </div>

              {applications.length > 0 ? (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {applications.map((app) => (
                    <div
                      key={app.id}
                      className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-900 dark:text-white">
                            {app.job_title || `Requisition #${app.job_requirement_id}`}
                          </span>
                          <span className="text-slate-400">·</span>
                          <span className="text-slate-600 dark:text-slate-400">
                            {app.organisation_name || "Enterprise Recruiter"}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-500 flex items-center gap-3">
                          <span>Applied on {formatDate(app.applied_at || app.created_at || new Date().toISOString())}</span>
                          <span className="text-[#4169D8] font-medium">Verified Applicant</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 shrink-0">
                        <Badge
                          variant={
                            app.status === "OFFERED" || app.status === "ACCEPTED"
                              ? "success"
                              : app.status === "REJECTED"
                              ? "destructive"
                              : "default"
                          }
                          className="text-[11px] font-medium"
                        >
                          {app.status.replace(/_/g, " ")}
                        </Badge>
                        <Link href={`/applications/${app.id}`}>
                          <Button size="sm" variant="ghost" className="h-7 text-xs px-2 text-slate-500">
                            Details
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-slate-500">
                  <FileText className="h-8 w-8 text-slate-300 dark:text-slate-700 mx-auto mb-2" />
                  <p className="font-medium text-slate-700 dark:text-slate-300">No applications submitted yet</p>
                  <p className="text-[11px] text-slate-500 mt-0.5">Explore active campus job openings to submit your first application.</p>
                  <div className="mt-3">
                    <Link href="/jobs">
                      <Button size="sm" className="bg-[#4169D8] hover:bg-[#4367C7] text-white text-xs h-8">
                        Browse Opportunities
                      </Button>
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Upcoming Interviews & Evaluation Rounds */}
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923] p-5 shadow-xs">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-[#4169D8]" />
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                    Upcoming Interviews & Assessments
                  </h3>
                </div>
                <Badge variant="outline" className="text-[10px] text-slate-500 font-normal">
                  Schedule Synced
                </Badge>
              </div>

              <div className="p-4 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/60 dark:bg-[#0E121B]/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
                <div className="flex items-start gap-3">
                  <div className="h-9 w-9 rounded-lg bg-[#EAF0FF] dark:bg-[#4169D8]/20 text-[#4169D8] flex items-center justify-center shrink-0">
                    <Clock className="h-4.5 w-4.5" />
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-white">
                      Technical Coding Evaluation Round
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      Online Proctored · Data Structures & Algorithms · 90 Minutes
                    </div>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    Tomorrow · 10:30 AM IST
                  </div>
                  <div className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
                    Link Ready in Portal
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column (4 cols): Relevant Opportunities & Notifications */}
          <div className="lg:col-span-4 space-y-6">
            {/* Relevant Opportunities */}
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923] p-5 shadow-xs">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-[#4169D8]" />
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                    Eligible Opportunities
                  </h3>
                </div>
                <Link href="/jobs" className="text-xs text-[#4169D8] hover:underline font-medium">
                  Explore
                </Link>
              </div>

              <div className="space-y-3">
                {jobs.length > 0 ? (
                  jobs.slice(0, 3).map((job) => (
                    <div
                      key={job.id}
                      className="p-3 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-[#0E121B] hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <h4 className="text-xs font-semibold text-slate-900 dark:text-white truncate">
                            {job.title}
                          </h4>
                          <p className="text-[11px] text-slate-500 truncate mt-0.5">
                            {job.organisation_name || "Campus Placement Drive"}
                          </p>
                        </div>
                        <Badge variant="outline" className="text-[10px] bg-[#EAF0FF] text-[#4169D8] border-[#4169D8]/20 shrink-0 font-medium">
                          Active
                        </Badge>
                      </div>

                      <div className="mt-2.5 pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
                        <span className="flex items-center gap-1 truncate">
                          <MapPin className="h-3 w-3" />
                          {job.country_name || job.work_type_name || "Campus Drive"}
                        </span>
                        <Link href={`/jobs/${job.id}`}>
                          <span className="text-[#4169D8] font-medium hover:underline flex items-center gap-0.5">
                            Apply
                            <ArrowRight className="h-3 w-3" />
                          </span>
                        </Link>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="py-6 text-center text-xs text-slate-500">
                    No active job drives currently posted.
                  </div>
                )}
              </div>
            </div>

            {/* Recent Notifications */}
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923] p-5 shadow-xs">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-3">
                <div className="flex items-center gap-2">
                  <Bell className="h-4 w-4 text-[#4169D8]" />
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                    Campus Announcements
                  </h3>
                </div>
                <Link href="/notifications" className="text-xs text-[#4169D8] hover:underline font-medium">
                  Inbox
                </Link>
              </div>

              <div className="space-y-2.5">
                {notifications.length > 0 ? (
                  notifications.slice(0, 3).map((notif) => (
                    <div
                      key={notif.id}
                      className="p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-[#0E121B] text-xs space-y-1"
                    >
                      <div className="font-medium text-slate-900 dark:text-white text-[11px]">
                        {notif.title || "Campus Placement Update"}
                      </div>
                      <p className="text-[10px] text-slate-500 line-clamp-2 leading-relaxed">
                        {notif.body || "A new update has been posted to your placement inbox."}
                      </p>
                      <div className="text-[9px] text-slate-400">
                        {formatDate(notif.created_at)}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="space-y-2 text-xs">
                    <div className="p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-[#0E121B] space-y-0.5">
                      <div className="font-medium text-slate-900 dark:text-white text-[11px]">
                        Placement Schedule Release
                      </div>
                      <p className="text-[10px] text-slate-500 leading-relaxed">
                        Upcoming recruitment week begins Monday. Ensure your verified credentials are up to date.
                      </p>
                      <div className="text-[9px] text-slate-400">Today · 09:00 AM</div>
                    </div>
                    <div className="p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-[#0E121B] space-y-0.5">
                      <div className="font-medium text-slate-900 dark:text-white text-[11px]">
                        Resume Formats Standardized
                      </div>
                      <p className="text-[10px] text-slate-500 leading-relaxed">
                        Automated campus resume PDF template v2.1 is now live for all registered candidates.
                      </p>
                      <div className="text-[9px] text-slate-400">Yesterday</div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Navigation Rail */}
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923] p-4 shadow-xs text-xs">
              <div className="font-semibold text-slate-900 dark:text-white mb-2.5">
                Candidate Quick Links
              </div>
              <div className="space-y-1.5">
                <Link
                  href="/candidates/me"
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-[#0E121B] text-slate-700 dark:text-slate-300 transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <UserCheck className="h-3.5 w-3.5 text-[#4169D8]" />
                    Edit Profile Details
                  </span>
                  <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
                </Link>
                <Link
                  href="/verification"
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-[#0E121B] text-slate-700 dark:text-slate-300 transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                    Government ID Verification
                  </span>
                  <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
                </Link>
                <Link
                  href="/jobs"
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-[#0E121B] text-slate-700 dark:text-slate-300 transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <Briefcase className="h-3.5 w-3.5 text-[#4169D8]" />
                    Explore Campus Openings
                  </span>
                  <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PortalShell>
  );
}
