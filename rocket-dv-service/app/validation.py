"""输入合法性校验。所有违规均以带明确原因的 ValidationError 抛出。"""
from __future__ import annotations

from .physics import StageInput


class ValidationError(Exception):
    """携带全部违规原因列表的校验错误。"""

    def __init__(self, reasons: list[str]):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


def validate_stage(stage: StageInput, index: int) -> list[str]:
    """校验单级，返回违规原因列表（空列表表示合法）。"""
    reasons: list[str] = []
    label = stage.name or f"第{index + 1}级"

    if stage.exhaust_velocity <= 0.0:
        reasons.append(f"{label}: 有效排气速度必须大于零 (ve={stage.exhaust_velocity})")
    if stage.structural_mass <= 0.0:
        reasons.append(f"{label}: 结构质量必须大于零 (m_struct={stage.structural_mass})")
    if stage.propellant_mass < 0.0:
        reasons.append(f"{label}: 推进剂质量不能为负 (m_prop={stage.propellant_mass})")
    if stage.burn_time <= 0.0:
        reasons.append(f"{label}: 有效工作时间必须大于零 (t_burn={stage.burn_time})")
    if stage.drag_loss < 0.0:
        reasons.append(f"{label}: 阻力扣减不能为负 (drag_loss={stage.drag_loss})")

    # 燃料耗尽质量必须小于点火质量：mf = 结构 + 上级 + 载荷，m0 = mf + 推进剂
    # 推进剂为零时 mf == m0，属于非法输入（数学上 Δv=0，但服务不允许静默通过）
    if stage.propellant_mass == 0.0:
        reasons.append(f"{label}: 燃料耗尽质量等于点火质量（推进剂为零），该级无法提供速度增量")

    return reasons


def validate_vehicle(
    stages: list[StageInput],
    payload_mass: float = 0.0,
    required_delta_v: float | None = None,
) -> None:
    """校验整箭构型；任何违规都抛出 ValidationError。"""
    reasons: list[str] = []

    if len(stages) < 1:
        reasons.append("级数不足一级：至少需要一级")
    if payload_mass < 0.0:
        reasons.append(f"载荷质量不能为负 (payload={payload_mass})")
    if required_delta_v is not None and required_delta_v < 0.0:
        reasons.append(f"目标速度增量不能为负 (required={required_delta_v})")

    for i, stage in enumerate(stages):
        reasons.extend(validate_stage(stage, i))

    # 推进剂为零却索要正的速度增量
    if (
        required_delta_v is not None
        and required_delta_v > 0.0
        and stages
        and all(s.propellant_mass == 0.0 for s in stages)
    ):
        reasons.append("推进剂总量为零，却要求正的速度增量：无法满足")

    if reasons:
        raise ValidationError(reasons)
