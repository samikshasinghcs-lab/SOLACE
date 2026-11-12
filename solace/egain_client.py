"""Authenticated client for eGain AI Knowledge Hub retrieval APIs.

Retrieves source chunks only; it deliberately does not generate policy answers.
Tenant-specific endpoints must come from eGain Client Application metadata.
"""
from __future__ import annotations
import json
import os
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class EGainError(RuntimeError):
    """Raised when eGain is unavailable or rejects a request."""


class EGainNotConfigured(EGainError):
    """Raised when required eGain environment settings are absent."""


class EGainKnowledgeClient:
    def __init__(self, environ=None, opener=None):
        self.environ = environ if environ is not None else os.environ
        self.opener = opener or urlopen
        self._token = None
        self._token_expires_at = 0
        self._lock = threading.Lock()

    def _config(self):
        required = (
            "EGAIN_TOKEN_URL", "EGAIN_API_DOMAIN", "EGAIN_CLIENT_ID",
            "EGAIN_CLIENT_SECRET", "EGAIN_PORTAL_ID", "EGAIN_SCOPE",
        )
        missing = [key for key in required if not self.environ.get(key)]
        if missing:
            raise EGainNotConfigured("Missing eGain settings: " + ", ".join(missing))
        return {key: self.environ[key] for key in required}

    def _access_token(self):
        with self._lock:
            if self._token and time.time() < self._token_expires_at - 60:
                return self._token
            cfg = self._config()
            form = {
                "grant_type": "client_credentials",
                "client_id": cfg["EGAIN_CLIENT_ID"],
                "client_secret": cfg["EGAIN_CLIENT_SECRET"],
                "scope": cfg["EGAIN_SCOPE"],
            }
            req = Request(
                cfg["EGAIN_TOKEN_URL"],
                data=urlencode(form).encode("utf-8"),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            payload = self._json_request(req)
            token = payload.get("access_token")
            if not token:
                raise EGainError("eGain token response did not contain access_token")
            self._token = token
            self._token_expires_at = time.time() + int(payload.get("expires_in", 300))
            return token

    def retrieve(self, query, language=None):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        cfg = self._config()
        lang = language or self.environ.get("EGAIN_LANGUAGE", "en-US")
        params = urlencode({"q": query.strip(), "$lang": lang})
        url = f"{cfg['EGAIN_API_DOMAIN'].rstrip('/')}/core/aiservices/v4/{cfg['EGAIN_PORTAL_ID']}/retrieve?{params}"
        req = Request(
            url,
            headers={"Authorization": "Bearer " + self._access_token(), "Accept": "application/json"},
            method="POST",
        )
        return {
            "provider": "eGain AI Knowledge Hub",
            "mode": "retrieval_only",
            "query": query.strip(),
            "language": lang,
            "results": self._json_request(req),
            "answer_generation": False,
            "grounding_policy": "Use only retrieved approved sources; abstain and escalate if evidence is missing, stale, contradictory or irrelevant.",
        }

    def _json_request(self, request):
        try:
            with self.opener(request, timeout=20) as response:
                raw = response.read()
        except HTTPError as exc:
            detail = exc.read(2048).decode("utf-8", "replace")
            raise EGainError(f"eGain HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise EGainError(f"eGain request failed: {exc}") from exc
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EGainError("eGain returned invalid JSON") from exc


_default_client = EGainKnowledgeClient()


def retrieve_knowledge(query, language=None):
    return _default_client.retrieve(query, language)
