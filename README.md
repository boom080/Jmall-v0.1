# 🛍️ Jmall v0.1 — AI 电商模拟经营平台

> 商家练上架，用户当土豪。一个 AI 驱动的、游戏化的、多风格电商模拟平台。

## 🎮 核心玩法

**每个人既是商家也是顾客。**

- 🏪 **商家模式** — AI Agent 团队辅助上架：市场调研 → 文案生成 → 合规审查 → 多风格预览
- 👑 **买家模式** — 签到领金币 → 虚拟购买 → 暴击返利 → 收藏展示 → 排行榜
- 💰 **金币经济** — 签到/卖出赚金币，用金币解锁 AI 助手功能，控制真实 token 成本

## 🤖 AI Agent 协作体系

| Agent | 职责 | 模型策略 |
|-------|------|---------|
| 🎯 编排 Agent | 任务分解、多 Agent 调度 | 强模型 |
| 📈 市场调研 Agent | Tavily 真实搜索行业趋势 | 低成本模型 |
| ✍️ 文案 Agent | 5 大平台风格文案生成 | 强模型 |
| ⚖️ 审核 Agent | 价格异常/内容污染自动拦截 | 低成本模型 |
| 🎨 风格 Agent | 拼多多/淘宝/京东/苏宁/小红书风格适配 | 中等模型 |

## 🏗️ 技术架构

```
Docker Compose 一键部署
├── Vue3 前端 (port 5175)
├── Python FastAPI Agent 服务 (port 18080)
├── Java Spring Boot 后端 (port 10301)
├── MySQL 8.0 — 业务数据
├── PostgreSQL 16 + pgvector — RAG 向量存储
├── Redis 7 — 缓存/Session
├── Go 压测目标 (port 19090)
└── Prometheus + Grafana — 可观测
```

## 🚀 快速启动

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 AI API Key（可选，不填使用 mock 模式）

# 2. 一键启动
docker compose up -d

# 3. 访问
# 前端: http://localhost:5175
# Grafana: http://localhost:3000 (admin/jmall123)
```

## 📁 项目结构

```
jmall/
├── docker-compose.yml          # 一键部署
├── jmall-backend/              # Java Spring Boot API
├── jmall-agent/                # Python Agent 服务（核心）
├── jmall-web/                  # Vue3 前端
├── jmall-bench/                # Go 压测目标
├── docker/                     # 配置和初始化脚本
└── docs/                       # 文档
```

## 🧪 测试

```bash
# Java 后端测试
cd jmall-backend && mvn test

# Python Agent 测试
cd jmall-agent && pytest

# 前端测试
cd jmall-web && npm run test:run
```

## 📋 技术栈

- **前端**: Vue 3 + TypeScript + Vite + Pinia + Element Plus
- **Agent 服务**: Python FastAPI + LangGraph + LangChain + pgvector
- **后端**: Java 17 + Spring Boot 3 + MyBatis-Plus
- **数据库**: MySQL 8.0 + PostgreSQL 16 + Redis 7
- **LLM**: DeepSeek / Qwen / OpenAI-compatible
- **搜索**: Tavily Search API
- **监控**: Prometheus + Grafana
- **部署**: Docker Compose

## 🎯 项目定位

本项目不是线上商用平台，而是一个：
- 🤖 **Agent 开发**能力的展示 — 多 Agent 协作、LLM 路由、成本控制
- 🧪 **测试开发**能力的展示 — LLM-as-Judge、RAG 质量追踪、性能测试
- 🎮 **产品设计**能力的展示 — 游戏化经济系统、双角色平台

## 📄 License

MIT
