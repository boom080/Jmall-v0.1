# Bug 回归测试案例

> 记录开发过程中发现的 Bug 及对应的回归测试案例，用于验证修复效果和防止回归。
> 每个案例包含：问题描述 → 复现步骤 → 修复方案 → 验证命令 → 预期结果。

---

## Bug 0.1 — 未登录用户访问收藏状态触发 401

**发现日期**: 2026-08-07  
**严重程度**: 中  
**影响范围**: 商品详情页 — 未登录用户浏览

### 问题描述
商品详情页 `ProductDetail.vue` 在 `onMounted` 时无条件调用 `GET /api/collections/check/{productId}`，未登录用户访问时后端返回 401，导致页面异常。

### 复现步骤
```bash
# 不携带 token 访问商品详情 — 前端 JS 会自动调用 /api/collections/check/1
curl -s 'http://localhost:10301/api/collections/check/1'
# 预期（修复前）: HTTP 401
# 预期（修复后）: 前端不发起此请求（authStore.isAuthenticated 守卫拦截）
```

### 修复方案
```typescript
// ProductDetail.vue — 添加认证守卫
if (authStore.isAuthenticated) {
  try { collected.value = await http.get(`/collections/check/${product.value!.id}`) }
  catch { /* ignore */ }
}
```

### 验证测试
```bash
# 1. 未登录用户访问商品详情页，不应看到控制台 401 错误
# 2. 收藏按钮应显示为未收藏状态（空心图标）
# 3. 登录后重新访问，收藏状态应正确加载
```

---

## Bug 0.3 — 购买动效金币显示为 0

**发现日期**: 2026-08-07  
**严重程度**: 高（用户可见）  
**影响范围**: 购买后弹出动效

### 问题描述
购买成功后动效中的金币数字始终显示 0，无论实际获得多少金币。

### 复现步骤
```bash
# 注册买家 → 签到 → 购买任意商品
# 观察购买动效中的金币数字
# 修复前: 动效显示 "+0 🪙"
# 修复后: 动效显示实际获得的金币数
```

### 修复方案
```typescript
// App.vue — provide 回调接收并转发 goldEarned 参数
provide('triggerPurchaseEffect', (product: any, multiplier: number, goldEarned: number) => {
  purchaseEffectRef.value?.play(product, multiplier, goldEarned)
})
```

### 根因
`provide` 回调只有 2 个参数，`PurchaseEffect.play()` 签名要求 3 个参数（product, multiplier, goldEarned），第三个参数被丢弃。

### 验证测试
```bash
BUYER_TOKEN=$(curl -s -X POST 'http://localhost:10301/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"buyer1","password":"test123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

# 执行购买
curl -s -X POST 'http://localhost:10301/api/transactions' \
  -H "Authorization: Bearer $BUYER_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"productId":1,"quantity":1}' | python3 -c "
import sys,json
d = json.load(sys.stdin)['data']
assert d['goldEarned'] > 0, f'goldEarned should be > 0, got {d[\"goldEarned\"]}'
print(f'✅ goldEarned = {d[\"goldEarned\"]} (multiplier x{d[\"multiplier\"]})')
"
```

---

## Bug 0.4 — applyStyle 不写入表单字段

**发现日期**: 2026-08-07  
**严重程度**: 中  
**影响范围**: 商家商品编辑器 — AI 风格应用

### 问题描述
点击「应用」风格按钮后，AI 生成的 title 和 detail 没有填充到表单中，用户必须手动复制粘贴。

### 复现步骤
```bash
# 前端操作：
# 1. 进入商家后台 → 商品编辑器
# 2. 选择商品 → AI 面板选择风格 → 点击「生成预览」
# 3. 点击「应用」按钮
# 修复前: 标题和描述字段仍为空/旧值
# 修复后: 标题和描述字段自动填充为 AI 生成的内容
```

### 修复方案
```typescript
// ProductEditor.vue — applyStyle() 填充表单
function applyStyle(style: string) {
  form.style = style as PlatformStyle
  if (stylePreviews.value?.[style]) {
    const preview = stylePreviews.value[style]
    if (preview.title) form.title = preview.title
    if (preview.detail) form.description = preview.detail
    ElMessage.success(`已应用「${style}」风格预览 — 标题和描述已更新`)
  }
}
```

### 验证测试
```bash
# 前端手动验证：
# 1. 生成风格预览后，验证 stylePreviews 对象中有 title 和 detail
# 2. 点击「应用」，验证 form.title 和 form.description 已更新
# 3. 页面上的输入框应显示新的内容
```

---

## Bug 0.5 — 前端 8 个成就 vs 后端 5 个成就（契约漂移）

**发现日期**: 2026-08-07  
**严重程度**: 高  
**影响范围**: 成就墙页面 + 成就触发逻辑

### 问题描述
前端硬编码了 8 个成就卡片，但后端只定义了 5 个。其中 `COLLECTOR_10` 的检查逻辑还有语义错误（统计购买记录而非收藏记录）。

### 复现步骤
```bash
# 查看前端成就列表
curl -s 'http://localhost:5175/achievements' | grep -c 'achievement'
# 修复前: 前端显示 8 张卡片
# 修复后: 前后端一致

# 测试 COLLECTOR_10 触发
# 修复前: 购买 10 件商品触发（错误 — 名称为 "Collector" 应统计收藏）
# 修复后: 收藏 10 件商品触发（正确）
```

### 修复方案
```java
// AchievementService.java — 新增 3 个成就
// SALE_10: 店铺售出 ≥10 件
// NIGHT_OWL: 凌晨 00:00-05:00 期间购买
// WHALE: 单笔交易获得 ≥1,000,000 金币
// 修正 COLLECTOR_10: 从 Transaction 统计改为 UserCollection 统计

// TransactionService + CollectionService — 成就触发点补充
achievementService.checkAndUnlock(store.getUserId());  // 卖家成就
achievementService.checkAndUnlock(userId);              // 收藏触发 COLLECTOR
```

### 验证测试
```bash
SELLER_TOKEN=$(curl -s -X POST 'http://localhost:10301/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"e2etest","password":"test123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

# 检查成就列表应有 8 个（前后端一致）
curl -s 'http://localhost:10301/api/achievements' \
  -H "Authorization: Bearer $SELLER_TOKEN" | python3 -c "
import sys,json
items = json.load(sys.stdin)['data']
expected_keys = {'FIRST_PURCHASE','COLLECTOR_10','BIG_SPENDER_100K','STREAK_7','SHOP_OWNER','SALE_10','NIGHT_OWL','WHALE'}
actual_keys = {a['key'] for a in items}
assert actual_keys == expected_keys, f'Keys mismatch: {actual_keys ^ expected_keys}'
print(f'✅ All 8 achievements present: {sorted(actual_keys)}')
"
```

---

## Bug 0.6 — Achievements.vue 将 API 对象当 Pinia Store 调用

**发现日期**: 2026-08-07  
**严重程度**: 高（运行时崩溃）  
**影响范围**: 成就墙页面完全不可用

### 问题描述
```typescript
// 错误: gamificationApi 是 API 服务对象，不是 Store 构造函数
const gamificationStore = gamificationApi()
// 正确:
const gamificationStore = useGamificationStore()
```

### 复现步骤
```bash
# 前端访问 /achievements 路径
# 修复前: 页面崩溃，控制台报 TypeError: gamificationApi is not a function
# 修复后: 页面正常渲染成就列表
```

### 验证测试
```bash
# 前端页面应返回 200
curl -s -o /dev/null -w "%{http_code}" 'http://localhost:5175/achievements'
# 预期: 200
```

---

## Bug 1.1 — ProductFeed 数据解包路径错误

**发现日期**: 2026-08-07  
**严重程度**: 中  
**影响范围**: 商品列表页 — 商品不显示

### 问题描述
后端 `ProductController.list()` 返回 `Map.of("records", list, "total", count)`，前端用 `result.items || result` 解包，`items` 字段不存在。

### 复现步骤
```bash
# 访问商品列表 API
curl -s 'http://localhost:10301/api/products' | python3 -c "
import sys,json
d = json.load(sys.stdin)['data']
# 修复前: 前端访问 result.items 得到 undefined
# 修复后: 前端访问 result.records 得到商品数组
assert 'records' in d, 'Should have records field'
print(f'✅ {d[\"total\"]} records found')
"
```

### 修复方案
```typescript
// ProductFeed.vue — 正确解包后端的 Map 结构
const result = await http.get('/products', { page, size, keyword })
products.value = result.records || result.items || []
```

---

## Bug 1.2 — AiProxyService 路由路径不匹配

**发现日期**: 2026-08-07  
**严重程度**: 高  
**影响范围**: 知识库管理功能完全不可用

### 问题描述
Java 后端 `AiProxyService` 请求 Agent 的 `/api/knowledge-bases`，但 Agent 的路由注册在 `/api/merchant/knowledge-bases`。

### 复现步骤
```bash
# 通过 Java 代理访问知识库列表
TOKEN=$(curl -s -X POST 'http://localhost:10301/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"e2etest","password":"test123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

# 修复前: Java 请求 /api/knowledge-bases → Agent 返回 404
# 修复后: Java 请求 /api/merchant/knowledge-bases → Agent 正确响应
curl -s 'http://localhost:10301/api/ai/knowledge-bases' \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d = json.load(sys.stdin)
assert d['code'] == 10000, f'Should succeed, got {d}'
print('✅ Knowledge base API accessible via proxy')
"
```

---

## Bug 1.3 — AiProxyService forward() 方法编译错误

**发现日期**: 2026-08-07  
**严重程度**: 高（编译失败）  
**影响范围**: 后端无法正常编译

### 问题描述
重构 `forward()` → `forwardGet()`/`forwardPost()`/`forwardDelete()` 后，`getStyles()` 和 `getCostStats()` 仍调用旧的 `forward()` 方法。

### 修复方案
```java
// getStyles() — forward() → forwardGet()
return forwardGet("/api/ai/styles");
// getCostStats() — forward() → forwardGet()
return forwardGet("/api/admin/cost-stats");
```

---

## Bug 1.4 — Jackson 解析 Agent 响应失败

**发现日期**: 2026-08-07  
**严重程度**: 中  
**影响范围**: AI Proxy 返回的 JSON 被双重包装

### 问题描述
`forwardGet/forwardPost` 返回 `RestTemplate` 的 `String` 响应体，直接传递给 `R.ok()`，导致前端收到 string 而非解析后的 JSON 对象。

### 修复方案
```java
// AiProxyService — 新增 parseForwardResponse()
private R parseForwardResponse(ResponseEntity<String> response) {
    ObjectMapper mapper = new ObjectMapper();
    Object parsed = mapper.readValue(response.getBody(), Object.class);
    return R.ok(parsed);
}
```

### 验证测试
```bash
TOKEN=$(curl -s -X POST 'http://localhost:10301/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"e2etest","password":"test123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

# AI styles 端点应返回数组而非字符串
curl -s 'http://localhost:10301/api/ai/styles' \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d = json.load(sys.stdin)
data = d['data']
assert isinstance(data, list), f'data should be list, got {type(data).__name__}'
print(f'✅ Styles returned as list: {len(data)} items')
"
```

---

## Bug 1.5 — Auth 拦截器 excludePathPatterns 导致 UserContext 为 null

**发现日期**: 2026-08-07  
**严重程度**: 高  
**影响范围**: `GET /api/stores/mine` 和 `GET /api/products/mine` 始终返回错误

### 问题描述
WebConfig 中 `/api/stores/**` 和 `/api/products/**` 被排除出拦截器，导致 `/api/stores/mine` 和 `/api/products/mine` 也跳过拦截器，`UserContext` 从未被设置，`getUserId()` 返回 null。

### 复现步骤
```bash
TOKEN=$(curl -s -X POST 'http://localhost:10301/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"e2etest","password":"test123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

# 修复前
echo "=== Before fix ==="
curl -s 'http://localhost:10301/api/stores/mine' \
  -H "Authorization: Bearer $TOKEN"
# Response: {"code":10040,"msg":"store not found","data":{}}
# Backend log: WHERE (user_id = ?) Parameters: null  ← userId is null!

# 修复后
echo "=== After fix ==="
curl -s 'http://localhost:10301/api/stores/mine' \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d = json.load(sys.stdin)
assert d['code'] == 10000, f'Should return store, got {d}'
assert d['data']['name'] != '', 'Store name should not be empty'
print(f'✅ Store found: {d[\"data\"][\"name\"]} (id={d[\"data\"][\"id\"]})')
"
```

### 根因分析
```
Spring AntPathMatcher:
  /api/stores/** 匹配 → /api/stores/mine   (被排除，拦截器不执行)
  /api/stores/** 匹配 → /api/stores/1       (也被排除)
  
  getById(1) 不需要 UserContext → 碰巧能工作，掩盖了问题
  getMyStore() 需要 UserContext.getUserId() → null → WHERE user_id = null → 0 rows
```

### 修复方案
改为 optional auth 模式 — 拦截器覆盖全部 `/api/**`，GET/OPTIONS 无 token 也能通过，POST/PUT/DELETE 必须有效 token。WebConfig 排除列表从 8 条缩减为 2 条。

### 验证测试
```bash
TOKEN=$(curl -s -X POST 'http://localhost:10301/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"e2etest","password":"test123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

# 测试 1: stores/mine 有 token 应返回店铺
curl -s 'http://localhost:10301/api/stores/mine' \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json; d=json.load(sys.stdin)
assert d['code']==10000, f'stores/mine with auth failed: {d}'
print('✅ Test 1: stores/mine with auth — OK')
"

# 测试 2: products/mine 有 token 应返回商品
curl -s 'http://localhost:10301/api/products/mine?size=2' \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json; d=json.load(sys.stdin)
assert d['code']==10000, f'products/mine with auth failed: {d}'
print('✅ Test 2: products/mine with auth — OK')
"

# 测试 3: 公开 GET 无 token 应允许
curl -s 'http://localhost:10301/api/products' | python3 -c "
import sys,json; d=json.load(sys.stdin)
assert d['code']==10000, f'public products failed: {d}'
print('✅ Test 3: public GET /api/products without token — OK')
"

# 测试 4: POST 无 token 应拒绝
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  'http://localhost:10301/api/stores' \
  -H 'Content-Type: application/json' \
  -d '{"name":"hack"}')
assert [ "$HTTP_CODE" = "401" ] && echo "✅ Test 4: POST without token returns 401" || echo "❌ Test 4: expected 401, got $HTTP_CODE"
```

---

## 端到端购买流程完整验证

### 一键回归脚本
```bash
#!/bin/bash
# 端到端购买流程回归测试
# 用法: bash docs/e2e-regression.sh

BASE="http://localhost:10301"
PASS=0
FAIL=0

check() {
  local desc="$1" actual="$2" expected="$3"
  if echo "$actual" | grep -q "$expected"; then
    echo "  ✅ $desc"; ((PASS++))
  else
    echo "  ❌ $desc (expected '$expected', got '$actual')"; ((FAIL++))
  fi
}

echo "=== Jmall E2E Regression Test ==="
echo ""

# 1. Register unique user
echo "1. Registration"
R=$(curl -s -X POST "$BASE/api/auth/register" -H 'Content-Type: application/json' \
  -d "{\"username\":\"regtest_$(date +%s)\",\"password\":\"test123\",\"nickname\":\"回归测试\"}")
check "Registration succeeds" "$R" "success"

# 2. Login
echo "2. Login"
TOKEN=$(curl -s -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
  -d '{"username":"e2etest","password":"test123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")
check "Login returns token" "$TOKEN" "eyJ"

# 3. Checkin
echo "3. Checkin"
C=$(curl -s -X POST "$BASE/api/checkin" -H "Authorization: Bearer $TOKEN")
check "Checkin succeeds" "$C" "goldReward"

# 4. Public product listing
echo "4. Public products"
P=$(curl -s "$BASE/api/products")
check "Products accessible without auth" "$P" '"code":10000'

# 5. Product search
echo "5. Search"
S=$(curl -s "$BASE/api/products?keyword=龙井")
check "Search returns results" "$S" "龙井"

# 6. Store mine
echo "6. Store mine"
SM=$(curl -s "$BASE/api/stores/mine" -H "Authorization: Bearer $TOKEN")
check "Store mine with auth" "$SM" "测试店铺"

# 7. Products mine
echo "7. Products mine"
PM=$(curl -s "$BASE/api/products/mine?size=5" -H "Authorization: Bearer $TOKEN")
check "Products mine with auth" "$PM" '"code":10000'

# 8. Profile
echo "8. Profile"
PR=$(curl -s "$BASE/api/user/profile" -H "Authorization: Bearer $TOKEN")
check "Profile accessible" "$PR" "username"

# 9. Achievements
echo "9. Achievements"
A=$(curl -s "$BASE/api/achievements" -H "Authorization: Bearer $TOKEN")
check "Achievements list" "$A" "SHOP_OWNER"

# 10. Leaderboard (public)
echo "10. Leaderboard"
L=$(curl -s "$BASE/api/leaderboard/spenders")
check "Leaderboard spenders public" "$L" "totalSpent"

# 11. Auth guard: POST without token
echo "11. Auth guard"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/stores" \
  -H 'Content-Type: application/json' -d '{"name":"unauthorized"}')
check "POST without token returns 401" "$HTTP" "401"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
```

---

## 已知遗留问题（待修复）

| # | 问题 | 影响 | 优先级 |
|---|------|------|--------|
| KB-1 | MyBatis-Plus 分页 total 始终返回 0 | 前端分页组件无法显示总页数 | P2 |
| KB-2 | Leaderboard sellers 缺少 username 字段 | 销售榜只显示 storeId，前端无法展示用户名 | P2 |
| KB-3 | ProductFeed + App.vue 购买逻辑重复 | 两处维护相同的 purchase→effect→achievement 流程 | P3 |
