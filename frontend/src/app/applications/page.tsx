"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  FileText,
  Building,
  Calendar,
  ExternalLink,
  Briefcase,
  Loader2,
  AlertCircle,
  Filter,
} from "lucide-react";
import { getMyApplications } from "@/lib/api/applications";
import { ApplicationResponse } from "@/types/applications";
import { useAuth } from "@/lib/auth/context";
import { formatDate } from "@/lib/utils";

export default function ApplicationsPage() {
  const { activeRole } = useAuth();
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadApplications() {
      try {
        setIsLoading(true);
        setError(null);
        const res = await getMyApplications({ page: 1, page_size: 50 });
        if (isMounted) {
          setApplications(res.items || []);
        }
      } catch (err: unknown) {
        if (isMounted) {
          // If not candidate role, endpoint returns 403
          setError(
            err instanceof Error
              ? err.message
              : "Unable to retrieve applications. Ensure you are signed in with an authorized role."
          );
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadApplications();
    return () => {
      isMounted = false;
    };
  }, []);

  const filteredApplications = applications.filter((app) => {
    if (statusFilter === "ALL") return true;
    const currentStatus = app.status || app.status_code || "";
    return currentStatus.toUpperCase() === statusFilter;
  });

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

  return (
    <DashboardShell
      title="Application Tracking & Submissions"
      breadcrumbs={[{ label: "Applications" }]}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              My Job Applications
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Track live status updates and progression for your submitted job requirements.
            </p>
          </div>

          <Link href="/jobs">
            <Button className="gap-2">
              <Briefcase className="h-4 w-4" />
              Explore Open Requirements
            </Button>
          </Link>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {["ALL", "APPLIED", "SCREENING", "INTERVIEW", "OFFERED", "HIRED", "REJECTED"].map((status) => (
            <Button
              key={status}
              variant={statusFilter === status ? "primary" : "outline"}
              size="sm"
              onClick={() => setStatusFilter(status)}
              className="text-xs"
            >
              {status}
            </Button>
          ))}
        </div>

        {/* Content Section */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          </div>
        ) : error ? (
          <Card className="border-red-200 dark:border-red-900/50">
            <CardContent className="pt-6 text-center space-y-4">
              <AlertCircle className="h-10 w-10 text-red-500 mx-auto" />
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Notice</h2>
              <p className="text-sm text-slate-500 max-w-md mx-auto">{error}</p>
              <Link href="/jobs">
                <Button variant="outline">Browse Available Jobs</Button>
              </Link>
            </CardContent>
          </Card>
        ) : filteredApplications.length === 0 ? (
          <Card>
            <CardContent className="py-16 text-center space-y-4">
              <FileText className="h-12 w-12 text-slate-300 dark:text-slate-600 mx-auto" />
              <div className="space-y-1">
                <h3 className="font-semibold text-lg text-slate-900 dark:text-white">
                  No applications found
                </h3>
                <p className="text-sm text-slate-500 max-w-sm mx-auto">
                  {statusFilter === "ALL"
                    ? "You haven't submitted any job applications yet. Discover matching roles and apply today."
                    : `No applications currently in '${statusFilter}' status.`}
                </p>
              </div>
              <Link href="/jobs">
                <Button className="mt-2">Discover Open Jobs</Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                Submitted Applications ({filteredApplications.length})
              </CardTitle>
              <CardDescription>
                Authoritative lifecycle status from the Talentra application pipeline.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Application ID</TableHead>
                    <TableHead>Job Requirement</TableHead>
                    <TableHead>Organisation</TableHead>
                    <TableHead>Applied At</TableHead>
                    <TableHead>Current Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredApplications.map((app) => {
                    const currentStatus = app.status || app.status_code || "APPLIED";
                    const appliedDate = app.applied_at || app.created_at || "";
                    return (
                      <TableRow key={app.id}>
                        <TableCell className="font-mono text-xs">#{app.id}</TableCell>
                        <TableCell className="font-medium text-slate-900 dark:text-white">
                          <Link
                            href={`/jobs/${app.job_requirement_id}`}
                            className="hover:underline flex items-center gap-1.5"
                          >
                            {app.job_title || `Job #${app.job_requirement_id}`}
                          </Link>
                        </TableCell>
                        <TableCell className="text-slate-600 dark:text-slate-400">
                          {app.organisation_name || `Organisation #${app.organisation_id}`}
                        </TableCell>
                        <TableCell className="text-slate-500 text-xs">
                          {formatDate(appliedDate)}
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusBadgeVariant(currentStatus)}>
                            {currentStatus}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Link href={`/applications/${app.id}`}>
                            <Button variant="outline" size="sm" className="gap-1.5">
                              View Details
                              <ExternalLink className="h-3.5 w-3.5" />
                            </Button>
                          </Link>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
