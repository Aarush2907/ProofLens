import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.results import (
    ClaimRecord,
    ContradictionRecord,
    EvidenceRecord,
    SourceRecord,
    VerificationRecord,
)
from app.schemas.research import EvidenceGraphRead, GraphEdgeRead, GraphNodeRead
from app.services.research import get_research_question


def load_evidence_graph(db: Session, question_id: uuid.UUID) -> EvidenceGraphRead:
    """Build the graph from saved rows only.

    A node or edge is included when a source, claim, evidence passage, or
    contradiction row exists. Nothing is added to make the picture look fuller.
    """

    question = get_research_question(db, question_id)
    sources = list(
        db.scalars(
            select(SourceRecord)
            .where(SourceRecord.research_question_id == question.id)
            .order_by(SourceRecord.position)
        ).all()
    )
    claims = list(
        db.scalars(
            select(ClaimRecord)
            .where(ClaimRecord.research_question_id == question.id)
            .order_by(ClaimRecord.position)
        ).all()
    )
    verifications = {
        item.claim_id: item
        for item in db.scalars(
            select(VerificationRecord).where(VerificationRecord.research_question_id == question.id)
        ).all()
    }
    evidence = list(
        db.scalars(
            select(EvidenceRecord)
            .where(EvidenceRecord.research_question_id == question.id)
            .order_by(EvidenceRecord.stance, EvidenceRecord.passage)
        ).all()
    )
    contradictions = list(
        db.scalars(
            select(ContradictionRecord).where(ContradictionRecord.research_question_id == question.id)
        ).all()
    )

    nodes = [
        GraphNodeRead(id=f"question:{question.id}", kind="question", label=question.question),
    ]
    edges = []
    source_ids = set()
    claim_ids = set()

    for source in sources:
        node_id = f"source:{source.id}"
        source_ids.add(source.id)
        nodes.append(
            GraphNodeRead(
                id=node_id,
                kind="source",
                label=source.title,
                url=source.url,
            )
        )
        edges.append(GraphEdgeRead(source=f"question:{question.id}", target=node_id, relation="retrieved"))

    for claim in claims:
        node_id = f"claim:{claim.id}"
        claim_ids.add(claim.id)
        verdict = verifications.get(claim.id)
        nodes.append(
            GraphNodeRead(
                id=node_id,
                kind="claim",
                label=claim.text,
                url=claim.source_url,
                status=verdict.status if verdict else "",
                review_status=claim.review_status,
                explanation=verdict.explanation if verdict else "",
            )
        )
        if claim.source_id in source_ids:
            edges.append(
                GraphEdgeRead(source=f"source:{claim.source_id}", target=node_id, relation="extracted")
            )

    for item in evidence:
        if item.claim_id not in claim_ids or not item.passage.strip():
            continue
        node_id = f"evidence:{item.id}"
        nodes.append(
            GraphNodeRead(
                id=node_id,
                kind="evidence",
                label=item.passage,
                url=item.source_url,
                stance=item.stance,
                passage=item.passage,
            )
        )
        relation = "supports" if item.stance == "supporting" else "contradicts"
        edges.append(GraphEdgeRead(source=node_id, target=f"claim:{item.claim_id}", relation=relation))

    for item in contradictions:
        if item.claim_id in claim_ids and item.other_claim_id in claim_ids:
            edges.append(
                GraphEdgeRead(
                    source=f"claim:{item.claim_id}",
                    target=f"claim:{item.other_claim_id}",
                    relation="disagrees",
                )
            )

    return EvidenceGraphRead(nodes=nodes, edges=edges)
