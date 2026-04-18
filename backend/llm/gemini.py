import json
import os

import google.genai as genai
import google.genai.types as t

from llm.base import BaseLLMProvider, LLMResponse, ToolCall


class GeminiProvider(BaseLLMProvider):

    def __init__(self) -> None:
        self._client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    def normalize_history(self, history: list[dict]) -> list[t.Content]:
        normalized = []
        for message in history:
            role = message["role"]
            content = message.get("content")

            if role == "user":
                normalized.append(t.Content(role="user", parts=[t.Part(text=content)]))

            elif role == "assistant" and "tool_call" in message:
                normalized.append(t.Content(
                    role="model",
                    parts=[
                        t.Part(
                            function_call=t.FunctionCall(
                                name=message["tool_call"]["name"],
                                args=message["tool_call"]["args"],
                            )
                        )
                    ],
                ))

            elif role == "assistant":
                normalized.append(t.Content(role="model", parts=[t.Part(text=content)]))

            elif role == "tool":
                normalized.append(t.Content(
                    role="user",
                    parts=[
                        t.Part(
                            function_response=t.FunctionResponse(
                                name=message["name"],
                                response={"result": json.loads(content)},
                            )
                        )
                    ],
                ))

        return normalized

    def normalize_tools(self, tools: list[dict]) -> list[t.Tool]:
        declarations = [
            t.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=tool["parameters"],
            )
            for tool in tools
        ]
        return [t.Tool(function_declarations=declarations)]

    async def chat(
        self,
        history: list[dict],
        tools: list[dict],
        system_prompt: str,
    ) -> LLMResponse:
        normalized_history = self.normalize_history(history)
        normalized_tools = self.normalize_tools(tools)

        config = t.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=normalized_tools,
        )

        response = await self._client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=normalized_history,
            config=config,
        )

        if response.function_calls:
            fc = response.function_calls[0]
            return LLMResponse(
                text=None,
                tool_call=ToolCall(name=fc.name, args=dict(fc.args)),
            )

        return LLMResponse(text=response.text, tool_call=None)
