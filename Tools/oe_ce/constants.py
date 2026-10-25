DEFAULT_OBSIDIA_CORE = r"C:\Projects\Assistant\294100\2519492373\1.6\Core"
DEFAULT_OBSIDIA_BIOTECH = r"C:\Projects\Assistant\294100\2519492373\1.6\Biotech"
DEFAULT_OBSIDIA_ANOMALY = r"C:\Projects\Assistant\294100\2519492373\1.6\Anomaly"
DEFAULT_OBSIDIA_IDEOLOGY = r"C:\Projects\Assistant\294100\2519492373\1.6\Ideology"
DEFAULT_OBSIDIA_ROYALTY = r"C:\Projects\Assistant\294100\2519492373\1.6\Royalty"
DEFAULT_OBSIDIA_VEF = r"C:\Projects\Assistant\294100\2519492373\1.6\Mods\VEF"
DEFAULT_OBSIDIA_MU = r"C:\Projects\Assistant\294100\2519492373\1.6\Mods\MechanoidUpgrades"

ROYALTY_PACKAGE = "Ludeon.RimWorld.Royalty"
BIOTECH_PACKAGE = "Ludeon.RimWorld.Biotech"
ANOMALY_PACKAGE = "Ludeon.RimWorld.Anomaly"
IDEOLOGY_PACKAGE = "Ludeon.RimWorld.Ideology"
VEF_PACKAGE = "OskarPotocki.VanillaFactionsExpanded.Core"
MU_PACKAGE = "GoGaTio.MechanoidUpgrades"

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
# Shared CE-style calibers: rifle ammo also fits sniper / LMG / HMG, pistol ammo
# also fits SMGs. Damage class still splits (fire rifle ≠ emp rifle).
CALIBER_BY_TYPE = {
    "pistol": "pistol",
    "smg": "pistol",
    "shotgun": "shotgun",
    "rifle": "rifle",
    "sniper": "rifle",
    "lmg": "rifle",
    "minigun": "rifle",
    "bow": "bow",
    "launcher": "launcher",
    "rocket": "rocket",
}
DAMAGE_CLASSES = (
    "ballistic", "energy", "fire", "emp", "acid", "cryo", "bio",
)
ELEMENTAL_CLASSES = frozenset(
    {"energy", "fire", "emp", "acid", "cryo", "bio"}
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
