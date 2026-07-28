#!/usr/bin/env python3

import sys
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "bin"))

PYQT_AVAILABLE = importlib.util.find_spec("PyQt5") is not None
pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt5 is required to import cell_def_tab")

if PYQT_AVAILABLE:
    from cell_def_tab import CellDef, CellDefException


def make_cell_def_with_intracellular(intracellular):
    cell_def = CellDef.__new__(CellDef)
    cell_def.debug_print_fill_xml = False
    cell_def.indent10 = "\n          "
    cell_def.indent12 = "\n            "
    cell_def.indent14 = "\n              "
    cell_def.indent16 = "\n                "
    cell_def.indent18 = "\n                  "
    cell_def.param_d = {"default": {"intracellular": intracellular}}
    return cell_def


def test_dfba_intracellular_serializes_from_param_dict():
    cell_def = make_cell_def_with_intracellular({
        "type": "dfba",
        "settings": {
            "sbml_filename": "./config/metabolism.xml",
            "intracellular_dt": "0.01",
        },
        "transport_model": {
            "exchanges": [{
                "substrate": "glucose",
                "fba_flux": "EX_glc__D_e",
                "Km": "1.0",
                "Vmax": "10.0",
            }],
        },
        "growth_model": {
            "cell_density": "1.0",
            "reference_volume": "2494",
            "max_growth_rate": "0.00072",
            "objective_reaction": "biomass_reaction",
        },
        "death_model": {
            "enabled": True,
            "death_type": "apoptosis",
            "death_trigger_flux": "EX_o2_e",
            "death_flux_threshold": "-0.01",
            "death_rate_increase": "0.001",
        },
    })
    pheno = ET.Element("phenotype")

    cell_def.fill_xml_intracellular(pheno, "default")

    intracellular = pheno.find("intracellular")
    assert intracellular is not None
    assert intracellular.attrib["type"] == "dfba"
    assert intracellular.find("./settings/sbml_filename").text == "./config/metabolism.xml"
    assert intracellular.find("./settings/intracellular_dt").text == "0.01"
    assert intracellular.find("./transport_model/exchange").attrib["substrate"] == "glucose"
    assert intracellular.find("./transport_model/exchange/fba_flux").text == "EX_glc__D_e"
    assert intracellular.find("./growth_model/objective_reaction").text == "biomass_reaction"
    assert intracellular.find("./death_model").attrib["enabled"] == "true"


def test_dfba_intracellular_requires_sbml_filename():
    cell_def = make_cell_def_with_intracellular({
        "type": "dfba",
        "settings": {"intracellular_dt": "0.01"},
    })
    pheno = ET.Element("phenotype")

    with pytest.raises(CellDefException):
        cell_def.fill_xml_intracellular(pheno, "default")
