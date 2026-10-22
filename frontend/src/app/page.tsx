"use client";

import { useState } from "react";
import Link from "next/link";
import {
  GraduationCap,
  ArrowRight,
  CheckCircle2,
  Building2,
  FileCheck2,
  Clock,
  ShieldCheck,
  Menu,
  X,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/layout/theme-toggle";

export default function HomePage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F9FC] dark:bg-[#080A0F] text-[#17233D] dark:text-[#F4F6FC] transition-colors">
      {/* ─── Top Navigation ─────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 w-full bg-white/90 dark:bg-[#080A0F]/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-8">
              <Link href="/" className="flex items-center gap-2.5">
                <div className="h-9 w-9 rounded-lg bg-[#5278D9] flex items-center justify-center text-white shadow-xs">
                  <GraduationCap className="h-5 w-5" />
                </div>
                <div className="flex flex-col">
                  <span className="text-base font-bold tracking-tight text-slate-900 dark:text-slate-100 leading-none">
                    Talentra
                  </span>
                  <span className="text-[10px] text-slate-500 font-medium">Campus Placement</span>
                </div>
              </Link>

              {/* Desktop Nav Links */}
              <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600 dark:text-slate-300">
                <Link href="/jobs" className="hover:text-[#5278D9] transition-colors">
                  Opportunities
                </Link>
                <a href="#how-it-works" className="hover:text-[#5278D9] transition-colors">
                  How It Works
                </a>
                <a href="#for-students" className="hover:text-[#5278D9] transition-colors">
                  For Students
                </a>
                <a href="#verification" className="hover:text-[#5278D9] transition-colors">
                  Verification & Privacy
                </a>
                <a href="#about" className="hover:text-[#5278D9] transition-colors">
                  About
                </a>
              </div>
            </div>

            {/* Right Actions */}
            <div className="hidden md:flex items-center gap-3">
              <ThemeToggle />
              <Link href="/sign-in">
                <Button variant="ghost" size="sm" className="text-sm font-medium">
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button size="sm" className="bg-[#5278D9] hover:bg-[#4367C7] text-white text-sm font-medium px-4 h-9 rounded-lg shadow-xs">
                  Get Started
                </Button>
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <div className="flex items-center gap-2 md:hidden">
              <ThemeToggle />
              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
                aria-label="Toggle navigation"
              >
                {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923] px-4 pt-2 pb-4 space-y-3">
            <Link
              href="/jobs"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-1.5 text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Opportunities
            </Link>
            <a
              href="#how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-1.5 text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              How It Works
            </a>
            <a
              href="#for-students"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-1.5 text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              For Students
            </a>
            <a
              href="#verification"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-1.5 text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Verification & Privacy
            </a>
            <div className="pt-2 border-t border-slate-200 dark:border-slate-800 flex items-center gap-3">
              <Link href="/sign-in" className="flex-1">
                <Button variant="outline" size="sm" className="w-full">
                  Sign In
                </Button>
              </Link>
              <Link href="/register" className="flex-1">
                <Button size="sm" className="w-full bg-[#5278D9] hover:bg-[#4367C7] text-white">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        )}
      </nav>

      {/* ─── Hero Section ───────────────────────────────────────────────────── */}
      <section className="relative pt-16 pb-20 md:pt-24 md:pb-28 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12 md:mb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#5278D9]/20 bg-[#EAF0FF] dark:bg-[#5278D9]/10 text-[#5278D9] text-xs font-semibold mb-6">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Campus Career & Placement Platform</span>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.15]">
              Your talent. <br className="hidden sm:inline" />
              Your next opportunity.
            </h1>
            <p className="mt-5 text-lg sm:text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto font-normal leading-relaxed">
              Build your profile, discover relevant opportunities, and manage your career journey in one place.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3.5">
              <Link href="/register" className="w-full sm:w-auto">
                <Button size="lg" className="w-full sm:w-auto bg-[#5278D9] hover:bg-[#4367C7] text-white font-medium h-12 px-6 rounded-lg text-sm shadow-sm gap-2">
                  <span>Get Started</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/jobs" className="w-full sm:w-auto">
                <Button variant="outline" size="lg" className="w-full sm:w-auto border-slate-300 dark:border-slate-700 font-medium h-12 px-6 rounded-lg text-sm bg-white dark:bg-[#151923]">
                  Explore Opportunities
                </Button>
              </Link>
            </div>
          </div>

          {/* Product Preview — Clean, Understated & Believable */}
          <div className="relative mx-auto max-w-5xl">
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923] shadow-lg overflow-hidden">
              {/* Window Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-[#111420] text-xs text-slate-500">
                <div className="flex items-center gap-2">
                  <div className="h-2.5 w-2.5 rounded-full bg-slate-300 dark:bg-slate-700" />
                  <div className="h-2.5 w-2.5 rounded-full bg-slate-300 dark:bg-slate-700" />
                  <div className="h-2.5 w-2.5 rounded-full bg-slate-300 dark:bg-slate-700" />
                  <span className="ml-2 font-mono text-[11px] text-slate-400">talentra.io/portal/candidate</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[10px] bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900/60 font-medium">
                    Verified Student Record
                  </Badge>
                </div>
              </div>

              {/* Preview Content Grid */}
              <div className="p-6 grid grid-cols-1 md:grid-cols-12 gap-6 bg-slate-50/50 dark:bg-[#0E121B]">
                {/* Left Column: Candidate Summary Card */}
                <div className="md:col-span-4 space-y-4">
                  <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923]">
                    <div className="flex items-start gap-3">
                      <div className="h-12 w-12 rounded-lg bg-[#5278D9]/10 text-[#5278D9] font-bold text-base flex items-center justify-center shrink-0 border border-[#5278D9]/20">
                        AN
                      </div>
                      <div className="min-w-0">
                        <div className="font-semibold text-sm text-slate-900 dark:text-white truncate">
                          Ananya Sharma
                        </div>
                        <div className="text-xs text-slate-500 truncate">
                          B.Tech Computer Science
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          Class of 2026 · CGPA 8.84
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
                      <div className="flex items-center justify-between text-xs mb-1.5">
                        <span className="text-slate-500 font-medium">Profile Completeness</span>
                        <span className="font-semibold text-[#5278D9]">85%</span>
                      </div>
                      <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div className="bg-[#5278D9] h-1.5 rounded-full" style={{ width: "85%" }} />
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-wrap gap-1.5">
                      <span className="px-2 py-0.5 text-[11px] rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium">
                        TypeScript
                      </span>
                      <span className="px-2 py-0.5 text-[11px] rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium">
                        Python
                      </span>
                      <span className="px-2 py-0.5 text-[11px] rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium">
                        FastAPI
                      </span>
                      <span className="px-2 py-0.5 text-[11px] rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium">
                        PostgreSQL
                      </span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923] flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <FileCheck2 className="h-4 w-4 text-[#5278D9]" />
                      <span className="font-medium text-slate-700 dark:text-slate-300">Resume Uploaded</span>
                    </div>
                    <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">Verified PDF</span>
                  </div>
                </div>

                {/* Right Column: Opportunity & Live Application Pipeline */}
                <div className="md:col-span-8 space-y-4">
                  {/* Job Requisition Card */}
                  <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923]">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-sm text-slate-900 dark:text-white">
                            Associate Systems Engineer
                          </span>
                          <Badge variant="outline" className="text-[10px] font-medium bg-[#EAF0FF] text-[#5278D9] border-[#5278D9]/20">
                            Eligible
                          </Badge>
                        </div>
                        <div className="text-xs text-slate-500 mt-1 flex items-center gap-3">
                          <span className="flex items-center gap-1">
                            <Building2 className="h-3.5 w-3.5 text-slate-400" />
                            Cloud Native Solutions
                          </span>
                          <span>Bangalore · On-site</span>
                          <span className="font-medium text-slate-700 dark:text-slate-300">₹8.5 — ₹12 LPA</span>
                        </div>
                      </div>
                      <Badge className="bg-[#E4F5EC] text-[#28844D] border-0 text-[11px] font-medium">
                        Drive Active
                      </Badge>
                    </div>

                    {/* Eligibility Checklist */}
                    <div className="mt-3.5 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs grid grid-cols-2 sm:grid-cols-3 gap-2 text-slate-600 dark:text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                        <span>Min 7.5 CGPA (You: 8.84)</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                        <span>CS / IT Branch</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                        <span>0 Active Backlogs</span>
                      </div>
                    </div>
                  </div>

                  {/* Stage-by-Stage Application Progression */}
                  <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923]">
                    <div className="flex items-center justify-between mb-3 text-xs">
                      <span className="font-semibold text-slate-900 dark:text-white">
                        Application Status Tracker
                      </span>
                      <span className="text-[11px] text-slate-500">Requisition #REQ-4091</span>
                    </div>

                    <div className="grid grid-cols-4 gap-2 text-center">
                      <div className="p-2.5 rounded border border-emerald-200 bg-[#E4F5EC] dark:bg-emerald-950/30 dark:border-emerald-900/60">
                        <div className="text-[10px] text-emerald-700 dark:text-emerald-400 font-semibold uppercase tracking-wider">
                          Step 1
                        </div>
                        <div className="text-xs font-semibold text-emerald-900 dark:text-emerald-200 mt-0.5">
                          Applied
                        </div>
                        <div className="text-[10px] text-emerald-600 dark:text-emerald-400 mt-0.5">Completed</div>
                      </div>

                      <div className="p-2.5 rounded border border-emerald-200 bg-[#E4F5EC] dark:bg-emerald-950/30 dark:border-emerald-900/60">
                        <div className="text-[10px] text-emerald-700 dark:text-emerald-400 font-semibold uppercase tracking-wider">
                          Step 2
                        </div>
                        <div className="text-xs font-semibold text-emerald-900 dark:text-emerald-200 mt-0.5">
                          Screening
                        </div>
                        <div className="text-[10px] text-emerald-600 dark:text-emerald-400 mt-0.5">Shortlisted</div>
                      </div>

                      <div className="p-2.5 rounded border border-[#5278D9]/30 bg-[#EAF0FF] dark:bg-[#5278D9]/10 dark:border-[#5278D9]/40">
                        <div className="text-[10px] text-[#5278D9] font-semibold uppercase tracking-wider">
                          Step 3
                        </div>
                        <div className="text-xs font-semibold text-slate-900 dark:text-white mt-0.5">
                          Technical
                        </div>
                        <div className="text-[10px] text-[#5278D9] font-medium mt-0.5">Scheduled Oct 26</div>
                      </div>

                      <div className="p-2.5 rounded border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-[#111420] opacity-60">
                        <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
                          Step 4
                        </div>
                        <div className="text-xs font-semibold text-slate-600 dark:text-slate-400 mt-0.5">
                          Decision
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">Final Offer</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Section: How Talentra Works ────────────────────────────────────── */}
      <section id="how-it-works" className="py-20 border-t border-slate-200/80 dark:border-slate-800 bg-white dark:bg-[#080A0F]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mb-14">
            <span className="text-xs font-semibold text-[#5278D9] uppercase tracking-wider">Process Workflow</span>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
              How Talentra Works
            </h2>
            <p className="mt-3 text-base text-slate-600 dark:text-slate-400">
              A structured, transparent lifecycle connecting students, placement offices, and hiring organizations.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-[#F7F9FC] dark:bg-[#151923]">
              <div className="h-10 w-10 rounded-lg bg-[#EAF0FF] dark:bg-[#5278D9]/20 text-[#5278D9] flex items-center justify-center font-bold text-sm mb-4">
                01
              </div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Create Verified Profile</h3>
              <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Add academics, semester scores, projects, verified credentials, and standardized resume in one place.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-[#F7F9FC] dark:bg-[#151923]">
              <div className="h-10 w-10 rounded-lg bg-[#E4F5EC] dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-sm mb-4">
                02
              </div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Automated Eligibility</h3>
              <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Requisitions match your CGPA, branch, and graduation year automatically—never guess if you qualify.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-[#F7F9FC] dark:bg-[#151923]">
              <div className="h-10 w-10 rounded-lg bg-[#EEE8FF] dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold text-sm mb-4">
                03
              </div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Stage-by-Stage Tracking</h3>
              <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Monitor your application status through screening, assessments, and interviews with complete clarity.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-[#F7F9FC] dark:bg-[#151923]">
              <div className="h-10 w-10 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 flex items-center justify-center font-bold text-sm mb-4">
                04
              </div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Interviews & Offers</h3>
              <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Receive scheduled interview invitations and official offer letters with integrated campus placement governance.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Section: For Students (Profile & Resume) ───────────────────────── */}
      <section id="for-students" className="py-20 border-t border-slate-200/80 dark:border-slate-800 bg-[#F7F9FC] dark:bg-[#080A0F]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <span className="text-xs font-semibold text-[#5278D9] uppercase tracking-wider">Candidate Experience</span>
              <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
                A single profile that powers all your applications.
              </h2>
              <p className="mt-4 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                Fill out your details once. Talentra maintains your unified candidate record for all campus drives, internships, and hiring opportunities.
              </p>

              <div className="mt-8 space-y-4">
                <div className="flex items-start gap-3">
                  <div className="h-6 w-6 rounded-md bg-[#EAF0FF] dark:bg-[#5278D9]/20 text-[#5278D9] flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle2 className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-white">College-Verified Education Records</h4>
                    <p className="text-xs text-slate-500 mt-0.5">Maintain verified semester grades, branch, roll number, and transcript attachments.</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="h-6 w-6 rounded-md bg-[#EAF0FF] dark:bg-[#5278D9]/20 text-[#5278D9] flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle2 className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-white">Standardized Resume Generation</h4>
                    <p className="text-xs text-slate-500 mt-0.5">Generate clean, recruiter-ready profile PDFs formatted for campus drives.</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="h-6 w-6 rounded-md bg-[#EAF0FF] dark:bg-[#5278D9]/20 text-[#5278D9] flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle2 className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-white">Structured Skills & Projects</h4>
                    <p className="text-xs text-slate-500 mt-0.5">Showcase real code repositories, technical projects, certifications, and demonstrated strengths.</p>
                  </div>
                </div>
              </div>

              <div className="mt-8">
                <Link href="/register">
                  <Button className="bg-[#5278D9] hover:bg-[#4367C7] text-white text-sm font-medium rounded-lg h-10 px-5 gap-2">
                    <span>Build Your Profile</span>
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              </div>
            </div>

            {/* Visual Column */}
            <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#151923] shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <span className="text-xs font-semibold text-slate-900 dark:text-white">Profile Sections</span>
                <span className="text-[11px] text-[#5278D9] font-medium">10 Standardized Categories</span>
              </div>

              <div className="grid grid-cols-2 gap-2.5 text-xs">
                {[
                  "Personal Information",
                  "Academic Background",
                  "Technical Skills",
                  "Internships & Experience",
                  "Academic Projects",
                  "Certifications",
                  "Resume & Documents",
                  "Government Verification",
                  "Job Preferences",
                  "Privacy & Consent",
                ].map((item, idx) => (
                  <div
                    key={item}
                    className="flex items-center gap-2 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-[#0E121B]"
                  >
                    <span className="text-[10px] font-mono text-slate-400 font-semibold">{String(idx + 1).padStart(2, "0")}</span>
                    <span className="font-medium text-slate-700 dark:text-slate-300 truncate">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Section: Privacy & Verification ─────────────────────────────────── */}
      <section id="verification" className="py-20 border-t border-slate-200/80 dark:border-slate-800 bg-white dark:bg-[#080A0F]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mb-14">
            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
              Security & Compliance
            </span>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
              Privacy and Government Verification
            </h2>
            <p className="mt-3 text-base text-slate-600 dark:text-slate-400">
              Zero raw PII persistence, explicit purpose-bound consent, and cryptographic proof of identity.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-[#F7F9FC] dark:bg-[#151923]">
              <div className="h-10 w-10 rounded-lg bg-[#EAF0FF] dark:bg-[#5278D9]/20 text-[#5278D9] flex items-center justify-center mb-4">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Aadhaar & PAN Validation</h3>
              <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Strict format validation with 4-digit grouped display. Raw document numbers are never persisted or echoed back.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-[#F7F9FC] dark:bg-[#151923]">
              <div className="h-10 w-10 rounded-lg bg-[#E4F5EC] dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-4">
                <FileCheck2 className="h-5 w-5" />
              </div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Document Tokenization</h3>
              <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Documents are cryptographically verified and masked. Authorized parties only see verification status pills.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-[#F7F9FC] dark:bg-[#151923]">
              <div className="h-10 w-10 rounded-lg bg-[#EEE8FF] dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 flex items-center justify-center mb-4">
                <Clock className="h-5 w-5" />
              </div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Explicit Purpose Consent</h3>
              <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Every verification requires logged consent with explicit purpose scoping and time-bounded retention policies.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Final CTA Section ──────────────────────────────────────────────── */}
      <section className="py-16 border-t border-slate-200/80 dark:border-slate-800 bg-[#F7F9FC] dark:bg-[#111420]">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Ready to launch your career journey?
          </h2>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-400 max-w-xl mx-auto">
            Create your verified student profile and discover opportunities matched directly to your academic credentials.
          </p>
          <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link href="/register" className="w-full sm:w-auto">
              <Button size="lg" className="w-full sm:w-auto bg-[#5278D9] hover:bg-[#4367C7] text-white font-medium h-11 px-6 rounded-lg text-sm">
                Create Free Profile
              </Button>
            </Link>
            <Link href="/sign-in" className="w-full sm:w-auto">
              <Button variant="outline" size="lg" className="w-full sm:w-auto border-slate-300 dark:border-slate-700 font-medium h-11 px-6 rounded-lg text-sm bg-white dark:bg-[#151923]">
                Sign In to Account
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* ─── Footer ─────────────────────────────────────────────────────────── */}
      <footer id="about" className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-[#080A0F] py-12 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-8">
            <div className="col-span-2">
              <div className="flex items-center gap-2 mb-3">
                <div className="h-7 w-7 rounded-lg bg-[#5278D9] flex items-center justify-center text-white">
                  <GraduationCap className="h-4 w-4" />
                </div>
                <span className="font-bold text-sm text-slate-900 dark:text-white">Talentra</span>
              </div>
              <p className="text-xs text-slate-500 max-w-xs leading-relaxed">
                Campus placement, verified student portfolios, and enterprise recruitment platform.
              </p>
              <div className="mt-3 text-[11px] text-slate-400">
                Connected to FastAPI & PostgreSQL · 9 Persona Architecture
              </div>
            </div>

            <div>
              <div className="font-semibold text-slate-900 dark:text-white mb-3">Platform</div>
              <ul className="space-y-2">
                <li><Link href="/jobs" className="hover:text-slate-900 dark:hover:text-white transition-colors">Opportunities</Link></li>
                <li><a href="#how-it-works" className="hover:text-slate-900 dark:hover:text-white transition-colors">How It Works</a></li>
                <li><a href="#for-students" className="hover:text-slate-900 dark:hover:text-white transition-colors">For Students</a></li>
                <li><Link href="/verification" className="hover:text-slate-900 dark:hover:text-white transition-colors">Verification</Link></li>
              </ul>
            </div>

            <div>
              <div className="font-semibold text-slate-900 dark:text-white mb-3">Candidate</div>
              <ul className="space-y-2">
                <li><Link href="/portal/candidate" className="hover:text-slate-900 dark:hover:text-white transition-colors">Candidate Workspace</Link></li>
                <li><Link href="/candidates/me" className="hover:text-slate-900 dark:hover:text-white transition-colors">My Profile</Link></li>
                <li><Link href="/applications" className="hover:text-slate-900 dark:hover:text-white transition-colors">My Applications</Link></li>
                <li><Link href="/notifications" className="hover:text-slate-900 dark:hover:text-white transition-colors">Notifications</Link></li>
              </ul>
            </div>

            <div>
              <div className="font-semibold text-slate-900 dark:text-white mb-3">Security & Portals</div>
              <ul className="space-y-2">
                <li><Link href="/portal/admin" className="hover:text-slate-900 dark:hover:text-white transition-colors">Platform Admin</Link></li>
                <li><Link href="/portal/employer" className="hover:text-slate-900 dark:hover:text-white transition-colors">Employer Portal</Link></li>
                <li><Link href="/portal/placement-officer" className="hover:text-slate-900 dark:hover:text-white transition-colors">Placement Officer</Link></li>
                <li><Link href="/support" className="hover:text-slate-900 dark:hover:text-white transition-colors">Help & Support</Link></li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
            <div>© {new Date().getFullYear()} Talentra Campus Placement Platform. All rights reserved.</div>
            <div className="flex items-center gap-6">
              <span>Privacy Scoped</span>
              <span>ISO 27001 Aligned</span>
              <span>Zero Raw PII Storage</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
