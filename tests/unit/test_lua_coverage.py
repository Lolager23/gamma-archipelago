from lupa.luajit21 import LuaRuntime

from tools.lua_coverage import TRACE_SETUP


def test_collector_counts_unexecuted_class_methods_and_handles_cycles(tmp_path):
    source = tmp_path / "gamma_ap_class_probe.script"
    source.write_text(
        "window = {}\nwindow.self = window\n"
        "function window:render()\n"
        "    local text = 'tracked'\n"
        "    return text\nend\n",
        encoding="utf-8",
    )
    runtime = LuaRuntime(unpack_returned_tuples=True)
    runtime.execute("jit.off(); jit.flush()")
    runtime.execute(TRACE_SETUP)
    module = runtime.globals().load_ap_module(str(source))
    expected = runtime.globals().ap_coverage.expected["@" + str(source)]
    executed = runtime.globals().ap_coverage.executed["@" + str(source)]
    assert expected[4] is True and not executed[4]
    assert module.window.render(module.window) == "tracked"
    assert executed[4] is True
