import lib.io as io
import lib.general as general
import lib.game_files as game_files
import lib.constants as const
import time
import os
import re
from mwcleric.wiki_client import WikiClient

# Set endfield wiki as mw.cleric site
site = WikiClient("endfield.wiki.gg")

RDM_AREAS_OUTPUT = os.path.join(const.OUTPUT_DIR, "rdm_areas_page_data.txt")
RDM_REGIONS_OUTPUT = os.path.join(const.OUTPUT_DIR, "rdm_regions_page_data.txt")
os.makedirs(const.OUTPUT_DIR, exist_ok=True)

paths = game_files.build_paths(const.INPUT_DIR)

text_table = io.load_languages(const.INPUT_DIR)["en"]
rdm_table = io.load_json(paths["rdm_table"])
rewards_table = io.load_json(paths["reward_table"])

# Class to organize data a bit
class DevelopmentLevel:
	def __init__(self, level: int, lvlDict: dict):
		self.level = level
		self.capacity = lvlDict["bandwidth"]
		self.zipline = lvlDict["travelPoleLimit"]
		self.combat = lvlDict["battleBuildingLimit"]
		self.purity_up = lvlDict["isMineOutputUp"]

		self.is_max_purity = lvlDict["isFinalMaxMineOutputUp"]
		self.is_max_capacity = lvlDict["isFinalMaxBandwidth"]
		self.is_max_zipline = lvlDict["isFinalMaxTravelPoleLimit"]
		self.is_max_combat = lvlDict["isFinalMaxBattleBuildingLimit"]

	# Compare with another Development level
	def shouldAdd(self, prev) -> bool:
		if prev is None:
			return True
		if (self.capacity != prev.capacity
				or self.zipline != prev.zipline
				or self.combat != prev.combat):
			return True
		if self.purity_up and not prev.purity_up:
			return True
		if self.is_max_purity:
			return True
		return False

# Data for pages
region_lvls = {}
areas = {a: [] for a in const.LEVEL_LOCATION.values()}

# Gather Data
for region in rdm_table.values():
	region_name = general.resolve_text(text_table, region["domainName"]["id"])
	region_lvls[region_name] = []
	region_id = region["domainId"]
	header_clr = region["domainColor"]

	exp_needed = 0
	for level in region["domainDevelopmentLevel"]:
		lvl = level["domainDevelopmentLevel"]  # Actual level number
		stock_limit = "{:,}".format(level["moneyLimit"]) # Format limit to match "xxx,xxx,xxx" format
		version = level["versionStart"]
		rewards = {}

		region_lvl_areas = {}
		for area in level["domainDevelopmentLevelEffect"].values():
			area_name = const.LEVEL_LOCATION.get(area["levelId"])
			if not area_name:
				continue
			area_data = DevelopmentLevel(lvl, area)
			prev = areas[area_name][-1] if areas[area_name] else None
			if area_data.shouldAdd(prev):
				areas[area_name].append(area_data)
				region_lvl_areas[area_name] = area_data

		rewards_list = rewards_table.get(level["rewardId"])
		if rewards_list:
			for item in rewards_list["itemBundles"]:
				v = list(item.values())
				item_name = const.ITEM_TYPE_NAME_BY_ID.get(v[1], v[1])
				if item_name: rewards[item_name] = v[0]

		region_lvls[region_name].append({
			"lvl": lvl,
			"stock_limit": stock_limit,
			"exp_needed": exp_needed,
			"version": version,
			"areas": region_lvl_areas,
			"rewards": rewards,
		})
		exp_needed = level["levelUpExp"]

# Process Data
with open(RDM_REGIONS_OUTPUT, "w", encoding="utf-8") as out:
	page = site.client.pages["Regional Development"]
	wikitext = page.text()

	i = 0
	for region_name, lvl_list in region_lvls.items():
		lines = []
		if i > 0: lines.append("|-|")
		lines.append(f"{region_name}=")
		lines.append("{{Regional Development Metric head}}")

		for lvl_data in lvl_list:
			lvl = lvl_data["lvl"]
			stock_limit = lvl_data["stock_limit"]
			exp_needed = lvl_data["exp_needed"]

			if lvl != 1:
				lines.append(f"{{{{Regional Development Metric level|{lvl}|{region_name}|{stock_limit}|{exp_needed}")
				rewards = []
				for name, count in lvl_data["rewards"].items():
					rewards.append(f"{name}: {count}")
				lines.append(f"|items = {', '.join(rewards)}")
				lines.append("}}")

			if lvl_data["areas"]:
				for area_name, area_lvl in lvl_data["areas"].items():

					prev = areas[area_name][ areas[area_name].index(area_lvl) - 1 ]
					changes = []

					if area_lvl.is_max_purity:
						changes.append("Mineral Purity:: Maxed")
					elif area_lvl.purity_up:
						changes.append("Mineral Purity:: Increased")
					if area_lvl.capacity != prev.capacity:
						changes.append(f"Protocol Capacity:: {prev.capacity} -> {area_lvl.capacity}{' {{Color|(Maxed)|0}}' if area_lvl.is_max_capacity else ''}")
					if area_lvl.zipline != prev.zipline:
						changes.append(f"Zipline Placement Limit:: {prev.zipline} -> {area_lvl.zipline}{' {{Color|(Maxed)|0}}' if area_lvl.is_max_zipline else ''}")
					if area_lvl.combat != prev.combat:
						changes.append(f"Combat Facility Limit:: {prev.combat} -> {area_lvl.combat}{' {{Color|(Maxed)|0}}' if area_lvl.is_max_combat else ''}")

					if changes:
						if site.client.pages[area_name + " (location)"].exists:
							area_name = f"{area_name} (location){{{{!}}}}{area_name}"
						lines.append(f"{{{{Regional Development Metric area|{area_name}")
						lines.append("|changes =")
						for j, ch in enumerate(changes):
							if j < len(changes) - 1:
								lines.append(ch + ",")
							else:
								lines.append(ch + "}}")

		lines.append("{{Table end}}")
		table = ("\n".join(lines))
		wikitext = re.sub(fr"(\|-\|\s*)?{region_name}=[\s\S]*?{{{{Table end}}}}", table, wikitext)
		i += 1

	out.write(f"""{{{{-start-}}}}
'''Regional Development'''
{wikitext}
{{{{-end-}}}}

""")

with open(RDM_AREAS_OUTPUT, "w", encoding="utf-8") as out:
	for area, lvls in areas.items():
		area = general.sanitize_name(area)

		table = "{{Area overview head}}\n"
		for i, l in enumerate(lvls):
			purity = "Default" if i == 0 else "Maxed" if l.is_max_purity else "Increased" if l.purity_up else "-"
			table += f"{{{{Area overview cell|level={l.level}|mineral={purity}|protocol={l.capacity}|zipline={l.zipline}|combat={l.combat}}}}}" + "\n"
		table += "{{Table end}}"
		
		page = site.client.pages[area + " (location)"]
		if page.exists:
			pass
		else: page = site.client.pages[area]
		if page.exists:
			wikitext = re.sub(r"{{Area overview head}}[\s\S]*?{{Table end}}", table, page.text(), re.DOTALL | re.MULTILINE)
			out.write(f"""{{{{-start-}}}}
'''{area}'''
{wikitext}
{{{{-end-}}}}

""")
			time.sleep(2)