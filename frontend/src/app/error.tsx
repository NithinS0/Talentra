"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertOctagon, RefreshCw, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log exception to client console
    console.error("Talentra Application Error Boundary Caught:", error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-50 dark:bg-slate-950">
      <Card className="max-w-md w-full border-red-200 dark:border-red-900/50 text-center shadow-xl">
        <CardHeader className="space-y-2 pb-4">
          <div className="mx-auto h-16 w-16 rounded-2xl bg-red-100 dark:bg-red-950/60 text-red-600 dark:text-red-400 flex items-center justify-center">
            <AlertOctagon className="h-8 w-8" />
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Application Error
          </CardTitle>
          <CardDescription className="text-sm">
            An unexpected error occurred while executing this component.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-xs font-mono text-left text-red-700 dark:text-red-300 overflow-x-auto">
            {error.message || "Unknown error encountered"}
          </div>

          <div className="flex flex-col sm:flex-row gap-2 pt-2">
            <Button variant="primary" onClick={() => reset()} className="flex-1 gap-2">
              <RefreshCw className="h-4 w-4" />
              Try Again
            </Button>
            <Link href="/dashboard" className="flex-1">
              <Button variant="outline" className="w-full gap-2">
                <Home className="h-4 w-4" />
                Dashboard
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
