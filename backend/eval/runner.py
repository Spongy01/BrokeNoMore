import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from langfuse import Langfuse

from eval.fixtures import setup_eval_db, teardown_eval_db, test_engine, test_session_maker
from eval.questions import QUESTIONS

# Monkeypatch before anything that touches the DB executes tool calls.
import database
database.engine = test_engine
database.async_session_maker = test_session_maker

import tools
tools.async_session_maker = test_session_maker

from langchain_core.messages import AIMessage
from services.agent_service import run_agent, _get_graph  # noqa: E402

DATASET_NAME = "finance_agent_eval_v1"


def _ensure_dataset(lf: Langfuse):
    """Create and seed the dataset if it doesn't already have all 30 items."""
    try:
        dataset = lf.get_dataset(DATASET_NAME)
        if len(dataset.items) == len(QUESTIONS):
            print(f"Dataset '{DATASET_NAME}' already seeded ({len(dataset.items)} items), skipping.")
            return dataset
        print(f"Dataset '{DATASET_NAME}' exists but has {len(dataset.items)} items (expected {len(QUESTIONS)}), re-seeding...")
    except Exception:
        print(f"Dataset '{DATASET_NAME}' not found, creating...")
        lf.create_dataset(
            name=DATASET_NAME,
            description="Golden Q&A pairs for the BrokeNoMore finance agent eval.",
        )

    for q in QUESTIONS:
        lf.create_dataset_item(
            dataset_name=DATASET_NAME,
            input={"question": q["question"]},
            expected_output={
                "expected_tool": q["expected_tool"],
                "expected_contains": q["expected_contains"],
            },
            metadata={"category": q["category"], "id": q["id"]},
        )

    dataset = lf.get_dataset(DATASET_NAME)
    print(f"Seeded {len(dataset.items)} items into '{DATASET_NAME}'.")
    return dataset


async def run_eval(run_name: str) -> dict:
    lf = Langfuse()
    dataset = _ensure_dataset(lf)

    await setup_eval_db()

    # Ensure a fresh graph is built against the patched session maker
    import services.agent_service as svc
    svc._graph = None

    results = []

    for item in dataset.items:
        meta = item.metadata or {}
        qid = meta.get("id", "?")
        question_text = item.input["question"]
        expected_tool = item.expected_output["expected_tool"]
        expected_contains = item.expected_output["expected_contains"]
        category = meta.get("category", "unknown")

        try:
            thread_id = str(uuid4())
            response, _, trace_id = await run_agent(
                user_id="eval_user",
                message=question_text,
                thread_id=thread_id,
            )

            # Link this trace to the dataset item under the named run.
            # Must run in a thread — the sync Fern HTTP client conflicts with
            # the running event loop if called directly from async code.
            await asyncio.to_thread(
                lf.api.dataset_run_items.create,
                run_name=run_name,
                dataset_item_id=item.id,
                trace_id=trace_id,
            )

            # Retrieve full message history from checkpointer to find tool calls
            graph = await _get_graph()
            state = await graph.aget_state(
                config={"configurable": {"thread_id": thread_id}}
            )
            messages = state.values.get("messages", [])

            tool_used = None
            for msg in messages:
                if isinstance(msg, AIMessage) and msg.tool_calls:
                    tool_used = msg.tool_calls[0]["name"]
                    break

            tool_correct = tool_used == expected_tool
            answer_correct = all(
                s.lower() in response.lower()
                for s in expected_contains
            )
            passed = tool_correct and answer_correct

            lf.create_score(
                trace_id=trace_id,
                name="tool_routing",
                value=1.0 if tool_correct else 0.0,
                comment=f"called={tool_used or 'none'}, expected={expected_tool}",
                metadata={"category": category},
            )
            lf.create_score(
                trace_id=trace_id,
                name="answer_accuracy",
                value=1.0 if answer_correct else 0.0,
                metadata={"category": category},
            )

        except Exception as exc:
            response = f"ERROR: {exc}"
            tool_used = None
            tool_correct = False
            answer_correct = False
            passed = False

        result = {
            "id": qid,
            "question": question_text,
            "expected_tool": expected_tool,
            "tool_used": tool_used or "none",
            "tool_correct": tool_correct,
            "answer_correct": answer_correct,
            "response": response,
            "passed": passed,
        }
        results.append(result)

        status = "PASS" if passed else "FAIL"
        print(f"Q{qid:02d} {status} | tool={tool_used or 'none'} | {question_text[:60]}")

    # Flush the eval client once after all runs are complete
    lf.flush()

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count
    tool_correct_count = sum(1 for r in results if r["tool_correct"])
    answer_correct_count = sum(1 for r in results if r["answer_correct"])

    summary = {
        "run_name": run_name,
        "total": total,
        "passed": passed_count,
        "failed": failed_count,
        "tool_accuracy": round(tool_correct_count / total * 100, 1),
        "answer_accuracy": round(answer_correct_count / total * 100, 1),
        "overall_accuracy": round(passed_count / total * 100, 1),
        "failures": [
            {"id": r["id"], "question": r["question"]}
            for r in results
            if not r["passed"]
        ],
        "results": results,
    }

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = results_dir / f"eval_{timestamp}.json"
    output_path.write_text(json.dumps(summary, indent=2))

    await teardown_eval_db()

    print("\n--- EVAL SUMMARY ---")
    print(f"Run name:        {run_name}")
    print(f"Total:           {total}")
    print(f"Passed:          {passed_count}")
    print(f"Failed:          {failed_count}")
    print(f"Tool accuracy:   {summary['tool_accuracy']}%")
    print(f"Answer accuracy: {summary['answer_accuracy']}%")
    print(f"Overall:         {summary['overall_accuracy']}%")
    if summary["failures"]:
        print("\nFailed questions:")
        for f in summary["failures"]:
            print(f"  Q{f['id']:02d}: {f['question']}")
    print(f"\nResults saved to: {output_path}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the BrokeNoMore eval suite.")
    parser.add_argument(
        "--run-name",
        default=None,
        help="Name for this eval run in Langfuse (default: eval_run_<timestamp>)",
    )
    args = parser.parse_args()

    _run_name = args.run_name or f"eval_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    asyncio.run(run_eval(_run_name))
