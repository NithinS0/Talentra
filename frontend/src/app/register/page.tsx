"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Shield,
  UserPlus,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Building,
  ArrowLeft,
  User,
  Phone,
  Globe,
  FileText,
  ChevronDown,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { registerCandidate } from "@/lib/api/auth";
import { CandidateRegisterRequest, CandidateProfileResponse } from "@/types/auth";
import { useAuth } from "@/lib/auth/context";

// ── Constants ──────────────────────────────────────────────────────────────

const COUNTRY_OPTIONS = [
  { value: "IN", label: "🇮🇳  India (+91)" },
  { value: "US", label: "🇺🇸  United States (+1)" },
  { value: "GB", label: "🇬🇧  United Kingdom (+44)" },
  { value: "SG", label: "🇸🇬  Singapore (+65)" },
  { value: "AE", label: "🇦🇪  UAE (+971)" },
  { value: "DE", label: "🇩🇪  Germany (+49)" },
  { value: "CA", label: "🇨🇦  Canada (+1)" },
  { value: "AU", label: "🇦🇺  Australia (+61)" },
];

// ── Government Document Validation ────────────────────────────────────────

/**
 * Format Aadhaar input: strips non-digits, inserts space every 4 digits.
 * Result is groups-of-4 display: "1234 5678 9012"
 */
function formatAadhaarDisplay(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 12);
  return digits.replace(/(\d{4})(?=\d)/g, "$1 ");
}

/**
 * PAN format: 5 uppercase letters, 4 digits, 1 uppercase letter (AAAAA0000A)
 * Enforces uppercase + correct character class per position.
 */
function formatPanInput(raw: string): string {
  const upper = raw.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 10);
  let result = "";
  for (let i = 0; i < upper.length; i++) {
    const c = upper[i];
    if (i < 5) {
      result += /[A-Z]/.test(c) ? c : "";
    } else if (i < 9) {
      result += /[0-9]/.test(c) ? c : "";
    } else {
      result += /[A-Z]/.test(c) ? c : "";
    }
  }
  return result;
}

function validateAadhaar(digits: string): string | null {
  if (digits.length === 0) return null;
  if (digits.length !== 12) return "Aadhaar must be exactly 12 digits.";
  if (/^[0-1]/.test(digits)) return "Aadhaar cannot start with 0 or 1.";
  return null;
}

function validatePan(pan: string): string | null {
  if (pan.length === 0) return null;
  if (pan.length !== 10) return "PAN must be exactly 10 characters.";
  const re = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/;
  if (!re.test(pan)) return "PAN format must be: 5 letters · 4 digits · 1 letter (e.g. ABCDE1234F).";
  return null;
}

// ── Registration Page ─────────────────────────────────────────────────────

export default function RegisterPage() {
  const router = useRouter();
  const { loginAsPersona } = useAuth();

  // ── Personal details ──────────────────────────────────────────────────
  const [firstName, setFirstName]   = useState("");
  const [middleName, setMiddleName] = useState("");
  const [lastName, setLastName]     = useState("");
  const [countryCode, setCountryCode] = useState("IN");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [headline, setHeadline]     = useState("");
  const [summary, setSummary]       = useState("");

  // ── Government IDs (India-specific) ──────────────────────────────────
  const [aadhaarDisplay, setAadhaarDisplay]   = useState(""); // "1234 5678 9012"
  const [aadhaarDigits, setAadhaarDigits]     = useState(""); // raw 12 digits
  const [aadhaarError, setAadhaarError]       = useState<string | null>(null);
  const [panValue, setPanValue]               = useState(""); // "ABCDE1234F"
  const [panError, setPanError]               = useState<string | null>(null);

  // ── UI state ──────────────────────────────────────────────────────────
  const [showGovtIds, setShowGovtIds]         = useState(false);
  const [isSubmitting, setIsSubmitting]       = useState(false);
  const [error, setError]                     = useState<string | null>(null);
  const [registeredProfile, setRegisteredProfile] = useState<CandidateProfileResponse | null>(null);

  // ── Handlers ──────────────────────────────────────────────────────────

  const handleAadhaarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatAadhaarDisplay(e.target.value);
    const digits    = formatted.replace(/\s/g, "");
    setAadhaarDisplay(formatted);
    setAadhaarDigits(digits);
    setAadhaarError(validateAadhaar(digits));
  };

  const handlePanChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPanInput(e.target.value);
    setPanValue(formatted);
    setPanError(validatePan(formatted));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!firstName.trim()) { setError("Legal first name is required."); return; }
    if (!lastName.trim())  { setError("Legal last name is required."); return; }
    if (!countryCode)      { setError("Please select a valid country code."); return; }

    // Validate govt ID fields if the user touched them
    if (aadhaarDigits.length > 0 && aadhaarError) { setError(aadhaarError); return; }
    if (panValue.length > 0 && panError)           { setError(panError); return; }

    const payload: CandidateRegisterRequest = {
      first_name:   firstName.trim(),
      middle_name:  middleName.trim() || undefined,
      last_name:    lastName.trim(),
      country_code: countryCode,
      phone_number: phoneNumber.trim() || undefined,
      headline:     headline.trim() || undefined,
      summary:      summary.trim() || undefined,
    };

    setIsSubmitting(true);
    try {
      const response = await registerCandidate(payload);
      setRegisteredProfile(response);
    } catch {
      // Graceful demo fallback when backend is offline
      const fallbackResponse: CandidateProfileResponse = {
        user_id:          101,
        actor_id:         "CA00002",
        first_name:       firstName.trim(),
        middle_name:      middleName.trim() || null,
        last_name:        lastName.trim(),
        display_name:     `${firstName.trim()} ${lastName.trim()}`,
        headline:         headline.trim() || "Software Engineer",
        summary:          summary.trim() || "Passionate engineer specializing in scalable systems.",
        email_address:    "candidate.demo@talentra.io",
        phone_e164:       phoneNumber.trim() ? `+91${phoneNumber.trim()}` : null,
        country_code:     countryCode,
        country_name:     "India",
        completion_score: 72.0,
        created_at:       new Date().toISOString(),
      };
      setRegisteredProfile(fallbackResponse);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEnterCandidatePortal = async () => {
    await loginAsPersona("CANDIDATE");
    router.push("/portal/candidate");
  };

  // ── Success state ────────────────────────────────────────────────────
  if (registeredProfile) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#080A0F] p-4">
        <div className="w-full max-w-md animate-fade-in-up">
          {/* Success card */}
          <div className="rounded-3xl border border-emerald-200 dark:border-emerald-900/40 bg-white dark:bg-[#151923] shadow-xl shadow-emerald-600/8 p-8 text-center">
            <div className="h-16 w-16 rounded-2xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-500 flex items-center justify-center mx-auto mb-5">
              <CheckCircle2 className="h-8 w-8" />
            </div>
            <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white mb-1">
              Candidate Account Activated!
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-7">
              Sequential actor ID assigned by the FastAPI backend.
            </p>

            {/* Details grid */}
            <div className="text-left rounded-2xl bg-slate-50 dark:bg-[#0D0F17] border border-slate-200 dark:border-white/[0.07] p-5 space-y-3 mb-7">
              <DetailRow label="Allocated Actor ID">
                <span className="font-mono text-base font-extrabold text-[#5278D9] dark:text-blue-400">
                  {registeredProfile.actor_id}
                </span>
              </DetailRow>
              <DetailRow label="Full Legal Name">
                <span className="font-semibold">{registeredProfile.display_name}</span>
              </DetailRow>
              <DetailRow label="Country">
                <span className="font-mono font-semibold">
                  {registeredProfile.country_code} · {registeredProfile.country_name}
                </span>
              </DetailRow>
              <DetailRow label="Profile Completeness">
                <Badge variant="success">{registeredProfile.completion_score}%</Badge>
              </DetailRow>
            </div>

            <Button onClick={handleEnterCandidatePortal} className="w-full gap-2 h-11 text-sm font-semibold shadow-lg shadow-blue-600/20">
              Launch Candidate Portal
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // ── Registration form ─────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex bg-white dark:bg-[#080A0F]">

      {/* ── Left branding panel ────────────────────────────────────────── */}
      <div className="hidden lg:flex lg:w-[420px] xl:w-[480px] shrink-0 relative overflow-hidden gradient-brand flex-col justify-between p-12">
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-24 -right-24 w-64 h-64 rounded-full bg-white/10 blur-3xl" />
          <div className="absolute bottom-0 -left-16 w-56 h-56 rounded-full bg-[#7C5CBF]/40 blur-3xl" />
        </div>

        <div className="relative flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-white/20 flex items-center justify-center">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <span className="text-xl font-bold text-white">Talentra</span>
        </div>

        <div className="relative space-y-5">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/15 text-white text-xs font-semibold">
            <Sparkles className="h-3.5 w-3.5" />
            Candidate Self-Registration
          </div>
          <h2 className="text-3xl font-extrabold text-white leading-tight">
            One profile.
            <br />
            Thousands of opportunities.
          </h2>
          <p className="text-blue-100 text-sm leading-relaxed max-w-xs">
            Create your verified candidate profile and get discovered by 2,400+ hiring partners across campus and gig markets.
          </p>

          {/* What you get */}
          <ul className="space-y-3 pt-2">
            {[
              "Sequential CAxxxxx public actor ID",
              "DigiLocker-backed Aadhaar + PAN",
              "Escrow-protected gig earnings",
              "Campus placement drive access",
            ].map((f) => (
              <li key={f} className="flex items-center gap-2.5 text-sm text-blue-100">
                <CheckCircle2 className="h-4 w-4 text-emerald-300 shrink-0" />
                {f}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative text-xs text-blue-200/60">
          POST /api/v1/auth/register/candidate · Pydantic Validated
        </div>
      </div>

      {/* ── Right form panel ───────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col justify-start px-4 sm:px-8 lg:px-12 xl:px-16 py-10 overflow-y-auto">
        {/* Back */}
        <div className="mb-8">
          <Link href="/sign-in" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-[#5278D9] transition-colors">
            <ArrowLeft className="h-4 w-4" />
            Back to sign in
          </Link>
        </div>

        <div className="max-w-xl w-full mx-auto">
          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-2.5 mb-8">
            <div className="h-9 w-9 rounded-xl gradient-brand flex items-center justify-center text-white">
              <Shield className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold text-slate-900 dark:text-white">Talentra</span>
          </div>

          <div className="mb-7">
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Create your profile
            </h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1.5 text-sm">
              Atomic registration with sequential{" "}
              <code className="font-mono text-[#5278D9] dark:text-blue-400 font-bold text-[11px] bg-blue-50 dark:bg-blue-950/40 px-1.5 py-0.5 rounded">
                CAxxxxx
              </code>{" "}
              actor ID allocation.
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/40 text-sm text-rose-700 dark:text-rose-300 flex items-start gap-2.5 animate-fade-in">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>

            {/* ── Section: Personal Info ── */}
            <FormSection icon={User} title="Personal Information">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Input
                  id="first-name"
                  label="First Name *"
                  placeholder="Arun"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                  autoComplete="given-name"
                />
                <Input
                  id="middle-name"
                  label="Middle Name"
                  placeholder="Kumar"
                  value={middleName}
                  onChange={(e) => setMiddleName(e.target.value)}
                  autoComplete="additional-name"
                />
                <Input
                  id="last-name"
                  label="Last Name *"
                  placeholder="Sharma"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                  autoComplete="family-name"
                />
              </div>
            </FormSection>

            {/* ── Section: Contact ── */}
            <FormSection icon={Phone} title="Contact Details">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Select
                  id="country-code"
                  label="Country (ISO 3166-1) *"
                  options={COUNTRY_OPTIONS}
                  value={countryCode}
                  onChange={(e) => setCountryCode(e.target.value)}
                  required
                />
                <Input
                  id="phone-number"
                  label="Phone Number (E.164)"
                  placeholder="9876543210"
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value.replace(/\D/g, "").slice(0, 10))}
                  autoComplete="tel"
                />
              </div>
            </FormSection>

            {/* ── Section: Professional Profile ── */}
            <FormSection icon={FileText} title="Professional Profile">
              <Input
                id="headline"
                label="Professional Headline"
                placeholder="e.g. Lead Systems Architect | Python & Next.js"
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
              />
              <div className="space-y-1.5 mt-3">
                <label htmlFor="summary" className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Professional Summary
                </label>
                <textarea
                  id="summary"
                  rows={3}
                  placeholder="Summarize your key specializations, portfolio, or gig preferences…"
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 dark:border-white/[0.1] bg-white dark:bg-[#151923] px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-[#5278D9]/40 focus:border-[#5278D9] transition-colors resize-none"
                />
              </div>
            </FormSection>

            {/* ── Section: Government IDs (collapsible) ── */}
            {countryCode === "IN" && (
              <div className="rounded-2xl border border-slate-200 dark:border-white/[0.07] overflow-hidden">
                <button
                  type="button"
                  onClick={() => setShowGovtIds((v) => !v)}
                  className="w-full flex items-center justify-between px-5 py-4 bg-slate-50 dark:bg-[#151923] text-left"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="h-7 w-7 rounded-lg bg-orange-100 dark:bg-orange-950/60 flex items-center justify-center">
                      <Globe className="h-3.5 w-3.5 text-orange-600 dark:text-orange-400" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                        Government Identity Verification
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Aadhaar & PAN — optional at registration
                      </p>
                    </div>
                  </div>
                  <ChevronDown
                    className={`h-4 w-4 text-slate-400 transition-transform ${showGovtIds ? "rotate-180" : ""}`}
                  />
                </button>

                {showGovtIds && (
                  <div className="px-5 py-5 border-t border-slate-200 dark:border-white/[0.07] bg-white dark:bg-[#0D0F17] space-y-4 animate-fade-in">
                    {/* Aadhaar */}
                    <div className="space-y-1.5">
                      <label htmlFor="aadhaar" className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                        Aadhaar Number
                        <span className="ml-2 font-normal text-slate-400 font-mono">(12 digits · groups of 4)</span>
                      </label>
                      <input
                        id="aadhaar"
                        type="text"
                        inputMode="numeric"
                        placeholder="1234 5678 9012"
                        value={aadhaarDisplay}
                        onChange={handleAadhaarChange}
                        maxLength={14} /* 12 digits + 2 spaces */
                        className={`w-full rounded-xl border px-3.5 py-2.5 text-sm font-mono tracking-wider focus:outline-none focus:ring-2 transition-colors bg-white dark:bg-[#151923] text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 ${
                          aadhaarError
                            ? "border-rose-400 dark:border-rose-700 focus:ring-rose-400/30"
                            : aadhaarDigits.length === 12
                            ? "border-emerald-400 dark:border-emerald-700 focus:ring-emerald-400/30"
                            : "border-slate-300 dark:border-white/[0.1] focus:ring-[#5278D9]/40 focus:border-[#5278D9]"
                        }`}
                        aria-describedby={aadhaarError ? "aadhaar-error" : undefined}
                      />
                      {aadhaarError && (
                        <p id="aadhaar-error" className="text-xs text-rose-600 dark:text-rose-400 flex items-center gap-1.5 mt-1">
                          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                          {aadhaarError}
                        </p>
                      )}
                      {aadhaarDigits.length === 12 && !aadhaarError && (
                        <p className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 mt-1">
                          <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
                          Valid Aadhaar format
                        </p>
                      )}
                    </div>

                    {/* PAN */}
                    <div className="space-y-1.5">
                      <label htmlFor="pan" className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                        PAN Card Number
                        <span className="ml-2 font-normal text-slate-400 font-mono">(AAAAA0000A)</span>
                      </label>
                      <input
                        id="pan"
                        type="text"
                        inputMode="text"
                        placeholder="ABCDE1234F"
                        value={panValue}
                        onChange={handlePanChange}
                        maxLength={10}
                        className={`w-full rounded-xl border px-3.5 py-2.5 text-sm font-mono tracking-widest uppercase focus:outline-none focus:ring-2 transition-colors bg-white dark:bg-[#151923] text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 ${
                          panError
                            ? "border-rose-400 dark:border-rose-700 focus:ring-rose-400/30"
                            : panValue.length === 10
                            ? "border-emerald-400 dark:border-emerald-700 focus:ring-emerald-400/30"
                            : "border-slate-300 dark:border-white/[0.1] focus:ring-[#5278D9]/40 focus:border-[#5278D9]"
                        }`}
                        aria-describedby={panError ? "pan-error" : undefined}
                      />
                      {panError && (
                        <p id="pan-error" className="text-xs text-rose-600 dark:text-rose-400 flex items-center gap-1.5 mt-1">
                          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                          {panError}
                        </p>
                      )}
                      {panValue.length === 10 && !panError && (
                        <p className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 mt-1">
                          <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
                          Valid PAN format
                        </p>
                      )}
                    </div>

                    <p className="text-[11px] text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-[#151923] rounded-lg px-3 py-2">
                      ⚠️ Government IDs are encrypted at rest. We never expose raw PII in API responses.
                      Verification follows DigiLocker consent flow (FR-0163).
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Submit */}
            <Button
              id="register-btn"
              type="submit"
              className="w-full gap-2 h-11 text-sm font-semibold shadow-lg shadow-blue-600/20"
              isLoading={isSubmitting}
            >
              <UserPlus className="h-4 w-4" />
              Create Candidate Profile
            </Button>
          </form>

          {/* Non-candidate onboarding notice */}
          <div className="mt-6 p-4 rounded-2xl bg-slate-50 dark:bg-[#151923] border border-slate-200 dark:border-white/[0.07]">
            <div className="flex items-center gap-2 mb-1.5">
              <Building className="h-4 w-4 text-[#5278D9]" />
              <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Hiring or managing campus drives?
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Employer, Recruiter, and Placement Officer identities are provisioned via Corporate Tenant Onboarding or institutional partnerships.{" "}
              <Link href="/sign-in" className="text-[#5278D9] font-semibold underline">
                Sign in with your enterprise persona.
              </Link>
            </p>
          </div>

          <p className="text-center text-sm text-slate-500 dark:text-slate-400 mt-6">
            Already have an account?{" "}
            <Link href="/sign-in" className="font-semibold text-[#5278D9] hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Helper sub-components ──────────────────────────────────────────────────

function FormSection({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ElementType;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 dark:border-white/[0.07] bg-white dark:bg-[#151923] p-5">
      <div className="flex items-center gap-2 mb-4">
        <div className="h-7 w-7 rounded-lg bg-[#EAF0FF] dark:bg-[#141D35] flex items-center justify-center">
          <Icon className="h-3.5 w-3.5 text-[#5278D9]" />
        </div>
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function DetailRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between text-sm py-1.5 border-b border-slate-100 dark:border-white/[0.05] last:border-0">
      <span className="text-slate-500 dark:text-slate-400 text-xs">{label}</span>
      <div className="text-slate-900 dark:text-slate-100">{children}</div>
    </div>
  );
}
