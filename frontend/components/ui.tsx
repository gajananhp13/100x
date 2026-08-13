import type { ReactNode } from "react";
import type { VerificationStatus } from "@/lib/types";
import { STATUS_LABELS } from "@/lib/types";

export function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

const statusClasses: Record<VerificationStatus, string> = {
  verified: "bg-emerald-soft text-emerald",
  strong_evidence: "bg-teal-soft text-teal",
  partial_evidence: "bg-amber-soft text-amber",
  limited_evidence: "bg-orange-soft text-orange",
  no_public_evidence: "bg-slate-soft text-slate",
};

export function StatusBadge({ status, className }: { status: VerificationStatus; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold whitespace-nowrap",
        statusClasses[status],
        className,
      )}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}

export function Chip({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-line bg-surface px-2.5 py-0.5 text-xs text-ink-2",
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Card({
  children,
  className,
  padded = true,
}: {
  children: ReactNode;
  className?: string;
  padded?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border border-line bg-surface shadow-[0_1px_2px_rgba(16,24,40,0.04)]",
        padded && "p-5",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function Button({
  children,
  onClick,
  variant = "primary",
  size = "md",
  disabled,
  className,
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "ghost" | "outline" | "danger";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  className?: string;
  type?: "button" | "submit";
}) {
  const bases =
    "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 disabled:opacity-50 disabled:pointer-events-none";
  const sizes = { sm: "px-3 py-1.5 text-xs", md: "px-4 py-2 text-sm", lg: "px-6 py-3 text-sm" };
  const variants = {
    primary: "bg-accent text-white hover:bg-accent-strong",
    ghost: "text-ink-2 hover:bg-slate-soft",
    outline: "border border-line-strong bg-surface text-ink hover:border-ink/30",
    danger: "bg-rose text-white hover:bg-rose/90",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={cn(bases, sizes[size], variants[variant], className)}
    >
      {children}
    </button>
  );
}

export function ProgressBar({
  value,
  className,
  tone = "accent",
}: {
  value: number;
  className?: string;
  tone?: "accent" | "emerald" | "amber" | "rose" | "slate";
}) {
  const tones = {
    accent: "bg-accent",
    emerald: "bg-emerald",
    amber: "bg-amber",
    rose: "bg-rose",
    slate: "bg-slate",
  };
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className={cn("h-2 w-full overflow-hidden rounded-full bg-line", className)}>
      <div
        className={cn("h-full rounded-full transition-all duration-700", tones[tone])}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}

export function ScoreRing({
  value,
  size = 96,
  stroke = 7,
  label,
  tone = "emerald",
}: {
  value: number;
  size?: number;
  stroke?: number;
  label?: string;
  tone?: "emerald" | "accent" | "amber" | "slate";
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(100, value));
  const colors = {
    emerald: { ring: "#0ea371", bg: "#d3efe4" },
    accent: { ring: "#5b5bd6", bg: "#dedeef" },
    amber: { ring: "#d97706", bg: "#f0e0bd" },
    slate: { ring: "#8a94a6", bg: "#e3e6ec" },
  };
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={colors[tone].bg} strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={colors[tone].ring}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c - (clamped / 100) * c}
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold" style={{ color: colors[tone].ring }}>
          {Math.round(clamped)}
        </span>
        {label && <span className="text-[10px] font-medium text-muted">{label}</span>}
      </div>
    </div>
  );
}

export function Stat({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: ReactNode;
  sub?: string;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border border-line bg-surface p-3">
      <div className="text-[11px] font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className={cn("mt-0.5 text-lg font-semibold", accent)}>{value}</div>
      {sub && <div className="text-xs text-muted">{sub}</div>}
    </div>
  );
}

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
    <div className="mb-4 flex items-start gap-3">
      {index && (
        <span className="mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent-soft text-sm font-semibold text-accent">
          {index}
        </span>
      )}
      <div>
        <h2 className="text-lg font-semibold text-ink">{title}</h2>
        {subtitle && <p className="mt-0.5 max-w-2xl text-sm text-muted">{subtitle}</p>}
      </div>
    </div>
  );
}

export function Spinner({ size = 18, className }: { size?: number; className?: string }) {
  return (
    <span
      className={cn(
        "inline-block animate-spin rounded-full border-2 border-current border-r-transparent align-middle",
        className,
      )}
      style={{ width: size, height: size }}
    />
  );
}