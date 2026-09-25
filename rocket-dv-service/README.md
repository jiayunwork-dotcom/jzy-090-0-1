# 多级火箭速度增量核算引擎

基于齐奥尔科夫斯基火箭方程的常驻 HTTP 核算服务：只做质量比与速度增量计算，
仅经接口对外提供，无前端页面、无账户体系。

## 物理模型

- 单级理想速度增量：`Δv = ve · ln(m0/mf)`
  - `m0`（点火质量）= 本级总质量 + 全部上级质量 + 载荷
  - `mf`（耗尽质量）= 本级结构质量 + 全部上级质量 + 载荷
- 多级总速度增量 = 各级理想值逐级相加（绝不拿整箭质量做一次对数）
- 重力损失：`Δv_g = g · t_burn`（竖直起飞简化，g = 9.80665 m/s²）
- 大气阻力：可选的逐段扣减项 `drag_loss`（默认 0）
- 净速度增量 = 理想值 − 重力损失 − 阻力扣减（只会变小，不会变大）

## 模块划分

| 文件 | 职责 |
|---|---|
| `app/physics.py` | 火箭方程内核：质量比链、理想 Δv、重力/阻力扣减（纯标准库） |
| `app/validation.py` | 输入合法性校验，违规抛出带明确原因的 `ValidationError` |
| `app/models.py` | Pydantic 请求/响应模型 |
| `app/service.py` | 单次一箭构型核算调度 |
| `app/batch.py` | 批量候选构型比选调度（各构型结论独立） |
| `app/reference.py` | 预置两级参考算例与同等结构比单级对照 |
| `app/main.py` | FastAPI 接口层 |

## 接口

- `GET /health` — 健康检查
- `POST /api/v1/delta-v/single` — 单次一箭构型核算：逐级质量比、逐级速度增量、重力损失与净值
- `POST /api/v1/delta-v/batch` — 一批候选构型批量比选，各构型结论各自独立
- `GET /api/v1/reference` — 载入预置两级算例并与假想单级对照，验证「分级优于塞单级」

请求示例：

```json
{
  "name": "两级构型",
  "payload_mass": 1500.0,
  "stages": [
    {"name": "一级", "exhaust_velocity": 3000.0, "structural_mass": 9000.0,
     "propellant_mass": 40000.0, "burn_time": 100.0, "drag_loss": 120.0},
    {"name": "二级", "exhaust_velocity": 3400.0, "structural_mass": 3000.0,
     "propellant_mass": 12000.0, "burn_time": 150.0}
  ]
}
```

`stages` 按点火顺序排列：首元素为最底级。

## 本地运行

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 测试

```bash
pytest -q
```

测试锁定的不变量包括：排气速度加倍则理想速度增量加倍、结构约束内加注推进剂
则质量比与速度增量升高、分级优于同等结构比单级、mf == m0 时 Δv 为零、
重力损失只减不增、批量比选各构型互不写串。

## Docker

```bash
docker build -t rocket-dv .
docker run -p 8000:8000 rocket-dv          # 启动服务，监听 8000
docker run --rm rocket-dv pytest -q        # 容器内执行自动化测试
```
