from __future__ import annotations

import uuid
from typing import Any, Iterator, List

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field, PrivateAttr, model_validator

from llm.base import LLMResponse
from llm.gemini import GeminiProvider


class GeminiChatModel(BaseChatModel):
    """LangChain BaseChatModel wrapper around GeminiProvider.

    Keeps google-genai (new SDK) and avoids langchain-google-genai / google-generativeai.
    """

    system_prompt: str = ""
    tool_definitions: List[dict] = Field(default_factory=list)

    _provider: Any = PrivateAttr(default=None)

    @model_validator(mode="after")
    def _init_provider(self) -> "GeminiChatModel":
        self._provider = GeminiProvider()
        return self

    @property
    def _llm_type(self) -> str:
        return "gemini-genai"

    def bind_tools(self, tools: List[dict], **kwargs) -> "GeminiChatModel":
        return GeminiChatModel(
            system_prompt=self.system_prompt,
            tool_definitions=tools,
        )

    # --- message conversion helpers ---

    def _to_history(self, messages: list[BaseMessage]) -> list[dict]:
        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                if msg.tool_calls:
                    tc = msg.tool_calls[0]
                    history.append({
                        "role": "assistant",
                        "tool_call": {"name": tc["name"], "args": tc["args"]},
                    })
                else:
                    history.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, ToolMessage):
                history.append({
                    "role": "tool",
                    "content": msg.content,
                    "name": msg.name,
                })
        return history

    def _to_ai_message(self, response: LLMResponse) -> AIMessage:
        if response.tool_call is not None:
            tc = response.tool_call
            return AIMessage(
                content="",
                tool_calls=[{
                    "name": tc.name,
                    "args": tc.args,
                    "id": str(uuid.uuid4()),
                    "type": "tool_call",
                }],
            )
        return AIMessage(content=response.text or "")

    # --- LangChain required interface ---

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        raise NotImplementedError("Use async interface only (ainvoke / astream).")

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        history = self._to_history(messages)
        response = await self._provider.chat(
            history, self.tool_definitions, self.system_prompt
        )
        ai_message = self._to_ai_message(response)
        llm_output = {"token_usage": response.usage, "model_name": self._provider._model}
        return ChatResult(generations=[ChatGeneration(message=ai_message)], llm_output=llm_output)

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> Iterator[ChatGeneration]:
        raise NotImplementedError("Streaming not supported via this wrapper.")
