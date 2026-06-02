# Jrunmall User Web

## 当前范围

用户端当前已包含：

- 首页
- 商品列表页
- 商品详情页
- 购物车页
- 下单确认页
- 订单列表页
- 订单详情页
- 秒杀调试页
- 登录页
- 注册页
- 用户中心页
- 地址管理页

## 已完成链路

- 真实商品接口展示
- 真实登录态 MVP
- 地址管理
- 普通下单与模拟支付
- 普通订单 + 秒杀订单统一后端聚合查询
- 订单详情地址快照展示
- 未登录访问购物车 / 下单 / 订单 / 秒杀 / 地址页时登录保护

## 当前边界

- 不接真实支付
- 不做复杂省市区组件
- 用户中心仍是最小版

## 关键接口

- `POST /user/auth/register`
- `POST /user/auth/login`
- `POST /user/auth/logout`
- `GET /user/auth/me`
- `GET /user/addresses`
- `POST /user/addresses`
- `PUT /user/addresses/{addressId}`
- `DELETE /user/addresses/{addressId}`
- `GET /product/user/cart/items`
- `POST /product/user/orders`
- `GET /product/user/orders/all`
- `GET /product/user/orders/all/{orderRef}`
- `POST /product/user/orders/{orderId}/pay`

## 环境变量

`.env.example`

```env
VITE_API_BASE_URL=/api
VITE_API_PROXY_TARGET=http://127.0.0.1:10301
VITE_APP_TITLE=Jrunmall User
```

## 本地启动

```powershell
cd D:\java-projects\GuliMall\jrunmall-user-web
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

或：

```powershell
scripts\start-user-web.bat
```

## 测试与构建

```powershell
npm run test:run
npm run build
```

## 本地验证结论

截至 2026-05-07，已真实验证：

- 注册
- 登录
- 地址新增
- 加购
- 普通下单
- 订单详情地址快照展示
- 退出登录后访问购物车接口返回 `401`

详细见：

- `../docs/5.6-jrunmall-local-runbook.md`
- `../docs/5.7-jrunmall-local-stack-validation.md`
- `../docs/5.6-jrunmall-demo-script.md`





