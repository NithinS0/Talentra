"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Sparkles,
  Building,
  Calendar,
  DollarSign,
  PlusCircle,
  ExternalLink,
  Search,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { listGigRequests, createGigRequest } from "@/lib/api/gig";
import { GigRequestResponse, GigRequestCreate } from "@/types/gig";
import { useAuth } from "@/lib/auth/context";
import { formatDate } from "@/lib/utils";

export default function GigMarketplacePage() {
  const { activeRole } = useAuth();
  const [gigs, setGigs] = useState<GigRequestResponse[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Gig Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [orgId, setOrgId] = useState<number>(1);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priceAmount, setPriceAmount] = useState<number>(50000);
  const [currencyCode, setCurrencyCode] = useState("INR");
  const [pricingTypeId, setPricingTypeId] = useState<number>(1); // 1: FIXED, 2: HOURLY
  const [startDate, setStartDate] = useState("2026-11-01T09:00:00Z");
  const [endDate, setEndDate] = useState("2026-11-30T18:00:00Z");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadGigs() {
      try {
        const res = await listGigRequests({ skip: 0, limit: 50 });
        if (isMounted) setGigs(res.items || []);
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load gig marketplace requests");
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadGigs();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleCreateGig = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError(null);

    try {
      const payload: GigRequestCreate = {
        requester_organisation_id: Number(orgId),
        title: title.trim(),
        description: description.trim(),
        price_amount: Number(priceAmount),
        currency_code: currencyCode.trim().toUpperCase(),
        pricing_type_code_id: Number(pricingTypeId),
        starts_at: startDate,
        ends_at: endDate,
      };

      const created = await createGigRequest(payload);
      setGigs((prev) => [created, ...prev]);
      setFormSuccess(true);
      setShowCreateModal(false);
      setTitle("");
      setDescription("");
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create gig requirement");
    } finally {
      setIsSubmitting(false);
    }
  };

  const canPostGig = ["EMPLOYER", "RECRUITER", "SUPER_ADMIN", "ACCOUNT_ADMIN"].includes(activeRole);

  const filteredGigs = gigs.filter((gig) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      gig.title.toLowerCase().includes(term) ||
      (gig.description && gig.description.toLowerCase().includes(term)) ||
      (gig.organisation_name && gig.organisation_name.toLowerCase().includes(term))
    );
  });

  return (
    <DashboardShell
      title="Gig Marketplace & Micro-Engagements"
      breadcrumbs={[{ label: "Gig Marketplace" }]}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Gig Marketplace & Freelance Engagements
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Discover verified project deliverables, fixed-price milestones, and talent contracts.
            </p>
          </div>

          {canPostGig && (
            <Button onClick={() => setShowCreateModal(true)} className="gap-2">
              <PlusCircle className="h-4 w-4" />
              Post Gig Requirement
            </Button>
          )}
        </div>

        {formSuccess && (
          <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 flex items-center gap-3 text-emerald-800 dark:text-emerald-300">
            <CheckCircle2 className="h-5 w-5 shrink-0" />
            <p className="font-semibold text-sm">Gig requirement posted to marketplace successfully!</p>
          </div>
        )}

        {/* Search Bar */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex gap-3">
          <div className="relative flex-1">
            <Search className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search by gig title, deliverables, or keywords..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Modal: Post Gig Requirement */}
        {showCreateModal && (
          <Card className="border-indigo-200 dark:border-indigo-900 shadow-lg">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-indigo-600" />
                Post Gig Requirement
              </CardTitle>
              <CardDescription>
                Provisions a freelance milestone mandate with validated pricing and delivery window.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleCreateGig}>
              <CardContent className="space-y-4">
                {formError && (
                  <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 text-xs text-red-600 dark:text-red-300">
                    {formError}
                  </div>
                )}
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Gig Title *
                  </label>
                  <input
                    type="text"
                    required
                    minLength={3}
                    maxLength={180}
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Next.js High-Throughput Escrow Dashboard"
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Deliverable Scope & Requirements *
                  </label>
                  <textarea
                    required
                    minLength={10}
                    rows={4}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Specify project milestones, tech stack, and deliverable acceptance criteria..."
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Pricing Model
                    </label>
                    <select
                      value={pricingTypeId}
                      onChange={(e) => setPricingTypeId(Number(e.target.value))}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value={1}>Fixed Price</option>
                      <option value={2}>Rate / Hourly</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Price Amount *
                    </label>
                    <input
                      type="number"
                      required
                      min={1}
                      value={priceAmount}
                      onChange={(e) => setPriceAmount(Number(e.target.value))}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Currency (3-Letter ISO) *
                    </label>
                    <input
                      type="text"
                      required
                      maxLength={3}
                      value={currencyCode}
                      onChange={(e) => setCurrencyCode(e.target.value.toUpperCase())}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Start Date
                    </label>
                    <input
                      type="text"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      End Date
                    </label>
                    <input
                      type="text"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-xs"
                    />
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowCreateModal(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmitting} className="gap-2">
                  {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  Publish Gig
                </Button>
              </CardFooter>
            </form>
          </Card>
        )}

        {/* Content Section */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          </div>
        ) : error ? (
          <Card className="border-red-200 dark:border-red-900/50">
            <CardContent className="pt-6 text-center space-y-4">
              <AlertCircle className="h-10 w-10 text-red-500 mx-auto" />
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Unable to Load Gig Marketplace</h2>
              <p className="text-sm text-slate-500 max-w-md mx-auto">{error}</p>
            </CardContent>
          </Card>
        ) : filteredGigs.length === 0 ? (
          <Card>
            <CardContent className="py-16 text-center space-y-4">
              <Sparkles className="h-12 w-12 text-slate-300 dark:text-slate-600 mx-auto" />
              <div className="space-y-1">
                <h3 className="font-semibold text-lg text-slate-900 dark:text-white">
                  No gig requirements found
                </h3>
                <p className="text-sm text-slate-500 max-w-sm mx-auto">
                  {searchTerm
                    ? `No gig requirements match '${searchTerm}'.`
                    : "No active gig requests in the marketplace right now."}
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                Available Gigs ({filteredGigs.length})
              </CardTitle>
              <CardDescription>
                Verified freelancer deliverables with transparent escrow and pricing terms.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Gig ID</TableHead>
                    <TableHead>Title & Scope</TableHead>
                    <TableHead>Organisation</TableHead>
                    <TableHead>Pricing</TableHead>
                    <TableHead>Window</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredGigs.map((gig) => (
                    <TableRow key={gig.id}>
                      <TableCell className="font-mono text-xs">#{gig.id}</TableCell>
                      <TableCell className="font-semibold text-slate-900 dark:text-white max-w-xs">
                        <Link
                          href={`/gigs/${gig.id}`}
                          className="hover:underline flex items-center gap-1.5"
                        >
                          <Sparkles className="h-3.5 w-3.5 text-indigo-500 shrink-0" />
                          <span className="truncate">{gig.title}</span>
                        </Link>
                      </TableCell>
                      <TableCell className="text-xs text-slate-600 dark:text-slate-400">
                        {gig.organisation_name || `Org #${gig.requester_organisation_id}`}
                      </TableCell>
                      <TableCell className="text-xs font-semibold text-slate-900 dark:text-white">
                        {gig.price_amount?.toLocaleString()} {gig.currency_code} ({gig.pricing_type || "FIXED"})
                      </TableCell>
                      <TableCell className="text-xs text-slate-500">
                        {formatDate(gig.starts_at)} – {formatDate(gig.ends_at)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={gig.status === "OPEN" ? "default" : "outline"}
                        >
                          {gig.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/gigs/${gig.id}`}>
                          <Button variant="outline" size="sm" className="gap-1.5">
                            View & Apply
                            <ExternalLink className="h-3.5 w-3.5" />
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
