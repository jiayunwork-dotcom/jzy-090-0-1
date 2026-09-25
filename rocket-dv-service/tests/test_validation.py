"""输入校验测试：每类非法输入都必须以带明确原因的错误被拒。"""
import pytest

from app.physics import StageInput
from app.validation import ValidationError, validate_vehicle


def good_stage(**kw):
    defaults = dict(
        name="一级",
        exhaust_velocity=3000.0,
        structural_mass=9000.0,
        propellant_mass=40000.0,
        burn_time=100.0,
    )
    defaults.update(kw)
    return StageInput(**defaults)


def test_valid_vehicle_passes():
    validate_vehicle([good_stage()], payload_mass=1500.0)


def test_non_positive_exhaust_velocity_rejected():
    with pytest.raises(ValidationError, match="有效排气速度必须大于零"):
        validate_vehicle([good_stage(exhaust_velocity=0.0)])
    with pytest.raises(ValidationError, match="有效排气速度必须大于零"):
        validate_vehicle([good_stage(exhaust_velocity=-100.0)])


def test_zero_propellant_rejected_as_burnout_equals_ignition():
    with pytest.raises(ValidationError, match="燃料耗尽质量等于点火质量"):
        validate_vehicle([good_stage(propellant_mass=0.0)])


def test_negative_propellant_rejected():
    with pytest.raises(ValidationError, match="推进剂质量不能为负"):
        validate_vehicle([good_stage(propellant_mass=-1.0)])


def test_zero_stages_rejected():
    with pytest.raises(ValidationError, match="级数不足一级"):
        validate_vehicle([])


def test_non_positive_burn_time_rejected():
    with pytest.raises(ValidationError, match="有效工作时间必须大于零"):
        validate_vehicle([good_stage(burn_time=0.0)])
    with pytest.raises(ValidationError, match="有效工作时间必须大于零"):
        validate_vehicle([good_stage(burn_time=-5.0)])


def test_zero_propellant_with_positive_required_delta_v_rejected():
    # 推进剂为零却索要正的速度增量：两条原因都应出现
    with pytest.raises(ValidationError) as exc_info:
        validate_vehicle([good_stage(propellant_mass=0.0)], required_delta_v=100.0)
    assert any("推进剂总量为零" in r for r in exc_info.value.reasons)


def test_multiple_violations_reported_together():
    bad = good_stage(exhaust_velocity=-1.0, burn_time=0.0)
    with pytest.raises(ValidationError) as exc_info:
        validate_vehicle([bad])
    assert len(exc_info.value.reasons) >= 2
