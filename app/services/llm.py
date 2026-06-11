import asyncio
import json
import logging
import re
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def _clean_json_response(text: str) -> str:
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text.strip()


def _extract_json_block(text: str) -> str:
    """Find the outermost {...} or [...] block."""
    for pattern in (r"\{[\s\S]+\}", r"\[[\s\S]+\]"):
        m = re.search(pattern, text)
        if m:
            return m.group(0)
    return text


def _aggressive_clean(text: str) -> str:
    """Fix Chinese curly quotes and unescaped control chars inside string values."""
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")

    def escape_inner(m):
        s = m.group(0)
        inner = s[1:-1]
        inner = inner.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return '"' + inner + '"'

    text = re.sub(r'"(?:[^"\\]|\\.)*"', escape_inner, text)
    return text


def parse_json_response(text: str) -> Any:
    cleaned = _clean_json_response(text)

    for attempt in [
        lambda t: json.loads(t),
        lambda t: json.loads(_extract_json_block(t)),
        lambda t: json.loads(_aggressive_clean(t)),
        lambda t: json.loads(_aggressive_clean(_extract_json_block(t))),
    ]:
        try:
            return attempt(cleaned)
        except (json.JSONDecodeError, Exception):
            continue

    logger.error(f"JSON parse failed. Raw text (first 600 chars):\n{text[:600]}")
    raise ValueError(f"无法解析 LLM 返回的 JSON，原始内容: {text[:200]}")


class LLMClient:
    def __init__(self):
        self.provider = settings.llm_provider.lower()
        if self.provider == "anthropic":
            self.model = settings.anthropic_model
            self.api_key = settings.anthropic_api_key
        else:
            self.model = settings.deepseek_model
            self.api_key = settings.deepseek_api_key

    async def chat(self, system: str, user: str, max_tokens: int = 4096) -> str:
        if self.provider == "anthropic":
            return await self._call_anthropic(system, user, max_tokens)
        return await self._call_deepseek(system, user, max_tokens)

    async def _post(self, url: str, headers: dict, payload: dict) -> dict:
        """POST with retry on 5xx errors (3 attempts, exponential backoff)."""
        last_err = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code in (502, 503, 504) and attempt < 2:
                        wait = 2 ** attempt  # 1s, 2s
                        logger.warning(f"HTTP {resp.status_code} from proxy, retry {attempt+1}/3 in {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    return resp.json()
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_err = e
                if attempt < 2:
                    wait = 2 ** attempt
                    logger.warning(f"Request error: {e}, retry {attempt+1}/3 in {wait}s")
                    await asyncio.sleep(wait)
        raise last_err or Exception("请求失败")

    async def _call_anthropic(self, system: str, user: str, max_tokens: int) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        base = settings.anthropic_base_url.rstrip("/")
        data = await self._post(f"{base}/v1/chat/completions", headers, payload)
        return data["choices"][0]["message"]["content"]

    async def _call_deepseek(self, system: str, user: str, max_tokens: int) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        base_url = settings.deepseek_base_url.rstrip("/")
        data = await self._post(f"{base_url}/chat/completions", headers, payload)
        return data["choices"][0]["message"]["content"]

    async def test_connection(self) -> tuple[bool, str, str]:
        try:
            if self.provider == "anthropic":
                headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                payload = {"model": self.model, "max_tokens": 50,
                           "messages": [{"role": "system", "content": "你是助手。"},
                                        {"role": "user", "content": "用一句话介绍你自己。"}]}
                base = settings.anthropic_base_url.rstrip("/")
                data = await self._post(f"{base}/v1/chat/completions", headers, payload)
                actual_model = data.get("model", self.model)
                text = data["choices"][0]["message"]["content"]
                return True, text, actual_model
            else:
                result = await self.chat("你是助手。", "用一句话介绍你自己。", max_tokens=50)
                return True, result, self.model
        except Exception as e:
            return False, str(e), self.model
