from oe_ce.body_models import BodyEntry
from oe_ce.emit_bodies import ANIMAL, MECHANOID, emit_body_xml
from oe_ce.scan_bodies import BodyPart, ScannedBody

BIOTECH = "Ludeon.RimWorld.Biotech"
ANOMALY = "Ludeon.RimWorld.Anomaly"


def _part(def_name, xpath, *, depth=None, groups=(), children=None, custom_label=None):
    return BodyPart(def_name, custom_label, depth, tuple(groups), xpath, children or [])


def _body(name, core, custom=True):
    return ScannedBody(name, [core], custom)


def test_beetle_natural_armor_skips_inside_organs():
    stomach = _part("Stomach", 'corePart/parts/li[def="Stomach"]', depth="Inside")
    eye = _part("Eye", 'corePart/parts/li[def="Eye"]')
    core = _part("Body", "corePart", children=[stomach, eye])
    xml = emit_body_xml(
        [BodyEntry("OEArachnaLike", "beetle")],
        {"OEArachnaLike": _body("OEArachnaLike", core)},
        ANIMAL,
    )
    assert "CoveredByNaturalArmor" in xml
    assert 'defName="OEArachnaLike"' in xml
    assert "MayRequire" not in xml
    assert 'corePart/parts/li[def="Eye"]' in xml
    assert 'corePart/parts/li[def="Stomach"]/groups' not in xml
    assert 'corePart/parts/li[def="Eye"]/groups' in xml
    assert "corePart/groups" in xml


def test_dominator_lancer_leg_coverage_unwrapped():
    leg = _part("MechanicalLeg", 'corePart/parts/li[def="MechanicalLeg"]')
    core = _part("MechanicalThorax", "corePart", children=[leg])
    xml = emit_body_xml(
        [BodyEntry("OEDominator", "lancer")],
        {"OEDominator": _body("OEDominator", core)},
        MECHANOID,
    )
    assert "<coverage>0.18</coverage>" in xml
    assert 'corePart/parts/li[def="MechanicalLeg"]' in xml
    assert "MayRequire" not in xml
    assert 'defName="OEDominator"' in xml


def test_octo_scyther_wrapped_biotech():
    core = _part("OEOctoHood", "corePart")
    xml = emit_body_xml(
        [BodyEntry("OEMechanicalOcto", "scyther", may_require=BIOTECH)],
        {"OEMechanicalOcto": _body("OEMechanicalOcto", core)},
        MECHANOID,
    )
    assert 'MayRequire="Ludeon.RimWorld.Biotech"' in xml
    assert "<li Class=" in xml
    assert "<operations>" in xml
    assert "<Operation Class=" not in xml.split("<operations>")[1].split("</operations>")[0]
    assert "CoveredByNaturalArmor" in xml
    assert "corePart/groups" in xml
    assert 'defName="OEMechanicalOcto"' in xml


def test_octo_absent_from_scan_is_omitted():
    xml = emit_body_xml(
        [BodyEntry("OEMechanicalOcto", "scyther", may_require=BIOTECH)],
        {},
        MECHANOID,
    )
    assert "OEMechanicalOcto" not in xml


def test_returned_keeps_custom_limb_group_and_adds_leftarm():
    limb = _part(
        "OEReturnedArm",
        'corePart/parts/li[def="OEReturnedArm"]',
        groups=("OE_ReturnedLeftLimb",),
    )
    core = _part("Torso", "corePart", groups=("Torso",), children=[limb])
    xml = emit_body_xml(
        [BodyEntry("OEReturnedLike", "human", may_require=ANOMALY)],
        {"OEReturnedLike": _body("OEReturnedLike", core)},
        ANIMAL,
    )
    assert 'MayRequire="Ludeon.RimWorld.Anomaly"' in xml
    assert "OE_ReturnedLeftLimb" in xml
    assert "LeftArm" in xml
    assert 'corePart/parts/li[def="OEReturnedArm"]/groups' in xml
