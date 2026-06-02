# docker-sql.md

## 1. 文档目的

本文只说明 Jrunmall 本地 Docker MySQL 与业务 SQL 的数据库归属关系。具体重置、导入、检查命令不写在本文，统一放在 `docs/Jrun.md`。

## 2. Docker MySQL 与业务 SQL 的关系

`docker-compose.local.yml` 定义的 MySQL 容器名是 `jrunmall-mysql-local`。`docker/mysql/init/00-create-databases.sql` 用于 MySQL volume 首次为空时自动建库，当前应创建：

- `jrunmall_pms`
- `jrunmall_ums`
- `jrunmall_commerce`

Docker MySQL 启动成功只代表 MySQL 进程可用，不代表业务 SQL 已导入成功。业务表仍需要按 SQL 文件导入。

## 3. 第一次初始化需要创建的数据库

| 数据库 | 职责 | 允许的业务表类型 |
|---|---|---|
| `jrunmall_pms` | 商品库 | `pms_*`、必要的 `undo_log` |
| `jrunmall_ums` | 用户/会员库 | `ums_*`、必要的 `undo_log` |
| `jrunmall_commerce` | Jrunmall 订单/交易库 | `jrunmall_user_order`、`jrunmall_user_order_item` |

`jrunmall_oms` 是原课程订单库 SQL 对应的数据库，不是当前 Jrunmall 订单表的目标库。

## 4. SQL 文件导入顺序

最终导入顺序固定为：

1. `resource/db/jrunmall_pms.sql` -> `jrunmall_pms`
2. `resource/db/jrunmall_ums.sql` -> `jrunmall_ums`
3. `resource/db/jrunmall_commerce.sql` -> `jrunmall_commerce`
4. `resource/db/5.1-auth-address.sql` -> `jrunmall_commerce`
5. `resource/db/seckill_product_seed.sql` -> `jrunmall_pms`
6. `resource/db/seckill_order_seed.sql` -> `jrunmall_commerce`

旧混合版 `resource/db/jrunmall_seckill_e2e_seed.sql` 已删除。秒杀商品测试数据和订单测试数据分开维护，不再保留单文件跨库初始化写法。

## 5. SQL 文件与目标数据库对照表

| 顺序 | SQL 文件 | 目标数据库 | 主要作用 | 创建/修改的主要表 | 是否必执行 | 备注 |
|---:|---|---|---|---|---|---|
| 1 | `docker/mysql/init/00-create-databases.sql` | MySQL 实例级 | Docker 首次空 volume 初始化时建库 | `jrunmall_pms`、`jrunmall_ums`、`jrunmall_commerce` | 是 | 不导入业务表 |
| 2 | `resource/db/jrunmall_pms.sql` | `jrunmall_pms` | 商品库结构与商品种子数据 | `pms_attr`、`pms_attr_attrgroup_relation`、`pms_attr_group`、`pms_brand`、`pms_category`、`pms_category_brand_relation`、`pms_comment_replay`、`pms_product_attr_value`、`pms_sku_images`、`pms_sku_info`、`pms_sku_sale_attr_value`、`pms_spu_comment`、`pms_spu_images`、`pms_spu_info`、`pms_spu_info_desc`、`undo_log` | 是 | 商品、购物车商品快照、秒杀商品快照依赖 |
| 3 | `resource/db/jrunmall_ums.sql` | `jrunmall_ums` | 会员库结构与地址种子数据 | `ums_growth_change_history`、`ums_integration_change_history`、`ums_member`、`ums_member_collect_spu`、`ums_member_collect_subject`、`ums_member_level`、`ums_member_login_log`、`ums_member_receive_address`、`ums_member_statistics_info`、`undo_log` | 是 | 登录注册与地址管理依赖 |
| 4 | `resource/db/jrunmall_commerce.sql` | `jrunmall_commerce` | Jrunmall 订单/交易表 | `jrunmall_user_order`、`jrunmall_user_order_item` | 是 | 文件内已创建并使用 `jrunmall_commerce` |
| 5 | `resource/db/5.1-auth-address.sql` | `jrunmall_commerce` | 给订单主表补地址快照字段 | 修改 `jrunmall_user_order`：`address_id`、`receiver_name`、`receiver_phone`、`receiver_address` | 是 | 文件内已创建并使用 `jrunmall_commerce`，可重复执行 |
| 6 | `resource/db/seckill_product_seed.sql` | `jrunmall_pms` | 秒杀 E2E 商品测试数据 | `pms_category`、`pms_sku_info` | 否 | 不创建、不修改订单表 |
| 7 | `resource/db/seckill_order_seed.sql` | `jrunmall_commerce` | 秒杀 E2E 订单测试数据占位 | 当前不写入固定订单行 | 否 | 不定义正式表结构；正式表由 `jrunmall_commerce.sql` 创建 |
| 8 | `resource/db/jrunmall_oms.sql` | `jrunmall_oms` | 原课程订单库 | `mq_message`、`oms_order`、`oms_order_item`、`oms_order_operate_history`、`oms_order_return_apply`、`oms_order_return_reason`、`oms_order_setting`、`oms_payment_info`、`oms_refund_info`、`undo_log` | 否 | 当前 Jrunmall 订单表不导入这里 |

## 6. 数据库与业务表对照表

| 数据库 | 表名 | 来源 SQL | 业务含义 | 对应模块 | 是否测试/种子数据 |
|---|---|---|---|---|---|
| `jrunmall_pms` | `pms_attr` | `jrunmall_pms.sql` | 商品属性 | `jrunmall-product` | 否 |
| `jrunmall_pms` | `pms_attr_attrgroup_relation` | `jrunmall_pms.sql` | 属性与属性分组关系 | `jrunmall-product` | 否 |
| `jrunmall_pms` | `pms_attr_group` | `jrunmall_pms.sql` | 商品属性分组 | `jrunmall-product` | 否 |
| `jrunmall_pms` | `pms_brand` | `jrunmall_pms.sql` | 商品品牌 | `jrunmall-product` | 否 |
| `jrunmall_pms` | `pms_category` | `jrunmall_pms.sql`、`seckill_product_seed.sql` | 商品分类 | `jrunmall-product`、`jrunmall-order` 秒杀商品快照 | seed 中的 `cat_id=225` 是测试数据 |
| `jrunmall_pms` | `pms_category_brand_relation` | `jrunmall_pms.sql` | 分类品牌关系 | `jrunmall-product` | 否 |
| `jrunmall_pms` | `pms_comment_replay` | `jrunmall_pms.sql` | 商品评论回复 | `jrunmall-product` | 否 |
| `jrunmall_pms` | `pms_product_attr_value` | `jrunmall_pms.sql` | 商品属性值 | `jrunmall-product` | 否 |
| `jrunmall_pms` | `pms_sku_images` | `jrunmall_pms.sql` | SKU 图片 | `jrunmall-product` | 否 |
| `jrunmall_pms` | `pms_sku_info` | `jrunmall_pms.sql`、`seckill_product_seed.sql` | SKU 主表 | `jrunmall-product`、`jrunmall-order` 秒杀商品快照 | seed 中的 `sku_id=14` 是测试数据 |
| `jrunmall_pms` | `pms_sku_sale_attr_value` | `jrunmall_pms.sql` | SKU 销售属性 | `jrunmall-product` | 否 |
| `jrunmall_pms` | `pms_spu_comment` | `jrunmall_pms.sql` | SPU 评论 | `jrunmall-product` | 否 |
| `jrunmall_pms` | `pms_spu_images` | `jrunmall_pms.sql` | SPU 图片 | `jrunmall-product` | 否 |
| `jrunmall_pms` | `pms_spu_info` | `jrunmall_pms.sql` | SPU 主表 | `jrunmall-product` | 否 |
| `jrunmall_pms` | `pms_spu_info_desc` | `jrunmall_pms.sql` | SPU 描述 | `jrunmall-product` | 否 |
| `jrunmall_pms` | `undo_log` | `jrunmall_pms.sql` | Seata undo 表 | 历史事务支持 | 否 |
| `jrunmall_ums` | `ums_member` | `jrunmall_ums.sql` | 会员主表、登录注册 | `jrunmall-member` | 否 |
| `jrunmall_ums` | `ums_member_receive_address` | `jrunmall_ums.sql` | 收货地址主数据 | `jrunmall-member`、`jrunmall-product` 地址聚合 | 否 |
| `jrunmall_ums` | `ums_*` 其他表 | `jrunmall_ums.sql` | 会员等级、收藏、积分、登录日志、统计信息 | `jrunmall-member` | 否 |
| `jrunmall_ums` | `undo_log` | `jrunmall_ums.sql` | Seata undo 表 | 历史事务支持 | 否 |
| `jrunmall_commerce` | `jrunmall_user_order` | `jrunmall_commerce.sql`、`5.1-auth-address.sql` | Jrunmall 普通订单和秒杀订单主表 | `jrunmall-product`、`jrunmall-order` | 否 |
| `jrunmall_commerce` | `jrunmall_user_order_item` | `jrunmall_commerce.sql` | Jrunmall 订单项快照表 | `jrunmall-product`、`jrunmall-order` | 否 |
| `jrunmall_oms` | `oms_*` | `jrunmall_oms.sql` | 原课程订单表 | 原 `jrunmall-order` | 否 |

## 7. 订单相关表说明

`jrunmall_user_order` 最终只在 `jrunmall_commerce` 中创建。它承载普通订单和秒杀订单主记录，包含订单号、用户快照、状态、金额、数量、订单来源、秒杀幂等 token、地址快照、创建时间、支付时间和更新时间。

地址快照字段包括：

- `address_id`
- `receiver_name`
- `receiver_phone`
- `receiver_address`

`jrunmall_user_order_item` 最终只在 `jrunmall_commerce` 中创建。它承载订单项商品快照，包含 SKU、SPU、标题、分类、封面、摘要、单价、数量和行金额。

秒杀 E2E 中不再在 `jrunmall_pms` 创建订单表。`seckill_product_seed.sql` 只写商品测试数据，`seckill_order_seed.sql` 只面向 `jrunmall_commerce`，Redis 初始化另见 `docs/seckill-redis-init.md`。

最终后端数据源约定：

- `jrunmall-product` 主数据源仍连接 `jrunmall_pms`，但普通订单实体使用全限定表名 `jrunmall_commerce.jrunmall_user_order*`。
- `jrunmall-order` 默认连接 `jrunmall_commerce`，秒杀商品快照查询使用 `jrunmall_pms.pms_sku_info` 与 `jrunmall_pms.pms_category`。
- `jrunmall-member` 连接 `jrunmall_ums`。

## 8. 常见错误

- `No database selected`：通常是执行 SQL 时没有目标库。当前 `jrunmall_commerce.sql` 和 `5.1-auth-address.sql` 已内置 `USE jrunmall_commerce`，但仍建议按导入顺序执行。
- SQL 重复导入：`jrunmall_pms.sql` 和 `jrunmall_ums.sql` 包含 `DROP TABLE IF EXISTS`，重复导入会清空并重建对应表。
- 表已存在：`jrunmall_commerce.sql` 使用 `CREATE TABLE IF NOT EXISTS`，如果表结构曾经错误，建议先删除并重建业务库。
- 字段已存在：`5.1-auth-address.sql` 会通过 `INFORMATION_SCHEMA.COLUMNS` 判断字段是否存在，可重复执行。
- Docker 启动成功但表不存在：说明只启动了 MySQL，没有导入业务 SQL。
- `jrunmall_pms` 中出现 `jrunmall_user_order*`：说明导入过旧版混合 SQL 或错误目标库，需要重置 `jrunmall_pms` 并按新顺序导入。
- Java 查不到订单表：确认 `jrunmall_commerce` 已导入，并确认 `jrunmall-product` 对订单实体使用全限定表名，`jrunmall-order` 使用 `jrunmall_commerce`。

## 9. 首次初始化说明

首次初始化需要建库并导入 SQL。具体 Windows CMD 操作见 `docs/Jrun.md`。

## 10. 后续启动场景判断

- 第一次启动且库为空：需要建库并导入 SQL。
- 已导入过 SQL 且未删除库：不需要重复导入。
- 只停止/启动容器且未删除 volume：不需要重导 SQL。
- 删除了 `jrunmall_pms`、`jrunmall_ums`、`jrunmall_commerce`：需要重新导入对应 SQL。
- 执行 `docker compose down -v` 或删除 MySQL volume 后：需要重新建库并导入 SQL。
- 只启动 Docker 不等于 SQL 导入成功，必须检查表是否存在。



