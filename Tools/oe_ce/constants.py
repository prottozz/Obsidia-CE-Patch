DEFAULT_OBSIDIA_CORE = r"C:\Projects\Assistant\294100\2519492373\1.6\Core"

# Core ThingDefs that have verbs but are melee weapons (catalogued in melee.yaml).
RANGED_SCAN_EXCLUDE = frozenset(
    {
        "OES_Katana",
        "OMC_Whip",
        "EGO_Whip",
        "OMG_Trophy_PowerGuitar",
        "OTC_Trophy_Cards_I",
    }
)

WEAPON_TYPES = (
    "pistol", "smg", "shotgun", "rifle", "sniper",
    "bow", "lmg", "minigun", "launcher", "rocket",
)
DAMAGE_CLASSES = (
    "ballistic", "energy", "fire", "emp", "acid", "cryo", "bio",
)
EMP_SIDE_TYPES = frozenset(
    ("shotgun", "rifle", "sniper", "lmg", "minigun", "bow")
)
BASE_CARTRIDGES = ("standard", "ap", "hp")
RUNGS = (
    "proto", "odc_t1", "odc_t2", "odc_t3", "odc_t4",
    "occ", "otc", "omc", "oec", "oe",
    "occ_reforge", "omc_mod", "oec_t2", "otc_t2",
    "cac_t1", "cac_t2", "bio_t3", "bio_t4",
    "omg", "heroic", "trophy", "mech",
)
YAML_CLASS_FILES = {
    "ballistic": "ballistic.yaml",
    "energy": "energy.yaml",
    "fire": "fire.yaml",
    "emp": "emp.yaml",
    "acid": "acid.yaml",
    "cryo": "cryo.yaml",
    "bio": "bio.yaml",
}
