import json

from llm.base import BaseLLMProvider
from llm.gemini import GeminiProvider
from tools import (
    TOOL_DEFINITIONS,
    get_category_trend,
    get_monthly_summary,
    get_recent_transactions,
    get_spending_by_category,
    get_top_merchants,
)

SYSTEM_PROMPT = (
    "You are a personal finance assistant. You have access to tools that query "
    "the user's real transaction data. Use tools whenever the question relates to "
    "the user's actual spending, transactions, categories, or financial history. "
    "Respond conversationally and helpfully."
)

TOOL_REGISTRY = {
    "get_spending_by_category": get_spending_by_category,
    "get_monthly_summary": get_monthly_summary,
    "get_top_merchants": get_top_merchants,
    "get_recent_transactions": get_recent_transactions,
    "get_category_trend": get_category_trend,
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

    for _ in range(5):
        response = await provider.chat(history, TOOL_DEFINITIONS, SYSTEM_PROMPT)

        if response.tool_call is not None:
            tc = response.tool_call
            fn = TOOL_REGISTRY[tc.name]

            # Always use server-side user_id — never trust what Gemini sends
            args = {k: v for k, v in tc.args.items() if k != "user_id"}
            result = await fn(user_id, **args)

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

        elif response.text is not None:
            history = [*history, {"role": "assistant", "content": response.text}]
            return response.text, history

    return _FALLBACK, history
