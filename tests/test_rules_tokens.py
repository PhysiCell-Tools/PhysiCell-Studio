#!/usr/bin/env python3
"""The invariants rules_tokens.extract_cell_type() quietly depends on.

It parses a token by matching it against the cell type templates, after rejecting RESERVED --
the fixed tokens that look parameterized ("attack duration" against "attack {}"). RESERVED is
the union of both vocabularies' literals, which is only safe while no literal of one is
matchable by the other's templates. Nothing enforces that; these tests do.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "bin"))

import rules_tokens as rt


CELL_TYPES = ["macrophage", "CD8+ T cell", "blood vessel", "tumor"]
SUBSTRATES = ["oxygen", "resource", "pro-inflammatory"]


def _cell_type_templates(recipe):
    return tuple(payload for kind, payload in recipe if kind == rt._CTS)


def _match(token, templates):
    """What extract_cell_type() would pull out, ignoring RESERVED.

    Duplicates its matching loop (rules_tokens.py, the sorted-by-length scan) so the tests
    can ask what the templates match with RESERVED out of the way. Keep the two in step:
    if they diverge, these tests pass while asserting nothing about the real function.
    """
    for template in sorted(templates, key=len, reverse=True):
        prefix, _, suffix = template.partition("{}")
        if token.startswith(prefix) and token.endswith(suffix):
            name = token[len(prefix): len(token) - len(suffix) if suffix else None]
            if name:
                return name
    return None


def test_reserved_does_not_reach_across_vocabularies():
    """No literal of one vocabulary is parseable by the other's cell type templates.

    RESERVED merges both, so a collision here would mean a signal literal silently
    suppressing a behaviour that names a cell type, or the reverse -- and the failure would
    be a missing warning, not an error. Split RESERVED by vocabulary if this ever trips.
    """
    signal_literals = rt._literals(rt.SIGNAL_RECIPE)
    behavior_literals = rt._literals(rt.BEHAVIOR_RECIPE)

    for literals, others, label in (
        (signal_literals, _cell_type_templates(rt.BEHAVIOR_RECIPE), "signal"),
        (behavior_literals, _cell_type_templates(rt.SIGNAL_RECIPE), "behavior"),
    ):
        for literal in literals:
            assert _match(literal, others) is None, (
                "%s literal %r parses as a cell type under the other vocabulary's templates; "
                "RESERVED can no longer be shared between the two" % (label, literal))


def test_reserved_covers_every_literal_its_own_templates_would_mis_parse():
    """The positive half: RESERVED has to hold the literals that do look parameterized."""
    for recipe in (rt.SIGNAL_RECIPE, rt.BEHAVIOR_RECIPE):
        own = _cell_type_templates(recipe)
        for literal in rt._literals(recipe):
            if _match(literal, own) is not None:
                assert literal in rt.RESERVED, (
                    "%r parses as a cell type but is not RESERVED" % literal)
                assert rt.extract_cell_type(literal) is None


def test_every_generated_cell_type_token_reads_back():
    """Round trip: whatever the vocabularies build, extract_cell_type() recovers."""
    signals = rt.build_signal_list(SUBSTRATES, CELL_TYPES)
    behaviors = rt.build_behavior_list(SUBSTRATES, CELL_TYPES)

    for recipe, tokens in ((rt.SIGNAL_RECIPE, signals), (rt.BEHAVIOR_RECIPE, behaviors)):
        expected = {template.format(name): name
                    for template in _cell_type_templates(recipe)
                    for name in CELL_TYPES}
        for token in tokens:
            assert rt.extract_cell_type(token) == expected.get(token), token
        assert expected, "recipe carries no cell type templates"


def test_substrate_tokens_are_not_read_as_cell_types():
    """A substrate name is a signal on its own, so its template is "{}" -- it matches anything.

    extract_cell_type() only consults the cell type templates, all of which carry a prefix.
    """
    for substrate in SUBSTRATES:
        for template in rt.SUBSTRATE_TEMPLATES:
            token = template.format(substrate)
            if _match(token, _cell_type_templates(rt.SIGNAL_RECIPE)
                             + _cell_type_templates(rt.BEHAVIOR_RECIPE)) is None:
                assert rt.extract_cell_type(token) is None, token


def test_new_modules_import_without_the_biwt_package():
    """Studio ships without `biwt` installed; the bridge modules must still import.

    They name two things from it -- HOST_SOURCE and DomainSource -- behind try/except, and
    the fallbacks have to carry the same values, or a Studio with the package and one
    without would disagree about which template is "the host's".
    """
    import importlib

    class Block:
        def find_spec(self, name, path=None, target=None):
            if name == "biwt" or name.startswith("biwt."):
                raise ImportError("blocked by test")
            return None

    blocker = Block()
    saved = {k: v for k, v in sys.modules.items()
             if k.split(".")[0] in ("biwt", "biwt_bridge", "biwt_bridge_ui")}
    for name in saved:
        del sys.modules[name]
    sys.meta_path.insert(0, blocker)
    try:
        bridge = importlib.import_module("biwt_bridge")
        assert bridge.HOST_SOURCE == "<host>"
        try:
            ui = importlib.import_module("biwt_bridge_ui")
        except ImportError:
            return          # no PyQt5 in this environment; the pure half is what matters
        assert ui._biwt_version() == ""
        for value, label in (("host", "from Studio"), ("data", "from data"),
                             ("user", "user-edited"), ("default", "BIWT default")):
            assert ui._domain_source_label(value) == label, value
    finally:
        sys.meta_path.remove(blocker)
        for name in [k for k in sys.modules
                     if k.split(".")[0] in ("biwt", "biwt_bridge", "biwt_bridge_ui")]:
            del sys.modules[name]
        sys.modules.update(saved)
