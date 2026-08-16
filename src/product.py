from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(slots=True)
class CpuSpec:
    cores: int | None
    speed: float | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CpuSpec:
        return cls(
            cores=data.get("cores"),
            speed=data.get("speed"),
        )

@dataclass(slots=True)
class GpuSpec:
    cores: int | None
    speed: float | None
    memory: float | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GpuSpec:
        return cls(
            cores=data.get("cores"),
            speed=data.get("speed"),
            memory=data.get("memory"),
        )


@dataclass(slots=True)
class ProductSpecs:
    speed_unit: str | None
    memory_unit: str | None
    cpus: list[CpuSpec]
    gpu: GpuSpec | None
    ram: float | None
    ram_speed: float | None
    audio_memory: float | None
    video_memory: float | None
    storage_gb: float | None
    storage_speed: float | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProductSpecs:
        cpu_data = data.get("cpus", [])
        if not isinstance(cpu_data, list):
            raise ValueError("'specs.cpus' must be an array.")

        gpu_data = data.get("gpu")
        if gpu_data is not None and not isinstance(gpu_data, dict):
            raise ValueError("'specs.gpu' must be an object or null.")

        return cls(
            speed_unit=data.get("speed_unit"),
            memory_unit=data.get("memory_unit"),
            cpus=[
                CpuSpec.from_dict(cpu)
                for cpu in cpu_data
                if isinstance(cpu, dict)
            ],
            gpu=GpuSpec.from_dict(gpu_data) if gpu_data is not None else None,
            ram=data.get("ram"),
            ram_speed=data.get("ram_speed"),
            audio_memory=data.get("audio_memory"),
            video_memory=data.get("video_memory"),
            storage_gb=data.get("storage_gb"),
            storage_speed=data.get("storage_speed"),
        )


@dataclass(slots=True)
class ProductVariant:
    variant_name: str
    release_year: int
    launch_price: float
    specs: ProductSpecs

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProductVariant:
        variant_name = data.get("variant_name")
        if not isinstance(variant_name, str) or not variant_name.strip():
            raise ValueError("'variant_name' must be a non-empty string.")

        release_year = data.get("release_year")

        if isinstance(release_year, bool) or not isinstance(release_year, int):
            raise ValueError("'release_year' must be an integer.")

        launch_price = data.get("launch_price")
        if isinstance(launch_price, bool) or not isinstance(
            launch_price,
            (int, float),
        ):
            raise ValueError("'launch_price' must be a number.")

        specs = data.get("specs")
        if not isinstance(specs, dict):
            raise ValueError("'specs' must be an object.")

        return cls(
            variant_name=variant_name.strip(),
            release_year=release_year,
            launch_price=float(launch_price),
            specs=ProductSpecs.from_dict(specs),
        )


@dataclass(slots=True)
class Product:
    main_name: str
    brand: str
    category: str
    variants: list[ProductVariant]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Product:
        text_fields = {}
        for field_name in ("main_name", "brand", "category"):
            value = data.get(field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"'{field_name}' must be a non-empty string."
                )
            text_fields[field_name] = value.strip()

        variants = data.get("variants")
        if not isinstance(variants, list) or not variants:
            raise ValueError("'variants' must be a non-empty array.")

        if not all(isinstance(variant, dict) for variant in variants):
            raise ValueError("Every variant must be an object.")

        return cls(
            main_name=text_fields["main_name"],
            brand=text_fields["brand"],
            category=text_fields["category"],
            variants=[
                ProductVariant.from_dict(variant)
                for variant in variants
            ],
        )
