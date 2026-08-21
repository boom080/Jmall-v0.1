# Jrunmall Seckill Go

## 定位

`jrunmall-seckill-go` 是用户端秒杀 / 抢购热点链路的 Go 服务，不替代 Java 主业务，只负责：

- 秒杀活动预热
- 库存热点控制
- 幂等校验
- 抢购入口
- Redis Streams 写入

## 当前接口

- `GET /health`
- `POST /api/seckill/warmup`
- `POST /api/seckill/purchase`
- `POST /api/seckill/submit`

## 环境变量

`.env.example`

```env
JRUNMALL_SECKILL_ADDR=127.0.0.1:19090
JRUNMALL_SECKILL_REDIS_URL=redis://127.0.0.1:6379/0
JRUNMALL_SECKILL_STREAM=jrunmall:seckill:orders
JRUNMALL_SECKILL_KEY_PREFIX=jrunmall:seckill
JRUNMALL_SECKILL_ORDER_TOKEN_PREFIX=SEC
```

如果你要覆盖默认值，建议复制：

```powershell
copy .env.example .env.local
```

`scripts/start-seckill-go.bat` 当前会优先加载 `.env.local`。

## 本地启动

```powershell
cd D:\java-projects\Jrunmall\jrunmall-seckill-go
go mod tidy
go test ./...
go run .\cmd\server
```

或：

```powershell
scripts\start-seckill-go.bat
```

## 与 Java 的关系

Go 服务抢购成功后向 Redis Stream：

- `jrunmall:seckill:orders`

写入事件字段：

- `requestId`
- `userId`
- `skuId`
- `quantity`
- `seckillSessionId`
- `orderToken`
- `timestamp`

当前 Java 真实消费端为：

- `jrunmall-order`

## 当前边界

- 秒杀链路已完成真实 Redis Streams 本地联调
- 普通商品、购物车、普通订单、模拟支付仍由 Java 主业务承接
- dead-letter 可见化 / 人工补偿入口仍未做



