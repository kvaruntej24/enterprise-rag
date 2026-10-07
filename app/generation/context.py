from app.retrieval.semantic import SearchResult


def build_context(
    results: list[SearchResult], max_chars: int = 6000
) -> tuple[str, list[SearchResult]]:
    blocks: list[str] = []
    used: list[SearchResult] = []
    total = 0
    for result in results:
        location = result.source + (f", page {result.page}" if result.page else "")
        block = f"[{len(used) + 1}] ({location})\n{result.content}"
        if used and total + len(block) > max_chars:
            break
        blocks.append(block)
        used.append(result)
        total += len(block)
    return "\n\n".join(blocks), used