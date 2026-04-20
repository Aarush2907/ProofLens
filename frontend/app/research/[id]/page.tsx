import { Suspense } from "react";
import type { Metadata } from "next";
import { SessionView } from "@/features/research/SessionView";

export const metadata: Metadata = {
  title: "Research run",
};

export default function ResearchRunPage({ params }: PageProps<"/research/[id]">) {
  return (
    <Suspense fallback={<p className="text-sm text-muted">Loading this research run…</p>}>
      <ResolvedRun params={params} />
    </Suspense>
  );
}

async function ResolvedRun({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <SessionView id={id} />;
}
