import json
import os
from .constants import LANGUAGE_FILES


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_languages(input_dir):
    language = {}
    for lang, filename in LANGUAGE_FILES.items():
        path = os.path.join(input_dir, filename)
        language[lang] = load_json(path)
    return language