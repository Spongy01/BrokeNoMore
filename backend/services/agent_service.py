import json

from langfuse import Langfuse

from llm.base import BaseLLMProvider
from llm.gemini import GeminiProvider
from tools import (
    TOOL_DEFINITIONS,
    execute_custom_sql,
    get_category_trend,
    get_monthly_summary,
    get_recent_transactions,
    get_spending_by_category,
    get_spending_by_source,
    get_top_merchants,
)

langfuse = Langfuse()

SYSTEM_PROMPT = (
    "You are a personal finance assistant. You have access to tools that query "
    "the user's real transaction data. Use tools whenever the question relates to "
    "the user's actual spending, transactions, categories, or financial history. "
    "Respond conversationally and helpfully. "
    "All transaction data is from 2026. "
    "Never ask the user for their user ID — it is handled automatically. "
    "Always call a tool before answering any financial question; never answer from memory. "
    "Prefer the specific tools (get_spending_by_category, get_monthly_summary, "
    "get_top_merchants, get_recent_transactions, get_category_trend, get_spending_by_source) "
    "whenever they can answer the question. Only use execute_custom_sql for questions "
    "that require custom filtering or grouping not covered by the other tools."
)

TOOL_REGISTRY = {
    "get_spending_by_category": get_spending_by_category,
    "get_monthly_summary": get_monthly_summary,
    "get_top_merchants": get_top_merchants,
    "get_recent_transactions": get_recent_transactions,
    "get_category_trend": get_category_trend,
    "get_spending_by_source": get_spending_by_source,
    "execute_custom_sql": execute_custom_sql,
}

_FALLBACK = (
    "I wasn't able to retrieve that information, please try rephrasing your question."
)


async def run_agent(
    user_id: str,
    message: str,
    history: list[dict],
    provider: BaseLLMProvider = None,
) -> tuple[str, list[dict]]:
    if provider is None:
        provider = GeminiProvider()

    history = [*history, {"role": "user", "content": message}]
    total_tool_calls = 0

    with langfuse.start_as_current_observation(
        name="run_agent",
        as_type="agent",
        input={"user_id": user_id, "message": message},
        metadata={"history_length": len(history)},
    ) as trace:
        for i in range(5):
            with trace.start_as_current_observation(
                name=f"iteration_{i}",
                as_type="span",
                input={"history_length": len(history)},
            ) as span:
                response = await provider.chat(history, TOOL_DEFINITIONS, SYSTEM_PROMPT)

                if response.tool_call is not None:
                    tc = response.tool_call
                    fn = TOOL_REGISTRY[tc.name]

                    # Always use server-side user_id — never trust what Gemini sends
                    final_args = {k: v for k, v in tc.args.items() if k != "user_id"}

                    with span.start_as_current_observation(
                        name=f"tool_call_{tc.name}",
                        as_type="tool",
                        input={"tool": tc.name, "args": final_args},
                    ) as tool_span:
                        result = await fn(user_id, **final_args)
                        total_tool_calls += 1
                        tool_span.update(output=result)

                    history = [
                        *history,
                        {
                            "role": "assistant",
                            "tool_call": {"name": tc.name, "args": dict(tc.args)},
                        },
                        {
                            "role": "tool",
                            "content": json.dumps(result),
                            "name": tc.name,
                        },
                    ]
                    span.update(output={"tool_called": tc.name})

                elif response.text is not None:
                    history = [*history, {"role": "assistant", "content": response.text}]
                    span.update(output={"response": response.text})

                    trace.update(
                        output={"response": response.text},
                        metadata={"iterations": i + 1, "total_tool_calls": total_tool_calls},
                    )
                    langfuse.flush()
                    return response.text, history

        trace.update(
            output={"response": _FALLBACK},
            metadata={"iterations": 5, "total_tool_calls": total_tool_calls},
        )

    langfuse.flush()
    return _FALLBACK, history
