# Jrunmall Merchant Web

## 当前范围

商家端当前负责：

- 商品管理可编辑版
- 普通订单只读页
- 秒杀订单只读页
- AI 工作台
- 知识库管理最小闭环

## 已完成链路

- 商品列表与编辑弹窗
- 编辑字段：
  - `title`
  - `category`
  - `price`
  - `sellingPoints`
  - `coverUrl`
  - `status`
- 知识库新增
- 文本导入
- chunk / embedding 状态查看
- 跳转 AI 工作台
- 基于知识库生成商品文案

## 图片策略

- `coverUrl` 为空时继续使用占位图
- 当前已支持：
  - 手动编辑图片 URL
  - 通过 Java 正式接口上传图片到 OSS 后回填 `coverUrl`
- 当前未支持：
  - 完整图片上传管理系统
  - 多图上传
  - 图片裁剪

## OSS 上传说明

商家端上传流程：

`Merchant Web -> jrunmall-product -> OSS -> 回填 coverUrl`

当前注意事项：

- 若未填写根目录 `.env.local` 中的 `JRUNMALL_OSS_*` 变量，上传会失败
- 上传失败时页面会明确提示，并保留手动填写图片 URL 的 fallback

## 关键接口

### 商品管理

- `GET /product/merchant/products`
- `GET /product/merchant/products/{id}`
- `PUT /product/merchant/products/{id}`
- `POST /product/merchant/products/upload-image`

### 知识库

- `GET /product/merchant/knowledge-bases`
- `POST /product/merchant/knowledge-bases`
- `GET /product/merchant/knowledge-bases/{knowledgeBaseId}/documents`
- `POST /product/merchant/knowledge-bases/{knowledgeBaseId}/documents/text`

### AI 工作台

- `GET /product/ai/models`
- `GET /product/ai/knowledge-bases`
- `POST /product/ai/product-copy/generate`

## 环境变量

看 `.env.example`：

```env
VITE_API_BASE_URL=/api
VITE_API_PROXY_TARGET=http://127.0.0.1:10301
VITE_ORDER_API_BASE_URL=http://127.0.0.1:9000
VITE_APP_TITLE=Jrunmall Merchant
```

## 本地启动

```powershell
cd D:\java-projects\GuliMall\jrunmall-merchant-web
npm install
npm run dev -- --host 127.0.0.1 --port 5175
```

或：

```powershell
scripts\start-merchant-web.bat
```

## 测试与构建

```powershell
npm run test:run
npm run build
```

## 当前边界

- 不扩第二个 AI 功能
- 不做复杂文件上传 / PDF 解析
- 不做商家端复杂报表





