"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Shield,
  KeyRound,
  Laptop,
  Users,
  Search,
  PlusCircle,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Trash2,
  RefreshCw,
  LogOut,
} from "lucide-react";
import {
  getLicence,
  createLicence,
  updateLicenceStatus,
  allocateSeat,
  releaseSeat,
  registerDevice,
  revokeDevice,
  cleanupExpiredSessions,
} from "@/lib/api/licences";
import {
  LicenceResponse,
  LicenceCreatePayload,
  SeatAllocationResponse,
  DeviceResponse,
} from "@/types/licences";
import { formatDate } from "@/lib/utils";

export default function LicencesPage() {
  const [licenceIdInput, setLicenceIdInput] = useState<string>("1");
  const [activeLicence, setActiveLicence] = useState<LicenceResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Seat Allocation Form State
  const [targetUserId, setTargetUserId] = useState<string>("");
  const [recentAllocations, setRecentAllocations] = useState<SeatAllocationResponse[]>([]);
  const [isAllocatingSeat, setIsAllocatingSeat] = useState<boolean>(false);

  // Device Management State
  const [deviceFingerprint, setDeviceFingerprint] = useState<string>("");
  const [deviceLabel, setDeviceLabel] = useState<string>("");
  const [registeredDevices, setRegisteredDevices] = useState<DeviceResponse[]>([]);
  const [isRegisteringDevice, setIsRegisteringDevice] = useState<boolean>(false);

  // Create Licence Form State
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [newLicenceCode, setNewLicenceCode] = useState<string>("");
  const [newAccountId, setNewAccountId] = useState<string>("1");
  const [newMaxUsers, setNewMaxUsers] = useState<string>("5");
  const [newMaxDevices, setNewMaxDevices] = useState<string>("2");
  const [isCreatingLicence, setIsCreatingLicence] = useState<boolean>(false);

  // Session Cleanup State
  const [isCleaningSessions, setIsCleaningSessions] = useState<boolean>(false);

  const fetchLicenceDetails = useCallback(async (id: number) => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await getLicence(id);
      setActiveLicence(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : `Failed to load licence #${id}`);
      setActiveLicence(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function init() {
      try {
        const res = await getLicence(1);
        if (isMounted) setActiveLicence(res);
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load initial licence");
        }
      }
    }
    init();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const idNum = parseInt(licenceIdInput, 10);
    if (isNaN(idNum) || idNum <= 0) {
      setError("Please enter a valid positive integer licence ID");
      return;
    }
    fetchLicenceDetails(idNum);
  };

  const handleStatusTransition = async (newStatusCode: number, label: string) => {
    if (!activeLicence) return;
    const confirmed = window.confirm(`Are you sure you want to transition licence #${activeLicence.id} to ${label}?`);
    if (!confirmed) return;

    try {
      setIsLoading(true);
      setError(null);
      const updated = await updateLicenceStatus(activeLicence.id, {
        status_code_id: newStatusCode,
        reason: `Administrative transition to ${label}`,
      });
      setActiveLicence(updated);
      setSuccessMessage(`Licence #${updated.id} status successfully updated to ${updated.status}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update licence status");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAllocateSeat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeLicence) return;
    const uId = parseInt(targetUserId, 10);
    if (isNaN(uId) || uId <= 0) {
      setError("Please provide a valid numeric User ID for seat allocation.");
      return;
    }

    try {
      setIsAllocatingSeat(true);
      setError(null);
      const res = await allocateSeat({
        licence_id: activeLicence.id,
        user_id: uId,
      });
      setRecentAllocations((prev) => [res, ...prev]);
      setSuccessMessage(`Seat #${res.id} successfully allocated to User #${res.user_id}`);
      setTargetUserId("");
      // Refresh licence metrics
      await fetchLicenceDetails(activeLicence.id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to allocate seat");
    } finally {
      setIsAllocatingSeat(false);
    }
  };

  const handleReleaseSeat = async (allocationId: number) => {
    const confirmed = window.confirm(`Are you sure you want to release seat allocation #${allocationId}?`);
    if (!confirmed || !activeLicence) return;

    try {
      setIsLoading(true);
      setError(null);
      await releaseSeat(allocationId, "Administrative seat deallocation");
      setRecentAllocations((prev) => prev.filter((a) => a.id !== allocationId));
      setSuccessMessage(`Seat #${allocationId} successfully released`);
      await fetchLicenceDetails(activeLicence.id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to release seat");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterDevice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (deviceFingerprint.length !== 64) {
      setError("Device fingerprint hash must be exactly 64 hexadecimal characters (SHA-256).");
      return;
    }

    try {
      setIsRegisteringDevice(true);
      setError(null);
      const res = await registerDevice({
        device_fingerprint_hash: deviceFingerprint.toLowerCase(),
        device_label: deviceLabel || "Web Browser Device",
      });
      setRegisteredDevices((prev) => [res, ...prev.filter((d) => d.id !== res.id)]);
      setSuccessMessage(`Device #${res.id} registered successfully.`);
      setDeviceFingerprint("");
      setDeviceLabel("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to register device");
    } finally {
      setIsRegisteringDevice(false);
    }
  };

  const handleRevokeDevice = async (deviceId: number) => {
    const reason = window.prompt("Reason for device revocation:", "Security compliance policy");
    if (!reason) return;

    try {
      setIsLoading(true);
      setError(null);
      const updated = await revokeDevice(deviceId, { reason });
      setRegisteredDevices((prev) =>
        prev.map((d) => (d.id === deviceId ? updated : d))
      );
      setSuccessMessage(`Device #${deviceId} revoked. Linked active sessions terminated.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to revoke device");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateLicence = async (e: React.FormEvent) => {
    e.preventDefault();
    const accId = parseInt(newAccountId, 10);
    const maxU = parseInt(newMaxUsers, 10);
    const maxD = parseInt(newMaxDevices, 10);

    if (!newLicenceCode || isNaN(accId) || isNaN(maxU) || isNaN(maxD) || maxU <= 0 || maxD <= 0) {
      setError("Please ensure valid positive integers for seats and device limits.");
      return;
    }

    try {
      setIsCreatingLicence(true);
      setError(null);
      const now = new Date();
      const validUntil = new Date();
      validUntil.setFullYear(now.getFullYear() + 1);

      const payload: LicenceCreatePayload = {
        licence_code: newLicenceCode,
        account_id: accId,
        max_users: maxU,
        max_devices_per_user: maxD,
        valid_from: now.toISOString(),
        valid_until: validUntil.toISOString(),
      };

      const res = await createLicence(payload);
      setActiveLicence(res);
      setLicenceIdInput(res.id.toString());
      setShowCreateModal(false);
      setSuccessMessage(`Licence '${res.licence_code}' (#${res.id}) created successfully.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create licence");
    } finally {
      setIsCreatingLicence(false);
    }
  };

  const handleCleanupSessions = async () => {
    try {
      setIsCleaningSessions(true);
      setError(null);
      const res = await cleanupExpiredSessions();
      setSuccessMessage(`Session cleanup completed: ${res.cleaned_count} expired session(s) pruned.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Session cleanup failed");
    } finally {
      setIsCleaningSessions(false);
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status.toUpperCase()) {
      case "ACTIVE":
        return "success";
      case "SUSPENDED":
        return "warning";
      case "REVOKED":
      case "EXPIRED":
        return "destructive";
      default:
        return "default";
    }
  };

  return (
    <DashboardShell
      title="Licences, Seats, Devices & Sessions"
      breadcrumbs={[{ label: "Licences" }]}
    >
      <div className="space-y-6">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Licence & Session Governance (Module M07)
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Manage enterprise licence capacity, concurrent seat allocations, registered devices, and active session limits.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleCleanupSessions}
              disabled={isCleaningSessions}
              className="flex items-center gap-2"
            >
              {isCleaningSessions ? (
                <Loader2 className="w-4 h-4 animate-spin text-slate-500" />
              ) : (
                <RefreshCw className="w-4 h-4 text-slate-500" />
              )}
              Cleanup Expired Sessions
            </Button>
            <Button
              variant="primary"
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2"
            >
              <PlusCircle className="w-4 h-4" />
              Create Licence
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
            <button
              onClick={() => setError(null)}
              className="text-xs underline hover:no-underline"
            >
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
            <button
              onClick={() => setSuccessMessage(null)}
              className="text-xs underline hover:no-underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Licence Lookup Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Search className="w-4 h-4 text-primary" />
              Licence Lookup & Metrics
            </CardTitle>
            <CardDescription>
              Fetch authoritative capacity metrics and current seat allocation from the FastAPI backend.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSearch} className="flex gap-3 max-w-md">
              <input
                type="number"
                placeholder="Licence ID (e.g. 1)"
                value={licenceIdInput}
                onChange={(e) => setLicenceIdInput(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                min="1"
              />
              <Button type="submit" variant="primary" disabled={isLoading}>
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Inspect"}
              </Button>
            </form>

            {activeLicence && (
              <div className="mt-6 border-t border-slate-200 dark:border-slate-800 pt-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                  <div>
                    <div className="flex items-center gap-3">
                      <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                        {activeLicence.licence_code}
                      </h2>
                      <Badge variant={getStatusBadgeVariant(activeLicence.status)}>
                        {activeLicence.status}
                      </Badge>
                      <Link
                        href={`/licences/${activeLicence.id}`}
                        className="text-xs text-primary hover:underline font-medium"
                      >
                        Open Details View &rarr;
                      </Link>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      Account #{activeLicence.account_id} • Valid: {formatDate(activeLicence.valid_from)} to {formatDate(activeLicence.valid_until)}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      onClick={() => handleStatusTransition(1, "ACTIVE")}
                      disabled={isLoading || activeLicence.status === "ACTIVE"}
                    >
                      Set Active
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleStatusTransition(2, "SUSPENDED")}
                      disabled={isLoading || activeLicence.status === "SUSPENDED"}
                    >
                      Suspend
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={() => handleStatusTransition(3, "REVOKED")}
                      disabled={isLoading || activeLicence.status === "REVOKED"}
                    >
                      Revoke
                    </Button>
                  </div>
                </div>

                {/* Capacity Summary Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-900/50">
                    <div className="flex items-center gap-2 text-slate-500 text-xs font-medium mb-1">
                      <Users className="w-4 h-4 text-primary" />
                      Total Seat Capacity
                    </div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white">
                      {activeLicence.max_users}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">FR-0098 seat limit</div>
                  </div>

                  <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-900/50">
                    <div className="flex items-center gap-2 text-slate-500 text-xs font-medium mb-1">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      Allocated Seats
                    </div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white">
                      {activeLicence.allocated_seats}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">Concurrently locked</div>
                  </div>

                  <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-900/50">
                    <div className="flex items-center gap-2 text-slate-500 text-xs font-medium mb-1">
                      <KeyRound className="w-4 h-4 text-indigo-500" />
                      Available Seats
                    </div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white">
                      {activeLicence.available_seats}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">Remaining headroom</div>
                  </div>

                  <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-900/50">
                    <div className="flex items-center gap-2 text-slate-500 text-xs font-medium mb-1">
                      <Laptop className="w-4 h-4 text-amber-500" />
                      Devices / User
                    </div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white">
                      {activeLicence.max_devices_per_user}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">FR-0099 device bound</div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Seat Allocation and Release Section */}
        {activeLicence && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Users className="w-4 h-4 text-primary" />
                  Allocate User Seat
                </CardTitle>
                <CardDescription>
                  Assign a user to Licence #{activeLicence.id}. Enforced under transactional lock.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAllocateSeat} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      User Account ID
                    </label>
                    <input
                      type="number"
                      placeholder="e.g. 2"
                      value={targetUserId}
                      onChange={(e) => setTargetUserId(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                      min="1"
                      required
                    />
                  </div>
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={isAllocatingSeat || activeLicence.available_seats <= 0}
                    className="w-full flex items-center justify-center gap-2"
                  >
                    {isAllocatingSeat ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <PlusCircle className="w-4 h-4" />
                    )}
                    Allocate Seat
                  </Button>
                  {activeLicence.available_seats <= 0 && (
                    <p className="text-xs text-red-500 font-medium text-center">
                      Capacity reached: No available seats left on this licence.
                    </p>
                  )}
                </form>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Shield className="w-4 h-4 text-emerald-500" />
                  Seat Allocations & Unassignment (FR-0110)
                </CardTitle>
                <CardDescription>
                  Releasing a seat transactionally restores capacity immediately.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {recentAllocations.length === 0 ? (
                  <div className="py-8 text-center text-slate-500 text-sm">
                    No recent seat actions in this session. Allocate a seat or enter User ID.
                  </div>
                ) : (
                  <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Allocation ID</TableHead>
                          <TableHead>User ID</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Allocated At</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {recentAllocations.map((alloc) => (
                          <TableRow key={alloc.id}>
                            <TableCell className="font-mono text-xs">#{alloc.id}</TableCell>
                            <TableCell className="font-medium text-xs">User #{alloc.user_id}</TableCell>
                            <TableCell>
                              <Badge variant="success">{alloc.status}</Badge>
                            </TableCell>
                            <TableCell className="text-xs text-slate-500">
                              {formatDate(alloc.created_at)}
                            </TableCell>
                            <TableCell className="text-right">
                              <Button
                                variant="destructive"
                                onClick={() => handleReleaseSeat(alloc.id)}
                                className="h-8 px-2 text-xs flex items-center gap-1"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                                Release Seat
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Registered Devices Governance Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Laptop className="w-4 h-4 text-amber-500" />
                Register Device (FR-0108)
              </CardTitle>
              <CardDescription>
                Idempotent device fingerprint registration using SHA-256 hash.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRegisterDevice} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    SHA-256 Fingerprint Hash (64 Hex chars)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                    value={deviceFingerprint}
                    onChange={(e) => setDeviceFingerprint(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-mono border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    maxLength={64}
                    required
                  />
                  <div className="flex justify-between items-center mt-1">
                    <span className="text-[10px] text-slate-400">
                      {deviceFingerprint.length} / 64 chars
                    </span>
                    <button
                      type="button"
                      onClick={() =>
                        setDeviceFingerprint(
                          "a".repeat(64)
                        )
                      }
                      className="text-[10px] text-primary hover:underline"
                    >
                      Insert demo hash
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Device Label
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. MacBook Pro - Office"
                    value={deviceLabel}
                    onChange={(e) => setDeviceLabel(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                  />
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  disabled={isRegisteringDevice}
                  className="w-full flex items-center justify-center gap-2"
                >
                  {isRegisteringDevice ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <PlusCircle className="w-4 h-4" />
                  )}
                  Register Device
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Shield className="w-4 h-4 text-purple-500" />
                Active Device Registry & Revocation (FR-0106)
              </CardTitle>
              <CardDescription>
                Revoking a device terminates all linked sessions immediately.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {registeredDevices.length === 0 ? (
                <div className="py-8 text-center text-slate-500 text-sm">
                  No devices registered in this view. Use the form to register an active client device.
                </div>
              ) : (
                <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Device ID</TableHead>
                        <TableHead>Label</TableHead>
                        <TableHead>Fingerprint Hash</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {registeredDevices.map((dev) => (
                        <TableRow key={dev.id}>
                          <TableCell className="font-mono text-xs">#{dev.id}</TableCell>
                          <TableCell className="font-medium text-xs">
                            {dev.device_label || "Standard Client"}
                          </TableCell>
                          <TableCell className="font-mono text-[11px] text-slate-500 max-w-[180px] truncate">
                            {dev.device_fingerprint_hash}
                          </TableCell>
                          <TableCell>
                            <Badge variant={dev.is_active ? "success" : "destructive"}>
                              {dev.is_active ? "ACTIVE" : "REVOKED"}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            {dev.is_active && (
                              <Button
                                variant="destructive"
                                onClick={() => handleRevokeDevice(dev.id)}
                                className="h-8 px-2 text-xs flex items-center gap-1"
                              >
                                <LogOut className="w-3.5 h-3.5" />
                                Revoke Device
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Create Licence Modal Dialog */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg max-w-md w-full p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  Create Subscription Licence
                </h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  &times;
                </button>
              </div>
              <p className="text-xs text-slate-500">
                FR-0098, FR-0099: Enforces positive integer limits for max seats and devices per user.
              </p>

              <form onSubmit={handleCreateLicence} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Licence Code
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. TALENTRA-ENT-2026-A"
                    value={newLicenceCode}
                    onChange={(e) => setNewLicenceCode(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Account ID
                  </label>
                  <input
                    type="number"
                    value={newAccountId}
                    onChange={(e) => setNewAccountId(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    min="1"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Max Seats
                    </label>
                    <input
                      type="number"
                      value={newMaxUsers}
                      onChange={(e) => setNewMaxUsers(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                      min="1"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Max Devices / User
                    </label>
                    <input
                      type="number"
                      value={newMaxDevices}
                      onChange={(e) => setNewMaxDevices(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                      min="1"
                      required
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowCreateModal(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={isCreatingLicence}
                    className="flex items-center gap-2"
                  >
                    {isCreatingLicence && <Loader2 className="w-4 h-4 animate-spin" />}
                    Confirm Creation
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
