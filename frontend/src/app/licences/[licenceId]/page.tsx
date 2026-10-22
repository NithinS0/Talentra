"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Shield,
  KeyRound,
  Laptop,
  Users,
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Calendar,
} from "lucide-react";
import {
  getLicence,
  updateLicenceStatus,
  allocateSeat,
} from "@/lib/api/licences";
import { LicenceResponse } from "@/types/licences";
import { formatDate } from "@/lib/utils";

interface PageProps {
  params: Promise<{ licenceId: string }>;
}

export default function LicenceDetailPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const licenceId = parseInt(resolvedParams.licenceId, 10);

  const [licence, setLicence] = useState<LicenceResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [allocatingUserId, setAllocatingUserId] = useState<string>("");
  const [isAllocating, setIsAllocating] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      if (isNaN(licenceId) || licenceId <= 0) {
        setError("Invalid licence identifier");
        setIsLoading(false);
        return;
      }
      try {
        setIsLoading(true);
        setError(null);
        const res = await getLicence(licenceId);
        if (isMounted) {
          setLicence(res);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load licence details");
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, [licenceId]);

  const handleStatusChange = async (statusCode: number, label: string) => {
    if (!licence) return;
    const ok = window.confirm(`Transition licence #${licence.id} status to ${label}?`);
    if (!ok) return;

    try {
      setIsLoading(true);
      setError(null);
      const updated = await updateLicenceStatus(licence.id, {
        status_code_id: statusCode,
        reason: `Status transition to ${label}`,
      });
      setLicence(updated);
      setSuccessMessage(`Status updated to ${updated.status}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update status");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAllocateSeat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!licence) return;
    const uId = parseInt(allocatingUserId, 10);
    if (isNaN(uId) || uId <= 0) {
      setError("Please provide a valid user account ID");
      return;
    }

    try {
      setIsAllocating(true);
      setError(null);
      await allocateSeat({
        licence_id: licence.id,
        user_id: uId,
      });
      setSuccessMessage(`Seat allocated to User #${uId}`);
      setAllocatingUserId("");
      const refreshed = await getLicence(licence.id);
      setLicence(refreshed);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to allocate seat");
    } finally {
      setIsAllocating(false);
    }
  };

  const getStatusBadge = (statusName: string) => {
    switch (statusName.toUpperCase()) {
      case "ACTIVE":
        return "success";
      case "SUSPENDED":
        return "warning";
      case "REVOKED":
      case "EXPIRED":
        return "destructive";
      default:
        return "default";
    }
  };

  if (isLoading && !licence) {
    return (
      <DashboardShell title="Licence Details" breadcrumbs={[{ label: "Licences", href: "/licences" }, { label: "Details" }]}>
        <div className="flex items-center justify-center py-24">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell
      title={licence ? `Licence: ${licence.licence_code}` : "Licence Details"}
      breadcrumbs={[
        { label: "Licences", href: "/licences" },
        { label: licence ? licence.licence_code : `#${licenceId}` },
      ]}
    >
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Link
            href="/licences"
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Licences
          </Link>
          {licence && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={() => handleStatusChange(1, "ACTIVE")}
                disabled={isLoading || licence.status === "ACTIVE"}
              >
                Set Active
              </Button>
              <Button
                variant="outline"
                onClick={() => handleStatusChange(2, "SUSPENDED")}
                disabled={isLoading || licence.status === "SUSPENDED"}
              >
                Suspend
              </Button>
              <Button
                variant="destructive"
                onClick={() => handleStatusChange(3, "REVOKED")}
                disabled={isLoading || licence.status === "REVOKED"}
              >
                Revoke
              </Button>
            </div>
          )}
        </div>

        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-lg flex items-center gap-3 text-red-700 dark:text-red-400">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}

        {successMessage && (
          <div className="p-4 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 rounded-lg flex items-center gap-3 text-emerald-700 dark:text-emerald-400">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm font-medium">{successMessage}</span>
          </div>
        )}

        {licence && (
          <>
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-3">
                      <CardTitle className="text-xl font-bold">{licence.licence_code}</CardTitle>
                      <Badge variant={getStatusBadge(licence.status)}>{licence.status}</Badge>
                    </div>
                    <CardDescription className="mt-1">
                      Account #{licence.account_id} • Created {formatDate(licence.created_at)}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Calendar className="w-4 h-4" />
                    <span>
                      {formatDate(licence.valid_from)} — {formatDate(licence.valid_until)}
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-900/50">
                    <div className="flex items-center gap-2 text-slate-500 text-xs font-medium mb-1">
                      <Users className="w-4 h-4 text-primary" />
                      Total Seat Limit
                    </div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white">
                      {licence.max_users}
                    </div>
                  </div>

                  <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-900/50">
                    <div className="flex items-center gap-2 text-slate-500 text-xs font-medium mb-1">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      Allocated Seats
                    </div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white">
                      {licence.allocated_seats}
                    </div>
                  </div>

                  <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-900/50">
                    <div className="flex items-center gap-2 text-slate-500 text-xs font-medium mb-1">
                      <KeyRound className="w-4 h-4 text-indigo-500" />
                      Available Seats
                    </div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white">
                      {licence.available_seats}
                    </div>
                  </div>

                  <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-900/50">
                    <div className="flex items-center gap-2 text-slate-500 text-xs font-medium mb-1">
                      <Laptop className="w-4 h-4 text-amber-500" />
                      Max Devices / User
                    </div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white">
                      {licence.max_devices_per_user}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Shield className="w-4 h-4 text-primary" />
                    Seat Assignment Form
                  </CardTitle>
                  <CardDescription>
                    Assign a seat to a user under this licence.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleAllocateSeat} className="space-y-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                        User Account ID
                      </label>
                      <input
                        type="number"
                        placeholder="e.g. 5"
                        value={allocatingUserId}
                        onChange={(e) => setAllocatingUserId(e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                        min="1"
                        required
                      />
                    </div>
                    <Button
                      type="submit"
                      variant="primary"
                      disabled={isAllocating || licence.available_seats <= 0}
                      className="w-full"
                    >
                      {isAllocating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Confirm Seat Allocation"}
                    </Button>
                    {licence.available_seats <= 0 && (
                      <p className="text-xs text-red-500 text-center font-medium">
                        Capacity Exceeded: Cannot allocate seat without increasing licence capacity.
                      </p>
                    )}
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Licence Metadata & Policy</CardTitle>
                  <CardDescription>Audited operational properties</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Internal ID:</span>
                    <span className="font-mono">{licence.id}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Customer Account:</span>
                    <span>Account #{licence.account_id}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Status Code ID:</span>
                    <span className="font-mono">{licence.status_code_id}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Last Updated:</span>
                    <span>{formatDate(licence.updated_at)}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}
