"use client";

import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import { CheckCircle2, Info, X, XCircle } from "lucide-react";

type ToastKind = "success" | "error" | "info";
interface ToastItem {
  id: number;
  kind: ToastKind;
  message: string;
}

interface ToastContextValue {
  toast: (message: string, kind?: ToastKind) => void;
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

let toastId = 0;

const KIND_STYLES: Record<ToastKind, { ring: string; icon: ReactNode }> = {
  success: { ring: "border-emerald-200", icon: <CheckCircle2 className="h-5 w-5 text-emerald-500" /> },
  error: { ring: "border-red-200", icon: <XCircle className="h-5 w-5 text-red-500" /> },
  info: { ring: "border-brand-200", icon: <Info className="h-5 w-5 text-brand-500" /> },
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  const toast = useCallback(
    (message: string, kind: ToastKind = "success") => {
      const id = ++toastId;
      setToasts((t) => [...t, { id, kind, message }]);
      setTimeout(() => dismiss(id), 4200);
    },
    [dismiss]
  );

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="pointer-events-none fixed right-4 top-4 z-[100] flex w-80 flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`animate-fade-up pointer-events-auto flex items-start gap-3 rounded-xl border bg-white p-3.5 shadow-pop ${KIND_STYLES[t.kind].ring}`}
          >
            {KIND_STYLES[t.kind].icon}
            <p className="flex-1 text-sm font-medium text-ink-800">{t.message}</p>
            <button
              onClick={() => dismiss(t.id)}
              className="cursor-pointer text-ink-400 transition-colors hover:text-ink-700"
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}