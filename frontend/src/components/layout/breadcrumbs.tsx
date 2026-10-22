"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Home } from "lucide-react";

export function Breadcrumbs() {
  const pathname = usePathname();
  if (pathname === "/" || pathname === "/dashboard") return null;

  const segments = pathname.split("/").filter(Boolean);

  return (
    <nav aria-label="Breadcrumb" className="flex items-center space-x-2 text-xs text-slate-500 dark:text-slate-400 py-2">
      <Link href="/dashboard" className="flex items-center hover:text-indigo-600 transition-colors">
        <Home className="h-3.5 w-3.5" />
      </Link>
      {segments.map((segment, index) => {
        const href = `/${segments.slice(0, index + 1).join("/")}`;
        const isLast = index === segments.length - 1;
        const formattedTitle = segment
          .replace(/-/g, " ")
          .replace(/\b\w/g, (c) => c.toUpperCase());

        return (
          <React.Fragment key={href}>
            <ChevronRight className="h-3 w-3 text-slate-400" />
            {isLast ? (
              <span className="font-semibold text-slate-800 dark:text-slate-200">{formattedTitle}</span>
            ) : (
              <Link href={href} className="hover:text-indigo-600 transition-colors">
                {formattedTitle}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
