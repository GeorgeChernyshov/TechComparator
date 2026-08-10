import sys
import wikipedia


def search_wikipedia(query: str, limit: int = 5) -> str:
    lines = []
    for index, title in enumerate(wikipedia.search(query, results=limit), start=1):
        page = wikipedia.page(title, auto_suggest=False)
        lines.append(f"{index}. {page.title}")
        lines.append(f"   {page.url}")
        lines.append(f"   {page.summary.splitlines()[0]}")
    return "\n".join(lines) if lines else "No results."


def main() -> int:
    query = " ".join(sys.argv[1:]).strip() or "PlayStation 2 launch price"
    print(search_wikipedia(query))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
