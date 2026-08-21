"""Prepare demo RAG knowledge base using real Tavily Search + Qwen Embedding.

Usage (inside Docker):
    python scripts/prepare_demo_kb.py

Requires:
    - TAVILY_API_KEY env var (passed from docker-compose)
    - RAG_EMBEDDING_PROVIDER=qwen (with API key and base URL configured)
    - PostgreSQL + pgvector running and accessible via DATABASE_URL
"""

import json
import logging
import sys
import time
from typing import Any, Dict, List, Set

from app.core.config import Settings
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.retrieval.rag_retriever import assess_rag_quality
from app.retrieval.service import RetrievalService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_base_service import KnowledgeBaseService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# Search topics organized by content category
# ═══════════════════════════════════════════════════════════════════════

SEARCH_TOPICS: List[Dict[str, str]] = [
    # ---- E-commerce copywriting norms (电商文案写作规范) ----
    {"query": "电商详情页文案写作规范 淘宝商品描述 结构化方法 最佳实践", "category": "文案规范"},
    {"query": "电商文案写作技巧 提升转化率 标题卖点优化", "category": "文案规范"},
    {"query": "商品描述内容营销 电商文案行业标准 内容创作", "category": "文案规范"},
    {"query": "电商商品详情页信息结构 图文排版 用户阅读习惯", "category": "文案规范"},

    # ---- Product selling point extraction (商品卖点提炼方法) ----
    {"query": "FAB法则 电商卖点提炼 特征优势利益 实际案例", "category": "卖点方法"},
    {"query": "商品核心卖点提炼技巧 差异化营销 USP独特卖点", "category": "卖点方法"},
    {"query": "电商爆款产品卖点包装 消费者心理学 痛点文案", "category": "卖点方法"},
    {"query": "场景化营销卖点文案 情感化表达 用户画像", "category": "卖点方法"},

    # ---- Platform copywriting styles (淘宝/京东/小红书文案特点) ----
    {"query": "小红书种草文案写作技巧 标题公式 笔记文案 爆款", "category": "平台风格"},
    {"query": "淘宝商品标题优化 SEO关键词布局 搜索排名技巧 2024", "category": "平台风格"},
    {"query": "京东商品详情页文案规范 专业卖点描述 参数化展示", "category": "平台风格"},
    {"query": "拼多多文案特点 价格导向 社交裂变 下沉市场营销", "category": "平台风格"},
    {"query": "抖音电商短视频带货文案 口播脚本技巧 直播话术", "category": "平台风格"},
    {"query": "电商平台文案风格对比 淘宝vs京东vs小红书vs拼多多", "category": "平台风格"},

    # ---- Advertising law compliance (广告法合规) ----
    {"query": "广告法禁用词 极限用语清单 电商合规 违禁词 最第一", "category": "广告合规"},
    {"query": "互联网广告管理办法 电商营销合规要点 2024 处罚案例", "category": "广告合规"},
    {"query": "食品化妆品广告合规 功效宣称规范 虚假宣传认定", "category": "广告合规"},
    {"query": "电商平台广告审核标准 敏感词过滤 合规自查清单", "category": "广告合规"},

    # ---- Tea industry knowledge (茶叶行业) ----
    {"query": "茶叶电商文案 卖点描述 年轻化营销 新式茶饮", "category": "茶叶行业"},
    {"query": "茶叶礼盒送礼场景 包装文案 消费者偏好 高端茶", "category": "茶叶行业"},
    {"query": "龙井茶 铁观音 普洱茶 电商平台销售文案 品类特点", "category": "茶叶行业"},

    # ---- Phone industry knowledge (手机行业) ----
    {"query": "智能手机电商文案 功能卖点写作 拍照芯片续航", "category": "手机行业"},
    {"query": "手机拍照功能文案 影像系统 夜景人像 AI摄影", "category": "手机行业"},

    # ---- Small appliance industry knowledge (小家电行业) ----
    {"query": "小家电电商文案 场景化营销 厨房电器 生活电器", "category": "小家电行业"},
    {"query": "空气炸锅 破壁机 不粘锅 厨房小电电商卖点文案", "category": "小家电行业"},
    {"query": "个护小家电文案 电动牙刷 吹风机 美容仪 健康生活", "category": "小家电行业"},
]

# Minimum content length to keep a result
MIN_CONTENT_LENGTH = 100
# Delay between Tavily API calls (seconds)
API_DELAY_SECONDS = 1.5
# Max results per search query
MAX_RESULTS_PER_QUERY = 4


def build_settings() -> Settings:
    """Build Settings from Docker environment (reads real Qwen/Tavily config)."""
    return Settings(_env_file=None)


def build_services(settings: Settings):
    """Build the full service stack for ingestion."""
    repository = KnowledgeBaseRepository(settings)
    embedding_service = EmbeddingService(settings)
    chunking_service = ChunkingService(settings)
    kb_service = KnowledgeBaseService(repository, embedding_service, chunking_service)
    retrieval_service = RetrievalService(settings, repository, embedding_service)
    return kb_service, retrieval_service


def collect_articles(settings: Settings) -> List[Dict[str, Any]]:
    """Use Tavily Search API to collect articles across all topics.

    Returns deduplicated, quality-filtered article list.
    """
    tavily_key = (settings.tavily_api_key or "").strip()
    if not tavily_key:
        logger.error("TAVILY_API_KEY is not configured — cannot search the web")
        sys.exit(1)

    try:
        from tavily import TavilyClient
    except ImportError:
        logger.error("tavily-python is not installed — cannot search the web")
        sys.exit(1)

    client = TavilyClient(api_key=tavily_key)
    all_articles: List[Dict[str, Any]] = []
    seen_urls: Set[str] = set()
    seen_titles: Set[str] = set()

    for idx, topic in enumerate(SEARCH_TOPICS, 1):
        query = topic["query"]
        category = topic["category"]
        logger.info("[%d/%d] Searching: %s", idx, len(SEARCH_TOPICS), query[:80])

        try:
            response = client.search(
                query,
                search_depth="advanced",
                max_results=MAX_RESULTS_PER_QUERY,
                include_answer=False,
            )
            results = response.get("results") or []
            logger.info("  → %d raw results", len(results))

            for result in results:
                url = (result.get("url") or "").strip()
                title = (result.get("title") or "").strip()
                content = (result.get("content") or "").strip()

                # Skip empty, duplicate, or too-short results
                if not title or not content:
                    continue
                if len(content) < MIN_CONTENT_LENGTH:
                    continue
                if url and url in seen_urls:
                    continue
                # Skip near-duplicate titles (first 30 chars match)
                title_key = title[:30].lower()
                if title_key in seen_titles:
                    continue

                if url:
                    seen_urls.add(url)
                seen_titles.add(title_key)

                all_articles.append({
                    "title": title,
                    "url": url,
                    "content": content,
                    "category": category,
                    "search_query": query,
                    "tavily_score": result.get("score", 0.0),
                })

        except Exception as exc:
            logger.warning("  ✗ Search failed: %s", exc)

        # Rate limiting between searches
        if idx < len(SEARCH_TOPICS):
            time.sleep(API_DELAY_SECONDS)

    logger.info("Collected %d articles after dedup (from %d searches)", len(all_articles), len(SEARCH_TOPICS))
    return all_articles


def import_articles(
    articles: List[Dict[str, Any]],
    kb_service: KnowledgeBaseService,
    kb_id: str,
) -> Dict[str, int]:
    """Import collected articles into the knowledge base.

    Each article becomes a text document that goes through:
    clean → chunk → embed (Qwen) → pgvector.
    """
    stats: Dict[str, int] = {"imported": 0, "skipped_duplicate": 0, "skipped_error": 0, "total_chunks": 0}
    total = len(articles)

    for idx, article in enumerate(articles, 1):
        title = article["title"]
        url = article["url"]
        category = article["category"]

        # Build rich document text with metadata header
        text = (
            f"【资料标题】{title}\n"
            f"【来源网址】{url}\n"
            f"【内容分类】{category}\n"
            f"【搜索关键词】{article['search_query']}\n"
            f"\n{article['content']}"
        )

        try:
            doc = kb_service.import_text_document(
                kb_id,
                title=title,
                content=text,
                source_type="tavily_search",
                source_filename=url,
            )
            stats["imported"] += 1
            stats["total_chunks"] += doc.chunkCount
            logger.info(
                "[%d/%d] ✓ %s (chunks=%d) [%s]",
                idx, total, title[:50], doc.chunkCount, category,
            )
        except ValueError as exc:
            # content-hash detected duplicate
            if "duplicate" in str(exc).lower() or any(
                kw in str(exc).lower() for kw in ["已存在", "重复", "already"]
            ):
                stats["skipped_duplicate"] += 1
                logger.info("[%d/%d] = dup: %s", idx, total, title[:50])
            else:
                stats["skipped_error"] += 1
                logger.warning("[%d/%d] ✗ error: %s — %s", idx, total, title[:50], exc)
        except Exception as exc:
            stats["skipped_error"] += 1
            logger.warning("[%d/%d] ✗ error: %s — %s", idx, total, title[:50], exc)

    return stats


def print_summary(
    articles: List[Dict[str, Any]],
    stats: Dict[str, int],
    kb_id: str,
    kb_service: KnowledgeBaseService,
) -> None:
    """Print a summary of the import operation."""
    print("\n" + "=" * 70)
    print("  Demo KB Import Summary")
    print("=" * 70)

    # Category distribution
    categories: Dict[str, int] = {}
    for a in articles:
        cat = a["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\n  Knowledge Base ID: {kb_id}")
    print(f"  Articles collected:  {len(articles)}")
    print(f"  Documents imported:  {stats['imported']}")
    print(f"  Duplicates skipped:  {stats['skipped_duplicate']}")
    print(f"  Errors skipped:      {stats['skipped_error']}")
    print(f"  Total chunks:        {stats['total_chunks']}")

    print("\n  Source categories:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"    {cat}: {count} articles")

    # Verify via list
    docs = kb_service.list_documents(kb_id)
    summaries = kb_service.list_knowledge_bases()
    kb_info = next((s for s in summaries if s.id == kb_id), None)
    print(f"\n  KB documents (from API): {len(docs)}")
    if kb_info:
        print(f"  KB chunks (from API):   {kb_info.chunkCount}")
        print(f"  Embedding status:       {kb_info.embeddingStatus}")

    print("=" * 70)


def main():
    logger.info("=" * 60)
    logger.info("Preparing jmall-demo-kb with real Tavily + Qwen data")
    logger.info("=" * 60)

    # 1. Build services
    settings = build_settings()
    logger.info("Embedding provider: %s", settings.rag_embedding_provider)
    logger.info("Embedding model:    %s", settings.rag_embedding_model)
    logger.info("Embedding dim:      %d", settings.resolved_embedding_dimension())
    logger.info("Database URL:       %s", settings.database_url[:60] + "..." if len(settings.database_url) > 60 else settings.database_url)

    kb_service, _retrieval_service = build_services(settings)

    # 2. Collect articles via Tavily
    logger.info("\n--- Phase 1: Collecting articles via Tavily Search ---")
    articles = collect_articles(settings)

    if not articles:
        logger.error("No articles collected — check TAVILY_API_KEY and network")
        sys.exit(1)

    # 3. Create the demo knowledge base
    logger.info("\n--- Phase 2: Creating knowledge base ---")
    kb = kb_service.create_knowledge_base(
        "jmall-demo-kb",
        "Jmall 电商文案 RAG 演示知识库 — 包含电商文案规范、平台风格、广告法合规、商品行业知识",
    )
    logger.info("Created KB: %s (%s)", kb.id, kb.label)

    # 4. Import all articles
    logger.info("\n--- Phase 3: Importing articles (clean → chunk → embed → pgvector) ---")
    stats = import_articles(articles, kb_service, kb.id)

    # 5. Summary
    print_summary(articles, stats, kb.id, kb_service)

    # 6. Write the KB ID to a file for the verify script
    meta_path = "/app/data/demo_kb_meta.json"
    import os
    os.makedirs(os.path.dirname(meta_path), exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"kb_id": kb.id, "category_counts": categories}, f, ensure_ascii=False, indent=2)
    logger.info("Metadata saved to %s", meta_path)


if __name__ == "__main__":
    main()
