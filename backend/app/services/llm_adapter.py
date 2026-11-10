import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMConfig:
    """Configuration for LLM providers."""
    def __init__(self):
        # Provider selection: 'mock' | 'groq' | 'openai' | 'anthropic'
        self.provider = os.getenv("LLM_PROVIDER", "mock").lower()
        self.model = os.getenv("LLM_MODEL")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))
        self.timeout = float(os.getenv("LLM_TIMEOUT", "30.0"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))

        # Keys
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
        self.anthropic_base_url = os.getenv("ANTHROPIC_BASE_URL")

        # Set default model based on provider if not explicitly set
        if not self.model:
            if self.provider == "groq":
                self.model = "llama-3.3-70b-versatile"
            elif self.provider == "openai":
                self.model = "gpt-4o-mini"
            elif self.provider == "anthropic":
                self.model = "claude-3-5-haiku-20241022"
            else:
                self.model = "deterministic-academic-solver"


class LLMAdapter:
    """Provider-independent LLM adapter supporting OpenAI, Groq, Anthropic, and deterministic mock."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        fallback_data: Optional[Dict[str, Any]] = None,
    ) -> T:
        """Generates structured output validated against a Pydantic model schema.
        
        Supports mock mode, live APIs with exponential backoff retries, and schema validation.
        """
        if self.config.provider == "mock" or not self._has_valid_credentials():
            if fallback_data is not None:
                return response_model.model_validate(fallback_data)
            raise ValueError(f"Provider '{self.config.provider}' requested in mock mode without fallback data.")

        # Real API dispatch
        raw_json_str = None
        last_error = None

        for attempt in range(1, self.config.max_retries + 1):
            try:
                if self.config.provider == "groq":
                    raw_json_str = self._call_groq(system_prompt, user_prompt, response_model)
                elif self.config.provider == "openai":
                    raw_json_str = self._call_openai(system_prompt, user_prompt, response_model)
                elif self.config.provider == "anthropic":
                    raw_json_str = self._call_anthropic(system_prompt, user_prompt, response_model)
                else:
                    raise ValueError(f"Unsupported LLM provider: {self.config.provider}")

                # Validate JSON into model
                parsed = json.loads(raw_json_str)
                return response_model.model_validate(parsed)

            except Exception as e:
                last_error = e
                logger.warning(f"LLM call attempt {attempt}/{self.config.max_retries} failed: {e}")
                if attempt < self.config.max_retries:
                    time.sleep(2 ** attempt)

        # If live call failed and fallback is available, use fallback
        if fallback_data is not None:
            logger.warning(f"All LLM retries failed. Falling back to deterministic solver: {last_error}")
            return response_model.model_validate(fallback_data)

        raise RuntimeError(f"LLM invocation failed after {self.config.max_retries} retries: {last_error}")

    def _has_valid_credentials(self) -> bool:
        if self.config.provider == "groq":
            return bool(self.config.groq_api_key)
        elif self.config.provider == "openai":
            return bool(self.config.openai_api_key)
        elif self.config.provider == "anthropic":
            return bool(self.config.anthropic_api_key)
        return False

    def _call_groq(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> str:
        """Calls Groq API with JSON mode."""
        import urllib.request
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.groq_api_key}",
            "Content-Type": "application/json",
        }
        schema = response_model.model_json_schema()
        prompt_with_schema = f"{user_prompt}\n\nYou MUST respond with valid JSON matching this schema:\n{json.dumps(schema)}"

        data = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_with_schema},
            ],
            "temperature": self.config.temperature,
            "response_format": {"type": "json_object"},
        }
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]

    def _call_openai(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> str:
        """Calls OpenAI API with JSON object response format."""
        import urllib.request
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "Content-Type": "application/json",
        }
        schema = response_model.model_json_schema()
        prompt_with_schema = f"{user_prompt}\n\nYou MUST respond with valid JSON matching this schema:\n{json.dumps(schema)}"

        data = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_with_schema},
            ],
            "temperature": self.config.temperature,
            "response_format": {"type": "json_object"},
        }
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]

    def _call_anthropic(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> str:
        """Calls Anthropic API or Anthropic-compatible local proxy."""
        import urllib.request
        base_url = (self.config.anthropic_base_url or "https://api.anthropic.com").rstrip("/")
        url = f"{base_url}/v1/messages"
        headers = {
            "x-api-key": self.config.anthropic_api_key or "none",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        schema = response_model.model_json_schema()
        user_content = f"{user_prompt}\n\nOutput only valid JSON adhering strictly to:\n{json.dumps(schema)}"

        data = {
            "model": self.config.model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_content}],
            "temperature": self.config.temperature,
        }
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            content = body["content"][0]["text"]
            # Extract JSON from markdown backticks if wrapped
            json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content)
            return json_match.group(1) if json_match else content

