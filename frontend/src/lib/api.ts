import type { IcpCriteria, ICP, Lead, DiscoveryResult, LeadList, LeadStats, User, ChatMessage, ChatReply } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = "Request failed";
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return (await res.json()) as T;
  return (await res.text()) as unknown as T;
}

const TOKEN_KEY = "prospex_token";
const USER_KEY = "prospex_user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setSession(token: string, user: User) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getUser(): User | null {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || "null");
  } catch {
    return null;
  }
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(getToken());
}

export const api = {
  // Auth
  register: (data: { email: string; password: string; full_name: string }) =>
    request<{ access_token: string; user: User }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  login: (data: { email: string; password: string }) =>
    request<{ access_token: string; user: User }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // ICPs
  parseIcp: (raw_input: string) =>
    request<{ criteria: IcpCriteria }>("/api/icps/parse", {
      method: "POST",
      body: JSON.stringify({ raw_input }),
    }),
  createIcp: (data: { raw_input: string; name?: string }) =>
    request<ICP>("/api/icps", { method: "POST", body: JSON.stringify(data) }),
  listIcps: () => request<ICP[]>("/api/icps"),
  updateIcp: (id: number, data: Partial<ICP>) =>
    request<ICP>(`/api/icps/${id}`, { method: "PUT", body: JSON.stringify(data) }),

  // Discovery
  runDiscovery: (icp_id: number) =>
    request<DiscoveryResult>("/api/discovery/run", {
      method: "POST",
      body: JSON.stringify({ icp_id }),
    }),

  // Leads
  listLeads: (params: Record<string, string | number | boolean | undefined> = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") qs.set(k, String(v));
    });
    const query = qs.toString();
    return request<LeadList>(`/api/leads${query ? `?${query}` : ""}`);
  },
  getLead: (id: number) => request<Lead>(`/api/leads/${id}`),
  updateLeadStatus: (id: number, status: string) =>
    request<Lead>(`/api/leads/${id}?status=${encodeURIComponent(status)}`, {
      method: "PATCH",
    }),
  bulkUpdateStatus: (lead_ids: number[], status: string) =>
    request<{ updated: number }>("/api/leads/bulk-status", {
      method: "POST",
      body: JSON.stringify({ lead_ids, status }),
    }),
  leadStats: () => request<LeadStats>("/api/leads/stats/summary"),

  // AI chat assistant
  chatSend: (message: string, history: ChatMessage[] = [], lead_id?: number) =>
    request<ChatReply>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, history: history.slice(-10), lead_id }),
    }),

  // Export
  exportCsv: async (params: Record<string, string | number | undefined | null> = {}) => {
    const token = getToken();
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
    });
    const res = await fetch(`${API_BASE}/api/export/csv?${qs.toString()}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new ApiError(res.status, "Export failed");
    return res.text();
  },
};