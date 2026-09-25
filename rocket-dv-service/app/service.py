"""核算调度层：把请求模型转成物理内核输入，先校验后计算，再组装报告。"""
from __future__ import annotations

from .models import StageReport, VehicleReport, VehicleSpec
from .physics import StageInput, evaluate_vehicle
from .validation import validate_vehicle


def spec_to_stages(spec: VehicleSpec) -> list[StageInput]:
    return [
        StageInput(
            name=s.name or f"第{i + 1}级",
            exhaust_velocity=s.exhaust_velocity,
            structural_mass=s.structural_mass,
            propellant_mass=s.propellant_mass,
            burn_time=s.burn_time,
            drag_loss=s.drag_loss,
        )
        for i, s in enumerate(spec.stages)
    ]


def evaluate_spec(spec: VehicleSpec) -> VehicleReport:
    """单次一箭构型核算：逐级质量比、逐级速度增量、重力损失与净值。"""
    stages = spec_to_stages(spec)
    validate_vehicle(stages, spec.payload_mass, spec.required_delta_v)
    result = evaluate_vehicle(stages, spec.payload_mass)

    meets: bool | None = None
    if spec.required_delta_v is not None:
        meets = result.total_net_delta_v >= spec.required_delta_v

    return VehicleReport(
        name=spec.name,
        stages=[
            StageReport(
                name=r.name,
                ignition_mass=r.ignition_mass,
                burnout_mass=r.burnout_mass,
                mass_ratio=r.mass_ratio,
                ideal_delta_v=r.ideal_delta_v,
                gravity_loss=r.gravity_loss,
                drag_loss=r.drag_loss,
                net_delta_v=r.net_delta_v,
            )
            for r in result.stages
        ],
        total_ideal_delta_v=result.total_ideal_delta_v,
        total_gravity_loss=result.total_gravity_loss,
        total_drag_loss=result.total_drag_loss,
        total_net_delta_v=result.total_net_delta_v,
        required_delta_v=spec.required_delta_v,
        meets_requirement=meets,
    )
