from lib.io import load_json
from lib.constants import LANGUAGE_FILES, ATTRIBUTE_TYPE, ATTRIBUTE_TYPE_ALT, ATTRIBUTE_TYPE_RAW, TARGET_LEVELS, SPACESHIP_ROOM_TYPE, SPACESHIP_ROOM_TYPE_ALT, TARGET_LEVELS
from lib.format_text import module_format, efdb_format
import lib.general as general
from collections import OrderedDict, defaultdict
import math
import html
import re

def get_weapon_type(weapon_id: str) -> str:
    wid = weapon_id.lower()
    if "claym" in wid:
        return "Great Sword"
    if "funnel" in wid:
        return "Arts Unit"
    if "pistol" in wid:
        return "Handcannon"
    if "sword" in wid:
        return "Sword"
    if "lance" in wid:
        return "Polearm"
    return "Unknown"

def resolve_skill_name(skill_id, skill_patch, language, lang="en"):
    entry = skill_patch.get(skill_id)
    if not entry:
        return ""
    bundle = entry.get("SkillPatchDataBundle", [])
    if not bundle:
        return ""
    name_id = bundle[0].get("skillName", {}).get("id")
    return general.resolve_text(language[lang], name_id)

def build_weapon_skill_lua(skill_id, skill_patch, language, lang="en"):
    entry = skill_patch.get(skill_id)
    if not entry:
        return ""

    bundle = entry.get("SkillPatchDataBundle", [])
    if not bundle:
        return ""

    name_id = bundle[0].get("skillName", {}).get("id")
    skill_name = general.resolve_text(language[lang], name_id)
    if not skill_name:
        return ""

    texts = []
    blackboards = []

    for rank in bundle:
        desc_id = rank.get("description", {}).get("id")
        raw_text = general.resolve_text(language[lang], desc_id)
        texts.append(raw_text)

        bb = rank.get("blackboard", [])
        blackboards.append({b.get("key"): b.get("value") for b in bb if "value" in b})

    if not texts or not blackboards:
        return ""

    base_text = texts[0].replace("\n", " ")

    placeholder_matches = list(re.finditer(r"\{([^}:]+)(?::([^}]+))?\}", base_text))
    values = []

    for i, match in enumerate(placeholder_matches):
        key = match.group(1)
        raw_val = match.group(2)

        col = []
        for rank_vals in blackboards:
            v = rank_vals.get(key, 0.0)
            if raw_val and "%" in raw_val:
                v = round(v * 100, 2)
            else:
                v = round(v, 2)
            col.append(v)

        if len(set(col)) == 1:
            base_text = base_text.replace(match.group(0), f"{col[0]:.2f}" + ("%"
                                     if raw_val and "%" in raw_val else ""))
        else:
            base_text = base_text.replace(match.group(0), f"{{{len(values)}}}" + ("%"
                                     if raw_val and "%" in raw_val else ""))
            values.append(col)

    safe_text = module_format(base_text).replace('"', '\\"')

    if values:
        values_str = "{" + ", ".join("{" + ",".join(f"{v:.2f}" for v in col) + "}" for col in values) + "}"
    else:
        values_str = "{}"

    return f'["{skill_name}"] = {{text = "{safe_text}", values = {values_str}}}'

def resolve_tuning_items(weapon_id, weapon_basic, breakthrough_table, item_table, language, lang="en"):
    weapon_data = weapon_basic.get(weapon_id)
    if not weapon_data:
        return []

    btid = weapon_data.get("breakthroughTemplateId")
    breakthrough = breakthrough_table.get(btid)
    if not breakthrough:
        return []

    steps = breakthrough.get("list", [])
    output = []

    for step in steps[1:]:
        items = step.get("breakItemList", [])
        parts = []
        for item in items:
            item_id = item.get("id")
            count = item.get("count", 0)
            item_entry = item_table.get(item_id)
            if not item_entry:
                continue
            name_id = item_entry.get("name", {}).get("id")
            localized_name = general.resolve_text(language[lang], name_id)
            parts.append(f"{{{{I|{localized_name}|{count}}}}}")
        gold = step.get("breakthroughGold")
        if gold:
            parts.append(f"{{{{I|T-Creds|{gold}}}}}")
        output.append(" ".join(parts))
    return output


def get_batk_values(level_template_id, weapon_upgrade_table):
    upgrade_entry = weapon_upgrade_table.get(level_template_id)
    if not upgrade_entry:
        return [""] * 6
    levels = upgrade_entry.get("list", [])
    target_levels = [1, 20, 40, 60, 80, 99]
    base_atks = []
    for lvl in target_levels:
        match = next((x for x in levels if x.get("weaponLv") == lvl), None)
        base_atks.append(str(match.get("baseAtk")) if match else "")
    return base_atks

def build_weapon_nav_lists(weapon_basic, item_table, language, lang="en"):
    sword_list = []
    great_sword_list = []
    polearm_list = []
    handcannon_list = []
    arts_unit_list = []

    temp_sword = []
    temp_great_sword = []
    temp_polearm = []
    temp_handcannon = []
    temp_arts_unit = []

    for weapon_id, weapon_data in weapon_basic.items():
        item_data = item_table.get(weapon_id)
        if not item_data:
            continue

        name_id = item_data.get("name", {}).get("id")
        weapon_name = general.resolve_text(language[lang], name_id)
        rarity = item_data.get("rarity", 0)

        entry_text = f"* {{{{Navitem|{weapon_name}|{rarity}}}}}"

        weapon_type = get_weapon_type(weapon_id)
        if weapon_type == "Sword":
            temp_sword.append((rarity, weapon_name, entry_text))
        elif weapon_type == "Great Sword":
            temp_great_sword.append((rarity, weapon_name, entry_text))
        elif weapon_type == "Polearm":
            temp_polearm.append((rarity, weapon_name, entry_text))
        elif weapon_type == "Handcannon":
            temp_handcannon.append((rarity, weapon_name, entry_text))
        elif weapon_type == "Arts Unit":
            temp_arts_unit.append((rarity, weapon_name, entry_text))

    sword_list = [e[2] for e in sorted(temp_sword, key=lambda x: (-x[0], x[1]))]
    great_sword_list = [e[2] for e in sorted(temp_great_sword, key=lambda x: (-x[0], x[1]))]
    polearm_list = [e[2] for e in sorted(temp_polearm, key=lambda x: (-x[0], x[1]))]
    handcannon_list = [e[2] for e in sorted(temp_handcannon, key=lambda x: (-x[0], x[1]))]
    arts_unit_list = [e[2] for e in sorted(temp_arts_unit, key=lambda x: (-x[0], x[1]))]

    weapon_sword = "\n".join(sword_list)
    weapon_great_sword = "\n".join(great_sword_list)
    weapon_polearm = "\n".join(polearm_list)
    weapon_handcannon = "\n".join(handcannon_list)
    weapon_arts_unit = "\n".join(arts_unit_list)

    return weapon_sword, weapon_great_sword, weapon_polearm, weapon_handcannon, weapon_arts_unit
