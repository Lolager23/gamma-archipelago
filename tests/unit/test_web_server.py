import http.client
import json
import socket
import threading
from types import SimpleNamespace

import pytest

from gamma_archipelago.configuration import defaults
from gamma_archipelago.web_generation import GenerationBusy
from gamma_archipelago.web_server import serve


@pytest.fixture
def web(tmp_path):
    for filename in ("index.html", "style.css", "app.js", "ui.js", "form_state.js"):
        (tmp_path / filename).write_text("asset")
    generator = SimpleNamespace(generate=lambda document, seed: ("AP_test.zip", b"seed archive"))
    server = serve(tmp_path, generator, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(method, path, data=None, headers=None, end_body=False, stall_body=False):
        if stall_body:
            server.RequestHandlerClass.body_timeout_seconds = 0.1
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        payload = json.dumps(data) if isinstance(data, dict) else data
        response_headers = {
            "Origin": f"http://127.0.0.1:{server.server_port}",
            "Content-Type": "application/json",
            **(headers or {}),
        }
        connection.request(method, path, payload, response_headers)
        if end_body:
            connection.sock.shutdown(socket.SHUT_WR)
        response = connection.getresponse()
        status, received, body = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return status, received, body

    yield request, generator
    server.shutdown()
    server.server_close()
    thread.join()


def test_metadata_assets_preview_and_exports(web):
    request, _ = web
    status, headers, body = request("GET", "/api/metadata")
    assert status == 200 and "presets" in json.loads(body)
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "img-src 'self' data:" in headers["Content-Security-Policy"]
    for path in ("/", "/index.html", "/style.css", "/app.js", "/ui.js", "/form_state.js"):
        assert request("GET", path)[2] == b"asset"
    body = {"options": defaults(), "name": "Owen", "seed": "123"}
    assert json.loads(request("POST", "/api/preview", body)[2])["network_checks"] == 33
    status, headers, content = request("POST", "/api/yaml", body)
    assert status == 200 and json.loads(content)["name"] == "Owen"
    assert "gamma-player.yaml" in headers["Content-Disposition"]
    status, _, content = request("POST", "/api/generate", body)
    assert status == 200 and content == b"seed archive"


@pytest.mark.parametrize(
    "method,path,headers,status",
    [
        ("GET", "/../pyproject.toml", {}, 404),
        ("POST", "/api/unknown", {}, 404),
        ("GET", "/", {"Host": "attacker.test"}, 403),
        ("POST", "/api/preview", {"Origin": "https://attacker.test"}, 403),
        ("POST", "/api/preview", {"Origin": ""}, 403),
        ("POST", "/api/preview", {"Content-Type": "text/plain"}, 400),
        ("POST", "/api/preview", {"Content-Length": "65537"}, 400),
        ("POST", "/api/preview", {"Content-Length": "nonsense"}, 400),
        ("POST", "/api/preview", {"Content-Length": "0"}, 400),
    ],
)
def test_http_boundaries_refuse_foreign_origins_paths_and_bad_sizes(
    web, method, path, headers, status
):
    payload = None if method == "GET" or "Content-Length" in headers else {"options": defaults()}
    assert web[0](method, path, payload, headers)[0] == status


@pytest.mark.parametrize(
    "body", ["{broken", "[]", "{}", '{"options":[]}', '{"options":{},"assumptions":1}']
)
def test_bad_json_shapes_are_actionable(web, body):
    status, _, result = web[0]("POST", "/api/preview", body)
    assert status == 400 and "error" in json.loads(result)


@pytest.mark.parametrize(
    "error,status", [(GenerationBusy("busy"), 409), (OSError("disk full"), 400)]
)
def test_generation_errors_are_reported(web, error, status):
    def fail(document, seed):
        raise error

    request, generator = web
    generator.generate = fail
    response = request(
        "POST", "/api/generate", {"options": defaults(), "name": "Owen", "seed": "1"}
    )
    assert response[0] == status and str(error) in response[2].decode()


def test_truncated_body_cannot_be_accepted_as_a_complete_configuration(web):
    body = {"options": defaults()}
    advertised = len(json.dumps(body).encode()) + 5
    status, _, response = web[0](
        "POST", "/api/preview", body, {"Content-Length": str(advertised)}, end_body=True
    )
    assert status == 400 and "incomplete" in json.loads(response)["error"]


def test_extreme_json_nesting_returns_a_bounded_error_instead_of_dropping_connection(web):
    body = '{"options":{"nested":' + "[" * 2000 + "0" + "]" * 2000 + "}}"
    status, _, response = web[0]("POST", "/api/preview", body)
    assert status == 400 and "nesting" in json.loads(response)["error"]


def test_stalled_request_times_out_and_server_handles_the_next_request(web):
    body = {"options": defaults()}
    advertised = len(json.dumps(body).encode()) + 5
    status, _, response = web[0](
        "POST", "/api/preview", body, {"Content-Length": str(advertised)}, stall_body=True
    )
    assert status == 400 and "timed out" in json.loads(response)["error"]
    assert web[0]("POST", "/api/preview", body)[0] == 200


def test_depth_limit_ignores_brackets_and_escaped_quotes_inside_strings(web):
    body = {"options": defaults(), "note": '[{\\"' * 1000}
    assert web[0]("POST", "/api/preview", body)[0] == 200
