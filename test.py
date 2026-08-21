import sys
import wikipedia
from pathlib import Path
from src.comparison import compare_products
from src.database import find_product
from src.product import Product, ProductVariant

DB_FILE = Path(__file__).resolve().with_name("tech_knowledge.db")

def search_wikipedia(query: str, limit: int = 5) -> str:
    lines = []
    for index, title in enumerate(wikipedia.search(query, results=limit), start=1):
        page = wikipedia.page(title, auto_suggest=False)
        lines.append(f"{index}. {page.title}")
        lines.append(f"   {page.url}")
        lines.append(f"   {page.summary.splitlines()[0]}")
    return "\n".join(lines) if lines else "No results."

def get_variant(product: Product, variant_name: str) -> ProductVariant:
    for variant in product.variants:
        if variant.variant_name.casefold() == variant_name.casefold():
            return variant
    raise ValueError(
        f"Variant '{variant_name}' was not found for {product.main_name}."
    )


def main() -> None:
    # query = " ".join(sys.argv[1:]).strip() or "PlayStation 2 launch price"
    # print(search_wikipedia(query))
    atari2600 = find_product("Atari 2600", DB_FILE)
    nes = find_product("Nintendo Entertainment System", DB_FILE)
    snes = find_product("Super Nintendo Entertainment System", DB_FILE)
    ps1 = find_product("PlayStation", DB_FILE)
    ps2 = find_product("PlayStation 2", DB_FILE)
    ps3 = find_product("PlayStation 3", DB_FILE)
    ps4 = find_product("PlayStation 4", DB_FILE)
    ps5 = find_product("PlayStation 5", DB_FILE)
    macPro = find_product("MacBook Pro", DB_FILE)
    macAir = find_product("MacBook Air", DB_FILE)
    tuf = find_product("ASUS TUF Gaming", DB_FILE)

    if ps3 is None or ps4 is None:
        raise ValueError("PlayStation 4 and PlayStation 5 must exist in the database.")

    score = compare_products(
        # get_variant(atari2600, "Base"),
        # get_variant(nes, "Base"),
        # get_variant(snes, "Base"),
        # get_variant(ps1, "Base"),
        # get_variant(ps2, "Base"),
        # get_variant(ps3, "Base"),
        # get_variant(ps4, "Base"),
        # get_variant(ps5, "Base"),
        # get_variant(macPro, "16-inch i7 16GB/512GB"),
        get_variant(macAir, "13-inch M3 8-core GPU 16GB/512GB"),
        get_variant(tuf, "F15 FX507ZM i7-12700H RTX 3060 16GB/1024GB"),
    )
    print(score)


if __name__ == "__main__":
    main()
