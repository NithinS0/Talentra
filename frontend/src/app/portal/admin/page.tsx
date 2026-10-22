"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ShieldCheck, Users, ArrowRight, CheckCircle2, ShieldAlert } from "lucide-react";
import { listAdminUsers } from "@/lib/api/admin";
import { AdminUserResponse } from "@/types/admin";
import { formatDate } from "@/lib/utils";

export default function AdminPortalPage() {
  const [users, setUsers] = useState<AdminUserResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadAdminOperations() {
      try {
        setLoading(true);
        const res = await listAdminUsers({ page_size: 10 });
        if (isMounted && res?.items) {
          setUsers(res.items);
        }
      } catch (err) {
        console.error("Failed to load operations admin data:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadAdminOperations();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <PortalShell
      allowedRoles={["ADMIN", "SUPER_ADMIN"]}
      portalName="Platform Operations Admin Portal"
      portalDescription="Identity compliance queues, tenant user administration, support escalations, and dispute reviews."
      badgeLabel="Platform Admin"
      breadcrumbs={[{ label: "Portals" }, { label: "Operations Admin" }]}
    >
      <div className="space-y-6">
        {/* ─── Operations Header Strip ───────────────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Operations & Compliance Oversight
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Identity verification queues, account standing, and customer dispute resolution.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <Link href="/verification">
              <Button variant="outline" size="sm" className="h-8 text-xs font-medium gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                ID Verification Queue
              </Button>
            </Link>
            <Link href="/administration">
              <Button size="sm" className="h-8 text-xs font-medium gap-1.5">
                <Users className="h-3.5 w-3.5" />
                User Directory
              </Button>
            </Link>
          </div>
        </div>

        {/* ─── User Accounts Under Administration Table ──────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-[#4169D8]" />
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                Active Tenant Accounts
              </h3>
            </div>
            <Link href="/administration" className="text-xs text-[#4169D8] hover:underline font-medium">
              View All Users
            </Link>
          </div>

          {loading ? (
            <div className="py-12 text-center text-xs text-slate-500">
              Loading tenant user records...
            </div>
          ) : users.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">User Identity</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Assigned Roles</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Created Date</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Account Status</TableHead>
                    <TableHead className="text-right text-xs uppercase font-semibold text-slate-500">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((u) => (
                    <TableRow key={u.id} className="text-xs">
                      <TableCell>
                        <div className="font-semibold text-slate-900 dark:text-white">
                          {u.display_name || u.email_address}
                        </div>
                        <div className="text-[11px] text-slate-500">
                          {u.email_address}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {u.roles?.map((r) => (
                            <Badge key={r} variant="outline" className="text-[9px] font-mono">
                              {r}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-500">
                        {formatDate(u.created_at)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={u.account_status_code_id === 1 ? "success" : "destructive"}
                          className="text-[10px] font-medium"
                        >
                          {u.account_status || (u.account_status_code_id === 1 ? "ACTIVE" : "SUSPENDED")}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href="/administration">
                          <Button variant="ghost" size="sm" className="h-7 text-xs px-2 text-[#4169D8]">
                            Review
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-500">
              No user accounts found under current search scope.
            </div>
          )}
        </div>

        {/* ─── Operations Shortcuts ───────────────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link href="/verification" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  ID Verification Review
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Review pending candidate government ID documents and confirm verification standing.
              </p>
            </div>
          </Link>

          <Link href="/administration" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  User Account Controls
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Manage credential locks, session revocations, and user password resets.
              </p>
            </div>
          </Link>

          <Link href="/support" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Support & Escalations
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Resolve tenant support inquiries, dispute tickets, and platform appeals.
              </p>
            </div>
          </Link>
        </div>
      </div>
    </PortalShell>
  );
}
