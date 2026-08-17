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
            speed_unit TEXT,
            memory_unit TEXT,
            gpu_cores INTEGER,
            gpu_speed REAL,
            gpu_memory REAL,
            ram REAL,
            ram_speed REAL,
            audio_memory REAL,
            video_memory REAL,
            storage_gb REAL,
            storage_speed REAL,
            UNIQUE(product_id, variant_name),
            FOREIGN KEY (product_id)
                REFERENCES tech_products(id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tech_variant_cpus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variant_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            cores INTEGER,
            speed REAL,
            UNIQUE(variant_id, position),
            FOREIGN KEY (variant_id)
                REFERENCES tech_variants(id)
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
                    row = conn.execute(
                        """
                        SELECT id
                        FROM tech_variants
                        WHERE product_id = ?
                          AND variant_name = ? COLLATE NOCASE
                        """,
                        (product_id, variant.variant_name),
                    ).fetchone()

                    specs = variant.specs
                    gpu = specs.gpu
                    values = (
                        variant.variant_name,
                        variant.release_year,
                        variant.launch_price,
                        specs.speed_unit,
                        specs.memory_unit,
                        gpu.cores if gpu else None,
                        gpu.speed if gpu else None,
                        gpu.memory if gpu else None,
                        specs.ram,
                        specs.ram_speed,
                        specs.audio_memory,
                        specs.video_memory,
                        specs.storage_gb,
                        specs.storage_speed,
                    )

                    if row is None:
                        cursor = conn.execute(
                            """
                            INSERT INTO tech_variants (
                                product_id,
                                variant_name,
                                release_year,
                                launch_price,
                                speed_unit,
                                memory_unit,
                                gpu_cores,
                                gpu_speed,
                                gpu_memory,
                                ram,
                                ram_speed,
                                audio_memory,
                                video_memory,
                                storage_gb,
                                storage_speed
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (product_id, *values),
                        )
                        variant_id = cursor.lastrowid
                        counts["variants_inserted"] += 1
                    else:
                        variant_id = row[0]
                        conn.execute(
                            """
                            UPDATE tech_variants
                            SET variant_name = ?,
                                release_year = ?,
                                launch_price = ?,
                                speed_unit = ?,
                                memory_unit = ?,
                                gpu_cores = ?,
                                gpu_speed = ?,
                                gpu_memory = ?,
                                ram = ?,
                                ram_speed = ?,
                                audio_memory = ?,
                                video_memory = ?,
                                storage_gb = ?,
                                storage_speed = ?
                            WHERE id = ?
                            """,
                            (*values, variant_id),
                        )
                        counts["variants_updated"] += 1

                    conn.execute(
                        "DELETE FROM tech_variant_cpus WHERE variant_id = ?",
                        (variant_id,),
                    )
                    conn.executemany(
                        """
                        INSERT INTO tech_variant_cpus (
                            variant_id,
                            position,
                            cores,
                            speed
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        [
                            (variant_id, position, cpu.cores, cpu.speed)
                            for position, cpu in enumerate(specs.cpus)
                        ],
                    )

        return counts
    finally:
        conn.close()
