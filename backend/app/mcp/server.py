"""ProofLens MCP server.

The research API starts this process and talks to it over stdio. Running
`python -m app.mcp.server` serves the same tools.
"""

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from app.mcp import tools
from app.mcp.schemas import (
    ExtractClaimsOutput,
    RetrieveSourceOutput,
    SearchEvidenceOutput,
    SearchWebOutput,
    VerifyClaimOutput,
)
from app.research.errors import ResearchError

server = MCPServer(
    "ProofLens",
    instructions=(
        "Search, read, extract, check, and retrieve evidence for one ProofLens research session. "
        "Do not treat a tool error as a source."
    ),
    version="0.4.0",
)


def _fail(exc: Exception) -> None:
    raise ToolError(str(exc)) from exc


@server.tool(
    name="search_web",
    description="Search the web for sources that might bear on a research question. Returns titles, URLs, and snippets. Does not decide whether a claim is true.",
)
def search_web(query: str, limit: int = 5) -> SearchWebOutput:
    """Search the configured web search provider."""
    try:
        return SearchWebOutput.model_validate(tools.search_web(query, limit))
    except (tools.ToolInputError, ResearchError) as exc:
        _fail(exc)


@server.tool(
    name="retrieve_source",
    description="Fetch the text of one http or https source. Reuses a fresh stored copy instead of downloading it again, and stores the text for the given research session.",
)
def retrieve_source(
    url: str,
    limit: int = 4000,
    session_id: str = "",
    source_id: str = "",
    title: str = "",
) -> RetrieveSourceOutput:
    """Read one source page, or a stored copy of that page."""
    try:
        return RetrieveSourceOutput.model_validate(
            tools.retrieve_source(url, limit, session_id, source_id, title)
        )
    except (tools.ToolInputError, ResearchError) as exc:
        _fail(exc)


@server.tool(
    name="extract_claims",
    description="Extract checkable statements from source passages. Each claim keeps the source URL it was taken from. The caller decides which claims to keep.",
)
def extract_claims(sources: list[dict]) -> ExtractClaimsOutput:
    """Pull claim drafts out of already retrieved source text."""
    try:
        return ExtractClaimsOutput.model_validate(tools.extract_claims(sources))
    except (tools.ToolInputError, ResearchError) as exc:
        _fail(exc)


@server.tool(
    name="verify_claim",
    description="Compare one claim with one passage and return a status, an explanation, and any quoted excerpt. The excerpt is not trusted until the caller checks that it appears in the passage.",
)
def verify_claim(claim: str, passage: str) -> VerifyClaimOutput:
    """Ask the model to judge one claim against one passage."""
    try:
        return VerifyClaimOutput.model_validate(tools.verify_claim(claim, passage))
    except (tools.ToolInputError, ResearchError) as exc:
        _fail(exc)


@server.tool(
    name="search_evidence",
    description="Find stored evidence passages similar to a claim. Results from the current research session are preferred. Passages from earlier sessions are included only when they are similar enough, and each result names its session.",
)
def search_evidence(query: str, session_id: str, limit: int = 4) -> SearchEvidenceOutput:
    """Search stored passages for one session, plus clearly related memory."""
    try:
        return SearchEvidenceOutput.model_validate(tools.search_evidence(query, session_id, limit))
    except (tools.ToolInputError, ResearchError) as exc:
        _fail(exc)


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
