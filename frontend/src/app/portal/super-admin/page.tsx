"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ShieldAlert, Server, Users, ArrowRight, ShieldCheck, FileText } from "lucide-react";
import { listAuditEvents, listAdminUsers } from "@/lib/api/admin";
import { checkBackendHealth } from "@/lib/api/auth";
import { AuditEventResponse, AdminUserResponse } from "@/types/admin";
import { formatDate } from "@/lib/utils";

export default function SuperAdminPortalPage() {
  const [auditEvents, setAuditEvents] = useState<AuditEventResponse[]>([]);
  const [users, setUsers] = useState<AdminUserResponse[]>([]);
  const [healthStatus, setHealthStatus] = useState<string>("checking...");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadAdminData() {
      try {
        setLoading(true);
        const [auditRes, usersRes, healthRes] = await Promise.allSettled([
          listAuditEvents({ page_size: 5 }),
          listAdminUsers({ page_size: 5 }),
          checkBackendHealth(),
        ]);

        if (!isMounted) return;

        if (auditRes.status === "fulfilled" && auditRes.value?.items) {
          setAuditEvents(auditRes.value.items);
        }
        if (usersRes.status === "fulfilled" && usersRes.value?.items) {
          setUsers(usersRes.value.items);
        }
        if (healthRes.status === "fulfilled") {
          setHealthStatus(healthRes.value?.status || "healthy");
        }
      } catch (err) {
        console.error("Failed to load Super Admin data:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadAdminData();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <PortalShell
      allowedRoles={["SUPER_ADMIN"]}
      portalName="Super Admin Governance Portal"
      portalDescription="Global platform governance, RBAC role administration, audit compliance logs, and security oversight."
      badgeLabel="Tier 0 Root"
      breadcrumbs={[{ label: "Portals" }, { label: "Super Admin" }]}
    >
      <div className="space-y-6">
        {/* ─── Governance Header Strip ───────────────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Platform Health & Security Governance
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              System health: <span className="font-semibold text-emerald-600 dark:text-emerald-400">{healthStatus}</span> · Enforcing double-entry ledger and immutable audit compliance.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <Link href="/master-data">
              <Button variant="outline" size="sm" className="h-8 text-xs font-medium">
                Master Data
              </Button>
            </Link>
            <Link href="/administration">
              <Button size="sm" className="h-8 text-xs font-medium gap-1.5">
                <Users className="h-3.5 w-3.5" />
                Manage Users
              </Button>
            </Link>
          </div>
        </div>

        {/* ─── Recent Audit Events Table ─────────────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-[#4169D8]" />
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                Immutable Security & Audit Log
              </h3>
            </div>
            <Link href="/administration" className="text-xs text-[#4169D8] hover:underline font-medium">
              View Audit Console
            </Link>
          </div>

          {loading ? (
            <div className="py-12 text-center text-xs text-slate-500">
              Loading security audit events...
            </div>
          ) : auditEvents.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Timestamp</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Actor Identity</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Event Action</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Severity</TableHead>
                    <TableHead className="text-right text-xs uppercase font-semibold text-slate-500">Target Resource</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {auditEvents.map((evt) => (
                    <TableRow key={evt.id} className="text-xs">
                      <TableCell className="font-mono text-slate-500">
                        {formatDate(evt.occurred_at)}
                      </TableCell>
                      <TableCell>
                        <span className="font-semibold text-slate-900 dark:text-white font-mono">
                          {evt.actor_user_id ? `USR-${evt.actor_user_id}` : "SYSTEM"}
                        </span>
                      </TableCell>
                      <TableCell className="font-mono text-slate-700 dark:text-slate-300">
                        {evt.action_code}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className="text-[10px] font-mono text-[#4169D8]"
                        >
                          AUDIT_LOG
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-mono text-slate-500 text-[11px]">
                        {evt.resource_type || "SYSTEM"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-500">
              <ShieldCheck className="h-7 w-7 text-emerald-500 mx-auto mb-1.5" />
              <p className="font-medium text-slate-700 dark:text-slate-300">No anomalous security events detected</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Audit log records are immutable and retained under 7-year regulatory compliance.</p>
            </div>
          )}
        </div>

        {/* ─── Quick Admin Navigation ─────────────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link href="/administration" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  RBAC User Governance
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Inspect platform accounts, enforce session revocations, and manage security locks.
              </p>
            </div>
          </Link>

          <Link href="/licences" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Tenant Licence Mart
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Review seat quotas, device concurrency caps, and tenant licence allocations.
              </p>
            </div>
          </Link>

          <Link href="/master-data" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Master Data Catalogs
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Update industry classifications, academic disciplines, and standard skill taxonomies.
              </p>
            </div>
          </Link>
        </div>
      </div>
    </PortalShell>
  );
}
