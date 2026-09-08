"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquareText,
  Radar,
  Sparkles,
  Target,
  Users,
  X,
} from "lucide-react";
import { clearSession, getUser } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/icp", label: "New ICP", icon: Target },
  { href: "/dashboard/leads", label: "Leads", icon: Users },
  { href: "/dashboard/chat", label: "Assistant", icon: MessageSquareText },
];

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const user = getUser();

  useEffect(() => {
    if (!getUser()) router.replace("/login");
  }, [router]);

  function handleLogout() {
    setOpen(false);
    clearSession();
    router.replace("/");
  }

  const active = NAV.find((n) =>
    n.href === "/dashboard" ? pathname === "/dashboard" : pathname.startsWith(n.href)
  );

  const sidebar = (
    <>
      <div className="flex items-center justify-between px-5 py-5">
        <Link
          href="/dashboard"
          className="flex items-center gap-2.5"
          onClick={() => setOpen(false)}
        >
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-violet-600 text-lg font-bold text-white shadow-md shadow-brand-500/30">
            <Radar className="h-5 w-5" />
          </span>
          <div>
            <div className="text-sm font-bold leading-tight text-ink-900">Prospex</div>
            <div className="text-[11px] font-medium text-ink-400">AI Lead Discovery</div>
          </div>
        </Link>
        <button
          onClick={() => setOpen(false)}
          className="cursor-pointer rounded-lg p-1 text-ink-400 hover:bg-ink-100 lg:hidden"
          aria-label="Close sidebar"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV.map((item) => {
          const isActive = active?.href === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className={`relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all ${
                isActive
                  ? "bg-gradient-to-r from-brand-50 to-violet-50 text-brand-700"
                  : "text-ink-500 hover:bg-ink-50 hover:text-ink-900"
              }`}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-brand-500" />
              )}
              <Icon className={`h-[18px] w-[18px] ${isActive ? "text-brand-600" : "text-ink-400"}`} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-4 pb-3">
        <Link
          href="/dashboard/icp"
          className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-violet-600 px-4 py-2.5 text-sm font-bold text-white shadow-md shadow-brand-500/30 transition-all hover:shadow-lg hover:shadow-brand-500/40 active:scale-[0.98]"
        >
          <Sparkles className="h-4 w-4" />
          New discovery
        </Link>
      </div>

      <div className="border-t border-ink-100 p-4">
        <div className="flex items-center gap-3">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 text-sm font-bold text-white">
            {(user?.full_name || "U").charAt(0).toUpperCase()}
          </span>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-semibold text-ink-800">
              {user?.full_name || user?.email || "User"}
            </div>
            <div className="truncate text-xs text-ink-400">{user?.email || ""}</div>
          </div>
          <button
            onClick={handleLogout}
            className="cursor-pointer rounded-lg p-2 text-ink-400 transition-colors hover:bg-red-50 hover:text-red-600"
            title="Sign out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </>
  );

  return (
    <div className="min-h-screen bg-ink-50">
      {/* Mobile top bar */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-ink-200 bg-white/85 px-4 py-3 backdrop-blur lg:hidden">
        <div className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-brand-500 to-violet-600 text-white">
            <Radar className="h-4 w-4" />
          </span>
          <span className="text-sm font-bold text-ink-900">Prospex</span>
        </div>
        <button
          onClick={() => setOpen(true)}
          className="cursor-pointer rounded-lg border border-ink-200 p-2 text-ink-600"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>
      </header>

      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-ink-200 bg-white lg:flex">
        {sidebar}
      </aside>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-ink-900/40 backdrop-blur-sm" onClick={() => setOpen(false)} />
          <aside className="animate-fade-up absolute inset-y-0 left-0 flex w-72 flex-col bg-white shadow-pop">
            {sidebar}
          </aside>
        </div>
      )}

      <main className="px-4 py-6 sm:px-6 lg:ml-64 lg:px-10 lg:py-8">
        <div className="mx-auto max-w-6xl animate-fade-up">{children}</div>
      </main>
    </div>
  );
}