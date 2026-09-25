"""火箭方程物理内核（仅标准库）。

职责：质量比链、齐奥尔科夫斯基理想速度增量、重力损失与可选阻力扣减。
本模块只做纯计算，不做输入合法性把关（见 validation.py），
但理想速度增量函数本身在 mf == m0 时按数学定义返回 0。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

STANDARD_GRAVITY = 9.80665  # m/s^2，竖直起飞简化重力模型


@dataclass(frozen=True)
class StageInput:
    """单级输入。stages 列表按点火顺序排列：索引 0 为最底级（最先点火）。"""

    name: str
    exhaust_velocity: float  # 有效排气速度 ve, m/s
    structural_mass: float  # 结构质量, kg
    propellant_mass: float  # 推进剂质量, kg
    burn_time: float  # 有效工作时间, s
    drag_loss: float = 0.0  # 可选大气阻力速度增量扣减, m/s

    @property
    def total_mass(self) -> float:
        return self.structural_mass + self.propellant_mass


@dataclass(frozen=True)
class StageResult:
    name: str
    ignition_mass: float  # m0：本级总质量 + 全部上级质量 + 载荷
    burnout_mass: float  # mf：本级结构质量 + 全部上级质量 + 载荷
    mass_ratio: float  # m0 / mf
    ideal_delta_v: float  # ve * ln(m0/mf)
    gravity_loss: float  # g * t_burn
    drag_loss: float  # 可选阻力扣减
    net_delta_v: float  # ideal - gravity - drag


@dataclass(frozen=True)
class VehicleResult:
    stages: tuple[StageResult, ...] = field(default_factory=tuple)
    total_ideal_delta_v: float = 0.0
    total_gravity_loss: float = 0.0
    total_drag_loss: float = 0.0
    total_net_delta_v: float = 0.0


def ideal_delta_v(exhaust_velocity: float, ignition_mass: float, burnout_mass: float) -> float:
    """齐奥尔科夫斯基理想速度增量 Δv = ve · ln(m0/mf)。

    mf == m0 时 ln(1) = 0，速度增量为零。
    """
    if ignition_mass <= 0.0:
        raise ValueError("点火质量必须为正")
    if burnout_mass <= 0.0:
        raise ValueError("燃料耗尽质量必须为正")
    return exhaust_velocity * math.log(ignition_mass / burnout_mass)


def gravity_loss(burn_time: float, g: float = STANDARD_GRAVITY) -> float:
    """竖直起飞简化重力损失 Δv_g = g · t_burn（只从理想值中扣除）。"""
    return g * burn_time


def evaluate_stage(stage: StageInput, upper_mass: float, g: float = STANDARD_GRAVITY) -> StageResult:
    """计算单级。upper_mass 为该级上方所有级的总质量与载荷之和。"""
    m0 = upper_mass + stage.total_mass
    mf = m0 - stage.propellant_mass
    ideal = ideal_delta_v(stage.exhaust_velocity, m0, mf)
    g_loss = gravity_loss(stage.burn_time, g)
    net = ideal - g_loss - stage.drag_loss
    return StageResult(
        name=stage.name,
        ignition_mass=m0,
        burnout_mass=mf,
        mass_ratio=m0 / mf,
        ideal_delta_v=ideal,
        gravity_loss=g_loss,
        drag_loss=stage.drag_loss,
        net_delta_v=net,
    )


def evaluate_vehicle(
    stages: list[StageInput],
    payload_mass: float = 0.0,
    g: float = STANDARD_GRAVITY,
) -> VehicleResult:
    """多级总速度增量 = 各级理想值逐级相加（绝不用整箭质量做一次对数）。"""
    if not stages:
        raise ValueError("级数不足一级")

    results: list[StageResult] = []
    # 自顶向下累加上方质量：第 i 级的 upper_mass = 载荷 + 其上方各级总质量
    upper_mass = payload_mass
    for stage in reversed(stages):
        results.append(evaluate_stage(stage, upper_mass, g))
        upper_mass += stage.total_mass
    results.reverse()  # 恢复为点火顺序

    return VehicleResult(
        stages=tuple(results),
        total_ideal_delta_v=sum(r.ideal_delta_v for r in results),
        total_gravity_loss=sum(r.gravity_loss for r in results),
        total_drag_loss=sum(r.drag_loss for r in results),
        total_net_delta_v=sum(r.net_delta_v for r in results),
    )
