import parser_lib.io as io
import parser_lib.helpers as helpers
import parser_lib.game_files as game_files
import parser_lib.constants as const
import os

# Output file
OPERATOR_PAGE_OUTPUT = os.path.join(const.OUTPUT_DIR, "full_operator_page_data.txt")
os.makedirs(const.OUTPUT_DIR, exist_ok=True)

paths = game_files.build_paths(const.INPUT_DIR)

item_table = io.load_json(paths["item_table"])
skill_patch = io.load_json(paths["skill_patch"])
char_table = io.load_json(paths["character_table"])
char_growth = io.load_json(paths["character_growth"])
char_profession = io.load_json(paths["character_profession"])
char_tags = io.load_json(paths["character_tags"])
char_battle_tags = io.load_json(paths["character_battle_tags"])
char_tag_des = io.load_json(paths["character_tag_des"])
char_potential = io.load_json(paths["character_potential"])
char_base_skill = io.load_json(paths["character_base_skill"])
base_skill = io.load_json(paths["base_skill"])
potential_effect = io.load_json(paths["potential_effect"])
tag_data = io.load_json(paths["tag_data"])
gacha_pool_content = io.load_json(paths["gacha_pool_content"])
gacha_pool = io.load_json(paths["gacha_pool"])
enums_table = io.load_json(paths["enums_table"])

# Load language files
language = io.load_languages(const.INPUT_DIR)

# Make that sausage
with open(OPERATOR_PAGE_OUTPUT, "w", encoding="utf-8") as out:
    for operator_id, operator_data in char_table.items():
        if operator_id in ("chr_0003_endminf", "chr_9000_endmin"):
            continue

        # Operator names
        name_id = operator_data["name"]["id"]
        operator_name = helpers.resolve_text(language["en"], name_id)
        operator_name_clean = helpers.sanitize_name(operator_name)
        
        # Make sure the endmin's page has both images and file names
        if operator_name == "Endministrator":
            operator_display_id = "chr_0003_endminf, chr_0002_endminm"
            operator_name_image = (
                f"{helpers.sanitize_image_name(operator_name)}_(Female)_Splash Art.png:Female;\n"
                f"{helpers.sanitize_image_name(operator_name)}_(Male)_Splash Art.png:Male"
            )
        else:
            operator_display_id = operator_id
            operator_name_image = f"{helpers.sanitize_image_name(operator_name)} Splash Art.png"
        cn_name = helpers.resolve_text(language["cn"], name_id)
        tc_name = helpers.resolve_text(language["tc"], name_id)
        jp_name = helpers.resolve_text(language["jp"], name_id)
        kr_name = helpers.resolve_text(language["kr"], name_id)
        sp_name = helpers.resolve_text(language["sp"], name_id)
        ru_name = helpers.resolve_text(language["ru"], name_id)

        # Operator info
        rarity = operator_data.get("rarity", "")
        prof_id = operator_data.get("profession")
        prof_name_id = char_profession[str(prof_id)]["name"]["id"]
        profession = helpers.resolve_text(language["en"], prof_name_id)
        weapon = const.WEAPON_TYPE.get(operator_data.get("weaponType"), "")
        element = const.ELEMENT_TYPE.get(operator_data.get("charTypeId"), "")
        faction = helpers.resolve_operator_faction(operator_id, char_tags, tag_data, language)
        operator_tags = helpers.resolve_operator_tags(operator_data, char_battle_tags, language)
        banner = helpers.resolve_operator_gacha_pools(operator_id, gacha_pool_content, gacha_pool, language)
        operator_quote = helpers.get_operator_quote(operator_data, operator_id, language)

        # Operator stats
        mainAttr = const.ATTRIBUTE_TYPE.get(operator_data.get("mainAttrType"), "")
        subAttr = const.ATTRIBUTE_TYPE.get(operator_data.get("subAttrType"), "")
        extracted_stats = helpers.get_operator_attributes(char_table, operator_id)
        operator_stats = helpers.build_operator_stats_block(extracted_stats)

        # Operator infobox
        full_text, gender, birthdate, race, infection, strength, skill, tactical, originium = helpers.get_operator_profile_records(operator_data, language)
        hobbyname1, hobbyname2, expertname1, expertname2, hobbydesc1, hobbydesc2, expertdesc1, expertdesc2, prefer = helpers.get_operator_hobbies_and_expertise(operator_id, char_tags, tag_data, char_tag_des, language)

        # Operator potentials and rank up items
        operator_potentials = helpers.get_operator_potentials(operator_id, char_potential, potential_effect, language, enums_table)
        operator_upgrade_items = helpers.get_operator_upgrade_items(operator_id, char_growth, item_table, language)

        # Operator skills
        operator_combat_skills = helpers.get_operator_combat_skills(operator_id, char_growth, skill_patch, language, weapon)
        operator_skill_items = helpers.get_operator_skill_items(operator_id, char_growth, item_table, language)

        # Operator Talents and Base Skills
        operator_mainattr_talent = helpers.main_attribute_talent(operator_id, char_growth, language, mainAttr)
        operator_unique_talent = helpers.operator_passive_talents(operator_id, operator_name, char_growth, potential_effect, language, enums_table)
        operator_gear_talent = helpers.operator_outfit_talent(operator_id, char_growth, language)
        operator_talent_costs = helpers.operator_talent_costs(operator_id, char_growth, item_table, language, mainAttr)
        operator_base_skills = helpers.operator_base_skills(operator_id, char_growth, base_skill, language)
        base_skill_costs = helpers.operator_base_talent_costs(operator_id, char_growth, item_table, base_skill, language)

        # Output
        out.write(f"""{{{{-start-}}}}
'''{operator_name_clean}'''
{{{{Operator info
|name = {operator_name}
|rarity = {rarity}
|class = {profession}
|weapon = {weapon}
|element = {element}
|faction = {faction}
|tags = {operator_tags}
|main = {mainAttr}
|sub = {subAttr}
|headhunting = {banner}
|quote = {operator_quote}
}}}}
{{{{Operator tab}}}}
{{{{Operator infobox
|rarity = {rarity}star
|name = {operator_name}
|image = 
{operator_name_image}
|filename = {operator_display_id}
|cnname = {cn_name}
|tcname = {tc_name}
|jpname = {jp_name}
|krname = {kr_name}
|spname = {sp_name}
|runame = {ru_name}
|realname =  
|fileno = 
|theme = 
|illustrator = 
|jpcv = 
|cncv = 
|encv = 
|krcv = 
|gender = {gender}
|age =
|experience = 
|birthplace =
|birthdate = {birthdate}
|race = {race}
|height = 
|infection = {infection}
|strength = {strength}
|tactical = {tactical}
|skill = {skill}
|originium = {originium}
|exp1 = {expertname1}
|exp1d = {expertdesc1}
|exp2 = {expertname2}
|exp2d = {expertdesc2}
|hb1 = {hobbyname1}
|hb1d = {hobbydesc1}
|hb2 = {hobbyname2}
|hb2d = {hobbydesc2}
|prefer = {prefer}
}}}}

==Profile==


==Stats==
{{{{Operator data
|main = {mainAttr}
|sub = {subAttr}
{operator_stats}
{operator_upgrade_items}
{operator_potentials}
}}}}

==Combat Skills==
{operator_combat_skills}
{operator_skill_items}

==Talents==
{operator_mainattr_talent}
{operator_unique_talent}
{operator_gear_talent}
{operator_talent_costs}

==Base Skills==
{operator_base_skills}
{base_skill_costs}

==Changelog==
{{Changelog|
*'''EVENT_NAME_HERE''' introduced.}}

==Navigation==
{{Operators}}

{{{{-stop-}}}}

""")
