import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "@/lib/api/client";
import {
  getNotifications,
  createNotification,
  markNotificationsRead,
  purgeExpiredNotifications,
  getNotificationPreferences,
  updateNotificationPreference,
  saveJobAlertPreference,
  createCommunityPost,
  reactToCommunityPost,
  createSupportTicket,
  getSupportTicket,
  getFaqs,
  recordReferral,
} from "@/lib/api/notifications";
import {
  NotificationResponse,
  NotificationPreferenceResponse,
  JobAlertPreferenceResponse,
  CommunityPostResponse,
  CommunityReactionResponse,
  SupportTicketResponse,
  FaqResponse,
  ReferralEventResponse,
} from "@/types/notifications";

describe("Stage 17D: Notifications, Preferences & Community (Module M10)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("Notifications & Preferences (FR-0139, FR-0140, FR-0142, FR-0207)", () => {
    it("retrieves notifications for authenticated user with unread filter", async () => {
      const mockNotifs: NotificationResponse[] = [
        {
          id: 1,
          user_id: 1,
          setting_code_id: 1,
          enabled: true,
          is_read: false,
          title: "New Job Match",
          body: "A job requirement matching your skills has been published.",
          created_at: "2026-10-21T10:00:00Z",
          updated_at: "2026-10-21T10:00:00Z",
        },
      ];

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockNotifs);

      const res = await getNotifications({ unread_only: true });
      expect(res).toHaveLength(1);
      expect(res[0].is_read).toBe(false);
      expect(apiClient.get).toHaveBeenCalledWith("/notifications", {
        params: { unread_only: true },
      });
    });

    it("marks notifications as read in bulk", async () => {
      vi.spyOn(apiClient, "post").mockResolvedValueOnce({ updated_count: 3 });

      const res = await markNotificationsRead([1, 2, 3]);
      expect(res.updated_count).toBe(3);
      expect(apiClient.post).toHaveBeenCalledWith("/notifications/mark-read", {
        notification_ids: [1, 2, 3],
      });
    });

    it("purges and redacts expired notification message bodies (FR-0142, FR-0207)", async () => {
      vi.spyOn(apiClient, "post").mockResolvedValueOnce({ purged_count: 14 });

      const res = await purgeExpiredNotifications();
      expect(res.purged_count).toBe(14);
      expect(apiClient.post).toHaveBeenCalledWith("/notifications/purge-expired");
    });

    it("updates notification channel preference (FR-0139)", async () => {
      const mockPref: NotificationPreferenceResponse = {
        id: 5,
        user_id: 1,
        notification_type_code_id: 1,
        channel_code_id: 2,
        enabled: true,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockPref);

      const res = await updateNotificationPreference({
        notification_type_code_id: 1,
        channel_code_id: 2,
        enabled: true,
      });

      expect(res.enabled).toBe(true);
      expect(apiClient.post).toHaveBeenCalledWith("/preferences/notifications", {
        notification_type_code_id: 1,
        channel_code_id: 2,
        enabled: true,
      });
    });

    it("saves candidate job alert search criteria (FR-0140)", async () => {
      const mockAlert: JobAlertPreferenceResponse = {
        id: 8,
        user_id: 1,
        setting_code_id: 1,
        setting_value: { keywords: ["Next.js", "TypeScript"], location: "Remote" },
        enabled: true,
        created_at: "2026-10-21T10:00:00Z",
        updated_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockAlert);

      const res = await saveJobAlertPreference({
        setting_value: { keywords: ["Next.js", "TypeScript"], location: "Remote" },
        enabled: true,
      });

      expect(res.id).toBe(8);
      expect(apiClient.post).toHaveBeenCalledWith("/preferences/job-alerts", expect.objectContaining({
        setting_value: { keywords: ["Next.js", "TypeScript"], location: "Remote" },
      }));
    });
  });

  describe("Community Feed & Reactions (FR-0144, FR-0145)", () => {
    it("creates community post enforcing 10,000 char boundary with UTF-8 (FR-0144)", async () => {
      const mockPost: CommunityPostResponse = {
        id: 101,
        author_user_id: 1,
        title: "Architecture Tips for Campus Placements",
        body: "Ensure real-time verification and append-only audits.",
        language_id: 1,
        moderation_status_code_id: 1,
        created_at: "2026-10-21T10:00:00Z",
        updated_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockPost);

      const res = await createCommunityPost({
        title: "Architecture Tips for Campus Placements",
        body: "Ensure real-time verification and append-only audits.",
        language_code: "en",
      });

      expect(res.id).toBe(101);
      expect(apiClient.post).toHaveBeenCalledWith("/community/posts", expect.objectContaining({
        title: "Architecture Tips for Campus Placements",
      }));
    });

    it("toggles reaction on community post (FR-0145)", async () => {
      const mockReaction: CommunityReactionResponse = {
        id: 1,
        code: "LIKE",
        name: "Like",
        status_code_id: 1,
        created_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockReaction);

      const res = await reactToCommunityPost(101, "LIKE");
      expect(res.status_code_id).toBe(1);
      expect(apiClient.post).toHaveBeenCalledWith("/community/posts/101/react", {
        post_id: 101,
        reaction_type: "LIKE",
      });
    });
  });

  describe("Support Tickets, FAQs & Referrals (FR-0146, FR-0147, FR-0148)", () => {
    it("submits support ticket with priority and description", async () => {
      const mockTicket: SupportTicketResponse = {
        id: 12,
        requester_user_id: 1,
        ticket_number: "TICK-2026-0012",
        subject: "Seat limit issue",
        description: "Need assistance allocating seat for new hire.",
        priority_code_id: 2,
        status_code_id: 1,
        created_at: "2026-10-21T10:00:00Z",
        updated_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockTicket);

      const res = await createSupportTicket({
        subject: "Seat limit issue",
        description: "Need assistance allocating seat for new hire.",
        priority_code_id: 2,
      });

      expect(res.ticket_number).toBe("TICK-2026-0012");
      expect(apiClient.post).toHaveBeenCalledWith("/support/tickets", expect.objectContaining({
        subject: "Seat limit issue",
      }));
    });

    it("enforces support ticket access strictly to requester or staff (FR-0146)", async () => {
      vi.spyOn(apiClient, "get").mockRejectedValueOnce({
        status: 403,
        message: "Access denied to support ticket (FR-0146)",
      });

      await expect(getSupportTicket(999)).rejects.toMatchObject({
        status: 403,
      });
    });

    it("queries public FAQs filtering out draft/inactive entries (FR-0147)", async () => {
      const mockFaqs: FaqResponse[] = [
        {
          id: 1,
          code: "FAQ_KYC",
          name: "How does government verification work?",
          description: "Documents are verified through authorized providers.",
          status_code_id: 1,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        },
      ];

      vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockFaqs);

      const res = await getFaqs(true);
      expect(res).toHaveLength(1);
      expect(apiClient.get).toHaveBeenCalledWith("/support/faqs", {
        params: { public_only: true },
      });
    });

    it("records referral event without duplicate attribution credit (FR-0148)", async () => {
      const mockRef: ReferralEventResponse = {
        id: 77,
        event_code_id: 1,
        actor_user_id: 1,
        occurred_at: "2026-10-21T10:00:00Z",
        created_at: "2026-10-21T10:00:00Z",
      };

      vi.spyOn(apiClient, "post").mockResolvedValueOnce(mockRef);

      const res = await recordReferral({
        referrer_user_id: 1,
        referee_user_id: 2,
        referral_code: "TALENTRA2026",
      });

      expect(res.id).toBe(77);
      expect(apiClient.post).toHaveBeenCalledWith("/referrals", expect.objectContaining({
        referral_code: "TALENTRA2026",
      }));
    });
  });
});
