import glob
import os
import re
import pytest


def expect_in(text, needle, message):
    if needle not in text:
        pytest.fail(message, pytrace=False)


def test_suffix_map_matches_longest_key_first(source):
    expect_in(source("endfield_item_parser.py"), "sorted(suffix_map.items(), key=lambda kv: len(kv[0]), reverse=True)",
              "endfield_item_parser.py: suffix_map is no longer matched longest key first")


def test_item_info_rejects_blank_names(source):
    expect_in(source("endfield_item_parser.py"), "if not self.name.strip()",
              "endfield_item_parser.py: GeneralItemInfo no longer rejects blank names")


def test_operator_wiki_section_keeps_subheadings(source):
    expect_in(source("endfield_operator_parser.py"), r"(?=\n==[^=]|$)",
              "endfield_operator_parser.py: get_wiki_section lookahead changed; ===sub=== headings may split sections")


def test_skill_stats_grouped_by_skill_id(source):
    expect_in(source(os.path.join("lib", "helpers", "operator.py")), "group_key = (condition_id, s_id, pos)",
              "lib/helpers/operator.py: extract_skill_stats no longer groups by (condition_id, s_id, pos)")


@pytest.mark.parametrize("parser", ["endfield_operator_parser.py", "endfield_enemy_parser.py", "endfield_weapon_parser.py"])
def test_fetch_wikitext_reraises(source, parser):
    if not re.search(r"if attempt == attempts:\s*\n\s*raise\b", source(parser)):
        pytest.fail(f"{parser}: fetch_wikitext no longer re-raises after the last retry", pytrace=False)


SCRIPTS = ["sophia-parser.sh"]
NOT_PUSHED = {"template_enemy_nav_data.txt", "template_gear_nav_data.txt", "full_mission_page_data.txt"}


@pytest.mark.parametrize("script", SCRIPTS)
def test_every_output_file_is_pushed(root, source, script, report):
    outputs = set()
    for parser in glob.glob(os.path.join(root, "endfield_*_parser.py")):
        outputs |= set(re.findall(r'^\w+_OUTPUT = os\.path\.join\(const\.OUTPUT_DIR, "([^"]+)"\)',
                                  source(os.path.basename(parser)), re.M))
    pushed = set(re.findall(r'^\s*python3 pwb\.py pagefromfile -file:"\$PARSER_DIR/output/([^"]+)"', source(script), re.M))
    report(f"Output files with no push line in {script}", outputs - NOT_PUSHED - pushed)
