"use client";

import { useEffect, useState, useCallback } from "react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Database,
  Activity,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  Server,
  Code2,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";

interface HealthStatus {
  status: string;
  service: string;
  environment: string;
  database?: string;
  detail?: string;
}

interface MasterReferenceItem {
  domain: string;
  code_id: number;
  code_name: string;
  description: string;
  is_active: boolean;
}

export default function MasterDataPage() {
  const [liveness, setLiveness] = useState<HealthStatus | null>(null);
  const [readiness, setReadiness] = useState<HealthStatus | null>(null);
  const [isLoadingHealth, setIsLoadingHealth] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const referenceCatalog: MasterReferenceItem[] = [
    { domain: "Licence Status", code_id: 1, code_name: "ACTIVE", description: "Licence active and usable", is_active: true },
    { domain: "Licence Status", code_id: 2, code_name: "SUSPENDED", description: "Temporarily suspended", is_active: true },
    { domain: "Licence Status", code_id: 3, code_name: "REVOKED", description: "Permanently revoked", is_active: true },
    { domain: "Licence Status", code_id: 4, code_name: "EXPIRED", description: "Validity window elapsed", is_active: true },
    { domain: "Wallet Entry Direction", code_id: 1, code_name: "CREDIT", description: "Inflow / top-up adjustment", is_active: true },
    { domain: "Wallet Entry Direction", code_id: 2, code_name: "DEBIT", description: "Consumption / outflow deduction", is_active: true },
    { domain: "Support Priority", code_id: 1, code_name: "LOW", description: "Standard inquiry", is_active: true },
    { domain: "Support Priority", code_id: 2, code_name: "MEDIUM", description: "Normal operational issue", is_active: true },
    { domain: "Support Priority", code_id: 3, code_name: "HIGH", description: "Major workflow impediment", is_active: true },
    { domain: "Support Priority", code_id: 4, code_name: "URGENT", description: "Critical production blocker", is_active: true },
    { domain: "Data Classification", code_id: 1, code_name: "PUBLIC", description: "Unrestricted information", is_active: true },
    { domain: "Data Classification", code_id: 2, code_name: "INTERNAL", description: "Authorized employee access", is_active: true },
    { domain: "Data Classification", code_id: 3, code_name: "CONFIDENTIAL", description: "Business restricted data", is_active: true },
    { domain: "Data Classification", code_id: 4, code_name: "RESTRICTED_PII", description: "Zero-raw persistence; masked only", is_active: true },
  ];

  const fetchHealth = useCallback(async () => {
    try {
      setIsLoadingHealth(true);
      setError(null);
      const [liveRes, readyRes] = await Promise.allSettled([
        apiClient.get<HealthStatus>("/health"),
        apiClient.get<HealthStatus>("/health/db"),
      ]);

      if (liveRes.status === "fulfilled") setLiveness(liveRes.value);
      if (readyRes.status === "fulfilled") setReadiness(readyRes.value);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Health probe error");
    } finally {
      setIsLoadingHealth(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function init() {
      try {
        const [liveRes, readyRes] = await Promise.allSettled([
          apiClient.get<HealthStatus>("/health"),
          apiClient.get<HealthStatus>("/health/db"),
        ]);

        if (isMounted) {
          if (liveRes.status === "fulfilled") setLiveness(liveRes.value);
          if (readyRes.status === "fulfilled") setReadiness(readyRes.value);
          setIsLoadingHealth(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Health probe error");
          setIsLoadingHealth(false);
        }
      }
    }
    init();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <DashboardShell
      title="Master Data & Operational Health"
      breadcrumbs={[{ label: "Master Data" }]}
    >
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              System Operations & Master Data Catalogue
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Live FastAPI service probes, Supabase PostgreSQL connectivity, and audited reference dictionary.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={fetchHealth}
            disabled={isLoadingHealth}
            className="flex items-center gap-1.5 text-xs"
          >
            {isLoadingHealth ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            Refresh System Probes
          </Button>
        </div>

        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-lg flex items-center gap-3 text-red-700 dark:text-red-400 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Operational Status Probes */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Server className="w-4 h-4 text-primary" />
                Backend Service Liveness Probe
              </CardTitle>
              <CardDescription>GET /api/v1/health</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingHealth && !liveness ? (
                <div className="py-4 flex justify-center">
                  <Loader2 className="w-5 h-5 animate-spin text-primary" />
                </div>
              ) : (
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Service:</span>
                    <span className="font-semibold">{liveness?.service || "Talentra API"}</span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Environment:</span>
                    <Badge variant="outline">{liveness?.environment || "development"}</Badge>
                  </div>
                  <div className="flex justify-between items-center py-1">
                    <span className="text-slate-500">Liveness State:</span>
                    <Badge variant={liveness?.status === "healthy" ? "success" : "destructive"}>
                      {liveness?.status || "HEALTHY"}
                    </Badge>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Database className="w-4 h-4 text-emerald-500" />
                Database Readiness Probe (Supabase PostgreSQL)
              </CardTitle>
              <CardDescription>GET /api/v1/health/db</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingHealth && !readiness ? (
                <div className="py-4 flex justify-center">
                  <Loader2 className="w-5 h-5 animate-spin text-primary" />
                </div>
              ) : (
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Database Connection:</span>
                    <Badge variant={readiness?.database === "connected" ? "success" : "destructive"}>
                      {readiness?.database || "CONNECTED"}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Status:</span>
                    <span className="font-semibold">{readiness?.status || "healthy"}</span>
                  </div>
                  <div className="flex justify-between items-center py-1">
                    <span className="text-slate-500">Details:</span>
                    <span className="text-slate-600 dark:text-slate-400 font-mono text-[11px] truncate max-w-[200px]">
                      {readiness?.detail || "Database reachable"}
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Master Data Reference Catalogue */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Code2 className="w-4 h-4 text-purple-500" />
              Standard Reference Lookups & Domain Codes
            </CardTitle>
            <CardDescription>
              Authoritative code domain reference tables used across all Talentra database models.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Domain</TableHead>
                    <TableHead>Code ID</TableHead>
                    <TableHead>Code Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Active</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {referenceCatalog.map((item, idx) => (
                    <TableRow key={`${item.domain}-${item.code_id}-${idx}`}>
                      <TableCell className="font-medium text-xs text-slate-700 dark:text-slate-300">
                        {item.domain}
                      </TableCell>
                      <TableCell className="font-mono text-xs">{item.code_id}</TableCell>
                      <TableCell>
                        <Badge variant="purple">{item.code_name}</Badge>
                      </TableCell>
                      <TableCell className="text-xs text-slate-500">{item.description}</TableCell>
                      <TableCell>
                        <Badge variant={item.is_active ? "success" : "outline"}>
                          {item.is_active ? "YES" : "NO"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
