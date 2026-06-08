from lib.constants import BASE_DIR, MISSION_IMPORTANCE, MISSION_TYPE, LEVEL_LOCATION
import lib.general as general
from collections import defaultdict, deque
from datetime import datetime
import os
import re

def build_mission_box(mission_id, mission_data, mission_type_info_table, reward_table, item_table, sorted_missions, text_table, language, lang="en"):
    mission_importance = MISSION_IMPORTANCE.get(mission_data.get("missionImportance"), "")
    mission_location = LEVEL_LOCATION.get(mission_data.get("levelId"), "")

    raw_type = mission_data.get("missionType")
    mission_view_type = mission_type_info_table.get(str(raw_type), {}).get("missionViewType")
    mission_type = MISSION_TYPE.get(mission_view_type, "")

    reward_id = mission_data.get("rewardId", "")
    item_bundles = reward_table.get(reward_id, {}).get("itemBundles", [])
    reward_lines = []
    for i, bundle in enumerate(item_bundles):
        item_id = bundle.get("id", "")
        count = bundle.get("count", 0)
        name_id = item_table.get(item_id, {}).get("name", {}).get("id", "")
        name = general.resolve_text(language[lang], name_id)
        if name:
            reward_lines.append(f"|reward{i + 1} = {name},{count}")
    mission_rewards = "\n".join(reward_lines)

    idx = sorted_missions.index(mission_id)
    prev_id = sorted_missions[idx - 1] if idx > 0 else None
    next_id = sorted_missions[idx + 1] if idx < len(sorted_missions) - 1 else None

    def resolve_name(mid):
        if not mid:
            return ""
        entry = text_table.get(f"{mid}_name", {})
        return general.resolve_text(language[lang], entry.get("id", ""))

    mission_prev = resolve_name(prev_id)
    mission_next = resolve_name(next_id)

    return mission_importance, mission_location, mission_type, mission_view_type, mission_rewards, mission_prev, mission_next

def build_map_episode_starts(mission_table, mission_type_info_table):
    map_ep_starts = {}
    for mid, mdata in mission_table.items():
        raw_type = mdata.get("missionType")
        view_type = mission_type_info_table.get(str(raw_type), {}).get("missionViewType")
        if view_type != 0:
            continue
        level_id = mdata.get("levelId", "")
        m = re.search(r'map(\d+)', level_id)
        if not m:
            continue
        map_key = f"map{m.group(1)}"
        nums = re.findall(r'\d+', mid)
        if nums:
            ep_num = int(nums[0])
            if map_key not in map_ep_starts or ep_num < map_ep_starts[map_key]:
                map_ep_starts[map_key] = ep_num
    return map_ep_starts

def _to_roman(n):
    vals = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    result = ""
    for v, s in vals:
        while n >= v:
            result += s
            n -= v
    return result

def build_mission_header(mission_id, mission_type, mission_importance, mission_view_type, level_id, map_ep_starts, text_table, language, lang="en"):
    header_color = {"Urgent": "Yellow", "Important": "Green", "Secondary": "Blue"}.get(mission_importance, "")
    header_icon = mission_view_type + 1 if mission_view_type is not None else ""
    header_chaptertitle = ""
    header_chapter = ""
    header_process = ""
    if mission_type == "Main Mission" and mission_id.startswith("e"):
        nums = re.findall(r'\d+', mission_id)
        map_match = re.search(r'map(\d+)', level_id or "")
        if len(nums) >= 2 and map_match:
            map_key = f"map{map_match.group(1)}"
            ep_num = int(nums[0])
            first_ep = map_ep_starts.get(map_key, ep_num)
            ep_entry = text_table.get(f"ep{nums[0]}_name", {})
            header_chaptertitle = general.resolve_text(language[lang], ep_entry.get("id", ""))
            header_process = _to_roman(ep_num - first_ep + 1)
            header_chapter = _to_roman(int(map_match.group(1)))
    return header_color, header_icon, header_chaptertitle, header_chapter, header_process

def build_mission_content(desc_groups, format_fn=None):
    blocks = []
    for desc_text, obj_texts in desc_groups:
        desc = format_fn(desc_text) if format_fn else desc_text
        objs = [format_fn(o) if format_fn else o for o in obj_texts]
        if not objs:
            tasks_str = "|tasks = "
        else:
            task_lines = [f"{{{{Mission task | {o}}}}}" for o in objs]
            tasks_str = "|tasks = " + "\n".join(task_lines)
        blocks.append(f"{{{{Mission content\n|desc = {desc}\n{tasks_str}\n}}}}")
    return "".join(blocks)

def save_new_missions_to_list(new_ids):
    if not new_ids:
        return

    file_path = os.path.join(BASE_DIR, "lib", "mission_list.py")
    today = datetime.now().strftime("%Y-%m-%d")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i in range(len(lines) - 1, -1, -1):
        if "]" in lines[i]:
            lines.insert(i, f'    # Added {today}\n')
            for idx, item_id in enumerate(new_ids):
                lines.insert(i + 1 + idx, f'    "{item_id}",\n')
            break

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def resolve_mission_descriptions(mission_id, mission_data, text_table, language, lang="en"):
    quest_dic = mission_data.get("questDic", {})
    if not quest_dic:
        return []

    initial_desc_key = mission_data.get("missionDescription", {}).get("key", "")
    quest_ids = set(quest_dic.keys())

    in_degree = {qid: 0 for qid in quest_ids}
    adj = defaultdict(list)
    for qid, quest in quest_dic.items():
        for prev_qid in quest.get("prevQuestIdList", []):
            if prev_qid in quest_ids:
                adj[prev_qid].append(qid)
                in_degree[qid] += 1

    def quest_num(qid):
        try:
            return int(qid.split("#")[-1])
        except (ValueError, IndexError):
            return 0

    queue = deque(sorted(
        (qid for qid, deg in in_degree.items() if deg == 0),
        key=quest_num
    ))

    current_desc_key = initial_desc_key
    groups = []  # [[desc_key, [obj_keys]], ...]

    while queue:
        qid = queue.popleft()
        quest = quest_dic[qid]

        if quest.get("overrideMissionDesc") and quest.get("descriptionOverride", {}).get("key"):
            current_desc_key = quest["descriptionOverride"]["key"]

        obj_keys = [
            obj["description"]["key"]
            for obj in quest.get("objectiveList", [])
            if obj.get("description", {}).get("key")
        ]

        if obj_keys:
            if groups and groups[-1][0] == current_desc_key:
                groups[-1][1].extend(obj_keys)
            else:
                groups.append([current_desc_key, list(obj_keys)])

        for next_qid in sorted(adj[qid], key=quest_num):
            in_degree[next_qid] -= 1
            if in_degree[next_qid] == 0:
                queue.append(next_qid)

    parts = []
    for desc_key, obj_keys in groups:
        desc_entry = text_table.get(desc_key, {})
        desc_text = general.resolve_text(language[lang], desc_entry.get("id", "")) if desc_entry else ""

        obj_texts = []
        recent = []
        for key in obj_keys:
            if (entry := text_table.get(key)) and (text := general.resolve_text(language[lang], entry.get("id", ""))):
                if text not in recent:
                    obj_texts.append(text)
                    recent.append(text)
                    if len(recent) > 2:
                        recent.pop(0)

        if desc_text.strip() or obj_texts:
            parts.append((desc_text, obj_texts))

    return parts
