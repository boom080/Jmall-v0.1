"""Full end-to-end pipeline demo with real RAG + real embeddings.

Demonstrates the complete flow for 3 demo products:
  1. Product input
  2. RAG retrieval (Qwen embedding → pgvector → top-5 chunks)
  3. RAG quality assessment
  4. Agent orchestration (graph pipeline)
  5. Final output with citations

Usage (inside Docker):
    python scripts/demo_full_pipeline.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List

from app.agents.graph import AgentOrchestratorGraph
from app.core.config import Settings
from app.providers.factory import ProviderFactory
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.retrieval.rag_retriever import assess_rag_quality
from app.retrieval.service import RetrievalService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_base_service import KnowledgeBaseService

logging.basicConfig(
    level=logging.WARNING,  # Keep logs quiet during demo
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
# Enable info for our demo output
logging.getLogger("demo").setLevel(logging.INFO)
demo = logging.getLogger("demo")

# ═══════════════════════════════════════════════════════════════════════
# Demo products
# ═══════════════════════════════════════════════════════════════════════

DEMO_PRODUCTS = [
    {
        "name": "明前龙井礼盒",
        "category": "茶叶",
        "description": "2025年明前特级龙井，产自西湖核心产区，手工炒制，豆香浓郁，适合送礼和自饮",
        "price": "398",
        "target_style": "taobao",
    },
    {
        "name": "AI智能拍照手机 X200",
        "category": "手机数码",
        "description": "2亿像素AI影像系统，120Hz高刷屏，5000mAh长续航电池，支持夜景人像和AI消除",
        "price": "2999",
        "target_style": "jd",
    },
    {
        "name": "全自动空气炸锅 AF-508",
        "category": "厨房电器",
        "description": "5.5L大容量，360°热风循环，少油健康炸，8大智能菜单，不粘内胆易清洗",
        "price": "259",
        "target_style": "xiaohongshu",
    },
]


def build_settings() -> Settings:
    return Settings(_env_file=None)


def find_demo_kb(settings: Settings) -> str:
    repository = KnowledgeBaseRepository(settings)
    kb_service = KnowledgeBaseService(
        repository, EmbeddingService(settings), ChunkingService(settings),
    )
    for s in kb_service.list_knowledge_bases():
        if "demo" in s.label.lower():
            return s.id
    return ""


def demo_rag_retrieval(
    retrieval_service: RetrievalService,
    kb_id: str,
    product: Dict[str, str],
) -> Dict[str, Any]:
    """Step 1+2: Real RAG retrieval with quality assessment."""
    query = f"{product['name']} {product['category']} {product['description']}"

    t0 = time.perf_counter()
    chunks = retrieval_service.retrieve(kb_id, query, top_k=5)
    elapsed = time.perf_counter() - t0

    quality = assess_rag_quality(chunks)
    quality["retrieval_ms"] = round(elapsed * 1000)

    return {"query": query, "chunks": chunks, "quality": quality}


def demo_agent_orchestration(
    settings: Settings,
    provider_factory: ProviderFactory,
    retrieval_service: RetrievalService,
    kb_id: str,
    product: Dict[str, str],
) -> Dict[str, Any]:
    """Step 3: Full agent orchestration graph."""
    graph = AgentOrchestratorGraph(
        settings=settings,
        provider_factory=provider_factory,
        retrieval_service=retrieval_service,
    )

    state = {
        "user_request": f"为{product['name']}生成{product['target_style']}风格商品文案",
        "product_info": {
            "title": product["name"],
            "category": product["category"],
            "description": product["description"],
            "price": product["price"],
        },
        "target_style": product["target_style"],
        "knowledge_base_id": kb_id,
        "errors": [],
    }

    t0 = time.perf_counter()
    result = asyncio.run(graph.invoke(state))
    elapsed = time.perf_counter() - t0

    return {
        "orchestration_ms": round(elapsed * 1000),
        "rag_quality": result.get("rag_quality", {}),
        "rag_context_used": bool(result.get("rag_context")),
        "copy_drafts": result.get("copy_drafts", {}),
        "market_research": result.get("market_research", {}),
        "errors": result.get("errors", []),
    }


def demo_print_header(title: str, width: int = 80):
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}")


def demo_print_step(step: int, title: str):
    print(f"\n  ┌─ Step {step}: {title}")


def demo_print_rag_results(chunks: List[Dict], quality: Dict, width: int = 80):
    """Pretty-print RAG retrieval results."""
    q = quality
    label = q["quality"].upper()

    # Quality badge
    if q["quality"] == "high":
        badge = "● HIGH"
    elif q["quality"] == "medium":
        badge = "◐ MEDIUM"
    elif q["quality"] == "low":
        badge = "○ LOW"
    else:
        badge = "— EMPTY"

    print(f"\n  RAG Quality: {badge}")
    print(f"  top1_score={q['top1_score']:.4f}  avg_score={q['avg_score']:.4f}  "
          f"chunks={q['result_count']}  latency={q.get('retrieval_ms', 0)}ms")

    if not chunks:
        print("  (no chunks retrieved)")
        return

    print(f"\n  {'Rank':<5} {'Score':<10} {'Source':<48} {'Content'}")
    print(f"  {'─'*4}  {'─'*9}  {'─'*47}  {'─'*22}")
    for i, c in enumerate(chunks, 1):
        score = float(c.get("score") or 0)
        url = (c.get("sourceFilename") or "")
        # Truncate URL for display
        if len(url) > 48:
            url = url[:45] + "..."
        content = (c.get("content") or "").replace("\n", " ")[:85]
        bar = "█" * min(int(score * 20), 20)
        print(f"  {i:<5} {score:.4f} {bar[:10]:<10} {url:<48} {content}")


def demo_print_agent_output(result: Dict[str, Any]):
    """Pretty-print agent orchestration results."""
    copy = result.get("copy_drafts", {})
    market = result.get("market_research", {})
    rag_quality = result.get("rag_quality", {})
    errors = result.get("errors", [])

    print(f"\n  Orchestration completed in {result.get('orchestration_ms', 0)}ms")

    # RAG quality from agent state
    if rag_quality:
        q_label = rag_quality.get("quality", "?").upper()
        print(f"  RAG quality (from agent state): {q_label}  "
              f"top1={rag_quality.get('top1_score', 0):.4f}  "
              f"avg={rag_quality.get('avg_score', 0):.4f}")

    # Copy drafts
    if copy:
        titles = copy.get("titles", [])
        if titles:
            print(f"\n  【生成的标题】")
            for t in titles[:3]:
                print(f"    • {t}")

        selling_points = copy.get("selling_points", [])
        if selling_points:
            print(f"\n  【核心卖点】")
            for sp in selling_points[:5]:
                print(f"    ✓ {sp}")

        detail = copy.get("detail_copy", "")
        if detail:
            detail_short = detail[:200].replace("\n", " ")
            print(f"\n  【详情页文案（节选）】")
            print(f"    {detail_short}{'...' if len(detail) > 200 else ''}")

        pending = copy.get("pending_confirmations", [])
        if pending:
            print(f"\n  【待商家确认】")
            for p in pending[:3]:
                print(f"    ⚠ {p}")

    # Market research
    if market:
        trends = market.get("trends_summary", "")
        if trends:
            print(f"\n  【市场趋势】")
            print(f"    {trends[:150]}")

    # Errors
    if errors:
        print(f"\n  【流程中的错误】")
        for e in errors[:3]:
            print(f"    ✗ {str(e)[:120]}")

    print(f"\n  RAG used: {result.get('rag_context_used', False)}")
    print(f"  Style: {copy.get('style_name', copy.get('style', '?'))}")


def demo_print_summary(all_results: List[Dict], width: int = 80):
    """Print overall demo summary."""
    print(f"\n\n{'═' * width}")
    print(f"  Demo Summary — 3 Products × Full Pipeline")
    print(f"{'═' * width}")

    print(f"\n  {'Product':<26} {'Style':<14} {'RAG Quality':<12} {'Top1':<9} {'Avg':<9} {'Chunks'}")
    print(f"  {'─'*25}  {'─'*13}  {'─'*11}  {'─'*8}  {'─'*8}  {'─'*6}")

    for r in all_results:
        name = r["product"]
        style = r["style"]
        q = r["quality"]
        print(f"  {name:<26} {style:<14} {q['quality']:<12} {q['top1_score']:<9.4f} {q['avg_score']:<9.4f} {q['result_count']}")

    # Aggregate
    highs = sum(1 for r in all_results if r["quality"]["quality"] == "high")
    mediums = sum(1 for r in all_results if r["quality"]["quality"] == "medium")
    top1s = [r["quality"]["top1_score"] for r in all_results if r["quality"]["top1_score"] > 0]
    avgs = [r["quality"]["avg_score"] for r in all_results if r["quality"]["avg_score"] > 0]

    print(f"\n  Aggregate RAG Quality:")
    print(f"    HIGH: {highs}/{len(all_results)}  MEDIUM: {mediums}/{len(all_results)}")
    if top1s:
        print(f"    Top1 range: {min(top1s):.4f} – {max(top1s):.4f}  (mean: {sum(top1s)/len(top1s):.4f})")
    if avgs:
        print(f"    Avg  range: {min(avgs):.4f} – {max(avgs):.4f}  (mean: {sum(avgs)/len(avgs):.4f})")

    print(f"\n{'═' * width}\n")


def main():
    demo.info("╔══════════════════════════════════════════════════════════════╗")
    demo.info("║     Jmall RAG 全链路 Demo 验收                                ║")
    demo.info("║     Real Qwen Embedding + pgvector + Agent Orchestration     ║")
    demo.info("╚══════════════════════════════════════════════════════════════╝")

    # Setup
    settings = build_settings()
    demo.info("Setup: embedding=%s model=%s dim=%d",
             settings.rag_embedding_provider,
             settings.rag_embedding_model,
             settings.resolved_embedding_dimension())

    # Find demo KB
    kb_id = find_demo_kb(settings)
    if not kb_id:
        demo.error("Demo KB not found! Run prepare_demo_kb.py first.")
        sys.exit(1)
    demo.info("Knowledge Base: %s", kb_id)

    # Build services
    repository = KnowledgeBaseRepository(settings)
    embedding_service = EmbeddingService(settings)
    retrieval_service = RetrievalService(settings, repository, embedding_service)
    provider_factory = ProviderFactory(settings)
    demo.info("AI Provider: %s (mock for demo, RAG is real)", settings.ai_provider)

    all_results = []

    for idx, product in enumerate(DEMO_PRODUCTS, 1):
        demo_print_header(f"Product {idx}/{len(DEMO_PRODUCTS)}: {product['name']}")

        # ── Input ──
        print(f"\n  【商品信息】")
        print(f"  品名: {product['name']}")
        print(f"  类目: {product['category']}")
        print(f"  描述: {product['description']}")
        print(f"  价格: ¥{product['price']}")
        print(f"  风格: {product['target_style']}")

        # ── Step 1+2: RAG Retrieval + Quality ──
        demo_print_step(1, "RAG 检索 — Qwen Embedding → pgvector cosine similarity")
        rag_result = demo_rag_retrieval(retrieval_service, kb_id, product)
        demo_print_rag_results(rag_result["chunks"], rag_result["quality"])

        # ── Step 3: Agent Orchestration ──
        demo_print_step(2, "Agent 编排 — Orchestrator → MarketResearch → Copywriter → Reviewer → StyleAdapter")
        orch_result = demo_agent_orchestration(
            settings, provider_factory, retrieval_service, kb_id, product,
        )
        demo_print_agent_output(orch_result)

        # Collect for summary
        all_results.append({
            "product": product["name"],
            "style": product["target_style"],
            "quality": rag_result["quality"],
            "chunks": [{
                "score": float(c.get("score") or 0),
                "source": (c.get("sourceFilename") or "")[:60],
                "content": (c.get("content") or "")[:100],
            } for c in rag_result["chunks"]],
            "copy_drafts": orch_result.get("copy_drafts", {}),
            "orchestration_ms": orch_result.get("orchestration_ms", 0),
        })

    # ── Summary ──
    demo_print_summary(all_results)

    # Write detailed report
    output_path = "/app/data/demo_full_pipeline_results.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "kb_id": kb_id,
            "embedding_provider": settings.rag_embedding_provider,
            "embedding_model": settings.rag_embedding_model,
            "results": all_results,
        }, f, ensure_ascii=False, indent=2)
    demo.info("Detailed results saved to %s", output_path)

    demo.info("Demo complete — all 3 products processed successfully.")


if __name__ == "__main__":
    main()
