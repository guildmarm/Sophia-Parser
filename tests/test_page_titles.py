import glob
import os
import re
import pytest
import lib.general as general
import lib.constants as const


def blank_names(entries, en):
    return [entry_id for entry_id, name_id in entries
            if not general.sanitize_name(general.resolve_text(en, name_id)).strip()]


def test_operator_names_resolve(table, en, report):
    entries = [(oid, data["name"]["id"]) for oid, data in table("character_table").items()
               if oid not in ("chr_0003_endminf", "chr_9000_endmin")]
    report("Operators with blank names", blank_names(entries, en))


def test_enemy_names_resolve(table, en, report):
    display = table("enemy_display")
    entries = [(eid, display[eid].get("name", {}).get("id")) for eid in table("enemy_attribute") if display.get(eid)]
    report("Enemies with blank names", blank_names(entries, en))


def test_weapon_names_resolve(table, en, report):
    items = table("item_table")
    entries = [(wid, items[wid].get("name", {}).get("id")) for wid in table("weapon_basic") if items.get(wid)]
    report("Weapons with blank names", blank_names(entries, en))


def test_gear_names_resolve(table, en, report):
    items = table("item_table")
    entries = [(gid, items[gid].get("name", {}).get("id")) for gid in table("equip_table") if items.get(gid)]
    report("Gear with blank names", blank_names(entries, en))


OUTPUT_FILES = sorted(glob.glob(os.path.join(const.OUTPUT_DIR, "*.txt")))


@pytest.mark.parametrize("path", OUTPUT_FILES, ids=os.path.basename)
def test_output_titles_not_blank(path, report):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    titles = re.findall(r"\{\{-start-\}\}\n'''(.*?)'''", text)
    missing = text.count("{{-start-}}") - len(titles)
    report("Page blocks without a '''Title''' line", [f"{missing} block(s)"] if missing else [])
    bad = [t for t in titles if not t.strip() or t.startswith("/") or re.search(r"[\[\]{}]", t)]
    report("Blank or invalid titles", [repr(t) for t in bad])
