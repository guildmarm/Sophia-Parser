import lib.io as io
import lib.general as general
import lib.helpers.enemy as enemy
import lib.game_files as game_files
import lib.constants as const
import time
import os
import re
import mwparserfromhell
from argparse import ArgumentParser
from mwcleric.auth_credentials import AuthCredentials
from mwcleric.wikigg_client import WikiggClient
from mwcleric.page_modifier import PageModifierBase

parser = ArgumentParser(prog="endfield_enemy_parser")
parser.add_argument("-force", action="store_true", help="Overwrite the existing page")
parser.add_argument("-summary", help="The text used as an edit summary for the upload. If the page exists, standard messages for prepending, appending, or replacement are appended after it")
args = parser.parse_args()

auth = AuthCredentials(user_file="bot")
site = WikiggClient("endfield", credentials=auth)
lag = 10
force = args.force
summary = args.summary

paths = game_files.build_paths(const.INPUT_DIR)

item_table = io.load_json(paths["item_table"])
enemy_attr = io.load_json(paths["enemy_attribute"])
enemy_ability = io.load_json(paths["enemy_ability"])
enemy_display = io.load_json(paths["enemy_display"])
distribution_info = io.load_json(paths["distribution_info"])
enemy_drop = io.load_json(paths["enemy_drop"])
enemy_type = io.load_json(paths["enemy_type"])
enemy_group = io.load_json(paths["enemy_group"])
wiki_group = io.load_json(paths["wiki_group"])

# Load language files
language = io.load_languages(const.INPUT_DIR)

# mw.cleric helpers
def get_wiki_section(text, header):
    parsed = mwparserfromhell.parse(text)
    for section in parsed.get_sections(levels=[2]):
        headings = section.filter_headings()
        if headings and headings[0].title.strip().lower() == header.lower():
            heading_len = len(str(headings[0]))
            return str(section)[heading_len:].strip()
    return ""

enemy_name_counts = {}
duplicate_name_map = {}

for enemy_id, display_data in enemy_display.items():
    name_id = display_data.get("name", {}).get("id")
    enemy_name = general.resolve_text(language["en"], name_id)
    enemy_name_clean = general.sanitize_name(enemy_name)
    enemy_name_counts[enemy_name_clean] = enemy_name_counts.get(enemy_name_clean, 0) + 1
    duplicate_name_map.setdefault(enemy_name_clean, []).append(enemy_id)

duplicate_name_map = {k: v for k, v in duplicate_name_map.items() if len(v) > 1}

wikitexts = {}
for enemy_id, attr_data in enemy_attr.items():
    display_data = enemy_display.get(enemy_id)
    if not display_data:
        continue

    # Enemy names
    name_id = display_data.get("name", {}).get("id")
    enemy_name = general.resolve_text(language["en"], name_id)
    enemy_name_clean = general.sanitize_name(enemy_name)
    enemy_name_image = general.sanitize_image_name(enemy_name)

    # Append the ID if there are duplicates but just the last part of it
    enemy_name, enemy_name_clean, enemy_name_image, enemy_alternate_text = enemy.resolve_enemy_names(enemy_id, enemy_name, enemy_name_clean, enemy_name_image, enemy_name_counts, duplicate_name_map)
    cn_name = general.resolve_text(language["cn"], name_id)
    tc_name = general.resolve_text(language["tc"], name_id)
    jp_name = general.resolve_text(language["jp"], name_id)
    kr_name = general.resolve_text(language["kr"], name_id)
    sp_name = general.resolve_text(language["sp"], name_id)
    ru_name = general.resolve_text(language["ru"], name_id)

    # mw.cleric input
    wiki_overview = ""
    wiki_addition = ""
    wiki_changelog = ""
    wiki_enemy_tab = ""

    page = site.client.pages[enemy_name_clean]
    if page.exists:
        wikitext = page.text()
        parsed_code = mwparserfromhell.parse(wikitext)
        wiki_overview = get_wiki_section(wikitext, "Overview")
        wiki_addition = get_wiki_section(wikitext, "See Also")
        wiki_changelog = get_wiki_section(wikitext, "Changelog")
        for template in parsed_code.filter_templates():
            if template.name.matches("Enemy tab"):
                wiki_enemy_tab = "{{Enemy tab}}\n"
                break

    # Enemy description
    desc_id = display_data.get("description", {}).get("id")
    enemy_desc = general.resolve_text(language["en"], desc_id)

    # Enemy species
    enemy_species = enemy.resolve_enemy_species(enemy_id, enemy_group, wiki_group, language)

    # Enemy type
    display_type_id = display_data.get("displayType")
    type_data = enemy_type.get(str(display_type_id), {})
    type_name_id = type_data.get("name", {}).get("id")
    enemy_class = general.resolve_text(language["en"], type_name_id)
    enemy_article = "an" if enemy_class and enemy_class[0].lower() in "aeiou" else "a"

    # Enemy abilities
    enemy_ability_text = enemy.resolve_enemy_abilities(display_data, enemy_ability, language)

    # Enemy locations
    enemy_location = enemy.resolve_enemy_locations(display_data, distribution_info, language)

    # Enemy drops
    enemy_drop_item = enemy.resolve_enemy_drops(enemy_id, enemy_drop, item_table, language)

    # Enemy stats
    enemy_hp, enemy_atk, enemy_def = enemy.resolve_enemy_level_stats(attr_data)

    # Level independent stats
    enemy_weight, enemy_attack_range, enemy_stagger_hp, enemy_stagger_time, enemy_stagger_damage, physical_resist, nature_resist, cryo_resist, electric_resist, heat_resist, aether_resist, enemy_sp_gain = enemy.resolve_enemy_independent_stats(attr_data)

    # Output
    output = (f"""\
{wiki_enemy_tab}{{{{Enemy infobox
|name = {enemy_name}
|image = {enemy_name_image}_sprite.png
|filename = {enemy_id}
|cnname = {cn_name}
|tcname = {tc_name}
|jpname = {jp_name}
|krname = {kr_name}
|spname = {sp_name}
|runame = {ru_name}
|type = {enemy_species}
|class = {enemy_class}
|attack = 
|damage = 
|upgrade = }}}}
'''{enemy_name}''' is {enemy_article} [[{enemy_class} enemy]] in ''[[Arknights: Endfield]]''.{enemy_alternate_text}

{{{{Enemy description|{enemy_desc}}}}}

==Stats==
{{{{Enemy data
|HP = {enemy_hp}
|ATK = {enemy_atk}
|DEF = {enemy_def}
|SHP = {enemy_stagger_hp}
|SR = {enemy_stagger_time}
|SD = {enemy_stagger_damage}
|SPG = {enemy_sp_gain}
|AR = {enemy_attack_range}
|Weight = {enemy_weight}
|wphysical = {physical_resist}
|wfire = {heat_resist}
|welectric = {electric_resist}
|wice = {cryo_resist}
|wnature = {nature_resist}
|waether = {aether_resist}
|abilities = {enemy_ability_text}
|location = {enemy_location}
|drops = {enemy_drop_item}
|addendum = }}}}

==Overview==
{wiki_overview}

==See Also==
{wiki_addition}

==Changelog==
{wiki_changelog}

==Navigation==
{{{{Enemies}}}}
[[Category:{enemy_class} enemies]]
""")
    wikitexts[enemy_name_clean] = output

    # Short sleep between parses so there's no error with timeouts on the wiki API
    time.sleep(2)

remaining_pagenames = set(wikitexts.keys())
processed_pagenames = set()

page_list = site.pages_using("Enemy infobox", namespace=0)

class EnemyPage(PageModifierBase):
    def update_plaintext(self, text):
        pagename = self.current_page.name
        wikitext = wikitexts.get(pagename)
        if wikitext:
            processed_pagenames.add(pagename)
            remaining_pagenames.discard(pagename)
            text = wikitext
        return text

# Make that sausage
if not force:
    # If page already exists, skip it
    pagenames = {page.name for page in page_list}
    processed_pagenames += pagenames
    remaining_pagenames -= pagenames
EnemyPage(site, page_list=page_list, skip_pages=processed_pagenames, lag=lag, summary=summary).run()
if remaining_pagenames:
    EnemyPage(site, title_list=sorted(remaining_pagenames), lag=lag, summary=summary).run()