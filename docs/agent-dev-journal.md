# Agent 开发技术日志

> 记录 Jmall 项目中 Agent 开发遇到的问题、解决方案及面试可讲的技术亮点。
> 每次发现值得关注的技术点后追加到本文档中。

---

## 一、技术点索引

| # | 技术点 | 分类 | 标签 |
|---|--------|------|------|
| 1 | [LangGraph 多 Agent 线性编排 + 容错降级](#1-langgraph-多-agent-线性编排--容错降级) | Agent 架构 | `LangGraph` `容错` `多Agent协作` |
| 2 | [分层 LLM 路由：按任务复杂度分派模型](#2-分层-llm-路由按任务复杂度分派模型) | Agent 架构 | `成本优化` `模型路由` `分层策略` |
| 3 | [Fact Guard 事实守卫 — LLM 反幻觉机制](#3-fact-guard-事实守卫--llm-反幻觉机制) | 安全 & 质量 | `反幻觉` `后处理` `合规` |
| 4 | [AI Proxy 模式 + 金币计费网关](#4-ai-proxy-模式--金币计费网关) | 基础设施 | `网关模式` `计费` `服务解耦` |
| 5 | [双模 RAG 存储：JSON File / PostgreSQL+pgvector](#5-双模-rag-存储json-file--postgresqlpgvector) | RAG & 存储 | `pgvector` `策略模式` `无DB也能跑` |
| 6 | [Go 秒杀服务：Redis Lua 原子化库存扣减](#6-go-秒杀服务redis-lua-原子化库存扣减) | 性能 & 并发 | `Lua脚本` `原子操作` `热点库存` |
| 7 | [Mock-First 开发模式：零 API Key 本地开发](#7-mock-first-开发模式零-api-key-本地开发) | 工程化 | `Mock` `本地开发` `解耦` |
| 8 | [JSON 输出多策略解析](#8-json-输出多策略解析) | Prompt 工程 | `结构化输出` `鲁棒性` `解析` |
| 9 | [合规审查两步策略：规则 + LLM](#9-合规审查两步策略规则--llm) | 安全 & 质量 | `规则引擎` `混合审查` |
| 10 | [Token 成本追踪系统](#10-token-成本追踪系统) | 成本控制 | `token计价` `预算管理` `可观测` |
| 11 | [Embedding 向量维度 Runtime 校验](#11-embedding-向量维度-runtime-校验) | RAG & 存储 | `防御性编程` `pgvector` |
| 12 | [中文电商 Prompt 工程实践](#12-中文电商-prompt-工程实践) | Prompt 工程 | `电商领域` `中文Prompt` `结构化` |
| 13 | [Vue provide/inject 类型安全缺口与响应式陷阱](#13-vue-provideinject-类型安全缺口与响应式陷阱) | 前端架构 | `Vue3` `依赖注入` `类型安全` |
| 14 | [前后端成就定义的契约漂移与枚举收敛](#14-前后端成就定义的契约漂移与枚举收敛) | 全栈协作 | `契约管理` `枚举` `数据一致性` |
| 15 | [Spring 拦截器路径排除导致 authenticated 端点丢失用户上下文](#15-spring-拦截器路径排除导致-authenticated-端点丢失用户上下文) | 基础设施 | `Spring Interceptor` `认证` `AntPathMatcher` |
| 16 | [微服务间 API 路由契约不一致：Java Proxy 与 Python Agent 路径偏差](#16-微服务间-api-路由契约不一致java-proxy-与-python-agent-路径偏差) | 全栈协作 | `API Gateway` `路径契约` `跨服务调试` |
| 17 | [LangGraph 状态键与节点名命名空间冲突](#17-langgraph-状态键与节点名命名空间冲突) | Agent 架构 | `LangGraph` `StateGraph` `Breaking Change` |
| 18 | [Agent 服务遗留 schema 引用导致 PostgreSQL 查询失败](#18-agent-服务遗留-schema-引用导致-postgresql-查询失败) | 基础设施 | `数据库迁移` `配置管理` `遗留清理` |

---

## 二、技术深入分析

### 1. LangGraph 多 Agent 线性编排 + 容错降级

**遇到的问题**

5 个 AI Agent（编排、市场调研、文案、合规审查、风格适配）需要串联执行。线下 LLM API 随时可能超时、限流或返回非预期结果。如果其中一个 Agent 挂了，整个流程不应该崩溃 — 对最终用户来说，拿到"部分结果 + 错误提示"远比一个 500 错误有用。

**解决方案**

采用 LangGraph `StateGraph` 构建 6 节点线性流水线，每个节点内置 try/except + 条件边实现容错：

```
START -> parse_intent -> market_research -> copy_generation
       -> compliance_review -> style_adaptation -> aggregate_results -> END
```

关键设计：
- **每个节点独立 try/except**：异常被捕获、记录到 `state["errors"]`，然后注入可用的 fallback 数据（如市场调研失败时返回空关键词 + 兜底建议），流程继续
- **条件边**：`add_conditional_edges` 根据 `state["errors"]` 决定路由 — 大多数错误只是记录并继续，只有编排意图解析失败才直接跳到聚合
- **Fallback 链**：文案生成失败 → 用原始商品标题生成兜底文案；合规审查不可用 → 返回 warning + 建议人工审查

```python
# graph.py - 节点的容错模式
async def _run_market_research(self, state: AgentGraphState) -> AgentGraphState:
    try:
        agent = self._get_market_research()
        update = await agent.run(dict(state))
        state.update(update)
    except Exception as exc:
        logger.error("market_research failed: %s", exc)
        state["errors"].append(f"market_research: {exc}")
        state["market_research"] = {
            "trends_summary": f"市场调研暂时不可用（{exc}）",
            "hot_keywords": [],
            "suggestions": ["请稍后重试市场调研"],
        }
    return state
```

**面试可讲点**

- "不是简单的 try-catch，而是设计了完整的 fallback 数据链 — 每个节点失败后注入的兜底数据结构与成功时完全一致，下游节点不需要感知上游是否失败"
- "LangGraph 的条件边让错误路由变成了声明式配置，而不是在节点内写 if-else 面条代码"
- "对用户透明：前端看到的永远是 `{overall_status, result, errors[]}` 三件套，即使内部走了 3 个 fallback，用户也能知道哪些部分是可用的、哪些需重试"
- "实际场景中 LLM API 的可用性远低于传统 API，这种设计保证了 95%+ 的请求至少能返回部分结果"

---

### 2. 分层 LLM 路由：按任务复杂度分派模型

**遇到的问题**

一个电商上架流程涉及多种 AI 任务：市场搜索与总结（简单）、文案创作（复杂）、合规审查（简单）、风格改写（中等）。所有任务用同一个最强模型？太贵。所有任务用同一个便宜模型？文案质量差。如何在不同任务之间动态选择模型以优化性价比？

**解决方案**

将 Agent 按 `agent_type` 分类到三个成本层级：

```python
TASK_COMPLEXITY = {
    "market_research": "cheap",     # 简单搜索+摘要
    "compliance_review": "cheap",   # 规则检查+简单 LLM
    "copy_generation": "strong",    # 创意写作
    "style_adaptation": "medium",   # 内容改写
    "orchestration": "strong",      # 规划+分解
}
```

路由优先级设计：
1. **Per-tier 覆盖**：`AGENT_STRONG_PROVIDER` / `AGENT_MEDIUM_PROVIDER` / `AGENT_CHEAP_PROVIDER` 可分别指定不同层级的模型供应商
2. **全局 fallback**：`AI_PROVIDER` → 自动检测（哪个 API Key 配了用哪个） → `mock`
3. **模型也可按层覆盖**：`AGENT_STRONG_MODEL=deepseek-v4-pro`，不设则用 provider 默认

实际配置示例：
```
AGENT_STRONG_PROVIDER=deepseek   AGENT_STRONG_MODEL=deepseek-v4-pro  # 文案
AGENT_MEDIUM_PROVIDER=qwen       AGENT_MEDIUM_MODEL=qwen-plus        # 风格
AGENT_CHEAP_PROVIDER=deepseek    AGENT_CHEAP_MODEL=deepseek-v4-flash # 搜索
```

**面试可讲点**

- "这是一个经典的策略模式应用于 LLM 路由 — 不是简单选一个模型，而是让每个任务用'刚好够好'的模型，降低总体 token 成本 60-80%"
- "路由逻辑是确定性的（基于静态映射），不是让 LLM 自己判断复杂度 — 避免了'用贵的模型判断该用哪个便宜模型'的套娃问题"
- "成本感知的架构设计：中等复杂度用 Qwen Plus（$0.4/$1.2 per 1M tokens），创意写作用 DeepSeek V4 Pro，搜索审查用 DeepSeek V4 Flash（便宜 10x 以上）"
- "可扩展性：新增一个 Agent 类型只需在 TASK_COMPLEXITY 加一行映射，路由层零改动"

---

### 3. Fact Guard 事实守卫 — LLM 反幻觉机制

**遇到的问题**

LLM 在生成商品文案时倾向于"脑补" — 输入只说了"不粘锅"，它可能写出"采用美国杜邦特氟龙涂层，通过 FDA 认证"。这在电商场景是巨大的合规风险，一旦被举报虚假宣传，商家要承担法律责任。

**解决方案**

设计了两层后处理机制：

**第一层：高风险声明字典**
```python
HIGH_RISK_FACTS = {
    "减少油烟": "请商家提供官方检测报告确认油烟减少数据",
    "永不粘锅": "请避免使用绝对化用语，替换为'优质不粘涂层'",
    "FDA认证": "请商家提供FDA认证编号",
    "销量第一": "请提供第三方销量排名数据来源",
    "100%天然": "请提供成分检测报告",
}
```

**第二层：保守替换表**
```python
CONSERVATIVE_REPLACEMENTS = {
    "永不粘锅": "持久不粘",
    "绝对不含有害物质": "通过安全检测",
    "全球首创": "创新设计",
}
```

逻辑流程：
1. LLM 生成文案
2. 遍历 `HIGH_RISK_FACTS`，检查生成内容是否包含这些短语
3. 如果包含且**输入证据中未提及** → 列入 `pending_confirmations`（要求商家确认），同时用 `CONSERVATIVE_REPLACEMENTS` 替换
4. 如果输入证据中包含（如商家自己在知识库写了"通过FDA认证"）→ 放行

**面试可讲点**

- "这不是 prompt 约束（'请不要编造'），而是确定性后处理 — prompt 约束不能 100% 保证，代码可以"
- "区分了'规则驱动的安全网'和'LLM 驱动的灵活性'：规则负责拦截已知高风险模式，LLM 负责创意生成，各司其职"
- "对商家形成闭环：不是直接删除风险内容，而是标记为'待确认'，商家可以主动提供证据解封 — 既保证安全，又不损失信息"
- "可配置的字典设计意味着法务团队可以直接维护 HIGH_RISK_FACTS 而不需要改代码"

---

### 4. AI Proxy 模式 + 金币计费网关

**遇到的问题**

Python Agent 服务负责 AI 推理，Java 后端负责业务逻辑。如果前端直接调 Agent 服务，后端无法控制用量和计费。而且 LLM API 调用是花钱的 — DeepSeek V4 Pro 虽然便宜但大量调用也会产生费用。如何对用户透明地控制 AI 使用成本？

**解决方案**

Java 后端的 `AiProxyService` 作为 AI 网关：

```
前端 → Java 后端 (10301) → Python Agent (18080) → LLM API
          ↑
     扣金币 / 退款
```

核心机制（`AiProxyService.java:110-138`）：

```java
private R forwardAndCharge(String path, Object body, long cost) {
    Long userId = UserContext.getUserId();

    // Step 1: 扣金币（余额不足直接拒绝，不调用 AI）
    if (userId != null && cost > 0) {
        boolean deducted = userService.deductGold(userId, cost, "ai_cost", "AI service usage");
        if (!deducted) {
            return R.error(10020, "insufficient gold for AI service");
        }
    }

    try {
        // Step 2: 转发请求到 Python Agent 服务
        ResponseEntity<String> response = restTemplate.postForEntity(url, entity, String.class);
        return R.ok("AI service response", response.getBody());
    } catch (Exception e) {
        // Step 3: 失败退款
        if (userId != null && cost > 0) {
            userService.addGold(userId, cost, "refund", "Refund for failed AI service");
        }
        return R.error(50001, "AI service error: " + e.getMessage());
    }
}
```

定价策略：

| 操作 | 金币消耗 | 说明 |
|------|---------|------|
| 完整上架流程 (orchestrate) | 100g | 5 个 Agent 协作 |
| 文案生成 (product copy) | 200g | 核心价值功能 |
| 合规审查 (review) | 150g | 安全保障 |
| 市场洞察 (insights) | 150g | 数据驱动 |

**面试可讲点**

- "这是一个典型的 API Gateway + Billing 模式：网关层处理认证、计费、转发、容错，Agent 服务专注于推理逻辑"
- "金币经济充当了 rate limiting 的自然形式 — 不需要复杂的令牌桶算法，用户签到赚金币 → 花金币调 AI → 没钱了就等明天签到，天然形成成本天花板"
- "Java ↔ Python 微服务解耦：Agent 服务不知道金币的存在，后端不知道 LLM 的具体实现，两边通过 HTTP 协议解耦"
- "先扣后返的退款策略：只有成功从余额扣减才发起 AI 请求，失败后自动退款到 GoldLedger（不可变流水），避免了对账不一致"

---

### 5. 双模 RAG 存储：JSON File / PostgreSQL+pgvector

**遇到的问题**

Agent 服务需要向量检索能力（pgvector），但本地开发时不想装 PostgreSQL。正式环境用 pgvector 实现高效余弦相似度搜索，本地环境用 JSON 文件也能跑完整的 RAG 流程。如何让同一套代码适配两种完全不同的存储后端？

**解决方案**

`KnowledgeBaseRepository` 实现了策略模式的双后端切换：

```python
class KnowledgeBaseRepository:
    def __init__(self, settings, data_dir="data"):
        if settings.database_url:
            self._engine = create_engine(settings.database_url)
            self._mode = "postgresql"
            self._ensure_tables()
        else:
            self._db_path = os.path.join(data_dir, "merchant_ai_store.json")
            self._mode = "json"
            self._ensure_json_file()
```

两类后端的关键差异处理：

| 维度 | JSON 文件模式 | PostgreSQL + pgvector 模式 |
|------|-------------|---------------------------|
| 存储 | 单个 JSON 文件 | 3 张表 (knowledge_bases, documents, chunks) |
| 向量搜索 | Python `_dot_product()` 内存计算 | pgvector `<=>` 余弦距离算子 |
| 并发 | 不适合（文件锁） | 完整的事务隔离 |
| 启动要求 | 零依赖 | 需要 pgvector 扩展 |
| 适用场景 | 本地开发、demo | 生产环境 |

向量搜索的 SQL 生成：
```sql
-- pgvector 模式
SELECT id, content, 1 - (embedding <=> :query_embedding) AS score
FROM knowledge_chunks
WHERE knowledge_base_id = :kb_id
  AND 1 - (embedding <=> :query_embedding) >= :min_score
ORDER BY score DESC
LIMIT :top_k
```

**面试可讲点**

- "不是简单的 if-else，而是两个后端实现同一套 Repository 接口，上层 Service 层完全无感知 — 标准的策略模式"
- "向量搜索的两条路径：Python 实现 dot product 完全自包含（适合演示），pgvector 实现用 HNSW 索引（适合生产），同一套测试跑在两套后端上"
- "迁移路径自然：本地开发用 JSON 文件 → 配置 DATABASE_URL → 自动切换到 pgvector，零代码改动"
- "这种设计模式在开源项目中也适用：让贡献者不需要搭建完整的 PostgreSQL 环境就能运行全部 RAG 功能"

---

### 6. Go 秒杀服务：Redis Lua 原子化库存扣减

**遇到的问题**

秒杀场景的核心痛点：库存扣减不是原子的。如果先读库存、判断充足、再写回 — 两个并发请求可能同时读到库存=1，都判断为充足，都执行扣减，最终超卖。传统的 Java 分布式锁方案在高并发下成为瓶颈。

**解决方案**

用 Go 语言实现独立秒杀服务，核心是用 Redis Lua 脚本将整个"检查 + 扣减 + 写事件"逻辑原子化：

```lua
-- seckillLuaScript (Go store.go)
-- KEYS[1]=stockHash  KEYS[2]=idemKey(用户幂等)
-- KEYS[3]=requestKey KEYS[4]=streamName KEYS[5]=activityKey

-- 1. 活动存在性检查
if redis.call("EXISTS", activityKey) == 0 then
  return {"ACTIVITY_NOT_FOUND", 0, ""}
end

-- 2. 幂等检查（同一用户重复提交）
if redis.call("EXISTS", idemKey) == 1 then
  return {"DUPLICATE_REQUEST", remaining, previousEventId}
end

-- 3. 时间窗口检查
local startAt = redis.call("HGET", activityKey, "startAt")
local endAt = redis.call("HGET", activityKey, "endAt")
if timestamp < startAt then return {"NOT_STARTED", ...} end
if timestamp > endAt   then return {"ENDED", ...} end

-- 4. 库存检查 + 扣减（原子操作）
local stock = tonumber(redis.call("HGET", stockHash, "stock"))
if stock < quantity then return {"SOLD_OUT", stock, ""} end

-- 5. 扣减 + 幂等标记 + 写入订单 Stream（三合一）
redis.call("HSET", stockHash, "stock", stock - quantity)
redis.call("SET", idemKey, requestId, "EX", 86400)
redis.call("XADD", streamName, "*", "orderToken", orderToken, ...)
```

**面试可讲点**

- "Lua 脚本在 Redis 中是一体执行的，天然避免竞态条件 — 不需要分布式锁，性能提升数量级"
- "为什么用 Go 而不是继续用 Java？— Go 的 goroutine 调度开销极低，适合 Redis 网络 IO 密集型场景；而且秒杀服务独立部署，即使挂了也不影响主站"
- "幂等 Key 设计：用 `{activityId}:{userId}` 而非 `{requestId}` — 防止同一用户换 requestId 重复下单"
- "`XADD` 写入 Redis Stream：不是直接落数据库，而是发布事件由 Java 消费者异步消费 → 避免了秒杀高峰对 MySQL 的冲击"
- "双后端设计 (MemoryStore / RedisStore)：单元测试用内存实现，集成测试和生产用 Redis，Store 接口保证行为一致性"

---

### 7. Mock-First 开发模式：零 API Key 本地开发

**遇到的问题**

Agent 服务依赖 3 个外部 API（DeepSeek、Qwen、Tavily 搜索），如果不配 API Key 服务直接报错。新开发者 clone 项目后无法立刻跑起来体验功能，前端团队也需要能独立开发不依赖 LLM 服务。

**解决方案**

所有外部依赖都有 Mock 实现：

| 外部依赖 | Mock 实现 | 特点 |
|---------|----------|------|
| LLM (DeepSeek/Qwen) | `mock_provider.py` | 返回固定但合理的 JSON 响应 |
| Embedding | `mock_embedding_provider.py` | SHA256 确定性向量（相同输入=相同向量） |
| Tavily 搜索 | `tools/search.py` 内置 fallback | 返回预设的电商趋势数据 |

`ProviderFactory.chat()` 的 fallback 链：
```python
def chat(self, provider_name, model, messages):
    if provider_name == "mock":
        return self.mock_provider.chat(messages)  # 无需 API Key
    try:
        return self.real_provider.chat(messages)
    except httpx.HTTPError:
        return self.mock_provider.chat(messages)  # API 挂了也不崩
```

**面试可讲点**

- "Mock 不是简单的 return hardcoded string — Embedding 的 mock 用 SHA256 对输入做确定性映射，保证相同文本在 mock 模式下向量相似度计算依然有效"
- "Mock 和真实 Provider 实现同一接口，通过 factory 创建 — 切换模式只需要改一个环境变量 `AI_PROVIDER=mock`"
- "实际开发流程：前端用 mock 模式独立开发 UI → 后端联调用真实 API → CI 跑测用 mock（零成本） → 生产用真实 API"

---

### 8. JSON 输出多策略解析

**遇到的问题**

LLM 的 JSON 输出不可靠 — 有时直接输出纯 JSON，有时包裹在 ```json 代码块里，有时前后有解释文字，有时 JSON 本身有格式问题。如果直接 `json.loads()`，30%+ 的请求会因为解析失败而报错。

**解决方案**

实现四层降级解析策略：

```python
def _parse_json_response(self, content: str) -> dict:
    # 策略 1: 直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 策略 2: 提取 markdown 代码块
    import re
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 策略 3: 提取最外层花括号
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # 策略 4: 返回原始内容作为 text fallback
    return {"raw_text": content, "parse_error": True}
```

**面试可讲点**

- "不是对 LLM 说'请输出合法 JSON'就完事了 — 多策略解析把解析成功率从 ~70% 提升到 99%+"
- "正则提取 `{.*}` 看似粗糙，但在中文场景下非常有效（LLM 经常在 JSON 前后加'好的，以下是结果：'）"
- "策略 4 不抛异常而是返回标记了 `parse_error` 的 dict：让调用方可以降级处理而不是直接 500"

---

### 9. 合规审查两步策略：规则 + LLM

**遇到的问题**

电商合规审查有两个层次的需求：确定性违规（广告法禁词"最好""第一"、价格异常 999999 元）和语义性违规（夸大宣传、虚假承诺）。前者用规则匹配 100% 准确，后者需要 LLM 理解语义。只用规则 → 漏掉语义违规，只用 LLM → 浪费 token 在简单的字符串匹配上。

**解决方案**

`ReviewerAgent` 采用两步审查：

**第一步：规则检查（确定性、零成本）**
```python
# 广告法禁词检查
FORBIDDEN_TERMS = ["最好", "第一", "唯一", "国家级", "世界级", "100%", "永不"]
# 价格异常检查
if price > 99999 or (original_price > 0 and price < original_price * 0.01)
# 标题长度检查
if len(title) > 120
```

**第二步：LLM 审查（语义理解）**
- 将规则检查的结果作为上下文传给 LLM
- LLM 专注于规则无法覆盖的语义问题（虚假承诺、过度售卖、不实对比）
- 最终 `review_result` 合并两部分结果

**面试可讲点**

- "这是一个典型的混合决策系统：确定性规则做前置过滤，LLM 做语义兜底 — 既保证关键违规 100% 拦截，又不浪费 token"
- "规则和 LLM 之间不是互斥而是互补：规则结果作为 LLM 的 'hint' 传入，让 LLM 更聚焦于规则未覆盖的灰色地带"
- "可演进性：前期规则少 LLM 多（快速上线），后期规则不断完善（降低 LLM 调用频率和成本）"

---

### 10. Token 成本追踪系统

**遇到的问题**

使用 LLM API 产生的费用难以追踪。一次 orchestrate 调用会触发 4-6 次 LLM 调用（不同 Agent），每次调用的 provider、model、token 数量都不同。如何知道每天花了多少钱、钱花在哪个 Agent 上？

**解决方案**

`CostTracker` 维护内存级别的调用记录，每次 LLM API 返回后记录：

```python
class TokenUsage:
    provider: str      # deepseek / qwen
    model: str          # deepseek-v4-pro / qwen-plus
    input_tokens: int
    output_tokens: int
    agent_type: str     # copy_generation / market_research ...
    timestamp: datetime

    @property
    def cost_usd(self) -> float:
        pricing = DEFAULT_PRICING[self.model]
        return (input_tokens / 1_000_000) * pricing["input"] \
             + (output_tokens / 1_000_000) * pricing["output"]
```

内置多模型定价表（USD/1M tokens）：

| 模型 | 输入 | 输出 |
|------|------|------|
| deepseek-chat | $0.14 | $0.28 |
| qwen-plus | $0.40 | $1.20 |
| gpt-4o | $2.50 | $10.00 |

每日预算预警：
```python
if self.get_daily_cost() > self.settings.agent_cost_budget_daily:  # default $5.00
    logger.warning("Daily cost budget exceeded!")
```

暴露管理接口：`GET /api/admin/cost-stats` 返回 `{daily_cost, total_cost, cost_by_agent, over_budget}`。

**面试可讲点**

- "成本可观测性是 LLM 应用上线的前提 — 不知道花了多少钱就没办法做成本优化"
- "按 Agent 维度统计：一眼看出是文案 Agent 最烧钱（strong tier）还是市场调研 Agent 调用最多（频繁搜索），针对性优化"
- "定价表硬编码而非数据库：模型价格变动频率低（每季度甚至每年），硬编码避免了额外的数据库查询；需要更新时改一行代码即可"
- "`cost_by_agent` 的分组统计让成本归属清晰 — 如果某个 Agent 的成本突然飙升，可以立即定位到是调用频率问题还是模型切换问题"

---

### 11. Embedding 向量维度 Runtime 校验

**遇到的问题**

不同 Embedding 模型生成的向量维度不同：text-embedding-v4 是 1024 维，text-embedding-v3 是 1536 维，而 mock 模式默认只有 8 维。如果在 pgvector 建表时指定了 `vector(1024)` 但实际 embedding 输出了 1536 维 → 插入失败；如果用了 8 维 → 向量搜索质量极差但不会报错，悄悄退化。

**解决方案**

`EmbeddingService` 在首次调用 embedding API 后校验维度：

```python
def _validate_dimensions(self, dimensions: int) -> None:
    expected = self.settings.resolved_embedding_dimension()
    if dimensions != expected:
        raise RuntimeError(
            f"Embedding dimension mismatch: got {dimensions}, "
            f"expected {expected} (from pgvector schema or config). "
            f"Check your RAG_EMBEDDING_MODEL setting."
        )
```

**面试可讲点**

- "这是一个防御性编程的典范 — 在最早可能的时机（首次 embedding 调用后）发现配置错误，而不是等到插入数据库报错"
- "配置文件中有 `resolved_embedding_dimension()` 这种动态解析方法 — 未配置时默认 8（mock 模式），配置后从 env 读取，给开发者明确的配置引导"

---

### 12. 中文电商 Prompt 工程实践

**遇到的问题**

通用 LLM 生成的电商文案缺乏平台特色 — 淘宝、拼多多、京东、小红书、苏宁的用户心智完全不同。拼多多要"砍价""拼团"的紧迫感，小红书要"种草""真实体验"的生活感，京东要"正品""物流快"的信任感。如何让同一个模型产出 5 种不同风格？

**解决方案**

每个电商平台定义了结构化的风格描述：

```python
SUPPORTED_STYLES = {
    "pinduoduo": {
        "name": "拼多多",
        "description": "价格导向、紧迫感强、口语化、强调拼团和低价",
        "tone": "marketing",
    },
    "xiaohongshu": {
        "name": "小红书",
        "description": "种草风格、生活方式化、真实体验分享、年轻化表达",
        "tone": "warm",
    },
    ...
}
```

StyleAdapterAgent 将品类通用文案 + 目标平台风格描述 + 合规结果一起喂给 LLM，让它在这个约束空间内改写。改写前后保持核心卖点不变，只调整语气、用词、排版风格。

**面试可讲点**

- "把风格定义为结构化数据（name/description/tone）而不是直接写死在 prompt 里 — 新增平台只需加一行配置"
- "5 种风格共用一个 StyleAdapterAgent + 同一个 medium-tier 模型 → 成本可控"
- "tone 参数（marketing/professional/warm）是可下游消费的元数据，前端可以根据 tone 选择不同的视觉风格渲染"

---

### 13. Vue provide/inject 类型安全缺口与响应式陷阱

**遇到的问题**

购买动效组件 `PurchaseEffect` 需要接收 3 个参数（product、multiplier、goldEarned），通过 Vue 的 `provide/inject` 机制从 `App.vue` 传递到各子页面。但 `App.vue` 中的 `provide` 回调只声明了 2 个参数：

```typescript
// App.vue — 只接收了 2 个参数
provide('triggerPurchaseEffect', (product: any, multiplier: number) => {
  purchaseEffectRef.value?.play(product, multiplier)  // goldEarned 丢失!
})

// ProductDetail.vue — 调用时传了 3 个参数
triggerPurchaseEffect?.(product.value, result.multiplier, result.goldEarned)
```

JavaScript 的弱类型特性让这个 Bug 静默存活 — 第三个参数被无声丢弃，`PurchaseEffect.play()` 的 `gold` 形参始终为 `undefined`，导致购买后金币数永远显示 0。TypeScript 的类型注解 `(product: any, multiplier: number)` 不会警告调用方传了多余的参数（TS 的类型兼容性设计允许函数接收少于声明的参数）。

**解决方案**

修复核心是让 provide 回调签名与调用方和消费方对齐：

```typescript
// App.vue — 修复后
provide('triggerPurchaseEffect', (product: any, multiplier: number, goldEarned: number) => {
  purchaseEffectRef.value?.play(product, multiplier, goldEarned)
})
```

同时发现更深层的问题：`ProductFeed.vue` 中也有一份独立的 `triggerPurchaseEffect` 调用逻辑，存在相同隐患。更健壮的方案是用类型化的 InjectionKey：

```typescript
// 理想方案（TypeScript + Vue3）
import type { InjectionKey } from 'vue'
interface PurchaseEffectFn {
  (product: Product, multiplier: number, goldEarned: number): void
}
export const TRIGGER_KEY: InjectionKey<PurchaseEffectFn> = Symbol('triggerPurchaseEffect')
```

**面试可讲点**

- "Vue3 的 provide/inject 是字符串 key + any 类型的组合，TypeScript 无法在编译期发现参数数量不匹配 — 这是前端动态类型系统中的经典防御缺口"
- "根源在于没有使用 InjectionKey 做类型约束。`provide(key, value)` 中的 value 是 `any` 类型，Vue 的类型推导到此为止。一旦函数签名在 3 个文件中各写一遍，漂移是必然的"
- "更深层的问题：购买动效的触发逻辑在 ProductDetail 和 ProductFeed 中重复了。正确做法是提取一个 `usePurchase()` composable，集中管理购买→动效→金币更新的流程，消除多份拷贝之间的不一致"
- "修复后不只是改了 1 个参数，而是将采购流程中的 3 个关注点（扣款、动效、成就）封装为统一的行为契约"

---

### 14. 前后端成就定义的契约漂移与枚举收敛

**遇到的问题**

项目有 3 处「成就」定义：

| 位置 | 数量 | 说明 |
|------|------|------|
| 前端 `types/index.ts` | 8 个 | UI 展示用，含 name/description/icon |
| 后端 `AchievementService.AchievementDef` | 5 个 | 解锁逻辑的实际执行者 |
| 数据库 `jmall_achievement` | 无约束 | 只存 key 字符串，无外键/ENUM |

后端少定义了 3 个成就（SALE_10, NIGHT_OWL, WHALE），导致前端成就墙有 3 个永远锁着的"僵尸成就"。更隐蔽的是 `COLLECTOR_10` — 前端描述为「收藏 10 件商品」，后端却统计的是「购买 10 次」。名称相同但含义不同，没有一个人（代码审查者、测试者、AI）发现过。

**解决方案**

分三步修复：

**第一步：后端补齐成就定义**
```java
// AchievementService.java — 新增 3 个成就
SALE_10("SALE_10", "Hot Seller", "Sell 10 items from your store", 800L),
NIGHT_OWL("NIGHT_OWL", "Night Owl", "Make a purchase between midnight and 5 AM", 300L),
WHALE("WHALE", "Whale", "Earn over 1,000,000 gold from a single purchase", 5000L);
```

**第二步：修复 COLLECTOR_10 语义（name-behavior mismatch）**
```java
// 修复前 — 统计购买次数（与"收藏"语义不符）
txnWrapper.eq(Transaction::getBuyerId, userId);
if (transactionRepository.selectCount(txnWrapper) >= 10) { ... }

// 修复后 — 统计 UserCollection 记录（匹配"收藏"语义）
colWrapper.eq(UserCollection::getUserId, userId);
if (collectionRepository.selectCount(colWrapper) >= 10) { ... }
```

**第三步：在正确的时机触发检查**

COLLECTOR_10 需要在收藏操作后触发，但 `CollectionService.add()` 原来没有调用 `achievementService.checkAndUnlock()`。同样，SALE_10（卖家售出 10 件）在 `TransactionService.purchase()` 中只检查了买家成就，漏了卖家的。

```java
// CollectionService.add() — 收藏后触发成就检查
collectionRepository.insert(collection);
achievementService.checkAndUnlock(userId);  // 新增

// TransactionService.purchase() — 买家 + 卖家双检查
achievementService.checkAndUnlock(buyerId);  // 已有
achievementService.checkAndUnlock(store.getUserId());  // 新增 — 触发 SALE_10
```

**面试可讲点**

- "这是一个典型的'契约漂移'问题：3 个数据源定义了同一概念但各自演化，没有任何编译期或运行时的约束保证它们一致。在有多个开发者并行推进前后端时，这种情况几乎必然发生"
- "根源设计缺陷：成就定义应该是单一事实来源（Single Source of Truth）。当前架构中前端和后端各自硬编码枚举 — 正确的做法是后端定义一个 `/api/achievements/definitions` 端点，前端动态拉取。这样新增成就只需要改后端，前端自动同步"
- "COLLECTOR_10 的问题更值得讲 — UI 文案和数据库操作描述的是两件不同的事，但它竟然通过了代码审查。说明 name-behavior mismatch 是最隐蔽的一类 bug：变量名/UI 文案告诉你它在做 A，代码实际在做 B。审查者往往被命名'说服'跳过对实现逻辑的仔细检查"
- "修复过程中还发现了一个牵连 bug：Achievements.vue 把 API 服务对象 `gamificationApi` 当作 Pinia store 构造函数调用。这种错误在运行时才会暴露，再次说明前端缺乏编译期类型检查的危险"

---

### 15. Spring 拦截器路径排除导致 authenticated 端点丢失用户上下文

**遇到的问题**

`GET /api/stores/mine` 始终返回 `code:10040 "store not found"`，但直接查询 `/api/stores/1` 能正确返回店铺数据，且 MySQL 中确认店铺存在（user_id=5）。后端日志显示 MyBatis 查询参数为 `null` — 即 `UserContext.getUserId()` 返回 null。同样的 bug 也影响 `GET /api/products/mine`。

原因链：为了让产品列表和店铺详情可以公开访问，`WebConfig` 中把 `/api/stores/**` 和 `/api/products/**` 加入了拦截器排除列表。但 Spring 的 `AntPathMatcher` 中 `/**` 匹配**所有子路径**，导致 `/api/stores/mine` 和 `/api/products/mine` 也被排除 — 拦截器的 `preHandle()` 根本不执行，`UserContext` 从未被设置，`getUserId()` 返回 null。而 `getById(1)` 不需要 UserContext（直接按 path variable 查询），所以它碰巧能工作 — 这掩盖了问题。

```java
// WebConfig.java — 有缺陷的排除规则
.excludePathPatterns(
    "/api/stores",      // 只排除 /api/stores 精确路径
    "/api/stores/**",   // 排除 /api/stores/ 下所有子路径 — 包括 /mine！
    "/api/products/**", // 同样的问题：排除 /api/products/mine
)
```

这是典型的"过度排除"bug：为了公开只读端点而打开了比预期更大的访问窗口，同时意外移除了需要认证的端点所需的认证上下文。

**解决方案**

改用 **optional auth 模式**替代路径排除：让所有 `/api/**` 请求都经过拦截器，但允许 GET 请求在无 token 的情况下通过（不设置 UserContext 即可）。写操作（POST/PUT/DELETE）仍然必须有有效 token。

**LoginInterceptor.java** — 核心改动：

```java
@Override
public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
    String authHeader = request.getHeader("Authorization");

    if (!StringUtils.hasText(authHeader) || !authHeader.startsWith("Bearer ")) {
        // GET/OPTIONS 允许无认证通过 — UserContext 保持空，由业务层按需检查
        if ("GET".equalsIgnoreCase(request.getMethod())
                || "OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }
        response.setStatus(401);
        return false;
    }

    String token = authHeader.substring(7);
    try {
        Long userId = jwtUtil.getUserIdFromToken(token);
        String username = jwtUtil.getUsernameFromToken(token);
        LoginUser loginUser = new LoginUser();
        loginUser.setUserId(userId);
        loginUser.setUsername(username);
        loginUser.setRole("user");
        UserContext.setUser(loginUser);
        return true;
    } catch (Exception e) {
        // 无效 token 在 GET 请求上也放行（前端可提示重新登录）
        if ("GET".equalsIgnoreCase(request.getMethod())
                || "OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }
        response.setStatus(401);
        return false;
    }
}
```

同时将 WebConfig 的排除列表恢复为最小集：
```java
.excludePathPatterns(
    "/api/auth/register",
    "/api/auth/login"
)
```

**面试可讲点**

- "Spring MVC 的 `excludePathPatterns` 使用 AntPathMatcher，`/**` 会递归匹配所有子路径。当你为一个控制器排除只读端点时，很容易连带排除同路径前缀下的认证端点。在有 RESTful 路由设计（同路径不同方法）的系统中，路径排除的粒度不够 — 它不能按 HTTP method 区分"
- "正确的做法是让拦截器支持 optional auth：所有请求都进入拦截器，在内部根据 HTTP method 和 token 存在性决定是否放行。这样读操作可以公开访问（UserContext 为空），写操作必须携带有效 token。这比维护不断膨胀的排除列表更可维护 — 新增一个公开只读端点不需要修改拦截器配置"
- "这种 bug 的特点是 `getById(id)` 能工作但 `getMyStore()` 不能 — 前者不需要当前用户上下文（靠 URL 参数定位），后者需要从 ThreadLocal 中取 userId。两个接口返回类似的业务数据，但一条走通一条失败，这是'隐形认证依赖'的特征：看似相同的 API 调用，内部是否依赖 `UserContext` 决定了它能不依赖拦截器工作"
- "从更广的视角看，这反映了认证架构的两种范式之争：**路径级认证**（URL pattern + 排除列表）vs **操作级认证**（在每个操作中检查权限）。Spring Security 的 `@PreAuthorize` 和自定义注解属于后者。在项目初期用路径排除快速上线没问题，但在端点数量增长后，应该考虑迁移到声明式注解认证"

---

### 16. 微服务间 API 路由契约不一致：Java Proxy 与 Python Agent 路径偏差

**遇到的问题**

AiProxyService 中 styles、product/copy、product/review、product/insights 等端点全部返回 404。具体表现为 Java 后端日志显示 `404 Not Found`，但 Agent 服务明明在运行。

对比发现 Java 代理和 Python Agent 使用了不同的路径前缀：
- Java `AiProxyService`：`/api/ai/styles`, `/api/ai/product/copy`, `/api/ai/product/review`, `/api/ai/product/insights`
- Python Agent 实际路由：`/api/styles` (styles_router), `/api/agent/product/copy` (agent.router)

不一致的根因是 Java 侧用了 `"/api/ai/"` 前缀，但 Agent 的 `agent.router` 使用 `prefix="/agent"` 而 `styles_router` 没有额外前缀。对外（前端）暴露的 `ApiProxyController` 使用 `/api/ai` 前缀是正确的 — 前端不需要知道内部的路径结构。但代理层向 Agent 转发时，应该使用 Agent 实际注册的路径。

```java
// AiProxyService.java — 修复前（错误的 Agent 路径）
public R getStyles() {
    return forwardGet("/api/ai/styles");  // Agent 没有 /api/ai 前缀，只有 /api/styles
}
public R generateProductCopy(...) {
    return forwardAndCharge("/api/ai/product/copy", ...);  // Agent 是 /api/agent/product/copy
}

// 修复后（匹配 Agent 实际路由）
public R getStyles() {
    return forwardGet("/api/styles");
}
public R generateProductCopy(...) {
    return forwardAndCharge("/api/agent/product/copy", ...);
}
```

**面试可讲点**

- "微服务间 API 路由不匹配是最常见的联调失败原因之一。问题不在于路径写错了，而在于**没有统一的契约** — Java 和 Python 两个服务各自'猜测'对方的路径约定，但没有一个中间件或文档来同步。这就像两个人各自画了一张地图，结果对不上"
- "解决方法通常是：1) OpenAPI/Swagger spec 作为服务间契约的单一事实来源；2) 在 API Gateway 层做路径重写；3) 或者至少有一个共享的 constants 文件。本项目中前端的 `/api/ai/*` 是面向客户的 API 路径，后端代理层负责内部路由转译 — 这本身是好的模式（前端不感知后端微服务拓扑），但代理层到 Agent 的路径映射需要同步维护"
- "这种 bug 的特点是**直接访问 Agent 能 work，通过代理不行**。调试方法：先确认 Agent 的 `/docs` (FastAPI 自动生成) 列出所有路由，然后逐条对比 Java 的 proxy 方法。FastAPI 的 `/openapi.json` 可以用作自动化契约测试的数据源"

---

### 17. LangGraph 状态键与节点名命名空间冲突

**遇到的问题**

Agent 启动后访问知识库列表返回 `500 Internal Server Error`。查看日志发现：

```
ValueError: 'market_research' is already being used as a state key
```

崩溃发生在 `AgentOrchestratorGraph.__init__()` → `_build_graph()` → `graph.add_node("market_research", ...)`。

根因：LangGraph v0.2+ 中，`StateGraph` 的 state keys（TypedDict 字段）和 node names 共享同一个命名空间。`AgentGraphState` TypedDict 定义了 `market_research: Optional[dict]`，同时 `add_node("market_research", ...)` 尝试用相同的字符串注册节点，触发冲突。

这个问题在 LangGraph 的 CHANGELOG 中是一个 documented breaking change — 早期版本允许 state key 和 node name 同名，但在并行执行优化中引入了这个约束。

**解决方案**

将冲突的节点名改为带前缀的版本（只改 3 处）：

```python
# graph.py — 修复
graph.add_node("node_market_research", self._run_market_research)  # was: "market_research"

# 对应的条件边也需要更新
graph.add_conditional_edges(
    "parse_intent",
    self._after_parse_intent,
    {
        "market_research": "node_market_research",  # 路由目标改为新节点名
        "copy_generation": "copy_generation",
        "error": "aggregate_results",
    },
)

graph.add_conditional_edges(
    "node_market_research",  # 源节点也改为新名称
    ...
)
```

不需要修改状态键名 — 那样需要改动 5 个文件中所有 `state["market_research"]` 和 `state.get("market_research", {})` 的引用。

**面试可讲点**

- "LangGraph v0.2 引入了一个 breaking change：state keys 和 node names 不能同名。这是因为内部实现中两者共享同一个 channel 命名空间。如果你从一个老的 LangGraph 示例代码开始，这个错误几乎是必然会遇到的 — 大多数教程用 state key 的名字来命名对应的 node"
- "修复策略的选择体现了重构中的**最小改动面原则**：改 node name 只需要 3 处，改 state key 需要跨 5 个文件改十几处。前者更安全，且 bug 更少"
- "这个问题也暴露了 TypedDict 和 StateGraph 之间的隐式耦合 — 框架层面无法在编译期检测到这种冲突，只能运行时抛异常。如果 LangGraph 在 `add_node` 时能检查并给出更明确的错误信息，或者 IDE 插件能提前提示，开发体验会好很多"

---

### 18. Agent 服务遗留 schema 引用导致 PostgreSQL 查询失败

**遇到的问题**

修复 LangGraph 冲突后，知识库列表仍然返回 500。日志显示：

```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) 
relation "jrunmall_merchant_ai.knowledge_bases" does not exist
```

Agent 的 SQLAlchemy 查询硬编码了 `jrunmall_merchant_ai` schema，但项目重构后（从 jrunmall → jmall）PostgreSQL 初始化脚本 (`01-rag-schema.sql`) 创建的 schema 名为 `jmall_rag`。

```python
# config.py — 修复前
merchant_schema: str = Field("jrunmall_merchant_ai", env="MERCHANT_AI_SCHEMA")
#                           ^^^^^^^^^^^^^^^^^^^^^^ 旧项目遗留下的默认值

# config.py — 修复后
merchant_schema: str = Field("jmall_rag", env="MERCHANT_AI_SCHEMA")
```

**面试可讲点**

- "这是典型的'项目重命名遗留问题' — 代码从 git 仓库名到 package 名都改了，但有一些**隐藏在默认值里的字符串常量**没有被扫到。这些字符串不会引起编译错误或 linter 警告，只有在运行时才会暴露"
- "防御措施：1) 项目重命名后用 grep 全量搜索旧名称；2) 关键配置项不要依赖默认值，在 docker-compose 或 K8s ConfigMap 中显式设置；3) 启动时的 readiness probe 应该验证数据库连接和表是否可访问，而不是等到第一个请求才暴露"
- "注意到 BOTH 问题（#17 和 #18）都导致了同一个 API 返回 500 — 但根因完全不同。第一个 bug 修完后 API 仍然失败，因为 LangGraph 异常发生后 Agent 的依赖注入层抛了另一个异常，遮盖了真实的 DB schema 问题。多层错误叠加是微服务调试中最耗时的场景"

---

## 三、开发时间线

### 2026-08-07 上午 — 项目初始化

- 项目从 gulimall/jrunmall 重构为 jmall，清理历史代码
- Docker Compose 一键部署环境搭建完成（8 个容器：MySQL, PostgreSQL+pgvector, Redis, Backend, Agent, Frontend, Bench, Prometheus+Grafana）
- Agent 服务 5 大 Agent 全部就位：Orchestrator / MarketResearch / Copywriter / Reviewer / StyleAdapter
- 分层 LLM 路由实现完成（Strong/Medium/Cheap 三层）
- RAG 双模存储完成（JSON File / PostgreSQL+pgvector）
- Fact Guard 反幻觉机制已实现
- Token 成本追踪系统已实现
- Go 秒杀服务 Redis Lua 原子操作已实现
- Java 后端 AI Proxy + 金币计费网关已实现
- .env 配置完成，AI_PROVIDER=deepseek（真实调用），所有服务正常运行

### 2026-08-07 下午 — Phase 0 Bug 修复 + Phase 1 核心闭环（8 项完成）

**Phase 0 — Bug 修复：**
- **Bug 0.1**: 收藏按钮在未登录用户访问商品详情时触发 401 重定向 → 为 check API 调添加 `authStore.isAuthenticated` 守卫
- **Bug 0.2**: 收藏页数据取不到 → 模板已正确使用 `item.title`（而非 `item.product?.title`），验证通过无修改
- **Bug 0.3**: 购买动效金币显示为 0 → App.vue `provide` 回调丢失 `goldEarned` 参数，修复为 3 参数版本
- **Bug 0.4**: applyStyle 不写入表单 → ProductEditor.vue 的 `applyStyle()` 现在将 AI 生成的 title + detail 填入表单字段
- **Bug 0.5**: 成就前后端不一致 → 后端新增 SALE_10/NIGHT_OWL/WHALE 3 个成就，修复 COLLECTOR_10 从「统计购买」改为「统计收藏」

**额外修复：**
- ProductEditor.vue: `computed` import 从文件末尾移到顶部 import 语句
- Achievements.vue: `gamificationApi()` 调用改为 `useGamificationStore()`（API 服务对象被错误地当 Pinia store 构造函数调用）
- CollectionService: 收藏操作后触发 `achievementService.checkAndUnlock()`
- TransactionService: 购买后也为卖家触发成就检查（SALE_10）

**Phase 1 — 核心闭环补全：**
- **1.1 Dashboard**: 从 `GET /api/stores/mine` 拉取 totalSales/level，从 `GET /api/products/mine` 拉取 productCount，替换硬编码 stats
- **1.2 知识库管理**: 完整重写 KnowledgeBase.vue — KB 列表、创建、TXT 上传、文档查看、删除，发现并修复了 Java AiProxy 路由路径不匹配 (Agent 用 `/api/merchant/knowledge-bases` 但 Java 代理用 `/api/knowledge-bases`)
- **1.3 Profile 个人中心**: 用户信息卡片、金币余额、签到状态、金币流水时间线、快捷入口（成就/收藏/排行）
- **1.4 商品搜索**: 后端 ProductService 添加 keyword LIKE 查询（title + description），前端 ProductFeed 添加搜索框 + Enter 触发 + 清空重置

**发现并修复的新 Bug：**
- AiProxyService 路由路径不匹配 — 修复为 `/api/merchant/knowledge-bases` 并添加 `forwardGet/forwardPost/forwardDelete` 方法 + Jackson JSON 解析
- AiProxyService `forward()` 返回 raw string 包裹在 R.ok() 中 → 新增 `parseForwardResponse()` 用 ObjectMapper 解析为结构化 JSON
- ProductFeed.vue 数据解包错误 — `result.items || result` 应为 `result.records || result.items`，后端返回 `Map.of("records", ..., "total", ...)`
- 新增 `GET /api/user/gold-ledger` 端点（金币流水查询）为 Profile 页面提供数据源
- 新增 `GET /api/ai/knowledge-bases/{kbId}/documents` 和 `DELETE /api/ai/knowledge-bases/{kbId}` 代理端点

### 2026-08-07 下午（续）— Phase 1.5 端到端联调 + Auth 架构修复

**Phase 1.5 — 端到端联调测试：**
- ✅ 注册/登录：成功（JWT token 正确签发，sub=userId，alg=HS384）
- ✅ 签到：buyer1 签到获得 700 gold（连续 1 天）
- ✅ 商品浏览（公开访问）：GET /api/products 无需认证返回 1 件商品
- ✅ 商品搜索（keyword=龙井）：正确过滤 1 条结果
- ✅ 购买流程：buyer1 购买 product#1（12800 gold），卖家获得 12800 gold 销售收入
- ✅ 购买动效：x10 multiplier 触发，buyer 额外获得 128000 gold
- ✅ 成就解锁：seller → SHOP_OWNER，buyer → FIRST_PURCHASE（含 100 gold bonus）
- ✅ 金币流水：buyer 和 seller 两侧 ledger 记录完整（purchase/sale/bonus/checkin）
- ✅ Dashboard：totalSales=1, level=1, productCount=1
- ✅ 排行榜：/api/leaderboard/spenders 和 /api/leaderboard/sellers 正常返回
- ✅ 前端页面：/ /dashboard /profile /achievements 全部返回 200

**发现并修复的关键 Bug — Auth 拦截器路径排除导致 UserContext 为 null：**
- `GET /api/stores/mine` 和 `GET /api/products/mine` 因 WebConfig 中 `/api/stores/**` 和 `/api/products/**` 被排除出拦截器，`UserContext.getUserId()` 返回 null
- 根因：Spring AntPathMatcher 的 `/**` 匹配所有子路径，无法区分公开只读端点（`/api/stores/1`）和需认证端点（`/api/stores/mine`）
- 修复：改为 optional auth 模式 — 拦截器覆盖全部 `/api/**`，GET/OPTIONS 无 token 也能通过（UserContext 为空），POST/PUT/DELETE 必须有有效 token
- WebConfig 排除列表从 8 条缩减为 2 条（仅 /api/auth/register 和 /api/auth/login）
- 详见 [技术点 #15](#15-spring-拦截器路径排除导致-authenticated-端点丢失用户上下文)

**已知遗留问题：**
- MyBatis-Plus 分页 total=0（PaginationInnerInterceptor 在 3.5.9 版本中无法解析，待调研）
- 排行榜 sellers 端点缺少 username 字段（只返回 storeId/totalSales/rank）

### 2026-08-07 下午（续2）— Agent 服务修复 + 13 项全量回归测试通过

**Agent 服务 Bug 修复（3 项）：**

**Bug A1 — LangGraph 状态键/节点名冲突：**
- `AgentGraphState` TypedDict 中的 `market_research` 字段与 `add_node("market_research", ...)` 同名
- LangGraph v0.2+ 中两者共享命名空间，运行时抛出 `ValueError: 'market_research' is already being used as a state key`
- 修复：节点改名为 `node_market_research`（3 处改动），避免大规模修改 state key（跨 5 个文件）

**Bug A2 — PostgreSQL schema 遗留引用：**
- Agent `config.py` 默认 `merchant_schema = "jrunmall_merchant_ai"`，但初始化脚本创建的是 `jmall_rag`
- 导致 SQLAlchemy 查询 `jrunmall_merchant_ai.knowledge_bases` → `UndefinedTable`
- 修复：默认值改为 `jmall_rag`

**Bug A3 — Java ↔ Python Agent 路由路径不匹配：**
- `AiProxyService` 使用错误的 Agent 路径前缀：
  - `forwardGet("/api/ai/styles")` → Agent 实际是 `/api/styles`
  - `forwardAndCharge("/api/ai/product/copy", ...)` → Agent 实际是 `/api/agent/product/copy`
- 修复：4 个 proxy 方法的转发路径改为与 Agent 路由器注册路径一致
- 注：前端感知的路径不变（`/api/ai/*`），只是代理层到 Agent 的内部路径修正

**回归测试结果：**
- 全部 13 项测试通过（认证/签到/公开浏览/搜索/店铺管理/Profile/金币流水/成就/排行榜/安全守卫/AI 样式/AI 知识库）
- 测试脚本：`docs/e2e-regression.sh`
- 测试案例文档：`docs/bug-regression-test-cases.md`

---

## 使用说明

### 何时追加

在开发过程中遇到以下情况时，追加到本文档：

1. **解决了一个有技术含量的难题** — 问自己"这个问题在面试中怎么讲？"
2. **做了一个有 trade-off 的架构决策** — 为什么选 A 不选 B？
3. **实现了一个可复用的模式** — 这个模式可能在其他项目中也用到
4. **踩了一个坑并修复了** — 这个坑别人也可能遇到

### 追加格式

每个技术点在「技术深入分析」部分新增一个章节，格式：

```markdown
### N. 标题

**遇到的问题**

（2-3 句描述问题场景和为什么难）

**解决方案**

（代码片段或架构描述，说明怎么解决的）

**面试可讲点**

- "要点 1"
- "要点 2"
- "要点 3"
```

同时在「技术点索引」表格新增一行，在「开发时间线」追加一条记录。

### 面试使用

- 每个技术点的「面试可讲点」都是可以直接说的 bullet points
- 结合索引表格快速定位想讲的方向
- 每个点都关联了具体的代码文件和行数，面试时可以精确引用

---

## 2026-08-09 — Phase 2 体验打磨完成

### 完成情况

Phase 2 共 5 项任务，其中 4 项（2.1-2.4）已在之前会话中完成，本次补齐了 2.5（状态覆盖）。

**Phase 2.1 店铺装修** — `StoreManager.vue` 实现了店铺名称/品类/描述的编辑、主题色/Banner 标题/副标题的装修配置（含实时预览卡片）、店铺数据统计、保存时 decorationConfig 以 JSON 字符串写入 Store 表。前后端完整打通。

**Phase 2.2 购买动效** — `PurchaseEffect.vue` 使用 `canvas-confetti` 库实现分层 confetti 爆发（普通/稀有/史诗/传说四档），金币数字动画使用 ease-out cubic 缓动函数，CSS particles 背景飘落效果。通过 Vue provide/inject 在 App.vue 全局注入。

**Phase 2.3 商品图片上传** — `ProductEditor.vue` 集成 Element Plus `el-upload`，前端校验文件类型和大小（max 5MB），后端 `UploadController` 按日期组织存储，最多 6 张图片，以逗号分隔的 URL 字符串存入 Product 表。

**Phase 2.4 AI 风格预览卡片** — `ProductEditor.vue` 右侧 Agent 面板中展示各平台（拼多多/淘宝/京东/苏宁/小红书）风格的预览卡片，包含平台色渐变顶栏、标题（不同字号）、卖点列表（不同密度）、详情摘要、"应用此风格"按钮。点击后将 AI 生成的标题和描述填入表单。

**Phase 2.5 状态覆盖** — 为 7 个页面补全了 loading / error / empty 三种状态，统一采用 Element Plus 的 `el-skeleton` / `el-result` / `el-empty` 组件，保持视觉一致性。覆盖了 ProductDetail, Dashboard, Collection, Achievements, Leaderboard, Profile, KnowledgeBase, StoreManager 共 8 个页面。

### 面试可讲点

- **"前端状态的三种面孔"** — Loading / Error / Empty 是前端最容易被忽略但用户感知最强的状态。一个有经验的前端会在每个数据获取点问自己：「数据还没到时显示什么？」「出错了显示什么？」「没数据显示什么？」这不是技术难度问题，而是工程纪律问题。
- **"el-result 组件是错误状态的最佳实践"** — 相比自己写 error div，Element Plus 的 `el-result` 提供了标准化的图标、标题、描述、操作区，用户一眼就能理解发生了什么以及怎么做。统一的错误 UI 建立了用户对产品的信任感。
