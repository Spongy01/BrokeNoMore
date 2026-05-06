"""
Usage: python -m eval.metrics --run-name <run_name>

Fetches all traces for a Langfuse dataset run and prints:
  - Latency metrics (p50, p80, p95, mean, max)
  - Aggregate tool_routing and answer_accuracy scores
  - Per-category accuracy breakdown
  - Failed queries (any score == 0.0)
"""
import argparse
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from langfuse import Langfuse  # noqa: E402

DATASET_NAME = "finance_agent_eval_v1"


def fetch_run_data(lf: Langfuse, run_name: str):
    run = lf.get_dataset_run(dataset_name=DATASET_NAME, run_name=run_name)
    if not run.dataset_run_items:
        raise SystemExit(f"No items found in run '{run_name}'. Has the eval been run?")
    return run


def main(run_name: str) -> None:
    lf = Langfuse()
    run = fetch_run_data(lf, run_name)

    print(f"\nFetching {len(run.dataset_run_items)} traces for run '{run_name}'...")

    latencies = []
    # {span_name: [total latency per trace]}  — multiple same-named spans are summed per trace
    span_latencies: dict[str, list[float]] = {"call_model": [], "call_tools": [], "other/overhead": []}
    tool_scores = []
    answer_scores = []
    # {category: {"tool": [values], "answer": [values]}}
    by_category: dict[str, dict[str, list[float]]] = {}
    failures = []

    for run_item in run.dataset_run_items:
        trace = lf.api.trace.get(run_item.trace_id)

        # Question from first human message in trace input
        try:
            question = trace.input["messages"][0]["content"]
        except (KeyError, IndexError, TypeError):
            question = "<unknown>"

        latencies.append(trace.latency)

        call_model_total = sum(
            obs.latency for obs in trace.observations
            if obs.name == "call_model" and obs.latency is not None
        )
        call_tools_total = sum(
            obs.latency for obs in trace.observations
            if obs.name == "call_tools" and obs.latency is not None
        )
        span_latencies["call_model"].append(call_model_total)
        span_latencies["call_tools"].append(call_tools_total)
        span_latencies["other/overhead"].append(
            max(0.0, trace.latency - call_model_total - call_tools_total)
        )

        tool_val = None
        answer_val = None
        tool_comment = ""

        for score in trace.scores:
            cat = (score.metadata or {}).get("category", "unknown")
            if cat not in by_category:
                by_category[cat] = {"tool": [], "answer": []}

            if score.name == "tool_routing":
                tool_val = score.value
                tool_comment = score.comment or ""
                by_category[cat]["tool"].append(score.value)
                tool_scores.append(score.value)
            elif score.name == "answer_accuracy":
                answer_val = score.value
                by_category[cat]["answer"].append(score.value)
                answer_scores.append(score.value)

        if tool_val == 0.0 or answer_val == 0.0:
            failures.append({
                "question": question,
                "tool_routing": tool_val,
                "answer_accuracy": answer_val,
                "tool_comment": tool_comment,
            })

    # ── Latency ─────────────────────────────────────────────────────────────
    lat = np.array(latencies)
    print("\n── Latency (seconds) ──────────────────────────────────────")
    print(f"  p50:   {np.percentile(lat, 50):.2f}s")
    print(f"  p80:   {np.percentile(lat, 80):.2f}s")
    print(f"  p95:   {np.percentile(lat, 95):.2f}s")
    print(f"  mean:  {np.mean(lat):.2f}s")
    print(f"  max:   {np.max(lat):.2f}s")

    # ── Span latency breakdown ───────────────────────────────────────────────
    print("\n── Span Latency Breakdown ──────────────────────────────────")
    print(f"  {'span':<18}  {'p50':>6}  {'p95':>6}")
    print(f"  {'-' * 18}  {'-' * 6}  {'-' * 6}")
    for span_name, values in span_latencies.items():
        arr = np.array(values)
        print(f"  {span_name:<18}  {np.percentile(arr, 50):.2f}s  {np.percentile(arr, 95):.2f}s")

    # ── Aggregate scores ─────────────────────────────────────────────────────
    print("\n── Aggregate Scores ────────────────────────────────────────")
    if tool_scores:
        print(f"  tool_routing:    {sum(tool_scores) / len(tool_scores) * 100:.1f}%  ({int(sum(tool_scores))}/{len(tool_scores)})")
    if answer_scores:
        print(f"  answer_accuracy: {sum(answer_scores) / len(answer_scores) * 100:.1f}%  ({int(sum(answer_scores))}/{len(answer_scores)})")

    # ── Per-category breakdown ───────────────────────────────────────────────
    print("\n── Per-Category Accuracy ───────────────────────────────────")
    col_w = max(len(c) for c in by_category) + 2
    print(f"  {'category':<{col_w}}  {'tool_routing':>14}  {'answer_accuracy':>16}")
    print(f"  {'-' * col_w}  {'-' * 14}  {'-' * 16}")
    for cat in sorted(by_category):
        t = by_category[cat]["tool"]
        a = by_category[cat]["answer"]
        t_pct = f"{sum(t) / len(t) * 100:.0f}% ({int(sum(t))}/{len(t)})" if t else "n/a"
        a_pct = f"{sum(a) / len(a) * 100:.0f}% ({int(sum(a))}/{len(a)})" if a else "n/a"
        print(f"  {cat:<{col_w}}  {t_pct:>14}  {a_pct:>16}")

    # ── Failures ─────────────────────────────────────────────────────────────
    print(f"\n── Failed Queries ({len(failures)} / {len(run.dataset_run_items)}) ─────────────────────")
    if not failures:
        print("  All queries passed.")
    else:
        for f in failures:
            flags = []
            if f["tool_routing"] == 0.0:
                flags.append(f"tool FAIL  [{f['tool_comment']}]")
            if f["answer_accuracy"] == 0.0:
                flags.append("answer FAIL")
            print(f"  • {f['question']}")
            for flag in flags:
                print(f"      {flag}")

    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print metrics for a Langfuse eval run.")
    parser.add_argument("--run-name", required=True, help="Name of the Langfuse dataset run")
    args = parser.parse_args()
    main(args.run_name)
