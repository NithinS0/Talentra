"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  Building,
  Calendar,
  DollarSign,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Send,
  Shield,
  FileCheck,
} from "lucide-react";
import { getGigRequestDetails, applyToGigRequest } from "@/lib/api/gig";
import { GigRequestResponse } from "@/types/gig";
import { useAuth } from "@/lib/auth/context";
import { formatDate } from "@/lib/utils";

interface PageProps {
  params: Promise<{ gigId: string }>;
}

export default function GigDetailPage({ params }: PageProps) {
  const router = useRouter();
  const { activeRole } = useAuth();
  const resolvedParams = use(params);
  const gigId = parseInt(resolvedParams.gigId, 10);

  const [gig, setGig] = useState<GigRequestResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Proposal submission state
  const [showApplyForm, setShowApplyForm] = useState(false);
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadGig() {
      if (isNaN(gigId)) {
        setError("Invalid Gig ID");
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const data = await getGigRequestDetails(gigId);
        if (isMounted) {
          if (!data) {
            setError("Gig requirement not found or closed.");
          } else {
            setGig(data);
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load gig details");
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadGig();
    return () => {
      isMounted = false;
    };
  }, [gigId]);

  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setApplyError(null);

    try {
      await applyToGigRequest(gigId, {
        notes: notes.trim() || undefined,
      });
      setApplySuccess(true);
      setShowApplyForm(false);
      setNotes("");
    } catch (err: unknown) {
      setApplyError(err instanceof Error ? err.message : "Failed to submit gig proposal");
    } finally {
      setIsSubmitting(false);
    }
  };

  const isCandidateOrWorker = activeRole === "CANDIDATE" || activeRole === "CONSULTANT";

  if (isLoading) {
    return (
      <DashboardShell
        title="Gig Details"
        breadcrumbs={[{ label: "Gigs", href: "/gigs" }, { label: `#${gigId}` }]}
      >
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      </DashboardShell>
    );
  }

  if (error || !gig) {
    return (
      <DashboardShell
        title="Gig Details"
        breadcrumbs={[{ label: "Gigs", href: "/gigs" }, { label: "Error" }]}
      >
        <Card className="border-red-200 dark:border-red-900/50">
          <CardContent className="pt-6 text-center space-y-4">
            <AlertCircle className="h-10 w-10 text-red-500 mx-auto" />
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Gig Not Found</h2>
            <p className="text-sm text-slate-500">{error || "The requested gig does not exist or has expired."}</p>
            <Button onClick={() => router.push("/gigs")} variant="outline" className="gap-2">
              <ArrowLeft className="h-4 w-4" /> Back to Gig Marketplace
            </Button>
          </CardContent>
        </Card>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell
      title={gig.title}
      breadcrumbs={[{ label: "Gigs", href: "/gigs" }, { label: gig.title }]}
    >
      <div className="space-y-6">
        {/* Navigation & Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <Button onClick={() => router.push("/gigs")} variant="outline" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" /> Back to Marketplace
          </Button>

          <Badge variant={gig.status === "OPEN" ? "default" : "outline"}>
            {gig.status}
          </Badge>
        </div>

        {applySuccess && (
          <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 flex items-center gap-3 text-emerald-800 dark:text-emerald-300">
            <CheckCircle2 className="h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold text-sm">Proposal submitted successfully!</p>
              <p className="text-xs text-emerald-600 dark:text-emerald-400">
                The hiring organisation has been notified and will review your proposal.
              </p>
            </div>
          </div>
        )}

        {/* Primary Card */}
        <Card>
          <CardHeader>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <CardTitle className="text-2xl font-bold flex items-center gap-2">
                  <Sparkles className="h-6 w-6 text-indigo-600 shrink-0" />
                  {gig.title}
                </CardTitle>
                <CardDescription className="flex items-center gap-2 mt-1 text-base text-slate-600 dark:text-slate-300">
                  <Building className="h-4 w-4 text-slate-400" />
                  {gig.organisation_name || `Organisation #${gig.requester_organisation_id}`}
                </CardDescription>
              </div>

              {isCandidateOrWorker && !applySuccess && gig.status === "OPEN" && (
                <Button
                  onClick={() => setShowApplyForm(true)}
                  className="gap-2 bg-indigo-600 hover:bg-indigo-700"
                  size="lg"
                >
                  <Send className="h-4 w-4" />
                  Submit Proposal
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Meta attributes */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 text-sm">
              <div>
                <span className="text-xs text-slate-400 block font-medium">Pricing Model</span>
                <span className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5 block">
                  {gig.pricing_type || (gig.pricing_type_code_id === 1 ? "Fixed Price" : "Hourly / Rate")}
                </span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block font-medium">Compensation Amount</span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400 mt-0.5 block">
                  {gig.price_amount?.toLocaleString()} {gig.currency_code}
                </span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block font-medium">Execution Window</span>
                <span className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5 block text-xs">
                  {formatDate(gig.starts_at)} – {formatDate(gig.ends_at)}
                </span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block font-medium">Created On</span>
                <span className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5 block">
                  {formatDate(gig.created_at)}
                </span>
              </div>
            </div>

            {/* Scope / Description */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold tracking-wide uppercase text-slate-500">
                Deliverable Scope & Milestone Description
              </h3>
              <div className="prose dark:prose-invert max-w-none text-slate-800 dark:text-slate-200 text-sm whitespace-pre-line leading-relaxed">
                {gig.description}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Proposal Submission Form */}
        {showApplyForm && (
          <Card className="border-indigo-200 dark:border-indigo-900 shadow-md">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <FileCheck className="h-5 w-5 text-indigo-600" />
                Submit Proposal for {gig.title}
              </CardTitle>
              <CardDescription>
                Provide delivery notes and your proposed approach to fulfill this micro-engagement.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleApply}>
              <CardContent className="space-y-4">
                {applyError && (
                  <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-sm text-red-600 dark:text-red-300">
                    {applyError}
                  </div>
                )}
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Pitch & Delivery Timeline Notes
                  </label>
                  <textarea
                    rows={4}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Describe your technical approach, relevant past experience, and estimated timeline..."
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowApplyForm(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmitting} className="gap-2">
                  {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  Submit Proposal
                </Button>
              </CardFooter>
            </form>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
