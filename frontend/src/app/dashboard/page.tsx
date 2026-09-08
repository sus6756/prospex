"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  Crosshair,
  Flame,
  Gauge,
  Radar,
  Sparkles,
  Target,
  Users,
} from "lucide-react";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import type { LeadStats, ICP } from "@/types";
import { Skeleton, StatCardSkeleton } from "@/components/ui/Skeleton";

const STATUS_COLORS: Record<string, string> = {
  new: "#6366f1",
  contacted: "#0ea5e9",
  qualified: "#10b981",
  unqualified: "#f43f5e",
};

const BUCKET_COLORS = ["#ef4444", "#f59e0b", "#facc15", "#84cc16", "#10b981"];

export default function DashboardPage() {
  const [stats, setStats] = useState<LeadStats | null>(null);
  const [icps, setIcps] = useState<ICP[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [s, i] = await Promise.all([api.leadStats(), api.listIcps()]);
        setStats(s);
        setIcps(i);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <Skeleton className="h-8 w-40" />
          <Skeleton className="mt-2 h-4 w-72" />
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
        <div className="card">
          <Skeleton className="h-5 w-48" />
          <div className="mt-6 h-56" />
        </div>
      </div>
    );
  }

  const total = stats?.total ?? 0;
  const statusData = Object.entries(stats?.status_counts ?? {}).map(([name, value]) => ({
    name,
    value,
  }));
  const distData = (stats?.score_distribution ?? []).map((b) => ({ ...b }));
  const maxDist = Math.max(1, ...distData.map((d) => d.count));
  const maxSource = Math.max(1, ...Object.values(stats?.source_counts ?? {}));

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight text-ink-900">
            Overview
          </h1>
          <p className="mt-1 text-sm text-ink-500">Your lead pipeline at a glance.</p>
        </div>
        <Link href="/dashboard/icp" className="btn-primary">
          <Sparkles className="h-4 w-4" />
          New discovery
        </Link>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Total leads"
          value={String(total)}
          icon={Users}
          tint="from-brand-500 to-violet-500"
        />
        <MetricCard
          label="Average score"
          value={stats?.avg_score != null ? String(stats.avg_score) : "—"}
          icon={Gauge}
          tint="from-emerald-500 to-teal-500"
        />
        <MetricCard
          label="Top lead score"
          value={stats?.top_score != null ? String(stats.top_score) : "—"}
          icon={Flame}
          tint="from-amber-500 to-orange-500"
        />
        <MetricCard
          label="Active ICPs"
          value={String(stats?.active_icps ?? icps.length)}
          icon={Crosshair}
          tint="from-sky-500 to-cyan-500"
        />
      </div>

      {total === 0 ? (
        <div className="card relative overflow-hidden py-16 text-center">
          <div className="pointer-events-none absolute -top-24 left-1/2 h-48 w-96 -translate-x-1/2 rounded-full bg-brand-100/60 blur-3xl" />
          <div className="relative mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-violet-600 text-white shadow-lg shadow-brand-500/30">
            <Target className="h-7 w-7" />
          </div>
          <h2 className="mt-5 text-lg font-bold text-ink-900">Build your first lead list</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-ink-500">
            Define your Ideal Customer Profile in plain English, and Prospex will
            discover, enrich, and score matching leads for you.
          </p>
          <Link href="/dashboard/icp" className="btn-primary mt-6">
            Create an ICP
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      ) : (
        <div className="grid gap-5 lg:grid-cols-3">
          {/* Qualification mix donut */}
          <div className="card lg:col-span-1">
            <div className="mb-2 flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-ink-400" />
              <h2 className="font-bold text-ink-900">Qualification mix</h2>
            </div>
            {statusData.length ? (
              <>
                <div className="h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={statusData}
                        dataKey="value"
                        nameKey="name"
                        innerRadius={48}
                        outerRadius={72}
                        paddingAngle={3}
                        strokeWidth={0}
                      >
                        {statusData.map((entry) => (
                          <Cell key={entry.name} fill={STATUS_COLORS[entry.name] ?? "#94a3b8"} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  {statusData.map((s) => (
                    <div key={s.name} className="flex items-center gap-2 text-sm">
                      <span
                        className="h-2.5 w-2.5 rounded-full"
                        style={{ background: STATUS_COLORS[s.name] ?? "#94a3b8" }}
                      />
                      <span className="capitalize text-ink-600">{s.name}</span>
                      <span className="ml-auto font-bold text-ink-900">{s.value}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-sm text-ink-400">No leads yet.</p>
            )}
          </div>

          {/* Contacted/qualified stack + sources */}
          <div className="card lg:col-span-2">
            <div className="mb-4 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-ink-400" />
              <h2 className="font-bold text-ink-900">Score distribution</h2>
            </div>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distData} margin={{ top: 0, right: 0, left: -28, bottom: 0 }}>
                  <XAxis
                    dataKey="range"
                    tick={{ fontSize: 12, fill: "#64748b" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 12, fill: "#94a3b8" }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                    domain={[0, maxDist]}
                  />
                  <Tooltip cursor={{ fill: "rgb(99 102 241 / 0.06)" }} />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={42}>
                    {distData.map((_, i) => (
                      <Cell key={i} fill={BUCKET_COLORS[i % BUCKET_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="mt-5 border-t border-ink-100 pt-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-ink-400">Sources</h3>
              <div className="mt-3 space-y-2">
                {Object.entries(stats?.source_counts ?? {}).map(([source, count]) => (
                  <div key={source} className="flex items-center gap-3">
                    <span className="w-32 truncate text-sm text-ink-600">{source}</span>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-ink-100">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-brand-500 to-violet-500"
                        style={{ width: `${(count / maxSource) * 100}%` }}
                      />
                    </div>
                    <span className="w-8 text-right text-sm font-bold text-ink-900">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="card">
          <div className="mb-4 flex items-center gap-2">
            <Radar className="h-4 w-4 text-ink-400" />
            <h2 className="font-bold text-ink-900">Top geographies</h2>
          </div>
          {stats?.countries?.length ? (
            <div className="space-y-3">
              {stats.countries.slice(0, 6).map(([country, count], i) => (
                <div key={country} className="flex items-center gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-50 text-xs font-bold text-brand-600">
                    {i + 1}
                  </span>
                  <span className="flex-1 truncate text-sm text-ink-700">{country}</span>
                  <span className="text-sm font-bold text-ink-900">{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-ink-400">No geography data yet.</p>
          )}
        </div>

        <div className="card lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Crosshair className="h-4 w-4 text-ink-400" />
              <h2 className="font-bold text-ink-900">Your ICPs</h2>
            </div>
            <Link href="/dashboard/icp" className="text-sm font-bold text-brand-600 hover:text-brand-700">
              New ICP
              <ArrowRight className="ml-1 inline h-3.5 w-3.5" />
            </Link>
          </div>
          {icps.length ? (
            <div className="divide-y divide-ink-100">
              {icps.map((icp) => (
                <div key={icp.id} className="flex items-start justify-between gap-4 py-3.5 first:pt-0 last:pb-0">
                  <div className="min-w-0">
                    <div className="truncate font-semibold text-ink-900">
                      {icp.name || "Untitled ICP"}
                    </div>
                    <div className="mt-0.5 line-clamp-1 text-sm text-ink-500">{icp.raw_input}</div>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {(icp.company_size ?? []).slice(0, 2).map((s, i) => (
                        <span key={i} className="chip-muted">
                          {s}
                        </span>
                      ))}
                      {icp.industries.slice(0, 3).map((ind, i) => (
                        <span key={i} className="chip-brand">
                          {ind}
                        </span>
                      ))}
                    </div>
                  </div>
                  <Link
                    href={`/dashboard/leads?icp=${icp.id}`}
                    className="flex shrink-0 items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-semibold text-brand-600 transition-colors hover:bg-brand-50"
                  >
                    {((stats?.icp_counts ?? {})[icp.id] ?? 0) > 0 && (
                      <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs font-bold text-brand-700">
                        {(stats?.icp_counts ?? {})[icp.id]}
                      </span>
                    )}
                    View leads
                    <ArrowRight className="inline h-3.5 w-3.5" />
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-ink-400">No ICPs yet. Create your first one.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon: Icon,
  tint,
}: {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  tint: string;
}) {
  return (
    <div className="card relative overflow-hidden transition-all hover:-translate-y-0.5 hover:shadow-pop">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-3xl font-extrabold tracking-tight text-ink-900">{value}</div>
          <div className="mt-1 text-sm font-medium text-ink-500">{label}</div>
        </div>
        <span className={`grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br ${tint} text-white shadow-md`}>
          <Icon className="h-5 w-5" />
        </span>
      </div>
    </div>
  );
}