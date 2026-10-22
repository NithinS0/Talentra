"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Briefcase,
  Search,
  FileText,
  Building2,
  CheckCircle2,
  KeyRound,
  Shield,
  GraduationCap,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  Server,
} from "lucide-react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth/context";
import { checkBackendHealth } from "@/lib/api/auth";
import { getPortalPathForRole } from "@/lib/auth/session";

export default function DashboardPage() {
  const { session, user } = useAuth();
  const [backendHealth, setBackendHealth] = useState<string>("checking...");
  const [dbHealthy, setDbHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function testHealth() {
      try {
        const res = await checkBackendHealth();
        if (isMounted) {
          setBackendHealth(res.status || "healthy");
          setDbHealthy(res.database === "connected" || res.status === "healthy");
        }
      } catch {
        if (isMounted) {
          setBackendHealth("offline (mock session active)");
          setDbHealthy(false);
        }
      }
    }
    testHealth();
    return () => {
      isMounted = false;
    };
  }, []);

  const activeRole = session?.activeRole || "CANDIDATE";
  const actorId = session?.activeActorId || "CA00001";
  const portalPath = getPortalPathForRole(activeRole);

  return (
    <DashboardShell
      title="Workspace Overview"
      breadcrumbs={[{ label: "Workspace" }, { label: "Overview" }]}
    >
      <div className="space-y-6">
        {/* ─── Compact Header & Identity Strip ───────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  Workspace Overview
                </h1>
                <Badge variant="outline" className="font-mono text-xs">
                  {actorId}
                </Badge>
              </div>
              <p
                suppressHydrationWarning
                className="text-xs sm:text-sm text-slate-500 dark:text-slate-400"
              >
                Welcome back, {user?.display_name || "Authorized Operator"}. Your active session is authorized as{" "}
                <span className="font-semibold text-slate-900 dark:text-slate-200">
                  {activeRole.replace(/_/g, " ")}
                </span>
                .
              </p>
            </div>

            {/* Quick Actions & Status */}
            <div className="flex items-center gap-3 shrink-0">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-[#181E29] text-xs">
                <Server className="h-3.5 w-3.5 text-slate-400" />
                <span className="text-slate-500 dark:text-slate-400 text-[11px]">Backend API:</span>
                <span className="font-mono font-bold flex items-center gap-1.5 text-xs text-slate-800 dark:text-slate-200">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      dbHealthy ? "bg-emerald-500" : "bg-amber-500"
                    }`}
                  />
                  {backendHealth}
                </span>
              </div>

              <Link href={portalPath}>
                <Button size="sm" className="gap-1.5 h-8 text-xs font-medium">
                  Enter {activeRole.replace(/_/g, " ")} Portal
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* ─── Active Portal Highlight Card ──────────────────────────────── */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] p-5 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-[#4169D8] dark:text-[#8AA8FF]">
                  Current Primary Workspace
                </span>
              </div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                {activeRole.replace(/_/g, " ")} Dedicated Portal
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-2xl">
                Access your specialized operational dashboard, review tasks, manage workflows, and inspect live pipelines configured for your assigned role permissions.
              </p>
            </div>
            <Link href={portalPath}>
              <Button className="h-9 px-4 text-xs font-medium shrink-0">
                Open Primary Workspace
              </Button>
            </Link>
          </div>
        </div>

        {/* ─── Core Platform Workspaces Grid ─────────────────────────────── */}
        <div>
          <div className="mb-3">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
              Platform Modules
            </h3>
            <p className="text-xs text-slate-500">
              Direct access to verified Talentra workspaces based on role eligibility.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
            {[
              {
                title: "Jobs & Requirements",
                desc: "Discover opportunities, review criteria, and track openings.",
                href: "/jobs",
                icon: Briefcase,
                roles: ["CANDIDATE", "EMPLOYER", "RECRUITER", "PLACEMENT_OFFICER", "SUPER_ADMIN"],
              },
              {
                title: "Applications Funnel",
                desc: "Review submitted profiles, interview stages, and offers.",
                href: "/applications",
                icon: FileText,
                roles: ["CANDIDATE", "EMPLOYER", "RECRUITER", "PLACEMENT_OFFICER", "SUPER_ADMIN"],
              },
              {
                title: "Sourcing & Shortlists",
                desc: "Filter talent pools, manage candidate lists, and outreach.",
                href: "/sourcing",
                icon: Search,
                roles: ["EMPLOYER", "RECRUITER", "CONSULTANT", "SUPER_ADMIN"],
              },
              {
                title: "ID Verification",
                desc: "Submit consent and verify official government identity documents.",
                href: "/verification",
                icon: CheckCircle2,
                roles: ["CANDIDATE", "ADMIN", "SUPER_ADMIN"],
              },
              {
                title: "Organisations & Teams",
                desc: "Manage company settings, authorized members, and branding.",
                href: "/organisations",
                icon: Building2,
                roles: ["ACCOUNT_ADMIN", "EMPLOYER", "ADMIN", "SUPER_ADMIN"],
              },
              {
                title: "Gig Marketplace",
                desc: "Browse specialized consulting assignments and milestones.",
                href: "/gigs",
                icon: Sparkles,
                roles: ["CONSULTANT", "EMPLOYER", "SUPER_ADMIN"],
              },
              {
                title: "Licences & Seats",
                desc: "Seat allocation, concurrent sessions, and device tracking.",
                href: "/licences",
                icon: KeyRound,
                roles: ["ACCOUNT_ADMIN", "ADMIN", "SUPER_ADMIN"],
              },
              {
                title: "Administration & RBAC",
                desc: "System governance, user locking, and audit verification.",
                href: "/administration",
                icon: ShieldAlert,
                roles: ["ADMIN", "SUPER_ADMIN"],
              },
            ]
              .filter((item) => item.roles.includes(activeRole) || activeRole === "SUPER_ADMIN")
              .map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-[#4169D8] dark:hover:border-[#8AA8FF] transition-colors group flex flex-col justify-between"
                  >
                    <div className="space-y-2">
                      <div className="h-8 w-8 rounded-lg bg-[#EAF0FF] dark:bg-[#192440] text-[#4169D8] dark:text-[#8AA8FF] flex items-center justify-center">
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#4169D8] dark:group-hover:text-[#8AA8FF] transition-colors">
                        {item.title}
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                        {item.desc}
                      </p>
                    </div>
                    <div className="mt-3 flex items-center gap-1 text-[11px] font-medium text-[#4169D8] dark:text-[#8AA8FF]">
                      <span>Open Workspace</span>
                      <ArrowRight className="h-3 w-3" />
                    </div>
                  </Link>
                );
              })}
          </div>
        </div>

        {/* ─── Role Portals Reference Grid ───────────────────────────────── */}
        <div>
          <div className="mb-3">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
              Authorized Persona Portals (8 Portals)
            </h3>
            <p className="text-xs text-slate-500">
              Role-specific workflows protected by backend FastAPI authorization checks.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
            {[
              { role: "CANDIDATE", title: "Candidate", prefix: "CA", path: "/portal/candidate", desc: "Profile readiness, jobs, and application tracking", icon: GraduationCap },
              { role: "EMPLOYER", title: "Employer", prefix: "EM", path: "/portal/employer", desc: "Job requisitions, applicant review, and hiring", icon: Briefcase },
              { role: "RECRUITER", title: "Recruiter", prefix: "RE", path: "/portal/recruiter", desc: "Candidate sourcing, shortlists, and screening", icon: Search },
              { role: "PLACEMENT_OFFICER", title: "Placement Officer", prefix: "PO", path: "/portal/placement-officer", desc: "Campus recruitment drives and student rosters", icon: GraduationCap },
              { role: "CONSULTANT", title: "Consultant", prefix: "CO", path: "/portal/consultant", desc: "Sourcing gig deliverables and milestones", icon: Sparkles },
              { role: "ACCOUNT_ADMIN", title: "Account Admin", prefix: "AA", path: "/portal/account-admin", desc: "Tenant profile, team seats, and subscriptions", icon: Building2 },
              { role: "ADMIN", title: "Platform Admin", prefix: "AD", path: "/portal/admin", desc: "Compliance reviews, disputes, and operational oversight", icon: Shield },
              { role: "SUPER_ADMIN", title: "Super Admin", prefix: "SA", path: "/portal/super-admin", desc: "Global configuration, security audits, and system health", icon: ShieldAlert },
            ].map((p) => {
              const isCurrent = activeRole === p.role;
              const Icon = p.icon;
              return (
                <Link key={p.path} href={p.path} className="group">
                  <div
                    className={`p-3.5 rounded-xl border transition-all ${
                      isCurrent
                        ? "border-[#4169D8] dark:border-[#8AA8FF] bg-[#EAF0FF]/50 dark:bg-[#192440]/50"
                        : "border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11151D] hover:border-slate-300 dark:hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between pb-1.5">
                      <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {p.prefix}-Series
                      </span>
                      {isCurrent ? (
                        <Badge variant="default" className="text-[10px] px-1.5 py-0 font-medium">
                          ACTIVE
                        </Badge>
                      ) : (
                        <ArrowRight className="h-3 w-3 text-slate-400 group-hover:text-slate-600 transition-colors" />
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 mt-1">
                      <Icon className="h-3.5 w-3.5 text-slate-500" />
                      <div className="text-xs font-bold text-slate-900 dark:text-white">
                        {p.title}
                      </div>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                      {p.desc}
                    </p>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
