export type ActivityEvent = {
  id: number;
  session_id: string;
  kind: string;
  agent: string;
  message: string;
  detail: Record<string, unknown>;
  at: string;
  terminal: boolean;
};

export type HealthReport = {
  status: "ok" | "degraded";
  service: string;
  environment: string;
  database: "connected" | "unavailable";
  qdrant?: "connected" | "unavailable" | "not_configured";
  version: string;
  time: string;
};

export type ResearchQuestion = {
  id: string;
  question: string;
  status: string;
  stage?: string;
  error_message?: string | null;
  prompt_tokens?: number;
  completion_tokens?: number;
  estimated_cost_usd?: number;
  created_at: string;
  updated_at: string;
};

export type SourceQuality = {
  role: string;
  publisher: string;
  author_known: boolean;
  date_known: boolean;
  specific: boolean;
  reports_original_data: boolean;
  reasons: string[];
};

export type ResearchSource = {
  id: string;
  url: string;
  title: string;
  domain: string;
  snippet: string;
  content: string;
  search_query: string;
  author: string;
  published_on: string;
  retrieved_at: string | null;
  quality: SourceQuality;
};

export type Verification = {
  status: string;
  explanation: string;
  supporting_excerpt: string;
  opposing_excerpt: string;
};

export type EvidencePassage = {
  id: string;
  source_id: string | null;
  source_url: string;
  stance: string;
  passage: string;
};

export type ResearchClaim = {
  id: string;
  source_id: string | null;
  source_url: string;
  text: string;
  kind: string;
  review_status: string;
  verification: Verification | null;
  evidence: EvidencePassage[];
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

export type GraphNode = {
  id: string;
  kind: string;
  label: string;
  url: string;
  status: string;
  stance: string;
  passage: string;
  review_status: string;
  explanation: string;
};

export type GraphEdge = {
  source: string;
  target: string;
  relation: string;
};

export type EvidenceGraph = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
  };
};
