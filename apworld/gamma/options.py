"""Generation options; feature adapters declare availability as they are implemented."""

from dataclasses import dataclass

from Options import Choice, DefaultOnToggle, OptionList, PerGameCommonOptions, Range, Toggle


class ChecksMaps(DefaultOnToggle):
    """Enable maps checks; unsupported adapters reject generation."""

    display_name = "Checks: Maps"


class ChecksSettlements(Toggle):
    """Enable settlements checks; unsupported adapters reject generation."""

    display_name = "Checks: Settlements"


class ChecksMutantFirstKills(Toggle):
    """Enable mutant first kills checks; unsupported adapters reject generation."""

    display_name = "Checks: Mutant First Kills"


class ChecksFactionFirstKills(Toggle):
    """Enable faction first kills checks; unsupported adapters reject generation."""

    display_name = "Checks: Faction First Kills"


class ChecksArtefacts(Toggle):
    """Enable artefacts checks; unsupported adapters reject generation."""

    display_name = "Checks: Artefacts"


class ChecksQuestTypes(Toggle):
    """Enable quest types checks; unsupported adapters reject generation."""

    display_name = "Checks: Quest Types"


class ChecksGearUpgrades(Toggle):
    """Enable gear upgrades checks; unsupported adapters reject generation."""

    display_name = "Checks: Gear Upgrades"


class ChecksArmourTiers(Toggle):
    """Enable armour tiers checks; unsupported adapters reject generation."""

    display_name = "Checks: Armour Tiers"


class ChecksWeaponTiers(Toggle):
    """Enable weapon tiers checks; unsupported adapters reject generation."""

    display_name = "Checks: Weapon Tiers"


class ChecksKnifeTiers(Toggle):
    """Enable knife tiers checks; unsupported adapters reject generation."""

    display_name = "Checks: Knife Tiers"


class ChecksKillMilestones(Toggle):
    """Enable kill milestones checks; unsupported adapters reject generation."""

    display_name = "Checks: Kill Milestones"


class ChecksSideTaskMilestones(Toggle):
    """Enable side task milestones checks; unsupported adapters reject generation."""

    display_name = "Checks: Side Task Milestones"


class ChecksStoryMilestones(Toggle):
    """Enable story milestones checks; unsupported adapters reject generation."""

    display_name = "Checks: Story Milestones"


class ChecksRankMilestones(Toggle):
    """Enable rank milestones checks; unsupported adapters reject generation."""

    display_name = "Checks: Rank Milestones"


class RewardsLootStashes(Toggle):
    """Enable loot stashes rewards; unsupported adapters reject generation."""

    display_name = "Rewards: Loot Stashes"


class RewardsProgressionStashes(Toggle):
    """Enable progression stashes rewards; unsupported adapters reject generation."""

    display_name = "Rewards: Progression Stashes"


class RewardsQuestKeys(Toggle):
    """Enable quest keys rewards; unsupported adapters reject generation."""

    display_name = "Rewards: Quest Keys"


class RewardsFactionReputation(Toggle):
    """Enable faction reputation rewards; unsupported adapters reject generation."""

    display_name = "Rewards: Faction Reputation"


class RewardsStatLevels(Toggle):
    """Enable stat levels rewards; unsupported adapters reject generation."""

    display_name = "Rewards: Stat Levels"


class RewardsZoneKeys(Toggle):
    """Enable zone keys rewards; unsupported adapters reject generation."""

    display_name = "Rewards: Zone Keys"


class RewardsStartingGearUnlocks(Toggle):
    """Enable starting gear unlocks rewards; unsupported adapters reject generation."""

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


@dataclass
class GammaOptions(PerGameCommonOptions):
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
