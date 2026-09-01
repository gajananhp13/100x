"use client";

import { useId } from "react";

/** 10-axis radar (spider) chart, hand-rolled SVG. */
export function RadarChart({
  items,
  size = 320,
  labelSize = 10,
}: {
  items: Array<[string, number]>;
  size?: number;
  labelSize?: number;
}) {
  const uid = useId().replace(/:/g, "");
  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2 - labelSize * 2.2;
  const n = items.length;
  if (n < 3) return null;

  const pt = (i: number, radius: number): [number, number] => {
    const ang = (2 * Math.PI * i) / n - Math.PI / 2;
    return [cx + radius * Math.cos(ang), cy + radius * Math.sin(ang)];
  };

  const rings = [0.25, 0.5, 0.75, 1];
  const poly = items.map(([, v], i) => pt(i, r * Math.min(1, Math.max(0, v) / 100)));
  const labelPos = items.map(([label], i) => {
    const [x, y] = pt(i, r + labelSize * 1.6);
    return { label, x, y };
  });

  return (
    <svg width={size} height={size} role="img" aria-label="Score radar chart">
      <defs>
        <linearGradient id={`${uid}-fill`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#2563eb" stopOpacity="0.28" />
          <stop offset="100%" stopColor="#2563eb" stopOpacity="0.08" />
        </linearGradient>
      </defs>

      {rings.map((f) => (
        <polygon
          key={f}
          points={items.map((_, i) => pt(i, r * f).join(",")).join(" ")}
          fill="none"
          stroke="#e1e4eb"
          strokeWidth={f === 1 ? 1.1 : 0.7}
        />
      ))}
      {items.map((_, i) => {
        const [x, y] = pt(i, r);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#e1e4eb" strokeWidth={0.7} />;
      })}

      <polygon points={poly.map((p) => p.join(",")).join(" ")} fill={`url(#${uid}-fill)`} stroke="#1d4ed8" strokeWidth={2} strokeLinejoin="round" />
      {poly.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={3.2} fill="#2563eb" stroke="#fff" strokeWidth={1.2} />
      ))}

      {labelPos.map(({ label, x, y }, i) => (
        <text
          key={i}
          x={x}
          y={y}
          textAnchor={x < cx - 4 ? "end" : x > cx + 4 ? "start" : "middle"}
          dominantBaseline="middle"
          fontSize={labelSize}
          fill="#475569"
          fontWeight={500}
        >
          {label}
        </text>
      ))}
    </svg>
  );
}
