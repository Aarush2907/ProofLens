export function formatSavedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function statusLabel(status: string): string {
  if (status === "submitted") return "Submitted";
  if (status === "running") return "Running";
  if (status === "completed") return "Completed";
  if (status === "failed") return "Failed";
  return status;
}

export function statusDetail(status: string): string {
  if (status === "submitted") return "Saved. Research has not run.";
  if (status === "running") return "Research is in progress.";
  if (status === "completed") return "A report was saved from this run.";
  if (status === "failed") return "Research stopped before a finished report.";
  return "Recorded. No findings are attached.";
}

export function stageDetail(stage: string, status: string): string {
  if (status === "failed") return "Research stopped.";
  if (status === "submitted") return "Saved before a research run was started.";
  if (status === "completed" || stage === "completed") return "The report was saved from the completed run.";
  const copy: Record<string, string> = {
    researching: "The researcher is searching. Sources appear here when they are saved.",
    sources_collected: "Sources are saved. The extractor has not finished.",
    claims_extracted: "Claims are saved. The fact-checker has not finished.",
    claims_checked: "Verification is saved. The contradiction check has not finished.",
    contradictions_checked: "Contradictions are saved. The writer has not finished.",
    report_written: "The writer has finished. The run is being saved.",
  };
  return copy[stage] ?? "Research is in progress.";
}
