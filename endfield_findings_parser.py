import lib.io as io
import lib.general as general
import lib.game_files as game_files
import lib.constants as const
import lib.helpers.findings as findings_helper
import lib.findings_list as findings_list
import os
from mwcleric.wiki_client import WikiClient

# You can run this parser first time with commented wiki checks
# Set endfield wiki as mw.cleric site
site = WikiClient("endfield.wiki.gg")

# Output files
INVESTIGATIONS_PAGE_OUTPUT = os.path.join(const.OUTPUT_DIR, "investigations_page_data.txt")
NEXUS_PAGE_OUTPUT = os.path.join(const.OUTPUT_DIR, "nexus_files_page_data.txt")
AUDIO_PAGE_OUTPUT = os.path.join(const.OUTPUT_DIR, "audio_records_page_data.txt")
FINDINGS_PAGE_OUTPUT = os.path.join(const.OUTPUT_DIR, "findings_page_data.txt")

os.makedirs(const.OUTPUT_DIR, exist_ok=True)

paths = game_files.build_paths(const.INPUT_DIR)

all_text = io.load_languages(const.INPUT_DIR)["en"]
files_scr = io.load_json(paths["finding_text_table"])
audios_scr = io.load_json(paths["radio_table"])
prts_all_scr = io.load_json(paths["finding_single"])
prts_scr = io.load_json(paths["finding_group"])
category_scr = io.load_json(paths["finding_category"])
investig_scr = io.load_json(paths["investigate_table"])
comments_scr = io.load_json(paths["investigate_comment_table"])

all_singles_list = {}
all_groups_list = []

newly_processed_groups = []
newly_processed_investigations = []

for value in prts_scr.values():
	if not value["itemIds"]:
		print(f'Item "{findings_helper.get_text(all_text, value["name"])}"({value["firstLvId"]}) haven\'t any notes. Probably broken or outdated data')
		continue

	item_category = findings_helper.get_category(value["categoryId"], all_text)
	item_title_raw = findings_helper.get_text(all_text, value["name"])
	item_title = general.sanitize_name(findings_helper.unique_group_title(item_title_raw, item_category))

	item_icon = const.FINDINGS_WIKI_ICONS.get(value["icon"], value["icon"]) + ".png"
	if not item_icon.startswith("Finding_") and item_category == "Peculiars":
		item_icon = "Peculiar_" + general.sanitize_image_name(item_title_raw) + ".png"

	is_new = value["firstLvId"] not in findings_list.GROUP_LIST

	item = {
		"title": item_title,
		"raw_title": item_title_raw,
		"category": item_category,
		"type": findings_helper.get_type(value["icon"], category=item_category),
		"icon": item_icon,
		"internalID": value["firstLvId"],
		"internalIconID": value["icon"],
		"content": []
	}

	for item_id in value["itemIds"]:
		note = findings_helper.create_single_finding(all_text, item_id, group=item)

		note["raw_title"] = note["title"]
		note["title"] = general.sanitize_name(findings_helper.unique_finding_title(note["title"], item["category"]))  

		item["content"].append(note)
		all_singles_list[note.get("internalID")] = note

	# Skip Nexus Reports
	if item["category"] == "Reports":
		continue

	# Get locations and mission from first finding in list cuz' they're mostly share origin
	if item["content"] and isinstance(item["content"][0], dict):
		parsed = {
			"mission" : item["content"][0].get("mission"),
			"area" : item["content"][0].get("area"),
			"region" : item["content"][0].get("region"),
		}
		if parsed:
			item.update(parsed)

	if is_new:
		all_groups_list.append(item)
		newly_processed_groups.append(value["firstLvId"])

all_groups_list = findings_helper.merge_similar_groups(all_groups_list)

with open(AUDIO_PAGE_OUTPUT, "w", encoding="utf-8") as out:
	for f in filter(lambda d: d["category"] == "Audio Records", all_groups_list):
		f["title"] += " (Recording)" if site.client.pages[f["title"]].exists else ""
		clear_text = ""
		length = len(f["content"])
		for i, single in enumerate(f["content"], start=1):
			if length > 1:
				clear_text += "<tabber>\n" if i == 1 else "|-|\n"
				clear_text += f"Part {i}=\n"
				clear_text += f"{{{{Audio Record Head\n| filename = {f['internalID']}\n| title = {single['raw_title']}\n| type = {f['type']}}}}}\n" if length == i else f"{{{{Audio Record Head|nocargo=yes| title = {single['raw_title']}}}}}\n"
			else: 
				clear_text += f"{{{{Audio Record Head\n| filename = {f['internalID']}\n| title = {single['raw_title']}\n| type = {f['type']}}}}}\n"
			for line in single["content"]:
				split = line.split(": ", 1)
				clear_text += f"{{{{Audio Record cell|{split[0]}|{split[1]}}}}}" + "\n"
			location_params = []
			if single.get('area'): # REPLACE THIS TO GET FROM SINGLE
				location_params.append(f"area = {single['area']}")
			if single.get('region'):
				location_params.append(f"region = {single['region']}")
			if single.get('mission'):
				location_params.append(f"mission = {single['mission']}")

			if location_params:
				location_cell = (
					"{{Audio Record cell|mode=line}}\n"
					"{{Audio Record cell|" + "|".join(location_params) + "|mode=obtain}}\n"
				)
			else:
				location_cell = ""
			clear_text += location_cell
			if length > 1 and i == length:
				clear_text += "</tabber>\n"
		out.write(f"""{{{{-start-}}}}
'''{f['title']}'''
{clear_text}{{{{Audio Record end}}}}
{{{{-stop-}}}}

""")

with open(NEXUS_PAGE_OUTPUT, "w", encoding="utf-8") as out:
	for f in filter(lambda d: d["category"] == "Nexus Files", all_groups_list):
		desc = '\n\n'.join(f["content"][0]["content"])
		out.write(f"""{{{{-start-}}}}
'''Nexus Files: {f['title']}'''
{{{{Nexus Files
| filename = {f['internalID']}
| title = {f['raw_title']}
| type = {f['type']}
| desc = {desc}
}}}}
{{{{-stop-}}}}

""")

with open(FINDINGS_PAGE_OUTPUT, "w", encoding="utf-8") as out:
	for f in filter(lambda d: d["category"] not in ("Audio Records", "Nexus Files"), all_groups_list):
		out.write(f"{{{{-start-}}}}\n'''{f['title']}'''\n{{{{Finding\n")
		out.write(f"| filename = {f['internalID']}\n")
		out.write(f"| title = {f['raw_title']}\n")
		out.write(f"| category = {f['category']}\n")
		out.write(f"| type = {f['type']}\n")
		if f.get('area'): out.write(f"| area = {f.get('area')}\n")
		if f.get('region'): out.write(f"| region = {f.get('region')}\n")
		if f.get('mission'): out.write(f"| mission = {f.get('mission')}\n")
		if f["category"] == "Peculiars": out.write(f"| image = {f['icon']}")
		out.write(f"}}}}\n\n==Content==\n{{{{Finding bigview\n")
		for i, item in enumerate(f["content"], start=1):
			text = '\n\n'.join(item["content"])
			out.write(f"| name{i} = {item.get('raw_title', item['title'])}\n")
			out.write(f"| text{i} = {text}\n")
		out.write(f"}}}}")
		if f.get("merged_from") and len(f["merged_from"]) > 1:
			out.write(f"<!--\n  Merged from: {', '.join(f['merged_from'])} -->")
		out.write(f"\n{{{{-stop-}}}}\n\n")


with open(INVESTIGATIONS_PAGE_OUTPUT, "w", encoding="utf-8") as out:
	for value in investig_scr.values():
		if value["id"] in findings_list.INVESTIGATION_LIST:
			continue

		title = findings_helper.get_text(all_text, value["name"])
		desc = findings_helper.get_text(all_text, value["desc"])
		icon = const.INVESTIGATION_ICONS.get(value["type"], "Invalid")
		internalID = value["id"]
		unlockReport = all_singles_list.get(value["unlockPrts"])
		if unlockReport: unlockReport["content"] = '\n\n'.join(unlockReport["content"])
		region = const.REGION_NAME.get(value["domainId"], value["domainId"])
		sections = ["==Needed Files==", '<div style="display:grid; gap:20px;">']

		for i, section in enumerate(value["categoryDataList"]):
			findings = list(all_singles_list.get(f) for f in section["collectionIdList"])
			sections.append(f"{{{{Investigation section|{findings_helper.get_text(all_text, section['name'])}")
			if i == 0:
				sections.append(f"| filename = {internalID}")
				sections.append(f"| inv_title = {title}")
				sections.append(f"| icon = {icon}")
				sections.append(f"| region = {const.REGION_NAME.get(value['domainId'], value['domainId'])}")
			else: sections.append(f"| nocargo = yes")
			for j, f in enumerate(findings, start = 1):
				# Right now if u input params with \n template breaks, i would fix it later
				sections.append(f"| finding{j} = {{{{Findings view|{f.get('raw_title', f['title'])}|{f['group_category']}|{f['group_type']}|{general.sanitize_name(f['group_title'])}}}}}")
			for j, c in enumerate(section["noteIdList"], start = 1):
				sections.append(f"| comment{j} = {findings_helper.get_text(all_text, comments_scr.get(c).get('desc'))}")
			sections.append("}}")
		sections.append("</div>")
		sections = "\n\n".join(sections)

		title += " (Intel Gathering)" if site.client.pages[title].exists else ""

		out.write(f"""{{{{-start-}}}}
'''{general.sanitize_name(title)}'''
{sections}

==Content==
{{{{Nexus Files
| filename = {unlockReport["internalID"]}
| title = {unlockReport.get("raw_title", unlockReport["title"])}
| type = {unlockReport["group_type"]}
| desc = {unlockReport["content"] if unlockReport else "TBA"}
}}}}
{{{{-stop-}}}}

""")
		newly_processed_investigations.append(value["id"])

# Add new findings to exclusion lists
findings_helper.save_new_entries_to_list("GROUP_LIST", newly_processed_groups)
findings_helper.save_new_entries_to_list("INVESTIGATION_LIST", newly_processed_investigations)