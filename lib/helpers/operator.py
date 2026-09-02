from lib.io import load_json
from lib.constants import LANGUAGE_FILES, ATTRIBUTE_TYPE, ATTRIBUTE_TYPE_ALT, ATTRIBUTE_TYPE_RAW, TARGET_LEVELS, SPACESHIP_ROOM_TYPE, SPACESHIP_ROOM_TYPE_ALT, TARGET_LEVELS, DIALOGUE_TYPE
from lib.format_text import module_format, efdb_format
import lib.general as general
from collections import OrderedDict, defaultdict
import math
import html
import re

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
            tag_text = general.resolve_text(language[lang], tag_text_id)
            tag_names.append(tag_text)
    return ", ".join(tag_names)

def get_operator_quote(operator_data, operator_id, language, lang="en"):
    target_id = f"{operator_id}_13"
    for entry in operator_data.get("profileVoice", []):
        if entry.get("id") == target_id:
            desc_id = entry.get("voiceDesc", {}).get("id")
            if desc_id:
                return general.resolve_text(language[lang], desc_id)
    return ""

def resolve_operator_faction(operator_id, char_tags, tag_data, language, lang="en"):
    bloc_tag_id = char_tags[operator_id]["blocTagId"]
    if not bloc_tag_id:
        return ""
    tag_name_id = tag_data[bloc_tag_id]["tagName"]["id"]
    return general.resolve_text(language[lang], tag_name_id)

def get_starting_operator(operator_id):
    starting_operators = ("chr_0002_endminm", "chr_0003_endminf", "chr_9000_endmin", "chr_0004_pelica", "chr_0005_chen", "chr_0006_wolfgd")
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
    auth_value = ""
    infection_value = ""
    strength_value = ""
    skill_value = ""
    tactical_value = ""
    originium_value = ""

    for record in operator_data.get("profileRecord", []):
        desc_id = record.get("recordDesc", {}).get("id")
        if desc_id:
            text = general.resolve_text(language[lang], desc_id)
            output.append(text)
            match_gender = re.search(r"GENDER:\s*(.+)", text)
            if match_gender:
                gender_value = match_gender.group(1).strip()
            match_birthdate = re.search(r"DOB:\s*(.+)", text)
            if match_birthdate:
                birthdate_value = match_birthdate.group(1).strip()
            match_race = re.search(r"RACE:\s*(.+)", text)
            if match_race:
                race_value = f"{match_race.group(1).strip()}"
            match_auth = re.search(r"AUTHENTICATION:\s*(.+)", text)
            if match_auth:
                auth_value = f"{match_auth.group(1).strip()}"
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

    return "\n".join(output), gender_value, birthdate_value, race_value, auth_value, infection_value, strength_value, skill_value, tactical_value, originium_value

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
        text = general.resolve_text(language[lang], name_id)
        if text:
            resolved_hobbies.append(text)

    for tag_id in expert_ids:
        tag_entry = tag_data.get(tag_id)
        if not tag_entry:
            continue
        name_id = tag_entry.get("tagName", {}).get("id")
        if not name_id:
            continue
        text = general.resolve_text(language[lang], name_id)
        if text:
            resolved_experts.append(text)

    for tag_id in prefer_ids:
        tag_entry = tag_data.get(tag_id)
        if not tag_entry:
            continue
        name_id = tag_entry.get("tagName", {}).get("id")
        if not name_id:
            continue
        text = general.resolve_text(language[lang], name_id)
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
        return general.resolve_text(language[lang], desc_id)

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
            pot_names[level - 1] = general.resolve_text(language[lang], name_id)

        effect_key = f"{effect_operator_id}_potential_{level}"
        effect_entry = potential_effect.get(effect_key, {})
        desc_id = effect_entry.get("desc", {}).get("id")
        raw_desc = ""
        if desc_id and desc_id != "0":
            raw_desc = general.resolve_text(language[lang], desc_id)
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
                        if re.match(rf"^{re.escape(bb_key)}([+\-*/].*)?(:0(\.[0#]+)?%?)?$", placeholder):
                            expr = placeholder.split(':')[0]
                            expr = expr.replace(bb_key, str(float_value))
                            try:
                                evaluated = eval(expr)
                            except Exception:
                                evaluated = float_value
                            
                            if placeholder.endswith(("%", ":0%")):
                                evaluated_str = f"{round(evaluated * 100, 2)}%".replace(".0%", "%")
                            else:
                                prec_match = re.search(r":0\.(\d+)", placeholder)
                                if prec_match:
                                    precision = len(prec_match.group(1))
                                    evaluated_str = f"{evaluated:.{precision}f}"
                                else:
                                    evaluated_str = f"{round(evaluated, 2):g}"
                            
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
                    for enum_block in enums_table:
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
                item_name = general.resolve_text(language[lang], name_id)
                item_templates.append(f"{item_name} x{count}")
        
        results[wiki_key] = ", ".join(item_templates)

    return f"""|e1 = {results['e1']}
|e2 = {results['e2']}
|e3 = {results['e3']}
|e4 = {results['e4']}"""

def get_operator_combat_skills(operator_id, char_growth, skill_patch, language, weapon, wiki_skills={}, lang="en"):
    text_table = language[lang]
    cdata = char_growth.get(operator_id)
    if not cdata or not isinstance(cdata, dict):
        return ""

    def clean_text(text):
        return re.sub(r"<.*?>", "", text).strip()

    def wrap_label(text, label):
        return text.replace(label, f"<b>{label}</b>")

    def resolve_blackboard_placeholders(text, skill_ids):
        resolved = {}
        for s_id in skill_ids:
            skill_entry = skill_patch.get(s_id)
            if not skill_entry: continue
            bundles = skill_entry.get("SkillPatchDataBundle", [])
            for bundle in bundles:
                blackboard = bundle.get("blackboard", [])
                for entry in blackboard:
                    key, val = entry.get("key"), entry.get("value")
                    if key and val is not None and (key not in resolved or resolved[key] == 0):
                        resolved[key] = val

        for key, val in resolved.items():
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
                data_list = bundle.get("subDescDataList", []) or []
                for pos, entry in enumerate(data_list):
                    nid = entry.get("name", {}).get("id")
                    value = entry.get("desc", "")
                    condition_id = entry.get("conditionId", "")
                    if nid and str(nid) != "0":
                        label_key = str(nid)
                        stat_label = text_table.get(label_key, "").strip()
                        if not stat_label: stat_label = f"UNKNOWN_{label_key}"
                        group_key = (condition_id, s_id, pos)
                        if group_key not in stat_groups:
                            stat_groups[group_key] = {"label": stat_label, "values": []}
                        if value != "": stat_groups[group_key]["values"].append(value)
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

    dual_mode = any(
        bool(skill_map.get(f"{operator_id}_{s_key}", {}).get("conditionIcon1")) and
        skill_map.get(f"{operator_id}_{s_key}", {}).get("conditionIcon1") !=
        skill_map.get(f"{operator_id}_{s_key}", {}).get("conditionIcon2")
        for s_key, _, _ in skill_order
    )
    passes = [1, 2] if dual_mode else [None]

    tab_names = {}
    if dual_mode:
        for s_key, _, _ in skill_order:
            skill = skill_map.get(f"{operator_id}_{s_key}")
            if skill:
                for i in (1, 2):
                    nid = str(skill.get(f"conditionName{i}", {}).get("id", "0"))
                    if nid != "0":
                        name = text_table.get(nid, "").strip()
                        if name:
                            tab_names[i] = name
                if len(tab_names) == 2:
                    break

    pass_results = {k: [] for k in passes}

    for pass_num in passes:
        for s_key, type_num, icon_prefix in skill_order:
            skill = skill_map.get(f"{operator_id}_{s_key}")
            if not skill: continue

            icon_suffix = weapon_sanitized if s_key == "NormalAttack" else operator_name
            name_text = text_table.get(str(skill.get("name", {}).get("id", "")), "")

            base_desc = text_table.get(str(skill.get("desc", {}).get("id", "")), "")

            raw_desc = ""
            condition_prefix = ""
            if pass_num is not None:
                cdesc_id = str(skill.get(f"conditionDesc{pass_num}", {}).get("id", "0"))
                cpost_id = str(skill.get(f"conditionPostDesc{pass_num}", {}).get("id", "0"))
                cdesc = text_table.get(cdesc_id, "").strip() if cdesc_id != "0" else ""
                cpost = text_table.get(cpost_id, "").strip() if cpost_id != "0" else ""
                if cdesc:
                    cdesc_clean = re.sub(r'/\*|\*/', '', cdesc).strip()
                    if s_key == "ComboSkill" and cpost:
                        condition_prefix = cdesc_clean
                        raw_desc = cpost
                    else:
                        parts = [p for p in (base_desc, cdesc_clean, cpost) if p]
                        raw_desc = "\n".join(parts)

            if not raw_desc:
                raw_desc = base_desc

            skill_ids = skill.get("skillIdList", [])
            desc_text = resolve_blackboard_placeholders(raw_desc, skill_ids)
            desc_text = re.sub(r'\{floor:[^{}]+\}', 'N', desc_text)
            desc_text = efdb_format(desc_text)
            desc_text = clean_text(desc_text)

            if s_key == "NormalAttack":
                desc_text = wrap_label(desc_text, "BASIC ATTACK:")
                desc_text = desc_text.replace("\nDIVE ATTACK:", "<b>DIVE ATTACK:</b>")
                desc_text = desc_text.replace("\nFINISHER:", "<b>FINISHER:</b>")
            elif s_key in ["NormalSkill", "UltimateSkill"]:
                desc_text = "<b>SKILL DESCRIPTION:</b> " + desc_text
            elif s_key == "ComboSkill":
                desc_text = wrap_label(desc_text, "COMBO TRIGGER:")
                if "\n" in desc_text:
                    desc_text = desc_text.replace("\n", "<br /><b>SKILL DESCRIPTION:</b> ", 1)
                if condition_prefix:
                    cond_text = resolve_blackboard_placeholders(condition_prefix, skill_ids)
                    cond_text = re.sub(r'\{floor:[^{}]+\}', 'N', cond_text)
                    cond_text = efdb_format(cond_text)
                    cond_text = clean_text(cond_text)
                    cond_text = cond_text.replace("\n", "<br />")
                    desc_text = cond_text + "<br />" + desc_text
            desc_text = desc_text.replace("\n", "<br />")

            stat_lines, idx = [], 1
            cost_line = extract_cost_or_cooldown(skill_ids, s_key)
            if cost_line:
                l, v = cost_line
                stat_lines.append(f"|stat{idx}= {l}, {', '.join(v)}")
                idx += 1

            stat_groups = extract_skill_stats(skill_ids)
            active_condition = skill.get(f"conditionId{pass_num}", "") if pass_num is not None else None
            for (condition_id, _s_id, _pos), group in stat_groups.items():
                if active_condition is not None and condition_id and condition_id != active_condition:
                    continue
                display_label = group["label"]
                vals = group["values"]
                stat_lines.append(f"|stat{idx}= {display_label}, {', '.join(vals)}" if vals else f"|stat{idx}= {display_label}")
                idx += 1

            if not stat_lines: stat_lines = ["|stat1="]

            icon_num = "" if s_key == "NormalAttack" else (str(pass_num) if pass_num is not None else "")
            stat_block = "\n".join(stat_lines)
            pass_results[pass_num].append(f"""{{{{Combat skill
|name= {name_text}
|icon= {icon_prefix}-{icon_suffix}{icon_num}
|type= {{{{SB|{type_num}}}}}
|info= {wiki_skills.get(name_text, "")}
|desc= {desc_text}
{stat_block}
}}}}""")

    if dual_mode:
        tab1 = tab_names.get(1, "1")
        tab2 = tab_names.get(2, "2")
        block1 = "\n".join(pass_results[1])
        block2 = "\n".join(pass_results[2])
        return f"<tabber>\n{tab1}=\n{block1}\n|-|\n{tab2}=\n{block2}\n</tabber>"

    return "\n".join(pass_results[None])

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

def main_attribute_talent(operator_id, char_growth, language, mainAttr, wiki_talents={}, lang="en"):
    text_table = language.get(lang, {})
    cdata = char_growth.get(operator_id)
    if not cdata:
        return ""

    talent_map = cdata.get("talentNodeMap", {})
    suffixes = ["1", "3", "5", "7"]
    talent_name = ""
    talent_icon = mainAttr
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

            if talent_icon == mainAttr:
                for mod in attr_info.get("attributeModifiers", []):
                    name = ATTRIBUTE_TYPE.get(mod.get("attrType"))
                    if name and name != mainAttr:
                        talent_icon = f"{mainAttr} {name}"
                        break

            break_stage = attr_info.get("breakStage", 0)
            conds[i] = f"Elite {break_stage}"
            desc_id = str(attr_info.get("desc", {}).get("id", "0"))
            if desc_id != "0":
                descs[i] = text_table.get(desc_id, "").strip()

    return f"""{{{{Operator talent
|name = {talent_name}
|icon = {talent_icon}
|info = {wiki_talents.get(talent_name, "")}
|cond1 = {conds[0]}
|desc1 = {descs[0]}
|cond2 = {conds[1]}
|desc2 = {descs[1]}
|cond3 = {conds[2]}
|desc3 = {descs[2]}
|cond4 = {conds[3]}
|desc4 = {descs[3]}
}}}}"""

def operator_outfit_talent(operator_id, char_growth, language, wiki_talents={}, lang="en"):
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
|info = {wiki_talents.get(talent_name, "")}
|cond1 = {conds[0]}
|desc1 = {descs[0]}
|cond2 = {conds[1]}
|desc2 = {descs[1]}
|cond3 = {conds[2]}
|desc3 = {descs[2]}
}}}}"""

def operator_passive_talents(operator_id, operator_name, char_growth, potential_effect, language, enums_table, wiki_talents={}, lang="en"):
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
                talent_names[i] = general.resolve_text(language[lang], name_id)

            effect_key = f"{effect_operator_id}_talent_{current_level}"
            effect_entry = potential_effect.get(effect_key, {})
            desc_id = effect_entry.get("desc", {}).get("id")
            raw_desc = ""
            
            if desc_id and desc_id != "0":
                raw_desc = general.resolve_text(language[lang], desc_id)
                
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
                                    evaluated_str = f"{round(evaluated * 100, 2):g}%"
                                else:
                                    prec_match = re.search(r":0\.(\d+)", placeholder)
                                    if prec_match:
                                        precision = len(prec_match.group(1))
                                        evaluated_str = f"{evaluated:.{precision}f}"
                                    else:
                                        evaluated_str = f"{round(evaluated, 2):g}"

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
                        for enum_block in enums_table:
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

    talent1_name = talent_names[0] or talent_names[1] or talent_names[2]
    talent2_name = talent_names[3] or talent_names[4] or talent_names[5]
    return f"""{{{{Operator talent
|name = {talent1_name}
|icon = {operator_name} Talent 1 icon
|info = {wiki_talents.get(talent1_name, "")}
|cond1 = {conds[0]}
|desc1 = {descs[0]}
|cond2 = {conds[1]}
|desc2 = {descs[1]}
|cond3 = {conds[2]}
|desc3 = {descs[2]}
}}}}
{{{{Operator talent
|name = {talent2_name}
|icon = {operator_name} Talent 2 icon
|info = {wiki_talents.get(talent2_name, "")}
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

    talent_icon = mainAttr
    for suffix in ["1", "3", "5", "7"]:
        node = talent_map.get(f"{operator_id}_{suffix}")
        if node:
            attr_info = node.get("attributeNodeInfo", {})
            if talent_icon == mainAttr:
                for mod in attr_info.get("attributeModifiers", []):
                    name = ATTRIBUTE_TYPE.get(mod.get("attrType"))
                    if name and name != mainAttr:
                        talent_icon = f"{mainAttr} {name}"
                        break
            stage = attr_info.get("breakStage", 0)
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
|attr = {talent_icon}
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
    postfixes = ["", "", "", ""]
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
            postfixes[i] = s_data.get("skillNamePostfix", "")
            name_id = str(s_data.get("name", {}).get("id", "0"))
            if name_id != "0":
                raw_name = general.resolve_text(language[lang], name_id)
                clean_name = re.split(r'[\s\u0370-\u03ff\u1f00-\u1fff]+$', raw_name)[0]
                clean_name = re.split(r'\s+[IVXLC]+$', clean_name)[0]
                talent_names[i] = clean_name.strip()
            
            desc_id = str(s_data.get("desc", {}).get("id", "0"))
            if desc_id != "0":
                raw_desc = general.resolve_text(language[lang], desc_id)
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
|postfix1 = {postfixes[0]}
|cond1 = {conds[0]}
|desc1 = {descs[0]}
|postfix2 = {postfixes[1]}
|cond2 = {conds[1]}
|desc2 = {descs[1]}
}}}}
{{{{Operator base skill
|name = {talent_names[2] or talent_names[3]}
|icon = {icons[2] or icons[3]}
|facility = {facilities[2] or facilities[3]}
|postfix1 = {postfixes[2]}
|cond1 = {conds[2]}
|desc1 = {descs[2]}
|postfix2 = {postfixes[3]}
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

def resolve_cv_name(operator_data, char_table, operator_name, language, cv_key, lang="en"):
    if operator_name == "Endministrator":
        mirror_data = char_table.get("chr_0003_endminf", {})
        
        try:
            m_cv_id = operator_data["cvName"][cv_key]["id"]
            f_cv_id = mirror_data.get("cvName", {}).get(cv_key, {}).get("id", "0")
            
            m_cv = general.resolve_text(language[lang], m_cv_id) if m_cv_id != "0" else ""
            f_cv = general.resolve_text(language[lang], f_cv_id) if f_cv_id != "0" else ""
            
            if f_cv and m_cv:
                if f_cv == m_cv: return f_cv
                return f"\n*{f_cv} (Female) \n*{m_cv} (Male)"
            return f_cv or m_cv or ""
        except KeyError:
            pass

    try:
        cv_id = operator_data["cvName"][cv_key]["id"]
        if cv_id != "0":
            return general.resolve_text(language[lang], cv_id)
    except KeyError:
        pass
    return ""

def get_operator_archives(operator_data, language, lang="en"):
    records = operator_data.get("profileRecord", [])
    if not records:
        return ""

    archive_blocks = []

    for record in records:
        title_id = record.get("recordTitle", {}).get("id")
        title = general.resolve_text(language[lang], title_id) if title_id else ""
        desc_id = record.get("recordDesc", {}).get("id")
        raw_desc = general.resolve_text(language[lang], desc_id) if desc_id else ""
        
        if raw_desc:
            raw_desc = raw_desc.replace("<@profile.key>", "").replace("</>", "")
            formatted_desc = raw_desc.replace("\n", "<br/>")
        else:
            formatted_desc = ""

        block = f"{{{{Archive\n|title = {title}\n|text = {formatted_desc}\n}}}}"
        archive_blocks.append(block)

    return "\n\n".join(archive_blocks)

def get_operator_dialogue(operator_data, language, lang="en"):
    voice_records = operator_data.get("profileVoice", [])
    if not voice_records:
        return ""

    dialogue_entries = []

    for entry in voice_records:
        title_id = entry.get("voiceTitle", {}).get("id")
        title = general.resolve_text(language[lang], title_id).strip() if title_id else ""

        desc_id = entry.get("voiceDesc", {}).get("id")
        dialogue = general.resolve_text(language[lang], desc_id).replace("\n", " ").strip() if desc_id else ""

        if title.startswith("Topic:"):
            topic_name = title.split(":", 1)[1].strip()
            number = 37
            line = f"{{{{Operator dialogue cell|no={number}|topic={topic_name}|dialogue={dialogue}}}}}"
            dialogue_entries.append((number, line))
            continue

        number = DIALOGUE_TYPE.get(title)
        if number is None:
            continue

        line = f"{{{{Operator dialogue cell|no={number}|dialogue={dialogue}}}}}"
        dialogue_entries.append((number, line))

    dialogue_entries.sort(key=lambda x: x[0])

    return "\n".join([entry[1] for entry in dialogue_entries])

def get_operator_recommended_weapons(operator_id, rec_weapon, weapon_basic, language, lang="en"):
    rec_data = rec_weapon.get(operator_id, {})
    if not rec_data:
        return "", ""

    def resolve_weapon_names(weapon_ids):
        names = []
        for wpn_id in weapon_ids:
            wpn_data = weapon_basic.get(wpn_id)
            if not wpn_data:
                continue
            name_id = wpn_data.get("engName", {}).get("id")
            name = general.resolve_text(language[lang], name_id)
            if name:
                names.append(name)
        return ", ".join(names)

    matskill = resolve_weapon_names(rec_data.get("weaponIds1", []))
    matstats = resolve_weapon_names(rec_data.get("weaponIds2", []))

    return matskill, matstats