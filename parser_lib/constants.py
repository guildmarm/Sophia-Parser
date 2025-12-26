import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_DIR = os.path.join(BASE_DIR, "input", "TableCfgOutput")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

LANGUAGE_FILES = {
    "en": "I18nTextTable_EN.json",
    "cn": "I18nTextTable_CN.json",
    "tc": "I18nTextTable_TC.json",
    "jp": "I18nTextTable_JP.json",
    "kr": "I18nTextTable_KR.json",
    "sp": "I18nTextTable_MX.json",
    "ru": "I18nTextTable_RU.json",
}