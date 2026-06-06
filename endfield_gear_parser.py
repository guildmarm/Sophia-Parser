import lib.io as io
import lib.general as general
import lib.helpers.gear as gear
import lib.game_files as game_files
import lib.constants as const
import lib.format_text as format_text
import os

# Output file
GEAR_PAGE_OUTPUT = os.path.join(const.OUTPUT_DIR, "full_gear_page_data.txt")
GEAR_SET_TEMPLATE_OUTPUT = os.path.join(const.OUTPUT_DIR, "template_gear_set_data.txt")
GEAR_NAV_TEMPLATE_OUTPUT = os.path.join(const.OUTPUT_DIR, "template_gear_nav_data.txt")
GEAR_IMAGE_ICON_OUTPUT = os.path.join(const.OUTPUT_DIR, "gear_image_icon_data.txt")
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

# Gear set lines
gear_set_lines = gear.build_gear_set_lines(equip_table, item_table, equip_suit, language)

# Gear nav lines
gear_armor, gear_glove, gear_kit = gear.build_gear_nav_lists(equip_table, item_table, language)

# Make that sausage
with open(GEAR_PAGE_OUTPUT, "w", encoding="utf-8") as out:
    for gear_id, gear_data in equip_table.items():
        item_data = item_table.get(gear_id)
        if not item_data:
            continue

        # Gear formula source
        source_text = gear.resolve_gear_sources_from_formula(gear_id, equip_formula, item_table, system_jump_table, language)

        # Gear names
        name_id = item_data.get("name", {}).get("id")
        gear_name = general.resolve_text(language["en"], name_id)
        gear_name_clean = general.sanitize_name(gear_name)
        gear_name_image = general.sanitize_image_name(gear_name)
        cn_name = general.resolve_text(language["cn"], name_id)
        tc_name = general.resolve_text(language["tc"], name_id)
        jp_name = general.resolve_text(language["jp"], name_id)
        kr_name = general.resolve_text(language["kr"], name_id)
        sp_name = general.resolve_text(language["sp"], name_id)
        ru_name = general.resolve_text(language["ru"], name_id)

        # Descriptions
        desc = general.resolve_text(language["en"], item_data.get("desc", {}).get("id"))
        deco_desc = general.resolve_text(language["en"], item_data.get("decoDesc", {}).get("id"))

        # Gear type and rarity
        gear_type = gear.get_gear_part_type(gear_data)
        rarity = item_data.get("rarity", "")

        # Gear level and region
        gear_level = gear_data.get("minWearLv", "")
        gear_region = gear.get_gear_region(gear_data)

        # Gear set and effect
        gear_set, set_effect = gear.resolve_gear_set_and_effect(gear_id, equip_suit, skill_patch, language)
        set_effect_formatted = format_text.efdb_format(set_effect)
        gear_setname = f"{gear_set}" if gear_set else ""
        gear_set_template = f"{{{{Gear Set|{gear_set}}}}}" if gear_set else ""
        gear_set_section = f"==Set Items==" if gear_set else ""

        # Gear base and artificed stats
        (gear_def, gear_pstat, gear_pvalue, p_enhanced, gear_sstat, gear_svalue, s_enhanced, gear_tstat, gear_tvalue, t_enhanced) = gear.resolve_gear_attributes_sections(gear_data, attribute_filter, language)
        gear_artifice = gear.resolve_artifice_bool(p_enhanced, s_enhanced, t_enhanced)
        gear_def = gear.format_stat_value(gear_def, gear_artifice)
        gear_pvalue = gear.format_stat_value(gear_pvalue, gear_artifice)
        gear_svalue = gear.format_stat_value(gear_svalue, gear_artifice)
        gear_tvalue = gear.format_stat_value(gear_tvalue, gear_artifice)

        # Gear recipe
        gear_recipe = gear.resolve_gear_recipe(gear_id, equip_formula, item_table, language)

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

{{{{-stop-}}}}

""")

# Push icon redirects
with open(GEAR_IMAGE_ICON_OUTPUT, "w", encoding="utf-8") as out:
    for gear_id, gear_data in equip_table.items():
        item_data = item_table.get(gear_id)
        if not item_data:
            continue

        # Gear names
        name_id = item_data.get("name", {}).get("id")
        gear_name = general.resolve_text(language["en"], name_id)
        gear_name_clean = general.sanitize_name(gear_name)
        gear_name_image = general.sanitize_image_name(gear_name)
        
        out.write(f"""{{{{-start-}}}}
'''File:{gear_name_clean}_icon.png'''
#REDIRECT [[File:{gear_name_image}.png]]

{{{{-stop-}}}}

""")

# Make that sausage AGAIN (This is for the Gear Set template)
with open(GEAR_SET_TEMPLATE_OUTPUT, "w", encoding="utf-8") as out:
        out.write(f"""{{{{-start-}}}}
'''Template:Gear Set'''
<includeonly>
{{| width="100%" class="wikitable" cellpadding="5" style="margin-top:0; font-size:16px; border-style: hidden;"
! style="background-color:#2a2a2a; border-bottom: hidden; padding: 5px;" | [[{{{{{{1}}}}}}]] Gear Set
|-
| <div style="display: block; text-align: center; border-style: hidden;">{{{{#switch: {{{{{{1}}}}}}
{gear_set_lines}
}}}}</div>
|}}</includeonly><noinclude>{{{{Documentation}}}}[[Category:Table templates]]</noinclude>
{{{{-stop-}}}}
""")

# Make that sausage YET AGAIN (This is for the Gear Nav template)
with open(GEAR_NAV_TEMPLATE_OUTPUT, "w", encoding="utf-8") as out:
        out.write(f"""{{{{-start-}}}}
'''Template:Gears'''
<onlyinclude>{{{{Navbox
| Title = Gear
| State = {{{{{{state|collapsed}}}}}}
| Group style = padding:5px; vertical-align:middle; text-align:center; font-size:14px;
| Subgroup style = padding:5px; vertical-align:middle; text-align:left; font-size:14px;
| List style = vertical-align:middle; font-size:12px;
| Group 1 = [[File:Armor Gear Icon.png|36px|link=]]<br>Armor
| List 1 = {gear_armor}

| Group 2 = [[File:Glove Gear Icon.png|36px|link=]]<br>Gloves
| List 2 = {gear_glove}

| Group 3 = [[File:Kit Gear Icon.png|36px|link=]]<br>Kit
| List 3 = {gear_kit}

}}}}</onlyinclude><noinclude>This navbox template is used as a means to navigate a list of [[gears]].

To use this template, add <code><nowiki>{{{{Gears}}}}</nowiki></code> at the end of an article.

[[Category:Navboxes]]</noinclude>

{{{{-stop-}}}}
""")
