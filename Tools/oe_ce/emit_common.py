from __future__ import annotations


def format_num(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    if value == int(value):
        return str(int(value))
    return format(value, "g")


def thing_xpath(def_name: str, tag: str = "ThingDef") -> str:
    return f'Defs/{tag}[defName="{def_name}"]'


def named_xpath(name: str, tag: str = "ThingDef") -> str:
    return f'Defs/{tag}[@Name="{name}"]'


def ensure_node(def_name: str, node: str, tag: str = "ThingDef") -> str:
    base = thing_xpath(def_name, tag)
    path = f"{base}/{node}"
    return f"""  <Operation Class="PatchOperationConditional">
    <xpath>{path}</xpath>
    <match Class="PatchOperationTest">
      <xpath>{path}</xpath>
    </match>
    <nomatch Class="PatchOperationAdd">
      <xpath>{base}</xpath>
      <value>
        <{node} />
      </value>
    </nomatch>
  </Operation>"""


def set_stat(def_name: str, node: str, stat: str, value: float, tag: str = "ThingDef") -> str:
    return set_xpath_value(f"{thing_xpath(def_name, tag)}/{node}", stat, value)


def set_xpath_value(parent_xpath: str, stat: str, value: float | str) -> str:
    text = value if isinstance(value, str) else format_num(value)
    return f"""  <Operation Class="PatchOperationConditional">
    <xpath>{parent_xpath}/{stat}</xpath>
    <match Class="PatchOperationReplace">
      <xpath>{parent_xpath}/{stat}</xpath>
      <value>
        <{stat}>{text}</{stat}>
      </value>
    </match>
    <nomatch Class="PatchOperationAdd">
      <xpath>{parent_xpath}</xpath>
      <value>
        <{stat}>{text}</{stat}>
      </value>
    </nomatch>
  </Operation>"""


def as_sequence_item(op: str) -> str:
    text = op.strip()
    if not text.startswith("<Operation ") or not text.endswith("</Operation>"):
        raise ValueError(f"expected a top-level Patch Operation, got: {text[:80]!r}")
    text = "<li " + text[len("<Operation ") :]
    text = text[: -len("</Operation>")] + "</li>"
    return "\n".join(f"    {line}" if line else line for line in text.split("\n"))


def wrap_may_require(ops: list[str], packages: str) -> str:
    inner = "\n".join(as_sequence_item(op) for op in ops)
    return f"""  <Operation Class="PatchOperationSequence" MayRequire="{packages}">
    <operations>
{inner}
    </operations>
  </Operation>"""


def wrap_optional_xpath(ops: list[str], packages: str, xpath: str) -> str:
    inner = "\n".join(as_sequence_item(op) for op in ops)
    may = f' MayRequire="{packages}"' if packages else ""
    return f"""  <Operation Class="PatchOperationConditional"{may}>
    <xpath>{xpath}</xpath>
    <match Class="PatchOperationSequence">
      <operations>
{inner}
      </operations>
    </match>
    <nomatch Class="PatchOperationTest">
      <xpath>Defs</xpath>
    </nomatch>
  </Operation>"""


def wrap_optional_def(
    ops: list[str], packages: str, def_name: str, tag: str = "ThingDef"
) -> str:
    return wrap_optional_xpath(ops, packages, thing_xpath(def_name, tag))
