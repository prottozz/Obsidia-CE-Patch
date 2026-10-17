from __future__ import annotations


def format_num(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    if value == int(value):
        return str(int(value))
    return format(value, "g")


def thing_xpath(def_name: str) -> str:
    return f'Defs/ThingDef[defName="{def_name}"]'


def ensure_node(def_name: str, node: str) -> str:
    base = thing_xpath(def_name)
    return f"""  <Operation Class="PatchOperationConditional">
    <xpath>{base}/{node}</xpath>
    <nomatch Class="PatchOperationAdd">
      <xpath>{base}</xpath>
      <value>
        <{node} />
      </value>
    </nomatch>
  </Operation>"""


def set_stat(def_name: str, node: str, stat: str, value: float) -> str:
    base = thing_xpath(def_name)
    text = format_num(value)
    return f"""  <Operation Class="PatchOperationConditional">
    <xpath>{base}/{node}/{stat}</xpath>
    <match Class="PatchOperationReplace">
      <xpath>{base}/{node}/{stat}</xpath>
      <value>
        <{stat}>{text}</{stat}>
      </value>
    </match>
    <nomatch Class="PatchOperationAdd">
      <xpath>{base}/{node}</xpath>
      <value>
        <{stat}>{text}</{stat}>
      </value>
    </nomatch>
  </Operation>"""
