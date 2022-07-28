import os
import sys
from lxml import etree

class Validator:

    def __init__(self, xsd_path):
        parsed_xsd = etree.parse(xsd_path)  # Parse content of xsd file to ElementTree object
        self.xsdschema = etree.XMLSchema(parsed_xsd)

    def validate_xml(self, xml_path):
        parsed_xml = etree.parse(xml_path)
        # result = self.xsdschema.validate(parsed_xml)
        # return result
        self.xsdschema.assert_(parsed_xml)

# Get current path of script
SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
# xsd_path = os.path.abspath(os.path.join(SCRIPT_PATH, 'note.xsd'))
# xml_path = os.path.abspath(os.path.join(SCRIPT_PATH, 'note_example.xml'))
xsd_path = os.path.abspath(os.path.join(SCRIPT_PATH, 'PhysiCell_model.xsd'))
xml_path = os.path.abspath(os.path.join(SCRIPT_PATH, 'interactions.xml'))

validator = Validator(xsd_path)
validator.validate_xml(xml_path)

