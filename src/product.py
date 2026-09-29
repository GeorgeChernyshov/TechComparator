from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(slots=True)
class CpuSpec:
    cores: int | None
    speed: float | None
    ops_per_cycle: float | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CpuSpec:
        return cls(
            cores=data.get("cores"),
            speed=data.get("speed"),
            ops_per_cycle=data.get("ops_per_cycle"),
        )

@dataclass(slots=True)
class GpuSpec:
    cores: int | None
    speed: float | None
    ops_per_cycle: float | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GpuSpec:
        return cls(
            cores=data.get("cores"),
            speed=data.get("speed"),
            ops_per_cycle=data.get("ops_per_cycle"),
        )


@dataclass(slots=True)
class AudioSpec:
    cores: int | None
    speed: float | None
    ops_per_cycle: float | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AudioSpec:
        return cls(
            cores=data.get("cores"),
            speed=data.get("speed"),
            ops_per_cycle=data.get("ops_per_cycle"),
        )


@dataclass(slots=True)
class MemorySpec:
    name: str
    capacity: float | None
    bandwidth: float | None
    accessible_by: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemorySpec:
        expected_fields = {"name", "capacity", "bandwidth", "accessible_by"}
        if set(data) != expected_fields:
            raise ValueError(
                "Every memory source must contain exactly: "
                "'name', 'capacity', 'bandwidth', and 'accessible_by'."
            )

        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("'memory.name' must be a non-empty string.")

        for field_name in ("capacity", "bandwidth"):
            value = data.get(field_name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value <= 0
            ):
                raise ValueError(f"'memory.{field_name}' must be a positive number.")

        accessible_by = data["accessible_by"]
        if not isinstance(accessible_by, list) or not all(
            isinstance(value, str) for value in accessible_by
        ):
            raise ValueError("'memory.accessible_by' must be an array of strings.")
        allowed_accessors = {"cpu", "gpu", "audio"}
        if any(value not in allowed_accessors for value in accessible_by):
            raise ValueError(
                "'memory.accessible_by' entries must be 'cpu', 'gpu', or 'audio'."
            )
        if len(accessible_by) != len(set(accessible_by)):
            raise ValueError("'memory.accessible_by' cannot contain duplicates.")

        return cls(
            name=name.strip(),
            capacity=data["capacity"],
            bandwidth=data["bandwidth"],
            accessible_by=accessible_by,
        )


@dataclass(slots=True)
class StorageSpec:
    name: str
    capacity: float
    bandwidth: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StorageSpec:
        expected_fields = {"name", "capacity", "bandwidth"}
        if set(data) != expected_fields:
            raise ValueError(
                "Every storage source must contain exactly: "
                "'name', 'capacity', and 'bandwidth'."
            )

        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("'storage.name' must be a non-empty string.")

        for field_name in ("capacity", "bandwidth"):
            value = data.get(field_name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value <= 0
            ):
                raise ValueError(f"'storage.{field_name}' must be a positive number.")

        return cls(
            name=name.strip(),
            capacity=float(data["capacity"]),
            bandwidth=float(data["bandwidth"]),
        )


@dataclass(slots=True)
class ProductSpecs:
    speed_unit: str | None
    memory_unit: str | None
    cpus: list[CpuSpec]
    gpu: GpuSpec | None
    audio: AudioSpec | None
    memory: list[MemorySpec]
    storage: list[StorageSpec]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProductSpecs:
        cpu_data = data.get("cpus", [])
        if not isinstance(cpu_data, list):
            raise ValueError("'specs.cpus' must be an array.")

        gpu_data = data.get("gpu")
        if gpu_data is not None and not isinstance(gpu_data, dict):
            raise ValueError("'specs.gpu' must be an object or null.")

        audio_data = data.get("audio")
        if audio_data is not None and not isinstance(audio_data, dict):
            raise ValueError("'specs.audio' must be an object or null.")

        memory_data = data.get("memory", [])
        if not isinstance(memory_data, list):
            raise ValueError("'specs.memory' must be an array.")

        if not all(isinstance(memory, dict) for memory in memory_data):
            raise ValueError("Every memory source must be an object.")

        storage_data = data.get("storage", [])
        if not isinstance(storage_data, list):
            raise ValueError("'specs.storage' must be an array.")

        if not all(isinstance(storage, dict) for storage in storage_data):
            raise ValueError("Every storage source must be an object.")

        return cls(
            speed_unit=data.get("speed_unit"),
            memory_unit=data.get("memory_unit"),
            cpus=[
                CpuSpec.from_dict(cpu)
                for cpu in cpu_data
                if isinstance(cpu, dict)
            ],
            gpu=GpuSpec.from_dict(gpu_data) if gpu_data is not None else None,
            audio=(
                AudioSpec.from_dict(audio_data)
                if audio_data is not None
                else None
            ),
            memory=[MemorySpec.from_dict(memory) for memory in memory_data],
            storage=[StorageSpec.from_dict(storage) for storage in storage_data],
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
