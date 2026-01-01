import parser_lib.io as io
import parser_lib.helpers as helpers
import parser_lib.game_files as game_files
import parser_lib.constants as const
import os

# Output file
OUTPUT_FILE = os.path.join(const.OUTPUT_DIR, "full_operator_page_data.txt")
os.makedirs(const.OUTPUT_DIR, exist_ok=True)

paths = game_files.build_paths(const.INPUT_DIR)

item_table = io.load_json(paths["item_table"])
skill_patch = io.load_json(paths["skill_patch"])
skill_patch = io.load_json(paths["character_table"])
skill_patch = io.load_json(paths["character_growth"])

# Load language files
language = io.load_languages(const.INPUT_DIR)

# Make that sausage
with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for operator_id, operator_data in operator_basic.items():
        item_data = item_table.get(operator_id)
        if not item_data:
            continue

        # Operator names
        name_id = item_data.get("name", {}).get("id")
        operator_name = helpers.resolve_text(language["en"], name_id)
        operator_name_clean = helpers.sanitize_name(operator_name)
        operator_name_image = helpers.sanitize_image_name(operator_name)
        cn_name = helpers.resolve_text(language["cn"], name_id)
        tc_name = helpers.resolve_text(language["tc"], name_id)
        jp_name = helpers.resolve_text(language["jp"], name_id)
        kr_name = helpers.resolve_text(language["kr"], name_id)
        sp_name = helpers.resolve_text(language["sp"], name_id)
        ru_name = helpers.resolve_text(language["ru"], name_id)

        # Output
        out.write(f"""{{{{-start-}}}}
'''{operator_name_clean}'''
{{{{Operator info
|name = {operator_name}
|rarity = {rarity}
|class = 
|weapon = 
|element = 
|faction = 
|tags = 
|main = 
|sub = 
|headhunting = 
|quote = 
}}}}
{{{{Operator tab}}}}
{{{{Operator infobox
|rarity = {rarity}
|name = {operator_name}
|image = 
{operator_name_image} Splash Art.png
|filename = {operator_id}
|cnname = {cn_name}
|tcname = {tc_name}
|jpname = {jp_name}
|krname = {kr_name}
|spname = {sp_name}
|runame = {ru_name}
|realname =  
|fileno = 
|theme = 
|illustrator = 
|jpcv = 
|cncv = 
|encv = 
|krcv = 
|gender = 
|age =
|experience = 
|birthplace =
|birthdate = 
|race = 
|height = 
|infection = 
|strength = 
|mobility = 
|endurance = 
|tactical = 
|skill = 
|originium = 
|related = 
|exp1 = 
|exp1d = 
|exp2 = 
|exp2d = 
|hb1 = 
|hb1d = 
|hb2 = 
|hb2d = 
}}}}

==Profile==


==Stats==

{{{{Operator data
{operator_stats}
{operator_potentials}
{operator_upgrade_items}
}}}}

==Combat Skills==

{operator_combat_skills}
{operator_skill_items}

==Talents==
{{Operator talent
|name = Forged
|icon = STR
|cond1 = Elite 1
|desc1 = Operator Strength +10.
|cond2 = Elite 2
|desc2 = Operator Strength +15.
|cond3 = Elite 3
|desc3 = Operator Strength +15.
|cond4 = Elite 4
|desc4 = Operator Strength +20.}}
{{Operator talent
|name = Inflamed for the Assault
|icon = Ember Talent 1 icon
|cond1 = Elite 1
|desc1 = When casting the battle skill {{Color|Forward|7}} March and the combo skill {{Color|Frontline Support|7}}, Ember gains of {{Color|30%|1d}} {{G|Protect|Protection}} and is less likely to be interrupted.{{Sic}}
|cond2 = Elite 2
|desc2 = When casting the battle skill {{Color|Forward|7}} March and the combo skill {{Color|Frontline Support|7}}, Ember gains of {{Color|50%|1d}} {{G|Protect|Protection}} and is less likely to be interrupted.{{Sic}}}}
{{Operator talent
|name = Pay the Ferric Price
|icon = Ember Talent 2 icon
|cond1 = Elite 2
|desc1 = When Ember receives DMG from the enemy, she gains ATK {{Color|+6%|1d}} for 7s. This effect can reach 3 stacks.
|cond2 = Elite 3
|desc2 = When Ember receives DMG from the enemy, she gains ATK {{Color|+9%|1d}} for 7s. This effect can reach 3 stacks.}}
{{Operator talent
|name = Outfitting
|icon = Gear icon
|cond1 = Elite 1
|desc1 = Activate this to let the operator equip blue quality gear.
|cond2 = Elite 2
|desc2 = Activate this to let the operator equip purple quality gear.
|cond3 = Elite 3
|desc3 = Activate this to let the operator equip gold quality gear.}}

==Base Skills==
{{Operator base skill
|name = Special Northern Training
|icon = MFG-efficiency
|facility = Manufacturing Cabin
|cond1 = Elite 1
|desc1 = Assign to [[Manufacturing Cabin]] to grant operator EXP material production efficiency +10%
|cond2 = Elite 3
|desc2 = Assign to Manufacturing Cabin to grant operator EXP material production efficiency +20%}}
{{Operator base skill
|name = Mycologist
|icon = GC-fungus
|facility = Growth Chamber
|cond1 = Elite 2
|desc1 = Assign to Growth Chamber to grant fungal matter growth rate +10%
|cond2 = Elite 4
|desc2 = Assign to Growth Chamber to grant fungal matter growth rate +20%}}

==Changelog==
{{Changelog|
*'''EVENT_NAME_HERE''' introduced.}}

==Navigation==
{{Operators}}

{{{{-stop-}}}}

""")
