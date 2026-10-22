"use client";

import { useEffect, useState, useCallback } from "react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Bell,
  CheckCircle2,
  Trash2,
  Filter,
  AlertCircle,
  Loader2,
  Settings,
  Mail,
  Smartphone,
  Shield,
  Briefcase,
} from "lucide-react";
import {
  getNotifications,
  markNotificationsRead,
  purgeExpiredNotifications,
  getNotificationPreferences,
  updateNotificationPreference,
  saveJobAlertPreference,
} from "@/lib/api/notifications";
import {
  NotificationResponse,
  NotificationPreferenceResponse,
} from "@/types/notifications";
import { formatDate } from "@/lib/utils";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [preferences, setPreferences] = useState<NotificationPreferenceResponse[]>([]);
  const [unreadOnly, setUnreadOnly] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Preference update state
  const [isUpdatingPref, setIsUpdatingPref] = useState<boolean>(false);
  const [isPurging, setIsPurging] = useState<boolean>(false);

  // Job Alert filter state
  const [alertKeywords, setAlertKeywords] = useState<string>("React, TypeScript");
  const [alertLocation, setAlertLocation] = useState<string>("Remote");
  const [isSavingAlert, setIsSavingAlert] = useState<boolean>(false);

  const loadNotificationsData = useCallback(async (onlyUnread: boolean) => {
    try {
      setIsLoading(true);
      setError(null);
      const [fetchedNotifs, fetchedPrefs] = await Promise.all([
        getNotifications({ unread_only: onlyUnread }),
        getNotificationPreferences(),
      ]);
      setNotifications(fetchedNotifs || []);
      setPreferences(fetchedPrefs || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load notifications");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function init() {
      try {
        const [fetchedNotifs, fetchedPrefs] = await Promise.all([
          getNotifications({ unread_only: unreadOnly }),
          getNotificationPreferences(),
        ]);
        if (isMounted) {
          setNotifications(fetchedNotifs || []);
          setPreferences(fetchedPrefs || []);
          setIsLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load notifications");
          setIsLoading(false);
        }
      }
    }
    init();
    return () => {
      isMounted = false;
    };
  }, [unreadOnly]);

  const handleMarkAllRead = async () => {
    const unreadIds = notifications.filter((n) => !n.is_read).map((n) => n.id);
    if (unreadIds.length === 0) return;

    try {
      setIsLoading(true);
      setError(null);
      const res = await markNotificationsRead(unreadIds);
      setNotifications((prev) =>
        prev.map((n) => (unreadIds.includes(n.id) ? { ...n, is_read: true } : n))
      );
      setSuccessMessage(`Marked ${res.updated_count} notification(s) as read.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to mark notifications read");
    } finally {
      setIsLoading(false);
    }
  };

  const handlePurgeExpired = async () => {
    try {
      setIsPurging(true);
      setError(null);
      const res = await purgeExpiredNotifications();
      setSuccessMessage(`Data retention purge completed: ${res.purged_count} expired notification body/bodies redacted (FR-0142, FR-0207).`);
      await loadNotificationsData(unreadOnly);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Retention purge failed");
    } finally {
      setIsPurging(false);
    }
  };

  const handleTogglePreference = async (typeId: number, channelId: number, currentEnabled: boolean) => {
    try {
      setIsUpdatingPref(true);
      setError(null);
      const updated = await updateNotificationPreference({
        notification_type_code_id: typeId,
        channel_code_id: channelId,
        enabled: !currentEnabled,
      });

      setPreferences((prev) => {
        const filtered = prev.filter(
          (p) => !(p.notification_type_code_id === typeId && p.channel_code_id === channelId)
        );
        return [...filtered, updated];
      });
      setSuccessMessage("Notification channel preference updated.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update preference");
    } finally {
      setIsUpdatingPref(false);
    }
  };

  const handleSaveJobAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSavingAlert(true);
      setError(null);
      await saveJobAlertPreference({
        setting_value: {
          keywords: alertKeywords.split(",").map((s) => s.trim()),
          location: alertLocation,
        },
        enabled: true,
      });
      setSuccessMessage("Job alert search criteria saved (FR-0140).");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save job alert preference");
    } finally {
      setIsSavingAlert(false);
    }
  };

  const isChannelEnabled = (typeId: number, channelId: number): boolean => {
    const pref = preferences.find(
      (p) => p.notification_type_code_id === typeId && p.channel_code_id === channelId
    );
    return pref ? pref.enabled : true;
  };

  return (
    <DashboardShell
      title="Notification Centre & Preferences"
      breadcrumbs={[{ label: "Notifications" }]}
    >
      <div className="space-y-6">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Notification Centre (Module M10)
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Personal in-app alerts, delivery channels, retention purge, and job notification preferences.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handlePurgeExpired}
              disabled={isPurging}
              className="flex items-center gap-1.5 text-xs"
            >
              {isPurging ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5 text-slate-500" />}
              Purge Expired Bodies (FR-0142)
            </Button>
            <Button
              variant="primary"
              onClick={handleMarkAllRead}
              disabled={isLoading || notifications.every((n) => n.is_read)}
              className="flex items-center gap-1.5 text-xs"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              Mark All as Read
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Notifications Feed */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Bell className="w-4 h-4 text-primary" />
                    In-App Notifications
                  </CardTitle>
                  <CardDescription>
                    Scoped exclusively to your authenticated user account.
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant={unreadOnly ? "primary" : "outline"}
                    onClick={() => setUnreadOnly(!unreadOnly)}
                    className="h-8 px-2.5 text-xs flex items-center gap-1"
                  >
                    <Filter className="w-3 h-3" />
                    {unreadOnly ? "Showing Unread" : "All Alerts"}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                </div>
              ) : notifications.length === 0 ? (
                <div className="py-16 text-center text-slate-500 text-sm">
                  {unreadOnly ? "No unread notifications." : "No notifications on record."}
                </div>
              ) : (
                <div className="space-y-3">
                  {notifications.map((notif) => (
                    <div
                      key={notif.id}
                      className={`p-4 border rounded-lg transition-colors ${
                        notif.is_read
                          ? "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50"
                          : "border-primary/40 bg-primary/5 dark:bg-primary/10"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2">
                          {!notif.is_read && (
                            <span className="w-2 h-2 rounded-full bg-primary flex-shrink-0" />
                          )}
                          <h4 className="font-semibold text-slate-900 dark:text-white text-sm">
                            {notif.title || `Notification #${notif.id}`}
                          </h4>
                        </div>
                        <span className="text-[11px] text-slate-400 whitespace-nowrap">
                          {formatDate(notif.created_at)}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-300 mt-2 leading-relaxed">
                        {notif.body || "Notification details redacted or expired."}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Preferences & Settings */}
          <div className="space-y-6 lg:col-span-1">
            {/* Channel Preferences Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Settings className="w-4 h-4 text-primary" />
                  Delivery Channels (FR-0139)
                </CardTitle>
                <CardDescription>
                  Configure preferred delivery channels per notification category.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  {/* Job Alerts */}
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800 text-xs">
                    <div className="flex items-center gap-2">
                      <Briefcase className="w-3.5 h-3.5 text-slate-500" />
                      <span className="font-medium text-slate-700 dark:text-slate-300">Job Alerts (Email)</span>
                    </div>
                    <Button
                      variant={isChannelEnabled(1, 2) ? "primary" : "outline"}
                      onClick={() => handleTogglePreference(1, 2, isChannelEnabled(1, 2))}
                      disabled={isUpdatingPref}
                      className="h-7 px-2 text-[11px]"
                    >
                      {isChannelEnabled(1, 2) ? "Enabled" : "Muted"}
                    </Button>
                  </div>

                  {/* Application Updates */}
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800 text-xs">
                    <div className="flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-slate-500" />
                      <span className="font-medium text-slate-700 dark:text-slate-300">App Updates (In-App)</span>
                    </div>
                    <Button
                      variant={isChannelEnabled(2, 1) ? "primary" : "outline"}
                      onClick={() => handleTogglePreference(2, 1, isChannelEnabled(2, 1))}
                      disabled={isUpdatingPref}
                      className="h-7 px-2 text-[11px]"
                    >
                      {isChannelEnabled(2, 1) ? "Enabled" : "Muted"}
                    </Button>
                  </div>

                  {/* Security Alerts */}
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800 text-xs">
                    <div className="flex items-center gap-2">
                      <Shield className="w-3.5 h-3.5 text-slate-500" />
                      <span className="font-medium text-slate-700 dark:text-slate-300">Security Alerts (Email)</span>
                    </div>
                    <Button
                      variant={isChannelEnabled(3, 2) ? "primary" : "outline"}
                      onClick={() => handleTogglePreference(3, 2, isChannelEnabled(3, 2))}
                      disabled={isUpdatingPref}
                      className="h-7 px-2 text-[11px]"
                    >
                      {isChannelEnabled(3, 2) ? "Enabled" : "Muted"}
                    </Button>
                  </div>

                  {/* SMS Alerts */}
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <Smartphone className="w-3.5 h-3.5 text-slate-500" />
                      <span className="font-medium text-slate-700 dark:text-slate-300">SMS Notifications</span>
                    </div>
                    <Button
                      variant={isChannelEnabled(1, 3) ? "primary" : "outline"}
                      onClick={() => handleTogglePreference(1, 3, isChannelEnabled(1, 3))}
                      disabled={isUpdatingPref}
                      className="h-7 px-2 text-[11px]"
                    >
                      {isChannelEnabled(1, 3) ? "Enabled" : "Muted"}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Candidate Job Alert Criteria (FR-0140) */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-indigo-500" />
                  Job Alert Criteria (FR-0140)
                </CardTitle>
                <CardDescription>
                  Customise matching criteria for automatic candidate alerts.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSaveJobAlert} className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Target Skills / Keywords
                    </label>
                    <input
                      type="text"
                      value={alertKeywords}
                      onChange={(e) => setAlertKeywords(e.target.value)}
                      className="w-full px-3 py-1.5 text-xs border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                      placeholder="e.g. Python, FastAPI, React"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Preferred Location
                    </label>
                    <input
                      type="text"
                      value={alertLocation}
                      onChange={(e) => setAlertLocation(e.target.value)}
                      className="w-full px-3 py-1.5 text-xs border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                      placeholder="e.g. Bengaluru, Remote"
                      required
                    />
                  </div>
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={isSavingAlert}
                    className="w-full h-8 text-xs flex items-center justify-center gap-1.5"
                  >
                    {isSavingAlert ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Save Alert Filters"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
