"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ArrowRight,
  Building2,
  CheckCircle2,
  Loader2,
  Plus,
  Table2,
  Users,
  XCircle,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { DiscoveryResult, Lead } from "@/types";
import { ScoreBadge } from "@/components/ui/ScoreBadge";

const STEPS = [
  { label: "Parsing ICP criteria", key: "parse" },
  { label: "Querying web data sources", key: "web" },
  { label: "Querying Crunchbase-like data", key: "crunchbase" },
  { label: "Searching LinkedIn profiles", key: "linkedin" },
  { label: "Hunter.io contact verification", key: "hunter" },
  { label: "Enriching & scoring leads", key: "enrich" },
];

export default function DiscoveryPage() {
  return (
    <Suspense fallback={<div className="py-24 text-center text-sm text-ink-500">Loading…</div>}>
      <DiscoveryPageInner />
    </Suspense>
  );
}

function DiscoveryPageInner() {
  const router = useRouter();
  const params = useSearchParams();
  const icpId = Number(params.get("run"));
  const icpName = params.get("name") || "";
  const [phase, setPhase] = useState<(typeof STEPS)[number]["key"]>("parse");
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<DiscoveryResult | null>(null);
  const [preview, setPreview] = useState<Lead[]>([]);
  const ranRef = useRef(false);

  const run = useCallback(async () => {
    if (!icpId || ranRef.current) return;
    ranRef.current = true;

    for (const step of STEPS) {
      await new Promise((r) => setTimeout(r, 650));
      setPhase(step.key);
    }

    try {
      const res = await api.runDiscovery(icpId);
      setResult(res);
      const leads = await api.listLeads({ icp_id: icpId, limit: 8, sort_by: "score" });
      setPreview(leads.leads);
      setPhase("enrich");
      await new Promise((r) => setTimeout(r, 500));
      setDone(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Discovery failed");
      setDone(true);
    }
  }, [icpId]);

  useEffect(() => {
    const t = setTimeout(run, 0);
    return () => clearTimeout(t);
  }, [run]);

  const currentIdx = STEPS.findIndex((s) => s.key === phase);

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold tracking-tight text-ink-900">
        Discovering leads{icpName ? ` for “${icpName}”` : ""}
      </h1>
      <p className="mt-1 text-sm text-ink-500">
        Searching multiple data sources in parallel, enriching contacts, and scoring every match.
      </p>

      {error && (
        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!done ? (
        <div className="card mt-6 space-y-1 p-6">
          {STEPS.map((step, i) => {
            const isCurrent = i === currentIdx;
            const isPast = i < currentIdx;
            return (
              <div
                key={step.key}
                className={`flex items-center gap-3 rounded-xl px-2 py-2.5 transition-colors ${
                  isCurrent ? "bg-brand-50/60" : ""
                }`}
              >
                <span
                  className={`grid h-8 w-8 shrink-0 place-items-center rounded-full text-xs font-bold ${
                    isPast
                      ? "bg-emerald-100 text-emerald-700"
                      : isCurrent
                        ? "bg-gradient-to-br from-brand-500 to-violet-600 text-white shadow-md shadow-brand-500/30"
                        : "bg-ink-100 text-ink-400"
                  }`}
                >
                  {isPast ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : isCurrent ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    i + 1
                  )}
                </span>
                <span
                  className={`text-sm ${
                    isCurrent ? "font-bold text-ink-900" : isPast ? "text-ink-500" : "text-ink-400"
                  }`}
                >
                  {step.label}
                </span>
                {isCurrent && (
                  <span className="ml-auto text-xs font-semibold text-brand-600">working…</span>
                )}
              </div>
            );
          })}
        </div>
      ) : result ? (
        <div className="mt-6 space-y-6 animate-fade-up">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <ResultCard label="Discovered" value={result.total_discovered} />
            <ResultCard label="Qualified leads" value={result.scored_count} accent="from-brand-500 to-violet-600" />
            <ResultCard label="Enriched" value={result.enriched_count} />
            <ResultCard label="Duplicates merged" value={result.duplicates_merged} />
          </div>

          <div className="card">
            <h2 className="mb-4 flex items-center gap-2 font-bold text-ink-900">
              <Building2 className="h-4 w-4 text-ink-400" />
              Top matches
            </h2>
            {preview.length === 0 ? (
              <p className="text-sm text-ink-400">No new leads found for this ICP.</p>
            ) : (
              <div className="divide-y divide-ink-100">
                {preview.map((lead, i) => (
                  <div
                    key={lead.id}
                    className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
                  >
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="hidden h-8 w-8 shrink-0 place-items-center rounded-lg bg-ink-50 text-sm font-bold text-ink-500 sm:grid">
                        {i + 1}
                      </span>
                      <div className="min-w-0">
                        <div className="truncate font-semibold text-ink-900">
                          {lead.company?.name}
                        </div>
                        <div className="truncate text-sm text-ink-500">
                          {lead.company?.industry} · {lead.company?.country} ·{" "}
                          <Users className="mr-0.5 inline h-3 w-3 text-ink-400" />
                          {lead.contacts.length} contacts
                        </div>
                      </div>
                    </div>
                    <ScoreBadge score={lead.score} />
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <button onClick={() => router.push("/dashboard/leads")} className="btn-primary flex-1 py-2.5">
              <Table2 className="h-4 w-4" />
              View full lead list
              <ArrowRight className="h-4 w-4" />
            </button>
            <button onClick={() => router.push("/dashboard/icp")} className="btn-secondary flex-1 py-2.5">
              <Plus className="h-4 w-4" />
              New ICP
            </button>
          </div>
        </div>
      ) : (
        <div className="card mt-6 py-16 text-center text-ink-400">
          <XCircle className="mx-auto h-8 w-8" />
          <p className="mt-2 text-sm">No discovery run started.</p>
        </div>
      )}
    </div>
  );
}

function ResultCard({
  label,
  value,
  accent = "from-ink-500 to-ink-600",
}: {
  label: string;
  value: number;
  accent?: string;
}) {
  return (
    <div className="card relative overflow-hidden">
      <div
        className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${accent} opacity-70`}
      />
      <div className="flex h-full flex-col items-center justify-center py-2">
        <div className="flex items-center gap-1.5 text-3xl font-extrabold tracking-tight text-ink-900">
          {value}
        </div>
        <div className="mt-1 text-xs font-medium text-ink-500">{label}</div>
      </div>
    </div>
  );
}