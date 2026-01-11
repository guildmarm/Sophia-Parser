from lib.io import load_json
from lib.constants import LANGUAGE_FILES, ATTRIBUTE_TYPE, ATTRIBUTE_TYPE_ALT, ATTRIBUTE_TYPE_RAW, TARGET_LEVELS, SPACESHIP_ROOM_TYPE, SPACESHIP_ROOM_TYPE_ALT, TARGET_LEVELS
from lib.format_text import module_format, efdb_format
import lib.general as general
from collections import OrderedDict, defaultdict
import math
import html
import re

def resolve_enemy_names(enemy_id, enemy_name, enemy_name_clean, enemy_name_image, enemy_name_counts, duplicate_name_map):
    if enemy_name_counts.get(enemy_name_clean, 0) > 1:
        short_id = enemy_id.split("_")[-1]
        enemy_name_clean = f"{enemy_name_clean} ({short_id})"
        enemy_name = f"{enemy_name} ({short_id})"
        enemy_name_image = f"{enemy_name_image}_{short_id}"

        alternate_ids = [eid for eid in duplicate_name_map[enemy_name_clean.split(" (")[0]] if eid != enemy_id]
        alternate_names = []
        for alt_id in alternate_ids:
            alt_short = alt_id.split("_")[-1]
            alternate_names.append(f"{enemy_name_clean.split(' (')[0]} ({alt_short})")

        enemy_alternate_text = ""
        if alternate_names:
            enemy_alternate_text = " Alternate form(s): " + ", ".join(f"[[{name}]]" for name in alternate_names)
    else:
        enemy_alternate_text = ""
        
    return enemy_name, enemy_name_clean, enemy_name_image, enemy_alternate_text

def resolve_enemy_species(enemy_id, enemy_group, wiki_group, language, lang="en"):
    enemy_species = ""
    for entry_id, entry_data in enemy_group.items():
        ref_id = entry_data.get("refMonsterTemplateId")
        if ref_id == enemy_id:
            group_id = entry_data.get("groupId")
            break
    else:
        group_id = None

    if group_id:
        group_name_id = None
        for group_type, group_list_data in wiki_group.items():
            for group in group_list_data.get("list", []):
                if group.get("groupId") == group_id:
                    group_name_id = group.get("groupName", {}).get("id")
                    break
            if group_name_id:
                break
        
        if group_name_id:
            enemy_species = general.resolve_text(language[lang], group_name_id)
            
    return enemy_species

def resolve_enemy_abilities(display_data, enemy_ability, language, lang="en"):
    enemy_ability_list = []
    ability_desc_ids = display_data.get("abilityDescIds", [])
    for ability_id in ability_desc_ids:
        ability_data = enemy_ability.get(str(ability_id), {})
        desc_id = ability_data.get("description", {}).get("id")
        ability_text = general.resolve_text(language[lang], desc_id)
        if ability_text:
            enemy_ability_list.append(f"*{ability_text}")

    return "\n".join(enemy_ability_list)

def resolve_enemy_locations(display_data, distribution_info, language, lang="en"):
    enemy_location_list = []
    distribution_ids = display_data.get("distributionIds", [])
    for dist_id in distribution_ids:
        dist_data = distribution_info.get(str(dist_id), {})
        area_name_id = dist_data.get("areaName", {}).get("id")
        area_name = general.resolve_text(language[lang], area_name_id)
        if area_name:
            enemy_location_list.append(f"*{area_name}")

    if not enemy_location_list:
        enemy_location_list.append("*TBA")

    return "\n".join(enemy_location_list)

def resolve_enemy_drops(enemy_id, enemy_drop, item_table, language, lang="en"):
    drop_data = enemy_drop.get(enemy_id, {})
    drop_item_ids = drop_data.get("dropItemIds", [])
    enemy_drop_item_list = []

    for item_id in drop_item_ids:
        item_data = item_table.get(str(item_id), {})
        item_name_id = item_data.get("name", {}).get("id")
        item_name = general.resolve_text(language[lang], item_name_id)
        if item_name:
            enemy_drop_item_list.append(f"{{{{I|{item_name}}}}}")

    return " ".join(enemy_drop_item_list)

def resolve_enemy_level_stats(attr_data):
    level_blocks = attr_data.get("levelDependentAttributes", [])
    level_stat_map = {}

    for block in level_blocks:
        attrs = block.get("attrs", [])
        level = None
        stat_map = {}

        for attr in attrs:
            attr_type = attr.get("attrType")
            attr_value = attr.get("attrValue")

            if attr_type == 0:
                level = attr_value
            else:
                stat_map[attr_type] = attr_value

        if level is not None:
            level_stat_map[level] = stat_map

    hp_values = []
    atk_values = []
    def_values = []

    for lvl in TARGET_LEVELS:
        stats = level_stat_map.get(lvl, {})

        hp_values.append(str(stats.get(1, "")))
        atk_values.append(str(stats.get(2, "")))
        def_values.append(str(stats.get(3, "")))

    enemy_hp = ", ".join(hp_values)
    enemy_atk = ", ".join(atk_values)
    enemy_def = ", ".join(def_values)

    return enemy_hp, enemy_atk, enemy_def

def resolve_enemy_independent_stats(attr_data):
    independent_block = attr_data.get("levelIndependentAttributes", {})
    independent_stats = {}

    for attr in independent_block.get("attrs", []):
        attr_type = attr.get("attrType")
        attr_value = attr.get("attrValue")
        independent_stats[attr_type] = attr_value

    enemy_weight = independent_stats.get(8, "")
    enemy_attack_range = independent_stats.get(12, "")
    enemy_stagger_hp = independent_stats.get(20, "")
    enemy_stagger_time = independent_stats.get(21, "")
    enemy_stagger_damage = independent_stats.get(27, "")

    physical_resist = independent_stats.get(80, "")
    nature_resist = independent_stats.get(81, "")
    cryo_resist = independent_stats.get(82, "")
    electric_resist = independent_stats.get(83, "")
    heat_resist = independent_stats.get(84, "")
    aether_resist = independent_stats.get(85, "")

    return (
        enemy_weight, enemy_attack_range, enemy_stagger_hp, enemy_stagger_time, 
        enemy_stagger_damage, physical_resist, nature_resist, cryo_resist, 
        electric_resist, heat_resist, aether_resist
    )

def build_enemy_nav_lists(enemy_attr, enemy_display, enemy_group, wiki_group, enemy_type, language, enemy_name_counts, duplicate_name_map, lang="en"):
    class_weights = {
        "Boss": 5,
        "Alpha": 4,
        "Elite": 3,
        "Advanced": 2,
        "Common": 1
    }

    temp_aggeloi = []
    temp_landbreakers = []
    temp_pirates = []
    temp_wildlife = []

    for enemy_id, attr_data in enemy_attr.items():
        display_data = enemy_display.get(enemy_id)
        if not display_data:
            continue

        enemy_species = resolve_enemy_species(enemy_id, enemy_group, wiki_group, language, lang)
        
        name_id = display_data.get("name", {}).get("id")
        enemy_name = general.resolve_text(language[lang], name_id)
        enemy_name, _, _, _ = resolve_enemy_names(enemy_id, enemy_name, general.sanitize_name(enemy_name), general.sanitize_image_name(enemy_name), enemy_name_counts, duplicate_name_map)
        
        display_type_id = display_data.get("displayType")
        type_data = enemy_type.get(str(display_type_id), {})
        type_name_id = type_data.get("name", {}).get("id")
        enemy_class = general.resolve_text(language[lang], type_name_id)
        
        entry_text = f"{{{{Enemy Icon|{enemy_name}|{enemy_class}}}}}"
        weight = class_weights.get(enemy_class, 0)

        if enemy_species == "Aggeloi":
            temp_aggeloi.append((weight, enemy_name, entry_text))
        elif enemy_species == "Landbreakers":
            temp_landbreakers.append((weight, enemy_name, entry_text))
        elif enemy_species == "Cangzei Pirates":
            temp_pirates.append((weight, enemy_name, entry_text))
        elif enemy_species == "Wildlife":
            temp_wildlife.append((weight, enemy_name, entry_text))

    def finalize_list(temp_list):
        sorted_items = sorted(temp_list, key=lambda x: (-x[0], x[1]))
        return " &bull; ".join([e[2] for e in sorted_items])

    return finalize_list(temp_aggeloi), finalize_list(temp_landbreakers), finalize_list(temp_pirates), finalize_list(temp_wildlife)