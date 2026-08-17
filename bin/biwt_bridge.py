"""
biwt_bridge.py - turn what BIWT returns into cell definitions this model can hold.

BiwtResult.cell_templates is {cell type: (path, template name, content)}, one entry per cell
type the walkthrough assigned a template to. `content` is a <phenotype> block verbatim from a
.toml library -- except when `path` is biwt.types.HOST_SOURCE, which means the user picked one
of this model's own cell types: no content, and `template name` is the cell type to copy.

A template knows nothing about the model it is joining, so it names substrates and cell types
that may not exist here, and it carries no name or ID of its own. Everything in this module
exists to close that gap before the XML reaches Studio's config.

No PyQt5 -- this is all ElementTree and csv, so the rules below can be tested
without standing up a QApplication. The dialogs live in biwt_bridge_ui.py.

Three things here are load-bearing rather than tidy, all of them because of how
populate_tree_cell_defs.py and cell_def_tab.py read a config back in:

  * IDs must come out 0..N-1. With "auto number IDs when saved" unticked -- its default --
    cell_def_tab.fill_xml() walks `for count in range(len(param_d))` and emits only the cell
    def whose ID is `count`, so a gap or a duplicate silently drops a cell type from the file
    the next time the user saves.
  * <secretion> must name exactly the substrates the model has. fill_xml_secretion() iterates
    the model's substrate list and indexes param_d[cdef]["secretion"][substrate], which
    populate_tree_cell_defs fills *from the XML* -- so a missing entry is a modal error
    dialog per substrate per cell type, not a default.
  * A cell definition missing a phenotype section takes Studio down: validate_cell_defs()
    and handle_parse_error() both end in sys.exit(-1). Hence repair_cell_defs().

Authors:
Dr. Daniel Bergman
Rf. Credits.md
"""

import copy
import csv
import os
import xml.etree.ElementTree as ET

import physicell_xml_defaults as pcdefaults
import rules_tokens
import xml_validate

try:
    from biwt.types import HOST_SOURCE
except Exception:
    # Only for importing this module without BIWT, e.g. to unit-test the XML rules. BIWT
    # documents the value as reserved and deliberately not a usable path.
    HOST_SOURCE = "<host>"


# Values a cell definition gets for something it never mentioned. These match
# cell_def_tab.new_secretion_params() and new_mechanics_params() so that a cell type
# reconciled here is indistinguishable from one the user added by hand.
ZERO_SECRETION = (
    ("secretion_rate", "0.0", "1/min"),
    ("secretion_target", "1.0", "substrate density"),
    ("uptake_rate", "0.0", "1/min"),
    ("net_export_rate", "0.0", "total substrate/min"),
)
DEFAULT_AFFINITY = "1.0"
DEFAULT_RATE = "0.0"
DEFAULT_SENSITIVITY = "0.0"

# The phenotype template library Studio ships, and the one it expects BIWT to have drawn
# from. Compared against the path BIWT reports so that phenotypes sourced from somewhere
# else are visible in the dialog rather than something the user has to infer.
BUNDLED_TEMPLATE_LIBRARY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "cell_templates", "cell_templates.toml")


def is_bundled_library(path):
    if not path:
        return False
    try:
        return os.path.samefile(path, BUNDLED_TEMPLATE_LIBRARY)
    except OSError:
        return os.path.abspath(path) == BUNDLED_TEMPLATE_LIBRARY

# BiwtResult.cell_templates is the field as of BIWT 0.5: {cell type: (path, name, content)}.
# The others are tried only so that a rename on BIWT's side degrades to a named problem in
# the dialog rather than a silent "BIWT sent nothing".
_CELL_DEF_ATTRS = (
    "cell_templates",
    "cell_definitions",
    "cell_defs",
)


# What a cell definition was actually built from, once resolved.
ORIGIN_TEMPLATE = "template"   # a template out of a .toml library
ORIGIN_HOST = "host"           # this model's own definition of another cell type
ORIGIN_DEFAULT = "default"     # Studio's default phenotype


class CellDefRequest:
    """One cell type BIWT asked Studio to build, and what it was built from.

    A request outlives content it cannot use: a template that will not parse is kept, with the
    reason in `error`, so the cell type is still reported as one a template was chosen for.

    Filled out in three passes: extract_cell_defs() records what BIWT said, resolve_cell_defs()
    produces `element` and `origin`, repair_cell_defs() fills any phenotype section still
    missing and records it in `filled`.
    """

    __slots__ = ("name", "source", "template_name", "content",
                 "element", "origin", "error", "filled")

    def __init__(self, name, source=None, template_name=None, content=""):
        self.name = name
        self.source = source                # a .toml path, HOST_SOURCE, or None
        self.template_name = template_name  # key in that file, or the host cell type
        self.content = content or ""
        self.element = None                 # set by resolve_cell_defs()
        self.origin = None                  # one of the ORIGIN_* values, likewise
        self.error = None                   # why `content` was unusable, if it was
        self.filled = []                    # phenotype paths taken from Studio's defaults

    def __repr__(self):
        return "CellDefRequest(%r, origin=%r, error=%r)" % (self.name, self.origin, self.error)

    def chose_template(self):
        """True if a template was named at all -- as opposed to left at "(none)"."""
        return self.template_name is not None

    def from_host(self):
        return self.source == HOST_SOURCE

    def describe_template(self):
        """The template as the user chose it, for the dialog. Empty if none was chosen."""
        if not self.chose_template():
            return ""
        if self.from_host():
            return 'this model\'s "%s"' % self.template_name
        if self.source:
            return '"%s" from %s' % (self.template_name, os.path.basename(self.source))
        return '"%s"' % self.template_name


class ReconcileReport:
    """What reconcile_cell_def() had to invent, for the receipt to name.

    Only what a user can act on. Reconciliation rewrites much more -- the chemotaxis target,
    every cell-type-keyed rate, the custom data -- but those come out either right or as the
    model's own values. A substrate left at zero is a real gap only the user can fill.
    """

    def __init__(self, name):
        self.name = name
        self.substrates_zeroed = []         # no values for these, from BIWT or the model
        self.dropped_cell_type_refs = []    # (container_tag, name), for the caller's summary


# ---------------------------------------------------------------------------
# Reading BIWT's result
# ---------------------------------------------------------------------------

def _looks_like_cell_defs(value):
    """True for a {name: content} mapping, false for BIWT's other dicts.

    cell_type_map is the one to keep out: it is {str: str|None} and would otherwise pass.
    """
    if not isinstance(value, dict) or not value:
        return False
    for key, item in value.items():
        if not isinstance(key, str):
            return False
        if isinstance(item, (tuple, list)):
            if len(item) != 3:
                return False
        elif not isinstance(item, (str, ET.Element)):
            return False
    return True


def _find_cell_def_payload(result):
    """The cell templates off *result*, or None."""
    for attr in _CELL_DEF_ATTRS:
        value = getattr(result, attr, None)
        if _looks_like_cell_defs(value):
            return value

    # No known name matched: accept any attribute shaped like the mapping, so a renamed field
    # still yields cell types instead of an empty result.
    for attr, value in sorted(vars(result).items()) if hasattr(result, "__dict__") else ():
        if attr == "cell_type_map":
            continue
        if _looks_like_cell_defs(value):
            return value
    return None


def _parse_content(content):
    """A <cell_definition> from template content, or (None, why it could not be used)."""
    if isinstance(content, ET.Element):
        return copy.deepcopy(content), None

    text = (content or "").strip()
    if not text:
        return None, None          # nothing supplied; not a failure
    try:
        element = ET.fromstring(text)
    except ET.ParseError as e:
        return None, "will not parse as XML (%s)" % e

    if element.tag == "cell_definition":
        return element, None
    if element.tag == "phenotype":
        # A template may hold just the phenotype; wrap it. assign_names_and_ids() and
        # inject_cell_defs() write name and ID, so their absence here costs nothing.
        wrapper = ET.Element("cell_definition")
        wrapper.append(element)
        return wrapper, None

    nested = element.find(".//cell_definition")
    if nested is not None:
        return copy.deepcopy(nested), None

    return None, "is not a cell definition (its root element is <%s>)" % element.tag


def extract_cell_defs(result):
    """Read BIWT's result into {name: CellDefRequest}.

    Records what BIWT said and nothing more -- see resolve_cell_defs() for turning that into
    XML. Nothing raises and nothing is discarded: content that will not parse is kept on the
    request as `error`, so the cell type is still reported as one a template was chosen for.
    """
    requests = {}
    if result is None:
        return requests

    payload = _find_cell_def_payload(result)
    if payload is None:
        return requests

    for key, value in payload.items():
        name = (key or "").strip()
        if not name or name in requests:
            # A blank name, or two that collide once trimmed. Neither can be built, and
            # neither is something the user can act on from here.
            continue

        source = template_name = None
        content = value
        if isinstance(value, (tuple, list)):
            source, template_name, content = value

        request = CellDefRequest(name, source, template_name, content)
        if not request.from_host():
            request.element, request.error = _parse_content(content)
        requests[name] = request

    return requests


def request_for_csv_type(name):
    """A request for a cell type the .csv places that BIWT assigned no template to."""
    return CellDefRequest(name)


def resolve_cell_defs(requests, cell_definitions_elm=None, nanohub_flag=False, data_dir=None):
    """Give every request an `element` and an `origin`.

    Three ways a cell definition gets built, in order of what was asked for:

      * the user picked one of this model's own cell types -- copy that definition. It is a
        copy, not a rename: the new type keeps the name BIWT returned, so the host type stays
        and the copy starts out identical. The copy is taken from the tree as loaded;
        recopy_host_definitions() refreshes it from the tree as it will be written.
      * a library template that parsed -- use it as-is.
      * anything else -- Studio's default phenotype. That covers a template that would not
        parse, a host cell type since renamed or deleted, and a type left at "(none)". `error`
        says which, and stays set so the dialog can distinguish them.
    """
    by_name = {}
    if cell_definitions_elm is not None:
        by_name = {cd.attrib.get("name"): cd
                   for cd in cell_definitions_elm.findall("cell_definition")}

    for request in requests.values():
        if request.origin is not None:
            # biwt_bridge_ui._resolve() runs this twice; on the second pass the element built
            # here would otherwise read as "a template that parsed" and relabel an
            # ORIGIN_DEFAULT request ORIGIN_TEMPLATE.
            continue

        if request.from_host():
            source = by_name.get(request.template_name)
            if source is not None:
                request.element = copy.deepcopy(source)
                request.origin = ORIGIN_HOST
            else:
                request.error = "is no longer in this model"
        elif request.element is not None:
            request.origin = ORIGIN_TEMPLATE

        if request.element is None:
            request.element = ET.Element("cell_definition")
            request.element.append(pcdefaults.default_phenotype(nanohub_flag, data_dir))
            request.origin = ORIGIN_DEFAULT

        request.element.attrib["name"] = request.name

    return requests


def recopy_host_definitions(requests, cell_definitions_elm):
    """Refresh host-sourced copies from *cell_definitions_elm*.

    resolve_cell_defs() runs before the dialog, against the tree as loaded, so the dialog can
    say where each definition will come from. The copy itself has to be taken from the tree as
    it will be *written*: a definition the user edited without saving differs between the two.
    """
    if cell_definitions_elm is None:
        return requests
    by_name = {cd.attrib.get("name"): cd
               for cd in cell_definitions_elm.findall("cell_definition")}
    for request in requests.values():
        if request.origin != ORIGIN_HOST:
            continue
        source = by_name.get(request.template_name)
        if source is not None:
            request.element = copy.deepcopy(source)
            request.element.attrib["name"] = request.name
            request.filled = []          # repair_cell_defs() runs again after this
    return requests


def repair_cell_defs(requests, default_phenotype=None, nanohub_flag=False, data_dir=None):
    """Fill in any phenotype section a cell definition arrived without.

    populate_tree_cell_defs' validate_cell_defs() and handle_parse_error() both end in
    sys.exit(-1) on an incomplete cell definition, so every phenotype section a template omits
    has to be filled before the XML is written. Each request records what was filled, so the
    dialog can name the sections rather than quietly inventing parameters.
    """
    if default_phenotype is None:
        default_phenotype = pcdefaults.default_phenotype(nanohub_flag, data_dir)

    template = ET.Element("cell_definition")
    template.append(default_phenotype)

    for request in requests.values():
        if request.element is None:
            continue
        # Appended, not assigned: biwt_bridge_ui._resolve() runs this a second time after
        # recopy_host_definitions(), by which point the first pass's sections are present, so
        # assigning would report every request as having needed nothing.
        # recopy_host_definitions() clears `filled` for the rows it rebuilds.
        for path in xml_validate.fill_missing(
                request.element, pcdefaults.CELL_DEF_SPEC, template):
            if path not in request.filled:
                request.filled.append(path)
    return requests


def classify_names(incoming_names, existing_names):
    """Split incoming names into (matched, added), on the stripped name alone.

    The one place Studio decides whether two cell type names are the same name. No fuzzy
    matching: "Macrophage" against an existing "macrophage" is a second cell type, not a
    correction.
    """
    existing = {(name or "").strip() for name in existing_names}
    matched, added = set(), []
    for raw in incoming_names:
        name = (raw or "").strip()
        if name in existing:
            matched.add(name)
        else:
            added.append(name)
    return matched, added


# ---------------------------------------------------------------------------
# Substrates
# ---------------------------------------------------------------------------

def collect_referenced_substrates(defs):
    """Every substrate the incoming cell definitions name, in first-seen order.

    Anything here that the model lacks gets added to it rather than dropped: a cell type that
    secretes or chemotaxes toward something is describing a substrate the model needs.

    Named, not used: a cell definition copied out of a PhysiCell model carries a <secretion>
    entry for every substrate that model has, nearly all at zero, so one cell type brings that
    model's whole microenvironment into a new config. Do not trim to the non-zero rates -- a
    rule, or a project's own C++, can tie a cell type to a substrate whose XML rates are all 0,
    and neither is visible from here.
    """
    found = []
    seen = set()

    def note(name):
        name = (name or "").strip()
        if name and name not in seen:
            seen.add(name)
            found.append(name)

    for entry in defs.values():
        element = entry.element
        if element is None:
            continue  # Unresolved: nothing to read. resolve_cell_defs() fills these in.
        for substrate in element.findall("phenotype/secretion/substrate"):
            note(substrate.attrib.get("name"))
        chemotaxis = element.find("phenotype/motility/options/chemotaxis/substrate")
        if chemotaxis is not None:
            note(chemotaxis.text)
        for sensitivity in element.findall(
                "phenotype/motility/options/advanced_chemotaxis/"
                "chemotactic_sensitivities/chemotactic_sensitivity"):
            note(sensitivity.attrib.get("substrate"))

    return found


def new_file_substrates(requests):
    """The microenvironment a brand-new config gets: (every substrate, the ones added).

    Studio's default microenvironment, plus every substrate the incoming cell types name. A
    new config starts from the defaults rather than from the open model, so the second list is
    what a cell type dragged in behind it -- see collect_referenced_substrates().
    """
    default = model_substrates(ET.fromstring(
        "<PhysiCell_settings><microenvironment_setup>%s</microenvironment_setup>"
        "</PhysiCell_settings>"
        % pcdefaults.XML_DEFAULT_SECTIONS["microenvironment_setup"].strip()))
    extra = [name for name in collect_referenced_substrates(requests) if name not in default]
    return default + extra, extra


def model_substrates(xml_root):
    """The model's substrate names, from the same place fill_substrates_comboboxes() reads."""
    if xml_root is None:
        return []
    return [
        var.attrib["name"]
        for var in xml_root.findall(".//microenvironment_setup/variable")
        if "name" in var.attrib
    ]


def model_cell_type_names(xml_root):
    if xml_root is None:
        return []
    return [
        cd.attrib["name"]
        for cd in xml_root.findall(".//cell_definitions/cell_definition")
        if "name" in cd.attrib
    ]


# ---------------------------------------------------------------------------
# Reconciling one cell definition against the model
# ---------------------------------------------------------------------------

def _index_by_attrib(container, tag, attrib):
    if container is None:
        return {}
    return {
        child.attrib[attrib]: child
        for child in container.findall(tag)
        if attrib in child.attrib
    }


def _replace_child(parent, old, new):
    """Swap *old* for *new* in place, keeping its position among its siblings."""
    if old is None:
        parent.append(new)
        return
    index = list(parent).index(old)
    parent.remove(old)
    parent.insert(index, new)


def _secretion_block(name, source):
    block = ET.Element("substrate", {"name": name})
    for tag, fallback, units in ZERO_SECRETION:
        child = ET.SubElement(block, tag, {"units": units})
        existing = source.find(tag) if source is not None else None
        if existing is not None and existing.text is not None:
            child.text = existing.text
            if "units" in existing.attrib:
                child.attrib["units"] = existing.attrib["units"]
        else:
            child.text = fallback
    return block


def _reconcile_secretion(element, substrates, existing_cd, report):
    phenotype = element.find("phenotype")
    old = phenotype.find("secretion")
    incoming = _index_by_attrib(old, "substrate", "name")
    existing = _index_by_attrib(
        existing_cd.find("phenotype/secretion") if existing_cd is not None else None,
        "substrate", "name")

    new = ET.Element("secretion")
    for name in substrates:
        if name in incoming:
            new.append(_secretion_block(name, incoming[name]))
        elif name in existing:
            new.append(_secretion_block(name, existing[name]))
        else:
            report.substrates_zeroed.append(name)
            new.append(_secretion_block(name, None))

    _replace_child(phenotype, old, new)


def _reconcile_chemotaxis(element, substrates, existing_cd):
    motility = element.find("phenotype/motility")
    if motility is None:
        return
    options = motility.find("options")
    if options is None:
        if not substrates:
            return
        options = ET.SubElement(motility, "options")

    chemotaxis = options.find("chemotaxis")
    if chemotaxis is None:
        # Absent is not safe, even though it means the same as disabled. Studio reads a
        # missing <chemotaxis> as an empty substrate name (populate_tree_cell_defs) and
        # writes it back out that way on the next save, and PhysiCell rejects the file:
        # "invalid substrate was not found in the microenvironment". It insists on a real
        # substrate whether or not chemotaxis is switched on, so name one and leave it off.
        if not substrates:
            return
        chemotaxis = ET.SubElement(options, "chemotaxis")
        xml_validate.set_text(chemotaxis, "enabled", "false")
        xml_validate.set_text(chemotaxis, "substrate", substrates[0])
        xml_validate.set_text(chemotaxis, "direction", "1")
        return

    substrate_elm = chemotaxis.find("substrate")
    wanted = (substrate_elm.text or "").strip() if substrate_elm is not None else ""
    if wanted in substrates:
        return  # collect_referenced_substrates() should have made this the common case

    fallback = ""
    if existing_cd is not None:
        previous = existing_cd.find("phenotype/motility/options/chemotaxis")
        if previous is not None:
            previous_substrate = previous.find("substrate")
            candidate = (previous_substrate.text or "").strip() if previous_substrate is not None else ""
            if candidate in substrates:
                fallback = candidate
                for tag in ("enabled", "direction"):
                    source = previous.find(tag)
                    if source is not None:
                        xml_validate.set_text(chemotaxis, tag, source.text)

    if not fallback and substrates:
        fallback = substrates[0]
        xml_validate.set_text(chemotaxis, "enabled", "false")

    if not fallback:
        # No substrates anywhere. Remove the element rather than blank the substrate:
        # populate_tree_cell_defs handles a missing <chemotaxis>, but reads .text.lower()
        # on the substrate it does find, and that raises on an empty one -- which lands in
        # handle_parse_error() and exits Studio.
        options.remove(chemotaxis)
        return

    xml_validate.set_text(chemotaxis, "substrate", fallback)


def _reconcile_sensitivities(element, substrates, existing_cd):
    advanced = element.find("phenotype/motility/options/advanced_chemotaxis")
    if advanced is None:
        return
    old = advanced.find("chemotactic_sensitivities")
    incoming = _index_by_attrib(old, "chemotactic_sensitivity", "substrate")
    existing = _index_by_attrib(
        existing_cd.find("phenotype/motility/options/advanced_chemotaxis/"
                         "chemotactic_sensitivities") if existing_cd is not None else None,
        "chemotactic_sensitivity", "substrate")

    new = ET.Element("chemotactic_sensitivities")
    for name in substrates:
        source = incoming.get(name, existing.get(name))
        child = ET.SubElement(new, "chemotactic_sensitivity", {"substrate": name})
        child.text = source.text if source is not None and source.text else DEFAULT_SENSITIVITY

    _replace_child(advanced, old, new)


def _reconcile_keyed_by_cell_type(element, path, child_tag, roster, existing_cd,
                                  default_value, units, report):
    """Rewrite a container whose children are keyed by cell type name.

    Same shape for adhesion affinities, phagocytosis/attack/fusion/transformation rates:
    keep what BIWT said about a cell type this model has, fall back to what the cell
    definition being replaced said, otherwise the default -- and drop names that are not
    cell types here, since nothing in the GUI would ever show them again.
    """
    container = element.find(path)
    if container is None:
        return

    incoming = _index_by_attrib(container, child_tag, "name")
    existing = _index_by_attrib(
        existing_cd.find(path) if existing_cd is not None else None, child_tag, "name")

    for name in incoming:
        if name not in roster:
            report.dropped_cell_type_refs.append((child_tag, name))

    new = ET.Element(container.tag, dict(container.attrib))
    names = roster
    for name in names:
        source = incoming.get(name, existing.get(name))
        attribs = {"name": name}
        if units:
            attribs["units"] = units
        child = ET.SubElement(new, child_tag, attribs)
        if source is not None:
            child.text = source.text if source.text is not None else default_value
            if units and "units" in source.attrib:
                child.attrib["units"] = source.attrib["units"]
        else:
            child.text = default_value

    parent_path = path.rpartition("/")[0]
    parent = element.find(parent_path) if parent_path else element
    _replace_child(parent, container, new)


def _reconcile_asymmetric_division(element, roster, report):
    """Drop probabilities naming cell types this model does not have.

    Nothing is added: populate_tree_cell_defs seeds every cell type (0, or 1.0 for the cell
    type itself) before reading the XML, so absent entries already have sensible values,
    and inventing probabilities here would change a distribution that is meant to sum to 1.
    """
    container = element.find("phenotype/cycle/standard_asymmetric_division")
    if container is None:
        return
    for child in list(container.findall("asymmetric_division_probability")):
        name = child.attrib.get("name")
        if name not in roster:
            container.remove(child)
            report.dropped_cell_type_refs.append(("asymmetric_division_probability", name))


def _reconcile_custom_data(element, custom_data_src):
    """Give a new cell type the model's custom variables.

    Custom data is shared across cell types in practice -- the Cell Types > Custom Data table
    is one table -- so a cell type arriving without any would show an empty table next to its
    neighbours. On a new config there is no source and it correctly gets none.
    """
    old = element.find("custom_data")
    if custom_data_src is None:
        if old is None:
            element.append(ET.Element("custom_data"))
        return
    new = copy.deepcopy(custom_data_src)
    if old is None:
        element.append(new)
    else:
        _replace_child(element, old, new)


_CELL_TYPE_KEYED = (
    ("phenotype/mechanics/cell_adhesion_affinities", "cell_adhesion_affinity",
     DEFAULT_AFFINITY, None),
    ("phenotype/cell_interactions/live_phagocytosis_rates", "phagocytosis_rate",
     DEFAULT_RATE, "1/min"),
    ("phenotype/cell_interactions/attack_rates", "attack_rate", DEFAULT_RATE, "1/min"),
    ("phenotype/cell_interactions/fusion_rates", "fusion_rate", DEFAULT_RATE, "1/min"),
    ("phenotype/cell_transformations/transformation_rates", "transformation_rate",
     DEFAULT_RATE, "1/min"),
)


def reconcile_cell_type_references(cell_definitions_elm, cell_type_names):
    """Square every cell definition's cross-references against the final roster.

    Adding a cell type is not just its own definition: every *other* definition has a row for
    it in each interaction matrix. Injected XML never passes through param_d, so the cell
    types already in the model would keep matrices that do not mention the new arrivals, and
    any stale name from the original file would survive untouched.

    Each definition's own values are preserved -- they are what is read first. Only names
    outside the roster are dropped, and only missing roster names are added, at the same
    defaults cell_def_tab uses.

    Returns [(cell_type, child_tag, dropped_name)].
    """
    dropped = []
    roster = list(cell_type_names)
    for element in cell_definitions_elm.findall("cell_definition"):
        report = ReconcileReport(element.attrib.get("name", ""))
        for path, tag, default, units in _CELL_TYPE_KEYED:
            _reconcile_keyed_by_cell_type(
                element, path, tag, roster, None, default, units, report)
        _reconcile_asymmetric_division(element, roster, report)
        dropped.extend((report.name, tag, name)
                       for tag, name in report.dropped_cell_type_refs)
    return dropped


def reconcile_cell_def(element, substrates, existing_cd=None, cell_type_names=(),
                       custom_data_src=None):
    """Make one incoming <cell_definition> consistent with the model it is joining.

    substrates and cell_type_names are the model's *final* rosters, after any substrate
    BIWT referenced has been added and any new cell type accounted for.
    """
    report = ReconcileReport(element.attrib.get("name", ""))
    substrates = list(substrates)
    roster = list(cell_type_names)

    if element.find("phenotype") is None:
        return report

    _reconcile_secretion(element, substrates, existing_cd, report)
    _reconcile_chemotaxis(element, substrates, existing_cd)
    _reconcile_sensitivities(element, substrates, existing_cd)

    for path, tag, default, units in _CELL_TYPE_KEYED:
        _reconcile_keyed_by_cell_type(
            element, path, tag, roster, existing_cd, default, units, report)

    _reconcile_asymmetric_division(element, roster, report)
    _reconcile_custom_data(element, custom_data_src)

    return report


# ---------------------------------------------------------------------------
# Assembling and injecting
# ---------------------------------------------------------------------------

def assign_names_and_ids(elements_by_name, start_id=0):
    """Write name and ID onto each cell definition. BIWT's own values are never used.

    BIWT sends none, and a template library could carry one of its own; either way
    cell_def_tab.fill_xml() drops any cell def whose ID is not its position in the sequence,
    so the numbering has to be Studio's.
    """
    for offset, (name, element) in enumerate(elements_by_name.items()):
        element.attrib["name"] = name
        element.attrib["ID"] = str(start_id + offset)
    return elements_by_name


def renumber_cell_definitions(cell_definitions_elm):
    """Force IDs to 0..N-1 in document order, after every insertion is done."""
    for index, cell_def in enumerate(cell_definitions_elm.findall("cell_definition")):
        cell_def.attrib["ID"] = str(index)


def is_2d(zmin, zmax, dz):
    """config_tab.fill_xml()'s rule: 2D when the z extent is no deeper than one voxel.

    One function so the dialog's "this makes the model 3D" warning and the value actually
    written to <use_2D> cannot disagree.
    """
    return (float(zmax) - float(zmin)) <= float(dz)


def patch_domain(domain_elm, domain, deltas=None):
    """Write BIWT's domain onto a <domain> element and recompute use_2D.

    BIWT supplies no voxel sizes, so dx/dy/dz come from *deltas* -- the open model's, one per
    axis, each left alone where None.
    """
    if domain_elm is None or domain is None:
        return
    for tag, value in (
        ("x_min", domain.xmin), ("x_max", domain.xmax),
        ("y_min", domain.ymin), ("y_max", domain.ymax),
        ("z_min", domain.zmin), ("z_max", domain.zmax),
    ):
        xml_validate.set_text(domain_elm, tag, value)

    if deltas:
        for tag, value in zip(("dx", "dy", "dz"), deltas):
            if value is not None:
                xml_validate.set_text(domain_elm, tag, value)

    try:
        dz = float(xml_validate.get_text(domain_elm, "dz", "20"))
    except (TypeError, ValueError):
        dz = 20.0
    xml_validate.set_text(
        domain_elm, "use_2D", "true" if is_2d(domain.zmin, domain.zmax, dz) else "false")


def _substrate_variable(name, index, template):
    variable = copy.deepcopy(template)
    variable.attrib["name"] = name
    variable.attrib["ID"] = str(index)
    return variable


def build_new_document(elements_by_name, domain=None, deltas=None, extra_substrates=(),
                       csv_folder=None, csv_file=None):
    """A whole <PhysiCell_settings> from Studio's defaults plus BIWT's cell definitions.

    Only BIWT's cell types go in -- no "default" -- so anything the user wants beyond what
    the data described, they add in Studio.
    """
    root = ET.Element("PhysiCell_settings", version="devel-version")

    for key in pcdefaults.SECTION_ORDER:
        fragment = pcdefaults.XML_DEFAULT_SECTIONS[key].strip()
        root.append(ET.fromstring("<%s>%s</%s>" % (key, fragment, key)))

        if key == pcdefaults.CELL_DEFINITIONS_AFTER:
            cell_definitions = ET.Element("cell_definitions")
            for element in elements_by_name.values():
                cell_definitions.append(element)
            root.append(cell_definitions)

    patch_domain(root.find("domain"), domain, deltas)

    microenv = root.find("microenvironment_setup")
    if microenv is not None and extra_substrates:
        variables = microenv.findall("variable")
        template = variables[0] if variables else None
        present = {v.attrib.get("name") for v in variables}
        index = len(variables)
        anchor = list(microenv).index(variables[-1]) + 1 if variables else 0
        for name in extra_substrates:
            if name in present or template is None:
                continue
            microenv.insert(anchor, _substrate_variable(name, index, template))
            anchor += 1
            index += 1

    initial = root.find("initial_conditions/cell_positions")
    if initial is not None:
        # The defaults arrive enabled and naming ./config/cells.csv. Left alone, a config the
        # caller did not want pointed at a .csv would load whatever sits at that path.
        pointing = csv_folder is not None or csv_file is not None
        initial.attrib["enabled"] = "true" if pointing else "false"
        if csv_folder is not None:
            xml_validate.set_text(initial, "folder", csv_folder)
        if csv_file is not None:
            xml_validate.set_text(initial, "filename", csv_file)

    return ET.ElementTree(root)


def inject_cell_defs(xml_root, elements_by_name, replaced_names=()):
    """Put the reconciled cell definitions into an existing config's <cell_definitions>.

    A replaced cell type keeps its position; new ones go after the last existing one. Only
    <cell_definition> children are added: populate_tree_cell_defs builds the XPath
    ".//cell_definition[i+1]" from an index that counts *every* child, so anything else in
    there shifts each subsequent lookup by one.
    """
    container = xml_root.find(".//cell_definitions")
    if container is None:
        return None

    replaced_names = set(replaced_names)
    by_name = {
        cd.attrib.get("name"): cd
        for cd in container.findall("cell_definition")
    }

    for name, element in elements_by_name.items():
        # The mapping key is the authoritative name -- a template wrapped from a bare
        # <phenotype> has no name attribute of its own, and populate_tree_cell_defs reads
        # cell_def.attrib['name'] unguarded. Set it here so this does not depend on
        # assign_names_and_ids having been called first.
        element.attrib["name"] = name
        old = by_name.get(name)
        if name in replaced_names and old is not None:
            _replace_child(container, old, element)
        else:
            container.append(element)

    renumber_cell_definitions(container)
    return container


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def rules_csv_path(xml_root, base_dir=None):
    """Where the config says its ruleset lives, or None."""
    if xml_root is None:
        return None
    ruleset = xml_root.find(".//cell_rules//rulesets//ruleset")
    if ruleset is None:
        return None
    folder = xml_validate.get_text(ruleset, "folder", "")
    filename = xml_validate.get_text(ruleset, "filename", "")
    if not filename:
        return None
    return os.path.join(base_dir or os.getcwd(), folder or "", filename)


def _is_rule(row):
    """rules_tab.fill_rules()'s own test for a row being a rule and not a comment.

    A rules CSV carries free-text comment lines alongside rules, and a rule the user toggled
    off is written as a comment too -- so "starts with //" does not separate them. What does
    is the shape: eight fields, the last of them the apply-to-dead flag.
    """
    return len(row) >= 8 and (row[7] or "").strip() in ("0", "1")


def count_rules(csv_path):
    """How many rules the ruleset holds. 0 if there is no file, or none that can be read."""
    if not csv_path or not os.path.isfile(csv_path):
        return 0
    try:
        with open(csv_path, "r") as handle:
            return sum(1 for row in csv.reader(handle) if _is_rule(row))
    except (OSError, csv.Error):
        return 0


def scan_rules_for_missing_types(csv_path, cell_type_names):
    """Rules that name a cell type the model will not have.

    A rule's first column is the cell type it applies to, and its signal and behavior can
    each carry another one inside the string ("contact with tumor", "transform to
    macrophage") -- so all three are checked, using the same token templates the rules tab
    builds those strings from.

    Returns [(row_number, column_label, cell_type)].
    """
    findings = []
    if not csv_path or not os.path.isfile(csv_path):
        return findings

    roster = set(cell_type_names)
    try:
        with open(csv_path, "r") as handle:
            for row_number, row in enumerate(csv.reader(handle), start=1):
                if not _is_rule(row):
                    # A comment line, not a rule. Its first field is prose, and reporting it
                    # as a cell type the model is missing is how a ruleset's own header ends
                    # up in a warning.
                    continue
                subject = (row[0] or "").strip()
                if subject.startswith("//"):
                    # rules_tab's convention for a rule that is toggled off. Still worth
                    # reporting: the user turned it off, they did not delete it.
                    subject = subject[2:].lstrip()
                if subject and subject not in roster:
                    findings.append((row_number, "cell type", subject))

                for index, label in ((1, "signal"), (3, "behavior")):
                    if len(row) <= index:
                        continue
                    named = rules_tokens.extract_cell_type((row[index] or "").strip())
                    if named and named not in roster:
                        findings.append((row_number, label, named))
    except (OSError, csv.Error):
        return findings

    return findings
