from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ConversationMessage:
    role: str
    content: str
    metadata: dict = field(default_factory=dict)


class ConversationManager:
    def __init__(self, max_history: int = 50):
        self._messages: list[ConversationMessage] = []
        self._max_history = max_history
        self._context: dict[str, Any] = {}

    def add_message(self, role: str, content: str, metadata: Optional[dict] = None):
        self._messages.append(
            ConversationMessage(role=role, content=content, metadata=metadata or {})
        )
        if len(self._messages) > self._max_history:
            self._messages.pop(0)

    def add_user_message(self, content: str):
        self.add_message("user", content)

    def add_assistant_message(self, content: str):
        self.add_message("assistant", content)

    def add_system_message(self, content: str):
        self.add_message("system", content)

    @property
    def messages(self) -> list[dict]:
        return [
            {"role": m.role, "content": m.content} for m in self._messages
        ]

    @property
    def history(self) -> list[ConversationMessage]:
        return list(self._messages)

    def clear(self):
        self._messages.clear()

    def set_context(self, key: str, value: Any):
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        return self._context.get(key, default)

    @property
    def context(self) -> dict:
        return dict(self._context)

    def to_json(self) -> str:
        return json.dumps({
            "messages": [
                {"role": m.role, "content": m.content, "metadata": m.metadata}
                for m in self._messages
            ],
            "context": self._context,
        })

    @classmethod
    def from_json(cls, data: str) -> ConversationManager:
        obj = json.loads(data)
        manager = cls()
        manager._messages = [
            ConversationMessage(**m) for m in obj.get("messages", [])
        ]
        manager._context = obj.get("context", {})
        return manager

    def trim_to_last(self, count: int):
        if len(self._messages) > count:
            self._messages = self._messages[-count:]
