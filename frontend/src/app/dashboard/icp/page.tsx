"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Bot,
  CheckCheck,
  Pencil,
  Sparkles,
  Target,
  Wand2,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { IcpCriteria } from "@/types";
import { ICP_TEMPLATES } from "@/types";
import { useToast } from "@/components/ui/Toast";

const CHIP_LABELS: Record<string, string> = {
  industries: "Industries",
  company_size: "Company size",
  geographies: "Geographies",
  tech_stack: "Tech stack",
  job_titles: "Decision makers",
  keywords: "Keywords",
};

export default function IcpPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [rawInput, setRawInput] = useState("");
  const [name, setName] = useState("");
  const [criteria, setCriteria] = useState<IcpCriteria | null>(null);
  const [editing, setEditing] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [editable, setEditable] = useState<Record<string, string>>({});

  function applyCriteria(c: IcpCriteria) {
    setCriteria(c);
    setEditable({
      industries: c.industries.join(", "),
      company_size: c.company_size.join(", "),
      geographies: c.geographies.join(", "),
      tech_stack: c.tech_stack.join(", "),
      job_titles: c.job_titles.join(", "),
      keywords: c.keywords.join(", "),
    });
  }

  async function handleParse() {
    if (!rawInput.trim()) return;
    setParsing(true);
    setError("");
    try {
      const res = await api.parseIcp(rawInput);
      applyCriteria(res.criteria);
      setName(res.criteria.notes ? `${rawInput.slice(0, 40).trim()}…` : "");
      toast("ICP parsed — review below");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to parse ICP");
    } finally {
      setParsing(false);
    }
  }

  function handleSaveEdits() {
    if (!criteria) return;
    const split = (v: string) => v.split(",").map((s) => s.trim()).filter(Boolean);
    setCriteria({
      ...criteria,
      industries: split(editable.industries),
      company_size: split(editable.company_size),
      geographies: split(editable.geographies),
      tech_stack: split(editable.tech_stack),
      job_titles: split(editable.job_titles),
      keywords: split(editable.keywords),
    });
    setEditing(false);
    toast("Criteria updated");
  }

  async function handleCreateAndDiscover() {
    if (!criteria) return;
    setCreating(true);
    setError("");
    try {
      const icp = await api.createIcp({ raw_input: rawInput, name: name || rawInput.slice(0, 40) });
      router.push(`/dashboard/lead?run=${icp.id}${name ? `&name=${encodeURIComponent(name)}` : ""}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create ICP");
      setCreating(false);
    }
  }

  const chips: { key: string; items: string[] }[] = criteria
    ? [
        ["industries", "company_size", "geographies"].map((k) => ({
          key: k,
          items: (criteria as unknown as Record<string, string[]>)[k] || [],
        })),
        ["tech_stack", "job_titles", "keywords"].map((k) => ({
          key: k,
          items: (criteria as unknown as Record<string, string[]>)[k] || [],
        })),
      ].flat()
    : [];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight text-ink-900">
          <Target className="h-6 w-6 text-brand-600" />
          Define your Ideal Customer
        </h1>
        <p className="mt-1 text-sm text-ink-500">
          Describe who you sell to in plain English. AI extracts the criteria — review and
          refine before discovering leads.
        </p>
      </div>

      <div className="card relative overflow-hidden">
        <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-brand-100/40 blur-3xl" />
        <div className="relative space-y-5">
          <div>
            <label className="label" htmlFor="icp-input">
              Your ICP in plain English
            </label>
            <textarea
              id="icp-input"
              rows={5}
              className="input resize-y font-normal"
              placeholder="e.g. Mid-sized SaaS companies in the United States targeting enterprise clients. Looking for CTOs, VP of Engineering and Head of Product decision makers. They should use Salesforce, AWS and be venture-backed."
              value={rawInput}
              onChange={(e) => setRawInput(e.target.value)}
            />
          </div>

          <div>
            <label className="label">Try an example</label>
            <div className="flex flex-wrap gap-2">
              {ICP_TEMPLATES.map((t) => (
                <button
                  key={t.name}
                  type="button"
                  onClick={() => setRawInput(t.text)}
                  className="chip-muted cursor-pointer border border-ink-200 hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700"
                >
                  {t.name}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700">
              {error}
            </div>
          )}

          <button
            type="button"
            onClick={handleParse}
            disabled={parsing || !rawInput.trim()}
            className="btn-primary w-full py-2.5 shadow-lg shadow-brand-500/20"
          >
            {parsing ? (
              <>
                <Bot className="h-4 w-4 animate-pulse" />
                Parsing with AI…
              </>
            ) : criteria ? (
              <>
                <Wand2 className="h-4 w-4" />
                Re-parse
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                AI-parse my ICP
              </>
            )}
          </button>
        </div>
      </div>

      {criteria && (
        <div className="card animate-fade-up space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-lg font-bold text-ink-900">
              <Bot className="h-5 w-5 text-brand-600" />
              Parsed criteria
            </h2>
            {!editing ? (
              <button onClick={() => setEditing(true)} className="btn-secondary">
                <Pencil className="h-4 w-4" />
                Edit
              </button>
            ) : (
              <div className="flex gap-2">
                <button onClick={() => setEditing(false)} className="btn-secondary">
                  Cancel
                </button>
                <button onClick={handleSaveEdits} className="btn-primary">
                  <CheckCheck className="h-4 w-4" />
                  Save edits
                </button>
              </div>
            )}
          </div>

          {editing ? (
            <div className="space-y-4">
              {Object.entries(CHIP_LABELS).map(([key, label]) => (
                <div key={key}>
                  <label className="label">
                    {label}{" "}
                    <span className="font-normal normal-case text-ink-400">
                      (comma-separated)
                    </span>
                  </label>
                  <input
                    className="input"
                    value={editable[key] || ""}
                    onChange={(e) => setEditable((p) => ({ ...p, [key]: e.target.value }))}
                  />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="label">ICP name</label>
                <input
                  className="input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. US SaaS Enterprise"
                />
              </div>
              {chips.map(({ key, items }) =>
                items.length ? (
                  <div key={key}>
                    <div className="label">{CHIP_LABELS[key] ?? key}</div>
                    <div className="flex flex-wrap gap-1.5">
                      {items.map((item, i) => (
                        <span key={i} className="chip-brand">
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null
              )}
              {(criteria.revenue_min != null || criteria.revenue_max != null) && (
                <div>
                  <div className="label">Revenue range</div>
                  <span className="chip-muted">
                    {criteria.revenue_min != null
                      ? `$${(criteria.revenue_min / 1e6).toFixed(0)}M`
                      : "unbounded"}{" "}
                    –{" "}
                    {criteria.revenue_max != null
                      ? `$${(criteria.revenue_max / 1e6).toFixed(0)}M`
                      : "unbounded"}
                  </span>
                </div>
              )}
              {criteria.funding_status && (
                <div>
                  <div className="label">Funding status</div>
                  <span className="chip-muted">{criteria.funding_status}</span>
                </div>
              )}
              {criteria.notes && (
                <div>
                  <div className="label">Notes</div>
                  <p className="rounded-xl bg-ink-50 px-4 py-2.5 text-sm text-ink-600">
                    {criteria.notes}
                  </p>
                </div>
              )}
            </div>
          )}

          <button
            onClick={handleCreateAndDiscover}
            disabled={creating}
            className="btn-primary w-full py-2.5 shadow-lg shadow-brand-500/20"
          >
            {creating ? (
              "Creating ICP…"
            ) : (
              <>
                Create ICP & Discover leads
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}