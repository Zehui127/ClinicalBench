#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI Adapter — Run medical scenarios with OpenAI-compatible LLMs.

Wraps AgentProtocol into an OpenAI chat completion loop:
1. Build system prompt + tools
2. Call OpenAI chat completion with tools
3. Parse function call response into ProtocolAction
4. Feed result back as tool result message
5. Repeat until conversation ends

Usage:
    from medical_task_suite.generation.v2.agent_protocol import OpenAIAdapter

    adapter = OpenAIAdapter(protocol)
    result = adapter.run_with_openai(client, model="gpt-4")

    # Or just get the messages for your own loop:
    messages = adapter.build_initial_messages()
    tools = adapter.get_openai_tools()
"""

import json
from typing import Dict, List, Optional, Any

from .protocol import AgentProtocol, ProtocolAction, ProtocolObservation, ProtocolResult


# System prompt template
SYSTEM_PROMPT = """You are a medical AI assistant conducting a clinical consultation.

You are speaking with a patient who has come to you with a health concern. Your job is to:
1. Gather information by asking the patient questions
2. Order appropriate tests when needed
3. Make a diagnosis when you have sufficient evidence
4. Prescribe appropriate treatment

Important guidelines:
- Ask one question at a time
- Be empathetic and professional
- Consider differential diagnoses
- Check for drug interactions and allergies before prescribing
- Make your diagnosis when you have gathered enough evidence
- You must use the provided tools — do not just respond with text

Available tools:
- ask_patient: Ask the patient a question
- order_lab: Order a laboratory test
- order_imaging: Order an imaging study
- check_drug_interaction: Check for drug interactions
- check_allergies: Check patient's allergy history
- make_diagnosis: Make your clinical diagnosis
- prescribe: Prescribe medication
- end_conversation: End the consultation
"""


class OpenAIAdapter:
    """
    Adapter for running medical scenarios with OpenAI-compatible APIs.

    Supports any client that follows the OpenAI chat completion interface:
    - openai.OpenAI
    - openai.AsyncOpenAI
    - Compatible endpoints (vLLM, TGI, etc.)
    """

    def __init__(
        self,
        protocol: AgentProtocol,
        system_prompt: str = SYSTEM_PROMPT,
        max_turns: int = 30,
    ):
        self.protocol = protocol
        self.system_prompt = system_prompt
        self.max_turns = max_turns

    def build_initial_messages(self) -> List[Dict[str, Any]]:
        """Build initial message list for OpenAI API call."""
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]

        # Start the protocol to get opening observation
        obs = self.protocol.start()
        messages.append({
            "role": "user",
            "content": obs.to_prompt(),
        })

        return messages

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Get tools in OpenAI function calling format."""
        return self.protocol.get_tools_openai()

    def parse_function_call(self, response_message: Any) -> Optional[ProtocolAction]:
        """
        Parse OpenAI function call response into ProtocolAction.

        Handles both tool_calls and function_call formats.
        """
        # OpenAI >= 1.0 format: tool_calls
        if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except (json.JSONDecodeError, TypeError):
                arguments = {}

            return ProtocolAction(tool_name=tool_name, arguments=arguments)

        # Legacy function_call format
        if hasattr(response_message, 'function_call') and response_message.function_call:
            fc = response_message.function_call
            try:
                arguments = json.loads(fc.arguments)
            except (json.JSONDecodeError, TypeError):
                arguments = {}

            return ProtocolAction(tool_name=fc.name, arguments=arguments)

        # Text-only response (no function call)
        content = response_message.content or ""
        if content:
            return ProtocolAction(
                tool_name="ask_patient",
                arguments={"question": content},
                raw_text=content,
            )

        return None

    def run_with_openai(
        self,
        client: Any,
        model: str = "gpt-4",
        temperature: float = 0.3,
        **kwargs,
    ) -> ProtocolResult:
        """
        Run the full scenario with an OpenAI client.

        Args:
            client: OpenAI client (openai.OpenAI or compatible)
            model: Model name
            temperature: Sampling temperature
            **kwargs: Additional arguments passed to chat.completions.create()

        Returns:
            ProtocolResult with full evaluation
        """
        messages = self.build_initial_messages()
        tools = self.get_openai_tools()

        for _ in range(self.max_turns):
            # Call LLM
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                temperature=temperature,
                **kwargs,
            )

            msg = response.choices[0].message

            # Parse action
            action = self.parse_function_call(msg)
            if action is None:
                break

            # Add assistant message to history
            messages.append(self._message_to_dict(msg))

            # Execute action
            obs = self.protocol.act(action)

            # Add observation as tool result
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_calls[0].id,
                    "content": obs.to_prompt(),
                })
            else:
                messages.append({
                    "role": "user",
                    "content": obs.to_prompt(),
                })

            # Check if done
            if obs.is_complete:
                break

        return self.protocol.evaluate()

    async def run_with_async_openai(
        self,
        client: Any,
        model: str = "gpt-4",
        temperature: float = 0.3,
        **kwargs,
    ) -> ProtocolResult:
        """
        Async version for openai.AsyncOpenAI.
        """
        messages = self.build_initial_messages()
        tools = self.get_openai_tools()

        for _ in range(self.max_turns):
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                temperature=temperature,
                **kwargs,
            )

            msg = response.choices[0].message
            action = self.parse_function_call(msg)
            if action is None:
                break

            messages.append(self._message_to_dict(msg))
            obs = self.protocol.act(action)

            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_calls[0].id,
                    "content": obs.to_prompt(),
                })
            else:
                messages.append({
                    "role": "user",
                    "content": obs.to_prompt(),
                })

            if obs.is_complete:
                break

        return self.protocol.evaluate()

    def run_with_callable(
        self,
        agent_fn,
        max_turns: int = 30,
    ) -> ProtocolResult:
        """
        Run with any callable agent function.

        agent_fn signature: (observation: ProtocolObservation, tools: List[ToolDefinition]) -> ProtocolAction

        This is the most flexible interface — works with any LLM framework.
        """
        obs = self.protocol.start()
        tools = self.protocol.get_tools()

        for _ in range(max_turns):
            if obs.is_complete:
                break

            action = agent_fn(obs, tools)
            if action is None:
                break

            obs = self.protocol.act(action)

        return self.protocol.evaluate()

    # ================================================================
    # Helpers
    # ================================================================

    @staticmethod
    def _message_to_dict(msg: Any) -> Dict[str, Any]:
        """Convert OpenAI message object to dict for conversation history."""
        d = {"role": "assistant"}

        if msg.content:
            d["content"] = msg.content

        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            d["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]

        return d
