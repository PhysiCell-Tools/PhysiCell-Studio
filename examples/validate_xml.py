# Validate one of our XML models against a schema
# alternatively, use:
#     xmllint --schema schema.xsd model_good_1.xml
#
import sys
from lxml import etree

if len(sys.argv) < 2:
    print("Missing: <.xml>")
    print(f"e.g.\npython {sys.argv[0]} biorobots.xml")
    sys.exit()

# Load the schema
with open("schema.xsd", "rb") as f:
    schema_doc = etree.parse(f)
schema = etree.XMLSchema(schema_doc)

# Parse and validate the XML
with open("model.xml", "rb") as f:
    xml_doc = etree.parse(f)

if schema.validate(xml_doc):
    print("XML is valid")
else:
    print("XML is invalid:")
    for error in schema.error_log:
        print(f"  Line {error.line}: {error.message}")
