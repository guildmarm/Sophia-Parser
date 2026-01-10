from .io import load_json
from .constants import LANGUAGE_FILES, ATTRIBUTE_TYPE, ATTRIBUTE_TYPE_ALT, ATTRIBUTE_TYPE_RAW, TARGET_LEVELS, SPACESHIP_ROOM_TYPE, SPACESHIP_ROOM_TYPE_ALT, TARGET_LEVELS
from .format_text import module_format, efdb_format
from collections import OrderedDict, defaultdict
import math
import html
import re

def resolve_text(lang_table, text_id):
    if not text_id or str(text_id) == "0":
        return ""
    return lang_table.get(str(text_id), "")

# Get those germs off (Can't have a page title with [] or {} in mediawiki)
def sanitize_name(name):
    if not name:
        return ""
    return name.replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")").replace("\u00B7", " ")

# Images cannot contain a colon. Seperated from the sanitized weapon name because page names CAN have a colon.
def sanitize_image_name(name):
    if not name:
        return ""
    return name.replace(":", "").replace(" ", "_")

def resolve_sources(source_ids, system_jump_table, language, lang="en"):
    if not source_ids:
        return ""
    sources = []
    for oid in source_ids:
        entry = system_jump_table.get(oid)
        if not entry:
            continue
        desc_id = entry.get("desc", {}).get("id")
        localized_desc = resolve_text(language[lang], desc_id)
        if localized_desc:
            sources.append(localized_desc)
    return ", ".join(sources)


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
    return resolve_text(language[lang], name_id)

def build_weapon_skill_lua(skill_id, skill_patch, language, lang="en"):
    entry = skill_patch.get(skill_id)
    if not entry:
        return ""

    bundle = entry.get("SkillPatchDataBundle", [])
    if not bundle:
        return ""

    name_id = bundle[0].get("skillName", {}).get("id")
    skill_name = resolve_text(language[lang], name_id)
    if not skill_name:
        return ""

    texts = []
    blackboards = []

    for rank in bundle:
        desc_id = rank.get("description", {}).get("id")
        raw_text = resolve_text(language[lang], desc_id)
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
            localized_name = resolve_text(language[lang], name_id)
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

def get_gear_part_type(equip_data):
    part_type = equip_data.get("partType")
    return {0: "Armor", 1: "Gloves", 2: "Kit",}.get(part_type, "")

def get_gear_region(equip_data):
    domain_id = equip_data.get("domainId")
    return {"domain_1": "Valley IV", "domain_2": "Wuling",}.get(domain_id, "")

def resolve_gear_attributes_sections(equip_data, attribute_filter, language, lang="en"):
    gear_def = ""
    pstat = pvalue = ""
    sstat = svalue = ""
    tstat = tvalue = ""

    p_enhanced = []
    s_enhanced = []
    t_enhanced = []

    base_def = equip_data.get("displayBaseAttrModifier")
    if base_def and base_def.get("attrType") == 3:
        val = base_def.get("attrValue")
        if val is not None:
            gear_def = str(val)

    modifiers = equip_data.get("displayAttrModifiers", [])

    filter_list = attribute_filter.get("equipExtraAttr", {}).get("list", [])

    for idx, mod in enumerate(modifiers):
        attr_type = mod.get("attrType")
        base_val = mod.get("attrValue")
        enhanced_vals = mod.get("enhancedAttrValues", [])
        composite_attr = mod.get("compositeAttr", "")

        if "DamageTakenScalar" in composite_attr or attr_type in (4, 5, 6, 7):
            if base_val is not None:
                base_val = 1 - base_val
            enhanced_vals = [1 - v for v in enhanced_vals]

        values = []
        if base_val is not None:
            values.append(str(base_val))
        values.extend(str(v) for v in enhanced_vals)
        values_str = ", ".join(values)

        stat_name = ""

        if attr_type == 0:
            for entry in filter_list:
                if (
                    entry.get("attributeType") == 0
                    and entry.get("compositeAttr") == composite_attr
                ):
                    name_id = entry.get("name", {}).get("id")
                    stat_name = resolve_text(language[lang], name_id)
                    break
        else:
            stat_name = ATTRIBUTE_TYPE.get(attr_type, "")

        if not stat_name:
            continue

        if idx == 0:
            pstat = stat_name
            pvalue = values_str
            p_enhanced = enhanced_vals
        elif idx == 1:
            sstat = stat_name
            svalue = values_str
            s_enhanced = enhanced_vals
        elif idx == 2:
            tstat = stat_name
            tvalue = values_str
            t_enhanced = enhanced_vals

    return (
        gear_def,
        pstat, pvalue, p_enhanced,
        sstat, svalue, s_enhanced,
        tstat, tvalue, t_enhanced,
    )

def resolve_artifice_bool(p_enhanced, s_enhanced, t_enhanced):
    if p_enhanced or s_enhanced or t_enhanced:
        return "yes"
    return "no"

def format_stat_value(value_str, artifice_bool):
    if not value_str:
        return ""

    numbers = [v.strip() for v in value_str.split(",")]

    if artifice_bool == "no" and len(set(numbers)) == 1:
        numbers = [numbers[0]]

    formatted = []
    for v in numbers:
        try:
            num = float(v)

            if 0 < num < 1:
                formatted.append(f"+{round(num * 100, 1)}%")
            else:
                rounded = round(num, 1)
                sign = '+' if rounded > 0 else '-' if rounded < 0 else ''
                abs_val = abs(rounded)
                formatted_val = (
                    str(int(abs_val)) if abs_val.is_integer() else str(abs_val)
                )
                formatted.append(f"{sign}{formatted_val}")
        except ValueError:
            formatted.append(v)

    return ", ".join(formatted)

def resolve_gear_set_and_effect(gear_id, equip_suit, skill_patch, language, lang="en"):
    gear_set = ""
    set_effect = ""

    for suit_key, suit_data in equip_suit.items():
        equip_list = suit_data.get("equipList", [])
        if gear_id not in equip_list:
            continue

        suit_name_id = suit_data.get("list", [{}])[0].get("suitName", {}).get("id")
        gear_set = language[lang].get(suit_name_id, "")
        skill_id = suit_data.get("list", [{}])[0].get("skillID", "")
        skill_entry = skill_patch.get(skill_id, {})
        bundle = skill_entry.get("SkillPatchDataBundle", [])
        if not bundle:
            break

        desc_id = bundle[0].get("description", {}).get("id")
        desc_text = language[lang].get(desc_id, "")
        blackboard = {bb["key"]: bb["value"] for bb in bundle[0].get("blackboard", []) if "key" in bb}

        def repl(match):
            sign = match.group("sign") or ""
            expr = match.group("expr")
            fmt = match.group("fmt")
            expr_eval = expr
            for key, val in blackboard.items():
                expr_eval = re.sub(rf"\b{re.escape(key)}\b", str(val), expr_eval)
            try:
                result = eval(expr_eval)
            except Exception:
                return match.group(0)

            if fmt == "0%":
                val_num = result * 100
                val_str = f"{int(round(val_num))}%"
            else:
                val_str = f"{int(round(result))}" if float(result).is_integer() else f"{result:.1f}"
            return f"{sign}{val_str}"

        pattern = r"(?P<sign>[+-]?)\{(?P<expr>[^{}:]+)(?::(?P<fmt>0%?))?\}"
        desc_text = re.sub(pattern, repl, desc_text)
        set_effect = desc_text
        break
    return gear_set, set_effect

def resolve_gear_recipe(gear_id, equip_formula, item_table, language, lang="en"):
    recipe_parts = []

    for formula in equip_formula.values():
        if formula.get("outcomeEquipId") == gear_id:
            cost_ids = formula.get("costItemId", [])
            cost_nums = formula.get("costItemNum", [])

            for item_id, count in zip(cost_ids, cost_nums):
                item_entry = item_table.get(item_id, {})
                name_id = item_entry.get("name", {}).get("id")
                item_name = language[lang].get(name_id, "")
                if item_name:
                    recipe_parts.append(f"{{{{I|{item_name}|{count}}}}}")
            break

    return " ".join(recipe_parts)

def resolve_gear_sources_from_formula(gear_id, equip_formula, item_table, system_jump_table, language, lang="en"):
    for formula in equip_formula.values():
        if formula.get("outcomeEquipId") != gear_id:
            continue

        formula_id = formula.get("formulaId")
        if not formula_id:
            return ""

        formula_item = item_table.get(formula_id)
        if not formula_item:
            return ""

        source_ids = formula_item.get("obtainWayIds", [])

        sources = []
        for oid in source_ids:
            entry = system_jump_table.get(oid)
            if not entry:
                continue
            desc_id = entry.get("desc", {}).get("id")
            localized_desc = resolve_text(language[lang], desc_id)
            if localized_desc:
                sources.append(localized_desc)

        if not sources:
            return ""

        if len(sources) == 1:
            return sources[0]

        return "\n".join(f"*{s}" for s in sources)

    return ""

def build_gear_set_lines(equip_table, item_table, equip_suit, language, lang="en"):
    gear_sets = {}

    for gear_id, gear_data in equip_table.items():
        item_data = item_table.get(gear_id)
        if not item_data:
            continue

        gear_set, _ = resolve_gear_set_and_effect(gear_id, equip_suit, {}, language, lang=lang)
        if not gear_set:
            continue

        gear_name = sanitize_name(resolve_text(language[lang], item_data.get("name", {}).get("id")))
        rarity = item_data.get("rarity", 0)
        gear_type = get_gear_part_type(gear_data)

        if gear_set not in gear_sets:
            gear_sets[gear_set] = []

        gear_sets[gear_set].append((rarity, gear_type, gear_name))

    lines = []
    type_order = {"Armor": 0, "Gloves": 1, "Kit": 2}

    for set_name, items in sorted(gear_sets.items()):
        sorted_items = sorted(items, key=lambda x: (x[0], type_order.get(x[1], 99), x[2]))
        item_strs = [f"{{{{Gear Icon|{name}|{rarity}}}}}" for rarity, _, name in sorted_items]
        line = f"| {set_name} = {' '.join(item_strs)}"
        lines.append(line)

    return "\n".join(lines)

def build_gear_nav_lists(equip_table, item_table, language, lang="en"):
    armor_list = []
    glove_list = []
    kit_list = []

    temp_armor = []
    temp_glove = []
    temp_kit = []

    for gear_id, gear_data in equip_table.items():
        item_data = item_table.get(gear_id)
        if not item_data:
            continue

        name_id = item_data.get("name", {}).get("id")
        gear_name = resolve_text(language[lang], name_id)
        rarity = item_data.get("rarity", 0)

        entry_text = f"{{{{Item Icon|{gear_name}|{rarity}}}}}"

        gear_type = get_gear_part_type(gear_data)
        if gear_type == "Armor":
            temp_armor.append((rarity, gear_name, entry_text))
        elif gear_type == "Gloves":
            temp_glove.append((rarity, gear_name, entry_text))
        elif gear_type == "Kit":
            temp_kit.append((rarity, gear_name, entry_text))

    armor_list = [e[2] for e in sorted(temp_armor, key=lambda x: (x[0], x[1]))]
    glove_list = [e[2] for e in sorted(temp_glove, key=lambda x: (x[0], x[1]))]
    kit_list = [e[2] for e in sorted(temp_kit, key=lambda x: (x[0], x[1]))]

    gear_armor = " ".join(armor_list)
    gear_glove = " ".join(glove_list)
    gear_kit = " ".join(kit_list)

    return gear_armor, gear_glove, gear_kit

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
        weapon_name = resolve_text(language[lang], name_id)
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

def operator_stats_truncate(value, decimals=3):
    factor = 10 ** decimals
    return math.trunc(value * factor) / factor

def get_operator_attributes(char_table, operator_id):
    operator = char_table.get(operator_id)
    if not operator:
        return {}

    entries = operator.get("attributes", [])
    extracted = {lvl: {} for lvl in TARGET_LEVELS}

    ROUND_ATTRS = {"STR", "AGL", "INT", "WIL"}

    for entry in entries:
        attrs = entry.get("Attribute", {}).get("attrs", [])
        level = None

        for item in attrs:
            if item.get("attrType") == 0:
                lvl = int(item.get("attrValue", 0))
                if lvl in TARGET_LEVELS:
                    level = lvl
                break

        if level is None:
            continue

        for item in attrs:
            attr_type = item.get("attrType")
            if attr_type in ATTRIBUTE_TYPE_ALT:
                name = ATTRIBUTE_TYPE_ALT[attr_type]
                value = item.get("attrValue")

                if name in ROUND_ATTRS and value is not None:
                    value = operator_stats_truncate(value, 3)

                extracted[level][name] = value

    return extracted

def build_operator_stats_block(extracted):
    def collect(attr_name):
        return [extracted[lvl].get(attr_name, "") for lvl in TARGET_LEVELS]

    hp_vals  = collect("HP")
    atk_vals = collect("ATK")
    str_vals = collect("STR")
    agl_vals = collect("AGL")
    int_vals = collect("INT")
    wil_vals = collect("WIL")

    cr_val = extracted[TARGET_LEVELS[0]].get("CR", "")
    as_val = extracted[TARGET_LEVELS[0]].get("AS", "")
    ar_val = extracted[TARGET_LEVELS[0]].get("AR", "")

    lines = []

    if any(hp_vals):
        lines.append(f"|HP = {', '.join(str(v) for v in hp_vals)}")
    if any(atk_vals):
        lines.append(f"|ATK = {', '.join(str(v) for v in atk_vals)}")
    if any(str_vals):
        lines.append(f"|STR = {', '.join(str(v) for v in str_vals)}")
    if any(agl_vals):
        lines.append(f"|AGL = {', '.join(str(v) for v in agl_vals)}")
    if any(int_vals):
        lines.append(f"|INT = {', '.join(str(v) for v in int_vals)}")
    if any(wil_vals):
        lines.append(f"|WIL = {', '.join(str(v) for v in wil_vals)}")

    if cr_val != "":
        lines.append(f"|CR = {cr_val}")
    if as_val != "":
        lines.append(f"|AS = {as_val}")
    if ar_val != "":
        lines.append(f"|AR = {ar_val} Meters")

    return "\n".join(lines)

def resolve_operator_tags(operator_data, char_battle_tags, language, lang="en"):
    tag_names = []
    for tag_key in operator_data.get("charBattleTagIds", []):
        tag_entry = char_battle_tags.get(tag_key)
        if tag_entry:
            tag_text_id = tag_entry.get("id")
            tag_text = resolve_text(language[lang], tag_text_id)
            tag_names.append(tag_text)
    return ", ".join(tag_names)

def get_operator_quote(operator_data, operator_id, language, lang="en"):
    target_id = f"{operator_id}_13"
    for entry in operator_data.get("profileVoice", []):
        if entry.get("id") == target_id:
            desc_id = entry.get("voiceDesc", {}).get("id")
            if desc_id:
                return resolve_text(language[lang], desc_id)
    return ""

def resolve_operator_faction(operator_id, char_tags, tag_data, language, lang="en"):
    bloc_tag_id = char_tags[operator_id]["blocTagId"]
    if not bloc_tag_id:
        return ""
    tag_name_id = tag_data[bloc_tag_id]["tagName"]["id"]
    return resolve_text(language[lang], tag_name_id)

def get_starting_operator(operator_id):
    starting_operators = ("chr_0002_endminm", "chr_0003_endminf", "chr_9000_endmin", "chr_0004_pelica", "chr_0005_chen")
    if operator_id in starting_operators:
        return "true"
    return ""

def resolve_operator_gacha_pools(operator_id, gacha_pool_content, gacha_pool, language, lang="en"):
    pool_names = []

    standard_list = gacha_pool_content.get("standard", {}).get("list", [])
    if any(entry.get("charId") == operator_id for entry in standard_list):
        pool_names.append("standard")
        return ", ".join(pool_names)

    for pool_key, pool_data in gacha_pool_content.items():
        if pool_key == "standard":
            continue
        if any(entry.get("charId") == operator_id for entry in pool_data.get("list", [])):
            pool_names.append("chartered")
            break

    return ", ".join(pool_names)

def get_operator_profile_records(operator_data, language, lang="en"):
    output = []
    gender_value = ""
    birthdate_value = ""
    race_value = ""
    infection_value = ""
    strength_value = ""
    skill_value = ""
    tactical_value = ""
    originium_value = ""

    for record in operator_data.get("profileRecord", []):
        desc_id = record.get("recordDesc", {}).get("id")
        if desc_id:
            text = resolve_text(language[lang], desc_id)
            output.append(text)
            match_gender = re.search(r"GENDER:\s*(.+)", text)
            if match_gender:
                gender_value = match_gender.group(1).strip()
            match_birthdate = re.search(r"DOB:\s*(.+)", text)
            if match_birthdate:
                birthdate_value = match_birthdate.group(1).strip()
            match_race = re.search(r"RACE:\s*(.+)", text)
            if match_race:
                race_value = f"[[{match_race.group(1).strip()}]]"
            match_infection = re.search(r"\[ORIPATHY INFECTION STATUS\]\s*\n(.+)", text)
            if match_infection:
                infection_value = match_infection.group(1).strip()
            match_strength = re.search(r"PHYSIOLOGICAL STRENGTH:\s*(.+)", text)
            if match_strength:
                strength_value = match_strength.group(1).strip()
            match_skill = re.search(r"COMBAT SKILL:\s*(.+)", text)
            if match_skill:
                skill_value = match_skill.group(1).strip()
            match_tactical = re.search(r"TACTICAL ACUMEN:\s*(.+)", text)
            if match_tactical:
                tactical_value = match_tactical.group(1).strip()
            match_originium = re.search(r"ORIGINIUM ARTS ASSIMILATION:\s*(.+)", text)
            if match_originium:
                originium_value = match_originium.group(1).strip().replace("</>", "")

    return "\n".join(output), gender_value, birthdate_value, race_value, infection_value, strength_value, skill_value, tactical_value, originium_value

def get_operator_hobbies_and_expertise(operator_id, char_tags, tag_data, char_tag_des, language, lang="en"):
    hobbyname1 = ""
    hobbyname2 = ""
    expertname1 = ""
    expertname2 = ""
    hobbydesc1 = ""
    hobbydesc2 = ""
    expertdesc1 = ""
    expertdesc2 = ""
    prefer = ""

    char_entry = char_tags.get(operator_id)
    if not char_entry:
        return hobbyname1, hobbyname2, expertname1, expertname2, hobbydesc1, hobbydesc2, expertdesc1, expertdesc2, prefer

    hobby_ids = char_entry.get("hobbyTagIds", [])
    expert_ids = char_entry.get("expertTagIds", [])
    prefer_ids = char_entry.get("giftPreferTagId", [])

    resolved_hobbies = []
    resolved_experts = []
    resolved_prefers = []

    for tag_id in hobby_ids:
        tag_entry = tag_data.get(tag_id)
        if not tag_entry:
            continue
        name_id = tag_entry.get("tagName", {}).get("id")
        if not name_id:
            continue
        text = resolve_text(language[lang], name_id)
        if text:
            resolved_hobbies.append(text)

    for tag_id in expert_ids:
        tag_entry = tag_data.get(tag_id)
        if not tag_entry:
            continue
        name_id = tag_entry.get("tagName", {}).get("id")
        if not name_id:
            continue
        text = resolve_text(language[lang], name_id)
        if text:
            resolved_experts.append(text)

    for tag_id in prefer_ids:
        tag_entry = tag_data.get(tag_id)
        if not tag_entry:
            continue
        name_id = tag_entry.get("tagName", {}).get("id")
        if not name_id:
            continue
        text = resolve_text(language[lang], name_id)
        if text:
            resolved_prefers.append(text)
    prefer = resolved_prefers[0] if resolved_prefers else ""

    if len(resolved_hobbies) > 0:
        hobbyname1 = resolved_hobbies[0]
    if len(resolved_hobbies) > 1:
        hobbyname2 = resolved_hobbies[1]
    if len(resolved_experts) > 0:
        expertname1 = resolved_experts[0]
    if len(resolved_experts) > 1:
        expertname2 = resolved_experts[1]

    tag_desc_entry = char_tag_des.get(operator_id, {}).get("tagDesc", {})

    def resolve_desc(tag_id):
        desc_id = tag_desc_entry.get(tag_id, {}).get("desc", {}).get("id")
        if not desc_id or desc_id == "0":
            return ""
        return resolve_text(language[lang], desc_id)

    if len(hobby_ids) > 0:
        hobbydesc1 = resolve_desc(hobby_ids[0])
    if len(hobby_ids) > 1:
        hobbydesc2 = resolve_desc(hobby_ids[1])
    if len(expert_ids) > 0:
        expertdesc1 = resolve_desc(expert_ids[0])
    if len(expert_ids) > 1:
        expertdesc2 = resolve_desc(expert_ids[1])

    return hobbyname1, hobbyname2, expertname1, expertname2, hobbydesc1, hobbydesc2, expertdesc1, expertdesc2, prefer

def get_operator_potentials(operator_id, char_potential, potential_effect, language, enums_table, lang="en"):
    bundles = char_potential.get(operator_id, {}).get("potentialUnlockBundle", [])
    pot_names = ["", "", "", "", ""]
    pot_descs = ["", "", "", "", ""]

    effect_operator_id = operator_id
    if operator_id == "chr_0002_endminm":
        effect_operator_id = "chr_9000_endmin"

    for bundle in bundles:
        level = bundle.get("level")
        if not (1 <= level <= 5):
            continue
        name_id = bundle.get("name", {}).get("id")
        if name_id and name_id != "0":
            pot_names[level - 1] = resolve_text(language[lang], name_id)

        effect_key = f"{effect_operator_id}_potential_{level}"
        effect_entry = potential_effect.get(effect_key, {})
        desc_id = effect_entry.get("desc", {}).get("id")
        raw_desc = ""
        if desc_id and desc_id != "0":
            raw_desc = resolve_text(language[lang], desc_id)
            for data in effect_entry.get("dataList", []):
                for bb in data.get("attachBuff", {}).get("blackboard", []):
                    key = bb.get("key")
                    value = bb.get("value")
                    if value is not None:
                        if f"{{{key}:0%}}" in raw_desc:
                            v_pct = value * 100
                            raw_desc = raw_desc.replace(f"{{{key}:0%}}", f"{v_pct:g}%")
                        decimal_pattern = rf"\{{{key}:0\.(\d+)\}}"
                        for match in re.findall(decimal_pattern, raw_desc):
                            precision = len(match)
                            formatted_val = f"{value:.{precision}f}"
                            raw_desc = raw_desc.replace(f"{{{key}:0.{match}}}", formatted_val)
                        raw_desc = raw_desc.replace(f"{{{key}:0}}", str(value))

                for bb in data.get("attachSkill", {}).get("blackboard", []):
                    key = bb.get("key")
                    value = bb.get("value")
                    if value is not None:
                        raw_desc = raw_desc.replace(f"{{{key}:0}}", str(value))
                        raw_desc = raw_desc.replace(f"{{{key}:0%}}", str(value)).replace(".0", "")

                bb_key = data.get("skillBbModifier", {}).get("bbKey")
                float_value = data.get("skillBbModifier", {}).get("floatValue")
                if bb_key and float_value is not None:
                    for placeholder in re.findall(r"\{([^}]+)\}", raw_desc):
                        if re.match(rf"^{re.escape(bb_key)}([+\-*/].*)?(:0|:0\.0|:0\.00|:0%|:0.0%|:0.00%)?$", placeholder):
                            expr = placeholder.split(':')[0]
                            expr = expr.replace(bb_key, str(float_value))
                            try:
                                evaluated = eval(expr)
                            except Exception:
                                evaluated = float_value
                            
                            if placeholder.endswith(("%", ":0%")):
                                evaluated_str = f"{round(evaluated * 100, 2)}%".replace(".0%", "%")
                            else:
                                evaluated_str = f"{round(evaluated, 2)}".replace(".0", "")
                            
                            raw_desc = raw_desc.replace(f"{{{placeholder}}}", evaluated_str)

                attr_type = data.get("attrModifier", {}).get("attrType")
                attr_value = data.get("attrModifier", {}).get("attrValue")
                if attr_type is not None and attr_value is not None:
                    attr_key = ATTRIBUTE_TYPE_RAW.get(attr_type)
                    if attr_key:
                        for placeholder in re.findall(r"\{([^}]+)\}", raw_desc):
                            if placeholder == f"{attr_key}:0%":
                                raw_desc = raw_desc.replace(f"{{{placeholder}}}", f"{round(attr_value * 100, 6)}%".replace(".0", ""))
                            elif placeholder == f"{attr_key}:0":
                                raw_desc = raw_desc.replace(f"{{{placeholder}}}", str(attr_value).replace(".0", ""))

                param_type = data.get("skillParamModifier", {}).get("paramType")
                param_value = data.get("skillParamModifier", {}).get("paramValue")
                if param_type is not None and param_value is not None:
                    enum_name = ""
                    for enum_block in enums_table.values():
                        if enum_block.get("name") == "ModifiableSkillParam":
                            for e in enum_block.get("enums", []):
                                if e.get("value") == param_type:
                                    enum_name = e.get("name", "")
                                    break
                    if enum_name:
                        key_variants = {enum_name, enum_name.lower(), enum_name[0].lower() + enum_name[1:]}
                        for placeholder in re.findall(r"\{([^}]+)\}", raw_desc):
                            for key in key_variants:
                                if re.match(rf"^-?([0-9\.\+\-\*/]*)?{re.escape(key)}([+\-*/][0-9\.]+)?(:0|:0%)?$", placeholder):
                                    parts = placeholder.split(':')
                                    math_part = parts[0]
                                    is_percent = parts[-1].endswith("%") if len(parts) > 1 else False
                                    expr = math_part.replace(key, f"({str(param_value)})")
                                    try:
                                        evaluated = eval(expr)
                                    except Exception:
                                        evaluated = param_value
                                    
                                    evaluated = round(evaluated, 6)
                                    if is_percent:
                                        evaluated_str = f"{evaluated * 100}%".replace(".0%", "%")
                                    else:
                                        evaluated_str = f"{evaluated:g}" 
                                        
                                    raw_desc = raw_desc.replace(f"{{{placeholder}}}", evaluated_str)

        pot_descs[level - 1] = efdb_format(raw_desc)

    return f"""|pot1 = {pot_descs[0]}
|pot1t = {pot_names[0]}
|pot2 = {pot_descs[1]}
|pot2t = {pot_names[1]}
|pot3 = {pot_descs[2]}
|pot3t = {pot_names[2]}
|pot4 = {pot_descs[3]}
|pot4t = {pot_names[3]}
|pot5 = {pot_descs[4]}
|pot5t = {pot_names[4]}"""

def get_operator_upgrade_items(operator_id, char_growth, item_table, language, lang="en"):
    operator_growth_data = char_growth.get(operator_id)
    if not operator_growth_data:
        return ""

    break_map = operator_growth_data.get("charBreakCostMap", {})
    
    mapping = [
        ("charBreak20", "e1"),
        ("charBreak40", "e2"),
        ("charBreak60", "e3"),
        ("charBreak70", "e4")
    ]

    results = {"e1": "", "e2": "", "e3": "", "e4": ""}

    for game_key, wiki_key in mapping:
        break_section = break_map.get(game_key)
        if not break_section:
            continue

        required_items = break_section.get("requiredItem", [])
        item_templates = []
        for item in required_items:
            item_id = item.get("id")
            count = item.get("count")
            item_info = item_table.get(item_id, {})
            name_id = item_info.get("name", {}).get("id")

            if name_id:
                item_name = resolve_text(language[lang], name_id)
                item_templates.append(f"{item_name} x{count}")
        
        results[wiki_key] = ", ".join(item_templates)

    return f"""|e1 = {results['e1']}
|e2 = {results['e2']}
|e3 = {results['e3']}
|e4 = {results['e4']}"""

def get_operator_combat_skills(operator_id, char_growth, skill_patch, language, weapon, lang="en"):
    text_table = language[lang]
    cdata = char_growth.get(operator_id)
    if not cdata or not isinstance(cdata, dict):
        return ""

    def clean_text(text):
        return re.sub(r"<.*?>", "", text).strip()

    def wrap_label(text, label):
        return text.replace(label, f"<b>{label}</b>")

    def resolve_blackboard_placeholders(text, skill_ids):
        for s_id in skill_ids:
            skill_entry = skill_patch.get(s_id)
            if not skill_entry: continue
            bundles = skill_entry.get("SkillPatchDataBundle", [])
            for bundle in bundles:
                blackboard = bundle.get("blackboard", [])
                for entry in blackboard:
                    key, val = entry.get("key"), entry.get("value")
                    if key and val is not None:
                        text = text.replace(f"{{{key}:0}}", str(val).replace(".0", ""))
                        text = text.replace(f"{{{key}:0.0}}", f"{val:.1f}")
                        text = text.replace(f"{{{key}:0.00}}", f"{val:.2f}")
                        val_pct = val * 100
                        text = text.replace(f"{{{key}:0%}}", f"{val_pct:g}%")
                        text = text.replace(f"{{{key}:0.0%}}", f"{val_pct:.1f}%")
                        text = text.replace(f"{{{key}:0.00%}}", f"{val_pct:.2f}%")
        return text

    def extract_skill_stats(skill_ids):
        stat_groups = OrderedDict()
        for s_id in skill_ids:
            skill_entry = skill_patch.get(s_id)
            if not skill_entry: continue
            bundles = skill_entry.get("SkillPatchDataBundle", [])
            for bundle in bundles:
                name_list = bundle.get("subDescNameList", []) or []
                values_list = bundle.get("subDescList", []) or []
                val_idx = 0
                for name_entry in name_list:
                    nid = name_entry.get("id")
                    if nid and str(nid) != "0":
                        value = values_list[val_idx] if val_idx < len(values_list) else ""
                        val_idx += 1
                        label_key = str(nid)
                        stat_label = text_table.get(label_key, "").strip()
                        if not stat_label: stat_label = f"UNKNOWN_{label_key}"
                        if stat_label not in stat_groups: stat_groups[stat_label] = []
                        if value != "": stat_groups[stat_label].append(value)
                while val_idx < len(values_list):
                    leftover = values_list[val_idx]
                    val_idx += 1
                    stat_label = f"LEFTOVER_{s_id}"
                    if stat_label not in stat_groups: stat_groups[stat_label] = []
                    stat_groups[stat_label].append(leftover)
        return stat_groups

    def extract_cost_or_cooldown(skill_ids, s_key):
        values, label = [], None
        for s_id in skill_ids:
            entry = skill_patch.get(s_id)
            if not entry: continue
            bundles = entry.get("SkillPatchDataBundle", [])
            for bundle in bundles:
                if s_key == "NormalSkill" and bundle.get("costType") == 1:
                    cost = bundle.get("costValue", 0)
                    if cost != 0: label, values = "SP Cost", values + [str(cost)]
                elif s_key == "UltimateSkill" and bundle.get("costType") == 0:
                    cost = bundle.get("costValue", 0)
                    if cost != 0: label, values = "Ultimate Energy Cost", values + [str(cost)]
                elif s_key == "ComboSkill" and "coolDown" in bundle:
                    label, values = "Cooldown", values + [str(bundle.get("coolDown", 0))]
        return (label, values) if label and values else None

    operator_name = cdata.get("engName", operator_id)
    if "Endministrator" in operator_name:
        operator_name = "Endmin"
    elif operator_name == "Chen Qianyu":
        operator_name = "Chen"
    
    operator_name = operator_name.replace(" ", "").capitalize()
    weapon_sanitized = weapon.replace(" ", "").capitalize()

    skill_order = [
        ("NormalAttack", 1, "Attack"),
        ("NormalSkill", 2, "Skill"),
        ("ComboSkill", 3, "Combo"),
        ("UltimateSkill", 4, "Ult")
    ]
    
    skill_map = cdata.get("skillGroupMap", {})
    results = []

    for s_key, type_num, icon_prefix in skill_order:
        skill = skill_map.get(f"{operator_id}_{s_key}")
        if not skill: continue

        icon_suffix = weapon_sanitized if s_key == "NormalAttack" else operator_name
        name_text = text_table.get(str(skill.get("name", {}).get("id", "")), "")
        raw_desc = text_table.get(str(skill.get("desc", {}).get("id", "")), "")

        skill_ids = skill.get("skillIdList", [])
        desc_text = resolve_blackboard_placeholders(raw_desc, skill_ids)
        desc_text = efdb_format(desc_text)
        desc_text = clean_text(desc_text)

        if s_key == "NormalAttack":
            desc_text = wrap_label(desc_text, "BASIC ATTACK:")
            desc_text = desc_text.replace("\nDIVE ATTACK:", "<br /><b>DIVE ATTACK:</b>")
            desc_text = desc_text.replace("\nFINISHER:", "<br /><b>FINISHER:</b>")
        elif s_key in ["NormalSkill", "UltimateSkill"]:
            desc_text = "<b>SKILL DESCRIPTION:</b> " + desc_text
        elif s_key == "ComboSkill":
            desc_text = wrap_label(desc_text, "COMBO TRIGGER:")
            if "\n" in desc_text:
                desc_text = desc_text.replace("\n", "<br /><b>SKILL DESCRIPTION:</b> ", 1)

        stat_lines, idx = [], 1
        cost_line = extract_cost_or_cooldown(skill_ids, s_key)
        if cost_line:
            l, v = cost_line
            stat_lines.append(f"|stat{idx}= {l}, {', '.join(v)}")
            idx += 1

        stat_groups = extract_skill_stats(skill_ids)
        for s_label, vals in stat_groups.items():
            stat_lines.append(f"|stat{idx}= {s_label}, {', '.join(vals)}" if vals else f"|stat{idx}= {s_label}")
            idx += 1

        if not stat_lines: stat_lines = ["|stat1="]
        
        stat_block = "\n".join(stat_lines)
        results.append(f"""{{{{Combat skill
|name= {name_text}
|icon= {icon_prefix}-{icon_suffix}
|type= {{{{SB|{type_num}}}}}
|desc= {desc_text}
{stat_block}
}}}}""")

    return "\n".join(results)

def get_operator_skill_items(operator_id, char_growth, item_table, language, lang="en"):
    text_table = language[lang]
    char_data = char_growth.get(operator_id)
    if not char_data:
        return ""

    def get_text(text_id):
        return text_table.get(str(text_id), f"[MISSING TEXT {text_id}]")

    def get_item_name(item_id):
        item = item_table.get(item_id)
        if not item:
            return f"[UNKNOWN ITEM {item_id}]"
        return get_text(item["name"]["id"])

    def format_items_for_cell(items):
        return [f"{get_item_name(item['id'])},{item['count']}" for item in items]

    skill_groups = char_data.get("skillGroupMap", {})
    skill_levels = char_data.get("skillLevelUp", [])
    skill_order_keys = ["NormalAttack", "NormalSkill", "ComboSkill", "UltimateSkill"]

    grouped = defaultdict(list)
    for entry in skill_levels:
        grouped[entry["skillGroupId"]].append(entry)

    skill_info = {}
    for skill_type in skill_order_keys:
        group_id = next((k for k in skill_groups if k.endswith(skill_type)), None)
        if group_id:
            skill_name = get_text(skill_groups[group_id]["name"]["id"])
            entries = grouped.get(group_id, [])
            entries.sort(key=lambda x: x["level"])
            skill_info[skill_type] = {"name": skill_name, "levels": entries}

    all_levels = sorted(list(set(e["level"] for s in skill_info.values() for e in s["levels"])))
    if not all_levels:
        return ""

    lines = ["{{Skill upgrade head}}"]
    seen_items_global = set()

    for level in all_levels:
        is_last_three = level in all_levels[-3:]
        cell_parts = [f"level={level}"]

        if level >= 10:
            for idx, skill_type in enumerate(skill_order_keys, 1):
                data = skill_info.get(skill_type)
                if data:
                    cell_parts.append(f"skill{idx}={data['name']}")

        for idx, skill_type in enumerate(skill_order_keys, 1):
            data = skill_info.get(skill_type)
            if not data:
                continue
            
            entry = next((e for e in data["levels"] if e["level"] == level), None)
            if entry:
                items_list = []
                if entry.get("itemBundle"):
                    items_list = format_items_for_cell(entry["itemBundle"])
                    items_key = tuple(items_list)
                    
                    if not is_last_three and items_key in seen_items_global:
                        continue
                    seen_items_global.add(items_key)

                if level < 10:
                    for i, itm in enumerate(items_list, 1):
                        cell_parts.append(f"m{i}={itm}")
                    if "goldCost" in entry:
                        cell_parts.append(f"m3=T-Creds,{entry['goldCost']}")
                else:
                    for i, itm in enumerate(items_list, 1):
                        cell_parts.append(f"m{idx}{i}={itm}")
                    if "goldCost" in entry:
                        cell_parts.append(f"m{idx}5=T-Creds,{entry['goldCost']}")

        lines.append("{{Skill upgrade cell|" + "|".join(cell_parts) + "}}")

    lines.append("{{Skill upgrade end}}")
    return "\n".join(lines)

def main_attribute_talent(operator_id, char_growth, language, mainAttr, lang="en"):
    text_table = language.get(lang, {})
    cdata = char_growth.get(operator_id)
    if not cdata:
        return ""

    talent_map = cdata.get("talentNodeMap", {})
    suffixes = ["1", "3", "5", "7"]
    talent_name = ""
    conds = ["", "", "", ""]
    descs = ["", "", "", ""]

    for i, suffix in enumerate(suffixes):
        node_id = f"{operator_id}_{suffix}"
        node = talent_map.get(node_id)
        if node:
            attr_info = node.get("attributeNodeInfo", {})
            if not talent_name:
                title_id = str(attr_info.get("title", {}).get("id", "0"))
                if title_id != "0":
                    full_name = text_table.get(title_id, "").strip()
                    talent_name = re.split(r'\s+[IVX]+$', full_name)[0]
            
            break_stage = attr_info.get("breakStage", 0)
            conds[i] = f"Elite {break_stage}"
            desc_id = str(attr_info.get("desc", {}).get("id", "0"))
            if desc_id != "0":
                descs[i] = text_table.get(desc_id, "").strip()

    return f"""{{{{Operator talent
|name = {talent_name}
|icon = {mainAttr}
|cond1 = {conds[0]}
|desc1 = {descs[0]}
|cond2 = {conds[1]}
|desc2 = {descs[1]}
|cond3 = {conds[2]}
|desc3 = {descs[2]}
|cond4 = {conds[3]}
|desc4 = {descs[3]}
}}}}"""

def operator_outfit_talent(operator_id, char_growth, language, lang="en"):
    text_table = language.get(lang, {})
    cdata = char_growth.get(operator_id)
    if not cdata:
        return ""

    break_map = cdata.get("charBreakCostMap", {})
    keys = ["equipBreakT2", "equipBreakT3", "equipBreakT4"]
    talent_name = ""
    conds = ["", "", ""]
    descs = ["", "", ""]

    for i, key in enumerate(keys):
        node = break_map.get(key)
        if node:
            if not talent_name:
                name_id = str(node.get("name", {}).get("id", "0"))
                if name_id != "0":
                    full_name = text_table.get(name_id, "").strip()
                    talent_name = re.split(r'\s+[IVX]+$', full_name)[0]
            
            break_stage = node.get("breakStage", 0)
            conds[i] = f"Elite {break_stage}"
            desc_id = str(node.get("description", {}).get("id", "0"))
            if desc_id != "0":
                descs[i] = text_table.get(desc_id, "").strip()

    return f"""{{{{Operator talent
|name = {talent_name}
|icon = Gear icon
|cond1 = {conds[0]}
|desc1 = {descs[0]}
|cond2 = {conds[1]}
|desc2 = {descs[1]}
|cond3 = {conds[2]}
|desc3 = {descs[2]}
}}}}"""

def operator_passive_talents(operator_id, operator_name, char_growth, potential_effect, language, enums_table, lang="en"):
    op_data = char_growth.get(operator_id, {})
    talent_nodes = op_data.get("talentNodeMap", {})

    levels = ["1_1", "1_2", "1_3", "2_1", "2_2", "2_3"]
    name_levels = ["0_1", "0_2", "0_3", "1_1", "1_2", "1_3"]
    descs = ["", "", "", "", "", ""]
    conds = ["", "", "", "", "", ""]
    talent_names = ["", "", "", "", "", ""]

    effect_operator_id = operator_id
    if operator_id == "chr_0002_endminm":
        effect_operator_id = "chr_9000_endmin"

    for i in range(len(levels)):
        current_level = levels[i]
        current_name_level = name_levels[i]
        node_key = f"{operator_id}_passive_skill_{current_name_level}"
        
        if node_key in talent_nodes:
            node = talent_nodes[node_key]
            passive_info = node.get("passiveSkillNodeInfo", {})
            
            break_stage = passive_info.get("breakStage", 0)
            conds[i] = f"Elite {break_stage}"
            
            name_id = passive_info.get("name", {}).get("id")
            if name_id and name_id != "0":
                talent_names[i] = resolve_text(language[lang], name_id)

            effect_key = f"{effect_operator_id}_talent_{current_level}"
            effect_entry = potential_effect.get(effect_key, {})
            desc_id = effect_entry.get("desc", {}).get("id")
            raw_desc = ""
            
            if desc_id and desc_id != "0":
                raw_desc = resolve_text(language[lang], desc_id)
                
                for data in effect_entry.get("dataList", []):
                    for source_path in ["attachBuff", "attachSkill"]:
                        for bb in data.get(source_path, {}).get("blackboard", []):
                            key = bb.get("key")
                            value = bb.get("value")
                            if key and value is not None:
                                for placeholder in re.findall(r"\{([^}]+)\}", raw_desc):
                                    if re.search(rf"\b{re.escape(key)}\b", placeholder):
                                        parts = placeholder.split(':')
                                        math_part = parts[0]
                                        expr = math_part.replace(key, str(value))
                                        try:
                                            evaluated = eval(expr)
                                        except Exception:
                                            evaluated = value

                                        if placeholder.endswith(("%", ":0%")):
                                            v_pct = evaluated * 100
                                            prec_match = re.search(r"0\.(\d+)%", placeholder)
                                            if prec_match:
                                                precision = len(prec_match.group(1))
                                                res = f"{v_pct:.{precision}f}%"
                                            else:
                                                res = f"{v_pct:g}%"
                                        else:
                                            prec_match = re.search(r"0\.(\d+)", placeholder)
                                            if prec_match:
                                                precision = len(prec_match.group(1))
                                                res = f"{evaluated:.{precision}f}"
                                            else:
                                                res = f"{evaluated:g}"
                                        
                                        raw_desc = raw_desc.replace(f"{{{placeholder}}}", res)

                    bb_key = data.get("skillBbModifier", {}).get("bbKey")
                    float_value = data.get("skillBbModifier", {}).get("floatValue")
                    if bb_key and float_value is not None:
                        for placeholder in re.findall(r"\{([^}]+)\}", raw_desc):
                            if re.search(rf"\b{re.escape(bb_key)}\b", placeholder):
                                parts = placeholder.split(':')
                                math_part = parts[0]
                                expr = math_part.replace(bb_key, str(float_value))
                                try:
                                    evaluated = eval(expr)
                                except Exception:
                                    evaluated = float_value
                                
                                if placeholder.endswith(("%", ":0%")):
                                    evaluated_str = f"{round(evaluated * 100, 2)}%".replace(".0%", "%")
                                else:
                                    evaluated_str = f"{round(evaluated, 2)}".replace(".0", "")
                                
                                raw_desc = raw_desc.replace(f"{{{placeholder}}}", evaluated_str)

                    attr_type = data.get("attrModifier", {}).get("attrType")
                    attr_value = data.get("attrModifier", {}).get("attrValue")
                    if attr_type is not None and attr_value is not None:
                        attr_key = ATTRIBUTE_TYPE_RAW.get(attr_type)
                        if attr_key:
                            for placeholder in re.findall(r"\{([^}]+)\}", raw_desc):
                                if placeholder == f"{attr_key}:0%":
                                    raw_desc = raw_desc.replace(f"{{{placeholder}}}", f"{round(attr_value * 100, 6)}%".replace(".0", ""))
                                elif placeholder == f"{attr_key}:0":
                                    raw_desc = raw_desc.replace(f"{{{placeholder}}}", str(attr_value).replace(".0", ""))

                    param_type = data.get("skillParamModifier", {}).get("paramType")
                    param_value = data.get("skillParamModifier", {}).get("paramValue")
                    if param_type is not None and param_value is not None:
                        enum_name = ""
                        for enum_block in enums_table.values():
                            if enum_block.get("name") == "ModifiableSkillParam":
                                for e in enum_block.get("enums", []):
                                    if e.get("value") == param_type:
                                        enum_name = e.get("name", "")
                                        break
                        if enum_name:
                            key_variants = {enum_name, enum_name.lower(), enum_name[0].lower() + enum_name[1:]}
                            for placeholder in re.findall(r"\{([^}]+)\}", raw_desc):
                                for key in key_variants:
                                    if re.search(rf"\b{re.escape(key)}\b", placeholder):
                                        parts = placeholder.split(':')
                                        math_part = parts[0]
                                        is_percent = parts[-1].endswith("%") if len(parts) > 1 else False
                                        expr = math_part.replace(key, f"({str(param_value)})")
                                        try:
                                            evaluated = eval(expr)
                                        except Exception:
                                            evaluated = param_value
                                        
                                        evaluated = round(evaluated, 6)
                                        if is_percent:
                                            evaluated_str = f"{evaluated * 100}%".replace(".0%", "%")
                                        else:
                                            evaluated_str = f"{evaluated:g}" 
                                            
                                        raw_desc = raw_desc.replace(f"{{{placeholder}}}", evaluated_str)

                descs[i] = efdb_format(raw_desc)
        else:
            descs[i] = ""
            conds[i] = ""

    return f"""{{{{Operator talent
|name = {talent_names[0] or talent_names[1] or talent_names[2]}
|icon = {operator_name} Talent 1 icon
|cond1 = {conds[0]}
|desc1 = {descs[0]}
|cond2 = {conds[1]}
|desc2 = {descs[1]}
|cond3 = {conds[2]}
|desc3 = {descs[2]}
}}}}
{{{{Operator talent
|name = {talent_names[3] or talent_names[4] or talent_names[5]}
|icon = {operator_name} Talent 2 icon
|cond1 = {conds[3]}
|desc1 = {descs[3]}
|cond2 = {conds[4]}
|desc2 = {descs[4]}
|cond3 = {conds[5]}
|desc3 = {descs[5]}
}}}}"""

def operator_talent_costs(operator_id, char_growth, item_table, language, mainAttr, lang="en"):
    text_table = language.get(lang, {})
    cdata = char_growth.get(operator_id, {})
    if not cdata:
        return ""

    def get_item_name(item_id):
        if item_id == "item_gold":
            return "T-Creds"
        item = item_table.get(item_id)
        if not item:
            return item_id
        name_id = str(item.get("name", {}).get("id", ""))
        return text_table.get(name_id, item_id).strip()

    def format_node_costs(node):
        if not node:
            return None
        req_items = node.get("requiredItem", [])
        if not req_items:
            return None
        return ", ".join([f"{get_item_name(itm['id'])} x{itm['count']}" for itm in req_items])

    tcost1_slots = ["-", "-", "-", "-"]
    tcost2_slots = ["-", "-", "-", "-"]
    tcost3_slots = ["-", "-", "-", "-"]
    tcost4_slots = ["-", "-", "-", "-"]

    talent_map = cdata.get("talentNodeMap", {})
    break_map = cdata.get("charBreakCostMap", {})

    for suffix in ["1", "3", "5", "7"]:
        node = talent_map.get(f"{operator_id}_{suffix}")
        if node:
            stage = node.get("attributeNodeInfo", {}).get("breakStage", 0)
            if 1 <= stage <= 4:
                cost_str = format_node_costs(node)
                if cost_str:
                    tcost1_slots[stage - 1] = cost_str

    for sub in ["1", "2", "3"]:
        node = talent_map.get(f"{operator_id}_passive_skill_0_{sub}")
        if node:
            stage = node.get("passiveSkillNodeInfo", {}).get("breakStage", 0)
            if 1 <= stage <= 4:
                cost_str = format_node_costs(node)
                if cost_str:
                    tcost2_slots[stage - 1] = cost_str

    for sub in ["1", "2", "3"]:
        node = talent_map.get(f"{operator_id}_passive_skill_1_{sub}")
        if node:
            stage = node.get("passiveSkillNodeInfo", {}).get("breakStage", 0)
            if 1 <= stage <= 4:
                cost_str = format_node_costs(node)
                if cost_str:
                    tcost3_slots[stage - 1] = cost_str

    gear_keys = ["equipBreakT1", "equipBreakT2", "equipBreakT3", "equipBreakT4"]
    for i, key in enumerate(gear_keys):
        node = break_map.get(key)
        if node:
            stage = node.get("breakStage", i + 1)
            if 1 <= stage <= 4:
                cost_str = format_node_costs(node)
                if cost_str:
                    tcost4_slots[stage - 1] = cost_str

    def finalize_row(slots):
        return "; ".join(slots) + ";"

    return f"""{{{{Operator talent cost
|type = Talent
|attr = {mainAttr}
|acost = {finalize_row(tcost1_slots)}
|tcost1 = {finalize_row(tcost2_slots)}
|tcost2 = {finalize_row(tcost3_slots)}
|gcost = {finalize_row(tcost4_slots)}
}}}}"""

def operator_base_skills(operator_id, char_growth, base_skill, language, lang="en"):
    if operator_id in ("chr_0002_endminm", "chr_0003_endminf", "chr_9000_endmin"):
        return "<i>The Endministrator does not possess any Base Skill.</i>"
    
    cdata = char_growth.get(operator_id, {})
    if not cdata:
        return ""

    talent_nodes = cdata.get("talentNodeMap", {})
    
    levels = ["0_1", "0_2", "1_1", "1_2"]
    bslevels = ["1_1", "1_2", "2_1", "2_2"]
    conds = ["", "", "", ""]
    talent_names = ["", "", "", ""]
    descs = ["", "", "", ""]
    facilities = ["", "", "", ""]
    icons = ["", "", "", ""]

    for i in range(len(levels)):
        node_key = f"fac_{operator_id}_{levels[i]}"
        node = talent_nodes.get(node_key)
        if node:
            fac_info = node.get("factorySkillNodeInfo", {})
            break_stage = fac_info.get("breakStage", 0)
            conds[i] = f"Elite {break_stage}"

        target_skill_id = f"spaceship_skill_{operator_id}_{bslevels[i]}"
        s_data = base_skill.get(target_skill_id)
        if s_data:
            name_id = str(s_data.get("name", {}).get("id", "0"))
            if name_id != "0":
                raw_name = resolve_text(language[lang], name_id)
                clean_name = re.split(r'[\s\u0370-\u03ff\u1f00-\u1fff]+$', raw_name)[0]
                clean_name = re.split(r'\s+[IVXLC]+$', clean_name)[0]
                talent_names[i] = clean_name.strip()
            
            desc_id = str(s_data.get("desc", {}).get("id", "0"))
            if desc_id != "0":
                raw_desc = resolve_text(language[lang], desc_id)
                descs[i] = efdb_format(raw_desc)

            room_type = s_data.get("roomType")
            facility_name = ""
            if room_type is not None:
                facility_name = SPACESHIP_ROOM_TYPE.get(str(room_type)) or SPACESHIP_ROOM_TYPE.get(room_type, "")
                facility_name_alt = SPACESHIP_ROOM_TYPE_ALT.get(str(room_type)) or SPACESHIP_ROOM_TYPE_ALT.get(room_type, "")
                facilities[i] = facility_name

            raw_icon = s_data.get("icon", "")
            if raw_icon and facility_name_alt:
                clean_icon_suffix = raw_icon.replace("facskill_spaceship_", "")
                icons[i] = f"{facility_name_alt}-{clean_icon_suffix}"

    return f"""{{{{Operator base skill
|name = {talent_names[0] or talent_names[1]}
|icon = {icons[0] or icons[1]}
|facility = {facilities[0] or facilities[1]}
|cond1 = {conds[0]}
|desc1 = {descs[0]}
|cond2 = {conds[1]}
|desc2 = {descs[1]}
}}}}
{{{{Operator base skill
|name = {talent_names[2] or talent_names[3]}
|icon = {icons[2] or icons[3]}
|facility = {facilities[2] or facilities[3]}
|cond1 = {conds[2]}
|desc1 = {descs[2]}
|cond2 = {conds[3]}
|desc2 = {descs[3]}
}}}}"""

def operator_base_talent_costs(operator_id, char_growth, item_table, base_skill, language, lang="en"):
    if operator_id in ("chr_0002_endminm", "chr_0003_endminf", "chr_9000_endmin"):
        return ""
    
    text_table = language.get(lang, {})
    cdata = char_growth.get(operator_id, {})
    if not cdata:
        return ""

    def get_item_name(item_id):
        if item_id == "item_gold":
            return "T-Creds"
        item = item_table.get(item_id)
        if not item:
            return item_id
        name_id = str(item.get("name", {}).get("id", ""))
        return text_table.get(name_id, item_id).strip()

    def format_node_costs(node):
        if not node:
            return None
        req_items = node.get("requiredItem", [])
        if not req_items:
            return None
        return ", ".join([f"{get_item_name(itm['id'])} x{itm['count']}" for itm in req_items])

    def get_skill_icon(suffix_list):
        for sub in suffix_list:
            major, minor = sub.split('_')
            bs_suffix = f"{int(major)+1}_{minor}"
            target_id = f"spaceship_skill_{operator_id}_{bs_suffix}"
            s_data = base_skill.get(target_id)
            
            if s_data:
                room_type = s_data.get("roomType")
                facility_name_alt = SPACESHIP_ROOM_TYPE_ALT.get(str(room_type)) or SPACESHIP_ROOM_TYPE_ALT.get(room_type, "")
                raw_icon = s_data.get("icon", "")
                
                if raw_icon and facility_name_alt:
                    clean_icon = raw_icon.replace("facskill_spaceship_", "")
                    return f"{facility_name_alt}-{clean_icon}"
        return ""

    bscost1_slots = ["-", "-", "-", "-"]
    bscost2_slots = ["-", "-", "-", "-"]
    talent_map = cdata.get("talentNodeMap", {})

    for sub in ["0_1", "0_2"]:
        node = talent_map.get(f"fac_{operator_id}_{sub}")
        if node:
            stage = node.get("factorySkillNodeInfo", {}).get("breakStage", 0)
            if 1 <= stage <= 4:
                cost_str = format_node_costs(node)
                if cost_str:
                    bscost1_slots[stage - 1] = cost_str

    for sub in ["1_1", "1_2"]:
        node = talent_map.get(f"fac_{operator_id}_{sub}")
        if node:
            stage = node.get("factorySkillNodeInfo", {}).get("breakStage", 0)
            if 1 <= stage <= 4:
                cost_str = format_node_costs(node)
                if cost_str:
                    bscost2_slots[stage - 1] = cost_str

    def finalize_row(slots):
        return "; ".join(slots) + ";"

    return f"""{{{{Operator talent cost
|type = Base Skill
|bs1icon = {get_skill_icon(["0_1", "0_2"])}
|bscost1 = {finalize_row(bscost1_slots)}
|bs2icon = {get_skill_icon(["1_1", "1_2"])}
|bscost2 = {finalize_row(bscost2_slots)}
}}}}"""

def resolve_cv_name(operator_data, language, cv_key, lang="en"):
    try:
        cv_id = operator_data["cvName"][cv_key]["id"]
        if cv_id != "0":
            return resolve_text(language[lang], cv_id)
    except KeyError:
        pass
    return ""

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
            enemy_species = resolve_text(language[lang], group_name_id)
            
    return enemy_species

def resolve_enemy_abilities(display_data, enemy_ability, language, lang="en"):
    enemy_ability_list = []
    ability_desc_ids = display_data.get("abilityDescIds", [])
    for ability_id in ability_desc_ids:
        ability_data = enemy_ability.get(str(ability_id), {})
        desc_id = ability_data.get("description", {}).get("id")
        ability_text = resolve_text(language[lang], desc_id)
        if ability_text:
            enemy_ability_list.append(f"*{ability_text}")

    return "\n".join(enemy_ability_list)

def resolve_enemy_locations(display_data, distribution_info, language, lang="en"):
    enemy_location_list = []
    distribution_ids = display_data.get("distributionIds", [])
    for dist_id in distribution_ids:
        dist_data = distribution_info.get(str(dist_id), {})
        area_name_id = dist_data.get("areaName", {}).get("id")
        area_name = resolve_text(language[lang], area_name_id)
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
        item_name = resolve_text(language[lang], item_name_id)
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
        enemy_name = resolve_text(language[lang], name_id)
        enemy_name, _, _, _ = resolve_enemy_names(enemy_id, enemy_name, sanitize_name(enemy_name), sanitize_image_name(enemy_name), enemy_name_counts, duplicate_name_map)
        
        display_type_id = display_data.get("displayType")
        type_data = enemy_type.get(str(display_type_id), {})
        type_name_id = type_data.get("name", {}).get("id")
        enemy_class = resolve_text(language[lang], type_name_id)
        
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