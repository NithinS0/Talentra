"use client";

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { DashboardShell } from "./dashboard-shell";
import { useAuth } from "@/lib/auth/context";
import { RoleCode } from "@/types/auth";
import { Badge } from "@/components/ui/badge";
import { ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { getPortalPathForRole } from "@/lib/auth/session";

interface PortalShellProps {
  children: React.ReactNode;
  allowedRoles: RoleCode[];
  portalName: string;
  portalDescription: string;
  badgeLabel?: string;
  breadcrumbs: { label: string; href?: string }[];
}

export function PortalShell({
  children,
  allowedRoles,
  portalName,
  portalDescription,
  badgeLabel,
  breadcrumbs,
}: PortalShellProps) {
  const { user, activeRole, activeActorId, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const isRoleAuthorized = allowedRoles.includes(activeRole) || activeRole === "SUPER_ADMIN";

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push(`/sign-in?returnUrl=${encodeURIComponent(pathname)}`);
      } else if (!isRoleAuthorized) {
        // Redirect to forbidden page if trying to access unauthorized portal
        router.push("/forbidden");
      }
    }
  }, [isLoading, isAuthenticated, isRoleAuthorized, pathname, router]);

  if (isLoading) {
    return (
      <DashboardShell requireAuth={true} breadcrumbs={breadcrumbs}>
        <div className="py-12 flex justify-center text-slate-500 text-sm">
          Verifying role authorization...
        </div>
      </DashboardShell>
    );
  }

  if (!isRoleAuthorized) {
    return (
      <DashboardShell requireAuth={true} breadcrumbs={breadcrumbs}>
        <div className="p-8 text-center max-w-lg mx-auto space-y-4">
          <div className="h-12 w-12 rounded-xl bg-red-100 dark:bg-red-950 text-red-600 flex items-center justify-center mx-auto">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <h2 className="text-xl font-bold">Unauthorized Portal Destination</h2>
          <p className="text-sm text-slate-500">
            Your active role <span className="font-semibold text-slate-900 dark:text-slate-100">{activeRole}</span> ({activeActorId})
            is not permitted to enter the {portalName}.
          </p>
          <div className="flex justify-center gap-3">
            <Link href={getPortalPathForRole(activeRole)}>
              <Button>Return to Authorized Portal</Button>
            </Link>
          </div>
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell requireAuth={true} title={portalName} breadcrumbs={breadcrumbs}>
      <div className="space-y-6">
        {/* Portal Header Card */}
        <div className="rounded-xl bg-white dark:bg-[#11151D] border border-slate-200 dark:border-slate-800 p-5 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {portalName}
                </h1>
                <Badge variant={activeRole === "SUPER_ADMIN" ? "destructive" : "default"}>
                  {badgeLabel || activeRole}
                </Badge>
              </div>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                {portalDescription}
              </p>
            </div>

            <div className="flex items-center gap-2.5 shrink-0">
              <div className="px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-[#181E29] border border-slate-200 dark:border-slate-800 text-xs">
                <span className="text-slate-500 dark:text-slate-400 block text-[10px] uppercase font-semibold">Active Actor ID</span>
                <span className="font-mono font-bold text-[#4169D8] dark:text-[#8AA8FF] text-xs">
                  {activeActorId}
                </span>
              </div>
              <div className="px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-[#181E29] border border-slate-200 dark:border-slate-800 text-xs">
                <span className="text-slate-500 dark:text-slate-400 block text-[10px] uppercase font-semibold">Identity</span>
                <span suppressHydrationWarning className="font-medium text-slate-800 dark:text-slate-200 text-xs truncate max-w-[140px] block">
                  {user?.display_name || "Authorized User"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Portal Content */}
        {children}
      </div>
    </DashboardShell>
  );
}
