#!/usr/bin/env bash
# Safe v0.2 regression: mocked providers/DBs; no login, coins, orders or publication.
set -euo pipefail
JMALL_REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${1:-}" == "--demo" ]]; then
  printf '%s\n' \
    'Jmall v0.2 人工演示（仅在本地演示账号执行）' \
    '1. 新建商品：苏打饼干 / 食品饮料。点击“免费检查信息”：应追问净含量等事实及目标人群。' \
    '2. 补规格“原味；净含量200克”、人群“办公室上班族”。再次免费检查：ready，未启动模型或扣费。' \
    '3. 选一个平台，明确点击“AI 检查并生成”（真实模型模式会产生费用）；只交付该平台主稿和Skill版本。' \
    '4. 无图时搜索：最多3个带来源候选；取消确认不回填，确认后才使用。无Provider配置时提示不可用，可上传自有图。' \
    '5. 修改副标题/规格，保存草稿；重开后修改和Skill版本保留，买家侧不可见。' \
    '6. 切换平台：旧稿不改标签，要求重新生成；发布门禁应阻止平台不匹配。' \
    '7. 检查并发布：缺图或未解决确认项时阻断。若要测试站内发布，先核验商品事实、图片来源和所有阻断项，再明确确认。' \
    '8. 成功页可返回店铺编辑；不合格修改不覆盖已发布内容。' \
    '9. Grafana / Jmall v0.2 产品漏斗：检查会话阶段、服务端事件、输入检查/生成结果及P95。没有流量时不要声称已达到线上指标。'
  exit 0
fi

command -v uv >/dev/null || { printf '%s\n' '需要 uv（Python 3.12 运行环境）'; exit 1; }
command -v npm >/dev/null || { printf '%s\n' '需要 Node.js/npm'; exit 1; }
[[ -d "$JMALL_REPO_DIR/jmall-web/node_modules" ]] || { printf '%s\n' '请先在 jmall-web 执行 npm ci'; exit 1; }

printf '%s\n' '[1/3] Python 全量回归（Mock，无外部模型调用）'
(
  cd "$JMALL_REPO_DIR/jmall-agent"
  AI_PROVIDER=mock AGENT_DEFAULT_PROVIDER=mock AGENT_STRONG_PROVIDER=mock \
    AGENT_MEDIUM_PROVIDER=mock AGENT_CHEAP_PROVIDER=mock RAG_EMBEDDING_PROVIDER=mock \
    PYTHONPATH=. uv run --python 3.12 --with-requirements requirements.txt pytest -q --disable-warnings
)
printf '%s\n' '[2/3] Java 全量回归（Mock repository，不连接业务数据库）'
if command -v mvn >/dev/null; then
  (cd "$JMALL_REPO_DIR/jmall-backend" && mvn test -q)
else
  command -v docker >/dev/null || { printf '%s\n' '需要 Maven 或 Docker'; exit 1; }
  docker run --rm -v "$JMALL_REPO_DIR/jmall-backend:/app" -v jmall_maven_cache:/root/.m2 \
    -w /app maven:3.9-amazoncorretto-17 mvn test -q
fi
printf '%s\n' '[3/3] 前端全量回归、类型检查与生产构建'
(cd "$JMALL_REPO_DIR/jmall-web" && npm run test:run && npm run build)
printf '%s\n' 'v0.2 自动回归完成。人工验收清单：bash scripts/v0.2-regression.sh --demo'
