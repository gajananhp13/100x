"use client";

import React, { type ReactNode, type ButtonHTMLAttributes, type InputHTMLAttributes } from "react";
import { Check, X, AlertTriangle, ChevronDown, Loader2, ChevronRight, FileText, Search, Inbox, Users } from "lucide-react";
import type { VerificationStatus } from "@/lib/types";
import { STATUS_LABELS } from "@/lib/types";
import { cn } from "@/lib/cn";

/* ─────────────────────────────────────────────────────────────────── */
/* Button                                                              */
/* ─────────────────────────────────────────────────────────────────── */
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  className,
  type = "button",
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center gap-1.5 font-medium rounded-lg transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#4f46e5]/40 disabled:opacity-50 disabled:pointer-events-none select-none";
  const sizes = {
    sm: "px-3 h-8 text-sm",
    md: "px-4 h-9 text-sm",
    lg: "px-5 h-10 text-sm",
  };
  const variants = {
    primary:
      "bg-[#4f46e5] text-white shadow-sm hover:bg-[#4338ca] hover:shadow-md active:scale-[0.98]",
    secondary:
      "bg-white text-[#09090b] border border-[#e4e4e7] hover:border-[#d4d4d8] hover:shadow-sm active:scale-[0.98]",
    ghost:
      "text-[#52525b] hover:bg-[#f4f4f5] hover:text-[#09090b] active:scale-[0.98]",
    danger:
      "bg-[#dc2626] text-white shadow-sm hover:bg-[#b91c1c] hover:shadow-md active:scale-[0.98]",
  };
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={cn(base, sizes[size], variants[variant], className)}
      {...props}
    >
      {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
      {children}
    </button>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Card                                                                */
/* ─────────────────────────────────────────────────────────────────── */
export interface CardProps {
  children: ReactNode;
  className?: string;
  variant?: "default" | "bordered" | "elevated";
  padded?: boolean;
}

export function Card({ children, className, variant = "default", padded = true }: CardProps) {
  const variants = {
    default: "bg-white border border-[#e4e4e7]",
    bordered: "bg-white border border-[#e4e4e7]",
    elevated: "bg-white border border-[#e4e4e7] shadow-sm",
  };
  return (
    <div className={cn("rounded-xl", variants[variant], padded && "p-5", className)}>
      {children}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Status Indicator                                                    */
/* ─────────────────────────────────────────────────────────────────── */
type StatusVariant = "verified" | "partial" | "none";

const STATUS_CONF: Record<
  StatusVariant,
  { bg: string; text: string; dot: string; icon: typeof Check | typeof AlertTriangle | typeof X }
> = {
  verified: { bg: "bg-[#f0fdf4]", text: "text-[#16a34a]", dot: "bg-[#16a34a]", icon: Check },
  partial:  { bg: "bg-[#fffbeb]", text: "text-[#d97706]", dot: "bg-[#d97706]", icon: AlertTriangle },
  none:     { bg: "bg-[#f4f4f5]", text: "text-[#a1a1aa]", dot: "bg-[#a1a1aa]", icon: X },
};

export function StatusIndicator({
  status,
  label,
  className,
}: {
  status: VerificationStatus;
  label?: boolean;
  className?: string;
}) {
  const map: Record<VerificationStatus, StatusVariant> = {
    verified: "verified",
    strong_evidence: "verified",
    partial_evidence: "partial",
    limited_evidence: "partial",
    no_public_evidence: "none",
  };
  const variant = map[status];
  const { bg, text, dot, icon: Icon } = STATUS_CONF[variant];

  if (label) {
    return (
      <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-semibold", bg, text, className)}>
        <Icon className="h-3 w-3 shrink-0" strokeWidth={2.5} />
        {STATUS_LABELS[status]}
      </span>
    );
  }
  return (
    <span className={cn("inline-flex items-center gap-1 text-sm font-medium", text, className)}>
      <Icon className="h-3.5 w-3.5 shrink-0" strokeWidth={2.5} />
    </span>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Progress Bar                                                        */
/* ─────────────────────────────────────────────────────────────────── */
export function ProgressBar({
  value,
  className,
  height = 5,
  color,
}: {
  value: number;
  className?: string;
  height?: number;
  color?: string;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  const barColor = color ?? (clamped >= 70 ? "#16a34a" : clamped >= 40 ? "#d97706" : "#a1a1aa");
  return (
    <div
      className={cn("w-full overflow-hidden rounded-full bg-[#f0f0f2]", className)}
      style={{ height }}
    >
      <div
        className="h-full rounded-full transition-all duration-500 ease-out"
        style={{ width: `${clamped}%`, background: barColor }}
      />
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Score Ring                                                          */
/* ─────────────────────────────────────────────────────────────────── */
export function ScoreRing({
  value,
  size = 96,
  stroke = 7,
  label,
}: {
  value: number;
  size?: number;
  stroke?: number;
  label?: string;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(100, value));
  const pct = clamped / 100;

  const color =
    clamped >= 70 ? "#16a34a" :
    clamped >= 40 ? "#d97706" :
                   "#a1a1aa";
  const bg = clamped >= 70 ? "#dcfce7" : clamped >= 40 ? "#fef9c3" : "#f0f0f2";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={bg} strokeWidth={stroke} />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={color} strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c - pct * c}
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-xl font-bold leading-none" style={{ color }}>{Math.round(clamped)}</span>
        {label && <span className="mt-0.5 text-[9px] font-semibold uppercase tracking-wide text-[#a1a1aa]">{label}</span>}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Stat Card                                                           */
/* ─────────────────────────────────────────────────────────────────── */
export function StatCard({
  label,
  value,
  sub,
  trend,
}: {
  label: string;
  value: ReactNode;
  sub?: string;
  trend?: { value: number; label: string };
}) {
  return (
    <div className="rounded-xl border border-[#e4e4e7] bg-white p-4">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-[#a1a1aa]">{label}</div>
      <div className="mt-1.5 text-2xl font-bold tracking-tight text-[#09090b]">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-[#71717a]">{sub}</div>}
      {trend && (
        <div className="mt-2 flex items-center gap-1 text-xs">
          <span className={cn("font-semibold", trend.value >= 0 ? "text-[#16a34a]" : "text-[#dc2626]")}>
            {trend.value >= 0 ? "+" : ""}{trend.value}%
          </span>
          <span className="text-[#a1a1aa]">{trend.label}</span>
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Chip / Tag                                                          */
/* ─────────────────────────────────────────────────────────────────── */
export function Chip({
  children,
  className,
  removable,
  onRemove,
  icon,
  tone = "default",
}: {
  children: ReactNode;
  className?: string;
  removable?: boolean;
  onRemove?: () => void;
  icon?: ReactNode;
  tone?: "default" | "brand" | "success" | "warning" | "error";
}) {
  const tones = {
    default: "border-[#e4e4e7] bg-[#f4f4f5] text-[#52525b]",
    brand:   "border-[#c7d2fe] bg-[#eef2ff] text-[#4f46e5]",
    success: "border-[#bbf7d0] bg-[#f0fdf4] text-[#16a34a]",
    warning: "border-[#fde68a] bg-[#fffbeb] text-[#d97706]",
    error:   "border-[#fecaca] bg-[#fef2f2] text-[#dc2626]",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium",
        tones[tone],
        className,
      )}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
      {removable && (
        <button
          onClick={onRemove}
          className="ml-0.5 rounded p-0.5 opacity-60 transition-opacity hover:opacity-100"
          aria-label="Remove"
        >
          <X className="h-3 w-3" strokeWidth={2.5} />
        </button>
      )}
    </span>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Section Header                                                      */
/* ─────────────────────────────────────────────────────────────────── */
export function SectionHeader({
  index,
  title,
  subtitle,
}: {
  index?: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="mb-5 flex items-start gap-3.5">
      {index && (
        <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[#eef2ff] text-xs font-bold text-[#4f46e5]">
          {index}
        </span>
      )}
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-[#09090b]">{title}</h2>
        {subtitle && <p className="mt-0.5 max-w-2xl text-sm leading-relaxed text-[#71717a]">{subtitle}</p>}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Spinner                                                             */
/* ─────────────────────────────────────────────────────────────────── */
export function Spinner({ size = 18, className }: { size?: number; className?: string }) {
  return (
    <Loader2
      className={cn("animate-spin text-[#4f46e5]", className)}
      style={{ width: size, height: size }}
      aria-label="Loading"
    />
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Input                                                               */
/* ─────────────────────────────────────────────────────────────────── */
export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export function Input({ label, error, helperText, className, id, ...props }: InputProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="mb-1.5 block text-xs font-semibold text-[#09090b]">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={cn(
          "h-8 w-full rounded-lg border bg-white px-3 text-sm text-[#09090b] placeholder:text-[#a1a1aa] transition-all",
          "focus:outline-none focus:ring-2 focus:ring-[#4f46e5]/25 focus:border-[#4f46e5]",
          error
            ? "border-[#dc2626] focus:border-[#dc2626] focus:ring-[#dc2626]/20"
            : "border-[#e4e4e7] hover:border-[#d4d4d8]",
          className,
        )}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} className="mt-1 text-xs text-[#dc2626]" role="alert">
          {error}
        </p>
      )}
      {helperText && !error && (
        <p id={`${inputId}-helper`} className="mt-1 text-xs text-[#a1a1aa]">
          {helperText}
        </p>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Textarea                                                            */
/* ─────────────────────────────────────────────────────────────────── */
export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export function Textarea({ label, error, helperText, className, id, ...props }: TextareaProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="mb-1.5 block text-xs font-semibold text-[#09090b]">
          {label}
        </label>
      )}
      <textarea
        id={inputId}
        className={cn(
          "w-full resize-y rounded-lg border bg-white px-3 py-2 text-sm text-[#09090b] placeholder:text-[#a1a1aa] transition-all min-h-[100px]",
          "focus:outline-none focus:ring-2 focus:ring-[#4f46e5]/25 focus:border-[#4f46e5]",
          error
            ? "border-[#dc2626] focus:border-[#dc2626] focus:ring-[#dc2626]/20"
            : "border-[#e4e4e7] hover:border-[#d4d4d8]",
          className,
        )}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} className="mt-1 text-xs text-[#dc2626]" role="alert">
          {error}
        </p>
      )}
      {helperText && !error && (
        <p id={`${inputId}-helper`} className="mt-1 text-xs text-[#a1a1aa]">
          {helperText}
        </p>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Label / Badge                                                       */
/* ─────────────────────────────────────────────────────────────────── */
export function Label({
  children,
  className,
  tone = "default",
}: {
  children: ReactNode;
  className?: string;
  tone?: "default" | "success" | "warning" | "brand" | "error";
}) {
  const tones = {
    default: "bg-[#f4f4f5] text-[#52525b] border border-[#e4e4e7]",
    success: "bg-[#f0fdf4] text-[#16a34a] border border-[#bbf7d0]",
    warning: "bg-[#fffbeb] text-[#d97706] border border-[#fde68a]",
    brand:   "bg-[#eef2ff] text-[#4f46e5] border border-[#c7d2fe]",
    error:   "bg-[#fef2f2] text-[#dc2626] border border-[#fecaca]",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Dropdown Menu                                                       */
/* ─────────────────────────────────────────────────────────────────── */
export function DropdownMenu({
  trigger,
  items,
  align = "end",
}: {
  trigger: ReactNode;
  items: Array<{ label: string; onClick: () => void; danger?: boolean; icon?: ReactNode }>;
  align?: "start" | "end";
}) {
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <div onClick={() => setOpen((o) => !o)}>{trigger}</div>
      {open && (
        <div
          className={cn(
            "absolute z-50 mt-1.5 min-w-[160px] rounded-xl border border-[#e4e4e7] bg-white p-1 shadow-lg",
            align === "end" ? "right-0" : "left-0",
          )}
        >
          {items.map((item, i) => (
            <button
              key={i}
              onClick={() => { item.onClick(); setOpen(false); }}
              className={cn(
                "flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-colors",
                item.danger
                  ? "text-[#dc2626] hover:bg-[#fef2f2]"
                  : "text-[#09090b] hover:bg-[#f4f4f5]",
              )}
            >
              {item.icon && <span className="shrink-0">{item.icon}</span>}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Tabs                                                                */
/* ─────────────────────────────────────────────────────────────────── */
export function Tabs({
  tabs,
  defaultValue,
  onChange,
  className,
}: {
  tabs: Array<{ value: string; label: string }>;
  defaultValue: string;
  onChange?: (value: string) => void;
  className?: string;
}) {
  const [active, setActive] = React.useState(defaultValue);
  return (
    <div className={className}>
      <div className="flex gap-0.5 rounded-lg bg-[#f4f4f5] p-1 mb-4">
        {tabs.map((tab) => (
          <button
            key={tab.value}
            onClick={() => { setActive(tab.value); onChange?.(tab.value); }}
            className={cn(
              "flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-all",
              active === tab.value
                ? "bg-white text-[#09090b] shadow-sm"
                : "text-[#71717a] hover:text-[#09090b]",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Breadcrumb                                                          */
/* ─────────────────────────────────────────────────────────────────── */
export function Breadcrumb({ items }: { items: Array<{ label: string; href?: string }> }) {
  return (
    <nav className="flex flex-wrap items-center gap-1 text-sm text-[#71717a]" aria-label="Breadcrumb">
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && <ChevronRight className="h-3.5 w-3.5 text-[#a1a1aa]" />}
          {item.href ? (
            <a href={item.href} className="transition-colors hover:text-[#09090b]">{item.label}</a>
          ) : (
            <span className="font-medium text-[#09090b]">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Empty State                                                         */
/* ─────────────────────────────────────────────────────────────────── */
const EMPTY_ICONS: Record<string, typeof FileText> = {
  file: FileText, search: Search, inbox: Inbox, users: Users,
};

export function EmptyState({
  title,
  description,
  action,
  illustration = "inbox",
}: {
  title: string;
  description: string;
  action?: { label: string; onClick: () => void };
  illustration?: keyof typeof EMPTY_ICONS;
}) {
  const Icon = EMPTY_ICONS[illustration];
  return (
    <div className="flex flex-col items-center justify-center py-14 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#f4f4f5] text-[#a1a1aa]">
        <Icon className="h-7 w-7" />
      </div>
      <h3 className="mt-4 text-base font-semibold text-[#09090b]">{title}</h3>
      <p className="mt-1.5 max-w-sm text-sm text-[#71717a]">{description}</p>
      {action && (
        <Button className="mt-5" onClick={action.onClick}>{action.label}</Button>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Tooltip (CSS-based, hover-only)                                     */
/* ─────────────────────────────────────────────────────────────────── */
export function Tooltip({
  content,
  children,
  position = "top",
}: {
  content: string;
  children: ReactNode;
  position?: "top" | "bottom" | "left" | "right";
}) {
  return (
    <div className="group relative inline-block">
      {children}
      <div
        className={cn(
          "pointer-events-none absolute z-50 whitespace-nowrap rounded-md bg-[#09090b] px-2.5 py-1 text-[11px] font-medium text-white opacity-0 shadow-sm transition-opacity duration-150 group-hover:opacity-100",
          position === "top"    && "bottom-full left-1/2 mb-1.5 -translate-x-1/2",
          position === "bottom" && "top-full left-1/2 mt-1.5 -translate-x-1/2",
          position === "left"   && "right-full top-1/2 mr-1.5 -translate-y-1/2",
          position === "right"  && "left-full top-1/2 ml-1.5 -translate-y-1/2",
        )}
        role="tooltip"
      >
        {content}
      </div>
    </div>
  );
}
