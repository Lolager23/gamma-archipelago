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
    for filename in (
        "index.html",
        "style.css",
        "app.js",
        "ui.js",
        "form_state.js",
        "reward_controls.js",
    ):
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
    for path in (
        "/",
        "/index.html",
        "/style.css",
        "/app.js",
        "/ui.js",
        "/form_state.js",
        "/reward_controls.js",
    ):
        assert request("GET", path)[2] == b"asset"
    body = {"options": defaults(), "name": "Owen", "seed": "123"}
    assert json.loads(request("POST", "/api/preview", body)[2])["network_checks"] == 33
    status, headers, content = request("POST", "/api/yaml", body)
    assert status == 200 and json.loads(content)["name"] == "Owen"
    assert "gamma-player.yaml" in headers["Content-Disposition"]
    status, _, content = request("POST", "/api/generate", body)
    assert status == 200 and content == b"seed archive"


@pytest.mark.parametrize(
    "method,path,headers,status,reason",
    [
        ("GET", "/../pyproject.toml", {}, 404, "Not found"),
        ("POST", "/api/unknown", {}, 404, "Not found"),
        ("GET", "/", {"Host": "attacker.test"}, 403, "local workbench address"),
        ("POST", "/api/preview", {"Origin": "https://attacker.test"}, 403, "originate"),
        ("POST", "/api/preview", {"Origin": ""}, 403, "originate"),
        ("POST", "/api/preview", {"Content-Type": "text/plain"}, 400, "application/json"),
        ("POST", "/api/preview", {"Content-Length": "65537"}, 400, "1–65536 bytes"),
        ("POST", "/api/preview", {"Content-Length": "nonsense"}, 400, "invalid literal"),
        ("POST", "/api/preview", {"Content-Length": "0"}, 400, "1–65536 bytes"),
    ],
)
def test_http_boundaries_refuse_foreign_origins_paths_and_bad_sizes(
    web, method, path, headers, status, reason
):
    # These requests are rejected from headers/route alone. A body can race the
    # early close on Windows, aborting the socket before the response is read.
    actual, _, response = web[0](method, path, None, headers)
    assert actual == status
    assert reason in json.loads(response)["error"]


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


def test_reward_controls_preserve_exact_exports_and_refuse_over_capacity_generation(web):
    from gamma_archipelago.presets import presets

    request, generator = web
    options = presets()["living_legend"] | {"basic_loot_stashes": 72}
    body = dict(name="RewardReview", seed="20261123", options=options)
    status, _, data = request("POST", "/api/preview", body)
    assert status == 200
    budget = json.loads(data)["pool_budget"]
    assert (
        sum(
            count
            for name, count in budget["guaranteed_useful"].items()
            if name.startswith("Basic Loot Stash:")
        )
        == 72
    )
    status, _, data = request("POST", "/api/yaml", body)
    assert status == 200
    exported = json.loads(data)
    assert exported[exported["game"]]["basic_loot_stashes"] == 72

    options["rewards_loot_stashes"] = 0
    status, _, data = request("POST", "/api/preview", body)
    disabled = json.loads(data)
    assert status == 200 and disabled["configuration"]["basic_loot_stashes"] == 72
    assert not any(row.get("category") == "rewards_loot_stashes" for row in disabled["rewards"])
    options["rewards_loot_stashes"] = 1
    options["basic_loot_stashes"] = 500
    generator.generate = lambda *_: pytest.fail("Invalid pool must not invoke generation")
    for route in ("/api/preview", "/api/yaml", "/api/generate"):
        status, _, data = request("POST", route, body)
        assert status == 400 and "exceed available reliable checks" in json.loads(data)["error"]
    options["basic_loot_stashes"] = 4
    assert request("POST", "/api/preview", body)[0] == 200
