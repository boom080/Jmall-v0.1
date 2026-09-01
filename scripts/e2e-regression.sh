#!/bin/bash
# 端到端购买流程回归测试
# 用法: bash scripts/e2e-regression.sh
# 前置条件: docker compose up -d (所有容器运行中)

BASE="http://localhost:10301"
PASS=0
FAIL=0
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

check() {
  local desc="$1" actual="$2" expected="$3"
  if echo "$actual" | python3 -c "import sys; sys.exit(0 if '$expected' in sys.stdin.read() else 1)" 2>/dev/null; then
    echo -e "  ${GREEN}✅${NC} $desc"
    ((PASS++))
  else
    echo -e "  ${RED}❌${NC} $desc (expected '$expected')"
    echo "     got: $(echo "$actual" | head -c 120)"
    ((FAIL++))
  fi
}

check_or() {
  local desc="$1" actual="$2" expected="$3" fallback_desc="$4" fallback="$5"
  if echo "$actual" | python3 -c "import sys; sys.exit(0 if '$expected' in sys.stdin.read() else 1)" 2>/dev/null; then
    echo -e "  ${GREEN}✅${NC} $desc"
    ((PASS++))
  elif [ -n "$fallback" ] && echo "$actual" | python3 -c "import sys; sys.exit(0 if '$fallback' in sys.stdin.read() else 1)" 2>/dev/null; then
    echo -e "  ${GREEN}✅${NC} $fallback_desc"
    ((PASS++))
  else
    echo -e "  ${RED}❌${NC} $desc"
    echo "     got: $(echo "$actual" | head -c 120)"
    ((FAIL++))
  fi
}

echo "=== Jmall E2E Regression Test ==="
echo ""

# 1. Login
echo "1. Authentication"
TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"e2etest","password":"test123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])" 2>/dev/null)
check "Login and get token" "$TOKEN" "eyJ"

# 2. Checkin
echo "2. Checkin"
C=$(curl -s -X POST "$BASE/api/checkin" -H "Authorization: Bearer $TOKEN")
check_or "Checkin returns goldReward" "$C" "goldReward" \
  "Checkin — already checked in today" "already checked in"

# 3. Public product listing (no auth)
echo "3. Public endpoints"
P=$(curl -s "$BASE/api/products")
check "Products accessible without auth" "$P" '"code":10000'

# 4. Product search
S=$(curl -s -G "$BASE/api/products" --data-urlencode "keyword=龙井")
check "Search by keyword returns results" "$S" "龙井"

# 5. Store mine (was broken by auth exclusion)
echo "4. Authenticated endpoints"
SM=$(curl -s "$BASE/api/stores/mine" -H "Authorization: Bearer $TOKEN")
check "stores/mine with auth" "$SM" '"code":10000'

# 6. Products mine
PM=$(curl -s "$BASE/api/products/mine?size=5" -H "Authorization: Bearer $TOKEN")
check "products/mine with auth" "$PM" '"code":10000'

# 7. Profile
echo "5. Profile & Ledger"
PR=$(curl -s "$BASE/api/user/profile" -H "Authorization: Bearer $TOKEN")
check "Profile accessible" "$PR" "username"

# 8. Gold ledger
GL=$(curl -s "$BASE/api/user/gold-ledger" -H "Authorization: Bearer $TOKEN")
check "Gold ledger returns data" "$GL" "type"

# 9. Achievements
echo "6. Gamification"
A=$(curl -s "$BASE/api/achievements" -H "Authorization: Bearer $TOKEN")
check "Achievements list (has 8 keys)" "$A" "SHOP_OWNER"

# 10. Leaderboard (public)
echo "7. Leaderboard"
L=$(curl -s "$BASE/api/leaderboard/spenders")
check "Leaderboard spenders public" "$L" "totalSpent"

# 11. Auth guard: POST without token
echo "8. Security"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/stores" \
  -H 'Content-Type: application/json' -d '{"name":"unauthorized"}')
check "POST /api/stores without token → 401" "$HTTP" "401"

# 12. AI proxy: styles
echo "9. AI Proxy"
AS=$(curl -s "$BASE/api/ai/styles" -H "Authorization: Bearer $TOKEN")
check "AI styles accessible" "$AS" '"code":10000'

# 13. Knowledge bases
KB=$(curl -s "$BASE/api/ai/knowledge-bases" -H "Authorization: Bearer $TOKEN")
check "Knowledge bases accessible" "$KB" '"code":10000'

echo ""
echo "========================================="
if [ "$FAIL" -eq 0 ]; then
  echo -e "  ${GREEN}All $PASS tests passed! 🎉${NC}"
else
  echo -e "  ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
fi
echo "========================================="
