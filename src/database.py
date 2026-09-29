import sqlite3

from src.product import (
    AudioSpec,
    CpuSpec,
    GpuSpec,
    MemorySpec,
    Product,
    ProductSpecs,
    ProductVariant,
    StorageSpec,
)


def _find_product_id_in_connection(
    conn: sqlite3.Connection,
    product_name: str,
) -> int | None:
    """Return an exact match, or a single unambiguous name fragment match."""
    normalized_name = product_name.strip()
    exact_match = conn.execute(
        """
        SELECT id
        FROM tech_products
        WHERE main_name = ? COLLATE NOCASE
        """,
        (normalized_name,),
    ).fetchone()
    if exact_match is not None:
        return exact_match[0]

    matches = conn.execute(
        """
        SELECT id
        FROM tech_products
        WHERE main_name LIKE ? COLLATE NOCASE
        """,
        (f"%{normalized_name}%",),
    ).fetchall()
    return matches[0][0] if len(matches) == 1 else None


def find_product(product_name: str, db_file: str) -> Product | None:
    """Return a stored product as a validated Product object."""
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        product_id = _find_product_id_in_connection(conn, product_name)
        if product_id is None:
            return None

        product_row = conn.execute(
            """
            SELECT id, main_name, brand, category
            FROM tech_products
            WHERE id = ?
            """,
            (product_id,),
        ).fetchone()

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
                audio_cores,
                audio_speed,
                audio_ops_per_cycle
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

            memory_rows = conn.execute(
                """
                SELECT id, name, capacity, bandwidth
                FROM tech_variant_memory_sources
                WHERE variant_id = ?
                ORDER BY position
                """,
                (variant_row["id"],),
            ).fetchall()

            memory = []
            for memory_row in memory_rows:
                access_rows = conn.execute(
                    """
                    SELECT accessor
                    FROM tech_variant_memory_access
                    WHERE memory_source_id = ?
                    ORDER BY position
                    """,
                    (memory_row["id"],),
                ).fetchall()
                memory.append(
                    MemorySpec(
                        name=memory_row["name"],
                        capacity=memory_row["capacity"],
                        bandwidth=memory_row["bandwidth"],
                        accessible_by=[row["accessor"] for row in access_rows],
                    )
                )

            storage_rows = conn.execute(
                """
                SELECT name, capacity, bandwidth
                FROM tech_variant_storage_sources
                WHERE variant_id = ?
                ORDER BY position
                """,
                (variant_row["id"],),
            ).fetchall()
            storage = [
                StorageSpec(
                    name=row["name"],
                    capacity=row["capacity"],
                    bandwidth=row["bandwidth"],
                )
                for row in storage_rows
            ]

            gpu = (
                GpuSpec(
                    cores=variant_row["gpu_cores"],
                    speed=variant_row["gpu_speed"],
                    ops_per_cycle=variant_row["gpu_ops_per_cycle"],
                )
                if any(
                    variant_row[field] is not None
                    for field in (
                        "gpu_cores",
                        "gpu_speed",
                        "gpu_ops_per_cycle",
                    )
                )
                else None
            )

            audio = (
                AudioSpec(
                    cores=variant_row["audio_cores"],
                    speed=variant_row["audio_speed"],
                    ops_per_cycle=variant_row["audio_ops_per_cycle"],
                )
                if any(
                    variant_row[field] is not None
                    for field in (
                        "audio_cores",
                        "audio_speed",
                        "audio_ops_per_cycle",
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
                        audio=audio,
                        memory=memory,
                        storage=storage,
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
        return _find_product_id_in_connection(conn, product_name)
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
            audio_cores INTEGER,
            audio_speed REAL,
            audio_ops_per_cycle REAL,
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tech_variant_memory_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variant_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            name TEXT NOT NULL,
            capacity REAL,
            bandwidth REAL,
            UNIQUE(variant_id, position),
            FOREIGN KEY (variant_id)
                REFERENCES tech_variants(id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tech_variant_memory_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_source_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            accessor TEXT NOT NULL CHECK (accessor IN ('cpu', 'gpu', 'audio')),
            UNIQUE(memory_source_id, position),
            UNIQUE(memory_source_id, accessor),
            FOREIGN KEY (memory_source_id)
                REFERENCES tech_variant_memory_sources(id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tech_variant_storage_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variant_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            name TEXT NOT NULL,
            capacity REAL NOT NULL,
            bandwidth REAL NOT NULL,
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
                    audio = specs.audio
                    values = (
                        variant.variant_name,
                        variant.release_year,
                        variant.launch_price,
                        specs.speed_unit,
                        specs.memory_unit,
                        gpu.cores if gpu else None,
                        gpu.speed if gpu else None,
                        gpu.ops_per_cycle if gpu else None,
                        audio.cores if audio else None,
                        audio.speed if audio else None,
                        audio.ops_per_cycle if audio else None,
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
                                audio_cores,
                                audio_speed,
                                audio_ops_per_cycle
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                                audio_cores = ?,
                                audio_speed = ?,
                                audio_ops_per_cycle = ?
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

                    conn.execute(
                        "DELETE FROM tech_variant_memory_sources WHERE variant_id = ?",
                        (variant_id,),
                    )
                    for position, memory_source in enumerate(specs.memory):
                        cursor = conn.execute(
                            """
                            INSERT INTO tech_variant_memory_sources (
                                variant_id,
                                position,
                                name,
                                capacity,
                                bandwidth
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                variant_id,
                                position,
                                memory_source.name,
                                memory_source.capacity,
                                memory_source.bandwidth,
                            ),
                        )
                        memory_source_id = cursor.lastrowid
                        conn.executemany(
                            """
                            INSERT INTO tech_variant_memory_access (
                                memory_source_id,
                                position,
                                accessor
                            )
                            VALUES (?, ?, ?)
                            """,
                            [
                                (memory_source_id, access_position, accessor)
                                for access_position, accessor in enumerate(
                                    memory_source.accessible_by
                                )
                            ],
                        )

                    conn.execute(
                        "DELETE FROM tech_variant_storage_sources WHERE variant_id = ?",
                        (variant_id,),
                    )
                    conn.executemany(
                        """
                        INSERT INTO tech_variant_storage_sources (
                            variant_id,
                            position,
                            name,
                            capacity,
                            bandwidth
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        [
                            (
                                variant_id,
                                position,
                                storage_source.name,
                                storage_source.capacity,
                                storage_source.bandwidth,
                            )
                            for position, storage_source in enumerate(specs.storage)
                        ],
                    )

        return counts
    finally:
        conn.close()
