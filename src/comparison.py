from __future__ import annotations

import json
from src.product import ProductVariant
from dataclasses import asdict

GPU_DECREASE = 2
AUDIO_DECREASE = 2

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
    """Return the raw directional product of numeric B-spec/A-spec ratios."""
    try:
        specs_a = variant_a.specs
        specs_b = variant_b.specs

        speed_unit = compare_speed_units(
            specs_a.speed_unit,
            specs_b.speed_unit
        )

        cpu_a = sum(
            (cpu.cores ** 0.8) * cpu.speed * cpu.ops_per_cycle
            for cpu in specs_a.cpus
        )

        cpu_b = sum(
            (cpu.cores ** 0.8) * cpu.speed * cpu.ops_per_cycle
            for cpu in specs_b.cpus
        ) * speed_unit

        memory_unit = compare_memory_units(
            specs_a.memory_unit,
            specs_b.memory_unit
        )

        cpu_memory_a = 0
        gpu_memory_a = 0
        shared_memory_a = 0
        audio_memory_a = 0
        storage_a = 0

        for mem in specs_a.memory:
            if "gpu" in mem.accessible_by and "cpu" in mem.accessible_by:
                shared_memory_a += (
                    ((mem.capacity / 2) ** 0.5)
                    * (mem.bandwidth ** 0.7)
                )
            elif "cpu" in mem.accessible_by:
                cpu_memory_a += (
                    (mem.capacity ** 0.5)
                    * (mem.bandwidth ** 0.7)
                )
            elif "gpu" in mem.accessible_by:
                gpu_memory_a += (
                    (mem.capacity ** 0.5)
                    * (mem.bandwidth ** 0.7)
                )
            elif "audio" in mem.accessible_by:
                audio_memory_a += (
                    (mem.capacity ** 0.5)
                    * (mem.bandwidth ** 0.7)
                )

        for storage in specs_a.storage:
            storage_a += (
                (storage.capacity ** 0.5)
                * (storage.bandwidth ** 0.7)
            )

        cpu_memory_b = 0
        gpu_memory_b = 0
        shared_memory_b = 0
        audio_memory_b = 0
        storage_b = 0

        for mem in specs_b.memory:
            if "gpu" in mem.accessible_by and "cpu" in mem.accessible_by:
                shared_memory_b += (
                    (((mem.capacity / 2) * memory_unit) ** 0.5)
                    * ((mem.bandwidth * memory_unit) ** 0.7)
                )
            elif "cpu" in mem.accessible_by:
                cpu_memory_b += (
                    ((mem.capacity * memory_unit) ** 0.5)
                    * ((mem.bandwidth * memory_unit) ** 0.7)
                )
            elif "gpu" in mem.accessible_by:
                gpu_memory_b += (
                    ((mem.capacity * memory_unit) ** 0.5)
                    * ((mem.bandwidth * memory_unit) ** 0.7)
                )
            elif "audio" in mem.accessible_by:
                audio_memory_b += (
                    ((mem.capacity * memory_unit) ** 0.5)
                    * ((mem.bandwidth * memory_unit) ** 0.7)
                )

        for storage in specs_b.storage:
            storage_b += (
                ((storage.capacity * memory_unit) ** 0.5)
                * ((storage.bandwidth * memory_unit) ** 0.7)
            )

        cpu_wm_a = cpu_a * (cpu_memory_a + shared_memory_a)
        gpu_wm_a = 0
        audio_wm_a = 0

        if (specs_a.gpu is not None):
            gpu_a = (
                (specs_a.gpu.cores ** 0.8)
                * specs_a.gpu.speed
                * (specs_a.gpu.ops_per_cycle or 1)
                / GPU_DECREASE
            )

            gpu_wm_a = gpu_a * (gpu_memory_a + shared_memory_a)

        if (specs_a.audio is not None):
            audio_a = (
                (specs_a.audio.cores ** 0.8)
                * specs_a.audio.speed
                * (specs_a.audio.ops_per_cycle or 1)
                / AUDIO_DECREASE
            )

            audio_wm_a += audio_a * audio_memory_a

        secondary_wm_a = gpu_wm_a if specs_a.gpu is not None else (cpu_wm_a / 4)
        total_a = (
            cpu_wm_a * (secondary_wm_a + audio_wm_a) * storage_a
        ) ** 0.5

        cpu_wm_b = cpu_b * (cpu_memory_b + shared_memory_b)
        gpu_wm_b = 0
        audio_wm_b = 0

        if (specs_b.gpu is not None):
            gpu_b = (
                (specs_b.gpu.cores ** 0.8)
                * specs_b.gpu.speed
                * speed_unit
                * (specs_b.gpu.ops_per_cycle or 1)
                / GPU_DECREASE
            )

            gpu_wm_b = gpu_b * (gpu_memory_b + shared_memory_b)

        if (specs_b.audio is not None):
            audio_b = (
                (specs_b.audio.cores ** 0.8)
                * specs_b.audio.speed
                * speed_unit
                * (specs_b.audio.ops_per_cycle or 1)
                / AUDIO_DECREASE
            )

            audio_wm_b = audio_b * audio_memory_b

        secondary_wm_b = gpu_wm_b if specs_b.gpu is not None else (cpu_wm_b / 4)
        total_b = (
            cpu_wm_b * (secondary_wm_b + audio_wm_b) * storage_b
        ) ** 0.5

        return total_b / total_a
    except Exception as err:
        print(f"Something went wrong: {err}")
        print(f"Product A: {json.dumps(asdict(variant_a))}")
        print(f"Product B: {json.dumps(asdict(variant_b))}")
