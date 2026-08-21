"""Verify the demo knowledge base with real retrieval queries.

Usage (inside Docker):
    python scripts/verify_demo_kb.py

Reports per-query: top-K chunks, similarity scores, rag_quality, and
aggregate score distribution to help evaluate the 0.8 / 0.5 thresholds.
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List

from app.core.config import Settings
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.retrieval.rag_retriever import assess_rag_quality
from app.retrieval.service import RetrievalService
from app.services.embedding_service import EmbeddingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# Verification queries covering all demo categories
# ═══════════════════════════════════════════════════════════════════════

VERIFY_QUERIES: List[str] = [
    # Category: 茶叶行业
    "茶叶礼盒适合年轻消费者的卖点",
    # Category: 平台风格
    "小红书商品文案应该采用什么风格",
    # Category: 广告合规
    "商品宣传中哪些词可能违反广告法",
    # Category: 卖点方法
    "如何用FAB法则提炼商品卖点",
    # Category: 文案规范
    "淘宝商品详情页文案应该包含哪些要素",
    # Category: 小家电行业
    "空气炸锅的电商卖点如何写",
    # Category: 手机行业
    "智能手机拍照功能应该突出哪些卖点",
    # Category: 平台风格
    "拼多多文案和京东文案有什么不同",
    # Category: 广告合规
    "食品类商品广告有哪些合规要求",
    # Category: 茶叶行业
    "高端茶叶送礼场景的文案写法",
]


def build_settings() -> Settings:
    return Settings(_env_file=None)


def build_services(settings: Settings):
    repository = KnowledgeBaseRepository(settings)
    embedding_service = EmbeddingService(settings)
    retrieval_service = RetrievalService(settings, repository, embedding_service)
    return retrieval_service


def load_kb_id() -> str:
    """Try to load kb_id from the meta file written by prepare_demo_kb.py."""
    meta_path = "/app/data/demo_kb_meta.json"
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            return meta.get("kb_id", "")
    return ""


def find_demo_kb(settings: Settings) -> str:
    """Find the jmall-demo-kb by scanning existing KBs."""
    from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
    from app.services.chunking_service import ChunkingService
    from app.services.knowledge_base_service import KnowledgeBaseService

    repository = KnowledgeBaseRepository(settings)
    kb_service = KnowledgeBaseService(
        repository,
        EmbeddingService(settings),
        ChunkingService(settings),
    )
    summaries = kb_service.list_knowledge_bases()

    # Try meta file first
    from_meta = load_kb_id()
    if from_meta:
        match = next((s for s in summaries if s.id == from_meta), None)
        if match:
            return from_meta

    # Fall back to label match
    for s in summaries:
        if "demo" in s.label.lower() or "jmall-demo" in s.label.lower():
            return s.id

    # Last resort: most recently created KB
    if summaries:
        return summaries[0].id

    return ""


def pad(s: str, width: int) -> str:
    """Pad a string to a fixed width, truncating with … if needed."""
    if len(s) <= width:
        return s.ljust(width)
    return s[: width - 1] + "…"


def run_verification(retrieval_service: RetrievalService, kb_id: str) -> List[Dict[str, Any]]:
    """Run all verification queries and return structured results."""
    print("\n" + "=" * 85)
    print("  RAG Demo KB Verification — Real Retrieval Results")
    print("=" * 85)

    all_results: List[Dict[str, Any]] = []
    scores_all: List[float] = []

    for idx, query in enumerate(VERIFY_QUERIES, 1):
        print(f"\n{'─' * 85}")
        print(f"  Query {idx}: {query}")
        print(f"{'─' * 85}")

        chunks = retrieval_service.retrieve(kb_id, query, top_k=5)
        quality = assess_rag_quality(chunks)

        result = {
            "query": query,
            "quality": quality,
            "chunks": [
                {
                    "rank": i + 1,
                    "score": round(float(c.get("score") or 0), 4),
                    "source": (c.get("sourceFilename") or c.get("metadata", {}).get("source_filename", ""))[:80],
                    "content_preview": (c.get("content") or "")[:120],
                }
                for i, c in enumerate(chunks)
            ],
        }
        all_results.append(result)

        # Collect scores
        for c in chunks:
            s = float(c.get("score") or 0)
            if s > 0:
                scores_all.append(s)

        # Display
        quality_label = quality["quality"].upper()
        print(f"  RAG Quality: {quality_label} | top1={quality['top1_score']:.4f} | "
              f"avg={quality['avg_score']:.4f} | count={quality['result_count']}")

        if not chunks:
            print("  (no results)")
            continue

        # Table header
        print(f"\n  {'Rank':<5} {'Score':<10} {'Source':<45} {'Content Preview'}")
        print(f"  {'─'*4}  {'─'*9}  {'─'*44}  {'─'*24}")

        for chunk in result["chunks"]:
            score_str = f"{chunk['score']:.4f}"
            source = chunk["source"].split("/")[-1] if "/" in chunk["source"] else chunk["source"]
            source = source or "(unknown)"
            preview = chunk["content_preview"].replace("\n", " ")
            print(f"  {chunk['rank']:<5} {score_str:<10} {pad(source, 40)}  {preview[:80]}")

    # Store for summary
    return all_results, scores_all


def print_distribution(scores_all: List[float], all_results: List[Dict[str, Any]]) -> None:
    """Print score distribution and threshold evaluation."""
    print(f"\n\n{'=' * 85}")
    print("  Score Distribution & Threshold Evaluation")
    print(f"{'=' * 85}")

    if not scores_all:
        print("  No scores to analyze.")
        return

    # Per-query quality breakdown
    quality_counts = {"high": 0, "medium": 0, "low": 0, "empty": 0}
    for r in all_results:
        q = r["quality"]["quality"]
        quality_counts[q] = quality_counts.get(q, 0) + 1

    print(f"\n  Quality distribution across {len(all_results)} queries:")
    total = len(all_results)
    for level in ["high", "medium", "low", "empty"]:
        count = quality_counts.get(level, 0)
        pct = f"({100 * count / total:.1f}%)" if total else ""
        bar = "█" * count
        print(f"    {level:>6}: {count} {pct} {bar}")

    # Score statistics
    print(f"\n  Score statistics (across {len(scores_all)} chunks):")
    print(f"    Min:    {min(scores_all):.4f}")
    print(f"    Max:    {max(scores_all):.4f}")
    print(f"    Mean:   {sum(scores_all) / len(scores_all):.4f}")
    sorted_scores = sorted(scores_all)
    n = len(sorted_scores)
    print(f"    Median: {sorted_scores[n // 2]:.4f}")
    print(f"    P25:    {sorted_scores[n // 4]:.4f}")
    print(f"    P75:    {sorted_scores[3 * n // 4]:.4f}")

    # Threshold evaluation
    print(f"\n  Threshold evaluation:")
    above_08 = sum(1 for s in scores_all if s >= 0.8)
    between_05_08 = sum(1 for s in scores_all if 0.5 <= s < 0.8)
    below_05 = sum(1 for s in scores_all if s < 0.5)
    print(f"    ≥ 0.8 (high):     {above_08:>4} chunks ({100 * above_08 / len(scores_all):.1f}%)")
    print(f"    0.5–0.8 (medium): {between_05_08:>4} chunks ({100 * between_05_08 / len(scores_all):.1f}%)")
    print(f"    < 0.5 (low):      {below_05:>4} chunks ({100 * below_05 / len(scores_all):.1f}%)")

    # Top-1 score distribution
    top1_scores = [r["quality"]["top1_score"] for r in all_results if r["quality"]["top1_score"] > 0]
    if top1_scores:
        print(f"\n  Top-1 score distribution across {len(top1_scores)} queries with results:")
        print(f"    Min:    {min(top1_scores):.4f}")
        print(f"    Max:    {max(top1_scores):.4f}")
        print(f"    Mean:   {sum(top1_scores) / len(top1_scores):.4f}")

    # Threshold reasonability assessment
    print(f"\n  Threshold reasonability:")
    if above_08 / max(len(scores_all), 1) < 0.05:
        print(f"    ⚠  ≥0.8 chunks are very rare ({above_08}/{len(scores_all)}).")
        print(f"       Consider lowering the 'high' threshold to 0.7.")
    elif above_08 / max(len(scores_all), 1) > 0.4:
        print(f"    ⚠  ≥0.8 chunks are very common ({above_08}/{len(scores_all)}).")
        print(f"       Consider raising the 'high' threshold to 0.85–0.9.")
    else:
        print(f"    ✓ 'high' threshold (≥0.8) appears reasonable.")

    if below_05 / max(len(scores_all), 1) < 0.1:
        print(f"    ⚠  <0.5 chunks are very rare ({below_05}/{len(scores_all)}).")
        print(f"       Consider raising the 'low'/'medium' boundary to 0.6.")
    elif below_05 / max(len(scores_all), 1) > 0.5:
        print(f"    ⚠  <0.5 chunks are very common ({below_05}/{len(scores_all)}).")
        print(f"       Embedding quality may be poor, or threshold may be too strict.")
    else:
        print(f"    ✓ 'medium' threshold (≥0.5) appears reasonable.")

    print(f"\n{'=' * 85}\n")


def main():
    logger.info("Loading settings and services...")
    settings = build_settings()

    logger.info("Embedding: %s / %s / dim=%d",
                settings.rag_embedding_provider,
                settings.rag_embedding_model,
                settings.resolved_embedding_dimension())

    retrieval_service = build_services(settings)

    # Find the demo KB
    kb_id = find_demo_kb(settings)
    if not kb_id:
        logger.error("No demo KB found! Run prepare_demo_kb.py first.")
        sys.exit(1)

    logger.info("Using KB: %s", kb_id)

    # Run all verification queries
    all_results, scores_all = run_verification(retrieval_service, kb_id)

    # Print distribution
    print_distribution(scores_all, all_results)

    # Write detailed results to JSON for further analysis
    output_path = "/app/data/demo_kb_verify_results.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "kb_id": kb_id,
            "queries": len(all_results),
            "quality_distribution": {
                q: sum(1 for r in all_results if r["quality"]["quality"] == q)
                for q in ["high", "medium", "low", "empty"]
            },
            "results": all_results,
        }, f, ensure_ascii=False, indent=2)
    logger.info("Detailed results saved to %s", output_path)


if __name__ == "__main__":
    main()
