# ai-services

## 定位

`ai-services` 承接商家端 AI 能力，当前保持：

- LangChain / LangGraph 商品文案 workflow
- 真实 RAG：txt 上传、chunking、embedding、pgvector 检索
- provider / model 切换

## 当前能力

- `GET /health`
- `GET /api/catalog/models`
- `GET /api/catalog/knowledge-bases`
- `GET /api/merchant/knowledge-bases`
- `POST /api/merchant/knowledge-bases`
- `POST /api/merchant/knowledge-bases/upload-txt`
- `GET /api/merchant/knowledge-bases/{knowledgeBaseId}/documents`
- `POST /api/merchant/knowledge-bases/{knowledgeBaseId}/documents/text`
- `POST /api/merchant/knowledge-bases/{knowledgeBaseId}/documents/pdf`
- `POST /api/product-copy/generate`
- `POST /api/mock/product-copy`：兼容旧本地调用，正式 Java 默认已切到 `/api/product-copy/generate`

## 已完成的真实 RAG 闭环

- 网页上传 txt 自动创建知识库和文档。
- UTF-8 文本读取、清洗、段落优先切 chunk。
- mock / OpenAI-compatible embedding provider。
- PostgreSQL + pgvector 表结构与按知识库过滤检索。
- `chunks.content` + `chunks.embedding` 参与商品文案生成。
- 响应返回 `response_source`、`usedChunks`、`citations`。

## 存储策略

推荐真实 RAG 配置：

- `DATABASE_URL`
- `resource\db\5.6-rag-ingestion.sql`

未配置 `DATABASE_URL` 时保留空文件存储用于本地开发自检和单元测试，不再内置演示知识库或 fake fallback 数据。

## Provider / Embedding 策略

聊天 provider：

- `mock`
- `deepseek`
- `qwen`
- OpenAI-compatible chat API

embedding provider：

- `mock-embedding`：本地开发默认，便于无 API Key 跑通测试。
- `openai-compatible`：通过 `RAG_EMBEDDING_BASE_URL`、`RAG_EMBEDDING_API_KEY`、`RAG_EMBEDDING_MODEL` 接入 OpenAI-compatible embedding API。

真实 embedding 未配置时不要填写假 API Key。正式语义检索应配置真实 provider；开发环境可以使用 mock，响应会明确返回当前 `embeddingProvider`。

## 环境变量

看：

- `.env.example`
- `.env.local.example`

当前读取优先级：

1. `.env.local`
2. `.env`

关键变量：

```env
AI_SERVICE_ENV=local
AI_SERVICE_HOST=127.0.0.1
AI_SERVICE_PORT=18080
AI_PROVIDER=mock
AI_MODEL_NAME=mock-product-copy-v1
AI_RAG_ENABLED=true
MERCHANT_AI_DATA_FILE=data/merchant_ai_store.json

DATABASE_URL=
REDIS_URL=

RAG_EMBEDDING_PROVIDER=
RAG_EMBEDDING_BASE_URL=
RAG_EMBEDDING_API_KEY=
RAG_EMBEDDING_MODEL=
RAG_EMBEDDING_DIMENSION=
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=120
RAG_TOP_K=5

DEEPSEEK_API_KEY=
QWEN_API_KEY=
```

## 本地启动

```powershell
scripts\start-ai-services.bat --install
scripts\start-ai-services.bat
```

## 测试

```powershell
cd D:\java-projects\GuliMall\ai-services
python -m pytest
```

## 当前边界

- txt 上传是本次真实 RAG 主链路。
- PDF / 多文件追加保留旧入口和后续扩展空间。
- 不扩第二个 AI 功能。
- 真实语义检索需要配置 OpenAI-compatible embedding provider。
