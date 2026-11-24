from collections import Counter
import lib.general as general
import lib.constants as const
import lib.item_list as item_list
import lib.mission_list as mission_list
from lib.helpers.enemy import resolve_enemy_independent_stats


def test_sanitize_name():
    assert general.sanitize_name("A[B]{C}·<i>D</i>") == "A(B)(C) D"


def test_sanitize_image_name():
    assert general.sanitize_image_name("Ward: Base [1]") == "Ward_Base_(1)"


def test_resolve_text_blank_ids():
    assert general.resolve_text({"0": "x"}, 0) == ""
    assert general.resolve_text({}, "123") == ""


def physical_resist(attrs):
    data = {"levelIndependentAttributes": {"attrs": [{"attrType": t, "attrValue": v} for t, v in attrs.items()]}}
    return resolve_enemy_independent_stats(data)[5]


def test_enemy_resist_uses_base_when_not_one():
    assert physical_resist({80: 0.8, 94: 50}) == 0.8


def test_enemy_resist_falls_back_to_offset():
    assert physical_resist({80: 1, 94: 20}) == "0.8"
    assert physical_resist({}) == "1"


def test_dialogue_titles_still_exist_in_game_text(table, en, report):
    titles = {general.resolve_text(en, v.get("voiceTitle", {}).get("id")).strip()
              for op in table("character_table").values() for v in op.get("profileVoice", [])}
    report("DIALOGUE_TYPE keys no longer in game text", set(const.DIALOGUE_TYPE) - titles)


def test_item_list_has_no_duplicates(report):
    report("Duplicate IDs in ITEM_LIST", [i for i, n in Counter(item_list.ITEM_LIST).items() if n > 1])


def test_mission_list_has_no_duplicates(report):
    report("Duplicate IDs in MISSION_LIST", [m for m, n in Counter(mission_list.MISSION_LIST).items() if n > 1])
