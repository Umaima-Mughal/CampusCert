"""Tiny Groq client (OpenAI-compatible chat completions, JSON mode). Uses httpx, already in requirements."""
import json
import re
import time
from typing import Callable, Optional

import httpx

from .config import AISettings, get_ai_settings


class GroqError(Exception):
    """`status` is the HTTP status we want to show the examiner (503 = not set up, 429 = busy, 502 = bad answer)."""

    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.message = message
        self.status = status


def _loads_lenient(text: str) -> dict:
    """JSON mode normally returns clean JSON; this also survives ```json fences or text around it."""
    text = (text or "").strip()
    try:
        return json.loads(text)
    except ValueError:
        pass
    fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        return json.loads(fenced)
    except ValueError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start:end + 1])
    raise ValueError("no JSON object found")


def _call_model(client: httpx.Client, cfg: AISettings, model: str, messages: list,
                max_tokens: int, temperature: float, sleep: Callable[[float], None]) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"}
    last = GroqError("The AI service did not answer.", 502)
    for attempt in range(3):
        try:
            res = client.post(cfg.api_url, json=payload, headers=headers)
        except httpx.TimeoutException:
            last = GroqError("The AI service took too long to answer. Try again.", 504)
            continue
        except httpx.HTTPError:
            last = GroqError("Could not reach the AI service. Check the internet connection.", 502)
            sleep(1.5)
            continue

        if res.status_code == 200:
            try:
                content = res.json()["choices"][0]["message"]["content"]
                return _loads_lenient(content)
            except (ValueError, KeyError, IndexError, TypeError):
                last = GroqError("The AI returned an answer that could not be read. Try again.", 502)
                continue
        if res.status_code in (401, 403):
            raise GroqError("The AI service rejected the API key. Check GROQ_API_KEY in your .env file.", 503)
        if res.status_code == 429:
            try:
                wait = float(res.headers.get("retry-after", ""))
            except ValueError:
                wait = 2.0 * (attempt + 1)
            last = GroqError("The free AI limit was reached. Wait a minute and try again.", 429)
            if attempt < 2:
                sleep(min(wait, 20.0))
            continue
        if res.status_code >= 500:
            last = GroqError("The AI service is having problems. Try again shortly.", 502)
            sleep(1.5)
            continue
        # 400 / 404 etc: bad request or a model that no longer exists. Let the caller try the fallback model.
        detail = ""
        try:
            detail = res.json().get("error", {}).get("message", "")
        except ValueError:
            pass
        raise GroqError(f"The AI service refused the request ({res.status_code}). {detail}".strip(), 502)
    raise last


def chat_json(messages: list, cfg: Optional[AISettings] = None, *, max_tokens: int = 3000,
              temperature: float = 0.4, transport: Optional[httpx.BaseTransport] = None,
              sleep: Callable[[float], None] = time.sleep) -> dict:
    """Send `messages` to Groq and return the reply parsed as a JSON object."""
    cfg = cfg or get_ai_settings()
    if not cfg.api_key:
        raise GroqError("AI paper generation is not set up yet. Add GROQ_API_KEY to the .env file "
                        "(free key: console.groq.com/keys) and restart the backend.", 503)
    models = [cfg.GROQ_MODEL]
    if cfg.GROQ_FALLBACK_MODEL and cfg.GROQ_FALLBACK_MODEL != cfg.GROQ_MODEL:
        models.append(cfg.GROQ_FALLBACK_MODEL)
    last: Optional[GroqError] = None
    with httpx.Client(timeout=httpx.Timeout(cfg.AI_TIMEOUT_SECONDS), transport=transport) as client:
        for model in models:
            try:
                return _call_model(client, cfg, model, messages, max_tokens, temperature, sleep)
            except GroqError as e:
                if e.status == 503:      # missing / rejected key: another model will not help
                    raise
                last = e
    raise last or GroqError("The AI service did not answer.", 502)
