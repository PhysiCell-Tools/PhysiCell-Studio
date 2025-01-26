"""

Custom Data UI rules:
* populate_tree_cell_defs.py - parse the config file (.xml) and creates the param_d dict:
     * param_d[cell_type]['custom_data'][custom_var_name] = [value, conserved_flag]
     * master_custom_d[custom_var_name] = [units, desc]
   * attempt to create a master list of custom var names which will be the union of all
     unique custom var names across all <cell_definition>. This would allow more flexibility
     when users have a legacy config file. Of course when they save the .xml from the Studio,
     it will write out the entire block of ALL custom vars in each <cell_definition>.

* create_custom_data_tab(): 
   * defines self.custom_data_table = QTableWidget() with 5 columns: 
         Name, Value, Conserved, Units, Description
   * each of those table's cells actually defines another type of widget, 
     e.g, MyQLineEdit, which has a callback function whenever its text changes. 
     The checkbox for "Conserved" is unique.

* update_custom_data_params():
   * called whenever a different cell type is selected in the self.tree = QTreeWidget()

* 
   * maintains the global list of custom var names
* 
    def custom_data_name_changed(self, text):
    def custom_data_value_changed(self, text):
    def custom_var_conserved_clicked(self,bval):
    def custom_data_units_changed(self, text):
    def custom_data_desc_changed(self, text):


Authors:
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
and rf. Credits.md
"""

import os
import sys
import shutil
import copy
import logging
import inspect
import string
import random
import numpy as np
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from PyQt5.QtCore import Qt, QRect, QEvent
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QIcon, QFont, QStandardItemModel, QValidator
from studio_classes import QLabelSeparator, ExtendedCombo, QLineEdit_custom, OptionalDoubleValidator, DoubleValidatorOpenInterval, DoubleValidatorWidgetBounded, AttackRateValidator, QRadioButton_custom, HoverWarning, HoverQuestion, StudioTab, QComboBox_custom, QCheckBox_custom
from rules_tab import create_reserved_words, find_and_replace_rule_cell
from sbml_intra import SBML_ODEs
from cell_def_cycle_tab import CycleTab
from cell_def_tab_param_updates import CellDefParamUpdates

class CellDefException(Exception):
    pass

class QLineEdit_color(QLineEdit):  # it's insane to have to do this!
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # newtab.setStyleSheet("background-color: rgb(236,236,236)")

        # argh, doesn't seem to work!
        style = """
            QLineEdit:enabled {
                color: black;
                background-color: white; 
            }
            QLineEdit:disabled {
                color: black;
                background-color: gray;
            }
            """
        self.setStyleSheet(style)
        # self.setStyleSheet("background-color: white")

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

# Overloading the QCheckBox widget 
class MyQCheckBox(QCheckBox):
    vname = None
    # idx = None  # index
    wrow = 0  # widget's row in a table
    wcol = 0  # widget's column in a table

# Overloading the QLineEdit widget to let us map it to its variable name. Ugh.
class MyQLineEdit(QLineEdit):
    vname = None
    # idx = None  # index
    wrow = 0
    wcol = 0
    prev = None

class CellDef(StudioTab):
    def __init__(self, xml_creator):
        super().__init__(xml_creator)
        
        self.celldef_param_updates = CellDefParamUpdates(self)

        random.seed(42)   # for reproducibility (cough). Needed for pytest results.
        self.param_d = {}  # a dict of dicts
        self.num_dec = 5  # how many digits to right of decimal point?

        self.default_sval = '0.0'  # default scalar value (as string)
        self.default_affinity = '1.0'
        self.default_bval = False
        self.default_time_units = "min"
        self.default_rate_units = "1/min"

        self.rules_tab = None   # update in studio.py

        # rf. https://www.w3.org/TR/SVG11/types.html#ColorKeywords
        self.row_color1 = "background-color: Tan"
        self.row_color2 =  "background-color: LightGreen"

        self.checkbox_style = """
                QCheckBox::indicator:pressed
                {
                    background-color: lightgreen;
                }
                QCheckBox::indicator:unchecked
                {
                    border: 1px solid #5A5A5A;
                    background-color: rgb(236,236,236);
                }
                """

        self.ics_tab = None

        self.current_cell_def = None
        self.cell_adhesion_affinity_celltype = None

        self.new_cell_def_count = 0
        self.label_width = 210
        self.units_width = 35
        self.fixed_checkbox_column_width = 60
        self.idx_current_cell_def = 1    # 1-offset for XML (ElementTree, ET)
        self.xml_root = None
        self.config_path = None
        self.debug_print_fill_xml = True
        # self.custom_var_count = 0  # no longer used? just get len(self.master_custom_var_d)

        self.master_custom_var_d = {}    # dict: [unique custom var name]=[row#, units, desc]
        self.custom_units_default = ''
        self.custom_desc_default = ''
        # self.master_custom_units = []
        # self.master_custom_desc = []
        # self.custom_data_units_width = 90

        self.cycle_duration_flag = False

        self.substrate_list = []
        self.celltypes_list = []

        # Use a QStackedWidget to let us swap out sets of widgets, depending on the cycle model chosen.
        # self.cycle_tab.stacked_cycle = QStackedWidget()

        # transition rates
        self.stack_trate_live_idx = -1 
        self.stack_trate_Ki67_idx = -1 
        self.stack_trate_advancedKi67_idx = -1 
        self.stack_trate_flowcyto_idx = -1 
        self.stack_trate_flowcytosep_idx = -1 
        self.stack_trate_quiescent_idx = -1 

        # duration rates
        self.stack_duration_live_idx = -1 
        self.stack_duration_Ki67_idx = -1 
        self.stack_duration_advancedKi67_idx = -1 
        self.stack_duration_flowcyto_idx = -1 
        self.stack_duration_flowcytosep_idx = -1 
        self.stack_duration_quiescent_idx = -1 

        self.stacked_volume = QStackedWidget()

        # ugly attempt to prettyprint XML
        self.indent1 = '\n'
        self.indent6 = '\n      '
        self.indent8 = '\n        '
        self.indent10 = '\n          '
        self.indent12 = '\n            '
        self.indent14 = '\n              '
        self.indent16 = '\n                '
        self.indent18 = '\n                  '
        self.indent20 = '\n                    '

        # self.cell_defs = CellDefInstances()
        self.cell_def_horiz_layout = QHBoxLayout()

        self.splitter = QSplitter()

        # tree_widget_width = 160
        tree_widget_width = 190
        tree_widget_height = 400
        # tree_widget_height = 1200

        self.tree = QTreeWidget() # tree is overkill; list would suffice; meh.
        # stylesheet = """
        # QTreeWidget::item:selected{
        #     background-color: rgb(236,236,236);
        #     color: black;
        # }
        # """
        stylesheet = """
        QTreeWidget::item:selected{
            background-color: rgb(236,236,236);
            color: black;
        }
        QTreeWidget::item{
            border-bottom: 1px solid black;
            border-left:   1px solid black;
            border-right:  1px solid black;
        }
        """
        self.tree.setStyleSheet(stylesheet)  # don't allow arrow keys to select
        self.tree.setFocusPolicy(QtCore.Qt.NoFocus)  # don't allow arrow keys to select
        # self.tree.setStyleSheet("background-color: lightgray")
        # self.tree.setFixedWidth(tree_widget_width)
        self.tree.setFixedHeight(tree_widget_height)
        # self.tree.setColumnCount(1)
        self.tree.setColumnCount(2)
        # self.tree.setColumnWidth(50,5)   # doesn't work

        self.tree.itemClicked.connect(self.tree_item_clicked_cb)
        self.tree.itemChanged.connect(self.tree_item_changed_cb)   # rename a cell type

        # header = QTreeWidgetItem(["---  Cell Type  ---"])
        header = QTreeWidgetItem(["  ---  Cell Type ---","-- ID --"])
        # self.tree.resizeColumnToContents(5)

        self.tree.setHeaderItem(header)

        self.physiboss_boolean_frame = QFrame()
        self.physiboss_signals = []
        self.physiboss_behaviours = []
        items = []
        model = QtCore.QStringListModel()
        model.setStringList(["aaa","bbb"])


        self.empty_frame = QFrame()
        # self.ode_sbml_frame = QFrame()
        # self.ode_sbml_frame = SBML_ODEs(nanohub_flag, microenv_tab, celldef_tab))
        self.ode_sbml_frame = SBML_ODEs(None, None, self)

        self.cell_def_horiz_layout.addWidget(self.tree)

        self.scroll_cell_def_tree = QScrollArea()
        # self.scroll_cell_def_tree.setWidget(self.tree)

        #-----------
        self.auto_number_IDs_checkbox = QCheckBox_custom("auto number IDs when saved\n(beware of cells.csv using IDs)")

        tree_w_vbox = QVBoxLayout()
        tree_w_vbox.addWidget(self.auto_number_IDs_checkbox)
        tree_w_vbox.addWidget(self.tree)

        # splitter.addWidget(self.tree)
        self.splitter.addWidget(self.scroll_cell_def_tree)

        #------------------
        tree_w_hbox = QHBoxLayout()
        # self.controls_hbox = QHBoxLayout()
        self.new_button = QPushButton("New")
        self.new_button.clicked.connect(self.new_cell_def)
        self.new_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        # self.controls_hbox.addWidget(self.new_button)
        tree_w_hbox.addWidget(self.new_button)

        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_cell_def)
        self.copy_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        # self.controls_hbox.addWidget(self.copy_button)
        tree_w_hbox.addWidget(self.copy_button)

        self.delete_button = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
        self.delete_button.clicked.connect(self.delete_cell_def)
        self.delete_button.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        del_btn_width = 50
        self.delete_button.setFixedWidth(del_btn_width)
        tree_w_hbox.addWidget(self.delete_button)

        #---------
        self.tree_w = QWidget()
        tree_w_vbox.addLayout(tree_w_hbox)
        self.tree_w.setLayout(tree_w_vbox)
        self.scroll_cell_def_tree.setWidget(self.tree_w)

        #------------------
        self.custom_data_tab = QWidget()

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("background-color: rgb(236,236,236)")
        self.splitter.addWidget(self.tab_widget)

        # self.tab_widget.addTab(self.create_cycle_tab(),"Cycle")
        self.tab_widget.addTab(CycleTab(self),"Cycle")
        self.tab_widget.addTab(self.create_death_tab(),"Death")
        self.tab_widget.addTab(self.create_volume_tab(),"Volume")
        self.tab_widget.addTab(self.create_mechanics_tab(),"Mechanics")
        self.tab_widget.addTab(self.create_motility_tab(),"Motility")
        self.tab_widget.addTab(self.create_secretion_tab(),"Secretion")
        self.tab_widget.addTab(self.create_interaction_tab(),"Interactions")
        self.tab_widget.addTab(self.create_intracellular_tab(),"Intracellular")
        self.tab_widget.addTab(self.create_custom_data_tab(),"Custom Data")
        self.tab_widget.addTab(self.create_miscellaneous_tab(),"Misc")

        #---rwh
        self.cell_types_tabs_layout = QGridLayout()
        self.cell_types_tabs_layout.addWidget(self.tab_widget, 0,0,1,1) # w, row, column, rowspan, colspan

    def get_current_celldef(self):
        return self.current_cell_def
    #----------------------------------------------------------------------
    def check_valid_cell_defs(self):
        if self.auto_number_IDs_checkbox.isChecked():
            return

        print('---- check_valid_cell_defs(): ---')

        error_msg = """
Error: Cell Type IDs need to consist of unique integers, include 0, and can be re-ordered to form a sequence (0,1,2,...,N), e.g.,
<br><br>
Valid: (0,1,2,3) or (3,0,2,1)<br>
Invalid: (0,2,3) or (1,2,3)
<br><br>
Please fix the IDs in the Cell Types tab. Also, be mindful of how this may affect a cell.csv file that references cell types by ID.
"""

        valid = True

        # -- check for duplicate names
        found = set()
        dupes = [x for x in self.param_d.keys() if x in found or found.add(x)]
        print("dupes=",dupes)
        if dupes:
            valid = False
        else:
            # -- check for duplicate IDs
            id_l = []
            for cdname in self.param_d.keys():
                id_num = int(self.param_d[cdname]["ID"])
                # print('{cdname}, {self.param_d[cdname]["ID"]}')
                print(f'{cdname}, {self.param_d[cdname]["ID"]}')
                id_l.append(id_num)
            print(f"id_l={id_l}")

            id_l.sort()
            print(f"id_l (sorted)={id_l}")

            for count, value in enumerate(id_l):
                if count != value:
                    valid = False
                    break

        # -- check for ID=0 
        if 0 in id_l:
            print("  found 0 ID")
        else:
            print("  ERROR: No 0 ID")
            valid = False
            # msg = "Error: one cell type must have ID=0"

        if not valid:
            msgBox = QMessageBox()
            msgBox.setTextFormat(Qt.RichText)
            msgBox.setText(error_msg)
            msgBox.setStandardButtons(QMessageBox.Ok)
            returnValue = msgBox.exec()

    #----------------------------------------------------------------------
    def custom_duplicate_error(self,row,col,msg):
        # if self.custom_data_table.cellWidget(row,col).text()  == '0':
            # return
        msgBox = QMessageBox()
        msgBox.setTextFormat(Qt.RichText)
        msgBox.setText(msg)
        msgBox.setStandardButtons(QMessageBox.Ok)
        returnValue = msgBox.exec()

    #----------------------------------------------------------------------
    def custom_table_error(self,row,col,msg):
        # if self.custom_data_table.cellWidget(row,col).text()  == '0':
        #     return
        msgBox = QMessageBox()
        msgBox.setTextFormat(Qt.RichText)
        msgBox.setText(msg)
        msgBox.setStandardButtons(QMessageBox.Ok)
        returnValue = msgBox.exec()

        # Attempt to only warn once... oh well, annoy the user.
        # self.custom_data_edit_active = not self.custom_data_edit_active

    #----------------------------------------------------------------------
    # Set all the default params to what they are in PhysiCell (C++), e.g., *_standard_models.cpp, etc.
    def init_default_phenotype_params(self, cdname, reset_mapping):
        print("----- init_default_phenotype_params(self, cdname): reset_mapping=",reset_mapping)
        self.new_cycle_params(cdname, True)
        self.new_asym_div_params(cdname, reset_mapping)
        self.new_death_params(cdname)
        self.new_volume_params(cdname)
        self.new_mechanics_params(cdname, reset_mapping)
        self.new_motility_params(cdname)
        self.new_secretion_params(cdname)
        self.new_interaction_params(cdname, reset_mapping)
        self.new_intracellular_params(cdname)
        self.new_custom_data_params(cdname)

        self.new_miscellaneous_params(cdname)

        # print("\n\n",self.param_d)
        # self.custom_data_tab.param_d = self.param_d
        # self.custom_data_tab.new_custom_data_params(cdname)

    #----------------------------------------------------------------------
    # @QtCore.Slot()
    def new_cell_def(self):
        print('\n------ new_cell_def()')
        # cdname = "cell_def%02d" % self.new_cell_def_count
        # if cdname in self.param_d.keys():
        #     print('new_cell_def(): duplicate name, changing to a random string')
        #     cdname = self.random_name()

        prefix = "ntype_"
        cdname = self.random_name(prefix,3)
        while True:
            if cdname in self.param_d.keys():
                print('new_cell_def(): duplicate name, changing to a random string')
                cdname = self.random_name(prefix,3)
            else:
                break

        self.new_cell_def_named(cdname) # added by DRB to make it easier for BIWT to add a new cell type programmatically

    def new_cell_def_named(self, cdname):

        # Make a new cell type (that's a copy of the currently selected one)
        self.param_d[cdname] = copy.deepcopy(self.param_d[self.current_cell_def])
        self.param_d[cdname]["ID"] = str(self.new_cell_def_count)

        self.init_default_phenotype_params(cdname, True)

        self.current_cell_def = cdname

        self.add_new_celltype(cdname)  # add to all qcomboboxes that have celltypes (e.g., in interactions)

        #-----  Update this new cell def's widgets' values
        num_items = self.tree.invisibleRootItem().childCount()

        treeitem = QTreeWidgetItem([cdname, self.param_d[cdname]["ID"]])
        treeitem.setFlags(treeitem.flags() | QtCore.Qt.ItemIsEditable)
        self.tree.insertTopLevelItem(num_items,treeitem)
        self.tree.setCurrentItem(treeitem)

        self.tree_item_clicked_cb(treeitem, 0)

        self.new_cell_def_count += 1

    #----------------------
    # When a cell type is selected(via double-click) and renamed
    def tree_item_changed_cb(self, it,col):
        logging.debug(f'--------- tree_item_changed_cb(): {it}, {col}, {it.text(col)}')  # col 0 is name; 1 is ID
        # print(f'--------- tree_item_changed_cb(): {it}, {col}, {it.text(col)}')  
        currentIndex= self.tree.currentIndex()
        # print(f'currentIndex= {currentIndex}')
        # print("dir= ",dir(currentIndex))
        row = currentIndex.row()
        # print(f'currentIndex.row()= {currentIndex.row()}')

        item_idx = self.tree.indexFromItem(self.tree.currentItem()).row() 
        # print(f'item_idx= {item_idx}')

        if col == 1:  # ID
            cdname = it.text(0)
            self.param_d[cdname]["ID"] = it.text(1)
            return

        prev_name = self.current_cell_def
        logging.debug(f'prev_name= {prev_name}')
        # print(f'prev_name= {prev_name}')
        # new_name = it.text(col)
        new_name = it.text(0)
        id_num = it.text(1)
        print("cell_def_tab:  tree_item_changed_cb(): keys=", self.param_d.keys())

        while True:
            if new_name in self.param_d.keys():
                print("\n------ ERROR: name exists!")
                msgBox = QMessageBox()
                msgBox.setTextFormat(Qt.RichText)
                # msgBox.setText("Error: duplicate name, please rename.")
                msgBox.setText("Error: Duplicate name. We will append a random suffix.")
                msgBox.setStandardButtons(QMessageBox.Ok)
                returnValue = msgBox.exec()
                new_name = self.random_name(new_name+"_",3)
                # print("----- new_name (after append suffix) = ",new_name)

                treeitem = QTreeWidgetItem([new_name, id_num])
                treeitem.setFlags(treeitem.flags() | QtCore.Qt.ItemIsEditable)
                # self.tree.topLevelItem(0).child(1).setText(0, "foo")
                # self.tree.topLevelItem(0).setText(0, "foo")
                # num_items = self.tree.invisibleRootItem().childCount()
                # self.tree.insertTopLevelItem(num_items,treeitem)
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(self.tree.currentItem()))
                self.tree.insertTopLevelItem(item_idx,treeitem)
                self.tree.setCurrentItem(treeitem)
                # self.tree.show()

                # num_items = self.tree.invisibleRootItem().childCount()
                # # print("tree has num_items = ",num_items)
                # treeitem = QTreeWidgetItem([cdname_copy, self.param_d[cdname_copy]["ID"]])
                # treeitem.setFlags(treeitem.flags() | QtCore.Qt.ItemIsEditable)
                # self.tree.insertTopLevelItem(num_items,treeitem)
                # self.tree.setCurrentItem(treeitem)
                # self.tree_item_clicked_cb(treeitem, 0)

            else:
                break

        # For now, need to copy/paste this section into pytest code, 
        self.current_cell_def = new_name
        logging.debug(f'new name= {self.current_cell_def}')
        # print(f'new name= {self.current_cell_def}')
        self.param_d[self.current_cell_def] = self.param_d.pop(prev_name)  # sweet

        self.live_phagocytosis_celltype = self.current_cell_def
        self.attack_rate_celltype = self.current_cell_def
        self.fusion_rate_celltype = self.current_cell_def
        self.transformation_rate_celltype = self.current_cell_def

        # print(f'before calling renamed_celltype(): prev_name= {prev_name}')
        self.renamed_celltype(prev_name, self.current_cell_def)

    #----------------------------------------------------------------------
    def random_name(self,prefix,num_chars):
        letters = string.ascii_lowercase
        # return ''.join(random.choice(letters) for i in range(num_chars))
        rstring = ''.join(random.choice(letters) for i in range(num_chars))
        return (prefix + rstring)

    #----------------------------------------------------------------------
    # @QtCore.Slot()
    # Make a new cell_def (that's a copy of the currently selected one)
    def copy_cell_def(self):
        print('------ copy_cell_def()')
        # cdname_copy = "cell_def%02d" % self.new_cell_def_count
        prefix = "ctype_"
        cdname_copy = self.random_name(prefix,3)
        while True:
            if cdname_copy in self.param_d.keys():
                print('copy_cell_def(): duplicate name, changing to a random string')
                cdname_copy = self.random_name(prefix,3)
            else:
                break

        cdname_original = self.current_cell_def
        self.param_d[cdname_copy] = copy.deepcopy(self.param_d[cdname_original])

        self.param_d[cdname_copy]["ID"] = str(self.new_cell_def_count)  # rwh Note: we won't do this if we auto-generate the ID #s at "save"

        for cdname in self.param_d.keys():    # for each cell def, set how it interacts with new cell based on how it interacted with original cell
            self.param_d[cdname]['live_phagocytosis_rate'][cdname_copy] = self.param_d[cdname]['live_phagocytosis_rate'][cdname_original]
            self.param_d[cdname]['attack_rate'][cdname_copy] = self.param_d[cdname]['attack_rate'][cdname_original]
            self.param_d[cdname]['fusion_rate'][cdname_copy] = self.param_d[cdname]['fusion_rate'][cdname_original]
            self.param_d[cdname]['transformation_rate'][cdname_copy] = self.param_d[cdname]['transformation_rate'][cdname_original]

            self.param_d[cdname]['asymmetric_division_probability'][cdname_copy] = self.param_d[cdname]['asymmetric_division_probability'][cdname_original]

            self.param_d[cdname]['cell_adhesion_affinity'][cdname_copy] = self.param_d[cdname]['cell_adhesion_affinity'][cdname_original]  # default affinity
           
        self.param_d[cdname_original]['asymmetric_division_probability'][cdname_copy] = '0'  # default to keeping asym div weights to other cell types, but assume no info on weight to new cell type
        self.param_d[cdname_copy]['asymmetric_division_probability'][cdname_original] = '0'  # default to keeping asym div weights to other cell types, but assume no info on weight to original cell type
        logging.debug(f'--> copy_cell_def():\n {self.param_d[cdname_copy]}')
        # print('2) copy_cell_def(): param_d.keys=',self.param_d.keys())

        # for k in self.param_d.keys():
        #     print(" (pre-new vals)===>>> ",k, " : ", self.param_d[k])
        #     print()
        # print()

        self.current_cell_def = cdname_copy
        # self.cell_type_name.setText(cdname)

        self.add_new_celltype(cdname_copy)  # add to all qcomboboxes that have celltypes (e.g., in interactions)
        # print('3) copy_cell_def(): param_d.keys=',self.param_d.keys())

        #-----  Update this new cell def's widgets' values
        num_items = self.tree.invisibleRootItem().childCount()
        # print("tree has num_items = ",num_items)
        # treeitem = QTreeWidgetItem([cdname_copy])
        treeitem = QTreeWidgetItem([cdname_copy, self.param_d[cdname_copy]["ID"]])
        treeitem.setFlags(treeitem.flags() | QtCore.Qt.ItemIsEditable)
        self.tree.insertTopLevelItem(num_items,treeitem)
        self.tree.setCurrentItem(treeitem)

        self.tree_item_clicked_cb(treeitem, 0)

        self.new_cell_def_count += 1
        
    #----------------------------------------------------------------------
    def show_delete_warning(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Not allowed to delete all cell types.")
        #    msgBox.setWindowTitle("Example")
        msgBox.setStandardButtons(QMessageBox.Ok)
        # msgBox.buttonClicked.connect(msgButtonClick)

        returnValue = msgBox.exec()
        # if returnValue == QMessageBox.Ok:
            # print('OK clicked')

    #----------------------------------------------------------------------
    # @QtCore.Slot()
    def delete_cell_def(self):
        num_items = self.tree.invisibleRootItem().childCount()
        print('------ delete_cell_def: num_items=',num_items)
        if num_items == 1:
            # print("Not allowed to delete all substrates.")
            # QMessageBox.information(self, "Not allowed to delete all substrates")
            self.show_delete_warning()
            return

        self.new_cell_def_count -= 1

        item_idx = self.tree.indexFromItem(self.tree.currentItem()).row() 
        print('------      item_idx=',item_idx)
        # delete celltype from dropdowns

        # remove from the dropdown widgets:
        # Mechanics
        self.cell_adhesion_affinity_dropdown.removeItem(item_idx)
        # Interactions
        self.live_phagocytosis_dropdown.removeItem(item_idx)
        self.attack_rate_dropdown.removeItem(item_idx)
        self.fusion_rate_dropdown.removeItem(item_idx)
        self.cell_transformation_dropdown.removeItem(item_idx)

        # ICs
        if self.ics_tab:
            self.ics_tab.celltype_combobox.removeItem(item_idx)

        # But ALSO remove from the dicts:
        logging.debug(f'--- cell_adhesion_affinity= {self.param_d[self.current_cell_def]["cell_adhesion_affinity"]}')
        print(f'\ndelete_cell_def(): ----- cell_adhesion_affinity= {self.param_d[self.current_cell_def]["cell_adhesion_affinity"]}')

        # remove from the widgets

        # TODO: is this safe? Seems so.
        del self.param_d[self.current_cell_def]

        # do *after* removing from param_d keys.
        if self.rules_tab:
            self.rules_tab.delete_celltype(item_idx)

        # For the remaining cell defs, if any, remove the deleted cell def from certain dicts
        for cdef in self.param_d.keys():
            # Mechanics
            self.param_d[cdef]['cell_adhesion_affinity'].pop(self.current_cell_def,0)  

            # Interactions
            self.param_d[cdef]['live_phagocytosis_rate'].pop(self.current_cell_def,0)
            self.param_d[cdef]['attack_rate'].pop(self.current_cell_def,0)
            self.param_d[cdef]['fusion_rate'].pop(self.current_cell_def,0)
            self.param_d[cdef]['transformation_rate'].pop(self.current_cell_def,0)
            self.param_d[cdef]['asymmetric_division_probability'].pop(self.current_cell_def,0)

        self.cycle_tab.delete_celltype(self.current_cell_def)

        item_idx = self.tree.indexFromItem(self.tree.currentItem()).row()   # rwh: apparently not used?
        self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(self.tree.currentItem()))

        self.current_cell_def = self.tree.currentItem().text(0)

        self.tree_item_clicked_cb(self.tree.currentItem(), 0)

    #--------------------------------------------------------
    def create_death_tab(self):
        death_tab = QWidget()
        death_tab.setStyleSheet("background-color: rgb(236,236,236)")
        death_tab.setStyleSheet("QLineEdit { background-color: white }")
        death_tab_scroll = QScrollArea()
        glayout = QGridLayout()

        #----------------
        label = QLabel("Apoptosis")
        label.setFixedSize(100,20)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet('background-color: orange')  # yellow?
        idr = 0
        glayout.addWidget(label, idr,0, 1,4) # w, row, column, rowspan, colspan

        label = QLabel("death rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_death_rate = QLineEdit(objectName="apoptosis_death_rate")
        self.apoptosis_death_rate.textChanged.connect(self.cell_def_pheno_rate_changed)
        self.apoptosis_death_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_death_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_death_rate_warning_label = HoverWarning("")
        glayout.addWidget(self.apoptosis_death_rate_warning_label, idr, 3, 1, 1) # w, row, column, rowspan, colspan

        #-------
        hbox = QHBoxLayout()
        hbox.setSpacing(0)
        hbox.setContentsMargins(0, 0, 0, 0)

        self.apoptosis_rb1 = QRadioButton_custom("transition rate     ", parent=self)  # OMG, leave "self" for QButtonGroup
        self.apoptosis_rb1.toggled.connect(self.apoptosis_phase_transition_cb)

        self.apoptosis_rb2 = QRadioButton_custom("duration", parent=self)
        self.apoptosis_rb2.toggled.connect(self.apoptosis_phase_transition_cb)

        hbox.addWidget(self.apoptosis_rb1)

        hbox.addWidget(self.apoptosis_rb2)

        radio_frame = QFrame()
        radio_frame.setStyleSheet("QFrame{ border : 1px solid black; }")
        radio_frame.setLayout(hbox)
        radio_frame.setFixedWidth(210)  # omg
        radio_frame.setFixedHeight(30)
        idr += 1
        glayout.addWidget(radio_frame, idr,0, 1,2) # w, row, column, rowspan, colspan

        #-----
        label = QLabel("phase 0->1 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_01_trate = QLineEdit(objectName="apoptosis_01_trate")
        self.apoptosis_01_trate.textChanged.connect(self.cell_def_pheno_rate_changed)
        self.apoptosis_01_trate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_01_trate, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_01_fixed_trate = QCheckBox_custom("Fixed", maximumWidth=self.fixed_checkbox_column_width, objectName="apoptosis_01_fixed")
        self.apoptosis_01_fixed_trate.toggled.connect(self.cell_def_fixed_clicked)
        glayout.addWidget(self.apoptosis_01_fixed_trate, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_01_trate_warning_label = HoverWarning("")
        glayout.addWidget(self.apoptosis_01_trate_warning_label, idr, 4, 1, 1) # w, row, column, rowspan, colspan

        #-----
        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_01_duration = QLineEdit(objectName="apoptosis_01_duration")
        self.apoptosis_01_duration.textChanged.connect(self.cell_def_pheno_duration_changed)
        self.apoptosis_01_duration.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_01_duration, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_01_fixed_duration = QCheckBox_custom("Fixed", maximumWidth=self.fixed_checkbox_column_width, objectName="apoptosis_01_fixed")
        self.apoptosis_01_fixed_duration.toggled.connect(self.cell_def_fixed_clicked)
        glayout.addWidget(self.apoptosis_01_fixed_duration, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_01_duration_warning_label = HoverWarning("")
        glayout.addWidget(self.apoptosis_01_duration_warning_label, idr, 4, 1, 1) # w, row, column, rowspan, colspan

        #-------------------
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,4) # w, row, column, rowspan, colspan

        label = QLabel("unlysed fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_unlysed_rate = QLineEdit(objectName="apoptosis_unlysed_rate")
        self.apoptosis_unlysed_rate.textChanged.connect(self.cell_def_param_changed)
        self.apoptosis_unlysed_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_unlysed_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("lysed fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_lysed_rate = QLineEdit(objectName="apoptosis_lysed_rate")
        self.apoptosis_lysed_rate.textChanged.connect(self.cell_def_param_changed)
        self.apoptosis_lysed_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_lysed_rate, idr,1, 1,1) # w, row, column, rowspan, colspan
        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("cytoplasmic biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_cytoplasmic_biomass_change_rate = QLineEdit(objectName="apoptosis_cyto_rate")
        self.apoptosis_cytoplasmic_biomass_change_rate.textChanged.connect(self.cell_def_param_changed)
        self.apoptosis_cytoplasmic_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_cytoplasmic_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("nuclear biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_nuclear_biomass_change_rate = QLineEdit(objectName="apoptosis_nuclear_rate")
        self.apoptosis_nuclear_biomass_change_rate.textChanged.connect(self.cell_def_param_changed)
        self.apoptosis_nuclear_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_nuclear_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("calcification rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_calcification_rate = QLineEdit(objectName="apoptosis_calcif_rate")
        self.apoptosis_calcification_rate.textChanged.connect(self.cell_def_param_changed)
        self.apoptosis_calcification_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_calcification_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("relative rupture volume")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_relative_rupture_volume = QLineEdit(objectName="apoptosis_rel_rupture_volume")
        self.apoptosis_relative_rupture_volume.textChanged.connect(self.cell_def_param_changed)
        self.apoptosis_relative_rupture_volume.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_relative_rupture_volume, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #------------------------------------------------------
        label = QLabel("Necrosis")
        label.setFixedSize(100,20)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet('background-color: orange')
        idr += 1
        glayout.addWidget(label, idr,0, 1,4) # w, row, column, rowspan, colspan

        label = QLabel("death rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_death_rate = QLineEdit(objectName="necrosis_death_rate")
        self.necrosis_death_rate.textChanged.connect(self.cell_def_pheno_rate_changed)
        self.necrosis_death_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_death_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_death_rate_warning_label = HoverWarning("")
        glayout.addWidget(self.necrosis_death_rate_warning_label, idr, 3, 1, 1) # w, row, column, rowspan, colspan

        #-------
        hbox = QHBoxLayout()
        hbox.setSpacing(0)
        hbox.setContentsMargins(0, 0, 0, 0)

        self.necrosis_rb1 = QRadioButton_custom("transition rate     ", parent=self)  # OMG, leave "self" for QButtonGroup
        self.necrosis_rb1.toggled.connect(self.necrosis_phase_transition_cb)

        self.necrosis_rb2 = QRadioButton_custom("duration", parent=self)
        self.necrosis_rb2.toggled.connect(self.necrosis_phase_transition_cb)

        hbox.addWidget(self.necrosis_rb1)
        hbox.addWidget(self.necrosis_rb2)

        radio_frame = QFrame()
        radio_frame.setStyleSheet("QFrame{ border : 1px solid black; }")
        radio_frame.setLayout(hbox)
        radio_frame.setFixedWidth(210)  # omg
        radio_frame.setFixedHeight(30)
        idr += 1
        glayout.addWidget(radio_frame, idr,0, 1,2) # w, row, column, rowspan, colspan

        #-----
        label = QLabel("phase 0->1 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_01_trate = QLineEdit(objectName="necrosis_01_trate")
        self.necrosis_01_trate.textChanged.connect(self.cell_def_pheno_rate_changed)
        self.necrosis_01_trate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_01_trate, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_01_fixed_trate = QCheckBox_custom("Fixed", maximumWidth=self.fixed_checkbox_column_width, objectName="necrosis_01_fixed")
        self.necrosis_01_fixed_trate.toggled.connect(self.cell_def_fixed_clicked)
        glayout.addWidget(self.necrosis_01_fixed_trate, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_01_trate_warning_label = HoverWarning("")
        glayout.addWidget(self.necrosis_01_trate_warning_label, idr, 4, 1, 1) # w, row, column, rowspan, colspan

        #-----
        label = QLabel("phase 1->2 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_12_trate = QLineEdit(objectName="necrosis_12_trate")
        self.necrosis_12_trate.textChanged.connect(self.cell_def_pheno_rate_changed)
        self.necrosis_12_trate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_12_trate, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_12_fixed_trate = QCheckBox_custom("Fixed", maximumWidth=self.fixed_checkbox_column_width, objectName="necrosis_12_fixed")
        self.necrosis_12_fixed_trate.toggled.connect(self.cell_def_fixed_clicked)
        glayout.addWidget(self.necrosis_12_fixed_trate, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_12_trate_warning_label = HoverWarning("")
        glayout.addWidget(self.necrosis_12_trate_warning_label, idr, 4, 1, 1) # w, row, column, rowspan, colspan

        #-----------------
        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_01_duration = QLineEdit(objectName="necrosis_01_duration")
        self.necrosis_01_duration.textChanged.connect(self.cell_def_pheno_duration_changed)
        self.necrosis_01_duration.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_01_duration, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_01_fixed_duration = QCheckBox_custom("Fixed", maximumWidth=self.fixed_checkbox_column_width, objectName="necrosis_01_fixed")
        self.necrosis_01_fixed_duration.toggled.connect(self.cell_def_fixed_clicked)
        glayout.addWidget(self.necrosis_01_fixed_duration, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_01_duration_warning_label = HoverWarning("")
        glayout.addWidget(self.necrosis_01_duration_warning_label, idr, 4, 1, 1) # w, row, column, rowspan, colspan

        #----
        label = QLabel("phase 1 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_12_duration = QLineEdit(objectName="necrosis_12_duration")
        self.necrosis_12_duration.textChanged.connect(self.cell_def_pheno_duration_changed)
        self.necrosis_12_duration.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_12_duration, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_12_fixed_duration = QCheckBox_custom("Fixed", maximumWidth=self.fixed_checkbox_column_width, objectName="necrosis_12_fixed")
        self.necrosis_12_fixed_duration.toggled.connect(self.cell_def_fixed_clicked)
        glayout.addWidget(self.necrosis_12_fixed_duration, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_12_duration_warning_label = HoverWarning("")
        glayout.addWidget(self.necrosis_12_duration_warning_label, idr, 4, 1, 1) # w, row, column, rowspan, colspan

        #-------------------
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,4) # w, row, column, rowspan, colspan

        label = QLabel("unlysed fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_unlysed_rate = QLineEdit(objectName="necrosis_unlysed_rate")
        self.necrosis_unlysed_rate.textChanged.connect(self.cell_def_param_changed)
        self.necrosis_unlysed_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_unlysed_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("lysed fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_lysed_rate = QLineEdit(objectName="necrosis_lysed_rate")
        self.necrosis_lysed_rate.textChanged.connect(self.cell_def_param_changed)
        self.necrosis_lysed_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_lysed_rate, idr,1, 1,1) # w, row, column, rowspan, colspan
        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        
        label = QLabel("cytoplasmic biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_cytoplasmic_biomass_change_rate = QLineEdit(objectName="necrosis_cyto_rate")
        self.necrosis_cytoplasmic_biomass_change_rate.textChanged.connect(self.cell_def_param_changed)
        self.necrosis_cytoplasmic_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_cytoplasmic_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("nuclear biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_nuclear_biomass_change_rate = QLineEdit(objectName="necrosis_nuclear_rate")
        self.necrosis_nuclear_biomass_change_rate.textChanged.connect(self.cell_def_param_changed)
        self.necrosis_nuclear_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_nuclear_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("calcification rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_calcification_rate = QLineEdit(objectName="necrosis_calcif_rate")
        self.necrosis_calcification_rate.textChanged.connect(self.cell_def_param_changed)
        self.necrosis_calcification_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_calcification_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("relative rupture volume")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_relative_rupture_volume = QLineEdit(objectName="necrosis_rel_rupture_rate")
        self.necrosis_relative_rupture_volume.textChanged.connect(self.cell_def_param_changed)
        self.necrosis_relative_rupture_volume.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_relative_rupture_volume, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---------
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,4) # w, row, column, rowspan, colspan

        self.reset_death_button = QPushButton("Reset to PhysiCell defaults")
        self.reset_death_button.setFixedWidth(200)
        self.reset_death_button.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        self.reset_death_button.clicked.connect(self.reset_death_cb)
        idr += 1
        glayout.addWidget(self.reset_death_button, idr,0, 1,1) # w, row, column, rowspan, colspan

        #--------
        death_tab_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        death_tab_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        death_tab_scroll.setWidgetResizable(True)
        death_tab_scroll.setWidget(death_tab) 

        death_tab.setLayout(glayout)
        return death_tab_scroll

    #--------------------------------------------------------
    def reset_death_cb(self):
        self.new_death_params(self.current_cell_def)
        self.tree_item_clicked_cb(self.tree.currentItem(), 0)

    #--------------------------------------------------------
    def apoptosis_phase_transition_cb(self):
        logging.debug(f'\n  ---- apoptosis_phase_transition_cb: ')

        radioBtn = self.sender()
        if radioBtn.isChecked():
            logging.debug(f'apoptosis: ------>> {radioBtn.text()}')

        if "duration" in radioBtn.text():
            logging.debug(f'apoptosis_phase_transition_cb: --> duration')
            self.apoptosis_duration_flag = True
            self.apoptosis_01_trate.setReadOnly(True)
            self.apoptosis_01_trate.setStyleSheet("background-color: lightgray")  
            self.apoptosis_01_fixed_trate.setEnabled(False)

            self.apoptosis_01_duration.setReadOnly(False)
            self.apoptosis_01_duration.setStyleSheet("background-color: white")
            self.apoptosis_01_fixed_duration.setEnabled(True)
        else:  # transition rates
            logging.debug(f'apoptosis_phase_transition_cb: NOT duration')
            self.apoptosis_duration_flag = False
            self.apoptosis_01_duration.setReadOnly(True)
            self.apoptosis_01_duration.setStyleSheet("background-color: lightgray")  
            self.apoptosis_01_fixed_duration.setEnabled(False)

            self.apoptosis_01_trate.setReadOnly(False)
            self.apoptosis_01_trate.setStyleSheet("background-color: white")  
            self.apoptosis_01_fixed_trate.setEnabled(True)

        self.param_d[self.current_cell_def]['apoptosis_duration_flag'] = self.apoptosis_duration_flag

    #------------
    def necrosis_phase_transition_cb(self):
        # rb1.toggled.connect(self.updateLabel)(self, idx_choice):
        # print('self.cycle_rows_vbox.count()=', self.cycle_rows_vbox.count())
        logging.debug(f'\n  ---- necrosis_phase_transition_cb: ')

        radioBtn = self.sender()
        if radioBtn.isChecked():
            logging.debug(f'necrosis: ------>>{radioBtn.text()}')

        if "duration" in radioBtn.text():
            logging.debug(f'necrosis_phase_transition_cb: --> duration')
            self.necrosis_duration_flag = True
            self.necrosis_01_trate.setReadOnly(True)
            self.necrosis_01_trate.setStyleSheet("background-color: lightgray")
            self.necrosis_01_fixed_trate.setEnabled(False)
            self.necrosis_12_trate.setReadOnly(True)
            self.necrosis_12_trate.setStyleSheet("background-color: lightgray")
            self.necrosis_12_fixed_trate.setEnabled(False)

            self.necrosis_01_duration.setReadOnly(False)
            self.necrosis_01_duration.setStyleSheet("background-color: white")
            self.necrosis_01_fixed_duration.setEnabled(True)
            self.necrosis_12_duration.setReadOnly(False)
            self.necrosis_12_duration.setStyleSheet("background-color: white")
            self.necrosis_12_fixed_duration.setEnabled(True)
        else:  # transition rates
            logging.debug(f'necrosis_phase_transition_cb: NOT duration')
            self.necrosis_duration_flag = False
            self.necrosis_01_duration.setReadOnly(True)
            self.necrosis_01_duration.setStyleSheet("background-color: lightgray")
            self.necrosis_01_fixed_duration.setEnabled(False)
            self.necrosis_12_duration.setReadOnly(True)
            self.necrosis_12_duration.setStyleSheet("background-color: lightgray")
            self.necrosis_12_fixed_duration.setEnabled(False)

            self.necrosis_01_trate.setReadOnly(False)
            self.necrosis_01_trate.setStyleSheet("background-color: white")  
            self.necrosis_01_fixed_trate.setEnabled(True)
            self.necrosis_12_trate.setReadOnly(False)
            self.necrosis_12_trate.setStyleSheet("background-color: white")  
            self.necrosis_12_fixed_trate.setEnabled(True)

        self.param_d[self.current_cell_def]['necrosis_duration_flag'] = self.necrosis_duration_flag

    #--------------------------------------------------------
    def create_volume_tab(self):
        volume_tab = QWidget()
        volume_tab.setStyleSheet("background-color: rgb(236,236,236)")
        glayout = QGridLayout()

        label = QLabel("Phenotype: volume")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)

        label = QLabel("total")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr = 0
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_total = QLineEdit_color(objectName="volume_total")
        self.volume_total.textChanged.connect(self.cell_def_param_changed)
        self.volume_total.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_total, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("micron^3")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("fluid fraction")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_fluid_fraction = QLineEdit_color(objectName="volume_fluid_fraction")
        self.volume_fluid_fraction.textChanged.connect(self.cell_def_param_changed)
        self.volume_fluid_fraction.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_fluid_fraction, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("nuclear")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_nuclear = QLineEdit_color(objectName="volume_nuclear")
        self.volume_nuclear.textChanged.connect(self.cell_def_param_changed)
        self.volume_nuclear.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_nuclear, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("micron^3")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        
        #---
        label = QLabel("fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_fluid_change_rate = QLineEdit_color(objectName="volume_fluid_change_rate")
        self.volume_fluid_change_rate.textChanged.connect(self.cell_def_param_changed)
        self.volume_fluid_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_fluid_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("cytoplasmic biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_cytoplasmic_biomass_change_rate = QLineEdit_color(objectName="volume_cytoplasmic_rate")
        self.volume_cytoplasmic_biomass_change_rate.textChanged.connect(self.cell_def_param_changed)
        self.volume_cytoplasmic_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_cytoplasmic_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("nuclear biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_nuclear_biomass_change_rate = QLineEdit_color(objectName="volume_nuclear_rate")
        self.volume_nuclear_biomass_change_rate.textChanged.connect(self.cell_def_param_changed)
        self.volume_nuclear_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_nuclear_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        
        #---
        label = QLabel("calcification fraction")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_calcified_fraction = QLineEdit_color(objectName="volume_calcif_fraction")
        self.volume_calcified_fraction.textChanged.connect(self.cell_def_param_changed)
        self.volume_calcified_fraction.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_calcified_fraction, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("calcified rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_calcification_rate = QLineEdit_color(objectName="volume_calcif_rate")
        self.volume_calcification_rate.textChanged.connect(self.cell_def_param_changed)
        self.volume_calcification_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_calcification_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        
        #---
        # <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>
        label = QLabel("relative rupture volume")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.relative_rupture_volume = QLineEdit_color(objectName="volume_rel_rupture_vol")
        self.relative_rupture_volume.textChanged.connect(self.cell_def_param_changed)
        self.relative_rupture_volume.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.relative_rupture_volume, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---------
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,4) # w, row, column, rowspan, colspan

        self.reset_volume_button = QPushButton("Reset to PhysiCell defaults")
        self.reset_volume_button.setFixedWidth(200)
        self.reset_volume_button.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        self.reset_volume_button.clicked.connect(self.reset_volume_cb)
        idr += 1
        glayout.addWidget(self.reset_volume_button, idr,0, 1,1) # w, row, column, rowspan, colspan

        #------
        for idx in range(5):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idr += 1
            glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan

        #------
        volume_tab.setLayout(glayout)
        return volume_tab

    #--------------------------------------------------------
    def reset_volume_cb(self):
        self.new_volume_params(self.current_cell_def)
        self.tree_item_clicked_cb(self.tree.currentItem(), 0)

    #--------------------------------------------------------
    def create_mechanics_tab(self):
        mechanics_tab = QWidget()
        mechanics_tab.setStyleSheet("background-color: rgb(236,236,236)")
        glayout = QGridLayout()

        label = QLabel("Phenotype: mechanics")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)

        # opposite of 'is_movable' in C++
        self.unmovable_w = QCheckBox_custom("unmovable (not available yet)")
        self.unmovable_w.setEnabled(True)   # disabled until implemented in C++?
        self.unmovable_w.setChecked(False)
        idr = 0

        label = QLabel("cell-cell adhesion strength")
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        idr = 0
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.cell_cell_adhesion_strength = QLineEdit_color(objectName="mechanics_adhesion")
        self.cell_cell_adhesion_strength.textChanged.connect(self.cell_def_param_changed)
        self.cell_cell_adhesion_strength.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cell_cell_adhesion_strength, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("micron/min")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("cell-cell repulsion strength")
        # label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.cell_cell_repulsion_strength = QLineEdit_color(objectName="mechanics_repulsion")
        self.cell_cell_repulsion_strength.textChanged.connect(self.cell_def_param_changed)
        self.cell_cell_repulsion_strength.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cell_cell_repulsion_strength, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("micron/min")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        ### cell-bm interactions; save for later (db: 2024-05-31)
        #-----
        # self.new_stuff = False
        self.new_stuff = True

        #---
        label = QLabel("relative max adhesion distance")
        # label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.relative_maximum_adhesion_distance = QLineEdit_color(objectName="mechanics_adhesion_distance")
        self.relative_maximum_adhesion_distance.textChanged.connect(self.cell_def_param_changed)
        self.relative_maximum_adhesion_distance.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.relative_maximum_adhesion_distance, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("cell adhesion affinity")
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.cell_adhesion_affinity_dropdown = QComboBox_custom()
        glayout.addWidget(self.cell_adhesion_affinity_dropdown, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.cell_adhesion_affinity_dropdown.currentIndexChanged.connect(self.cell_adhesion_affinity_dropdown_changed_cb)  # beware: will be triggered on a ".clear" too

        self.cell_adhesion_affinity = QLineEdit_color()
        self.cell_adhesion_affinity.textChanged.connect(self.cell_adhesion_affinity_changed)
        self.cell_adhesion_affinity.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cell_adhesion_affinity , idr,2, 1,1) # w, row, column, rowspan, colspan
    
        #---
        label = QLabel("Cell-cell adhesion strength alternatives")
        label.setFixedHeight(20)
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)
        idr += 1
        glayout.addWidget(label, idr,0, 1,5) # w, row, column, rowspan, colspan

        #--------
        label = QLabel("relative equilibrium distance")
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.set_relative_equilibrium_distance = QLineEdit_color(objectName="mechanics_relative_equilibrium_distance")
        self.set_relative_equilibrium_distance.textChanged.connect(self.set_relative_equilibrium_distance_cb)
        self.set_relative_equilibrium_distance.setValidator(QtGui.QDoubleValidator(bottom=0.0)) # PhysiCell sets this to 2.0 if it is bigger than 2.0 anyways
        glayout.addWidget(self.set_relative_equilibrium_distance, idr,2, 1,1) # w, row, column, rowspan, colspan

        self.set_relative_equilibrium_distance_enabled = QCheckBox_custom("enable", objectName="mechanics_relative_equilibrium_distance_enabled")
        self.set_relative_equilibrium_distance_enabled.stateChanged.connect(self.set_relative_equilibrium_distance_enabled_cb)
        glayout.addWidget(self.set_relative_equilibrium_distance_enabled, idr,0, 1,1, alignment=QtCore.Qt.AlignRight) # w, row, column, rowspan, colspan

        self.set_relative_equilibrium_distance_warning_label = HoverWarning("PhysiCell sets this to 2.0 if it is bigger than 2.0.")
        glayout.addWidget(self.set_relative_equilibrium_distance_warning_label, idr, 4, 1,1) # w, row, column, rowspan, colspan

        #--------
        label = QLabel("absolute equilibrium distance")
        # label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.set_absolute_equilibrium_distance = QLineEdit_color(objectName="mechanics_absolute_equilibrium_distance")
        self.set_absolute_equilibrium_distance.textChanged.connect(self.set_absolute_equilibrium_distance_cb)
        self.set_absolute_equilibrium_distance.setValidator(QtGui.QDoubleValidator(bottom=0.0))
        glayout.addWidget(self.set_absolute_equilibrium_distance, idr,2, 1,1) # w, row, column, rowspan, colspan

        self.set_absolute_equilibrium_distance_enabled = QCheckBox_custom("enable", objectName="mechanics_absolute_equilibrium_distance_enabled")
        self.set_absolute_equilibrium_distance_enabled.stateChanged.connect(self.set_absolute_equilibrium_distance_enabled_cb)
        glayout.addWidget(self.set_absolute_equilibrium_distance_enabled, idr,0, 1,1, alignment=QtCore.Qt.AlignRight) # w, row, column, rowspan, colspan

        units = QLabel("micron")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.set_absolute_equilibrium_distance_warning_label = HoverWarning("")
        glayout.addWidget(self.set_absolute_equilibrium_distance_warning_label, idr, 4, 1,1) # w, row, column, rowspan, colspan

        self.cell_adhesion_strength_group = QButtonGroup(exclusive=False)
        self.cell_adhesion_strength_group.addButton(self.set_relative_equilibrium_distance_enabled, 0)
        self.cell_adhesion_strength_group.addButton(self.set_absolute_equilibrium_distance_enabled, 1)
        self.cell_adhesion_strength_group.buttonToggled.connect(self.cell_adhesion_strength_group_cb)
        
        #--------------------------------
        # ------ horiz separator -----
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,4) # w, row, column, rowspan, colspan

        label = QLabel("elastic constant")
        # label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.elastic_constant = QLineEdit_color(objectName="mechanics_elastic_constant")
        self.elastic_constant.textChanged.connect(self.cell_def_param_changed)
        self.elastic_constant.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.elastic_constant, idr,2, 1,1) # w, row, column, rowspan, colspan
        self.elastic_constant.setEnabled(True)

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #--
        label = QLabel("attachment rate")
        # label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.attachment_rate = QLineEdit_color(objectName="attachment_rate")
        self.attachment_rate.textChanged.connect(self.cell_def_mechano_rate_changed)
        self.attachment_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.attachment_rate, idr,2, 1,1) # w, row, column, rowspan, colspan
        self.attachment_rate.setEnabled(True)

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.attachment_rate_warning_label = HoverWarning("")
        glayout.addWidget(self.attachment_rate_warning_label, idr, 4, 1,1) # w, row, column, rowspan, colspan

        #--
        label = QLabel("detachment rate")
        # label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.detachment_rate = QLineEdit_color(objectName="detachment_rate")
        self.detachment_rate.textChanged.connect(self.cell_def_mechano_rate_changed)
        self.detachment_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.detachment_rate, idr,2, 1,1) # w, row, column, rowspan, colspan
        self.detachment_rate.setEnabled(True)

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.detachment_rate_warning_label = HoverWarning("")
        glayout.addWidget(self.detachment_rate_warning_label, idr, 4, 1,1) # w, row, column, rowspan, colspan

        #--
        label = QLabel("maximum number of attachments")
        # label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.max_num_attachments = QLineEdit_color(objectName="mechanics_max_num_attachments")
        self.max_num_attachments.textChanged.connect(self.cell_def_param_changed)
        self.max_num_attachments.setValidator(QtGui.QIntValidator(bottom=0))
        glayout.addWidget(self.max_num_attachments, idr,2, 1,1) # w, row, column, rowspan, colspan
        self.max_num_attachments.setEnabled(True)

        #---------
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,4) # w, row, column, rowspan, colspan

        self.reset_mechanics_button = QPushButton("Reset to PhysiCell defaults")
        self.reset_mechanics_button.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        self.reset_mechanics_button.clicked.connect(self.reset_mechanics_cb)
        idr += 1
        glayout.addWidget(self.reset_mechanics_button, idr,0, 1,1) # w, row, column, rowspan, colspan

        #------
        for idx in range(5):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idr += 1
            glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan

        #------
        # vlayout.setVerticalSpacing(10)  # rwh - argh
        mechanics_tab.setLayout(glayout)
        return mechanics_tab

    #--------------------------------------------------------
    def reset_mechanics_cb(self):
        # print("--- reset_mechanics_cb:  self.current_cell_def= ",self.current_cell_def)
        self.new_mechanics_params(self.current_cell_def, True)
        self.tree_item_clicked_cb(self.tree.currentItem(), 0)

    #--------------------------------------------------------
    def create_motility_tab(self):
        motility_tab = QWidget()
        motility_tab.setStyleSheet("background-color: rgb(236,236,236)")
        # motility_tab.setStyleSheet("QLineEdit { background-color: white }")
        glayout = QGridLayout()

        label = QLabel("Phenotype: motility")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)

        #---
        label = QLabel("speed")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # label.setStyleSheet("border: 1px solid black;")
        idr = 0
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.speed = QLineEdit_color(objectName="speed")
        self.speed.textChanged.connect(self.cell_def_param_changed)
        self.speed.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.speed, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("micron/min")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # units.setStyleSheet("border: 1px solid black;")
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("persistence time")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.persistence_time = QLineEdit_color(objectName="persistence_time")
        self.persistence_time.textChanged.connect(self.cell_def_mechano_duration_changed)
        self.persistence_time.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.persistence_time, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        self.persistence_time_warning_label = HoverWarning("")
        glayout.addWidget(self.persistence_time_warning_label, idr, 3, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("migration bias")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.migration_bias = QLineEdit_color(objectName="migration_bias")
        self.migration_bias.textChanged.connect(self.cell_def_param_changed)
        self.migration_bias.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.migration_bias, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        
        #---
        self.motility_enabled = QCheckBox_custom("enable motility", objectName="motility_enabled")
        self.motility_enabled.clicked.connect(self.cell_def_param_changed)
        idr += 1
        glayout.addWidget(self.motility_enabled, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.motility_use_2D = QCheckBox_custom("2D", objectName="motility_use_2D")
        self.motility_use_2D.clicked.connect(self.cell_def_param_changed)
        glayout.addWidget(self.motility_use_2D, idr,1, 1,1) # w, row, column, rowspan, colspan

        #---
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,2) # w, row, column, rowspan, colspan

        label = QLabel("Chemotaxis")
        label.setFixedWidth(200)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet('background-color: orange')
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.chemotaxis_enabled = QCheckBox_custom("enabled")
        self.chemotaxis_enabled.clicked.connect(self.chemotaxis_enabled_cb)
        glayout.addWidget(self.chemotaxis_enabled, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.motility_substrate_dropdown = QComboBox_custom()
        idr += 1
        glayout.addWidget(self.motility_substrate_dropdown, idr,0, 1,1) # w, row, column, rowspan, colspan
        self.motility_substrate_dropdown.currentIndexChanged.connect(self.motility_substrate_changed_cb)  # beware: will be triggered on a ".clear" too

        self.chemotaxis_direction_towards = QRadioButton_custom("towards")
        self.chemotaxis_direction_towards.clicked.connect(self.chemotaxis_direction_cb)

        self.chemotaxis_direction_against = QRadioButton_custom("against")
        self.chemotaxis_direction_against.clicked.connect(self.chemotaxis_direction_cb)

        hbox = QHBoxLayout()
        hbox.addWidget(self.chemotaxis_direction_towards)
        hbox.addWidget(self.chemotaxis_direction_against)
        # glayout.addLayout(hbox, idr,1, 1,1) # w, row, column, rowspan, colspan

        radio_frame = QFrame()
        radio_frame.setStyleSheet("QFrame{ border : 1px solid black; }")
        radio_frame.setLayout(hbox)
        radio_frame.setFixedWidth(170)  # omg
        glayout.addWidget(radio_frame, idr,1, 1,1) # w, row, column, rowspan, colspan

        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,2) # w, row, column, rowspan, colspan

        label = QLabel("Advanced Chemotaxis")
        label.setFixedWidth(200)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet('background-color: orange')
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.advanced_chemotaxis_enabled = QCheckBox_custom("enabled")
        self.advanced_chemotaxis_enabled.clicked.connect(self.advanced_chemotaxis_enabled_cb)
        glayout.addWidget(self.advanced_chemotaxis_enabled, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.normalize_each_gradient = QCheckBox_custom("normalize gradient", objectName="normalize_each_gradient")
        self.normalize_each_gradient.clicked.connect(self.cell_def_param_changed)
        glayout.addWidget(self.normalize_each_gradient, idr,2, 1,1) # w, row, column, rowspan, colspan

        self.motility2_substrate_dropdown = QComboBox_custom()
        idr += 1
        glayout.addWidget(self.motility2_substrate_dropdown, idr,0, 1,1) # w, row, column, rowspan, colspan
        self.motility2_substrate_dropdown.currentIndexChanged.connect(self.motility2_substrate_changed_cb)  # beware: will be triggered on a ".clear" too

        label = QLabel("sensitivity")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.chemo_sensitivity = QLineEdit_color()
        self.chemo_sensitivity.textChanged.connect(self.chemo_sensitivity_changed)
        self.chemo_sensitivity.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.chemo_sensitivity, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---------
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,4) # w, row, column, rowspan, colspan

        self.reset_motility_button = QPushButton("Reset to PhysiCell defaults")
        self.reset_motility_button.setFixedWidth(200)
        self.reset_motility_button.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        self.reset_motility_button.clicked.connect(self.reset_motility_cb)
        idr += 1
        glayout.addWidget(self.reset_motility_button, idr,0, 1,1) # w, row, column, rowspan, colspan

        #------
        for idx in range(8):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idr += 1
            glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan

        #------
        # vlayout.setVerticalSpacing(10)  # rwh - argh
        motility_tab.setLayout(glayout)
        return motility_tab

    #--------------------------------------------------------
    def reset_motility_cb(self):
        # print("--- reset_motility_cb:  self.current_cell_def= ",self.current_cell_def)
        self.new_motility_params(self.current_cell_def)
        self.tree_item_clicked_cb(self.tree.currentItem(), 0)

    #--------------------------------------------------------
    def create_secretion_tab(self):
        secretion_tab = QWidget()
        secretion_tab.setStyleSheet("background-color: rgb(236,236,236)")
        # secretion_tab.setStyleSheet("QLineEdit { background-color: white }")
        glayout = QGridLayout()

        label = QLabel("Phenotype: secretion")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)

        self.secretion_substrate_dropdown = QComboBox_custom()
        idr = 0
        glayout.addWidget(self.secretion_substrate_dropdown, idr,0, 1,1) # w, row, column, rowspan, colspan
        self.secretion_substrate_dropdown.currentIndexChanged.connect(self.secretion_substrate_changed_cb)  # beware: will be triggered on a ".clear" too

        label = QLabel("secretion rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # label.setStyleSheet("border: 1px solid black;")
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.secretion_rate = QLineEdit_color()
        self.secretion_rate.textChanged.connect(self.secretion_rate_changed)
        self.secretion_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.secretion_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # units.setStyleSheet("border: 1px solid black;")
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("target")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # label.setStyleSheet("border: 1px solid black;")
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.secretion_target = QLineEdit_color()
        self.secretion_target.textChanged.connect(self.secretion_target_changed)
        self.secretion_target.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.secretion_target, idr,1, 1,1) # w, row, column, rowspan, colspan

        # units = QLabel("substrate density")
        units = QLabel("sub. density")
        # units.setFixedWidth(self.units_width+5)
        # units.setFixedWidth(110)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # units.setStyleSheet("border: 1px solid black;")
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("uptake rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.uptake_rate = QLineEdit_color()
        self.uptake_rate.textChanged.connect(self.uptake_rate_changed)
        self.uptake_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.uptake_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("net export rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.secretion_net_export_rate = QLineEdit_color()
        self.secretion_net_export_rate.textChanged.connect(self.secretion_net_export_rate_changed)
        self.secretion_net_export_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.secretion_net_export_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("total/min")
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---------
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,4) # w, row, column, rowspan, colspan

        self.reset_secretion_button = QPushButton("Reset to PhysiCell defaults")
        self.reset_secretion_button.setFixedWidth(200)
        self.reset_secretion_button.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        self.reset_secretion_button.clicked.connect(self.reset_secretion_cb)
        idr += 1
        glayout.addWidget(self.reset_secretion_button, idr,0, 1,1) # w, row, column, rowspan, colspan

        #------
        for idx in range(11):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idr += 1
            glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan

        #------
        # vlayout.setVerticalSpacing(10)  # rwh - argh
        secretion_tab.setLayout(glayout)
        return secretion_tab

    #--------------------------------------------------------
    def reset_secretion_cb(self):
        # print("--- reset_secretion_cb:  self.current_cell_def= ",self.current_cell_def)
        self.new_secretion_params(self.current_cell_def)
        self.tree_item_clicked_cb(self.tree.currentItem(), 0)

    #--------------------------------------------------------
    def create_interaction_tab(self):
        interaction_tab = QWidget()
        interaction_tab.setStyleSheet("background-color: rgb(236,236,236)")
        glayout = QGridLayout()

        label = QLabel("Phenotype: interaction")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)

        label = QLabel("apoptotic phagocytosis rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr = 0
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.apoptotic_phagocytosis_rate = QLineEdit_color(objectName="apoptotic_phagocytosis_rate")
        self.apoptotic_phagocytosis_rate.textChanged.connect(self.cell_def_pheno_rate_changed)
        self.apoptotic_phagocytosis_rate.setValidator(QtGui.QDoubleValidator(bottom=0))
        glayout.addWidget(self.apoptotic_phagocytosis_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.apoptotic_phagocytosis_rate_warning_label = HoverWarning("")
        glayout.addWidget(self.apoptotic_phagocytosis_rate_warning_label, idr, 4, 1, 1) # w, row, column, rowspan, colspan
        
        label = QLabel("necrotic phagocytosis rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.necrotic_phagocytosis_rate = QLineEdit_color(objectName="necrotic_phagocytosis_rate")
        self.necrotic_phagocytosis_rate.textChanged.connect(self.cell_def_pheno_rate_changed)
        self.necrotic_phagocytosis_rate.setValidator(QtGui.QDoubleValidator(bottom=0))
        glayout.addWidget(self.necrotic_phagocytosis_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.necrotic_phagocytosis_rate_warning_label = HoverWarning("")
        glayout.addWidget(self.necrotic_phagocytosis_rate_warning_label, idr, 4, 1, 1) # w, row, column, rowspan, colspan

        label = QLabel("other dead phagocytosis rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.other_dead_phagocytosis_rate = QLineEdit_color(objectName="other_dead_phagocytosis_rate")
        self.other_dead_phagocytosis_rate.textChanged.connect(self.cell_def_pheno_rate_changed)
        self.other_dead_phagocytosis_rate.setValidator(QtGui.QDoubleValidator(bottom=0))
        glayout.addWidget(self.other_dead_phagocytosis_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.other_dead_phagocytosis_rate_warning_label = HoverWarning("")
        glayout.addWidget(self.other_dead_phagocytosis_rate_warning_label, idr, 4, 1, 1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("live phagocytosis rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.live_phagocytosis_dropdown = QComboBox_custom()
        glayout.addWidget(self.live_phagocytosis_dropdown, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.live_phagocytosis_dropdown.currentIndexChanged.connect(self.live_phagocytosis_dropdown_changed_cb)  # beware: will be triggered on a ".clear" too

        self.live_phagocytosis_rate = QLineEdit_color()
        self.live_phagocytosis_rate.textChanged.connect(self.live_phagocytosis_rate_changed)
        self.live_phagocytosis_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.live_phagocytosis_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.live_phagocytosis_rate_fast_label = HoverWarning("")
        glayout.addWidget(self.live_phagocytosis_rate_fast_label, idr, 4, 1, 1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("attack rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.attack_rate_dropdown = QComboBox_custom()
        glayout.addWidget(self.attack_rate_dropdown, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.attack_rate_dropdown.currentIndexChanged.connect(self.attack_rate_dropdown_changed_cb)  # beware: will be triggered on a ".clear" too

        self.attack_rate = QLineEdit_custom()
        self.attack_rate.textChanged.connect(self.attack_rate_changed)
        # save this for if/when immogenicity is implemented
        ##############################################################################################
        # if hasattr(self, 'immunogenicity_dropdown'): # then immunogenicity has been implemented    #
        #     validator = AttackRateValidator(self)                                                  #
        # else:                                                                                      #
        #     validator = QtGui.QDoubleValidator(bottom=0.0)                                         #
        ##############################################################################################
        validator = QtGui.QDoubleValidator(bottom=0.0) # no longer want to highlight the box red if rate is too high (just show warning (!) )
        self.attack_rate.setValidator(validator)
        glayout.addWidget(self.attack_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.attack_rate_fast_label = HoverWarning("")
        glayout.addWidget(self.attack_rate_fast_label, idr, 4, 1, 1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("attack damage rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.attack_damage_rate = QLineEdit_color()
        self.attack_damage_rate.textChanged.connect(self.attack_damage_rate_changed)
        self.attack_damage_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.attack_damage_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("attack duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.attack_duration = QLineEdit_color()
        self.attack_duration.textChanged.connect(self.attack_duration_changed)
        self.attack_duration.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.attack_duration , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("fusion rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.fusion_rate_dropdown = QComboBox_custom()
        glayout.addWidget(self.fusion_rate_dropdown, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.fusion_rate_dropdown.currentIndexChanged.connect(self.fusion_rate_dropdown_changed_cb)  # beware: will be triggered on a ".clear" too

        self.fusion_rate = QLineEdit_color()
        self.fusion_rate.textChanged.connect(self.fusion_rate_changed)
        self.fusion_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.fusion_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.fusion_rate_fast_label = HoverWarning("")
        glayout.addWidget(self.fusion_rate_fast_label, idr, 4, 1, 1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("transformation rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.cell_transformation_dropdown = QComboBox_custom()
        glayout.addWidget(self.cell_transformation_dropdown, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.cell_transformation_dropdown.currentIndexChanged.connect(self.cell_transformation_dropdown_changed_cb)  # beware: will be triggered on a ".clear" too

        self.transformation_rate = QLineEdit_color()
        self.transformation_rate.textChanged.connect(self.transformation_rate_changed)
        self.transformation_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.transformation_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        self.transformation_rate_fast_label = HoverWarning("")
        glayout.addWidget(self.transformation_rate_fast_label, idr, 4, 1, 1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("damage rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.damage_rate = QLineEdit_color()
        self.damage_rate.textChanged.connect(self.damage_rate_changed)
        self.damage_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.damage_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("damage repair rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.damage_repair_rate = QLineEdit_color()
        self.damage_repair_rate.textChanged.connect(self.damage_repair_rate_changed)
        self.damage_repair_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.damage_repair_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #------
        # label = QLabel("immunogenicity")
        # label.setFixedWidth(self.label_width)
        # label.setAlignment(QtCore.Qt.AlignRight)
        # idr += 1
        # glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        # self.immunogenicity_dropdown = QComboBox_custom()
        # glayout.addWidget(self.immunogenicity_dropdown, idr,1, 1,1) # w, row, column, rowspan, colspan

        # self.immunogenicity_dropdown.currentIndexChanged.connect(self.immunogenicity_dropdown_changed_cb)  # beware: will be triggered on a ".clear" too

        # self.transformation_rate = QLineEdit_color()
        # self.transformation_rate.textChanged.connect(self.transformation_rate_changed)
        # self.transformation_rate.setValidator(QtGui.QDoubleValidator())
        # glayout.addWidget(self.transformation_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        # units = QLabel(self.default_rate_units)
        # units.setFixedWidth(self.units_width)
        # units.setAlignment(QtCore.Qt.AlignLeft)
        # glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #---------
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,4) # w, row, column, rowspan, colspan

        self.reset_interaction_button = QPushButton("Reset to PhysiCell defaults")
        self.reset_interaction_button.setFixedWidth(200)
        self.reset_interaction_button.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        self.reset_interaction_button.clicked.connect(self.reset_interaction_cb)
        idr += 1
        glayout.addWidget(self.reset_interaction_button, idr,0, 1,1) # w, row, column, rowspan, colspan

        #------
        for idx in range(7):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idr += 1
            glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan

        #------
        # vlayout.setVerticalSpacing(10)  # rwh - argh
        interaction_tab.setLayout(glayout)

        return interaction_tab

    #--------------------------------------------------------
    def reset_interaction_cb(self):
        # print("--- reset_interaction_cb:  self.current_cell_def= ",self.current_cell_def)
        self.new_interaction_params(self.current_cell_def, True)
        self.tree_item_clicked_cb(self.tree.currentItem(), 0)

    #--------------------------------------------------------
    def cell_adhesion_affinity_changed(self,text):
        # print("cell_adhesion_affinity_changed:  text=",text)
        self.param_d[self.current_cell_def]['cell_adhesion_affinity'][self.cell_adhesion_affinity_celltype] = text

    #--------------------------------------------------------
    def set_relative_equilibrium_distance_cb(self, text):
        if self.sender().validator().validate(text,0)[0]==QValidator.Acceptable and float(text) > 2.0:
            self.set_relative_equilibrium_distance_warning_label.show_icon()
        else:
            self.set_relative_equilibrium_distance_warning_label.hide_icon()
        self.cell_def_param_changed(text)
    #--------------------------------------------------------
    def set_relative_equilibrium_distance_enabled_cb(self, bval):
        self.set_relative_equilibrium_distance.setEnabled(bval)
        self.cell_def_param_changed(bval)
    #--------------------------------------------------------
    def set_absolute_equilibrium_distance_cb(self, text):
        show_warning = False
        if self.sender().validator().validate(text,0)[0]==QValidator.Acceptable:
            d = float(text)
            V = float(self.param_d[self.current_cell_def]['volume_total'])
            r = (3*V/(4*np.pi))**(1/3)
            show_warning = d > 2*r
        
        if show_warning:
            self.set_absolute_equilibrium_distance_warning_label.show_icon()
            msg = f"""
            WARNING: The distance is greater than twice the radius of the cell.
            PhysiCell will reduce this distance to twice the cell radius.
            May as well decrease the distance to {2*r:.2f} or increase the total volume to {4*np.pi*(d**3)/3:.0f}.
            """
            self.set_absolute_equilibrium_distance_warning_label.setHoverText(msg)
        else:
            self.set_absolute_equilibrium_distance_warning_label.hide_icon()
        self.cell_def_param_changed(text)
    #--------------------------------------------------------
    def set_absolute_equilibrium_distance_enabled_cb(self, bval):
        self.set_absolute_equilibrium_distance.setEnabled(bval)
        self.cell_def_param_changed(bval)
    #--------------------------------------------------------
    def cell_adhesion_strength_group_cb(self, checkbox, bval):
        idx = self.cell_adhesion_strength_group.id(checkbox)
        other_idx = (idx+1) % 2
        if bval == True:
            self.cell_adhesion_strength_group.button(other_idx).setChecked(False)
            self.cell_cell_adhesion_strength.setEnabled(False)
        elif self.cell_adhesion_strength_group.button(other_idx).isChecked() == False:
            # if both are False, then activate cell_cell_adhesion_strength (it should be impossible for the other to be True here, but just in case we check that it is False)
            self.cell_cell_adhesion_strength.setEnabled(True)

    #--------------------------------------------------------
    def live_phagocytosis_rate_changed(self,text):
        celltype_name = self.live_phagocytosis_dropdown.currentText()
        self.param_d[self.current_cell_def]['live_phagocytosis_rate'][celltype_name] = text
        self.check_rate_too_fast(text, self.live_phagocytosis_rate_fast_label)
    #--------------------------------------------------------
    def attack_rate_changed(self,text):
        celltype_name = self.attack_rate_dropdown.currentText()
        self.param_d[self.current_cell_def]['attack_rate'][celltype_name] = text

        if self.attack_rate.validator.validate(text, 0)[0] == QValidator.Intermediate:
            return
        
        mech_dt_str = self.xml_creator.config_tab.mechanics_dt.text()
        if self.is_dt_set(self.attack_rate_fast_label, "mechanics_dt", mech_dt_str) == False:
            return
        
        mech_dt = float(mech_dt_str)
        attack_rate = float(text) 
        max_val = 1/mech_dt
        attack_prob = attack_rate * mech_dt
        if "immunogenicity" in self.param_d[self.current_cell_def].keys():
            immunogenicity = float(self.param_d[self.current_cell_def]["immunogenicity"][self.attack_rate_dropdown.currentText()])
            attack_prob *= immunogenicity
            max_val /= immunogenicity
            denom = "(immunogenicity * mechanics_dt)"
        else:  
            denom = "mechanics_dt"
        if attack_prob > 1:
            self.attack_rate_fast_label.show_icon()
            self.attack_rate_fast_label.setHoverText(f"WARNING: An attack rate > 1/{denom} is instantaneous. May as well set to {max_val}.")
        else:
            self.attack_rate_fast_label.hide_icon()
    #--------------------------------------------------------
    def attack_damage_rate_changed(self,text):
        self.param_d[self.current_cell_def]['attack_damage_rate'] = text
    #--------------------------------------------------------
    def attack_duration_changed(self,text):
        self.param_d[self.current_cell_def]['attack_duration'] = text
    #--------------------------------------------------------
    def fusion_rate_changed(self,text):
        celltype_name = self.fusion_rate_dropdown.currentText()
        self.param_d[self.current_cell_def]['fusion_rate'][celltype_name] = text
        self.check_rate_too_fast(text, self.fusion_rate_fast_label)
    #--------------------------------------------------------
    def transformation_rate_changed(self,text):
        celltype_name = self.cell_transformation_dropdown.currentText()
        self.param_d[self.current_cell_def]['transformation_rate'][celltype_name] = text
        self.check_rate_too_fast(text, self.transformation_rate_fast_label, time_step="phenotype_dt")
    #--------------------------------------------------------
    def damage_rate_changed(self,text):
        self.param_d[self.current_cell_def]['damage_rate'] = text
    #--------------------------------------------------------
    def damage_repair_rate_changed(self,text):
        self.param_d[self.current_cell_def]['damage_repair_rate'] = text

    #--------------------------------------------------------
    # def immunogenicity_changed(self,text):
    #     # print("transformation_rate_changed:  text=",text)
    #     celltype_name = self.immunogenicity_dropdown.currentText()
    #     # self.param_d[self.current_cell_def]['transformation_rate'][self.transformation_rate_celltype] = text
    #     self.param_d[self.current_cell_def]['transformation_rate'][celltype_name] = text


    #--------------------------------------------------------
    # def create_molecular_tab(self):
    #     label = QLabel("Phenotype: molecular")
    #     label.setStyleSheet("background-color: orange")
    #     label.setAlignment(QtCore.Qt.AlignCenter)
    #     self.vbox.addWidget(label)


    def choose_bnd_file(self):
        file , check = QFileDialog.getOpenFileName(None, "Please select a MaBoSS BND file",
                                               "", "MaBoSS BND Files (*.bnd)")
        if check:
            self.physiboss_bnd_file.setText(os.path.relpath(file, os.getcwd()))
            
    def choose_cfg_file(self):
        file , check = QFileDialog.getOpenFileName(None, "Please select a MaBoSS CFG file",
                                               "", "MaBoSS CFG Files (*.cfg)")
        if check:
            self.physiboss_cfg_file.setText(os.path.relpath(file, os.getcwd()))

    def physiboss_bnd_filename_changed(self, text):
        if self.param_d[self.current_cell_def]["intracellular"] is not None:
            self.param_d[self.current_cell_def]["intracellular"]['bnd_filename'] = text
            self.physiboss_update_list_nodes()
    
    def physiboss_cfg_filename_changed(self, text):
        if self.param_d[self.current_cell_def]["intracellular"] is not None:
            self.param_d[self.current_cell_def]["intracellular"]['cfg_filename'] = text
            self.physiboss_update_list_parameters()

    def physiboss_update_list_signals(self):

        if self.current_cell_def == None:
            return
        if self.param_d[self.current_cell_def]["intracellular"] is not None:

            self.physiboss_signals = []
            for substrate in self.substrate_list:
                self.physiboss_signals.append(substrate)

            for substrate in self.substrate_list:
                self.physiboss_signals.append("intracellular " + substrate)
        
            for substrate in self.substrate_list:
                self.physiboss_signals.append(substrate + " gradient")
        
            self.physiboss_signals += ["pressure", "volume"]

            for celltype in self.celltypes_list:
                self.physiboss_signals.append("contact with " + celltype)

            for custom_data in self.master_custom_var_d.keys():
                self.physiboss_signals.append("custom:" + custom_data)

            self.physiboss_signals += ["contact with live cell", "contact with dead cell", "contact with basement membrane", "damage", "dead", "total attack time", "time", "damage delivered"]

            for i, (name, _, _, _, _, _, _, _) in enumerate(self.physiboss_inputs):
                name.currentIndexChanged.disconnect()
                name.clear()
                for signal in self.physiboss_signals:
                    name.addItem(signal)
            
                if (self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["name"] is not None
                    and self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["name"] in self.physiboss_signals
                ):
                    name.setCurrentIndex(self.physiboss_signals.index(self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["name"]))
                else:
                    name.setCurrentIndex(-1)
        
                name.currentIndexChanged.connect(lambda index, i=i: self.physiboss_inputs_signal_changed(i, index))

    def physiboss_update_list_behaviours(self):

        if self.current_cell_def == None:
            return
        if self.param_d[self.current_cell_def]["intracellular"] is not None:

            self.physiboss_behaviours = []
            for substrate in self.substrate_list:
                self.physiboss_behaviours.append(substrate + " secretion")

            for substrate in self.substrate_list:
                self.physiboss_behaviours.append(substrate + " secretion target")
        
            for substrate in self.substrate_list:
                self.physiboss_behaviours.append(substrate + " uptake")

            for substrate in self.substrate_list:
                self.physiboss_behaviours.append("chemotactic response to " + substrate)

            for substrate in self.substrate_list:
                self.physiboss_behaviours.append(substrate + " export")

            for custom_data in self.master_custom_var_d.keys():
                self.physiboss_behaviours.append("custom:" + custom_data)
        
            self.physiboss_behaviours += [
                "cycle entry", "exit from cycle phase 0", "exit from cycle phase 1", "exit from cycle phase 2", "exit from cycle phase 3", "exit from cycle phase 4", "exit from cycle phase 5",
                "apoptosis", "necrosis", "migration speed", "migration bias", "migration persistence time", "chemotactic response to oxygen", 
                "cell-cell adhesion", "cell-cell adhesion elastic constant"
            ]

            for celltype in self.celltypes_list:
                self.physiboss_behaviours.append("adhesive affinity to " + celltype)

            self.physiboss_behaviours += ["relative maximum adhesion distance", "cell-cell repulsion", "cell-BM adhesion", "cell-BM repulsion", "phagocytose apoptotic cell", "phagocytose necrotic cell", "phagocytose other dead cell"]

            for celltype in self.celltypes_list:
                self.physiboss_behaviours.append("phagocytose " + celltype)

            for celltype in self.celltypes_list:
                self.physiboss_behaviours.append("attack " + celltype)

            for celltype in self.celltypes_list:
                self.physiboss_behaviours.append("fuse " + celltype)

            for celltype in self.celltypes_list:
                self.physiboss_behaviours.append("transform to " + celltype)


            for i, (name, _, _, _, _, _, _, _) in enumerate(self.physiboss_outputs):
                name.currentIndexChanged.disconnect()
                name.clear()
                for behaviour in self.physiboss_behaviours:
                    name.addItem(behaviour)

                if (self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["name"] is not None
                    and self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["name"] in self.physiboss_behaviours
                ):
                    name.setCurrentIndex(self.physiboss_behaviours.index(self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["name"]))
                else:
                    name.setCurrentIndex(-1)

                name.currentIndexChanged.connect(lambda index, i=i: self.physiboss_outputs_behaviour_changed(i, index))

    def physiboss_update_list_nodes(self):

        t_intracellular = self.param_d[self.current_cell_def]["intracellular"]
        
        if t_intracellular is not None:

            # Here I started by looking at both the bnd and the cfg
            if (
                t_intracellular is not None 
                and "bnd_filename" in t_intracellular.keys() 
                and t_intracellular['bnd_filename'] is not None 
                and len(t_intracellular['bnd_filename']) > 0
                and os.path.exists(os.path.join(os.getcwd(), t_intracellular["bnd_filename"])) 
                ):
                list_nodes = []
                with open(os.path.join(os.getcwd(), t_intracellular["bnd_filename"]), 'r') as bnd_file:
                    list_nodes = [node.split(" ")[1].strip() for node in bnd_file.readlines() if node.strip().lower().startswith("node")]
            
                if len(list_nodes) > 0:
                    self.param_d[self.current_cell_def]["intracellular"]["list_nodes"] = list_nodes

                for i, (node, _, _, _) in enumerate(self.physiboss_initial_states):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_initial_value_node_changed(i, index))

                    if (self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i]["node"] is not None
                        and self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i]["node"] in list_nodes
                    ):
                        node.setCurrentIndex(list_nodes.index(self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i]["node"]))
                    elif self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i]["node"] == "" or self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i]["node"] not in list_nodes:
                        node.setCurrentIndex(0)
                        self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i]["node"] = list_nodes[0]
                    else:
                        self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i]["node"] = ""
                        node.setCurrentIndex(-1)

                for i, (node, _, _, _) in enumerate(self.physiboss_mutants):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_mutants_node_changed(i, index))

                    if (self.param_d[self.current_cell_def]["intracellular"]["mutants"][i]["node"] is not None
                        and self.param_d[self.current_cell_def]["intracellular"]["mutants"][i]["node"] in list_nodes
                    ):
                        node.setCurrentIndex(list_nodes.index(self.param_d[self.current_cell_def]["intracellular"]["mutants"][i]["node"]))
                    elif self.param_d[self.current_cell_def]["intracellular"]["mutants"][i]["node"] == "" or self.param_d[self.current_cell_def]["intracellular"]["mutants"][i]["node"] not in list_nodes:
                        node.setCurrentIndex(0)
                        self.param_d[self.current_cell_def]["intracellular"]["mutants"][i]["node"] = list_nodes[0]
                    else:
                        self.param_d[self.current_cell_def]["intracellular"]["mutants"][i]["node"] = ""
                        node.setCurrentIndex(-1)


                for i, (_, node, _, _, _, _, _, _) in enumerate(self.physiboss_inputs):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_inputs_node_changed(i, index))

                    if (self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["node"] is not None
                        and self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["node"] in list_nodes
                    ):
                        node.setCurrentIndex(list_nodes.index(self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["node"]))
                    elif self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["node"] == "" or self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["node"] not in list_nodes:
                        node.setCurrentIndex(0)
                        self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["node"] = list_nodes[0]
                    else:
                        self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["node"] = ""
                        node.setCurrentIndex(-1)
        
                for i, (_, node, _, _, _, _, _, _) in enumerate(self.physiboss_outputs):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_outputs_node_changed(i, index))

                    if (self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["node"] is not None
                        and self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["node"] in list_nodes
                    ):
                        node.setCurrentIndex(list_nodes.index(self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["node"]))
                    elif self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["node"] == "" or self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["node"] not in list_nodes:
                        node.setCurrentIndex(0)
                        self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["node"] = list_nodes[0]
                    else:
                        self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["node"] = ""
                        node.setCurrentIndex(-1)
          
    def physiboss_update_list_parameters(self):
        
        t_intracellular = self.param_d[self.current_cell_def]["intracellular"]        
        if t_intracellular is not None:
            # Here I started by looking at both the bnd and the cfg
            if (
                t_intracellular is not None 
                and "cfg_filename" in t_intracellular.keys() 
                and t_intracellular['cfg_filename'] is not None \
                and len(t_intracellular['cfg_filename']) > 0
                and os.path.exists(os.path.join(os.getcwd(), t_intracellular["cfg_filename"])) 
                # and t_intracellular["cfg_filename"] and and os.path.exists(t_intracellular["cfg_filename"])
                ):
                list_parameters = []
                # list_internal_nodes = []
                with open(os.path.join(os.getcwd(), t_intracellular["cfg_filename"]), 'r') as cfg_file:
                    for line in cfg_file.readlines():
                        if line.strip().startswith("$"):
                            list_parameters.append(line.split("=")[0].strip())
                            
                        # elif ".is_internal" in line:
                        #     tokens = line.split("=")
                        #     value = tokens[1].strip()[:-1].lower() in ["1", "true"]
                        #     node = tokens[0].strip().replace(".is_internal", "")
                        #     if value:
                        #         list_internal_nodes.append(node)
                
                # list_output_nodes = list(set(self.param_d[self.current_cell_def]["intracellular"]["list_nodes"]).difference(set(list_internal_nodes)))
                if len(list_parameters) > 0:
                    self.param_d[self.current_cell_def]["intracellular"]["list_parameters"] = list_parameters
                
                for i, (param, _, _, _) in enumerate(self.physiboss_parameters):
                    param.currentIndexChanged.disconnect()
                    param.clear()
                    for name in list_parameters:
                        param.addItem(name)
                    param.currentIndexChanged.connect(lambda index, i=i: self.physiboss_parameters_node_changed(i, index))

                    if (self.param_d[self.current_cell_def]["intracellular"]["parameters"][i]["name"] is not None
                        and self.param_d[self.current_cell_def]["intracellular"]["parameters"][i]["name"] in list_parameters
                    ):
                        param.setCurrentIndex(list_parameters.index(self.param_d[self.current_cell_def]["intracellular"]["parameters"][i]["name"]))
                    elif self.param_d[self.current_cell_def]["intracellular"]["parameters"][i]["name"] == "" or self.param_d[self.current_cell_def]["intracellular"]["parameters"][i]["name"] not in list_parameters:
                        param.setCurrentIndex(0)
                        self.param_d[self.current_cell_def]["intracellular"]["parameters"][i]["name"] = list_parameters[0]
                    else:
                        self.param_d[self.current_cell_def]["intracellular"]["parameters"][i]["name"] = ""
                        param.setCurrentIndex(-1)

    def physiboss_time_step_changed(self, text):
        if self.param_d[self.current_cell_def]["intracellular"] is not None:
            self.param_d[self.current_cell_def]["intracellular"]['time_step'] = text
    
    def physiboss_scaling_changed(self, text):
        if self.param_d[self.current_cell_def]["intracellular"] is not None:
            self.param_d[self.current_cell_def]["intracellular"]['scaling'] = text
    
    def physiboss_time_stochasticity_changed(self, text):
        if self.param_d[self.current_cell_def]["intracellular"] is not None:
            self.param_d[self.current_cell_def]["intracellular"]['time_stochasticity'] = text
    
    def physiboss_starttime_changed(self, text):
        if self.param_d[self.current_cell_def]["intracellular"] is not None:
            self.param_d[self.current_cell_def]["intracellular"]['start_time'] = text
    
    def physiboss_clicked_add_initial_value(self):
        self.physiboss_add_initial_values()
        self.param_d[self.current_cell_def]["intracellular"]["initial_values"].append({
            'node': self.param_d[self.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.param_d[self.current_cell_def]["intracellular"].keys() else "",
            'value': "1.0"
        })

    def physiboss_add_initial_values(self):

        initial_states_editor = QHBoxLayout()
        initial_states_dropdown = QComboBox_custom()
        initial_states_dropdown.setFixedWidth(150)
        if "list_nodes" in self.param_d[self.current_cell_def]["intracellular"]:
            for node in self.param_d[self.current_cell_def]["intracellular"]["list_nodes"]:
                initial_states_dropdown.addItem(node)
        initial_states_value = QLineEdit("1.0")
        initial_states_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
        initial_states_remove.setStyleSheet("QPushButton { color: black }")

        id = len(self.physiboss_initial_states)
        initial_states_dropdown.currentIndexChanged.connect(lambda index, id=id: self.physiboss_initial_value_node_changed(id, index))
        initial_states_value.textChanged.connect(lambda text, id=id: self.physiboss_initial_value_value_changed(id, text))
        initial_states_remove.clicked.connect(lambda _, id=id: self.physiboss_clicked_remove_initial_values(id))

        initial_states_editor.addWidget(initial_states_dropdown)
        initial_states_editor.addWidget(initial_states_value)
        initial_states_editor.addWidget(initial_states_remove)

        self.physiboss_initial_states_layout.addLayout(initial_states_editor)
        self.physiboss_initial_states.append((initial_states_dropdown, initial_states_value, initial_states_remove, initial_states_editor))

    def physiboss_clicked_remove_initial_values(self, i):
        self.physiboss_remove_initial_values(i)
        del self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i]

    def physiboss_remove_initial_values(self, id):
        self.physiboss_initial_states[id][0].currentIndexChanged.disconnect()
        self.physiboss_initial_states[id][0].deleteLater()
        self.physiboss_initial_states[id][1].textChanged.disconnect()
        self.physiboss_initial_states[id][1].deleteLater()
        self.physiboss_initial_states[id][2].clicked.disconnect()
        self.physiboss_initial_states[id][2].deleteLater()
        self.physiboss_initial_states[id][3].deleteLater()
        del self.physiboss_initial_states[id]
        
        # Here we should remap the clicked method to have the proper id
        for i, initial_state in enumerate(self.physiboss_initial_states):
            node, value, button, _ = initial_state
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_initial_value_node_changed(i, index))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text, i=i: self.physiboss_initial_value_value_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.physiboss_clicked_remove_initial_values(i))

    def physiboss_clear_initial_values(self):
        for i, _ in reversed(list(enumerate(self.physiboss_initial_states))):
            self.physiboss_remove_initial_values(i)
    
    def physiboss_initial_value_node_changed(self, i, index):
        if index >= 0:
            self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i]['node'] = self.param_d[self.current_cell_def]["intracellular"]["list_nodes"][index]

    def physiboss_initial_value_value_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i]['value'] = text
    
    def physiboss_clicked_add_mutant(self):
        self.physiboss_add_mutant()
        self.param_d[self.current_cell_def]["intracellular"]["mutants"].append({
            'node': self.param_d[self.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.param_d[self.current_cell_def]["intracellular"].keys() else "",
            'value': "0",
        })

    def physiboss_add_mutant(self):

        mutants_editor = QHBoxLayout()        
        
        mutants_node_dropdown = QComboBox_custom()
        mutants_node_dropdown.setFixedWidth(150)
        if "list_nodes" in self.param_d[self.current_cell_def]["intracellular"]:
            for node in self.param_d[self.current_cell_def]["intracellular"]["list_nodes"]:
                mutants_node_dropdown.addItem(node)
        
        mutants_value = QLineEdit("0")
        mutants_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
        id = len(self.physiboss_mutants)
        mutants_node_dropdown.currentIndexChanged.connect(lambda index, id=id: self.physiboss_mutants_node_changed(id, index))
        mutants_value.textChanged.connect(lambda text, id=id: self.physiboss_mutants_value_changed(id, text))
        mutants_remove.clicked.connect(lambda _, id=id: self.physiboss_clicked_remove_mutant(id))

        mutants_editor.addWidget(mutants_node_dropdown)
        mutants_editor.addWidget(mutants_value)
        mutants_editor.addWidget(mutants_remove)
        self.physiboss_mutants_layout.addLayout(mutants_editor)
        self.physiboss_mutants.append((mutants_node_dropdown, mutants_value, mutants_remove, mutants_editor))

    def physiboss_clicked_remove_mutant(self, i):
        self.physiboss_remove_mutant(i)
        del self.param_d[self.current_cell_def]["intracellular"]["mutants"][i]

    def physiboss_remove_mutant(self, id):
        self.physiboss_mutants[id][0].currentIndexChanged.disconnect()
        self.physiboss_mutants[id][0].deleteLater()
        self.physiboss_mutants[id][1].textChanged.disconnect()
        self.physiboss_mutants[id][1].deleteLater()
        self.physiboss_mutants[id][2].clicked.disconnect()
        self.physiboss_mutants[id][2].deleteLater()
        self.physiboss_mutants[id][3].deleteLater()
        del self.physiboss_mutants[id]
      
        # Here we should remap the clicked method to have the proper id
        for i, mutant in enumerate(self.physiboss_mutants):
            name, value, button, _ = mutant
            name.currentIndexChanged.disconnect()
            name.currentIndexChanged.connect(lambda index, i=i: self.physiboss_mutants_node_changed(i, index))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text, i=i: self.physiboss_mutants_value_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.physiboss_clicked_remove_mutant(i))

    def physiboss_clear_mutants(self):
        for i, _ in reversed(list(enumerate(self.physiboss_mutants))):
            self.physiboss_remove_mutant(i)
    
    def physiboss_mutants_node_changed(self, i, index):
        if index >= 0:
            self.param_d[self.current_cell_def]["intracellular"]["mutants"][i]["node"] = self.param_d[self.current_cell_def]["intracellular"]["list_nodes"][index]

    def physiboss_mutants_value_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["mutants"][i]["value"] = text

    def physiboss_clicked_add_parameter(self):
        self.physiboss_add_parameter()
        self.param_d[self.current_cell_def]["intracellular"]["parameters"].append({
            'name': self.param_d[self.current_cell_def]["intracellular"]["list_parameters"][0] if "list_nodes" in self.param_d[self.current_cell_def]["intracellular"].keys() else "",
            'value': "1.0"
        })

    def physiboss_add_parameter(self):

        parameters_editor = QHBoxLayout()
        parameters_dropdown = QComboBox_custom()
        parameters_dropdown.setFixedWidth(150)
        if "list_parameters" in self.param_d[self.current_cell_def]["intracellular"]:
            for parameter in self.param_d[self.current_cell_def]["intracellular"]["list_parameters"]:
                parameters_dropdown.addItem(parameter)
        parameters_value = QLineEdit("1.0")
        parameters_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
       
        id = len(self.physiboss_parameters)
        parameters_dropdown.currentIndexChanged.connect(lambda index, id=id: self.physiboss_parameters_node_changed(id, index))
        parameters_value.textChanged.connect(lambda text, id=id: self.physiboss_parameters_value_changed(id, text))
        parameters_remove.clicked.connect(lambda _, id=id: self.physiboss_clicked_remove_parameter(id))

        parameters_editor.addWidget(parameters_dropdown)
        parameters_editor.addWidget(parameters_value)
        parameters_editor.addWidget(parameters_remove)
        self.physiboss_parameters_layout.addLayout(parameters_editor)
        self.physiboss_parameters.append((parameters_dropdown, parameters_value, parameters_remove, parameters_editor))

    def physiboss_clicked_remove_parameter(self, i):
        self.physiboss_remove_parameter(i)
        del self.param_d[self.current_cell_def]["intracellular"]["parameters"][i]

    def physiboss_remove_parameter(self, id):
        self.physiboss_parameters[id][0].currentIndexChanged.disconnect()
        self.physiboss_parameters[id][0].deleteLater()
        self.physiboss_parameters[id][1].textChanged.disconnect()
        self.physiboss_parameters[id][1].deleteLater()
        self.physiboss_parameters[id][2].clicked.disconnect()
        self.physiboss_parameters[id][2].deleteLater()
        self.physiboss_parameters[id][3].deleteLater()
        del self.physiboss_parameters[id]

        # Here we should remap the clicked method to have the proper id
        for i, parameter in enumerate(self.physiboss_parameters):
            name, value, button, _ = parameter
            name.currentIndexChanged.disconnect()
            name.currentIndexChanged.connect(lambda index, i=i: self.physiboss_parameters_node_changed(i, index))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text, i=i: self.physiboss_parameters_value_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.physiboss_clicked_remove_parameter(i))
        
    def physiboss_clear_parameters(self):
        for i, _ in reversed(list(enumerate(self.physiboss_parameters))):
            self.physiboss_remove_parameter(i)

    def physiboss_parameters_node_changed(self, i, index):
        if index >= 0:
            self.param_d[self.current_cell_def]["intracellular"]["parameters"][i]["name"] = self.param_d[self.current_cell_def]["intracellular"]["list_parameters"][index]

    def physiboss_parameters_value_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["parameters"][i]["value"] = text
    
    def physiboss_clicked_add_input(self):
        self.physiboss_add_input()
        self.param_d[self.current_cell_def]["intracellular"]["inputs"].append({
            'name': self.physiboss_signals[0],
            'node': self.param_d[self.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.param_d[self.current_cell_def]["intracellular"].keys() else "",
            'action': 'activation',
            'threshold': "1.0",
            'inact_threshold': "1.0",
            'smoothing': "0"
        })

    def physiboss_add_input(self):

        inputs_editor = QHBoxLayout()

        inputs_signal_dropdown = QComboBox_custom()

        for signal in self.physiboss_signals:
            inputs_signal_dropdown.addItem(signal)
        
        inputs_node_dropdown = QComboBox_custom()

        if "list_nodes" in self.param_d[self.current_cell_def]["intracellular"]:
            for node in self.param_d[self.current_cell_def]["intracellular"]["list_nodes"]:
                inputs_node_dropdown.addItem(node)
        
        inputs_action = QComboBox_custom()

        inputs_action.addItem("activation")
        inputs_action.addItem("inhibition")

        inputs_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)

        id = len(self.physiboss_inputs)
        inputs_node_dropdown.currentIndexChanged.connect(lambda index, id=id: self.physiboss_inputs_node_changed(id, index))
        inputs_signal_dropdown.currentIndexChanged.connect(lambda text, id=id: self.physiboss_inputs_signal_changed(id, text))
        inputs_action.currentIndexChanged.connect(lambda index, id=id: self.physiboss_inputs_action_changed(id, index))
        inputs_remove.clicked.connect(lambda _, id=id: self.physiboss_clicked_remove_input(id))

        inputs_editor.addWidget(inputs_signal_dropdown)
        inputs_editor.setStretch(0, 1)
        inputs_editor.addWidget(inputs_action)
        inputs_editor.setStretch(1, 1)
        inputs_editor.addWidget(inputs_node_dropdown)
        inputs_editor.setStretch(2, 1)
        
        inputs_threshold = QLineEdit("1.0")
        inputs_inact_threshold = QLineEdit("1.0")
        inputs_smoothing = QLineEdit("0")
        inputs_threshold.textChanged.connect(lambda text, id=id: self.physiboss_inputs_threshold_changed(id, text))
        inputs_inact_threshold.textChanged.connect(lambda text, id=id: self.physiboss_inputs_inact_threshold_changed(id, text))
        inputs_smoothing.textChanged.connect(lambda text, id=id: self.physiboss_inputs_smoothing_changed(id, text))
        
        inputs_editor.addWidget(inputs_threshold)
        inputs_threshold.setFixedWidth(70)
        inputs_editor.addWidget(inputs_inact_threshold)
        inputs_inact_threshold.setFixedWidth(70)
        inputs_editor.addWidget(inputs_smoothing)
        inputs_smoothing.setFixedWidth(70)


        inputs_remove.setFixedWidth(30)
        inputs_editor.addWidget(inputs_remove)


        self.physiboss_inputs_layout.addLayout(inputs_editor)
        self.physiboss_inputs.append((inputs_signal_dropdown, inputs_node_dropdown, inputs_action, inputs_threshold, inputs_inact_threshold, inputs_smoothing, inputs_remove, inputs_editor))#, inputs_editor_2))
    
    def physiboss_inputs_signal_changed(self, i, index):
        if index >= 0:
            self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["name"] = self.physiboss_signals[index]
        
    def physiboss_inputs_node_changed(self, i, index):
        if index >= 0:
            self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["node"] = self.param_d[self.current_cell_def]["intracellular"]["list_nodes"][index]
        
    def physiboss_inputs_action_changed(self, i, index):
        self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["action"] = "activation" if index == 0 else "inhibition"

    def physiboss_inputs_threshold_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["threshold"] = text

    def physiboss_inputs_inact_threshold_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["inact_threshold"] = text

    def physiboss_inputs_smoothing_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["smoothing"] = text

    def physiboss_clicked_remove_input(self, i):
        self.physiboss_remove_input(i)
        del self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]

    def physiboss_remove_input(self, id):
        self.physiboss_inputs[id][0].currentIndexChanged.disconnect()
        self.physiboss_inputs[id][0].deleteLater()
        self.physiboss_inputs[id][1].currentIndexChanged.disconnect()
        self.physiboss_inputs[id][1].deleteLater()
        self.physiboss_inputs[id][2].currentIndexChanged.disconnect()
        self.physiboss_inputs[id][2].deleteLater()
        self.physiboss_inputs[id][3].textChanged.disconnect()
        self.physiboss_inputs[id][3].deleteLater()
        self.physiboss_inputs[id][4].textChanged.disconnect()
        self.physiboss_inputs[id][4].deleteLater()
        self.physiboss_inputs[id][5].textChanged.disconnect()
        self.physiboss_inputs[id][5].deleteLater()
        self.physiboss_inputs[id][6].clicked.disconnect()
        self.physiboss_inputs[id][6].deleteLater()
        del self.physiboss_inputs[id]

        # Here we should remap the clicked method to have the proper id
        for i, input in enumerate(self.physiboss_inputs):
            signal, node, action, threshold, inact_threshold, smoothing, button, _ = input
            signal.currentIndexChanged.disconnect()
            signal.currentIndexChanged.connect(lambda index, i=i: self.physiboss_inputs_signal_changed(i, index))
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_inputs_node_changed(i, index))
            action.currentIndexChanged.disconnect()
            action.currentIndexChanged.connect(lambda index, i=i: self.physiboss_inputs_action_changed(i, index))
            threshold.textChanged.disconnect()
            threshold.textChanged.connect(lambda text, i=i: self.physiboss_inputs_threshold_changed(i, text))
            inact_threshold.textChanged.disconnect()
            inact_threshold.textChanged.connect(lambda text, i=i: self.physiboss_inputs_inact_threshold_changed(i, text))
            smoothing.textChanged.disconnect()
            smoothing.textChanged.connect(lambda text, i=i: self.physiboss_inputs_smoothing_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.physiboss_clicked_remove_input(i))
        
    def physiboss_clear_inputs(self):
        for i, _ in reversed(list(enumerate(self.physiboss_inputs))):
            self.physiboss_remove_input(i)

    def physiboss_clicked_add_output(self):
        self.physiboss_add_output()
        self.param_d[self.current_cell_def]["intracellular"]["outputs"].append({
            'name': self.physiboss_behaviours[0],
            'node': self.param_d[self.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.param_d[self.current_cell_def]["intracellular"].keys() else "",
            'action': 'activation',
            'value': "1.0",
            'basal_value': "0.0",
            'smoothing': "0"
        })

    def physiboss_add_output(self):

        outputs_editor = QHBoxLayout()
        outputs_behaviour_dropdown = QComboBox_custom()

        for behaviour in self.physiboss_behaviours:
            outputs_behaviour_dropdown.addItem(behaviour)
        
        outputs_node_dropdown = QComboBox_custom()

        if "list_nodes" in self.param_d[self.current_cell_def]["intracellular"]:
            for node in self.param_d[self.current_cell_def]["intracellular"]["list_nodes"]:
                outputs_node_dropdown.addItem(node)
        
        outputs_action = QComboBox_custom()

        outputs_action.addItem("activation")
        outputs_action.addItem("inhibition")
        outputs_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
        outputs_remove.setFixedWidth(30)


        id = len(self.physiboss_outputs)
        outputs_node_dropdown.currentIndexChanged.connect(lambda index, id=id: self.physiboss_outputs_node_changed(id, index))
        outputs_behaviour_dropdown.currentIndexChanged.connect(lambda text, id=id: self.physiboss_outputs_behaviour_changed(id, text))
        outputs_action.currentIndexChanged.connect(lambda index, id=id: self.physiboss_outputs_action_changed(id, index))
        outputs_remove.clicked.connect(lambda _, id=id: self.physiboss_clicked_remove_output(id))

        outputs_editor.addWidget(outputs_node_dropdown)
        outputs_editor.setStretch(0, 1)
        outputs_editor.addWidget(outputs_action)
        outputs_editor.setStretch(1, 1)
        outputs_editor.addWidget(outputs_behaviour_dropdown)
        outputs_editor.setStretch(2, 1)
        
        outputs_value = QLineEdit("1.0")
        outputs_basal_value = QLineEdit("0.0")
        outputs_smoothing = QLineEdit("0")        
        outputs_value.textChanged.connect(lambda text, id=id: self.physiboss_outputs_value_changed(id, text))
        outputs_basal_value.textChanged.connect(lambda text, id=id: self.physiboss_outputs_basal_value_changed(id, text))
        outputs_smoothing.textChanged.connect(lambda text, id=id: self.physiboss_outputs_smoothing_changed(id, text))
        
        outputs_editor.addWidget(outputs_value)
        outputs_editor.addWidget(outputs_basal_value)
        outputs_editor.addWidget(outputs_smoothing)

        outputs_value.setFixedWidth(70)
        outputs_basal_value.setFixedWidth(70)
        outputs_smoothing.setFixedWidth(70)
        
        outputs_editor.addWidget(outputs_remove)

        self.physiboss_outputs_layout.addLayout(outputs_editor)
        self.physiboss_outputs.append((outputs_behaviour_dropdown, outputs_node_dropdown, outputs_action, outputs_value, outputs_basal_value, outputs_smoothing, outputs_remove, outputs_editor))#, outputs_editor_2))
    
    def physiboss_outputs_behaviour_changed(self, i, index):
        if index >= 0:
            self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["name"] = self.physiboss_behaviours[index]
        
    def physiboss_outputs_node_changed(self, i, index):
        if index >= 0:
            self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["node"] = self.param_d[self.current_cell_def]["intracellular"]["list_nodes"][index]

    def physiboss_outputs_action_changed(self, i, index):
        self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["action"] = "activation" if index == 0 else "inhibition"

    def physiboss_outputs_value_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["value"] = text

    def physiboss_outputs_basal_value_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["basal_value"] = text

    def physiboss_outputs_smoothing_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["smoothing"] = text

    def physiboss_clicked_remove_output(self, i):
        self.physiboss_remove_output(i)
        del self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]

    def physiboss_remove_output(self, id):
        self.physiboss_outputs[id][0].currentIndexChanged.disconnect()
        self.physiboss_outputs[id][0].deleteLater()
        self.physiboss_outputs[id][1].currentIndexChanged.disconnect()
        self.physiboss_outputs[id][1].deleteLater()
        self.physiboss_outputs[id][2].currentIndexChanged.disconnect()
        self.physiboss_outputs[id][2].deleteLater()
        self.physiboss_outputs[id][3].textChanged.disconnect()
        self.physiboss_outputs[id][3].deleteLater()
        self.physiboss_outputs[id][4].textChanged.disconnect()
        self.physiboss_outputs[id][4].deleteLater()
        self.physiboss_outputs[id][5].textChanged.disconnect()
        self.physiboss_outputs[id][5].deleteLater()
        self.physiboss_outputs[id][6].clicked.disconnect()
        self.physiboss_outputs[id][6].deleteLater()
        del self.physiboss_outputs[id]

        # Here we should remap the clicked method to have the proper id
        for i, output in enumerate(self.physiboss_outputs):
            name, node, action, value, basal_value, smoothing, button, _ = output
            name.currentIndexChanged.disconnect()
            name.currentIndexChanged.connect(lambda index, i=i: self.physiboss_outputs_behaviour_changed(i, index))
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_outputs_node_changed(i, index))
            action.currentIndexChanged.disconnect()
            action.currentIndexChanged.connect(lambda index, i=i: self.physiboss_outputs_action_changed(i, index))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text, i=i: self.physiboss_outputs_value_changed(i, text))
            basal_value.textChanged.disconnect()
            basal_value.textChanged.connect(lambda text, i=i: self.physiboss_outputs_basal_value_changed(i, text))
            smoothing.textChanged.disconnect()
            smoothing.textChanged.connect(lambda text, i=i: self.physiboss_outputs_smoothing_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.physiboss_clicked_remove_output(i))
            
    def physiboss_clear_outputs(self):
        for i, _ in reversed(list(enumerate(self.physiboss_outputs))):
            self.physiboss_remove_output(i)

    def physiboss_global_inheritance_checkbox_cb(self, bval):
        self.physiboss_global_inheritance_flag = bval
        if self.param_d[self.current_cell_def]["intracellular"] is not None:
            self.param_d[self.current_cell_def]["intracellular"]["global_inheritance"] = str(bval)

    def physiboss_clicked_add_node_inheritance(self):
        self.physiboss_add_node_inheritance()
        self.param_d[self.current_cell_def]["intracellular"]["node_inheritance"].append({
            'node': self.param_d[self.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.param_d[self.current_cell_def]["intracellular"].keys() else "",
            'flag': str(not self.physiboss_global_inheritance),
        })
        
    def physiboss_add_node_inheritance(self):
        
        node_inheritance_editor = QHBoxLayout()
        node_inheritance_dropdown = QComboBox_custom()
        node_inheritance_dropdown.setFixedWidth(200)
        if "list_nodes" in self.param_d[self.current_cell_def]["intracellular"]:
            for node in self.param_d[self.current_cell_def]["intracellular"]["list_nodes"]:
                node_inheritance_dropdown.addItem(node)
        
                
        node_inheritance_checkbox = QCheckBox_custom('Node-specific inheritance')
        node_inheritance_checkbox.setEnabled(True)
        node_inheritance_checkbox.setChecked(not self.physiboss_global_inheritance_flag)
        
        node_inheritance_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)


        id = len(self.physiboss_node_specific_inheritance)
        node_inheritance_dropdown.currentIndexChanged.connect(lambda index, id=id: self.physiboss_node_inheritance_node_changed(id, index))
        node_inheritance_checkbox.clicked.connect(lambda bval, id=id: self.physiboss_node_inheritance_flag_changed(id, bval))
        node_inheritance_remove.clicked.connect(lambda _, id=id: self.physiboss_clicked_remove_node_inheritance(id))
        node_inheritance_remove.setFixedWidth(30)
        node_inheritance_editor.addWidget(node_inheritance_dropdown)
        node_inheritance_editor.addWidget(node_inheritance_checkbox)
        node_inheritance_editor.addWidget(node_inheritance_remove)
        node_inheritance_editor.addStretch(1)
        
       
        self.physiboss_inheritance_layout.addLayout(node_inheritance_editor)
        self.physiboss_node_specific_inheritance.append((node_inheritance_dropdown, node_inheritance_checkbox, node_inheritance_remove, node_inheritance_editor))
    
    def physiboss_remove_node_inheritance(self, id):
        self.physiboss_node_specific_inheritance[id][0].currentIndexChanged.disconnect()
        self.physiboss_node_specific_inheritance[id][0].deleteLater()
        self.physiboss_node_specific_inheritance[id][1].clicked.disconnect()
        self.physiboss_node_specific_inheritance[id][1].deleteLater()
        self.physiboss_node_specific_inheritance[id][2].clicked.disconnect()
        self.physiboss_node_specific_inheritance[id][2].deleteLater()
        self.physiboss_node_specific_inheritance[id][3].deleteLater()
        del self.physiboss_node_specific_inheritance[id]
    
    
        # Here we should remap the clicked method to have the proper id
        for i, node_inheritance in enumerate(self.physiboss_node_specific_inheritance):
            node, flag, remove, _ = node_inheritance
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_node_inheritance_node_changed(i, index))
            flag.clicked.disconnect()
            flag.clicked.connect(lambda bval, i=i: self.physiboss_node_inheritance_flag_changed(i, bval))
            remove.clicked.disconnect()
            remove.clicked.connect(lambda _, i=i: self.physiboss_clicked_remove_node_inheritance(i))
      
    def physiboss_node_inheritance_node_changed(self, i, index):
        if index >= 0:
            self.param_d[self.current_cell_def]["intracellular"]["node_inheritance"][i]["node"] = self.param_d[self.current_cell_def]["intracellular"]["list_nodes"][index]
  
    def physiboss_node_inheritance_flag_changed(self, i, bval):
        self.param_d[self.current_cell_def]["intracellular"]["node_inheritance"][i]["flag"] = str(bval)
  
    def physiboss_clicked_remove_node_inheritance(self, i):
        self.physiboss_remove_node_inheritance(i)
        del self.param_d[self.current_cell_def]["intracellular"]["node_inheritance"][i]
        
    def physiboss_clear_node_inheritance(self):
        for i, _ in reversed(list(enumerate(self.physiboss_node_specific_inheritance))):
            self.physiboss_remove_node_inheritance(i)

    def intracellular_type_changed(self, index):

        self.physiboss_boolean_frame.hide()
        self.ode_sbml_frame.hide()
        self.empty_frame.show()

        if index == 0 and self.current_cell_def is not None:
            logging.debug(f'intracellular_type_changed(): {self.current_cell_def}')
            # print(f'intracellular_type_changed(): {self.current_cell_def}')
            self.empty_frame.show()
            if "intracellular" in self.param_d[self.current_cell_def].keys():
                self.physiboss_bnd_file.setText("")
                self.physiboss_cfg_file.setText("")
                self.physiboss_clear_initial_values()
                self.physiboss_clear_mutants()
                self.physiboss_clear_parameters()
                self.physiboss_clear_inputs()
                self.physiboss_clear_outputs()
                self.physiboss_clear_node_inheritance()
                self.physiboss_time_step.setText("12.0")
                self.physiboss_time_stochasticity.setText("0.0")
                self.physiboss_scaling.setText("1.0")
                self.physiboss_starttime.setText("0.0")
                self.physiboss_global_inheritance_checkbox.setChecked(False)
                self.param_d[self.current_cell_def]["intracellular"] = None
                
        elif index == 1:
            # print("PhysiBoSS")
            logging.debug(f'intracellular is boolean')
            if self.param_d[self.current_cell_def]["intracellular"] is None:
                self.param_d[self.current_cell_def]["intracellular"] = {"type": "maboss"}
                
            if 'initial_values' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.param_d[self.current_cell_def]["intracellular"]["initial_values"] = []
                self.physiboss_clear_initial_values()
            
            if 'mutants' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.param_d[self.current_cell_def]["intracellular"]["mutants"] = []
                self.physiboss_clear_mutants()

            if 'parameters' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.param_d[self.current_cell_def]["intracellular"]["parameters"] = []
                self.physiboss_clear_parameters()

            if 'inputs' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.param_d[self.current_cell_def]["intracellular"]["inputs"] = []
                self.physiboss_clear_inputs()

            if 'outputs' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.param_d[self.current_cell_def]["intracellular"]["outputs"] = []
                self.physiboss_clear_outputs()

            if 'node_inheritance' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.param_d[self.current_cell_def]["intracellular"]["node_inheritance"] = []
                self.physiboss_clear_node_inheritance()

            if 'time_step' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.physiboss_time_step.setText("12.0")

            if 'time_stochasticity' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.physiboss_time_stochasticity.setText("0.0")
            
            if 'scaling' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.physiboss_scaling.setText("1.0")
            
            if 'start_time' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.physiboss_starttime.setText("0.0")
                
            if 'global_inheritance' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.param_d[self.current_cell_def]["intracellular"]["global_inheritance"] = "False"
                self.physiboss_global_inheritance_checkbox.setChecked(False)
            self.physiboss_update_list_signals()
            self.physiboss_update_list_behaviours()
            self.physiboss_boolean_frame.show()
        elif index == 2:
            # logging.debug(f'intracellular is SBML ODEs')
            if "intracellular" not in self.param_d[self.current_cell_def].keys():
                self.param_d[self.current_cell_def]["intracellular"] = None
            self.ode_sbml_frame.show()
        elif index == 3:
            pass
            # logging.debug(f'intracellular is FBA')
        else:
            pass
            # logging.debug(f'intracellular is Unkown')
        
    #--------------------------------------------------------
    def create_intracellular_tab(self):
        intracellular_tab = QWidget()
        intracellular_tab.setStyleSheet("QPushButton { color: black }")
        intracellular_tab_scroll = QScrollArea()
        glayout = QVBoxLayout()

        label = QLabel("Phenotype: intracellular")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)

        type_hbox = QHBoxLayout()

        type_label = QLabel("Type")
        type_hbox.addWidget(type_label)

        self.intracellular_type_dropdown = QComboBox_custom()
        self.intracellular_type_dropdown.setFixedWidth(300)
        self.intracellular_type_dropdown.currentIndexChanged.connect(self.intracellular_type_changed)
        self.intracellular_type_dropdown.addItem("none")
        self.intracellular_type_dropdown.addItem("Boolean")
        self.intracellular_type_dropdown.addItem("ODEs")
        # self.intracellular_type_dropdown.addItem("fba")
        # self.intracellular_type_dropdown.model().item(3).setEnabled(False)
        type_hbox.addWidget(self.intracellular_type_dropdown)

        # glayout.addLayout(type_hbox, idr,0, 1,1) # w, row, column, rowspan, colspan
        glayout.addLayout(type_hbox)#, idr,0, 1,1) # w, row, column, rowspan, colspan


        # -------  PhysiBoSS Boolean  -------

        # self.boolean_frame = QFrame()
        ly = QVBoxLayout()
        self.physiboss_boolean_frame.setLayout(ly)

        bnd_hbox = QHBoxLayout()

        bnd_label = QLabel("MaBoSS BND file")
        bnd_hbox.addWidget(bnd_label)

        self.physiboss_bnd_file = QLineEdit()
        self.physiboss_bnd_file.textChanged.connect(self.physiboss_bnd_filename_changed)
        bnd_hbox.addWidget(self.physiboss_bnd_file)


        bnd_button = QPushButton("Choose BND file")
        bnd_button.clicked.connect(self.choose_bnd_file)

        bnd_hbox.addWidget(bnd_button)
        ly.addLayout(bnd_hbox)

        cfg_hbox = QHBoxLayout()

        cfg_label = QLabel("MaBoSS CFG file")
        cfg_hbox.addWidget(cfg_label)

        self.physiboss_cfg_file = QLineEdit()
        self.physiboss_cfg_file.textChanged.connect(self.physiboss_cfg_filename_changed)
        cfg_hbox.addWidget(self.physiboss_cfg_file)

        cfg_button = QPushButton("Choose CFG file")
        cfg_button.clicked.connect(self.choose_cfg_file)

        cfg_hbox.addWidget(cfg_button)
        ly.addLayout(cfg_hbox)

        time_step_hbox = QHBoxLayout()

        time_step_label = QLabel("Time step")
        time_step_hbox.addWidget(time_step_label)

        self.physiboss_time_step = QLineEdit()
        self.physiboss_time_step.textChanged.connect(self.physiboss_time_step_changed)
        # Commenting it because for french, we need to use a comma, which then get written in the XML and might cause problems
        # self.physiboss_time_step.setValidator(QtGui.QDoubleValidator())

        time_step_hbox.addWidget(self.physiboss_time_step)

        ly.addLayout(time_step_hbox)

        scaling_hbox = QHBoxLayout()

        scaling_label = QLabel("Scaling")
        scaling_hbox.addWidget(scaling_label)

        self.physiboss_scaling = QLineEdit()
        self.physiboss_scaling.textChanged.connect(self.physiboss_scaling_changed)
        # Commenting it because for french, we need to use a comma, which then get written in the XML and might cause problems
        # self.physiboss_scaling.setValidator(QtGui.QDoubleValidator())

        scaling_hbox.addWidget(self.physiboss_scaling)

        ly.addLayout(scaling_hbox)

        time_stochasticity_hbox = QHBoxLayout()

        time_stochasticity_label = QLabel("Time stochasticity")
        time_stochasticity_hbox.addWidget(time_stochasticity_label)

        self.physiboss_time_stochasticity = QLineEdit()
        self.physiboss_time_stochasticity.textChanged.connect(self.physiboss_time_stochasticity_changed)
        # Commenting it because for french, we need to use a comma, which then get written in the XML and might cause problems
        # self.physiboss_time_stochasticity.setValidator(QtGui.QDoubleValidator())

        time_stochasticity_hbox.addWidget(self.physiboss_time_stochasticity)

        ly.addLayout(time_stochasticity_hbox)

        starttime_hbox = QHBoxLayout()

        starttime_label = QLabel("Start time")
        starttime_hbox.addWidget(starttime_label)

        self.physiboss_starttime = QLineEdit()
        self.physiboss_starttime.textChanged.connect(self.physiboss_starttime_changed)
        # Commenting it because for french, we need to use a comma, which then get written in the XML and might cause problems
        # self.physiboss_scaling.setValidator(QtGui.QDoubleValidator())

        starttime_hbox.addWidget(self.physiboss_starttime)

        ly.addLayout(starttime_hbox)


        initial_states_groupbox = QGroupBox("Initial states")
        self.physiboss_initial_states_layout = QVBoxLayout()
        initial_states_labels = QHBoxLayout()

        initial_states_node_label = QLabel("Node")
        initial_states_value_label = QLabel("Value")
        initial_states_labels.addWidget(initial_states_node_label)
        initial_states_labels.addWidget(initial_states_value_label)
        self.physiboss_initial_states_layout.addLayout(initial_states_labels)

        self.physiboss_initial_states = []
        initial_states_groupbox.setLayout(self.physiboss_initial_states_layout)

        ly.addWidget(initial_states_groupbox)
        
        initial_states_addbutton = QPushButton("Add new initial value")
        initial_states_addbutton.setStyleSheet("QPushButton { color: black }")
        initial_states_addbutton.clicked.connect(self.physiboss_clicked_add_initial_value)
        ly.addWidget(initial_states_addbutton)

        
        mutants_groupbox = QGroupBox("Mutants")
        self.physiboss_mutants_layout = QVBoxLayout()
        mutants_labels = QHBoxLayout()

        mutants_node_label = QLabel("Node")
        mutants_value_label = QLabel("Value")
        mutants_labels.addWidget(mutants_node_label)
        mutants_labels.addWidget(mutants_value_label)
        self.physiboss_mutants_layout.addLayout(mutants_labels)
        mutants_groupbox.setLayout(self.physiboss_mutants_layout)
        
        self.physiboss_mutants = []
        ly.addWidget(mutants_groupbox)
 
        mutants_addbutton = QPushButton("Add new mutant")
        mutants_addbutton.setStyleSheet("QPushButton { color: black }")
        mutants_addbutton.clicked.connect(self.physiboss_clicked_add_mutant)
        ly.addWidget(mutants_addbutton)

        parameters_groupbox = QGroupBox("Parameters")

        self.physiboss_parameters_layout = QVBoxLayout()
        parameters_labels = QHBoxLayout()

        parameters_node_label = QLabel("Name")
        parameters_value_label = QLabel("Value")
        parameters_labels.addWidget(parameters_node_label)
        parameters_labels.addWidget(parameters_value_label)
        self.physiboss_parameters_layout.addLayout(parameters_labels)
        parameters_groupbox.setLayout(self.physiboss_parameters_layout)

        self.physiboss_parameters = []
        ly.addWidget(parameters_groupbox)

        parameters_addbutton = QPushButton("Add new parameter")
        parameters_addbutton.setStyleSheet("QPushButton { color: black }")
        parameters_addbutton.clicked.connect(self.physiboss_clicked_add_parameter)
        ly.addWidget(parameters_addbutton)

        inputs_groupbox = QGroupBox("Inputs")

        self.physiboss_inputs_layout = QVBoxLayout()
        self.physiboss_inputs_layout.setAlignment(Qt.AlignTop)
        inputs_labels = QHBoxLayout()

        inputs_signal_label = QLabel("Signal")
        inputs_node_label = QLabel("Node")
        inputs_action_label = QLabel("Action")
        inputs_threshold_label = QLabel("Thr")
        inputs_inact_threshold_label = QLabel("Inact. Thr")
        inputs_smoothing_label = QLabel("Smoothing")


        inputs_labels.addWidget(inputs_signal_label)
        inputs_signal_label.setMinimumWidth(240)
        inputs_labels.setStretch(0, 1)
        inputs_labels.addWidget(inputs_action_label)
        inputs_action_label.setMinimumWidth(50)
        inputs_labels.setStretch(1, 1)
        inputs_labels.addWidget(inputs_node_label)
        inputs_node_label.setMinimumWidth(50)
        inputs_labels.setStretch(2, 1)
        inputs_labels.addWidget(inputs_threshold_label)
        inputs_threshold_label.setFixedWidth(70)
        inputs_labels.addWidget(inputs_inact_threshold_label)
        inputs_inact_threshold_label.setFixedWidth(70)
        inputs_labels.addWidget(inputs_smoothing_label)
        inputs_smoothing_label.setFixedWidth(70)
        inputs_labels.addSpacing(35)

        self.physiboss_inputs_layout.addLayout(inputs_labels)
        inputs_groupbox.setLayout(self.physiboss_inputs_layout)

        self.physiboss_inputs = []
        ly.addWidget(inputs_groupbox)

        inputs_addbutton = QPushButton("Add new input")
        inputs_addbutton.setStyleSheet("QPushButton { color: black }")
        inputs_addbutton.clicked.connect(self.physiboss_clicked_add_input)
        ly.addWidget(inputs_addbutton)

        outputs_groupbox = QGroupBox("Outputs")

        self.physiboss_outputs_layout = QVBoxLayout()
        outputs_labels = QHBoxLayout()

        outputs_signal_label = QLabel("Behavior")
        outputs_node_label = QLabel("Node")
        outputs_action_label = QLabel("Action")
        outputs_value_label = QLabel("Value")
        outputs_basal_value_label = QLabel("Base value")
        outputs_smoothing_label = QLabel("Smoothing")

        outputs_labels.addWidget(outputs_node_label)
        outputs_node_label.setMinimumWidth(50)
        outputs_labels.setStretch(0, 1)
        outputs_labels.addWidget(outputs_action_label)
        outputs_action_label.setMinimumWidth(40)
        outputs_labels.setStretch(1, 1)
        outputs_labels.addWidget(outputs_signal_label)
        outputs_signal_label.setMinimumWidth(250)
        outputs_labels.setStretch(2, 1)
        outputs_labels.addWidget(outputs_value_label)
        outputs_value_label.setFixedWidth(70)
        outputs_labels.addWidget(outputs_basal_value_label)
        outputs_basal_value_label.setFixedWidth(70)
        outputs_labels.addWidget(outputs_smoothing_label)
        outputs_labels.addSpacing(40)

        self.physiboss_outputs_layout.addLayout(outputs_labels)
        outputs_groupbox.setLayout(self.physiboss_outputs_layout)

        self.physiboss_outputs = []
        ly.addWidget(outputs_groupbox)

        outputs_addbutton = QPushButton("Add new output")
        outputs_addbutton.setStyleSheet("QPushButton { color: black }")
        outputs_addbutton.clicked.connect(self.physiboss_clicked_add_output)
        ly.addWidget(outputs_addbutton)


        inheritance_groupbox = QGroupBox("Inheritance")

        self.physiboss_inheritance_layout = QVBoxLayout()

        self.physiboss_global_inheritance = QHBoxLayout()

        self.physiboss_global_inheritance_checkbox = QCheckBox_custom('Global inheritance')
        self.physiboss_global_inheritance_flag = False
        self.physiboss_global_inheritance_checkbox.setEnabled(True)
        self.physiboss_global_inheritance_checkbox.setChecked(self.physiboss_global_inheritance_flag)
        self.physiboss_global_inheritance_checkbox.clicked.connect(self.physiboss_global_inheritance_checkbox_cb)
        self.physiboss_global_inheritance.addWidget(self.physiboss_global_inheritance_checkbox)
        self.physiboss_inheritance_layout.addLayout(self.physiboss_global_inheritance)
        
        
        inheritance_labels = QHBoxLayout()
        inheritance_node_label = QLabel("Node")
        inheritance_node_label.setFixedWidth(200)
        inheritance_value_label = QLabel("Value")
        inheritance_value_label.setFixedWidth(150)
        inheritance_labels.addWidget(inheritance_node_label)
        inheritance_labels.addWidget(inheritance_value_label)
        inheritance_labels.addStretch(1)

        self.physiboss_inheritance_layout.addLayout(inheritance_labels)
        inheritance_groupbox.setLayout(self.physiboss_inheritance_layout)
        self.physiboss_node_specific_inheritance = []

        ly.addWidget(inheritance_groupbox)

        inheritance_addbutton = QPushButton("Add node-specific inheritance")
        inheritance_addbutton.clicked.connect(self.physiboss_clicked_add_node_inheritance)
        ly.addWidget(inheritance_addbutton)


        glayout.addWidget(self.physiboss_boolean_frame)
        glayout.addStretch()


        # -------  "None" intracellular frame  -------
        vbox = QVBoxLayout()
        self.empty_frame.setLayout(vbox)

        hbox = QHBoxLayout()
        empty_label = QLabel("")
        hbox.addWidget(empty_label)
        vbox.addLayout(hbox)

        glayout.addWidget(self.empty_frame)
        glayout.addStretch()

        # -------  ODE SBML frame  -------
        glayout.addWidget(self.ode_sbml_frame)
        # glayout.addStretch()   # ??

        #-------------------------------------------
        intracellular_tab_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        intracellular_tab_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        intracellular_tab_scroll.setWidgetResizable(True)
        intracellular_tab_scroll.setWidget(intracellular_tab) 

        intracellular_tab.setLayout(glayout)

        intracellular_tab.setLayout(glayout)
        return intracellular_tab_scroll

    # --- mechanics
    def enable_mech_params(self, bval):
        print("---- enable_mech_params()  bval= ",bval)
        self.cell_cell_adhesion_strength.setEnabled(bval)
        self.cell_cell_repulsion_strength.setEnabled(bval)
        self.relative_maximum_adhesion_distance.setEnabled(bval)
        self.cell_adhesion_affinity_dropdown.setEnabled(bval)
        self.cell_adhesion_affinity.setEnabled(bval)
        self.set_relative_equilibrium_distance.setEnabled(bval)
        self.set_relative_equilibrium_distance_enabled.setEnabled(bval)
        self.set_absolute_equilibrium_distance.setEnabled(bval)
        self.set_absolute_equilibrium_distance_enabled.setEnabled(bval)

    # def unmovable_cb(self,bval):
    #     # print("--------- unmovable_cb()  called!  bval=",bval)
    #     self.param_d[self.current_cell_def]['is_movable'] = not bval  # uh, this isn't not confusing :/
    #     self.enable_mech_params(not bval)

    # def cell_bm_adhesion_strength_changed(self, text):
    #     self.param_d[self.current_cell_def]['mechanics_BM_adhesion'] = text
    # def cell_bm_repulsion_strength_changed(self, text):
    #     self.param_d[self.current_cell_def]['mechanics_BM_repulsion'] = text

    def chemotaxis_enabled_cb(self,bval):
        self.param_d[self.current_cell_def]['motility_chemotaxis'] = bval
        if bval:
            self.advanced_chemotaxis_enabled.setChecked(False)
            self.param_d[self.current_cell_def]['motility_advanced_chemotaxis'] = False
            self.motility2_substrate_dropdown.setEnabled(False)
            self.chemo_sensitivity.setEnabled(False)
            self.normalize_each_gradient.setEnabled(False)

        self.motility_substrate_dropdown.setEnabled(bval)
        self.chemotaxis_direction_towards.setEnabled(bval)
        self.chemotaxis_direction_against.setEnabled(bval)

    def advanced_chemotaxis_enabled_cb(self,bval):
        self.param_d[self.current_cell_def]['motility_advanced_chemotaxis'] = bval
        if bval:
            self.motility_substrate_dropdown.setEnabled(False)
            self.chemotaxis_direction_towards.setEnabled(False)
            self.chemotaxis_direction_against.setEnabled(False)

            self.chemotaxis_enabled.setChecked(False)
            self.param_d[self.current_cell_def]['motility_chemotaxis'] = False

        self.motility2_substrate_dropdown.setEnabled(bval)
        self.chemo_sensitivity.setEnabled(bval)
        self.normalize_each_gradient.setEnabled(bval)

    def chemo_sensitivity_changed(self, text):
        logging.debug(f'----- chemo_sensitivity_changed() = {text}')
        subname = self.param_d[self.current_cell_def]['motility_advanced_chemotaxis_substrate']
        if subname == "":
            logging.debug(f' ... but motility_advanced_chemotaxis_substrate is empty string, so return!')
            return
        logging.debug(f'----- chemo_sensitivity_changed(): subname = {subname}')
        # print("       keys() = ",self.param_d[self.current_cell_def].keys())
        self.param_d[self.current_cell_def]['chemotactic_sensitivity'][subname] = text
        logging.debug(f'     chemotactic_sensitivity (dict)= {self.param_d[self.current_cell_def]["chemotactic_sensitivity"]}')
        # if 'chemo_sensitivity' in self.param_d[self.current_cell_def].keys():
            # self.param_d[self.current_cell_def]['chemo_sensitivity'][subname] = text

    # --- secretion
    def secretion_rate_changed(self, text):
        self.param_d[self.current_cell_def]["secretion"][self.current_secretion_substrate]['secretion_rate'] = text
    def secretion_target_changed(self, text):
        self.param_d[self.current_cell_def]["secretion"][self.current_secretion_substrate]['secretion_target'] = text
    def uptake_rate_changed(self, text):
        self.param_d[self.current_cell_def]["secretion"][self.current_secretion_substrate]['uptake_rate'] = text
    def secretion_net_export_rate_changed(self, text):
        self.param_d[self.current_cell_def]["secretion"][self.current_secretion_substrate]['net_export_rate'] = text

    #--------------------------------------------------------
    def clear_all_var_name_prev(self):
        for irow in range(self.max_custom_data_rows):
            self.custom_data_table.cellWidget(irow,self.custom_icol_name).prev = None

    #--------------------------------------------------------
    def custom_data_search_cb(self, s):
        if not s:
            s = 'thisisadummystring'

        for irow in range(self.max_custom_data_rows):
            if s in self.custom_data_table.cellWidget(irow,self.custom_icol_name).text():
                backcolor = "background: bisque"
                self.custom_data_table.cellWidget(irow,self.custom_icol_name).setStyleSheet(backcolor)
                # self.custom_data_table.selectRow(irow)  # don't do this; keyboard input -> cell 
            else:
                backcolor = "background: white"
                self.custom_data_table.cellWidget(irow,self.custom_icol_name).setStyleSheet(backcolor)
            # self.custom_data_table.setCurrentItem(item)

    #--------------------------------------------------------
    def add_row_custom_table(self, row_num):
        # row_num = self.max_custom_data_rows - 1
        self.custom_data_table.insertRow(row_num)
        for irow in [row_num]:
            # print("=== add_row_custom_table(): irow=",irow)
            # ------- custom data variable name
            w_varname = MyQLineEdit()
            w_varname.setFrame(False)
            rx_valid_varname = QtCore.QRegExp("^[a-zA-Z][a-zA-Z0-9_]+$")
            name_validator = QtGui.QRegExpValidator(rx_valid_varname )
            w_varname.setValidator(name_validator)

            self.custom_data_table.setCellWidget(irow, self.custom_icol_name, w_varname)   # 1st col
            w_varname.vname = w_varname  
            w_varname.wrow = irow
            w_varname.wcol = 0   # beware: hard-coded 
            w_varname.textChanged[str].connect(self.custom_data_name_changed)  # being explicit about passing a string 

            # ------- custom data variable value
            w_varval = MyQLineEdit('0.0')
            w_varval.setFrame(False)
            w_varval.vname = w_varname  
            w_varval.wrow = irow
            w_varval.wcol = 1   # beware: hard-coded 
            w_varval.setValidator(QtGui.QDoubleValidator())
            self.custom_data_table.setCellWidget(irow, self.custom_icol_value, w_varval)
            w_varval.textChanged[str].connect(self.custom_data_value_changed)  # being explicit about passing a string 


            # ------- custom data variable conserved flag (equally divided during cell division)
            w_var_conserved = MyQCheckBox()
            w_var_conserved.setStyleSheet(self.checkbox_style)
            w_var_conserved.vname = w_varname  
            w_var_conserved.wrow = irow
            w_var_conserved.wcol = 2

            # rwh NB! Leave these lines in (for less confusing clicking/coloring of cell)
            item = QTableWidgetItem('')
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            self.custom_data_table.setItem(irow, self.custom_icol_conserved, item)

            self.custom_data_table.setCellWidget(irow, self.custom_icol_conserved, w_var_conserved)

            # ------- custom data variable units
            w_var_units = MyQLineEdit()
            w_var_units.setFrame(False)
            w_var_units.setFrame(False)
            w_var_units.vname = w_varname  
            w_var_units.wrow = irow
            w_var_units.wcol = 3   # beware: hard-coded 
            self.custom_data_table.setCellWidget(irow, self.custom_icol_units, w_var_units)
            w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- custom data variable description
            w_var_desc = MyQLineEdit()
            w_var_desc.setFrame(False)
            w_var_desc.vname = w_varname  
            w_var_desc.wrow = irow
            w_var_desc.wcol = 4   # beware: hard-coded 
            self.custom_data_table.setCellWidget(irow, self.custom_icol_desc, w_var_desc)
            w_var_desc.textChanged[str].connect(self.custom_data_desc_changed)  # being explicit about passing a string 


    #--------------------------------------------------------
    # Delete an entire row from the Custom Data subtab. Somewhat tricky...
    def delete_custom_data_cb(self):
        debug_me = False
        row = self.custom_data_table.currentRow()
        print("------------- delete_custom_data_cb(), row=",row)
        try:
            varname = self.custom_data_table.cellWidget(row,self.custom_icol_name).text()
        except:
            return
        if debug_me:
            print(" custom var name= ",varname)
            print(" master_custom_var_d.keys()= ",self.master_custom_var_d.keys())
            # print(" master_custom_var_d= ",self.master_custom_var_d)

        if varname in self.master_custom_var_d.keys():
            self.master_custom_var_d.pop(varname)
            for key in self.master_custom_var_d.keys():
                if self.master_custom_var_d[key][0] > row:   # remember: [row, units, description]
                    self.master_custom_var_d[key][0] -= 1
            # remove (pop) this custom var name from ALL cell types
            for cdef in self.param_d.keys():
                if debug_me:
                    print(f"   popping {varname} from {cdef}")
                self.param_d[cdef]['custom_data'].pop(varname)

        # Since each widget in each row had an associated row #, we need to decrement all those following
        # the row that was just deleted.
        for irow in range(row, self.max_custom_data_rows):
            # print("---- decrement wrow in irow=",irow)
            self.custom_data_table.cellWidget(irow,self.custom_icol_name).wrow -= 1  # sufficient to only decr the "name" column

            # print(f"   after removing {varname}, master_custom_var_d= ",self.master_custom_var_d)

        self.custom_data_table.removeRow(row)

        self.add_row_custom_table(self.max_custom_data_rows - 1)
        self.enable_all_custom_data()
        # print(" 2)master_custom_var_d= ",self.master_custom_var_d)
        # print("------------- LEAVING  delete_custom_data_cb")

    #--------------------------------------------------------
    def create_custom_data_tab(self):

        # table columns
        self.custom_icol_name = 0  # custom var Name
        self.custom_icol_value = 1  # custom var Value
        self.custom_icol_conserved = 2  # custom Conserve checkbox
        self.custom_icol_units = 3  # custom Units
        self.custom_icol_desc = 4  # custom Description

        # self.master_custom_var_d = {}   # will have value= [units, desc]

        # self.custom_var_d = {}   # will have value= [units, desc]
        self.custom_var_conserved = False
        self.custom_var_value_str_default = '0.0'
        self.custom_var_conserved_default = False

        self.custom_table_disabled = False

        custom_data_tab = QWidget()
        custom_data_tab_scroll = QScrollArea()

        # glayout = QGridLayout()
        vlayout = QVBoxLayout()
        hlayout = QHBoxLayout()

        self.custom_data_search = QLineEdit(styleSheet="background-color: white")
        self.custom_data_search.setFixedWidth(400)
        self.custom_data_search.setPlaceholderText("Search for Name...")
        self.custom_data_search.textChanged.connect(self.custom_data_search_cb)
        hlayout.addWidget(self.custom_data_search)

        # delete_custom_data_btn = QPushButton("Delete row")
        # delete_custom_data_btn.clicked.connect(self.delete_custom_data_cb)
        # delete_custom_data_btn.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        # hlayout.addWidget(delete_custom_data_btn)

        # hlayout.addWidget(QLabel("(click row #)"))

        hlayout.addStretch()
        vlayout.addLayout(hlayout)

        #-------
        self.custom_data_table = QTableWidget()
        # self.custom_data_table.cellClicked.connect(self.custom_data_cell_was_clicked)
        self.max_custom_data_rows = 100
        self.max_custom_data_cols = 5

        # self.max_custom_rows_edited = self.max_custom_data_rows 

        self.custom_data_table.setColumnCount(self.max_custom_data_cols)
        self.custom_data_table.setRowCount(self.max_custom_data_rows)
        # self.custom_data_table.setHorizontalHeaderLabels(['Conserve','Name','Value','Units','Desc'])
        self.custom_data_table.setHorizontalHeaderLabels(['Name','Value','Conserve','Units','Description'])
        self.custom_data_table.setStyleSheet("background-color: white")
        # Don't like the behavior these offer, e.g., locks down width of 0th column :/
        # header = self.custom_data_table.horizontalHeader()       
        # header.setSectionResizeMode(0, QHeaderView.Stretch)
        # header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            
        for irow in range(self.max_custom_data_rows):
            # ------- custom data variable name
            w_varname = MyQLineEdit()
            w_varname.setFrame(False)
            rx_valid_varname = QtCore.QRegExp("^[a-zA-Z][a-zA-Z0-9_]+$")
            name_validator = QtGui.QRegExpValidator(rx_valid_varname )
            w_varname.setValidator(name_validator)

            self.custom_data_table.setCellWidget(irow, self.custom_icol_name, w_varname)   # 1st col

            # item = QTableWidgetItem('')
            # # item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            # self.custom_data_table.setItem(irow, self.custom_icol_name, item)   # 1st col is var name
            # self.custom_data_table.setCellWidget(irow, self.custom_icol_name, w_varname)   # 1st col

            # self.custom_data_name.append(w_varname)
            w_varname.vname = w_varname  
            w_varname.wrow = irow
            w_varname.wcol = 0   # beware: hard-coded 
            # w_varname.idx = irow   # rwh: is .idx used?
            w_varname.textChanged[str].connect(self.custom_data_name_changed)  # being explicit about passing a string 


            # ------- custom data variable value
            w_varval = MyQLineEdit('0.0')
            w_varval.setFrame(False)
            # item = QTableWidgetItem('')
            w_varval.vname = w_varname  
            w_varval.wrow = irow
            w_varval.wcol = 1   # beware: hard-coded 
            # w_varval.idx = irow   # rwh: is .idx used?
            w_varval.setValidator(QtGui.QDoubleValidator())
            self.custom_data_table.setCellWidget(irow, self.custom_icol_value, w_varval)
            w_varval.textChanged[str].connect(self.custom_data_value_changed)  # being explicit about passing a string 


            # ------- custom data variable conserved flag (equally divided during cell division)
            # item = QTableWidgetItem('')
            # item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            # # Later...attempt fancy: disable checkable UNTIL custom var is defined...
            # # flags = item.flags()
            # # flags &= ~QtCore.Qt.ItemIsEditable
            # # flags |= QtCore.Qt.ItemIsUserCheckable 
            # # flags &= ~QtCore.Qt.ItemIsUserCheckable   # make uncheckable (until a custom var defined)
            # # item.setFlags(flags)
            # item.setCheckState(QtCore.Qt.Unchecked)
            # self.custom_data_table.setItem(irow, self.custom_icol_conserved, item)
            # # self.custom_data_table.item(irow, 0).setEnabled(False)

            w_var_conserved = MyQCheckBox()
            w_var_conserved.setStyleSheet(self.checkbox_style)
            # w_var_conserved.setFrame(False)
            w_var_conserved.vname = w_varname  
            w_var_conserved.wrow = irow
            w_var_conserved.wcol = 2
            w_var_conserved.clicked.connect(self.custom_var_conserved_clicked)

            # item = QTableWidgetItem('')
            # item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            # item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            # self.custom_data_table.setItem(irow, self.custom_icol_conserved, item)

            # rwh NB! Leave these lines in (for less confusing clicking/coloring of cell)
            item = QTableWidgetItem('')
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            self.custom_data_table.setItem(irow, self.custom_icol_conserved, item)

            self.custom_data_table.setCellWidget(irow, self.custom_icol_conserved, w_var_conserved)


            # ------- custom data variable units
            w_var_units = MyQLineEdit()
            w_var_units.setFrame(False)
            w_var_units.setFrame(False)
            # item = QTableWidgetItem('')
            w_var_units.vname = w_varname  
            w_var_units.wrow = irow
            w_var_units.wcol = 3   # beware: hard-coded 
            # w_var_units.idx = irow
            # w_varval.setValidator(QtGui.QDoubleValidator())
            # self.custom_data_table.setItem(irow, self.custom_icol_units, item)
            self.custom_data_table.setCellWidget(irow, self.custom_icol_units, w_var_units)
            w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 


            # ------- custom data variable description
            w_var_desc = MyQLineEdit()
            w_var_desc.setFrame(False)
            # item = QTableWidgetItem('')
            w_var_desc.vname = w_varname  
            w_var_desc.wrow = irow
            w_var_desc.wcol = 4   # beware: hard-coded 
            # w_var_desc.idx = irow
            # w_varval.setValidator(QtGui.QDoubleValidator())
            # self.custom_data_table.setItem(irow, self.custom_icol_desc, item)
            self.custom_data_table.setCellWidget(irow, self.custom_icol_desc, w_var_desc)
            w_var_desc.textChanged[str].connect(self.custom_data_desc_changed)  # being explicit about passing a string 

        vlayout.addWidget(self.custom_data_table)

        #----------
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("click row # to "))

        delete_custom_data_btn = QPushButton("Delete parameter")
        delete_custom_data_btn.clicked.connect(self.delete_custom_data_cb)
        delete_custom_data_btn.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        hlayout.addWidget(delete_custom_data_btn)

        hlayout.addStretch()
        vlayout.addLayout(hlayout)

        #--------------
        self.layout = QVBoxLayout(self)
        # self.layout.addLayout(self.controls_hbox)

        self.layout.addWidget(self.splitter)

        custom_data_tab_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        custom_data_tab_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        custom_data_tab_scroll.setWidgetResizable(True)
        custom_data_tab_scroll.setWidget(custom_data_tab) 


        # custom_data_tab.setLayout(glayout)
        custom_data_tab.setLayout(vlayout)
        return custom_data_tab_scroll

    #----------------------------------------
    def disable_table_cells_for_duplicate_name(self, widget=None):
        # disable all cells in the Custom Data table
        backcolor = "background: lightgray"
        for irow in range(0,self.max_custom_data_rows):
            for icol in range(self.max_custom_data_cols):
                self.custom_data_table.cellWidget(irow,icol).setEnabled(False)
                self.custom_data_table.cellWidget(irow,icol).setStyleSheet(backcolor)   # yellow
                # self.sender().setStyleSheet("color: red;")

        if widget:   # enable only(!) the widget that needs to be fixed (because it's a duplicate)
            wrow = widget.wrow
            wcol = widget.wcol
            self.custom_data_table.cellWidget(wrow,wcol).setEnabled(True)
            # self.custom_data_table.setCurrentItem(None)
            backcolor = "background: white"
            self.custom_data_table.cellWidget(wrow,wcol).setStyleSheet(backcolor)
            self.custom_data_table.setCurrentCell(wrow,wcol)

        # Also disable the cell type tree
        self.tree.setEnabled(False)

    #----------------------------------------
    def enable_all_custom_data(self):
        # for irow in range(self.max_custom_vars):
        # for irow in range(self.max_custom_rows_edited):
        backcolor = "background: white"
        for irow in range(self.max_custom_data_rows):
            for icol in range(5):
                # if (icol != 2) and (irow != row) and (icol != col):
                # if irow > 47:
                    # print("enable all(): irow,icol=",irow,icol)
                # if self.custom_data_table.cellWidget(irow,icol):
                self.custom_data_table.cellWidget(irow,icol).setEnabled(True)
                self.custom_data_table.cellWidget(irow,icol).setStyleSheet(backcolor)
                if icol == 2:
                    self.custom_data_table.cellWidget(irow,icol).setStyleSheet(self.checkbox_style)
                # else:
                    # print("oops!  self.custom_data_table.cellWidget(irow,icol) is None")
                # self.sender().setStyleSheet("color: red;")

        # self.custom_data_table.cellWidget(self.max_custom_rows_edited+1,0).setEnabled(True)
        # self.custom_data_table.cellWidget(self.max_custom_rows_edited+1,0).setStyleSheet("background: white")

        self.tree.setEnabled(True)

    #----------------------------------------
    # Callback when user edits a "Name" cell in the table. Somewhat tricky...
    # (self.master_custom_var_d is created in populate_tree_cell_defs.py if custom vars in .xml)
    def custom_data_name_changed(self, text):
        # logging.debug(f'\n--------- cell_def_tab.py: custom_data tab: custom_data_name_changed() --------')
        if self.rules_tab:
            self.rules_tab.update_rules_for_custom_data = True

        debug_me = False
        if debug_me:
            print(f'\n--------- custom_data_name_changed() --------')
        # logging.debug(f'   self.current_cell_def = {self.current_cell_def}')
        # print("incoming master_custom_var_d= ",self.master_custom_var_d)
        # print(f'custom_data_name_changed():   self.current_cell_def = {self.current_cell_def}')
        # print(f'custom_data_name_changed():   text= {text}')

        if not self.custom_data_edit_active:  # hack to avoid unwanted callback
            # print("--- edit is not active, leaving!")
            return

        vname = self.sender().vname.text()
        # print(f'  len(vname)= {len(vname)}')
        if debug_me:
            print(f'  vname (.text())= {vname}')

        prev_name = self.sender().prev
        if debug_me:
            print(f'  prev_name= {prev_name}')

        len_vname = len(vname)
        # user has deleted the entire name; remove any prev name from the relevant dicts
        if len_vname == 0:
            if debug_me:
                print("--------- handling len(vname)==0 ")
                print("1) master_custom_var_d= ",self.master_custom_var_d)
            if prev_name:
                if debug_me:
                    print(f"--------- pop prev_name {prev_name}")
                self.master_custom_var_d.pop(prev_name)
                # print("2) master_custom_var_d= ",self.master_custom_var_d)
                for cdname in self.param_d.keys():
                    self.param_d[cdname]["custom_data"].pop(prev_name)
                    # print(f"3) self.param_d[{cdname}]['custom_data']= ",self.param_d[cdname]['custom_data'])

                self.sender().prev = None  # update previous to be None
            # return

        else:  # vname has >=1 length
            wrow = self.sender().wrow
            if debug_me:
                print("--------- handling len(vname) >= 1. wrow= ",wrow)
            # next_row = self.sender().wrow + 1
            # print("  len(vname)>=1.  next_row= ",next_row)

            # check for duplicate name; if so, disable entire table forcing this name to be changed
            if vname in self.master_custom_var_d.keys():
                # print(f"-- found {vname} in master_custom_var_d: {self.master_custom_var_d}")
                self.disable_table_cells_for_duplicate_name(self.sender())
                self.custom_table_disabled = True
                # print("--------- 1) leave function")
                return  # --------- leave function


            # else:  # new name is not a duplicate
            elif len_vname == 1:   # starting with a new name (1st char)
                if debug_me:
                    print("pre: wrow, self.max_custom_data_rows= ",wrow,self.max_custom_data_rows)

                # If we're at the last row, add N(=10) more rows to the table.
                if wrow == self.max_custom_data_rows-1:
                    # print("pre: wrow, self.max_custom_data_rows= ",wrow,self.max_custom_data_rows)
                    # print("add 10 rows")
                    for ival in range(10):
                        self.add_row_custom_table(self.max_custom_data_rows+ival)
                    self.max_custom_data_rows += 10
                    # print("post: wrow, self.max_custom_data_rows= ",wrow,self.max_custom_data_rows)
                    # print("self.max_custom_data_rows= ",self.max_custom_data_rows)

                units_str = self.custom_data_table.cellWidget(wrow,self.custom_icol_units).text()
                desc_str = self.custom_data_table.cellWidget(wrow,self.custom_icol_desc).text()
                # self.master_custom_var_d[vname] = ['','']  # default [units, desc]
                if prev_name:
                    # this is replacing a previous name; it's NOT a new var
                    if debug_me:
                        print(f" replace (pop) {prev_name} with {vname} on master_custom_var_d and all param_d cdname")
                        print(f" master_custom_var_d.keys() = {self.master_custom_var_d.keys()} ")
                    self.master_custom_var_d[vname] = self.master_custom_var_d.pop(prev_name)
                    for cdname in self.param_d.keys():
                        self.param_d[cdname]["custom_data"][vname] = self.param_d[cdname]["custom_data"].pop(prev_name)

                else:  # a NEW var
                    if debug_me:
                        print(f" Adding a NEW var {vname}")
                    self.master_custom_var_d[vname] = [wrow, units_str, desc_str]  # default [units, desc]
                # print(f'post adding {vname} --> {self.master_custom_var_d}')

                # -- since we're adding this var for the 1st time, add it to each cell type, using same values
                    val = self.custom_data_table.cellWidget(wrow,self.custom_icol_value).text()
                    bval = self.custom_data_table.cellWidget(wrow,self.custom_icol_conserved).isChecked()
                    for cdname in self.param_d.keys():
                        # print(f'--- cdname= {cdname},  vname={vname}')
                        self.param_d[cdname]["custom_data"][vname] = [val, bval]    # [value, conserved flag] 

                self.sender().prev = vname  # update the previous to be the current

            else:  # length of vname >= 1 
                # print(f'--- len_vname >= 1:  vname={vname},  prev_name={prev_name}')
                if prev_name:   # if this name had a previous name, update it (pop the previous) in the dicts
                    # print(f'----- prev_name={prev_name}')
                    self.master_custom_var_d[vname] = self.master_custom_var_d.pop(prev_name)
                    # print("after replacing prev with new: master_custom_var_d= ",self.master_custom_var_d)
                    # self.master_custom_var_d.pop(prev_name)

                    # units_str = self.custom_data_table.cellWidget(wrow,self.custom_icol_units).text()
                    # desc_str = self.custom_data_table.cellWidget(wrow,self.custom_icol_desc).text()
                    # self.master_custom_var_d[vname] = ['','']  # default [units, desc]
                    # self.master_custom_var_d[vname] = [wrow, units_str, desc_str]  # default [units, desc]
                    # print("after replacing prev with new: master_custom_var_d= ",self.master_custom_var_d)


                    for cdname in self.param_d.keys():
                        # print(f'--- cdname= {cdname},  vname={vname},  prev_name={prev_name}')
                        self.param_d[cdname]["custom_data"][vname] = self.param_d[cdname]["custom_data"].pop(prev_name)
                    self.sender().prev = vname  # update the previous to be the current

                else:
                    # print(f'----- no prev_name; add to dicts')
                    units_str = self.custom_data_table.cellWidget(wrow,self.custom_icol_units).text()
                    desc_str = self.custom_data_table.cellWidget(wrow,self.custom_icol_desc).text()
                    # self.master_custom_var_d[vname] = ['','']  # default [units, desc]
                    self.master_custom_var_d[vname] = [wrow, units_str, desc_str]  # default [units, desc]
                    # print(f"after adding {vname} -->  {self.master_custom_var_d}")

                    val = self.custom_data_table.cellWidget(wrow,self.custom_icol_value).text()
                    bval = self.custom_data_table.cellWidget(wrow,self.custom_icol_conserved).isChecked()
                    for cdname in self.param_d.keys():
                        # print(f'--- cdname= {cdname},  vname={vname}')
                        self.param_d[cdname]["custom_data"][vname] = [val, bval]    # [value, conserved flag] 

                    self.sender().prev = vname  # update the previous to be the current

        self.max_custom_vars = len(self.master_custom_var_d)
        # print("- max_custom_vars = ",self.max_custom_vars)
        # self.sender().prev = vname

        # Let's use whatever is there now

        # print("    master_custom_var_d= ",self.master_custom_var_d)

        if self.custom_table_disabled:
            self.enable_all_custom_data()
            self.custom_table_disabled = False

        old_name = f"custom:{prev_name}"
        new_name = f"custom:{text}"
        self.update_par_dist_behaviors(old_name, new_name)
        # print(f'============== leave custom_data_name_changed() --------')


    #--------------------------------------------------------------
    # Callback when user edit a Value cell in the table. Somewhat tricky...
    def custom_data_value_changed(self, text):
        if not self.current_cell_def:
            return

        if not self.custom_data_edit_active:
            # print("custom_data_value_changed(): returning due to active edit False!")
            return

        # print("custom_data_value_changed(): self.current_cell_def= ",self.current_cell_def)
        # print("self.sender() = ", self.sender())
        vname = self.sender().vname.text()

        wrow = self.sender().wrow
        wcol = self.sender().wcol

        if len(vname) == 0:
            # print("HEY! define var name before value!")
            self.custom_table_error(wrow,wcol,"(#1) Define Name first!")
            self.custom_data_table.cellWidget(wrow,wcol).setText(self.custom_var_value_str_default)

            # item = QTableWidgetItem('')
            # self.custom_data_table.setItem(row, col, item)   # 1st col is var name
            return

        # self.param_d[self.current_cell_def]['custom_data'][vname] = [text, conserved_flag]  
        self.param_d[self.current_cell_def]['custom_data'][vname][0] = text  # [value, conserved flag]
        # print("custom_data_value_changed(): = self.param_d[self.current_cell_def]['custom_data'][vname][0]",self.param_d[self.current_cell_def]['custom_data'][vname][0])

    #----------------------------------------
    def custom_var_conserved_clicked(self,bval):
        # print("== custom_var_conserved_clicked(): bval=",bval)
        if not self.current_cell_def:
            return

        if not self.custom_data_edit_active:
            # print("custom_var_conserved_clicked(): returning due to active edit False!")
            return
        # print("self.sender().wrow = ", self.sender().wrow)
        vname = self.sender().vname.text()
        # print("    vname= ",vname)

        wrow = self.sender().wrow
        wcol = self.sender().wcol

        if len(vname) == 0:
            # print("HEY! define var name before clicking conserved flag!")
            self.custom_table_error(wrow,wcol,"(#2) Define Name first!")
            self.custom_data_table.cellWidget(wrow,wcol).setChecked(False)
            return

        self.param_d[self.current_cell_def]['custom_data'][vname][1] = bval  # [value, conserved flag]
        # print("custom_data_value_changed(): = self.param_d[self.current_cell_def]['custom_data'][vname][0]",self.param_d[self.current_cell_def]['custom_data'][vname][0])


    #----------------------------------------
    # NOTE: it doesn't matter what cell type is selected; units are the same for ALL. Just unique to custom var name.
    def custom_data_units_changed(self, text):
        debug_me = False
        # logging.debug(f'\n--------- cell_def_tab.py: custom_data_units_changed() --------')
        # logging.debug(f'   self.current_cell_def = {self.current_cell_def}')
        if debug_me:
            print(f'custom_data_units_changed():   self.current_cell_def = {self.current_cell_def}')
            print(f'custom_data_units_changed(): ----  text= {text}')

        # print("self.sender().wrow = ", self.sender().wrow)
        varname = self.sender().vname.text()
        if debug_me:
            print("    varname= ",varname)
        wrow = self.sender().wrow
        wcol = self.sender().wcol

        if len(varname) == 0 and self.custom_data_edit_active:
            # print("HEY! define var name before clicking conserved flag!")
            self.custom_table_error(wrow,wcol,"(#3) Define Name first!")
            # for line in traceback.format_stack():
            #     print(line.strip())
            # self.custom_data_table.cellWidget(wrow,wcol).setText(self.custom_var_value_str_default)
            return

        # print(f"-------   its varname is {varname}")
        if varname not in self.master_custom_var_d.keys():
            self.master_custom_var_d[varname] = [wrow, '', '']   # [wrow, units, desc]
        self.master_custom_var_d[varname][1] = text   # hack, hard-coded
        # print("self.master_custom_var_d[varname]= ",self.master_custom_var_d[varname])

        # print(f'============== leave custom_data_units_changed() --------')

    #----------------------------------------
    def custom_data_desc_changed(self, text):
        # logging.debug(f'\n--------- cell_def_tab.py: custom_data_desc_changed() --------')
        # print(f'custom_data_desc_changed():   self.current_cell_def = {self.current_cell_def}')
        # print(f'custom_data_desc_changed():   text= {text}')

        varname = self.sender().vname.text()
        # print("    varname= ",varname)
        wrow = self.sender().wrow
        wcol = self.sender().wcol

        if len(varname) == 0 and self.custom_data_edit_active:
            # print("HEY! define var name before clicking conserved flag!")
            self.custom_table_error(wrow,wcol,"(#4) Define Name first!")
            # self.custom_data_table.cellWidget(wrow,wcol).setText(self.custom_var_value_str_default)
            return

        # print(f"-------   its varname is {varname}")
        if varname not in self.master_custom_var_d.keys():
            self.master_custom_var_d[varname] = [wroww, '', '']   # [wrow, units, desc]
        self.master_custom_var_d[varname][2] = text  # hack, hard-code
        # print("self.master_custom_var_d[varname]= ",self.master_custom_var_d[varname])

        # print(f'============== leave custom_data_desc_changed() --------')


    #--------------------------------------------------------
    # called from studio.py for a new model
    def clear_custom_data_tab(self):
        # logging.debug(f'\n\n------- cell_def_tab.py: clear_custom_data_tab(self):  self.custom_var_count = {self.custom_var_count}')

        self.custom_data_edit_active = False

        for irow in range(self.max_custom_data_rows):
            self.custom_data_table.cellWidget(irow,self.custom_icol_name).setText('')
            self.custom_data_table.cellWidget(irow,self.custom_icol_value).setText('0.0')
            self.custom_data_table.cellWidget(irow,self.custom_icol_conserved).setCheckState(False)
            self.custom_data_table.cellWidget(irow,self.custom_icol_units).setText('')
            self.custom_data_table.cellWidget(irow,self.custom_icol_desc).setText('')
        
        self.custom_data_search.setText('')

        self.custom_data_edit_active = True

    #--------------------------------------------------------
    def create_miscellaneous_tab(self):
            
        par_dist_label = QLabelSeparator("Parameter Distributions")

        self.par_dist_cell_type_disabled_checkbox = QCheckBox_custom(f"Disable all parameter distributions for {self.current_cell_def}")
        self.par_dist_cell_type_disabled_checkbox.stateChanged.connect(self.par_dist_cell_type_disabled_cb)

        self.par_dist_display_button = QPushButton("Display/update distributions for current cell type.")
        self.par_dist_display_button.clicked.connect(self.par_dist_display_button_cb)

        hbox_cell_type_par_dist = QHBoxLayout()
        hbox_cell_type_par_dist.addWidget(self.par_dist_cell_type_disabled_checkbox)
        hbox_cell_type_par_dist.addWidget(self.par_dist_display_button)
        hbox_cell_type_par_dist.addStretch()

        self.behavior_model = QStandardItemModel()
        self.par_dist_behavior_combobox = ExtendedCombo()
        self.par_dist_behavior_combobox.setModel(self.behavior_model)
        self.par_dist_behavior_combobox.setModelColumn(0)
        self.par_dist_behavior_combobox.currentIndexChanged.connect(self.par_dist_behavior_changed_cb)
        self.par_dist_behavior_combobox.editTextChanged.connect(self.par_dist_behavior_text_changed_cb)

        self.par_dist_enable_checkbox = QCheckBox_custom("Enable")
        self.par_dist_enable_checkbox.stateChanged.connect(self.par_dist_enable_cb)

        self.par_distributions_combobox = QComboBox_custom()
        self.par_distributions_combobox.addItems(["None", "Uniform", "Log Uniform", "Normal", "Log Normal", "Log10 Normal"])
        self.par_distributions_combobox.currentIndexChanged.connect(self.par_distribution_changed_cb)

        self.par_dist_enforce_base_checkbox = QCheckBox_custom("Enforce base value within distribution")
        self.par_dist_enforce_base_checkbox.stateChanged.connect(self.par_dist_enforce_base_cb)
        self.par_dist_enforce_base_question_label = HoverQuestion("Enforced at PhysiCell runtime.")

        self.par_dist_distribution_equation = QLabel("")

        hbox_par_dist_1 = QHBoxLayout()

        hbox_par_dist_1.addWidget(QLabel("Behavior:"))
        hbox_par_dist_1.addWidget(self.par_dist_behavior_combobox)
        hbox_par_dist_1.addWidget(self.par_dist_enable_checkbox)
        hbox_par_dist_1.addStretch()

        hbox_par_dist_2 = QHBoxLayout()

        hbox_par_dist_2.addWidget(QLabel("Distribution:"))
        hbox_par_dist_2.addWidget(self.par_distributions_combobox)

        hbox_par_dist_2.addWidget(self.par_dist_enforce_base_checkbox)
        hbox_par_dist_2.addWidget(self.par_dist_enforce_base_question_label)
        hbox_par_dist_2.addStretch()
        hbox_par_dist_2.addWidget(self.par_dist_distribution_equation)

        hbox_par_dist_parameters = QHBoxLayout()
        self.par_dist_par_label = []
        self.par_dist_par_lineedit = []
        self.help_stacks = {}
        for i in range(4):
            self.par_dist_par_label.append(QLabel(""))
            qline_edt = QLineEdit_custom(enabled=False)
            qline_edt.setValidator(QtGui.QDoubleValidator())
            qline_edt.textChanged.connect(self.par_dist_parameters_changed_cb)
            self.par_dist_par_lineedit.append(qline_edt)
            hbox_par_dist_parameters.addWidget(self.par_dist_par_label[i])
            hbox_par_dist_parameters.addWidget(self.par_dist_par_lineedit[i])
            help_stack = QStackedWidget()
            help_stack.addWidget(HoverWarning("")) # remember that the warning is index 0
            help_stack.addWidget(HoverQuestion("")) # ...and the question is index 1
            help_stack.setFixedWidth(15)
            help_stack.setFixedHeight(15)
            self.help_stacks[qline_edt] = help_stack
            hbox_par_dist_parameters.addWidget(help_stack)

        vbox = QVBoxLayout()
        vbox.addWidget(par_dist_label)
        vbox.addLayout(hbox_cell_type_par_dist)
        vbox.addLayout(hbox_par_dist_1)
        vbox.addLayout(hbox_par_dist_2)
        vbox.addLayout(hbox_par_dist_parameters)
        vbox.addStretch()

        miscellaneous_tab = QWidget()
        miscellaneous_tab.setLayout(vbox)

        miscellaneous_tab_scroll_area = QScrollArea()
        miscellaneous_tab_scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        miscellaneous_tab_scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        miscellaneous_tab_scroll_area.setWidgetResizable(True)
        miscellaneous_tab_scroll_area.setWidget(miscellaneous_tab)

        return miscellaneous_tab_scroll_area

    def par_dist_cell_type_disabled_cb(self, state):
        if self.current_cell_def is None: # happens at studio initialization
            return
        enabled = state != QtCore.Qt.Checked
        self.param_d[self.current_cell_def]["par_dists_disabled"] = (not enabled)
        self.par_dist_display_button.setEnabled(enabled)
        self.par_dist_behavior_combobox.setEnabled(enabled)
        if enabled:
            # par_dist_behavior_combobox will handle enabling par_dist_enable_checkbox if necessary
            self.par_dist_behavior_combobox.editTextChanged.emit(self.par_dist_behavior_combobox.currentText())
        else:
            self.par_dist_enable_checkbox.setEnabled(False)
            self.par_dist_distribution_widgets_set_enabled(False)

    def par_dist_display_button_cb(self):
        # create new window and print distribution infomration there
        if self.current_cell_def is None:
            return
        if self.current_cell_def not in self.param_d.keys():
            return
        if "par_dists" not in self.param_d[self.current_cell_def].keys():
            return
        if len(self.param_d[self.current_cell_def]["par_dists"]) == 0:
            return
        
        # create new window
        self.par_dist_window = QWidget()
        self.par_dist_window.setWindowTitle(f"Parameter Distributions for {self.current_cell_def}")
        self.par_dist_window.setGeometry(100, 100, 800, 600)
        vbox = QVBoxLayout()
        
        for key, value in self.param_d[self.current_cell_def]["par_dists"].items():
            if "distribution" not in value.keys() or value["distribution"] == "None":
                continue
            # add a line to the QDialog box about this parameter distribution
            label = QLabel(f"Behavior: {key}\nEnabled: {value['enabled']}\nDistribution: {value['distribution']}\nParameters: {value['parameters']}\nCheck base: {value['enforce_base']}")
            vbox.addWidget(label)
        
        vbox.addStretch()
        self.par_dist_window.setLayout(vbox)
        self.par_dist_window.hide()
        self.par_dist_window.show()

    def par_dist_current_responses(self):
        return [self.par_dist_behavior_combobox.itemText(i) for i in range(self.par_dist_behavior_combobox.count())]

    def par_dist_fill_responses_widget(self, response_l):
        # loop over all current items in the combobox and check if they are in the response list
        current_response_list = self.par_dist_current_responses()
        for response in current_response_list:
            if response not in response_l:
                self.par_dist_behavior_combobox.removeItem(self.par_dist_behavior_combobox.findText(response))
        for response in response_l:
            # check if response is an item in self.par_dist_behavior_combobox
            if self.par_dist_behavior_combobox.findText(response) == -1:
                self.par_dist_behavior_combobox.addItem(response)

    def par_dist_behavior_text_changed_cb(self, text):
        if not self.is_behavior(text):
            self.par_dist_enable_checkbox.setEnabled(False)
            self.par_dist_distribution_widgets_set_enabled(False)
        elif (self.current_cell_def in self.param_d.keys()) and (not self.param_d[self.current_cell_def]["par_dists_disabled"]):
            self.create_behavior_dict(self.current_cell_def, text, overwrite=False) # include keyword to emphasize to future devs that we are not overwriting the dict if it exists
            self.par_dist_enable_checkbox.setEnabled(True)
            self.par_dist_behavior_combobox.currentIndexChanged.emit(self.par_dist_behavior_combobox.currentIndex()) # force this cb now even before the user hits tab/enter/leaves focus and causes the update (it can be confusing to see the previous index pars before hitting enter)
       
    def par_dist_behavior_changed_cb(self, idx):
        cdname = self.current_cell_def
        if cdname is None or cdname not in self.param_d.keys():
            return # make sure this cell type is one we want (e.g. not currently being deleted)
        behavior = self.par_dist_behavior_combobox.currentText()
        if behavior == '' or self.param_d[cdname]["par_dists_disabled"]:
            return # this can happen when new behaviors are added and the list is cleared OR if the distributions are disabled but the behavior box is updated for other reasons

        if behavior not in self.param_d[cdname]["par_dists"].keys():
            self.create_behavior_dict(cdname, behavior, overwrite=False) # include keyword to emphasize to future devs that we are not overwriting the dict if it exists
            if self.par_dist_enable_checkbox.isChecked(): # set the enabled to False if the checkbox is checked
                self.par_dist_enable_checkbox.setChecked(False)
            else: # otherwise, emit the unchecked state to deactivate downstream widgets
                self.par_dist_enable_checkbox.stateChanged.emit(QtCore.Qt.Unchecked)
            self.par_dist_enforce_base_checkbox.setChecked(False)
            if self.par_distributions_combobox.currentIndex() == 0:
                self.par_distributions_combobox.currentIndexChanged.emit(0)
            else:
                self.par_distributions_combobox.setCurrentIndex(0) # reset to distribution to None
        else: # behavior has previously been set, proceed with caution based on prev distribution and current distribution
            old_dict = copy.deepcopy(self.param_d[cdname]["par_dists"][behavior]["parameters"])
            if self.param_d[cdname]["par_dists"][behavior]["distribution"] != self.par_distributions_combobox.currentText():
                self.par_distributions_combobox.setCurrentIndex(self.par_distributions_combobox.findText(self.param_d[cdname]["par_dists"][behavior]["distribution"]))
            else:
                self.par_distributions_combobox.currentIndexChanged.emit(self.par_distributions_combobox.currentIndex())
            self.par_dist_set_pars_from_dict(old_dict)
            self.par_dist_enforce_base_checkbox.setChecked(self.param_d[cdname]["par_dists"][behavior]["enforce_base"])
            if self.par_dist_enable_checkbox.isChecked() != self.param_d[cdname]["par_dists"][behavior]["enabled"]:
                # if the checkbox is not in the correct state, set it to the correct state (and thus emit the correct state)
                self.par_dist_enable_checkbox.setChecked(self.param_d[cdname]["par_dists"][behavior]["enabled"])
            else:
                # no need to toggle the checkbox, just emit the current state
                self.par_dist_enable_checkbox.stateChanged.emit(self.par_dist_enable_checkbox.checkState())
    
    def par_dist_enable_cb(self, state):
        bval = state == QtCore.Qt.Checked
        behavior = self.par_dist_behavior_combobox.currentText()
        if behavior in self.param_d[self.current_cell_def]["par_dists"].keys():
            self.param_d[self.current_cell_def]["par_dists"][self.par_dist_behavior_combobox.currentText()]["enabled"] = bval
        self.par_dist_distribution_widgets_set_enabled(bval)
        if bval:
            # if we are enabling the distribution, emit the signal of selecting this distribution
            self.par_distributions_combobox.currentIndexChanged.emit(self.par_distributions_combobox.currentIndex())

    def par_dist_distribution_widgets_set_enabled(self, enabled):
        # enable everything downstream of the behavior: the distribution, enforcement, and parameters
        # if disabling the parameters, hide the help stacks
        self.par_distributions_combobox.setEnabled(enabled)
        self.par_dist_enforce_base_checkbox.setEnabled(enabled)
        for pdple in self.par_dist_par_lineedit:
            pdple.setEnabled(enabled)
            if not enabled:
                self.par_dist_hide_help_stack(self.help_stacks[pdple])
                
    def par_distribution_changed_cb(self, idx):
        cdname = self.current_cell_def
        if cdname is None or cdname not in self.param_d.keys():
            return # make sure this cell type is one we want (e.g. not currently being deleted)
        current_dist = self.par_distributions_combobox.currentText()
        behavior = self.par_dist_behavior_combobox.currentText()
        self.create_behavior_dict(cdname, behavior, overwrite=False) # include keyword to emphasize to future devs that we are not overwriting the dict if it exists
        self.par_dist_enforce_base_checkbox.setChecked(self.param_d[cdname]["par_dists"][behavior]["enforce_base"])
        if ("distribution" in self.param_d[cdname]["par_dists"][behavior].keys()) and (current_dist == self.param_d[cdname]["par_dists"][behavior]["distribution"]):
            # if we have the correct distribution already in a dict, note this so we make use of those parameters
            distribution_pars_in_dict = True
        else:
            # otherwise, we don't want to keep the old parameters (if they even exist); we will create a brand new dictionary below
            distribution_pars_in_dict = False

        self.param_d[cdname]["par_dists"][behavior]["distribution"] = current_dist

        # next, find the distribution and update fields
        par_labels = [""] * 4
        par_texts = [""] * 4
        # default to hiding all icons
        for pdple in self.par_dist_par_lineedit:
            help_stack = self.help_stacks[pdple]
            self.par_dist_hide_help_stack(help_stack)

        if current_dist == "None":
            par_enabled = [False] * 4
            self.param_d[cdname]["par_dists"][behavior]["parameters"] = {}
            self.par_dist_distribution_equation.setText("")
        elif current_dist == "Uniform" or current_dist == "Log Uniform":
            par_labels[0] = "Min:"
            self.par_dist_par_lineedit[0].setObjectName("min")
            par_labels[1] = "Max:"
            self.par_dist_par_lineedit[1].setObjectName("max")
            if current_dist == "Uniform":
                self.par_dist_par_lineedit[0].setValidator(QtGui.QDoubleValidator())
                help_stack = self.help_stacks[self.par_dist_par_lineedit[0]]
                help_stack.widget(0).setHoverText("Min is required!")
                self.par_dist_par_lineedit[1].setValidator(QtGui.QDoubleValidator())
                help_stack = self.help_stacks[self.par_dist_par_lineedit[1]]
                help_stack.widget(0).setHoverText("Max is required!")
                self.par_dist_distribution_equation.setText("Behavior ~ U(Min, Max)")
            elif current_dist == "Log Uniform": # log uniform must be postive
                self.par_dist_par_lineedit[0].setValidator(DoubleValidatorOpenInterval(bottom=0))
                help_stack = self.help_stacks[self.par_dist_par_lineedit[0]]
                help_stack.widget(0).setHoverText("Min is required! And it must be > 0.")
                help_stack.widget(1).setHoverText("Min represents the actual behavior value, not the exponent.\nMin must be positive.")
                help_stack.widget(1).show_icon()
                self.par_dist_par_lineedit[1].setValidator(DoubleValidatorOpenInterval(bottom=0))
                help_stack = self.help_stacks[self.par_dist_par_lineedit[1]]
                help_stack.widget(0).setHoverText("Max is required! And it must be > 0.")
                help_stack.widget(1).setHoverText("Max represents the actual behavior value, not the exponent.\nMax must be positive.")
                help_stack.widget(1).show_icon()
                self.par_dist_distribution_equation.setText("Behavior ~ exp(Z)\nZ ~ U(log(Min), log(Max))")
            else:
                raise NotImplementedError(f"Error: Invalid distribution selected??? Current distribution = {current_dist} is not among those we have a formula for displaying. Whoever added this distribution should add a formula here.")

            par_enabled = [True, True, False, False]
            if distribution_pars_in_dict:
                if "min" in self.param_d[cdname]["par_dists"][behavior]["parameters"].keys():
                    par_texts[0] = self.param_d[cdname]["par_dists"][behavior]["parameters"]["min"]
                if "max" in self.param_d[cdname]["par_dists"][behavior]["parameters"].keys():
                    par_texts[1] = self.param_d[cdname]["par_dists"][behavior]["parameters"]["max"]
            else:
                new_dict = {"min": "", "max": ""}
                self.param_d[cdname]["par_dists"][behavior]["parameters"] = new_dict
        else:
            par_enabled = [True] * 4
            if current_dist == "Normal":
                par_labels[0] = "Mean:"
                help_stack = self.help_stacks[self.par_dist_par_lineedit[0]]
                help_stack.widget(0).setHoverText("Mean is required!")
                par_labels[1] = "Std Dev:"
                help_stack = self.help_stacks[self.par_dist_par_lineedit[1]]
                help_stack.widget(0).setHoverText("Std Dev is required!")
                # set these here rather than checking again later
                self.par_dist_par_lineedit[2].setValidator(OptionalDoubleValidator())
                self.par_dist_par_lineedit[3].setValidator(OptionalDoubleValidator())
                self.par_dist_distribution_equation.setText("Behavior ~ N(Mean, Std Dev)\nlb \u2264 Behavior \u2264 ub")
            elif current_dist == "Log Normal" or current_dist == "Log10 Normal":
                par_labels[0] = "\u03BC:"
                help_stack = self.help_stacks[self.par_dist_par_lineedit[0]]
                help_stack.widget(0).setHoverText("\u03BC is required!\n\u03BC can be negative as it represents the exponent.")
                help_stack.widget(1).setHoverText("\u03BC represents the exponent, not the actual behavior value.\n\u03BC can be negative.")
                help_stack.widget(1).show_icon()
                par_labels[1] = "\u03C3:"
                help_stack = self.help_stacks[self.par_dist_par_lineedit[1]]
                help_stack.widget(0).setHoverText("\u03C3 is required!\n\u03C3 must be > 0 as it represents the standard deviation of the exponent.")
                help_stack.widget(1).setHoverText("\u03C3 represents the standard deviation of the exponent, not the actual behavior value.\n\u03C3 must be > 0.")
                help_stack.widget(1).show_icon()
                # set these here rather than checking again later
                self.par_dist_par_lineedit[2].setValidator(OptionalDoubleValidator(bottom=0))
                help_stack = self.help_stacks[self.par_dist_par_lineedit[2]]
                help_stack.widget(1).setHoverText("Lower bound is on the behavior values, not the exponent.\nThus, it must be non-negative.\nSetting to 0 allows arbitrarily small, positive behavior values.")
                help_stack.widget(1).show_icon()
                self.par_dist_par_lineedit[3].setValidator(OptionalDoubleValidator(bottom=0))
                help_stack = self.help_stacks[self.par_dist_par_lineedit[3]]
                help_stack.widget(1).setHoverText("Upper bound is on the behavior values, not the exponent.\nThus, it must be positive.\nSetting this to 0 would result in an ill-formed distribution.")
                help_stack.widget(1).show_icon()
                if current_dist == "Log Normal":
                    self.par_dist_distribution_equation.setText("Behavior ~ exp(Z), Z ~ N(\u03BC, \u03C3)\nlb \u2264 Behavior \u2264 ub")
                else:
                    self.par_dist_distribution_equation.setText("Behavior ~ 10^Z, Z ~ N(\u03BC, \u03C3)\nlb \u2264 Behavior \u2264 ub")
            else:
                raise ValueError(f"Error: Invalid distribution selected??? Current distribution = {current_dist}")

            par_labels[2] = "Lower Bound (optional):"
            par_labels[3] = "Upper Bound (optional):"

            self.par_dist_par_lineedit[0].setObjectName("mu")
            self.par_dist_par_lineedit[0].setValidator(QtGui.QDoubleValidator())
            self.par_dist_par_lineedit[1].setObjectName("sigma")
            self.par_dist_par_lineedit[1].setValidator(QtGui.QDoubleValidator(bottom=0))
            self.par_dist_par_lineedit[2].setObjectName("lower_bound") # validator set above
            self.par_dist_par_lineedit[3].setObjectName("upper_bound") # validator set above

            if distribution_pars_in_dict:
                if "mu" in self.param_d[cdname]["par_dists"][behavior]["parameters"].keys():
                    par_texts[0] = self.param_d[cdname]["par_dists"][behavior]["parameters"]["mu"]
                if "sigma" in self.param_d[cdname]["par_dists"][behavior]["parameters"].keys():
                    par_texts[1] = self.param_d[cdname]["par_dists"][behavior]["parameters"]["sigma"]
                if "lower_bound" in self.param_d[cdname]["par_dists"][behavior]["parameters"].keys():
                    par_texts[2] = self.param_d[cdname]["par_dists"][behavior]["parameters"]["lower_bound"]
                if "upper_bound" in self.param_d[cdname]["par_dists"][behavior]["parameters"].keys():
                    par_texts[3] = self.param_d[cdname]["par_dists"][behavior]["parameters"]["upper_bound"]
            else:
                new_dict = {"mu": "", "sigma": "", "lower_bound": "", "upper_bound": ""}
                self.param_d[cdname]["par_dists"][behavior]["parameters"] = new_dict

        for pdpl, pdple, label, text, enabled in zip(self.par_dist_par_label, self.par_dist_par_lineedit, par_labels, par_texts, par_enabled):
            # actually set all the stuff gathered above
            pdpl.setText(label)
            pdple.setEnabled(enabled) # disable it first so that the textChanged signal triggers the right callbacks
            pdple.setText(text)

        self.par_dist_validate_all_parameters() # possibly redundant, originally added to allow for higher-order parameter checks, e.g. make sure that min<max. decided that's just on the user

    def par_dist_set_pars_from_dict(self, par_d):
        # get the pars from the dictionary and write to the line edits
        for pdple in self.par_dist_par_lineedit:
            pdple.setText("") # reset all the text before filling it in
        for k, v in par_d.items():
            if k == "min":
                self.par_dist_par_lineedit[0].setText(v)
            elif k == "max":
                self.par_dist_par_lineedit[1].setText(v)
            elif k == "mu":
                self.par_dist_par_lineedit[0].setText(v)
            elif k == "sigma":
                self.par_dist_par_lineedit[1].setText(v)
            elif k == "lower_bound":
                self.par_dist_par_lineedit[2].setText(v)
            elif k == "upper_bound":
                self.par_dist_par_lineedit[3].setText(v)
            else:
                raise ValueError(f"Error: Invalid parameter key {k} in par_dist_set_pars_from_dict()")

    def par_dist_validate_all_parameters(self):
        # this was written to validate that min<max values, but I have set that side project aside for now because it was slowing down key dev
        # I think it is still unnecessary, but the help stacks may actually depend on this, so I'm leaving it in for now
        for pdple in self.par_dist_par_lineedit:
            if pdple.isEnabled():
                is_acceptable = pdple.check_validity(pdple.text())
                self.par_dist_toggle_help_stack(pdple, is_acceptable)

    def par_dist_enforce_base_cb(self, state):
        if self.current_cell_def is None:
            return
        behavior = self.par_dist_behavior_combobox.currentText()
        if behavior in self.param_d[self.current_cell_def]["par_dists"].keys():
            self.param_d[self.current_cell_def]["par_dists"][self.par_dist_behavior_combobox.currentText()]["enforce_base"] = state == QtCore.Qt.Checked
        if state == QtCore.Qt.Checked:
            self.par_dist_enforce_base_question_label.show_icon()
        else:
            self.par_dist_enforce_base_question_label.hide_icon()
    
    def par_dist_hide_help_stack(self, help_stack):
        for i in range(help_stack.count()):
            help_stack.widget(i).hide_icon()

    def par_dist_toggle_help_stack(self, sender, is_acceptable):
        help_stack = self.help_stacks[sender]
        if sender.isEnabled() == False:
            self.par_dist_hide_help_stack(help_stack)
            return
        if not is_acceptable:
            help_stack.setCurrentIndex(0)
            help_stack.widget(0).show_icon()
        else:
            help_stack.setCurrentIndex(1)
    
    def par_dist_parameters_changed_cb(self, text):
        # single callback for any parameter line edits changes
        # makes sure everything looks good, updates help icons, and updates the dictionary
        if self.current_cell_def is None:
            return
        sender = self.sender()
        object_name = sender.objectName()
        if object_name == "":
            return # likely reaching here during startup
        is_acceptable = sender.check_validity(text)
        self.par_dist_toggle_help_stack(sender, is_acceptable)
        behavior = self.par_dist_behavior_combobox.currentText()
        if behavior in self.param_d[self.current_cell_def]["par_dists"].keys():
            self.param_d[self.current_cell_def]["par_dists"][behavior]["parameters"][object_name] = text
            self.par_dist_validate_all_parameters()
        
    def create_behavior_dict(self, cdname, behavior, overwrite=False):
        if cdname not in self.param_d.keys():
            raise ValueError(f"create_behavior_dict(): {cdname} not in self.param_d.keys(). It should always be in the dictionary!")
        if "par_dists" not in self.param_d[cdname].keys():
            self.param_d[cdname]["par_dists"] = {}
        new_dict = {"enabled": False, "distribution": "None", "enforce_base": False, "parameters": {}}
        if overwrite or (behavior not in self.param_d[cdname]["par_dists"].keys()):
            self.param_d[cdname]["par_dists"][behavior] = new_dict
        else: # add any missing keys to default values
            for k in new_dict.keys():
                if (k not in self.param_d[cdname]["par_dists"][behavior].keys()):
                    self.param_d[cdname]["par_dists"][behavior][k] = new_dict[k]

    def is_behavior(self, text):
        return text in self.par_dist_current_responses()
    
    def current_text_is_behavior(self):
        return self.is_behavior(self.par_dist_behavior_combobox.currentText())

    #--------------------------------------------------------
    # @QtCore.Slot()
    def cycle_changed_cb(self, idx):
        if self.current_cell_def:
            self.param_d[self.current_cell_def]['cycle_choice_idx'] = idx

        self.customize_cycle_choices()

    def motility_substrate_changed_cb(self, idx):
        logging.debug(f'------ motility_substrate_changed_cb(): idx = {idx}')
        logging.debug(f'       motility_substrate_changed_cb(): self.current_cell_def = {self.current_cell_def}')
        if self.current_cell_def == None:
            return
        val = self.motility_substrate_dropdown.currentText()
        logging.debug(f'                         text = {val}')
        # print(self.param_d[self.current_cell_def])
        self.param_d[self.current_cell_def]["motility_chemotaxis_substrate"] = val
        # self.param_d[cell_def_name]["motility_chemotaxis_idx"] = idx

        if idx == -1:
            return

    def motility2_substrate_changed_cb(self, idx):  # dropdown widget
        logging.debug(f'------ motility2_substrate_changed_cb(): idx = {idx}')

        subname = self.motility2_substrate_dropdown.currentText()
        logging.debug(f'   text (subname) = {subname}')
        if subname == '':
            logging.debug(f'   subname is empty, return!')
            return
        if self.current_cell_def == None:
            return
        if subname not in self.param_d[self.current_cell_def]['chemotactic_sensitivity'].keys():
            logging.debug(f'   subname is empty, return!')
            return

        self.param_d[self.current_cell_def]['motility_advanced_chemotaxis_substrate'] = subname  # rwh - why have this??
        logging.debug(f'    motility_advanced_chemotaxis_substrate= {self.param_d[self.current_cell_def]["motility_advanced_chemotaxis_substrate"]}')
        # self.param_d[cell_def_name]["motility_chemotaxis_idx"] = idx

        # print(self.chemotactic_sensitivity_dict[val])
        logging.debug(f'   chemotactic_sensitivity = {self.param_d[self.current_cell_def]["chemotactic_sensitivity"]}')
        newval = self.param_d[self.current_cell_def]['chemotactic_sensitivity'][subname]
        # print(" .  newval= ",newval)
        self.chemo_sensitivity.setText(newval)

        if idx == -1:
            return

    #---- in mechanics subtab
    def cell_adhesion_affinity_dropdown_changed_cb(self, idx):
        print('\n------ cell_adhesion_affinity_dropdown_changed_cb(): idx = ',idx)

        celltype_name = self.cell_adhesion_affinity_dropdown.currentText()
        self.cell_adhesion_affinity_celltype = celltype_name
        print("   self.cell_adhesion_affinity_celltype = ",celltype_name)

        if self.cell_adhesion_affinity_celltype in self.param_d[self.current_cell_def]["cell_adhesion_affinity"].keys():
            self.cell_adhesion_affinity.setText(self.param_d[self.current_cell_def]["cell_adhesion_affinity"][self.cell_adhesion_affinity_celltype])
        else:
            self.cell_adhesion_affinity.setText(self.default_affinity)

        if idx == -1:
            return

    #---- in interactions subtab
    def live_phagocytosis_dropdown_changed_cb(self, idx):
        celltype_name = self.live_phagocytosis_dropdown.currentText()
        self.live_phagocytosis_celltype = celltype_name

        if self.live_phagocytosis_celltype in self.param_d[self.current_cell_def]["live_phagocytosis_rate"].keys():
            self.live_phagocytosis_rate.setText(self.param_d[self.current_cell_def]["live_phagocytosis_rate"][self.live_phagocytosis_celltype])
        else:
            self.live_phagocytosis_rate.setText(self.default_sval)

        if idx == -1:
            return

    def attack_rate_dropdown_changed_cb(self, idx):
        celltype_name = self.attack_rate_dropdown.currentText()
        self.attack_rate_celltype = celltype_name

        if self.attack_rate_celltype in self.param_d[self.current_cell_def]["attack_rate"].keys():
            self.attack_rate.setText(self.param_d[self.current_cell_def]["attack_rate"][self.attack_rate_celltype])
        else:
            self.attack_rate.setText(self.default_sval)

        if idx == -1:
            return

    def fusion_rate_dropdown_changed_cb(self, idx):
        celltype_name = self.fusion_rate_dropdown.currentText()
        self.fusion_rate_celltype = celltype_name

        if self.fusion_rate_celltype in self.param_d[self.current_cell_def]["fusion_rate"].keys():
            self.fusion_rate.setText(self.param_d[self.current_cell_def]["fusion_rate"][self.fusion_rate_celltype])
        else:
            self.fusion_rate.setText(self.default_sval)

        if idx == -1:
            return

    def cell_transformation_dropdown_changed_cb(self, idx):
        celltype_name = self.cell_transformation_dropdown.currentText()
        self.transformation_rate_celltype = celltype_name

        if self.transformation_rate_celltype in self.param_d[self.current_cell_def]["transformation_rate"].keys():
            # print("       setText for ", self.transformation_rate_celltype, " = ",self.default_sval)
            self.transformation_rate.setText(self.param_d[self.current_cell_def]["transformation_rate"][self.transformation_rate_celltype])
        else:
            # print("       setText = (default)= ",self.default_sval)
            self.transformation_rate.setText(self.default_sval)

        if idx == -1:
            return

    def immunogenicity_dropdown_changed_cb(self, idx):
        celltype_name = self.cell_transformation_dropdown.currentText()
        self.transformation_rate_celltype = celltype_name

        if self.transformation_rate_celltype in self.param_d[self.current_cell_def]["transformation_rate"].keys():
            self.transformation_rate.setText(self.param_d[self.current_cell_def]["transformation_rate"][self.transformation_rate_celltype])
        else:
            self.transformation_rate.setText(self.default_sval)

        if idx == -1:
            return


    #---------------------------
    # @QtCore.Slot()
    def secretion_substrate_changed_cb(self, idx):
        # print('------ secretion_substrate_changed_cb(): idx = ',idx)
        self.current_secretion_substrate = self.secretion_substrate_dropdown.currentText()
        # print("    self.current_secretion_substrate = ",self.current_secretion_substrate)
        if idx == -1:
            return

        self.update_secretion_params()

        # uep = self.xml_root.find('.//microenvironment_setup')  # find unique entry point
        # secretion_substrate_path = self.xml_root.find(".//cell_definitions//cell_definition[" + str(self.idx_current_cell_def) + "]//phenotype//secretion//substrate[" + str(idx+1) + "]")
        # if (secretion_substrate_path):
        #     print(secretion_substrate_path)

        # <substrate name="virus">
        #     <secretion_rate units="1/min">0</secretion_rate>
        #     <secretion_target units="substrate density">1</secretion_target>
        #     <uptake_rate units="1/min">10</uptake_rate>
        #     <net_export_rate units="total substrate/min">0</net_export_rate> 
        # </substrate> 
        # uep = self.xml_root.find(".//cell_definitions//cell_definition")
        # print(" secretion_rate=", secretion_substrate_path.find('.//secretion_rate').text ) 
        # self.secretion_rate.setText(secretion_substrate_path.find(".//secretion_rate").text)
        # self.secretion_target.setText(secretion_substrate_path.find(".//secretion_target").text)
        # self.uptake_rate.setText(secretion_substrate_path.find(".//uptake_rate").text)
        # self.secretion_net_export_rate.setText(secretion_substrate_path.find(".//net_export_rate").text)


    #-------------------------------------------------------------------------------------
        # self.cycle_dropdown.addItem("live cells")   # 0 -> 0
        # self.cycle_dropdown.addItem("basic Ki67")   # 0 -> 1, 1 -> 0
        # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
        # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0
        # self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0
        # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0
    def cycle_phase_transition_cb(self):

        radioBtn = self.sender()
        if "duration" in radioBtn.text():
            self.cycle_duration_flag = True
            self.customize_cycle_choices()
        else:  # transition rates
            self.cycle_duration_flag = False
            self.customize_cycle_choices()

        self.param_d[self.current_cell_def]['cycle_duration_flag'] = self.cycle_duration_flag
        
    def chemotaxis_direction_cb(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            if "toward" in radioBtn.text():
                self.param_d[self.current_cell_def]["motility_chemotaxis_towards"] = True
            else:
                self.param_d[self.current_cell_def]["motility_chemotaxis_towards"] = False

    #-----------------------------------------------------------------------------------------
    # Fill them using the given model (the .xml)
    def fill_substrates_comboboxes(self):
        logging.debug(f'cell_def_tab.py: ------- fill_substrates_comboboxes')
        # print("self.substrate_list = ",self.substrate_list)
        self.substrate_list.clear()  # rwh/todo: where/why/how is this list maintained?
        self.motility_substrate_dropdown.clear()
        self.motility2_substrate_dropdown.clear()
        self.secretion_substrate_dropdown.clear()
        uep = self.xml_root.find('.//microenvironment_setup')  # find unique entry point
        # vp = []   # pointers to <variable> nodes
        if uep:
            idx = 0
            for var in uep.findall('variable'):
                # vp.append(var)
                logging.debug(f' --> {var.attrib["name"]}')
                name = var.attrib['name']
                self.substrate_list.append(name)
                self.motility_substrate_dropdown.addItem(name)   # beware - triggers a callback! motility_substrate_changed_cb
                self.motility2_substrate_dropdown.addItem(name)
                self.secretion_substrate_dropdown.addItem(name)
        # print("cell_def_tab.py: ------- fill_substrates_comboboxes:  self.substrate_list = ",self.substrate_list)
        self.physiboss_update_list_signals()
        self.physiboss_update_list_behaviours()

    #-----------------------------------------------------------------------------------------
    # Fill them using the given model (the .xml)
    def fill_celltypes_comboboxes(self):
        logging.debug(f'cell_def_tab.py: ------- fill_celltypes_comboboxes')
        # print(f'cell_def_tab.py: ------- fill_celltypes_comboboxes')
        # print("self.celltypes_list = ",self.celltypes_list)
        self.celltypes_list.clear()  # rwh/todo: where/why/how is this list maintained?
        self.live_phagocytosis_dropdown.clear()
        self.attack_rate_dropdown.clear()
        self.fusion_rate_dropdown.clear()
        self.cell_transformation_dropdown.clear()
        self.cycle_tab.reset_asym_div_table()
        # self.immunogenicity_dropdown.clear()

        self.cell_adhesion_affinity_dropdown.clear()
        uep = self.xml_root.find('.//cell_definitions')  # find unique entry point
        # vp = []   # pointers to <variable> nodes
        if uep:
            idx = 0
            for i, var in enumerate(uep.findall('cell_definition')):
                # vp.append(var)
                # print(" --> ",var.attrib['name'])
                name = var.attrib['name']
                self.celltypes_list.append(name)
                self.live_phagocytosis_dropdown.addItem(name)
                self.attack_rate_dropdown.addItem(name)
                self.fusion_rate_dropdown.addItem(name)
                self.cell_transformation_dropdown.addItem(name)
                # self.immunogenicity_dropdown.addItem(name)

                self.cell_adhesion_affinity_dropdown.addItem(name)

                val = self.param_d[self.current_cell_def]['asymmetric_division_probability'][name]
                self.cycle_tab.add_row_to_asym_div_table(name, val=val)

                # self.ics_tab.celltype_combobox.addItem(name)

        self.cycle_tab.asym_div_normalize_probabilities() # to get the coloring right
        # print("cell_def_tab.py: ------- fill_celltypes_comboboxes:  self.celltypes_list = ",self.celltypes_list)
        self.physiboss_update_list_signals()
        self.physiboss_update_list_behaviours()

    #-----------------------------------------------------------------------------------------
    def add_new_celltype_comboboxes(self, name):
        logging.debug(f'cell_def_tab.py: ------- add_new_celltype_comboboxes {name}')
        self.celltypes_list.append(name)
        self.live_phagocytosis_dropdown.addItem(name)
        self.attack_rate_dropdown.addItem(name)
        self.fusion_rate_dropdown.addItem(name)
        self.cell_transformation_dropdown.addItem(name)
        # self.immunogenicity_dropdown.addItem(name)

        self.cell_adhesion_affinity_dropdown.addItem(name)

        if self.ics_tab:
            self.ics_tab.update_colors_list()
            self.ics_tab.celltype_combobox.addItem(name)
        if self.rules_tab:
            self.rules_tab.add_new_celltype(name)

        self.cycle_tab.add_row_to_asym_div_table(name)

    #-----------------------------------------------------------------------------------------
    def delete_substrate(self, item_idx, new_substrate):

        # 1) delete it from the comboboxes

        # subname = self.motility_substrate_dropdown.itemText(item_idx)
        subname = self.motility2_substrate_dropdown.itemText(item_idx)
        self.substrate_list.remove(subname)

        # update all dropdown/comboboxes
        self.motility_substrate_dropdown.removeItem(item_idx)
        self.motility2_substrate_dropdown.removeItem(item_idx)
        self.secretion_substrate_dropdown.removeItem(item_idx)
        # self.motility_substrate_dropdown.clear()
        # self.secretion_substrate_dropdown.clear()

        # 2) update (delete) in the param_d dict
        for cdname in self.param_d.keys():  # for all cell defs, rename secretion substrate
            if subname == self.param_d[cdname]["motility_chemotaxis_substrate"]:
                self.param_d[cdname]["motility_chemotaxis_substrate"] = new_substrate

            if subname == self.param_d[cdname]["motility_advanced_chemotaxis_substrate"]:
                self.param_d[cdname]["motility_advanced_chemotaxis_substrate"] = new_substrate

            if subname in self.param_d[cdname]["secretion"]:
                del_key = self.param_d[cdname]["secretion"].pop(subname)

            if subname in self.param_d[cdname]["chemotactic_sensitivity"]:
                del_key = self.param_d[cdname]["chemotactic_sensitivity"].pop(subname)
            # rwh: hmm, what about these?
            # self.param_d[cdname]["motility_chemotaxis_substrate"] = new_name
            # self.param_d[cdname]["motility_advanced_chemotaxis_substrate"] = new_name

            # print("--- cell_def_tab.py: delete_substrate(), after deletion, param_d=  ",self.param_d[cdname])
        # print("--- after deletion, param_d=  ",self.param_d[cdname]["secretion"])
        # print("\n--- after deletion, self.current_secretion_substrate=  ",self.current_secretion_substrate)

        # if old_name == self.current_secretion_substrate:
        #     self.current_secretion_substrate = new_name
        self.physiboss_update_list_signals()
        self.physiboss_update_list_behaviours()

    #-----------------------------------------------------------------------------------------
    def add_new_substrate_comboboxes(self, substrate_name):
        # print("cell_def_tab.py: ------- add_new_substrate_comboboxes")
        self.substrate_list.append(substrate_name)
        # print("self.substrate_list = ",self.substrate_list)
        # self.substrate_list.clear()
        # self.motility_substrate_dropdown.clear()
        # self.secretion_substrate_dropdown.clear()
        # self.substrate_list.append(name)
        self.motility_substrate_dropdown.addItem(substrate_name)
        self.motility2_substrate_dropdown.addItem(substrate_name)
        self.secretion_substrate_dropdown.addItem(substrate_name)
        self.physiboss_update_list_signals()
        self.physiboss_update_list_behaviours()

    #-----------------------------------------------------------------------------------------
    # When a user renames a substrate in the Microenv tab, we need to update all 
    # cell_defs data structures that reference it.
    def renamed_substrate(self, old_name,new_name):
        # 1) update in the comboboxes associated with motility(chemotaxis) and secretion
        # print("cell_def_tab.py: ------- renamed_substrate")
        # print("       old_name = ",old_name)
        # print("       new_name = ",new_name)
        self.substrate_list = [new_name if x==old_name else x for x in self.substrate_list]
        # print("self.substrate_list = ",self.substrate_list)

        for idx in range(len(self.substrate_list)):
            # print("idx,old,new = ",idx, old_name,new_name)
            # if old_name in self.motility_substrate_dropdown.itemText(idx):
            if old_name == self.motility_substrate_dropdown.itemText(idx):
                # print("old in dropdown: ", self.motility_substrate_dropdown.itemText(idx))
                self.motility_substrate_dropdown.setItemText(idx, new_name)
            if old_name == self.motility2_substrate_dropdown.itemText(idx):
                self.motility2_substrate_dropdown.setItemText(idx, new_name)
            if old_name == self.secretion_substrate_dropdown.itemText(idx):
                self.secretion_substrate_dropdown.setItemText(idx, new_name)

        # 2) update in the param_d dict
        for cdname in self.param_d.keys():  # for all cell defs, rename motility/chemotaxis and secretion substrate
            # print("--- cdname = ",cdname)
            # print("--- old: ",self.param_d[cdname]["secretion"])
            # print("--- new_name: ",new_name)
            if self.param_d[cdname]["motility_chemotaxis_substrate"] == old_name:
                self.param_d[cdname]["motility_chemotaxis_substrate"] = new_name

            if self.param_d[cdname]["motility_advanced_chemotaxis_substrate"] == old_name:
                self.param_d[cdname]["motility_advanced_chemotaxis_substrate"] = new_name

            # update dicts that use substrates as keys
            self.param_d[cdname]["secretion"][new_name] = self.param_d[cdname]["secretion"].pop(old_name)
            self.param_d[cdname]["chemotactic_sensitivity"][new_name] = self.param_d[cdname]["chemotactic_sensitivity"].pop(old_name)

        if old_name == self.current_secretion_substrate:
            self.current_secretion_substrate = new_name

        if self.rules_tab:
            # print("     calling self.rules_tab.substrate_rename")
            self.rules_tab.substrate_rename(idx,old_name,new_name)

        self.physiboss_update_list_signals()
        self.physiboss_update_list_behaviours()
        self.update_par_dist_behaviors(old_name, new_name)

    #-----------------------------------------------------------------------------------------
    # When a user renames a cell type in this tab, we need to update all 
    # data structures (e.g., QComboBox) that reference it.  Including Rules tab(!)
    def renamed_celltype(self, old_name,new_name):

        # print(f'\ncell_def_tab.py: ------- renamed_celltype() {old_name} -> {new_name}')
        self.cell_adhesion_affinity_celltype = new_name
        # print(f'------- setting self.cell_adhesion_affinity_celltype= {new_name}')

        # 1) update in the comboboxes associated with motility(chemotaxis) and secretion
        logging.debug(f'cell_def_tab.py: ------- renamed_celltype() {old_name} -> {new_name}')
        # print(f'cell_def_tab.py: ------- renamed_celltype() {old_name} -> {new_name}')
        self.celltypes_list = [new_name if x==old_name else x for x in self.celltypes_list]
        logging.debug(f'    self.celltypes_list= {self.celltypes_list}')
        # print(f'    self.celltypes_list= {self.celltypes_list}')
        # print()
        logging.debug(f' ')
        for cdname in self.param_d.keys():
            logging.debug(f'{self.param_d[cdname]}')
            logging.debug(f'\n----')

        # 1) update all dropdown widgets containing the cell def names
        for idx in range(len(self.celltypes_list)):
            # print("     idx,old,new = ",idx, old_name,new_name)
            # if old_name in self.motility_substrate_dropdown.itemText(idx):
            if old_name == self.live_phagocytosis_dropdown.itemText(idx):
                self.live_phagocytosis_dropdown.setItemText(idx, new_name)
            if old_name == self.attack_rate_dropdown.itemText(idx):
                self.attack_rate_dropdown.setItemText(idx, new_name)
            if old_name == self.fusion_rate_dropdown.itemText(idx):
                self.fusion_rate_dropdown.setItemText(idx, new_name)
            if old_name == self.cell_transformation_dropdown.itemText(idx):
                self.cell_transformation_dropdown.setItemText(idx, new_name)
            # if old_name == self.immunogenicity_dropdown.itemText(idx):
            #     self.immunogenicity_dropdown.setItemText(idx, new_name)

            if old_name == self.cell_adhesion_affinity_dropdown.itemText(idx):
                self.cell_adhesion_affinity_dropdown.setItemText(idx, new_name)
            if self.ics_tab and (old_name == self.ics_tab.celltype_combobox.itemText(idx)):
                self.ics_tab.celltype_combobox.setItemText(idx, new_name)

            if self.rules_tab and (old_name == self.rules_tab.celltype_combobox.itemText(idx)):
                # print("    calling self.rules_tab.celltype_combobox.setItemText")
                # self.rules_tab.celltype_combobox.setItemText(idx, new_name)
                self.rules_tab.cell_def_rename(idx,old_name,new_name)

        # 2) also update all param_d dicts that involve cell def names
        logging.debug(f'--- renaming all dicts with cell defs')
        for cdname in self.param_d.keys():  # for all cell defs, rename motility/chemotaxis and secretion substrate
            logging.debug(f'--- cdname = {cdname}')
            self.param_d[cdname]["live_phagocytosis_rate"][new_name] = self.param_d[cdname]["live_phagocytosis_rate"].pop(old_name)
            self.param_d[cdname]["attack_rate"][new_name] = self.param_d[cdname]["attack_rate"].pop(old_name)
            self.param_d[cdname]["fusion_rate"][new_name] = self.param_d[cdname]["fusion_rate"].pop(old_name)
            self.param_d[cdname]["transformation_rate"][new_name] = self.param_d[cdname]["transformation_rate"].pop(old_name)
            self.param_d[cdname]["cell_adhesion_affinity"][new_name] = self.param_d[cdname]["cell_adhesion_affinity"].pop(old_name)
            self.param_d[cdname]["asymmetric_division_probability"][new_name] = self.param_d[cdname]["asymmetric_division_probability"].pop(old_name)

        self.cycle_tab.cell_def_rename(old_name, new_name)

        self.physiboss_update_list_signals()
        self.physiboss_update_list_behaviours()

        self.update_par_dist_behaviors(old_name, new_name)

    def update_par_dist_behaviors(self, old_name, new_name):
        response_l = self.rules_tab.create_response_list()
        self.par_dist_fill_responses_widget(response_l + ["Volume"]) # everything else is lowercase, but this can stand out because it's not a true behavior, but rather the unique non-behavior that can be set by ICs
        self.rename_behavior_distributions(old_name, new_name)

    def rename_behavior_distributions(self, old_name, new_name):
        possible_superstrings = self.celltypes_list
        possible_superstrings += self.substrate_list
        reserved_words = create_reserved_words()
        possible_superstrings += reserved_words
        super_strings = [x for x in possible_superstrings if (old_name in x) and (old_name != x)] # the other elements in the list that contain the old_name
        for cdname in self.param_d.keys():
            if "par_dists" in self.param_d[cdname].keys():
                behavior_keys = list(self.param_d[cdname]["par_dists"].keys()) # do this to avoid changing keys while iterating
                for behavior in behavior_keys:
                    if behavior == '':
                        continue # empty behaviors seem to crop up sometimes
                    new_behavior_name = find_and_replace_rule_cell(old_name, new_name, super_strings, behavior)
                    if new_behavior_name != behavior:
                        self.param_d[cdname]["par_dists"][new_behavior_name] = self.param_d[cdname]["par_dists"].pop(behavior) # sweet

    #-----------------------------------------------------------------------------------------
    # Use default values found in PhysiCell, e.g., *_standard_models.cpp, etc.
    def new_cycle_params(self, cdname, reset_type_flag):
        if reset_type_flag:
            self.param_d[cdname]['cycle_choice_idx'] = 0

        self.param_d[cdname]['cycle_live_00_trate'] = '0.00072'

        self.param_d[cdname]['cycle_Ki67_01_trate'] = '3.63108e-3'
        self.param_d[cdname]['cycle_Ki67_10_trate'] = '1.07527e-3'

        self.param_d[cdname]['cycle_advancedKi67_01_trate'] = '4.60405e-3'
        self.param_d[cdname]['cycle_advancedKi67_12_trate'] = '1.28205e-3'
        self.param_d[cdname]['cycle_advancedKi67_20_trate'] = '6.66666e-3'

        self.param_d[cdname]['cycle_flowcyto_01_trate'] = '0.00324'
        self.param_d[cdname]['cycle_flowcyto_12_trate'] = '0.00208'
        self.param_d[cdname]['cycle_flowcyto_20_trate'] = '0.00333'

        self.param_d[cdname]['cycle_flowcytosep_01_trate'] = '0.00335'
        self.param_d[cdname]['cycle_flowcytosep_12_trate'] = '0.00208'
        self.param_d[cdname]['cycle_flowcytosep_23_trate'] = '0.00417'
        self.param_d[cdname]['cycle_flowcytosep_30_trate'] = '0.01667'   # C++ had only 4-digits: 0.0167 ??

        self.param_d[cdname]['cycle_quiescent_01_trate'] = '3.63108e-3'
        self.param_d[cdname]['cycle_quiescent_10_trate'] = '1.07527e-3'

        # duration times
        self.param_d[cdname]['cycle_live_00_duration'] = '1388.88889'

        self.param_d[cdname]['cycle_Ki67_01_duration'] = '275.40015'
        self.param_d[cdname]['cycle_Ki67_10_duration'] = '929.99898'

        self.param_d[cdname]['cycle_advancedKi67_01_duration'] = '217.20007'
        self.param_d[cdname]['cycle_advancedKi67_12_duration'] = '780.00078'
        self.param_d[cdname]['cycle_advancedKi67_20_duration'] = '150.00015'

        self.param_d[cdname]['cycle_flowcyto_01_duration'] = '308.64198'
        self.param_d[cdname]['cycle_flowcyto_12_duration'] = '480.76923'
        self.param_d[cdname]['cycle_flowcyto_20_duration'] = '300.30030'

        self.param_d[cdname]['cycle_flowcytosep_01_duration'] = '298.50746'
        self.param_d[cdname]['cycle_flowcytosep_12_duration'] = '480.76923'
        self.param_d[cdname]['cycle_flowcytosep_23_duration'] = '239.80815'
        self.param_d[cdname]['cycle_flowcytosep_30_duration'] = '59.88024'

        self.param_d[cdname]['cycle_quiescent_01_duration'] = '275.40016'
        self.param_d[cdname]['cycle_quiescent_10_duration'] = '929.99898'

        #-------------------------
        # transition rates "fixed"
        bval = self.default_bval
        self.param_d[cdname]['cycle_live_00_fixed_trate'] = bval

        self.param_d[cdname]['cycle_Ki67_01_fixed_trate'] = bval
        self.param_d[cdname]['cycle_Ki67_10_fixed_trate'] = True

        self.param_d[cdname]['cycle_advancedKi67_01_fixed_trate'] = bval
        self.param_d[cdname]['cycle_advancedKi67_12_fixed_trate'] = True
        self.param_d[cdname]['cycle_advancedKi67_20_fixed_trate'] = True

        self.param_d[cdname]['cycle_flowcyto_01_fixed_trate'] = bval
        self.param_d[cdname]['cycle_flowcyto_12_fixed_trate'] = bval
        self.param_d[cdname]['cycle_flowcyto_20_fixed_trate'] = bval

        self.param_d[cdname]['cycle_flowcytosep_01_fixed_trate'] = bval
        self.param_d[cdname]['cycle_flowcytosep_12_fixed_trate'] = bval
        self.param_d[cdname]['cycle_flowcytosep_23_fixed_trate'] = bval
        self.param_d[cdname]['cycle_flowcytosep_30_fixed_trate'] = bval

        self.param_d[cdname]['cycle_quiescent_01_fixed_trate'] = bval
        self.param_d[cdname]['cycle_quiescent_10_fixed_trate'] = True

        #------ duration times "fixed"
        self.param_d[cdname]['cycle_live_00_fixed_duration'] = bval

        self.param_d[cdname]['cycle_Ki67_01_fixed_duration'] = bval
        self.param_d[cdname]['cycle_Ki67_10_fixed_duration'] = True

        self.param_d[cdname]['cycle_advancedKi67_01_fixed_duration'] = bval
        self.param_d[cdname]['cycle_advancedKi67_12_fixed_duration'] = True
        self.param_d[cdname]['cycle_advancedKi67_20_fixed_duration'] = True

        self.param_d[cdname]['cycle_flowcyto_01_fixed_duration'] = bval
        self.param_d[cdname]['cycle_flowcyto_12_fixed_duration'] = bval
        self.param_d[cdname]['cycle_flowcyto_20_fixed_duration'] = bval

        self.param_d[cdname]['cycle_flowcytosep_01_fixed_duration'] = bval
        self.param_d[cdname]['cycle_flowcytosep_12_fixed_duration'] = bval
        self.param_d[cdname]['cycle_flowcytosep_23_fixed_duration'] = bval
        self.param_d[cdname]['cycle_flowcytosep_30_fixed_duration'] = bval

        self.param_d[cdname]['cycle_quiescent_01_fixed_duration'] = bval
        self.param_d[cdname]['cycle_quiescent_10_fixed_duration'] = True

    def new_asym_div_params(self, cdname, creating_new_cell_in_studio):
        if not creating_new_cell_in_studio:
            return
        self.param_d[cdname]['asymmetric_division_probability'] = {}
        self.param_d[cdname]['asymmetric_division_enabled'] = False
        for cdname2 in self.param_d.keys():
            self.param_d[cdname]['asymmetric_division_probability'][cdname2] = '0' if cdname != cdname2 else '1.0'
            self.param_d[cdname2]['asymmetric_division_probability'][cdname] = '0' if cdname != cdname2 else '1.0'

    def new_death_params(self, cdname):
        sval = self.default_sval
        duration_sval = '1.e9'
        self.param_d[cdname]["death_rate"] = '5.31667e-05'   # deprecated??
        self.param_d[cdname]["apoptosis_death_rate"] = '5.31667e-05'
        self.param_d[cdname]["apoptosis_01_duration"] = '516'
        self.param_d[cdname]["apoptosis_01_fixed_duration"] = False

        self.param_d[cdname]["apoptosis_duration_flag"] = False

        self.param_d[cdname]["apoptosis_unlysed_rate"] = '0.05'
        self.param_d[cdname]["apoptosis_lysed_rate"] = '0'
        self.param_d[cdname]["apoptosis_cyto_rate"] = '1.66667e-02'
        self.param_d[cdname]["apoptosis_nuclear_rate"] = '5.83333e-03'
        self.param_d[cdname]["apoptosis_calcif_rate"] = '0'
        self.param_d[cdname]["apoptosis_rel_rupture_volume"] = '2.0'

        #-----
        self.param_d[cdname]["necrosis_death_rate"] = sval

        self.param_d[cdname]["necrosis_01_trate"] = '9e9'
        self.param_d[cdname]["necrosis_01_fixed_trate"] = False
        self.param_d[cdname]["necrosis_12_trate"] = '1.15741e-05'
        self.param_d[cdname]["necrosis_12_fixed_trate"] = True

        self.param_d[cdname]["necrosis_duration_flag"] = False

        self.param_d[cdname]["necrosis_01_duration"] = '1.11111e-10'
        self.param_d[cdname]["necrosis_01_fixed_duration"] = False
        self.param_d[cdname]["necrosis_12_duration"] = '86399.80646'
        self.param_d[cdname]["necrosis_12_fixed_duration"] = True

        self.param_d[cdname]["necrosis_unlysed_rate"] = '1.11667e-02'
        self.param_d[cdname]["necrosis_lysed_rate"] = '8.33333e-4'
        self.param_d[cdname]["necrosis_cyto_rate"] = '5.33333e-05'
        self.param_d[cdname]["necrosis_nuclear_rate"] = '2.16667e-4'
        self.param_d[cdname]["necrosis_calcif_rate"] = '7e-05'
        self.param_d[cdname]["necrosis_rel_rupture_rate"] = '2.0'

    def new_volume_params(self, cdname):   # rf. core/*_phenotype.cpp
        sval = self.default_sval
        # use PhysiCell_phenotype.cpp: Volume::Volume() values
        self.param_d[cdname]["volume_total"] = '2494'
        self.param_d[cdname]["volume_fluid_fraction"] = '0.75'
        self.param_d[cdname]["volume_nuclear"] = '540'
        self.param_d[cdname]["volume_fluid_change_rate"] = '0.05'  # 3.0 / 60
        self.param_d[cdname]["volume_cytoplasmic_rate"] = '0.0045'   # 0.27 / 60
        self.param_d[cdname]["volume_nuclear_rate"] = '0.0055'   # 0.33 / 60
        self.param_d[cdname]["volume_calcif_fraction"] = '0.0'
        self.param_d[cdname]["volume_calcif_rate"] = '0.0'
        self.param_d[cdname]["volume_rel_rupture_vol"] = '2'

    def new_mechanics_params(self, cdname_new, reset_mapping):  # rf. PhysiCell core/*_phenotype.cpp constructor
        print("---- new_mechanics_params(): cdname_new= ",cdname_new)
        sval = self.default_sval

        # self.param_d[cdname_new]['is_movable'] = False
        # use defaults found in phenotype.cpp:Mechanics() instead of 0.0
        self.param_d[cdname_new]["mechanics_adhesion"] = '0.4'
        self.param_d[cdname_new]["mechanics_repulsion"] = '10.0'
        self.param_d[cdname_new]["mechanics_adhesion_distance"] = '1.25'

        self.param_d[cdname_new]["mechanics_relative_equilibrium_distance"] = '1.8'
        self.param_d[cdname_new]["mechanics_absolute_equilibrium_distance"] = '15.12'

        self.param_d[cdname_new]["mechanics_relative_equilibrium_distance_enabled"] = False
        self.param_d[cdname_new]["mechanics_absolute_equilibrium_distance_enabled"] = False

        self.param_d[cdname_new]["mechanics_elastic_constant"] = '0.01'
        self.param_d[cdname_new]["attachment_rate"] = '0.0'
        self.param_d[cdname_new]["detachment_rate"] = '0.0'
        self.param_d[cdname_new]["mechanics_max_num_attachments"] = '12'

        if reset_mapping:
            for cdname in self.param_d.keys():    # for each cell def
                for cdname2 in self.param_d.keys():    # for each cell def
            #         # print('cdname2= ',cdname2)
                    if (cdname == cdname_new) or (cdname2 == cdname_new): 
                        self.param_d[cdname]['cell_adhesion_affinity'][cdname2] = '1.0'  # default affinity

    def new_motility_params(self, cdname):
        print("new_motility_params(): ",cdname)
        sval = self.default_sval
        self.param_d[cdname]["speed"] = '1.0'
        self.param_d[cdname]["persistence_time"] = '5.0'
        self.param_d[cdname]["migration_bias"] = '0.5'

        self.param_d[cdname]["motility_enabled"] = False
        self.param_d[cdname]["motility_use_2D"] = True
        self.param_d[cdname]["motility_chemotaxis"] = False
        self.param_d[cdname]["motility_chemotaxis_towards"] = True

        self.param_d[cdname]["motility_advanced_chemotaxis"] = False
        self.param_d[cdname]["normalize_each_gradient"] = False
        # self.motility_substrate_dropdown.setCurrentText(self.param_d[self.current_cell_def]["motility_chemotaxis_substrate"])
        # self.param_d[self.current_cell_def]["motility_chemotaxis_substrate"] = sval
        for substrate_name in self.param_d[cdname]["chemotactic_sensitivity"].keys():
            self.param_d[cdname]["chemotactic_sensitivity"][substrate_name] = '0.0'

    def new_secretion_params(self, cdname):
        print("new_secretion_params(): ",cdname)
        # print("new_secretion_params(): self.current_secretion_substrate = ",self.current_secretion_substrate)
        # print("        self.param_d[cdname]['secretion'] = ",self.param_d[cdname]["secretion"])
        sval = self.default_sval
        for substrate_name in self.param_d[cdname]["secretion"].keys():
            self.param_d[cdname]["secretion"][substrate_name]["secretion_rate"] = sval
            self.param_d[cdname]["secretion"][substrate_name]["secretion_target"] = '1.0'
            self.param_d[cdname]["secretion"][substrate_name]["uptake_rate"] = sval
            self.param_d[cdname]["secretion"][substrate_name]["net_export_rate"] = sval

    def new_interaction_params(self, cdname_new, reset_mapping):
        logging.debug(f'\n--------new_interaction_params(): cdname_new= {cdname_new}, reset_mapping= {reset_mapping}')
        # print(f'\n--------new_interaction_params(): cdname_new= {cdname_new}, reset_mapping= {reset_mapping}')
        sval = self.default_sval
        self.param_d[cdname_new]["apoptotic_phagocytosis_rate"] = sval
        self.param_d[cdname_new]["necrotic_phagocytosis_rate"] = sval
        self.param_d[cdname_new]["other_dead_phagocytosis_rate"] = sval
        self.param_d[cdname_new]["attack_damage_rate"] = '1.0'
        self.param_d[cdname_new]["attack_duration"] = '0.1'
        # <cell_integrity>
        self.param_d[cdname_new]["damage_rate"] = '0.0'
        self.param_d[cdname_new]["damage_repair_rate"] = '0.0'

        if reset_mapping:
            for cdname in self.param_d.keys():    # for each cell def
                for cdname2 in self.param_d.keys():    # for each cell def
                    if (cdname == cdname_new) or (cdname2 == cdname_new): 
                        self.param_d[cdname]['live_phagocytosis_rate'][cdname2] = sval
                        self.param_d[cdname]['attack_rate'][cdname2] = sval
                        self.param_d[cdname]['fusion_rate'][cdname2] = sval
                        self.param_d[cdname]['transformation_rate'][cdname2] = sval

        # print("\n--------new_interaction_params(): param_d= ",self.param_d)
        # sys.exit(-1)

    def new_intracellular_params(self, cdname):

        logging.debug(f'\n--------new_intracellular_params(): cdname_new= {cdname}')
        self.param_d[cdname]["intracellular"] = None


    def add_new_substrate(self, sub_name):  # called for both "New" and "Copy" of substrate/signal
        self.add_new_substrate_comboboxes(sub_name)

        sval = self.default_sval

        # for all cell defs: 
        for cdname in self.param_d.keys():  
            # print('cdname = ',cdname)
            # print(self.param_d[cdname]["secretion"])

            # initialize secretion params
            self.param_d[cdname]["secretion"][sub_name] = {}
            self.param_d[cdname]["secretion"][sub_name]["secretion_rate"] = sval
            self.param_d[cdname]["secretion"][sub_name]["secretion_target"] = "1.0"
            self.param_d[cdname]["secretion"][sub_name]["uptake_rate"] = sval
            self.param_d[cdname]["secretion"][sub_name]["net_export_rate"] = sval

            # initialize motility advanced chemotaxis params
            self.param_d[cdname]["chemotactic_sensitivity"][sub_name] = sval
        
        self.physiboss_update_list_signals()
        self.physiboss_update_list_behaviours()

        if self.rules_tab:
            self.rules_tab.add_new_substrate(sub_name)


    def add_new_celltype(self, cdname):
        self.add_new_celltype_comboboxes(cdname)
        self.physiboss_update_list_signals()
        self.physiboss_update_list_behaviours()
        # sval = self.default_sval
        # for cdname in self.param_d.keys():  # for all cell defs, initialize secretion params
        #     # print('cdname = ',cdname)
        #     # # print(self.param_d[cdname]["secretion"])
        #     self.param_d[cdname]["secretion"][sub_name] = {}
        #     self.param_d[cdname]["secretion"][sub_name]["secretion_rate"] = sval
        #     self.param_d[cdname]["secretion"][sub_name]["secretion_target"] = sval
        #     self.param_d[cdname]["secretion"][sub_name]["uptake_rate"] = sval
        #     self.param_d[cdname]["secretion"][sub_name]["net_export_rate"] = sval


    def new_custom_data_params(self, cdname):
        logging.debug(f'------- new_custom_data_params() -----')
        # print(f'------- new_custom_data_params() -----')
        sval = self.default_sval
        if 'custom_data' not in self.param_d[cdname].keys():
            return
        num_vals = len(self.param_d[cdname]['custom_data'].keys())
        logging.debug(f'num_vals = {num_vals}')
        idx = 0
        for key in self.param_d[cdname]['custom_data'].keys():
            logging.debug(f'{key}, {self.param_d[cdname]["custom_data"][key]}')
            # self.custom_data_name[idx].setText(key)
            self.param_d[cdname]['custom_data'][key] = [self.custom_var_value_str_default, self.custom_var_conserved_default]   # [value, conserved flag]
            idx += 1

    def new_miscellaneous_params(self, cdname):
        self.param_d[cdname]["par_dists"] = {}
        self.param_d[cdname]["par_dists_disabled"] = True
     
    #-----------------------------------------------------------------------------------------
    def update_death_params(self):
        # print("\n\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        # print("\n ------------------  update_death_params() ")
        cdname = self.current_cell_def
        self.apoptosis_death_rate.setText(self.param_d[cdname]["apoptosis_death_rate"])

        if self.param_d[cdname]['apoptosis_duration_flag']:
            # print(" ------------------  apoptosis_rb2.setChecked(True) ")
            self.apoptosis_rb2.setChecked(True)
        else:
            # print(" ------------------  apoptosis_rb1.setChecked(True) ")
            self.apoptosis_rb1.setChecked(True)
        self.apoptosis_01_duration.setText(self.param_d[cdname]["apoptosis_01_duration"])
        self.apoptosis_01_fixed_duration.setChecked(self.param_d[cdname]["apoptosis_01_fixed_duration"])
        # vs.
        self.apoptosis_01_trate.setText(self.param_d[cdname]["apoptosis_01_trate"])
        self.apoptosis_01_fixed_trate.setChecked(self.param_d[cdname]["apoptosis_01_fixed_trate"])

        self.apoptosis_unlysed_rate.setText(self.param_d[cdname]["apoptosis_unlysed_rate"])
        self.apoptosis_lysed_rate.setText(self.param_d[cdname]["apoptosis_lysed_rate"])
        self.apoptosis_cytoplasmic_biomass_change_rate.setText(self.param_d[cdname]["apoptosis_cyto_rate"])
        self.apoptosis_nuclear_biomass_change_rate.setText(self.param_d[cdname]["apoptosis_nuclear_rate"])
        self.apoptosis_calcification_rate.setText(self.param_d[cdname]["apoptosis_calcif_rate"])
        self.apoptosis_relative_rupture_volume.setText(self.param_d[cdname]["apoptosis_rel_rupture_volume"])

        #-----
        self.necrosis_death_rate.setText(self.param_d[cdname]["necrosis_death_rate"])

        if self.param_d[cdname]['necrosis_duration_flag']:
            # print(" ------------------  necrosis_rb2.setChecked(True) ")
            self.necrosis_rb2.setChecked(True)
        else:
            # print(" ------------------  necrosis_rb1.setChecked(True) ")
            self.necrosis_rb1.setChecked(True)
        self.necrosis_01_duration.setText(self.param_d[cdname]["necrosis_01_duration"])
        self.necrosis_01_fixed_duration.setChecked(self.param_d[cdname]["necrosis_01_fixed_duration"])
        self.necrosis_12_duration.setText(self.param_d[cdname]["necrosis_12_duration"])
        self.necrosis_12_fixed_duration.setChecked(self.param_d[cdname]["necrosis_12_fixed_duration"])
        # vs.
        self.necrosis_01_trate.setText(self.param_d[cdname]["necrosis_01_trate"])
        self.necrosis_01_fixed_trate.setChecked(self.param_d[cdname]["necrosis_01_fixed_trate"])
        self.necrosis_12_trate.setText(self.param_d[cdname]["necrosis_12_trate"])
        self.necrosis_12_fixed_trate.setChecked(self.param_d[cdname]["necrosis_12_fixed_trate"])

        self.necrosis_unlysed_rate.setText(self.param_d[cdname]["necrosis_unlysed_rate"])
        self.necrosis_lysed_rate.setText(self.param_d[cdname]["necrosis_lysed_rate"])
        self.necrosis_cytoplasmic_biomass_change_rate.setText(self.param_d[cdname]["necrosis_cyto_rate"])
        self.necrosis_nuclear_biomass_change_rate.setText(self.param_d[cdname]["necrosis_nuclear_rate"])
        self.necrosis_calcification_rate.setText(self.param_d[cdname]["necrosis_calcif_rate"])
        self.necrosis_relative_rupture_volume.setText(self.param_d[cdname]["necrosis_rel_rupture_rate"])
        # print("\n\n ~~~~~~~~~~~~~~~~~~~~~~~~~  leaving  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")


    #-----------------------------------------------------------------------------------------
    def update_volume_params(self):
        cdname = self.current_cell_def
        self.volume_total.setText(self.param_d[cdname]["volume_total"])
        self.volume_fluid_fraction.setText(self.param_d[cdname]["volume_fluid_fraction"])
        self.volume_nuclear.setText(self.param_d[cdname]["volume_nuclear"])
        self.volume_fluid_change_rate.setText(self.param_d[cdname]["volume_fluid_change_rate"])
        self.volume_cytoplasmic_biomass_change_rate.setText(self.param_d[cdname]["volume_cytoplasmic_rate"])
        self.volume_nuclear_biomass_change_rate.setText(self.param_d[cdname]["volume_nuclear_rate"])
        self.volume_calcified_fraction.setText(self.param_d[cdname]["volume_calcif_fraction"])
        self.volume_calcification_rate.setText(self.param_d[cdname]["volume_calcif_rate"])
        self.relative_rupture_volume.setText(self.param_d[cdname]["volume_rel_rupture_vol"])

    #-----------------------------------------------------------------------------------------
    def update_mechanics_params(self):
        cdname = self.current_cell_def
        self.cell_cell_adhesion_strength.setText(self.param_d[cdname]["mechanics_adhesion"])
        self.cell_cell_repulsion_strength.setText(self.param_d[cdname]["mechanics_repulsion"])
        self.relative_maximum_adhesion_distance.setText(self.param_d[cdname]["mechanics_adhesion_distance"])

        if self.cell_adhesion_affinity_celltype:
            logging.debug(f'key 0= {self.cell_adhesion_affinity_celltype}')
            logging.debug(f'keys 1= {self.param_d.keys()}')
            logging.debug(f'keys 2= {self.param_d[cdname]["cell_adhesion_affinity"].keys()}')

            # print(f'key 0= {self.cell_adhesion_affinity_celltype}')
            # print(f'keys 1= {self.param_d.keys()}')
            # print(f'keys 2= {self.param_d[cdname]["cell_adhesion_affinity"].keys()}')

            if self.cell_adhesion_affinity_celltype is not None:
                try:
                    self.cell_adhesion_affinity.setText(self.param_d[cdname]["cell_adhesion_affinity"][self.cell_adhesion_affinity_celltype])
                except:
                    error_msg = f'\nError: cell_def_tab.py: update_mechanics_params(): cdname={cdname}, cell_adhesion_affinity.setText, self.cell_adhesion_affinity_celltype={self.cell_adhesion_affinity_celltype}'
                    print(error_msg)

                    print(f'[{cdname}]["cell_adhesion_affinity"] = {self.param_d[cdname]["cell_adhesion_affinity"]}')

                    # msgBox = QMessageBox()
                    # msgBox.setIcon(QMessageBox.Information)
                    # # msgBox.setText(error_msg)
                    # msgBox.setText(f'Error: invalid self.cell_adhesion_affinity_celltype= {self.cell_adhesion_affinity_celltype}')
                    # msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                    # returnValue = msgBox.exec()

                    self.cell_adhesion_affinity_celltype = None

        self.set_relative_equilibrium_distance.setText(self.param_d[cdname]["mechanics_relative_equilibrium_distance"])
        self.set_relative_equilibrium_distance_enabled.setChecked(self.param_d[cdname]["mechanics_relative_equilibrium_distance_enabled"])

        self.set_absolute_equilibrium_distance.setText(self.param_d[cdname]["mechanics_absolute_equilibrium_distance"])
        self.set_absolute_equilibrium_distance_enabled.setChecked(self.param_d[cdname]["mechanics_absolute_equilibrium_distance_enabled"])

        self.elastic_constant.setText(self.param_d[cdname]["mechanics_elastic_constant"])
        self.attachment_rate.setText(self.param_d[cdname]["attachment_rate"])
        self.detachment_rate.setText(self.param_d[cdname]["detachment_rate"])
        self.max_num_attachments.setText(self.param_d[cdname]["mechanics_max_num_attachments"])


    #-----------------------------------------------------------------------------------------
    def update_motility_params(self):
        cdname = self.current_cell_def
        logging.debug(f'\n----- update_motility_params():  cdname= {cdname}')
        # print('motility_advanced_chemotaxis=',self.param_d[cdname]["motility_advanced_chemotaxis"])

        self.speed.setText(self.param_d[cdname]["speed"])
        self.persistence_time.setText(self.param_d[cdname]["persistence_time"])
        self.migration_bias.setText(self.param_d[cdname]["migration_bias"])

        self.motility_enabled.setChecked(self.param_d[cdname]["motility_enabled"])

        # if self.param_d[cdname]["motility_enabled"]:
        if self.param_d[cdname]["motility_chemotaxis"]:
            logging.debug(f'   (simple) chemotaxis motility is enabled:')
            self.param_d[cdname]["motility_advanced_chemotaxis"] = False
            self.chemotaxis_enabled_cb(True)
        else:
            self.chemotaxis_enabled_cb(False)

        self.motility_use_2D.setChecked(self.param_d[cdname]["motility_use_2D"])
        self.chemotaxis_enabled.setChecked(self.param_d[cdname]["motility_chemotaxis"])
        self.motility_substrate_dropdown.setCurrentText(self.param_d[cdname]["motility_chemotaxis_substrate"])
        logging.debug(f'     setting motility_substrate_dropdown (for cdname= {cdname} ) = {self.param_d[cdname]["motility_chemotaxis_substrate"]}')

        if self.param_d[cdname]["motility_chemotaxis_towards"]:
            self.chemotaxis_direction_towards.setChecked(True)
        else:
            self.chemotaxis_direction_against.setChecked(True)

        # Advanced Chemotaxis
        self.motility2_substrate_dropdown.setCurrentText(self.param_d[cdname]["motility_advanced_chemotaxis_substrate"])
        logging.debug(f'     setting motility2_substrate_dropdown (for cdname= {cdname} ) = {self.param_d[cdname]["motility_advanced_chemotaxis_substrate"]}')

        if self.param_d[cdname]["motility_advanced_chemotaxis"]:
            self.advanced_chemotaxis_enabled.setChecked(True)
            self.advanced_chemotaxis_enabled_cb(True)
        else:
            self.advanced_chemotaxis_enabled.setChecked(False)
            self.advanced_chemotaxis_enabled_cb(False)

        if self.param_d[cdname]["normalize_each_gradient"]:
            self.normalize_each_gradient.setChecked(True)
            # self.normalize_each_gradient_cb(True) # all this function (used to) does is set self.param_d[cdname]["normalize_each_gradient"] to True, but we're because it already is True
        else:
            self.normalize_each_gradient.setChecked(False)
            # self.normalize_each_gradient_cb(False) # all this function (used to) does is set self.param_d[cdname]["normalize_each_gradient"] to False, but we're because it already is False

        # print('chemotactic_sensitivity= ',self.param_d[cdname]['chemotactic_sensitivity'])
        # foobar now None
        logging.debug(f'    chemotactic_sensitivity= {self.param_d[cdname]["chemotactic_sensitivity"]}')
        if self.param_d[cdname]['motility_advanced_chemotaxis_substrate'] == 'foobar':
            logging.debug(f'-- motility_advanced_chemotaxis_substrate is foobar')
        else:
            if len(self.param_d[cdname]['motility_advanced_chemotaxis_substrate']) > 0:
                logging.debug(f'new val = {self.param_d[cdname]["chemotactic_sensitivity"][self.param_d[cdname]["motility_advanced_chemotaxis_substrate"]]}')
        # self.chemo_sensitivity.setText('42')
            if len(self.param_d[cdname]['motility_advanced_chemotaxis_substrate']) > 0:
                self.chemo_sensitivity.setText(self.param_d[cdname]['chemotactic_sensitivity'][self.param_d[cdname]['motility_advanced_chemotaxis_substrate']])

        # sys.exit(-1)
        logging.debug(f'----- leave update_motility_params()\n')

    #-----------------------------------------------------------------------------------------
    def update_secretion_params(self):
        cdname = self.current_cell_def
        if cdname == None:
            return

        logging.debug(f'update_secretion_params(): cdname = {cdname}')
        logging.debug(f'update_secretion_params(): self.current_secretion_substrate = {self.current_secretion_substrate}')
        logging.debug(f'{self.param_d[cdname]["secretion"]}')

        try:
            self.secretion_rate.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["secretion_rate"])
            self.secretion_target.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["secretion_target"])
            self.uptake_rate.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["uptake_rate"])
            self.secretion_net_export_rate.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["net_export_rate"])
        except:
            msg = f"Error parsing secretion parameters for {self.current_secretion_substrate} for cell type {cdname}. Please fix your XML config file."
            print(msg)
            msgBox = QMessageBox()
            msgBox.setTextFormat(Qt.RichText)
            msgBox.setText(msg)
            msgBox.setStandardButtons(QMessageBox.Ok)
            returnValue = msgBox.exec()

        # rwh: also update the qdropdown to select the substrate

    #-----------------------------------------------------------------------------------------
    def update_interaction_params(self):
        cdname = self.current_cell_def
        self.apoptotic_phagocytosis_rate.setText(self.param_d[cdname]["apoptotic_phagocytosis_rate"])
        self.necrotic_phagocytosis_rate.setText(self.param_d[cdname]["necrotic_phagocytosis_rate"])
        self.other_dead_phagocytosis_rate.setText(self.param_d[cdname]["other_dead_phagocytosis_rate"])
        self.attack_damage_rate.setText(self.param_d[cdname]["attack_damage_rate"])
        self.attack_duration.setText(self.param_d[cdname]["attack_duration"])

        if self.live_phagocytosis_celltype in self.param_d[cdname]["live_phagocytosis_rate"].keys():
            self.live_phagocytosis_rate.setText(self.param_d[cdname]["live_phagocytosis_rate"][self.live_phagocytosis_celltype])
        else:
            self.live_phagocytosis_rate.setText(self.default_sval)

        if self.attack_rate_celltype in self.param_d[cdname]["attack_rate"].keys():
            self.attack_rate.setText(self.param_d[cdname]["attack_rate"][self.attack_rate_celltype])
        else:
            self.attack_rate.setText(self.default_sval)

        if self.fusion_rate_celltype in self.param_d[cdname]["fusion_rate"].keys():
            self.fusion_rate.setText(self.param_d[cdname]["fusion_rate"][self.fusion_rate_celltype])
        else:
            self.fusion_rate.setText(self.default_sval)

        if self.transformation_rate_celltype in self.param_d[cdname]["transformation_rate"].keys():
            self.transformation_rate.setText(self.param_d[cdname]["transformation_rate"][self.transformation_rate_celltype])
        else:
            self.transformation_rate.setText(self.default_sval)

        self.damage_rate.setText(self.param_d[cdname]["damage_rate"])
        self.damage_repair_rate.setText(self.param_d[cdname]["damage_repair_rate"])

    #-----------------------------------------------------------------------------------------
    def missing_boolean_info_popup(self, dups_dict):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Intracellular (boolean) info is missing. ")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        returnValue = msgBox.exec()
        # if returnValue == QMessageBox.Ok:
            # print('OK clicked')

    #-----------------------------------------------------------------------------------------
    def update_intracellular_params(self):
        cdname = self.current_cell_def
        if self.param_d[cdname]["intracellular"] is not None:
            if self.param_d[cdname]["intracellular"]["type"] == "maboss":
                
                self.physiboss_clear_initial_values()
                self.physiboss_clear_mutants()
                self.physiboss_clear_parameters()
                self.physiboss_clear_node_inheritance()
                self.physiboss_clear_inputs()
                self.physiboss_clear_outputs()

                self.intracellular_type_dropdown.setCurrentIndex(1)
                if "bnd_filename" in self.param_d[cdname]["intracellular"].keys(): 
                    self.physiboss_bnd_file.setText(self.param_d[cdname]["intracellular"]["bnd_filename"])
                if "cfg_filename" in self.param_d[cdname]["intracellular"].keys():
                    self.physiboss_cfg_file.setText(self.param_d[cdname]["intracellular"]["cfg_filename"])

                if "time_step" in self.param_d[cdname]["intracellular"].keys():
                    self.physiboss_time_step.setText(self.param_d[cdname]["intracellular"]["time_step"])
                if "time_stochasticity" in self.param_d[cdname]["intracellular"].keys():
                    self.physiboss_time_stochasticity.setText(self.param_d[cdname]["intracellular"]["time_stochasticity"])
                if "scaling" in self.param_d[cdname]["intracellular"].keys():
                    self.physiboss_scaling.setText(self.param_d[cdname]["intracellular"]["scaling"])
                if "start_time" in self.param_d[cdname]["intracellular"].keys():
                    self.physiboss_starttime.setText(self.param_d[cdname]["intracellular"]["start_time"])
                if "global_inheritance" in self.param_d[cdname]["intracellular"].keys():
                    self.physiboss_global_inheritance_checkbox.setChecked(self.param_d[cdname]["intracellular"]["global_inheritance"] == "True")

                self.fill_substrates_comboboxes()
                self.fill_celltypes_comboboxes()
                self.physiboss_update_list_signals()
                self.physiboss_update_list_behaviours()
                self.physiboss_update_list_nodes()
                self.physiboss_update_list_parameters()
                
                for i, node_inheritance in enumerate(self.param_d[cdname]["intracellular"]["node_inheritance"]):
                    self.physiboss_add_node_inheritance()
                    node, flag, _, _ = self.physiboss_node_specific_inheritance[i]
                    node.setCurrentIndex(self.param_d[cdname]["intracellular"]["list_nodes"].index(node_inheritance["node"]))
                    flag.setChecked(node_inheritance["flag"] == "True")
                    
                for i, initial_value in enumerate(self.param_d[cdname]["intracellular"]["initial_values"]):
                    self.physiboss_add_initial_values()
                    node, value, _, _ = self.physiboss_initial_states[i]
                    if "list_nodes" in self.param_d[cdname]["intracellular"].keys():
                        node.setCurrentIndex(self.param_d[cdname]["intracellular"]["list_nodes"].index(initial_value["node"]))
                        value.setText(initial_value["value"])
                    else:
                        print("----- ERROR(0): update_intracellular_params() has no 'list_nodes' key.")
                        break

                for i, mutant in enumerate(self.param_d[cdname]["intracellular"]["mutants"]):
                    self.physiboss_add_mutant()
                    node, value, _, _ = self.physiboss_mutants[i]
                    if "list_nodes" not in self.param_d[cdname]["intracellular"].keys():
                        print("----- ERROR(1): update_intracellular_params() has no 'list_nodes' key.")
                        break
                    node.setCurrentIndex(self.param_d[cdname]["intracellular"]["list_nodes"].index(mutant["node"]))
                    value.setText(mutant["value"])

                for i, parameter in enumerate(self.param_d[cdname]["intracellular"]["parameters"]):
                    self.physiboss_add_parameter()
                    name, value, _, _ = self.physiboss_parameters[i]
                    if "list_nodes" not in self.param_d[cdname]["intracellular"].keys():
                        print("----- ERROR(2): update_intracellular_params() has no 'list_nodes' key.")
                        break
                    name.setCurrentIndex(self.param_d[cdname]["intracellular"]["list_parameters"].index(parameter["name"]))
                    value.setText(parameter["value"])

                
                for i, input in enumerate(self.param_d[cdname]["intracellular"]["inputs"]):
                    self.physiboss_add_input()
                    name, node, action, threshold, inact_threshold, smoothing, _, _ = self.physiboss_inputs[i]
                    logging.debug(f'update_intracellular_params(): cdname={cdname},  {input["name"]}={input["name"]}')
                    logging.debug(f'  param_d= {self.param_d[cdname]["intracellular"]}')
                    name.setCurrentIndex(self.physiboss_signals.index(input["name"]))
                    if "list_nodes" not in self.param_d[cdname]["intracellular"].keys():
                        print("----- ERROR(3): update_intracellular_params() has no 'list_nodes' key.")
                        break
                    node.setCurrentIndex(self.param_d[cdname]["intracellular"]["list_nodes"].index(input["node"]))
                    action.setCurrentIndex(1 if input["action"] == "inhibition" else 0)
                    threshold.setText(input["threshold"])
                    inact_threshold.setText(input["inact_threshold"])
                    smoothing.setText(input["smoothing"])

                for i, output in enumerate(self.param_d[cdname]["intracellular"]["outputs"]):
                    self.physiboss_add_output()
                    name, node, action, value, basal_value, smoothing, _, _ = self.physiboss_outputs[i]
                    name.setCurrentIndex(self.physiboss_behaviours.index(output["name"]))
                    if "list_nodes" not in self.param_d[cdname]["intracellular"].keys():
                        print("----- ERROR(4): update_intracellular_params() has no 'list_nodes' key.")
                        break
                    node.setCurrentIndex(self.param_d[cdname]["intracellular"]["list_nodes"].index(output["node"]))
                    action.setCurrentIndex(1 if output["action"] == "inhibition" else 0)
                    value.setText(output["value"])
                    basal_value.setText(output["basal_value"])
                    smoothing.setText(output["smoothing"])

            elif self.param_d[cdname]["intracellular"]["type"] == "roadrunner":
                print("------ Parsing roadrunner intracellular params")
                self.ode_sbml_frame.fill_gui(cdname)
                self.intracellular_type_dropdown.setCurrentIndex(2)
                # if "sbml_filename" in self.param_d[cdname]["intracellular"].keys(): 
                    # self.ode_sbml_frame.sbml_file.setText(self.param_d[cdname]["intracellular"]["sbml_filename"])

        else:
            self.intracellular_type_dropdown.setCurrentIndex(0)

    #-----------------------------------------------------------------------------------------
    def update_custom_data_params(self):
        cdname = self.current_cell_def
        # print("\n--------- cell_def_tab.py: update_custom_data_params():  cdname= ",cdname)
        debug_me = False
        if debug_me:
            print("\n--------- cell_def_tab.py: update_custom_data_params():  self.param_d[cdname]['custom_data'] = ",self.param_d[cdname]['custom_data'])

        if 'custom_data' not in self.param_d[cdname].keys():
            return

        self.clear_custom_data_tab()  # clean out before re-populating

        num_vals = len(self.param_d[cdname]['custom_data'].keys())
        # print("  -------- custom_data # keys =", num_vals)
        # return

        idx = 0
        self.custom_data_edit_active = False

        for key in self.param_d[cdname]['custom_data'].keys():
            # print("--------- update_custom_data_params():  key = ",key)
            # logging.debug(f'["custom_data"]keys() = {self.param_d[cdname]["custom_data"].keys()}')
            # logging.debug(f'["custom_data"]keys() = {self.param_d[cdname]["custom_data"].keys()}')
            # print(f'["custom_data"]keys() = {self.param_d[cdname]["custom_data"].keys()}')
            # print("cell_def_tab.py: update_custom_data_params(): ",key,self.param_d[cdname]['custom_data'][key])

            if len(key) > 0:  # probably not necessary anymore
                # logging.debug(f'cell_def_tab.py: update_custom_data_params(): {key},{self.param_d[cdname]["custom_data"][key]}')
                # print(f'       update_custom_data_params(): custom_data= {self.param_d[cdname]["custom_data"]}')
                # print(f'       update_custom_data_params(): {key},{self.param_d[cdname]["custom_data"][key]}')

                irow = self.master_custom_var_d[key][0]
                # print("---- irow=",irow)
                #------------- name
                # self.custom_data_table.cellWidget(idx,self.custom_icol_name).setText(key)   # rwh: tricky; custom var name
                self.custom_data_table.cellWidget(irow,self.custom_icol_name).setText(key)   # rwh: tricky; custom var name
                self.custom_data_table.cellWidget(irow,self.custom_icol_name).prev = key 

                # self.custom_data_table.cellWidget(idx,self.custom_icol_name).setStyleSheet("color: black;")

                #------------- value
                self.custom_data_table.cellWidget(irow,self.custom_icol_value).setText(self.param_d[cdname]['custom_data'][key][0]) 

                #------------- conserved
                self.custom_data_table.cellWidget(irow,self.custom_icol_conserved).setChecked(self.param_d[cdname]['custom_data'][key][1]) 


                # NOTE: the following two (units, desc) are the same across all cell types
                #------------- units
                # print(f"    update_custom_data_params(): master_custom_var_d= {self.master_custom_var_d}")
                self.custom_data_table.cellWidget(irow,self.custom_icol_units).setText(self.master_custom_var_d[key][1])

                #------------- description
                self.custom_data_table.cellWidget(irow,self.custom_icol_desc).setText(self.master_custom_var_d[key][2])

            idx += 1

        self.custom_data_edit_active = True

    def update_misc_params(self):
        cdname = self.current_cell_def
        self.par_dist_cell_type_disabled_checkbox.setText(f"Disable all parameter distributions for {cdname}")
        self.par_dist_display_button.setText(f"Display/update parameter distributions for {cdname}")    
        if self.param_d[cdname]["par_dists_disabled"] != self.par_dist_cell_type_disabled_checkbox.isChecked():
            self.par_dist_cell_type_disabled_checkbox.setChecked(self.param_d[cdname]["par_dists_disabled"])
        else:
            state = QtCore.Qt.Checked if self.param_d[cdname]["par_dists_disabled"] else QtCore.Qt.Unchecked
            self.par_dist_cell_type_disabled_checkbox.stateChanged.emit(state)
            
        if self.param_d[cdname]["par_dists_disabled"]:
            self.par_dist_enable_checkbox.setChecked(False)
            self.par_dist_enforce_base_checkbox.setChecked(False)
            for pdple in self.par_dist_par_lineedit:
                pdple.setText('') # do not let the previous cell def param values affect this cell def param values

    #-----------------------------------------------------------------------------------------
    def reset_to_blank(self):
        self.clear_custom_data_tab()
        self.param_d.clear()  # seems unnecessary as being done in populate_tree. argh.
        self.current_cell_def = None
        self.cell_adhesion_affinity_celltype = None
        self.cycle_tab.reset_asym_div_table() # drb: at some point this will be self.cycle_tab.reset_to_blank() I suppose...

    def clear_custom_data_params(self):
        # called from pmb.py: load_mode() -> show_sample_model() -> reset_xml_root() (drb: It seems that this is only called from model.py as of 2024-11-15)
        cdname = self.current_cell_def
        if not cdname:
            return
        # print("--------- clear_custom_data_params():  self.param_d[cdname]['custom_data'] = ",self.param_d[cdname]['custom_data'])
        num_vals = len(self.param_d[cdname]['custom_data'].keys())
        # print("num_vals =", num_vals)
        idx = 0
        for idx in range(num_vals):
        # for key in self.param_d[cdname]['custom_data'].keys():
            # print(key,self.param_d[cdname]['custom_data'][key])
            self.custom_data_name[idx].setText('')
            self.custom_data_value[idx].setText('')
            self.custom_data_conserved[idx].setChecked(False)
            # idx += 1

    #-----------------------------------------------------------------------------------------
    # User selects a cell def from the tree on the left. We need to fill in ALL widget values from param_d
    def tree_item_clicked_cb(self, it,col):
        self.current_cell_def = it.text(0)

        # fill in the GUI with this cell def's params

        self.cycle_tab.update_cycle_params()
        self.update_death_params()
        self.update_volume_params()
        self.update_mechanics_params()
        self.update_motility_params()
        self.update_secretion_params()
        self.update_interaction_params()
        self.update_intracellular_params()
        # self.update_molecular_params()
        self.update_custom_data_params()

        self.update_misc_params()


    #-------------------------------------------------------------------
    def first_cell_def_name(self):
        uep = self.xml_root.find(".//cell_definitions//cell_definition")
        if uep:
                return(uep.attrib['name'])

    def iterate_tree(self, node, count, subs):
        for idx in range(count):
            item = node.child(idx)
            # print('******* State: %s, Text: "%s"' % (Item.checkState(3), Item.text(0)))
            subs.append(item.text(0))
            child_count = item.childCount()
            if child_count > 0:
                self.iterate_tree(item, child_count)

    #-------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
   
    #-------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml_death(self,pheno,cdname):  # we use "cdname" here instead of cdef (for easier copy/paste from elsewhere)
        death = ET.SubElement(pheno, "death")
        death.text = self.indent12  # affects indent of child
        death.tail = "\n" + self.indent10

        model = ET.SubElement(death, "model",{"code":"100", "name":"apoptosis"})
        model.text = self.indent14  # affects indent of child
        model.tail = self.indent12

        subelm = ET.SubElement(model, "death_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdname]["apoptosis_death_rate"]
        subelm.tail = self.indent14

        if self.param_d[cdname]['apoptosis_duration_flag']:
            subelm = ET.SubElement(model, "phase_durations",{"units":self.default_time_units})
            subelm.text = self.indent16
            subelm.tail = self.indent14

            bval = "false"
            if self.param_d[cdname]["apoptosis_01_fixed_duration"]:
                bval = "true"
            subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":bval})
            subelm2.text = self.param_d[cdname]["apoptosis_01_duration"]
            subelm2.tail = self.indent14
        else:   # transition rate
            subelm = ET.SubElement(model, "phase_transition_rates",{"units":self.default_rate_units})
            subelm.text = self.indent16
            subelm.tail = self.indent14

            bval = "false"
            if self.param_d[cdname]["apoptosis_01_fixed_trate"]:
                bval = "true"
            subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0","end_index":"1", "fixed_duration":bval})
            subelm2.text = self.param_d[cdname]["apoptosis_01_trate"]
            subelm2.tail = self.indent14

        elm = ET.SubElement(model, "parameters")
        elm.text = self.indent16  # affects indent of child
        elm.tail = self.indent12

        subelm = ET.SubElement(elm, "unlysed_fluid_change_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdname]["apoptosis_unlysed_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "lysed_fluid_change_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdname]["apoptosis_lysed_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "cytoplasmic_biomass_change_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdname]["apoptosis_cyto_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "nuclear_biomass_change_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdname]["apoptosis_nuclear_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "calcification_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdname]["apoptosis_calcif_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "relative_rupture_volume",{"units":"dimensionless"})
        subelm.text = self.param_d[cdname]["apoptosis_rel_rupture_volume"]
        subelm.tail = self.indent14

        #---------------------------------
        model = ET.SubElement(death, "model",{"code":"101", "name":"necrosis"})
        model.text = self.indent14  # affects indent of child
        model.tail = self.indent10

        subelm = ET.SubElement(model, "death_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdname]["necrosis_death_rate"]
        subelm.tail = self.indent14

        if self.param_d[cdname]['necrosis_duration_flag']:
            subelm = ET.SubElement(model, "phase_durations",{"units":self.default_time_units})
            subelm.text = self.indent16
            subelm.tail = self.indent14

            bval = "false"
            if self.param_d[cdname]["necrosis_01_fixed_duration"]:
                bval = "true"
            subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":bval})
            subelm2.text = self.param_d[cdname]["necrosis_01_duration"]
            subelm2.tail = self.indent14

            bval = "false"
            if self.param_d[cdname]["necrosis_12_fixed_duration"]:
                bval = "true"
            subelm2 = ET.SubElement(subelm, "duration",{"index":"1", "fixed_duration":bval})
            subelm2.text = self.param_d[cdname]["necrosis_12_duration"]
            subelm2.tail = self.indent14
        else:   # transition rate
            subelm = ET.SubElement(model, "phase_transition_rates",{"units":self.default_rate_units})
            subelm.text = self.indent16
            subelm.tail = self.indent14

            bval = "false"
            if self.param_d[cdname]["necrosis_01_fixed_trate"]:
                bval = "true"
            subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0","end_index":"1", "fixed_duration":bval})
            subelm2.text = self.param_d[cdname]["necrosis_01_trate"]
            subelm2.tail = self.indent16

            bval = "false"
            if self.param_d[cdname]["necrosis_12_fixed_trate"]:
                bval = "true"
            subelm2 = ET.SubElement(subelm, "rate",{"start_index":"1","end_index":"2", "fixed_duration":bval})
            subelm2.text = self.param_d[cdname]["necrosis_12_trate"]
            subelm2.tail = self.indent14

        elm = ET.SubElement(model, "parameters")
        elm.text = self.indent16  # affects indent of child
        elm.tail = self.indent12

        subelm = ET.SubElement(elm, "unlysed_fluid_change_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdname]["necrosis_unlysed_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "lysed_fluid_change_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdname]["necrosis_lysed_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "cytoplasmic_biomass_change_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdname]["necrosis_cyto_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "nuclear_biomass_change_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdname]["necrosis_nuclear_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "calcification_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdname]["necrosis_calcif_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "relative_rupture_volume",{"units":"dimensionless"})
        subelm.text = self.param_d[cdname]["necrosis_rel_rupture_rate"]
        subelm.tail = self.indent14


    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml_volume(self,pheno,cdef):
        volume = ET.SubElement(pheno, "volume")
        volume.text = self.indent12  # affects indent of child
        volume.tail = "\n" + self.indent10

        vol_total = float(self.param_d[cdef]['volume_total'])
        vol_nuclear = float(self.param_d[cdef]['volume_nuclear'])
        if vol_total < vol_nuclear:
            msg = f"WARNING: {cdef} cell type has Volume total ({vol_total}) less than nuclear ({vol_nuclear})!"
            print(msg)
            msgBox = QMessageBox()
            msgBox.setTextFormat(Qt.RichText)
            msgBox.setText(msg)
            msgBox.setStandardButtons(QMessageBox.Ok)
            returnValue = msgBox.exec()

        elm = ET.SubElement(volume, 'total',{"units":"micron^3"})
        elm.text = self.param_d[cdef]['volume_total']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'fluid_fraction',{"units":"dimensionless"})
        elm.text = self.param_d[cdef]['volume_fluid_fraction']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'nuclear',{"units":"micron^3"})
        elm.text = self.param_d[cdef]['volume_nuclear']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'fluid_change_rate',{"units":self.default_rate_units})
        elm.text = self.param_d[cdef]['volume_fluid_change_rate']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'cytoplasmic_biomass_change_rate',{"units":self.default_rate_units})
        # elm.text = self.param_d[cdef]['volume_cytoplasmic_biomass_change_rate']
        elm.text = self.param_d[cdef]['volume_cytoplasmic_rate']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'nuclear_biomass_change_rate',{"units":self.default_rate_units})
        elm.text = self.param_d[cdef]['volume_nuclear_rate']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'calcified_fraction',{"units":"dimensionless"})
        elm.text = self.param_d[cdef]['volume_calcif_fraction']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'calcification_rate',{"units":self.default_rate_units})
        elm.text = self.param_d[cdef]['volume_calcif_rate']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'relative_rupture_volume',{"units":"dimensionless"})
        elm.text = self.param_d[cdef]['volume_rel_rupture_vol']
        elm.tail = self.indent10


    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml_mechanics(self,pheno,cdef):
        mechanics = ET.SubElement(pheno, "mechanics")
        mechanics.text = self.indent12  # affects indent of child
        mechanics.tail = "\n" + self.indent10

        elm = ET.SubElement(mechanics, 'cell_cell_adhesion_strength',{"units":"micron/min"})
        elm.text = self.param_d[cdef]['mechanics_adhesion']
        elm.tail = self.indent12

        elm = ET.SubElement(mechanics, 'cell_cell_repulsion_strength',{"units":"micron/min"})
        elm.text = self.param_d[cdef]['mechanics_repulsion']
        elm.tail = self.indent12

        elm = ET.SubElement(mechanics, 'relative_maximum_adhesion_distance',{"units":"dimensionless"})
        elm.text = self.param_d[cdef]['mechanics_adhesion_distance']
        elm.tail = self.indent12

        ca_rates = ET.SubElement(mechanics, "cell_adhesion_affinities")
        ca_rates.text = self.indent16
        ca_rates.tail = self.indent12

        logging.debug(f'--- cell_adhesion_affinity= {self.param_d[cdef]["cell_adhesion_affinity"]}')
        for key in self.param_d[cdef]['cell_adhesion_affinity'].keys():
            # argh, not sure why this is necessary, but without it, we can get empty entries if we read in a saved mymodel.xml
            if len(key) == 0:  
                continue
            val = self.param_d[cdef]['cell_adhesion_affinity'][key]
            logging.debug(f'{key}  --> {val}')
            elm = ET.SubElement(ca_rates, 'cell_adhesion_affinity', {"name":key})
            elm.text = val
            elm.tail = self.indent16

        # sys.exit(1)  #rwh

        elm = ET.SubElement(mechanics, 'options')
        elm.text = self.indent14
        elm.tail = self.indent12

        bval = "false"
        if self.param_d[cdef]['mechanics_relative_equilibrium_distance_enabled']:
            bval = "true"
        subelm = ET.SubElement(elm, 'set_relative_equilibrium_distance',{"enabled":bval, "units":"dimensionless"})
        subelm.text = self.param_d[cdef]['mechanics_relative_equilibrium_distance'] 
        subelm.tail = self.indent14

        bval = "false"
        if self.param_d[cdef]['mechanics_absolute_equilibrium_distance_enabled']:
            bval = "true"
        subelm = ET.SubElement(elm, 'set_absolute_equilibrium_distance',{"enabled":bval, "units":"micron"})
        subelm.text = self.param_d[cdef]['mechanics_absolute_equilibrium_distance'] 
        subelm.tail = self.indent12

        # new_stuff (June 2022) mechanics params
        # elm = ET.SubElement(mechanics, 'cell_BM_adhesion_strength',{"units":"micron/min"})
        # elm.text = self.param_d[cdef]["mechanics_BM_adhesion"]
        # elm.tail = self.indent12

        # elm = ET.SubElement(mechanics, 'cell_BM_repulsion_strength',{"units":"micron/min"})
        # elm.text = self.param_d[cdef]["mechanics_BM_repulsion"]
        # elm.tail = self.indent12

        elm = ET.SubElement(mechanics, 'attachment_elastic_constant',{"units":self.default_rate_units})
        elm.text = self.param_d[cdef]["mechanics_elastic_constant"]
        elm.tail = self.indent12

        elm = ET.SubElement(mechanics, 'attachment_rate',{"units":self.default_rate_units})
        elm.text = self.param_d[cdef]["attachment_rate"]
        elm.tail = self.indent12

        elm = ET.SubElement(mechanics, 'detachment_rate',{"units":self.default_rate_units})
        elm.text = self.param_d[cdef]["detachment_rate"]
        elm.tail = self.indent10

        elm = ET.SubElement(mechanics, 'maximum_number_of_attachments')
        elm.text = self.param_d[cdef]["mechanics_max_num_attachments"]
        elm.tail = self.indent10

    #-------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml_motility(self,pheno,cdef):
        motility = ET.SubElement(pheno, "motility")
        motility.text = self.indent12  # affects indent of child
        motility.tail = "\n" + self.indent10


        elm = ET.SubElement(motility, 'speed',{"units":"micron/min"})
        elm.text = self.param_d[cdef]['speed']
        elm.tail = self.indent12

        elm = ET.SubElement(motility, 'persistence_time',{"units":"min"})
        elm.text = self.param_d[cdef]['persistence_time']
        elm.tail = self.indent12
        
        elm = ET.SubElement(motility, 'migration_bias',{"units":"dimensionless"})
        elm.text = self.param_d[cdef]['migration_bias']
        elm.tail = self.indent12

        options = ET.SubElement(motility, 'options')
        options.text = self.indent14
        options.tail = self.indent10

        bval = "false"
        if self.param_d[cdef]['motility_enabled']:
            bval = "true"
        elm = ET.SubElement(options, 'enabled')
        elm.text = bval
        elm.tail = self.indent14

        bval = "false"
        if self.param_d[cdef]['motility_use_2D']:
            bval = "true"
        elm = ET.SubElement(options, 'use_2D')
        elm.text = bval
        elm.tail = self.indent14

        taxis = ET.SubElement(options, 'chemotaxis')
        taxis.text = self.indent16
        taxis.tail = self.indent14

        bval = "false"
        if self.param_d[cdef]['motility_chemotaxis']:
            bval = "true"
        elm = ET.SubElement(taxis, 'enabled')
        elm.text = bval
        elm.tail = self.indent16

        elm = ET.SubElement(taxis, 'substrate')
        if self.debug_print_fill_xml:
            logging.debug(f'\n\n ====================> fill_xml_motility(): {self.param_d[cdef]["motility_chemotaxis_substrate"]} = {self.param_d[cdef]["motility_chemotaxis_substrate"]} \n\n')
        elm.text = self.param_d[cdef]['motility_chemotaxis_substrate']
        elm.tail = self.indent16

        direction = "-1"
        if self.param_d[cdef]["motility_chemotaxis_towards"]:
            direction = "1"
        elm = ET.SubElement(taxis, 'direction')
        elm.text = direction
        elm.tail = self.indent14

        adv_taxis = ET.SubElement(options, 'advanced_chemotaxis')
        adv_taxis.text = self.indent16
        adv_taxis.tail = self.indent12

        bval = "false"
        if self.param_d[cdef]['motility_advanced_chemotaxis']:
            bval = "true"
        elm = ET.SubElement(adv_taxis, 'enabled')
        elm.text = bval
        elm.tail = self.indent16

        bval = "false"
        if self.param_d[cdef]['normalize_each_gradient']:
            bval = "true"
        elm = ET.SubElement(adv_taxis, 'normalize_each_gradient')
        elm.text = bval
        elm.tail = self.indent16

        chemo_sens = ET.SubElement(adv_taxis, 'chemotactic_sensitivities')
        chemo_sens.text = self.indent18
        chemo_sens.tail = self.indent16

        logging.debug(f'fill_xml_motility(): {self.param_d[cdef]["chemotactic_sensitivity"]}')
        for key in self.param_d[cdef]['chemotactic_sensitivity'].keys():
            val = self.param_d[cdef]['chemotactic_sensitivity'][key]
            logging.debug(f'{key}  --> {val}')
            elm = ET.SubElement(chemo_sens, 'chemotactic_sensitivity', {"substrate":key})
            elm.text = val
            elm.tail = self.indent18


    #-------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml_secretion(self,pheno,cdef):
        secretion = ET.SubElement(pheno, "secretion")
        secretion.text = self.indent12  # affects indent of child
        secretion.tail = "\n" + self.indent10

        if self.debug_print_fill_xml:
            logging.debug(f'\n\n ====================> fill_xml_secretion()\n')
            logging.debug(f'self.substrate_list = {self.substrate_list}')
        for substrate in self.substrate_list:
            if self.debug_print_fill_xml:
                logging.debug(f'substrate = {substrate}')
            if (substrate == "blood_vessel_distance") or (substrate == "pbm_gbm_distance"):
                continue
            elm = ET.SubElement(secretion, "substrate",{"name":substrate})
            if elm == None:
                if self.debug_print_fill_xml:
                    logging.debug(f'elm is None')
            elm.text = self.indent14
            elm.tail = self.indent12

            try:
                subelm = ET.SubElement(elm, "secretion_rate",{"units":self.default_rate_units})
                subelm.text = self.param_d[cdef]["secretion"][substrate]["secretion_rate"]
                subelm.tail = self.indent14

                subelm = ET.SubElement(elm, "secretion_target",{"units":"substrate density"})
                subelm.text = self.param_d[cdef]["secretion"][substrate]["secretion_target"]
                subelm.tail = self.indent14

                subelm = ET.SubElement(elm, "uptake_rate",{"units":self.default_rate_units})
                subelm.text = self.param_d[cdef]["secretion"][substrate]["uptake_rate"]
                subelm.tail = self.indent14

                subelm = ET.SubElement(elm, "net_export_rate",{"units":"total substrate/min"})
                subelm.text = self.param_d[cdef]["secretion"][substrate]["net_export_rate"]
                subelm.tail = self.indent12
            except:
                msg = f"Error: unable to update XML secretion parameters for {substrate} for cell type {cdef}. Please fix your XML config file."
                print(msg)
                msgBox = QMessageBox()
                msgBox.setTextFormat(Qt.RichText)
                msgBox.setText(msg)
                msgBox.setStandardButtons(QMessageBox.Ok)
                returnValue = msgBox.exec()

    #-------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml_interactions(self,pheno,cdef):
        if self.debug_print_fill_xml:
            logging.debug(f'------------------- fill_xml_interactions():  cdef= {cdef}')
            print(f'------------------- fill_xml_interactions():  cdef= {cdef}')

        interactions = ET.SubElement(pheno, "cell_interactions")
        interactions.text = self.indent12  # affects indent of child
        interactions.tail = "\n" + self.indent10

        subelm = ET.SubElement(interactions, "apoptotic_phagocytosis_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdef]["apoptotic_phagocytosis_rate"]
        subelm.tail = self.indent12

        subelm = ET.SubElement(interactions, "necrotic_phagocytosis_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdef]["necrotic_phagocytosis_rate"]
        subelm.tail = self.indent12

        subelm = ET.SubElement(interactions, "other_dead_phagocytosis_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdef]["other_dead_phagocytosis_rate"]
        subelm.tail = self.indent12

        #-----
        lpr = ET.SubElement(interactions, "live_phagocytosis_rates")
        lpr.text = self.indent16
        lpr.tail = "\n" + self.indent12

        logging.debug(f'--- live_phagocytosis_rate= {self.param_d[cdef]["live_phagocytosis_rate"]}')
        for key in self.param_d[cdef]['live_phagocytosis_rate'].keys():
            logging.debug(f'  key in live_phagocytosis_rate= {key}')
            print(f'  key in live_phagocytosis_rate= {key}')
            if len(key) == 0:
                continue
            val = self.param_d[cdef]['live_phagocytosis_rate'][key]
            logging.debug(f'{key}  --> {val}')
            print(f'{key}  --> {val}')
            elm = ET.SubElement(lpr, 'phagocytosis_rate', {"name":key, "units":self.default_rate_units})
            elm.text = val
            elm.tail = self.indent16
            
        # elm.tail = "\n" + self.indent10

        #-----
        arates = ET.SubElement(interactions, "attack_rates")
        arates.text = self.indent18
        arates.tail = "\n" + self.indent12

        logging.debug(f'--- attack_rate= {self.param_d[cdef]["attack_rate"]}')
        for key in self.param_d[cdef]['attack_rate'].keys():
            # argh, not sure why this is necessary, but without it, we can get empty entries if we read in a saved mymodel.xml
            if len(key) == 0:  
                continue
            val = self.param_d[cdef]['attack_rate'][key]
            logging.debug(f'{key}  --> {val}')
            elm = ET.SubElement(arates, 'attack_rate', {"name":key, "units":self.default_rate_units})
            elm.text = val
            elm.tail = self.indent18

        #-----
        subelm = ET.SubElement(interactions, "attack_damage_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdef]["attack_damage_rate"]
        subelm.tail = self.indent12

        subelm = ET.SubElement(interactions, "attack_duration",{"units":self.default_time_units})
        subelm.text = self.param_d[cdef]["attack_duration"]
        subelm.tail = self.indent12

        #-----
        frates = ET.SubElement(interactions, "fusion_rates")
        frates.text = self.indent18
        frates.tail = "\n" + self.indent10

        logging.debug(f'--- fusion_rate= {self.param_d[cdef]["fusion_rate"]}')
        for key in self.param_d[cdef]['fusion_rate'].keys():
            # argh, not sure why this is necessary, but without it, we can get empty entries if we read in a saved mymodel.xml
            if len(key) == 0:
                continue
            val = self.param_d[cdef]['fusion_rate'][key]
            logging.debug(f'{key}  --> {val}')
            elm = ET.SubElement(frates, 'fusion_rate', {"name":key, "units":self.default_rate_units})
            elm.text = val
            elm.tail = self.indent18

        #---------------------------
        xforms = ET.SubElement(pheno, "cell_transformations")
        xforms.text = self.indent12  # affects indent of child
        xforms.tail = "\n" + self.indent10

        trates = ET.SubElement(xforms, "transformation_rates")
        trates.text = self.indent16
        trates.tail = self.indent12

        for key in self.param_d[cdef]['transformation_rate'].keys():
            # argh, not sure why this is necessary, but without it, we can get empty entries if we read in a saved mymodel.xml
            if len(key) == 0:
                continue
            val = self.param_d[cdef]['transformation_rate'][key]
            logging.debug(f'{key}  --> {val}')
            elm = ET.SubElement(trates, 'transformation_rate', {"name":key, "units":self.default_rate_units})
            elm.text = val
            elm.tail = self.indent16

        #-----
        integrity = ET.SubElement(pheno, "cell_integrity")
        integrity.text = self.indent12  # affects indent of child
        integrity.tail = "\n" + self.indent10

        subelm = ET.SubElement(integrity, "damage_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdef]["damage_rate"]
        subelm.tail = self.indent12

        subelm = ET.SubElement(integrity, "damage_repair_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdef]["damage_repair_rate"]
        subelm.tail = self.indent12

    #-------------------------------------------------------------------
    # Get values from the dict and generate/write a new XML
    def fill_xml_intracellular(self, pheno, cdef):
        if self.debug_print_fill_xml:
            logging.debug(f'------------------- cell_def_tab.py:  fill_xml_intracellular()')
            logging.debug(f'------ ["intracellular"]: for {cdef}')
            logging.debug(f'{self.param_d[cdef]["intracellular"]}')

            #-----  rwh: Sep 2024
            # self.param_d[cdef]['intracellular'] = {}
            if "none" in self.intracellular_type_dropdown.currentText():
                self.param_d[cdef]['intracellular'] = None
            # elif "Boolean" in self.intracellular_type_dropdown.currentText():
            #     self.param_d[cdef]['intracellular'] = {}
            #     self.param_d[cdef]['intracellular']['type'] = "maboss"
            elif "ODEs" in self.intracellular_type_dropdown.currentText():
                print(f'\n\n------------------- cell_def_tab.py:  fill_xml_intracellular()')
                self.param_d[cdef]['intracellular'] = {}
                self.param_d[cdef]['intracellular']['type'] = "roadrunner"
                print(f'------------------- ',self.param_d[cdef]['intracellular'])

            if self.param_d[cdef]['intracellular'] is not None:
                print(f'------ fill_xml_intracellular:  {self.param_d[cdef]["intracellular"]}')

                if self.param_d[cdef]['intracellular']['type'] == "maboss":
                            
                    # Checking if you should prevent saving because of missing input
                    if 'bnd_filename' not in self.param_d[cdef]['intracellular'] or self.param_d[cdef]['intracellular']['bnd_filename'] in [None, ""]:
                        raise CellDefException("Missing BND file in the " + cdef + " cell definition ")

                    if 'cfg_filename' not in self.param_d[cdef]['intracellular'] or self.param_d[cdef]['intracellular']['cfg_filename'] in [None, ""]:
                        raise CellDefException("Missing CFG file in the " + cdef + " cell definition ")

                    intracellular = ET.SubElement(pheno, "intracellular", {"type": "maboss"})
                    intracellular.text = self.indent12  # affects indent of child
                    intracellular.tail = "\n" + self.indent10

                    bnd_filename = ET.SubElement(intracellular, "bnd_filename")
                    bnd_filename.text = self.param_d[cdef]['intracellular']['bnd_filename']
                    bnd_filename.tail = self.indent12

                    cfg_filename = ET.SubElement(intracellular, "cfg_filename")
                    cfg_filename.text = self.param_d[cdef]['intracellular']['cfg_filename']
                    cfg_filename.tail = self.indent12

                    if len(self.param_d[cdef]['intracellular']['initial_values']) > 0:
                        initial_values = ET.SubElement(intracellular, "initial_values")
                        initial_values.text = self.indent14
                        initial_values.tail = self.indent12
                        
                        for initial_value_def in self.param_d[cdef]['intracellular']['initial_values']:
                            if initial_value_def["node"] != "" and initial_value_def["value"] != "":
                                initial_value = ET.SubElement(initial_values, "initial_value", {"intracellular_name": initial_value_def["node"]})
                                initial_value.text = initial_value_def["value"]
                                initial_value.tail = self.indent14
                        initial_value.tail = self.indent12
                        
                    # Settings
                    settings = ET.SubElement(intracellular, "settings")
                    settings.text = self.indent14
                    settings.tail = self.indent12
                
                    time_step = ET.SubElement(settings, "intracellular_dt")
                    time_step.text = self.param_d[cdef]['intracellular']['time_step']
                    time_step.tail = self.indent14
                    
                    time_stochasticity = ET.SubElement(settings, "time_stochasticity")
                    time_stochasticity.text = self.param_d[cdef]['intracellular']['time_stochasticity']
                    time_stochasticity.tail = self.indent14
                    
                    scaling = ET.SubElement(settings, "scaling")
                    scaling.text = self.param_d[cdef]['intracellular']['scaling']
                    scaling.tail = self.indent12
                    
                    start_time = ET.SubElement(settings, "start_time")
                    start_time.text = self.param_d[cdef]['intracellular']['start_time']
                    start_time.tail = self.indent12
                    
                    inheritance = ET.SubElement(settings, "inheritance", {"global": self.param_d[cdef]['intracellular']['global_inheritance']})
                    if len(self.param_d[cdef]["intracellular"]["node_inheritance"]) > 0:
                        for node_inheritance_def in self.param_d[cdef]["intracellular"]["node_inheritance"]:
                            if node_inheritance_def["node"] != "" and node_inheritance_def["flag"] != "":
                                node_inheritance = ET.SubElement(inheritance, "inherit_node", {"intracellular_name": node_inheritance_def["node"]})
                                node_inheritance.text = node_inheritance_def["flag"]
                                node_inheritance.tail = self.indent16

                    if len(self.param_d[cdef]["intracellular"]["mutants"]) > 0:
                        scaling.tail = self.indent14
                        mutants = ET.SubElement(settings, "mutations")
                        mutants.text = self.indent16
                        mutants.tail = self.indent14
                        
                        for mutant_def in self.param_d[cdef]["intracellular"]["mutants"]:
                            if mutant_def["node"] != "" and mutant_def["value"] != "":
                                mutant = ET.SubElement(mutants, "mutation", {"intracellular_name": mutant_def["node"]})
                                mutant.text = mutant_def["value"]
                                mutant.tail = self.indent16

                        mutant.tail = self.indent12

                    if len(self.param_d[cdef]['intracellular']['parameters']) > 0:
                        scaling.tail = self.indent14

                        parameters = ET.SubElement(settings, "parameters")
                        parameters.text = self.indent16
                        parameters.tail = self.indent14
                        
                        for parameter_def in self.param_d[cdef]['intracellular']['parameters']:
                            if parameter_def["name"] != "" and parameter_def["value"] != "":
                                parameter = ET.SubElement(parameters, "parameter", {"intracellular_name": parameter_def["name"]})
                                parameter.text = parameter_def["value"]
                                parameter.tail = self.indent16

                        parameter.tail = self.indent12

                    # Mapping
                    if len(self.param_d[cdef]['intracellular']['inputs']) > 0 or len(self.param_d[cdef]['intracellular']['outputs']) > 0:
                        mapping = ET.SubElement(intracellular, "mapping")
                        mapping.text = self.indent14
                        mapping.tail = self.indent12

                        tag_input = None
                        for input in self.param_d[cdef]['intracellular']['inputs']:
                            
                            if input['name'] != '' and input['node'] != '' and input['threshold'] != '' and input['action'] != '':
                                attribs = {
                                    'physicell_name': input['name'], 'intracellular_name': input['node'], 
                                }

                                tag_input = ET.SubElement(mapping, 'input', attribs)
                                tag_input.text = self.indent16
                                tag_input.tail = self.indent14

                                tag_input_settings = ET.SubElement(tag_input, "settings")
                                tag_input_settings.text = self.indent18
                                tag_input_settings.tail = self.indent16
                                tag_input_action = ET.SubElement(tag_input_settings, "action")
                                tag_input_action.text = input["action"]
                                tag_input_action.tail = self.indent18

                                tag_input_threshold = ET.SubElement(tag_input_settings, "threshold")
                                tag_input_threshold.text = input["threshold"]
                                tag_input_threshold.tail = self.indent18

                                t_last_tag = tag_input_threshold
                                if input["inact_threshold"] != input["threshold"]:
                                    tag_input_inact_threshold = ET.SubElement(tag_input_settings, "inact_threshold")
                                    tag_input_inact_threshold.text = input["inact_threshold"]
                                    tag_input_inact_threshold.tail = self.indent18
                                    t_last_tag = tag_input_inact_threshold
                                if input["smoothing"] != "":
                                    tag_input_smoothing = ET.SubElement(tag_input_settings, "smoothing")
                                    tag_input_smoothing.text = input["smoothing"]
                                    tag_input_smoothing.tail = self.indent18
                                    t_last_tag = tag_input_smoothing

                                t_last_tag.tail = self.indent14
                                
                        tag_output = None
                        for output in self.param_d[cdef]['intracellular']['outputs']:

                            if output['name'] != '' and output['node'] != '' and output['value'] != '' and output['action'] != '':
                                attribs = {
                                    'physicell_name': output['name'], 'intracellular_name': output['node'], 
                                }

                                tag_output = ET.SubElement(mapping, 'output', attribs)
                                tag_output.text = self.indent16
                                tag_output.tail = self.indent12
                                
                                tag_output_settings = ET.SubElement(tag_output, "settings")
                                tag_output_settings.text = self.indent18
                                tag_output_settings.tail = self.indent14

                                tag_output_action = ET.SubElement(tag_output_settings, "action")
                                tag_output_action.text = output["action"]
                                tag_output_action.tail = self.indent18

                                tag_output_value = ET.SubElement(tag_output_settings, "value")
                                tag_output_value.text = output["value"]
                                tag_output_value.tail = self.indent18

                                t_last_tag = tag_output_value

                                if output["basal_value"] != output["value"]:
                                    tag_output_base_value = ET.SubElement(tag_output_settings, "base_value")
                                    tag_output_base_value.text = output["basal_value"]
                                    tag_output_base_value.tail = self.indent18
                                    t_last_tag = tag_output_base_value
                                
                                if output["smoothing"] != "":
                                    tag_output_smoothing = ET.SubElement(tag_output_settings, "smoothing")
                                    tag_output_smoothing.text = output["smoothing"]
                                    tag_output_smoothing.tail = self.indent18
                                    t_last_tag = tag_output_smoothing

                                t_last_tag.tail = self.indent14
                                
                        
                        if len(self.param_d[cdef]['intracellular']['outputs']) == 0 and tag_input is not None:
                            tag_input.tail = self.indent12
                        elif tag_output is not None:
                            tag_output.tail = self.indent12


                elif self.param_d[cdef]['intracellular']['type'] == "roadrunner":
                    self.ode_sbml_frame.fill_xml(pheno, cdef)
                    

        if self.debug_print_fill_xml:
            logging.debug(f'\n')
    #-------------------------------------------------------------------
    # Get values from the dict and generate/write a new XML
    def fill_xml_custom_data(self, custom_data, cdef):
        elm = None
        if self.debug_print_fill_xml:
            # logging.debug(f'------------------- fill_xml_custom_data():  self.custom_var_count = {self.custom_var_count}')
            # print(f'------------------- fill_xml_custom_data():  self.custom_var_count = {self.custom_var_count}')
            logging.debug(f'------ ["custom_data"]: for {cdef}')
            # print(self.param_d[cdef]['custom_data'])

        # if self.custom_var_count == 0:
        #     logging.debug(f' fill_xml_custom_data():  leaving due to count=0')
        #     return

        idx = 0
        for key_name in self.param_d[cdef]['custom_data'].keys():
            # print(f'---------\nfill_xml_custom_data()  key_name= {key_name}, len(key_name)={len(key_name)}')
            if len(key_name) == 0:
                self.custom_table_error(-1,-1,f"Warning: There is at least one empty Cell Type Custom Data variable name.")
                continue
            elif len(self.param_d[cdef]['custom_data'][key_name][0]) == 0:  # value for this var for this cell def
                self.custom_table_error(-1,-1,f"Warning: Not saving '{key_name}' due to missing value.")
                continue
            # print(f"fill_xml_custom_data() {self.param_d[cdef]['custom_data'][key_name]}")
            # print("len custom_var_d=", len(self.master_custom_var_d[key_name]))
            if key_name not in self.master_custom_var_d.keys():   # rwh: would this ever happen?
                # print(f' fill_xml_custom_data():  weird, key_name {key_name} not in master_custom_var_d. Adding dummy [0,"", ""].')
                self.master_custom_var_d[key_name] = [0, '','']  # [wrow, units, desc]
            # print(f'fill_xml_custom_data():  custom_var_d= {self.master_custom_var_d[key_name]}')
            units = self.master_custom_var_d[key_name][1]  # hack, hard-coded
            # print(f'  units = {units}')
            desc = self.master_custom_var_d[key_name][2]  # hack, hard-coded
            # print(f'  desc = {desc}')

            conserved = "false"
            if self.param_d[cdef]['custom_data'][key_name][1]:  # hack, hard-coded
            # if self.custom_data_conserved[idx].checkState():
                conserved = "true"
            idx += 1
            elm = ET.SubElement(custom_data, key_name, 
                    { "conserved":conserved,
                      "units":units,
                      "description":desc } )

            # elm.text = self.param_d[cdef]['custom_data'][key_name]  # value for this var for this cell def
            elm.text = self.param_d[cdef]['custom_data'][key_name][0]  # value for this var for this cell def
            elm.tail = self.indent10

        # print("\n------ updated cell_def custom_data:")
        # print(self.param_d[cdef]['custom_data'])

        if elm:
            elm.tail = self.indent8   # back up 2 for the very last one

        # if self.debug_print_fill_xml:
        #     logging.debug(f'\n')

    def fill_par_dists(self, par_dists, cdef):
        elm = None
        if self.debug_print_fill_xml:
            logging.debug(f'------ ["initial_parameter_distributions"]: for {cdef}')

        if "par_dists" not in self.param_d[cdef].keys():
            return
        # if self.param_d[cdef]['par_dists_disabled']:
        #     return

        for key_name, value in self.param_d[cdef]['par_dists'].items():
            if "distribution" not in value.keys() or value["distribution"] == "None":
                continue
            enabled = "true" if value["enabled"] else "false"
            enforce_base = "true" if value["enforce_base"] else "false"
            dist_type = value["distribution"]
            # remove whitespaces from dist_type
            dist_type = dist_type.replace(" ", "")
            dist_elm = ET.SubElement(par_dists, "distribution", 
                    { "enabled":enabled,
                      "type":dist_type,
                      "check_base":enforce_base } )
            behavior_elm = ET.SubElement(dist_elm, "behavior")
            behavior_elm.text = key_name
            for par_name, par_value in value["parameters"].items():
                if par_value == "":
                    continue # adding a blank element will cause pugixml to record a value of 0
                par_elm = ET.SubElement(dist_elm, par_name)
                par_elm.text = par_value

        if elm:
            elm.tail = self.indent8   # back up 2 for the very last one

    #-------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml(self):
        logging.debug(f'\n\n----------- cell_def_tab.py: fill_xml(): ----------')

        uep = self.xml_root.find('.//cell_definitions') # guaranteed to exist since we start with a valid model
        if uep:
            # Begin by removing all previously defined cell defs in the .xml
            for cell_def in uep.findall('cell_definition'):
                uep.remove(cell_def)

        # Obtain a list of all cell defs in self.tree (QTreeWidget()). Used below.
        cdefs_in_tree = []
        num_cdefs = self.tree.invisibleRootItem().childCount()  # rwh: get number of items in tree
        logging.debug(f'num cell defs = {num_cdefs}')
        self.iterate_tree(self.tree.invisibleRootItem(), num_cdefs, cdefs_in_tree)
        logging.debug(f'cdefs_in_tree ={cdefs_in_tree}')

        uep = self.xml_root.find('.//cell_definitions')


        # Note: at this point, the IDs should be guaranteed to be in a, possibly unordered, sequence of IDs
        # whose #s include 0-N. For example, there may appear in the order ID=2, ID=0, ID=1. When we write out
        # these cell_defs, we want to put them in sequential order: 0,1,2.
        id_l = []
        for cdef in self.param_d.keys():
            id_l.append(self.param_d[cdef]["ID"])
        print(f'------------cell_def_tab.py: fill_xml(): (original) IDs = {id_l}')

        idx = 0
        done = False

        num_outer_loops = len(self.param_d.keys())
        if self.auto_number_IDs_checkbox.isChecked():
            num_outer_loops = 1

        for count in range(num_outer_loops):
            # print("---- count= ",count)
            for cdef in self.param_d.keys():
                if not self.auto_number_IDs_checkbox.isChecked():
                    if int(self.param_d[cdef]["ID"]) != count:
                        continue

                logging.debug(f'\n--- key in param_d.keys() = {cdef}')
                if cdef in cdefs_in_tree or self.xml_creator.pytest_flag:
                    logging.debug(f'matched! {cdef}')

            # <cell_definition name="round cell" ID="0">
            # 	<phenotype>
            # 		<cycle code="5" name="live">  
            # 			<phase_transition_rates units="1/min"> 
            # 				<rate start_index="0" end_index="0" fixed_duration="true">0.000072</rate>
            # 			</phase_transition_rates>
            # 		</cycle>
            # vs.
                        # <phase_durations units="min"> 
                        # 	<duration index="0" fixed_duration="false">300.0</duration>
                        # 	<duration index="1" fixed_duration="true">480</duration>
                        # 	<duration index="2" fixed_duration="true">240</duration>
                        # 	<duration index="3" fixed_duration="true">60</duration>
                        # </phase_durations>
                    # print("cell_def_tab.py: fill_xml(): --> ",var.attrib['ID'])
                    if self.auto_number_IDs_checkbox.isChecked():
                        elm = ET.Element("cell_definition", 
                                {"name":cdef, "ID":str(idx)})
                    else:
                        elm = ET.Element("cell_definition", 
                                {"name":cdef, "ID":self.param_d[cdef]["ID"]})  # rwh: if retaining original IDs.
                    elm.tail = '\n' + self.indent6
                    elm.text = self.indent8
                    pheno = ET.SubElement(elm, 'phenotype')
                    pheno.text = self.indent10
                    pheno.tail = self.indent8

                    self.cycle_tab.fill_xml(pheno,cdef)
                    self.fill_xml_death(pheno,cdef)
                    self.fill_xml_volume(pheno,cdef)
                    self.fill_xml_mechanics(pheno,cdef)
                    self.fill_xml_motility(pheno,cdef)
                    self.fill_xml_secretion(pheno,cdef)
                    self.fill_xml_interactions(pheno,cdef)
                    self.fill_xml_intracellular(pheno,cdef)

                    # ------- custom data ------- 
                    custom_data = ET.SubElement(elm, 'custom_data')
                    custom_data.text = self.indent10
                    custom_data.tail = self.indent6
                    self.fill_xml_custom_data(custom_data,cdef)

                    par_dists_enabled = "false"
                    if "par_dists_disabled" in self.param_d[cdef].keys():
                        par_dists_enabled = "false" if self.param_d[cdef]["par_dists_disabled"] else "true"
                    par_dists = ET.SubElement(elm, 'initial_parameter_distributions',
                                            { "enabled":par_dists_enabled })
                    par_dists.text = self.indent10
                    par_dists.tail = self.indent6
                    self.fill_par_dists(par_dists, cdef)

                    uep.insert(idx,elm)
                    idx += 1

        logging.debug(f'----------- end cell_def_tab.py: fill_xml(): ----------')

    #-------------------------------------------------------------------
    # Simple text summary of cell types phenotypes
    def summary(self, textW):
        print("cell_def_tab.py: ----------------- summary() ---------------")
        for cdef in self.param_d.keys():
            textW.appendPlainText(">>> "+cdef)
            textW.appendPlainText("-- mechanics")
            textW.appendPlainText(self.param_d[cdef]['mechanics_adhesion'])
