"""Executable-line coverage under LuaJIT; this deliberately makes no branch-coverage claim."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED: dict[str, set[int]] = {}
EXECUTED: dict[str, set[int]] = {}

TRACE_SETUP = r"""
ap_coverage = {expected={}, executed={}, visited={}}
function ap_collect_function(fn)
    if ap_coverage.visited[fn] then return end
    ap_coverage.visited[fn] = true
    local info = debug.getinfo(fn, "SL")
    if info.source:find("gamma_ap_", 1, true) then
        ap_coverage.expected[info.source] = ap_coverage.expected[info.source] or {}
        for line in pairs(info.activelines or {}) do
            ap_coverage.expected[info.source][line] = true
        end
    end
    for index=1,100 do
        local name,value=debug.getupvalue(fn,index)
        if not name then break end
        if type(value)=="function" then ap_collect_function(value) end
    end
end
debug.sethook(function(_,line)
    local source = debug.getinfo(2,"S").source
    if source:find("gamma_ap_",1,true) then
        ap_coverage.executed[source] = ap_coverage.executed[source] or {}
        ap_coverage.executed[source][line] = true
    end
end,"l")
function load_ap_module(path)
    local env=setmetatable({}, {__index=_G})
    local chunk=assert(loadfile(path))
    setfenv(chunk,env)
    ap_collect_function(chunk)
    chunk()
    for _,value in pairs(env) do
        if type(value)=="function" then ap_collect_function(value) end
    end
    return env
end
"""


def collect(runtime):
    runtime.execute("debug.sethook()")
    for kind, destination in (("expected", EXPECTED), ("executed", EXECUTED)):
        for source, lines in runtime.globals().ap_coverage[kind].items():
            name = Path(source.removeprefix("@")).name
            destination.setdefault(name, set()).update(lines.keys())


def report() -> bool:
    output = {}
    for name, expected in sorted(EXPECTED.items()):
        if name == "gamma_ap_catalog.script":
            continue  # Generated data is covered by catalogue parity assertions.
        missing = expected - EXECUTED.get(name, set())
        percent = 100 * (len(expected) - len(missing)) / max(1, len(expected))
        output[name] = {
            "line_percent": percent,
            "executable_lines": len(expected),
            "missing_lines": sorted(missing),
        }
        print(f"Lua {name}: {percent:.2f}% executable lines; missing={sorted(missing)}")
    destination = ROOT / "artifacts"
    destination.mkdir(exist_ok=True)
    (destination / "lua-coverage.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    return bool(output) and all(item["line_percent"] >= 95 for item in output.values())
