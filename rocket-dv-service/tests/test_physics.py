"""物理内核不变量测试：盯住火箭方程的正确性规则。"""
import math

import pytest

from app.physics import (
    STANDARD_GRAVITY,
    StageInput,
    evaluate_vehicle,
    gravity_loss,
    ideal_delta_v,
)


def make_stage(ve=3000.0, struct=9000.0, prop=40000.0, burn=100.0, drag=0.0, name="s"):
    return StageInput(
        name=name,
        exhaust_velocity=ve,
        structural_mass=struct,
        propellant_mass=prop,
        burn_time=burn,
        drag_loss=drag,
    )


class TestIdealDeltaV:
    def test_tsiolkovsky_value(self):
        # Δv = ve * ln(m0/mf)
        assert ideal_delta_v(3000.0, 1000.0, 500.0) == pytest.approx(3000.0 * math.log(2.0))

    def test_zero_when_burnout_equals_ignition(self):
        # 燃料耗尽质量恰好等于点火质量时速度增量为零
        assert ideal_delta_v(3000.0, 1000.0, 1000.0) == 0.0

    def test_doubling_exhaust_velocity_doubles_ideal_delta_v(self):
        base = ideal_delta_v(3000.0, 5000.0, 2000.0)
        doubled = ideal_delta_v(6000.0, 5000.0, 2000.0)
        assert doubled == pytest.approx(2.0 * base)

    def test_more_propellant_raises_mass_ratio_and_delta_v(self):
        low = ideal_delta_v(3000.0, 5000.0, 4000.0)   # 推进剂 1000
        high = ideal_delta_v(3000.0, 6000.0, 4000.0)  # 推进剂 2000，结构不变
        assert 6000.0 / 4000.0 > 5000.0 / 4000.0
        assert high > low


class TestGravityLoss:
    def test_gravity_loss_is_g_times_burn_time(self):
        assert gravity_loss(100.0) == pytest.approx(STANDARD_GRAVITY * 100.0)

    def test_gravity_loss_only_shrinks_net(self):
        stage = make_stage(burn=100.0)
        result = evaluate_vehicle([stage]).stages[0]
        assert result.gravity_loss > 0.0
        assert result.net_delta_v == pytest.approx(
            result.ideal_delta_v - result.gravity_loss - result.drag_loss
        )
        assert result.net_delta_v < result.ideal_delta_v

    def test_drag_loss_only_shrinks_net(self):
        stage = make_stage(drag=150.0)
        result = evaluate_vehicle([stage]).stages[0]
        assert result.net_delta_v == pytest.approx(
            result.ideal_delta_v - result.gravity_loss - 150.0
        )


class TestStaging:
    def test_upper_stages_counted_in_lower_ignition_mass(self):
        # 一级的 m0 必须计入二级与载荷
        s1 = make_stage(struct=9000.0, prop=40000.0, name="一级")
        s2 = make_stage(ve=3400.0, struct=3000.0, prop=12000.0, name="二级")
        result = evaluate_vehicle([s1, s2], payload_mass=1500.0)
        r1, r2 = result.stages
        assert r1.ignition_mass == pytest.approx(49000.0 + 15000.0 + 1500.0)
        assert r1.burnout_mass == pytest.approx(9000.0 + 15000.0 + 1500.0)
        assert r2.ignition_mass == pytest.approx(15000.0 + 1500.0)
        assert r2.burnout_mass == pytest.approx(3000.0 + 1500.0)

    def test_total_is_sum_of_stages_not_single_log(self):
        s1 = make_stage(struct=9000.0, prop=40000.0, name="一级")
        s2 = make_stage(ve=3400.0, struct=3000.0, prop=12000.0, name="二级")
        result = evaluate_vehicle([s1, s2], payload_mass=1500.0)
        r1, r2 = result.stages
        assert result.total_ideal_delta_v == pytest.approx(
            r1.ideal_delta_v + r2.ideal_delta_v
        )
        # 绝不能等于整箭起飞质量对最终净载荷的一次对数
        whole_log = 3000.0 * math.log((49000.0 + 15000.0 + 1500.0) / 1500.0)
        assert result.total_ideal_delta_v != pytest.approx(whole_log)

    def test_staging_beats_single_stage_at_same_structural_ratio(self):
        # 相同结构质量、相同推进剂、相同载荷：分级总速度增量应高于塞单级
        s1 = make_stage(ve=3000.0, struct=9000.0, prop=40000.0, burn=100.0, name="一级")
        s2 = make_stage(ve=3400.0, struct=3000.0, prop=12000.0, burn=150.0, name="二级")
        staged = evaluate_vehicle([s1, s2], payload_mass=1500.0)

        single = make_stage(ve=3200.0, struct=12000.0, prop=52000.0, burn=250.0, name="单级")
        monolithic = evaluate_vehicle([single], payload_mass=1500.0)

        assert staged.total_ideal_delta_v > monolithic.total_ideal_delta_v

    def test_empty_stage_list_rejected(self):
        with pytest.raises(ValueError, match="级数不足一级"):
            evaluate_vehicle([])
