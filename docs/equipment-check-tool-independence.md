# Equipment checks without repair tools

Weapon-role, firearm repair-class, armour-tier and knife-tier checks observe usable
gear, not the act of repairing it. Starting equipment, trader purchases and loot
may already meet the configured condition threshold. Neither generation rules,
PDA availability nor the native observer therefore requires Basic, Advanced or
Expert tools for these checks.

The default 65% threshold remains. In class-based GAMMA sessions firearm checks
read the average condition of required weapon parts, rather than the engine's
forced body condition. Class permissions, skipped-tier credit and independent
regional requirements remain in effect. A tool reward can be placed on an
equipment check when its remaining access requirements are satisfied.

This change does not remove tools from the pool or unlock native toolkit use.
Repair/crafting permissions, checks for installing upgrades, story readiness and
high mutant-diversity readiness retain their existing requirements. Retired
catalogue mappings `armour_tools` and `knife_tools` are retained for older bundle
readers but are no longer consumed by current equipment-check rules.

IDs, wire configuration, receipt order and saved completed checks are unchanged.
Already generated archives retain their original placements and server-side
logic; deploying a matching updated add-on can relax the local observer without
rerolling rewards. This PR does not deploy, switch the running multiworld, write
saves, change the local developer panel or touch the normal installation.

Regressions cover starting pistol/SMG and purchased knife access with no tool
reward, class permissions independently of tools, all equipment categories in
legacy/named/generic tool configurations, native condition boundaries, skipped
tiers, PDA availability, preserved upgrade gates, and generation reachability.
Native engine acceptance remains reserved for Owen.
