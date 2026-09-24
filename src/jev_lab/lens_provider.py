"""Replaceable typed-decision adapters for the cognitive agent.

The text model and the decision model are separate components.  This module
defines the small contract between them; Jev is one implementation, not a
required part of the agent or of a larger WHOLE system.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

import httpx


@dataclass(frozen=True, slots=True)
class LensDecision:
    selected: tuple[str, ...]
    probabilities: Mapping[str, float] = field(default_factory=dict)
    provider: str = "unknown"
    model: str | None = None
    request_id: str | None = None

    def prompt_context(self, threshold: float) -> str:
        active = ", ".join(self.selected) or "none"
        scored = [
            f"{name}={self.probabilities[name]:.2f}"
            for name in self.selected
            if name in self.probabilities
        ]
        scores = f" Selected relevance probabilities: {', '.join(scored)}." if scored else ""
        floor = (
            ["calibration"]
            if "calibration" in self.selected
            and self.probabilities.get("calibration", threshold) < threshold
            else []
        )
        floor_note = (
            f" Code included {', '.join(floor)} as a calibration floor despite being below threshold."
            if floor else ""
        )
        return (
            f"Typed decision adapter selected these analysis lenses (threshold {threshold:.2f}): "
            f"{active}.{scores}{floor_note} Treat these and their probabilities only as "
            "attention-allocation hints; they are not findings "
            "about the truth of the request or evidence that a cognitive bias is present. "
            "Answer the user's request directly and keep conclusions grounded in its evidence."
        )


class DecisionProvider(Protocol):
    """A pluggable component that selects bounded analysis actions."""

    name: str

    async def select_lenses(
        self,
        state: str,
        lens_definitions: Mapping[str, str],
        *,
        threshold: float,
        max_lenses: int = 8,
    ) -> LensDecision: ...


def validate_lens_decision(
    decision: LensDecision,
    lens_definitions: Mapping[str, str],
    *,
    max_lenses: int = 8,
) -> LensDecision:
    """Validate a provider result at the replaceable-component boundary."""
    if not isinstance(decision, LensDecision):
        raise TypeError("decision provider must return LensDecision")
    allowed = set(lens_definitions)
    selected: list[str] = []
    for raw_name in decision.selected:
        if not isinstance(raw_name, str) or raw_name not in allowed:
            raise ValueError(f"decision provider returned an unknown lens: {raw_name!r}")
        if raw_name not in selected:
            selected.append(raw_name)
    if len(selected) > max(1, max_lenses):
        raise ValueError(f"decision provider selected more than {max_lenses} lenses")

    probabilities: dict[str, float] = {}
    for raw_name, raw_value in decision.probabilities.items():
        if raw_name not in allowed:
            raise ValueError(f"decision provider scored an unknown lens: {raw_name!r}")
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            raise ValueError(f"decision provider returned a nonnumeric score for {raw_name}")
        value = float(raw_value)
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"decision provider returned an invalid score for {raw_name}")
        probabilities[raw_name] = value

    return LensDecision(
        selected=tuple(selected),
        probabilities=probabilities,
        provider=str(decision.provider),
        model=decision.model,
        request_id=decision.request_id,
    )


class JevDecisionProvider:
    """TypeSafe System One adapter. Sends only the current user turn."""

    name = "typesafe-jev"
    DEFAULT_URL = "https://api.typesafe.ai/v1/systemone"
    MAX_STATE_CHARS = 12_000

    def __init__(
        self,
        api_key: str,
        *,
        api_url: str = DEFAULT_URL,
        model: str = "jev-1.13.0",
        timeout_s: float = 8.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("TYPESAFE_API_KEY is required when Jev lens selection is enabled")
        self._api_key = api_key
        self.api_url = api_url.strip()
        self.model = model.strip() or "jev-1.13.0"
        self.timeout_s = min(20.0, max(1.0, float(timeout_s)))

    @classmethod
    def from_env(cls) -> "JevDecisionProvider":
        return cls(
            os.getenv("TYPESAFE_API_KEY", ""),
            api_url=os.getenv("TYPESAFE_API_URL", cls.DEFAULT_URL),
            model=os.getenv("TYPESAFE_JEV_MODEL", "jev-1.13.0"),
        )

    async def select_lenses(
        self,
        state: str,
        lens_definitions: Mapping[str, str],
        *,
        threshold: float,
        max_lenses: int = 8,
    ) -> LensDecision:
        from .safety import require_live
        require_live()
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Jev threshold must be between 0 and 1")
        clean_state = state.strip()
        if not clean_state:
            raise ValueError("Jev state cannot be empty")
        if len(clean_state) > self.MAX_STATE_CHARS:
            raise ValueError("current turn exceeds the Jev input limit; use local lens selection")

        questions: dict[str, dict[str, Any]] = {}
        for name, definition in lens_definitions.items():
            questions[f"lens_{name}"] = {
                "type": "noul",
                "instructions": (
                    f"Would applying the {name} analysis lens materially improve the correctness "
                    "or usefulness of an answer to this request? Judge relevance, not whether any "
                    "particular conclusion or bias is true."
                ),
                "criteria": {
                    "true": f"This perspective is materially relevant to the request: {definition}",
                    "false": "This perspective would not materially improve the answer.",
                },
            }

        payload = {"model": self.model, "state": clean_state, "questions": questions}
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

        answers = result.get("answers") if isinstance(result, dict) else None
        if not isinstance(answers, dict):
            raise ValueError("Jev returned no typed answers")
        probabilities: dict[str, float] = {}
        for name in lens_definitions:
            answer = answers.get(f"lens_{name}")
            if not isinstance(answer, dict) or answer.get("type") != "noul":
                raise ValueError(f"Jev returned an invalid Noul answer for lens {name}")
            value = answer.get("noul")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
                raise ValueError(f"Jev returned an invalid probability for lens {name}")
            probabilities[name] = float(value)

        ranked = sorted(
            (name for name, probability in probabilities.items() if probability >= threshold),
            key=lambda name: (-probabilities[name], name),
        )[:max(1, max_lenses)]
        # Calibration remains a deterministic code-owned floor so the answer
        # acknowledges uncertainty even when the selector is sparse.
        if "calibration" in lens_definitions and "calibration" not in ranked:
            if len(ranked) >= max(1, max_lenses):
                ranked.pop()
            ranked.append("calibration")
        return LensDecision(
            selected=tuple(ranked),
            probabilities=probabilities,
            provider=self.name,
            model=str(result.get("model") or self.model),
            request_id=response.headers.get("x-typesafe-request-id"),
        )
