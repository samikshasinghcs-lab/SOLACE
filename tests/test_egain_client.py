import io
import json
import unittest
from urllib.parse import parse_qs

from solace.egain_client import EGainKnowledgeClient, EGainNotConfigured


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class FakeOpener:
    def __init__(self):
        self.requests = []

    def __call__(self, request, timeout=20):
        self.requests.append(request)
        if request.full_url.endswith("/oauth/token"):
            return FakeResponse({"access_token": "test-token", "expires_in": 3600})
        return FakeResponse({"chunks": [{"text": "Use the official portal.", "source": "approved-article-1"}]})


class EGainClientTests(unittest.TestCase):
    def setUp(self):
        self.env = {
            "EGAIN_TOKEN_URL": "https://tenant.example/oauth/token",
            "EGAIN_API_DOMAIN": "https://api.example",
            "EGAIN_CLIENT_ID": "client",
            "EGAIN_CLIENT_SECRET": "secret",
            "EGAIN_PORTAL_ID": "PZ-123",
            "EGAIN_LANGUAGE": "en-US",
        }
        self.opener = FakeOpener()
        self.client = EGainKnowledgeClient(self.env, self.opener)

    def test_retrieve_uses_oauth_and_retrieval_endpoint(self):
        result = self.client.retrieve("How do I report a lost PAN?")
        self.assertEqual(result["provider"], "eGain AI Knowledge Hub")
        self.assertEqual(result["mode"], "retrieval_only")
        self.assertFalse(result["answer_generation"])
        self.assertEqual(result["results"]["chunks"][0]["source"], "approved-article-1")
        self.assertEqual(len(self.opener.requests), 2)
        api_request = self.opener.requests[1]
        self.assertIn("/core/aiservices/v4/PZ-123/retrieve?", api_request.full_url)
        self.assertEqual(api_request.get_header("Authorization"), "Bearer test-token")
        self.assertEqual(parse_qs(api_request.full_url.split("?", 1)[1])["q"], ["How do I report a lost PAN?"])

    def test_token_is_cached(self):
        self.client.retrieve("first")
        self.client.retrieve("second")
        self.assertEqual(sum(r.full_url.endswith("/oauth/token") for r in self.opener.requests), 1)

    def test_missing_config_fails_closed(self):
        client = EGainKnowledgeClient({}, self.opener)
        with self.assertRaises(EGainNotConfigured):
            client.retrieve("test")

    def test_empty_query_is_rejected(self):
        with self.assertRaises(ValueError):
            self.client.retrieve("  ")


if __name__ == "__main__":
    unittest.main()
