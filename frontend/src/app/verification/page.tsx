"use client";

import { useEffect, useState } from "react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  FileCheck2,
  ShieldAlert,
  Lock,
  AlertCircle,
  CheckCircle2,
  Loader2,
  KeyRound,
  Network,
  ToggleRight,
} from "lucide-react";
import {
  captureVerificationConsent,
  initiateVerification,
  getSecureDocumentUrl,
  submitVerificationReview,
  getIntegrationRegister,
  evaluateFeatureFlag,
} from "@/lib/api/verification";
import {
  VerificationCaseResponse,
  IntegrationBoundaryEntry,
  FeatureFlagResponse,
} from "@/types/verification";
import { formatDate } from "@/lib/utils";

export default function VerificationPage() {
  const [integrations, setIntegrations] = useState<IntegrationBoundaryEntry[]>([]);
  const [isLoadingIntegrations, setIsLoadingIntegrations] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Consent & Initiation Form State (FR-0163, FR-0164, FR-0209)
  const [docType, setDocType] = useState<string>("AADHAAR");
  const [fileName, setFileName] = useState<string>("document.pdf");
  const [docMime, setDocMime] = useState<string>("application/pdf");
  const [purpose, setPurpose] = useState<string>("KYC_ONBOARDING");
  const [rawMaskCandidate, setRawMaskCandidate] = useState<string>("");
  const [docFormatError, setDocFormatError] = useState<string | null>(null);
  const [consentGranted, setConsentGranted] = useState<boolean>(true);
  const [isInitiating, setIsInitiating] = useState<boolean>(false);
  const [activeCase, setActiveCase] = useState<VerificationCaseResponse | null>(null);

  const formatDocInput = (val: string, type: string) => {
    if (type === "AADHAAR") {
      const clean = val.replace(/\D/g, "").slice(0, 12);
      const parts = clean.match(/.{1,4}/g);
      return parts ? parts.join(" ") : clean;
    }
    if (type === "PAN") {
      const upper = val.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 10);
      let res = "";
      for (let i = 0; i < upper.length; i++) {
        const c = upper[i];
        if (i < 5) res += /[A-Z]/.test(c) ? c : "";
        else if (i < 9) res += /[0-9]/.test(c) ? c : "";
        else res += /[A-Z]/.test(c) ? c : "";
      }
      return res;
    }
    return val;
  };

  const validateDocInput = (val: string, type: string): string | null => {
    if (!val) return "Identifier is required.";
    if (type === "AADHAAR") {
      const clean = val.replace(/\s/g, "");
      if (clean.length !== 12) return "Aadhaar must be exactly 12 digits.";
      if (/^[0-1]/.test(clean)) return "Aadhaar cannot start with 0 or 1.";
      return null;
    }
    if (type === "PAN") {
      if (val.length !== 10) return "PAN must be exactly 10 characters.";
      if (!/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(val)) {
        return "PAN must follow format: 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F).";
      }
      return null;
    }
    return null;
  };

  // Presigned URL
  const [presignedUrl, setPresignedUrl] = useState<string | null>(null);
  const [isFetchingUrl, setIsFetchingUrl] = useState<boolean>(false);

  // Review Form (Dual Control: FR-0175, FR-0178)
  const [reviewDecision, setReviewDecision] = useState<string>("VERIFIED");
  const [reviewReason, setReviewReason] = useState<string>("Document validity verified against official records.");
  const [isHighRiskOverride, setIsHighRiskOverride] = useState<boolean>(false);
  const [secondApproverId, setSecondApproverId] = useState<string>("");
  const [isReviewing, setIsReviewing] = useState<boolean>(false);

  // Feature Flag State (FR-0215)
  const [flagCode, setFlagCode] = useState<string>("KYC_DIGILOCKER_INTEGRATION");
  const [flagSubject, setFlagSubject] = useState<string>("user-account-1");
  const [flagResult, setFlagResult] = useState<FeatureFlagResponse | null>(null);
  const [isEvaluatingFlag, setIsEvaluatingFlag] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    async function loadRegister() {
      try {
        setIsLoadingIntegrations(true);
        const list = await getIntegrationRegister();
        if (isMounted) setIntegrations(list || []);
      } catch (err: unknown) {
        if (isMounted) setError(err instanceof Error ? err.message : "Failed to load integration boundary register");
      } finally {
        if (isMounted) setIsLoadingIntegrations(false);
      }
    }
    loadRegister();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleInitiateVerification = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);
      setDocFormatError(null);

      const validationErr = validateDocInput(rawMaskCandidate, docType);
      if (validationErr) {
        setDocFormatError(validationErr);
        setError(validationErr);
        return;
      }

      if (!consentGranted) {
        setError("Explicit consent is required before initiating verification.");
        return;
      }

      setIsInitiating(true);

      // Step 1: Capture explicit consent with documented purpose (FR-0163)
      const consent = await captureVerificationConsent({
        user_id: 1,
        permitted_purpose: purpose,
        policy_version: "v1.0",
        granted: true,
      });

      // Normalize digits for API (without spaces for Aadhaar)
      const normalizedIdentifier = docType === "AADHAAR" ? rawMaskCandidate.replace(/\s/g, "") : rawMaskCandidate;

      // Step 2: Initiate case with zero raw PII persistence (FR-0164, FR-0209)
      const res = await initiateVerification({
        user_id: 1,
        document_type: docType,
        file_name: fileName,
        file_mime_type: docMime,
        consent_record_id: consent.consent_record_id,
        purpose: purpose,
        raw_identifier_for_masking_only: normalizedIdentifier,
      });

      setActiveCase(res);
      setSuccessMessage(
        `Verification Case #${res.case_id} created with zero raw PII persistence. Masked: ${res.masked_identifier || "XXXX-XXXX-XXXX"}. Malware scan: ${res.malware_scan_status}.`
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Verification initiation failed");
    } finally {
      setIsInitiating(false);
    }
  };

  const handleFetchSecureUrl = async () => {
    if (!activeCase) return;
    try {
      setIsFetchingUrl(true);
      setError(null);
      const res = await getSecureDocumentUrl(activeCase.case_id);
      setPresignedUrl(res.presigned_url);
      setSuccessMessage(`Short-lived presigned document URL generated. Token expires at ${formatDate(res.expires_at)}.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to generate presigned access URL");
    } finally {
      setIsFetchingUrl(false);
    }
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCase) return;

    try {
      setIsReviewing(true);
      setError(null);
      const res = await submitVerificationReview(activeCase.case_id, {
        decision: reviewDecision,
        reason: reviewReason,
        reviewer_user_id: 1,
        is_high_risk_override: isHighRiskOverride,
        second_approver_user_id: isHighRiskOverride ? parseInt(secondApproverId, 10) || 2 : null,
      });

      setActiveCase(res);
      setSuccessMessage(`Review decision '${res.status}' submitted successfully.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Review submission rejected (dual control requirement)");
    } finally {
      setIsReviewing(false);
    }
  };

  const handleEvaluateFlag = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsEvaluatingFlag(true);
      setError(null);
      const res = await evaluateFeatureFlag({
        flag_code: flagCode,
        subject_key: flagSubject,
        environment: "production",
      });
      setFlagResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Feature flag evaluation failed");
    } finally {
      setIsEvaluatingFlag(false);
    }
  };

  return (
    <DashboardShell
      title="Government Verification & Integrations"
      breadcrumbs={[{ label: "Verification" }]}
    >
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Government Identity Verification & Boundary Registers (Stage 14)
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Zero raw PII persistence, SHA-256 fingerprint tokenization, short-lived presigned URLs, and dual control governance.
          </p>
        </div>

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

        {/* Verification Initiation & Active Case Review */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Initiation Form (FR-0163, FR-0164, FR-0209) */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <FileCheck2 className="w-4 h-4 text-primary" />
                Initiate ID Verification (Zero Raw PII: FR-0209)
              </CardTitle>
              <CardDescription>
                Captures explicit consent, validates MIME type, and stores masked identifiers only.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleInitiateVerification} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Document Type
                    </label>
                    <select
                      value={docType}
                      onChange={(e) => setDocType(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    >
                      <option value="AADHAAR">Aadhaar Card</option>
                      <option value="PAN">PAN Card</option>
                      <option value="PASSPORT">Passport</option>
                      <option value="VOTER_ID">Voter ID</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Document Purpose
                    </label>
                    <select
                      value={purpose}
                      onChange={(e) => setPurpose(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    >
                      <option value="KYC_ONBOARDING">KYC Onboarding</option>
                      <option value="EMPLOYMENT_BACKGROUND_CHECK">Employment Check</option>
                      <option value="GIG_PAYOUT_COMPLIANCE">Gig Payout Compliance</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    {docType === "AADHAAR" ? "Aadhaar Number (12 Digits)" : docType === "PAN" ? "Permanent Account Number (PAN)" : "Document Identifier"} (Transient Only)
                  </label>
                  <input
                    type="text"
                    value={rawMaskCandidate}
                    onChange={(e) => {
                      const formatted = formatDocInput(e.target.value, docType);
                      setRawMaskCandidate(formatted);
                      setDocFormatError(validateDocInput(formatted, docType));
                    }}
                    placeholder={docType === "AADHAAR" ? "1234 5678 9012" : docType === "PAN" ? "ABCDE1234F" : "Document identifier"}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-mono"
                    required
                  />
                  {docFormatError && (
                    <span className="text-xs text-rose-500 mt-1 block font-sans">
                      {docFormatError}
                    </span>
                  )}
                  <span className="text-[10px] text-slate-400 mt-1 block">
                    Zero raw PII rule: Formatted for display, tokenized with SHA-256, and never echoed or stored in cleartext.
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      File Name
                    </label>
                    <input
                      type="text"
                      value={fileName}
                      onChange={(e) => setFileName(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Allowed MIME Type
                    </label>
                    <select
                      value={docMime}
                      onChange={(e) => setDocMime(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    >
                      <option value="application/pdf">application/pdf</option>
                      <option value="image/png">image/png</option>
                      <option value="image/jpeg">image/jpeg</option>
                    </select>
                  </div>
                </div>

                {/* Explicit Consent Checkbox (FR-0163) */}
                <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
                  <label className="flex items-start gap-2.5 cursor-pointer text-xs">
                    <input
                      type="checkbox"
                      checked={consentGranted}
                      onChange={(e) => setConsentGranted(e.target.checked)}
                      className="mt-0.5 h-4 w-4 rounded text-[#5278D9] focus:ring-[#5278D9]"
                    />
                    <span className="text-slate-600 dark:text-slate-300 leading-relaxed">
                      I grant explicit consent to verify this document for <strong className="text-slate-900 dark:text-white">{purpose}</strong>. I understand that raw identifiers are tokenized and stored in masked form only.
                    </span>
                  </label>
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  disabled={isInitiating || !consentGranted || !!docFormatError}
                  className="w-full flex items-center justify-center gap-2 bg-[#5278D9] hover:bg-[#4367C7]"
                >
                  {isInitiating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                  Consent & Initiate Verification
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Active Case Review & Presigned URL Access */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-500" />
                Case Review & Dual Control (FR-0175, FR-0178)
              </CardTitle>
              <CardDescription>
                Authoritative case status, short-lived presigned access, and dual approval workflow.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!activeCase ? (
                <div className="py-12 text-center text-slate-500 text-sm">
                  Initiate a verification case on the left to inspect real-time case metrics and perform reviews.
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg space-y-2 bg-slate-50/50 dark:bg-slate-900/50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm">Case #{activeCase.case_id}</span>
                        <Badge variant="purple">{activeCase.document_type}</Badge>
                      </div>
                      <Badge variant={activeCase.status === "VERIFIED" ? "success" : "warning"}>
                        {activeCase.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs text-slate-500">
                      <div>Masked ID: <span className="font-mono text-slate-700 dark:text-slate-300">{activeCase.masked_identifier}</span></div>
                      <div>Malware Scan: <span className="font-semibold text-emerald-600">{activeCase.malware_scan_status}</span></div>
                      <div>Provider: <span className="font-medium text-slate-700 dark:text-slate-300">{activeCase.provider_code}</span></div>
                      <div>Purpose: <span className="font-medium text-slate-700 dark:text-slate-300">{activeCase.purpose}</span></div>
                    </div>
                  </div>

                  {/* Secure URL Generator (FR-0165) */}
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      onClick={handleFetchSecureUrl}
                      disabled={isFetchingUrl}
                      className="text-xs flex items-center gap-1.5"
                    >
                      {isFetchingUrl ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <KeyRound className="w-3.5 h-3.5" />}
                      Generate Signed Access URL (FR-0165)
                    </Button>
                    {presignedUrl && (
                      <span className="text-xs text-emerald-600 font-mono truncate max-w-xs">
                        URL Generated & Bound
                      </span>
                    )}
                  </div>

                  {/* Review Decision Form */}
                  <form onSubmit={handleSubmitReview} className="space-y-3 pt-2 border-t border-slate-100 dark:border-slate-800">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                          Decision
                        </label>
                        <select
                          value={reviewDecision}
                          onChange={(e) => setReviewDecision(e.target.value)}
                          className="w-full px-3 py-1.5 text-xs border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                        >
                          <option value="VERIFIED">VERIFIED</option>
                          <option value="REJECTED">REJECTED</option>
                          <option value="ESCALATED_FOR_DUAL_CONTROL">ESCALATE FOR DUAL CONTROL</option>
                        </select>
                      </div>
                      <div className="flex items-center gap-2 pt-5">
                        <input
                          type="checkbox"
                          id="highRisk"
                          checked={isHighRiskOverride}
                          onChange={(e) => setIsHighRiskOverride(e.target.checked)}
                          className="rounded border-slate-300"
                        />
                        <label htmlFor="highRisk" className="text-xs font-medium text-slate-700 dark:text-slate-300">
                          Dual Control Override
                        </label>
                      </div>
                    </div>

                    {isHighRiskOverride && (
                      <div>
                        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                          Second Approver User ID (FR-0178)
                        </label>
                        <input
                          type="number"
                          placeholder="e.g. 2"
                          value={secondApproverId}
                          onChange={(e) => setSecondApproverId(e.target.value)}
                          className="w-full px-3 py-1.5 text-xs border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                          min="1"
                          required={isHighRiskOverride}
                        />
                      </div>
                    )}

                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Review Rationale
                      </label>
                      <input
                        type="text"
                        value={reviewReason}
                        onChange={(e) => setReviewReason(e.target.value)}
                        className="w-full px-3 py-1.5 text-xs border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                        required
                      />
                    </div>

                    <Button
                      type="submit"
                      variant="primary"
                      disabled={isReviewing}
                      className="w-full h-8 text-xs flex items-center justify-center gap-1.5"
                    >
                      {isReviewing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Submit Review Decision"}
                    </Button>
                  </form>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Integration Boundary Register (FR-0183) */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Network className="w-4 h-4 text-primary" />
              External Integration Boundary Register (FR-0183)
            </CardTitle>
            <CardDescription>
              Authoritative ownership, timeout bounds, retry policies, and idempotency guarantees for third-party systems.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingIntegrations ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-5 h-5 animate-spin text-primary" />
              </div>
            ) : integrations.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-sm">
                No external integration boundaries registered.
              </div>
            ) : (
              <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Provider</TableHead>
                      <TableHead>Purpose</TableHead>
                      <TableHead>Source of Truth</TableHead>
                      <TableHead>Timeout</TableHead>
                      <TableHead>Retry Policy</TableHead>
                      <TableHead>Idempotency</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {integrations.map((integ) => (
                      <TableRow key={integ.provider_code}>
                        <TableCell className="font-semibold text-xs">
                          {integ.display_name}
                          <span className="font-mono text-[10px] text-slate-400 block">{integ.provider_code}</span>
                        </TableCell>
                        <TableCell className="text-xs text-slate-600 dark:text-slate-300">
                          {integ.purpose}
                        </TableCell>
                        <TableCell className="text-xs font-mono">{integ.source_of_truth}</TableCell>
                        <TableCell className="text-xs font-mono">{integ.timeout_seconds}s</TableCell>
                        <TableCell className="text-xs text-slate-500">{integ.retry_policy}</TableCell>
                        <TableCell className="text-xs font-mono text-slate-500">{integ.idempotency_policy}</TableCell>
                        <TableCell>
                          <Badge variant="success">{integ.status}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Feature Flag Rollout Evaluator (FR-0215, FR-0216) */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <ToggleRight className="w-4 h-4 text-indigo-500" />
              Deterministic Feature Flag Rollout (FR-0215)
            </CardTitle>
            <CardDescription>
              Evaluate percentage rollout deterministically based on subject hash.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleEvaluateFlag} className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                placeholder="Flag Code"
                value={flagCode}
                onChange={(e) => setFlagCode(e.target.value)}
                className="w-full sm:w-1/2 px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-mono"
                required
              />
              <input
                type="text"
                placeholder="Subject Key (User/Tenant)"
                value={flagSubject}
                onChange={(e) => setFlagSubject(e.target.value)}
                className="w-full sm:w-1/3 px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                required
              />
              <Button
                type="submit"
                variant="outline"
                disabled={isEvaluatingFlag}
                className="text-xs flex items-center gap-1.5 whitespace-nowrap"
              >
                {isEvaluatingFlag ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Evaluate"}
              </Button>
            </form>

            {flagResult && (
              <div className="mt-4 p-3 border border-slate-100 dark:border-slate-800 rounded-md flex items-center justify-between text-xs">
                <div>
                  <span className="font-bold">{flagResult.flag_code}</span>: {flagResult.evaluation_reason}
                </div>
                <Badge variant={flagResult.enabled ? "success" : "destructive"}>
                  {flagResult.enabled ? "ENABLED" : "DISABLED"}
                </Badge>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
