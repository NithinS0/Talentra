"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { GraduationCap, Users, Calendar, ArrowRight, BarChart3, FileText } from "lucide-react";
import { listJobs } from "@/lib/api/jobs";
import { JobResponse } from "@/types/jobs";
import { formatDate } from "@/lib/utils";

export default function PlacementOfficerPortalPage() {
  const [drives, setDrives] = useState<JobResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadPlacementDrives() {
      try {
        setLoading(true);
        const res = await listJobs({ page_size: 10 });
        if (isMounted && res?.items) {
          setDrives(res.items);
        }
      } catch (err) {
        console.error("Failed to load placement drives:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadPlacementDrives();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <PortalShell
      allowedRoles={["PLACEMENT_OFFICER", "SUPER_ADMIN"]}
      portalName="College Placement Officer Portal"
      portalDescription="Manage campus hiring drives, verify institutional student rosters, and track placement outcomes."
      badgeLabel="Institutional TPO"
      breadcrumbs={[{ label: "Portals" }, { label: "Placement Officer" }]}
    >
      <div className="space-y-6">
        {/* ─── Institutional Overview Header ─────────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Campus Placement Workspace
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Coordinated recruitment drives, batch student rosters, and placement conversion metrics.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <Link href="/analytics">
              <Button variant="outline" size="sm" className="h-8 text-xs font-medium gap-1.5">
                <BarChart3 className="h-3.5 w-3.5" />
                Placement Analytics
              </Button>
            </Link>
            <Link href="/candidates">
              <Button size="sm" className="h-8 text-xs font-medium gap-1.5">
                <Users className="h-3.5 w-3.5" />
                Student Roster
              </Button>
            </Link>
          </div>
        </div>

        {/* ─── Active Campus Recruitment Drives Table ─────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-[#4169D8]" />
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                Active Campus Recruitment Drives
              </h3>
            </div>
            <span className="text-xs text-slate-500">
              {drives.length} active opportunities
            </span>
          </div>

          {loading ? (
            <div className="py-12 text-center text-xs text-slate-500">
              Loading campus recruitment drives...
            </div>
          ) : drives.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Company & Role</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Employment Type</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Target Location</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Drive Status</TableHead>
                    <TableHead className="text-right text-xs uppercase font-semibold text-slate-500">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {drives.map((drive) => (
                    <TableRow key={drive.id} className="text-xs">
                      <TableCell>
                        <div className="font-semibold text-slate-900 dark:text-white">
                          {drive.title}
                        </div>
                        <div className="text-[11px] text-slate-500">
                          {drive.organisation_name || "Campus Partner"} · REQ-{String(drive.id).padStart(5, "0")}
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-600 dark:text-slate-400">
                        {drive.employment_type_name || "Full-time"}
                      </TableCell>
                      <TableCell className="text-slate-500">
                        {drive.country_name || drive.work_type_name || "Campus Drive"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={drive.status === "ACTIVE" ? "success" : "default"}
                          className="text-[10px] font-medium"
                        >
                          {drive.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/jobs/${drive.id}`}>
                          <Button variant="ghost" size="sm" className="h-7 text-xs px-2 text-[#4169D8]">
                            View Details
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
                  No active campus drives scheduled
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Opportunities opened by employers for campus hiring will appear here.
                </p>
              </div>
              <Link href="/jobs">
                <Button size="sm" className="h-8 text-xs font-medium">
                  Browse All Requisitions
                </Button>
              </Link>
            </div>
          )}
        </div>

        {/* ─── Institutional Action Cards ─────────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link href="/candidates" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Student Eligibility Roster
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Filter batch students by branch, CGPA cutoff, and verification standing.
              </p>
            </div>
          </Link>

          <Link href="/applications" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Batch Application Funnel
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Track campus applications across Shortlisted, Interview, and Offer stages.
              </p>
            </div>
          </Link>

          <Link href="/analytics" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Placement Reports
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Review batch placement ratios, average compensation tiers, and recruiting companies.
              </p>
            </div>
          </Link>
        </div>
      </div>
    </PortalShell>
  );
}
