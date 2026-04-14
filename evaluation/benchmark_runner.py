"""
benchmark_runner.py
Orchestrates retrieval evaluation against a ground-truth QA dataset.

Usage:
    python -m evaluation.benchmark_runner --domain finance --qa ground_truth/sample_qa.json --k 5
"""

import argparse
import json
import os
from datetime import datetime, timezone

from core.vector_store import load_index
from evaluation.metrics import precision_at_k, recall_at_k, mean_reciprocal_rank, ndcg_at_k


def run_benchmark(domain: str, qa_path: str, k: int = 5) -> dict:
    """
    Run full retrieval benchmark for a domain.

    Args:
        domain:  The domain name (must have a saved FAISS index).
        qa_path: Path to the ground-truth JSON file.
        k:       Number of documents to retrieve per query.

    Returns:
        Summary dict with aggregate metrics and per-question details.
    """
    with open(qa_path, "r", encoding="utf-8") as f:
        qa_pairs = json.load(f)

    # Filter to matching domain (if qa file contains multiple domains)
    qa_pairs = [q for q in qa_pairs if q.get("domain", domain) == domain]
    if not qa_pairs:
        raise ValueError(f"No QA pairs found for domain '{domain}' in {qa_path}.")

    vector_store = load_index(domain)

    results = []
    for item in qa_pairs:
        question = item["question"]
        relevant_ids = item.get("relevant_chunk_ids", [])

        # Retrieve top-k chunks
        retrieved_docs = vector_store.similarity_search(question, k=k)
        retrieved_ids = [doc.metadata.get("chunk_id", "") for doc in retrieved_docs]

        p_at_k = precision_at_k(retrieved_ids, relevant_ids, k)
        r_at_k = recall_at_k(retrieved_ids, relevant_ids, k)
        mrr = mean_reciprocal_rank(retrieved_ids, relevant_ids)
        ndcg = ndcg_at_k(retrieved_ids, relevant_ids, k)

        results.append({
            "id": item.get("id", ""),
            "question": question,
            "retrieved_ids": retrieved_ids,
            "relevant_ids": relevant_ids,
            "precision_at_k": round(p_at_k, 4),
            "recall_at_k": round(r_at_k, 4),
            "mrr": round(mrr, 4),
            "ndcg_at_k": round(ndcg, 4),
        })

    # Aggregate
    n = len(results)
    summary = {
        "domain": domain,
        "k": k,
        "num_questions": n,
        "avg_precision_at_k": round(sum(r["precision_at_k"] for r in results) / n, 4),
        "avg_recall_at_k": round(sum(r["recall_at_k"] for r in results) / n, 4),
        "avg_mrr": round(sum(r["mrr"] for r in results) / n, 4),
        "avg_ndcg_at_k": round(sum(r["ndcg_at_k"] for r in results) / n, 4),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "per_question": results,
    }
    return summary


def save_report(results: dict, output_dir: str = "evaluation/reports") -> str:
    """Save benchmark results as a JSON report and print a summary table."""
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"benchmark_{results['domain']}_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    _print_summary(results)
    print(f"\nReport saved to: {path}")
    return path


def _print_summary(results: dict) -> None:
    print(f"\n{'='*55}")
    print(f"  Benchmark Results — domain: {results['domain']}, k={results['k']}")
    print(f"{'='*55}")
    print(f"  Questions evaluated : {results['num_questions']}")
    print(f"  Precision@{results['k']}         : {results['avg_precision_at_k']:.4f}")
    print(f"  Recall@{results['k']}            : {results['avg_recall_at_k']:.4f}")
    print(f"  MRR                 : {results['avg_mrr']:.4f}")
    print(f"  NDCG@{results['k']}              : {results['avg_ndcg_at_k']:.4f}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RAG retrieval benchmark.")
    parser.add_argument("--domain", required=True, help="Domain name (must have saved index).")
    parser.add_argument("--qa", default="evaluation/ground_truth/sample_qa.json",
                        help="Path to ground-truth QA JSON file.")
    parser.add_argument("--k", type=int, default=5, help="Number of docs to retrieve.")
    args = parser.parse_args()

    report = run_benchmark(domain=args.domain, qa_path=args.qa, k=args.k)
    save_report(report)
