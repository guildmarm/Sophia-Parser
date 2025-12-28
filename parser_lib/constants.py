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

ATTRIBUTE_TYPE = {
    0: "Level",
    1: "HP",
    2: "Attack",
    3: "Defense",
    4: "Physical DMG Reduction",
    5: "Heat DMG Reduction",
    6: "Electric DMG Reduction",
    7: "Cryo DMG Reduction",
    9: "Critical Rate",
    10: "Critical DMG",
    17: "Basic Attack DMG Bonus",
    26: "Stagger Efficiency Bonus",
    28: "Ultimate DMG Bonus",
    29: "Treatment Bonus",
    30: "Treatment Received Bonus",
    32: "Battle Skill DMG Bonus",
    33: "Combo Skill DMG Bonus",
    35: "Heat Burst DMG Increase",
    36: "Electric Burst DMG Increase",
    37: "Cryo Burst DMG Increase",
    38: "Nature Burst DMG Increase",
    39: "Strength",
    40: "Agility",
    41: "Intellect",
    42: "Will",
    44: "Ultimate Gain Efficiency",
    47: "Combo Skill Cooldown Reduction",
    48: "Nature DMG Reduction",
    49: "Arts Reaction and Burst DMG",
    50: "Physical DMG Bonus",
    51: "Heat DMG Bonus",
    52: "Electric DMG Bonus",
    53: "Cryo DMG Bonus",
    54: "Nature DMG Bonus",
    56: "Combustion Boost",
    57: "Electrification Boost",
    58: "Solidification Boost",
    59: "Corrosion Boost",
    60: "Æther DMG Reduction",
    61: "DMG Bonus vs. Staggered",
    80: "Physical Resistance",
    81: "Nature Resistance",
    82: "Cryo Resistance",
    83: "Electric Resistance",
    84: "Heat Resistance",
    85: "Æther Resistance",
    87: "Arts Intensity",
  }