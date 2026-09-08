export function scoreColor(score: number): string {
  if (score >= 80) return "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200";
  if (score >= 60) return "bg-lime-50 text-lime-700 ring-1 ring-lime-200";
  if (score >= 40) return "bg-amber-50 text-amber-700 ring-1 ring-amber-200";
  return "bg-red-50 text-red-700 ring-1 ring-red-200";
}

export function scoreRingColor(score: number): string {
  if (score >= 80) return "#10b981";
  if (score >= 60) return "#84cc16";
  if (score >= 40) return "#f59e0b";
  return "#ef4444";
}

export function ScoreBadge({ score, size = "md" }: { score: number; size?: "sm" | "md" | "lg" }) {
  const pad = size === "sm" ? "px-2 py-0.5 text-[11px]" : size === "lg" ? "px-3 py-1.5 text-sm" : "px-2.5 py-1 text-xs";
  return (
    <span
      className={`inline-flex items-center rounded-lg font-bold ${pad} ${scoreColor(score)}`}
      title={`Score: ${score}/100`}
    >
      {Math.round(score)}
      <span className="ml-0.5 font-medium opacity-70">/100</span>
    </span>
  );
}

export function ScoreRing({ score, size = 64 }: { score: number; size?: number }) {
  const r = size / 2 - 5;
  const circ = 2 * Math.PI * r;
  const filled = (Math.min(100, Math.max(0, score)) / 100) * circ;
  const color = scoreRingColor(score);
  return (
    <div className="relative inline-grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth="6"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circ}`}
        />
      </svg>
      <div className="absolute text-sm font-bold text-ink-900">{Math.round(score)}</div>
    </div>
  );
}