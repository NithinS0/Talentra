"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Briefcase, PlusCircle, Users, ArrowRight, FileText, CheckCircle2 } from "lucide-react";
import { listJobs } from "@/lib/api/jobs";
import { JobResponse } from "@/types/jobs";
import { formatDate } from "@/lib/utils";

export default function EmployerPortalPage() {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadEmployerData() {
      try {
        setLoading(true);
        const res = await listJobs({ page_size: 10 });
        if (isMounted && res?.items) {
          setJobs(res.items);
        }
      } catch (err) {
        console.error("Failed to load employer jobs:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadEmployerData();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <PortalShell
      allowedRoles={["EMPLOYER", "SUPER_ADMIN"]}
      portalName="Employer Hiring Portal"
      portalDescription="Manage job requisitions, review candidate applicant pipelines, and progress recruitment workflows."
      badgeLabel="Employer"
      breadcrumbs={[{ label: "Portals" }, { label: "Employer" }]}
    >
      <div className="space-y-6">
        {/* ─── Operational Overview Header ───────────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Talent Acquisition Pipeline
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Active requisitions and applicant review stages associated with your authorized organization.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <Link href="/applications">
              <Button variant="outline" size="sm" className="h-8 text-xs font-medium gap-1.5">
                <Users className="h-3.5 w-3.5" />
                Review Applications
              </Button>
            </Link>
            <Link href="/jobs/new">
              <Button size="sm" className="h-8 text-xs font-medium gap-1.5">
                <PlusCircle className="h-3.5 w-3.5" />
                Post Requisition
              </Button>
            </Link>
          </div>
        </div>

        {/* ─── Active Job Requisitions Table ─────────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
            <div className="flex items-center gap-2">
              <Briefcase className="h-4 w-4 text-[#4169D8]" />
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                Active Job Requisitions
              </h3>
            </div>
            <span className="text-xs text-slate-500">
              {jobs.length} requisitions
            </span>
          </div>

          {loading ? (
            <div className="py-12 text-center text-xs text-slate-500">
              Loading active job requisitions...
            </div>
          ) : jobs.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Requisition</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Location / Mode</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Created Date</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Status</TableHead>
                    <TableHead className="text-right text-xs uppercase font-semibold text-slate-500">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.map((job) => (
                    <TableRow key={job.id} className="text-xs">
                      <TableCell>
                        <div className="font-semibold text-slate-900 dark:text-white">
                          {job.title}
                        </div>
                        <div className="text-[11px] text-slate-500">
                          REQ-{String(job.id).padStart(5, "0")} · {job.organisation_name || "Enterprise"}
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-600 dark:text-slate-400">
                        {job.country_name || job.work_type_name || "Campus Drive"}
                      </TableCell>
                      <TableCell className="text-slate-500">
                        {formatDate(job.created_at || new Date().toISOString())}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={job.status === "ACTIVE" ? "success" : "default"}
                          className="text-[10px] font-medium"
                        >
                          {job.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/jobs/${job.id}`}>
                          <Button variant="ghost" size="sm" className="h-7 text-xs px-2 text-[#4169D8]">
                            Manage
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-slate-500 space-y-3">
              <FileText className="h-8 w-8 text-slate-300 dark:text-slate-700 mx-auto" />
              <div>
                <p className="font-medium text-slate-700 dark:text-slate-300">
                  No active job requisitions found
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Create your first job requisition to start receiving campus and candidate applications.
                </p>
              </div>
              <Link href="/jobs/new">
                <Button size="sm" className="h-8 text-xs font-medium">
                  Create First Requisition
                </Button>
              </Link>
            </div>
          )}
        </div>

        {/* ─── Hiring Stages & Shortcuts ──────────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link href="/applications" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Applicant Review Funnel
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Progress candidates across Screening, Technical Review, Interview, and Offer stages.
              </p>
            </div>
          </Link>

          <Link href="/candidates" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Candidate Directory
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Discover verified candidates by skill tags, academic branch, and graduation cycle.
              </p>
            </div>
          </Link>

          <Link href="/organisations" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Organization Profile
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Manage recruitment branding, authorized team recruiters, and hiring policies.
              </p>
            </div>
          </Link>
        </div>
      </div>
    </PortalShell>
  );
}
