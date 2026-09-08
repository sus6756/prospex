"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2, Lock, Mail, Radar, User } from "lucide-react";
import { api, ApiError, setSession } from "@/lib/api";

export default function AuthPage({
  mode,
}: {
  mode: "login" | "register";
}) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isRegister = mode === "register";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res =
        mode === "register"
          ? await api.register({ email, password, full_name: fullName })
          : await api.login({ email, password });
      setSession(res.access_token, res.user);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-brand-50 via-ink-50 to-white px-6">
      <div className="pointer-events-none absolute -top-24 -left-24 h-72 w-72 rounded-full bg-brand-200/40 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-violet-200/40 blur-3xl" />
      <div className="relative w-full max-w-md">
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-2.5">
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-violet-600 text-white shadow-lg shadow-brand-500/30">
              <Radar className="h-6 w-6" />
            </span>
            <span className="text-xl font-bold tracking-tight text-ink-900">Prospex</span>
          </Link>
          <h1 className="mt-6 text-2xl font-bold text-ink-900">
            {isRegister ? "Create your account" : "Welcome back"}
          </h1>
          <p className="mt-1 text-sm text-ink-500">
            {isRegister
              ? "Start discovering qualified leads in minutes."
              : "Sign in to your lead discovery workspace."}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card animate-fade-up space-y-4 shadow-pop">
          {isRegister && (
            <div>
              <label className="label" htmlFor="fullName">
                Full name
              </label>
              <div className="relative">
                <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
                <input
                  id="fullName"
                  className="input pl-9"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Ada Lovelace"
                />
              </div>
            </div>
          )}
          <div>
            <label className="label" htmlFor="email">
              Email
            </label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
              <input
                id="email"
                type="email"
                required
                className="input pl-9"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
              />
            </div>
          </div>
          <div>
            <label className="label" htmlFor="password">
              Password
            </label>
            <div className="relative">
              <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
              <input
                id="password"
                type="password"
                required
                minLength={6}
                className="input pl-9"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
          </div>

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full py-2.5 shadow-lg shadow-brand-500/20"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {loading
              ? isRegister
                ? "Creating account…"
                : "Signing in…"
              : isRegister
                ? "Create account"
                : "Sign in"}
          </button>

          <p className="text-center text-sm text-ink-500">
            {isRegister ? (
              <>
                Already have an account?{" "}
                <a href="/login" className="font-medium text-brand-600 hover:underline">
                  Sign in
                </a>
              </>
            ) : (
              <>
                New to Prospex?{" "}
                <a href="/register" className="font-medium text-brand-600 hover:underline">
                  Create an account
                </a>
              </>
            )}
          </p>
        </form>
      </div>
    </div>
  );
}