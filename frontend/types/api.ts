export type HealthReport = {
  status: "ok" | "degraded";
  service: string;
  environment: string;
  database: "connected" | "unavailable";
  version: string;
  time: string;
};

export type ResearchQuestion = {
  id: string;
  question: string;
  status: string;
  stage?: string;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
};

export type ResearchSource = {
  url: string;
  title: string;
  snippet: string;
  content: string;
  search_query: string;
};

export type Verification = {
  status: string;
  explanation: string;
  supporting_excerpt: string;
  opposing_excerpt: string;
};

export type ResearchClaim = {
  id: string;
  source_url: string;
  text: string;
  kind: string;
  verification: Verification | null;
};

export type Contradiction = {
  explanation: string;
  context: string;
  claim_text: string;
  other_claim_text: string;
  source_url: string;
  other_source_url: string;
};

export type Finding = {
  text: string;
  citation_urls: string[];
  certainty: string;
};

export type ResearchReport = {
  summary: string;
  findings: Finding[];
  uncertainties: string[];
  limitations: string[];
};

export type ResearchSession = ResearchQuestion & {
  sources: ResearchSource[];
  claims: ResearchClaim[];
  contradictions: Contradiction[];
  report: ResearchReport | null;
};

export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
  };
};
