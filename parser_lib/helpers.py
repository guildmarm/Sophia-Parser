from .io import load_json
from .constants import LANGUAGE_FILES

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

    # Skip first lv1 step; start at lv20
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