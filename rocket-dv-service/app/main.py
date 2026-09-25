"""FastAPI 接口层：仅经 HTTP 对外提供核算能力，无前端、无账户体系。"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .batch import evaluate_batch
from .models import BatchReport, BatchSpec, VehicleReport, VehicleSpec
from .reference import REFERENCE_TWO_STAGE, equivalent_single_stage
from .service import evaluate_spec
from .validation import ValidationError

app = FastAPI(
    title="多级火箭速度增量核算引擎",
    version="1.0.0",
    description="基于齐奥尔科夫斯基火箭方程的质量比与速度增量核算服务",
)


@app.exception_handler(ValidationError)
async def validation_error_handler(_: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.reasons})


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/v1/delta-v/single", response_model=VehicleReport)
def single(spec: VehicleSpec) -> VehicleReport:
    """单次一箭构型核算：逐级质量比、逐级速度增量、重力损失与净值。"""
    return evaluate_spec(spec)


@app.post("/api/v1/delta-v/batch", response_model=BatchReport)
def batch(spec: BatchSpec) -> BatchReport:
    """一批候选构型批量比选：各构型结论各自独立，互不写串。"""
    return evaluate_batch(spec.configurations)


@app.get("/api/v1/reference")
def reference() -> dict:
    """载入预置两级参考算例，并与同等结构比的假想单级对照一并返回。"""
    staged = evaluate_spec(REFERENCE_TWO_STAGE)
    single_stage = evaluate_spec(equivalent_single_stage())
    return {
        "two_stage": staged,
        "single_stage_equivalent": single_stage,
        "staging_advantage": staged.total_net_delta_v - single_stage.total_net_delta_v,
        "conclusion": (
            f"分级净速度增量 {staged.total_net_delta_v:.1f} m/s，"
            f"单级对照 {single_stage.total_net_delta_v:.1f} m/s，"
            f"分级占优 {staged.total_net_delta_v - single_stage.total_net_delta_v:.1f} m/s"
        ),
    }
