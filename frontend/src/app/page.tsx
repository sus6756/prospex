"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  BarChart3,
  Bot,
  Database,
  FileSpreadsheet,
  Mail,
  Radar,
  ScanSearch,
  Sparkles,
  Target,
} from "lucide-react";
import { isAuthenticated } from "@/lib/api";

const FEATURES = [
  {
    title: "Natural Language ICP",
    desc: "Describe your ideal customer in plain English — AI turns it into a structured, editable target profile.",
    icon: Bot,
    tint: "from-brand-500 to-violet-500",
  },
  {
    title: "Multi-Source Discovery",
    desc: "Search across web data, Crunchbase-style firmographics, LinkedIn profiles, and Hunter.io in parallel.",
    icon: ScanSearch,
    tint: "from-sky-500 to-cyan-500",
  },
  {
    title: "Contact Enrichment",
    desc: "Real names, verified email patterns, titles, and LinkedIn URLs for every stakeholder.",
    icon: Mail,
    tint: "from-fuchsia-500 to-pink-500",
  },
  {
    title: "AI Lead Scoring",
    desc: "Every lead ranked 0–100 with a transparent breakdown and plain-English explanation per criterion.",
    icon: BarChart3,
    tint: "from-emerald-500 to-teal-500",
  },
  {
    title: "Duplicate Detection",
    desc: "Fuzzy matching on domain, name, and email merges or flags duplicates automatically.",
    icon: Database,
    tint: "from-amber-500 to-orange-500",
  },
  {
    title: "Search, Filter & Export",
    desc: "Drill into your pipeline, then export clean CSV or JSON for your CRM.",
    icon: FileSpreadsheet,
    tint: "from-indigo-500 to-blue-500",
  },
];

const STEPS = [
  {
    num: "01",
    title: "Define your ICP",
    desc: "Type who you want to sell to in plain English — industry, size, geography, tech stack, job titles.",
  },
  {
    num: "02",
    title: "AI finds & enriches",
    desc: "Discovery scans multiple sources in parallel, then enriches companies and decision-makers.",
  },
  {
    num: "03",
    title: "Score & act",
    desc: "Every lead is ranked with a clear explanation. Filter, qualify, and export to your CRM.",
  },
];

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated()) router.replace("/dashboard");
  }, [router]);

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-ink-50">
      {/* Ambient background blobs */}
      <div className="pointer-events-none absolute -top-32 left-1/2 h-[480px] w-[720px] -translate-x-1/2 rounded-full bg-gradient-to-r from-brand-200/40 via-violet-200/40 to-fuchsia-200/40 blur-3xl" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top-right,rgb(99_102_241/_0.08),transparent_45%)]" />

      <header className="relative border-b border-ink-200/60 bg-white/70 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-violet-600 text-white shadow-md shadow-brand-500/30">
              <Radar className="h-5 w-5" />
            </span>
            <span className="text-lg font-bold tracking-tight text-ink-900">Prospex</span>
          </div>
          <nav className="flex items-center gap-3">
            <Link href="/login" className="btn-secondary">
              Sign in
            </Link>
            <Link href="/register" className="btn-primary">
              Get started
            </Link>
          </nav>
        </div>
      </header>

      <main className="relative">
        {/* Hero */}
        <section className="mx-auto max-w-6xl px-6 pt-16 pb-16 text-center sm:pt-24">
          <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50/80 px-4 py-1.5 text-xs font-semibold text-brand-700">
            <Sparkles className="h-3.5 w-3.5" />
            AI-powered B2B lead discovery
          </div>
          <h1 className="mx-auto max-w-3xl text-4xl font-extrabold leading-[1.1] tracking-tight text-ink-900 sm:text-6xl">
            Find your next B2B customers with{" "}
            <span className="gradient-text">AI-powered precision</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-ink-500">
            Describe your ideal customer. Prospex discovers matching companies and
            decision-makers, enriches their contact data, and ranks every lead so your
            sales team only chases the best-fit opportunities.
          </p>
          <div className="mt-9 flex items-center justify-center gap-4">
            <Link href="/register" className="btn-primary px-6 py-3 text-base shadow-lg shadow-brand-500/25">
              Start discovering leads
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href="/login" className="btn-secondary px-6 py-3 text-base">
              Sign in
            </Link>
          </div>

          <div className="mx-auto mt-14 max-w-2xl rounded-2xl border border-ink-200 bg-white/80 p-6 text-left shadow-pop backdrop-blur">
            <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-ink-400">
              <Target className="h-3.5 w-3.5" />
              Example — type this and hit Discover
            </p>
            <p className="mt-3 rounded-xl bg-ink-50 px-4 py-3 font-mono text-sm text-ink-700">
              “Mid-sized SaaS companies in the United States targeting enterprise
              clients. Looking for CTOs, VP of Engineering, and Head of Product
              decision makers, venture-backed, using Salesforce and AWS.”
            </p>
          </div>
        </section>

        {/* Features */}
        <section className="mx-auto max-w-6xl px-6 pb-20">
          <h2 className="text-center text-3xl font-bold tracking-tight text-ink-900">
            Everything you need to build a clean pipeline
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-center text-ink-500">
            From raw description to a qualified, exportable lead list — in one flow.
          </p>
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="group card hover:-translate-y-1 transition-all duration-200 hover:shadow-pop"
              >
                <span
                  className={`grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br ${f.tint} text-white shadow-md transition-transform group-hover:scale-110`}
                >
                  <f.icon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 font-bold text-ink-900">{f.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-ink-500">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* How it works */}
        <section className="border-y border-ink-200 bg-white">
          <div className="mx-auto max-w-6xl px-6 py-20">
            <h2 className="text-center text-3xl font-bold tracking-tight text-ink-900">
              Three steps to a qualified pipeline
            </h2>
            <div className="mt-12 grid gap-8 sm:grid-cols-3">
              {STEPS.map((s, i) => (
                <div key={s.num} className="relative text-center sm:text-left">
                  {i < STEPS.length - 1 && (
                    <div className="absolute right-[-10%] top-6 hidden h-px w-[60%] bg-gradient-to-r from-brand-200 to-transparent sm:block" />
                  )}
                  <span className="gradient-text text-4xl font-extrabold">{s.num}</span>
                  <h3 className="mt-3 font-bold text-ink-900">{s.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-ink-500">{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="mx-auto max-w-6xl px-6 py-20 text-center">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-600 via-violet-600 to-fuchsia-600 px-6 py-16 shadow-xl shadow-brand-500/30">
            <div className="pointer-events-none absolute -top-20 -right-20 h-64 w-64 rounded-full bg-white/10 blur-2xl" />
            <div className="pointer-events-none absolute -bottom-24 -left-16 h-64 w-64 rounded-full bg-white/10 blur-2xl" />
            <h2 className="mx-auto max-w-2xl text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to fill your pipeline with high-quality leads?
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-brand-100">
              Create a free account and run your first discovery in under a minute.
            </p>
            <Link
              href="/register"
              className="mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-base font-bold text-brand-700 shadow-lg transition-all hover:-translate-y-0.5 hover:shadow-xl"
            >
              Create free account
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-ink-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-6 text-center text-sm text-ink-400">
          Prospex — AI Lead Discovery & Qualification Platform
        </div>
      </footer>
    </div>
  );
}