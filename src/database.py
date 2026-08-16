from dataclasses import asdict
import json
import sqlite3

from src.product import Product


def init_agent_database(db_file: str) -> None:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tech_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            main_name TEXT NOT NULL COLLATE NOCASE UNIQUE,
            brand TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tech_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            variant_name TEXT NOT NULL COLLATE NOCASE,
            release_year INTEGER NOT NULL,
            launch_price REAL NOT NULL,
            spec_json TEXT NOT NULL CHECK(json_valid(spec_json)),
            UNIQUE(product_id, variant_name),
            FOREIGN KEY (product_id)
                REFERENCES tech_products(id)
                ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()
    print("[Log] SQLite database successfully initialized.")

def save_research_results(
    products: list[Product],
    db_file: str,
) -> dict[str, int]:
    counts = {
        "products_inserted": 0,
        "products_updated": 0,
        "variants_inserted": 0,
        "variants_updated": 0,
    }

    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        with conn:
            for product in products:
                row = conn.execute(
                    """
                    SELECT id
                    FROM tech_products
                    WHERE main_name = ? COLLATE NOCASE
                    """,
                    (product.main_name,),
                ).fetchone()

                if row is None:
                    cursor = conn.execute(
                        """
                        INSERT INTO tech_products (main_name, brand, category)
                        VALUES (?, ?, ?)
                        """,
                        (product.main_name, product.brand, product.category),
                    )
                    product_id = cursor.lastrowid
                    counts["products_inserted"] += 1
                else:
                    product_id = row[0]
                    conn.execute(
                        """
                        UPDATE tech_products
                        SET main_name = ?, brand = ?, category = ?
                        WHERE id = ?
                        """,
                        (
                            product.main_name,
                            product.brand,
                            product.category,
                            product_id,
                        ),
                    )
                    counts["products_updated"] += 1

                for variant in product.variants:
                    spec_json = json.dumps(
                        asdict(variant.specs),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    row = conn.execute(
                        """
                        SELECT id
                        FROM tech_variants
                        WHERE product_id = ?
                          AND variant_name = ? COLLATE NOCASE
                        """,
                        (product_id, variant.variant_name),
                    ).fetchone()

                    values = (
                        variant.variant_name,
                        variant.release_year,
                        variant.launch_price,
                        spec_json,
                    )

                    if row is None:
                        conn.execute(
                            """
                            INSERT INTO tech_variants (
                                product_id,
                                variant_name,
                                release_year,
                                launch_price,
                                spec_json
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (product_id, *values),
                        )
                        counts["variants_inserted"] += 1
                    else:
                        conn.execute(
                            """
                            UPDATE tech_variants
                            SET variant_name = ?,
                                release_year = ?,
                                launch_price = ?,
                                spec_json = ?
                            WHERE id = ?
                            """,
                            (*values, row[0]),
                        )
                        counts["variants_updated"] += 1

        return counts
    finally:
        conn.close()
