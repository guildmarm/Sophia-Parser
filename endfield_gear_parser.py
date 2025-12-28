import parser_lib.io as io
import parser_lib.helpers as helpers
import parser_lib.game_files as game_files
import parser_lib.constants as const
import parser_lib.format_text as format_text
import os

# Output file
OUTPUT_FILE = os.path.join(const.OUTPUT_DIR, "full_gear_page_data.txt")
os.makedirs(const.OUTPUT_DIR, exist_ok=True)

paths = game_files.build_paths(const.INPUT_DIR)

item_table = io.load_json(paths["item_table"])
equip_formula = io.load_json(paths["equip_formula"])
equip_suit = io.load_json(paths["equip_suit"])
equip_table = io.load_json(paths["equip_table"])
system_jump_table = io.load_json(paths["system_jump"])
skill_patch = io.load_json(paths["skill_patch"])
attribute_filter = io.load_json(paths["attribute_filter"])

# Load language files
language = io.load_languages(const.INPUT_DIR)

# Make that sausage
with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for gear_id, gear_data in equip_table.items():
        item_data = item_table.get(gear_id)
        if not item_data:
            continue

        source_ids = item_data.get("obtainWayIds", [])
        source_text = helpers.resolve_sources(source_ids, system_jump_table, language)

        # Gear names
        name_id = item_data.get("name", {}).get("id")
        gear_name = helpers.resolve_text(language["en"], name_id)
        gear_name_clean = helpers.sanitize_name(gear_name)
        gear_name_image = helpers.sanitize_image_name(gear_name)
        cn_name = helpers.resolve_text(language["cn"], name_id)
        tc_name = helpers.resolve_text(language["tc"], name_id)
        jp_name = helpers.resolve_text(language["jp"], name_id)
        kr_name = helpers.resolve_text(language["kr"], name_id)
        sp_name = helpers.resolve_text(language["sp"], name_id)
        ru_name = helpers.resolve_text(language["ru"], name_id)

        # Descriptions
        desc = helpers.resolve_text(language["en"], item_data.get("desc", {}).get("id"))
        deco_desc = helpers.resolve_text(language["en"], item_data.get("decoDesc", {}).get("id"))

        # Gear type and rarity
        gear_type = helpers.get_gear_part_type(gear_data)
        rarity = item_data.get("rarity", "")

        # Gear level and region
        gear_level = gear_data.get("minWearLv", "")
        gear_region = helpers.get_gear_region(gear_data)

        # Gear set and effect
        gear_set, set_effect = helpers.resolve_gear_set_and_effect(gear_id, equip_suit, skill_patch, language)
        set_effect_formatted = format_text.efdb_format(set_effect)
        gear_setname = f"[[{gear_set}]]" if gear_set else ""
        gear_set_template = f"{{{{Gear Set|{gear_set}}}}}" if gear_set else ""
        gear_set_section = f"==Set Items==" if gear_set else ""

        # Gear base and artificed stats
        (gear_def, gear_pstat, gear_pvalue, p_enhanced, gear_sstat, gear_svalue, s_enhanced, gear_tstat, gear_tvalue, t_enhanced) = helpers.resolve_gear_attributes_sections(gear_data, attribute_filter, language)
        gear_artifice = helpers.resolve_artifice_bool(p_enhanced, s_enhanced, t_enhanced)
        gear_def = helpers.format_stat_value(gear_def, gear_artifice)
        gear_pvalue = helpers.format_stat_value(gear_pvalue, gear_artifice)
        gear_svalue = helpers.format_stat_value(gear_svalue, gear_artifice)
        gear_tvalue = helpers.format_stat_value(gear_tvalue, gear_artifice)

        # Gear recipe
        gear_recipe = helpers.resolve_gear_recipe(gear_id, equip_formula, item_table, language)

        out.write(f"""{{{{-start-}}}}
'''{gear_name_clean}'''
{{{{Gear infobox
|name = {gear_name}
|image = {gear_name_image}.png
|filename = {gear_id}
|cnname = {cn_name}
|tcname = {tc_name}
|jpname = {jp_name}
|krname = {kr_name}
|spname = {sp_name}
|runame = {ru_name}
|rarity = {rarity}
|artifice = {gear_artifice}
|type = {gear_type}
|level = {gear_level}
|region = {gear_region}
|source = {source_text}
}}}}
'''{gear_name}''' is a {{{{gear|{rarity}|{gear_type}}}}}gear item.

{{{{Item description|{desc}|{deco_desc}}}}}

==Stats==
{{{{Gear data
|defense = {gear_def}
|pstat = {gear_pstat}
|pvalue = {gear_pvalue}
|sstat = {gear_sstat}
|svalue = {gear_svalue}
|tstat = {gear_tstat}
|tvalue = {gear_tvalue}
|setname = {gear_setname}
|seteffect = {set_effect_formatted}
|recipe = {gear_recipe}
}}}}

{gear_set_section}
{gear_set_template}
{{{{Gears|state=collapsed}}}}
[[Category:Gear]]
[[Category:{gear_type}]]

{{{{-stop-}}}}

""")
