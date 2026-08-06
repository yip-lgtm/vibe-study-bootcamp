"""
Unified LLM Client for Multi-Agent Pipeline

Supports multiple providers via a single `complete()` function:
  - MiniMax (default, via Anthropic-compatible API)
  - Anthropic Claude
  - OpenAI / Azure OpenAI
  - Ollama (local)
  - Any OpenAI-compatible API

Auto-detects provider from environment:
  MINIMAX_API_KEY       -> MiniMax (default)
  ANTHROPIC_API_KEY     -> Anthropic Claude
  OPENAI_API_KEY        -> OpenAI
  OLLAMA_HOST           -> local Ollama

Usage:
    from _pipeline.llm_client import complete, get_default_model
    resp = complete(
        messages=[{"role": "user", "content": "Hello"}],
        system="You are a researcher.",
        model=get_default_model(),
        max_tokens=1024,
    )
    print(resp.text)
    print(f"tokens: {resp.input_tokens} in / {resp.output_tokens} out")
"""
from __future__ import annotations
import os
import json
import time
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Iterator, Tuple

import httpx


log = logging.getLogger(__name__)


# Module-level tracking of all LLM calls (for token usage reporting)
_all_responses: List["LLMResponse"] = []


def get_usage_report() -> Dict[str, Any]:
    """Get summary of all LLM calls made in this session."""
    total_in = sum(r.input_tokens for r in _all_responses)
    total_out = sum(r.output_tokens for r in _all_responses)
    total_latency = sum(r.latency_ms for r in _all_responses)
    return {
        "calls": len(_all_responses),
        "input_tokens": total_in,
        "output_tokens": total_out,
        "total_tokens": total_in + total_out,
        "latency_ms": total_latency,
        "by_model": {
            model: {
                "calls": sum(1 for r in _all_responses if r.model == model),
                "input_tokens": sum(r.input_tokens for r in _all_responses if r.model == model),
                "output_tokens": sum(r.output_tokens for r in _all_responses if r.model == model),
            }
            for model in set(r.model for r in _all_responses)
        }
    }


def reset_usage_tracking() -> None:
    """Reset the global LLM call tracker."""
    global _all_responses
    _all_responses = []


# ===== Provider configuration =====

@dataclass
class ProviderConfig:
    """LLM provider configuration."""
    name: str
    base_url: str
    api_key: Optional[str]
    default_model: str
    auth_style: str  # "bearer" or "x-api-key"


# MiniMax (OpenAI-compatible API)
# IMPORTANT: sk-cp- Subscription Keys (Token Plan) use api.minimax.io (OpenAI-format)
# api.minimaxi.com is for pay-as-you-go (Chinese region)
MINIMAX_TOKEN_PLAN_BASE = "https://api.minimax.io/v1"
MINIMAX_PAYG_BASE = "https://api.minimaxi.com/v1"
MINIMAX_MODEL = "MiniMax-M3"  # default model

# Heuristic: sk-cp- keys are Token Plan (use api.minimax.io)
# Other keys (e.g. sk-...) are pay-as-you-go (use api.minimaxi.com)
def _minimax_base_for_key(api_key: str) -> str:
    """Return the right MiniMax base URL based on key prefix."""
    if api_key and api_key.startswith("sk-cp-"):
        return MINIMAX_TOKEN_PLAN_BASE
    return MINIMAX_PAYG_BASE

# Anthropic
ANTHROPIC_BASE = "https://api.anthropic.com"
ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"

# OpenAI
OPENAI_BASE = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-4o-mini"

# Ollama
OLLAMA_BASE = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3.1"


def detect_provider() -> ProviderConfig:
    """Auto-detect provider from environment variables (priority: MiniMax > Anthropic > OpenAI > Ollama)."""
    if os.environ.get("MINIMAX_API_KEY"):
        key = os.environ.get("MINIMAX_API_KEY")
        return ProviderConfig(
            name="MiniMax",
            base_url=os.environ.get("MINIMAX_BASE_URL", _minimax_base_for_key(key)),
            api_key=key,
            default_model=os.environ.get("MINIMAX_MODEL", MINIMAX_MODEL),
            auth_style="bearer",  # OpenAI-format endpoint uses Bearer auth
        )
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ProviderConfig(
            name="Anthropic",
            base_url=os.environ.get("ANTHROPIC_BASE_URL", ANTHROPIC_BASE),
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            default_model=os.environ.get("ANTHROPIC_MODEL", ANTHROPIC_MODEL),
            auth_style="x-api-key",
        )
    if os.environ.get("OPENAI_API_KEY"):
        return ProviderConfig(
            name="OpenAI",
            base_url=os.environ.get("OPENAI_BASE_URL", OPENAI_BASE),
            api_key=os.environ.get("OPENAI_API_KEY"),
            default_model=os.environ.get("OPENAI_MODEL", OPENAI_MODEL),
            auth_style="bearer",
        )
    if os.environ.get("OLLAMA_HOST") or os.path.exists("/usr/local/bin/ollama"):
        return ProviderConfig(
            name="Ollama",
            base_url=os.environ.get("OLLAMA_HOST", OLLAMA_BASE),
            api_key="ollama",  # Ollama doesn't need a real key
            default_model=os.environ.get("OLLAMA_MODEL", OLLAMA_MODEL),
            auth_style="bearer",
        )
    # No provider — return MiniMax with no key (will fail at call time)
    return ProviderConfig(
        name="MiniMax",
        base_url=MINIMAX_PAYG_BASE,
        api_key=os.environ.get("MINIMAX_API_KEY"),
        default_model=MINIMAX_MODEL,
        auth_style="bearer",
    )


def get_default_model() -> str:
    """Get the default model for the detected provider."""
    return detect_provider().default_model


# ===== Response types =====

@dataclass
class LLMResponse:
    """Unified LLM response."""
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = ""
    raw: Dict[str, Any] = None  # full response for debugging
    latency_ms: int = 0


# ===== Core call =====

def complete(
    messages: List[Dict[str, str]],
    system: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    timeout: float = 120.0,
    provider: Optional[ProviderConfig] = None,
) -> LLMResponse:
    """
    Call LLM with messages, returning LLMResponse.

    Args:
        messages: list of {"role": "user"|"assistant", "content": "..."}
        system: optional system prompt
        model: model name (defaults to provider's default)
        max_tokens: max output tokens
        temperature: 0-1, lower = more deterministic
        timeout: seconds
        provider: override auto-detected provider

    Returns:
        LLMResponse with text, model, token usage, etc.
    """
    cfg = provider or detect_provider()
    model = model or cfg.default_model

    # Build request
    # MiniMax uses OpenAI-compatible /v1/chat/completions (works better in cloud envs)
    if cfg.name in ("MiniMax", "OpenAI"):
        url = f"{cfg.base_url.rstrip('/')}/chat/completions"
    elif cfg.name == "Anthropic":
        url = f"{cfg.base_url.rstrip('/')}/v1/messages"
    else:
        url = f"{cfg.base_url.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    if cfg.auth_style == "bearer":
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    elif cfg.auth_style == "x-api-key":
        headers["x-api-key"] = cfg.api_key

    # Body: Anthropic format
    if cfg.name == "Anthropic":
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system:
            body["system"] = system
    else:  # OpenAI format (MiniMax, OpenAI, Ollama)
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": msgs,
        }

    if not cfg.api_key:
        raise RuntimeError(
            f"No API key for provider {cfg.name}. "
            "Set MINIMAX_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY."
        )

    t0 = time.time()
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        log.error(f"LLM API error: {e.response.status_code} {e.response.text[:500]}")
        raise
    latency_ms = int((time.time() - t0) * 1000)

    # Parse response
    if cfg.name == "Anthropic":
        # Anthropic format: {"content": [{"type": "text", "text": "..."}]}
        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")
        usage = data.get("usage", {})
        resp = LLMResponse(
            text=text,
            model=data.get("model", model),
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            stop_reason=data.get("stop_reason", ""),
            raw=data,
            latency_ms=latency_ms,
        )
        _all_responses.append(resp)
        return resp
    else:
        # OpenAI format: {"choices": [{"message": {"content": "..."}}]}
        raw_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        # Strip MiniMax reasoning tags (MiniMax-M3 outputs <think>...</think> before final answer)
        import re
        text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
        usage = data.get("usage", {})
        # If all tokens went to thinking (empty text), use raw content minus thinking
        if not text and raw_text:
            # Extract only non-thinking parts
            parts = re.split(r'</think>', raw_text)
            text = parts[-1].strip() if len(parts) > 1 else raw_text.strip()
        resp = LLMResponse(
            text=text,
            model=data.get("model", model),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            stop_reason=data.get("choices", [{}])[0].get("finish_reason", ""),
            raw=data,
            latency_ms=latency_ms,
        )
        _all_responses.append(resp)
        return resp


# ===== Convenience: print usage summary =====

def print_usage_summary(responses: List[LLMResponse]) -> None:
    """Print aggregated token usage for a list of LLM responses."""
    total_in = sum(r.input_tokens for r in responses)
    total_out = sum(r.output_tokens for r in responses)
    total_latency = sum(r.latency_ms for r in responses)
    print(f"LLM usage: {len(responses)} calls, "
          f"{total_in:,} in + {total_out:,} out = {total_in + total_out:,} tokens, "
          f"latency {total_latency/1000:.1f}s")
