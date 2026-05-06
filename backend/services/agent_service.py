import json

import aiosqlite
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import MessagesState
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
from langfuse.types import TraceContext

from llm.gemini_chat_model import GeminiChatModel
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

_model = GeminiChatModel(system_prompt=SYSTEM_PROMPT).bind_tools(TOOL_DEFINITIONS)
_graph = None
_db_conn = None
_langfuse = Langfuse()


def _should_continue(state: MessagesState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "call_tools"
    return END


async def _call_model(state: MessagesState, config: RunnableConfig) -> dict:
    response = await _model.ainvoke(state["messages"], config=config)
    return {"messages": [response]}


async def _call_tools(state: MessagesState, config: RunnableConfig) -> dict:
    user_id = config["configurable"]["user_id"]
    last = state["messages"][-1]

    tool_messages = []
    for tc in last.tool_calls:
        fn = TOOL_REGISTRY.get(tc["name"])
        if fn is None:
            result = {"error": f"Unknown tool: {tc['name']}"}
        else:
            # user_id is always injected server-side — never from LLM args
            args = {k: v for k, v in tc["args"].items() if k != "user_id"}
            result = await fn(user_id, **args)

        tool_messages.append(
            ToolMessage(
                content=json.dumps(result),
                name=tc["name"],
                tool_call_id=tc["id"],
            )
        )

    return {"messages": tool_messages}


async def _get_graph():
    global _graph, _db_conn
    if _graph is None:
        _db_conn = await aiosqlite.connect("checkpoints.db")
        checkpointer = AsyncSqliteSaver(_db_conn)
        await checkpointer.setup()

        builder = StateGraph(MessagesState)
        builder.add_node("call_model", _call_model)
        builder.add_node("call_tools", _call_tools)
        builder.set_entry_point("call_model")
        builder.add_conditional_edges("call_model", _should_continue)
        builder.add_edge("call_tools", "call_model")

        _graph = builder.compile(checkpointer=checkpointer)

    return _graph


async def run_agent(
    user_id: str,
    message: str,
    thread_id: str,
) -> tuple[str, str, str]:
    graph = await _get_graph()

    with _langfuse.start_as_current_observation(
        name="run_agent",
        as_type="agent",
        input={"user_id": user_id, "message": message, "thread_id": thread_id},
    ) as trace:
        captured_trace_id = trace.trace_id
        langfuse_handler = LangfuseCallbackHandler(
            trace_context=TraceContext(trace_id=trace.trace_id, parent_span_id=trace.id),
        )
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config={
                "configurable": {"thread_id": thread_id, "user_id": user_id},
                "recursion_limit": 10,
                "callbacks": [langfuse_handler],
            },
        )

        last = result["messages"][-1]
        response_text = last.content if isinstance(last, AIMessage) else _FALLBACK
        response_text = response_text or _FALLBACK

        tool_calls_made = [
            m.tool_calls[0]["name"]
            for m in result["messages"]
            if isinstance(m, AIMessage) and m.tool_calls
        ]
        trace.update(
            output={"response": response_text},
            metadata={"tool_calls": tool_calls_made, "thread_id": thread_id},
        )

    _langfuse.flush()
    return response_text, thread_id, captured_trace_id
