"use client";

import { useEffect, useState, useCallback } from "react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  ShieldAlert,
  Users,
  FileText,
  KeyRound,
  Lock,
  Database,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Search,
  UserCheck,
  UserX,
  Play,
  RotateCw,
} from "lucide-react";
import {
  listAdminUsers,
  grantUserRole,
  revokeUserRole,
  updateUserStatus,
  softDeleteUser,
  listAuditEvents,
  revokeIdentitySession,
  getAccessReview,
  getDataClassification,
} from "@/lib/api/admin";
import { runRetentionJob } from "@/lib/api/verification";
import {
  AdminUserResponse,
  AuditEventResponse,
  AccessReviewReportResponse,
  DataClassificationResponse,
} from "@/types/admin";
import { RetentionJobSummaryResponse } from "@/types/verification";
import { formatDate } from "@/lib/utils";

export default function AdministrationPage() {
  const [users, setUsers] = useState<AdminUserResponse[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEventResponse[]>([]);
  const [accessReview, setAccessReview] = useState<AccessReviewReportResponse | null>(null);
  const [dataClassification, setDataClassification] = useState<DataClassificationResponse | null>(null);
  const [retentionSummary, setRetentionSummary] = useState<RetentionJobSummaryResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // User Governance State
  const [selectedUser, setSelectedUser] = useState<AdminUserResponse | null>(null);
  const [roleToGrant, setRoleToGrant] = useState<string>("RECRUITER");
  const [isGrantingRole, setIsGrantingRole] = useState<boolean>(false);

  // Session Revocation State (FR-0066)
  const [revokeSessionId, setRevokeSessionId] = useState<string>("");
  const [revokeReason, setRevokeReason] = useState<string>("Administrative revocation");
  const [isRevokingSession, setIsRevokingSession] = useState<boolean>(false);

  // Retention Scheduler Form (FR-0177, FR-0196)
  const [retentionTargetClass, setRetentionTargetClass] = useState<string>("KYC_DOCUMENTS");
  const [retentionDays, setRetentionDays] = useState<number>(2555);
  const [retentionDryRun, setRetentionDryRun] = useState<boolean>(true);
  const [isRunningRetention, setIsRunningRetention] = useState<boolean>(false);

  const loadAdminData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [usersRes, auditRes, accessRes, classRes] = await Promise.allSettled([
        listAdminUsers({ page: 1, page_size: 15 }),
        listAuditEvents({ page: 1, page_size: 20 }),
        getAccessReview(),
        getDataClassification(),
      ]);

      if (usersRes.status === "fulfilled") setUsers(usersRes.value.items || []);
      if (auditRes.status === "fulfilled") setAuditEvents(auditRes.value.items || []);
      if (accessRes.status === "fulfilled") setAccessReview(accessRes.value);
      if (classRes.status === "fulfilled") setDataClassification(classRes.value);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load administration data");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function init() {
      try {
        const [usersRes, auditRes, accessRes, classRes] = await Promise.allSettled([
          listAdminUsers({ page: 1, page_size: 15 }),
          listAuditEvents({ page: 1, page_size: 20 }),
          getAccessReview(),
          getDataClassification(),
        ]);

        if (isMounted) {
          if (usersRes.status === "fulfilled") setUsers(usersRes.value.items || []);
          if (auditRes.status === "fulfilled") setAuditEvents(auditRes.value.items || []);
          if (accessRes.status === "fulfilled") setAccessReview(accessRes.value);
          if (classRes.status === "fulfilled") setDataClassification(classRes.value);
          setIsLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load administration data");
          setIsLoading(false);
        }
      }
    }
    init();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleGrantRole = async (userId: number) => {
    try {
      setIsGrantingRole(true);
      setError(null);
      const updated = await grantUserRole({
        user_id: userId,
        role_code: roleToGrant,
      });
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
      setSuccessMessage(`Role '${roleToGrant}' granted to User #${userId} (FR-0055).`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Role grant rejected (privilege escalation prevention: FR-0068)");
    } finally {
      setIsGrantingRole(false);
    }
  };

  const handleRevokeRole = async (userId: number, roleCode: string) => {
    const reason = window.prompt(`Reason for revoking role ${roleCode}:`, "Role cleanup");
    if (!reason) return;

    try {
      setIsLoading(true);
      setError(null);
      const updated = await revokeUserRole({
        user_id: userId,
        role_code: roleCode,
        reason,
      });
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
      setSuccessMessage(`Role '${roleCode}' revoked from User #${userId}.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Role revocation failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleStatusChange = async (userId: number, statusCode: number, label: string) => {
    const reason = window.prompt(`Mandatory audit reason for transitioning account status to ${label}:`, "Compliance policy update");
    if (!reason) return;

    try {
      setIsLoading(true);
      setError(null);
      const updated = await updateUserStatus(userId, {
        account_status_code_id: statusCode,
        reason,
      });
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
      setSuccessMessage(`Account status updated to ${label} (FR-0060, FR-0201).`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Account status update rejected");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSoftDelete = async (userId: number) => {
    const reason = window.prompt("Mandatory audit reason for soft deletion:", "Account deactivated upon user request");
    if (!reason) return;

    try {
      setIsLoading(true);
      setError(null);
      const updated = await softDeleteUser(userId, reason);
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
      setSuccessMessage(`User #${userId} soft-deleted with timestamp recorded in deleted_at (FR-0063).`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Soft delete failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRevokeSession = async (e: React.FormEvent) => {
    e.preventDefault();
    const sId = parseInt(revokeSessionId, 10);
    if (isNaN(sId) || sId <= 0) {
      setError("Please specify a valid Session ID to revoke.");
      return;
    }

    try {
      setIsRevokingSession(true);
      setError(null);
      await revokeIdentitySession(sId, { session_id: sId, reason: revokeReason });
      setSuccessMessage(`Identity session #${sId} revoked and access terminated immediately (FR-0066).`);
      setRevokeSessionId("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Session revocation failed");
    } finally {
      setIsRevokingSession(false);
    }
  };

  const handleRunRetention = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsRunningRetention(true);
      setError(null);
      const res = await runRetentionJob({
        dry_run: retentionDryRun,
        target_data_class: retentionTargetClass,
        retention_days: retentionDays,
      });
      setRetentionSummary(res);
      setSuccessMessage(
        `Retention job #${res.job_id} completed (${res.dry_run ? "DRY RUN" : "LIVE PURGE"}): ${res.evaluated_records} evaluated, ${res.eligible_for_purge} eligible, ${res.purged_records} purged (FR-0177).`
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Retention job failed");
    } finally {
      setIsRunningRetention(false);
    }
  };

  return (
    <DashboardShell
      title="Administration, RBAC & Audit Governance"
      breadcrumbs={[{ label: "Administration" }]}
    >
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Administrative Governance & Security Auditing (Module M04)
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Immutable audit logging, privileged access reviews, data classification inventory, and role elevation governance.
          </p>
        </div>

        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-lg flex items-center justify-between text-red-700 dark:text-red-400">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium">{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-xs underline">
              Dismiss
            </button>
          </div>
        )}

        {successMessage && (
          <div className="p-4 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 rounded-lg flex items-center justify-between text-emerald-700 dark:text-emerald-400">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium">{successMessage}</span>
            </div>
            <button onClick={() => setSuccessMessage(null)} className="text-xs underline">
              Dismiss
            </button>
          </div>
        )}

        {/* User Governance & RBAC Table (FR-0055, FR-0063, FR-0068) */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <Users className="w-4 h-4 text-primary" />
                  User Account & Role Governance (FR-0055, FR-0068)
                </CardTitle>
                <CardDescription>
                  Enforces permission denial by default, prevents privilege escalation, and logs status transitions.
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={roleToGrant}
                  onChange={(e) => setRoleToGrant(e.target.value)}
                  className="px-2 py-1 text-xs border border-slate-300 dark:border-slate-700 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                >
                  <option value="RECRUITER">RECRUITER</option>
                  <option value="EMPLOYER">EMPLOYER</option>
                  <option value="PLACEMENT_OFFICER">PLACEMENT_OFFICER</option>
                  <option value="ACCOUNT_ADMIN">ACCOUNT_ADMIN</option>
                  <option value="ADMIN">ADMIN</option>
                </select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {users.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-sm">
                No users returned for administrative review.
              </div>
            ) : (
              <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>User ID</TableHead>
                      <TableHead>Name & Email</TableHead>
                      <TableHead>Account Status</TableHead>
                      <TableHead>Assigned Roles</TableHead>
                      <TableHead className="text-right">Governance Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((u) => (
                      <TableRow key={u.id} className={u.deleted_at ? "opacity-60 bg-slate-50/50 dark:bg-slate-900/50" : ""}>
                        <TableCell className="font-mono text-xs">#{u.id}</TableCell>
                        <TableCell>
                          <div className="font-semibold text-xs text-slate-900 dark:text-white">
                            {u.display_name}
                          </div>
                          <span className="text-[11px] text-slate-400 block font-mono">
                            {u.email_address || "No email on record"}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge variant={u.account_status === "ACTIVE" ? "success" : "destructive"}>
                            {u.deleted_at ? "SOFT_DELETED" : u.account_status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {u.roles.map((r) => (
                              <span
                                key={r}
                                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                              >
                                {r}
                                <button
                                  type="button"
                                  onClick={() => handleRevokeRole(u.id, r)}
                                  className="text-red-500 hover:text-red-700"
                                  title={`Revoke role ${r}`}
                                >
                                  &times;
                                </button>
                              </span>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <Button
                              variant="outline"
                              onClick={() => handleGrantRole(u.id)}
                              disabled={isGrantingRole || u.roles.includes(roleToGrant)}
                              className="h-7 px-2 text-[11px]"
                            >
                              + Grant {roleToGrant}
                            </Button>
                            {u.account_status === "ACTIVE" ? (
                              <Button
                                variant="outline"
                                onClick={() => handleStatusChange(u.id, 2, "SUSPENDED")}
                                className="h-7 px-2 text-[11px]"
                              >
                                Suspend
                              </Button>
                            ) : (
                              <Button
                                variant="outline"
                                onClick={() => handleStatusChange(u.id, 1, "ACTIVE")}
                                className="h-7 px-2 text-[11px]"
                              >
                                Activate
                              </Button>
                            )}
                            {!u.deleted_at && (
                              <Button
                                variant="destructive"
                                onClick={() => handleSoftDelete(u.id)}
                                className="h-7 px-2 text-[11px]"
                              >
                                Soft Delete
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Append-Only Audit Trail (FR-0059, FR-0060, FR-0064, FR-0201) */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-emerald-500" />
              Append-Only Security Audit Trail (FR-0059, FR-0064)
            </CardTitle>
            <CardDescription>
              Audit records are strictly append-only and cannot be updated or deleted. Sensitive credentials redacted.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {auditEvents.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-sm">
                No audit events on record.
              </div>
            ) : (
              <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Event ID</TableHead>
                      <TableHead>Action Code</TableHead>
                      <TableHead>Resource Type</TableHead>
                      <TableHead>Actor User</TableHead>
                      <TableHead>Occurred (UTC)</TableHead>
                      <TableHead>Sanitized Metadata</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {auditEvents.map((evt) => (
                      <TableRow key={evt.id}>
                        <TableCell className="font-mono text-xs">#{evt.id}</TableCell>
                        <TableCell>
                          <Badge variant="purple">{evt.action_code}</Badge>
                        </TableCell>
                        <TableCell className="text-xs font-mono">{evt.resource_type}</TableCell>
                        <TableCell className="text-xs font-medium">
                          {evt.actor_user_id ? `User #${evt.actor_user_id}` : "SYSTEM"}
                        </TableCell>
                        <TableCell className="text-xs text-slate-500 whitespace-nowrap">
                          {formatDate(evt.occurred_at)}
                        </TableCell>
                        <TableCell className="font-mono text-[10px] text-slate-500 max-w-[200px] truncate">
                          {evt.metadata_redacted ? JSON.stringify(evt.metadata_redacted) : "—"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Session Revocation & Data Retention Administration */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Identity Session Revocation (FR-0066) */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Lock className="w-4 h-4 text-primary" />
                Session Revocation & Access Termination (FR-0066)
              </CardTitle>
              <CardDescription>
                Revoke an active user identity session to immediately terminate access tokens.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRevokeSession} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Target Session ID
                  </label>
                  <input
                    type="number"
                    placeholder="e.g. 12"
                    value={revokeSessionId}
                    onChange={(e) => setRevokeSessionId(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    min="1"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Audit Revocation Reason
                  </label>
                  <input
                    type="text"
                    value={revokeReason}
                    onChange={(e) => setRevokeReason(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    required
                  />
                </div>
                <Button
                  type="submit"
                  variant="destructive"
                  disabled={isRevokingSession}
                  className="w-full flex items-center justify-center gap-2"
                >
                  {isRevokingSession ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                  Revoke Identity Session
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Data Retention Scheduler (FR-0177, FR-0196) */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Database className="w-4 h-4 text-indigo-500" />
                Data Retention & Purge Scheduler (FR-0177)
              </CardTitle>
              <CardDescription>
                Evaluates retention eligibility with strict legal-hold protection and dry-run preview.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRunRetention} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Data Classification
                    </label>
                    <select
                      value={retentionTargetClass}
                      onChange={(e) => setRetentionTargetClass(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    >
                      <option value="KYC_DOCUMENTS">KYC_DOCUMENTS (7 Years)</option>
                      <option value="INACTIVE_SESSIONS">INACTIVE_SESSIONS</option>
                      <option value="PROCESSED_WEBHOOKS">PROCESSED_WEBHOOKS</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Retention Window (Days)
                    </label>
                    <input
                      type="number"
                      value={retentionDays}
                      onChange={(e) => setRetentionDays(parseInt(e.target.value, 10))}
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                      min="1"
                      required
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="dryRun"
                    checked={retentionDryRun}
                    onChange={(e) => setRetentionDryRun(e.target.checked)}
                    className="rounded border-slate-300"
                  />
                  <label htmlFor="dryRun" className="text-xs font-medium text-slate-700 dark:text-slate-300">
                    Dry Run Mode (Simulate count without executing purge)
                  </label>
                </div>

                <Button
                  type="submit"
                  variant={retentionDryRun ? "outline" : "destructive"}
                  disabled={isRunningRetention}
                  className="w-full flex items-center justify-center gap-2"
                >
                  {isRunningRetention ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  {retentionDryRun ? "Execute Retention Dry Run" : "Execute Live Retention Purge"}
                </Button>
              </form>

              {retentionSummary && (
                <div className="mt-4 p-3 border border-slate-100 dark:border-slate-800 rounded-md text-xs space-y-1">
                  <div className="flex justify-between font-semibold">
                    <span>Job #{retentionSummary.job_id} ({retentionSummary.data_class})</span>
                    <Badge variant={retentionSummary.dry_run ? "outline" : "warning"}>
                      {retentionSummary.dry_run ? "DRY_RUN" : "LIVE"}
                    </Badge>
                  </div>
                  <div className="text-slate-500">
                    Evaluated: {retentionSummary.evaluated_records} • Eligible: {retentionSummary.eligible_for_purge} • Purged: {retentionSummary.purged_records} • Legal Hold: {retentionSummary.skipped_due_to_legal_hold}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Data Governance Classification Catalog (FR-0065) */}
        {dataClassification && dataClassification.items && dataClassification.items.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Database className="w-4 h-4 text-purple-500" />
                Data Governance & Sensitive Column Classification Catalog (FR-0065)
              </CardTitle>
              <CardDescription>
                Categorization of database fields into Public, Internal, Confidential, and Restricted PII tiers.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden max-h-64 overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Table Name</TableHead>
                      <TableHead>Column Name</TableHead>
                      <TableHead>Classification Tier</TableHead>
                      <TableHead>Data Type</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dataClassification.items.map((item, idx) => (
                      <TableRow key={`${item.table_name}-${item.column_name}-${idx}`}>
                        <TableCell className="font-mono text-xs">{item.table_name}</TableCell>
                        <TableCell className="font-semibold text-xs">{item.column_name}</TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              item.classification === "RESTRICTED_PII"
                                ? "destructive"
                                : item.classification === "CONFIDENTIAL"
                                ? "warning"
                                : "outline"
                            }
                          >
                            {item.classification}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-xs text-slate-400">
                          {item.data_type}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
