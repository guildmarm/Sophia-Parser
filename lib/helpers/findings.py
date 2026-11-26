import lib.io as io
import lib.general as general
import lib.game_files as game_files
import lib.format_text as format_text
from lib.constants import FINDINGS_WIKI_ICONS
from lib.constants import LEVEL_LOCATION
from lib.constants import REGION_NAME
from lib.constants import INPUT_DIR
from lib.constants import BASE_DIR
import re
import os
from datetime import datetime
import difflib

paths = game_files.build_paths(INPUT_DIR)

all_text = io.load_languages(INPUT_DIR)["en"]
files_scr = io.load_json(paths["finding_text_table"])
audios_scr = io.load_json(paths["radio_table"])
prts_all_scr = io.load_json(paths["finding_single"])
prts_scr = io.load_json(paths["finding_group"])
category_scr = io.load_json(paths["finding_category"])

FINDING_ID_RE = re.compile(
	r"(?:(?P<area>(?P<region>map\d{2})_lv\d{3})"
	r"|(?P<region_only>map\d{2})"
	r"|(?<![a-z0-9])(?P<mission>[a-z]+\d+(?:l\d+)?m\d+(?:d\d+)?))"
)
SUFFIXES = ["Second", "Third", "Fourth", "Fifth", "Sixth",
			"Seventh", "Eighth", "Ninth", "Tenth"]
MERGE_SIMILARITY_THRESHOLD = 0.7

_group_title_counts = {}
_finding_title_counts = {}

def get_text(lang, s):
	return format_text.findings_format(general.resolve_text(lang, s.get("id", s) ) ) # General clear

def get_type(s, category="Manuscripts"):
	if category in ("Peculiars", "Audio Records", "Reports"):
		return category
	return FINDINGS_WIKI_ICONS.get(s, s).replace("Finding_", "")

def get_category(s, text):
	category_map = {
		"collection": "Peculiars",
		"digital": "E-Files",
		"document": "Nexus Files",
		"media": "Audio Records",
		"paper": "Manuscripts",
		"report": "Reports"
	}
	if s in category_map:
		return category_map[s]
	return general.resolve_text(text, category_scr.get(s))

def parse_id(item_id):
	v = {}
	m = FINDING_ID_RE.search(item_id)
	if not m:
		return None
	region = m.group("region") or m.group("region_only")
	v["region"] = REGION_NAME.get(region, region) if region else None
	v["area"] = LEVEL_LOCATION.get( m.group("area"), m.group("area") )
	v["mission"] = m.group("mission")
	return v

# Implement a polymorphism to use this func in other places if it would be needed
def create_single_finding(all_text, item_id, group=None):
	if group:
		return __create_single_finding_main(all_text, item_id, group)
	else:
		return __create_single_finding_by_id(all_text, item_id)

# Creating a finding to return
def __create_single_finding_main(all_text, item_id, group):
	item = prts_all_scr.get(item_id)
	
	if item is None:
		return None

	content = []
	if group["category"] == "Audio Records":
		text = audios_scr.get(item["contentId"])
		if text:
			content = [ f'{re.sub(r" ?{.+?}", "", get_text(all_text, d["actorName"]))}: {get_text(all_text, d["radioText"])}' for d in text.get("radioSingleDataList") ]
	else:
		text = files_scr.get(item["contentId"])
		if text:
			content = [ get_text(all_text, d["content"]) for d in text.get("contentList") ]
	
	locations = parse_id(item["contentId"])
	result = {
				"title": get_text(all_text, item["name"]),
				"internalID": item_id,
				"groupID": item["firstLvId"],
				"group_title": group["title"],
				"group_category": group["category"],
				"group_type": group["type"],
				"content": content
			}
	if locations:
		result.update(locations)
	return result

# Getting a group of finding for main function
def __create_single_finding_by_id(all_text, item_id):
	if prts_all_scr.get(item_id) is None:
		return None

	tmp = prts_scr.get(prts_all_scr.get(item_id)["firstLvId"])
	group = {
		"title": get_text(all_text, tmp["name"]),
		"type": get_type( tmp["icon"], category=get_category(tmp["categoryId"], all_text) ),
	}

	return __create_single_finding_main(all_text, item_id, group=group)


def save_new_entries_to_list(list_name, new_ids):
	if not new_ids:
		return

	file_path = os.path.join(BASE_DIR, "lib", "findings_list.py")
	today = datetime.now().strftime("%Y-%m-%d")

	with open(file_path, "r", encoding="utf-8") as f:
		lines = f.readlines()

	# Locate the list declaration
	start = None
	for i, line in enumerate(lines):
		if line.lstrip().startswith(f"{list_name} ="):
			start = i
			break
	if start is None:
		raise ValueError(f"{list_name} not found in {file_path}")

	# Locate the first closing bracket after the declaration
	close = None
	for i in range(start, len(lines)):
		if "]" in lines[i]:
			close = i

			lines.insert(close, f"    # Added {today}\n")
			for idx, item_id in enumerate(new_ids):
				lines.insert(close + 1 + idx, f'    "{item_id}",\n')
			break
	if close is None:
		raise ValueError(f"Closing bracket for {list_name} not found")

	with open(file_path, "w", encoding="utf-8") as f:
		f.writelines(lines)

# Made with AI, so... Yeah
def __make_unique(title, category, counts):
	seen = counts.get(title, [])
	if not seen:
		counts[title] = [category]
		return title

	if category in seen:
		same_count = seen.count(category)
		suffix = SUFFIXES[same_count - 1] if same_count - 1 < len(SUFFIXES) else f"#{same_count + 1}"
	else:
		suffix = category[:-1]

	counts[title] = seen + [category]
	return f"{title} ({suffix})"

def __full_text(item):
	parts = []
	for sub in item.get("content", []):
		if isinstance(sub, dict):
			parts.extend(sub.get("content", []))
	return "\n\n".join(parts)

def __merge_cluster(cluster):
	first = cluster[0]
	merged = dict(first)
	merged["title"] = first.get("raw_title", first["title"])

	combined_content = []
	for g in cluster:
		for sub in g["content"]:
			new_sub = dict(sub)
			new_sub.setdefault("raw_title", new_sub["title"])
			combined_content.append(new_sub)

	merged["content"] = combined_content
	merged["merged_from"] = [g["internalID"] for g in cluster]
	return merged

# Groups often have same title as single finding in it
def unique_group_title(title, category):
	# Append (Second), (Third), ... if a group with this title already exists.
	return __make_unique(title, category, _group_title_counts)

def unique_finding_title(title, category):
	# Append (Second), (Third), ... if a finding with this title already exists.
	return __make_unique(title, category, _finding_title_counts)

def merge_similar_groups(groups, threshold=MERGE_SIMILARITY_THRESHOLD, skip_categories=("Nexus Files",)):
	result = []
	by_title = {}
	for g in groups:
		if g["category"] in skip_categories:
			result.append(g)
			continue
		key = (g["category"], g.get("raw_title", g["title"]))
		by_title.setdefault(key, []).append(g)

	for same_title in by_title.values():
		if len(same_title) == 1:
			result.append(same_title[0])
			continue

		used = set()
		for i, g in enumerate(same_title):
			if i in used:
				continue
			cluster = [g]
			used.add(i)

			for j in range(i + 1, len(same_title)):
				if j in used:
					continue
				ratio = difflib.SequenceMatcher(
					None, __full_text(g), __full_text(same_title[j])
				).ratio()
				if ratio >= threshold:
					cluster.append(same_title[j])
					used.add(j)

			if len(cluster) == 1:
				result.append(cluster[0])
			else:
				result.append(__merge_cluster(cluster))

	return result