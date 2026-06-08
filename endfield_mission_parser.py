import lib.io as io
import lib.general as general
import lib.helpers.mission as mission
import lib.game_files as game_files
import lib.constants as const
import lib.format_text as format_text
import lib.mission_list as mission_list
import os
import re

def _natural_sort_key(mid):
    return [int(p) if p.isdigit() else p for p in re.split(r'(\d+)', mid)]

# Output file
MISSION_PAGE_OUTPUT = os.path.join(const.OUTPUT_DIR, "full_mission_page_data.txt")
os.makedirs(const.OUTPUT_DIR, exist_ok=True)

paths = game_files.build_paths(const.INPUT_DIR)

text_table = io.load_json(paths["text_table"])
mission_table = io.load_json(paths["mission_table"])
mission_type_info_table = io.load_json(paths["mission_type_info"])
reward_table = io.load_json(paths["reward_table"])
item_table = io.load_json(paths["item_table"])
language = io.load_languages(const.INPUT_DIR)

# Mission list functions
found_mission_ids = set()
for key in text_table.keys():
    if key.startswith("objective_"):
        parts = key.split("_")
        if len(parts) > 1:
            found_mission_ids.add(parts[1])

found_mission_ids = {
    mid for mid in found_mission_ids
    if general.resolve_text(language["en"], text_table.get(f"{mid}_name", {}).get("id", ""))
}

newly_processed_missions = [
    m_id for m_id in sorted(found_mission_ids)
    if m_id not in mission_list.MISSION_LIST
]

if newly_processed_missions:
    mission.save_new_missions_to_list(newly_processed_missions)
    mission_list.MISSION_LIST.extend(newly_processed_missions)

# Make that sausage
sorted_mission_ids = sorted(found_mission_ids, key=_natural_sort_key)
map_ep_starts = mission.build_map_episode_starts(mission_table, mission_type_info_table)

with open(MISSION_PAGE_OUTPUT, "w", encoding="utf-8") as out:
    for mission_id in sorted_mission_ids:

        mission_name_key = f"{mission_id}_name"
        name_entry = text_table.get(mission_name_key, {})
        name_internal_id = name_entry.get("id")

        mission_data = mission_table.get(mission_id, {})
        mission_name = general.resolve_text(language["en"], name_internal_id)
        sanitized_mission_name = general.sanitize_name(mission_name)
        desc_groups = mission.resolve_mission_descriptions(mission_id, mission_data, text_table, language)
        mission_content = mission.build_mission_content(desc_groups, format_fn=format_text.efdb_format)

        mission_importance, mission_location, mission_type, mission_view_type, mission_rewards, mission_prev, mission_next = mission.build_mission_box(mission_id, mission_data, mission_type_info_table, reward_table, item_table, sorted_mission_ids, text_table, language)
        sanitized_mission_prev = general.sanitize_name(mission_prev)
        sanitized_mission_next = general.sanitize_name(mission_next)
        header_color, header_icon, header_chaptertitle, header_chapter, header_process = mission.build_mission_header(mission_id, mission_type, mission_importance, mission_view_type, mission_data.get("levelId"), map_ep_starts, text_table, language)

        out.write(f"""{{{{-start-}}}}
'''{sanitized_mission_name}'''
{{{{Mission tracker}}}}
{{{{Mission header
|id = {mission_id}
|color = {header_color}
|icon = {header_icon}
|name = {mission_name}
|region = {mission_location}
|bg =
|facicon =
|chaptertitle = {header_chaptertitle}
|chapter = {header_chapter}
|process = {header_process}}}}}
{{{{Mission box
|name = {mission_name}
|type = {mission_type}
|importance = {mission_importance}
|location = {mission_location}
|box =
{mission_content}
{mission_rewards}
|prereq = 
|prev = {sanitized_mission_prev}
|next = {sanitized_mission_next}
|note =
}}}}
{{{{-stop-}}}}

""")