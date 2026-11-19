import {
  $,
  categoryOptions,
  loadoutOptions,
  assumptionOptions,
  showRoster,
  showSummary,
} from "/ui.js";

let metadata,
  options,
  assumptions,
  result = null,
  revision = 0,
  timer,
  generating = false;

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
    options,
    assumptions,
    name: $("player").value,
    seed: $("seed").value,
  };
}

function enableActions() {
  const nameValid =
    /^[A-Za-z0-9_ -]{1,16}$/.test($("player").value) &&
    $("player").value.trim();
  const seed = $("seed").value;
  const seedValid =
    /^\d{1,20}$/.test(seed) && BigInt(seed) <= 18446744073709551615n;
  $("export").disabled = !result || !nameValid || generating;
  $("generate").disabled = !result || !nameValid || !seedValid || generating;
  if (result) {
    $("validation").className = "validation";
    $("validation").textContent = !nameValid
      ? "Use a player name of 1–16 letters, numbers, spaces, underscores or hyphens."
      : !seedValid
        ? "Enter a seed from 0 to 18446744073709551615."
        : "Configuration valid. Ready to generate.";
  }
}

async function refresh(expected) {
  try {
    const response = await request("/api/preview", body());
    const data = await response.json();
    if (expected !== revision) return;
    result = data;
    options = data.configuration;
    document.querySelectorAll("#gear-options select").forEach((node) => {
      node.value = options[node.dataset.option];
    });
    $("connection").textContent =
      "Connected to your local Archipelago planner.";
    enableActions();
  } catch (error) {
    if (expected !== revision) return;
    result = null;
    $("validation").className = "validation error";
    $("validation").textContent = error.message;
    enableActions();
  }
  showSummary(result, metadata, options);
  showRoster(result, metadata);
}

function schedule() {
  clearTimeout(timer);
  revision += 1;
  result = null;
  enableActions();
  $("validation").textContent = "Checking settings…";
  $("preset-status").textContent = "Custom configuration";
  const current = revision;
  timer = setTimeout(() => refresh(current), 150);
}

function changeOption(key, value) {
  options[key] = value;
  schedule();
}

function loadPreset() {
  options = structuredClone(metadata.presets[$("preset").value]);
  categoryOptions("check-options", metadata.checks, options, changeOption);
  categoryOptions("reward-options", metadata.rewards, options, changeOption);
  loadoutOptions(metadata, options, changeOption);
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
  $("search").addEventListener("input", () => showRoster(result, metadata));
  $("roster-kind").addEventListener("change", () =>
    showRoster(result, metadata),
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
    $("preset").value = "mvp";
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
