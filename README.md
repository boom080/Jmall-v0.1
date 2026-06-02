# Jrunmall 电商 AI 文案生成与 RAG 知识库系统

Jrunmall 是一个基于 Java 电商后端、Vue3 用户端与商家端、Python FastAPI AI 服务构建的本地电商 AI 应用项目。项目用于学习、开发和面试展示，不是线上商用项目；真实 AI/RAG 能力需要开发者在本地自行配置 API Key 和数据库依赖。

本仓库是从本地历史工程中导出的 Jrunmall 精简版本，只保留当前可运行项目主线。它不是原始 GuliMall 课程资料仓库，也不包含旧课程笔记、历史源码备份、旧前端、个人本地配置或旧 Git 历史。

真实运行时请按模板自行创建 `.env.local`、`ai-services/.env.local` 和 `docker/local/.env.local`。这些本地配置文件不提交到 GitHub。

## 项目模块

- `gulimall-product`：当前 Jrunmall 商品、用户端聚合、购物车、普通订单、商家商品、AI 转发入口。
- `gulimall-member`：用户注册、登录、会员与地址相关能力。
- `gulimall-order`：秒杀订单落库、Redis Stream 消费与商家端秒杀订单查询。
- `gulimall-ai-adapter`：Java AI Adapter，连接商品服务、Python AI 服务和 LangChain4j/OpenAI-compatible 模型。
- `ai-services`：Python FastAPI AI 服务，提供商品文案生成、知识库、chunking、embedding、RAG 检索。
- `jrunmall-merchant-web`：Vue3 商家端，包含商品管理、普通订单、秒杀订单、知识库和 AI 工作台。
- `jrunmall-user-web`：Vue3 用户端，包含商品浏览、详情、购物车、下单、订单、秒杀入口。
- `jrunmall-seckill-go`：Go 秒杀热点服务，负责 Redis 库存扣减、幂等控制和 Stream 写入。
- `docker-compose.local.yml`、`docker/`：本地 MySQL、Redis、PostgreSQL 依赖。
- `docs/`、`scripts/`：启动、数据初始化、安全检查与本地运维脚本。

## 项目亮点

- 用户端电商业务闭环：注册/登录、地址、商品列表/详情、购物车、下单、模拟支付、订单查询。
- 商家端商品管理：商品列表、创建、编辑、上下架、图片上传配置入口。
- 商家端 AI 文案生成：可选择 mock、DeepSeek、Qwen、LangChain4j/OpenAI-compatible 等模型来源。
- Java AI Adapter：隔离商品业务与 AI 服务调用，处理模型选项、密钥解析、RAG 响应映射。
- Python FastAPI `ai-services`：承接知识库导入、chunking、embedding、RAG 检索和文案生成流程。
- RAG 知识库：支持 txt 上传创建知识库、粘贴文本/PDF 文档导入接口、chunking、embedding 入库与检索。
- PostgreSQL + pgvector：目标结构使用 `knowledge_chunks.embedding vector(1024)`，支持按知识库过滤的向量检索。
- openai-compatible embedding：可通过 `RAG_EMBEDDING_*` 切换真实 embedding provider；无 Key 时可用 mock embedding 本地跑通。
- 前端引用来源展示：文案结果返回 `response_source`、`usedChunks`、`citations`，商家端展示命中的 chunk 与来源。
- Docker 本地环境：MySQL、Redis、PostgreSQL 由本地 compose 管理，便于统一启动和排查。

## 技术栈

- Java / Spring Boot / MyBatis-Plus / JUnit
- Python / FastAPI / SQLAlchemy / Pytest
- Vue3 / Vite / Element Plus / Pinia / Vitest
- MySQL / Redis / PostgreSQL / pgvector
- Docker Compose
- Qwen / DeepSeek / OpenAI-compatible Chat API
- openai-compatible embedding
- Go / Redis Streams

## 系统架构

商家端前端 -> Java `gulimall-product` / `gulimall-ai-adapter` -> Python `ai-services` -> PostgreSQL / pgvector -> LLM 或 embedding provider。

用户端电商链路主要经过 `jrunmall-user-web` -> `gulimall-product` -> MySQL/Redis。秒杀热点链路经过 `gulimall-product` -> `jrunmall-seckill-go` -> Redis Streams -> `gulimall-order` -> MySQL。

## RAG 工作流

1. 商家端创建知识库，或上传 UTF-8 txt 创建知识库。
2. 可向已有知识库导入粘贴文本或 PDF 文档。
3. `ai-services` 清洗文档并按段落优先切 chunk。
4. embedding provider 为每个 chunk 生成向量。
5. chunk、metadata、embedding 写入 PostgreSQL + pgvector。
6. 生成商品文案时，前端提交 `knowledgeBaseId`、商品信息和模型选择。
7. Python 根据商品信息生成 query embedding，只在指定知识库下检索 chunks。
8. 命中 chunks 会拼接进 prompt 证据区。
9. 响应返回文案、`response_source=rag`、`usedChunks` 和 `citations`；未命中时返回 `no_rag_fallback`，不阻断普通文案生成。

## 本地启动

详细启动步骤见：

- `docs/Jrun.md`：Docker、MySQL、Redis、PostgreSQL、SQL 初始化与依赖排查。
- `docs/run.md`：Java、Python、Go、用户端、商家端启动和最小体验流程。

常用顺序：

```cmd
cd /d D:\java-projects\GuliMall
docker compose --env-file docker\local\.env.local -f docker-compose.local.yml up -d
scripts\start-ai-services.bat --install 127.0.0.1 18080
scripts\start-java-local.bat product
scripts\start-merchant-web.bat
scripts\start-user-web.bat
```

普通电商闭环还需要 `member`，秒杀闭环还需要 `order` 和 `jrunmall-seckill-go`：

```cmd
scripts\start-java-local.bat member
scripts\start-java-local.bat order
scripts\start-seckill-go.bat
```

## 环境变量与密钥安全

- `.env.example`、`ai-services/.env.example`、`.env.local.example` 只能放模板和占位符，可以提交。
- `.env.local`、`ai-services/.env.local`、`docker/local/.env.local` 是本地真实配置，不能提交。
- 真实 MySQL/PostgreSQL 密码、百炼/Qwen/DeepSeek/OpenAI API Key、OSS Secret 都不要写入 README、docs 或代码。
- `mock` provider 可用于无真实 API Key 的本地开发；真实 RAG 语义检索需要配置 `RAG_EMBEDDING_PROVIDER=openai-compatible` 和对应 `RAG_EMBEDDING_*`。

## 测试

- Python：`cd ai-services && pytest`
- Java AI Adapter：`mvn -s .mvn\local-settings.xml -pl :jrunmall-ai-adapter -am test`
- Java product：`mvn -s .mvn\local-settings.xml -pl :jrunmall-product -am test`
- 商家端：`cd jrunmall-merchant-web && npm run test:run`
- 用户端：`cd jrunmall-user-web && npm run test:run`

部分完整 Spring 上下文测试依赖本地 MySQL/Redis/PostgreSQL 和 root 认证配置，失败时先按 `docs/Jrun.md` 检查 Docker 依赖。

## 项目截图

当前未整理可提交的项目截图。后续截图请放到 `docs/screenshots/`，说明见 `docs/screenshots/README.md`。

## 当前限制

- 不是生产上线项目，也不声明服务真实用户或线上转化数据。
- 支付为模拟支付。
- 真实 AI/RAG 需要自行配置 API Key。
- 本地 MySQL/Redis/PostgreSQL 依赖 Docker。
- Go 秒杀、Java 订单消费和 RAG pgvector 需要按文档完成本地初始化后验证。
