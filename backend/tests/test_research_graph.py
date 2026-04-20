import uuid

from app.research.contracts import (
    ClaimBatch,
    Disagreement,
    DisagreementBatch,
    ExtractedClaim,
    FindingDraft,
    ReportDraft,
    SearchHit,
    SearchQueryPlan,
    Verdict,
)
from app.research.errors import ResearchError
from app.research.graph import build_graph
from app.research.persist import save_progress
from app.research.state import initial_state


PASSAGE_A = (
    "Adults who slept seven hours recalled 20 percent more word pairs than adults who slept four hours."
)
PASSAGE_B = (
    "Adults who slept seven hours recalled 5 percent more word pairs than adults who slept four hours."
)
URL_A = "https://example.edu/sleep-a"
URL_B = "https://example.edu/sleep-b"


def search_hits(query: str, _limit: int):
    return [
        SearchHit(title="Study A", url=URL_A, snippet=PASSAGE_A, content=PASSAGE_A, query=query),
        SearchHit(title="Study A copy", url=URL_A + "/", snippet=PASSAGE_A, content=PASSAGE_A, query=query),
        SearchHit(title="Study B", url=URL_B, snippet=PASSAGE_B, content=PASSAGE_B, query=query),
    ]


def scripted_model(schema, _system: str, user: str):
    if schema is SearchQueryPlan:
        return SearchQueryPlan(queries=["sleep and memory consolidation"])
    if schema is ClaimBatch:
        return ClaimBatch(
            claims=[
                ExtractedClaim(source_url=URL_A, text=PASSAGE_A, kind="statistic"),
                ExtractedClaim(
                    source_url="https://invented.example/nope",
                    text="This source was not retrieved and must be dropped from the claims.",
                    kind="fact",
                ),
                ExtractedClaim(source_url=URL_B, text=PASSAGE_B, kind="statistic"),
                ExtractedClaim(
                    source_url=URL_A,
                    text="More sleep is the most important health habit for every adult.",
                    kind="opinion",
                ),
            ]
        )
    if schema is Verdict:
        excerpt = PASSAGE_A if "20 percent" in user else PASSAGE_B
        return Verdict(status="Verified", explanation="The passage states this figure.", supporting_excerpt=excerpt)
    if schema is DisagreementBatch:
        ids = [line.split(" | ", 1)[0] for line in user.splitlines() if " | " in line]
        return DisagreementBatch(
            disagreements=[
                Disagreement(
                    claim_id_a=ids[0],
                    claim_id_b=ids[1],
                    kind="conflicting_number_or_date",
                    explanation="The studies report different recall gains for the same comparison.",
                    context="Both compare seven hours of sleep with four hours.",
                ),
                Disagreement(
                    claim_id_a=ids[0],
                    claim_id_b=ids[1],
                    kind="different_publication_date",
                    explanation="The papers were published in different years.",
                    context="Only the publication dates differ.",
                ),
            ]
        )
    if schema is ReportDraft:
        return ReportDraft(
            summary="Two retrieved studies report different recall gains for the same sleep comparison.",
            findings=[
                FindingDraft(
                    text="One retrieved study reported a 20 percent recall gain.",
                    citation_urls=[URL_A, "https://invented.example/extra"],
                    certainty="supported",
                ),
                FindingDraft(
                    text="A finding that cites nothing we retrieved.",
                    citation_urls=["https://invented.example/extra"],
                    certainty="supported",
                ),
            ],
            uncertainties=["The studies do not explain the difference."],
            limitations=["Only two sources were collected."],
        )
    raise AssertionError(schema.__name__)


def test_graph_uses_search_results_and_keeps_each_agent_in_order():
    state = build_graph(
        model=scripted_model,
        search=search_hits,
        fetch_page=lambda _url, _limit: "",
    ).invoke(initial_state("What evidence links sleep and memory?"))

    assert [step for step in state["trace"] if not step.endswith(":error") and step != "fail"] == [
        "researcher",
        "extractor",
        "fact_checker",
        "contradiction_detector",
        "writer",
    ]
    assert [source["url"] for source in state["sources"]] == [URL_A, URL_B]
    assert all(claim["source_url"] != "https://invented.example/nope" for claim in state["claims"])
    assert len(state["contradictions"]) == 1
    opinions = [claim for claim in state["claims"] if claim["kind"] == "opinion"]
    opinion_verdict = next(item for item in state["verifications"] if item["claim_id"] == opinions[0]["id"])
    assert opinion_verdict["status"] == "Insufficient evidence"
    assert state["report"]["findings"][0]["citation_urls"] == [URL_A]
    assert any("no collected source" in item for item in state["report"]["limitations"])
    assert state["report"]["summary"]


def test_search_failure_is_retried_once():
    calls = {"count": 0}

    def flaky_search(query: str, limit: int):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ResearchError("temporary search failure", retryable=True)
        return search_hits(query, limit)

    state = build_graph(
        model=scripted_model,
        search=flaky_search,
        fetch_page=lambda _url, _limit: "",
    ).invoke(initial_state("What evidence links sleep and memory?"))

    assert calls["count"] == 2
    assert "researcher:error" in state["trace"]
    assert state["failed"] is False
    assert state["sources"]


def test_configuration_error_is_not_retried():
    def missing_key(_query: str, _limit: int):
        raise ResearchError("Search API key is not configured.", retryable=False)

    state = build_graph(
        model=scripted_model,
        search=missing_key,
        fetch_page=lambda _url, _limit: "",
    ).invoke(initial_state("What evidence links sleep and memory?"))

    assert state["trace"].count("researcher:error") == 1
    assert state["trace"][-1] == "fail"
    assert state["failed"] is True
    assert state["sources"] == []


def test_graph_result_is_stored_for_the_question(client):
    created = client.post(
        "/api/research",
        json={"question": "What evidence links sleep and memory consolidation?"},
    ).json()
    state = build_graph(
        model=scripted_model,
        search=search_hits,
        fetch_page=lambda _url, _limit: "",
    ).invoke(initial_state(created["question"]))

    save_progress(uuid.UUID(created["id"]), state, finished=True)
    detail = client.get(f"/api/research/{created['id']}")

    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "completed"
    assert [source["url"] for source in body["sources"]] == [URL_A, URL_B]
    assert body["claims"]
    assert body["contradictions"][0]["explanation"]
    assert body["report"]["summary"]
    assert body["report"]["findings"][0]["citation_urls"] == [URL_A]
