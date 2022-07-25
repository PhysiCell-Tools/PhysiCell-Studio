# xml_hier2flat.py - convert a hierarchical PhysiCell_settings.xml (with inheritance 
#                    of <cell_definitions>) into one without inheritance, i.e., 
#                    each <cell_definition> is "flattened" (expanded to be complete).
#                    
# Usage:
# $ python xml_hier2flat.py <hierarchical XML>
#
# Author: Randy Heiland
#

import xml.etree.ElementTree as ET
import sys
import string
import copy
import os

show_debug = False

orig_xml_file = "PhysiCell_settings.xml"
argc = len(sys.argv)
print('argc=',argc)
if argc == 2:
    orig_xml_file = sys.argv[1]
elif argc > 2:
    print('Error: too many args. Only 1 allowd (optional):  [.xml config file]')
#print('argv=',sys.argv)

"""
For example:
	<cell_definitions>
		<cell_definition name="A" ID="0" visible="false">
			<p1>0</p1>
			<p2>42</p2>
			<p3>43</p3>
			<custom_data>
				<cval>0.0</cval> 
			</custom_data>
		</cell_definition>
		<cell_definition name="A1" ID="1" parent_type="A">
			<p1>1</p1>
			<custom_data>
				<cval>1.1</cval> 
			</custom_data>
		</cell_definition>
		<cell_definition name="A2 ID="2" parent_type="A">
			<p1>2</p1>
			<custom_data>
				<cval>2.2</cval> 
			</custom_data>
		</cell_definition>
"""

#--------------------------------------------------
print("\n--- Phase 0: Build cell_defs_dict: {cell_def_name : {'ID':value, 'parent':value}, ...} \n\
         and parent_children_dict: {parent_cell_def_name : [child1, child2, ...], ...}")

tree = ET.parse(orig_xml_file)  
xml_root = tree.getroot()

# "cell_def" will be a dict with key = cell_def name, value = {'ID':value, 'parent':value}
cell_defs_dict = {}
parent_children_dict = {}
children_list = []

cell_defs = tree.find('cell_definitions')
print('cell_defs =',cell_defs)
for cd in list(cell_defs):
    print(cd.attrib)
    attrib_dict = {}
    attrib_dict['ID'] = cd.attrib['ID']

    if 'parent_type' in cd.attrib.keys():
        attrib_dict['parent'] = cd.attrib['parent_type']
    else:
        attrib_dict['parent'] = None

    if 'visible' in cd.attrib.keys():
        attrib_dict['visible'] = cd.attrib['visible']

    # if 'parent_type' in cd.attrib.keys():
    #     children_list.append(cd.attrib['name'])
    #     attrib_dict['parent'] = cd.attrib['parent_type']
    #     parent_children_dict[cd.attrib['parent_type']] = children_list
    # else:
    #     attrib_dict['parent'] = None
    #     parent_children_dict[cd.attrib['name']] = None
    cell_defs_dict[cd.attrib['name']] = attrib_dict

print('\n cell_defs_dict= ',cell_defs_dict)  
kv = list(cell_defs_dict.items())
print('\n kv (a list)=',kv)
# for cd in cell_defs_dict:
for cd in kv:
    # print(type(cd[1]))
    print('cd[0] = ',cd[0])
    id_parent = list(cd[1].values()) 
    print('id_parent= ', id_parent)
    if id_parent[1]:  # is there a parent?
        print(' -- id_parent[1] =', id_parent[1])
        print('    (before)parent_children_dict= ',parent_children_dict)  
        # parent_children_dict[cd[0]] = id_parent[1]
        if (id_parent[1] in parent_children_dict.keys()):
            parent_children_dict[id_parent[1]].append(cd[0])
        else:
            # parent_children_dict[id_parent[1]] = list(cd[0])
            parent_children_dict[id_parent[1]] = [cd[0]]
        print('    (after)parent_children_dict= ',parent_children_dict)  

        # if (parent_children_dict[id_parent[1]]):
        #     parent_children_dict[id_parent[1]].append(cd[0])
        # else:
        #     parent_children_dict[id_parent[1]] = []
        
    # if cd.values['parent']:
        # print(' found parent for ',cd.values['parent'])

print("\n-------------------------------------------------------")
print(' parent_children_dict= ',parent_children_dict)
print("-------------------------------------------------------\n")

xml_root = tree.getroot()
# sys.exit()
#--------------------------------------------------
print("\n--- Phase 1: Remove all <cell_definition> nodes with a 'parent_type' attribute.")
cell_defs = tree.find('cell_definitions')
for cd in list(cell_defs):
    # print(cell_def.tag, cell_defs_dict.attrib['name'])
    if show_debug:
        print(cd.attrib)
        print(cd.attrib.keys())
    if ('parent_type' in cd.attrib.keys()):
        if show_debug:
            print("--- removing ", cd.attrib['name'])
        cell_defs.remove(cd)

new_xml_file = "tmp1.xml"
print("---> ",new_xml_file)
tree.write(new_xml_file)
# sys.exit()

#=================================================================================
#=================================================================================
# This is where we want to iterate on all parents, e.g., if
#    parent_children_dict=  {'A': ['A1', 'A2'], 'A2': ['A21', 'A22']}
# then insert 2 new (flattened) copies of A, then fill those in with values from A1 and A2, respectively.
# Then insert 2 copies of (the flattened) A2, then fill those in with values from A21 and A22.

#---------  iterate over all parents -----------
print("\n--- Phase 2: For each child of 'parent_type', make a copy of its parent.")
print('list(parent_children_dict.keys()) = ',list(parent_children_dict.keys()))
# print('list(parent_children_dict.keys())[0] = ',list(parent_children_dict.keys())[0])
# print('list(parent_children_dict.values())[0] = ',list(parent_children_dict.values())[0])

#---------  iterate over all parents -----------
idx = 0
try:
    parent_name = list(parent_children_dict.keys())[idx]
except:
    print("**** No more parents to process.")
    sys.exit()
print("  parent_name=",parent_name)
children_list = list(parent_children_dict.values())[idx]
print("  children_list=",children_list)
tree = ET.parse(new_xml_file)  
xml_root = tree.getroot()
cell_defs = tree.find('cell_definitions')
# print('cell_defs=',cell_defs)
parent_cell_def = xml_root.find("cell_definitions//cell_definition[@name='" + parent_name +"']")
root_name = parent_cell_def.attrib['name'] 
if show_debug:
    print("   root_name = ",root_name)
cd_vals = list(cell_defs_dict.values())
if show_debug:
    print("cd_vals = ",cd_vals)

for child in children_list:
    if show_debug:
        print('inserting child of ',root_name)
        print('ID= ', cell_defs_dict[child]['ID'])
    new_node = copy.deepcopy(parent_cell_def)
    new_node.attrib['name'] = child
    new_node.attrib['ID'] = cell_defs_dict[child]['ID']

    if 'visible' in cell_defs_dict[child].keys():
        # print("---- inserting visible attrib since in ",cell_defs_dict[child].keys())
        new_node.attrib['visible'] = cell_defs_dict[child]['visible']
    else:
        # print("---- inserting visible=true attrib since in it was absent ")
        new_node.attrib['visible'] = "true"

    cell_defs.append(new_node)

# new_xml_file = "tmp2.xml"
new_xml_file = "tmp_flat.xml"
print("---> ",new_xml_file)
tree.write(new_xml_file)

print("\n------> calling recurse_xml()")
print("         with ",orig_xml_file, new_xml_file)
cmd = "python recurse_xml.py " + orig_xml_file + "  " + new_xml_file
os.system(cmd)  # might consider better alternatives later

# sys.exit()

#=================================================================================
#---------  iterate over next parent -----------
# new_xml_file = "tmp3.xml"   # output from recurse_xml.py
# new_xml_file = "recurse_xml_out.xml"   # output from recurse_xml.py
new_xml_file = "flat_xml_out.xml"   # NOTE: this should be the same name as used in recurse_xml.py !
idx = 1
try:
    parent_name = list(parent_children_dict.keys())[idx]
except:
    print("**** No more parents to process.\n")
    print("\n**************************************************")
    print("  YOU SHOULD CHECK that the output file, " + new_xml_file + ", does indeed define your model correctly.")
    print("  And it is up to you to rename this file to be whatever name you want.")
    print("**************************************************\n")

    sys.exit()

print("  parent_name=",parent_name)
children_list = list(parent_children_dict.values())[idx]
print("  children_list=",children_list)
tree = ET.parse(new_xml_file)  
xml_root = tree.getroot()
cell_defs = tree.find('cell_definitions')
# print('cell_defs=',cell_defs)
parent_cell_def = xml_root.find("cell_definitions//cell_definition[@name='" + parent_name +"']")
root_name = parent_cell_def.attrib['name'] 
if show_debug:
    print("   root_name = ",root_name)
cd_vals = list(cell_defs_dict.values())
if show_debug:
    print("cd_vals = ",cd_vals)

for child in children_list:
    if show_debug:
        print('inserting child of ',root_name)
        print('ID= ', cell_defs_dict[child]['ID'])
    new_node = copy.deepcopy(parent_cell_def)
    new_node.attrib['name'] = child
    new_node.attrib['ID'] = cell_defs_dict[child]['ID']

    if 'visible' in cell_defs_dict[child].keys():
        # print("---- inserting visible attrib since in ",cell_defs_dict[child].keys())
        new_node.attrib['visible'] = cell_defs_dict[child]['visible']
    else:
        # print("---- inserting visible=true attrib since in it was absent ")
        new_node.attrib['visible'] = "true"

    cell_defs.append(new_node)

# new_xml_file = "tmp_idx1.xml"
new_xml_file = "tmp_flat.xml"
print("---> ",new_xml_file)
tree.write(new_xml_file)

print("\n------> calling recurse_xml()")
print("         with ",orig_xml_file, new_xml_file)
cmd = "python recurse_xml.py " + orig_xml_file + " " + new_xml_file
os.system(cmd)  # might consider better alternatives later

sys.exit()