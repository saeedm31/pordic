"""Minimal client for any OpenAI-compatible chat API (OpenAI, Ollama, OpenRouter, ...).

Uses plain HTTP so there is no SDK version to break, and the same code works
with a hosted model or a free local one.
"""

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
# Some models only accept their default temperature, so it is only sent when set.
TEMPERATURE = os.environ.get("OPENAI_TEMPERATURE")
TIMEOUT = 60


class LLMError(Exception):
    """The model could not be reached or did not return usable JSON."""


def is_configured():
    """A key is needed for hosted APIs; local servers such as Ollama work without one."""
    return bool(API_KEY) or "api.openai.com" not in BASE_URL


def chat_json(system, user):
    """Send one system + user message and return the reply parsed as a JSON object."""
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_object"},
    }
    if TEMPERATURE:
        payload["temperature"] = float(TEMPERATURE)
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}

    try:
        r = requests.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise LLMError(f"Could not reach the model provider: {e.__class__.__name__}") from e
    if r.status_code != 200:
        raise LLMError(f"Model provider returned HTTP {r.status_code}")

    try:
        content = r.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
    except (ValueError, KeyError, IndexError, TypeError) as e:
        raise LLMError("The model did not return valid JSON") from e
    if not isinstance(data, dict):
        raise LLMError("The model did not return a JSON object")
    return data
