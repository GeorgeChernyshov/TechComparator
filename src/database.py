import sqlite3

from src.product import (
    CpuSpec,
    GpuSpec,
    Product,
    ProductSpecs,
    ProductVariant,
)

def find_product(product_name: str, db_file: str) -> Product | None:
    """Return a stored product as a validated Product object."""
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        product_row = conn.execute(
            """
            SELECT id, main_name, brand, category
            FROM tech_products
            WHERE main_name = ? COLLATE NOCASE
            """,
            (product_name.strip(),),
        ).fetchone()

        if product_row is None:
            return None

        variants: list[ProductVariant] = []

        variant_rows = conn.execute(
            """
            SELECT
                id,
                variant_name,
                release_year,
                launch_price,
                speed_unit,
                memory_unit,
                gpu_cores,
                gpu_speed,
                gpu_ops_per_cycle,
                gpu_memory_bandwidth,
                gpu_memory,
                ram,
                ram_bandwidth,
                audio_memory,
                video_memory,
                storage_gb,
                storage_speed
            FROM tech_variants
            WHERE product_id = ?
            ORDER BY id
            """,
            (product_row["id"],),
        ).fetchall()

        for variant_row in variant_rows:
            cpu_rows = conn.execute(
                """
                SELECT cores, speed, cpu_ops_per_cycle
                FROM tech_variant_cpus
                WHERE variant_id = ?
                ORDER BY position
                """,
                (variant_row["id"],),
            ).fetchall()

            gpu = (
                GpuSpec(
                    cores=variant_row["gpu_cores"],
                    speed=variant_row["gpu_speed"],
                    ops_per_cycle=variant_row["gpu_ops_per_cycle"],
                    memory_bandwidth=variant_row["gpu_memory_bandwidth"],
                    memory=variant_row["gpu_memory"],
                )
                if any(
                    variant_row[field] is not None
                    for field in (
                        "gpu_cores",
                        "gpu_speed",
                        "gpu_ops_per_cycle",
                        "gpu_memory_bandwidth",
                        "gpu_memory",
                    )
                )
                else None
            )

            variants.append(
                ProductVariant(
                    variant_name=variant_row["variant_name"],
                    release_year=variant_row["release_year"],
                    launch_price=variant_row["launch_price"],
                    specs=ProductSpecs(
                        speed_unit=variant_row["speed_unit"],
                        memory_unit=variant_row["memory_unit"],
                        cpus=[
                            CpuSpec(
                                cores=row["cores"],
                                speed=row["speed"],
                                ops_per_cycle=row["cpu_ops_per_cycle"],
                            )
                            for row in cpu_rows
                        ],
                        gpu=gpu,
                        ram=variant_row["ram"],
                        ram_bandwidth=variant_row["ram_bandwidth"],
                        audio_memory=variant_row["audio_memory"],
                        video_memory=variant_row["video_memory"],
                        storage_gb=variant_row["storage_gb"],
                        storage_speed=variant_row["storage_speed"],
                    ),
                )
            )

        return Product(
            main_name=product_row["main_name"],
            brand=product_row["brand"],
            category=product_row["category"],
            variants=variants,
        )
    finally:
        conn.close()

def find_product_id(product_name: str, db_file: str) -> int | None:
    """Return the database ID for a product, if it exists."""
    conn = sqlite3.connect(db_file)
    try:
        row = conn.execute(
            """
            SELECT id
            FROM tech_products
            WHERE main_name = ? COLLATE NOCASE
            """,
            (product_name.strip(),),
        ).fetchone()
        return row[0] if row is not None else None
    finally:
        conn.close()

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
            gpu_ops_per_cycle REAL,
            gpu_memory_bandwidth REAL,
            gpu_memory REAL,
            ram REAL,
            ram_bandwidth REAL,
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
            cpu_ops_per_cycle REAL,
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
                        gpu.ops_per_cycle if gpu else None,
                        gpu.memory_bandwidth if gpu else None,
                        gpu.memory if gpu else None,
                        specs.ram,
                        specs.ram_bandwidth,
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
                                gpu_ops_per_cycle,
                                gpu_memory_bandwidth,
                                gpu_memory,
                                ram,
                                ram_bandwidth,
                                audio_memory,
                                video_memory,
                                storage_gb,
                                storage_speed
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                                gpu_ops_per_cycle = ?,
                                gpu_memory_bandwidth = ?,
                                gpu_memory = ?,
                                ram = ?,
                                ram_bandwidth = ?,
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
                            speed,
                            cpu_ops_per_cycle
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        [
                            (
                                variant_id,
                                position,
                                cpu.cores,
                                cpu.speed,
                                cpu.ops_per_cycle,
                            )
                            for position, cpu in enumerate(specs.cpus)
                        ],
                    )

        return counts
    finally:
        conn.close()
