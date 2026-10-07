#!/usr/bin/env python3
"""Which cell definitions Studio builds from a BIWT result, and from what.

extract_cell_defs() builds one request per cell type BIWT returned. A type BIWT assigned a
template to is built from that. A type left at "(none)" is absent from BIWT's mapping, so
Studio decides: copy this model's definition when the model has one by that name, Studio's
default phenotype otherwise -- the same rule whether the destination is a merge or a new file.

The new-file case is the one that went wrong: a type the open model already defined got no
request at all, so a new config built from the requests did not define it, and the .csv it
pointed at named a cell type nothing defined ("Invalid cell type name" in the ICs tab).
"""

import sys
import types
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1] / "bin"))

import biwt_bridge as bridge


KNOWN = "Neurod1 Zic2a glutamatergic neurons"       # defined in the open model
KNOWN_TOO = "Neurod1 Zic2a glutamatergic neurons2"  # likewise
NEW = "Merged A"                                    # renamed in BIWT; model has never seen it
MODEL = [KNOWN, KNOWN_TOO, "default"]


def _model_cell_definitions(*names):
    """A <cell_definitions> whose each definition is told apart by a custom_data value."""
    container = ET.Element("cell_definitions")
    for index, name in enumerate(names):
        cd = ET.SubElement(container, "cell_definition", name=name, ID=str(index))
        phenotype = ET.SubElement(cd, "phenotype")
        ET.SubElement(phenotype, "marker").text = "from model: %s" % name
    return container


def _result(*placed, unplaced=(), templates=None):
    """A BIWT result placing one cell of each of *placed*; *unplaced* are kept zero-count types."""
    coordinates = pd.DataFrame({
        "x": range(len(placed)), "y": [0.0] * len(placed), "z": [0.0] * len(placed),
        "type": list(placed)})
    cell_type_map = {name: name for name in placed + tuple(unplaced)}
    return types.SimpleNamespace(coordinates=coordinates, cell_type_map=cell_type_map,
                                 cell_templates=templates or {})


# ---------------------------------------------------------------------------
# Which types get a request
# ---------------------------------------------------------------------------

def test_every_returned_type_gets_a_request():
    requests = bridge.extract_cell_defs(_result(KNOWN, NEW, KNOWN_TOO), MODEL)
    assert list(requests) == [KNOWN, NEW, KNOWN_TOO]   # BIWT's order, kept


def test_a_kept_type_with_no_cells_is_still_defined():
    # BIWT allows a count of zero at its counts step: the type reaches the host in
    # cell_type_map and places nothing. Only a deleted type (mapped to None) is gone.
    result = _result(KNOWN, unplaced=(NEW,))
    result.cell_type_map["Dropped in BIWT"] = None
    assert list(bridge.extract_cell_defs(result, [])) == [KNOWN, NEW]


def test_merged_originals_yield_one_request():
    result = _result(NEW)
    result.cell_type_map = {"cluster 3": NEW, "cluster 7": NEW, "cluster 9": None}
    assert list(bridge.extract_cell_defs(result, [])) == [NEW]


# ---------------------------------------------------------------------------
# What each request is built from
# ---------------------------------------------------------------------------

def test_a_type_biwt_chose_a_template_for_uses_it():
    result = _result(KNOWN, templates={KNOWN: ("/lib.toml", "neuron", "<phenotype/>")})
    request = bridge.extract_cell_defs(result, MODEL)[KNOWN]
    assert request.source == "/lib.toml"
    assert request.element is not None      # parsed, not copied from the model


def test_a_type_the_model_defines_is_copied_from_the_model():
    request = bridge.extract_cell_defs(_result(KNOWN), MODEL)[KNOWN]
    assert request.from_host()
    assert request.template_name == KNOWN
    assert request.chose_template()         # so it is never reported as "no template chosen"


def test_a_type_the_model_lacks_is_left_for_the_default():
    request = bridge.extract_cell_defs(_result(NEW), MODEL)[NEW]
    assert not request.from_host()
    assert not request.chose_template()


def test_studio_match_is_stripped_and_exact_but_keeps_studio_spelling():
    request = bridge.extract_cell_defs(_result("Zorg"), ["  Zorg "])["Zorg"]
    assert request.from_host()
    assert request.template_name == "  Zorg "   # looked up by Studio's own spelling
    assert not bridge.extract_cell_defs(_result("zorg"), ["Zorg"])["zorg"].from_host()


def test_resolve_copies_the_model_definition_under_biwts_name():
    requests = bridge.extract_cell_defs(_result(KNOWN), MODEL)
    bridge.resolve_cell_defs(requests, _model_cell_definitions(*MODEL))
    request = requests[KNOWN]
    assert request.origin == bridge.ORIGIN_HOST
    assert request.element.attrib["name"] == KNOWN
    assert request.element.find("phenotype/marker").text == "from model: %s" % KNOWN


# ---------------------------------------------------------------------------
# The reported failure, end to end through the new-file builders
# ---------------------------------------------------------------------------

def test_new_file_defines_every_type_biwt_returns():
    requests = bridge.extract_cell_defs(_result(KNOWN, NEW, KNOWN_TOO), MODEL)
    bridge.resolve_cell_defs(requests, _model_cell_definitions(*MODEL))
    bridge.repair_cell_defs(requests)
    elements = {name: request.element for name, request in requests.items()}
    tree = bridge.build_new_document(bridge.assign_names_and_ids(elements),
                                     csv_folder="./config", csv_file="cells.csv")

    root = tree.getroot()
    assert bridge.model_cell_type_names(root) == [KNOWN, NEW, KNOWN_TOO]
    # The known ones are the model's definitions, not generic ones; "default" did not come.
    for name in (KNOWN, KNOWN_TOO):
        cd = root.find(".//cell_definition[@name='%s']" % name)
        assert cd.find("phenotype/marker").text == "from model: %s" % name
    assert root.find(".//cell_definition[@name='%s']/phenotype/marker" % NEW) is None
