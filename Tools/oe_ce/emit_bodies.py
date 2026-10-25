from __future__ import annotations

from oe_ce.body_models import BodyEntry
from oe_ce.emit_common import as_sequence_item, set_xpath_value, thing_xpath, wrap_optional_def
from oe_ce.scan_bodies import BodyPart, ScannedBody

ANIMAL = "animal"
MECHANOID = "mechanoid"

NATURAL_ARMOR = "CoveredByNaturalArmor"

SCYTHER_DEFS = frozenset({
    "MechanicalNeck", "MechanicalHead", "OEMechanicalHead",
    "SightSensor", "HearingSensor", "SmellSensor",
    "MechanicalShoulder", "MechanicalArm", "MechanicalHand", "MechanicalFinger",
    "MechanicalLeg", "MechanicalFoot",
    "Reactor", "FluidReprocessor",
})

LANCER_COVERAGE = {
    "MechanicalShoulder": 0.15,
    "MechanicalLeg": 0.18,
    "FluidReprocessor": 0.05,
}

HUMAN_COVERAGE = {
    "Ribcage": 0.07, "Pelvis": 0.05, "Stomach": 0.05, "Heart": 0.04,
    "Lung": 0.055, "Kidney": 0.03, "Liver": 0.06, "Neck": 0.055,
    "Brain": 0.9, "Eye": 0.05, "Ear": 0.05, "Nose": 0.08,
    "Shoulder": 0.085, "Clavicle": 0.06, "Humerus": 0.15, "Radius": 0.15,
    "Femur": 0.15, "Tibia": 0.15,
}

HUMAN_ARM_LABELS = {
    "left arm": "LeftArm",
    "right arm": "RightArm",
    "left shoulder": "LeftShoulder",
    "right shoulder": "RightShoulder",
}

QUAD_DEFS = frozenset({"Neck", "Head", "AnimalJaw", "Leg", "Paw"})


def _kind_of(def_name: str) -> str:
    if def_name.startswith("OEMechanical") or def_name == "OEDominator":
        return MECHANOID
    return ANIMAL


def _iter_parts(root: BodyPart):
    yield root
    for child in root.children:
        yield from _iter_parts(child)


def _outside(part: BodyPart) -> bool:
    return (part.depth or "Outside") != "Inside"


def _ensure_groups(body: str, xpath: str) -> str:
    path = f'{thing_xpath(body, "BodyDef")}/{xpath}/groups'
    base = f'{thing_xpath(body, "BodyDef")}/{xpath}'
    return f'''  <Operation Class="PatchOperationConditional">
    <xpath>{path}</xpath>
    <match Class="PatchOperationTest">
      <xpath>{path}</xpath>
    </match>
    <nomatch Class="PatchOperationAdd">
      <xpath>{base}</xpath>
      <value>
        <groups />
      </value>
    </nomatch>
  </Operation>'''


def _add_group(body: str, xpath: str, group: str) -> str:
    path = f'{thing_xpath(body, "BodyDef")}/{xpath}/groups'
    return f'''  <Operation Class="PatchOperationAdd">
    <xpath>{path}</xpath>
    <value>
      <li>{group}</li>
    </value>
  </Operation>'''


def _add_group_when_marker(body: str, xpath: str, marker: str, group: str) -> str:
    marker_path = f'{thing_xpath(body, "BodyDef")}/{xpath}/groups/li[.="{marker}"]'
    add_op = _add_group(body, xpath, group)
    inner = as_sequence_item(add_op)
    return f'''  <Operation Class="PatchOperationConditional">
    <xpath>{marker_path}</xpath>
    <match Class="PatchOperationSequence">
      <operations>
{inner}
      </operations>
    </match>
    <nomatch Class="PatchOperationTest">
      <xpath>{marker_path}</xpath>
    </nomatch>
  </Operation>'''


def _set_coverage(body: str, xpath: str, value: float) -> str:
    return set_xpath_value(f'{thing_xpath(body, "BodyDef")}/{xpath}', "coverage", value)


def _natural_armor_ops(body: str, part: BodyPart) -> list[str]:
    ops = [_ensure_groups(body, part.xpath)]
    if NATURAL_ARMOR not in part.groups:
        ops.append(_add_group(body, part.xpath, NATURAL_ARMOR))
    return ops


def _beetle_ops(body: str, root: BodyPart) -> list[str]:
    ops: list[str] = []
    for part in _iter_parts(root):
        if part.xpath == "corePart" or _outside(part):
            ops.extend(_natural_armor_ops(body, part))
    return ops


def _scyther_ops(body: str, root: BodyPart) -> list[str]:
    ops: list[str] = []
    for part in _iter_parts(root):
        if part.xpath == "corePart" or (part.def_name and part.def_name in SCYTHER_DEFS):
            ops.extend(_natural_armor_ops(body, part))
    return ops


def _lancer_ops(body: str, root: BodyPart) -> list[str]:
    ops = _scyther_ops(body, root)
    for part in _iter_parts(root):
        if part.def_name and part.def_name in LANCER_COVERAGE:
            ops.append(_set_coverage(body, part.xpath, LANCER_COVERAGE[part.def_name]))
    return ops


def _human_ops(body: str, root: BodyPart) -> list[str]:
    ops: list[str] = []
    for part in _iter_parts(root):
        if _outside(part):
            ops.extend(_natural_armor_ops(body, part))
        if part.def_name and part.def_name in HUMAN_COVERAGE:
            ops.append(_set_coverage(body, part.xpath, HUMAN_COVERAGE[part.def_name]))
        label_key = (part.custom_label or "").lower()
        if label_key in HUMAN_ARM_LABELS:
            group = HUMAN_ARM_LABELS[label_key]
            if group not in part.groups:
                ops.append(_add_group(body, part.xpath, group))
        if "OE_ReturnedLeftLimb" in part.groups and "LeftArm" not in part.groups:
            ops.append(_add_group_when_marker(body, part.xpath, "OE_ReturnedLeftLimb", "LeftArm"))
        if "OE_ReturnedRightLimb" in part.groups and "RightArm" not in part.groups:
            ops.append(_add_group_when_marker(body, part.xpath, "OE_ReturnedRightLimb", "RightArm"))
    return ops


def _quadruped_ops(body: str, root: BodyPart) -> list[str]:
    ops: list[str] = []
    for part in _iter_parts(root):
        if part.xpath == "corePart" or (part.def_name and part.def_name in QUAD_DEFS):
            ops.extend(_natural_armor_ops(body, part))
    return ops


def _ops_for_analogue(analogue: str, body_name: str, root: BodyPart) -> list[str]:
    if analogue in ("beetle", "fingerspike"):
        return _beetle_ops(body_name, root)
    if analogue == "scyther":
        return _scyther_ops(body_name, root)
    if analogue == "lancer":
        return _lancer_ops(body_name, root)
    if analogue == "human":
        return _human_ops(body_name, root)
    if analogue == "quadruped":
        return _quadruped_ops(body_name, root)
    return []


def emit_body_xml(
    entries: list[BodyEntry],
    scanned: dict[str, ScannedBody],
    kind: str,
) -> str:
    rows = [
        e for e in entries
        if e.def_name in scanned and _kind_of(e.def_name) == kind
    ]
    rows.sort(key=lambda e: e.def_name)
    blocks: list[str] = []
    for entry in rows:
        body = scanned[entry.def_name]
        if not body.parts:
            continue
        root = body.parts[0]
        ops = _ops_for_analogue(entry.analogue, entry.def_name, root)
        if entry.may_require:
            blocks.append(
                wrap_optional_def(ops, entry.may_require, entry.def_name, tag="BodyDef")
            )
        else:
            blocks.extend(ops)
    inner = "\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n{inner}\n</Patch>\n'
