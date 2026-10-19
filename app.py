"""pordic: a European Portuguese translator and dictionary (Flask app)."""

import logging
import os
import threading
import time
from collections import defaultdict, deque

from flask import Flask, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

import llm
import translator

app = Flask(__name__)
app.json.sort_keys = False  # keep conjugations in eu, tu, ele... order
log = logging.getLogger(__name__)

# Behind nginx, Heroku or another proxy, set TRUST_PROXY=1 so rate limits use the real client IP.
if os.environ.get("TRUST_PROXY") == "1":
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)


class RateLimiter:
    """Allow at most `limit` requests per `window` seconds per client. Keeps API costs in check."""

    def __init__(self, limit, window=60.0):
        self.limit, self.window = limit, window
        self.hits = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key, now=None):
        now = time.monotonic() if now is None else now
        with self.lock:
            q = self.hits[key]
            while q and now - q[0] >= self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True


limiter = RateLimiter(int(os.environ.get("RATE_LIMIT_PER_MINUTE", 20)))


def handle(action):
    """Shared request handling: config check, rate limit, input and model errors."""
    if not llm.is_configured():
        return jsonify(error="The translator isn't set up yet: OPENAI_API_KEY is missing."), 503
    if not limiter.allow(request.remote_addr or "unknown"):
        return jsonify(error="Too many requests. Please wait a minute and try again."), 429
    body = request.get_json(silent=True) or {}
    try:
        return jsonify(action(body))
    except translator.InputError as e:
        return jsonify(error=str(e)), 400
    except llm.LLMError as e:
        log.warning("Model error: %s", e)
        return jsonify(error="The translation service had a problem. Please try again."), 502


@app.post("/api/translate")
def api_translate():
    return handle(lambda b: translator.translate(b.get("text"), b.get("direction", "auto"),
                                                 b.get("register", "neutral")))


@app.post("/api/lookup")
def api_lookup():
    return handle(lambda b: translator.lookup(b.get("word")))


@app.get("/health")
def health():
    return jsonify(ok=True, configured=llm.is_configured(), model=llm.MODEL)


@app.get("/")
def index():
    return render_template("index.html", max_text=translator.MAX_TEXT, max_word=translator.MAX_WORD)


if __name__ == "__main__":
    # Local development only. In production: gunicorn app:app (see Procfile / Dockerfile).
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 5004)))
