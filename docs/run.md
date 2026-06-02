# Jrunmall 项目启动手册

如果涉及建库、导入 SQL、Redis 初始化、PostgreSQL 初始化，请先看 `docs/Jrun.md`。本文只负责启动项目和完成本地体验流程。

Jrun.md = 数据库 / Docker 依赖 / Redis / SQL 操作手册。  
run.md = 项目启动和体验手册。

## 1. 文档定位

本文只记录如何启动本地项目，不展开数据库导入细节。数据库初始化、SQL 导入、Redis 初始化、PostgreSQL 初始化、Docker volume 判断和依赖排查全部看 `docs/Jrun.md`。

本文所有命令均使用 Windows CMD。

复制命令时只复制代码块里的命令本体，不要复制 CMD 左侧提示符 `D:\java-projects\GuliMall>`，也不要把 Maven 输出里的 `[INFO]`、`[WARNING]`、`[ERROR]` 行粘回 CMD 执行。否则 CMD 会把这些日志当成新命令，出现 `'[INFO]' 不是内部或外部命令`、`此时不应有 >` 这类连锁报错。

## 2. 启动前提

启动前确认：

- 本机 Maven 使用 JDK 17，执行 `mvn -version` 时 Java 版本应显示 17。
- Docker 依赖已按 `docs/Jrun.md` 准备好。
- MySQL 业务 SQL 已导入。
- Redis / PostgreSQL 已启动。
- Java 本地环境变量已配置在项目根目录 `.env.local`。
- 前端环境变量已按对应 `.env.example` 配置。
- 不要把 `docker\local\.env.local` 当作 Java 后端环境变量文件使用。

## 3. 启动 Docker 依赖

```cmd
cd /d D:\java-projects\GuliMall
docker compose --env-file docker\local\.env.local -f docker-compose.local.yml up -d
docker ps
```

数据库导入不在本文展开，按 `docs/Jrun.md` 操作。

## 4. 检查依赖是否运行

MySQL alive：

```cmd
docker exec jrunmall-mysql-local mysqladmin ping -uroot -p你的MySQL密码
```

Redis ping：

```cmd
docker exec jrunmall-redis-local redis-cli ping
```

PostgreSQL ready：

```cmd
docker exec -e PGPASSWORD=你的PostgreSQL密码 jrunmall-postgres-local pg_isready -U postgres -d jrunmall_ai
```

详细解释、密码占位符和异常处理看 `docs/Jrun.md`。

## 5. 构建 Java 模块

当前根 `pom.xml` 是多模块 Maven 工程。只构建本地体验主要链路可用：

```cmd
cd /d D:\java-projects\GuliMall
mvn -s .mvn\local-settings.xml -pl :jrunmall-common,:jrunmall-member,:jrunmall-product,:jrunmall-order -am -DskipTests package
```

如果需要构建全部模块：

```cmd
cd /d D:\java-projects\GuliMall
mvn -s .mvn\local-settings.xml -DskipTests package
```

单模块构建示例：

```cmd
cd /d D:\java-projects\GuliMall
mvn -s .mvn\local-settings.xml -pl :jrunmall-admin -am -DskipTests package
```

当前 Maven artifactId 已迁移为 `jrunmall-*`。物理目录仍保留 `gulimall-*` 作为兼容遗留，所以 `scripts\start-java-local.bat` 仍按真实目录定位 POM。

## 6. 启动 Java 后端

当前 `scripts\start-java-local.bat` 真实支持三个参数：`member`、`product`、`order`。

脚本会先从根工程执行 `-pl :jrunmall-模块名 -am -DskipTests install`，把 `jrunmall-common` 等本地 Maven 依赖安装到本机仓库，然后再启动目标服务。直接用单个子模块 POM 启动时，如果本地仓库还没有这些 SNAPSHOT 依赖，会报 `jrunmall-common:jar:0.0.1-SNAPSHOT is missing`。

分别打开三个 CMD 窗口运行：

```cmd
cd /d D:\java-projects\GuliMall
scripts\start-java-local.bat member
```

```cmd
cd /d D:\java-projects\GuliMall
scripts\start-java-local.bat product
```

```cmd
cd /d D:\java-projects\GuliMall
scripts\start-java-local.bat order
```

当前本地端口来自各模块 `application-local.yml`：

- `jrunmall-member`：`8000`
- `jrunmall-product`：`10301`
- `jrunmall-order`：`9000`

前端默认通过 `VITE_API_PROXY_TARGET=http://127.0.0.1:10301` 访问 `jrunmall-product`。

## 7. 启动 ai-services

项目存在 `ai-services`，并有真实启动脚本 `scripts\start-ai-services.bat`。

首次安装依赖并启动：

```cmd
cd /d D:\java-projects\GuliMall
scripts\start-ai-services.bat --install 127.0.0.1 18080
```

后续复用已有虚拟环境启动：

```cmd
cd /d D:\java-projects\GuliMall
scripts\start-ai-services.bat 127.0.0.1 18080
```

`ai-services` 支持 `DATABASE_URL` 指向 PostgreSQL + pgvector 后写入真实 RAG 表。未配置 `DATABASE_URL` 时只保留空文件存储用于本地单元测试和接口自检，不再内置假知识库数据。

### 7.1 商家端 LangChain4j 模型密钥

商家端“商品 AI 工作台”的模型切换现在走两条链路：

- `LangChain4j / ...`：`jrunmall-product -> gulimall-ai-adapter -> LangChain4j -> OpenAI-compatible Chat API`
- `Mock / ...`：`jrunmall-product -> gulimall-ai-adapter -> ai-services`

你的真实模型密钥填写在项目根目录 `.env.local` 或系统环境变量里。启动 `jrunmall-product` 的 `scripts\start-java-local.bat product` 会自动读取 `.env.local`。

如果你要在商家端下拉框中切换 **DeepSeek V4 Pro** 和 **Qwen3-Max**，分别填写下面两组配置。`*_MODEL` 是旧的单模型配置，`*_MODELS` 是当前推荐的多模型配置；填写 `*_MODELS` 后，同一个公司的多个模型会同时出现在商家端下拉框里。

```env
# DeepSeek
JRUNMALL_AI_DEEPSEEK_API_KEY=你的 DeepSeek API Key
JRUNMALL_AI_DEEPSEEK_BASE_URL=https://api.deepseek.com
JRUNMALL_AI_DEEPSEEK_MODEL=deepseek-chat
JRUNMALL_AI_DEEPSEEK_MODELS=deepseek-chat

# Qwen / 阿里云百炼 DashScope OpenAI 兼容模式
JRUNMALL_AI_QWEN_API_KEY=你的阿里云百炼 API Key
JRUNMALL_AI_QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
JRUNMALL_AI_QWEN_MODEL=qwen3-max
JRUNMALL_AI_QWEN_MODELS=qwen3-max,qwen3.6-plus
```

只有检测到对应 API Key 的真实模型才会出现在商家端模型下拉框中：

- `DeepSeek / deepseek-chat` 读取 `JRUNMALL_AI_DEEPSEEK_API_KEY`
- `Qwen / qwen3-max`、`Qwen / qwen3.6-plus` 读取 `JRUNMALL_AI_QWEN_API_KEY`，也兼容 `QWEN_API_KEY`、`DASHSCOPE_API_KEY`

如果你想增加 Qwen 同公司的其他模型，只改这一行即可，例如：

```env
JRUNMALL_AI_QWEN_MODELS=qwen3-max,qwen3.6-plus,qwen-turbo
```

如果你使用 Qwen 国际站或其他地域，把 `JRUNMALL_AI_QWEN_BASE_URL` 改为对应地域的 OpenAI 兼容地址。未配置对应 Key 时，该真实模型不会进入下拉框；如果页面仍显示旧模型，重启 `product` 并刷新商家端页面。

### 7.2 知识库说明与存储位置

知识库属于商家端 AI / RAG 数据，不是 MySQL 商品业务表。商家端入口在 `http://127.0.0.1:5175` 的“知识库管理”页面；前端上传 txt 到 `jrunmall-product` 的 `/product/ai/knowledge-bases/upload-txt`，`product` 再通过 `gulimall-ai-adapter` 转发到 `ai-services` 的 `/api/merchant/knowledge-bases/upload-txt`。

真实 RAG 推荐配置 `DATABASE_URL`，目标 schema 初始化脚本在 `resource\db\5.6-rag-ingestion.sql`。该脚本启用 `pgvector` 并创建 `knowledge_bases`、`knowledge_documents`、`knowledge_chunks`，其中 chunk 表保存 `chunks.content` 和 `chunks.embedding`。本地清理旧假库只手动执行 `scripts\cleanup_fake_rag_data.sql`，不要放进业务启动流程。

如果数据库为空，商家端知识库下拉和知识库页面会显示“暂无知识库，请上传 txt 创建”。旧的 `MERCHANT_AI_DATA_FILE` 文件存储不再内置演示库，只作为无 PostgreSQL 时的开发兜底存储。

知识库导入的实际应用路径：在“知识库管理”页填写知识库名称、说明并选择 txt 文件，上传后 `ai-services` 会 UTF-8 读取、清洗、切 chunk、生成 embedding 并入库。生成商品文案时前端必须带 `knowledgeBaseId`，Java 默认调用 Python 的 `/api/product-copy/generate`，Python workflow 会只在指定知识库下检索 chunk，将命中的资料放进 prompt 的【电商知识库参考资料】区，并在响应中返回 `response_source`、`usedChunks` 和 `citations`。

快速验证知识库链路：

```cmd
curl http://127.0.0.1:10301/product/ai/knowledge-bases
curl http://127.0.0.1:18080/api/merchant/knowledge-bases
```

## 8. 启动秒杀 Go 服务

项目存在 `jrunmall-seckill-go`，并有真实启动脚本 `scripts\start-seckill-go.bat`。

```cmd
cd /d D:\java-projects\GuliMall
scripts\start-seckill-go.bat
```

默认健康地址为 `http://127.0.0.1:19090/health`。库存预热入口是 `POST /api/seckill/warmup`，Redis 初始化边界看 `docs/Jrun.md` 和 `docs/seckill-redis-init.md`。

## 9. 启动前端

### 9.1 用户端

真实目录：`jrunmall-user-web`。`package.json` 中启动脚本是 `npm run dev`，Vite 默认端口在 `vite.config.ts` 和启动脚本中为 `5174`。

```cmd
cd /d D:\java-projects\GuliMall
scripts\start-user-web.bat
```

等价手动命令：

```cmd
cd /d D:\java-projects\GuliMall\jrunmall-user-web
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

接口配置位置：

- `jrunmall-user-web\.env.example`
- `jrunmall-user-web\vite.config.ts`

默认：

- `VITE_API_BASE_URL=/api`
- `VITE_API_PROXY_TARGET=http://127.0.0.1:10301`

### 9.2 商家端

真实目录：`jrunmall-merchant-web`。`package.json` 中启动脚本是 `npm run dev`，Vite 默认端口在 `vite.config.ts` 和启动脚本中为 `5175`。

```cmd
cd /d D:\java-projects\GuliMall
scripts\start-merchant-web.bat
```

等价手动命令：

```cmd
cd /d D:\java-projects\GuliMall\jrunmall-merchant-web
npm install
npm run dev -- --host 127.0.0.1 --port 5175
```

接口配置位置：

- `jrunmall-merchant-web\.env.example`
- `jrunmall-merchant-web\vite.config.ts`

默认：

- `VITE_API_BASE_URL=/api`
- `VITE_API_PROXY_TARGET=http://127.0.0.1:10301`
- `VITE_ORDER_API_BASE_URL=http://127.0.0.1:9000`

## 10. 浏览器访问地址

- 用户端：`http://127.0.0.1:5174`
- 商家端：`http://127.0.0.1:5175`
- ai-services 健康检查：`http://127.0.0.1:18080/health`
- 秒杀 Go 服务健康检查：`http://127.0.0.1:19090/health`

如果本机 `.env.local` 或脚本参数改过端口，以实际启动输出为准。

## 11. 最小体验流程

用户端：

1. 打开 `http://127.0.0.1:5174`。
2. 注册或登录。
3. 查看商品列表。
4. 进入商品详情。
5. 加入购物车。
6. 进入购物车并下单。
7. 查看订单列表。
8. 打开订单详情并执行模拟支付。
9. 进入秒杀入口，验证抢购入口是否可用。

商家端：

1. 打开 `http://127.0.0.1:5175`。
2. 查看普通订单列表。
3. 查看秒杀订单列表。
4. 进入 AI 工作台或知识库页面，验证 ai-services 是否连通。

秒杀完整链路需要先完成 Redis 库存预热；预热与 Stream 规则看 `docs/Jrun.md`。

## 12. 常见启动问题

- Docker 没启动：先启动 Docker Desktop，再执行本文 Docker Compose 命令。
- 端口冲突：检查 `8000`、`9000`、`10301`、`18080`、`19090`、`5174`、`5175` 是否被占用；必要时调整脚本参数或配置文件。
- `product` 报 `Application finished with exit code: 1`：先看 Maven 报错前面的 Spring Boot 堆栈。如果 `10301` 已被占用，说明 `product` 已启动或上次进程未退出；确认是旧 `product` 进程后关闭旧窗口，或按 PID 结束后再重新执行 `scripts\start-java-local.bat product`。

```cmd
netstat -ano | findstr :10301
tasklist /FI "PID eq 进程号"
taskkill /PID 进程号 /F
```

- CMD 显示 `'锘緻echo' 不是内部或外部命令`：说明 `.bat` 文件被保存成了带 UTF-8 BOM 的编码；脚本文件必须保存为无 BOM 编码。
- Java 服务启动失败：先确认 `.env.local` 中 Java 变量存在，并确认 MySQL / Redis 已按 `docs/Jrun.md` 就绪。
- 前端代理错误：检查 `VITE_API_PROXY_TARGET` 是否指向 `http://127.0.0.1:10301`，商家端秒杀订单是否需要 `VITE_ORDER_API_BASE_URL=http://127.0.0.1:9000`。
- npm 依赖问题：删除前端本地 `node_modules` 后重新运行对应启动脚本，脚本会执行 `npm install`。
- 数据库、SQL、Redis 初始化、PostgreSQL 初始化问题：统一回到 `docs/Jrun.md`。




