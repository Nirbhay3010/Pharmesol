import os
import json
from openai import OpenAI
from tools import TOOLS, handle_tool_call

MODEL = "gpt-5.4-mini"


class SalesAgent:
    """Pharmesol inbound sales agent powered by OpenAI."""

    def __init__(self, system_prompt: str):
        self.client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))
        self.messages = [{"role": "system", "content": system_prompt}]

    def generate_greeting(self) -> str:
        """Generate the opening greeting (first assistant turn, no user message)."""
        response = self.client.chat.completions.create(
            model=MODEL,
            messages=self.messages,
            tools=TOOLS,
        )
        greeting = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": greeting})
        return greeting

    def chat(self, user_message: str) -> str:
        """Process a user message and return the agent's response."""
        self.messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=self.messages,
            tools=TOOLS,
        )

        # Handle tool calls in a loop until the model produces a final text response
        while response.choices[0].finish_reason == "tool_calls":
            assistant_message = response.choices[0].message
            self.messages.append(assistant_message)

            for tool_call in assistant_message.tool_calls:
                arguments = json.loads(tool_call.function.arguments)
                result = handle_tool_call(tool_call.function.name, arguments)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            response = self.client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=TOOLS,
            )

        reply = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": reply})
        return reply
