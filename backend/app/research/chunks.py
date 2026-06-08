"""Clean source text and split it into passages that can be stored."""


def clean_text(value: str) -> str:
    return " ".join((value or "").replace("\x00", " ").split())


def chunk_text(value: str, size: int, overlap: int) -> list[str]:
    text = clean_text(value)
    if not text:
        return []
    size = max(size, 200)
    overlap = max(0, min(overlap, size // 2))
    if len(text) <= size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            space = text.rfind(" ", start + size // 2, end)
            if space > start:
                end = space
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        next_start = max(end - overlap, start + 1)
        start = next_start
    return chunks
