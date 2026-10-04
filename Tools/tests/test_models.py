# Tools/tests/test_models.py
from oe_ce.models import Family, Member


def test_rifle_ballistic_gets_emp_cartridge():
    fam = Family(id="cerberus", type="rifle", class_name="ballistic", experimental=False, cartridges=None, members=[])
    assert fam.resolved_cartridges() == ["standard", "ap", "hp", "emp"]


def test_pistol_must_not_include_emp():
    fam = Family(id="impaler", type="pistol", class_name="ballistic", experimental=False, cartridges=None, members=[])
    assert fam.resolved_cartridges() == ["standard", "ap", "hp"]


def test_emp_class_rifle_has_only_emp_cartridge():
    fam = Family(id="quasar", type="rifle", class_name="emp", experimental=False, cartridges=None, members=[])
    assert fam.resolved_cartridges() == ["emp"]


def test_elemental_families_have_single_named_cartridge():
    fire = Family("nova", "sniper", "fire")
    acid = Family("celestial", "pistol", "acid")
    cryo = Family("conspirator", "shotgun", "cryo")
    assert fire.resolved_cartridges() == ["fire"]
    assert acid.resolved_cartridges() == ["acid"]
    assert cryo.resolved_cartridges() == ["cryo"]
    assert "emp" not in fire.resolved_cartridges()
    assert fire.ammo_def("fire") == "Ammo_OE_rifle_fire_fire"
    assert fire.default_cartridge() == "fire"


def test_rifle_sniper_and_minigun_share_caliber_ammo():
    rifle = Family("cerberus", "rifle", "ballistic")
    sniper = Family("nova", "sniper", "ballistic")
    hmg = Family("unchained", "minigun", "ballistic")
    assert rifle.ammo_def("standard") == "Ammo_OE_rifle_ballistic_standard"
    assert sniper.ammo_def("standard") == rifle.ammo_def("standard")
    assert hmg.ammo_def("standard") == rifle.ammo_def("standard")


def test_each_gun_has_its_own_ammoset_and_bullet():
    fam = Family(
        "cerberus",
        "rifle",
        "ballistic",
        members=[Member("OE_Rifle", "proto"), Member("OCC_Rifle", "occ")],
    )
    oe = fam.members[0]
    occ = fam.members[1]
    assert fam.member_ammo_set_def(oe) == "AmmoSet_OE_OE_Rifle"
    assert fam.member_ammo_set_def(occ) == "AmmoSet_OE_OCC_Rifle"
    assert fam.member_bullet_def(oe, "standard") == "Bullet_OE_OE_Rifle_standard"
    assert fam.member_bullet_def(occ, "standard") == "Bullet_OE_OCC_Rifle_standard"


def test_pistol_and_smg_share_ammo_not_rifle():
    pistol = Family("impaler", "pistol", "ballistic")
    smg = Family("fang", "smg", "ballistic")
    rifle = Family("cerberus", "rifle", "ballistic")
    assert pistol.ammo_def("standard") == "Ammo_OE_pistol_ballistic_standard"
    assert smg.ammo_def("standard") == pistol.ammo_def("standard")
    assert pistol.ammo_def("standard") != rifle.ammo_def("standard")


def test_experimental_keeps_unique_ammo():
    fam = Family("cronus", "sniper", "ballistic", experimental=True)
    assert fam.ammo_def("standard") == "Ammo_OE_exp_cronus_ballistic_standard"
    assert fam.display_label() == "cronus"
    hydra = Family("dark_hydra", "minigun", "ballistic", experimental=True)
    assert hydra.display_label() == "dark hydra"
    assert hydra.caliber() == "exp_dark_hydra"
