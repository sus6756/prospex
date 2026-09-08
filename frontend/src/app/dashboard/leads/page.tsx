"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowDownWideNarrow,
  ArrowUpWideNarrow,
  CheckCheck,
  Download,
  Search,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Lead } from "@/types";
import { ScoreBadge } from "@/components/ui/ScoreBadge";
import { RowSkeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/components/ui/Toast";

const STATUSES = ["new", "contacted", "qualified", "unqualified"];

export default function LeadsPage() {
  return (
    <Suspense fallback={<div className="py-24 text-center text-sm text-ink-500">Loading…</div>}>
      <LeadsPageInner />
    </Suspense>
  );
}

function LeadsPageInner() {
  const sp = useSearchParams();
  const { toast } = useToast();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [minScore, setMinScore] = useState<number | undefined>();
  const [status, setStatus] = useState("");
  const [source, setSource] = useState("");
  const [country, setCountry] = useState("");
  const [sortBy, setSortBy] = useState("score");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [bulkBusy, setBulkBusy] = useState(false);
  const icpId = sp.get("icp") ? Number(sp.get("icp")) : undefined;
  const [icpName, setIcpName] = useState("");

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 350);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    (async () => {
      if (icpId) {
        try {
          const icps = await api.listIcps();
          const icp = icps.find((i) => i.id === icpId);
          if (icp) setIcpName(icp.name || "");
        } catch {
          /* ignore */
        }
      }
    })();
  }, [icpId]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listLeads({
        limit: 100,
        icp_id: icpId,
        q: debouncedQ || undefined,
        min_score: minScore,
        status: status || undefined,
        source: source || undefined,
        country: country || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setLeads(data.leads);
      setTotal(data.total);
      setSelected(new Set());
    } finally {
      setLoading(false);
    }
  }, [debouncedQ, minScore, status, source, country, sortBy, sortOrder, icpId]);

  useEffect(() => {
    const t = setTimeout(load, 0);
    return () => clearTimeout(t);
  }, [load]);

  const sourceOptions = useMemo(
    () => Array.from(new Set(leads.map((l) => l.source).filter(Boolean))).sort(),
    [leads]
  );
  const countryOptions = useMemo(
    () => Array.from(new Set(leads.map((l) => l.company?.country).filter(Boolean))).sort(),
    [leads]
  );

  function toggleSelect(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    setSelected(
      selected.size === leads.length ? new Set() : new Set(leads.map((l) => l.id))
    );
  }

  async function handleBulkStatus(nextStatus: string) {
    if (!selected.size) return;
    setBulkBusy(true);
    try {
      const res = await api.bulkUpdateStatus(Array.from(selected), nextStatus);
      toast(`${res.updated} lead${res.updated === 1 ? "" : "s"} marked ${nextStatus}`);
      await load();
    } catch {
      toast("Could not update leads", "error");
    } finally {
      setBulkBusy(false);
    }
  }

  async function handleRowStatus(id: number, s: string) {
    try {
      await api.updateLeadStatus(id, s);
      setLeads((prev) => prev.map((l) => (l.id === id ? { ...l, status: s } : l)));
      toast("Status updated");
    } catch {
      toast("Could not update status", "error");
    }
  }

  async function handleCsvExport() {
    try {
      const csv = await api.exportCsv({
        icp_id: icpId,
        q: debouncedQ || null,
        min_score: minScore ?? null,
        status: status || null,
        source: source || null,
        country: country || null,
      });
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "leads.csv";
      a.click();
      URL.revokeObjectURL(url);
      toast("CSV exported");
    } catch {
      toast("Export failed", "error");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink-900">Leads</h1>
          <p className="mt-1 text-sm text-ink-500">
            {icpName ? `For ICP: ${icpName}` : "All qualified leads"} · {total} total
          </p>
        </div>
        <button onClick={handleCsvExport} className="btn-secondary">
          <Download className="h-4 w-4" />
          Export CSV
        </button>
      </div>

      <div className="card space-y-3">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
          <input
            className="input pl-9"
            placeholder="Search company, contact, title, email…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-ink-200 bg-ink-50/50 px-3 py-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-ink-500">Score ≥</label>
            <input
              type="number"
              min={0}
              max={100}
              className="w-16 rounded-md border border-ink-200 bg-white px-2 py-1 text-sm focus:border-brand-500 focus:outline-none"
              value={minScore ?? ""}
              onChange={(e) => setMinScore(e.target.value ? Number(e.target.value) : undefined)}
            />
          </div>
          <select className="input w-40" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <select className="input w-44" value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="">All sources</option>
            {sourceOptions.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <select className="input w-44" value={country} onChange={(e) => setCountry(e.target.value)}>
            <option value="">All countries</option>
            {countryOptions.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <select className="input w-44" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="score">Sort: Score</option>
            <option value="created_at">Sort: Date</option>
            <option value="name">Sort: Company</option>
          </select>
          <button
            onClick={() => setSortOrder((o) => (o === "desc" ? "asc" : "desc"))}
            className="btn-secondary"
            title="Toggle sort direction"
          >
            {sortOrder === "desc" ? (
              <ArrowDownWideNarrow className="h-4 w-4" />
            ) : (
              <ArrowUpWideNarrow className="h-4 w-4" />
            )}
            {sortOrder === "desc" ? "Desc" : "Asc"}
          </button>
        </div>

        {selected.size > 0 && (
          <div className="flex flex-wrap items-center gap-3 rounded-xl border border-brand-200 bg-brand-50/60 px-4 py-2.5">
            <span className="text-sm font-bold text-brand-700">{selected.size} selected</span>
            <div className="flex items-center gap-1">
              {STATUSES.map((s) => (
                <button
                  key={s}
                  disabled={bulkBusy}
                  onClick={() => handleBulkStatus(s)}
                  className="cursor-pointer rounded-lg px-2.5 py-1 text-xs font-bold capitalize text-ink-600 transition-colors hover:bg-white hover:text-brand-700 hover:shadow-sm disabled:opacity-50"
                >
                  <CheckCheck className="mr-1 inline h-3.5 w-3.5" />
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {loading ? (
        <div className="card overflow-hidden p-0">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <RowSkeleton key={i} />
          ))}
        </div>
      ) : leads.length === 0 ? (
        <div className="card py-16 text-center">
          <p className="text-ink-500">No leads match your current filters.</p>
          <Link href="/dashboard/icp" className="btn-primary mt-4">
            Create an ICP
          </Link>
        </div>
      ) : (
        <div className="card overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-200 bg-ink-50/50 text-left text-xs uppercase tracking-wide text-ink-500">
                  <th className="w-10 px-4 py-3">
                    <input
                      type="checkbox"
                      className="h-4 w-4 cursor-pointer accent-brand-600"
                      checked={selected.size === leads.length && leads.length > 0}
                      onChange={toggleAll}
                    />
                  </th>
                  <th className="px-4 py-3 font-semibold">Company</th>
                  <th className="px-4 py-3 font-semibold">Industry</th>
                  <th className="px-4 py-3 font-semibold">Country</th>
                  <th className="px-4 py-3 font-semibold">Decision makers</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold">Source</th>
                  <th className="px-4 py-3 text-right font-semibold">Score</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((lead) => (
                  <tr key={lead.id} className={`table-row ${selected.has(lead.id) ? "bg-brand-50/50" : ""}`}>
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        className="h-4 w-4 cursor-pointer accent-brand-600"
                        checked={selected.has(lead.id)}
                        onChange={() => toggleSelect(lead.id)}
                      />
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/dashboard/lead/${lead.id}`}
                        className="font-semibold text-ink-900 hover:text-brand-600"
                      >
                        {lead.company?.name || "—"}
                      </Link>
                      {lead.company?.domain && (
                        <div className="text-xs text-ink-400">{lead.company.domain}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-ink-600">{lead.company?.industry || "—"}</td>
                    <td className="px-4 py-3 text-ink-600">{lead.company?.country || "—"}</td>
                    <td className="px-4 py-3">
                      <div className="flex max-w-[260px] flex-wrap gap-1">
                        {lead.contacts.slice(0, 3).map((c, i) => (
                          <span
                            key={i}
                            className={c.is_decision_maker ? "chip-brand" : "chip-muted"}
                            title={c.title}
                          >
                            {c.full_name}
                          </span>
                        ))}
                        {lead.contacts.length > 3 && (
                          <span className="chip-muted text-ink-400">
                            +{lead.contacts.length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={lead.status}
                        onChange={(e) => handleRowStatus(lead.id, e.target.value)}
                        className={`cursor-pointer rounded-lg border-0 px-2 py-1 text-xs font-bold capitalize focus:outline-none focus:ring-2 focus:ring-brand-500/30 ${
                          lead.status === "qualified"
                            ? "bg-emerald-50 text-emerald-700"
                            : lead.status === "contacted"
                            ? "bg-sky-50 text-sky-700"
                            : lead.status === "unqualified"
                            ? "bg-red-50 text-red-700"
                            : "bg-ink-100 text-ink-600"
                        }`}
                      >
                        {STATUSES.map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      <span className="chip-muted">{lead.source}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <ScoreBadge score={lead.score} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}