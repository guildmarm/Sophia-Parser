import os

# Game Files
ITEM_TABLE = "ItemTable.json"
ENEMY_ATTRIBUTE = "EnemyAttributeTemplateTable.json"
ENEMY_ABILITY = "EnemyAbilityDescTable.json"
ENEMY_DISPLAY = "EnemyTemplateDisplayInfoTable.json"
DISTRIBUTION_INFO = "DistributionInfoTable.json"
ENEMY_DROP = "WikiEnemyDropTable.json"
ENEMY_TYPE = "DisplayEnemyTypeTable.json"
ENEMY_GROUP = "WikiEntryDataTable.json"
WIKI_GROUP = "WikiGroupTable.json"
WEAPON_BASIC = "WeaponBasicTable.json"
SKILL_PATCH = "SkillPatchTable.json"
WEAPON_BREAKTHROUGH = "WeaponBreakThroughTemplateTable.json"
WEAPON_UPGRADE = "WeaponUpgradeTemplateTable.json"
SYSTEM_JUMP = "SystemJumpTable.json"
EQUIP_FORMULA = "EquipFormulaTable.json"
EQUIP_PACK_FORMULA = "EquipPackFormulaTable.json"
EQUIP_PACK = "EquipPackTable.json"
EQUIP_SUIT = "EquipSuitTable.json"
EQUIP_TABLE = "EquipTable.json"
ATTRIBUTE_SHOW = "AttributeShowConfigTable.json"
ATTRIBUTE_FILTER = "AttributeFilterTable.json"
CHARACTER_TABLE = "CharacterTable.json"
CHARACTER_GROWTH = "CharGrowthTable.json"
CHARACTER_PROFESSION = "CharProfessionTable.json"
CHARACTER_TAGS = "CharacterTagTable.json"
CHARACTER_BATTLE_TAGS = "CharBattleTagTable.json"
CHARACTER_TAG_DES = "CharacterTagDesTable.json"
CHARACTER_POTENTIAL = "CharacterPotentialTable.json"
POTENTIAL_EFFECT = "PotentialTalentEffectTable.json"
CHARACTER_BASE_SKILL = "SpaceshipCharSkillTable.json"
BASE_SKILL = "SpaceshipSkillTable.json"
TAG_DATA = "TagDataTable.json"
GACHA_POOL_CONTENT = "GachaCharPoolContentTable.json"
GACHA_POOL = "GachaCharPoolTable.json"
ENUMS_TABLE = "Enums.json"



def build_paths(input_dir: str) -> dict[str, str]:
    return {
        "item_table": os.path.join(input_dir, ITEM_TABLE),
        "enemy_attribute": os.path.join(input_dir, ENEMY_ATTRIBUTE),
        "enemy_ability": os.path.join(input_dir, ENEMY_ABILITY),
        "enemy_display": os.path.join(input_dir, ENEMY_DISPLAY),
        "distribution_info": os.path.join(input_dir, DISTRIBUTION_INFO),
        "enemy_drop": os.path.join(input_dir, ENEMY_DROP),
        "enemy_type": os.path.join(input_dir, ENEMY_TYPE),
        "enemy_group": os.path.join(input_dir, ENEMY_GROUP),
        "wiki_group": os.path.join(input_dir, WIKI_GROUP),
        "weapon_basic": os.path.join(input_dir, WEAPON_BASIC),
        "skill_patch": os.path.join(input_dir, SKILL_PATCH),
        "weapon_breakthrough": os.path.join(input_dir, WEAPON_BREAKTHROUGH),
        "weapon_upgrade": os.path.join(input_dir, WEAPON_UPGRADE),
        "system_jump": os.path.join(input_dir, SYSTEM_JUMP),
        "equip_formula": os.path.join(input_dir, EQUIP_FORMULA),
        "equip_pack_formula": os.path.join(input_dir, EQUIP_PACK_FORMULA),
        "equip_pack": os.path.join(input_dir, EQUIP_PACK),
        "equip_suit": os.path.join(input_dir, EQUIP_SUIT),
        "equip_table": os.path.join(input_dir, EQUIP_TABLE),
        "attribute_show": os.path.join(input_dir, ATTRIBUTE_SHOW),
        "attribute_filter": os.path.join(input_dir, ATTRIBUTE_FILTER),
        "character_table": os.path.join(input_dir, CHARACTER_TABLE),
        "character_growth": os.path.join(input_dir, CHARACTER_GROWTH),
        "character_profession": os.path.join(input_dir, CHARACTER_PROFESSION),
        "character_tags": os.path.join(input_dir, CHARACTER_TAGS),
        "character_battle_tags": os.path.join(input_dir, CHARACTER_BATTLE_TAGS),
        "character_tag_des": os.path.join(input_dir, CHARACTER_TAG_DES),
        "character_potential": os.path.join(input_dir, CHARACTER_POTENTIAL),
        "potential_effect": os.path.join(input_dir, POTENTIAL_EFFECT),
        "character_base_skill": os.path.join(input_dir, CHARACTER_BASE_SKILL),
        "base_skill": os.path.join(input_dir, BASE_SKILL),
        "tag_data": os.path.join(input_dir, TAG_DATA),
        "gacha_pool_content": os.path.join(input_dir, GACHA_POOL_CONTENT),
        "gacha_pool": os.path.join(input_dir, GACHA_POOL),
        "enums_table": os.path.join(input_dir, ENUMS_TABLE),
    }