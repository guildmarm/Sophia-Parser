import lib.io as io
import lib.general as general
import lib.helpers.enemy as enemy
import lib.game_files as game_files
import lib.constants as const
import os

# Output file
ENEMY_PAGE_OUTPUT = os.path.join(const.OUTPUT_DIR, "full_enemy_page_data.txt")
ENEMY_NAV_TEMPLATE_OUTPUT = os.path.join(const.OUTPUT_DIR, "template_enemy_nav_data.txt")
os.makedirs(const.OUTPUT_DIR, exist_ok=True)

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

enemy_name_counts = {}
duplicate_name_map = {}

for enemy_id, display_data in enemy_display.items():
    name_id = display_data.get("name", {}).get("id")
    enemy_name = general.resolve_text(language["en"], name_id)
    enemy_name_clean = general.sanitize_name(enemy_name)
    enemy_name_counts[enemy_name_clean] = enemy_name_counts.get(enemy_name_clean, 0) + 1
    duplicate_name_map.setdefault(enemy_name_clean, []).append(enemy_id)

duplicate_name_map = {k: v for k, v in duplicate_name_map.items() if len(v) > 1}

# Stuff for enemy nav
enemy_aggeloi, enemy_landbreakers, enemy_pirates, enemy_wildlife = enemy.build_enemy_nav_lists(enemy_attr, enemy_display, enemy_group, wiki_group, enemy_type, language, enemy_name_counts, duplicate_name_map)

# Make that sausage
with open(ENEMY_PAGE_OUTPUT, "w", encoding="utf-8") as out:
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

        # Enemy abilities
        enemy_ability_text = enemy.resolve_enemy_abilities(display_data, enemy_ability, language)

        # Enemy locations
        enemy_location = enemy.resolve_enemy_locations(display_data, distribution_info, language)

        # Enemy drops
        enemy_drop_item = enemy.resolve_enemy_drops(enemy_id, enemy_drop, item_table, language)

        # Enemy stats
        enemy_hp, enemy_atk, enemy_def = enemy.resolve_enemy_level_stats(attr_data)

        # Level independent stats
        enemy_weight, enemy_attack_range, enemy_stagger_hp, enemy_stagger_time, enemy_stagger_damage, physical_resist, nature_resist, cryo_resist, electric_resist, heat_resist, aether_resist = enemy.resolve_enemy_independent_stats(attr_data)

        # Output
        out.write(f"""{{{{-start-}}}}
'''{enemy_name_clean}'''
{{{{Enemy infobox
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
The '''{enemy_name}''' is a [[{enemy_class} enemy]] in ''[[Arknights: Endfield]]''.{enemy_alternate_text}

{{{{Enemy description|{enemy_desc}}}}}

==Overview==
{{{{Enemy data
|HP = {enemy_hp}
|ATK = {enemy_atk}
|DEF = {enemy_def}
|SHP = {enemy_stagger_hp}
|SR = {enemy_stagger_time}
|SD = {enemy_stagger_damage}
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

==Navigation==
{{{{Enemies}}}}
[[Category:{enemy_class} enemies]]

{{{{-stop-}}}}

""")

# Make that sausage again (This is for the Enemy Nav template)
with open(ENEMY_NAV_TEMPLATE_OUTPUT, "w", encoding="utf-8") as out:
        out.write(f"""{{{{-start-}}}}
'''Template:Enemies'''
<onlyinclude>{{{{Navbox
| Title = Enemies
| State = {{{{{{state|expanded}}}}}}
| Group style = text-align:center;

| Group 1 = Aggeloi
| List 1 = {enemy_aggeloi}

| Group 2 = Landbreakers
| List 2 = {enemy_landbreakers}

| Group 3 = Cangzei Pirates
| List 3 = {enemy_pirates}

| Group 4 = Wildlife
| List 4 = {enemy_wildlife}

}}}}</onlyinclude><noinclude>This navbox template is used as a means to navigate a list of [[enemy|enemies]].

To use this template, add <code><nowiki>{{{{Enemies}}}}</nowiki></code> at the end of an article.

[[Category:Navboxes]]</noinclude>

{{{{-stop-}}}}

""")