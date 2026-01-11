import lib.io as io
import lib.general as general
import lib.helpers.operator as operator
import lib.game_files as game_files
import lib.constants as const
import os
import re
import mwparserfromhell
from mwcleric.wiki_client import WikiClient

# Set endfield wiki as mw.cleric site
site = WikiClient("endfield.wiki.gg")

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

# mw.cleric helpers
def get_wiki_section(text, header):
    pattern = rf"==\s*{header}\s*==\s*(.*?)(?=\n==|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

# Make that sausage
with open(OPERATOR_PAGE_OUTPUT, "w", encoding="utf-8") as out:
    for operator_id, operator_data in char_table.items():
        if operator_id in ("chr_0003_endminf", "chr_9000_endmin"):
            continue

        # Operator names
        name_id = operator_data["name"]["id"]
        operator_name = general.resolve_text(language["en"], name_id)
        operator_name_clean = general.sanitize_name(operator_name)

        # mw.cleric input
        wiki_params = {p: "" for p in ['realname', 'fileno', 'theme', 'illustrator', 'age', 'experience', 'birthplace', 'height']}
        wiki_profile = ""
        wiki_changelog = ""

        page = site.client.pages[operator_name]
        if page.exists:
            wikitext = page.text()
            parsed_code = mwparserfromhell.parse(wikitext)
            for template in parsed_code.filter_templates():
                if template.name.matches("Operator infobox"):
                    for p in wiki_params.keys():
                        if template.has(p):
                            wiki_params[p] = str(template.get(p).value).strip()
                    break
            
            wiki_profile = get_wiki_section(wikitext, "Profile")
            wiki_changelog = get_wiki_section(wikitext, "Changelog")
        
        # Make sure the endmin's page has both images and file names
        if operator_name == "Endministrator":
            operator_display_id = "chr_0003_endminf, chr_0002_endminm"
            operator_name_image = (
                f"{general.sanitize_image_name(operator_name)}_(Female)_Splash Art.png:Female;\n"
                f"{general.sanitize_image_name(operator_name)}_(Male)_Splash Art.png:Male"
            )
        else:
            operator_display_id = operator_id
            operator_name_image = f"{general.sanitize_image_name(operator_name)} Splash Art.png"
        cn_name = general.resolve_text(language["cn"], name_id)
        tc_name = general.resolve_text(language["tc"], name_id)
        jp_name = general.resolve_text(language["jp"], name_id)
        kr_name = general.resolve_text(language["kr"], name_id)
        sp_name = general.resolve_text(language["sp"], name_id)
        ru_name = general.resolve_text(language["ru"], name_id)

        # CV names
        cn_cv = operator.resolve_cv_name(operator_data, language, "ChiCVName")
        jp_cv = operator.resolve_cv_name(operator_data, language, "JapCVName")
        en_cv = operator.resolve_cv_name(operator_data, language, "EngCVName")
        kr_cv = operator.resolve_cv_name(operator_data, language, "KorCVName")

        # Operator info
        rarity = operator_data.get("rarity", "")
        prof_id = operator_data.get("profession")
        prof_name_id = char_profession[str(prof_id)]["name"]["id"]
        profession = general.resolve_text(language["en"], prof_name_id)
        profession = "Supporter" if profession == "Support" else profession
        weapon = const.WEAPON_TYPE.get(operator_data.get("weaponType"), "")
        element = const.ELEMENT_TYPE.get(operator_data.get("charTypeId"), "")
        faction = operator.resolve_operator_faction(operator_id, char_tags, tag_data, language)
        operator_tags = operator.resolve_operator_tags(operator_data, char_battle_tags, language)
        starting_operator = operator.get_starting_operator(operator_id)
        banner = operator.resolve_operator_gacha_pools(operator_id, gacha_pool_content, gacha_pool, language)
        operator_quote = operator.get_operator_quote(operator_data, operator_id, language)

        # Operator stats
        mainAttr = const.ATTRIBUTE_TYPE.get(operator_data.get("mainAttrType"), "")
        subAttr = const.ATTRIBUTE_TYPE.get(operator_data.get("subAttrType"), "")
        extracted_stats = operator.get_operator_attributes(char_table, operator_id)
        operator_stats = operator.build_operator_stats_block(extracted_stats)

        # Operator infobox
        full_text, gender, birthdate, race, infection, strength, skill, tactical, originium = operator.get_operator_profile_records(operator_data, language)
        hobbyname1, hobbyname2, expertname1, expertname2, hobbydesc1, hobbydesc2, expertdesc1, expertdesc2, prefer = operator.get_operator_hobbies_and_expertise(operator_id, char_tags, tag_data, char_tag_des, language)

        # Operator potentials and rank up items
        operator_potentials = operator.get_operator_potentials(operator_id, char_potential, potential_effect, language, enums_table)
        operator_upgrade_items = operator.get_operator_upgrade_items(operator_id, char_growth, item_table, language)

        # Operator skills
        operator_combat_skills = operator.get_operator_combat_skills(operator_id, char_growth, skill_patch, language, weapon)
        operator_skill_items = operator.get_operator_skill_items(operator_id, char_growth, item_table, language)

        # Operator Talents and Base Skills
        operator_mainattr_talent = operator.main_attribute_talent(operator_id, char_growth, language, mainAttr)
        operator_unique_talent = operator.operator_passive_talents(operator_id, operator_name, char_growth, potential_effect, language, enums_table)
        operator_gear_talent = operator.operator_outfit_talent(operator_id, char_growth, language)
        operator_talent_costs = operator.operator_talent_costs(operator_id, char_growth, item_table, language, mainAttr)
        operator_base_skills = operator.operator_base_skills(operator_id, char_growth, base_skill, language)
        base_skill_costs = operator.operator_base_talent_costs(operator_id, char_growth, item_table, base_skill, language)

        # Output
        out.write(f"""{{{{-start-}}}}
'''{operator_name_clean}'''
{{{{Operator infobox
|name = {operator_name}
|rarity = {rarity}
|class = {profession}
|weapon = {weapon}
|element = {element}
|faction = {faction}
|tags = {operator_tags}
|main = {mainAttr}
|sub = {subAttr}
|starting = {starting_operator}
|headhunting = {banner}
|quote = {operator_quote}
|image = 
{operator_name_image}
|filename = {operator_display_id}
|cnname = {cn_name}
|tcname = {tc_name}
|jpname = {jp_name}
|krname = {kr_name}
|spname = {sp_name}
|runame = {ru_name}
|realname = {wiki_params['realname']}
|fileno = {wiki_params['fileno']}
|theme = {wiki_params['theme']}
|illustrator = {wiki_params['illustrator']}
|jpcv = {jp_cv}
|cncv = {cn_cv}
|encv = {en_cv}
|krcv = {kr_cv}
|gender = {gender}
|age = {wiki_params['age']}
|experience = {wiki_params['experience']}
|birthplace = {wiki_params['birthplace']}
|birthdate = {birthdate}
|race = {race}
|height = {wiki_params['height']}
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
{wiki_profile}

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
{wiki_changelog}

==Navigation==
{{{{Operators}}}}

{{{{-stop-}}}}

""")
