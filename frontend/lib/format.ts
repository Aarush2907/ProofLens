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
  if (status === "submitted") {
    return "Submitted";
  }
  return status;
}

export function statusDetail(status: string): string {
  if (status === "submitted") {
    return "Saved. Research has not run.";
  }
  return "Recorded. No findings are attached.";
}
