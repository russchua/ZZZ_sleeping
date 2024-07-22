import json
from itertools import combinations_with_replacement, product

disk_set_effects = "disks_setup/set_effects/all_set_effects.json"
# other constants
constants_path = "constants.json"
target_path = "enemies/tyrfing.json"

with open(disk_set_effects) as f:
    disk_set_effects_dict = json.load(f)
with open(target_path) as f:
    target_stats = json.load(f)
with open(constants_path) as f:
    anomaly_data = json.load(f)["anomaly_data"]


def get_stats(character, weapon, disk):
    with open(character) as f:
        character_dict = json.load(f)
        character_stats = character_dict["character_stats"]
        motion_values = character_dict["motion_values"]
    with open(weapon) as f:
        weapon_stats = json.load(f)
    with open(disk) as f:
        other_stats = json.load(f)
    return character_stats, motion_values, weapon_stats, other_stats

def get_stat(stat_dict, stat_name, verbose = False):
    stat_value = stat_dict.get(stat_name)
    if stat_value is None:
        if verbose:
            print(f"{stat_name} not found in dictionary. Setting it to 0.")
        stat_value = 0
    return stat_value

def evaluate_disk_stat(
    disk_options,
    main_stat_dict = {
        "disk_4": "CRIT_DMG",
        "disk_5": "Elemental_Damage",
        "disk_6": "ATK_%",
    },
    sub_stat_dict = {
        "ATK_%": 9,
        "CRIT_Rate": 11,
        "CRIT_DMG" : 14,
    },
):
    assigned_stats = disk_options.get("main_3", {})
    # Add main_stats to assigned_stats:
    for disk_name, stat_name in main_stat_dict.items():
        curr_stat = assigned_stats.get(stat_name, 0)
        disk_stat = disk_options[disk_name].get(stat_name, 0)
        assigned_stats[stat_name] = curr_stat + disk_stat
    # Add sub_stats to assigned_stats:
    for stat_name, stat_rolls in sub_stat_dict.items():
        curr_stat = assigned_stats.get(stat_name, 0)
        disk_stat = disk_options["sub"].get(stat_name, 0) * stat_rolls
        assigned_stats[stat_name] = curr_stat + disk_stat
    return assigned_stats

def get_total_stats(
        character_stats,
        weapon_stats,
        other_stats,
    ):
    
    # Complete initialization of total_stats
    total_stats = {
        "Level": 60,
        "Level_Coefficient": 281,
        "DEF_Reduction": 0,
        "Stun_Bonus": 0,
    }
    total_stats["Total_HP"] = ((get_stat(character_stats, "Base_HP") + get_stat(weapon_stats, "Base_HP")) \
                            * (1 + get_stat(weapon_stats, "HP_%") + get_stat(other_stats, "HP_%")) + get_stat(other_stats, "Flat_HP")) \
                                * (1 + get_stat(weapon_stats, "Final_HP_%") + get_stat(other_stats, "Final_HP_%")) + get_stat(other_stats, "Final_Flat_HP")
    
    total_stats["Total_DEF"] = ((get_stat(character_stats, "Base_DEF") + get_stat(weapon_stats, "Base_DEF")) \
                            * (1 + get_stat(weapon_stats, "DEF_%") + get_stat(other_stats, "DEF_%")) + get_stat(other_stats, "Flat_DEF")) \
                                * (1 + get_stat(weapon_stats, "Final_DEF_%") + get_stat(other_stats, "Final_DEF_%")) + get_stat(other_stats, "Final_Flat_DEF")
    
    total_stats["Total_ATK"] = ((get_stat(character_stats, "Base_ATK") + get_stat(weapon_stats, "Base_ATK")) \
                            * (1 + get_stat(weapon_stats, "ATK_%") + get_stat(other_stats, "ATK_%")) + get_stat(other_stats, "Flat_ATK")) \
                                * (1 + get_stat(weapon_stats, "Final_ATK_%") + get_stat(other_stats, "Final_ATK_%")) + get_stat(other_stats, "Final_Flat_ATK")
    
    total_stats["CRIT_Rate"] = get_stat(character_stats, "CRIT_Rate") + get_stat(weapon_stats, "CRIT_Rate") + get_stat(other_stats, "CRIT_Rate")
    total_stats["CRIT_DMG"] = get_stat(character_stats, "CRIT_DMG") + get_stat(weapon_stats, "CRIT_DMG") + get_stat(other_stats, "CRIT_DMG")
    total_stats["PEN_Ratio"] = get_stat(character_stats, "PEN_Ratio") + get_stat(weapon_stats, "PEN_Ratio") + get_stat(other_stats, "PEN_Ratio")
    total_stats["Impact"] = get_stat(character_stats, "Impact") + get_stat(weapon_stats, "Impact")
    total_stats["Stun_Bonus"] = total_stats["Stun_Bonus"] + get_stat(character_stats, "Stun_Bonus") + get_stat(weapon_stats, "Stun_Bonus") \
        + get_stat(other_stats, "Stun_Bonus")
    total_stats["Anomaly_Mastery"] = get_stat(character_stats, "Anomaly_Mastery") + get_stat(weapon_stats, "Anomaly_Mastery")
    total_stats["Anomaly_Proficiency"] = get_stat(character_stats, "Anomaly_Proficiency") + get_stat(other_stats, "Anomaly_Proficiency") \
        + get_stat(weapon_stats, "Anomaly_Proficiency")
    total_stats["Energy_Regen"] = get_stat(character_stats, "Energy_Regen") + get_stat(weapon_stats, "Energy_Regen")
    total_stats["Buff_Level_Multiplier"] = 1 + 0.0169 * (total_stats["Level"] - 1)
    total_stats["DMG%_Multiplier"] = 1 + get_stat(character_stats, "DMG%_Multiplier") + get_stat(weapon_stats, "DMG%_Multiplier") + get_stat(other_stats, "DMG%_Multiplier")
    total_stats["DMG_Taken_Multiplier"] = 1
    # Complete initialization of target_stats
    target_stats["Effective_DEF"] = get_stat(target_stats, "DEF") * (1 - total_stats["PEN_Ratio"]) - get_stat(other_stats, "Flat_PEN")
    target_stats["DEF_Multiplier"] = total_stats["Level_Coefficient"] / (total_stats["Level_Coefficient"] + target_stats["Effective_DEF"])
    return total_stats, target_stats

def motion_to_damage(
    motion_values,
    total_stats,
    target_stats,
    interested_keys = ["Average_Outgoing_DMG"]
):
    # No anomaly damage calculated here
    # for each attack in motion_values
    for key, value in motion_values.items():
        motion_values[key]["Base_DMG"] = value["DMG"] / 100 * total_stats["Total_ATK"]
        motion_values[key]["RES_Multiplier"] = 1 + target_stats[value["Element"] + "_RES"]

        if "Daze_Buildup" in interested_keys:
            motion_values[key]["Daze_Buildup"] = value["Daze"] / 100 * total_stats["Impact"] * (1 - target_stats["Daze_Resist"]) * (1 + total_stats["Stun_Bonus"])
        
        motion_values[key]["Average_Outgoing_DMG"] = motion_values[key]["Base_DMG"] \
            * total_stats["DMG%_Multiplier"] \
            * total_stats["DMG_Taken_Multiplier"] \
            * target_stats["DEF_Multiplier"] \
            * motion_values[key]["RES_Multiplier"] \
            * target_stats["Stun_Multiplier"] \
            * (1 + total_stats["CRIT_Rate"] * total_stats["CRIT_DMG"])

    return motion_values


def combo_to_damage(
    damage_combo,
    motion_values,
    total_stats,
    target_stats,
    interested_keys = ["Average_Outgoing_DMG"]
):
    # No anomaly damage calculated here
    # for each attack in motion_values
    for key in damage_combo:
        motion_values[key]["Base_DMG"] = motion_values[key]["DMG"] / 100 * total_stats["Total_ATK"]
        motion_values[key]["RES_Multiplier"] = 1 + target_stats[motion_values[key]["Element"] + "_RES"]

        if "Daze_Buildup" in interested_keys:
            motion_values[key]["Daze_Buildup"] = motion_values[key]["Daze"] / 100 * total_stats["Impact"] * (1 - target_stats["Daze_Resist"]) * (1 + total_stats["Stun_Bonus"])
        
        motion_values[key]["Average_Outgoing_DMG"] = motion_values[key]["Base_DMG"] \
            * total_stats["DMG%_Multiplier"] \
            * total_stats["DMG_Taken_Multiplier"] \
            * target_stats["DEF_Multiplier"] \
            * motion_values[key]["RES_Multiplier"] \
            * target_stats["Stun_Multiplier"] \
            * (1 + total_stats["CRIT_Rate"] * total_stats["CRIT_DMG"])

    damage = 0
    for combo in damage_combo:
        damage += motion_values[combo]["Average_Outgoing_DMG"]
    return damage

def anomaly_buildup(
    Base_Anomaly_Buildup,
    AM_Bonus,
    Anomaly_Buildup_Bonus,
    Anomaly_Buildup_RES_reduction,
    AM,
):
    AM_Bonus = AM / 100
    Anomaly_Buildup = Base_Anomaly_Buildup \
        * AM_Bonus \
        * (1 + Anomaly_Buildup_Bonus) \
        * (1 - Anomaly_Buildup_RES_reduction)
    return Anomaly_Buildup

def damage_calculator(
        character_stats,
        motion_values,
        weapon_stats,
        other_stats,
        target_path = "enemies/tyrfing.json",
    ):
    # Get the total_stats
    total_stats, target_stats = get_total_stats(
        character_stats,
        weapon_stats,
        other_stats,
        target_path
    )
    # for each attack in motion_values
    for key, value in motion_values.items():
        print(f"motion_values: {motion_values}")
        print(f"value: {value}")
        print(f"total_stats: {total_stats}")
        motion_values[key]["Base_DMG"] = value["DMG"] / 100 * total_stats["Total_ATK"]
        motion_values[key]["RES_Multiplier"] = 1 + target_stats[value["Element"] + "_RES"]
        motion_values[key]["Daze_Buildup"] = value["Daze"] / 100 * total_stats["Impact"] * (1 - target_stats["Daze_Resist"]) * (1 + total_stats["Stun_Bonus"])
        
        motion_values[key]["Average_Outgoing_DMG"] = motion_values[key]["Base_DMG"] \
            * total_stats["DMG%_Multiplier"] \
            * total_stats["DMG_Taken_Multiplier"] \
            * target_stats["DEF_Multiplier"] \
            * motion_values[key]["RES_Multiplier"] \
            * target_stats["Stun_Multiplier"] \
            * (1 + total_stats["CRIT_Rate"] * total_stats["CRIT_DMG"])

    # Add anomaly damage to the motion_values
    motion_values["Anomaly_DMG"] = (anomaly_data[character_stats["Element"]] * total_stats["Total_ATK"]) \
        * total_stats["DMG%_Multiplier"] \
        * target_stats["DEF_Multiplier"] \
        * (1 + target_stats[character_stats["Element"] + "_RES"]) \
        * total_stats["DMG_Taken_Multiplier"] \
        * target_stats["Stun_Multiplier"] \
        * total_stats["Anomaly_Proficiency"]/100 \
        * total_stats["Buff_Level_Multiplier"]
    return motion_values

def calculate_after_assignment(
    character_stats,
    base_motion_values,
    weapon_stats,
    disk_stats,
    damage_combo = ["ultimate"],
    target_path = "enemies/tyrfing.json",
):

    total_stats, target_stats = get_total_stats(
        character_stats,
        weapon_stats,
        disk_stats,
        target_path
    )
    new_mv = motion_to_damage(base_motion_values, total_stats, target_stats)
    final_damage = combo_to_damage(damage_combo, new_mv)
    print(final_damage)


def generate_valid_combinations(
        total_points: int,
        max_per_stat: int,
        attributes = {
            "Flat_ATK": 22,
            "ATK_%": 0.03,
            "CRIT_Rate": 0.024,
            "CRIT_DMG" : 0.048,
            "Flat_PEN": 9
        },
    ):
    # Attribute is a dictionary like {"ATK": 0, "DEF": 0, "HP": 0}
    # Get all possible combinations with the limit constraint
    # Return a dictionary like {"ATK": 1, "DEF": 2, "HP": 3}
    valid_combinations = []
    for combination in product(range(max_per_stat + 1), repeat = len(attributes)):
        if sum(combination) == total_points:
            valid_combinations.append(dict(zip(attributes.keys(), combination)))
    return valid_combinations

def generate_main_disk_options(
    disk_4_attributes_of_interest = {
        "ATK_%": 0.3,
        "CRIT_Rate": 0.24,
        "CRIT_DMG" : 0.48
    },
    disk_5_attributes_of_interest = {
        "ATK_%": 0.3,
        "PEN_Ratio": 0.24,
        "Elemental_Damage": 0.3
    },
    disk_6_attributes_of_interest = {
        "ATK_%": 0.3
    }
):
    disk_4_combo = [key for key in disk_4_attributes_of_interest.keys()]
    disk_5_combo = [key for key in disk_5_attributes_of_interest.keys()]
    disk_6_combo = [key for key in disk_6_attributes_of_interest.keys()]

    return disk_4_combo, disk_5_combo, disk_6_combo

def generate_valid_disk_sets(
    sets = [
        "Chaotic_Metal",
        "Fanged_Metal",
        "Freedom_Blues",
        "Hormone_Punk",
        "Inferno_Metal",
        "Polar_Metal",
        "Puffer_Electro",
        "Shockstar_Disco",
        "Soul_Rock",
        "Swing_Jazz",
        "Thunder_Metal",
        "Woodpecker_Electro"
    ],
):
    # Get 2 sets, permutation counts e.g. ["Chaotic Metal", "Fanged Metal"] and ["Fanged Metal", "Chaotic Metal"]
    # but no repeats
    valid_combinations = []
    for combination in combinations_with_replacement(sets, 2):
        if combination[0] != combination[1]:
            valid_combinations.append(combination)
            valid_combinations.append([combination[1], combination[0]])
    return valid_combinations

def add_set_options_to_disk(
    disk_stats,
    set_options,
    stats_of_interest = [
        "DMG%_Multiplier",
        "CRIT_Rate",
        "CRIT_DMG",
        "Anomaly_Proficiency",
        "ATK_%",
        "Final_ATK_%",
        "PEN_Ratio",
    ]
):
    two_piece_effect = disk_set_effects_dict[set_options[0]]
    four_piece_effect = disk_set_effects_dict[set_options[1]]
    for this_stat in stats_of_interest:
        disk_stats[this_stat] = get_stat(disk_stats, this_stat) + get_stat(two_piece_effect["two"], this_stat, verbose = False)
        disk_stats[this_stat] = get_stat(disk_stats, this_stat) + get_stat(four_piece_effect["two"], this_stat, verbose = False)
        disk_stats[this_stat] = get_stat(disk_stats, this_stat) + get_stat(four_piece_effect["four"], this_stat, verbose = False)
    return disk_stats