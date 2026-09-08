"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { Bot, Loader2, MessageSquareText, Send, Sparkles, User } from "lucide-react";
import { api } from "@/lib/api";
import type { ChatMessage, LeadStats } from "@/types";
import { useToast } from "@/components/ui/Toast";

const QUICK_PROMPTS = [
  "Summarize my pipeline",
  "Which leads should I contact first?",
  "What does a strong ICP look like?",
  "Give me a cold-email opener for my top lead",
];

function renderReply(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|\n)/g);
  return parts.map((part, i) => {
    if (part === "\n") return <br key={i} />;
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-ink-800">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

export default function ChatPage() {
  const { toast } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<LeadStats | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.leadStats().then(setStats).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text: string) {
    const question = text.trim();
    if (!question || loading) return;
    setMessages((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setLoading(true);
    try {
      const history = messages.slice(-10);
      const res = await api.chatSend(question, history);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: "Sorry — I couldn't reach the AI provider. Please try again.",
        },
      ]);
      toast("Chat request failed", "error");
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    send(input);
  }

  const statusTotal = stats ? Object.values(stats.status_counts ?? {}).reduce((a, b) => a + b, 0) : 0;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight text-ink-900">
          <MessageSquareText className="h-6 w-6 text-brand-600" />
          AI Assistant
        </h1>
        <p className="mt-1 text-sm text-ink-500">
          Ask about your pipeline, leads, or how to build a better ICP. The assistant can see
          your workspace summary.
        </p>
      </div>

      {/* Workspace context */}
      {stats && (
        <div className="card flex flex-wrap items-center gap-x-6 gap-y-3 py-4">
          <span className="flex items-center gap-2 text-sm text-ink-600">
            <Sparkles className="h-4 w-4 text-brand-500" />
            <strong className="text-ink-900">{statusTotal}</strong> leads found
          </span>
          <span className="flex items-center gap-2 text-sm text-ink-600">
            Avg score <strong className="text-ink-900">{stats.avg_score ?? 0}</strong>
          </span>
          <span className="flex items-center gap-2 text-sm text-ink-600">
            Top score <strong className="text-ink-900">{stats.top_score}</strong>
          </span>
          {stats.status_counts?.qualified > 0 && (
            <span className="chip-green">{stats.status_counts.qualified} qualified</span>
          )}
          {stats.status_counts?.contacted > 0 && (
            <span className="chip-brand">{stats.status_counts.contacted} contacted</span>
          )}
          <span className="ml-auto text-xs text-ink-400">Assistant sees this context</span>
        </div>
      )}

      {/* Chat window */}
      <div className="card flex h-[520px] flex-col overflow-hidden p-0">
        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          {messages.length === 0 && !loading && (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-violet-600 text-white shadow-lg shadow-brand-500/30">
                <Bot className="h-8 w-8" />
              </div>
              <h2 className="mt-4 font-bold text-ink-900">Ask me anything about your pipeline</h2>
              <p className="mt-1 max-w-sm text-sm text-ink-500">
                I can summarize your leads, recommend who to contact, critique your ICP, or draft
                outreach messages.
              </p>
              <div className="mt-5 flex max-w-md flex-wrap justify-center gap-2">
                {QUICK_PROMPTS.map((p) => (
                  <button
                    key={p}
                    onClick={() => send(p)}
                    className="chip-brand cursor-pointer border border-brand-200 text-brand-700 transition-colors hover:bg-brand-100"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}
            >
              <span
                className={`grid h-8 w-8 shrink-0 place-items-center rounded-full ${
                  m.role === "user"
                    ? "bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white"
                    : "bg-gradient-to-br from-brand-500 to-violet-600 text-white"
                }`}
              >
                {m.role === "user" ? (
                  <User className="h-4 w-4" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
              </span>
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  m.role === "user"
                    ? "rounded-tr-sm bg-brand-600 text-white"
                    : "rounded-tl-sm border border-ink-200 bg-ink-50/70 text-ink-700"
                }`}
              >
                {m.role === "assistant" ? renderReply(m.content) : m.content}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-start gap-3">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-violet-600 text-white">
                <Bot className="h-4 w-4" />
              </span>
              <div className="flex items-center gap-2 rounded-2xl rounded-tl-sm border border-ink-200 bg-ink-50/70 px-4 py-3">
                <Loader2 className="h-4 w-4 animate-spin text-brand-500" />
                <span className="text-sm text-ink-500">Thinking…</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={onSubmit} className="flex items-center gap-2 border-t border-ink-200 p-3">
          <input
            className="input flex-1"
            placeholder="Ask about your leads, scoring, or outreach…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="btn-primary !px-3 !py-2.5"
            aria-label="Send"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}