"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth/context";
import {
  Users,
  Briefcase,
  FileText,
  Building2,
  ShieldAlert,
  Search,
  Sparkles,
  KeyRound,
  CreditCard,
  Bell,
  BarChart3,
  CheckCircle2,
  HelpCircle,
  FolderTree,
  Shield,
  GraduationCap,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  roles?: string[];
}

export const NAV_ITEMS: NavItem[] = [
  {
    label: "My Profile",
    href: "/candidates/me",
    icon: Users,
    roles: ["CANDIDATE"],
  },
  {
    label: "Jobs & Requirements",
    href: "/jobs",
    icon: Briefcase,
    roles: ["SUPER_ADMIN", "ADMIN", "ACCOUNT_ADMIN", "EMPLOYER", "RECRUITER", "PLACEMENT_OFFICER", "CANDIDATE"],
  },
  {
    label: "Applications Funnel",
    href: "/applications",
    icon: FileText,
    roles: ["SUPER_ADMIN", "ADMIN", "EMPLOYER", "RECRUITER", "PLACEMENT_OFFICER", "CANDIDATE"],
  },
  {
    label: "Candidate Profiles",
    href: "/candidates",
    icon: Users,
    roles: ["SUPER_ADMIN", "ADMIN", "EMPLOYER", "RECRUITER", "PLACEMENT_OFFICER"],
  },
  {
    label: "Organisations & Teams",
    href: "/organisations",
    icon: Building2,
    roles: ["SUPER_ADMIN", "ADMIN", "ACCOUNT_ADMIN", "EMPLOYER"],
  },
  {
    label: "Gig Marketplace",
    href: "/gigs",
    icon: Sparkles,
    roles: ["SUPER_ADMIN", "ADMIN", "EMPLOYER", "CONSULTANT"],
  },
  {
    label: "Sourcing & Shortlists",
    href: "/sourcing",
    icon: Search,
    roles: ["SUPER_ADMIN", "ADMIN", "EMPLOYER", "RECRUITER", "CONSULTANT"],
  },
  {
    label: "Licences & Seats",
    href: "/licences",
    icon: KeyRound,
    roles: ["SUPER_ADMIN", "ADMIN", "ACCOUNT_ADMIN"],
  },
  {
    label: "Billing & Wallet",
    href: "/billing",
    icon: CreditCard,
    roles: ["SUPER_ADMIN", "ADMIN", "ACCOUNT_ADMIN", "EMPLOYER", "CONSULTANT"],
  },
  {
    label: "Analytics & Marts",
    href: "/analytics",
    icon: BarChart3,
    roles: ["SUPER_ADMIN", "ADMIN", "ACCOUNT_ADMIN", "EMPLOYER", "PLACEMENT_OFFICER"],
  },
  {
    label: "ID Verification",
    href: "/verification",
    icon: CheckCircle2,
    roles: ["SUPER_ADMIN", "ADMIN", "CANDIDATE"],
  },
  {
    label: "Administration & RBAC",
    href: "/administration",
    icon: ShieldAlert,
    roles: ["SUPER_ADMIN", "ADMIN"],
  },
  {
    label: "Master Data",
    href: "/master-data",
    icon: FolderTree,
    roles: ["SUPER_ADMIN", "ADMIN"],
  },
  {
    label: "Notifications & Inbox",
    href: "/notifications",
    icon: Bell,
    roles: ["SUPER_ADMIN", "ADMIN", "ACCOUNT_ADMIN", "EMPLOYER", "RECRUITER", "CONSULTANT", "PLACEMENT_OFFICER", "CANDIDATE"],
  },
  {
    label: "Support & Help",
    href: "/support",
    icon: HelpCircle,
  },
];

export const PORTAL_ITEMS = [
  { label: "Super Admin Portal", href: "/portal/super-admin", icon: Shield, roles: ["SUPER_ADMIN"] },
  { label: "Platform Admin Portal", href: "/portal/admin", icon: ShieldAlert, roles: ["SUPER_ADMIN", "ADMIN"] },
  { label: "Account Admin Portal", href: "/portal/account-admin", icon: Building2, roles: ["SUPER_ADMIN", "ACCOUNT_ADMIN"] },
  { label: "Employer Portal", href: "/portal/employer", icon: Briefcase, roles: ["SUPER_ADMIN", "EMPLOYER"] },
  { label: "Recruiter Portal", href: "/portal/recruiter", icon: Search, roles: ["SUPER_ADMIN", "RECRUITER"] },
  { label: "Consultant Portal", href: "/portal/consultant", icon: Sparkles, roles: ["SUPER_ADMIN", "CONSULTANT"] },
  { label: "Candidate Portal", href: "/portal/candidate", icon: Users, roles: ["SUPER_ADMIN", "CANDIDATE"] },
  { label: "Placement Officer Portal", href: "/portal/placement-officer", icon: GraduationCap, roles: ["SUPER_ADMIN", "PLACEMENT_OFFICER"] },
];

export function Sidebar({ className }: { className?: string }) {
  const pathname = usePathname();
  const { activeRole } = useAuth();

  const filteredNavItems = NAV_ITEMS.filter((item) => {
    if (!item.roles) return true;
    return item.roles.includes(activeRole);
  });

  const filteredPortals = PORTAL_ITEMS.filter((item) => {
    return item.roles.includes(activeRole);
  });

  return (
    <aside
      className={cn(
        "flex flex-col w-64 border-r border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md h-[calc(100vh-4rem)] sticky top-16 transition-all",
        className
      )}
    >
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-4">
        {/* Active Role Portal */}
        <div>
          <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Active Role Portal
          </div>
          {filteredPortals.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-all mb-1",
                  isActive
                    ? "bg-[#4169D8] text-white font-semibold shadow-xs"
                    : "text-[#4169D8] dark:text-[#8AA8FF] bg-[#EAF0FF] dark:bg-[#192440] hover:bg-[#dfe8fd] dark:hover:bg-[#202d50] font-semibold"
                )}
              >
                <Icon className={cn("h-4 w-4 shrink-0", isActive ? "text-white" : "text-[#4169D8] dark:text-[#8AA8FF]")} />
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Main Workspaces */}
        <div>
          <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Platform Modules
          </div>
          <div className="space-y-0.5">
            {filteredNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                    isActive
                      ? "bg-[#EAF0FF] dark:bg-[#192440] text-[#4169D8] dark:text-[#8AA8FF] font-semibold"
                      : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200"
                  )}
                >
                  <Icon className={cn("h-4 w-4 shrink-0", isActive ? "text-[#4169D8] dark:text-[#8AA8FF]" : "text-slate-400")} />
                  <span className="truncate">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>

      {/* Contract Baseline Footer */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 text-[11px] text-slate-400 dark:text-slate-500">
        <div className="flex items-center justify-between">
          <span>FastAPI / Supabase</span>
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-500" title="Connected" />
        </div>
        <div className="text-[10px] text-slate-400 mt-0.5">Stage 17B Portals Active</div>
      </div>
    </aside>
  );
}
