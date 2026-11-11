import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Type, TypeVar
import dotenv
from pydantic import BaseModel

from app.services.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMConfig:
    """Configuration for LLM providers."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        dotenv.load_dotenv(override=True)
        # Provider selection: 'mock' | 'groq' | 'openai' | 'anthropic'
        self.provider = (provider or os.getenv("LLM_PROVIDER", "mock")).lower()
        self.model = model or os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
        self.fallback_model = fallback_model or os.getenv("LLM_FALLBACK_MODEL", "qwen/qwen3.8-27b")
        self.temperature = float(temperature if temperature is not None else os.getenv("LLM_TEMPERATURE", "0.0"))
        self.reasoning_effort = os.getenv("LLM_REASONING_EFFORT", "high")
        self.timeout = float(os.getenv("LLM_TIMEOUT", "60.0"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        self.max_concurrency = int(os.getenv("LLM_MAX_CONCURRENCY", "1"))
        self.structured_output = os.getenv("LLM_STRUCTURED_OUTPUT", "true").lower() in ("true", "1", "yes")

        # Keys (safely stripped of accidental whitespace)
        raw_groq_key = os.getenv("GROQ_API_KEY")
        self.groq_api_key = raw_groq_key.strip() if raw_groq_key else None

        raw_openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_API_KEY")
        self.openai_api_key = raw_openai_key.strip() if raw_openai_key else None

        raw_anthropic_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
        self.anthropic_api_key = raw_anthropic_key.strip() if raw_anthropic_key else None
        self.anthropic_base_url = os.getenv("ANTHROPIC_BASE_URL")
        self.groq_base_url = os.getenv("GROQ_BASE_URL")


class LLMAdapter:
    """Provider-independent LLM adapter supporting Groq SDK, OpenAI, Anthropic, and deterministic mock."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.tracker = UsageTracker.get_instance()
        self._groq_client = None

    def _get_groq_client(self):
        if self._groq_client is None:
            from groq import Groq
            client_kwargs = {
                "api_key": self.config.groq_api_key,
                "timeout": self.config.timeout,
            }
            if self.config.groq_base_url:
                client_kwargs["base_url"] = self.config.groq_base_url

            self._groq_client = Groq(**client_kwargs)
        return self._groq_client

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        fallback_data: Optional[Dict[str, Any]] = None,
        call_type: str = "general",
        question_id: Optional[str] = None,
        report_id: Optional[str] = None,
    ) -> T:
        """Generates structured output validated against a Pydantic model schema.
        
        Supports mock mode, live APIs with exponential backoff retries, and schema validation.
        """
        if self.config.provider == "mock" or not self._has_valid_credentials():
            if fallback_data is not None:
                return response_model.model_validate(fallback_data)
            raise ValueError(f"Provider '{self.config.provider}' requested in mock mode without fallback data.")

        # Live API dispatch
        if self.config.provider == "groq":
            return self._call_groq_sdk(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=response_model,
                call_type=call_type,
                question_id=question_id,
                report_id=report_id,
            )
        elif self.config.provider == "openai":
            raw_json_str = self._call_openai(system_prompt, user_prompt, response_model)
            return response_model.model_validate_json(raw_json_str)
        elif self.config.provider == "anthropic":
            raw_json_str = self._call_anthropic(system_prompt, user_prompt, response_model)
            return response_model.model_validate_json(raw_json_str)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.provider}")

    def _has_valid_credentials(self) -> bool:
        if self.config.provider == "groq":
            return bool(self.config.groq_api_key)
        elif self.config.provider == "openai":
            return bool(self.config.openai_api_key)
        elif self.config.provider == "anthropic":
            return bool(self.config.anthropic_api_key)
        return False

    def _call_groq_sdk(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        call_type: str,
        question_id: Optional[str],
        report_id: Optional[str],
    ) -> T:
        """Calls Groq API via official Groq SDK with retry-after handling, JSON schema, and usage tracking."""
        from groq import APIConnectionError, APIError, InternalServerError, RateLimitError

        client = self._get_groq_client()
        schema = response_model.model_json_schema()
        schema_name = response_model.__name__

        current_model = self.config.model
        last_error = None

        for attempt in range(1, self.config.max_retries + 1):
            t0 = time.time()
            structured_mode = "json_schema" if self.config.structured_output else "json_object"

            try:
                # Prepare call arguments
                kwargs: Dict[str, Any] = {
                    "model": current_model,
                    "temperature": self.config.temperature,
                }

                # High reasoning effort for supported models (e.g. gpt-oss-120b)
                if "oss" in current_model and self.config.reasoning_effort:
                    kwargs["reasoning_effort"] = self.config.reasoning_effort

                # Try strict JSON schema if enabled
                if structured_mode == "json_schema":
                    kwargs["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": schema_name,
                            "schema": schema,
                        },
                    }
                    kwargs["messages"] = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                else:
                    # json_object fallback mode
                    prompt_with_schema = f"{user_prompt}\n\nYou MUST respond with valid JSON matching this schema:\n{json.dumps(schema)}"
                    kwargs["response_format"] = {"type": "json_object"}
                    kwargs["messages"] = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt_with_schema},
                    ]

                # Non-streaming chat completion
                completion = client.chat.completions.create(**kwargs)
                latency_ms = (time.time() - t0) * 1000.0

                raw_content = completion.choices[0].message.content or "{}"
                usage = completion.usage

                prompt_tokens = usage.prompt_tokens if usage else 0
                completion_tokens = usage.completion_tokens if usage else 0
                total_tokens = usage.total_tokens if usage else 0
                reasoning_tokens = 0
                if usage and hasattr(usage, "completion_tokens_details") and usage.completion_tokens_details:
                    reasoning_tokens = getattr(usage.completion_tokens_details, "reasoning_tokens", 0) or 0

                # Record usage telemetry
                self.tracker.record(
                    call_type=call_type,
                    model=current_model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    reasoning_tokens=reasoning_tokens,
                    latency_ms=latency_ms,
                    question_id=question_id,
                    report_id=report_id,
                    request_id=completion.id,
                    structured_output_mode=structured_mode,
                    status_code=200,
                    status="success",
                )

                # Validate against target Pydantic schema
                return response_model.model_validate_json(raw_content)

            except RateLimitError as rle:
                last_error = rle
                latency_ms = (time.time() - t0) * 1000.0
                # Extract wait time from header or error string
                retry_after = 2.0 * attempt
                if hasattr(rle, "response") and rle.response is not None:
                    hdr_val = rle.response.headers.get("retry-after")
                    if hdr_val:
                        try:
                            retry_after = float(hdr_val) + 0.5
                        except Exception:
                            pass
                m = re.search(r"try again in ([0-9.]+)s", str(rle))
                if m:
                    retry_after = float(m.group(1)) + 0.5

                wait_sec = max(retry_after, 2.0)
                logger.warning(
                    f"Groq RateLimitError on attempt {attempt}/{self.config.max_retries}. Backing off for {wait_sec:.2f}s..."
                )
                self.tracker.record(
                    call_type=call_type,
                    model=current_model,
                    latency_ms=latency_ms,
                    question_id=question_id,
                    report_id=report_id,
                    structured_output_mode=structured_mode,
                    status_code=429,
                    status="rate_limited",
                    error=str(rle),
                )
                if attempt < self.config.max_retries:
                    time.sleep(wait_sec)

            except Exception as e:
                last_error = e
                latency_ms = (time.time() - t0) * 1000.0
                err_str = str(e)
                logger.warning(f"Groq invocation attempt {attempt}/{self.config.max_retries} failed: {e}")

                # If json_schema mode was rejected by the endpoint, fallback immediately to json_object mode
                if "json_schema" in err_str and self.config.structured_output:
                    logger.info("json_schema format not accepted; falling back to json_object mode with local validation.")
                    self.config.structured_output = False
                    continue

                # If primary model is unavailable or decommissioned, explicitly switch to fallback model
                if current_model != self.config.fallback_model and (
                    "model_not_found" in err_str or "decommissioned" in err_str or "does not exist" in err_str
                ):
                    logger.warning(
                        f"Primary model '{current_model}' unavailable. Explicitly falling back to '{self.config.fallback_model}'."
                    )
                    current_model = self.config.fallback_model
                    continue

                self.tracker.record(
                    call_type=call_type,
                    model=current_model,
                    latency_ms=latency_ms,
                    question_id=question_id,
                    report_id=report_id,
                    structured_output_mode=structured_mode,
                    status_code=500,
                    status="error",
                    error=err_str,
                )

                if attempt < self.config.max_retries:
                    time.sleep(2 ** attempt)

        # Fail closed: Do NOT invent results or substitute mock data in live mode!
        raise RuntimeError(
            f"Groq LLM invocation failed after {self.config.max_retries} retries on model '{current_model}': {last_error}"
        )

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
            json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content)
            return json_match.group(1) if json_match else content
