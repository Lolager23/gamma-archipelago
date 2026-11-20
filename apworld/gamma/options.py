"""Generation options; feature adapters declare availability as they are implemented."""

from dataclasses import dataclass

from Options import (
    Choice,
    DefaultOnToggle,
    OptionList,
    OptionSet,
    PerGameCommonOptions,
    Range,
    StartInventoryPool,
    Toggle,
)


class ChecksMaps(DefaultOnToggle):
    """Enable maps checks."""

    display_name = "Checks: Maps"


class ChecksSettlements(Toggle):
    """Enable settlements checks."""

    display_name = "Checks: Settlements"


class ChecksMutantFirstKills(Toggle):
    """Enable mutant first kills checks."""

    display_name = "Checks: Mutant First Kills"


class ChecksFactionFirstKills(Toggle):
    """Enable faction first kills checks."""

    display_name = "Checks: Faction First Kills"


class ChecksArtefacts(Toggle):
    """Enable artefacts checks."""

    display_name = "Checks: Artefacts"


class ChecksQuestTypes(Toggle):
    """Enable quest types checks."""

    display_name = "Checks: Quest Types"


class ChecksGearUpgrades(Toggle):
    """Enable gear upgrades checks."""

    display_name = "Checks: Gear Upgrades"


class ChecksArmourTiers(Toggle):
    """Enable armour tiers checks."""

    display_name = "Checks: Armour Tiers"


class ChecksWeaponTiers(Toggle):
    """Enable weapon tiers checks."""

    display_name = "Checks: Weapon Tiers"


class ChecksKnifeTiers(Toggle):
    """Enable knife tiers checks."""

    display_name = "Checks: Knife Tiers"


class ChecksKillMilestones(Toggle):
    """Enable kill milestones checks."""

    display_name = "Checks: Kill Milestones"


class ChecksSideTaskMilestones(Toggle):
    """Enable side task milestones checks."""

    display_name = "Checks: Side Task Milestones"


class ChecksStoryMilestones(Toggle):
    """Enable story milestones checks."""

    display_name = "Checks: Story Milestones"


class ChecksRankMilestones(Toggle):
    """Enable rank milestones checks."""

    display_name = "Checks: Rank Milestones"


class SupplyAmmoCalibre(Choice):
    """Choose the calibre for ammunition packages; ordinary native box sizes apply."""

    display_name = "Supply package ammunition calibre"
    option_9x18 = 0
    option_9x19 = 1
    option_545 = 2
    option_556 = 3
    option_762 = 4
    default = 0


class RewardsSupplyMedical(Toggle):
    """Enable bounded useful medical supply packages in the optional filler pool."""

    display_name = "rewards supply medical"


class RewardsSupplyMaintenance(Toggle):
    """Enable bounded useful maintenance supply packages in the optional filler pool."""

    display_name = "rewards supply maintenance"


class RewardsSupplyAmmunition(Toggle):
    """Enable bounded useful ammunition supply packages in the optional filler pool."""

    display_name = "rewards supply ammunition"


class RewardsSupplyExpedition(Toggle):
    """Enable bounded useful expedition supply packages in the optional filler pool."""

    display_name = "rewards supply expedition"


class RewardsConvenience(Toggle):
    """Up to three bounded carry-capacity rewards using the supported keyed weight API."""

    display_name = "Rewards: Convenience"


class OpeningPolicy(Choice):
    """Protect local Cordon equipment permissions, or retain legacy/challenge placement."""

    display_name = "Opening protection"
    option_legacy_or_challenge = 0
    option_protected = 1
    default = 0


class AccessPacing(Choice):
    """Existing randomized zone frontier, or prioritize reachable major hubs."""

    display_name = "Zone access pacing"
    option_random_frontier = 0
    option_hubs_first = 1
    default = 0


class CombatLogic(Choice):
    """Conservative AP permission assumptions; never a guarantee of native equipment condition."""

    display_name = "Combat readiness logic"
    option_any_weapon = 0
    option_firearm = 1
    option_firearm_and_protection = 2
    default = 0


class GrindProfile(Choice):
    """Resolve kill/side-task thresholds from a profile, or retain custom lists."""

    display_name = "Grind thresholds"
    option_custom = 0
    option_short = 1
    option_standard = 2
    option_extended = 3
    default = 0


class GenerationPreview(Choice):
    """Optional JSON report in the generated archive; placements explicitly reveal spoilers."""

    display_name = "Generation preview report"
    option_disabled = 0
    option_summary = 1
    option_spoiler_placements = 2
    default = 0


class PermissionSupplies(Toggle):
    """Attach one-time bounded supplies to supported permission receipts; default off."""

    display_name = "Permission plus supplies"


class RewardsWorkshopAccess(Toggle):
    """Separate AP permissions for repair, upgrades and crafting at supported native routes."""

    display_name = "Rewards: Workshop access"


class RewardsRecipeAccess(Toggle):
    """AP permission for general, medical, ammunition and artefact recipe groups."""

    display_name = "Rewards: Recipe access"


class RewardsProgressiveTools(Toggle):
    """Three progressive basic/advanced/expert workshop permissions; physical tools still apply."""

    display_name = "Rewards: Progressive tools"


class RewardsLootStashes(Toggle):
    """Enable loot stashes rewards."""

    display_name = "Rewards: Loot Stashes"


class RewardsProgressionStashes(Toggle):
    """Enable progression stashes rewards."""

    display_name = "Rewards: Progression Stashes"


class RewardsQuestKeys(Toggle):
    """Enable quest keys rewards."""

    display_name = "Rewards: Quest Keys"


class RewardsFactionReputation(Toggle):
    """Enable faction reputation rewards."""

    display_name = "Rewards: Faction Reputation"


class RewardsStatLevels(Toggle):
    """Enable stat levels rewards."""

    display_name = "Rewards: Stat Levels"


class RewardsZoneKeys(Toggle):
    """Enable zone keys rewards."""

    display_name = "Rewards: Zone Keys"


class RewardsStartingGearUnlocks(Toggle):
    """Enable starting gear unlocks rewards."""

    display_name = "Rewards: Starting Gear Unlocks"


class Goal(Choice):
    """Choose the actual completion condition. Unimplemented goals reject generation."""

    display_name = "Goal"
    option_pilot_tour = 0
    option_psi_protection = 1
    option_brain_scorcher = 2
    option_meet_strelok = 3
    option_living_legend = 4
    option_all_x_labs = 5
    default = 0


class StartingGear(Choice):
    """Normal equipment, absent initially, or unavailable until its AP unlock."""

    display_name = "Starting equipment mode"
    option_normal = 0
    option_absent = 1
    option_ap_locked = 2
    default = 0


class StartingQuantity(Range):
    """Percentage of ordinary starting supplies or money retained."""

    display_name = "Starting quantity percent"
    range_start = 0
    range_end = 100
    default = 100


class NoStartingWeapons(Toggle):
    """Omit both firearms and melee weapons unless individually AP-locked."""

    display_name = "No Starting Weapons"


class KillMilestones(OptionList):
    """Finite, strictly increasing cumulative kill thresholds."""

    display_name = "Kill milestones"
    default = [10, 25, 50, 100]


class SideTaskMilestones(OptionList):
    """Finite, strictly increasing completed side-task thresholds."""

    display_name = "Side-task milestones"
    default = [5, 10, 20, 40]


class ZoneUnlockTravel(Toggle):
    """Offer one optional settlement trip per zone key; never travel automatically."""

    display_name = "One-time travel after zone unlock"


class PdaTracker(DefaultOnToggle):
    """Enable tracker content in the AP PDA tab; disabled seeds show a disabled page."""

    display_name = "Archipelago PDA tracker"


class ScoutingMode(Choice):
    """Disable scouting, reveal rewards locally, or also create persistent AP location hints."""

    display_name = "PDA scouting and location hints"
    option_disabled = 0
    option_local = 1
    option_shared_hints = 2
    default = 0


class RewardPreviews(Toggle):
    """Show the actual next side-task and faction-standing check reward in the PDA."""

    display_name = "Next milestone reward previews"


class ChecksShops(Toggle):
    """One paid purchase check at each supported named trader; never one per repeat purchase."""

    display_name = "Checks: First ordinary trader purchase"


class ChecksShopPurchases(Toggle):
    """Buy three named AP checks each at Sidorovich, Barman and Sakharov.

    Each trader offers checks costing 2,500, 7,500 and 15,000 RU (75,000 RU total).
    The Archipelago shop button is in the trader window. Purchases are saved once;
    these are separate locations from the first ordinary trader purchase checks.
    Named NPC availability follows the missable service-check policy.
    """

    display_name = "Checks: Buy Archipelago shop contracts"


class ChecksFactionStanding(Toggle):
    """Finite goodwill thresholds reached with any supported non-hostile faction."""

    display_name = "Checks: Faction standing"


class DiscoveryMode(Choice):
    """Existing per-type checks, or one check for each of the first N distinct qualifying types."""

    display_name = "Discovery mode"
    option_per_type = 0
    option_first_n_distinct = 1
    default = 0


class MutantDiscoveryCount(Range):
    """Quota count; zero means all non-excluded mutant types. Used only in quota mode."""

    display_name = "Distinct mutant quota"
    range_start = 0
    range_end = 25
    default = 0


class FactionDiscoveryCount(MutantDiscoveryCount):
    """Quota count; zero means all non-excluded factions."""

    display_name = "Distinct faction quota"
    range_end = 13


class ArtefactDiscoveryCount(MutantDiscoveryCount):
    """Quota count; zero means all non-excluded artefact types."""

    display_name = "Distinct artefact quota"
    range_end = 66


class DiscoveryExclusions(OptionSet):
    """Canonical catalogue tokens, such as faction:stalker or artefact:af_atom."""

    display_name = "Excluded discovery types"
    default = frozenset()


class OptionalCheckPolicy(Choice):
    """Treatment of fragile named-shop and faction-standing checks."""

    display_name = "Missable service check policy"
    option_exclude_progression = 0
    option_omit = 1
    option_allow_progression = 2
    default = 0


@dataclass
class GammaOptions(PerGameCommonOptions):
    opening_policy: OpeningPolicy
    access_pacing: AccessPacing
    combat_logic: CombatLogic
    grind_profile: GrindProfile
    generation_preview: GenerationPreview
    start_inventory_from_pool: StartInventoryPool
    rewards_convenience: RewardsConvenience
    supply_ammo_calibre: SupplyAmmoCalibre
    rewards_supply_medical: RewardsSupplyMedical
    rewards_supply_maintenance: RewardsSupplyMaintenance
    rewards_supply_ammunition: RewardsSupplyAmmunition
    rewards_supply_expedition: RewardsSupplyExpedition
    permission_supplies: PermissionSupplies
    rewards_workshop_access: RewardsWorkshopAccess
    rewards_recipe_access: RewardsRecipeAccess
    rewards_progressive_tools: RewardsProgressiveTools
    mutant_discovery_mode: DiscoveryMode
    mutant_discovery_count: MutantDiscoveryCount
    faction_discovery_mode: DiscoveryMode
    faction_discovery_count: FactionDiscoveryCount
    artefact_discovery_mode: DiscoveryMode
    artefact_discovery_count: ArtefactDiscoveryCount
    discovery_exclusions: DiscoveryExclusions
    optional_check_policy: OptionalCheckPolicy
    checks_shops: ChecksShops
    checks_shop_purchases: ChecksShopPurchases
    checks_faction_standing: ChecksFactionStanding
    scouting_mode: ScoutingMode
    reward_previews: RewardPreviews
    checks_maps: ChecksMaps
    checks_settlements: ChecksSettlements
    checks_mutant_first_kills: ChecksMutantFirstKills
    checks_faction_first_kills: ChecksFactionFirstKills
    checks_artefacts: ChecksArtefacts
    checks_quest_types: ChecksQuestTypes
    checks_gear_upgrades: ChecksGearUpgrades
    checks_armour_tiers: ChecksArmourTiers
    checks_weapon_tiers: ChecksWeaponTiers
    checks_knife_tiers: ChecksKnifeTiers
    checks_kill_milestones: ChecksKillMilestones
    checks_side_task_milestones: ChecksSideTaskMilestones
    checks_story_milestones: ChecksStoryMilestones
    checks_rank_milestones: ChecksRankMilestones
    rewards_loot_stashes: RewardsLootStashes
    rewards_progression_stashes: RewardsProgressionStashes
    rewards_quest_keys: RewardsQuestKeys
    rewards_faction_reputation: RewardsFactionReputation
    rewards_stat_levels: RewardsStatLevels
    rewards_zone_keys: RewardsZoneKeys
    rewards_starting_gear_unlocks: RewardsStartingGearUnlocks
    zone_unlock_travel: ZoneUnlockTravel
    pda_tracker: PdaTracker
    goal: Goal
    no_starting_weapons: NoStartingWeapons
    starting_detector: StartingGear
    starting_pda: StartingGear
    starting_firearms: StartingGear
    starting_melee: StartingGear
    starting_outfit: StartingGear
    starting_helmet: StartingGear
    starting_backpack: StartingGear
    starting_tools: StartingGear
    starting_utilities: StartingGear
    starting_ammo: StartingQuantity
    starting_medicine: StartingQuantity
    starting_food: StartingQuantity
    starting_money: StartingQuantity
    kill_milestones: KillMilestones
    side_task_milestones: SideTaskMilestones
