from oe_ce.scan_shields import CoreShield, HANDHELD, INNATE, UPGRADE, WORN
from oe_ce.shield_models import (
    HandheldSet,
    InnateSet,
    ShieldCatalog,
    ShieldMember,
    UpgradeSet,
    WornSet,
)
from oe_ce.validate_shields import validate_shield_catalog

ARMOR = {"OCC_Armor_M"}


def _cat(**kwargs) -> ShieldCatalog:
    return ShieldCatalog(**kwargs)


def test_coverage_both_directions():
    cat = _cat(
        worn=[
            WornSet(
                "occ",
                "occ_reforge",
                "guardian",
                "inherit",
                [ShieldMember("OCC_Armor_M_Shield")],
            )
        ]
    )
    scanned = {
        "OCC_Armor_M_Shield": CoreShield(
            "OCC_Armor_M_Shield", WORN, True, "OCC_Armor_M"
        ),
        "ODC_Shield_Small": CoreShield("ODC_Shield_Small", HANDHELD),
    }
    errors = validate_shield_catalog(cat, scanned, ARMOR)
    assert any("ODC_Shield_Small" in e and "not in catalog" in e for e in errors)


def test_catalogued_missing_from_scan():
    cat = _cat(
        worn=[
            WornSet(
                "occ",
                "occ_reforge",
                "guardian",
                "inherit",
                [ShieldMember("OCC_Armor_M_Shield")],
            )
        ]
    )
    errors = validate_shield_catalog(cat, {}, ARMOR)
    assert any("OCC_Armor_M_Shield" in e and "not in scan" in e for e in errors)


def test_role_mismatch_and_unknown_rung():
    cat = _cat(
        worn=[
            WornSet(
                "occ",
                "occ_reforge",
                "guardian",
                "inherit",
                [ShieldMember("OCC_Armor_M_Barrier")],
            ),
            WornSet(
                "bad",
                "not_a_rung",
                "protector",
                "skip",
                [ShieldMember("OMG_Armor_Corsair")],
            ),
        ]
    )
    scanned = {
        "OCC_Armor_M_Barrier": CoreShield(
            "OCC_Armor_M_Barrier", WORN, False, "OCC_Armor_M"
        ),
        "OMG_Armor_Corsair": CoreShield("OMG_Armor_Corsair", WORN, False),
    }
    errors = validate_shield_catalog(cat, scanned, ARMOR)
    assert any("role" in e for e in errors)
    assert any("unknown rung" in e for e in errors)


def test_plate_inherit_requires_armor_parent_emit_rejects_it():
    inherit_ok = _cat(
        worn=[
            WornSet(
                "occ",
                "occ_reforge",
                "guardian",
                "inherit",
                [ShieldMember("OCC_Armor_M_Shield")],
            )
        ]
    )
    scanned = {
        "OCC_Armor_M_Shield": CoreShield(
            "OCC_Armor_M_Shield", WORN, True, "OCC_Armor_M"
        )
    }
    assert validate_shield_catalog(inherit_ok, scanned, ARMOR) == []

    inherit_bad = _cat(
        worn=[
            WornSet(
                "oes",
                "heroic",
                "guardian",
                "inherit",
                [ShieldMember("OES_Armor_Shield")],
            )
        ]
    )
    scanned_oes = {
        "OES_Armor_Shield": CoreShield("OES_Armor_Shield", WORN, True, None)
    }
    errors = validate_shield_catalog(inherit_bad, scanned_oes, ARMOR)
    assert any("inherit" in e for e in errors)

    emit_bad = _cat(
        worn=[
            WornSet(
                "occ",
                "occ_reforge",
                "guardian",
                "emit",
                [ShieldMember("OCC_Armor_M_Shield")],
            )
        ]
    )
    errors = validate_shield_catalog(emit_bad, scanned, ARMOR)
    assert any("emit" in e for e in errors)


def test_duplicate_and_upgrade_factor():
    cat = _cat(
        worn=[
            WornSet("a", "occ", "guardian", "skip", [ShieldMember("X")]),
            WornSet("b", "occ", "guardian", "skip", [ShieldMember("X")]),
        ],
        upgrades=[UpgradeSet("u", "nope", [ShieldMember("U")])],
        handheld=[HandheldSet("h", "occ", "tiny", [ShieldMember("H")])],
        innate=[InnateSet("i", "nope", [ShieldMember("I")])],
    )
    scanned = {
        "X": CoreShield("X", WORN, True),
        "U": CoreShield("U", UPGRADE),
        "H": CoreShield("H", HANDHELD),
        "I": CoreShield("I", INNATE),
    }
    errors = validate_shield_catalog(cat, scanned, ARMOR)
    assert any("duplicate" in e for e in errors)
    assert any("factor" in e for e in errors)
    assert any("size" in e for e in errors)
    assert any("analogue" in e for e in errors)


def _anomaly_commando() -> ShieldCatalog:
    return _cat(
        worn=[
            WornSet(
                "omg_protector_anomaly",
                "omg",
                "protector",
                "skip",
                [ShieldMember("OMG_Armor_Commando")],
                may_require="Ludeon.RimWorld.Anomaly",
            )
        ]
    )


def test_optional_worn_skipped_only_when_package_absent():
    assert validate_shield_catalog(_anomaly_commando(), {}, ARMOR) == []
    errors = validate_shield_catalog(
        _anomaly_commando(),
        {},
        ARMOR,
        present_packages=frozenset({"Ludeon.RimWorld.Anomaly"}),
    )
    assert any("OMG_Armor_Commando" in e and "not in scan" in e for e in errors)
    scanned = {"OMG_Armor_Commando": CoreShield("OMG_Armor_Commando", WORN, False)}
    assert (
        validate_shield_catalog(
            _anomaly_commando(),
            scanned,
            ARMOR,
            present_packages=frozenset({"Ludeon.RimWorld.Anomaly"}),
        )
        == []
    )
