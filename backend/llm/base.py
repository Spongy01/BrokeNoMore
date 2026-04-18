from dataclasses import dataclass, field


@dataclass
class ToolCall:
    name: str
    args: dict


@dataclass
class LLMResponse:
    text: str | None
    tool_call: ToolCall | None


class BaseLLMProvider:

    async def chat(
        self,
        history: list[dict],
        tools: list[dict],
        system_prompt: str,
    ) -> LLMResponse:
        raise NotImplementedError

    def normalize_history(self, history: list[dict]) -> list:
        raise NotImplementedError

    def normalize_tools(self, tools: list[dict]) -> list:
        raise NotImplementedError
