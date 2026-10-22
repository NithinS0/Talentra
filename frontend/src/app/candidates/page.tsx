"use client";

import Link from "next/link";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Users, UserCheck, Shield, ExternalLink, Compass, Briefcase, FileText } from "lucide-react";
import { useAuth } from "@/lib/auth/context";

export default function CandidatesDirectoryPage() {
  const { activeRole } = useAuth();
  const isCandidate = activeRole === "CANDIDATE";

  return (
    <DashboardShell
      title="Candidate Directory & Privacy Governance"
      breadcrumbs={[{ label: "Candidates" }]}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Candidate Profiles & Talent Discovery
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Talentra privacy-first talent registry governed by candidate blocking, mandate scoping, and GDPR.
            </p>
          </div>

          {isCandidate && (
            <Link href="/candidates/me">
              <Button className="gap-2">
                <Users className="h-4 w-4" />
                View My Profile
              </Button>
            </Link>
          )}
        </div>

        {/* Candidate Privacy Notice Banner */}
        <div className="p-5 rounded-2xl bg-indigo-50/60 dark:bg-indigo-950/20 border border-indigo-200 dark:border-indigo-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <Shield className="h-6 w-6 text-indigo-600 dark:text-indigo-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="font-semibold text-slate-900 dark:text-white text-sm">
                Authoritative Candidate Privacy & Non-Disclosure Governance
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 max-w-2xl leading-relaxed">
                In strict compliance with Talentra security rules (FR-0117, FR-0121), raw candidate personal records and identity documents are never exposed in public directories. Candidates are discovered authoritatively via active job requirement applications or scoped sourcing requests.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Link href="/sourcing">
              <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                <Compass className="h-3.5 w-3.5" />
                Sourcing Shortlists
              </Button>
            </Link>
            <Link href="/applications">
              <Button size="sm" className="gap-1.5 text-xs">
                <FileText className="h-3.5 w-3.5" />
                Applications Pipeline
              </Button>
            </Link>
          </div>
        </div>

        {/* Discovery Portals Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <UserCheck className="h-5 w-5 text-indigo-600" />
                Candidate Self-Service
              </CardTitle>
              <CardDescription>
                Manage your own verified CA-series profile, contact details, and resume attachments.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/candidates/me">
                <Button className="w-full gap-2" variant="outline">
                  Manage My Profile
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Briefcase className="h-5 w-5 text-indigo-600" />
                Applicant Review
              </CardTitle>
              <CardDescription>
                Review candidates who have explicitly submitted applications to your company job requirements.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/jobs">
                <Button className="w-full gap-2" variant="outline">
                  Explore Requirements
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Compass className="h-5 w-5 text-indigo-600" />
                Consultant Headhunting
              </CardTitle>
              <CardDescription>
                External consultants source pre-screened talent mandates with privacy-masked identities.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/sourcing">
                <Button className="w-full gap-2" variant="outline">
                  View Sourcing Requests
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardShell>
  );
}
