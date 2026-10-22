"use client";

import Link from "next/link";
import { ShieldAlert, Home, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useAuth } from "@/lib/auth/context";

export default function ForbiddenPage() {
  const { session } = useAuth();

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-50 dark:bg-slate-950">
      <Card className="max-w-md w-full border-slate-200 dark:border-slate-800 text-center shadow-xl">
        <CardHeader className="space-y-2 pb-4">
          <div className="mx-auto h-16 w-16 rounded-2xl bg-red-100 dark:bg-red-950/60 text-red-600 dark:text-red-400 flex items-center justify-center">
            <ShieldAlert className="h-8 w-8" />
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            403 — Access Forbidden
          </CardTitle>
          <CardDescription className="text-sm">
            Your current actor identity does not possess the permissions required to access this endpoint or view this resource.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-3 rounded-lg bg-slate-100 dark:bg-slate-800/60 text-xs font-mono text-left space-y-1 text-slate-700 dark:text-slate-300">
            <div>Current Actor ID: <span className="font-bold text-indigo-600 dark:text-indigo-400">{session?.activeActorId || "ANONYMOUS"}</span></div>
            <div>Authorized Role: <span className="font-bold">{session?.activeRole || "NONE"}</span></div>
            <div>Enforcement Tier: <span className="text-emerald-600">FastAPI Authoritative RBAC</span></div>
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400">
            If you need access to this resource, switch to an authorized administrative persona or contact your organization administrator.
          </p>

          <div className="flex flex-col sm:flex-row gap-2 pt-2">
            <Link href="/dashboard" className="flex-1">
              <Button variant="primary" className="w-full gap-2">
                <Home className="h-4 w-4" />
                Return to Dashboard
              </Button>
            </Link>
            <Link href="/sign-in" className="flex-1">
              <Button variant="outline" className="w-full gap-2">
                <LogIn className="h-4 w-4" />
                Switch Persona
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
