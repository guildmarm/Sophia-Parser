import parser_lib.io as io
import parser_lib.helpers as helpers
import parser_lib.game_files as game_files
import parser_lib.constants as const
import os

TARGET_LEVELS = [1, 20, 40, 60, 80, 99]

# Output file
OUTPUT_FILE = os.path.join(const.OUTPUT_DIR, "full_enemy_page_data.txt")
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
    enemy_name = helpers.resolve_text(language["en"], name_id)
    enemy_name_clean = helpers.sanitize_name(enemy_name)
    enemy_name_counts[enemy_name_clean] = enemy_name_counts.get(enemy_name_clean, 0) + 1
    duplicate_name_map.setdefault(enemy_name_clean, []).append(enemy_id)

duplicate_name_map = {k: v for k, v in duplicate_name_map.items() if len(v) > 1}

# Make that sausage
with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for enemy_id, attr_data in enemy_attr.items():
        display_data = enemy_display.get(enemy_id)
        if not display_data:
            continue

        # Enemy names
        name_id = display_data.get("name", {}).get("id")
        enemy_name = helpers.resolve_text(language["en"], name_id)
        enemy_name_clean = helpers.sanitize_name(enemy_name)
        enemy_name_image = helpers.sanitize_image_name(enemy_name)

        # Append the ID if there are duplicates but just the last part of it
        if enemy_name_counts.get(enemy_name_clean, 0) > 1:
            short_id = enemy_id.split("_")[-1]
            enemy_name_clean = f"{enemy_name_clean} ({short_id})"
            enemy_name = f"{enemy_name} ({short_id})"
            enemy_name_image = f"{enemy_name_image}_{short_id}"

            alternate_ids = [eid for eid in duplicate_name_map[enemy_name_clean.split(" (")[0]] if eid != enemy_id]
            alternate_names = []
            for alt_id in alternate_ids:
                alt_short = alt_id.split("_")[-1]
                alternate_names.append(f"{enemy_name_clean.split(' (')[0]} ({alt_short})")

            enemy_alternate_text = ""
            if alternate_names:
                enemy_alternate_text = " Alternate form(s): " + ", ".join(f"[[{name}]]" for name in alternate_names)
        else:
            enemy_alternate_text = ""

        cn_name = helpers.resolve_text(language["cn"], name_id)
        tc_name = helpers.resolve_text(language["tc"], name_id)
        jp_name = helpers.resolve_text(language["jp"], name_id)
        kr_name = helpers.resolve_text(language["kr"], name_id)
        sp_name = helpers.resolve_text(language["sp"], name_id)
        ru_name = helpers.resolve_text(language["ru"], name_id)

        # Enemy description
        desc_id = display_data.get("description", {}).get("id")
        enemy_desc = helpers.resolve_text(language["en"], desc_id)

        # Enemy species
        enemy_species = ""
        for entry_id, entry_data in enemy_group.items():
            ref_id = entry_data.get("refMonsterTemplateId")
            if ref_id == enemy_id:
                group_id = entry_data.get("groupId")
                break
        else:
            group_id = None

        if group_id:
            # Search wiki_group for the matching groupId
            group_name_id = None
            for group_type, group_list_data in wiki_group.items():
                for group in group_list_data.get("list", []):
                    if group.get("groupId") == group_id:
                        group_name_id = group.get("groupName", {}).get("id")
                        break
                if group_name_id:
                    break
            
            if group_name_id:
                enemy_species = helpers.resolve_text(language["en"], group_name_id)

        # Enemy type
        display_type_id = display_data.get("displayType")
        type_data = enemy_type.get(str(display_type_id), {})
        type_name_id = type_data.get("name", {}).get("id")
        enemy_class = helpers.resolve_text(language["en"], type_name_id)

        # Enemy abilities
        enemy_ability_list = []

        ability_desc_ids = display_data.get("abilityDescIds", [])
        for ability_id in ability_desc_ids:
            ability_data = enemy_ability.get(str(ability_id), {})
            desc_id = ability_data.get("description", {}).get("id")
            ability_text = helpers.resolve_text(language["en"], desc_id)
            if ability_text:
                enemy_ability_list.append(f"*{ability_text}")

        enemy_ability_text = "\n".join(enemy_ability_list)

        # Enemy locations
        enemy_location_list = []

        distribution_ids = display_data.get("distributionIds", [])
        for dist_id in distribution_ids:
            dist_data = distribution_info.get(str(dist_id), {})
            area_name_id = dist_data.get("areaName", {}).get("id")
            area_name = helpers.resolve_text(language["en"], area_name_id)
            if area_name:
                enemy_location_list.append(f"*{area_name}")

        # Fallback if no locations
        if not enemy_location_list:
            enemy_location_list.append("*TBA")

        enemy_location = "\n".join(enemy_location_list)

        # Enemy drops
        drop_data = enemy_drop.get(enemy_id, {})
        drop_item_ids = drop_data.get("dropItemIds", [])
        enemy_drop_item_list = []

        for item_id in drop_item_ids:
            item_data = item_table.get(str(item_id), {})
            item_name_id = item_data.get("name", {}).get("id")
            item_name = helpers.resolve_text(language["en"], item_name_id)
            if item_name:
                enemy_drop_item_list.append(f"{{{{I|{item_name}}}}}")

        enemy_drop_item = " ".join(enemy_drop_item_list)

        # Enemy stats
        level_blocks = attr_data.get("levelDependentAttributes", [])
        level_stat_map = {}

        for block in level_blocks:
            attrs = block.get("attrs", [])
            level = None
            stat_map = {}

            for attr in attrs:
                attr_type = attr.get("attrType")
                attr_value = attr.get("attrValue")

                if attr_type == 0:
                    level = attr_value
                else:
                    stat_map[attr_type] = attr_value

            if level is not None:
                level_stat_map[level] = stat_map

        # Level dependent stats
        hp_values = []
        atk_values = []
        def_values = []

        for lvl in TARGET_LEVELS:
            stats = level_stat_map.get(lvl, {})

            hp_values.append(str(stats.get(1, "")))
            atk_values.append(str(stats.get(2, "")))
            def_values.append(str(stats.get(3, "")))

        enemy_hp = ", ".join(hp_values)
        enemy_atk = ", ".join(atk_values)
        enemy_def = ", ".join(def_values)

        # Level independent stats
        independent_block = attr_data.get("levelIndependentAttributes", {})
        independent_stats = {}

        for attr in independent_block.get("attrs", []):
            attr_type = attr.get("attrType")
            attr_value = attr.get("attrValue")
            independent_stats[attr_type] = attr_value

        enemy_weight = independent_stats.get(8, "")
        enemy_attack_range = independent_stats.get(12, "")
        enemy_stagger_hp = independent_stats.get(20, "")
        enemy_stagger_time = independent_stats.get(21, "")
        enemy_stagger_damage = independent_stats.get(27, "")

        physical_resist = independent_stats.get(80, "")
        nature_resist = independent_stats.get(81, "")
        cryo_resist = independent_stats.get(82, "")
        electric_resist = independent_stats.get(83, "")
        heat_resist = independent_stats.get(84, "")
        aether_resist = independent_stats.get(85, "")

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