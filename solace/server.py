"""HTTP API + web UI. Run: python -m solace.server (stdlib only)."""
import json, os, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from . import core, egain_bridge
from .egain_client import EGainError, EGainNotConfigured, retrieve_knowledge

J = "application/json"
WEB = os.path.join(core.ROOT, "web", "index.html")
CASE = re.compile(r"/api/case/(SOL-[A-F0-9]{8})(?:/([\\w.]+))?")

def route(method, path, data, headers=None):
    headers = headers or {}
    try:
        if method == "GET" and path == "/":
            with open(WEB, "rb") as f: return 200, f.read(), "text/html"
        if method == "GET" and path == "/api/dashboard": return 200, core.dashboard(), J
        if method == "POST" and path == "/api/case": return 201, core.open_case(data), J
        if method == "GET" and path == "/egain/health":
            status = egain_bridge.health()
            required = ("EGAIN_TOKEN_URL", "EGAIN_API_DOMAIN", "EGAIN_CLIENT_ID", "EGAIN_CLIENT_SECRET", "EGAIN_PORTAL_ID", "EGAIN_SCOPE")
            status["knowledge_retrieval_configured"] = all(os.environ.get(k) for k in required)
            status["knowledge_provider"] = "eGain AI Knowledge Hub"
            return 200, status, J
        if method == "POST" and path == "/api/knowledge/retrieve":
            key = os.environ.get("SOLACE_API_KEY")
            if not key: return 503, {"error": "SOLACE API is not configured; set SOLACE_API_KEY"}, J
            if headers.get("x-api-key") != key: return 401, {"error": "unauthorized"}, J
            try:
                return 200, retrieve_knowledge(data.get("query"), data.get("language")), J
            except EGainNotConfigured as exc:
                return 503, {"error": str(exc), "provider": "eGain AI Knowledge Hub"}, J
            except (EGainError, ValueError) as exc:
                return 502, {"error": str(exc), "provider": "eGain AI Knowledge Hub"}, J
        if method in ("GET", "POST") and path in ("/egain/context", "/egain/action"):
            key = os.environ.get("SOLACE_API_KEY")
            if not key: return 503, {"error": "eGain bridge is not configured; set SOLACE_API_KEY"}, J
            if headers.get("x-api-key") != key: return 401, {"error": "unauthorized"}, J
            payload = data if method == "POST" else {"case_id": headers.get("x-case-id", "")}
            if path == "/egain/context":
                if not payload.get("case_id"): return 400, {"error": "case_id is required"}, J
                return 200, egain_bridge.case_context(str(payload["case_id"])), J
            return 200, egain_bridge.execute_action(payload), J
        m = re.fullmatch(r"/api/shared/([\\w-]+)", path)
        if method == "GET" and m: return 200, core.shared_view(m.group(1)), J
        m = CASE.fullmatch(path)
        if m:
            cid, sub = m.groups()
            if method == "GET" and sub is None: return 200, core.view(cid), J
            if method == "DELETE" and sub is None: return 200, core.delete_case(cid), J
            if method == "GET" and sub == "reminders.ics": return 200, core.reminders_ics(cid), "text/calendar"
            if method == "POST" and sub == "chat": return 200, core.chat(cid, str(data.get("message", ""))), J
            if method == "POST" and sub == "action": return 200, core.run_action(cid, data.get("name"), data.get("args")), J
            if method == "POST" and sub == "share": return 200, core.share(cid), J
        return 404, {"error": "not found"}, J
    except KeyError as e: return 404, {"error": "not found: %s" % e}, J
    except ValueError as e: return 400, {"error": str(e)}, J

class H(BaseHTTPRequestHandler):
    def _do(self, method):
        n = int(self.headers.get("Content-Length") or 0)
        try: data = json.loads(self.rfile.read(n) or b"{}")
        except ValueError: data = {}
        hdrs = {k.lower(): v for k, v in self.headers.items()}
        code, body, ctype = route(method, self.path.split("?")[0], data, hdrs)
        if isinstance(body, (dict, list)): body = json.dumps(body)
        if isinstance(body, str): body = body.encode("utf-8")
        self.send_response(code); self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self): self._do("GET")
    def do_POST(self): self._do("POST")
    def do_DELETE(self): self._do("DELETE")
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("Solace on http://localhost:%d" % port)
    ThreadingHTTPServer(("", port), H).serve_forever()
