import {
  $,
  categoryOptions,
  loadoutOptions,
  assumptionOptions,
  showRoster,
  showSummary,
  advancedOptions,
  syncAdvanced,
} from "./ui.js";
import {
  DraftConfiguration,
  playerNameError,
  validSeed,
} from "./form_state.js";

let metadata,
  assumptions,
  timer,
  generating = false;
const form = new DraftConfiguration();

async function request(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.error || `Request failed (${response.status})`);
  }
  return response;
}

function body() {
  return {
    options: form.options,
    assumptions,
    name: $("player").value,
    seed: $("seed").value,
  };
}

function enableActions() {
  const nameError = playerNameError($("player").value);
  const seedValid = validSeed($("seed").value);
  $("export").disabled = !form.result || nameError || generating;
  $("generate").disabled =
    !form.result || nameError || !seedValid || generating;
  if (form.result) {
    $("validation").className = "validation";
    $("validation").textContent = nameError
      ? nameError
      : !seedValid
        ? "Enter a seed from 0 to 18446744073709551615."
        : "Configuration valid. Ready to generate.";
  }
}

async function refresh(expected) {
  try {
    const response = await request("/api/preview", body());
    const data = await response.json();
    if (!form.accept(expected, data)) return;
    renderGear();
    $("connection").textContent =
      "Connected to your local Archipelago planner.";
    enableActions();
  } catch (error) {
    if (expected !== form.revision) return;
    form.result = null;
    if (error instanceof TypeError) {
      $("connection").textContent =
        "Local planner is unavailable. Restart it, then change a setting to retry.";
    }
    $("validation").className = "validation error";
    $("validation").textContent = error.message;
    enableActions();
  }
  showSummary(form.result, metadata, form.options);
  showRoster(form.result, metadata);
}

function schedule() {
  clearTimeout(timer);
  enableActions();
  $("validation").textContent = "Checking settings…";
  $("preset-status").textContent = "Custom configuration";
  showSummary(null, metadata, form.options);
  showRoster(null, metadata);
  const current = form.revision;
  timer = setTimeout(() => refresh(current), 150);
}

function changeOption(key, value) {
  form.edit(key, value);
  renderGear();
  schedule();
}

function renderGear() {
  syncAdvanced(form.options);
  document.querySelectorAll("#gear-options select").forEach((node) => {
    const key = node.dataset.option;
    const overridden =
      Boolean(form.options.no_starting_weapons) &&
      ["starting_firearms", "starting_melee"].includes(key);
    node.value = overridden
      ? Math.max(1, form.options[key])
      : form.options[key];
    node.disabled = overridden;
  });
}

function loadPreset() {
  form.selectPreset(metadata.presets[$("preset").value]);
  const options = form.options;
  categoryOptions("check-options", metadata.checks, options, changeOption);
  categoryOptions("reward-options", metadata.rewards, options, changeOption);
  loadoutOptions(metadata, options, changeOption);
  advancedOptions(metadata, options, changeOption);
  renderGear();
  $("goal").value = options.goal;
  $("kill-milestones").value = options.kill_milestones.join(", ");
  $("task-milestones").value = options.side_task_milestones.join(", ");
  $("no-weapons").checked = options.no_starting_weapons === 1;
  $("unlock-travel").checked = options.zone_unlock_travel === 1;
  schedule();
  $("preset-status").textContent = "Preset configuration";
}

async function download(path) {
  const snapshot = structuredClone(body());
  generating = true;
  enableActions();
  $("generation-status").textContent = path.endsWith("generate")
    ? "Generating with Archipelago… This can take up to three minutes. Keep this tab open."
    : "Preparing your player YAML…";
  try {
    const response = await request(path, snapshot);
    const blob = await response.blob();
    const filename =
      response.headers
        .get("Content-Disposition")
        ?.match(/filename="([^"]+)"/)?.[1] ?? "gamma-download.zip";
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    $("generation-status").textContent =
      `Downloaded ${filename}. ${path.endsWith("generate") ? "The ZIP contains the seed and spoiler. No game or server was started." : "Add it to an Archipelago player-files folder to generate a session."}`;
  } catch (error) {
    $("generation-status").textContent = error.message;
  } finally {
    generating = false;
    enableActions();
  }
}

function bindControls() {
  $("discovery-exclusions").addEventListener("change", () =>
    changeOption(
      "discovery_exclusions",
      Array.from($("discovery-exclusions").selectedOptions, (node) => node.value),
    ),
  );
  $("preset").addEventListener("change", loadPreset);
  $("goal").addEventListener("change", () =>
    changeOption("goal", Number($("goal").value)),
  );
  $("no-weapons").addEventListener("change", () =>
    changeOption("no_starting_weapons", Number($("no-weapons").checked)),
  );
  $("unlock-travel").addEventListener("change", () =>
    changeOption("zone_unlock_travel", Number($("unlock-travel").checked)),
  );
  for (const [id, key] of [
    ["kill-milestones", "kill_milestones"],
    ["task-milestones", "side_task_milestones"],
  ]) {
    $(id).addEventListener("input", () => {
      const parts = $(id)
        .value.split(",")
        .map((value) => value.trim());
      changeOption(
        key,
        parts.every((value) => /^\d+$/.test(value)) ? parts.map(Number) : [],
      );
    });
  }
  ["player", "seed"].forEach((id) =>
    $(id).addEventListener("input", enableActions),
  );
  $("random-seed").addEventListener("click", () => {
    $("seed").value = String(crypto.getRandomValues(new Uint32Array(1))[0]);
    enableActions();
  });
  $("search").addEventListener("input", () =>
    showRoster(form.result, metadata),
  );
  $("roster-kind").addEventListener("change", () =>
    showRoster(form.result, metadata),
  );
  $("export").addEventListener("click", () => download("/api/yaml"));
  $("generate").addEventListener("click", () => download("/api/generate"));
  const tabs = [...document.querySelectorAll("[data-tab]")];
  tabs.forEach((button, index) => {
    button.addEventListener("click", () => {
      tabs.forEach((tab) => {
        const selected = tab === button;
        tab.setAttribute("aria-selected", String(selected));
        tab.tabIndex = selected ? 0 : -1;
        $(`${tab.dataset.tab}-pane`).hidden = !selected;
      });
    });
    button.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key))
        return;
      event.preventDefault();
      const next =
        event.key === "Home"
          ? 0
          : event.key === "End"
            ? tabs.length - 1
            : (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) %
              tabs.length;
      tabs[next].click();
      tabs[next].focus();
    });
    button.tabIndex = index === 0 ? 0 : -1;
  });
}

async function start() {
  try {
    const response = await fetch("/api/metadata");
    if (!response.ok) throw new Error("Planner could not load its catalogue.");
    metadata = await response.json();
    Object.keys(metadata.presets).forEach((name) =>
      $("preset").add(
        new Option(
          name.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase()),
          name,
        ),
      ),
    );
    $("preset").value = "standard";
    metadata.goals.forEach((row) =>
      $("goal").add(new Option(row.label, row.value)),
    );
    assumptions = Object.fromEntries(
      Object.entries(metadata.assumptions).map(([key, value]) => [
        key,
        value.default,
      ]),
    );
    assumptionOptions(metadata.assumptions, assumptions, (key, value) => {
      assumptions[key] = value;
      form.invalidate();
      schedule();
    });
    bindControls();
    loadPreset();
  } catch (error) {
    $("connection").textContent =
      `Could not connect: ${error.message} Start tools/run_generator_web.py and open its local address.`;
  }
}

start();
