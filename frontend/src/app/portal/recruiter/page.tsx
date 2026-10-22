"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Search, Users, ArrowRight, FileText, CheckCircle2 } from "lucide-react";
import { listJobs } from "@/lib/api/jobs";
import { listSourcingRequests } from "@/lib/api/sourcing";
import { JobResponse } from "@/types/jobs";
import { SourcingRequestResponse } from "@/types/sourcing";
import { formatDate } from "@/lib/utils";

export default function RecruiterPortalPage() {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [sourcingRequests, setSourcingRequests] = useState<SourcingRequestResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadRecruiterData() {
      try {
        setLoading(true);
        const [jobsRes, sourcingRes] = await Promise.allSettled([
          listJobs({ page_size: 5 }),
          listSourcingRequests({ page_size: 5 }),
        ]);

        if (!isMounted) return;

        if (jobsRes.status === "fulfilled" && jobsRes.value?.items) {
          setJobs(jobsRes.value.items);
        }
        if (sourcingRes.status === "fulfilled" && Array.isArray(sourcingRes.value)) {
          setSourcingRequests(sourcingRes.value);
        }
      } catch (err) {
        console.error("Failed to load recruiter data:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadRecruiterData();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <PortalShell
      allowedRoles={["RECRUITER", "SUPER_ADMIN"]}
      portalName="Recruiter Talent Sourcing Portal"
      portalDescription="Source qualified candidates across verified pools, curate client shortlists, and manage candidate outreach."
      badgeLabel="Recruiter"
      breadcrumbs={[{ label: "Portals" }, { label: "Recruiter" }]}
    >
      <div className="space-y-6">
        {/* ─── Sourcing Workspace Header ─────────────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Candidate Discovery & Outreach
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Assigned company requisitions, candidate search queries, and curated shortlists.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <Link href="/candidates">
              <Button variant="outline" size="sm" className="h-8 text-xs font-medium gap-1.5">
                <Users className="h-3.5 w-3.5" />
                Talent Directory
              </Button>
            </Link>
            <Link href="/sourcing">
              <Button size="sm" className="h-8 text-xs font-medium gap-1.5">
                <Search className="h-3.5 w-3.5" />
                Sourcing Search
              </Button>
            </Link>
          </div>
        </div>

        {/* ─── Assigned Job Requirements Table ───────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
            <div className="flex items-center gap-2">
              <Search className="h-4 w-4 text-[#4169D8]" />
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                Assigned Requisitions & Sourcing Requests
              </h3>
            </div>
            <Link href="/sourcing" className="text-xs text-[#4169D8] hover:underline font-medium">
              View All Sourcing
            </Link>
          </div>

          {loading ? (
            <div className="py-12 text-center text-xs text-slate-500">
              Loading sourcing requirements...
            </div>
          ) : jobs.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Mandate / Role</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Client Organization</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Location</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Status</TableHead>
                    <TableHead className="text-right text-xs uppercase font-semibold text-slate-500">Action</TableHead>
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
                          REQ-{String(job.id).padStart(5, "0")}
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-600 dark:text-slate-400">
                        {job.organisation_name || "Enterprise Client"}
                      </TableCell>
                      <TableCell className="text-slate-500">
                        {job.country_name || job.work_type_name || "Remote / Hybrid"}
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
                        <Link href={`/sourcing?job_id=${job.id}`}>
                          <Button variant="ghost" size="sm" className="h-7 text-xs px-2 text-[#4169D8]">
                            Source Talent
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
                  No active sourcing requests
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Assigned client requirements and candidate sourcing requests will appear here.
                </p>
              </div>
              <Link href="/candidates">
                <Button size="sm" className="h-8 text-xs font-medium">
                  Search Candidate Directory
                </Button>
              </Link>
            </div>
          )}
        </div>

        {/* ─── Sourcing Shortcuts ─────────────────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link href="/candidates" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Talent Search Directory
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Filter verified candidate profiles by skill matrices, academic credentials, and availability.
              </p>
            </div>
          </Link>

          <Link href="/sourcing" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Curated Shortlists
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Organize talent pools into client-specific shortlists and prepare candidate dossiers.
              </p>
            </div>
          </Link>

          <Link href="/applications" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Applicant Screening Queue
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Record screening interview notes and advance candidates to client interview rounds.
              </p>
            </div>
          </Link>
        </div>
      </div>
    </PortalShell>
  );
}
