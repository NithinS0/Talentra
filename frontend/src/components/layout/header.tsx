"use client";

import React, { useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { useAuth, DEMO_PERSONAS } from "@/lib/auth/context";
import { RoleCode } from "@/types/auth";
import { ThemeToggle } from "./theme-toggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  GraduationCap,
  LogOut,
  ChevronDown,
  ShieldCheck,
} from "lucide-react";

const emptySubscribe = () => () => {};

export function Header() {
  const { user, activeRole, activeActorId, isAuthenticated, logout, switchRole } = useAuth();
  const [roleMenuOpen, setRoleMenuOpen] = useState(false);
  const mounted = useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false
  );

  const showAuthenticatedState = mounted && isAuthenticated;

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-[#080A0F]/95 backdrop-blur-md">
      <div className="flex h-14 items-center justify-between px-4 sm:px-6">
        {/* Brand & Platform Identity */}
        <div className="flex items-center space-x-3">
          <Link href="/dashboard" className="flex items-center space-x-2.5 group">
            <div className="h-8 w-8 rounded-lg bg-[#5278D9] flex items-center justify-center text-white shadow-xs">
              <GraduationCap className="h-4.5 w-4.5" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-bold tracking-tight text-slate-900 dark:text-slate-100 leading-none">
                Talentra
              </span>
              <span className="text-[10px] text-slate-500 font-medium">Placement Platform</span>
            </div>
          </Link>

          {/* Environment & Actor ID Badge */}
          {showAuthenticatedState && (
            <div className="hidden md:flex items-center space-x-2 pl-4 border-l border-slate-200 dark:border-slate-800">
              <Badge variant="purple" className="font-mono font-semibold px-2 py-0.5 text-[11px]">
                {activeActorId}
              </Badge>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                Talentra Campus
              </span>
            </div>
          )}
        </div>

        {/* Right Nav: Persona Switcher, Theme, Profile */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          {showAuthenticatedState ? (
            <>
              {/* Role Switcher or Role Badge */}
              {user?.roles && user.roles.length > 1 ? (
                <div className="relative">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setRoleMenuOpen(!roleMenuOpen)}
                    className="flex items-center space-x-1.5 text-xs font-medium border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-300 rounded-lg h-8 px-2.5"
                  >
                    <ShieldCheck className="h-3.5 w-3.5 text-[#5278D9]" />
                    <span>{activeRole.replace(/_/g, " ")}</span>
                    <ChevronDown className="h-3 w-3 opacity-60" />
                  </Button>

                  {roleMenuOpen && (
                    <div
                      className="absolute right-0 mt-2 w-72 rounded-xl bg-white dark:bg-[#151923] shadow-xl border border-slate-200 dark:border-slate-800 p-2 z-50 text-xs"
                      onClick={() => setRoleMenuOpen(false)}
                    >
                      <div className="px-2 py-1.5 font-semibold text-slate-400 dark:text-slate-500 uppercase text-[10px] tracking-wider">
                        Switch Authorized Role
                      </div>
                      <div className="max-h-64 overflow-y-auto space-y-1">
                        {DEMO_PERSONAS.filter((p) =>
                          user.roles.includes(p.roleCode) || user.roles.includes("SUPER_ADMIN")
                        ).map((persona) => (
                          <button
                            key={persona.roleCode}
                            onClick={() => switchRole(persona.roleCode as RoleCode)}
                            className={`w-full text-left px-2.5 py-2 rounded-lg flex items-center justify-between transition-colors ${
                              activeRole === persona.roleCode
                                ? "bg-[#5278D9]/10 text-[#5278D9] font-medium"
                                : "hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
                            }`}
                          >
                            <div>
                              <div className="font-medium text-xs">{persona.name}</div>
                              <div className="text-[10px] text-slate-400">{persona.roleCode}</div>
                            </div>
                            <Badge variant="outline" className="font-mono text-[10px]">
                              {persona.actorId}
                            </Badge>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center space-x-1.5 text-xs font-medium border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-300 rounded-lg h-8 px-2.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-[#5278D9]" />
                  <span>{activeRole.replace(/_/g, " ")}</span>
                </div>
              )}

              {/* Theme Toggle */}
              <ThemeToggle />

              {/* User Profile & Sign Out */}
              <div className="flex items-center space-x-2 pl-2 border-l border-slate-200 dark:border-slate-800">
                <div className="hidden lg:flex flex-col text-right">
                  <span className="text-xs font-medium text-slate-800 dark:text-slate-200">
                    {user?.display_name || "Demo User"}
                  </span>
                  <span className="text-[10px] text-slate-400">{user?.email_address}</span>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={logout}
                  title="Sign out"
                  className="text-slate-500 hover:text-red-600 h-8 w-8"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </>
          ) : (
            <>
              <ThemeToggle />
              <Link href="/sign-in">
                <Button variant="outline" size="sm" className="h-8 text-xs">
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button variant="primary" size="sm" className="h-8 text-xs bg-[#5278D9] hover:bg-[#4367C7]">
                  Get Started
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
