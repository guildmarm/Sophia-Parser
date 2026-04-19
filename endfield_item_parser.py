import lib.io as io
import lib.general as general
import lib.helpers.item as item
import lib.game_files as game_files
import lib.constants as const
import lib.item_list as item_list
from lib.format_text import efdb_format
import os

# Output file
EMPLOYMENT_CONTRACT_OUTPUT = os.path.join(const.OUTPUT_DIR, "employment_contract_page_data.txt")
OPERATOR_TOKENS_OUTPUT = os.path.join(const.OUTPUT_DIR, "operator_tokens_page_data.txt")
OPERATOR_SNAPSHOTS_OUTPUT = os.path.join(const.OUTPUT_DIR, "operator_snapshots_page_data.txt")
PROGRESSION_MATERIALS_OUTPUT = os.path.join(const.OUTPUT_DIR, "progression_materials_page_data.txt")
RARE_MATERIALS_OUTPUT = os.path.join(const.OUTPUT_DIR, "rare_materials_page_data.txt")
GATHERABLES_OUTPUT = os.path.join(const.OUTPUT_DIR, "gatherables_page_data.txt")
NATURALS_OUTPUT = os.path.join(const.OUTPUT_DIR, "naturals_page_data.txt")
AIC_PRODUCTS_OUTPUT = os.path.join(const.OUTPUT_DIR, "aic_products_page_data.txt")
FACILITIES_OUTPUT = os.path.join(const.OUTPUT_DIR, "facilities_page_data.txt")
QUEST_ITEMS_OUTPUT = os.path.join(const.OUTPUT_DIR, "quest_items_page_data.txt")
GIFTS_OUTPUT = os.path.join(const.OUTPUT_DIR, "gifts_page_data.txt")
SEEDS_OUTPUT = os.path.join(const.OUTPUT_DIR, "seeds_page_data.txt")
CONTAINERS_OUTPUT = os.path.join(const.OUTPUT_DIR, "containers_page_data.txt")
CONSUMABLES_OUTPUT = os.path.join(const.OUTPUT_DIR, "consumables_page_data.txt")
PACKAGES_OUTPUT = os.path.join(const.OUTPUT_DIR, "packages_page_data.txt")
SYSTEM_BLUEPRINTS_OUTPUT = os.path.join(const.OUTPUT_DIR, "system_blueprints_page_data.txt")
#ESSENCES_OUTPUT = os.path.join(const.OUTPUT_DIR, "essences_page_data.txt")
FORMULAS_OUTPUT = os.path.join(const.OUTPUT_DIR, "formulas_page_data.txt")
PHOTO_OUTPUT = os.path.join(const.OUTPUT_DIR, "photo_page_data.txt")
PROFILE_OUTPUT = os.path.join(const.OUTPUT_DIR, "profile_page_data.txt")
ETCHSPACE_OUTPUT = os.path.join(const.OUTPUT_DIR, "etchspace_page_data.txt")
SANITY_OUTPUT = os.path.join(const.OUTPUT_DIR, "sanity_page_data.txt")
CURRENCY_OUTPUT = os.path.join(const.OUTPUT_DIR, "currency_page_data.txt")
HEADHUNTING_OUTPUT = os.path.join(const.OUTPUT_DIR, "headhunting_page_data.txt")
MISCELLANEOUS_OUTPUT = os.path.join(const.OUTPUT_DIR, "miscellaneous_page_data.txt")
os.makedirs(const.OUTPUT_DIR, exist_ok=True)

paths = game_files.build_paths(const.INPUT_DIR)

item_table = io.load_json(paths["item_table"])
item_type = io.load_json(paths["item_type"])
item_chest = io.load_json(paths["item_chest"])
use_item = io.load_json(paths["use_item"])
equip_item = io.load_json(paths["equip_item"])
reward_table = io.load_json(paths["reward_table"])
system_jump_table = io.load_json(paths["system_jump"])
skill_patch = io.load_json(paths["skill_patch"])

# Update item exclusion list
newly_processed_items = []

# Load language files
language = io.load_languages(const.INPUT_DIR)

# Duplicate item name check
name_counts = {}
for entry in item_table.values():
    n_id = entry.get("name", {}).get("id")
    name = general.resolve_text(language["en"], n_id)
    if name:
        name_counts[name] = name_counts.get(name, 0) + 1

# Common item info
class GeneralItemInfo:
    def __init__(self, item_id, item_data, language, system_jump_table, name_counts):
        name_id = item_data.get("name", {}).get("id")
        self.name = general.resolve_text(language["en"], name_id)

        if name_counts.get(self.name, 0) > 1:
            suffix_map = {
                "water": " (Clean Water)",
                "sewage": " (Sewage)",
                "grass_1": " (Jincao Solution)",
                "grass_2": " (Yazhen Solution)",
                "xiranite": " (Liquid Xiranite)",
                "xiranite_poly": " (Xircon Effluent)",
                "xiranite_lowpoly": " (Inert Xircon Effluent)",
                "acid": " (Precipitation Acid)",
                "xiranite_enr": " (Liquid Heavy Xiranite)",
                "copper": " (Cuprium Solution)",
                "copper_enr": " (Hetonite Solution)",
            }
            
            for key, val in suffix_map.items():
                if item_id.endswith(key):
                    self.name += val
                    break

        raw_type_id = item_data.get("type")
        self.type = const.ITEM_TYPE_NAME.get(raw_type_id, "")
        self.name_clean = general.sanitize_name(self.name)
        
        if "Endministrator" in self.name:
            self.item_id_output = f"{item_id}, {item_id.replace('chr_0003_endminf', 'chr_0002_endminm').replace('chr_0003_endmin', 'chr_0002_endminm')}"
            self.image = (
                f"\n"
                f"{general.sanitize_image_name(self.name)}_{general.sanitize_image_name(self.type)}_(Female).png:Female;\n"
                f"{general.sanitize_image_name(self.name)}_{general.sanitize_image_name(self.type)}_(Male).png:Male"
            )
        else:
            self.item_id_output = item_id
            self.image = f"{general.sanitize_image_name(self.name)}.png"

        self.cn = general.resolve_text(language["cn"], name_id)
        self.tc = general.resolve_text(language["tc"], name_id)
        self.jp = general.resolve_text(language["jp"], name_id)
        self.kr = general.resolve_text(language["kr"], name_id)
        self.sp = general.resolve_text(language["sp"], name_id)
        self.ru = general.resolve_text(language["ru"], name_id)
        self.desc = efdb_format(general.resolve_text(language["en"], item_data.get("desc", {}).get("id")))
        self.deco = efdb_format(general.resolve_text(language["en"], item_data.get("decoDesc", {}).get("id")))
        self.rarity = item_data.get("rarity", "")
        self.source = item.resolve_item_sources(item_id, item_table, system_jump_table, language)
        
        self.is_invalid = False
        if not self.name.strip() or any(x in self.name for x in ("TEST", "(OBSOLETE)", "TEMP", "(SIM)", "(Self-Powered)")):
            self.is_invalid = True

# Employment Contracts
with open(EMPLOYMENT_CONTRACT_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") != 4 or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean} (Employment Contract)'''
{{{{Item infobox
|name = {info.name} (Employment Contract)
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Employment Contracts
|rarity = {info.rarity}}}}}
'''{info.name} (Employment Contract)''' is an [[Employment Contracts|employment contract]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Employment Contracts]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Operator Tokens
with open(OPERATOR_TOKENS_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") != 42 or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Potential Tokens
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Potential Tokens|potential token]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Potential Tokens]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Operator Snapshots
with open(OPERATOR_SNAPSHOTS_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") != 76 or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Operator Snapshots
|rarity = {info.rarity}}}}}
'''{info.name}''' is an [[Operator Snapshots|operator snapshot]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Operator Snapshots]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Progression Materials
with open(PROGRESSION_MATERIALS_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") not in (7, 25, 26, 27, 95, 96) or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Progression Materials
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Progression Materials|progression material]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Progression Materials]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Rare Materials
with open(RARE_MATERIALS_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") != 8 or item_data.get("showingType") != 16 or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Rare Materials
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Rare Materials|rare material]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Rare Materials]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Gatherables
with open(GATHERABLES_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") != 8 or item_data.get("showingType") != 15 or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Gatherables
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Gatherables|gatherable]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Gatherables]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Naturals
with open(NATURALS_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") != 8 or item_data.get("sortId1") != -80 or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Naturals
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Naturals|natural]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

{{{{RecipeTable|ingredient={info.name_clean}}}}}
==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Naturals]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# AIC Products
with open(AIC_PRODUCTS_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") != 8 or item_data.get("sortId1") not in (-81, -82) or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = AIC Products
|rarity = {info.rarity}}}}}
'''{info.name}''' is an [[AIC Products|AIC product]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

{{{{RecipeTable|ingredient={info.name_clean}}}}}
==Acquisition==
{info.source}
{{{{RecipeTable|product={info.name_clean}}}}}

==Navigation==
{{{{Items}}}}
[[Category:AIC Products]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Facilities
with open(FACILITIES_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") not in (9, 10, 11, 54) or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        if item_id in item_list.ITEM_LIST or item_data.get("type") != 10:
            item_recipe = f"{{{{RecipeTable|product={info.name_clean}}}}}"
        else:
            item_recipe = ""

        facility_power = ""
        recipe_facility = ""

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Facility infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Facilities
|rarity = {info.rarity}
|power = {facility_power}}}}}
'''{info.name}''' is an [[AIC]] [[Facilities|facility]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==
{recipe_facility}
==Acquisition==
{info.source}
{item_recipe}

==Navigation==
{{{{Facilities}}}}
[[Category:Facilities]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Quest Items
with open(QUEST_ITEMS_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") != 13 or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Quest Items
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Quest Items|quest]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Quest Items]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Gifts
with open(GIFTS_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") != 33 or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Gifts
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Gifts|gift]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Gifts]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Seeds
with open(SEEDS_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") != 34 or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Seeds
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Seeds|seed]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Seeds]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Reward Containers
with open(CONTAINERS_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") not in (43, 60) or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        # Container item contents
        container_items = item.get_container_reward_items(item_id, item_chest, reward_table, item_table, language)

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Reward Containers
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Reward Containers|reward container]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

{container_items}

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Reward Containers]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Consumables
with open(CONSUMABLES_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") not in (48, 52) or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue
        
        # Item usage and tactical effects
        item_usage = item.get_item_usage_effect(item_id, use_item, language)
        usage_effect = f"===Usage Effect===\n{item_usage}\n" if item_usage.strip() else ""
        item_tactical = item.get_item_tactical_effect(item_id, equip_item, language)
        tactical_effect = f"===Tactical Effect===\n{item_tactical}\n" if item_tactical.strip() else ""

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Consumables
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Consumables|consumable]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

{usage_effect}
{tactical_effect}
==Acquisition==
{info.source}
{{{{RecipeTable|product={info.name_clean}}}}}

==Navigation==
{{{{Items}}}}
[[Category:Consumables]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Packages
with open(PACKAGES_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") != 56 or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Packages
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Packages|package]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Packages]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# System Blueprints
with open(SYSTEM_BLUEPRINTS_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") != 64 or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue
        if info.name == "System Blueprint":
            continue
            
        out.write(f"""{{{{-start-}}}}
'''{info.name_clean} (Blueprint)'''
{{{{Item infobox
|name = {info.name} (Blueprint)
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = System Blueprints
|rarity = {info.rarity}}}}}
'''{info.name} (Blueprint)''' is a [[System Blueprints|blueprint]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:System Blueprints]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

### Holding off on this for now because we'll need a unique output. The pages are unified into an Essences page on the wiki rather than individual entries.

## Essences
# with open(ESSENCES_OUTPUT, "w", encoding="utf-8") as out:
#     for item_id, item_data in item_table.items():
#         if item_id in item_list.ITEM_LIST or item_data.get("type") != 19 or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
#             continue

#         info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
#         if info.is_invalid:
#             continue
            
#         out.write(f"""{{{{-start-}}}}
# '''{info.name_clean}'''
# {{{{Item infobox
# |name = {info.name}
# |filename = {info.item_id_output}{info.image}
# |cnname = {info.cn}
# |tcname = {info.tc}
# |jpname = {info.jp}
# |krname = {info.kr}
# |spname = {info.sp}
# |runame = {info.ru}
# |type = Essences
# |rarity = {info.rarity}}}}}
# '''{info.name}''' is an [[Essences|essence]] [[item]] in ''[[Arknights: Endfield]]''.

# {{{{Item description|{info.decoDesc}}}}}
# ==Usage==
# {info.desc}
# ==Acquisition==
# {info.source}

# ==Navigation==
# {{{{Items}}}}
# [[Category:Essences]]

# {{{{-stop-}}}}

# """)
#        if item_id not in item_list.ITEM_LIST:
#            item_list.ITEM_LIST.append(item_id)
#            newly_processed_items.append(item_id)

# Formulas
with open(FORMULAS_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") not in (12, 39, 40, 47) or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        formula_append = ""
        if item_id in item_list.ITEM_LIST or item_data.get("type") == 47:
            formula_append = f" (Formula)"

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}{formula_append}'''
{{{{Item infobox
|name = {info.name}{formula_append}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Formulas
|rarity = {info.rarity}}}}}
'''{info.name}{formula_append}''' is a [[Formulas|formula]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Formulas]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Photo
with open(PHOTO_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") not in (58, 70) or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Photo
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Photo|photo]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Photo]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Profile
with open(PROFILE_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") not in (66, 67, 68) or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        profile_append = ""
        if item_id in item_list.ITEM_LIST or item_data.get("type") == 66:
            profile_append = f" (Portrait)"
        elif item_id in item_list.ITEM_LIST or item_data.get("type") == 67:
            profile_append = f" (Frame)"
        elif item_id in item_list.ITEM_LIST or item_data.get("type") == 68:
            profile_append = f" (Theme)"

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}{profile_append}'''
{{{{Item infobox
|name = {info.name}{profile_append}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Profile
|rarity = {info.rarity}}}}}
'''{info.name}{profile_append}''' is a [[Profile|profile]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Profile]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Etchspace
with open(ETCHSPACE_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") not in (71, 72, 74, 75, 77) or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Etchspace
|rarity = {info.rarity}}}}}
'''{info.name}''' is an [[Etchspace|etchspace]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Etchspace]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Sanity
with open(SANITY_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") not in (21, 22, 63, 97) or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Sanity
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Sanity|sanity]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Sanity]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Currency
with open(CURRENCY_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") not in (1, 2, 29, 44, 49, 53, 60, 61, 79, 88, 98) or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Currency
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Currency|currency]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Currency]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Headhunting
with open(HEADHUNTING_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if item_id in item_list.ITEM_LIST or item_data.get("type") not in (14, 82, 83) or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin")):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Headhunting
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Headhunting|headhunting]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Headhunting]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Miscellaneous
with open(MISCELLANEOUS_OUTPUT, "w", encoding="utf-8") as out:
    for item_id, item_data in item_table.items():
        if (item_id in item_list.ITEM_LIST or item_data.get("type") not in (8, 37, 38, 50, 51, 55, 65, 69, 80, 84, 85, 87, 89, 91) or (item_data.get("type") == 8 and item_data.get("sortId1") != -61) or any(x in item_id for x in ("chr_0002_endminm", "chr_9000_endmin"))):
            continue

        info = GeneralItemInfo(item_id, item_data, language, system_jump_table, name_counts)
        if info.is_invalid:
            continue

        out.write(f"""{{{{-start-}}}}
'''{info.name_clean}'''
{{{{Item infobox
|name = {info.name}
|filename = {info.item_id_output}
|images = {info.image}
|cnname = {info.cn}
|tcname = {info.tc}
|jpname = {info.jp}
|krname = {info.kr}
|spname = {info.sp}
|runame = {info.ru}
|type = Miscellaneous
|rarity = {info.rarity}}}}}
'''{info.name}''' is a [[Miscellaneous|miscellaneous]] [[item]] in ''[[Arknights: Endfield]]''.

{{{{Item description|{info.desc}|{info.deco}}}}}
==Usage==

==Acquisition==
{info.source}

==Navigation==
{{{{Items}}}}
[[Category:Miscellaneous]]

{{{{-stop-}}}}

""")
        if item_id not in item_list.ITEM_LIST:
            item_list.ITEM_LIST.append(item_id)
            newly_processed_items.append(item_id)

# Add new items to exclusion list
item.save_new_items_to_list(newly_processed_items)