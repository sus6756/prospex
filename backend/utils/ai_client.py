import json
import re
from typing import Any, Optional

from config import settings


def _provider_config() -> Optional[dict]:
    """Resolve which LLM provider is configured.

    Priority order:
      1. Anthropic (native SDK)
      2. Gemini (native SDK, free tier; structured output supported)
      3. OpenAI (optionally routed through an OpenAI-compatible base_url,
         e.g. Ollama, Groq, OpenRouter, vLLM, Together)
    """
    if settings.ANTHROPIC_API_KEY:
        return {
            "provider": "anthropic",
            "api_key": settings.ANTHROPIC_API_KEY,
            "base_url": None,
            "model": settings.ANTHROPIC_MODEL,
        }
    if settings.GEMINI_API_KEY:
        return {
            "provider": "gemini",
            "api_key": settings.GEMINI_API_KEY,
            "base_url": None,
            "model": settings.GEMINI_MODEL,
        }
    if settings.OPENAI_API_KEY or settings.OPENAI_BASE_URL:
        return {
            "provider": "openai" if not settings.OPENAI_BASE_URL else "openai_compatible",
            "api_key": settings.OPENAI_API_KEY or "none",
            "base_url": settings.OPENAI_BASE_URL or None,
            "model": settings.OPENAI_MODEL,
        }
    return None


def ai_available() -> bool:
    return _provider_config() is not None


def get_ai_client():
    """Backward-compatible accessor. Returns an OpenAI client when the
    provider is OpenAI-compatible, else a lightweight adapter."""
    cfg = _provider_config()
    if not cfg:
        return None
    if cfg["provider"] in ("openai", "openai_compatible"):
        try:
            from openai import OpenAI

            return OpenAI(
                api_key=cfg["api_key"] or "none",
                base_url=cfg["base_url"],
            )
        except ImportError:
            return None
    return None


def chat_json(
    system_prompt: str,
    user_prompt: str,
    json_schema: dict,
    temperature: float = 0.2,
    max_tokens: int = 1500,
) -> dict:
    cfg = _provider_config()
    if not cfg:
        raise RuntimeError("No AI provider configured (set OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_BASE_URL)")

    if cfg["provider"] == "anthropic":
        return _chat_json_anthropic(system_prompt, user_prompt, temperature, max_tokens, cfg)
    if cfg["provider"] == "gemini":
        return _chat_json_gemini(system_prompt, user_prompt, json_schema, temperature, max_tokens, cfg)
    return _chat_json_openai_compat(system_prompt, user_prompt, json_schema, temperature, max_tokens, cfg)


def chat_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 800,
) -> str:
    cfg = _provider_config()
    if not cfg:
        raise RuntimeError("No AI provider configured")

    if cfg["provider"] == "anthropic":
        return _chat_text_anthropic(system_prompt, user_prompt, temperature, max_tokens, cfg)
    if cfg["provider"] == "gemini":
        return _chat_text_gemini(system_prompt, user_prompt, temperature, max_tokens, cfg)
    return _chat_text_openai_compat(system_prompt, user_prompt, temperature, max_tokens, cfg)


def _chat_json_gemini(system_prompt, user_prompt, json_schema, temperature, max_tokens, cfg) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=cfg["api_key"])
    genai_config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json",
        temperature=temperature,
        max_output_tokens=max_tokens,
    )
    if json_schema:
        genai_config.response_schema = _google_schema(json_schema)
    resp = client.models.generate_content(
        model=cfg["model"],
        contents=user_prompt,
        config=genai_config,
    )
    return json.loads(_extract_json(resp.text or "{}"))


def _chat_text_gemini(system_prompt, user_prompt, temperature, max_tokens, cfg) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=cfg["api_key"])
    resp = client.models.generate_content(
        model=cfg["model"],
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    return resp.text or ""


def _google_schema(schema: dict) -> dict:
    """Convert an OpenAI-style JSON schema into one accepted by Google's
    structured-output API (single-type + nullable, no additionalProperties)."""
    def convert(node):
        if not isinstance(node, dict):
            return node
        converted = {}
        for key, value in node.items():
            if key == "additionalProperties":
                continue
            if key == "type" and isinstance(value, list):
                has_null = "null" in value
                primary = [t for t in value if t != "null"]
                converted["type"] = primary[0] if primary else "string"
                if has_null:
                    converted["nullable"] = True
            elif key == "properties":
                converted["properties"] = {
                    k: convert(v) for k, v in value.items()
                }
            elif key in ("items", "prefixItems"):
                converted[key] = convert(value)
            else:
                converted[key] = value
        return converted

    return convert(schema)


def _chat_json_openai_compat(system_prompt, user_prompt, json_schema, temperature, max_tokens, cfg) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=cfg["api_key"] or "none", base_url=cfg["base_url"])
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    def attempt(strict: bool):
        kwargs = dict(
            model=cfg["model"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if strict and json_schema:
            kwargs["response_format"] = {
                "type": "json_object",
                "json_schema": {"name": "response", "schema": json_schema, "strict": True},
            }
        else:
            kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content or "{}"
        return json.loads(_extract_json(content))

    try:
        if json_schema and cfg["provider"] == "openai":
            return attempt(True)
        return attempt(False)
    except Exception:
        # Strict JSON-schema mode is not supported by every compatible
        # endpoint (Ollama, some Gemini models). Retry without it.
        if cfg["provider"] != "openai" and json_schema:
            try:
                return attempt(False)
            except Exception:
                pass
        raise


def _chat_text_openai_compat(system_prompt, user_prompt, temperature, max_tokens, cfg) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=cfg["api_key"] or "none", base_url=cfg["base_url"])
    resp = client.chat.completions.create(
        model=cfg["model"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""


def _chat_json_anthropic(system_prompt, user_prompt, temperature, max_tokens, cfg) -> dict:
    from anthropic import Anthropic

    client = Anthropic(api_key=cfg["api_key"])
    resp = client.messages.create(
        model=cfg["model"],
        max_tokens=max_tokens,
        temperature=temperature,
        system=f"{system_prompt}\n\nYou must respond with a single valid JSON object and nothing else.",
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    return json.loads(_extract_json(text))


def _chat_text_anthropic(system_prompt, user_prompt, temperature, max_tokens, cfg) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=cfg["api_key"])
    resp = client.messages.create(
        model=cfg["model"],
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def _extract_json(text: str) -> str:
    """Pull the outermost JSON object out of a loose model response."""
    text = (text or "").strip()
    try:
        json.loads(text)
        return text
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text