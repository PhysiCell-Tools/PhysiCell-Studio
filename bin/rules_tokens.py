"""
rules_tokens.py - the grammar of PhysiCell rule signals and behaviors.

A rule is "<cell type>, <signal>, <direction>, <behavior>, ...". Signals and behaviors are
strings, and many of them carry a substrate or a cell type *inside* the string --
"contact with tumor", "transform to macrophage", "oxygen secretion". This module is the one
place that grammar is written down: rules_tab.create_signal_list()/create_response_list()
build the vocabularies from the recipes below, and extract_cell_type() reads a name back out
of a token.

"Behavior" throughout, not "response": the direction -- "increases", "decreases" -- is the
response, and the behavior is what it acts on. rules_tab's create_response_list() and
response_combobox name the same vocabulary the other way.

This module states it once:

    build_signal_list() / build_behavior_list()   produce the two vocabularies
    extract_cell_type(token)                      recovers a cell type from one token

Recipe order is combobox order: reordering a recipe, or a run within one, reorders the
signal and behavior dropdowns users see.

Beware RESERVED. Several fixed tokens look like parameterized ones -- "contact with dead
cell" against "contact with {}", "attack duration" against "attack {}" -- so
extract_cell_type() rules them out first, or it reports cell types named "dead cell" and
"duration".

Authors:
Dr. Daniel Bergman
Rf. Credits.md
"""

NUM_CYCLE_PHASES = 6  # rules_tab.create_reserved_words() hardwires the same 6

# Recipe item kinds. Each produces a contiguous run of tokens; the order of the runs, and
# the order within them, is the order the comboboxes show.
_SUBS = "subs"        # one token per substrate, from a template
_CTS = "cts"          # one token per cell type, from a template
_LITS = "lits"        # fixed tokens
_PHASES = "phases"    # one token per cycle phase index
_CUSTOM = "custom"    # one token per custom-data variable

SIGNAL_RECIPE = (
    (_SUBS, "{}"),
    (_SUBS, "intracellular {}"),
    (_SUBS, "{} gradient"),
    (_LITS, ("pressure", "volume")),
    (_CTS, "contact with {}"),
    (_LITS, (
        "contact with live cell", "contact with dead cell",
        "contact with apoptotic cell", "contact with necrotic cell",
        "contact with BM", "damage", "dead", "attacking",
        "total attack time", "damage delivered", "time", "apoptotic", "necrotic",
    )),
    (_CUSTOM, "custom:{}"),
)

BEHAVIOR_RECIPE = (
    (_SUBS, "{} secretion"),
    (_SUBS, "{} secretion target"),
    (_SUBS, "{} uptake"),
    (_SUBS, "{} export"),
    (_LITS, (
        "cycle entry", "attack damage rate", "attack duration",
        "damage rate", "damage repair rate",
    )),
    (_PHASES, "exit from cycle phase {}"),
    (_LITS, (
        "apoptosis", "necrosis",
        "migration speed", "migration bias", "migration persistence time",
    )),
    (_SUBS, "chemotactic response to {}"),
    (_LITS, ("cell-cell adhesion", "cell-cell adhesion elastic constant")),
    (_CTS, "adhesive affinity to {}"),
    (_LITS, (
        "relative maximum adhesion distance", "cell-cell repulsion",
        "cell-BM adhesion", "cell-BM repulsion",
        "phagocytose apoptotic cell", "phagocytose necrotic cell",
        "phagocytose other dead cell",
    )),
    (_CTS, "phagocytose {}"),
    (_CTS, "attack {}"),
    (_CTS, "fuse to {}"),
    (_CTS, "transform to {}"),
    (_CTS, "immunogenicity to {}"),
    (_CTS, "asymmetric division to {}"),
    (_LITS, (
        "is_movable", "cell attachment rate", "cell detachment rate",
        "maximum number of cell attachments",
    )),
    (_CUSTOM, "custom:{}"),
)


def _literals(recipe):
    out = []
    for kind, payload in recipe:
        if kind == _LITS:
            out.extend(payload)
        elif kind == _PHASES:
            out.extend(payload.format(i) for i in range(NUM_CYCLE_PHASES))
    return out


def _templates(item_kind):
    """The placeholder-carrying templates of one kind, taken from the recipes.

    Derived rather than listed again: extract_cell_type() has to work on exactly the strings
    build_signal_list()/build_behavior_list() produce, and a second hand-written copy is
    free to drift out of step with them.
    """
    found = []
    for recipe in (SIGNAL_RECIPE, BEHAVIOR_RECIPE):
        for kind, payload in recipe:
            if kind == item_kind and payload not in found:
                found.append(payload)
    return tuple(found)


CELL_TYPE_TEMPLATES = _templates(_CTS)
SUBSTRATE_TEMPLATES = _templates(_SUBS)

# Every fixed token in either vocabulary. extract_cell_type() rejects these before parsing,
# which is what stops "attack damage rate" from yielding a cell type named "damage rate".
#
# Shared across both rather than split by vocabulary, because the two do not overlap: no
# signal literal is parseable by a behavior template or the reverse, so the union suppresses
# nothing the halves would not. tests/test_rules_tokens.py holds that true.
RESERVED = frozenset(_literals(SIGNAL_RECIPE) + _literals(BEHAVIOR_RECIPE))


def _build(recipe, substrates, cell_types, custom_vars):
    tokens = []
    for kind, payload in recipe:
        if kind == _SUBS:
            tokens.extend(payload.format(s) for s in substrates)
        elif kind == _CTS:
            tokens.extend(payload.format(ct) for ct in cell_types)
        elif kind == _LITS:
            tokens.extend(payload)
        elif kind == _PHASES:
            tokens.extend(payload.format(i) for i in range(NUM_CYCLE_PHASES))
        elif kind == _CUSTOM:
            tokens.extend(payload.format(v) for v in custom_vars)
    return tokens


def build_signal_list(substrates, cell_types, custom_vars=()):
    return _build(SIGNAL_RECIPE, substrates, cell_types, custom_vars)


def build_behavior_list(substrates, cell_types, custom_vars=()):
    return _build(BEHAVIOR_RECIPE, substrates, cell_types, custom_vars)


def extract_cell_type(token):
    """The cell type named inside *token*, or None if it names none.

    Roster-free on purpose. scan_rules_for_missing_types() needs the names a rules file
    mentions precisely so it can report the ones that are *not* in the model, and filtering
    against the roster would drop exactly those. That works because every cell type template
    carries a prefix -- "attack {}", "transform to {}" -- so a token anchors itself. The
    substrate grammar cannot be read this way: a bare substrate name is a signal on its own,
    so one of its templates is "{}", which matches anything.
    """
    if not token:
        return None
    token = token.strip()
    if token in RESERVED:
        return None

    # Longest prefix first, so a short template cannot swallow a token a longer one matches.
    for template in sorted(CELL_TYPE_TEMPLATES, key=len, reverse=True):
        prefix, _, suffix = template.partition("{}")
        if not token.startswith(prefix) or not token.endswith(suffix):
            continue
        name = token[len(prefix): len(token) - len(suffix) if suffix else None]
        if name:
            return name
    return None
