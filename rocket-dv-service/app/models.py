"""Pydantic 请求/响应模型（仅做类型承载，业务校验在 validation.py）。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class StageSpec(BaseModel):
    name: str = Field(default="", description="级名称")
    exhaust_velocity: float = Field(description="有效排气速度 ve, m/s")
    structural_mass: float = Field(description="结构质量, kg")
    propellant_mass: float = Field(description="推进剂质量, kg")
    burn_time: float = Field(description="有效工作时间, s")
    drag_loss: float = Field(default=0.0, description="可选大气阻力扣减, m/s")


class VehicleSpec(BaseModel):
    name: str = Field(default="", description="构型名称")
    stages: list[StageSpec] = Field(description="按点火顺序排列：首元素为最底级")
    payload_mass: float = Field(default=0.0, description="净载荷质量, kg")
    required_delta_v: float | None = Field(default=None, description="可选目标速度增量, m/s")


class BatchSpec(BaseModel):
    configurations: list[VehicleSpec] = Field(description="一批候选构型")


class StageReport(BaseModel):
    name: str
    ignition_mass: float
    burnout_mass: float
    mass_ratio: float
    ideal_delta_v: float
    gravity_loss: float
    drag_loss: float
    net_delta_v: float


class VehicleReport(BaseModel):
    name: str
    stages: list[StageReport]
    total_ideal_delta_v: float
    total_gravity_loss: float
    total_drag_loss: float
    total_net_delta_v: float
    required_delta_v: float | None = None
    meets_requirement: bool | None = None


class BatchEntry(BaseModel):
    """批量比选中每个构型的独立结论：要么有结果，要么有错误，互不写串。"""

    index: int
    name: str
    ok: bool
    report: VehicleReport | None = None
    errors: list[str] | None = None


class BatchReport(BaseModel):
    results: list[BatchEntry]
