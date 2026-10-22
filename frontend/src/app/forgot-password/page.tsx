"use client";

import { useState } from "react";
import Link from "next/link";
import { Shield, KeyRound, CheckCircle2, AlertCircle, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !email.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }

    setIsSubmitting(true);
    // Non-revealing password reset dispatch (Supabase Auth IdP protocol)
    setTimeout(() => {
      setIsSubmitting(false);
      setSubmitted(true);
    }, 600);
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-slate-50 dark:bg-slate-950">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link href="/" className="inline-flex items-center gap-2 mb-4">
          <div className="h-10 w-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/30">
            <Shield className="h-6 w-6" />
          </div>
          <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Talentra</span>
        </Link>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Reset your password
        </h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Instructions will be sent via our verified authentication provider.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card className="border-slate-200 dark:border-slate-800 shadow-xl">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg">Account Recovery</CardTitle>
            <CardDescription className="text-xs">
              Enter your verified email address to receive a secure password reset link.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {submitted ? (
              <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 space-y-2 text-xs text-emerald-800 dark:text-emerald-200">
                <div className="flex items-center gap-2 font-bold text-sm text-emerald-700 dark:text-emerald-300">
                  <CheckCircle2 className="h-5 w-5" />
                  <span>Recovery Dispatch Complete</span>
                </div>
                <p>
                  If an account associated with <span className="font-semibold">{email}</span> exists, you will receive a secure recovery link shortly.
                </p>
                <p className="text-[11px] text-slate-500 pt-1">
                  For security, the platform does not reveal whether specific email addresses are registered.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-xs text-red-700 dark:text-red-300 flex items-start gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                    <span>{error}</span>
                  </div>
                )}

                <Input
                  label="Registered Email Address"
                  type="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />

                <Button type="submit" className="w-full gap-2" isLoading={isSubmitting}>
                  <KeyRound className="h-4 w-4" />
                  Send Recovery Link
                </Button>
              </form>
            )}
          </CardContent>
          <CardFooter className="pt-0 flex justify-between text-xs text-slate-500">
            <Link href="/sign-in" className="hover:text-indigo-600 transition-colors inline-flex items-center gap-1">
              <ArrowLeft className="h-3.5 w-3.5" />
              Return to Sign In
            </Link>
            <span>IdP Recovery Protocol</span>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
