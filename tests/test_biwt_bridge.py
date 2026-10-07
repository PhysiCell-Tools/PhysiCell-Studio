#!/usr/bin/env python3
"""What Studio does with a cell type BIWT returned but assigned no template to.

Such a type is absent from BIWT's mapping, so Studio has to decide its definition. The rule:
copy this model's definition when the model has one by that name, Studio's default phenotype
otherwise -- and the same rule whether the destination is a merge or a new file. The new-file
case is the one that went wrong: a type the open model already defined got no request at all,
so a new config built from the requests did not define it, and the .csv it pointed at named a
cell type nothing defined ("Invalid cell type name" in the ICs tab).
"""

import sys
import types
from pathlib import Path

import pandas as pd
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "bin"))

import biwt_bridge as bridge


KNOWN = "Neurod1 Zic2a glutamatergic neurons"       # defined in the open model
KNOWN_TOO = "Neurod1 Zic2a glutamatergic neurons2"  # likewise
NEW = "Merged A"                                    # renamed in BIWT; model has never seen it


def _model_cell_definitions(*names):
    """A <cell_definitions> whose each definition is told apart by a custom_data value."""
    import xml.etree.ElementTree as ET
    container = ET.Element("cell_definitions")
    for index, name in enumerate(names):
        cd = ET.SubElement(container, "cell_definition", name=name, ID=str(index))
        phenotype = ET.SubElement(cd, "phenotype")
        ET.SubElement(phenotype, "marker").text = "from model: %s" % name
    return container


def _result(*placed, unplaced=()):
    """A BIWT result placing one cell of each of *placed*; *unplaced* are kept zero-count types."""
    coordinates = pd.DataFrame({
        "x": range(len(placed)), "y": [0.0] * len(placed), "z": [0.0] * len(placed),
        "type": list(placed)})
    cell_type_map = {name: name for name in placed + tuple(unplaced)}
    return types.SimpleNamespace(coordinates=coordinates, cell_type_map=cell_type_map,
                                 cell_templates={})


# ---------------------------------------------------------------------------
# request_for_csv_type: the rule itself
# ---------------------------------------------------------------------------

def test_csv_type_the_host_defines_is_a_copy_of_the_host_definition():
    request = bridge.request_for_csv_type(KNOWN, [KNOWN, "default"])
    assert request.from_host()
    assert request.template_name == KNOWN
    assert request.chose_template()   # so it is never reported as "no template chosen"


def test_csv_type_the_host_lacks_is_left_for_the_default():
    request = bridge.request_for_csv_type(NEW, [KNOWN, "default"])
    assert not request.from_host()
    assert not request.chose_template()


def test_host_match_uses_the_stripped_name_but_keeps_the_host_spelling():
    # classify_names() is the one matching rule: stripped, exact, case-sensitive.
    request = bridge.request_for_csv_type("Zorg", ["  Zorg "])
    assert request.from_host()
    assert request.template_name == "  Zorg "   # looked up by the host's own spelling
    assert not bridge.request_for_csv_type("zorg", ["Zorg"]).from_host()


def test_resolve_copies_the_host_definition_under_the_csv_name():
    container = _model_cell_definitions(KNOWN, "default")
    requests = {KNOWN: bridge.request_for_csv_type(KNOWN, [KNOWN, "default"])}
    bridge.resolve_cell_defs(requests, container)
    request = requests[KNOWN]
    assert request.origin == bridge.ORIGIN_HOST
    assert request.element.attrib["name"] == KNOWN
    assert request.element.find("phenotype/marker").text == "from model: %s" % KNOWN


# ---------------------------------------------------------------------------
# The completion flow's request pass, driven without a dialog
# ---------------------------------------------------------------------------

def _flow(model_types):
    """A BiwtCompletionFlow over a stub Studio holding *model_types*."""
    ui = pytest.importorskip("biwt_bridge_ui")   # needs PyQt5
    celldef_tab = types.SimpleNamespace(param_d={name: {} for name in model_types})
    xml_creator = types.SimpleNamespace(celldef_tab=celldef_tab)
    ics_tab = types.SimpleNamespace(xml_creator=xml_creator)
    return ui.BiwtCompletionFlow(ics_tab)


def test_every_returned_type_gets_a_request_whatever_the_model_holds():
    flow = _flow([KNOWN, KNOWN_TOO, "default"])
    requests = bridge.extract_cell_defs(_result(KNOWN, NEW, KNOWN_TOO))
    assert requests == {}   # the templates step was skipped

    flow._add_requests_for_unassigned_types(_result(KNOWN, NEW, KNOWN_TOO), requests)

    assert sorted(requests) == sorted([KNOWN, NEW, KNOWN_TOO])
    assert requests[KNOWN].from_host() and requests[KNOWN_TOO].from_host()
    assert not requests[NEW].from_host()


def test_a_kept_type_with_no_cells_is_still_defined():
    # BIWT allows a count of zero at its counts step: the type reaches the host in
    # cell_type_map and places nothing. Only the deleted ones (mapped to None) are gone.
    flow = _flow([])
    result = _result(KNOWN, unplaced=(NEW,))
    result.cell_type_map["Dropped in BIWT"] = None
    requests = bridge.extract_cell_defs(result)

    flow._add_requests_for_unassigned_types(result, requests)

    assert sorted(requests) == sorted([KNOWN, NEW])


def test_a_type_biwt_chose_a_template_for_is_left_alone():
    flow = _flow([KNOWN])
    result = _result(KNOWN)
    result.cell_templates = {KNOWN: ("/lib.toml", "neuron", "<phenotype/>")}
    requests = bridge.extract_cell_defs(result)

    flow._add_requests_for_unassigned_types(result, requests)

    assert list(requests) == [KNOWN]
    assert requests[KNOWN].source == "/lib.toml"


def test_new_file_defines_every_type_the_csv_places():
    """The reported failure, end to end through the pure functions the new-file path calls."""
    flow = _flow([KNOWN, KNOWN_TOO, "default"])
    result = _result(KNOWN, NEW, KNOWN_TOO)
    requests = bridge.extract_cell_defs(result)
    flow._add_requests_for_unassigned_types(result, requests)

    container = _model_cell_definitions(KNOWN, KNOWN_TOO, "default")
    bridge.resolve_cell_defs(requests, container)
    bridge.repair_cell_defs(requests)
    elements = {name: request.element for name, request in requests.items()}
    tree = bridge.build_new_document(bridge.assign_names_and_ids(elements),
                                     csv_folder="./config", csv_file="cells.csv")

    defined = bridge.model_cell_type_names(tree.getroot())
    assert sorted(defined) == sorted([KNOWN, NEW, KNOWN_TOO])
    # The known ones are the model's definitions, not generic ones; "default" did not come.
    root = tree.getroot()
    for name in (KNOWN, KNOWN_TOO):
        cd = root.find(".//cell_definition[@name='%s']" % name)
        assert cd.find("phenotype/marker").text == "from model: %s" % name
    assert root.find(".//cell_definition[@name='%s']/phenotype/marker" % NEW) is None
