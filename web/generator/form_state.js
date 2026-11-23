// Draft choices belong to the form. Canonical previews never overwrite them.
export class DraftConfiguration {
  options = {};
  result = null;
  revision = 0;

  invalidate() {
    this.result = null;
    this.revision += 1;
  }

  selectPreset(values) {
    this.options = structuredClone(values);
    this.invalidate();
  }

  edit(name, value) {
    this.options[name] = value;
    this.invalidate();
  }

  accept(revision, result) {
    if (revision !== this.revision) return false;
    this.result = result;
    return true;
  }
}

export function playerNameError(value) {
  if (!/^[A-Za-z0-9_ -]{1,16}$/.test(value) || !value.trim()) {
    return "Use a player name of 1–16 letters, numbers, spaces, underscores or hyphens.";
  }
  return value.trim().toLowerCase() === "archipelago"
    ? "Player name Archipelago is reserved for the server."
    : "";
}

export function validSeed(value) {
  return /^\d{1,20}$/.test(value) && BigInt(value) <= 18446744073709551615n;
}

export function rewardQuantityState(definition, options) {
  const value = options[definition.key];
  const maximum = definition.maximum;
  const valid = Number.isSafeInteger(value) && value >= 0 && value <= maximum;
  return {
    value,
    valid,
    maximum,
    sliderMaximum: Math.max(definition.suggested_max, valid ? value : 0),
    enabled: options.reward_quantities === 1 &&
      (!definition.category || options[definition.category] === 1),
  };
}
