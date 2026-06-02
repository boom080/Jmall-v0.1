# 秒杀 Redis 初始化说明

本文只说明秒杀 Redis 初始化边界和 key 规则。完整数据库、Docker、MySQL、PostgreSQL、Redis 操作手册见 `docs/Jrun.md`；项目启动流程见 `docs/run.md`。

## 1. Redis 职责

Redis 负责秒杀热点链路中的临时状态：

- 秒杀库存计数
- 用户防重复抢购
- 请求到 Stream 事件映射
- Redis Streams 秒杀事件队列
- pending 消费重试状态
- dead-letter 流转状态

Redis 不负责正式订单落库。正式订单最终写入 MySQL 的 `jrunmall_commerce.jrunmall_user_order` 和 `jrunmall_commerce.jrunmall_user_order_item`。

## 2. MySQL 与 Redis 边界

- `resource\db\seckill_product_seed.sql`：只补 `jrunmall_pms` 中的秒杀商品测试数据。
- `resource\db\seckill_order_seed.sql`：只面向 `jrunmall_commerce`，当前不写入固定订单行。
- Redis 初始化：通过 Go 秒杀服务预热入口、Redis CLI 或专门脚本完成，不写入 MySQL SQL。

## 3. 当前 key 和 Stream 规则

当前 Go 秒杀服务默认配置：

| 项 | 默认值 |
|---|---|
| key prefix | `jrunmall:seckill` |
| Stream | `jrunmall:seckill:orders` |
| order token prefix | `SEC` |

默认 key 规则：

- 活动信息：`jrunmall:seckill:activity:{activityId}`
- 库存：`jrunmall:seckill:stock:{activityId}`
- 用户防重复：`jrunmall:seckill:idem:{activityId}:{userId}`
- 请求映射：`jrunmall:seckill:request:{requestId}`

订单服务默认消费配置：

- Consumer Group：`jrunmall-order-group`
- Consumer Name：`jrunmall-order-local`
- dead-letter Stream：`jrunmall:seckill:orders:dead`
- retry key prefix：`jrunmall:seckill:retry`

## 4. 本地初始化顺序

1. 先按 `docs/Jrun.md` 完成 MySQL 初始化。
2. 如需秒杀测试商品，导入 `resource\db\seckill_product_seed.sql`。
3. 启动 Redis 与 Go 秒杀服务，启动方式见 `docs/run.md`。
4. 调用 Go 秒杀服务的 `POST /api/seckill/warmup` 完成库存预热。
5. 抢购成功后，Go 服务写入 Redis Stream。
6. 由 `jrunmall-order` 消费 Redis Stream 并落库到 `jrunmall_commerce`。

当前代码已确认存在库存预热入口 `POST /api/seckill/warmup`。具体请求体以 `jrunmall-seckill-go` 当前代码和 README 为准。

## 5. 注意事项

- Redis 不需要建表。
- Redis key 由代码约定，不是 SQL 自动生成。
- 不要把 Redis 密码、真实端口或真实环境变量写入文档。
- pending 重试和 dead-letter 流转由 `jrunmall-order` 负责；dead-letter 可见化 / 人工补偿入口仍需继续补齐。



