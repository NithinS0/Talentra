import Link from "next/link";
import { FileQuestion, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-50 dark:bg-slate-950">
      <Card className="max-w-md w-full border-slate-200 dark:border-slate-800 text-center shadow-xl">
        <CardHeader className="space-y-2 pb-4">
          <div className="mx-auto h-16 w-16 rounded-2xl bg-amber-100 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center">
            <FileQuestion className="h-8 w-8" />
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            404 — Page Not Found
          </CardTitle>
          <CardDescription className="text-sm">
            The requested route or resource could not be found within the Talentra application matrix.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Stage 17A establishes the application framework, navigation shells, and token system. The complete 36 pages are scheduled for Stage 17B.
          </p>

          <div className="flex justify-center pt-2">
            <Link href="/dashboard">
              <Button variant="primary" className="gap-2">
                <Home className="h-4 w-4" />
                Return to Workspace
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
