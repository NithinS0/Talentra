"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Shield,
  Lock,
  AlertCircle,
  KeyRound,
  UserPlus,
  Eye,
  EyeOff,
  ChevronRight,
  ArrowLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth, DEMO_PERSONAS } from "@/lib/auth/context";
import { getSafeReturnUrl, getPortalPathForRole } from "@/lib/auth/session";

// ── Role colour map ────────────────────────────────────────────────────────
const ROLE_COLORS: Record<string, { bg: string; dot: string; text: string }> = {
  SUPER_ADMIN:       { bg: "bg-rose-100 dark:bg-rose-950/60",   dot: "bg-rose-500",   text: "text-rose-700 dark:text-rose-300" },
  ADMIN:             { bg: "bg-orange-100 dark:bg-orange-950/60", dot: "bg-orange-500", text: "text-orange-700 dark:text-orange-300" },
  ACCOUNT_ADMIN:     { bg: "bg-amber-100 dark:bg-amber-950/60",  dot: "bg-amber-500",  text: "text-amber-700 dark:text-amber-300" },
  EMPLOYER:          { bg: "bg-blue-100 dark:bg-blue-950/60",    dot: "bg-blue-500",   text: "text-blue-700 dark:text-blue-300" },
  RECRUITER:         { bg: "bg-indigo-100 dark:bg-indigo-950/60",dot: "bg-indigo-500", text: "text-indigo-700 dark:text-indigo-300" },
  CONSULTANT:        { bg: "bg-violet-100 dark:bg-violet-950/60",dot: "bg-violet-500", text: "text-violet-700 dark:text-violet-300" },
  CANDIDATE:         { bg: "bg-emerald-100 dark:bg-emerald-950/60",dot: "bg-emerald-500",text: "text-emerald-700 dark:text-emerald-300" },
  PLACEMENT_OFFICER: { bg: "bg-teal-100 dark:bg-teal-950/60",    dot: "bg-teal-500",   text: "text-teal-700 dark:text-teal-300" },
  GUEST:             { bg: "bg-slate-100 dark:bg-slate-800",      dot: "bg-slate-400",  text: "text-slate-700 dark:text-slate-300" },
};

// ── Sign-In form (needs Suspense for useSearchParams) ─────────────────────
function SignInContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnUrlParam = searchParams.get("returnUrl");

  const { login, switchPersona, error, clearError } = useAuth();

  const [email, setEmail]               = useState("candidate.demo@talentra.io");
  const [password, setPassword]         = useState("password123");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError]       = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setFormError(null);

    if (!email || !email.includes("@")) {
      setFormError("Please enter a valid email address.");
      return;
    }
    if (!password || password.length < 6) {
      setFormError("Password must be at least 6 characters.");
      return;
    }

    setIsSubmitting(true);
    try {
      await login(email, password);
      const target = getSafeReturnUrl(returnUrlParam, "/dashboard");
      router.push(target);
    } catch (err: unknown) {
      setFormError(
        err instanceof Error ? err.message : "Failed to sign in. Please verify your credentials."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectPersona = (actorId: string, pEmail: string, roleCode: string) => {
    setEmail(pEmail);
    setPassword("password123");
    switchPersona(actorId);
    const target = getSafeReturnUrl(returnUrlParam, getPortalPathForRole(roleCode));
    router.push(target);
  };

  const displayError = formError || error;

  return (
    <div className="min-h-screen flex bg-white dark:bg-[#080A0F]">

      {/* ── Left panel — branding ────────────────────────────────────────── */}
      <div className="hidden lg:flex lg:w-[480px] xl:w-[560px] shrink-0 relative overflow-hidden gradient-brand flex-col justify-between p-12">
        {/* Decorative blobs */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-32 -right-32 w-80 h-80 rounded-full bg-white/10 blur-3xl" />
          <div className="absolute bottom-0 -left-16 w-64 h-64 rounded-full bg-[#7C5CBF]/40 blur-3xl" />
        </div>

        {/* Logo */}
        <div className="relative flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <span className="text-xl font-bold text-white tracking-tight">Talentra</span>
        </div>

        {/* Taglines */}
        <div className="relative space-y-5">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/15 text-white text-xs font-semibold">
            <span className="status-dot online" />
            Campus &amp; Enterprise Marketplace
          </div>
          <h1 className="text-4xl font-extrabold text-white leading-tight tracking-tight">
            Your career,
            <br />
            secured &amp; verified
          </h1>
          <p className="text-blue-100 text-sm leading-relaxed max-w-xs">
            Join 48,000+ students and enterprise professionals on the platform with
            cryptographic milestone escrow and DigiLocker identity verification.
          </p>

          {/* Feature list */}
          <ul className="space-y-3">
            {[
              "Aadhaar & PAN identity verification",
              "Milestone-based escrow payments",
              "9 role-specific portals",
              "Campus & off-campus placement drives",
            ].map((f) => (
              <li key={f} className="flex items-center gap-3 text-sm text-blue-100">
                <span className="h-5 w-5 rounded-full bg-white/20 flex items-center justify-center shrink-0">
                  <ChevronRight className="h-3 w-3 text-white" />
                </span>
                {f}
              </li>
            ))}
          </ul>
        </div>

        {/* Footer note */}
        <div className="relative text-xs text-blue-200/70">
          Stage 17E · FastAPI + Next.js · Supabase PostgreSQL
        </div>
      </div>

      {/* ── Right panel — form ───────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col justify-center px-4 sm:px-8 lg:px-16 py-12 overflow-y-auto">
        {/* Back link */}
        <div className="mb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-[#5278D9] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to home
          </Link>
        </div>

        <div className="max-w-md w-full mx-auto">

          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-2.5 mb-8">
            <div className="h-9 w-9 rounded-xl gradient-brand flex items-center justify-center text-white shadow-lg shadow-blue-600/25">
              <Shield className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Talentra</span>
          </div>

          <div className="mb-8">
            <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              Welcome back
            </h2>
            <p className="text-slate-500 dark:text-slate-400 mt-1.5 text-sm">
              Sign in to your workspace or choose a demo persona below.
            </p>
          </div>

          {/* Error banner */}
          {displayError && (
            <div className="mb-5 p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/50 text-sm text-rose-700 dark:text-rose-300 flex items-start gap-2.5 animate-fade-in">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{displayError}</span>
            </div>
          )}

          {/* Sign-In form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              id="email"
              label="Email Address"
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />

            <div className="space-y-1">
              <div className="relative">
                <Input
                  id="password"
                  label="Password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((p) => !p)}
                  className="absolute right-3 bottom-[11px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <div className="flex justify-end">
                <Link
                  href="/forgot-password"
                  className="text-xs text-[#5278D9] hover:underline inline-flex items-center gap-1"
                >
                  <KeyRound className="h-3 w-3" />
                  Forgot password?
                </Link>
              </div>
            </div>

            <Button
              id="sign-in-btn"
              type="submit"
              className="w-full gap-2 mt-2 h-11 text-sm font-semibold shadow-lg shadow-blue-600/20"
              isLoading={isSubmitting}
            >
              <Lock className="h-4 w-4" />
              Sign In to Workspace
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200 dark:border-white/[0.08]" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-white dark:bg-[#080A0F] px-3 text-xs font-medium text-slate-400">
                Or sign in with a demo persona
              </span>
            </div>
          </div>

          {/* Persona quick grid */}
          <div className="space-y-2">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">
              9 Seeded Demo Actors
            </p>
            <div className="grid grid-cols-1 gap-2">
              {DEMO_PERSONAS.filter((p) => p.roleCode !== "GUEST").map((p) => {
                const colors = ROLE_COLORS[p.roleCode] || ROLE_COLORS.GUEST;
                return (
                  <button
                    key={p.actorId}
                    type="button"
                    id={`persona-${p.actorId.toLowerCase()}`}
                    onClick={() => handleSelectPersona(p.actorId, p.email, p.roleCode)}
                    className="flex items-center gap-3 w-full p-3 rounded-xl border border-slate-200 dark:border-white/[0.07] bg-slate-50 dark:bg-[#151923] hover:border-[#5278D9]/50 hover:bg-[#EAF0FF] dark:hover:bg-[#141D35] text-left transition-all group"
                  >
                    {/* Role dot + prefix */}
                    <div className={`shrink-0 h-8 w-8 rounded-lg ${colors.bg} flex items-center justify-center`}>
                      <span className={`font-mono text-[10px] font-bold ${colors.text}`}>
                        {p.actorId.slice(0, 2)}
                      </span>
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate group-hover:text-[#5278D9] transition-colors">
                        {p.name}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">{p.actorId}</div>
                    </div>

                    <span className={`shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full ${colors.bg} ${colors.text}`}>
                      {p.roleCode.replace(/_/g, " ")}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Register link */}
          <p className="text-center text-sm text-slate-500 dark:text-slate-400 mt-8">
            New to Talentra?{" "}
            <Link
              href="/register"
              className="font-semibold text-[#5278D9] hover:underline inline-flex items-center gap-1"
            >
              <UserPlus className="h-3.5 w-3.5" />
              Create a candidate account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function SignInPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-white dark:bg-[#080A0F]">
          <div className="flex flex-col items-center gap-3">
            <div className="h-10 w-10 rounded-xl gradient-brand flex items-center justify-center animate-pulse">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <p className="text-sm text-slate-500">Loading sign in…</p>
          </div>
        </div>
      }
    >
      <SignInContent />
    </Suspense>
  );
}
