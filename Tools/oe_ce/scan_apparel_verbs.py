"""Deploy verbs on DLC combat apparel (turret packs, disruptor flares, gas darts).

Core / Royalty grenadier kits keep vanilla verbs (playtested). DLC deploy verbs
whose projectile has a CE equivalent are converted; the rest must be listed in
KEEP_VANILLA_PROJECTILES so a new Obsidia gadget cannot slip through unpatched.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

from oe_ce.scan_apparel import _apparel_files, _dlc_trees, _kind, _layers
from oe_ce.scan_obsidia import ThingDefIndex, index_thingdefs, walk_parents

TURRET = "turret"
FLARE = "flare"
GAS = "gas"

# Projectile_SpawnsPawnZeroAge has no CE projectile class; vanilla verb kept.
KEEP_VANILLA_PROJECTILES = frozenset(
    {
        "Grenade_Armor_CAC_SwarmlingPack",
        "Grenade_Armor_OMG_SwarmlingPack",
    }
)
# Vanilla projectiles CE 1.7-Test already turns into ProjectileCE. A vanilla verb
# firing them breaks under CE, so the verb is converted; the projectile is not
# patched again here.
CE_PATCHED_VANILLA_PROJECTILES = {"Grenade_DisruptorFlare": FLARE}
_LAUNCH_VERBS = frozenset({"Verb_LaunchProjectileStatic", "Verb_LaunchProjectileStaticPsychic"})


@dataclass(frozen=True)
class DeployProjectile:
    def_name: str
    kind: str
    package: str
    fields: tuple[tuple[str, str], ...]

    def field(self, name: str) -> str | None:
        return dict(self.fields).get(name)


@dataclass(frozen=True)
class DeployApparel:
    def_name: str
    package: str
    verbs: tuple[ET.Element, ...]


@dataclass
class ApparelVerbScan:
    apparel: dict[str, DeployApparel]
    projectiles: dict[str, DeployProjectile]
    errors: list[str]


def _inherited(index: ThingDefIndex, el: ET.Element, path: str) -> ET.Element | None:
    for node in walk_parents(index, el):
        found = node.find(path)
        if found is not None:
            return found
    return None


def _inherited_text(index: ThingDefIndex, el: ET.Element, path: str) -> str | None:
    found = _inherited(index, el, path)
    if found is None or not (found.text or "").strip():
        return None
    return found.text.strip()


def _classify(index: ThingDefIndex, proj: ET.Element) -> str | None:
    thing_class = _inherited_text(index, proj, "thingClass")
    spawns = _inherited_text(index, proj, "projectile/spawnsThingDef") or ""
    if thing_class == "Projectile_SpawnsThing" and "TacticalTurret" in spawns:
        return TURRET
    if thing_class == "Projectile_SpawnsThing" and spawns == "DisruptorFlare":
        return FLARE
    if thing_class == "Projectile_Explosive" and _inherited_text(
        index, proj, "projectile/postExplosionSpawnThingDef"
    ):
        return GAS
    return None


def _fields(index: ThingDefIndex, proj: ET.Element) -> tuple[tuple[str, str], ...]:
    out: list[tuple[str, str]] = []
    for name in (
        "spawnsThingDef",
        "tryAdjacentFreeSpaces",
        "spinRate",
        "landedEffecter",
        "damageDef",
        "explosionRadius",
        "soundExplode",
        "postExplosionSpawnThingDef",
    ):
        value = _inherited_text(index, proj, f"projectile/{name}")
        if value is not None:
            out.append((name, value))
    return tuple(out)


def scan_apparel_verbs(
    core: Path,
    royalty: Path | None = None,
    *,
    biotech: Path | None = None,
    anomaly: Path | None = None,
    odyssey: Path | None = None,
) -> ApparelVerbScan:
    files = _apparel_files(core, required=True)
    if royalty is not None:
        files = files + _apparel_files(royalty, required=False)
    package_of: dict[str, str] = {}
    for root, pkg in _dlc_trees(None, biotech, anomaly, odyssey):
        dlc_files = _apparel_files(root, required=False)
        for def_name in index_thingdefs(dlc_files).by_def:
            package_of[def_name] = pkg
        files = files + dlc_files
    index = index_thingdefs(files)

    scan = ApparelVerbScan({}, {}, [])
    for def_name, el in sorted(index.by_def.items()):
        pkg = package_of.get(def_name)
        if pkg is None or el.get("Abstract") == "True":
            continue
        if _kind(_layers(index, el)) is None:
            continue
        verbs = _inherited(index, el, "verbs")
        if verbs is None:
            continue
        converted: list[ET.Element] = []
        for li in verbs.findall("li"):
            projectile = (li.findtext("defaultProjectile") or "").strip()
            if not projectile or projectile in KEEP_VANILLA_PROJECTILES:
                continue
            verb_class = (li.findtext("verbClass") or "").strip()
            proj_el = index.by_def.get(projectile)
            if proj_el is None:
                kind = CE_PATCHED_VANILLA_PROJECTILES.get(projectile)
            else:
                kind = _classify(index, proj_el)
            if verb_class not in _LAUNCH_VERBS or kind is None:
                scan.errors.append(
                    f"{def_name}: deploy verb {verb_class} -> {projectile} has no CE "
                    "conversion; add one or list it in KEEP_VANILLA_PROJECTILES"
                )
                continue
            converted.append(li)
            if proj_el is None:
                continue
            scan.projectiles.setdefault(
                projectile,
                DeployProjectile(
                    projectile, kind, package_of.get(projectile, pkg), _fields(index, proj_el)
                ),
            )
        if converted and len(converted) != len(verbs.findall("li")):
            scan.errors.append(
                f"{def_name}: mixes CE-convertible and vanilla verbs; verbs are replaced whole"
            )
            continue
        if converted:
            scan.apparel[def_name] = DeployApparel(def_name, pkg, tuple(converted))
    return scan
