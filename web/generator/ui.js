export const $ = (id) => document.getElementById(id);
export const title = (key) =>
  key
    .replace(/^starting_/, "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace("Pda", "PDA");
export const range = (values) => `${values[0]}–${values[1]} h`;

export function element(tag, text = "", className = "") {
  const node = document.createElement(tag);
  node.textContent = text;
  node.className = className;
  return node;
}

export function categoryOptions(container, definitions, options, change) {
  $(container).replaceChildren(
    ...definitions.map(({ key, label, count }) => {
      const row = element("label", "", "option");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.checked = options[key] === 1;
      input.dataset.option = key;
      input.addEventListener("change", () =>
        change(key, Number(input.checked)),
      );
      const badge = element("em", String(count));
      badge.dataset.count = key;
      row.append(input, element("span", label), badge);
      return row;
    }),
  );
}

export function loadoutOptions(metadata, options, change) {
  const classes = options.equipment_class_progression === 1;
  const classGroups = new Set(["starting_firearms", "starting_outfit", "starting_helmet", "starting_backpack"]);
  $("gear-options").replaceChildren(
    ...metadata.gear.filter((key) => !classes ||
      (!classGroups.has(key) && key !== "starting_melee" && key !== "starting_tools")).map((key) => {
      const label = element("label", title(key));
      const select = document.createElement("select");
      select.dataset.option = key;
      ["Normal starting gear", "Absent at start", "AP equip/use lock"].forEach(
        (name, index) => {
          select.add(new Option(name, index));
        },
      );
      select.value = options[key];
      select.addEventListener("change", () =>
        change(key, Number(select.value)),
      );
      label.append(select);
      return label;
    }),
    ...(classes ? metadata.advanced.filter(({key}) => /^initial_.*_class$/.test(key)).map(({key,label,choices}) => {
      const row = element("label", label);
      const select = document.createElement("select");
      select.dataset.option = key;
      choices.forEach((text,index) => select.add(new Option(text,index)));
      select.value = options[key];
      select.disabled = options.rewards_starting_gear_unlocks !== 1;
      select.addEventListener("change", () => change(key,Number(select.value)));
      row.append(select);
      return row;
    }) : []),
    ...(classes ? [element("p", "Knife use is always allowed. A missing starter knife and each permitted backpack tier are supplied free.")] : []),
  );
  $("quantity-options").replaceChildren(
    ...metadata.quantities.map((key) => {
      const label = element(
        "label",
        `Starting ${title(key).toLowerCase()} (%)`,
      );
      const input = document.createElement("input");
      input.type = "number";
      input.min = 0;
      input.max = 100;
      input.step = 1;
      input.dataset.option = key;
      input.value = options[key];
      input.addEventListener("input", () =>
        change(key, input.value === "" ? null : Number(input.value)),
      );
      label.append(input);
      return label;
    }),
  );
}

export function advancedOptions(metadata, options, change) {
  $("advanced-options").replaceChildren(
    ...metadata.advanced.filter(({key}) => !options.equipment_class_progression || !/^initial_.*_class$/.test(key)).map(({ key, label, maximum, choices }) => {
      const row = element("label", label);
      const input = document.createElement(choices ? "select" : "input");
      input.setAttribute("aria-label", label);
      if (choices) {
        choices.forEach((text, index) => input.add(new Option(text, index)));
      } else {
        input.type = "number";
        input.min = 0;
        input.max = maximum;
        input.step = 1;
      }
      input.dataset.option = key;
      input.dataset.advanced = "true";
      input.value = options[key];
      input.addEventListener("change", () =>
        change(key, input.value === "" ? null : Number(input.value)),
      );
      row.append(input);
      return row;
    }),
  );
  $("discovery-exclusions").replaceChildren(
    ...metadata.discovery_types.map(({ token }) => {
      const option = new Option(token.replaceAll("_", " "), token);
      option.selected = options.discovery_exclusions.includes(token);
      return option;
    }),
  );
}

export function syncAdvanced(options) {
  document.querySelectorAll("[data-advanced]").forEach((node) => {
    node.value = options[node.dataset.option];
    const match = node.dataset.option.match(/^(mutant|faction|artefact)_discovery_count$/);
    node.disabled = Boolean(match) && options[`${match[1]}_discovery_mode`] === 0;
  });
  $("kill-milestones").disabled = options.grind_profile > 0;
  $("task-milestones").disabled = options.grind_profile > 0;
}

const assumptionLabels = {
  pace_percent: ["Time multiplier", "%"],
  map_minutes: ["Travel per map", "min"],
  task_minutes: ["Time per task", "min"],
  artefact_minutes: ["Time per artefact", "min"],
  kills_per_hour: ["Kills per hour", "/ h"],
  session_hours: ["Session length", "h"],
  multiworld_wait_minutes: ["Extra multiworld waiting", "min"],
};

export function assumptionOptions(definitions, values, change) {
  $("assumption-options").replaceChildren(
    ...Object.entries(definitions).map(([key, rule]) => {
      const label = element("label", "", "assumption-field");
      const top = element("span", "", "range-label");
      const [name, unit] = assumptionLabels[key];
      const output = element("output", `${values[key]} ${unit}`);
      const input = document.createElement("input");
      input.id = `assumption-${key}`;
      input.type = "range";
      input.setAttribute("aria-label", name);
      input.min = rule.minimum;
      input.max = rule.maximum;
      input.step = 1;
      input.value = values[key];
      output.htmlFor = input.id;
      top.append(element("span", name), output);
      label.append(top, input);
      input.addEventListener("input", () => {
        output.textContent = `${input.value} ${unit}`;
        change(key, Number(input.value));
      });
      return label;
    }),
  );
}

export function showRoster(result, metadata) {
  const kind = $("roster-kind").value;
  const search = $("search").value.toLocaleLowerCase().trim();
  const labels = Object.fromEntries(
    [...metadata.checks, ...metadata.rewards].map((row) => [
      row.key,
      row.label,
    ]),
  );
  const rows = (result?.[kind] ?? [])
    .map((row) => ({
      name: row.name,
      category: labels[row.category] ?? "Base supplies",
      detail:
        kind === "checks"
          ? (metadata.levels[row.level] ?? "Any region") +
            (Number.isInteger(row.price) ? ` · ${row.price.toLocaleString()} RU` : "")
          : title(row.classification),
    }))
    .filter((row) =>
      Object.values(row).some((value) =>
        value.toLocaleLowerCase().includes(search),
      ),
    );
  $("detail-heading").textContent =
    kind === "checks" ? "Region / cost" : "Classification";
  $("roster-count").textContent = `${rows.length} shown`;
  $("roster").replaceChildren(
    ...rows.map((row) => {
      const tr = document.createElement("tr");
      tr.append(
        element("td", row.name),
        element("td", row.category),
        element("td", row.detail),
      );
      return tr;
    }),
  );
  if (!rows.length) {
    const cell = element(
      "td",
      result
        ? "No matching entries. Try another search."
        : "Fix the configuration to inspect its catalogue.",
    );
    cell.colSpan = 3;
    const tr = document.createElement("tr");
    tr.append(cell);
    $("roster").append(tr);
  }
}

export function showSummary(result, metadata, options) {
  $("budget-preview").textContent = result ? JSON.stringify({
    kind:result.preview_kind, budget:result.pool_budget,
    opening_permissions:result.opening_permissions, thresholds:result.resolved_thresholds,
    discovery:result.discovery_rosters, notes:result.notes,
  },null,2) : "Fix the configuration to calculate its budget.";
  const goal = metadata.goals.find((row) => row.value === Number(options.goal));
  $("goal-summary").textContent = goal.label;
  $("summary-copy").textContent =
    "Independent categories. One connected adventure.";
  $("check-total").textContent = result?.network_checks ?? "—";
  $("reward-total").textContent = result?.reward_types ?? "—";
  $("required-total").textContent = result
    ? `${result.required_rewards} required progression items`
    : "Check configuration below";
  $("slots-summary").textContent = result?.reward_slots ?? "—";
  $("progression-summary").textContent = result?.required_rewards ?? "—";
  $("time-total").textContent = result
    ? range(result.estimates.goal_hours)
    : "—";
  $("goal-range").textContent = result
    ? range(result.estimates.goal_hours)
    : "—";
  $("completion-range").textContent = result
    ? range(result.estimates.completion_hours)
    : "—";
  $("sessions-summary").textContent = result
    ? result.estimates.sessions.join("–")
    : "—";
  $("session-copy").textContent = result
    ? `At ${result.estimates.assumptions.session_hours} hours per session. Lower multipliers mean a faster run.`
    : "Estimate unavailable for invalid settings.";
  $("estimate-method").textContent =
    result?.estimates.method ?? "Fix settings to calculate an estimate.";
  $("breakdown").replaceChildren(
    ...Object.entries(result?.estimates.breakdown_hours ?? {}).map(
      ([key, value]) => {
        const row = element("div", "", "breakdown-row");
        row.append(element("span", title(key)), element("span", `${value} h`));
        return row;
      },
    ),
  );
  document.querySelectorAll("[data-count]").forEach((node) => {
    const key = node.dataset.count;
    const definition = [...metadata.checks, ...metadata.rewards].find(
      (row) => row.key === key,
    );
    node.textContent =
      result?.check_counts[key] ??
      result?.reward_counts[key] ??
      definition.count;
  });
}


export function rewardQuantityOptions(metadata, options, change) {
  $("reward-quantities").replaceChildren(...metadata.reward_quantities.map(
    ({key, label, suggested_max}) => {
      const row = element("label", "", "assumption-field");
      row.append(element("span", `${label} - suggested 0-${suggested_max}`));
      const slider = document.createElement("input");
      const number = document.createElement("input");
      slider.type = "range"; number.type = "number";
      slider.min = number.min = 0;
      slider.step = number.step = 1;
      slider.max = Math.max(suggested_max, options[key]);
      slider.value = number.value = options[key];
      slider.setAttribute("aria-label", label + " slider");
      number.setAttribute("aria-label", label + " exact count");
      const update = (value) => {
        slider.max = Math.max(suggested_max, value ?? 0);
        if (value !== null && Number.isFinite(value)) slider.value = value;
        number.value = value ?? "";
        change(key, value);
      };
      slider.addEventListener("input", () => update(Number(slider.value)));
      number.addEventListener("input", () => update(number.value === "" ? null : Number(number.value)));
      row.append(slider, number);
      return row;
    }));
}

export function showStepReport(report) {
  if (report?.kind !== "actual_generated_seed" || !report.paced_steps || !report.logical_spheres)
    throw new Error("Choose an actual GAMMA seed preview JSON with step analysis.");
  const container = $("step-report");
  container.replaceChildren();
  for (const [label, analysis] of [["AP progression: one tier per chain per step", report.paced_steps],
                                  ["Raw Archipelago logical spheres (unpaced)", report.logical_spheres]]) {
    container.append(element("h3", label));
    container.append(element("p", `${analysis.steps.length} steps - goal at step ${analysis.goal_step ?? "unreachable"} - ${analysis.unreachable_checks} unreachable checks. ${analysis.time_estimate}`));
    for (const step of analysis.steps) {
      const details = element("details");
      details.append(element("summary", `Step ${step.step}: ${step.checks} newly available checks`));
      const list = element("ul");
      for (const check of step.available_checks ?? [])
        list.append(element("li", `${check.location} -> ${check.item} (player ${check.recipient})`));
      if (!step.available_checks)
        list.append(element("li", "Names and rewards require a seed report with placement spoilers."));
      for (const event of step.local_events) list.append(element("li", `Local event: ${event}`));
      if (step.deferred_reward_count)
        list.append(element("li", `${step.deferred_reward_count} progressive rewards wait for later steps (one tier per chain per step).${step.deferred_rewards ? " " + step.deferred_rewards.join(", ") : ""}`));
      details.append(list); container.append(details);
    }
  }
}
