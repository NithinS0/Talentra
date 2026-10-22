"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Header } from "./header";
import { Sidebar } from "./sidebar";
import { Breadcrumbs } from "./breadcrumbs";
import { useAuth } from "@/lib/auth/context";
import { Loader2 } from "lucide-react";

interface DashboardShellProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  title?: string;
  breadcrumbs?: { label: string; href?: string }[];
}

export function DashboardShell({ children, requireAuth = true }: DashboardShellProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && requireAuth && !isAuthenticated) {
      router.push("/sign-in");
    }
  }, [isLoading, requireAuth, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--background)]">
        <div className="flex flex-col items-center space-y-3">
          <Loader2 className="h-8 w-8 animate-spin text-[#4169D8]" />
          <p className="text-sm font-medium text-slate-500">Initializing Talentra Platform...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)]">
      <Header />
      <div className="flex flex-1">
        <Sidebar className="hidden md:flex shrink-0" />
        <main className="flex-1 overflow-y-auto px-4 sm:px-8 py-6 max-w-7xl mx-auto w-full">
          <Breadcrumbs />
          <div className="mt-2">{children}</div>
        </main>
      </div>
    </div>
  );
}
