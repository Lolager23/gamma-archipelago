import { $, element } from "./ui.js";
import { rewardQuantityState } from "./form_state.js";

const groups = [
  ["Supplies for the journey", ["rewards_supply_medical", "rewards_supply_maintenance", "rewards_supply_ammunition", "rewards_supply_expedition"]],
  ["Stashes & artefacts", ["rewards_loot_stashes", "rewards_progression_stashes", "rewards_artefacts"]],
  ["Progression & access", ["rewards_starting_gear_unlocks", "rewards_zone_keys", "rewards_quest_keys", "rewards_progressive_tools", "rewards_workshop_access", "rewards_recipe_access", "rewards_drug_making_tools", "rewards_gunsmithing_tools", "rewards_artefact_melter"]],
  ["Faction, skills & carry", ["rewards_faction_reputation", "rewards_stat_levels", "rewards_convenience"]],
];
const policies = [
  ["reward_quantities", "Reserve repeatable copies", "Set guaranteed quantities below. Progression minima are calculated first."],
  ["varied_filler", "Varied spare-slot rewards", "Fill the remaining slots with enabled supplies and stashes."],
  ["randomized_stash_loot", "Varied stash contents", "Mix quantities and loot within each tier and calibre. Reloading keeps the assigned contents."],
];

function toggle(key, text, options, change) {
  const label = element("label", "", "reward-toggle");
  const input = document.createElement("input");
  input.type = "checkbox";
  input.dataset.option = key;
  input.checked = options[key] === 1;
  input.addEventListener("change", () => change(key, Number(input.checked)));
  label.append(input, element("span", text));
  return label;
}

function quantity(definition, options, change) {
  const row = element("div", "", "reward-quantity");
  const state = rewardQuantityState(definition, options);
  const name = element("label", definition.label);
  name.htmlFor = `reward-number-${definition.key}`;
  const pair = element("div", "", "reward-number-pair");
  const slider = document.createElement("input");
  const number = document.createElement("input");
  slider.type = "range"; number.type = "number";
  slider.min = number.min = 0;
  slider.step = number.step = 1;
  slider.max = state.sliderMaximum; number.max = definition.maximum;
  slider.value = number.value = options[definition.key];
  slider.dataset.rewardSlider = number.dataset.rewardNumber = definition.key;
  slider.setAttribute("aria-label", `${definition.label} slider`);
  number.setAttribute("aria-label", `${definition.label} exact count`);
  number.id = name.htmlFor;
  number.inputMode = "numeric";
  const hint = element("small");
  hint.id = `reward-hint-${definition.key}`;
  hint.dataset.rewardHint = definition.key;
  number.setAttribute("aria-describedby", hint.id);
  const update = (value) => {
    // Keep the numeric draft even when invalid; preview validation owns rejection.
    if (Number.isSafeInteger(value) && value >= 0 && value <= definition.maximum) {
      slider.max = Math.max(Number(slider.max), definition.suggested_max, value);
      slider.value = value;
    }
    number.value = value ?? "";
    change(definition.key, value);
  };
  slider.addEventListener("input", () => update(Number(slider.value)));
  number.addEventListener("input", () => update(number.value === "" ? null : Number(number.value)));
  pair.append(slider, number);
  row.append(name, pair, hint);
  return row;
}

function category(definition, metadata, options, change) {
  const card = element("section", "", "reward-card");
  card.dataset.rewardCategory = definition.key;
  const header = element("div", "", "reward-card-header");
  header.append(toggle(definition.key, definition.label, options, change));
  const badge = element("span", String(definition.count), "reward-type-count");
  badge.dataset.count = definition.key;
  badge.title = "Eligible reward types; repeatable copies are configured below.";
  header.append(badge);
  const requirement = element("p", "Minimum copies follow your checks and starting permissions.", "reward-rule");
  requirement.dataset.requiredCategory = definition.key;
  card.append(header, requirement);
  for (const row of metadata.reward_quantities.filter((row) => row.category === definition.key))
    card.append(quantity(row, options, change));
  return card;
}

export function rewardControls(metadata, options, change) {
  const root = $("reward-workbench");
  root.replaceChildren();
  const policy = element("div", "", "reward-policies");
  for (const [key, label, description] of policies) {
    const row = element("div", "", "reward-policy");
    row.append(toggle(key, label, options, change), element("p", description));
    policy.append(row);
  }
  root.append(policy);
  const budget = element("div", "", "reward-budget");
  budget.id = "reward-budget-summary";
  budget.setAttribute("role", "status");
  root.append(budget);
  const known = new Set();
  const appendGroup = (label, definitions) => {
    if (!definitions.length) return;
    const group = element("section", "", "reward-group");
    group.append(element("h3", label));
    const cards = element("div", "", "reward-cards");
    for (const definition of definitions) {
      known.add(definition.key);
      cards.append(category(definition, metadata, options, change));
    }
    group.append(cards); root.append(group);
  };
  for (const [label, keys] of groups)
    appendGroup(label, keys.map((key) => metadata.rewards.find((row) => row.key === key)).filter(Boolean));
  appendGroup("Other rewards", metadata.rewards.filter((row) => !known.has(row.key)));
  const extra = element("details", "", "reward-extras");
  extra.append(element("summary", "Extra basic toolkits"));
  extra.append(element("p", "These are physical kits. Workshop and tool-use permissions remain separate.", "reward-rule"));
  for (const row of metadata.reward_quantities.filter((row) => !row.category))
    extra.append(quantity(row, options, change));
  root.append(extra);
  syncRewardControls(metadata, options, null);
}

export function syncRewardControls(metadata, options, result, error = "") {
  const root = $("reward-workbench");
  if (!root) return;
  root.querySelectorAll("input[type=checkbox]").forEach((node) => {
    node.checked = options[node.dataset.option] === 1;
  });
  root.querySelectorAll("[data-reward-category]").forEach((node) => {
    node.classList.toggle("reward-disabled", options[node.dataset.rewardCategory] !== 1);
  });
  for (const definition of metadata.reward_quantities) {
    const state = rewardQuantityState(definition, options);
    const number = root.querySelector(`[data-reward-number="${definition.key}"]`);
    const slider = root.querySelector(`[data-reward-slider="${definition.key}"]`);
    number.disabled = slider.disabled = !state.enabled;
    if (number !== document.activeElement) number.value = state.value ?? "";
    if (state.valid) {
      slider.max = Math.max(Number(slider.max), state.sliderMaximum);
      slider.value = state.value;
    }
    number.setAttribute("aria-invalid", String(!state.valid && state.enabled));
    root.querySelector(`[data-reward-hint="${definition.key}"]`).textContent = !state.enabled
      ? "Enable this category and repeatable quantities to reserve copies."
      : !state.valid ? `Enter a whole number from 0 to ${state.maximum.toLocaleString()}.`
      : `Suggested 0–${definition.suggested_max} · exact counts can be higher.`;
  }
  const budget = $("reward-budget-summary");
  if (!result) {
    budget.textContent = error ? `Reward budget unavailable: ${error}` :
      "Checking reward capacity… Required progression is always reserved first.";
    root.querySelectorAll("[data-required-category]").forEach((node) => {
      node.textContent = "Required copies will be recalculated.";
    });
    return;
  }
  const plan = result.pool_budget;
  const extras = Object.values(plan.guaranteed_useful).reduce((sum, count) => sum + count, 0);
  budget.textContent = `${plan.required_copies} required + ${extras} requested / convenience + ${plan.filler_slots} spare = ${plan.network_checks} checks. ` +
    (options.reward_quantities === 0 ? "Weighted optional mode: exact counts are inactive." :
      options.varied_filler === 1 ? `${result.filler_choices.length} enabled spare-slot reward types.` : "Spare slots use legacy basic supplies.");
  const categories = new Map(result.rewards.map((row) => [row.name, row.category]));
  root.querySelectorAll("[data-required-category]").forEach((node) => {
    const key = node.dataset.requiredCategory;
    const count = Object.entries(plan.required_progression).reduce((sum, [name, copies]) => sum + (categories.get(name) === key ? copies : 0), 0);
    const adjustable = metadata.reward_quantities.some((row) => row.category === key);
    node.textContent = count ? `${count} required ${count === 1 ? "copy" : "copies"}, calculated automatically.${adjustable ? " Quantities below add extra copies." : ""}` :
      adjustable ? "Choose guaranteed copies. Extra supplies may also appear in spare slots." : "Copies are calculated from your enabled checks and starting settings.";
  });
}
