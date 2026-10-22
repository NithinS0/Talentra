"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Building2, KeyRound, CreditCard, ArrowRight, Users, FileText } from "lucide-react";
import { listOrganisations } from "@/lib/api/organisations";
import { getSubscriptionPlans } from "@/lib/api/subscriptions";
import { OrganisationResponse } from "@/types/organisations";
import { SubscriptionPlanResponse } from "@/types/subscriptions";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function AccountAdminPortalPage() {
  const [organisations, setOrganisations] = useState<OrganisationResponse[]>([]);
  const [plans, setPlans] = useState<SubscriptionPlanResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadAccountData() {
      try {
        setLoading(true);
        const [orgsRes, plansRes] = await Promise.allSettled([
          listOrganisations({ page_size: 5 }),
          getSubscriptionPlans(),
        ]);

        if (!isMounted) return;

        if (orgsRes.status === "fulfilled" && orgsRes.value?.items) {
          setOrganisations(orgsRes.value.items);
        }
        if (plansRes.status === "fulfilled" && Array.isArray(plansRes.value)) {
          setPlans(plansRes.value);
        }
      } catch (err) {
        console.error("Failed to load account admin data:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadAccountData();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <PortalShell
      allowedRoles={["ACCOUNT_ADMIN", "SUPER_ADMIN"]}
      portalName="Account Administrator Portal"
      portalDescription="Tenant organisation root, seat licence allocation, subscription billing, and invoice receipts."
      badgeLabel="Tenant Root"
      breadcrumbs={[{ label: "Portals" }, { label: "Account Admin" }]}
    >
      <div className="space-y-6">
        {/* ─── Tenant Overview Header ────────────────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Organisation Tenant Administration
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Manage authorized recruiter seats, team memberships, and enterprise subscription renewals.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <Link href="/billing">
              <Button variant="outline" size="sm" className="h-8 text-xs font-medium gap-1.5">
                <CreditCard className="h-3.5 w-3.5" />
                Subscription & Billing
              </Button>
            </Link>
            <Link href="/organisations">
              <Button size="sm" className="h-8 text-xs font-medium gap-1.5">
                <Building2 className="h-3.5 w-3.5" />
                Manage Team
              </Button>
            </Link>
          </div>
        </div>

        {/* ─── Tenant Organizations Table ─────────────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-[#4169D8]" />
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                Authorized Tenant Entity & Profiles
              </h3>
            </div>
            <Link href="/organisations" className="text-xs text-[#4169D8] hover:underline font-medium">
              View All Organisations
            </Link>
          </div>

          {loading ? (
            <div className="py-12 text-center text-xs text-slate-500">
              Loading organization details...
            </div>
          ) : organisations.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Organisation Name</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Jurisdiction / Country</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Created Date</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Status</TableHead>
                    <TableHead className="text-right text-xs uppercase font-semibold text-slate-500">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {organisations.map((org) => (
                    <TableRow key={org.id} className="text-xs">
                      <TableCell>
                        <div className="font-semibold text-slate-900 dark:text-white">
                          {org.display_name || org.legal_name}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono">
                          ORG-{String(org.id).padStart(5, "0")}
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-600 dark:text-slate-400">
                        {org.country_name || "Global / Multi-region"}
                      </TableCell>
                      <TableCell className="text-slate-500">
                        {formatDate(org.created_at)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="success"
                          className="text-[10px] font-medium"
                        >
                          ACTIVE
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/organisations/${org.id}`}>
                          <Button variant="ghost" size="sm" className="h-7 text-xs px-2 text-[#4169D8]">
                            Configure
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-500 space-y-2">
              <FileText className="h-7 w-7 text-slate-300 dark:text-slate-700 mx-auto" />
              <p className="font-medium text-slate-700 dark:text-slate-300">
                No organizations registered under this account
              </p>
              <p className="text-[11px] text-slate-500">
                Register your corporate entity to invite recruiters and publish campus jobs.
              </p>
              <Link href="/organisations">
                <Button size="sm" className="h-8 text-xs font-medium">
                  Register Organisation
                </Button>
              </Link>
            </div>
          )}
        </div>

        {/* ─── Available Subscription Plans ───────────────────────────────── */}
        {plans.length > 0 && (
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
              <div className="flex items-center gap-2">
                <CreditCard className="h-4 w-4 text-[#4169D8]" />
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                  Available Subscription Plans & Seat Capacities
                </h3>
              </div>
              <Link href="/billing" className="text-xs text-[#4169D8] hover:underline font-medium">
                Billing Console
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
              {plans.slice(0, 3).map((plan) => (
                <div
                  key={plan.id}
                  className="p-4 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-[#181E29] flex flex-col justify-between"
                >
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 dark:text-white">
                        {plan.plan_name}
                      </span>
                      <Badge variant="outline" className="text-[10px] font-mono">
                        {plan.plan_code}
                      </Badge>
                    </div>
                    <div className="text-lg font-bold text-[#4169D8] dark:text-[#8AA8FF] pt-1">
                      {formatCurrency(Number(plan.price_amount) || 0)}
                      <span className="text-xs font-normal text-slate-400"> / cycle</span>
                    </div>
                    <p className="text-[11px] text-slate-500">
                      Up to {plan.max_seats} Recruiter Seats
                    </p>
                  </div>
                  <div className="pt-3">
                    <Link href="/billing">
                      <Button variant="outline" size="sm" className="w-full h-7 text-xs">
                        View Plan
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ─── Tenant Admin Shortcuts ─────────────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link href="/organisations" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Team Members & Invites
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Invite hiring managers and recruiters to your authorized organization tenant.
              </p>
            </div>
          </Link>

          <Link href="/licences" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Seat & Session Controls
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Monitor concurrent recruiter logins, devices, and seat reallocation rules.
              </p>
            </div>
          </Link>

          <Link href="/billing" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Subscription & Invoices
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Review payment receipts, ledger tax invoices, and renewal terms.
              </p>
            </div>
          </Link>
        </div>
      </div>
    </PortalShell>
  );
}
