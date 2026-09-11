# Jmall 简历可用量化数据（2026-09-11 实测）

> 本文件只收录**本次实际运行产出**的数字。所有数字都能追溯到 `jmall-eval/results/2026-09-11/` 下的原始记录。
> **未实测、无法复现、或属于臆测的内容一律不写入本文件。**
> 代码基线：`3701f33fb2aea6128c4aa303013abaad289b7140`（tag `eval-baseline`）

## 0. 溯源信息

| 项目 | 值 |
|---|---|
| 基线 commit | `3701f33`（`git tag eval-baseline`，工作区干净、无未提交改动） |
| 实验日期 | 2026-09-11 |
| 结果目录 | `jmall-eval/results/2026-09-11/`（**仅本地保存，已加入 .gitignore，不上传仓库**） |
| 汇总文件 | `summary.json` / `summary.csv`（88 条指标，本地） |
| 评测代码 | `jmall-eval/`（与业务代码完全隔离，只读依赖 `jmall-agent`，未修改任何业务逻辑；**整个目录不入库**） |

> 说明：`jmall-eval/`（评测脚本、127 条标注数据集、逐条记录与日志）按仓库约定不上传 GitHub。
> 本文件中的每个数字依旧成立，但证明它们的原始记录只存在于本机；需要交付第三方核验时单独打包该目录即可。

复现命令：

```bash
# 阶段2 回归
cd jmall-agent && AI_PROVIDER=mock ... uv run --python 3.12 --with-requirements requirements.txt pytest -q
docker run --rm -v <repo>/jmall-backend:/app maven:3.9-amazoncorretto-17 mvn -B test
cd jmall-web && npm run test:run
docker run --rm -v <repo>/jmall-bench:/app golang:1.22 go test -v ./...

# 阶段3 Input Gate
python jmall-eval/datasets/build_input_gate_cases.py
PYTHONPATH=<repo>/jmall-agent:<repo>/jmall-eval python jmall-eval/python/eval_input_gate.py

# 阶段4 任务恢复（需先启动 docker Redis 与 eval server）
docker run -d --name jmall-eval-redis -p 6399:6379 redis:7-alpine
python jmall-eval/python/serve_for_recovery.py &
python jmall-eval/python/eval_job_recovery.py --repeats 20 --external-server

# 阶段5 真实模型生成（预算上限 1.5 USD）
AI_PROVIDER=qwen AGENT_STRONG_MODEL=qwen-plus ... python jmall-eval/python/eval_generation.py --budget-usd 1.5
```

---

## 1. 可以写进简历的指标

### 1.1 工程质量

| 指标 | 结果 | 样本量 | 证据文件 |
|---|---:|---:|---|
| 全栈自动化测试通过率 | **506 / 506 = 100%** | 506 条（Python 379 + Java 71 + Vue 52 + Go 4） | `logs/python_pytest.log`、`logs/java_mvn.log`、`logs/web_vitest.log`、`logs/go_test.log` |
| 测试规模 | Python 34 个测试文件 / 379 条；Java 11 个类 / 71 条；前端 7 个文件 / 52 条 | — | 同上 |

> 表述边界：必须写明是「Mock 模型 + Mock 数据源」的替身环境，不能暗示已在真实模型/真实数据库上验证。

### 1.2 确定性输入闸门（本轮最有说服力的自研指标）

| 指标 | 结果 | 样本量 | 证据文件 |
|---|---:|---:|---|
| 判定准确率 Accuracy | **88.19%** | 127 条人工标注样本（应放行 47 / 应拦截 80） | `input_gate_summary.json` |
| 拦截类 Precision / Recall / F1 | **87.36% / 95.00% / 91.02%** | 同上 | 同上 |
| 对抗与异常样本拦截 Recall | **93.44%**（57/61） | 61 条（主观描述、未知字段、否定描述、占位符、零宽字符、长文本空转等） | 同上 |
| 实测模型调用次数 / Token 增量 | **0 次 / 0 token** | 127 条全量判定 | 同上（`instrumentation_self_check` 证明探针可观测到调用） |
| 单样本平均判定耗时 | **1.79 ms** | 127 条 | 同上 |

关键设计点：闸门是**纯规则、不调用模型**的确定性组件，四个入口（免费体检 / 生成 / 预览 / 搜图）复用同一实现；
实测跑完全部 127 条判定 **没有产生任何一次模型调用**，因此"信息不足"的请求不会进入付费链路。

### 1.3 任务断连与恢复（真实 Redis）

| 指标 | 结果 | 样本量 | 证据文件 |
|---|---:|---:|---|
| 断连后恢复成功率 | **100%**（创建后立即断开 / 运行中打断 / 通过 active job 恢复，各 20 次） | 60 次恢复 + 20 次正常基线 + 20 次越权 = 100 次 | `job_recovery_summary.json`、`job_recovery_records.jsonl` |
| final_result 完整率 | **100%** | 60 次恢复 | 同上 |
| 恢复结果与正常结果关键字段一致率 | **100%** | 60 次恢复（比对 7 个关键字段） | 同上 |
| 丢失任务 / 重复任务 | **0 / 0**（共创建 100 个不同 job） | 100 次 | 同上 |
| 平均恢复耗时 | **约 0.36 s**（约 7 次轮询） | 60 次恢复 | 同上 |
| 跨用户越权读取拦截率 | **100%**（20/20 返回 404） | 20 次 | 同上 |

环境：真实 Redis 容器（非 fakeredis）、真实 uvicorn + HTTP SSE 流式、每个 Agent 注入 60 ms 延迟以制造"运行中打断"——
60 次恢复全部是在任务状态为 `RUNNING` 时打断的（`mid_run_disconnect_rate = 1.0`）。

### 1.4 真实模型商品生成（预算受控）

模型：Qwen（`strong/medium = qwen-plus`，`cheap = qwen-turbo`），35 次完整编排，预算上限 1.5 USD，**实际总花费 0.0303 USD**。

| 指标 | 结果 | 样本量 | 证据文件 |
|---|---:|---:|---|
| 平台 Skill 版本可追溯率 | **100%**（每次产出都带 `platform_skill_id` + `version`） | 35 次（15 商品 × 5 平台，其中 5 商品跑满 5 平台） | `generation_summary.json` |
| 标题长度符合 Skill 预算率 | **100%** | 35 次 | 同上 |
| 详情结构符合率（Skill 要求的章节齐备） | **100%** | 35 次 | 同上 |
| 副标题非空率 / SEO 词数落在 8–12 比例 | **100% / 100%** | 35 次 | 同上 |
| 广告法敏感/禁用表达命中 | **0 次** | 35 次 | 同上 |
| 事实一致性（自动匹配器口径） | **77.78%**（45 条数值声明中 10 条未在商家事实里逐字命中） | 45 条声明 | 同上 + `generation_fact_review.json` |
| 事实一致性（人工复核口径） | **100%**——10 条全部是单位/写法差异（`600ml` vs `600毫升`、`1.7L` vs `1.7升`），无一条凭空捏造 | 45 条声明 | `generation_fact_review.json`（逐条证据） |
| 端到端耗时 平均 / P50 / P95 | **27.18 s / 26.93 s / 31.05 s** | 35 次 | `generation_summary.json` |
| 各 Agent 平均耗时 | 文案生成 4.84 s、平台适配 3.66 s、市场调研 2.99 s、意图规划 2.52 s、合规审查 0.84 s | 35 次 | 同上 |
| 单任务平均 Token / 成本 | **11,960 tokens / 0.00087 USD**（输入 10,520 / 输出 1,441，5 次模型调用） | 35 次 | 同上 |

---

## 2. 不适合写进简历 / 必须避免的表述

以下内容**没有实测依据**，禁止出现在简历或面试表述中：

* 用户量、DAU、注册数、订单量、转化率、GMV
* "节省 X 小时人工""提升 X% 效率""降低 X% 成本"等商业收益
* 真实线上 P50/P95——本轮耗时来自单次实验环境（本地 + 真实 Qwen），不是线上流量
* Go 秒杀的 QPS / 超卖率——Go 服务没有 `/metrics` 端点，Prometheus 抓取恒为 `up=0`，**无法测量**
* 历史文档里的"496 条全绿"——已被本次 506 条实际结果取代，禁止再引用
* Git 中的 Bug 修复数量——仓库在本次整理前只有 3 个 release 级提交，`git log --grep="fix|修复"` 命中 0 条

---

## 3. 保留的失败与缺陷结果（不美化）

| 项 | 结果 | 说明 | 证据 |
|---|---|---|---|
| Input Gate 误伤（有效商品被拦） | 11 条 | 根因集中在两类：材质/单位白名单覆盖不足（TPE、橡胶、铝合金、英寸、帕、岁）、人群口语化表述未被识别（"适合…的人""主要卖给…群体"） | `input_gate_adjudication.json` |
| Input Gate 漏放（信息不足放行） | 4 条 | 跨字段近似重复事实未去重（`304不锈钢` 与 `304不锈钢内胆` 算成两条）、缺失表达语序依赖（"容量没…"）、开放人群兜底过宽（"知道的人"被接受） | 同上 |
| 合规终态 | 35 次运行**没有一次是 success/passed**：11 次 `needs_revision`、24 次 `ready_with_warnings`（合规服务 11 次 rejected / 23 次 warning / 1 次 passed） | 说明生成内容仍需要人工确认，不能宣称"一次通过" | `generation_records.jsonl` |
| 字段守卫触发率 | 51.43%（18/35） | `guarded=True` 表示平台 Skill 输出有字段被守卫逻辑替换，属于保护性降级，不是成功 | 同上 |
| 事实一致性自动口径 | 77.78% | 匹配器对单位写法不鲁棒，已如实保留自动口径与人工口径两个数 | `generation_fact_review.json` |
| 环境陷阱 | 本机直接运行时 `.env` 的 `JMALL_QWEN_API_KEY` 不在 `Settings` alias 列表内（容器内由 compose 重命名为 `QWEN_API_KEY`），会**静默回落 mock** | 首次"真实模型"试跑因此实际是 mock，已发现并修正为显式 `QWEN_API_KEY` 后重跑 | 本文件 §0 复现命令 |
| Git 历史 | 本次之前只有 3 个提交，v0.3 全部改动未提交；已按 9 个主题拆分提交 | 拆分前无法用 Git 证明任何迭代过程 | `git log` |
| `.gitignore` 缺陷 | `*.md` 规则导致 `docs/` 下所有文档从未入库 | 已加例外并将文档与评测产物纳入版本控制 | `.gitignore`、`git show 549c71a` |

---

## 4. 数据可靠性声明

1. 所有结果均由 `jmall-eval/` 下的脚本产生，脚本只读调用业务代码，没有修改任何业务逻辑。
2. 每个指标都能定位到：逐条记录文件（`*.jsonl`）+ 汇总文件（`*.json`）+ 原始运行日志（`logs/*.log`）。
3. 标注数据集 `jmall-eval/datasets/input_gate_cases.jsonl` 每条含 `rationale` 与 `source`，可逐条复核；
   其中 2 条标注错误已在 `input_gate_cases.reviewed.jsonl` 中标明并单独披露，**未混入头版数字**。
4. 阶段 5 使用真实付费模型，总成本 0.0303 USD，未触发 1.5 USD 预算上限；成本为公开牌价估算（非账单）。
