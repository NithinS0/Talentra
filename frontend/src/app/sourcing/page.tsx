"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Compass,
  Briefcase,
  Building,
  UserCheck,
  PlusCircle,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Clock,
  Shield,
  Ban,
} from "lucide-react";
import {
  listSourcingRequests,
  createSourcingRequest,
  respondToSourcingRequest,
  cancelSourcingRequest,
} from "@/lib/api/sourcing";
import { SourcingRequestResponse, SourcingRequestCreate } from "@/types/sourcing";
import { useAuth } from "@/lib/auth/context";
import { formatDate } from "@/lib/utils";

export default function SourcingPage() {
  const { activeRole, user } = useAuth();
  const [requests, setRequests] = useState<SourcingRequestResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Sourcing Request Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [jobId, setJobId] = useState("");
  const [consultantUserId, setConsultantUserId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Action processing state
  const [processingId, setProcessingId] = useState<number | null>(null);

  const fetchRequests = async () => {
    try {
      const res = await listSourcingRequests({ page: 1, page_size: 50 });
      setRequests(res.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load sourcing requests");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    async function loadInitial() {
      try {
        const res = await listSourcingRequests({ page: 1, page_size: 50 });
        if (isMounted) setRequests(res.items || []);
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load sourcing requests");
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadInitial();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      const payload: SourcingRequestCreate = {
        job_requirement_id: parseInt(jobId, 10),
        consultant_user_id: consultantUserId ? parseInt(consultantUserId, 10) : undefined,
      };

      await createSourcingRequest(payload);
      setActionSuccess("Sourcing request initiated successfully!");
      setShowCreateModal(false);
      setJobId("");
      setConsultantUserId("");
      await fetchRequests();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to create sourcing request");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConsultantDecision = async (requestId: number, decision: "ACCEPT" | "DECLINE") => {
    setProcessingId(requestId);
    setActionError(null);
    setActionSuccess(null);

    try {
      await respondToSourcingRequest(requestId, decision, `Decision ${decision} recorded via portal`);
      setActionSuccess(`Request #${requestId} has been ${decision.toLowerCase()}ed.`);
      await fetchRequests();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : `Failed to record ${decision.toLowerCase()} decision`);
    } finally {
      setProcessingId(null);
    }
  };

  const handleCancelRequest = async (requestId: number) => {
    if (!confirm("Are you sure you want to cancel this sourcing request?")) return;
    setProcessingId(requestId);
    setActionError(null);
    setActionSuccess(null);

    try {
      await cancelSourcingRequest(requestId, "Cancelled by employer");
      setActionSuccess(`Request #${requestId} has been cancelled.`);
      await fetchRequests();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to cancel request");
    } finally {
      setProcessingId(null);
    }
  };

  const isConsultant = activeRole === "CONSULTANT";
  const canCreate = ["EMPLOYER", "RECRUITER", "SUPER_ADMIN", "ACCOUNT_ADMIN"].includes(activeRole);
  const canManage = canCreate;

  const filteredRequests = requests.filter((req) => {
    if (statusFilter === "ALL") return true;
    return req.status.toUpperCase() === statusFilter;
  });

  const getStatusBadgeVariant = (status: string) => {
    switch (status.toUpperCase()) {
      case "ACCEPTED":
      case "COMPLETED":
        return "default";
      case "DECLINED":
      case "CANCELLED":
        return "destructive";
      default:
        return "outline";
    }
  };

  return (
    <DashboardShell
      title="Sourcing & Consultant Engagements"
      breadcrumbs={[{ label: "Sourcing Requests" }]}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Sourcing & External Consultant Requests
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Manage outsourced candidate headhunting, consultant mandates, and talent shortlists.
            </p>
          </div>

          {canCreate && (
            <Button onClick={() => setShowCreateModal(true)} className="gap-2">
              <PlusCircle className="h-4 w-4" />
              Initiate Sourcing Request
            </Button>
          )}
        </div>

        {actionSuccess && (
          <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 flex items-center gap-3 text-emerald-800 dark:text-emerald-300">
            <CheckCircle2 className="h-5 w-5 shrink-0" />
            <p className="font-semibold text-sm">{actionSuccess}</p>
          </div>
        )}

        {actionError && (
          <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 flex items-center gap-3 text-red-700 dark:text-red-300">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <p className="font-semibold text-sm">{actionError}</p>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {["ALL", "PENDING", "ACCEPTED", "DECLINED", "CANCELLED", "COMPLETED"].map((status) => (
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

        {/* Modal: Initiate Sourcing Request */}
        {showCreateModal && (
          <Card className="border-indigo-200 dark:border-indigo-900 shadow-lg">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Compass className="h-5 w-5 text-indigo-600" />
                Initiate Sourcing Request
              </CardTitle>
              <CardDescription>
                Assigns an open job requirement to an external consultant or public consultant pool.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleCreateRequest}>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Target Job Requirement ID *
                    </label>
                    <input
                      type="number"
                      required
                      min={1}
                      value={jobId}
                      onChange={(e) => setJobId(e.target.value)}
                      placeholder="e.g. 1"
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Target Consultant User ID (Optional)
                    </label>
                    <input
                      type="number"
                      min={1}
                      value={consultantUserId}
                      onChange={(e) => setConsultantUserId(e.target.value)}
                      placeholder="Leave blank for open pool"
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowCreateModal(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmitting} className="gap-2">
                  {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  Dispatch Request
                </Button>
              </CardFooter>
            </form>
          </Card>
        )}

        {/* Content Section */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          </div>
        ) : error ? (
          <Card className="border-red-200 dark:border-red-900/50">
            <CardContent className="pt-6 text-center space-y-4">
              <AlertCircle className="h-10 w-10 text-red-500 mx-auto" />
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Unable to Load Requests</h2>
              <p className="text-sm text-slate-500 max-w-md mx-auto">{error}</p>
            </CardContent>
          </Card>
        ) : filteredRequests.length === 0 ? (
          <Card>
            <CardContent className="py-16 text-center space-y-4">
              <Compass className="h-12 w-12 text-slate-300 dark:text-slate-600 mx-auto" />
              <div className="space-y-1">
                <h3 className="font-semibold text-lg text-slate-900 dark:text-white">
                  No sourcing requests found
                </h3>
                <p className="text-sm text-slate-500 max-w-sm mx-auto">
                  {statusFilter === "ALL"
                    ? "There are currently no active sourcing mandates for your organization."
                    : `No sourcing requests with status '${statusFilter}'.`}
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                Sourcing Mandates ({filteredRequests.length})
              </CardTitle>
              <CardDescription>
                Authoritative consultant engagement pipeline with backend audit validation.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Request ID</TableHead>
                    <TableHead>Job Requirement</TableHead>
                    <TableHead>Organisation</TableHead>
                    <TableHead>Assigned Consultant</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Requested Date</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRequests.map((req) => (
                    <TableRow key={req.id}>
                      <TableCell className="font-mono text-xs">#{req.id}</TableCell>
                      <TableCell className="font-semibold text-slate-900 dark:text-white">
                        <Link
                          href={`/jobs/${req.job_requirement_id}`}
                          className="hover:underline flex items-center gap-1.5"
                        >
                          <Briefcase className="h-3.5 w-3.5 text-indigo-500" />
                          {req.job_title || `Job #${req.job_requirement_id}`}
                        </Link>
                      </TableCell>
                      <TableCell className="text-xs text-slate-600 dark:text-slate-400">
                        {req.organisation_name}
                      </TableCell>
                      <TableCell className="text-xs text-slate-600 dark:text-slate-400">
                        {req.consultant_name || (req.consultant_user_id ? `Consultant #${req.consultant_user_id}` : "Open Pool")}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(req.status)}>
                          {req.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-slate-500 text-xs">
                        {formatDate(req.requested_at || req.created_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        {/* Consultant action buttons */}
                        {isConsultant && req.status === "PENDING" && (
                          <div className="flex items-center justify-end gap-1.5">
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-emerald-600 hover:text-emerald-700 h-8 px-2.5 text-xs"
                              disabled={processingId === req.id}
                              onClick={() => handleConsultantDecision(req.id, "ACCEPT")}
                            >
                              Accept
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-red-600 hover:text-red-700 h-8 px-2.5 text-xs"
                              disabled={processingId === req.id}
                              onClick={() => handleConsultantDecision(req.id, "DECLINE")}
                            >
                              Decline
                            </Button>
                          </div>
                        )}

                        {/* Employer cancel action */}
                        {canManage && req.status === "PENDING" && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-slate-500 hover:text-red-600 h-8 px-2.5 text-xs"
                            disabled={processingId === req.id}
                            onClick={() => handleCancelRequest(req.id)}
                          >
                            Cancel
                          </Button>
                        )}
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
