from pathlib import Path

import pytest

from gamma_archipelago.probe_report import parse_line

ROOT = Path(__file__).resolve().parents[2]


def load_probe(lua, *, task_hook=True, root="D:/AnomalyAP/appdata/"):
    lua.execute("""
        probe = {root='', now=1000, level='l01_escape', alive=true, logs={}, callbacks={},
                 created=0, fail_reward=false, artefact=false, classifier_error=false}
        db={actor={alive=function() return probe.alive end}}
        getFS=function() return {update_path=function() return probe.root end} end
        time_global=function() return probe.now end
        level={name=function() return probe.level end}
        printf=function(format, value) probe.logs[#probe.logs+1]=string.format(format,value) end
        RegisterScriptCallback=function(name,callback) probe.callbacks[name]=callback end
        UnregisterScriptCallback=function(name,callback)
            assert(probe.callbacks[name]==callback); probe.callbacks[name]=nil
        end
        IsArtefact=function(item)
            if probe.classifier_error then error('classifier failed') end
            return probe.artefact
        end
        alife_create_item=function(section,actor)
            assert(section=='bandage' and actor==db.actor)
            probe.created=probe.created+1
            if probe.fail_reward=='raise' then error('creation failed') end
            if probe.fail_reward then return nil end
            return {id=50}
        end
        task={completed=1, fail=2}
        callbacks_gameobject={task_callback=function() end}
        item={section=function() return 'af_medusa' end, id=function() return 123 end}
        box={id=function() return 456 end, name=function() return 'escape_static_stash' end}
        task_object={get_id=function() return 'esc_story_task' end}
    """)
    engine = lua.globals().probe
    engine.root = root
    if not task_hook:
        lua.globals().callbacks_gameobject = None
    loader = lua.globals().load_ap_module
    for name in ("capture", "game"):
        module = loader(str(ROOT / "probes/gamedata/scripts" / f"gamma_ap_probe_{name}.script"))
        lua.globals()[f"gamma_ap_probe_{name}"] = module
    module.on_game_start()
    return module, engine


def observations(engine):
    return [parse_line(line) for line in engine.logs.values()]


def test_probe_registers_supported_hooks_and_bounds_update_logging(lua):
    module, engine = load_probe(lua)
    assert set(engine.callbacks.keys()) == {
        "actor_on_first_update",
        "actor_on_update",
        "actor_on_item_take",
        "actor_on_item_take_from_box",
        "actor_on_task_callback",
        "save_state",
        "load_state",
    }
    module.actor_on_first_update()
    module.actor_on_update()
    engine.level = "l02_garbage"
    module.actor_on_update()
    assert [item.level for item in observations(engine) if item.event == "level"] == ["l01_escape"]
    engine.now += 500
    module.actor_on_update()
    engine.now += 500
    module.actor_on_update()
    assert [item.level for item in observations(engine) if item.event == "level"] == [
        "l01_escape",
        "l02_garbage",
    ]
    engine.alive = False
    module.actor_on_update()
    lua.globals().db.actor = None
    module.actor_on_update()
    assert len([item for item in observations(engine) if item.event == "level"]) == 2


def test_probe_observes_items_boxes_artefacts_and_task_outcomes_without_mutation(lua):
    module, engine = load_probe(lua)
    item, box = lua.globals().item, lua.globals().box
    module.actor_on_item_take(item)
    engine.artefact = True
    module.actor_on_item_take(item)
    module.actor_on_item_take_from_box(box, item)
    manager = lua.table_from(
        {
            "task_info": lua.table_from(
                {"esc_story_task": lua.table_from({"cancelled_by_actor": True})}
            )
        }
    )
    for status in (1, 2, 0):
        module.actor_on_task_callback(lua.globals().task_object, status, manager, "esc_story_task")
    module.actor_on_task_callback(lua.globals().task_object, 1, None, None)
    records = observations(engine)
    assert [record.values for record in records if record.event == "box"] == [
        ("456", "escape_static_stash", "af_medusa")
    ]
    assert len([record for record in records if record.event == "artefact"]) == 1
    tasks = [record.values for record in records if record.event == "task"]
    assert [value[1] for value in tasks] == ["completed", "failed", "other", "completed"]
    assert tasks[1][2] == "true"
    assert tasks[-1][2] == "false"
    assert manager.task_info.esc_story_task.cancelled_by_actor is True
    assert engine.created == 0


def test_probe_handles_bad_objects_classifier_errors_and_missing_task_extension(lua):
    module, engine = load_probe(lua, task_hook=False)
    assert "actor_on_task_callback" not in engine.callbacks
    assert observations(engine)[1].values[0] == "missing"
    module.actor_on_item_take(None)
    module.actor_on_item_take_from_box(None, lua.table())
    engine.classifier_error = True
    module.actor_on_item_take(lua.table())
    assert [record.values[0] for record in observations(engine) if record.event == "error"] == [
        "artefact_classifier"
    ]
    assert next(record for record in observations(engine) if record.event == "box").values == (
        "unavailable",
        "unavailable",
        "unavailable",
    )


def test_save_marker_is_namespaced_and_load_does_not_touch_pilot_receipts(lua):
    module, engine = load_probe(lua)
    data = lua.table_from({"gamma_archipelago_v1": "preserved", "other_mod": "preserved"})
    module.save_state(data)
    assert data.gamma_ap_probe_v1.marker == 1
    assert data.gamma_archipelago_v1 == "preserved" and data.other_mod == "preserved"
    module.save_state(data)
    assert data.gamma_ap_probe_v1.marker == 2
    module.load_state(data)
    module.load_state(lua.table())
    assert [record.values[:2] for record in observations(engine) if record.event == "load"] == [
        ("2", "restored"),
        ("0", "missing"),
    ]


@pytest.mark.parametrize("failure", [False, True, "raise"])
def test_reward_is_an_explicit_single_attempt_and_records_creation_only(lua, failure):
    module, engine = load_probe(lua)
    engine.fail_reward = failure
    assert engine.created == 0
    assert module.try_reward() is (failure is False)
    assert module.try_reward() is False
    assert engine.created == 1
    result = next(record for record in observations(engine) if record.event == "reward")
    assert result.values[:2] == ("bandage", "created" if failure is False else "failed")


@pytest.mark.parametrize("root", ["D:/Anomaly/appdata/", "D:/Other/appdata/"])
def test_original_or_unknown_root_is_refused_without_registration_or_rewards(lua, root):
    module, engine = load_probe(lua, root=root)
    assert not list(engine.callbacks.keys()) and not list(engine.logs.values())
    assert module.try_reward() is False


def test_root_is_rechecked_after_start_and_stop_unregisters_our_own_callbacks(lua):
    module, engine = load_probe(lua, root="D:\\AnomalyAP\\appdata\\")
    before = len(engine.logs)
    engine.root = "D:/Anomaly/appdata/"
    data = lua.table()
    for callback in (
        module.actor_on_first_update,
        module.actor_on_update,
        lambda: module.actor_on_item_take(lua.globals().item),
        lambda: module.actor_on_item_take_from_box(None, None),
        lambda: module.actor_on_task_callback(None, 1, None, None),
        lambda: module.save_state(data),
        lambda: module.load_state(data),
    ):
        callback()
    assert len(engine.logs) == before and not list(data.keys())
    assert module.try_reward() is False
    engine.root = "D:/AnomalyAP/appdata/"
    module.stop()
    assert not list(engine.callbacks.keys())
    assert observations(engine)[-1].event == "stopped"
    module.stop()
    module.actor_on_first_update()
    assert module.try_reward() is False
    module.on_game_start()
    engine.alive = False
    assert module.try_reward() is False
    lua.globals().db.actor = None
    assert module.try_reward() is False
    module.on_game_start()
    assert "save_state" in engine.callbacks


def test_capture_is_bounded_sanitized_and_validates_save_markers(lua):
    load_probe(lua)
    capture = lua.globals().gamma_ap_probe_capture
    state = capture.new_capture()
    assert capture.clean(None) == "-" and capture.clean("") == "-"
    assert capture.clean("a|b\nc") == "a_b_c"
    assert len(capture.clean("a" * 200)) == 96
    for _ in range(256):
        assert capture.record(state, 0, "item", None, None, None, None) is not None
    assert capture.record(state, 0, "item", None, None, None, None) is None
    assert capture.restore_marker(None) == (0, "missing")
    assert capture.restore_marker(lua.table_from({"schema": 1, "marker": 0})) == (0, "restored")
    for invalid in (
        42,
        {},
        {"schema": 2, "marker": 0},
        {"schema": 1, "marker": "x"},
        {"schema": 1, "marker": -1},
        {"schema": 1, "marker": 1000001},
        {"schema": 1, "marker": 0.5},
    ):
        value = lua.table_from(invalid) if isinstance(invalid, dict) else invalid
        assert capture.restore_marker(value) == (0, "invalid")
