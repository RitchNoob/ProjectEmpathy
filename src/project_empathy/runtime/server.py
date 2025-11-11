"""Self-contained HTTP server to expose the shim FastAPI app in production-like mode."""

from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Mapping, Optional
from urllib.parse import parse_qs, urlsplit

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient


class _EmpathyHTTPServer(ThreadingHTTPServer):
    """Small HTTP server wrapping the TestClient dispatcher."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address: tuple[str, int], app) -> None:
        super().__init__(server_address, _EmpathyRequestHandler)
        self.app = app
        self.test_client = TestClient(app)
        self._cors_options = _extract_cors_options(app)


class _EmpathyRequestHandler(BaseHTTPRequestHandler):
    server: _EmpathyHTTPServer  # type: ignore[assignment]

    def do_OPTIONS(self) -> None:  # noqa: N802 - inherited API
        self.send_response(204)
        self._write_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 - inherited API
        self._dispatch()

    def do_POST(self) -> None:  # noqa: N802 - inherited API
        self._dispatch()

    def do_PATCH(self) -> None:  # noqa: N802 - inherited API
        self._dispatch()

    def do_DELETE(self) -> None:  # noqa: N802 - inherited API
        self._dispatch()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003 - BaseHTTPRequestHandler API
        # Silence noisy request logs; CLI already surfaces service state.
        return

    # internal helpers -------------------------------------------------
    def _dispatch(self) -> None:
        try:
            response = self._call_app()
        except _BadRequest as exc:
            self.send_response(400)
            self._write_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"detail": str(exc)}).encode("utf-8"))
            return

        status_code = response.status_code
        body = response.content

        self.send_response(status_code)
        self._write_cors_headers()

        if body is None:
            self.end_headers()
            return

        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _call_app(self):
        client = self.server.test_client
        split_result = urlsplit(self.path)
        params = _flatten_query(parse_qs(split_result.query, keep_blank_values=True))
        headers = {key: value for key, value in self.headers.items()}

        json_payload: Any | None = None
        data_payload: Any | None = None

        if self.command in {"POST", "PATCH", "PUT"}:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw_body = self.rfile.read(length) if length else b""
            content_type = (self.headers.get("Content-Type") or "").lower()

            if raw_body:
                if "application/json" in content_type:
                    try:
                        json_payload = json.loads(raw_body.decode("utf-8"))
                    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
                        raise _BadRequest("JSON invalide") from exc
                elif "application/x-www-form-urlencoded" in content_type:
                    data_payload = _flatten_query(parse_qs(raw_body.decode("utf-8"), keep_blank_values=True))
                else:
                    data_payload = raw_body

        return client._request(  # type: ignore[attr-defined]
            self.command,
            split_result.path or "/",
            json=json_payload,
            data=data_payload,
            params=params,
            headers=headers,
        )

    def _write_cors_headers(self) -> None:
        options = self.server._cors_options
        allow_origin = options.get("allow_origin") or "*"
        self.send_header("Access-Control-Allow-Origin", allow_origin)
        self.send_header(
            "Access-Control-Allow-Methods",
            options.get("allow_methods") or "GET,POST,PATCH,DELETE,OPTIONS",
        )
        self.send_header("Access-Control-Allow-Headers", options.get("allow_headers") or "*")
        if options.get("allow_credentials"):
            self.send_header("Access-Control-Allow-Credentials", "true")


class _BadRequest(Exception):
    pass


def _flatten_query(values: Mapping[str, list[str]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, items in values.items():
        if not items:
            result[key] = ""
        elif len(items) == 1:
            result[key] = items[0]
        else:
            result[key] = items
    return result


def _extract_cors_options(app) -> Dict[str, Any]:
    allow_origin: Optional[str] = None
    allow_methods: Optional[str] = None
    allow_headers: Optional[str] = None
    allow_credentials = False

    for middleware in getattr(app, "middleware", []):
        if middleware.middleware_class is CORSMiddleware:
            options = middleware.options
            origins = options.get("allow_origins")
            if origins:
                if "*" in origins:
                    allow_origin = "*"
                else:
                    allow_origin = ",".join(str(origin) for origin in origins)
            methods = options.get("allow_methods")
            if methods:
                allow_methods = ",".join(str(method) for method in methods)
            headers = options.get("allow_headers")
            if headers:
                allow_headers = ",".join(str(header) for header in headers)
            allow_credentials = bool(options.get("allow_credentials"))
            break

    return {
        "allow_origin": allow_origin,
        "allow_methods": allow_methods,
        "allow_headers": allow_headers,
        "allow_credentials": allow_credentials,
    }


def serve_app(app, *, host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the shim FastAPI app until interrupted."""

    address = (host, port)
    with _EmpathyHTTPServer(address, app) as httpd:
        bind_host = host if host not in ("0.0.0.0", "::") else "127.0.0.1"
        effective = httpd.server_address
        url = f"http://{bind_host}:{effective[1]}"
        print(f"🌐 API disponible sur {url}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:  # pragma: no cover - interactive behaviour
            print("Arrêt du serveur demandé…")


def serve_in_thread(app, *, host: str = "127.0.0.1", port: int = 0):
    """Utility used in tests to run the HTTP server in the background."""

    httpd = _EmpathyHTTPServer((host, port), app)

    thread = threading.Thread(target=httpd.serve_forever, name="EmpathyHTTPServer", daemon=True)
    thread.start()
    return httpd, thread


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Serveur HTTP autonome pour Project Empathy")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    from project_empathy.main import create_app

    serve_app(create_app(), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI behaviour
    raise SystemExit(main())


__all__ = ["serve_app", "serve_in_thread", "main"]
