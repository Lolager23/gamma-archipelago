import test from "node:test";
import assert from "node:assert/strict";
import {
  DraftConfiguration,
  playerNameError,
  validSeed,
} from "../../web/generator/form_state.js";

test("canonical no-weapons previews never make temporary omissions permanent", () => {
  const form = new DraftConfiguration();
  form.selectPreset({
    starting_firearms: 0,
    starting_melee: 2,
    no_starting_weapons: 0,
  });
  form.edit("no_starting_weapons", 1);
  form.accept(form.revision, {
    configuration: {
      starting_firearms: 1,
      starting_melee: 2,
      no_starting_weapons: 1,
    },
  });
  assert.equal(form.options.starting_firearms, 0);
  form.edit("no_starting_weapons", 0);
  assert.equal(form.result, null);
  assert.equal(form.options.starting_firearms, 0);
  assert.equal(form.options.starting_melee, 2);
});

test("late previews cannot re-enable generation for an obsolete draft", () => {
  const form = new DraftConfiguration();
  form.selectPreset({ checks_maps: 1 });
  const old = form.revision;
  form.edit("checks_maps", 0);
  assert.equal(form.accept(old, { network_checks: 33 }), false);
  assert.equal(form.result, null);
  assert.equal(form.accept(form.revision, { network_checks: 0 }), true);
  form.invalidate();
  assert.equal(form.result, null);
});

test("presets and milestone arrays are copied instead of changing the source preset", () => {
  const preset = { checks_maps: 1, kill_milestones: [10, 25] };
  const form = new DraftConfiguration();
  form.selectPreset(preset);
  form.options.kill_milestones.push(50);
  form.edit("checks_maps", 0);
  assert.deepEqual(preset, { checks_maps: 1, kill_milestones: [10, 25] });
});

test("name rules catch blank, injection, reserved and overlong names before download", () => {
  for (const value of [
    "",
    " ",
    "Archipelago",
    "archipelago",
    " Archipelago ",
    "../name",
    "a".repeat(17),
    "name\nfield",
  ]) {
    assert.notEqual(playerNameError(value), "", value);
  }
  for (const value of ["Owen-AP_1", " Owen ", "a".repeat(16)])
    assert.equal(playerNameError(value), "");
});

test("seed validation handles zero and both sides of the 64-bit boundary without precision loss", () => {
  for (const value of ["0", "000", "18446744073709551615"])
    assert.equal(validSeed(value), true);
  for (const value of [
    "",
    "-1",
    "1.5",
    "１２",
    "1;calc",
    "18446744073709551616",
    "0".repeat(21),
  ])
    assert.equal(validSeed(value), false);
});
