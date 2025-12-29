from .io import load_json
from .constants import LANGUAGE_FILES, ATTRIBUTE_TYPE
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
    return name.replace(":", "").replace("\u00B7", "_").replace("\u03B1", "Alpha").replace("\u03B4", "Delta").replace(" ", "_")

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