import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "destructive" | "outline" | "purple";
}

export function Badge({ className, variant = "default", children, ...props }: BadgeProps) {
  const variants = {
    default:
      "bg-slate-100 text-slate-700 dark:bg-[#1E2335] dark:text-slate-300 border-transparent",
    success:
      "bg-[#E4F5EC] text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400 border-emerald-200/50 dark:border-emerald-800/40",
    warning:
      "bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400 border-amber-200/50 dark:border-amber-800/40",
    destructive:
      "bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-400 border-rose-200/50 dark:border-rose-800/40",
    outline:
      "border-slate-300 dark:border-white/[0.12] text-slate-700 dark:text-slate-300 bg-transparent",
    purple:
      "bg-[#EEE8FF] text-[#7C5CBF] dark:bg-violet-950/50 dark:text-violet-400 border-violet-200/50 dark:border-violet-800/40",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors leading-none",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
