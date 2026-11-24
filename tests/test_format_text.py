import glob
import inspect
import os
import re
import pytest
import lib.format_text as format_text
import lib.constants as const
import lib.general as general
import lib.helpers.weapon as weapon
import lib.helpers.operator as operator
import lib.helpers.gear as gear
import lib.helpers.item as item
import lib.helpers.enemy as enemy

LEFTOVER_TAG = re.compile(r"<[@#][\w.]+>|</>")
PATTERNS = {k: v for k, v in vars(format_text).items() if isinstance(v, re.Pattern)}
MODULE_FORMAT_SKIPS = {"BA_PD", "BA_PHY", "BA_CRYST", "BA_PULSE", "BA_FIRE", "BA_NATUR", "BA_ETHER"}
LUA_COLOR_TAGS = {"blue", "green", "stagger", "key", "grey"}


def sample_text(pattern):
    return pattern.pattern.replace("\\.", ".").replace("(.*?)", "word")


def patterns_used(fn):
    lines = [l for l in inspect.getsource(fn).splitlines() if not l.strip().startswith("#")]
    return set(re.findall(r"\b([A-Z_]+)\.sub\(", "\n".join(lines)))


def test_efdb_format_uses_every_pattern(report):
    report("Patterns with no .sub line in efdb_format", set(PATTERNS) - patterns_used(format_text.efdb_format))


def test_module_format_uses_every_pattern(report):
    report("Patterns with no .sub line in module_format", set(PATTERNS) - patterns_used(format_text.module_format) - MODULE_FORMAT_SKIPS)


@pytest.mark.parametrize("name", sorted(PATTERNS))
def test_efdb_format_converts_tag(name):
    out = format_text.efdb_format(sample_text(PATTERNS[name]))
    assert LEFTOVER_TAG.search(out) is None
    assert "word" in out


@pytest.mark.parametrize("name", sorted(set(PATTERNS) - MODULE_FORMAT_SKIPS))
def test_module_format_converts_tag(name):
    out = format_text.module_format(sample_text(PATTERNS[name]))
    assert LEFTOVER_TAG.search(out) is None
    assert "word" in out


def test_weapon_skill_text_is_fully_formatted(table, en, report):
    language = {"en": en}
    skill_ids = sorted({sid for data in table("weapon_basic").values() for sid in data.get("weaponSkillList", []) if sid})
    found = {}
    for sid in skill_ids:
        lua = weapon.build_weapon_skill_lua(sid, table("skill_patch"), language)
        tags = set(LEFTOVER_TAG.findall(lua)) | (set(re.findall(r"<([^/<>]+?)>", lua)) - LUA_COLOR_TAGS - {tag.strip("<>") for tag in LEFTOVER_TAG.findall(lua)})
        for tag in tags:
            found.setdefault(tag, []).append(sid)
    report("Weapon skills with unformatted or unknown tags", found)


def ids_by_tag(outputs):
    found = {}
    for entry_id, text in outputs:
        for tag in set(LEFTOVER_TAG.findall(text or "")):
            found.setdefault(tag, []).append(entry_id)
    return found


def test_operator_text_is_fully_formatted(table, en, report, monkeypatch):
    language = {"en": en}
    growth = table("character_growth")
    found = {}
    current = ""

    def checked_efdb_format(text):
        out = format_text.efdb_format(text)
        for tag in set(LEFTOVER_TAG.findall(out or "")):
            found.setdefault(tag, set()).add(current)
        return out

    monkeypatch.setattr(operator, "efdb_format", checked_efdb_format)
    for oid, data in table("character_table").items():
        if oid in ("chr_0003_endminf", "chr_9000_endmin"):
            continue
        name = general.resolve_text(en, data["name"]["id"])
        weapon_type = const.WEAPON_TYPE.get(data.get("weaponType"), "")
        main_attr = const.ATTRIBUTE_TYPE.get(data.get("mainAttrType"), "")
        calls = {
            "skills": lambda: operator.get_operator_combat_skills(oid, growth, table("skill_patch"), language, weapon_type),
            "talents": lambda: operator.operator_passive_talents(oid, name, growth, table("potential_effect"), language, table("pot_effect_enums")),
            "potentials": lambda: operator.get_operator_potentials(oid, table("character_potential"), table("potential_effect"), language, table("pot_effect_enums")),
            "main attribute talent": lambda: operator.main_attribute_talent(oid, growth, language, main_attr),
            "outfit talent": lambda: operator.operator_outfit_talent(oid, growth, language),
            "base skills": lambda: operator.operator_base_skills(oid, growth, table("base_skill"), language),
        }
        for label, call in calls.items():
            current = f"{oid} {label}"
            for tag in set(LEFTOVER_TAG.findall(call() or "")):
                found.setdefault(tag, set()).add(current)
    report("Operator text with unformatted tags", found)


def test_gear_set_effect_is_fully_formatted(table, en, report):
    language = {"en": en}
    items = table("item_table")
    outputs = [(gid, format_text.efdb_format(gear.resolve_gear_set_and_effect(gid, table("equip_suit"), table("skill_patch"), language)[1]))
               for gid in table("equip_table") if items.get(gid)]
    report("Gear set effects with unformatted tags", ids_by_tag(outputs))


def test_item_effects_are_fully_formatted(table, en, report):
    language = {"en": en}
    outputs = [(f"{iid} usage", item.get_item_usage_effect(iid, table("use_item"), language)) for iid in table("use_item")]
    outputs += [(f"{iid} tactical", item.get_item_tactical_effect(iid, table("equip_item"), language)) for iid in table("equip_item")]
    report("Item effects with unformatted tags", ids_by_tag(outputs))


def test_enemy_abilities_are_fully_formatted(table, en, report):
    language = {"en": en}
    display = table("enemy_display")
    outputs = [(eid, enemy.resolve_enemy_abilities(display[eid], table("enemy_ability"), language))
               for eid in table("enemy_attribute") if display.get(eid)]
    report("Enemy abilities with unformatted tags", ids_by_tag(outputs))


OUTPUT_FILES = sorted(glob.glob(os.path.join(const.OUTPUT_DIR, "*.txt")))
LUA_OUTPUT = "module_weapon_skill_data.txt"


@pytest.mark.parametrize("path", OUTPUT_FILES, ids=os.path.basename)
def test_output_has_no_leftover_tags(path, report):
    with open(path, encoding="utf-8") as f:
        report(f"Unformatted tags in {os.path.basename(path)}", set(LEFTOVER_TAG.findall(f.read())))


@pytest.mark.skipif(not os.path.isfile(os.path.join(const.OUTPUT_DIR, LUA_OUTPUT)), reason="no Lua output")
def test_lua_output_only_uses_known_color_tags(report):
    with open(os.path.join(const.OUTPUT_DIR, LUA_OUTPUT), encoding="utf-8") as f:
        texts = re.findall(r'text = "((?:[^"\\]|\\.)*)"', f.read())
    tags = {tag for text in texts for tag in re.findall(r"<([^/<>]+?)>", text)}
    report("Lua module tags not in the colors table", tags - LUA_COLOR_TAGS)
