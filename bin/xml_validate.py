"""
xml_validate.py - generic, spec-driven checking and repair of an ElementTree subtree.

Nothing here knows about PhysiCell. A caller supplies a *spec* -- a sequence of entries
describing the child paths an element is expected to have -- and gets back a list of
Problems, or has the gaps filled in from a template element.

get_text()/set_text() are the safe form of Studio's usual
`self.xml_root.find(".//x_min").text` (config_tab.py:696), which raises AttributeError on a
config that is merely incomplete. validate() reports which part of an element is wrong;
populate_tree_cell_defs.validate_cell_defs() reports only that it is.

Spec entry (a dict, so entries can grow fields without breaking callers):

    path       "phenotype/cycle" -- slash-separated, relative to the element passed in.
               May use ElementPath predicates ("death/model[@name='apoptosis']"), in which
               case the entry is reported but not filled: create its parent instead.
    required   True if its absence is an error rather than something to fill in.
    attribs    optional; attribute names that must be present on the element.
    any_of     optional; child tags, at least one of which must be present.

Authors:
Dr. Daniel Bergman
Rf. Credits.md
"""

import copy
import xml.etree.ElementTree as ET


MISSING = "missing"
EMPTY = "empty"
BAD_ATTRIB = "bad_attrib"


class Problem:
    """One thing wrong with an element, located by path."""

    __slots__ = ("path", "kind", "detail", "required")

    def __init__(self, path, kind, detail="", required=True):
        self.path = path
        self.kind = kind
        self.detail = detail
        self.required = required

    def __repr__(self):
        return "Problem(%r, %r, %r, required=%r)" % (self.path, self.kind, self.detail, self.required)

    def __str__(self):
        if self.detail:
            return "%s: %s (%s)" % (self.path, self.kind, self.detail)
        return "%s: %s" % (self.path, self.kind)


def _has_predicate(path):
    return "[" in path


def validate(elm, spec):
    """Check *elm* against *spec*. Returns a list of Problems, empty if it is clean."""
    problems = []
    if elm is None:
        return [Problem("", MISSING, "no element to validate")]

    for entry in spec:
        path = entry["path"]
        required = entry.get("required", True)
        found = elm.find(path)

        if found is None:
            problems.append(Problem(path, MISSING, required=required))
            continue

        for name in entry.get("attribs", ()):
            if name not in found.attrib:
                problems.append(
                    Problem(path, BAD_ATTRIB, "missing @%s" % name, required=required)
                )

        alternatives = entry.get("any_of", ())
        if alternatives and not any(found.find(alt) is not None for alt in alternatives):
            problems.append(
                Problem(
                    path,
                    EMPTY,
                    "needs one of: %s" % ", ".join(alternatives),
                    required=required,
                )
            )

    return problems


def _spec_order(spec, parent_path):
    """Tags the spec expects directly under *parent_path*, in spec order."""
    order = []
    for entry in spec:
        path = entry["path"]
        head, _, tail = path.rpartition("/")
        if head == parent_path and not _has_predicate(tail):
            order.append(tail)
    return order


def fill_missing(elm, spec, defaults_elm):
    """Copy any spec path absent from *elm* out of *defaults_elm*.

    Returns the list of paths filled in. Each is inserted at the position the spec implies
    among its siblings, so a repaired element keeps the section order the spec declares
    rather than collecting additions at the end.

    Entries whose path carries a predicate are skipped -- there is no general way to
    synthesize `model[@name='apoptosis']` -- so fill their parent instead and re-validate.
    """
    filled = []
    if elm is None or defaults_elm is None:
        return filled

    for entry in spec:
        path = entry["path"]
        if _has_predicate(path) or elm.find(path) is not None:
            continue

        source = defaults_elm.find(path)
        if source is None:
            continue

        parent_path, _, tag = path.rpartition("/")
        parent = find_or_create(elm, parent_path) if parent_path else elm
        if parent is None:
            continue

        # Land after every sibling the spec puts ahead of this one. The children already
        # present need not be in spec order, so take the highest such position, not the
        # last one looked at.
        order = _spec_order(spec, parent_path)
        index = 0
        if tag in order:
            children = list(parent)
            for earlier in order[: order.index(tag)]:
                existing = parent.find(earlier)
                if existing is not None:
                    index = max(index, children.index(existing) + 1)

        parent.insert(index, copy.deepcopy(source))
        filled.append(path)

    return filled


def find_or_create(elm, path):
    """find(), creating any missing elements along the way. Predicates are not supported.

    *path* is a chain of direct-child tags: "save/SVG/plot_substrate". Studio writes most
    of its paths as descendant searches -- ".//SVG//plot_substrate" -- and those are NOT
    interchangeable here: each "//" leaves an empty segment, which is skipped, so the tags
    around it are looked up and created as direct children. Handing this function
    ".//SVG//plot_substrate" on a root that keeps <SVG> under <save> appends a second,
    top-level <SVG><plot_substrate/> and returns that. find() the parent first, then
    create beneath it.
    """
    if elm is None:
        return None
    if not path:
        return elm
    if _has_predicate(path):
        return elm.find(path)

    current = elm
    for tag in path.split("/"):
        if not tag or tag == ".":
            continue
        found = current.find(tag)
        if found is None:
            found = ET.SubElement(current, tag)
        current = found
    return current


def get_text(elm, path, default=None):
    """Text at *path*, or *default* if the element is absent or has no text."""
    if elm is None:
        return default
    found = elm.find(path)
    if found is None or found.text is None:
        return default
    return found.text


def set_text(elm, path, value):
    """Set the text at *path*, creating the element (and its parents) if needed."""
    found = find_or_create(elm, path)
    if found is not None:
        found.text = str(value)
    return found
