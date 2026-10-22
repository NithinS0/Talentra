import React from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "destructive";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      children,
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled,
      ...props
    },
    ref
  ) => {
    const base =
      "inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none select-none";

    const variants = {
      primary:
        "bg-[#5278D9] text-white hover:bg-[#4268C8] active:bg-[#3A5BB8] focus-visible:ring-[#5278D9] shadow-sm shadow-blue-600/20",
      secondary:
        "bg-slate-100 text-slate-900 hover:bg-slate-200 dark:bg-[#1E2335] dark:text-slate-100 dark:hover:bg-[#252A40] focus-visible:ring-slate-500",
      outline:
        "border border-slate-300 dark:border-white/[0.12] bg-transparent hover:bg-slate-50 dark:hover:bg-white/[0.04] text-slate-800 dark:text-slate-200 focus-visible:ring-[#5278D9]",
      ghost:
        "bg-transparent hover:bg-slate-100 dark:hover:bg-white/[0.06] text-slate-700 dark:text-slate-300 focus-visible:ring-slate-500",
      destructive:
        "bg-rose-600 text-white hover:bg-rose-700 active:bg-rose-800 focus-visible:ring-rose-500 shadow-sm",
    };

    const sizes = {
      sm:   "text-xs px-3 py-1.5 h-8 gap-1.5",
      md:   "text-sm px-4 py-2 h-10 gap-2",
      lg:   "text-base px-6 py-3 h-12 gap-2",
      icon: "h-10 w-10 p-0",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(base, variants[variant], sizes[size], className)}
        {...props}
      >
        {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
