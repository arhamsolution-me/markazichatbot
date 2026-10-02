import time
import json
import asyncio
import logging
from typing import Any, Optional
import httpx
from app.config import settings

logger = logging.getLogger("markazi.llm")

class GroqKeyRotator:
    def __init__(self):
        self.keys = settings.groq_keys
        if not self.keys:
            logger.warning("No Groq API keys found in configuration!")
        self.current_index = 0
        self.key_cooldowns: dict[str, float] = {}
        self.lock = asyncio.Lock()

    async def get_active_key(self) -> str:
        async with self.lock:
            if not self.keys:
                raise ValueError("No Groq API keys configured.")

            now = time.time()
            total = len(self.keys)
            
            for i in range(total):
                idx = (self.current_index + i) % total
                candidate = self.keys[idx]
                cooldown_until = self.key_cooldowns.get(candidate, 0)
                if now >= cooldown_until:
                    self.current_index = (idx + 1) % total
                    return candidate
            
            best_key = min(self.keys, key=lambda k: self.key_cooldowns.get(k, 0))
            self.current_index = (self.keys.index(best_key) + 1) % total
            return best_key

    DEFAULT_TIMEOUT: float = 30.0
    STREAM_TIMEOUT: float = 40.0

    def mark_key_rate_limited(self, key: str, cooldown_seconds: float = 60.0):
        self.key_cooldowns[key] = time.time() + cooldown_seconds
        logger.warning(f"Key ...{key[-8:]} rate-limited. Placed in cooldown for {cooldown_seconds}s.")

    async def _handle_response_error(self, resp: httpx.Response, key: str, model_name: str) -> tuple[str, bool]:
        """Handles non-200 Groq responses and returns (new_model_name, should_retry)."""
        status = resp.status_code
        if status == 401:
            logger.warning(f"Groq 401 Invalid Key on ...{key[-8:]}. Disabling key permanently.")
            self.mark_key_rate_limited(key, 9999999.0)
            return model_name, True

        if status == 429:
            logger.warning(f"Groq 429 Rate Limit on key ...{key[-8:]}. Retrying with next key...")
            self.mark_key_rate_limited(key, 60.0)
            return model_name, True

        if status == 413:
            logger.warning(f"Groq 413 Payload Too Large on {model_name}. Switching to fallback {settings.GROQ_FALLBACK_MODEL}...")
            self.mark_key_rate_limited(key, 60.0)
            return settings.GROQ_FALLBACK_MODEL, True

        if status == 404:
            if model_name != settings.GROQ_FALLBACK_MODEL:
                logger.warning(f"Model {model_name} returned 404. Falling back to {settings.GROQ_FALLBACK_MODEL}...")
                return settings.GROQ_FALLBACK_MODEL, True
            raise RuntimeError(f"Groq API Error 404: {resp.text}")

        logger.error(f"Groq API Error {status}: {resp.text}")
        if status >= 500:
            await asyncio.sleep(0.5)
            return model_name, True
        raise RuntimeError(f"Groq API returned error {status}: {resp.text}")

    async def generate_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> str:
        model_name = model or settings.GROQ_MODEL
        tokens_limit = max_tokens or settings.MAX_TOKENS
        attempts = 0
        max_attempts = max(3, len(self.keys))

        while attempts < max_attempts:
            key = await self.get_active_key()
            attempts += 1
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": tokens_limit
            }

            try:
                async with asyncio.timeout(self.DEFAULT_TIMEOUT):
                    async with httpx.AsyncClient() as client:
                        resp = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers=headers,
                            json=payload
                        )

                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]

                model_name, should_retry = await self._handle_response_error(resp, key, model_name)
                if should_retry:
                    continue

            except (httpx.TimeoutException, TimeoutError):
                logger.warning(f"Groq request timed out on key ...{key[-8:]}. Retrying...")
                continue
            except Exception as e:
                logger.error(f"Exception during Groq request: {e}")
                if attempts >= max_attempts:
                    raise

        raise RuntimeError("Exceeded maximum Groq API key rotation attempts.")

    async def _handle_stream_error(self, response: httpx.Response, key: str, model_name: str) -> tuple[str, bool]:
        status = response.status_code
        if status == 401:
            logger.warning(f"Groq 401 on stream with key ...{key[-8:]}. Disabling key.")
            self.mark_key_rate_limited(key, 9999999.0)
            return model_name, True

        if status in (400, 413, 429):
            logger.warning(f"Groq stream error {status} on {model_name}. Switching to fallback {settings.GROQ_FALLBACK_MODEL}...")
            self.mark_key_rate_limited(key, 60.0)
            return settings.GROQ_FALLBACK_MODEL, True

        err_body = await response.aread()
        logger.error(f"Groq stream HTTP {status}: {err_body.decode()}")
        if status >= 500:
            await asyncio.sleep(0.5)
            return model_name, True
        raise RuntimeError(f"Groq stream error {status}: {err_body.decode()}")

    async def _yield_stream_tokens(self, response: httpx.Response):
        async for line in response.aiter_lines():
            if not line.startswith("data: "):
                continue
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                delta = chunk["choices"][0]["delta"].get("content", "")
                if delta:
                    yield delta
            except Exception:
                pass

    async def stream_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ):
        model_name = model or settings.GROQ_MODEL
        tokens_limit = max_tokens or settings.MAX_TOKENS
        max_attempts = len(self.keys) * 2
        attempts = 0

        while attempts < max_attempts:
            attempts += 1
            key = await self.get_active_key()
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": tokens_limit,
                "stream": True
            }
            try:
                async with asyncio.timeout(self.STREAM_TIMEOUT):
                    async with httpx.AsyncClient() as client:
                        async with client.stream("POST", "https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload) as response:
                            if response.status_code == 200:
                                async for token in self._yield_stream_tokens(response):
                                    yield token
                                return

                            model_name, should_retry = await self._handle_stream_error(response, key, model_name)
                            if should_retry:
                                continue

            except (httpx.TimeoutException, TimeoutError):
                logger.warning(f"Groq stream request timed out on key ...{key[-8:]}. Retrying...")
                continue
            except Exception:
                if attempts >= max_attempts:
                    raise
                await asyncio.sleep(0.5)
                continue

        raise RuntimeError("Exceeded maximum Groq streaming retry attempts.")

llm_client = GroqKeyRotator()
