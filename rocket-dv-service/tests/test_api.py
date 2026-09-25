"""接口层与参考算例测试。"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

TWO_STAGE_PAYLOAD = {
    "name": "测试两级",
    "payload_mass": 1500.0,
    "stages": [
        {
            "name": "一级",
            "exhaust_velocity": 3000.0,
            "structural_mass": 9000.0,
            "propellant_mass": 40000.0,
            "burn_time": 100.0,
            "drag_loss": 120.0,
        },
        {
            "name": "二级",
            "exhaust_velocity": 3400.0,
            "structural_mass": 3000.0,
            "propellant_mass": 12000.0,
            "burn_time": 150.0,
        },
    ],
}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_single_returns_per_stage_breakdown():
    resp = client.post("/api/v1/delta-v/single", json=TWO_STAGE_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["stages"]) == 2
    for stage in body["stages"]:
        assert stage["mass_ratio"] > 1.0
        assert stage["gravity_loss"] > 0.0
        # 净值 = 理想值 - 重力损失 - 阻力
        assert stage["net_delta_v"] == pytest.approx(
            stage["ideal_delta_v"] - stage["gravity_loss"] - stage["drag_loss"]
        )
        assert stage["net_delta_v"] < stage["ideal_delta_v"]
    total = body["total_net_delta_v"]
    assert total == pytest.approx(sum(s["net_delta_v"] for s in body["stages"]))


def test_single_rejects_invalid_input_with_reason():
    bad = {
        "stages": [
            {
                "exhaust_velocity": -1.0,
                "structural_mass": 9000.0,
                "propellant_mass": 40000.0,
                "burn_time": 100.0,
            }
        ]
    }
    resp = client.post("/api/v1/delta-v/single", json=bad)
    assert resp.status_code == 422
    assert any("有效排气速度" in r for r in resp.json()["detail"])


def test_single_rejects_zero_stages():
    resp = client.post("/api/v1/delta-v/single", json={"stages": []})
    assert resp.status_code == 422
    assert any("级数不足一级" in r for r in resp.json()["detail"])


def test_single_rejects_zero_propellant():
    bad = {
        "stages": [
            {
                "exhaust_velocity": 3000.0,
                "structural_mass": 9000.0,
                "propellant_mass": 0.0,
                "burn_time": 100.0,
            }
        ],
        "required_delta_v": 500.0,
    }
    resp = client.post("/api/v1/delta-v/single", json=bad)
    assert resp.status_code == 422


def test_batch_endpoint_keeps_configs_independent():
    payload = {
        "configurations": [
            TWO_STAGE_PAYLOAD,
            {**TWO_STAGE_PAYLOAD, "name": "非法构型",
             "stages": [{**TWO_STAGE_PAYLOAD["stages"][0], "exhaust_velocity": 0.0}]},
        ]
    }
    resp = client.post("/api/v1/delta-v/batch", json=payload)
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results[0]["ok"] and results[0]["report"]["total_net_delta_v"] > 0
    assert not results[1]["ok"] and results[1]["errors"]


def test_reference_example_staging_beats_single_stage():
    resp = client.get("/api/v1/reference")
    assert resp.status_code == 200
    body = resp.json()
    staged = body["two_stage"]["total_net_delta_v"]
    monolithic = body["single_stage_equivalent"]["total_net_delta_v"]
    assert staged > monolithic
    assert body["staging_advantage"] == pytest.approx(staged - monolithic)
    assert body["staging_advantage"] > 0
