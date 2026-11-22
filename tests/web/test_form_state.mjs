import test from "node:test";
import assert from "node:assert/strict";
import { advancedOptions, syncAdvanced, rewardQuantityOptions, showStepReport, loadoutOptions } from "../../web/generator/ui.js";
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

test("quota exclusions and custom thresholds remain draft choices when profiles resolve previews", () => {
  const preset={discovery_exclusions:["mutant:dog"],kill_milestones:[10,25],grind_profile:0};
  const form=new DraftConfiguration();
  form.selectPreset(preset);
  form.options.discovery_exclusions.push("faction:stalker");
  form.edit("grind_profile",1);
  assert.equal(form.accept(form.revision,{configuration:{kill_milestones:[5,15,30]}}),true);
  assert.deepEqual(form.options.kill_milestones,[10,25]);
  assert.deepEqual(preset.discovery_exclusions,["mutant:dog"]);
  form.edit("grind_profile",0);
  assert.deepEqual(form.options.kill_milestones,[10,25]);
});

test("advanced controls have labels, bounded values and preserve editable quota state", () => {
  const oldDocument = globalThis.document;
  const oldOption = globalThis.Option;
  const nodes = new Map();
  const makeNode = () => ({
    dataset: {}, attributes: {}, listeners: {}, children: [],
    append(...children) { this.children.push(...children); },
    add(child) { this.children.push(child); },
    replaceChildren(...children) { this.children = children; },
    setAttribute(key, value) { this.attributes[key] = value; },
    addEventListener(key, value) { this.listeners[key] = value; },
  });
  for (const id of ["advanced-options", "discovery-exclusions", "kill-milestones", "task-milestones"])
    nodes.set(id, makeNode());
  globalThis.document = {
    createElement: makeNode,
    getElementById: (id) => nodes.get(id),
    querySelectorAll: () => nodes.get("advanced-options").children.map((row) => row.children[0]),
  };
  globalThis.Option = class { constructor(text, value) { this.text = text; this.value = value; } };
  try {
    const options = {mutant_discovery_mode: 0, mutant_discovery_count: 15,
      grind_profile: 1, discovery_exclusions: ["mutant:dog"]};
    const edits = [];
    advancedOptions({advanced: [
      {key: "mutant_discovery_mode", label: "Mutant discovery mode", choices: ["Per type", "First N"]},
      {key: "mutant_discovery_count", label: "Mutant discovery count", maximum: 25},
    ], discovery_types: [{token: "mutant:dog"}]}, options, (...edit) => edits.push(edit));
    const [mode, count] = document.querySelectorAll("[data-advanced]");
    assert.equal(mode.attributes["aria-label"], "Mutant discovery mode");
    assert.equal(count.attributes["aria-label"], "Mutant discovery count");
    assert.equal(count.max, 25);
    syncAdvanced(options);
    assert.equal(count.disabled, true);
    assert.equal(nodes.get("task-milestones").disabled, true);
    syncAdvanced({...options, mutant_discovery_mode: 1, grind_profile: 0});
    assert.equal(count.disabled, false);
    assert.equal(count.value, 15);
    assert.equal(nodes.get("task-milestones").disabled, false);
    count.value = "12"; count.listeners.change();
    count.value = ""; count.listeners.change();
    assert.deepEqual(edits, [["mutant_discovery_count", 12], ["mutant_discovery_count", null]]);
    assert.equal(nodes.get("discovery-exclusions").children[0].selected, true);
  } finally {
    globalThis.document = oldDocument;
    globalThis.Option = oldOption;
  }
});

test("class loadout controls replace binary groups and allow a zero-class start", () => {
  const previous = globalThis.document, oldOption = globalThis.Option;
  const nodes = new Map();
  const makeNode = () => ({dataset:{},children:[],listeners:{},
    append(...children) {this.children.push(...children);},
    add(child) {this.children.push(child);},
    replaceChildren(...children) {this.children=children;},
    addEventListener(key,fn) {this.listeners[key]=fn;}});
  for (const id of ["gear-options","quantity-options"]) nodes.set(id,makeNode());
  globalThis.document = {getElementById:(id)=>nodes.get(id),createElement:makeNode};
  globalThis.Option = class {constructor(text,value) {this.text=text;this.value=value;}};
  try {
    const metadata={gear:["starting_pda","starting_firearms","starting_melee","starting_tools"],quantities:[],
      advanced:[{key:"initial_firearm_class",label:"Initial firearm class",choices:["None","A","B","C","D"]}]};
    const edits=[];
    loadoutOptions(metadata,{equipment_class_progression:1,rewards_starting_gear_unlocks:1,
      starting_pda:2,initial_firearm_class:1},(...edit)=>edits.push(edit));
    const controls=nodes.get("gear-options").children.flatMap(row=>row.children);
    assert.deepEqual(controls.map(node=>node.dataset.option),["starting_pda","initial_firearm_class"]);
    const classes=controls[1];
    assert.equal(classes.children[0].text,"None");
    classes.value="0"; classes.listeners.change();
    assert.deepEqual(edits,[["initial_firearm_class",0]]);
    loadoutOptions(metadata,{equipment_class_progression:0},()=>{});
    assert.equal(nodes.get("gear-options").children.length,4);
    loadoutOptions(metadata,{equipment_class_progression:1,rewards_starting_gear_unlocks:0},()=>{});
    assert.equal(nodes.get("gear-options").children[1].children[0].disabled,true);
  } finally {globalThis.document=previous;globalThis.Option=oldOption;}
});


test("reward quantity numeric entry can exceed the suggested slider range", () => {
  const previous = globalThis.document;
  const container = {children: [], replaceChildren(...children) {this.children = children;}};
  globalThis.document = {
    getElementById: () => container,
    createElement: () => ({children: [], listeners: {},
      append(...nodes) {this.children.push(...nodes);},
      setAttribute() {}, addEventListener(key, fn) {this.listeners[key] = fn;}}),
  };
  try {
    const edits = [];
    rewardQuantityOptions({reward_quantities: [{key:"medical_packages",label:"Medical",suggested_max:50}]},
      {medical_packages:4}, (...edit) => edits.push(edit));
    const [, slider, number] = container.children[0].children;
    assert.equal(number.max, undefined);
    number.value="72"; number.listeners.input();
    assert.equal(slider.max,72); assert.equal(slider.value,72);
    slider.value="20"; slider.listeners.input();
    assert.equal(number.value,20); assert.equal(slider.max,50);
    number.value=""; number.listeners.input();
    assert.deepEqual(edits, [["medical_packages",72],["medical_packages",20],["medical_packages",null]]);
  } finally {globalThis.document=previous;}
});

test("step report shows separate paced and logical lists using safe text", () => {
  const previous = globalThis.document;
  const node = () => ({children: [], append(...children) {this.children.push(...children);},
    replaceChildren(...children) {this.children=children;}});
  const container=node();
  globalThis.document={getElementById:()=>container,createElement:node};
  try {
    assert.throws(()=>showStepReport({}), /actual GAMMA/);
    const analysis={steps:[{step:1,checks:1,local_events:[],available_checks:[{location:"<img>",item:"PDA",recipient:1}]}],
      goal_step:1,unreachable_checks:0,time_estimate:"Uncalibrated"};
    showStepReport({kind:"actual_generated_seed",paced_steps:analysis,logical_spheres:analysis});
    assert.equal(container.children.filter(n=>n.textContent==="Paced steps: one tier per chain").length,1);
    assert.equal(container.children[2].children[1].children[0].textContent,"<img> -> PDA (player 1)");
    delete analysis.steps[0].available_checks;
    showStepReport({kind:"actual_generated_seed",paced_steps:analysis,logical_spheres:analysis});
    assert.match(container.children[2].children[1].children[0].textContent,/spoilers/);
  } finally {globalThis.document=previous;}
});
