# Pretty-print a .xml file
#
# Author: Elmar Bucher

import xml.etree.ElementTree as ET 

def pretty_print(infile,outfile):
    # load file
    tree = ET.parse(infile) 
    root = tree.getroot()

    # here the magic happens
    try:
        ET.indent(root, space='    ') 
    except:  # probably using Python < 3.9 (without "indent" method)
        return

    s_root = ET.tostring(root).decode("utf-8")

    # add a carriage return before each major block
    s_root = s_root.replace('\n    <','\n\n    <')
    s_root = s_root.replace('\n    </','    </')

    # write file
    f = open(outfile, 'w') 
    f.write(s_root) 
    f.close() 
