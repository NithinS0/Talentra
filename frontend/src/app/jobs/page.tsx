"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Search, Briefcase, PlusCircle, Building, MapPin, ExternalLink, Loader2, AlertCircle } from "lucide-react";
import { listJobs } from "@/lib/api/jobs";
import { JobResponse } from "@/types/jobs";
import { useAuth } from "@/lib/auth/context";
import { formatDate } from "@/lib/utils";

export default function JobsPage() {
  const { activeRole } = useAuth();
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadJobs() {
      try {
        setIsLoading(true);
        setError(null);
        const res = await listJobs({ search: searchTerm || undefined });
        if (isMounted) {
          setJobs(res.items || []);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load jobs");
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }
    loadJobs();
    return () => {
      isMounted = false;
    };
  }, [searchTerm]);

  const canPostJob = ["EMPLOYER", "RECRUITER", "SUPER_ADMIN", "ACCOUNT_ADMIN"].includes(activeRole);

  return (
    <DashboardShell
      title="Job Discovery & Requirements"
      breadcrumbs={[{ label: "Jobs" }]}
    >
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Job Requirements Directory
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Browse published job openings across verified employer organisations.
            </p>
          </div>

          {canPostJob && (
            <Link href="/jobs/new">
              <Button className="gap-2">
                <PlusCircle className="h-4 w-4" />
                Post Job Requirement
              </Button>
            </Link>
          )}
        </div>

        {/* Search & Filter Bar */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search by job title, keywords, or requirements..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-[#5278D9]"
            />
          </div>
        </div>

        {/* Content Section */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-[#5278D9]" />
          </div>
        ) : error ? (
          <Card className="border-red-200 dark:border-red-900/50">
            <CardContent className="pt-6 text-center space-y-4">
              <AlertCircle className="h-10 w-10 text-red-500 mx-auto" />
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Unable to Load Jobs</h2>
              <p className="text-sm text-slate-500 max-w-md mx-auto">{error}</p>
            </CardContent>
          </Card>
        ) : jobs.length === 0 ? (
          <Card>
            <CardContent className="py-16 text-center space-y-4">
              <Briefcase className="h-12 w-12 text-slate-300 dark:text-slate-600 mx-auto" />
              <div className="space-y-1">
                <h3 className="font-semibold text-lg text-slate-900 dark:text-white">
                  No published jobs found
                </h3>
                <p className="text-sm text-slate-500 max-w-sm mx-auto">
                  {searchTerm
                    ? `No job requirements match '${searchTerm}'. Try adjusting your query.`
                    : "No jobs are currently published in the system."}
                </p>
              </div>
              {canPostJob && (
                <Link href="/jobs/new">
                  <Button className="mt-2">Post Requirement</Button>
                </Link>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-bold">Published Jobs ({jobs.length})</CardTitle>
                <Badge variant="outline" className="text-xs">FastAPI /api/v1/jobs</Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Job ID</TableHead>
                    <TableHead>Job Title & Organisation</TableHead>
                    <TableHead>Work / Employment</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Posted</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.map((j) => (
                    <TableRow key={j.id}>
                      <TableCell className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">
                        JOB-{j.id}
                      </TableCell>
                      <TableCell>
                        <div className="font-semibold text-slate-900 dark:text-slate-100">{j.job_title}</div>
                        <div className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                          <Building className="h-3 w-3" />
                          <span>{j.organisation_name || `Org #${j.organisation_id}`}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Badge variant="outline">{j.employment_type_name || "Full Time"}</Badge>
                          <span className="text-xs text-slate-500">{j.work_type_name || "Remote"}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-xs text-slate-600 dark:text-slate-400">
                        <div className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5 text-slate-400" />
                          <span>{j.country_name || "Global Remote"}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={j.status_code === "OPEN" ? "default" : "outline"}>
                          {j.status_code}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-slate-500">
                        {formatDate(j.created_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/jobs/${j.id}`}>
                          <Button variant="outline" size="sm" className="gap-1">
                            View
                            <ExternalLink className="h-3 w-3" />
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
