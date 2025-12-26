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
    }