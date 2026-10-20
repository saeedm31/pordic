# 🇵🇹 pordic

**A translator and dictionary for European Portuguese, as spoken in Portugal, not Brazil.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Web-Flask-000000?logo=flask)](https://flask.palletsprojects.com/)
[![LLM](https://img.shields.io/badge/LLM-OpenAI%20%7C%20Ollama-412991)](#-choose-a-model)
[![Tests](https://github.com/saeedm31/pordic/actions/workflows/tests.yml/badge.svg)](https://github.com/saeedm31/pordic/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 💡 Why it exists

Most translators default to **Brazilian Portuguese**. If you live in Portugal, that gets you looks: you ask for the *trem* when it's the *comboio*, wait for the *ônibus* instead of the *autocarro*, and say *estou fazendo* instead of *estou a fazer*.

pordic always answers in European Portuguese and **shows you where Brazil would say it differently**, so you learn the difference instead of guessing.

## ✨ Features

**Translate**
- Any language → European Portuguese, or Portuguese → English, detected automatically
- Choose the tone: keep the original, informal (*tu*) or formal (*você / o senhor*)
- A "🇧🇷 In Brazil you would say" box listing words that differ, e.g. *comboio* / *trem*
- Short usage notes, copy button, Ctrl+Enter to translate

**Dictionary**
- Look up a Portuguese or English word and get the European Portuguese entry:
  - the headword with its article (*o comboio*)
  - part of speech, gender and plural
  - a pronunciation hint, as spoken in Lisbon
  - two example sentences
  - the present tense for verbs
  - the Brazilian equivalent

**Built to be deployed**
- Works with any OpenAI-compatible API: OpenAI, or **Ollama for free, fully local** use
- Rate limiting per visitor, so a public deployment can't run up your API bill
- Clear error messages, light and dark mode, mobile friendly

## 🧠 How it works

```
Browser ──► Flask API ──► prompt with pt-PT rules ──► LLM (JSON mode) ──► validate & clean ──► page
           /api/translate                               OpenAI / Ollama      translator.py
           /api/lookup
```

- **Prompts** (`translator.py`) set strict European Portuguese rules with examples (*comboio, autocarro, telemóvel, pequeno-almoço, estar a + infinitive*) and ask for a fixed JSON structure.
- **Validation:** every reply is checked and cleaned before it reaches the page, so a sloppy model answer can't break the interface.
- **Safety:**
  - The user's text is sent only as content to translate, and the model is told never to follow instructions inside it.
  - The page inserts all model output as plain text, never as HTML.
- **No SDK lock-in:** `llm.py` talks to the chat API over plain HTTP (about 50 lines), so there's no SDK version to break and you can switch provider by changing one setting.

## 🚀 Run it

```bash
git clone https://github.com/saeedm31/pordic.git
cd pordic
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # add your API key, or point it at Ollama
python app.py             # http://127.0.0.1:5004
```

### 🔌 Choose a model

| Provider | Settings in `.env` |
|---|---|
| **OpenAI** | `OPENAI_API_KEY=sk-...` and `OPENAI_MODEL=` any chat model on your account |
| **Ollama** (free, local) | `OPENAI_BASE_URL=http://localhost:11434/v1`, `OPENAI_MODEL=llama3.2`, no key needed |
| Others (OpenRouter, Groq, …) | Their OpenAI-compatible base URL, key and model name |

Larger models give noticeably better European Portuguese. Small local models sometimes slip into Brazilian forms.

### 🌍 Deploy

- **Docker:** `docker build -t pordic . && docker run -p 8000:8000 --env-file .env pordic`
- **Heroku / Render / Railway:** the `Procfile` runs `gunicorn app:app`. Set the variables from `.env.example` in the dashboard and `TRUST_PROXY=1`.

Keys are only read from environment variables. Never commit `.env`; it's in `.gitignore`.

## ✅ Tests

```bash
python -m unittest
```

20 tests, run offline against a fake model on every push (GitHub Actions):
- the prompts and pt-PT rules
- cleaning of messy model replies
- the HTTP client's error handling
- the rate limiter
- every API endpoint, including errors (400, 429, 502, 503)

## 🗺️ Ideas

- Pronunciation audio with a European Portuguese text-to-speech voice
- Save words to a personal vocabulary list
- Common false friends between Portugal and Brazil (*rapariga*, *propina*, *fato*…)

---

Built in Porto by [Saeed Hojjatpanah](https://github.com/saeedm31).
