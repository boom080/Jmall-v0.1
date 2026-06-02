# Jrunmall 数据库与本地依赖操作手册

Jrun.md = 数据库 / Docker 依赖 / Redis / SQL 操作手册。  
run.md = 项目启动和体验手册。

如果只是启动项目、访问前端或跑最小体验流程，看 `docs/run.md`。如果涉及建库、导入 SQL、Redis 初始化、PostgreSQL 初始化、本地 Docker 依赖排查，先看本文。

## 1. 文档定位

本文只负责本地数据库与依赖操作，包括 Docker、MySQL、PostgreSQL、Redis、SQL 导入、Redis 初始化和 Docker volume 判断。

本文不负责 Java 服务启动、前端启动、浏览器访问流程；这些内容统一放在 `docs/run.md`。本文不删除 Docker volume，不影响 Journey 项目容器，不修改业务代码。

所有命令都按 Windows CMD 编写。打开 CMD 后先进入项目根目录：

```cmd
cd /d D:\java-projects\GuliMall
```

命令中的 `你的MySQL密码`、`你的PostgreSQL密码` 都是占位符，执行时按本机配置替换。不要把真实密码写进文档、聊天记录或 Git 提交。

## 2. Docker 本地依赖说明

本项目本地 Docker 依赖由 `docker-compose.local.yml` 定义，环境变量来自 `docker\local\.env.local`。

| 依赖 | 容器名 | 用途 | 端口来源 |
|---|---|---|---|
| MySQL | `jrunmall-mysql-local` | 业务数据库 | `docker-compose.local.yml` 中的 `${JRUNMALL_MYSQL_PORT:-3306}` |
| Redis | `jrunmall-redis-local` | 购物车、登录态、秒杀库存、Redis Streams | `${JRUNMALL_REDIS_PORT:-6379}` |
| PostgreSQL | `jrunmall-postgres-local` | AI / RAG 相关预留或目标存储 | `${JRUNMALL_POSTGRES_PORT:-5432}` |

本地依赖启动命令放在 `docs/run.md`，本文只展开数据库和依赖操作细节。

## 3. env 文件分工

`docker\local\.env.local` 给 Docker Compose 用，变量名以 `JRUNMALL_*` 为主，例如 MySQL、Redis、PostgreSQL 的 Docker 端口和容器初始化参数。

项目根目录的 `.env.local` 给 Java 后端启动脚本用，新变量名以 `JRUNMALL_*` 为主，例如 `JRUNMALL_MYSQL_HOST`、`JRUNMALL_MYSQL_PORT`、`JRUNMALL_MYSQL_PASSWORD`、`JRUNMALL_REDIS_HOST`、`JRUNMALL_REDIS_PORT`。

两边变量名用途不同，不能混用。Java 进程不会自动读取 `docker\local\.env.local`，Docker Compose 也不会自动读取 Java 的 `.env.local`。当前 Java 配置优先读取 `JRUNMALL_*`，短期兼容旧环境变量；旧变量只作为技术遗留 fallback。

文档中不要写死真实密码；MySQL 统一写 `你的MySQL密码`，PostgreSQL 统一写 `你的PostgreSQL密码`。

## 4. MySQL 操作

MySQL 业务库当前只操作：

- `jrunmall_pms`
- `jrunmall_ums`
- `jrunmall_commerce`

不要把 `jrunmall_user_order*` 导入 `jrunmall_pms`。订单表最终只应在 `jrunmall_commerce`。

### 4.1 检查 MySQL alive

```cmd
docker exec jrunmall-mysql-local mysqladmin ping -uroot -p你的MySQL密码
```

预期结果包含 `mysqld is alive`。如果 MySQL 还在 `Restarting` 或无法连接，不要继续导入 SQL。

### 4.2 删除并重建三个业务库

这一步会删除三个业务库中的现有表和数据，但不会删除 Docker volume。

```cmd
docker exec -i jrunmall-mysql-local mysql -uroot -p你的MySQL密码 -e "DROP DATABASE IF EXISTS jrunmall_pms; DROP DATABASE IF EXISTS jrunmall_ums; DROP DATABASE IF EXISTS jrunmall_commerce; CREATE DATABASE jrunmall_pms DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE DATABASE jrunmall_ums DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE DATABASE jrunmall_commerce DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 4.3 导入商品库 SQL

```cmd
docker exec -i jrunmall-mysql-local mysql -uroot -p你的MySQL密码 jrunmall_pms < resource\db\jrunmall_pms.sql
```

### 4.4 导入用户库 SQL

```cmd
docker exec -i jrunmall-mysql-local mysql -uroot -p你的MySQL密码 jrunmall_ums < resource\db\jrunmall_ums.sql
```

### 4.5 导入订单 / 交易库 SQL

```cmd
docker exec -i jrunmall-mysql-local mysql -uroot -p你的MySQL密码 jrunmall_commerce < resource\db\jrunmall_commerce.sql
```

### 4.6 导入地址快照补丁 SQL

```cmd
docker exec -i jrunmall-mysql-local mysql -uroot -p你的MySQL密码 jrunmall_commerce < resource\db\5.1-auth-address.sql
```

### 4.7 可选导入秒杀商品 seed

只在需要秒杀 E2E 测试商品时导入。该文件只进入 `jrunmall_pms`。

```cmd
docker exec -i jrunmall-mysql-local mysql -uroot -p你的MySQL密码 jrunmall_pms < resource\db\seckill_product_seed.sql
```

### 4.8 可选导入秒杀订单 seed

当前该文件用于保留秒杀订单测试数据的独立入口，目标库是 `jrunmall_commerce`。

```cmd
docker exec -i jrunmall-mysql-local mysql -uroot -p你的MySQL密码 jrunmall_commerce < resource\db\seckill_order_seed.sql
```

### 4.9 检查商品库不能有订单表

```cmd
docker exec -i jrunmall-mysql-local mysql -uroot -p你的MySQL密码 -e "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='jrunmall_pms' AND TABLE_NAME IN ('jrunmall_user_order','jrunmall_user_order_item');"
```

预期结果：没有返回数据行。

### 4.10 检查订单库必须有订单表

```cmd
docker exec -i jrunmall-mysql-local mysql -uroot -p你的MySQL密码 -e "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='jrunmall_commerce' AND TABLE_NAME IN ('jrunmall_user_order','jrunmall_user_order_item') ORDER BY TABLE_NAME;"
```

预期结果：返回 `jrunmall_user_order` 和 `jrunmall_user_order_item`。

更多 MySQL 与业务 SQL 的归属说明见 `docs/docker-sql.md`，不要在多个文档重复维护大段 SQL 对照表。

## 5. PostgreSQL 操作

PostgreSQL 容器名是 `jrunmall-postgres-local`。端口来自 `docker\local\.env.local` 中的 `JRUNMALL_POSTGRES_PORT`，Compose 默认映射到容器内 `5432`。

当前用途：AI / RAG 真实知识库存储。`ai-services` 配置 `DATABASE_URL` 后会把网页上传的 txt 切块、embedding 和检索数据写入 PostgreSQL + pgvector；未配置时只保留空文件存储用于本地开发自检，不再内置假知识库数据。

检查 PostgreSQL 是否 ready：

```cmd
docker exec -e PGPASSWORD=你的PostgreSQL密码 jrunmall-postgres-local pg_isready -U postgres -d jrunmall_ai
```

如果本机 PostgreSQL 用户或数据库名不同，按 `docker\local\.env.local` 中的变量替换，但不要把真实密码写进文档。

当前 PostgreSQL SQL：

- `resource\db\5.6-rag-ingestion.sql`：启用 `pgvector`，创建 `jrunmall_merchant_ai` schema，以及 `knowledge_bases`、`knowledge_documents`、`knowledge_chunks` 等 RAG 相关表。
- `scripts\cleanup_fake_rag_data.sql`：本地手动清理旧 fake RAG 测试库，删除顺序为 chunks -> documents -> knowledge_bases，不会放入业务启动流程。

可选导入命令：

```cmd
docker exec -i -e PGPASSWORD=你的PostgreSQL密码 jrunmall-postgres-local psql -U postgres -d jrunmall_ai < resource\db\5.6-rag-ingestion.sql
```

清理旧 fake RAG 数据：

```cmd
docker exec -i -e PGPASSWORD=你的PostgreSQL密码 jrunmall-postgres-local psql -U postgres -d jrunmall_ai < scripts\cleanup_fake_rag_data.sql
```

`resource\db\jrunmall_ai.sql` 当前是 MySQL 风格 SQL，包含 `AUTO_INCREMENT`、`DATETIME` 等 MySQL 写法，不要当作 PostgreSQL 初始化脚本直接导入。

不要把 PostgreSQL 和 MySQL 表混淆：业务订单、商品、用户表在 MySQL；AI / RAG 目标表才进入 PostgreSQL。

## 6. Redis 操作

Redis 容器名是 `jrunmall-redis-local`。端口来自 `docker\local\.env.local` 中的 `JRUNMALL_REDIS_PORT`，Compose 默认映射到容器内 `6379`。

当前 `docker-compose.local.yml` 的 Redis command 是 `redis-server --appendonly yes`，未配置 Redis 密码。是否有密码必须以 `docker\local\.env.local` 和 Compose 文件为准；不要在文档写死密码。

Redis 当前用途：

- 用户购物车，例如代码约定的 `jrunmall:user:cart:{userId}`
- 登录态 / session 相关临时状态
- 秒杀库存热点控制
- 用户防重复抢购
- Redis Streams 秒杀事件队列
- pending 重试与 dead-letter 流转

Redis 不需要建表。Redis key 由代码约定和运行时写入，不是 SQL 自动生成。

### 6.1 Redis ping

```cmd
docker exec jrunmall-redis-local redis-cli ping
```

预期结果是 `PONG`。

### 6.2 秒杀 Redis key 规则

当前 Go 秒杀服务 `jrunmall-seckill-go` 的默认前缀来自 `JRUNMALL_SECKILL_KEY_PREFIX`，默认值是 `jrunmall:seckill`。

| 类型 | 默认规则 |
|---|---|
| 秒杀活动信息 | `jrunmall:seckill:activity:{activityId}` |
| 秒杀库存 key | `jrunmall:seckill:stock:{activityId}` |
| 用户防重复抢购 key | `jrunmall:seckill:idem:{activityId}:{userId}` |
| 请求到 Stream 事件映射 | `jrunmall:seckill:request:{requestId}` |
| 重试计数 key | `jrunmall:seckill:retry:{messageId}` |

### 6.3 Redis Stream 规则

当前默认 Redis Stream：

- `jrunmall:seckill:orders`

Go 服务写入字段：

- `requestId`
- `userId`
- `skuId`
- `quantity`
- `seckillSessionId`
- `orderToken`
- `timestamp`

Java 订单服务默认消费配置来自 `jrunmall-order/src/main/resources/application-local.yml`：

| 配置 | 默认值 |
|---|---|
| Consumer Group | `jrunmall-order-group` |
| Consumer Name | `jrunmall-order-local` |
| dead-letter stream | `jrunmall:seckill:orders:dead` |
| retry prefix | `jrunmall:seckill:retry` |
| pending idle | `60000` ms |
| max retry | `3` |

Consumer Name 规则：本地默认是 `jrunmall-order-local`；多实例运行时应通过 `JRUNMALL_SECKILL_CONSUMER_NAME` 配置成每个实例唯一的名字。

### 6.4 pending / dead-letter

`jrunmall-order` 会创建 Consumer Group，并通过 `POST /order/seckill/streams/consume-once` 消费新消息。消费失败的消息会留在 pending；`POST /order/seckill/streams/retry-pending` 会重试 pending 消息。

当重试次数达到 `JRUNMALL_SECKILL_MAX_RETRY_COUNT`，消息会写入 dead-letter stream `jrunmall:seckill:orders:dead`，随后对原 Stream 执行 ack。当前 dead-letter 可见化 / 人工补偿入口仍未完成，状态见 `docs/order-progress.md`。

### 6.5 库存预热入口

当前代码已确认 Go 秒杀服务存在库存预热入口：

- `POST /api/seckill/warmup`

启动方式见 `docs/run.md` 中的秒杀 Go 服务说明。Redis 秒杀初始化边界也参考 `docs/seckill-redis-init.md`，两份文档应保持一致：MySQL seed 只负责测试商品 / 订单结构，Redis 状态通过 Go 预热接口或 Redis CLI 单独维护。

## 7. Docker volume 说明

不删除 volume 的意思是：只停止或重启容器时，MySQL、PostgreSQL、Redis 的持久化数据还保留在 Docker volume 中。

删除业务库和删除 volume 的区别：

- 删除业务库：只删除 MySQL 容器内指定数据库，例如 `jrunmall_pms`、`jrunmall_ums`、`jrunmall_commerce`。
- 删除 volume：删除 Docker 持久化数据，MySQL / PostgreSQL / Redis 都可能回到首次初始化状态。

什么时候需要重新导入 SQL：

- 删除或重建了 `jrunmall_pms`、`jrunmall_ums`、`jrunmall_commerce`
- 执行过会清空表的 SQL
- 执行过 `docker compose down -v` 或手工删除了 MySQL volume
- Docker 启动成功但业务表不存在
- 曾把订单表误导入 `jrunmall_pms`

什么时候不需要重新导入 SQL：

- 只是 `docker compose up -d` 启动容器
- 只是停止 / 重启容器，且没有删除业务库或 volume
- 只是启动 Java / 前端服务
- 只是检查 Redis ping 或 PostgreSQL ready

## 8. 常见错误

- MySQL `Restarting`：通常是环境变量、初始化脚本或 volume 中旧数据异常。先看 `docker ps` 状态和 MySQL 容器日志；不要在未 alive 时导入 SQL。
- PostgreSQL `POSTGRES_PASSWORD` 为空：`docker\local\.env.local` 中 `JRUNMALL_POSTGRES_PASSWORD` 未设置或未被 Compose 读取。补齐后重新创建 PostgreSQL 容器。
- `Can't connect to MySQL server`：容器没启动、端口映射不一致、Java `.env.local` 的 `JRUNMALL_MYSQL_PORT` 与 Docker `JRUNMALL_MYSQL_PORT` 不一致，或 MySQL 尚未 ready。
- `Lost connection to MySQL server`：SQL 文件较大、MySQL 初始化中断或容器资源不足。确认 MySQL alive 后重新导入对应 SQL。
- `No database selected`：执行 SQL 时没有指定目标库。按本文命令在 `mysql` 后写明 `jrunmall_pms`、`jrunmall_ums` 或 `jrunmall_commerce`。
- Redis ping 不返回 `PONG`：Redis 容器未运行、容器名不对、端口配置不一致，或 Redis 启动失败。
- Docker 启动成功但表不存在：Compose 只保证容器启动，不代表业务 SQL 已导入。按本文 MySQL 操作导入 SQL 并检查表。
- SQL 重复导入导致数据被覆盖：`jrunmall_pms.sql`、`jrunmall_ums.sql` 等可能包含清表或重建表逻辑。重复导入前先确认是否允许覆盖本地数据。

## 9. 命令要求

- 本文所有命令均为 Windows CMD。
- 不使用 PowerShell 命令。
- 密码统一使用 `你的MySQL密码`、`你的PostgreSQL密码` 占位符。
- 不写死真实密码。
- 不展示 `docker\local\.env.local` 的真实内容。




