"""Verify RAG quality thresholds with intentionally irrelevant queries.

Compares retrieval scores between e-commerce-relevant queries and
off-topic queries to evaluate whether the 0.8 / 0.5 thresholds
adequately distinguish relevant from irrelevant content.

Usage (inside Docker):
    python scripts/verify_thresholds.py
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
# Irrelevant queries — deliberately off-topic for an e-commerce KB
# ═══════════════════════════════════════════════════════════════════════

IRRELEVANT_QUERIES: List[str] = [
    "Linux 如何查看 8080 端口占用？",
    "Python 如何实现快速排序？",
    "篮球投篮姿势怎么训练？",
    "明天天气怎么样？",
    "Kubernetes Pod 为什么 CrashLoopBackOff？",
    "如何学习英语口语？",
    "git merge 和 git rebase 有什么区别？",
    "如何选择适合自己的跑鞋？",
    "2024年诺贝尔物理学奖颁给了谁？",
    "Photoshop 如何抠图换背景？",
]

# Relevant queries from the earlier verification (for comparison)
RELEVANT_QUERIES: List[str] = [
    "茶叶礼盒适合年轻消费者的卖点",
    "小红书商品文案应该采用什么风格",
    "商品宣传中哪些词可能违反广告法",
    "如何用FAB法则提炼商品卖点",
    "淘宝商品详情页文案应该包含哪些要素",
    "空气炸锅的电商卖点如何写",
    "智能手机拍照功能应该突出哪些卖点",
    "拼多多文案和京东文案有什么不同",
    "食品类商品广告有哪些合规要求",
    "高端茶叶送礼场景的文案写法",
]


def build_settings() -> Settings:
    return Settings(_env_file=None)


def find_demo_kb(settings: Settings) -> str:
    repository = KnowledgeBaseRepository(settings)
    kb_service = KnowledgeBaseService(
        repository,
        EmbeddingService(settings),
        ChunkingService(settings),
    )
    summaries = kb_service.list_knowledge_bases()
    for s in summaries:
        if "demo" in s.label.lower() or "jmall-demo" in s.label.lower():
            return s.id
    if summaries:
        return summaries[0].id
    return ""


def run_queries(
    retrieval_service: RetrievalService,
    kb_id: str,
    queries: List[str],
    label: str,
) -> List[Dict[str, Any]]:
    """Run a batch of queries and return structured results."""
    results: List[Dict[str, Any]] = []
    top1_scores: List[float] = []
    avg_scores: List[float] = []

    print(f"\n{'─' * 90}")
    print(f"  {label} ({len(queries)} queries)")
    print(f"{'─' * 90}")

    for idx, query in enumerate(queries, 1):
        chunks = retrieval_service.retrieve(kb_id, query, top_k=5)
        quality = assess_rag_quality(chunks)

        top1_title = (chunks[0].get("content", "")[:60] if chunks else "(no results)")
        # Extract clean title from content
        if "【资料标题】" in top1_title:
            top1_title = top1_title.split("【资料标题】")[1].split("【")[0].strip()

        result = {
            "query": query,
            "quality": quality["quality"],
            "top1_score": quality["top1_score"],
            "avg_score": quality["avg_score"],
            "result_count": quality["result_count"],
            "top1_title": top1_title,
        }
        results.append(result)
        if quality["top1_score"] > 0:
            top1_scores.append(quality["top1_score"])
        if quality["avg_score"] > 0:
            avg_scores.append(quality["avg_score"])

        # Compact display
        quality_tag = f"[{quality['quality'].upper():>6}]"
        print(f"  {idx:>2}. {quality_tag} top1={quality['top1_score']:.4f}  "
              f"avg={quality['avg_score']:.4f}  n={quality['result_count']}  "
              f"→ {top1_title[:50]}")

    if top1_scores:
        print(f"\n  → top1 range: {min(top1_scores):.4f}–{max(top1_scores):.4f}  "
              f"mean: {sum(top1_scores)/len(top1_scores):.4f}")
    if avg_scores:
        print(f"  → avg  range: {min(avg_scores):.4f}–{max(avg_scores):.4f}  "
              f"mean: {sum(avg_scores)/len(avg_scores):.4f}")

    return results


def print_comparison(irrelevant: List[Dict], relevant: List[Dict]) -> None:
    """Side-by-side comparison and threshold evaluation."""
    print(f"\n\n{'=' * 90}")
    print("  Threshold Evaluation — Relevant vs Irrelevant Queries")
    print(f"{'=' * 90}")

    # 1. Per-group statistics
    def stats(results: List[Dict], name: str) -> Dict[str, Any]:
        top1s = [r["top1_score"] for r in results if r["top1_score"] > 0]
        avgs = [r["avg_score"] for r in results if r["avg_score"] > 0]
        quality_counts = {"high": 0, "medium": 0, "low": 0, "empty": 0}
        for r in results:
            quality_counts[r["quality"]] = quality_counts.get(r["quality"], 0) + 1

        print(f"\n  ┌─ {name} ({len(results)} queries)")
        print(f"  │  Quality: HIGH={quality_counts['high']}  MEDIUM={quality_counts['medium']}  "
              f"LOW={quality_counts['low']}  EMPTY={quality_counts['empty']}")
        if top1s:
            print(f"  │  Top-1 score: min={min(top1s):.4f}  max={max(top1s):.4f}  "
                  f"mean={sum(top1s)/len(top1s):.4f}  median={sorted(top1s)[len(top1s)//2]:.4f}")
        if avgs:
            print(f"  │  Avg  score:  min={min(avgs):.4f}  max={max(avgs):.4f}  "
                  f"mean={sum(avgs)/len(avgs):.4f}")
        print(f"  └─")
        return {"top1s": top1s, "avgs": avgs, "quality_counts": quality_counts}

    rel_stats = stats(relevant, "Relevant (电商)")
    irr_stats = stats(irrelevant, "Irrelevant (无关)")

    # 2. Overlap analysis
    rel_top1s = rel_stats["top1s"]
    irr_top1s = irr_stats["top1s"]

    if rel_top1s and irr_top1s:
        print(f"\n  ┌─ Score overlap analysis")
        print(f"  │  Relevant  top1 range:  [{min(rel_top1s):.4f}, {max(rel_top1s):.4f}]")
        print(f"  │  Irrelevant top1 range: [{min(irr_top1s):.4f}, {max(irr_top1s):.4f}]")

        overlap_min = max(min(rel_top1s), min(irr_top1s))
        overlap_max = min(max(rel_top1s), max(irr_top1s))
        if overlap_min < overlap_max:
            print(f"  │  ⚠ Overlap zone:        [{overlap_min:.4f}, {overlap_max:.4f}]")
            rel_in_overlap = sum(1 for s in rel_top1s if overlap_min <= s <= overlap_max)
            irr_in_overlap = sum(1 for s in irr_top1s if overlap_min <= s <= overlap_max)
            print(f"  │    Relevant queries in overlap:  {rel_in_overlap}/{len(rel_top1s)}")
            print(f"  │    Irrelevant queries in overlap: {irr_in_overlap}/{len(irr_top1s)}")
        else:
            sep = max(min(rel_top1s), min(irr_top1s)) - min(max(rel_top1s), max(irr_top1s))
            print(f"  │  ✓ No overlap — gap of {sep:.4f} between groups")
        print(f"  └─")

    # 3. Threshold-specific evaluation
    print(f"\n  ═══════════════════════════════════════════════════════════")
    print(f"  Threshold Verdict")
    print(f"  ═══════════════════════════════════════════════════════════")

    # 3a. HIGH ≥ 0.8
    rel_high = sum(1 for s in rel_top1s if s >= 0.8)
    irr_high = sum(1 for s in irr_top1s if s >= 0.8)
    print(f"\n  ┌─ Threshold: HIGH (top1 ≥ 0.8)")
    print(f"  │  Relevant  ≥ 0.8: {rel_high}/{len(rel_top1s)}")
    print(f"  │  Irrelevant ≥ 0.8: {irr_high}/{len(irr_top1s)}")
    if irr_high == 0:
        print(f"  │  ✓ No irrelevant queries flagged as HIGH — threshold is safe.")
    else:
        print(f"  │  ⚠ {irr_high} irrelevant queries would be wrongly classified as HIGH.")
    print(f"  └─")

    # 3b. MEDIUM 0.5–0.8
    rel_med = sum(1 for s in rel_top1s if 0.5 <= s < 0.8)
    irr_med = sum(1 for s in irr_top1s if 0.5 <= s < 0.8)
    print(f"\n  ┌─ Threshold: MEDIUM (0.5 ≤ top1 < 0.8)")
    print(f"  │  Relevant  in [0.5,0.8): {rel_med}/{len(rel_top1s)}")
    print(f"  │  Irrelevant in [0.5,0.8): {irr_med}/{len(irr_top1s)}")
    if irr_med > 0:
        print(f"  │  ⚠ {irr_med} irrelevant queries classified as MEDIUM (not LOW).")
        print(f"  │    This suggests the 0.5 lower bound may be too low — irrelevant")
        print(f"  │    queries still get ~0.5–0.7 cosine similarity on a dense KB.")
    else:
        print(f"  │  ✓ No irrelevant queries in MEDIUM range.")
    print(f"  └─")

    # 3c. LOW < 0.5
    rel_low = sum(1 for s in rel_top1s if 0 < s < 0.5)
    irr_low = sum(1 for s in irr_top1s if 0 < s < 0.5)
    print(f"\n  ┌─ Threshold: LOW (0 < top1 < 0.5)")
    print(f"  │  Relevant  < 0.5: {rel_low}/{len(rel_top1s)}")
    print(f"  │  Irrelevant < 0.5: {irr_low}/{len(irr_top1s)}")
    if irr_low > 0 and rel_low == 0:
        print(f"  │  ✓ LOW correctly separates irrelevant from relevant queries.")
    elif irr_low == 0 and rel_low == 0:
        print(f"  │  ⚠ No queries fall into LOW — the 0.5 boundary catches everything.")
        print(f"  │    The LOW category is effectively unused in practice.")
    print(f"  └─")

    # 3d. EMPTY
    irr_empty = irr_stats["quality_counts"]["empty"]
    print(f"\n  ┌─ EMPTY (no results)")
    print(f"  │  Irrelevant queries with no results: {irr_empty}/{len(irrelevant)}")
    print(f"  └─")

    # 4. Overall recommendation
    print(f"\n  ═══════════════════════════════════════════════════════════")
    print(f"  Overall Judgment")
    print(f"  ═══════════════════════════════════════════════════════════")

    all_top1s = rel_top1s + irr_top1s
    print(f"\n  Combined top1 range: [{min(all_top1s):.4f}, {max(all_top1s):.4f}]")

    # Decision logic
    can_high_separate = irr_high == 0
    can_medium_separate = irr_med == 0
    can_low_catch_all = irr_low >= len(irr_top1s) * 0.5  # at least half of irrelevant are LOW
    separation_gap = abs(
        (sum(rel_top1s) / len(rel_top1s) if rel_top1s else 0) -
        (sum(irr_top1s) / len(irr_top1s) if irr_top1s else 0)
    )

    print(f"\n  Q1: Is HIGH ≥ 0.8 reasonable?")
    if can_high_separate:
        print(f"     ✅ YES — no irrelevant queries reach ≥ 0.8.")
        print(f"        HIGH correctly signals genuinely strong retrieval matches.")
    else:
        print(f"     ⚠️  NO — {irr_high} irrelevant queries falsely classified as HIGH.")
        print(f"        Consider raising to 0.85.")

    print(f"\n  Q2: Is MEDIUM ≥ 0.5 too wide?")
    if irr_med > 3:
        print(f"     ⚠️  YES — {irr_med}/{len(irr_top1s)} irrelevant queries classified as MEDIUM.")
        print(f"        The 0.5 threshold is too low to filter out off-topic queries.")
        print(f"        Cosine similarity on dense KBs rarely drops below 0.5 even")
        print(f"        for unrelated content. Consider raising to 0.60–0.65.")
    elif irr_med > 0:
        print(f"     ⚠️  SLIGHTLY — {irr_med}/{len(irr_top1s)} irrelevant queries in MEDIUM.")
        print(f"        [33mConsider monitoring or raising to 0.55–0.60.")
    else:
        print(f"     ✅ NO — MEDIUM only contains relevant queries.")

    print(f"\n  Q3: Can LOW (< 0.5) identify irrelevant queries?")
    if irr_low >= len(irr_top1s) * 0.7:
        print(f"     ✅ YES — {irr_low}/{len(irr_top1s)} irrelevant queries correctly fall into LOW.")
    elif irr_low > 0:
        print(f"     ⚠️  PARTIALLY — only {irr_low}/{len(irr_top1s)} irrelevant queries in LOW.")
        print(f"        LOW is underused because the MEDIUM band is too wide.")
    else:
        print(f"     ❌ NO — 0 irrelevant queries in LOW.")
        print(f"        The 0.5 MEDIUM/LOW boundary is ineffective — it never fires.")
        print(f"        With Qwen v4 embeddings, even unrelated content scores ~0.55–0.70.")

    print(f"\n  Q4: Should thresholds be adjusted?")
    if not can_medium_separate and irr_med > 0:
        # Find a threshold that separates groups better
        if irr_top1s and rel_top1s:
            suggested = max(irr_top1s) + 0.02
            print(f"     📋 Suggested MEDIUM/LOW boundary: {suggested:.2f}")
            print(f"        (just above the highest irrelevant top1 score)")
            print(f"        This would move {sum(1 for s in irr_top1s if s < suggested)}/{len(irr_top1s)}")
            print(f"        irrelevant queries to LOW.")
        print(f"     📋 Suggested HIGH boundary: keep at 0.8 (no change needed).")
        print(f"     📋 Or: introduce a 'confidence penalty' — multiply score by a")
        print(f"        keyword-relevance factor before applying thresholds.")
    elif can_medium_separate:
        print(f"     📋 No adjustment needed — current thresholds work well.")
    else:
        print(f"     📋 Keep 0.8 for HIGH — it is safe.")
        print(f"     📋 Consider raising MEDIUM bottom from 0.5 → 0.60–0.65.")

    print(f"\n{'=' * 90}\n")


def main():
    logger.info("Loading settings and services...")
    settings = build_settings()

    logger.info("Embedding: %s / %s / dim=%d",
                settings.rag_embedding_provider,
                settings.rag_embedding_model,
                settings.resolved_embedding_dimension())

    repository = KnowledgeBaseRepository(settings)
    retrieval_service = RetrievalService(settings, repository, EmbeddingService(settings))

    # Find demo KB
    kb_id = find_demo_kb(settings)
    if not kb_id:
        logger.error("No demo KB found!")
        sys.exit(1)
    logger.info("Using KB: %s", kb_id)

    # Run both batches
    relevant_results = run_queries(retrieval_service, kb_id, RELEVANT_QUERIES, "Relevant (电商相关)")
    irrelevant_results = run_queries(retrieval_service, kb_id, IRRELEVANT_QUERIES, "Irrelevant (无关)")

    # Print comparison and threshold evaluation
    print_comparison(irrelevant_results, relevant_results)

    # Write detailed results
    output_path = "/app/data/threshold_verify_results.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "kb_id": kb_id,
            "relevant": relevant_results,
            "irrelevant": irrelevant_results,
        }, f, ensure_ascii=False, indent=2)
    logger.info("Detailed results saved to %s", output_path)


if __name__ == "__main__":
    main()
