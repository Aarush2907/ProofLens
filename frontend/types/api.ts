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
  created_at: string;
  updated_at: string;
};

export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
  };
};
