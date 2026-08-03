from lib.io import load_json
from lib.constants import LANGUAGE_FILES, ATTRIBUTE_TYPE, ATTRIBUTE_TYPE_ALT, ATTRIBUTE_TYPE_RAW, TARGET_LEVELS, SPACESHIP_ROOM_TYPE, SPACESHIP_ROOM_TYPE_ALT, TARGET_LEVELS, BASE_DIR, ITEM_TYPE_NAME
from lib.format_text import module_format, efdb_format
import lib.general as general
from collections import OrderedDict, defaultdict
from datetime import datetime
import math
import html
import re
import os

def resolve_item_sources(item_id, item_table, system_jump_table, language, lang="en"):
    item_data = item_table.get(item_id)
    if not item_data:
        return ""

    sources = []
    source_ids = item_data.get("obtainWayIds", [])

    for oid in source_ids:
        entry = system_jump_table.get(oid)
        if not entry:
            continue
            
        desc_id = entry.get("desc", {}).get("id")
        localized_desc = general.resolve_text(language[lang], desc_id)
        
        if localized_desc:
            sources.append(localized_desc)

    if not sources:
        hint_id = item_data.get("noObtainWayHint", {}).get("id")
        hint_text = general.resolve_text(language[lang], hint_id)
        return efdb_format(hint_text) if hint_text else ""

    if len(sources) == 1:
        return efdb_format(sources[0])

    final_output = "\n".join(f"*{s}" for s in sources)
    return efdb_format(final_output)

def get_container_reward_items(item_id, item_chest, reward_table, item_table, language, lang="en"):
    chest_data = item_chest.get(item_id)
    if not chest_data:
        return ""

    reward_id_list = chest_data.get("rewardIdList", [])
    final_output_lines = []

    for reward_id in reward_id_list:
        reward_data = reward_table.get(reward_id)
        if not reward_data:
            continue

        item_bundles = reward_data.get("itemBundles", [])
        bundle_icons = []

        for bundle in item_bundles:
            reward_item_id = bundle.get("id")
            reward_count = bundle.get("count", 1)

            item_info = item_table.get(reward_item_id)
            if item_info:
                reward_name_id = item_info.get("name", {}).get("id")
                reward_name = general.resolve_text(language[lang], reward_name_id)
                bundle_icons.append(f"{{{{I|{reward_name}|{reward_count}|gv=false}}}}")

        if bundle_icons:
            final_output_lines.append("*" + ", ".join(bundle_icons))

    return "\n".join(final_output_lines)

def get_item_usage_effect(item_id, use_item, language, lang="en"):
    entry = use_item.get(item_id)
    if not entry:
        return ""

    desc_id = entry.get("itemUseDesc", {}).get("id")
    raw_text = general.resolve_text(language[lang], desc_id)
    if not raw_text:
        return ""

    use_actions = entry.get("useActions", [])

    def resolve_value(k):
        k = k.strip()
        
        if "\\" in k:
            prefix, key = k.split("\\", 1)
            prefix = prefix.strip()
            key = key.strip()

            for action in use_actions:
                buff_data = action.get("buffBBData", {})
                if buff_data.get("buffId") == prefix:
                    for item in buff_data.get("blackboard", []):
                        if item.get("key") == key:
                            return float(item.get("value", 0.0))

                skill_data = action.get("skillBBData", {})
                if skill_data.get("skillId") == prefix:
                    for item in skill_data.get("blackboard", []):
                        if item.get("key") == key:
                            return float(item.get("value", 0.0))
            return 0.0

        try:
            return float(k)
        except ValueError:
            for action in use_actions:
                for data_type in ["buffBBData", "skillBBData"]:
                    bb_list = action.get(data_type, {}).get("blackboard", [])
                    for bb_item in bb_list:
                        if bb_item.get("key") == k:
                            return float(bb_item.get("value", 0.0))
            return 0.0

    placeholder_matches = list(re.finditer(r"\{([^}:]+)(?::([^}]+))?\}", raw_text))
    
    for match in reversed(placeholder_matches):
        full_match = match.group(0)
        key_raw = match.group(1).strip()
        raw_val = match.group(2)

        if "*" in key_raw:
            parts = key_raw.split("*")
            v = resolve_value(parts[0]) * resolve_value(parts[1])
        elif "/" in key_raw:
            parts = key_raw.split("/")
            v1 = resolve_value(parts[0])
            v2 = resolve_value(parts[1])
            v = v1 / v2 if v2 != 0 else 0.0
        elif "+" in key_raw:
            parts = key_raw.split("+")
            v = resolve_value(parts[0]) + resolve_value(parts[1])
        elif "-" in key_raw:
            parts = key_raw.split("-")
            v = resolve_value(parts[0]) - resolve_value(parts[1])
        else:
            v = resolve_value(key_raw)

        if raw_val and "%" in raw_val:
            formatted_value = f"{v * 100:.2f}".rstrip('0').rstrip('.') + "%"
        else:
            formatted_value = f"{v:.2f}".rstrip('0').rstrip('.')

        raw_text = raw_text.replace(full_match, formatted_value)

    return efdb_format(raw_text)

def get_item_tactical_effect(item_id, equip_item, language, lang="en"):
    entry = equip_item.get(item_id)
    if not entry:
        return ""

    desc_id = entry.get("equipDesc", {}).get("id")
    raw_text = general.resolve_text(language[lang], desc_id)
    if not raw_text:
        return ""

    def resolve_value(k):
        clean = k.split("\\")[-1].strip()
        
        if clean.lower().startswith("param"):
            try:
                param_idx = int(clean[5:]) - 1
                params = entry.get("condParams", [])
                return float(params[param_idx])
            except (ValueError, IndexError):
                return 0.0

        mapping = {
            "count": "chargeCount",
            "recover": "recoverTime",
            "cooldown": "cooldown",
            "cast": "castTime"
        }
        lookup_key = mapping.get(clean, clean)
        
        try:
            return float(lookup_key)
        except ValueError:
            val = entry.get(lookup_key, 0.0)
            try:
                return float(val)
            except (ValueError, TypeError):
                return 0.0

    placeholder_matches = list(re.finditer(r"\{([^}:]+)(?::([^}]+))?\}", raw_text))
    
    for match in reversed(placeholder_matches):
        full_match = match.group(0)
        key_raw = match.group(1).strip()
        raw_val = match.group(2)

        if "*" in key_raw:
            parts = key_raw.split("*")
            v = resolve_value(parts[0]) * resolve_value(parts[1])
        elif "/" in key_raw:
            parts = key_raw.split("/")
            v1 = resolve_value(parts[0])
            v2 = resolve_value(parts[1])
            v = v1 / v2 if v2 != 0 else 0.0
        elif "+" in key_raw:
            parts = key_raw.split("+")
            v = resolve_value(parts[0]) + resolve_value(parts[1])
        elif "-" in key_raw:
            parts = key_raw.split("-")
            v = resolve_value(parts[0]) - resolve_value(parts[1])
        else:
            v = resolve_value(key_raw)

        if raw_val and "%" in raw_val:
            formatted_value = f"{v * 100:.2f}".rstrip('0').rstrip('.') + "%"
        else:
            formatted_value = f"{v:.2f}".rstrip('0').rstrip('.')

        raw_text = raw_text.replace(full_match, formatted_value)

    return efdb_format(raw_text)

def save_new_items_to_list(new_ids):
    if not new_ids:
        return

    file_path = os.path.join(BASE_DIR, "lib", "item_list.py")
    today = datetime.now().strftime("%Y-%m-%d")
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i in range(len(lines) - 1, -1, -1):
        if "]" in lines[i]:
            lines.insert(i, f'    # Added {today}\n')
            for idx, item_id in enumerate(new_ids):
                lines.insert(i + 1 + idx, f'    "{item_id}",\n')
            break

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def compute_uncategorized_items(item_table, item_list_ids):
    uncat = defaultdict(list)
    item_list_set = set(item_list_ids)
    for item_id, item_data in item_table.items():
        item_type = item_data.get("type")
        if item_type in ITEM_TYPE_NAME or item_id in item_list_set:
            continue
        uncat[item_type].append(item_id)

    return dict(sorted(uncat.items(), key=lambda kv: (kv[0] is None, kv[0])))

def save_uncat_items(uncat_dict):
    file_path = os.path.join(BASE_DIR, "lib", "uncat_items.py")
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# Auto-generated {today} by lib/helpers/item.py::save_uncat_items\n",
        "# Item IDs whose type has no entry in ITEM_TYPE_NAME (lib/constants.py),\n",
        "# grouped by type id. Regenerated on every parser run - do not edit by hand.\n",
        "UNCAT_ITEMS = {\n",
    ]
    for item_type, ids in uncat_dict.items():
        lines.append(f"    {item_type!r}: [\n")
        for item_id in sorted(ids):
            lines.append(f'        "{item_id}",\n')
        lines.append("    ],\n")
    lines.append("}\n")

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)