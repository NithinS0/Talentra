"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Building2,
  Building,
  Users,
  MapPin,
  Calendar,
  ArrowLeft,
  AlertCircle,
  ShieldCheck,
  Loader2,
  UserCheck,
} from "lucide-react";
import { getOrganisationDetails, getOrganisationRecruiters } from "@/lib/api/organisations";
import { OrganisationResponse, RecruiterMappingResponse } from "@/types/organisations";
import { formatDate } from "@/lib/utils";

interface PageProps {
  params: Promise<{ organisationId: string }>;
}

export default function OrganisationDetailPage({ params }: PageProps) {
  const router = useRouter();
  const resolvedParams = use(params);
  const orgId = parseInt(resolvedParams.organisationId, 10);

  const [organisation, setOrganisation] = useState<OrganisationResponse | null>(null);
  const [recruiters, setRecruiters] = useState<RecruiterMappingResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      if (isNaN(orgId)) {
        setError("Invalid Organisation ID");
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const [orgData, recruitersData] = await Promise.all([
          getOrganisationDetails(orgId),
          getOrganisationRecruiters(orgId).catch(() => []),
        ]);

        if (isMounted) {
          setOrganisation(orgData);
          setRecruiters(recruitersData || []);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load organisation details");
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [orgId]);

  if (isLoading) {
    return (
      <DashboardShell
        title="Organisation Profile"
        breadcrumbs={[{ label: "Organisations", href: "/organisations" }, { label: `#${orgId}` }]}
      >
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      </DashboardShell>
    );
  }

  if (error || !organisation) {
    return (
      <DashboardShell
        title="Organisation Profile"
        breadcrumbs={[{ label: "Organisations", href: "/organisations" }, { label: "Error" }]}
      >
        <Card className="border-red-200 dark:border-red-900/50">
          <CardContent className="pt-6 text-center space-y-4">
            <AlertCircle className="h-10 w-10 text-red-500 mx-auto" />
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Organisation Record Not Found</h2>
            <p className="text-sm text-slate-500">
              {error || "The requested organisation does not exist or access was denied."}
            </p>
            <Button onClick={() => router.push("/organisations")} variant="outline" className="gap-2">
              <ArrowLeft className="h-4 w-4" /> Back to Organisations Directory
            </Button>
          </CardContent>
        </Card>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell
      title={organisation.display_name}
      breadcrumbs={[
        { label: "Organisations", href: "/organisations" },
        { label: organisation.display_name },
      ]}
    >
      <div className="space-y-6">
        {/* Header actions */}
        <div className="flex items-center justify-between">
          <Button onClick={() => router.push("/organisations")} variant="outline" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" /> Back to Directory
          </Button>

          <Badge variant={organisation.status_code === "ACTIVE" ? "default" : "outline"}>
            {organisation.status_code}
          </Badge>
        </div>

        {/* Overview Card */}
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <CardTitle className="text-2xl font-bold flex items-center gap-2">
                  <Building2 className="h-6 w-6 text-indigo-600" />
                  {organisation.display_name}
                </CardTitle>
                <CardDescription className="text-base text-slate-600 dark:text-slate-300 mt-1">
                  {organisation.legal_name}
                </CardDescription>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-medium">Entity ID:</span>
                <span className="font-mono text-xs px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200">
                  #{organisation.id}
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 text-sm">
              <div>
                <span className="text-xs text-slate-400 block font-medium">Primary Jurisdiction</span>
                <span className="font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-1.5 mt-0.5">
                  <MapPin className="h-3.5 w-3.5 text-slate-400" />
                  {organisation.primary_country_name || organisation.country_name || "India"}
                </span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block font-medium">Entity Type</span>
                <span className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5 block">
                  {organisation.organisation_type_code_id === 2
                    ? "Educational Institution"
                    : organisation.organisation_type_code_id === 3
                    ? "Staffing & Agency"
                    : "Commercial Enterprise"}
                </span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block font-medium">Registration Date</span>
                <span className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5 block">
                  {formatDate(organisation.created_at)}
                </span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block font-medium">Status</span>
                <span className="font-semibold text-emerald-600 dark:text-emerald-400 mt-0.5 block flex items-center gap-1">
                  <ShieldCheck className="h-4 w-4" />
                  {organisation.status_code}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recruiter Mapping Table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg flex items-center gap-2">
                  <UserCheck className="h-5 w-5 text-indigo-600" />
                  Mapped Recruiters & Authorization Boundaries
                </CardTitle>
                <CardDescription>
                  Recruiter accounts authorised to post jobs and review candidates on behalf of this organisation ({recruiters.length} mapped).
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {recruiters.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-sm">
                No recruiter accounts are currently mapped to this organisation entity.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Mapping ID</TableHead>
                    <TableHead>Recruiter Name</TableHead>
                    <TableHead>Recruiter Actor ID</TableHead>
                    <TableHead>User ID</TableHead>
                    <TableHead>Valid From</TableHead>
                    <TableHead>Valid Until</TableHead>
                    <TableHead>Assigned By</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recruiters.map((rec) => (
                    <TableRow key={rec.id}>
                      <TableCell className="font-mono text-xs">#{rec.id}</TableCell>
                      <TableCell className="font-medium text-slate-900 dark:text-white">
                        {rec.recruiter_name || `Recruiter #${rec.recruiter_user_id}`}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-indigo-600 dark:text-indigo-400">
                        {rec.recruiter_actor_id || "—"}
                      </TableCell>
                      <TableCell className="text-xs text-slate-500">
                        User #{rec.recruiter_user_id}
                      </TableCell>
                      <TableCell className="text-xs text-slate-500">
                        {formatDate(rec.valid_from)}
                      </TableCell>
                      <TableCell className="text-xs text-slate-500">
                        {rec.valid_until ? formatDate(rec.valid_until) : "Indefinite"}
                      </TableCell>
                      <TableCell className="text-xs text-slate-500">
                        Admin #{rec.assigned_by_user_id}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
