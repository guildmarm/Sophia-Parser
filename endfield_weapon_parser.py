import parser_lib.io as io
import parser_lib.helpers as helpers
import parser_lib.game_files as game_files
import parser_lib.constants as const
import os

# Output file
OUTPUT_FILE = os.path.join(const.OUTPUT_DIR, "full_weapon_page_data.txt")
os.makedirs(const.OUTPUT_DIR, exist_ok=True)

paths = game_files.build_paths(const.INPUT_DIR)

weapon_basic = io.load_json(paths["weapon_basic"])
item_table = io.load_json(paths["item_table"])
skill_patch = io.load_json(paths["skill_patch"])
breakthrough_table = io.load_json(paths["weapon_breakthrough"])
weapon_upgrade_table = io.load_json(paths["weapon_upgrade"])
system_jump_table = io.load_json(paths["system_jump"])

# Load language files
language = io.load_languages(const.INPUT_DIR)

# Make that sausage
with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for weapon_id, weapon_data in weapon_basic.items():
        item_data = item_table.get(weapon_id)
        if not item_data:
            continue

        source_ids = item_data.get("obtainWayIds", [])
        source_text = helpers.resolve_sources(source_ids, system_jump_table, language)
        
        # Weapon names
        name_id = item_data.get("name", {}).get("id")
        weapon_name = helpers.resolve_text(language["en"], name_id)
        weapon_name_clean = helpers.sanitize_name(weapon_name)
        weapon_name_image = helpers.sanitize_image_name(weapon_name)
        cn_name = helpers.resolve_text(language["cn"], name_id)
        tc_name = helpers.resolve_text(language["tc"], name_id)
        jp_name = helpers.resolve_text(language["jp"], name_id)
        kr_name = helpers.resolve_text(language["kr"], name_id)
        sp_name = helpers.resolve_text(language["sp"], name_id)
        ru_name = helpers.resolve_text(language["ru"], name_id)

        # Weapon descriptions. desc and decoDesc are the tooltip flavor text. weaponDesc is the Basic Info section.
        desc = helpers.resolve_text(language["en"], item_data.get("desc", {}).get("id"))
        deco_desc = helpers.resolve_text(language["en"], item_data.get("decoDesc", {}).get("id"))
        weapon_desc = helpers.resolve_text(language["en"], weapon_data.get("weaponDesc", {}).get("id")) or ""
        weapon_desc = weapon_desc.replace("\n", "<br>")

        # Weapon type and rarity
        weapon_type = helpers.get_weapon_type(weapon_id)
        rarity = weapon_data.get("rarity", "")

        # Weapon skills
        weapon_skill_ids = weapon_data.get("weaponSkillList", [])
        resolved_skills = [helpers.resolve_skill_name(sid, skill_patch, language) for sid in weapon_skill_ids if sid]

        weapon_potential_id = weapon_data.get("weaponPotentialSkill", "")
        resolved_potential = helpers.resolve_skill_name(weapon_potential_id, skill_patch, language)

        # Tuning items
        break_items = helpers.resolve_tuning_items(weapon_id, weapon_basic, breakthrough_table, item_table, language)
        t_values = ["", "", "", ""]
        for i in range(min(4, len(break_items))):
            t_values[i] = break_items[i]

        # Base atk
        level_template_id = weapon_data.get("levelTemplateId")
        batk_values = helpers.get_batk_values(level_template_id, weapon_upgrade_table)
        batk_str = ", ".join(batk_values)

        # Output
        out.write(f"""{{{{-start-}}}}
'''{weapon_name_clean}'''
{{{{Weapon infobox
|icon = {weapon_type}
|name = {weapon_name}
|rarity = {rarity}
|images = 
{weapon_name_image} icon.png:Icon;
{weapon_name_image}.png:Full;
{weapon_name_image} max model.png:Max
|filename = {weapon_id}
|cnname = {cn_name}
|tcname = {tc_name}
|jpname = {jp_name}
|krname = {kr_name}
|spname = {sp_name}
|runame = {ru_name}
|type = {weapon_type}
|source = {source_text}}}}}
'''{weapon_name}''' is a {rarity}★ [[{weapon_type}]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{desc}|{deco_desc}}}}}

==Stats==

{{{{Weapon data
|BATK = {batk_str}
|pot = Skill {{{{Color|{resolved_potential}|0}}}} improved.
|t1 = {t_values[0]}
|t2 = {t_values[1]}
|t3 = {t_values[2]}
|t4 = {t_values[3]}
}}}}

==Skills==
{{{{Weapon skill|{weapon_type}|{'|'.join(resolved_skills)}}}}}

==Basic Info==
{{{{Quote|{weapon_desc}}}}}


==Navigation==
{{{{Weapons}}}}

[[Category:Weapons]]
[[Category:{weapon_type}]]

{{{{-stop-}}}}

""")
