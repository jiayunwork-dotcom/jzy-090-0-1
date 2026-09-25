"""批量比选测试：各构型结论独立，互不写串、互不覆盖。"""
from app.batch import evaluate_batch
from app.models import StageSpec, VehicleSpec
from app.service import evaluate_spec


def make_spec(name, ve=3000.0, struct=9000.0, prop=40000.0, burn=100.0):
    return VehicleSpec(
        name=name,
        payload_mass=1500.0,
        stages=[
            StageSpec(
                name="一级",
                exhaust_velocity=ve,
                structural_mass=struct,
                propellant_mass=prop,
                burn_time=burn,
            )
        ],
    )


def test_batch_results_match_individual_evaluation():
    specs = [make_spec("A", ve=3000.0), make_spec("B", ve=3500.0), make_spec("C", ve=2800.0)]
    report = evaluate_batch(specs)
    assert len(report.results) == 3
    for entry, spec in zip(report.results, specs):
        assert entry.ok
        individual = evaluate_spec(spec)
        assert entry.report.total_net_delta_v == individual.total_net_delta_v


def test_batch_preserves_order_and_names():
    specs = [make_spec("甲", ve=3000.0), make_spec("乙", ve=3500.0)]
    report = evaluate_batch(specs)
    assert [e.index for e in report.results] == [0, 1]
    assert [e.name for e in report.results] == ["甲", "乙"]
    assert report.results[0].report.name == "甲"
    assert report.results[1].report.name == "乙"


def test_invalid_config_does_not_corrupt_others():
    good = make_spec("合法", ve=3000.0)
    bad = make_spec("非法", ve=-1.0)
    report = evaluate_batch([good, bad, good.model_copy(update={"name": "合法2"})])

    assert report.results[0].ok and report.results[0].report is not None
    assert not report.results[1].ok
    assert report.results[1].report is None
    assert any("有效排气速度" in r for r in report.results[1].errors)
    # 非法构型之后的结果依然正确且独立
    assert report.results[2].ok
    assert report.results[2].report.total_net_delta_v == report.results[0].report.total_net_delta_v


def test_identical_configs_give_identical_independent_results():
    specs = [make_spec("X"), make_spec("Y")]
    report = evaluate_batch(specs)
    r0, r1 = report.results
    assert r0.report.total_net_delta_v == r1.report.total_net_delta_v
    assert r0.report is not r1.report  # 对象各自独立
