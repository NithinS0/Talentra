import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "@/lib/api/client";
import {
  getSuperAdminDashboard,
  getEmployerDashboard,
  getRecruiterDashboard,
  getCandidateDashboard,
  getTpoDashboard,
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
  EmployerDashboardResponse,
  FunnelAggregationResponse,
  DailyRefreshResponse,
  WatermarkResponse,
  DataFreshnessResponse,
  CandidatePiiMinimized,
  KpiDefinitionResponse,
  DataQualityIssueResponse,
} from "@/types/analytics";

describe("Stage 17D: Analytics Layer & Reporting Marts (Stage 13)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("Role-Specific Dashboards", () => {
    it("retrieves Super Admin platform-wide dashboard metrics", async () => {
      const mockDash: SuperAdminDashboardResponse = {
        total_organisations: 4,
        total_jobs: 12,
        total_applications: 45,
        total_gig_assignments: 8,
        active_subscriptions_count: 5,
        watermark: "wt-20261021",
        refresh_lag_seconds: 12.5,
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockDash);

      const res = await getSuperAdminDashboard();
      expect(res.total_organisations).toBe(4);
      expect(res.total_jobs).toBe(12);
      expect(apiClient.get).toHaveBeenCalledWith("/analytics/dashboards/super-admin");
    });

    it("retrieves Employer dashboard for target organisation", async () => {
      const mockEmp: EmployerDashboardResponse = {
        organisation_id: 1,
        organisation_name: "Acme Corp",
        open_jobs_count: 5,
        total_applications_received: 30,
        interviews_scheduled: 12,
        offers_extended: 4,
        hires_count: 3,
        funnel: {
          as_of_date: "2026-10-21",
          total_applications: 30,
          total_hired: 3,
          overall_conversion_rate_percent: 10.0,
          stages: [],
        },
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockEmp);

      const res = await getEmployerDashboard(1);
      expect(res.organisation_name).toBe("Acme Corp");
      expect(apiClient.get).toHaveBeenCalledWith("/analytics/dashboards/employer", {
        params: { organisation_id: 1 },
      });
    });
  });

  describe("Application Funnel & Data Quality (FR-0151, FR-0152)", () => {
    it("retrieves application recruitment funnel progression (FR-0151)", async () => {
      const mockFunnel: FunnelAggregationResponse = {
        organisation_id: 1,
        as_of_date: "2026-10-21",
        total_applications: 100,
        total_hired: 8,
        overall_conversion_rate_percent: 8.0,
        stages: [
          { stage_name: "Applied", status_code_id: 1, count: 100, conversion_rate_percent: 100.0 },
          { stage_name: "Screened", status_code_id: 2, count: 60, conversion_rate_percent: 60.0 },
          { stage_name: "Interviewed", status_code_id: 3, count: 25, conversion_rate_percent: 41.7 },
          { stage_name: "Offered", status_code_id: 4, count: 10, conversion_rate_percent: 40.0 },
          { stage_name: "Hired", status_code_id: 5, count: 8, conversion_rate_percent: 80.0 },
        ],
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockFunnel);

      const res = await getApplicationFunnel({ organisation_id: 1 });
      expect(res.total_applications).toBe(100);
      expect(res.stages).toHaveLength(5);
      expect(res.overall_conversion_rate_percent).toBe(8.0);
      expect(apiClient.get).toHaveBeenCalledWith("/analytics/funnel", {
        params: { organisation_id: 1 },
      });
    });

    it("retrieves data quality issues catalogue (FR-0152)", async () => {
      const mockIssues: DataQualityIssueResponse[] = [
        {
          id: 1,
          code: "ORPHAN_APPLICATION_DIM",
          name: "Unmapped application dimension",
          status_code_id: 1,
          created_at: "2026-10-21T10:00:00Z",
        },
      ];

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockIssues);

      const res = await getDataQualityIssues();
      expect(res).toHaveLength(1);
      expect(apiClient.get).toHaveBeenCalledWith("/analytics/data-quality-issues");
    });
  });

  describe("Refresh, Watermarks & Freshness (FR-0153, FR-0157, FR-0161)", () => {
    it("triggers daily aggregate refresh (FR-0153)", async () => {
      const mockRefresh: DailyRefreshResponse = {
        status: "COMPLETED",
        refresh_date: "2026-10-21",
        records_processed: 150,
        source_watermark: "wt-20261021",
        run_id: 14,
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockRefresh);

      const res = await triggerDailyRefresh({});
      expect(res.run_id).toBe(14);
      expect(res.records_processed).toBe(150);
      expect(apiClient.post).toHaveBeenCalledWith("/analytics/refresh/daily", {});
    });

    it("retrieves refresh watermark (FR-0157)", async () => {
      const mockWm: WatermarkResponse = {
        last_watermark: "wt-20261021-1200",
        last_successful_run_at: "2026-10-21T12:00:00Z",
        status_code_id: 1,
        status_name: "SUCCESS",
        refresh_lag_seconds: 45.2,
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockWm);

      const res = await getRefreshWatermark();
      expect(res.last_watermark).toBe("wt-20261021-1200");
      expect(res.refresh_lag_seconds).toBe(45.2);
      expect(apiClient.get).toHaveBeenCalledWith("/analytics/refresh/watermark");
    });

    it("calculates UTC data freshness lag (FR-0161)", async () => {
      const mockFreshness: DataFreshnessResponse = {
        watermark_timestamp_utc: "2026-10-21T12:00:00Z",
        current_timestamp_utc: "2026-10-21T12:01:00Z",
        lag_seconds: 60.0,
        is_fresh: true,
      };

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockFreshness);

      const res = await getDataFreshness();
      expect(res.is_fresh).toBe(true);
      expect(res.lag_seconds).toBe(60.0);
      expect(apiClient.get).toHaveBeenCalledWith("/analytics/data-freshness");
    });
  });

  describe("Candidate Analytics & KPI Catalogue (FR-0154)", () => {
    it("retrieves PII minimized candidate metrics (FR-0154)", async () => {
      const mockPii: CandidatePiiMinimized[] = [
        {
          candidate_id: 42,
          masked_name: "R**** V****",
          masked_email: "r****@example.com",
          current_status: "INTERVIEWING",
          applications_count: 3,
        },
      ];

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockPii);

      const res = await getCandidatesPiiMinimized({ limit: 10 });
      expect(res[0].masked_name).toBe("R**** V****");
      expect(apiClient.get).toHaveBeenCalledWith("/analytics/candidates/pii-minimized", {
        params: { limit: 10 },
      });
    });

    it("retrieves approved business KPI definitions", async () => {
      const mockKpis: KpiDefinitionResponse[] = [
        {
          id: 1,
          code: "TIME_TO_HIRE",
          name: "Average Time to Hire",
          status_code_id: 1,
          description: "Days elapsed between application creation and hire status.",
        },
      ];

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockKpis);

      const res = await getKpiDefinitions();
      expect(res[0].code).toBe("TIME_TO_HIRE");
      expect(apiClient.get).toHaveBeenCalledWith("/analytics/kpi-definitions");
    });
  });
});
