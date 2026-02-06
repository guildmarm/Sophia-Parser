from .io import load_json
from .constants import LANGUAGE_FILES, ATTRIBUTE_TYPE, ATTRIBUTE_TYPE_ALT, ATTRIBUTE_TYPE_RAW, TARGET_LEVELS, SPACESHIP_ROOM_TYPE, SPACESHIP_ROOM_TYPE_ALT, TARGET_LEVELS
from .format_text import module_format, efdb_format
from collections import OrderedDict, defaultdict
import math
import html
import re

# Get text from text tables
def resolve_text(lang_table, text_id):
    if not text_id or str(text_id) == "0":
        return ""
    return lang_table.get(str(text_id), "")

# Get those germs off (Can't have a page title with [] or {} in mediawiki)
def sanitize_name(name):
    if not name:
        return ""
    return name.replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")").replace("\u00B7", " ").replace("<i>", "").replace("</i>", "")

# Images cannot contain a colon. Seperated from the sanitized weapon name because page names CAN have a colon.
def sanitize_image_name(name):
    if not name:
        return ""
    return name.replace(":", "").replace(" ", "_").replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")

# Source of system_jump_table values
def resolve_sources(source_ids, system_jump_table, language, lang="en"):
    if not source_ids:
        return ""
    sources = []
    for oid in source_ids:
        entry = system_jump_table.get(oid)
        if not entry:
            continue
        desc_id = entry.get("desc", {}).get("id")
        localized_desc = resolve_text(language[lang], desc_id)
        if localized_desc:
            sources.append(localized_desc)
    return ", ".join(sources)
