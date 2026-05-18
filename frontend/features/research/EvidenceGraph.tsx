"use client";

import { useEffect, useMemo, useState } from "react";
import { Background, Controls, ReactFlow, type Edge, type Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { fetchEvidenceGraph } from "@/lib/api";
import type { EvidenceGraph, GraphNode } from "@/types/api";

const COLUMN: Record<string, number> = {
  question: 0,
  source: 340,
  claim: 700,
  evidence: 1060,
};

export function EvidenceGraphView({ sessionId, refreshKey }: { sessionId: string; refreshKey: string }) {
  const [graph, setGraph] = useState<EvidenceGraph | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const next = await fetchEvidenceGraph(sessionId);
        if (!cancelled) {
          setGraph(next);
          setError(null);
        }
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "The evidence graph could not be loaded.");
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [sessionId, refreshKey]);

  const selected = graph?.nodes.find((node) => node.id === selectedId) ?? null;
  const related = useMemo(() => relatedNodes(graph, selected), [graph, selected]);
  const flow = useMemo(() => toFlow(graph), [graph]);

  if (error) {
    return <p className="text-sm text-danger">{error}</p>;
  }
  if (graph === null) {
    return <p className="text-sm text-muted">Loading the evidence graph…</p>;
  }
  if (graph.nodes.length === 1) {
    return <p className="text-sm text-muted">No sources or claims have been saved, so the graph has only the question.</p>;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <div className="h-[34rem] overflow-hidden rounded-2xl border border-line bg-panel">
        <ReactFlow
          nodes={flow.nodes}
          edges={flow.edges}
          fitView
          proOptions={{ hideAttribution: true }}
          onNodeClick={(_event, node) => setSelectedId(node.id)}
        >
          <Background />
          <Controls />
        </ReactFlow>
      </div>
      <GraphDetail node={selected} related={related} />
    </div>
  );
}

function toFlow(graph: EvidenceGraph | null): { nodes: Node[]; edges: Edge[] } {
  if (graph === null) {
    return { nodes: [], edges: [] };
  }
  const row = { question: 0, source: 0, claim: 0, evidence: 0 };
  const nodes = graph.nodes.map((node) => {
    const kind = node.kind in row ? node.kind : "claim";
    const y = row[kind as keyof typeof row] * 130;
    row[kind as keyof typeof row] += 1;
    return {
      id: node.id,
      position: { x: COLUMN[kind] ?? 0, y },
      data: { label: node.label.length > 160 ? `${node.label.slice(0, 157)}…` : node.label },
      style: nodeStyle(node),
    };
  });
  const edges = graph.edges.map((edge) => ({
    id: `${edge.source}:${edge.relation}:${edge.target}`,
    source: edge.source,
    target: edge.target,
    label: edge.relation,
  }));
  return { nodes, edges };
}

function nodeStyle(node: GraphNode): Record<string, string | number> {
  const border =
    node.kind === "evidence" && node.stance === "opposing"
      ? "#e09284"
      : node.kind === "claim"
        ? "#d7b07a"
        : "#8fb8b0";
  return {
    background: "#1a2430",
    color: "#ebe4d8",
    border: `1px solid ${border}`,
    borderRadius: 12,
    fontSize: 12,
    width: 240,
    padding: 8,
  };
}

function relatedNodes(graph: EvidenceGraph | null, selected: GraphNode | null): GraphNode[] {
  if (graph === null || selected === null) {
    return [];
  }
  const ids = new Set<string>();
  for (const edge of graph.edges) {
    if (edge.source === selected.id) ids.add(edge.target);
    if (edge.target === selected.id) ids.add(edge.source);
  }
  return graph.nodes.filter((node) => ids.has(node.id));
}

function GraphDetail({ node, related }: { node: GraphNode | null; related: GraphNode[] }) {
  if (node === null) {
    return (
      <aside className="rounded-2xl border border-line bg-panel px-4 py-4 text-sm leading-6 text-muted">
        Select a claim, source, or passage. The lines are only the relationships saved for this run.
      </aside>
    );
  }
  const sources = related.filter((item) => item.kind === "source");
  const evidence = related.filter((item) => item.kind === "evidence");
  return (
    <aside className="rounded-2xl border border-line bg-panel px-4 py-4">
      <p className="text-xs uppercase tracking-[0.16em] text-brass">{node.kind}</p>
      <h3 className="mt-2 font-serif text-xl leading-snug text-foreground">{node.label}</h3>
      {node.status ? <p className="mt-2 text-sm text-brass">{node.status}</p> : null}
      {node.review_status ? <p className="mt-1 text-xs uppercase tracking-wide text-muted">{node.review_status}</p> : null}
      {node.explanation ? <p className="mt-3 text-sm leading-6 text-muted">{node.explanation}</p> : null}
      {node.url ? (
        <a href={node.url} className="mt-3 block break-all text-xs text-sea" target="_blank" rel="noreferrer">
          {node.url}
        </a>
      ) : null}
      {node.passage ? <p className="mt-3 text-sm leading-6 text-foreground">{node.passage}</p> : null}
      {sources.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs uppercase tracking-[0.16em] text-muted">Connected sources</p>
          {sources.map((source) => (
            <a key={source.id} href={source.url} className="mt-2 block text-sm text-sea" target="_blank" rel="noreferrer">
              {source.label}
            </a>
          ))}
        </div>
      ) : null}
      {evidence.length > 0 ? (
        <div className="mt-4 space-y-3">
          <p className="text-xs uppercase tracking-[0.16em] text-muted">Connected passages</p>
          {evidence.map((item) => (
            <p key={item.id} className="text-sm leading-6 text-foreground">
              <span className="text-brass">{item.stance}. </span>
              {item.passage}
            </p>
          ))}
        </div>
      ) : null}
    </aside>
  );
}
