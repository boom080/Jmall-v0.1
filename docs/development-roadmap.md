# Jmall 开发路线图

> 基于当前代码完成度评估，按优先级排列的开发计划。

---

## 一、现状评估

### 已完成的（✅）

| 模块 | 功能 | 状态 |
|------|------|------|
| 基础设施 | Docker Compose 8 容器一键部署 | ✅ |
| Agent 服务 | 5 Agent 协作（编排/调研/文案/审查/风格） | ✅ |
| Agent 服务 | 分层 LLM 路由（Strong/Medium/Cheap） | ✅ |
| Agent 服务 | RAG 双模存储 + Fact Guard 反幻觉 | ✅ |
| Agent 服务 | Token 成本追踪 + 管理接口 | ✅ |
| Java 后端 | 注册/登录/JWT 认证 | ✅ |
| Java 后端 | 商品 CRUD + 分页 | ✅ |
| Java 后端 | 购买交易（随机倍率返利） | ✅ |
| Java 后端 | 签到（连续签到奖励递增） | ✅ |
| Java 后端 | 成就系统（5 个成就） | ✅ |
| Java 后端 | 金币流水账（不可变 ledger） | ✅ |
| Java 后端 | 排行榜（消费/销售双榜） | ✅ |
| Java 后端 | AI Proxy + 金币计费网关 | ✅ |
| Go 秒杀 | Redis Lua 原子化库存扣减 | ✅ |
| 前端 | 买家：商品列表、商品详情 | ✅ |
| 前端 | 商家：商品编辑器 + AI Agent 面板 | ✅ |
| 前端 | 成就墙、收藏页 | ✅ |
| 前端 | 登录/注册/JWT 自动续期 | ✅ |
| 前端 | Pinia 状态管理 + Axios R 包装自动解包 | ✅ |
| 监控 | Prometheus + Grafana | ✅ |

### 部分完成的（🔶）

| 模块 | 功能 | 缺失 |
|------|------|------|
| 前端 Dashboard | 工作台统计卡片 | 硬编码 stats=0，未调后端 API |
| 前端 ProductEditor | AI Agent 面板 | applyStyle() 未将 AI 结果写入表单；进度动画用 setTimeout 模拟 |
| 前端 ProductEditor | 商品编辑器 | AI 调真实 API 但有 mock fallback 兜底 |
| 前端 ProductDetail | 收藏按钮 | 只做了本地 toggle，从未调后端 API |
| 前端 购买动效 | PurchaseEffect 组件 | App.vue 的 provide 漏传 goldEarned 参数，导致金币数显示为 0 |
| 前端 Collection | 收藏展示页 | 模板用 `item.product?.title` 但后端返回的是扁平 Product 数组，数据取不到 |
| 后端/前端 | 搜索功能 | 无商品搜索接口 |
| 前端/后端 成就 | 定义不一致 | 后端只定义了 5 个成就，前端 types 里硬编码了 8 个 |
| Go 秒杀 | Redis Streams | dead-letter 补偿入口未做 |

### 占位/空壳（❌）

| 页面 | 当前状态 |
|------|---------|
| KnowledgeBase.vue | 11 行，"即将上线" |
| StoreManager.vue | 11 行，"店铺装修功能即将上线" |
| Profile.vue | 11 行，"个人中心功能即将上线" |

### 测试覆盖（⚠️）

| 服务 | 测试文件 | 状态 |
|------|---------|------|
| jmall-agent (Python) | 12 个 | ✅ |
| jmall-bench (Go) | 1 个 | 🔶 |
| jmall-backend (Java) | 0 个 | ❌ |
| jmall-web (Vue) | 0 个 | ❌ |

---

## 二、开发阶段

### 第零阶段：修 Bug（P0 — 立马修）

**目标**：把已发现的功能缺陷修掉，否则演示会翻车。

| # | Bug | 位置 | 预估 |
|---|-----|------|------|
| 0.1 | **收藏按钮不调 API** — ProductDetail "收藏" 只切换本地状态，从未 POST 到后端，刷新后消失 | ProductDetail.vue:70-72 | 小 |
| 0.2 | **收藏页数据取不到** — Collection.vue 模板用 `item.product?.title` 但后端返回扁平 Product[] | Collection.vue:16 + CollectionService.java | 小 |
| 0.3 | **购买动效金币显示为 0** — App.vue 的 provide 只传了 2 个参数，漏了 goldEarned | App.vue:95-97 + ProductDetail.vue:62 | 小 |
| 0.4 | **applyStyle 不写入表单** — AI 生成结果只在面板展示，点"应用"只弹 toast，不填表单 | ProductEditor.vue:229-237 | 小 |
| 0.5 | **成就定义前后端不一致** — 后端 5 个，前端 types 里 8 个，SALE_10/NIGHT_OWL/WHALE 永远不会解锁 | AchievementService.java + types/index.ts | 小 |

### 第一阶段：补齐核心闭环（P0 — 功能补全）

**目标**：让商家上架 → AI 辅助 → 买家购买 → 金币流转 的主链路完整可演示。

| # | 任务 | 涉及模块 | 预估 |
|---|------|---------|------|
| 1.1 | **Dashboard 接真实数据** — 从后端拉取 productCount / totalSales / storeLevel，替换硬编码 stats | 前端 + 后端 | 小 |
| 1.2 | **知识库管理页面** — 创建 KB、上传 TXT/PDF、查看文档列表、删除，对接 Agent 的 `/api/merchant/knowledge-bases` 接口 | 前端 | 中 |
| 1.3 | **Profile 个人中心** — 展示用户信息、金币余额、签到状态、操作历史（金币流水） | 前端 + 后端 | 中 |
| 1.4 | **商品搜索** — 后端增加关键词搜索接口（MyBatis-Plus like 查询），前端商品列表加搜索框 | 后端 + 前端 | 小 |
| 1.5 | **端到端联调测试** — 注册 → 签到 → 上架商品（AI 辅助）→ 买家购买 → 金币变化 → 成就解锁 → 排行榜更新，完整走通一遍 | 全部 | 中 |

### 第二阶段：体验打磨（P1 — 演示质量）

**目标**：让产品"像真的"，提升演示说服力。

| # | 任务 | 涉及模块 | 预估 |
|---|------|---------|------|
| 2.1 | **店铺装修页面** — 编辑店铺名称、品类、描述、上传 banner，Store 表已有 decoration_config JSON 字段 | 前端 + 后端 | 中 |
| 2.2 | **购买动效** — 点击购买后弹出 confetti + 暴击倍率动画（canvas-confetti 已安装但未集成到购买流程） | 前端 | 小 |
| 2.3 | **商品图片上传** — 目前前端用 placeholder 图片，需要对接图片上传（可用 OSS 或本地存储） | 后端 + 前端 | 中 |
| 2.4 | **风格预览卡片** — ProductEditor 中 AI 生成不同平台风格后，以卡片形式展示（目前只渲染了 JSON 文本），加上配色模拟 | 前端 | 中 |
| 2.5 | **错误状态覆盖** — 检查每个页面的 loading / empty / error 三种状态是否齐全 | 前端 | 小 |

### 第三阶段：Agent 能力增强（P2 — 技术亮点）

**目标**：让 AI 部分更智能、更可控。

| # | 任务 | 涉及模块 | 预估 |
|---|------|---------|------|
| 3.1 | **Agent 并行执行** — 当前 LangGraph 是串行节点，MarketResearch 和 CopyGeneration 实际上可以并行（调研不依赖文案），用 LangGraph 的 parallel 能力改造 | Agent | 中 |
| 3.2 | **流式输出 (SSE)** — Agent orchestrate 改为 Server-Sent Events，前端实时看到每个 Agent 的进度和输出，而非长时间 loading | Agent + 后端 + 前端 | 大 |
| 3.3 | **RAG 检索质量评估** — 建立 RAG 质量指标（命中率、相关性），可以用 LLM-as-Judge 自动打分 | Agent | 中 |
| 3.4 | **多轮对话上架** — 商家可以通过对话式交互逐步完善商品信息，而非一次性表单填写 | Agent + 前端 | 大 |
| 3.5 | **成本看板 (Grafana)** — 把 CostTracker 的数据暴露为 Prometheus metrics，在 Grafana 中呈现 token 消耗趋势 | Agent + 监控 | 小 |

### 第四阶段：测试与稳定性（P3 — 工程化）

**目标**：补测试、加监控、保证可维护性。

| # | 任务 | 涉及模块 | 预估 |
|---|------|---------|------|
| 4.1 | **Java 后端单元测试** — Service 层核心逻辑（Auth/Transaction/Checkin/AiProxy）单元测试 | 后端 | 大 |
| 4.2 | **Java 后端集成测试** — Testcontainers + MySQL/Redis 集成测试 | 后端 | 中 |
| 4.3 | **前端组件测试** — 关键组件（ProductEditor AI 面板、ProductFeed）用 vitest + vue-test-utils | 前端 | 中 |
| 4.4 | **E2E 测试** — Playwright 覆盖核心用户流程（注册→购买→签到） | 前端 | 中 |
| 4.5 | **Go 秒杀死信队列** — dead-letter 可见化 + 人工补偿入口 | Bench | 中 |
| 4.6 | **API 文档** — FastAPI 自动生成的 /docs 完善（补充描述和示例），Spring Boot 端接入 Swagger | 全部 | 小 |

---

## 三、优先级矩阵

```
                    影响力
              低           高
          ┌──────────┬──────────┐
    低    │ 4.5 死信  │ 2.1 店铺  │
          │ 4.6 文档  │ 2.3 图片  │
成        │          │ 1.4 搜索  │
本   ─────┼──────────┼──────────┤
          │ 4.1 测试  │ 1.1 Dash  │
    高    │ 4.2 集成  │ 1.2 知识库 │
          │ 3.2 流式  │ 1.3 个人  │
          │ 3.4 对话  │ 1.5 联调  │
          └──────────┴──────────┘
```

**建议执行顺序**：先做完第一阶段（1.1-1.5），核心闭环就能完整演示。然后根据实际可用时间在第二阶段到第四阶段中按需挑选。

---

## 四、里程碑

| 里程碑 | 完成标志 | 依赖 |
|--------|---------|------|
| **M1: 核心闭环** | 注册→签到→AI上架→购买→成就→排行 全链路可演示 | 第一阶段全部 |
| **M2: 演示就绪** | 有图片、有动效、有店铺装修，看起来像真的电商平台 | M1 + 第二阶段核心项 (2.1-2.4) |
| **M3: 技术深度** | Agent 并行 + SSE 流式 + RAG 质量评估 | M2 + 第三阶段核心项 (3.1-3.3) |
| **M4: 生产就绪** | 测试覆盖率 >60%，API 文档齐全，死信可补偿 | M3 + 第四阶段 |
