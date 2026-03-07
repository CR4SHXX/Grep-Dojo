"""GrepDojo AI service – Gemini initialization and low-level helpers."""
import json
import re
from typing import Any, Dict, Optional

import google.genai as genai
from google.genai import types as genai_types

from config.constants import (
    GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE_EXPLAIN,
    GEMINI_TEMPERATURE_HINT,
    GEMINI_TEMPERATURE_MISSION,
    GEMINI_TEMPERATURE_VALIDATE,
)
from utils.logger import get_logger

log = get_logger(__name__)


class AIService:
    """Wraps Gemini model calls with retry and JSON cleanup."""

    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._api_key = api_key
        log.info("AIService initialised")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_config(self, temperature: float) -> genai_types.GenerateContentConfig:
        return genai_types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
        )

    @staticmethod
    def _clean_json(raw: str) -> str:
        """Strip markdown fences and whitespace from raw AI text."""
        text = raw.strip()
        # Remove ```json ... ``` or ``` ... ```
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    def _call(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        """Send a prompt to Gemini and return raw text."""
        config = self._make_config(temperature)
        combined = f"{system_prompt}\n\n{user_prompt}"
        response = self._client.models.generate_content(
            model=GEMINI_MODEL,
            contents=combined,
            config=config,
        )
        return response.text

    def _call_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        retry_msg: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Call Gemini and parse JSON, with one retry on parse failure."""
        raw = self._call(system_prompt, user_prompt, temperature)
        cleaned = self._clean_json(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            log.warning("JSON parse failed (attempt 1): %s — raw: %s", exc, cleaned[:200])
            # Retry with corrective message
            correction = retry_msg or "Return ONLY valid JSON. Do not include markdown or extra text."
            raw2 = self._call(system_prompt, f"{user_prompt}\n\n{correction}", temperature)
            cleaned2 = self._clean_json(raw2)
            return json.loads(cleaned2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_mission(self, prompt_system: str, prompt_user: str) -> Dict[str, Any]:
        return self._call_json(prompt_system, prompt_user, GEMINI_TEMPERATURE_MISSION)

    def validate_command(self, prompt_system: str, prompt_user: str) -> Dict[str, Any]:
        return self._call_json(
            prompt_system,
            prompt_user,
            GEMINI_TEMPERATURE_VALIDATE,
        )

    def validate_command_retry(self, prompt_system: str, prompt_user: str, correction: str) -> Dict[str, Any]:
        """Second call with an explicit correction message appended."""
        corrected_user = f"{prompt_user}\n\n{correction}"
        return self._call_json(prompt_system, corrected_user, GEMINI_TEMPERATURE_VALIDATE)

    def get_hint(self, prompt_system: str, prompt_user: str) -> str:
        return self._call(prompt_system, prompt_user, GEMINI_TEMPERATURE_HINT)

    def get_explanation(self, prompt_system: str, prompt_user: str) -> str:
        return self._call(prompt_system, prompt_user, GEMINI_TEMPERATURE_EXPLAIN)
