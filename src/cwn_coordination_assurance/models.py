from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


PersistenceClass = Literal["ephemeral", "session", "durable"]


@dataclass(frozen=True)
class AgentWindow:
    agent_id: str
    principal_id: str
    start: float
    end: float

    def __post_init__(self) -> None:
        if not self.agent_id or not self.principal_id:
            raise ValueError("agent_id and principal_id are required")
        if self.end < self.start:
            raise ValueError("end must be >= start")


@dataclass(frozen=True)
class Surface:
    surface_id: str
    readers: frozenset[str]
    writers: frozenset[str]
    writes_per_writer_hour: float
    bits_per_write_upper_bound: float
    read_visibility: float = 1.0
    persistence_hours: float = 0.0
    persistence_class: PersistenceClass = "ephemeral"
    allowed_coordination: bool = False
    tenant_id: str = "default"
    purpose: str = "unspecified"

    def __post_init__(self) -> None:
        if not self.surface_id:
            raise ValueError("surface_id is required")
        for name, value in (
            ("writes_per_writer_hour", self.writes_per_writer_hour),
            ("bits_per_write_upper_bound", self.bits_per_write_upper_bound),
            ("persistence_hours", self.persistence_hours),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if not 0 <= self.read_visibility <= 1:
            raise ValueError("read_visibility must be in [0,1]")


@dataclass(frozen=True)
class Deployment:
    deployment_id: str
    agents: tuple[AgentWindow, ...]
    surfaces: tuple[Surface, ...]
    window_hours: float
    policy_epoch: str = "unknown"
    telemetry_coverage: float = 0.0
    calibration_id: str | None = None

    def __post_init__(self) -> None:
        if not self.deployment_id:
            raise ValueError("deployment_id is required")
        if self.window_hours < 0:
            raise ValueError("window_hours must be non-negative")
        if not 0 <= self.telemetry_coverage <= 1:
            raise ValueError("telemetry_coverage must be in [0,1]")
        ids = [a.agent_id for a in self.agents]
        if len(ids) != len(set(ids)):
            raise ValueError("agent_id must be unique within a snapshot")


@dataclass(frozen=True)
class MetricResult:
    metric_version: str
    structural_directed_pairs: int
    temporal_reachability_ratio: float
    information_capacity_upper_bound_bits: float
    spectral_criticality_proxy: float
    baseline_ce_max: float
    telemetry_coverage: float
    risk_state: Literal["UNKNOWN", "RESEARCH_ONLY"]
    warnings: tuple[str, ...] = field(default_factory=tuple)

