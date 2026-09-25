"""预置参考算例：两级构型 vs 同等结构比的假想单级对照。

服务启动后可直接载入本算例，把分级总速度增量与单级对照一并打出，
供人手工对照「分级优于塞单级」这条不变量。
"""
from __future__ import annotations

from .models import VehicleSpec, StageSpec

PAYLOAD_MASS = 1500.0  # kg

# 两级参考构型（底级在前）
REFERENCE_TWO_STAGE = VehicleSpec(
    name="参考两级构型",
    payload_mass=PAYLOAD_MASS,
    stages=[
        StageSpec(
            name="一级",
            exhaust_velocity=3000.0,
            structural_mass=9000.0,
            propellant_mass=40000.0,
            burn_time=100.0,
            drag_loss=120.0,
        ),
        StageSpec(
            name="二级",
            exhaust_velocity=3400.0,
            structural_mass=3000.0,
            propellant_mass=12000.0,
            burn_time=150.0,
        ),
    ],
)


def equivalent_single_stage(two_stage: VehicleSpec = REFERENCE_TWO_STAGE) -> VehicleSpec:
    """构造同等结构质量、同等推进剂、同等载荷的假想单级对照方案。

    排气速度取两级按推进剂加权的平均值，工作时间取两级之和，
    使对照方案在同等结构比下尽可能公平。
    """
    total_struct = sum(s.structural_mass for s in two_stage.stages)
    total_prop = sum(s.propellant_mass for s in two_stage.stages)
    total_burn = sum(s.burn_time for s in two_stage.stages)
    ve_weighted = (
        sum(s.exhaust_velocity * s.propellant_mass for s in two_stage.stages) / total_prop
    )
    return VehicleSpec(
        name="假想单级对照（同等结构比）",
        payload_mass=two_stage.payload_mass,
        stages=[
            StageSpec(
                name="单级",
                exhaust_velocity=ve_weighted,
                structural_mass=total_struct,
                propellant_mass=total_prop,
                burn_time=total_burn,
                drag_loss=sum(s.drag_loss for s in two_stage.stages),
            )
        ],
    )
