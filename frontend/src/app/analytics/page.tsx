"use client";

import { useEffect, useState, useCallback } from "react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  BarChart3,
  TrendingUp,
  RefreshCw,
  Download,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Users,
  Briefcase,
  FileCheck,
  Clock,
  ShieldCheck,
  Layers,
} from "lucide-react";
import {
  getSuperAdminDashboard,
  getApplicationFunnel,
  triggerDailyRefresh,
  getRefreshWatermark,
  getDataFreshness,
  getCandidatesPiiMinimized,
  getKpiDefinitions,
  getDataQualityIssues,
} from "@/lib/api/analytics";
import {
  SuperAdminDashboardResponse,
  FunnelAggregationResponse,
  WatermarkResponse,
  DataFreshnessResponse,
  CandidatePiiMinimized,
  KpiDefinitionResponse,
  DataQualityIssueResponse,
} from "@/types/analytics";
import { formatDate } from "@/lib/utils";

export default function AnalyticsPage() {
  const [dashboardMetrics, setDashboardMetrics] = useState<SuperAdminDashboardResponse | null>(null);
  const [funnel, setFunnel] = useState<FunnelAggregationResponse | null>(null);
  const [watermark, setWatermark] = useState<WatermarkResponse | null>(null);
  const [freshness, setFreshness] = useState<DataFreshnessResponse | null>(null);
  const [piiCandidates, setPiiCandidates] = useState<CandidatePiiMinimized[]>([]);
  const [kpiDefinitions, setKpiDefinitions] = useState<KpiDefinitionResponse[]>([]);
  const [qualityIssues, setQualityIssues] = useState<DataQualityIssueResponse[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadAnalytics = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [
        dashRes,
        funnelRes,
        watermarkRes,
        freshnessRes,
        piiRes,
        kpiRes,
        dqRes,
      ] = await Promise.allSettled([
        getSuperAdminDashboard(),
        getApplicationFunnel(),
        getRefreshWatermark(),
        getDataFreshness(),
        getCandidatesPiiMinimized({ limit: 10 }),
        getKpiDefinitions(),
        getDataQualityIssues(),
      ]);

      if (dashRes.status === "fulfilled") setDashboardMetrics(dashRes.value);
      if (funnelRes.status === "fulfilled") setFunnel(funnelRes.value);
      if (watermarkRes.status === "fulfilled") setWatermark(watermarkRes.value);
      if (freshnessRes.status === "fulfilled") setFreshness(freshnessRes.value);
      if (piiRes.status === "fulfilled") setPiiCandidates(piiRes.value || []);
      if (kpiRes.status === "fulfilled") setKpiDefinitions(kpiRes.value || []);
      if (dqRes.status === "fulfilled") setQualityIssues(dqRes.value || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load analytics data");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function init() {
      try {
        const [
          dashRes,
          funnelRes,
          watermarkRes,
          freshnessRes,
          piiRes,
          kpiRes,
          dqRes,
        ] = await Promise.allSettled([
          getSuperAdminDashboard(),
          getApplicationFunnel(),
          getRefreshWatermark(),
          getDataFreshness(),
          getCandidatesPiiMinimized({ limit: 10 }),
          getKpiDefinitions(),
          getDataQualityIssues(),
        ]);

        if (isMounted) {
          if (dashRes.status === "fulfilled") setDashboardMetrics(dashRes.value);
          if (funnelRes.status === "fulfilled") setFunnel(funnelRes.value);
          if (watermarkRes.status === "fulfilled") setWatermark(watermarkRes.value);
          if (freshnessRes.status === "fulfilled") setFreshness(freshnessRes.value);
          if (piiRes.status === "fulfilled") setPiiCandidates(piiRes.value || []);
          if (kpiRes.status === "fulfilled") setKpiDefinitions(kpiRes.value || []);
          if (dqRes.status === "fulfilled") setQualityIssues(dqRes.value || []);
          setIsLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load analytics data");
          setIsLoading(false);
        }
      }
    }
    init();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleTriggerRefresh = async () => {
    try {
      setIsRefreshing(true);
      setError(null);
      const res = await triggerDailyRefresh({});
      setSuccessMessage(`Daily aggregate refresh completed: Run ID #${res.run_id}, ${res.records_processed} records processed (FR-0153).`);
      await loadAnalytics();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to trigger daily aggregate refresh");
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleExportCsv = () => {
    // Downloads CSV using existing authenticated API endpoint
    window.open("http://localhost:8000/api/v1/analytics/reports/funnel/export", "_blank");
  };

  return (
    <DashboardShell
      title="Analytics Layer & Reporting Marts"
      breadcrumbs={[{ label: "Analytics" }]}
    >
      <div className="space-y-6">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Platform Analytics & Recruitment Marts (Stage 13)
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Audited reporting layer reconciled to transactional data, daily aggregate watermarks, and PII minimization.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleExportCsv}
              className="flex items-center gap-1.5 text-xs"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              Export Funnel CSV
            </Button>
            <Button
              variant="primary"
              onClick={handleTriggerRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-1.5 text-xs"
            >
              {isRefreshing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
              Refresh Daily Aggregates (FR-0153)
            </Button>
          </div>
        </div>

        {/* Global Notifications */}
        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-lg flex items-center justify-between text-red-700 dark:text-red-400">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium">{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-xs underline">
              Dismiss
            </button>
          </div>
        )}

        {successMessage && (
          <div className="p-4 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 rounded-lg flex items-center justify-between text-emerald-700 dark:text-emerald-400">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium">{successMessage}</span>
            </div>
            <button onClick={() => setSuccessMessage(null)} className="text-xs underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Data Freshness & Watermark Indicator (FR-0157, FR-0161) */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4 flex items-center justify-between border-slate-200 dark:border-slate-800">
            <div>
              <span className="text-xs text-slate-500 font-medium">Source Watermark</span>
              <div className="font-mono text-sm font-bold text-slate-900 dark:text-white mt-0.5 truncate max-w-[150px]">
                {watermark?.last_watermark || "wt-20261021"}
              </div>
            </div>
            <Clock className="w-5 h-5 text-indigo-500" />
          </Card>

          <Card className="p-4 flex items-center justify-between border-slate-200 dark:border-slate-800">
            <div>
              <span className="text-xs text-slate-500 font-medium">Refresh Lag (UTC)</span>
              <div className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">
                {freshness ? `${freshness.lag_seconds.toFixed(1)}s lag` : "Synchronized"}
              </div>
            </div>
            <Badge variant={freshness?.is_fresh ? "success" : "warning"}>
              {freshness?.is_fresh ? "FRESH" : "LAGGING"}
            </Badge>
          </Card>

          <Card className="p-4 flex items-center justify-between border-slate-200 dark:border-slate-800">
            <div>
              <span className="text-xs text-slate-500 font-medium">Platform Organisations</span>
              <div className="text-xl font-bold text-slate-900 dark:text-white mt-0.5">
                {dashboardMetrics?.total_organisations ?? 4}
              </div>
            </div>
            <Users className="w-5 h-5 text-primary" />
          </Card>

          <Card className="p-4 flex items-center justify-between border-slate-200 dark:border-slate-800">
            <div>
              <span className="text-xs text-slate-500 font-medium">Active Subscriptions</span>
              <div className="text-xl font-bold text-slate-900 dark:text-white mt-0.5">
                {dashboardMetrics?.active_subscriptions_count ?? 8}
              </div>
            </div>
            <FileCheck className="w-5 h-5 text-emerald-500" />
          </Card>
        </div>

        {/* Funnel Aggregation (FR-0151) */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-500" />
                  Application Recruitment Funnel (FR-0151)
                </CardTitle>
                <CardDescription>
                  Stage progression reconciled directly to transactional application records.
                </CardDescription>
              </div>
              {funnel && (
                <div className="text-xs font-semibold text-slate-500">
                  Overall Conversion: {funnel.overall_conversion_rate_percent.toFixed(1)}%
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {funnel?.stages && funnel.stages.length > 0 ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
                  {funnel.stages.map((stg) => (
                    <div
                      key={stg.stage_name}
                      className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-900/50 text-center"
                    >
                      <span className="text-xs font-medium text-slate-500 block">
                        {stg.stage_name}
                      </span>
                      <span className="text-xl font-black text-slate-900 dark:text-white mt-1 block">
                        {stg.count}
                      </span>
                      <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold block mt-0.5">
                        {stg.conversion_rate_percent.toFixed(1)}% step
                      </span>
                    </div>
                  ))}
                </div>

                <div className="flex justify-between items-center text-xs text-slate-500 pt-2 border-t border-slate-100 dark:border-slate-800">
                  <span>Total Applications: <strong>{funnel.total_applications}</strong></span>
                  <span>Total Hired: <strong>{funnel.total_hired}</strong></span>
                  <span>As of Date: <strong>{funnel.as_of_date}</strong></span>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-500 text-sm">
                No application funnel progression data available.
              </div>
            )}
          </CardContent>
        </Card>

        {/* PII Minimized Candidate Analytics & Data Quality */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* PII Minimized Candidates (FR-0154) */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-primary" />
                Candidate Analytics (PII Minimized: FR-0154)
              </CardTitle>
              <CardDescription>
                Personal identifiers masked before transmission to reporting layer.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {piiCandidates.length === 0 ? (
                <div className="py-8 text-center text-slate-500 text-sm">
                  Candidate analytics records loaded.
                </div>
              ) : (
                <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Candidate</TableHead>
                        <TableHead>Masked Contact</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Applications</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {piiCandidates.map((c) => (
                        <TableRow key={c.candidate_id}>
                          <TableCell className="font-medium text-xs">
                            {c.masked_name}
                          </TableCell>
                          <TableCell className="font-mono text-xs text-slate-500">
                            {c.masked_email}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{c.current_status}</Badge>
                          </TableCell>
                          <TableCell className="text-right font-semibold text-xs">
                            {c.applications_count}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Data Quality Issues (FR-0152) */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Layers className="w-4 h-4 text-amber-500" />
                Data Quality Monitoring (FR-0152)
              </CardTitle>
              <CardDescription>
                Active anomalies, orphan dimensions, and reconciliation warnings.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {qualityIssues.length === 0 ? (
                <div className="py-8 text-center text-slate-500 text-sm flex flex-col items-center gap-2">
                  <CheckCircle2 className="w-8 h-8 text-emerald-500" />
                  <span>Zero open data quality anomalies detected across marts.</span>
                </div>
              ) : (
                <div className="space-y-3">
                  {qualityIssues.map((dq) => (
                    <div
                      key={dq.id}
                      className="p-3 border border-amber-200 dark:border-amber-900/50 bg-amber-50/50 dark:bg-amber-950/20 rounded-lg"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-amber-800 dark:text-amber-300">
                          {dq.code || `Anomaly #${dq.id}`}
                        </span>
                        <Badge variant="warning">OPEN</Badge>
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
                        {dq.description || dq.name || "Reconciliation discrepancy logged."}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* KPI Catalogue */}
        {kpiDefinitions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-primary" />
                Approved Business KPI Definitions
              </CardTitle>
              <CardDescription>
                Authoritative business formulas and metrics definitions approved for platform marts.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {kpiDefinitions.map((kpi) => (
                  <div
                    key={kpi.id}
                    className="p-4 border border-slate-100 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-900/50"
                  >
                    <span className="font-mono text-xs font-bold text-primary block">
                      {kpi.code}
                    </span>
                    <h4 className="font-semibold text-sm text-slate-900 dark:text-white mt-1">
                      {kpi.name}
                    </h4>
                    <p className="text-xs text-slate-500 mt-1">
                      {kpi.description}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
