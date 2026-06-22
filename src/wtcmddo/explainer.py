"""OpenAI-compatible API integration for command explanation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from openai import APIError, OpenAI

from .config import get_api_key
from .prompts import SYSTEM_PROMPT

RISK_LEVEL = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@dataclass
class Explanation:
    explanation: str
    risk: RISK_LEVEL
    reason: str
    category: str
    raw: str


class ExplainerError(Exception):
    """Raised when explanation fails."""


class NotACommandError(Exception):
    """Raised when input is not a shell command."""


def _get_api_key() -> str:
    key = get_api_key()
    if not key:
        raise ExplainerError(
            "No API key found. Run 'wtcmddo setup' or set OPENROUTER_API_KEY."
        )
    return key


def explain_command(
    command: str,
    *,
    model: str = "openai/gpt-4o-mini",
    base_url: str = "https://openrouter.ai/api/v1",
) -> Explanation:
    """Send a command to the configured OpenAI-compatible API and return a structured explanation."""
    api_key = _get_api_key()

    client = OpenAI(base_url=base_url, api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": command},
            ],
            temperature=0.0,
            max_tokens=512,
        )
    except APIError as exc:
        raise ExplainerError(f"API error: {exc}") from exc

    content = completion.choices[0].message.content
    if content is None:
        raise ExplainerError("API returned empty content.")
    content = content.strip()

    if content == "NOT_A_COMMAND":
        raise NotACommandError("That doesn't look like a shell command.")

    return _parse_explanation(content)


def _parse_explanation(content: str) -> Explanation:
    """Parse the strict four-line output format."""
    lines = [line.strip() for line in content.splitlines() if line.strip()]

    fields: dict[str, str] = {}
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip().upper()] = value.strip()

    explanation = fields.get("EXPLANATION")
    risk = fields.get("RISK")
    reason = fields.get("REASON")
    category = fields.get("CATEGORY", "OTHER")

    if not explanation or not risk or not reason:
        raise ExplainerError(
            f"Failed to parse explanation. Raw output:\n{content}"
        )

    if risk not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
        raise ExplainerError(f"Unknown risk level: {risk}")

    return Explanation(
        explanation=explanation,
        risk=risk,  # type: ignore[arg-type]
        reason=reason,
        category=category,
        raw=content,
    )