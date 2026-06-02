# Jrunmall 生产级站点学习文档

本文解释本项目当前用户端、商家端、普通订单和秒杀链路的职责边界。它不是演示页说明，而是按生产级电商站点的结构来理解各服务。

## 1. 端口与服务职责

| 服务 | 本地端口 | 职责 |
| --- | ---: | --- |
| `jrunmall-user-web` | `5174` | 用户端商城：注册登录、商品浏览、购物车、下单、支付、订单、秒杀入口 |
| `jrunmall-merchant-web` | `5175` | 商家端后台：商品管理、普通订单、秒杀订单、AI 工作台、知识库管理 |
| `jrunmall-member` | `8000` | 用户注册、登录、会员资料 |
| `jrunmall-product` | `10301` | 用户端聚合 API、商品、购物车、普通订单、商家商品与普通订单 |
| `jrunmall-order` | `9000` | 秒杀订单落库、秒杀订单查询、Redis Stream 消费 |
| `jrunmall-seckill-go` | `19090` | 秒杀热点入口、库存扣减、幂等控制、写入 Redis Stream |
| `ai-services` | `18080` | 商品文案、知识库等 AI 辅助能力 |

## 2. 前端代理规则

用户端默认只走 `jrunmall-product`：

- 浏览器请求：`/api/product/user/...`
- Vite 转发到：`http://127.0.0.1:10301/product/user/...`

商家端有两类后端：

- `/api/product/...` 转发到 `http://127.0.0.1:10301`
- `/api/order/...` 转发到 `http://127.0.0.1:9000`

因此商家端秒杀订单页依赖 `jrunmall-order`，普通商品和普通订单页依赖 `jrunmall-product`。

## 3. 普通下单链路

1. 用户登录后，前端把 token 放到 `Authorization: Bearer ...`。
2. 加购接口写入 Redis 购物车。
3. 下单接口从 Redis 购物车读取商品快照，并写入 MySQL `jrunmall_commerce.jrunmall_user_order` 与 `jrunmall_user_order_item`。
4. 支付接口把普通订单状态从 `CREATED` 更新为 `PAID`。
5. 订单列表会同时尝试聚合普通订单和秒杀订单；如果 `jrunmall-order` 没启动，普通订单仍应正常显示。

## 4. 秒杀链路

秒杀不是直接由 Java 商品服务扣库存。生产级拆分是：

1. 用户端只展示秒杀商品、价格、限购数量和抢购按钮，不展示活动 ID、SKU ID、幂等 token、Stream event 等后台字段。
2. `jrunmall-product` 根据后端配置计算当前秒杀活动和商品，并把真实活动 ID、SKU ID、用户 ID、请求 ID 转发给 `jrunmall-seckill-go`。
3. `jrunmall-seckill-go` 承接高并发秒杀请求，在 Redis 中做库存扣减和用户幂等。
4. 抢购成功后写入 Redis Stream：`jrunmall:seckill:orders`。
5. `jrunmall-product` 会按秒杀 token 在 `jrunmall_commerce.jrunmall_user_order` 中创建或复用订单，使用户立即进入统一的地址确认和模拟支付流程。
6. `jrunmall-order` 自动消费 Stream；如果订单已由 `jrunmall-product` 创建，会按 `biz_token` 幂等复用，避免重复订单。
7. 用户端订单列表通过 `jrunmall-product` 聚合普通订单和秒杀订单。
8. 商家端秒杀订单页直接查询 `jrunmall-order` 的 `/order/merchant/seckill-orders`。

当前本地默认秒杀配置在 `jrunmall-product` 后端维护：

- `JRUNMALL_SECKILL_ACTIVITY_ID`，默认 `flash-20260429`
- `JRUNMALL_SECKILL_SKU_ID`，默认 `14`
- `JRUNMALL_SECKILL_LIMIT_PER_ORDER`，默认 `1`

这些值只用于后端计算和本地运维预热，不应该出现在用户端页面。

本地测试秒杀前必须完成库存预热：

```cmd
scripts\start-java-local.bat order
scripts\start-seckill-go.bat
scripts\warmup-seckill-local.bat flash-20260429 14 50
```

## 5. 商品数据

基础课程 SQL 中大部分 SKU 都挂在 `cat_id=225`，所以页面看起来像“所有商品都是同一个分类”。项目新增了：

```cmd
resource\db\jrunmall_demo_catalog_seed.sql
```

它补充了食品饮料、生鲜、家用电器、电脑办公、厨具、运动健康等多品类商品。导入后用户端和商家端会优先展示这些较新的 SKU。

## 6. 本地最小启动顺序

普通商城闭环：

```cmd
scripts\start-local-infra.bat
scripts\start-java-local.bat member
scripts\start-java-local.bat product
scripts\start-user-web.bat
scripts\start-merchant-web.bat
```

完整秒杀闭环：

```cmd
scripts\start-java-local.bat order
scripts\start-seckill-go.bat
scripts\warmup-seckill-local.bat flash-20260429 14 50
```

如果商家端秒杀订单 404，优先检查 `9000` 是否监听，以及商家端 Vite 是否已重启。

如果秒杀入口显示 `Connection refused 127.0.0.1:19090`，说明 Go 秒杀服务没有启动。
