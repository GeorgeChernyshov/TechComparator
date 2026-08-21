from __future__ import annotations

import json
from dataclasses import asdict

from src.product import ProductSpecs, ProductVariant

def compare_speed_units(unit_a: str, unit_b: str) -> float:
    units = ["Hz", "kHz", "MHz", "GHz", "THz"]

    try:
        index_a = units.index(unit_a)
        index_b = units.index(unit_b)
    except ValueError as error:
        raise ValueError(f"Unsupported speed unit: {error}") from error

    return 1000.0 ** (index_b - index_a)

def compare_memory_units(unit_a: str, unit_b: str) -> float:
    units = ["bytes", "KB", "MB", "GB", "TB"]

    try:
        index_a = units.index(unit_a)
        index_b = units.index(unit_b)
    except ValueError as error:
        raise ValueError(f"Unsupported memory unit: {error}") from error

    return 1000.0 ** (index_b - index_a)

def compare_products(
    variant_a: ProductVariant,
    variant_b: ProductVariant,
) -> float:
    """Return the raw directional product of numeric A-spec/B-spec ratios."""
    try:
        specs_a = variant_a.specs
        specs_b = variant_b.specs
        score = 1.0

        speed_unit = compare_speed_units(
            specs_a.speed_unit,
            specs_b.speed_unit
        )

        cpu_a = sum(
            cpu.cores * cpu.speed * cpu.ops_per_cycle
            for cpu in specs_a.cpus
        )

        cpu_b = sum(
            cpu.cores * cpu.speed * cpu.ops_per_cycle
            for cpu in specs_b.cpus
        ) * speed_unit

        print(f"cpu_a {cpu_a}")
        print(f"cpu_b {cpu_b}")

        memory_unit = compare_memory_units(
            specs_a.memory_unit,
            specs_b.memory_unit
        )

        if (specs_a.gpu is not None):
            gpu_a = (
                (specs_a.gpu.cores or 1) 
                * specs_a.gpu.speed 
                * (specs_a.gpu.ops_per_cycle or 1)
                / 40
            )

            print(f"gpu_a {gpu_a}")

            ram_a = specs_a.ram + (specs_a.audio_memory or 0)
            
            if (specs_a.gpu.memory is not None):
                cpu_wm_a = (
                    cpu_a 
                    * ram_a 
                    * specs_a.ram_bandwidth
                )

                gpu_wm_a = (
                    gpu_a
                    * specs_a.gpu.memory
                    * specs_a.gpu.memory_bandwidth
                )

                total_a = cpu_wm_a + gpu_wm_a
            else:
                #assuming 3/1 memory split
                unified_a = (cpu_a * 3/4) + (gpu_a / 4)

                total_a = (
                    unified_a 
                    * ram_a
                    * specs_a.ram_bandwidth
                )
        else:
            ram_a = (
                specs_a.ram 
                + (specs_a.audio_memory or 0)
                + (specs_a.video_memory or 0)
            )

            total_a = (
                cpu_a 
                * ram_a
                * specs_a.ram_bandwidth
            )
        
        if (specs_b.gpu is not None):
            gpu_b = (
                (specs_b.gpu.cores or 1) 
                * specs_b.gpu.speed 
                * speed_unit
                * (specs_b.gpu.ops_per_cycle or 1) 
                / 40
            )

            print(f"gpu_b {gpu_b}")

            ram_b = specs_b.ram + (specs_b.audio_memory or 0)

            if (specs_b.gpu.memory is not None):
                cpu_wm_b = (
                    cpu_b 
                    * ram_b 
                    * memory_unit
                    * specs_b.ram_bandwidth
                    * memory_unit
                )

                gpu_wm_b = (
                    gpu_b
                    * specs_b.gpu.memory
                    * memory_unit
                    * specs_b.gpu.memory_bandwidth
                    * memory_unit
                )

                total_b = cpu_wm_b + gpu_wm_b
            else:
                #assuming 3/1 memory split
                unified_b = (cpu_b * 3/4) + (gpu_b / 4)

                total_b = (
                    unified_b 
                    * ram_b
                    * memory_unit
                    * specs_b.ram_bandwidth
                    * memory_unit
                )
        else:
            ram_b = (
                specs_b.ram 
                + (specs_b.audio_memory or 0)
                + (specs_b.video_memory or 0)
            )

            total_b = (
                cpu_b 
                * ram_b
                * memory_unit
                * specs_b.ram_bandwidth
                * memory_unit
            )

        print(f"total_a {total_a}")
        print(f"total_b {total_b}")
        
        score = total_b / total_a

        if specs_a.storage_gb is None and specs_b.storage_gb is not None:
            storage_diff = 10
        elif specs_a.storage_gb is not None and specs_b.storage_gb is None:
            storage_diff = 0.1
        elif specs_a.storage_gb is None and specs_b.storage_gb is None:
            storage_diff = 1
        else:
            storage_diff = specs_b.storage_gb / specs_a.storage_gb

        if specs_a.storage_speed is None and specs_b.storage_speed is not None:
            storage_speed_diff = 10
        elif specs_a.storage_speed is not None and specs_b.storage_speed is None:
            storage_speed_diff = 0.1
        elif specs_a.storage_speed is None and specs_b.storage_speed is None:
            storage_speed_diff = 1
        else:
            storage_speed_diff = (
                specs_b.storage_speed 
                * speed_unit
                / specs_a.storage_speed
            )

        print(f"storage_diff {storage_diff}")
        print(f"storage_speed_diff {storage_speed_diff}")
        
        score *= storage_diff
        score *= storage_speed_diff

        return score
    except Exception as err:
        print(f"Something went wrong: {err}")
        print(f"Product A: {json.dumps(asdict(variant_a))}")
        print(f"Product B: {json.dumps(asdict(variant_b))}")
