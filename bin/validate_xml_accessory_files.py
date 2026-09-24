"""
validate_xml_accessory_files.py - check that the accessory files a PhysiCell config (.xml)
refers to actually exist.

Currently checks:
    <initial_conditions><cell_positions enabled="true"> : <folder>/<filename>

    all:
    <ruleset protocol="CBHG" version="3.0" format="csv" enabled="true">

A relative <folder> (e.g. "./config") is resolved against base_dir, which defaults to the
current working directory -- where PhysiCell resolves it when the model is run.

Usage:
    problems = validate_xml_accessory_files("config/PhysiCell_settings.xml")
    if problems:
        ...

or from the command line:
    python validate_xml_accessory_files.py config/PhysiCell_settings.xml
"""

import os
import sys
import xml.etree.ElementTree as ET


def validate_xml_accessory_files(config_file, base_dir=None):
    """Return a list of problem strings (empty if none) for the accessory files that
    config_file refers to."""
    if base_dir is None:
        base_dir = os.getcwd()

    try:
        root = ET.parse(config_file).getroot()
    except (OSError, ET.ParseError) as e:
        return [f"Unable to read config file '{config_file}': {e}"]

    problems = []
    problems += _check_cell_positions(root, base_dir)
    problems += _check_rulesets(root, base_dir)
    return problems


def _check_enabled_file(label, elem, base_dir):
    """Problems (a list of 0 or 1 strings) with the <folder>/<filename> of an element that
    is skipped unless enabled="true"."""
    if elem.attrib.get("enabled", "").strip().lower() != "true":
        return []

    folder = (elem.findtext("folder") or "").strip()
    filename = (elem.findtext("filename") or "").strip()
    if not filename:
        return [f"{label} is enabled, but its <filename> is missing or empty."]

    path = os.path.join(folder, filename)
    if not os.path.isabs(path):
        path = os.path.join(base_dir, path)
    if not os.path.isfile(path):
        return [f"{label} is enabled, but its file does not exist: {os.path.normpath(path)}"]
    return []


def _check_cell_positions(root, base_dir):
    uep = root.find(".//initial_conditions//cell_positions")
    if uep is None:
        return []
    return _check_enabled_file("cell_positions", uep, base_dir)


def _check_rulesets(root, base_dir):
    problems = []
    for ruleset in root.findall(".//cell_rules//rulesets//ruleset"):
        problems += _check_enabled_file("ruleset", ruleset, base_dir)
    return problems


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {os.path.basename(__file__)} <config.xml>")
        sys.exit(2)
    found = validate_xml_accessory_files(sys.argv[1])
    for msg in found:
        print(msg)
    sys.exit(1 if found else 0)
