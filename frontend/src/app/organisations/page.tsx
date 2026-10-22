"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Building2,
  Building,
  PlusCircle,
  Search,
  MapPin,
  ExternalLink,
  ShieldCheck,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { listOrganisations, createOrganisation } from "@/lib/api/organisations";
import { OrganisationResponse, OrganisationCreateRequest } from "@/types/organisations";
import { useAuth } from "@/lib/auth/context";
import { formatDate } from "@/lib/utils";

export default function OrganisationsPage() {
  const { activeRole } = useAuth();
  const [organisations, setOrganisations] = useState<OrganisationResponse[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Registration modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [legalName, setLegalName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [countryId, setCountryId] = useState<number>(101); // 101: India, 233: USA
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function fetchOrganisations() {
      try {
        setIsLoading(true);
        setError(null);
        const res = await listOrganisations({
          q: searchTerm || undefined,
          page: 1,
          page_size: 50,
        });
        if (isMounted) {
          setOrganisations(res.items || []);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load organisations");
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    fetchOrganisations();
    return () => {
      isMounted = false;
    };
  }, [searchTerm]);

  const handleCreateOrganisation = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError(null);

    try {
      const payload: OrganisationCreateRequest = {
        legal_name: legalName.trim(),
        display_name: displayName.trim(),
        primary_country_id: Number(countryId),
        organisation_type_code_id: 1,
      };

      const created = await createOrganisation(payload);
      setOrganisations((prev) => [created, ...prev]);
      setFormSuccess(true);
      setShowCreateModal(false);
      setLegalName("");
      setDisplayName("");
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to register organisation entity");
    } finally {
      setIsSubmitting(false);
    }
  };

  const canCreate = ["SUPER_ADMIN", "ACCOUNT_ADMIN", "EMPLOYER"].includes(activeRole);

  return (
    <DashboardShell
      title="Organisations & Accounts"
      breadcrumbs={[{ label: "Organisations" }]}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Organisation Entities & Accounts
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Verified corporate legal entities, memberships, and recruiter mapping governance.
            </p>
          </div>

          {canCreate && (
            <Button onClick={() => setShowCreateModal(true)} className="gap-2">
              <PlusCircle className="h-4 w-4" />
              Register Legal Entity
            </Button>
          )}
        </div>

        {formSuccess && (
          <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 flex items-center gap-3 text-emerald-800 dark:text-emerald-300">
            <CheckCircle2 className="h-5 w-5 shrink-0" />
            <p className="font-semibold text-sm">Organisation entity registered successfully!</p>
          </div>
        )}

        {/* Search Bar */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex gap-3">
          <div className="relative flex-1">
            <Search className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search by legal name or trade display name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Create Modal */}
        {showCreateModal && (
          <Card className="border-indigo-200 dark:border-indigo-900 shadow-lg">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Building2 className="h-5 w-5 text-indigo-600" />
                Register Organisation Legal Entity
              </CardTitle>
              <CardDescription>
                Provisions a verified corporate entity with primary country jurisdiction.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleCreateOrganisation}>
              <CardContent className="space-y-4">
                {formError && (
                  <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 text-xs text-red-600 dark:text-red-300">
                    {formError}
                  </div>
                )}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Registered Legal Business Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={legalName}
                      onChange={(e) => setLegalName(e.target.value)}
                      placeholder="e.g. Acme Technologies India Pvt. Ltd."
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Public Trade / Display Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      placeholder="e.g. Acme Tech"
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Primary Jurisdiction Country *
                  </label>
                  <select
                    value={countryId}
                    onChange={(e) => setCountryId(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value={101}>India (IN)</option>
                    <option value={233}>United States (US)</option>
                    <option value={232}>United Kingdom (GB)</option>
                    <option value={196}>Singapore (SG)</option>
                    <option value={13}>Australia (AU)</option>
                  </select>
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
                  Register Entity
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
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Unable to Load Organisations</h2>
              <p className="text-sm text-slate-500 max-w-md mx-auto">{error}</p>
            </CardContent>
          </Card>
        ) : organisations.length === 0 ? (
          <Card>
            <CardContent className="py-16 text-center space-y-4">
              <Building2 className="h-12 w-12 text-slate-300 dark:text-slate-600 mx-auto" />
              <div className="space-y-1">
                <h3 className="font-semibold text-lg text-slate-900 dark:text-white">
                  No organisation records found
                </h3>
                <p className="text-sm text-slate-500 max-w-sm mx-auto">
                  {searchTerm
                    ? `No organisations match '${searchTerm}'. Try adjusting your query.`
                    : "No organisation legal entities currently active in the directory."}
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Verified Organisations ({organisations.length})</CardTitle>
              <CardDescription>
                Live corporate records with authoritative status and country governance.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Entity ID</TableHead>
                    <TableHead>Display Trade Name</TableHead>
                    <TableHead>Registered Legal Name</TableHead>
                    <TableHead>Jurisdiction</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Registered</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {organisations.map((org) => (
                    <TableRow key={org.id}>
                      <TableCell className="font-mono text-xs">#{org.id}</TableCell>
                      <TableCell className="font-semibold text-slate-900 dark:text-white">
                        <Link
                          href={`/organisations/${org.id}`}
                          className="hover:underline flex items-center gap-2"
                        >
                          <Building className="h-4 w-4 text-indigo-500" />
                          {org.display_name}
                        </Link>
                      </TableCell>
                      <TableCell className="text-xs text-slate-600 dark:text-slate-400">
                        {org.legal_name}
                      </TableCell>
                      <TableCell className="text-xs text-slate-600 dark:text-slate-400">
                        {org.primary_country_name || org.country_name || "India"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={org.status_code === "ACTIVE" ? "default" : "outline"}
                        >
                          {org.status_code}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-slate-500 text-xs">
                        {formatDate(org.created_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/organisations/${org.id}`}>
                          <Button variant="outline" size="sm" className="gap-1.5">
                            Details & Team
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
