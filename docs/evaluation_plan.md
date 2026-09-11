# Jmall 简历项目深度与量化评测方案

> 文档性质：**项目审查 + 评测设计**，本阶段**不执行**任何大规模实验，不修改任何业务代码。
> 编写日期：2026-09-11；代码基线：本地工作区 `v0.3` 分支（v0.2 之后的改动**全部未提交**，详见 §2.5）。
> 规则：文中所有数字必须能追溯到「静态统计命令」「现有文档」或「未来将要执行的脚本输出文件」。**没有跑过的实验一律写成"待测"，不写成结果。**

---

## 0. 证据基线（本文档每个结论的来源）

| 编号 | 来源类型 | 说明 |
|---|---|---|
| E1 | 静态统计 | 仓库内文件行数、用例数、装饰器数量，可用 `find/wc/grep` 复现（命令见附录 A） |
| E2 | 既有文档 | `docs/v0.2-测试验收.md`、`docs/v0.2-PRD.md`、`docs/v0.1问题解决.md`、`README.md`。文档里的数字属于**既往记录**，必须重新运行才能在当前代码上复现 |
| E3 | 代码事实 | 具体 `__文件:行号 / 类 / 方法`，可逐条打开核对 |
| E4 | 运行产物 | 未来的评测脚本输出到 `jmall-eval/results/<YYYY-MM-DD>/`，这是唯一允许写进简历的"结果"来源 |

**当前工作区状态（必须知道的坑）**：`git rev-list --count HEAD = 3`，且 `main / v0.2 / v0.3` 三个分支指向同一提交。
`git status --porcelain` 显示 **37 个已修改文件 + 9 个未跟踪路径**（含 `jmall-agent/app/api/shopper.py`、`jmall-agent/app/services/shopper_intent_service.py`、
`jmall-web/src/components/game/CatchGoodsMiniGame.vue` 等 v0.3 新功能）。
因此：**Git 历史无法证明任何 v0.2 之后的开发过程**，所有 v0.3 的能力、修复记录只能靠代码本身和未来的评测输出证明。

---

## 一、当前项目已经实现了什么（只依据代码）

### 1.1 整体形态

| 模块 | 技术 | 规模（E1） | 说明（E3） |
|---|---|---|---|
| `jmall-agent` | Python 3.12 + FastAPI + LangGraph | 10,227 行 / 65 个 `.py` | AI Agent 服务，Compose 内网 `:18080`，不暴露宿主机端口 |
| `jmall-backend` | Java 17 + Spring Boot 3 + MyBatis-Plus + Redis | 7,037 行 / 92 个 `.java` | 主业务服务 `:10301` |
| `jmall-web` | Vue 3 + TS + Vite + Pinia + Vitest | 10,290 行 / 48 个 `.vue`+`.ts` | 前端 `:5175` |
| `jmall-bench` | Go + Redis Streams | 641 行 / 7 个 `.go` | 秒杀热点链路 `:19090`，**仅 `/health` + 3 个秒杀接口** |

九个 Compose 服务：`mysql / postgres / redis / backend / agent / frontend / bench / prometheus / grafana`（`docker-compose.yml`）。

### 1.2 Multi-Agent 编排（`jmall-agent/app/agents/graph.py`，796 行）

已实现的图结构（E3，`graph.py:185-269`）：

```
input_gate ──(ready?)─► parse_intent ──Send 并行──► node_market_research
     │                                          └──► rag_retrieval
     └─(needs_input)─► finalize_input_gate ──► END        │
                                                     join_research_rag
                                                          ▼
                                                    copy_generation
                                                          ▼
                                                   style_adaptation
                                                          ▼
                                                  compliance_review
                                                          ▼
                                                  aggregate_results ──► END
```

* **`input_gate` 是纯确定性规则引擎，不调用任何模型**（`app/agents/input_gate.py`，325 行）。
  加权打分：标题 20 / 品类 15 / 事实 30 / 人群 20 / 场景 15；`ready = not missing`；最多追问 3 条（`input_gate.py:304-324`）。
  它被**四个入口复用**：`/api/agent/input-assessment`、`/api/agent/product/copy`、`/api/styles/preview`、`/api/images/candidates`（`app/services/input_assessment_service.py` → `record_input_assessment`）。
  这是整个项目里**最值得量化**的部分：确定性、零成本、可离线批量跑。
* **并行扇出**使用 LangGraph `Send` API（`graph.py:736-740`），`market_research` 与 `rag_retrieval` 无依赖并行，再 `join`。
* **每个节点都有异常兜底**：`parse_intent` 失败降级为默认计划、`market_research` 失败返回空趋势、`rag_retrieval` 失败返回空上下文、
  `copy_generation` / `compliance_review` / `style_adaptation` 失败各自退化为可展示的降级稿（`graph.py:430-688`）。**这些降级路径是可测的**。
* **SSE 流式 + 任务持久化**：`app/services/job_store.py`（Redis，TTL 3600s），`api/agent.py:150-274` 的 `/orchestrate/stream`。
  关键实现：`asyncio.create_task` 在 `StreamingResponse` 之前启动并记录到 `_background_tasks`，**浏览器断开 SSE 后 job 仍在跑**（`agent.py:231-235`），
  前端可用 `/api/agent/jobs/{job_id}`、`/jobs/active/{user_id}`、`DELETE /jobs/{id}/consume` 恢复与消费。→ **任务恢复率可测**。

### 1.3 LLM 路由与成本治理

* `app/llm/router.py`：按 agent_type 映射到 `cheap/medium/strong` 三档，再按档选 provider/model，支持 `AGENT_{STRONG,MEDIUM,CHEAP}_{PROVIDER,MODEL}` 覆盖；
  **provider 可用性由 API Key 存在性校验**，无 Key 时全部回落到 `mock`（`router.py:67-101`）。
* `app/llm/cost_tracker.py`：每次调用记录 provider/model/input_tokens/output_tokens/agent_type，按内置单价表算 USD（表在 `cost_tracker.py:20-31`，注释明确说明是"公开牌价估算，非账单"），
  日预算默认 5 USD（`app/core/config.py:137`），超预算只告警不熔断。
* **`CostTracker._records` 是纯内存 List**（`cost_tracker.py:70`），进程重启即清零；`/api/admin/cost-stats` 读的就是这份内存数据（含 `scope_id` 维度，可区分单次编排）。
* `postgres/init/01-rag-schema.sql:66-79` 建了 `jmall_rag.ai_request_logs` 表，**但全仓库 Python 代码没有任何写入它的代码**（`grep -rn "ai_request_logs" --include="*.py"` 结果为空）。
  `app/repositories/request_log_repository.py` 只是一个 10 行的内存 List 桩。
  → **结论：模型调用目前没有任何持久化审计留痕**（详见 §4）。

### 1.4 RAG 知识库

* pgvector 真实向量检索：`(1 - (embedding <=> :vec)) as score`，HNSW 索引 `vector_cosine_ops`（`repositories/knowledge_base_repository.py:504-533`；`docker/postgres/init/01-rag-schema.sql:60`）。
  无 `DATABASE_URL` 时退化为文件仓储 `merchant_ai_store.json`（当前仅 63 字节，无真实语料）。
* 分块：`rag_chunk_size=800 / overlap=120`（`config.py:43-49`）；Embedding Provider 可插拔 `mock` / `openai-compatible`（`services/embedding_*`）。
* **RAG 质量评估代码已存在**：`app/retrieval/quality.py`（291 行）实现 LLM-as-Judge，打 1–5 分，计算 `hit_rate / MRR / NDCG / precision@k`，
  并暴露 `POST /api/admin/rag/evaluate`（`api/agent.py:717-765`）。**但仓库里没有标注好的 query→相关文档 ground truth 数据集，也没有跑过的结果文件。**
* 轻量阈值版：`assess_rag_quality()` 用 top1 分 ≥0.8/≥0.5 判 high/medium/low（`rag_retriever.py:8-49`）；
  `scripts/verify_thresholds.py` 是**已存在的评测脚本雏形**（10 条电商相关 + 10 条无关查询，输出 `/app/data/threshold_verify_results.json`），但目前不在任何自动化链路里。

### 1.5 Image Scout（联网图片候选）

`app/services/image_scout_service.py`（266 行）：先过确定性输入闸门 → 调 provider（`qwen_web_images` / `serpapi_google_images`）→ 安全归一化 → 最多 3 张。
纯函数、可离线测的部分：`is_safe_public_url()`（强制 https、禁止 localhost/内网域名/IP、禁凭据 URl、长度 ≤2048）、
`_url_resolves_public()`（DNS 解析 + `ipaddress.is_global`，超时 0.8s）、URL 去重、`assess_image_risks()`（水印/品牌/低分辨率元数据打标）。
→ **SSRF 防护与去重/数量约束是可行的高价值评测项**。

### 1.6 平台 Skill（5 套）

`app/platform_skills/definitions/{taobao,jd,pinduoduo,suning,xiaohongshu}.json` + `registry.py`，
`app/agents/style_adapter.py`（406 行）执行 Skill 并**始终返回 `platform_skill_id` / `platform_skill_version`**，
模型失败时返回基于商家事实的 `fallback` 草稿并对逐个字段做 `guarded` 兜底（`style_adapter.py:64-199`）。
→ **"Skill 版本可追溯率" 与 "字段守卫率" 是可测的结构化指标**（已有 Prometheus 计数 `jmall_platform_drafts_total{platform,metadata,fallback}`）。

### 1.7 Java 后端（依据 jmall-backend 代码）

* 15 个 Controller：商品 CRUD、草稿/发布/下架、购物车、订单、签到、成就、收藏、评价、店铺、排行榜、上传、认证、用户、AI 代理、埋点。
* **发布门禁**：`ProductPublishService.check()` 产出 14 类 `PublishBlocker`（`title_required` … `platform_mismatch` / `image_required` / `search_image_unconfirmed` / `pending_confirmations` / `compliance_rejected` 等），
  并含 SSRF 图片 URL 校验；已发布商品的 `update` 会二次复检，失败则 fail-closed 不改线上商品。
* **事务**：`@Transactional` 覆盖商品发布、下单、购买、金币增减、购物车等核心写路径；发布事件走 `TransactionSynchronization.afterCommit` 才计数。
* **指标**：Micrometer 两个 Counter —— `jmall_editor_sessions_total{stage}`、`jmall_product_events_total{event}`，
  经 `/actuator/prometheus` 暴露，**不落库**，进程内累计，重启清零（README 与 `docs/v0.2-测试验收.md:103` 均已注明）。
* **后端没有任何分布式锁 / 乐观锁 / `setIfAbsent`**；幂等依赖数据库唯一键（`uk_user_date`、`uk_user_achievement` 等）。
  `AiProxyService` 转发 Agent 的 10+ 个接口，连接 10s / 读 120s / SSE 300s，**无重试**，失败退金币。

### 1.8 前端

`ProductEditor.vue`（2,884 行）：7 阶段 SSE 状态机、`TextDecoder` 分帧解析、`localStorage` + 服务端 `/jobs/active` 对账的任务恢复（RUNNING 时 2s 轮询、异常 3s 重试）、
三态互斥防重复提交、Image Scout 请求序号 + 表单快照失效机制、发布前 `publishCheck` 二次确认。
Pinia 仅 `auth`、`gamification` 两个 store。埋点 `services/editorTelemetry.ts` 上报 5 阶段漏斗到 `/api/telemetry/editor-events`。

### 1.9 已经接好的可观测性

Prometheus 抓取 `backend:10301/actuator/prometheus`、`agent:18080/metrics`、`bench:19090`（`docker/prometheus/prometheus.yml`）。
**`bench` 的 Go 服务没有 `/metrics` 路由**（`internal/seckill/handler.go:16-21` 只有 `/health` 与 3 个秒杀接口），
因此 Go 抓取恒为 `up=0`——这与 `docs/v0.2-测试验收.md:103` 的记载一致。

### 1.10 README 中提到但**代码无法完全支撑**的点（写简历时必须降调）

| README/PRD 说法 | 代码实际状态 |
|---|---|
| "Go 秒杀热点链路" | 代码存在且有 4 个单测，但**无 metrics、无压测、未接入 Grafana**，不能给任何性能指标 |
| "Redis 缓存、任务状态和异步链路支持" | JobStore 确实基于 Redis；但**没有缓存层**（未见任何业务缓存读写） |
| "PostgreSQL + pgvector RAG 知识库" | 表结构与 SQL 真实存在，但**当前仓库不含任何真实语料**（`merchant_ai_store.json` 63 字节），需要先灌数据 |
| "Multi-Agent 商品内容生成" | 编排真实存在，但**没有对着"生成质量"的评测结果**，目前只有模块级 mock 测试 |

---

## 二、目前可以直接量化的指标

> 这里的"直接"= **不需要新写业务代码**，只需要：跑既有命令 / 读现有文档 / 静态统计。

### 2.1 测试规模（静态统计，E1）

| 范围 | 统计口径 | 数量 | 获取方式 |
|---|---|---|---|
| Python Agent | `tests/test_*.py` 文件数 | **34** | `ls jmall-agent/tests/test_*.py \| wc -l` |
| Python Agent | `def test_*` 函数数 | **245** | 附录 A-1 |
| Python Agent | `@pytest.mark.parametrize` 装饰器数 | **32** | 附录 A-1（实际 pytest item 数 > 函数数，故历史上报 374，见 2.2） |
| Java | 测试类 | **11** | `find jmall-backend/src/test -name "*.java"` |
| Java | `@Test` 数量 | **71** | 附录 A-2 |
| 前端 | 测试文件 | **7**（`src/__tests__/**`） | `find jmall-web/src/__tests__ -type f` |
| 前端 | `it()` 用例数 | **52** | 附录 A-3 |
| Go | `func Test*` | **4**（`service_test.go`） | 附录 A-4 |

> 注意：静态统计与"pytest 实际收集到的 item 数"不是一个口径（参数化会展开），写简历时统一用**运行后 pytest 报告的 item 数**。

### 2.2 历史全绿记录（E2，来自 `docs/v0.2-测试验收.md:13-20`，日期 2026-09-01，分支 v0.2）

| 范围 | 通过 | 失败 |
|---|---:|---:|
| Python Agent | 374 | 0 |
| Java 业务服务 | 70 | 0 |
| Vue 前端 | 52 | 0 |
| **合计** | **496** | **0** |

* **可复现命令**：`bash scripts/v0.2-regression.sh`（Python 用 uv+3.12 全 mock，Java 用 Maven 或 Maven Docker 镜像，前端 `npm run test:run && npm run build`）。
  脚本现在是贯通的、会返回非零退出码。
* **重要提醒**：这 496 是**当时 v0.2 提交状态**的结果。当前工作区多了 v0.3 未提交改动（新增 `test_shopper_intent.py` 5 例、修改 `AiProxyControllerTest.java` 等），
  **Java 71 ≠ 文档 70**，说明数量已变。要写进简历必须**重新跑一遍并保留新的运行产物**，不能直接引用 496。

### 2.3 文档记录的定点缺陷修复（E2，`docs/v0.2-测试验收.md:72-92`）

4 个"信息不足却被放行"的门禁缺陷，修复前后对比有明确记录：

| 案例 | 输入 | 修复前 | 修复后 |
|---|---|---|---|
| R1 主观评价伪装规格 | 规格：`很棒；喜欢` | `ready=true` / 85 分 | `needs_input` / 55 分 |
| R2 参数明确未知 | 规格：`材质未知；容量未知` | `ready=true` / 85 分 | `needs_input` / 55 分 |
| R3 人群明确未知 | 人群：`不知道呢` | `ready=true` / 85 分 | `needs_input` / 65 分 |
| R4 描述否定事实 | 整段否定描述 | `ready=true` / 85 分 | `needs_input` / 55 分 |

修复位置：`jmall-agent/app/agents/input_gate.py`（`_known_clauses` / `_has_concrete_marker` / `_grounded_facts` / `_has_audience`）。
文档同时记录了：14 条 HTTP 断言 14/14 通过且 **LLM Token 增量为 0**（因为闸门不调模型——这是一条非常漂亮的简历素材，但它属于文档记载，需要 §3.1 的脚本重跑后落到 2.4 的产物上）。

### 2.4 Image Scout 真实验收（E2，`docs/v0.2-测试验收.md:57-70`）

单次真实请求记录（**样本量 = 1，不能写成"成功率"**）：

* `serpapi`：接口 200 但上游 HTTP 401 → `provider_error`，候选 0 张。
* `qwen3.7-flash` / `qwen-flash`：调用成功但 `_normalize_candidates` 后 `no_results`，候选 0 张。
* `qwen-plus-latest`：**`status=ready`，候选 1 张**，来源主机 `img.alicdn.com`，风险标记 `license_unverified` / `visual_risk_unverified` / `resolution_unknown`。

### 2.5 Git 可证实的修改记录（E1，`git log`）

| 指标 | 数值 | 说明 |
|---|---|---|
| 仓库总提交数 | **3** | `chore: initialize clean jrunmall ai rag project`（2026-06-02）→ `release: Jmall v0.1`（2026-08-21）→ `release: Jmall v0.2`（2026-09-01） |
| **可证实的 Bug 修复提交** | **0** | `git log --oneline --grep="fix\|修复" -i` 为空；无 feature/fix 粒度提交历史 |
| 当前未提交改动 | 37 修改 + 9 未跟踪 | v0.3 全部工作区改动 |

**结论：Git 目前提供不了任何"修复数量 / 迭代频次"类证据。** 若要在简历上体现工程过程，唯一合规做法是把工作区改动按主题拆成规范提交（这属于 Git 操作，不属于改业务代码），后续再统计。

### 2.6 运行态指标（需要先把栈跑起来，E4 的前置）

`GET agent:18080/metrics` 与 `backend:10301/actuator/prometheus` 目前能输出的指标（仅当次进程累计，重启清零）：

| 指标 | 类型 | 标签 |
|---|---|---|
| `agent_requests_total` | Counter | agent_type, provider, model |
| `agent_tokens_total` | Counter | agent_type, direction |
| `agent_cost_total_usd` / `agent_cost_daily_usd` | Counter / Gauge | agent_type |
| `agent_budget_daily_usd` / `agent_over_budget` | Gauge | — |
| `agent_request_duration_seconds` | Histogram(buckets 0.5–60) | agent_type, provider |
| `image_search_requests_total` / `_duration_seconds` / `_candidates_total` | Counter/Histogram | provider, status |
| `jmall_input_assessments_total` / `_duration_seconds` | Counter/Histogram(buckets 0.001–1) | entrypoint, outcome |
| `jmall_generation_runs_total` / `_duration_seconds` / `_first_progress_seconds` | Counter/Histogram | entrypoint, platform, outcome |
| `jmall_platform_drafts_total` | Counter | platform, metadata, fallback |
| `jmall_editor_sessions_total` / `jmall_product_events_total` | Counter(Java Micrometer) | stage / event |

**P50/P95 的取法已经写在 Grafana 面板里**（`docker/grafana/dashboards/product-funnel.json`），可直接复用其 PromQL，例如：

```promql
histogram_quantile(0.95, sum by (le, entrypoint) (rate(jmall_input_assessment_duration_seconds_bucket[$__rate_interval])))
histogram_quantile(0.95, sum by (le, platform)   (rate(jmall_generation_first_progress_seconds_bucket[$__rate_interval])))
histogram_quantile(0.95, sum by (le, provider)   (rate(image_search_duration_seconds_bucket[$__rate_interval])))
```

⚠️ **直方图桶很粗**（如 `jmall_generation_duration_seconds` 桶 = 1/3/5/10/30/60/120/300/600 秒），`histogram_quantile` 只有插值精度，
简历上写 P95 时必须注明"基于 Prometheus 直方图插值"或直接导出**原始样本的精确分位数**（推荐后者，见 §3.6）。

### 2.7 代码/结构规模（E1，用于简历的"体量"描述）

178 个源码文件：Python 65（10,227 行）、Java 92（7,037 行）、前端 48（10,290 行）、Go 7（641 行）；
MySQL 11 张业务表；PostgreSQL `jmall_rag` 5 张表 + HNSW 向量索引 + 1 张**无写入方**的 `ai_request_logs`；9 个 Compose 服务。

---

## 三、目前不能直接量化、但可以通过新增评测脚本测量的指标

### 通用约定（隔离原则）

* 新增目录：**`jmall-eval/`**（新顶层目录，不进任何现有包）。
  * `jmall-eval/python/` — Python 评测脚本，**单向 import** `jmall-agent/app/*`，只读调用，**不改一行业务代码**。
  * `jmall-eval/java/` — 黑盒 HTTP 场景脚本（对 `:10301` 打接口，不改 Java 源码）。
  * `jmall-eval/datasets/` — 标注数据集（JSONL），每条含 `id / input / expected / rationale`。
  * `jmall-eval/results/<YYYY-MM-DD>/` — 唯一的结果落盘目录：`*.jsonl` 原始逐条记录 + `summary.json` 汇总 + `run_meta.json`（git commit、环境变量指纹、模型版本、脚本 sha256）。
* **不引入 mock-stub 替身去替换业务实现**；需要制造延迟/失败时，在评测脚本侧构造 provider/fake-transport 注入（依赖注入点是 `AgentOrchestratorGraph(settings, provider_factory, retrieval_service)`，天然可注入）。
* 每个脚本必须打印 **`pytest 风格 PASS/FAIL 计数 + 断言明细`**，并把原始记录落盘，保证"数字可追溯"。

---

### 3.1 【P0】Input Gate 充足性判定准确率

* **为什么值得测**：这是全项目唯一**零模型依赖、纯确定性**的决策组件；它直接决定"不浪费模型调用"（文档 2.3 已记载 Token 增量 0）。
  它能量产出**真正像样的 ML/规则系统评测表**：准确率、精确率、召回率、F1、混淆矩阵、分品类召回。
* **需要的数据集**：`jmall-eval/datasets/input_gate_cases.jsonl`，每条 `{id, product_info, expected_ready, expected_missing[], category}`。
  * 正例：6 大品类 × 段落/表格两种输入（可先从 `tests/test_input_gate*.py` 里已有样本抽取，避免凭空造数据）。
  * 反例：主观评价伪装规格、参数未知、人群未知、否定事实、空白仅名称品类、占位符（`测试商品`）、零宽字符注入。**每个反例必须写 `rationale`**，否则等于拍脑袋打标。
  * 建议规模：≥120 条（正/负大致均衡），并标注来源：哪些来自现有单测、哪些是新增。
* **需要新增脚本**：`jmall-eval/python/eval_input_gate.py`，直接调用 `app.agents.input_gate.assess_product_input`。
* **是否需要真实模型**：**不需要**，零成本、秒级。
* **输出**：`results/<date>/input_gate_records.jsonl`（逐条：`expected_ready / actual_ready / score / missing / questions`）、
  `input_gate_summary.json`（accuracy / precision / recall / F1 / 混淆矩阵 / 分品类与分反例类型的召回）、控制台表格。
* **可写进简历的说法示例**（跑出来后才写）：
  "针对 120 条标注样本的确定性输入闸门评测，整体准确率 X%，对抗类反例召回 Y%（N/Z）"。

---

### 3.2 【P0】全栈回归基线 + 覆盖率

* **为什么值得测**：这是所有其他指标的"入场券"。**当前没有任何一处开启了覆盖率统计**：
  * Python：`requirements.txt` 无 `pytest-cov`，无 `.coveragerc` / `pyproject.toml` 的覆盖配置。
  * Java：`pom.xml` 无 jacoco 插件。
  * 前端：`vite.config.ts` 配了 `coverage.provider: 'v8'`，但**未设 thresholds，且默认 `vitest run` 不出覆盖率**，需 `npm run test:coverage`。
* **需要新增**：仅**配置类改动**（加 pytest-cov、加 jacoco plugin、加 thresholds），不改业务逻辑。属于评测基础设施。
* **是否需要真实模型**：不需要（沿用 mock，见 `scripts/v0.2-regression.sh` 的环境变量）。
* **输出**：`results/<date>/regression_{python,java,web}.log` + `coverage_{python,java,web}.{xml,json}`，
  汇总出"用例总数/通过数/失败数/行覆盖率/分支覆盖率"。
* **注意**：分行/分支覆盖率要分别报，不要只报一个好看的数。

---

### 3.3 【P0】生成链路的结构化合规：事实一致性 + Skill 契约符合率

* **为什么值得测**：这是"AI 生成"唯一能**客观判定对错**的角度（另一角度是人评，见 §4）。
  判定依据全部来自代码里已有的东西：`platform_skills/definitions/*.json`（标题字数预算、关键词布局、禁用表达、详情结构）
  与提交的 `merchant_facts`（用于判定是否凭空捏造事实）。
* **需要的数据集**：`generation_cases.jsonl`（≥15 条商品，覆盖 6 品类；每个商品跑 1 个目标平台，另有 5 条跑满 5 平台）。
* **新增脚本**：`jmall-eval/python/eval_generation_contract.py`，对每次生成的 `draft` 输出做**规则校验器**：
  1. 标题长度 ≤ skill `titleBudget`（若 JSON 中字段名不同，以实际文件为准，脚本里做显式映射）；
  2. 禁用词命中的草稿数（`"最"`/"国家级"/"第一"/"根治" 等，词表取自 skill JSON 的禁用表达，不自创）；
  3. SEO 关键词数落在 8–12；
  4. 副标题非空；
  5. `platform_skill_id` / `platform_skill_version` 必现（即 `jmall_platform_drafts_total{metadata="present"}` 比率）；
  6. **事实一致性**：草稿中出现的规格/数值/材质是否都能在输入的 `merchant_facts` 文本中找到来源（用字符级/数字级匹配，输出"疑似编造项列表"供人工复核）；
  7. `fallback` / `guarded` 标记比例。
* **是否需要真实模型**：**需要**（Mock 模式返回的都是固定占位文案，第 6 项会全部失真）。
  成本可控：15 商品 × 1 平台 + 5 商品 × 5 平台 ≈ 40 次编排。跑之前必须设 `AGENT_COST_BUDGET_DAILY` 并在 `run_meta.json` 记录实际花费（从 `/api/admin/cost-stats` 取）。
* **输出**：`generation_records.jsonl`（每次编排的完整 `final_result` + 逐项校验结果）、
  `generation_summary.json`（各校验项通过率 + 每次编排 token/成本/耗时）。

---

### 3.4 【P1】单次生成的 Token / 成本 / 耗时分布（真实模型）

* **为什么值得测**：简历上"单次生成成本 ¥X / Tokens Y / 端到端 Zs"是极有说服力的数字，而且**项目里已经有完整的采集点**（cost_tracker + Prometheus + 各节点 `elapsed_ms`）。
* **数据来源**：`/api/admin/cost-stats`（内存最后一跳）+ `/metrics` 抓取 + SSE 每个 `agent_progress` 事件里的 `elapsed_ms`（`graph.py:426/479/591` 都会带）。
* **新增脚本**：`jmall-eval/python/eval_cost_latency.py` —— 对 N 次（建议 N≥20，且每个平台均衡）编排：
  记录 `总 tokens / USD / 每节点 elapsed_ms / first_progress 时间 / 端到端时间`，用**原始样本**算精确 P50/P95（不依赖 Prometheus 直方图插值）。
* **是否需要真实模型**：**需要**。建议与 3.3 **合并同一次运行**（一次编排同时产出质量与成本数据），避免双份开销。
* **输出**：`cost_latency_records.jsonl` + `cost_latency_summary.json`（按平台分组的 mean/P50/P95/min/max + 总计 token 与 USD）。
* **降本版**：同一脚本支持 `PROVIDER=mock` 跑"编排框架自身开销"（排队/并行/序列化耗时），明确标注为**不含模型耗时**。

---

### 3.5 【P1】任务恢复率 / 断点续跑成功率

* **为什么值得测**：README 宣称"页面刷新或网络中断后恢复任务"，代码里 Redis JobStore + SSE 后台任务确实存在，但 **`test_job_store.py` 只有 2 个用例且用 FakeRedis**（`docs/v0.2-测试验收.md:99` 自己写明"不证明真实 Redis 重启、跨进程和并发恢复"）。这是**当前最有价值的"补强型"评测**。
* **前置环境**：真实 Redis（`docker compose up -d redis agent`）。
* **新增脚本**：`jmall-eval/python/eval_job_resume.py`：
  场景矩阵：①正常运行到结束；②收到 `job_created` 后立刻断开 SSE → 轮询 `/jobs/{id}` 直到终态；③中途断开 → 重开 SSE；④任务不存在（404）；⑤跨用户越权读（应 403/404）。
  每个场景重复 N 次（建议 ≥20），**并用注入延迟的 provider 保证一定会"跑到一半断"**（在评测脚本侧构造，注入点是 graph 构造参数）。
* **是否需要真实模型**：**不需要**（用 mock 即可验证恢复语义；断连时机才是被测对象）。
* **输出**：`job_resume_records.jsonl`（job_id、场景、断开时机、是否拿到完整 final_result、终态状态、耗时）+ `job_resume_summary.json`（各场景恢复成功率）。
* **关键断言**：恢复得到的 `final_result` 必须与未断连那次的**关键字段一致**（等价性，而非仅仅有内容）。

---

### 3.6 【P1】Image Scout 安全性与去重 / 数量约束

* **为什么值得测**：`is_safe_public_url` / `_url_resolves_public` / `assess_image_risks` / 去重 / 上限 3 张，全是纯函数 + 可构造输入 →**可离线、可重复、零成本**，而且"SSRF 防护"是面试加分项。
* **数据集**：手写候选集（`image_scout_cases.jsonl`）：内网 IP、`127.0.0.1`、`localhost`、`.local/.internal` 后缀、带 userinfo 的 URL、`http://`、超长 URL、含空白/控制字符、
  重复 original_url、低分辨率（<600px 或 <360k px）、标题含水印/品牌词的相机—应有病原体。
* **新增脚本**：`jmall-eval/python/eval_image_scout.py`（纯函数调用 + 可选：起一个本地 HTTP server 模拟 "DNS 解析到内网" 的情况）。
* **是否需要真实模型/联网**：**不需要**（若要验 provider 的真实返回，单独标 `--live`，另计成本与配额）。
* **输出**：`image_scout_records.jsonl` + `image_scout_summary.json`（阻断率、误放行清单 — **任何一条误放行都要单独列出 URL**）。

---

### 3.7 【P2】RAG 检索质量（Recall@K / MRR@K / NDCG@K / 阈值分离度）

* **为什么值得测**：这是 RAG 项目最标准的量化面。`app/retrieval/quality.py` 的 LLM-as-Judge 已写好，缺的是**ground truth**。
* **前置**：必须先有真实语料。建议用 `jmall-agent/scripts/seed_professional_knowledge.py` / `prepare_demo_kb.py`（已存在）灌入 ≥20 篇电商运营文档（需在文档里记录文档来源与许可证），
  然后用真实 Embedding（`RAG_EMBEDDING_PROVIDER=openai-compatible`，**会产生费用**）生成 1024 维向量。
* **数据集**：`rag_cases.jsonl`：`{query, relevant_document_ids[]}`，每条至少 1 个相关文档；**20 条相关 + 10 条刻意无关**（可直接复用 `scripts/verify_thresholds.py` 里已经写好的 20 条查询）。
* **新增脚本**：`jmall-eval/python/eval_rag_retrieval.py`：
  1. 走 `RetrievalService.retrieve()` 取 top-k=5；
  2. 用 ground truth 算 `Recall@5 / MRR@5 / NDCG@5`（自己的落地金标准，不依赖 LLM）；
  3. **同时**调用已有 `RAGJudge` 产出 LLM 打分的 `hit_rate/avg_relevance`，与金标准做对比（这能量化"LLM-as-Judge 与人工标注的一致率"——很有谈资）。
* **是否需要真实模型**：检索阶段需要真实 Embedding；Judge 阶段需要真实 LLM。**若用 mock embedding（零向量），所有检索指标无意义，必须在报告里禁用该组合。**
* **输出**：`rag_records.jsonl`（每 query 的召回列表 + 命中情况 + judge 打分）+ `rag_summary.json`（Recall@5 / MRR@5 / NDCG@5 / 相关 vs 无关的 top1 分布 / 0.8 与 0.5 阈值的混淆表）。

---

### 3.8 【P2】发布门禁判定矩阵

* **为什么值得测**：14 类 `PublishBlocker` 是后端最硬核的规则逻辑，但目前**没有针对它的系统性用例集**（只有零散 service 层测试）。
* **数据集**：`publish_gate_cases.jsonl`：`{product_payload, expected_blockers[], should_publish}`（每类 blocker 至少 2 条：命中 / 不命中）。
* **新增脚本**：两种取法，推荐先做黑盒：
  * 黑盒：`jmall-eval/java/eval_publish_gate.py`（HTTP 打 `/api/products/{id}/publish-check` 或 Blackbox through ownership-bearing scenario Builder）；
  * 白盒（可选，属测试代码不属业务代码）：在 `jmall-backend/src/test/java/com/jmall/eval/` 下加一个参数化测试直接调 `ProductPublishService.check`。
* **是否需要真实模型**：不需要（门禁本身是纯规则；`compliance_rejected` 分支除外，可留待集成阶段）。
* **输出**：`publish_gate_records.jsonl` + `publish_gate_summary.json`（逐 blocker 类型的精确率/召回率 + 误放行清单）。

---

### 3.9 【P2】幂等 / 并发保护（**预期会发现缺陷**）

* **为什么值得测**：诚实地说，这是本项目**最可能测出问题**的一项。已确认代码中：`UserService.deductGold` 是读-改-写且无锁，`CheckinService.checkin` 先查后插且未捕获唯一键冲突，全项目无 `@Version`、无分布式锁（§1.7）。
* **新增脚本**：`jmall-eval/python/eval_idempotency.py`：
  对扣金币/签到/重复 SSE 提交/重复 consume job 等场景，用 N 并发（建议 10/50）重复请求，统计"重复扣费次数""重复签到成功数""重复扣金币导致的余额透支次数"。
* **输出**：`idempotency_records.jsonl` + `idempotency_summary.json`。
* **⚠️ 约定**：本阶段**不修业务代码**。如果测出 `超卖/重复扣费`，如实记录 —— 它本身是一条**诚实的技术发现**（可以在简历/面试里讲"我用评测发现了 X 缺陷"），
  整改要放到后续独立的功能提交里，且**不得把整治后的数字混入本次评测基线**。

---

### 3.10 【P3】Mock 降级路径覆盖

* **为什么值得测**：7 个图节点每个都有 except 分支，但**没人证明这些降级真的被走到了**。
* **新增脚本**：`jmall-eval/python/eval_graph_fallbacks.py` —— 注入"每个节点依次抛异常"的 provider/stub，断言：图仍能到达 `aggregate_results`、
  `final_result` 非空、`errors` 有正确前缀、`overall_status` 为约定值、`LLM Token 不增加`（降级前就失败的场景）。
* **是否需要真实模型**：不需要。
* **输出**：`graph_fallback_records.jsonl` + `graph_fallback_summary.json`（7 节点 × 故障注入的成功降级率、产出字段完整性）。

---

## 四、当前项目无法可靠测量的指标（不允许编造/估算）

| 指标 | 为什么现在不可测 | 硬证据 |
|---|---|---|
| **模型调用总次数 / 累计 Token / 累计成本（历史）** | `CostTracker._records` 是**进程内 List**，重启清零；`ai_request_logs` 表建了但**无任何代码写入**；仓库里没有任何历史调用日志或结果快照 | `cost_tracker.py:70`；`request_log_repository.py` 全文 10 行；`docker/postgres/init/01-rag-schema.sql:66`；`grep -rn "ai_request_logs" --include="*.py"` 为空 |
| **真实线上的 P50/P95/P99** | 没有真实用户流量；Prometheus 只有本地演示流量，且容器重启即清零；Redis/Container volume 里即便有数据也不可复现 | README:193 已自我声明"不等于用户 UV 或发布审计" |
| **生成文案的"质量"绝对分** | 没有人工标注的参考答案集；现有 `quality.py` 只有"相关性 1–5 的自证式打分"，属于**自评**，不是质量结论 | `app/retrieval/quality.py` 无 gold standard 输入 |
| **首字延迟 / 流式体验指标（真实模型）** | 在没付钱跑真实模型之前拿不到；用 mock 测出来的是框架开销，不能叫模型延迟 | `provider_factory.py` mock 分支不产生网络 IO |
| **Go 秒杀的 QPS / 延迟 / 超卖率** | **Go 服务没有 `/metrics` 端点**，Prometheus job `jmall-bench` 恒为 `up=0`；没有压测脚本 | `internal/seckill/handler.go:16-21`；`docs/v0.2-测试验收.md:103` |
| **Image Scout 候选"相关性/可用性"** | 样本量 = 1（见 2.4），且图片使用权未经核验（`image_scout_service.py` 主动打 `license_unverified` 标记） | `image_scout_service.py:238-243` |
| **缓存命中率** | 未见任何业务缓存读写实现（Redis 只用于 JobStore 与排行榜 ZSET） | 全仓库无 `@Cacheable` / 无 Python cache 读写 |
| **Git 中的 Bug 修复数量 / 迭代频次** | 仓库仅 3 个 release 级提交，v0.2 之后的全部改动未提交 | `git rev-list --count HEAD = 3`；`git log --grep="fix\|修复" -i` 为空 |
| **"提升 X%""节省 Y 小时" 类业务收益** | 没有任何对照组、没有真实使用者 | —— |

---

## 五、推荐评测顺序（按"简历价值 ÷ 获取成本"排序）

**原则**：先用零成本、确定性、可重复的实验把地基打牢，再花钱跑真实模型；每个阶段的产物都必须落到 `jmall-eval/results/<date>/`，且能写清"多久、跑了几条、花了多少钱"。

| 优先级 | 评测项 | 真实模型 | 预估成本 | 预估耗时 | 主要产出（可写进简历的形态） |
|---|---|---|---|---|---|
| **①** | §3.2 全栈回归基线 + 覆盖率 | 否 | 0 | 30–60 min | "34 个 Python 测试文件 / X 个用例 / 通过率 100% / 行覆盖 X%"，含三端分语言覆盖 |
| **②** | §3.1 Input Gate 准确率 | 否 | 0 | 2–4 h（主要是标注） | "120 条标注样本，准确率 X%，对抗反例召回 Y%；闸门不调用模型 → Token 消耗 0" |
| **③** | §3.6 Image Scout 安全与去重 | 否 | 0 | 2–3 h | "构造 N 类恶意/低质 URL，拦截率 X%，上限 3 张与去重 100% 生效" |
| **④** | §3.5 任务恢复率 | 否（需 Redis） | 0 | 3–4 h | "真实 Redis 下 5 类断连场景 × 20 次，恢复成功率 X%，恢复结果与未断连结果字段一致率 100%" |
| **⑤** | §3.10 降级路径覆盖 | 否 | 0 | 2–3 h | "7 个编排节点逐点故障注入，服务可用性 X%，降级产出字段完整率 Y%" |
| **⑥** | §3.3 + §3.4 生成契约 + 成本/延迟（**合并一次运行**） | **是** | 可控（建议先设 5 USD 预算上限，实际按 40 次编排计） | 4–6 h | "5 平台 × N 商品： Skill 契约符合率 X%、广告法禁用词命中 Y 条、事实一致性 Z%、Skill 版本可追溯率 100%；单次生成 P50/P95 耗时、Token、成本" |
| **⑦** | §3.8 发布门禁矩阵 | 否 | 0 | 4–6 h | "14 类阻断规则的系统化用例集，逐类精确率/召回率" |
| **⑧** | §3.7 RAG 检索质量 | **是**（Embedding + Judge） | 中（语料嵌入 + 判定调用） | 1–2 天（含灌语料） | "20 查询 × 人工标注：Recall@5 / MRR@5 / NDCG@5；LLM-as-Judge 与人工标注一致率" |
| **⑨** | §3.9 幂等 / 并发 | 否 | 0 | 3–4 h | 结果不确定：可能产出"发现 X 类并发缺陷"。**如实记录，不修饰** |

**排序理由**：
1. ①② 是唯一能**零成本拿到硬数字**的项，且 ② 直接对应"用规则把 AI 调用拦在门外"这一有说服力的设计点。
2. ③④⑤ 体现工程严谨性（安全、可靠性、容错），是面试追问密度最高的区域，且都不花钱。
3. ⑥ 是"AI 项目"的门面数据（成本/延迟/质量），但必须付钱，所以放到基建就绪之后，并强制绑定预算上限与 `run_meta.json` 留痕。
4. ⑧ 需要灌真实语料，投入最大，排后面；但它产出的是 RAG 岗最认的 IR 指标。
5. ⑨ 风险最高但洞察价值大，单独作为"诚实发现"处理，不影响主基线。

---

## 六、落地 checklist（下一阶段开工前）

1. `git` 先把 v0.3 工作区改动按主题拆提交（**不改业务代码，只是提交**），让 §2.5 的指标可用。
2. 建 `jmall-eval/` 目录骨架（`python/ java/ datasets/ results/`）+ `README.md`，说明"只读依赖业务代码、不修改业务代码"。
3. 补配置型工具：Python 加 `pytest-cov`、Java 加 jacoco、前端加 coverage thresholds（均属评测基础设施）。
4. 写 `jmall-eval/datasets/input_gate_cases.jsonl`（≥120 条，**每条带 rationale 与来源标注**）。
5. 跑 ① → 产出 `results/<date>/regression_*.log` 与覆盖率报告；**用新数字替换文档里的历史 496**。
6. 跑 ② → 产出 `input_gate_summary.json`；只有这一步之后，"准确率"这个词才允许出现在简历里。
7. 跑通之后，再决定是否花真实 Token 进入 ⑥⑧。

---

## 附录 A：复现本文档统计数据的命令

```bash
cd /Users/p668/projects/mall

# A-1 Python 用例与参数化
ls jmall-agent/tests/test_*.py | wc -l
grep -c "^\s*\(async \)\?def test_" jmall-agent/tests/*.py | awk -F: '{s+=$2} END {print s}'
grep -rn "@pytest.mark.parametrize" jmall-agent/tests/*.py | wc -l

# A-2 Java 用例
find jmall-backend/src/test -name "*.java" | wc -l
grep -rc "@Test" jmall-backend/src/test --include="*.java" | awk -F: '{s+=$2} END {print s}'

# A-3 前端用例
grep -rn "^\s*\(it\|test\)(" jmall-web/src/__tests__ | wc -l

# A-4 Go 用例
grep -c "func Test" jmall-bench/internal/seckill/service_test.go

# A-5 代码行数
find jmall-agent/app -name "*.py" | xargs wc -l | tail -1
find jmall-backend/src -name "*.java" | xargs wc -l | tail -1
find jmall-web/src -name "*.vue" -o -name "*.ts" | xargs wc -l | tail -1

# A-6 Git 事实
git rev-list --count HEAD
git log --oneline --grep="fix\|修复" -i | wc -l
git status --porcelain | wc -l

# A-7 历史全绿（会产生真实运行产物；属于评测动作，执行前请确认环境已就绪）
# bash scripts/v0.2-regression.sh
```

## 附录 B：文档中引用的关键代码位置速查

| 能力 | 位置 |
|---|---|
| LangGraph 编排图 | `jmall-agent/app/agents/graph.py:185-269` |
| 确定性输入闸门 | `jmall-agent/app/agents/input_gate.py:252-324` |
| LLM 分层路由 | `jmall-agent/app/llm/router.py:141-161` |
| 成本/Token 追踪 | `jmall-agent/app/llm/cost_tracker.py:86-199` |
| Prometheus 指标定义 | `jmall-agent/app/core/metrics.py:16-111` |
| RAG LLM-as-Judge | `jmall-agent/app/retrieval/quality.py:50-243` |
| pgvector 检索 SQL | `jmall-agent/app/repositories/knowledge_base_repository.py:498-533` |
| 已有阈值评测雏形 | `jmall-agent/scripts/verify_thresholds.py` |
| Image Scout 安全过滤 | `jmall-agent/app/services/image_scout_service.py:104-266` |
| 平台 Skill 执行与兜底 | `jmall-agent/app/agents/style_adapter.py:64-199` |
| 任务持久化与恢复 | `jmall-agent/app/services/job_store.py`、`app/api/agent.py:150-274` |
| 发布门禁 | `jmall-backend/src/main/java/com/jmall/service/ProductPublishService.java` |
| 后端埋点指标 | `jmall-backend/.../service/ProductMetrics.java`（`jmall_editor_sessions_total`、`jmall_product_events_total`） |
| SSE + 任务恢复（前端） | `jmall-web/src/views/merchant/ProductEditor.vue` |
| 回归脚本 | `scripts/v0.2-regression.sh`、`scripts/e2e-regression.sh` |
