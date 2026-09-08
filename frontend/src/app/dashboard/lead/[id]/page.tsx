"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Building2,
  Copy,
  ExternalLink,
  Globe,
  Link2,
  Mail,
  MapPin,
  Users,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Lead } from "@/types";
import { ScoreRing, scoreRingColor } from "@/components/ui/ScoreBadge";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/components/ui/Toast";

const STATUSES = ["new", "contacted", "qualified", "unqualified"];

export default function LeadDetailPage() {
  const params = useParams<{ id: string }>();
  const leadId = Number(params.id);
  const router = useRouter();
  const { toast } = useToast();
  const [lead, setLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setLead(await api.getLead(leadId));
      } catch {
        setError("Lead not found");
      } finally {
        setLoading(false);
      }
    })();
  }, [leadId]);

  async function setStatus(status: string) {
    if (!lead) return;
    try {
      const updated = await api.updateLeadStatus(lead.id, status);
      setLead(updated);
      toast(`Status set to ${status}`);
    } catch {
      toast("Could not update status", "error");
    }
  }

  function copyEmail(email: string) {
    navigator.clipboard?.writeText(email);
    toast("Email copied");
  }

  if (loading)
    return (
      <div className="mx-auto max-w-4xl space-y-6">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-10 w-1/2" />
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="card space-y-4 lg:col-span-3">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-4 w-full" />
            ))}
          </div>
          <div className="card space-y-4 lg:col-span-2">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </div>
      </div>
    );
  if (error || !lead)
    return <div className="card py-16 text-center text-sm text-ink-500">{error || "Not found"}</div>;

  const company = lead.company;
  const sortedDesc = [...(lead.score_breakdown || [])].sort((a, b) => b.weight - a.weight);
  const ringColor = scoreRingColor(lead.score);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <button
        onClick={() => router.back()}
        className="btn-ghost gap-1.5 !px-2 !py-1 text-sm"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to leads
      </button>

      {/* Hero */}
      <div className="card relative overflow-hidden p-0">
        <div className="h-2 bg-gradient-to-r from-brand-500 via-violet-500 to-fuchsia-500" />
        <div className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full bg-violet-100/50 blur-3xl" />
        <div className="flex flex-wrap items-center justify-between gap-6 p-6">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <span className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-violet-600 text-white shadow-md shadow-brand-500/30">
                <Building2 className="h-6 w-6" />
              </span>
              <div className="min-w-0">
                <h1 className="truncate text-2xl font-bold tracking-tight text-ink-900">
                  {company?.name || "—"}
                </h1>
                <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-ink-500">
                  {company?.industry && (
                    <span className="flex items-center gap-1">
                      <Zap className="h-3.5 w-3.5 text-ink-400" />
                      {company.industry}
                    </span>
                  )}
                  {company?.country && (
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5 text-ink-400" />
                      {company.location || company.country}
                    </span>
                  )}
                  {company?.size && (
                    <span className="flex items-center gap-1">
                      <Users className="h-3.5 w-3.5 text-ink-400" />
                      {company.size}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-5">
            <div className="flex items-center gap-3">
              <ScoreRing score={lead.score} size={84} />
              <div className="flex flex-col items-start">
                <span
                  className="text-2xl font-extrabold tracking-tight"
                  style={{ color: ringColor }}
                >
                  {Math.round(lead.score)}
                </span>
                <span className="text-xs font-semibold text-ink-400">/ 100 fit</span>
              </div>
            </div>
            <select
              className="input w-40"
              value={lead.status}
              onChange={(e) => setStatus(e.target.value)}
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  Status: {s}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {lead.score_explanation && (
        <div className="callout">
          <p className="text-xs font-bold uppercase tracking-wider text-brand-600">
            AI qualification summary
          </p>
          <p className="mt-1.5 text-sm leading-relaxed text-ink-700">{lead.score_explanation}</p>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="card space-y-5 lg:col-span-3">
          <h2 className="flex items-center gap-2 font-bold text-ink-900">
            <Building2 className="h-4 w-4 text-ink-400" />
            Company profile
          </h2>
          {company?.description && (
            <p className="text-sm leading-relaxed text-ink-600">{company.description}</p>
          )}

          <div className="grid grid-cols-2 gap-x-4 gap-y-5 text-sm">
            <Fact
              label="Website"
              value={company?.website || "—"}
              link={company?.website}
              icon={Globe}
            />
            <Fact
              label="LinkedIn"
              value={company?.linkedin_url || "—"}
              link={company?.linkedin_url}
              icon={Link2}
            />
            <Fact
              label="Employees"
              value={company?.employee_count ? String(company.employee_count) : "—"}
            />
            <Fact
              label="Annual revenue"
              value={
                company?.annual_revenue ? `$${(company.annual_revenue / 1e6).toFixed(1)}M` : "—"
              }
            />
            <Fact label="Founded" value={company?.founded ? String(company.founded) : "—"} />
            <Fact label="Phone" value={company?.phone || "—"} />
          </div>

          {company?.tech_stack && company.tech_stack.length > 0 && (
            <div>
              <div className="label mb-2">Tech stack</div>
              <div className="flex flex-wrap gap-1.5">
                {company.tech_stack.map((t, i) => (
                  <span key={i} className="chip-brand">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="card space-y-4 lg:col-span-2">
          <h2 className="font-bold text-ink-900">Score breakdown</h2>
          {sortedDesc.map((b) => {
            const tone =
              b.score >= 80
                ? "bg-emerald-500"
                : b.score >= 50
                ? "bg-amber-500"
                : "bg-red-500";
            return (
              <div key={b.criterion}>
                <div className="mb-1.5 flex items-center justify-between gap-2 text-sm">
                  <span className="font-semibold text-ink-700">{b.criterion}</span>
                  <span className={b.score >= 80 ? "chip-green" : b.score >= 50 ? "chip-amber" : "chip-red"}>
                    {Math.round(b.score)} · {Math.round(b.weight * 100)}%
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-ink-100">
                  <div
                    className={`h-full rounded-full ${tone} transition-all`}
                    style={{ width: `${b.score}%` }}
                  />
                </div>
                <p className="mt-1 text-xs leading-relaxed text-ink-400">{b.reason}</p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card">
        <h2 className="mb-4 flex items-center gap-2 font-bold text-ink-900">
          <Users className="h-4 w-4 text-ink-400" />
          Decision makers & contacts
          <span className="chip-brand ml-1">{lead.contacts.length} found</span>
        </h2>
        {lead.contacts.length === 0 ? (
          <p className="text-sm text-ink-400">No contacts found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-200 text-left text-xs uppercase tracking-wide text-ink-500">
                  <th className="py-2 pr-4 font-semibold">Name</th>
                  <th className="py-2 pr-4 font-semibold">Title</th>
                  <th className="py-2 pr-4 font-semibold">Email</th>
                  <th className="py-2 pr-4 font-semibold">Phone</th>
                  <th className="py-2 font-semibold">LinkedIn</th>
                </tr>
              </thead>
              <tbody>
                {lead.contacts.map((c) => (
                  <tr key={c.id} className="border-b border-ink-100 last:border-0">
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2 font-semibold text-ink-800">
                        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-gradient-to-br from-ink-200 to-ink-300 text-xs font-bold text-ink-700">
                          {(c.full_name || "?").charAt(0)}
                        </span>
                        {c.full_name}
                      </div>
                      {c.is_decision_maker && (
                        <span className="chip-brand mt-1">Decision maker</span>
                      )}
                    </td>
                    <td className="py-3 pr-4 text-ink-600">{c.title || "—"}</td>
                    <td className="py-3 pr-4">
                      {c.email ? (
                        <button
                          onClick={() => copyEmail(c.email!)}
                          className="group inline-flex items-center gap-1.5 font-mono text-xs text-ink-700 transition-colors hover:text-brand-600"
                          title="Copy email"
                        >
                          <Mail className="h-3.5 w-3.5 text-ink-400 group-hover:text-brand-500" />
                          {c.email}
                          <Copy className="h-3 w-3 text-ink-300 group-hover:text-brand-400" />
                        </button>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="py-3 pr-4 text-ink-600">{c.phone || "—"}</td>
                    <td className="py-3">
                      {c.linkedin_url ? (
                        <a
                          href={c.linkedin_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-brand-600 hover:underline"
                        >
                          Profile
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function Fact({
  label,
  value,
  link,
  icon: Icon,
}: {
  label: string;
  value: string;
  link?: string;
  icon?: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div>
      <div className="mb-0.5 flex items-center gap-1.5 text-xs uppercase tracking-wide text-ink-400">
        {Icon && <Icon className="h-3.5 w-3.5" />}
        {label}
      </div>
      {link ? (
        <a
          href={link}
          target="_blank"
          rel="noreferrer"
          className="mt-1 flex items-center gap-1 break-all text-sm font-medium text-brand-600 hover:underline"
        >
          {value}
          <ExternalLink className="h-3 w-3 shrink-0" />
        </a>
      ) : (
        <div className="mt-1 truncate text-sm font-medium text-ink-800">{value}</div>
      )}
    </div>
  );
}