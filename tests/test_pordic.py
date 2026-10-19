"""Tests for pordic. Run with: python -m unittest

The model is replaced by a fake, so the tests run offline and cost nothing.
"""

import json
import os
import unittest
from unittest import mock

os.environ.setdefault("OPENAI_API_KEY", "test-key")

import app as webapp  # noqa: E402
import llm  # noqa: E402
import translator  # noqa: E402

TRANSLATION = {
    "detected_language": "English",
    "target_language": "European Portuguese",
    "translation": "Onde fica a estação de comboios?",
    "brazilian_differences": [{"pt_pt": "comboio", "pt_br": "trem", "note": "train"}, "junk", {"pt_pt": ""}],
    "notes": ["'Estação' is feminine.", "", "extra", "too many"],
}

ENTRY = {
    "headword": "o comboio", "english": "train", "part_of_speech": "Noun", "gender": "masculine",
    "plural": "os comboios", "pronunciation": "kom-BOY-oo",
    "examples": [{"pt": "O comboio está atrasado.", "en": "The train is late."}, {"en": "no pt"}],
    "brazilian": {"word": "o trem", "note": "Used in Brazil."},
    "present_tense": {"eu": "x"},  # not a verb: must be dropped
}


def fake_response(payload, status=200):
    resp = mock.Mock(status_code=status)
    resp.json.return_value = {"choices": [{"message": {"content": json.dumps(payload)}}]}
    return resp


class CleaningTests(unittest.TestCase):
    def test_translation_is_cleaned(self):
        r = translator.clean_translation(TRANSLATION)
        self.assertEqual(r["translation"], "Onde fica a estação de comboios?")
        self.assertEqual(r["brazilian_differences"], [{"pt_pt": "comboio", "pt_br": "trem", "note": "train"}])
        self.assertEqual(r["notes"], ["'Estação' is feminine."])  # max 2 kept, empties dropped

    def test_missing_translation_is_an_error(self):
        with self.assertRaises(llm.LLMError):
            translator.clean_translation({"translation": "  "})

    def test_entry_is_cleaned(self):
        e = translator.clean_entry(ENTRY)
        self.assertEqual(e["part_of_speech"], "noun")
        self.assertEqual(e["gender"], "masculine")
        self.assertEqual(len(e["examples"]), 1)
        self.assertIsNone(e["present_tense"])
        self.assertEqual(e["brazilian"]["word"], "o trem")

    def test_verb_keeps_conjugation(self):
        verb = dict(ENTRY, headword="apanhar", part_of_speech="verb", gender="none",
                    present_tense={"eu": "apanho", "tu": "apanhas", "ele/ela/você": "apanha",
                                   "nós": "apanhamos", "eles/elas/vocês": "apanham", "vós": "ignored"})
        e = translator.clean_entry(verb)
        self.assertIsNone(e["gender"])
        self.assertEqual(list(e["present_tense"]), translator.PERSONS)

    def test_input_checks(self):
        with self.assertRaises(translator.InputError):
            translator.check_text("   ", 10)
        with self.assertRaises(translator.InputError):
            translator.check_text("x" * 11, 10)
        self.assertEqual(translator.check_text("  olá  ", 10), "olá")


class PromptTests(unittest.TestCase):
    @mock.patch("llm.requests.post")
    def test_translate_sends_pt_pt_rules_and_user_text(self, post):
        post.return_value = fake_response(TRANSLATION)
        translator.translate("Where is the train station?", "to_pt", "formal")
        body = post.call_args.kwargs["json"]
        system, user = body["messages"][0]["content"], body["messages"][1]["content"]
        self.assertIn("never Brazilian Portuguese", system)
        self.assertIn("Translate the text into European Portuguese", system)
        self.assertIn("never 'tu'", system)
        self.assertEqual(user, "Where is the train station?")
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertNotIn("temperature", body)  # only sent when configured

    def test_unknown_options_rejected(self):
        with self.assertRaises(translator.InputError):
            translator.translate("hello", direction="sideways")
        with self.assertRaises(translator.InputError):
            translator.translate("hello", register="pirate")


class LLMClientTests(unittest.TestCase):
    @mock.patch("llm.requests.post")
    def test_bad_json_is_an_error(self, post):
        resp = mock.Mock(status_code=200)
        resp.json.return_value = {"choices": [{"message": {"content": "not json"}}]}
        post.return_value = resp
        with self.assertRaises(llm.LLMError):
            llm.chat_json("s", "u")

    @mock.patch("llm.requests.post")
    def test_http_error_is_an_error(self, post):
        post.return_value = fake_response({}, status=401)
        with self.assertRaises(llm.LLMError):
            llm.chat_json("s", "u")

    @mock.patch("llm.requests.post", side_effect=llm.requests.ConnectionError("down"))
    def test_network_error_is_an_error(self, post):
        with self.assertRaises(llm.LLMError):
            llm.chat_json("s", "u")

    def test_local_server_needs_no_key(self):
        with mock.patch.object(llm, "API_KEY", ""), mock.patch.object(llm, "BASE_URL", "http://localhost:11434/v1"):
            self.assertTrue(llm.is_configured())
        with mock.patch.object(llm, "API_KEY", ""), mock.patch.object(llm, "BASE_URL", "https://api.openai.com/v1"):
            self.assertFalse(llm.is_configured())


class RateLimiterTests(unittest.TestCase):
    def test_limits_per_client_and_recovers(self):
        rl = webapp.RateLimiter(2, window=60)
        self.assertTrue(rl.allow("a", now=0))
        self.assertTrue(rl.allow("a", now=1))
        self.assertFalse(rl.allow("a", now=2))
        self.assertTrue(rl.allow("b", now=2))   # other clients unaffected
        self.assertTrue(rl.allow("a", now=61))  # window passed


class ApiTests(unittest.TestCase):
    def setUp(self):
        webapp.limiter = webapp.RateLimiter(100)
        self.client = webapp.app.test_client()

    @mock.patch("llm.requests.post")
    def test_translate_endpoint(self, post):
        post.return_value = fake_response(TRANSLATION)
        r = self.client.post("/api/translate", json={"text": "Where is the train station?"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["brazilian_differences"][0]["pt_br"], "trem")

    @mock.patch("llm.requests.post")
    def test_lookup_endpoint(self, post):
        post.return_value = fake_response(ENTRY)
        r = self.client.post("/api/lookup", json={"word": "comboio"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["headword"], "o comboio")

    def test_empty_input_is_400(self):
        r = self.client.post("/api/translate", json={"text": ""})
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.get_json())

    def test_no_body_is_400(self):
        self.assertEqual(self.client.post("/api/lookup", data="x").status_code, 400)

    @mock.patch("llm.requests.post")
    def test_model_failure_is_502(self, post):
        post.return_value = fake_response({}, status=500)
        r = self.client.post("/api/translate", json={"text": "hello"})
        self.assertEqual(r.status_code, 502)

    def test_rate_limit_is_429(self):
        webapp.limiter = webapp.RateLimiter(0)
        self.assertEqual(self.client.post("/api/translate", json={"text": "hi"}).status_code, 429)

    def test_missing_key_is_503(self):
        with mock.patch.object(llm, "API_KEY", ""), mock.patch.object(llm, "BASE_URL", "https://api.openai.com/v1"):
            self.assertEqual(self.client.post("/api/translate", json={"text": "hi"}).status_code, 503)

    def test_page_and_health(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"European Portuguese", page.data)
        self.assertTrue(self.client.get("/health").get_json()["ok"])


if __name__ == "__main__":
    unittest.main()
