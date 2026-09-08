export interface User {
  id: number;
  email: string;
  full_name: string;
}

export interface ICP {
  id: number;
  name: string;
  raw_input: string;
  industries: string[];
  company_size: string[];
  geographies: string[];
  revenue_min: number | null;
  revenue_max: number | null;
  tech_stack: string[];
  job_titles: string[];
  keywords: string[];
  funding_status: string;
  notes: string;
  created_at: string | null;
}

export interface IcpCriteria {
  industries: string[];
  company_size: string[];
  geographies: string[];
  revenue_min: number | null;
  revenue_max: number | null;
  tech_stack: string[];
  job_titles: string[];
  keywords: string[];
  funding_status: string;
  notes: string;
}

export interface ScoreBreakdownItem {
  criterion: string;
  score: number;
  weight: number;
  reason: string;
}

export interface Company {
  id: number;
  name: string;
  domain: string;
  industry: string;
  description: string;
  size: string;
  location: string;
  country: string;
  founded: number | null;
  website: string;
  linkedin_url: string;
  phone: string;
  annual_revenue: number | null;
  employee_count: number | null;
  tech_stack: string[];
}

export interface Contact {
  id: number;
  full_name: string;
  first_name: string;
  last_name: string;
  title: string;
  email: string;
  phone: string;
  linkedin_url: string;
  location: string;
  is_decision_maker: boolean;
  seniority: string;
}

export interface Lead {
  id: number;
  icp_id: number;
  owner_id: number;
  score: number;
  score_breakdown: ScoreBreakdownItem[];
  score_explanation: string;
  status: string;
  source: string;
  is_duplicate: boolean;
  created_at: string | null;
  company: Company | null;
  contacts: Contact[];
}

export interface LeadList {
  total: number;
  leads: Lead[];
}

export interface DiscoveryResult {
  lead_ids: number[];
  total_discovered: number;
  enriched_count: number;
  scored_count: number;
  duplicates_merged: number;
}

export interface LeadStats {
  total: number;
  avg_score: number;
  top_score: number;
  status_counts: Record<string, number>;
  source_counts: Record<string, number>;
  countries: [string, number][];
  score_distribution: { range: string; count: number }[];
  active_icps: number;
  icp_counts?: Record<number, number>;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatReply {
  reply: string;
}

export const ICP_TEMPLATES = [
  {
    name: "US SaaS · Enterprise",
    text: "Mid-sized SaaS companies in the United States targeting enterprise clients. Looking for CTOs, VP of Engineering, and Head of Product decision makers. They should use Salesforce, AWS and be venture-backed.",
  },
  {
    name: "European Fintech",
    text: "Fintech startups in Europe, seed to Series B funding. Sell to CFOs and VPs of Finance. Companies should be venture-backed and use cloud infrastructure with a focus on compliance.",
  },
  {
    name: "Healthcare Tech",
    text: "Healthcare technology companies in North America with 100-500 employees. Target Chief Medical Officers and Heads of Product. They should work with electronic health records and HIPAA-compliant cloud platforms.",
  },
];