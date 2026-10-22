"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Sparkles, DollarSign, ArrowRight, FileText, CheckCircle2 } from "lucide-react";
import { listGigRequests } from "@/lib/api/gig";
import { GigRequestResponse } from "@/types/gig";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function ConsultantPortalPage() {
  const [gigs, setGigs] = useState<GigRequestResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadConsultantData() {
      try {
        setLoading(true);
        const gigsRes = await listGigRequests({ limit: 5 });
        if (isMounted && gigsRes?.items) {
          setGigs(gigsRes.items);
        }
      } catch (err) {
        console.error("Failed to load consultant data:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadConsultantData();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <PortalShell
      allowedRoles={["CONSULTANT", "SUPER_ADMIN"]}
      portalName="Sourcing Consultant Portal"
      portalDescription="Manage technical screening mandates, submit expert assessments, and track consulting fee disbursements."
      badgeLabel="Consultant"
      breadcrumbs={[{ label: "Portals" }, { label: "Consultant" }]}
    >
      <div className="space-y-6">
        {/* ─── Consultant Workspace Header ───────────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Gig Engagements & Deliverables
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Technical screening assignments, candidate evaluations, and milestone disbursements.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <Link href="/gigs">
              <Button size="sm" className="h-8 text-xs font-medium gap-1.5">
                <Sparkles className="h-3.5 w-3.5" />
                Gig Marketplace
              </Button>
            </Link>
          </div>
        </div>

        {/* ─── Active Gig Deliverables Table ─────────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-[#4169D8]" />
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                Active Gig Assignments
              </h3>
            </div>
            <Link href="/gigs" className="text-xs text-[#4169D8] hover:underline font-medium">
              View All Gigs
            </Link>
          </div>

          {loading ? (
            <div className="py-12 text-center text-xs text-slate-500">
              Loading gig assignments...
            </div>
          ) : gigs.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Assignment Title</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Hiring Client</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Budget / Escrow</TableHead>
                    <TableHead className="text-xs uppercase font-semibold text-slate-500">Status</TableHead>
                    <TableHead className="text-right text-xs uppercase font-semibold text-slate-500">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {gigs.map((gig) => (
                    <TableRow key={gig.id} className="text-xs">
                      <TableCell>
                        <div className="font-semibold text-slate-900 dark:text-white">
                          {gig.title}
                        </div>
                        <div className="text-[11px] text-slate-500">
                          GIG-{String(gig.id).padStart(5, "0")}
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-600 dark:text-slate-400">
                        {gig.organisation_name || "Enterprise Client"}
                      </TableCell>
                      <TableCell className="font-semibold text-slate-900 dark:text-white">
                        {gig.price_amount ? formatCurrency(gig.price_amount) : "Milestone Based"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={gig.status === "OPEN" || gig.status === "ASSIGNED" ? "success" : "default"}
                          className="text-[10px] font-medium"
                        >
                          {gig.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/gigs/${gig.id}`}>
                          <Button variant="ghost" size="sm" className="h-7 text-xs px-2 text-[#4169D8]">
                            Details
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
                  No active gig assignments
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Browse the Gig Marketplace to bid on technical screening mandates.
                </p>
              </div>
              <Link href="/gigs">
                <Button size="sm" className="h-8 text-xs font-medium">
                  Explore Gig Marketplace
                </Button>
              </Link>
            </div>
          )}
        </div>

        {/* ─── Consultant Actions ─────────────────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link href="/gigs" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Open Gig Marketplace
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Discover contracts requiring specialized candidate evaluation and code review.
              </p>
            </div>
          </Link>

          <Link href="/sourcing" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Sourcing Requests
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Review client candidate criteria and submit matched profile recommendations.
              </p>
            </div>
          </Link>

          <Link href="/billing" className="group">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] transition-colors">
              <div className="flex items-center justify-between pb-1.5">
                <span className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] transition-colors">
                  Wallet & Disbursements
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4169D8] transition-colors" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Inspect milestone payouts, settlement timelines, and ledger balance.
              </p>
            </div>
          </Link>
        </div>
      </div>
    </PortalShell>
  );
}
