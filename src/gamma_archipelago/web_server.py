"""Loopback-only HTTP boundary for the local seed workbench."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

from .web_generation import GenerationBusy, SeedGenerator
from .web_planner import metadata, player_document, preview

ASSETS = {
    "/": "index.html",
    "/index.html": "index.html",
    "/style.css": "style.css",
    "/app.js": "app.js",
    "/ui.js": "ui.js",
    "/form_state.js": "form_state.js",
    "/reward_controls.js": "reward_controls.js",
}
TYPES = {".html": "text/html", ".css": "text/css", ".js": "text/javascript"}


def check_json_depth(payload: bytes) -> None:
    """Bound nesting before the JSON decoder, without counting quoted brackets."""
    depth = 0
    quoted = escaped = False
    for byte in payload:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > 16:
                raise ValueError("JSON nesting cannot exceed 16 levels")
        elif byte in (93, 125):
            depth -= 1


def make_handler(assets: Path, generator: SeedGenerator) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        body_timeout_seconds = 5.0

        def log_message(self, format: str, *args: Any) -> None:
            pass  # Requests contain configuration data; do not log their contents.

        def _allowed(self, mutation: bool = False) -> bool:
            port = cast(HTTPServer, self.server).server_port
            hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
            if self.headers.get("Host") not in hosts:
                self._json(403, {"error": "Use the local workbench address"})
                return False
            if mutation and self.headers.get("Origin") not in {"http://" + host for host in hosts}:
                self._json(403, {"error": "Requests must originate in the local workbench"})
                return False
            return True

        def _send(self, status: int, payload: bytes, kind: str, filename: str = "") -> None:
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' data:; "
                "object-src 'none'; frame-ancestors 'none'",
            )
            if filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(payload)

        def _json(self, status: int, value: object) -> None:
            self._send(status, json.dumps(value).encode(), "application/json")

        def do_GET(self) -> None:
            if not self._allowed():
                return
            if self.path == "/api/metadata":
                self._json(200, metadata())
            elif self.path in ASSETS:
                path = assets / ASSETS[self.path]
                self._send(200, path.read_bytes(), TYPES[path.suffix] + "; charset=utf-8")
            else:
                self._json(404, {"error": "Not found"})

        def _body(self) -> dict[str, Any]:
            if self.headers.get("Content-Type") != "application/json":
                raise ValueError("Send application/json")
            size = int(self.headers.get("Content-Length", "0"))
            if not 1 <= size <= 65536:
                raise ValueError("Request must contain 1–65536 bytes")
            self.connection.settimeout(self.body_timeout_seconds)
            try:
                payload = self.rfile.read(size)
            except TimeoutError as error:
                raise ValueError("Request body timed out before it was complete") from error
            if len(payload) != size:
                raise ValueError("Request body was incomplete; send the complete JSON document")
            check_json_depth(payload)
            value = json.loads(payload)
            if not isinstance(value, dict) or not isinstance(value.get("options"), dict):
                raise ValueError("Provide an options object")
            if not isinstance(value.get("assumptions", {}), dict):
                raise ValueError("Provide an assumptions object")
            return value

        def do_POST(self) -> None:
            if not self._allowed(mutation=True):
                return
            if self.path not in {"/api/preview", "/api/yaml", "/api/generate"}:
                self._json(404, {"error": "Not found"})
                return
            try:
                request = self._body()
                result = preview(request["options"], request.get("assumptions", {}))
                if self.path == "/api/preview":
                    self._json(200, result)
                else:
                    document = player_document(request.get("name"), request["options"])
                    if self.path == "/api/yaml":
                        self._send(
                            200,
                            (json.dumps(document, indent=2) + "\n").encode(),
                            "application/yaml",
                            "gamma-player.yaml",
                        )
                    else:
                        name, archive = generator.generate(document, request.get("seed"))
                        self._send(200, archive, "application/zip", name)
            except GenerationBusy as error:
                self._json(409, {"error": str(error)})
            except (ValueError, OSError) as error:
                self._json(400, {"error": str(error)})

    return Handler


def serve(assets: Path, generator: SeedGenerator, port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(assets, generator))
