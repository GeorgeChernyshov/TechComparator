import sys
from pathlib import Path

import wikipedia

from src.comparison import compare_products
from src.database import find_product
from src.product import Product, ProductVariant

DB_FILE = Path(__file__).resolve().with_name("tech_knowledge.db")
_VARIANT_PRODUCT_NAMES: dict[int, str] = {}


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
            _VARIANT_PRODUCT_NAMES[id(variant)] = product.main_name
            return variant
    raise ValueError(
        f"Variant '{variant_name}' was not found for {product.main_name}."
    )


def compare_against(
    variant_a: ProductVariant,
    variants_b: list[ProductVariant],
) -> list[float]:
    """Compare one reference variant against every variant in the list."""
    scores = []
    for variant_b in variants_b:
        score = compare_products(variant_a, variant_b)
        product_name = _VARIANT_PRODUCT_NAMES[id(variant_b)]
        print(f"{product_name}:{variant_b.variant_name}:{score}")
        scores.append(score)
    return scores


def main() -> None:
    # query = " ".join(sys.argv[1:]).strip() or "PlayStation 2 launch price"
    # print(search_wikipedia(query))
    ps2 = find_product("PlayStation 2", DB_FILE)
    ps3 = find_product("PlayStation 3", DB_FILE)
    ps4 = find_product("PlayStation 4", DB_FILE)
    ps5 = find_product("PlayStation 5", DB_FILE)
    ps1 = find_product("PlayStation", DB_FILE)
    snes = find_product("Super Nintendo Entertainment System", DB_FILE)
    nes = find_product("Nintendo Entertainment System", DB_FILE)
    atari2600 = find_product("Atari 2600", DB_FILE)
    macPro = find_product("MacBook Pro", DB_FILE)
    macAir = find_product("MacBook Air", DB_FILE)
    tuf = find_product("ASUS TUF Gaming", DB_FILE)
    channelF = find_product("Fairchild Channel F", DB_FILE)
    rcaStudio2 = find_product("RCA Studio II", DB_FILE)
    atari5200 = find_product("Atari 5200", DB_FILE)
    colecoVision = find_product("ColecoVision", DB_FILE)
    odyssey2 = find_product("Magnavox Odyssey 2", DB_FILE)
    vectrex = find_product("Vectrex", DB_FILE)
    arcadia2001 = find_product("Emerson Arcadia 2001", DB_FILE)
    astrocade = find_product("Bally Astrocade", DB_FILE)
    intellivision = find_product("Mattel Intellivision", DB_FILE)
    microvision = find_product("Milton Bradley Microvision", DB_FILE)
    sg1000 = find_product("SG-1000", DB_FILE)
    masterSystem = find_product("Sega Master System", DB_FILE)
    atari7800 = find_product("Atari 7800", DB_FILE)
    atariXegs = find_product("Atari XEGS", DB_FILE)
    turboGrafx16 = find_product("TurboGrafx-16", DB_FILE)
    genesis = find_product("Sega Genesis", DB_FILE)
    neoGeo = find_product("Neo Geo", DB_FILE)
    cdi = find_product("CD-i", DB_FILE)
    gameBoy = find_product("Game Boy", DB_FILE)
    atariLynx = find_product("Atari Lynx", DB_FILE)
    gameGear = find_product("Sega Game Gear", DB_FILE)
    turboExpress = find_product("TurboExpress", DB_FILE)
    n64 = find_product("Nintendo 64", DB_FILE)
    saturn = find_product("Sega Saturn", DB_FILE)
    threeDo = find_product("3DO", DB_FILE)
    jaguar = find_product("Atari Jaguar", DB_FILE)
    pcFx = find_product("PC-FX", DB_FILE)
    gameBoyColor = find_product("Game Boy Color", DB_FILE)
    neoGeoPocket = find_product("Neo Geo Pocket", DB_FILE)
    genesisNomad = find_product("Sega Genesis Nomad", DB_FILE)
    dreamcast = find_product("Sega Dreamcast", DB_FILE)
    gameCube = find_product("Nintendo GameCube", DB_FILE)
    xbox = find_product("Xbox", DB_FILE)
    gameBoyAdvance = find_product("Game Boy Advance", DB_FILE)
    wonderSwan = find_product("WonderSwan", DB_FILE)
    nGage = find_product("N-Gage", DB_FILE)
    wii = find_product("Nintendo Wii", DB_FILE)
    xbox360 = find_product("Xbox 360", DB_FILE)
    nintendoDs = find_product("Nintendo DS", DB_FILE)
    psp = find_product("PlayStation Portable", DB_FILE)
    wiiU = find_product("Wii U", DB_FILE)
    switch = find_product("Switch", DB_FILE)
    xboxOne = find_product("Xbox One", DB_FILE)
    threeDs = find_product("Nintendo 3DS", DB_FILE)
    psVita = find_product("PlayStation Vita", DB_FILE)
    xboxSeries = find_product("Xbox Series X/S", DB_FILE)
    switch2 = find_product("Switch 2", DB_FILE)

    compare_against(
        # get_variant(ps2, "Base"),
        # get_variant(ps3, "Base"),
        # get_variant(ps4, "Base"),
        # get_variant(ps4, "Pro"),
        # get_variant(ps5, "Base"),
        # get_variant(ps5, "Pro"),
        # get_variant(ps1, "Base"),
        # get_variant(snes, "Base"),
        # get_variant(nes, "Base"),
        # get_variant(nes, "Famicom Disk System"),
        # get_variant(atari2600, "Base"),
        # get_variant(macPro, "16-inch i7 16GB/512GB"),
        # get_variant(macAir, "13-inch M3 8-core GPU 16GB/256GB"),
        # get_variant(macAir, "13-inch M3 8-core GPU 16GB/512GB"),
        # get_variant(macAir, "13-inch M4 10-core GPU 16GB/512GB"),
        # get_variant(macAir, "13-inch M5 8-core GPU 16GB/512GB"),
        # get_variant(tuf, "F15 FX507ZM i7-12700H RTX 3060 16GB/512GB"),
        get_variant(tuf, "F15 FX507ZM i7-12700H RTX 3060 16GB/1024GB"),
        # get_variant(tuf, "Custom"),
        # get_variant(tuf, "F16 FX608LPG-BB94 Ultra 9 290HX Plus RTX 5070 16GB/1024GB"),
        # get_variant(channelF, "Base"),
        # get_variant(rcaStudio2, "Base"),
        # get_variant(atari5200, "Base"),
        # get_variant(colecoVision, "Base"),
        # get_variant(odyssey2, "Base"),
        # get_variant(vectrex, "Base"),
        # get_variant(arcadia2001, "Base"),
        # get_variant(astrocade, "Base"),
        # get_variant(intellivision, "Base"),
        # get_variant(microvision, "Base"),
        # get_variant(sg1000, "Base"),
        # get_variant(masterSystem, "Base"),
        # get_variant(atari7800, "Base"),
        # get_variant(atariXegs, "Base"),
        # get_variant(turboGrafx16, "Base"),
        # get_variant(genesis, "Base"),
        # get_variant(genesis, "Sega CD"),
        # get_variant(genesis, "Sega 32X"),
        # get_variant(genesis, "Sega CD + 32X"),
        # get_variant(neoGeo, "Base"),
        # get_variant(cdi, "Base"),
        # get_variant(gameBoy, "Base"),
        # get_variant(atariLynx, "Base"),
        # get_variant(gameGear, "Base"),
        # get_variant(turboExpress, "Base"),
        # get_variant(n64, "Base"),
        # get_variant(saturn, "Base"),
        # get_variant(threeDo, "Base"),
        # get_variant(jaguar, "Base"),
        # get_variant(pcFx, "Base"),
        # get_variant(gameBoyColor, "Base"),
        # get_variant(neoGeoPocket, "Base"),
        # get_variant(genesisNomad, "Base"),
        # get_variant(dreamcast, "Base"),
        # get_variant(gameCube, "Base"),
        # get_variant(xbox, "Base"),
        # get_variant(gameBoyAdvance, "Base"),
        # get_variant(wonderSwan, "Base"),
        # get_variant(nGage, "Base"),
        # get_variant(wii, "Base"),
        # get_variant(xbox360, "20 GB"),
        # get_variant(nintendoDs, "Base"),
        # get_variant(nintendoDs, "DSi"),
        # get_variant(psp, "Base"),
        # get_variant(psp, "PSP-2000"),
        # get_variant(wiiU, "Base"),
        # get_variant(switch, "Base"),
        # get_variant(xboxOne, "Base"),
        # get_variant(xboxOne, "One S"),
        # get_variant(xboxOne, "One X"),
        # get_variant(threeDs, "Base"),
        # get_variant(threeDs, "New"),
        # get_variant(psVita, "Base"),
        # get_variant(xboxSeries, "Series S"),
        # get_variant(xboxSeries, "Series X"),
        # get_variant(switch2, "Base"),
        # get_variant(macAir, "13-inch M3 8-core GPU 16GB/512GB"),
        # get_variant(macAir, "13-inch M4 10-core GPU 16GB/512GB"),
        # get_variant(macAir, "13-inch M5 8-core GPU 16GB/512GB"),
        [
            # get_variant(ps2, "Base"),
            # get_variant(ps3, "Base"),
            # get_variant(ps4, "Base"),
            # get_variant(ps4, "Pro"),
            # get_variant(ps5, "Base"),
            # get_variant(ps5, "Pro"),
            # get_variant(ps1, "Base"),
            # get_variant(snes, "Base"),
            # get_variant(nes, "Base"),
            # get_variant(nes, "Famicom Disk System"),
            # get_variant(atari2600, "Base"),
            # get_variant(macPro, "16-inch i7 16GB/512GB"),
            # get_variant(macAir, "13-inch M3 8-core GPU 16GB/256GB"),
            # get_variant(macAir, "13-inch M3 8-core GPU 16GB/512GB"),
            # get_variant(macAir, "13-inch M4 10-core GPU 16GB/512GB"),
            # get_variant(macAir, "13-inch M5 8-core GPU 16GB/512GB"),
            # get_variant(tuf, "F15 FX507ZM i7-12700H RTX 3060 16GB/512GB"),
            # get_variant(tuf, "F15 FX507ZM i7-12700H RTX 3060 16GB/1024GB"),
            get_variant(tuf, "Custom"),
            get_variant(tuf, "F16 FX608LPG-BB94 Ultra 9 290HX Plus RTX 5070 16GB/1024GB"),
            # get_variant(channelF, "Base"),
            # get_variant(rcaStudio2, "Base"),
            # get_variant(atari5200, "Base"),
            # get_variant(colecoVision, "Base"),
            # get_variant(odyssey2, "Base"),
            # get_variant(vectrex, "Base"),
            # get_variant(arcadia2001, "Base"),
            # get_variant(astrocade, "Base"),
            # get_variant(intellivision, "Base"),
            # get_variant(microvision, "Base"),
            # get_variant(sg1000, "Base"),
            # get_variant(masterSystem, "Base"),
            # get_variant(atari7800, "Base"),
            # get_variant(atariXegs, "Base"),
            # get_variant(turboGrafx16, "Base"),
            # get_variant(genesis, "Base"),
            # get_variant(genesis, "Sega CD"),
            # get_variant(genesis, "Sega 32X"),
            # get_variant(genesis, "Sega CD + 32X"),
            # get_variant(neoGeo, "Base"),
            # get_variant(cdi, "Base"),
            # get_variant(gameBoy, "Base"),
            # get_variant(atariLynx, "Base"),
            # get_variant(gameGear, "Base"),
            # get_variant(turboExpress, "Base"),
            # get_variant(n64, "Base"),
            # get_variant(saturn, "Base"),
            # get_variant(threeDo, "Base"),
            # get_variant(jaguar, "Base"),
            # get_variant(pcFx, "Base"),
            # get_variant(gameBoyColor, "Base"),
            # get_variant(neoGeoPocket, "Base"),
            # get_variant(genesisNomad, "Base"),
            # get_variant(dreamcast, "Base"),
            # get_variant(gameCube, "Base"),
            # get_variant(xbox, "Base"),
            # get_variant(gameBoyAdvance, "Base"),
            # get_variant(wonderSwan, "Base"),
            # get_variant(nGage, "Base"),
            # get_variant(wii, "Base"),
            # get_variant(xbox360, "20 GB"),
            # get_variant(nintendoDs, "DSi"),
            # get_variant(nintendoDs, "Base"),
            # get_variant(psp, "Base"),
            # get_variant(psp, "PSP-2000"),
            # get_variant(wiiU, "Base"),
            # get_variant(switch, "Base"),
            # get_variant(xboxOne, "Base"),
            # get_variant(xboxOne, "One S"),
            # get_variant(xboxOne, "One X"),
            # # get_variant(threeDs, "Base"),
            # # get_variant(threeDs, "New"),
            # # get_variant(psVita, "Base"),
            # get_variant(xboxSeries, "Series S"),
            # get_variant(xboxSeries, "Series X"),
            # get_variant(switch2, "Base"),
        ],
    )


if __name__ == "__main__":
    main()
