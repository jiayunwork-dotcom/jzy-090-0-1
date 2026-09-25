"""批量比选调度：一组候选构型一次算完，各构型结论相互独立。"""
from __future__ import annotations

from .models import BatchEntry, BatchReport, VehicleSpec
from .service import evaluate_spec
from .validation import ValidationError


def evaluate_batch(configurations: list[VehicleSpec]) -> BatchReport:
    """逐个构型独立核算。

    每个构型的中间量与结论各自独立：某个构型校验失败只影响自己的条目，
    不污染、不覆盖其他构型的结果，也不中断整批计算。
    """
    entries: list[BatchEntry] = []
    for i, spec in enumerate(configurations):
        try:
            report = evaluate_spec(spec)
        except ValidationError as exc:
            entries.append(BatchEntry(index=i, name=spec.name, ok=False, errors=exc.reasons))
        else:
            entries.append(BatchEntry(index=i, name=spec.name, ok=True, report=report))
    return BatchReport(results=entries)
