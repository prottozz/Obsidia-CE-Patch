from __future__ import annotations

from oe_ce.models import Family

_SYNTHERIUS_CLASSES = frozenset({"energy", "fire", "acid", "cryo", "emp", "bio"})
_MOONCLOTH_CLASSES = frozenset({"fire", "bio"})


def _ingredient_lines(thing: str, count: int) -> str:
    return (
        f"      <li><filter><thingDefs><li>{thing}</li></thingDefs></filter>"
        f"<count>{count}</count></li>"
    )


def _ingredients(fam: Family, *, large: bool) -> list[tuple[str, int]]:
    mult = 4 if large else 1
    items: list[tuple[str, int]] = [
        ("OE_Obsidian", 8 * mult),
        ("OE_Mythril", 4 * mult),
        ("OE_AmmoKit", 2 * mult),
    ]
    if fam.class_name in _SYNTHERIUS_CLASSES:
        items.append(("OE_Syntherius", 8 if large else 2))
    if fam.class_name in _MOONCLOTH_CLASSES:
        items.append(("OE_Mooncloth", 4 if large else 1))
    return items


def _emit_recipe(fam: Family, cartridge: str, *, large: bool) -> str:
    suffix = "large" if large else "small"
    product_count = 500 if large else 200
    ammo = fam.ammo_def(cartridge)
    def_name = f"MakeAmmo_OE_{fam.id}_{fam.class_name}_{cartridge}_{suffix}"
    label = f"make OE {fam.id} {fam.class_name} {cartridge} x{product_count}"
    work_amount = 5000 if large else 2000
    description = (
        f"Craft {product_count} rounds of OE {fam.id} {fam.class_name} "
        f"{cartridge} ammunition."
    )
    job_string = f"Making OE {fam.id} {fam.class_name} {cartridge} ammo."
    mats = _ingredients(fam, large=large)
    ing_block = "\n".join(_ingredient_lines(t, c) for t, c in mats)
    filter_lis = "\n".join(f"        <li>{t}</li>" for t, _ in mats)
    return f"""  <RecipeDef>
    <defName>{def_name}</defName>
    <label>{label}</label>
    <description>{description}</description>
    <jobString>{job_string}</jobString>
    <workAmount>{work_amount}</workAmount>
    <recipeUsers>
      <li>OE_WeaponWorkbench</li>
    </recipeUsers>
    <ingredients>
{ing_block}
    </ingredients>
    <fixedIngredientFilter>
      <thingDefs>
{filter_lis}
      </thingDefs>
    </fixedIngredientFilter>
    <products>
      <{ammo}>{product_count}</{ammo}>
    </products>
  </RecipeDef>"""


def emit_recipe_xml(families: list[Family]) -> str:
    sorted_families = sorted(families, key=lambda f: (f.class_name, f.id))
    blocks: list[str] = []
    for fam in sorted_families:
        for cart in fam.resolved_cartridges():
            blocks.append(_emit_recipe(fam, cart, large=False))
            blocks.append(_emit_recipe(fam, cart, large=True))
    inner = "\n\n".join(blocks)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n{inner}\n</Defs>'
