import asyncio
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

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


async def run_eval() -> dict:
    await setup_eval_db()

    # Ensure a fresh graph is built against the patched session maker
    import services.agent_service as svc
    svc._graph = None

    results = []

    for question in QUESTIONS:
        qid = question["id"]
        try:
            thread_id = str(uuid4())
            response, _ = await run_agent(
                user_id="eval_user",
                message=question["question"],
                thread_id=thread_id,
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

            tool_correct = tool_used == question["expected_tool"]
            answer_correct = all(
                s.lower() in response.lower()
                for s in question["expected_contains"]
            )
            passed = tool_correct and answer_correct

        except Exception as exc:
            response = f"ERROR: {exc}"
            tool_used = None
            tool_correct = False
            answer_correct = False
            passed = False

        result = {
            "id": qid,
            "question": question["question"],
            "expected_tool": question["expected_tool"],
            "tool_used": tool_used or "none",
            "tool_correct": tool_correct,
            "answer_correct": answer_correct,
            "response": response,
            "passed": passed,
        }
        results.append(result)

        status = "PASS" if passed else "FAIL"
        print(f"Q{qid:02d} {status} | tool={tool_used or 'none'} | {question['question'][:60]}")

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count
    tool_correct_count = sum(1 for r in results if r["tool_correct"])
    answer_correct_count = sum(1 for r in results if r["answer_correct"])

    summary = {
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
    asyncio.run(run_eval())
