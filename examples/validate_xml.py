from lxml import etree

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
