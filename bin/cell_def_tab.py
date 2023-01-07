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
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDoubleValidator
# from PyQt5.QtCore import Qt
# from cell_def_custom_data import CustomData



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

class CellDef(QWidget):
    def __init__(self, dark_mode):
        super().__init__()
        # global self.params_cell_def

        # primary key = cell def name
        # secondary keys: cycle_rate_choice, cycle_dropdown, 
        self.param_d = {}  # a dict of dicts
        self.num_dec = 5  # how many digits to right of decimal point?

        # self.chemotactic_sensitivity_dict = {}   # rwh - bogus/not useful since we need per cell type
        self.default_sval = '0.0'  # default scalar value (as string)
        self.default_affinity = '1.0'
        self.default_bval = False
        self.default_time_units = "min"
        self.default_rate_units = "1/min"

        # rf. https://www.w3.org/TR/SVG11/types.html#ColorKeywords
        self.row_color1 = "background-color: Tan"
        self.row_color2 =  "background-color: LightGreen"
        if dark_mode:
            self.row_color1 = "background-color: darkslategray"  # = rgb( 47, 79, 79)
            self.row_color2 =  "background-color: rgb( 99, 99, 10)"

        self.ics_tab = None

        self.current_cell_def = None
        self.cell_adhesion_affinity_celltype = None

        self.new_cell_def_count = 1
        self.label_width = 210
        self.units_width = 110
        self.idx_current_cell_def = 1    # 1-offset for XML (ElementTree, ET)
        self.xml_root = None
        self.config_path = None
        self.debug_print_fill_xml = True
        # self.custom_var_count = 0  # no longer used? just get len(self.master_custom_var_d)
        self.max_custom_data_rows = 99
        self.max_entries = self.max_custom_data_rows

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
        self.stacked_cycle = QStackedWidget()

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

        # used in fill_xml_cycle()
        self.cycle_combo_idx_code = {0:"5", 1:"1", 2:"0", 3:"2", 4:"6", 5:"7"}
        # TODO: check if these names must be specific in the C++ 
        self.cycle_combo_idx_name = {0:"live", 1:"basic Ki67", 2:"advanced Ki67", 3:"flow cytometry", 4:"Flow cytometry model (separated)", 5:"cycling quiescent"}

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

        # <substrate name="virus">
        #     <secretion_rate units="1/min">0</secretion_rate>
        #     <secretion_target units="substrate density">1</secretion_target>
        #     <uptake_rate units="1/min">10</uptake_rate>
        #     <net_export_rate units="total substrate/min">0</net_export_rate> 
        # </substrate> 

        # Create lists for cell type secretion values, for each substrate (index by substrate index)
        # self.secretion_rate_val = []  # .setText(uep.find(secretion_sub1_path+"secretion_rate").text)
        # self.secretion_target_val = []
        # self.secretion_uptake_rate_val = []
        # self.secretion_net_export_rate_val = []

        # self.cell_defs = CellDefInstances()
        self.cell_def_horiz_layout = QHBoxLayout()

        self.splitter = QSplitter()

        # tree_widget_width = 160
        tree_widget_width = 190
        tree_widget_height = 400
        # tree_widget_height = 1200

        self.tree = QTreeWidget() # tree is overkill; list would suffice; meh.
        self.tree.setFocusPolicy(QtCore.Qt.NoFocus)  # don't allow arrow keys to select
        # self.tree.setStyleSheet("background-color: lightgray")
        # self.tree.setFixedWidth(tree_widget_width)
        self.tree.setFixedHeight(tree_widget_height)
        # self.tree.setColumnCount(1)
        self.tree.itemClicked.connect(self.tree_item_clicked_cb)
        self.tree.itemChanged.connect(self.tree_item_changed_cb)   # rename a cell type

        header = QTreeWidgetItem(["---  Cell Type  ---"])

        self.tree.setHeaderItem(header)

        self.physiboss_boolean_frame = QFrame()
        self.physiboss_signals = []
        self.physiboss_behaviours = []
        items = []
        model = QtCore.QStringListModel()
        model.setStringList(["aaa","bbb"])

        self.cell_def_horiz_layout.addWidget(self.tree)

        self.scroll_cell_def_tree = QScrollArea()
        # self.scroll_cell_def_tree.setWidget(self.tree)

        #-----------
        tree_w_vbox = QVBoxLayout()
        tree_w_vbox.addWidget(self.tree)

        # splitter.addWidget(self.tree)
        self.splitter.addWidget(self.scroll_cell_def_tree)

        #------------------
        tree_w_hbox = QHBoxLayout()
        # self.controls_hbox = QHBoxLayout()
        self.new_button = QPushButton("New")
        self.new_button.clicked.connect(self.new_cell_def)
        self.new_button.setStyleSheet("background-color: lightgreen")
        # self.controls_hbox.addWidget(self.new_button)
        tree_w_hbox.addWidget(self.new_button)

        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_cell_def)
        self.copy_button.setStyleSheet("background-color: lightgreen")
        # self.controls_hbox.addWidget(self.copy_button)
        tree_w_hbox.addWidget(self.copy_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_cell_def)
        self.delete_button.setStyleSheet("background-color: yellow")
        # self.controls_hbox.addWidget(self.delete_button)
        tree_w_hbox.addWidget(self.delete_button)

        #---------
        self.tree_w = QWidget()
        tree_w_vbox.addLayout(tree_w_hbox)
        self.tree_w.setLayout(tree_w_vbox)
        self.scroll_cell_def_tree.setWidget(self.tree_w)

        #------------------
        # self.cycle_tab = QWidget()
        # self.death_tab = QWidget()
        # self.volume_tab = QWidget()
        # self.mechanics_tab = QWidget()
        # self.motility_tab = QWidget()
        # self.secretion_tab = QWidget()
        # self.interaction_tab = QWidget()

        self.custom_data_tab = QWidget()
        # self.custom_data_conserved = []  # rwh: do I use this?
        # self.custom_data_name = []
        # self.custom_data_value = []   # rwh: [text, conserved_flag] or [text, conserved_flag, units]?
        # self.custom_data_units = []
        # self.custom_data_description = []

        # self.scroll_params = QScrollArea()

        self.tab_widget = QTabWidget()
        # self.tab_params_widget = QTabWidget()
        # self.splitter.addWidget(self.scroll_params)
        self.splitter.addWidget(self.tab_widget)

        # self.tab_widget.setStyleSheet('''
        # QTabWidget {
        #     background: magenta;
        #     border: none;
        # }
        # QTabBar::tab {
        #     background: green;
        # }
        # ''')
        self.tab_widget.addTab(self.create_cycle_tab(),"Cycle")
        self.tab_widget.addTab(self.create_death_tab(),"Death")
        self.tab_widget.addTab(self.create_volume_tab(),"Volume")
        self.tab_widget.addTab(self.create_mechanics_tab(),"Mechanics")
        self.tab_widget.addTab(self.create_motility_tab(),"Motility")
        self.tab_widget.addTab(self.create_secretion_tab(),"Secretion")
        self.tab_widget.addTab(self.create_interaction_tab(),"Interactions")
        self.tab_widget.addTab(self.create_intracellular_tab(),"Intracellular")
        self.tab_widget.addTab(self.create_custom_data_tab(),"Custom Data")

        #---rwh
        # self.custom_data_tab = CustomData(False)
        # self.tab_widget.addTab(self.custom_data_tab,"Custom Data")
        # self.custom_data_tab.param_d = self.param_d

        self.cell_types_tabs_layout = QGridLayout()
        self.cell_types_tabs_layout.addWidget(self.tab_widget, 0,0,1,1) # w, row, column, rowspan, colspan
        # self.cell_types_tabs_layout.addWidget(self.tab_params_widget, 1,0,1,1) # w, row, column, rowspan, colspan

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
    def init_default_phenotype_params(self, cdname):
        self.new_cycle_params(cdname)
        self.new_death_params(cdname)
        self.new_volume_params(cdname)
        self.new_mechanics_params(cdname)
        self.new_motility_params(cdname)
        self.new_secretion_params(cdname)
        self.new_interaction_params(cdname)
        self.new_intracellular_params(cdname)
        self.new_custom_data_params(cdname)

        # print("\n\n",self.param_d)
        # self.custom_data_tab.param_d = self.param_d
        # self.custom_data_tab.new_custom_data_params(cdname)

    #----------------------------------------------------------------------
    # @QtCore.Slot()
    def new_cell_def(self):
        # print('------ new_cell_def')
        cdname = "cell_def%02d" % self.new_cell_def_count
        # Make a new substrate (that's a copy of the currently selected one)
        self.param_d[cdname] = copy.deepcopy(self.param_d[self.current_cell_def])
        self.param_d[cdname]["ID"] = str(self.new_cell_def_count)

        # for k in self.param_d.keys():
        #     print(" (pre-new vals)===>>> ",k, " : ", self.param_d[k])
        #     print()
        # print()

        self.init_default_phenotype_params(cdname)

        # print("\n ----- new dict:")
        # for k in self.param_d.keys():
        #     print(" ===>>> ",k, " : ", self.param_d[k])
        #     print()

        self.new_cell_def_count += 1
        self.current_cell_def = cdname

        self.add_new_celltype(cdname)  # add to all qcomboboxes that have celltypes (e.g., in interactions)

        #-----  Update this new cell def's widgets' values
        num_items = self.tree.invisibleRootItem().childCount()
        # print("tree has num_items = ",num_items)
        treeitem = QTreeWidgetItem([cdname])
        treeitem.setFlags(treeitem.flags() | QtCore.Qt.ItemIsEditable)
        self.tree.insertTopLevelItem(num_items,treeitem)
        self.tree.setCurrentItem(treeitem)

        self.tree_item_clicked_cb(treeitem, 0)

    #----------------------
    # When a cell type is selected(via double-click) and renamed
    def tree_item_changed_cb(self, it,col):
        logging.debug(f'--------- tree_item_changed_cb(): {it}, {col}, {it.text(col)}')  # col=0 always

        prev_name = self.current_cell_def
        logging.debug(f'prev_name= {prev_name}')
        self.current_cell_def = it.text(col)
        logging.debug(f'new name= {self.current_cell_def}')
        self.param_d[self.current_cell_def] = self.param_d.pop(prev_name)  # sweet

        self.renamed_celltype(prev_name, self.current_cell_def)

    #----------------------------------------------------------------------
    # @QtCore.Slot()
    # Make a new cell_def (that's a copy of the currently selected one)
    def copy_cell_def(self):
        # print('------ copy_cell_def')
        cdname_copy = "cell_def%02d" % self.new_cell_def_count
        cdname_original = self.current_cell_def
        self.param_d[cdname_copy] = copy.deepcopy(self.param_d[cdname_original])
        # self.param_d[cdname_copy]["ID"] = str(self.new_cell_def_count)  # no longer necessary; we auto-generate at 'save'

        # we need to add the newly created cell def into each cell def's interaction/transformation dicts, with values of the copy
        sval = self.default_sval
        for cdname in self.param_d.keys():    # for each cell def
            # for cdname2 in self.param_d[cdname]['live_phagocytosis_rate'].keys():    # for each cell def's 
            for cdname2 in self.param_d.keys():    # for each cell def
                # print('cdname2= ',cdname2)
                if (cdname == cdname_copy) or (cdname2 == cdname_copy): # use default if not available
                    self.param_d[cdname]['live_phagocytosis_rate'][cdname2] = sval
                    self.param_d[cdname]['attack_rate'][cdname2] = sval
                    self.param_d[cdname]['fusion_rate'][cdname2] = sval
                    self.param_d[cdname]['transformation_rate'][cdname2] = sval

                    self.param_d[cdname]['cell_adhesion_affinity'][cdname2] = '1.0'  # default affinity
                # else: # use values from copied cell def

        logging.debug(f'--> copy_cell_def():\n {self.param_d[cdname_copy]}')

        # for k in self.param_d.keys():
        #     print(" (pre-new vals)===>>> ",k, " : ", self.param_d[k])
        #     print()
        # print()

        self.new_cell_def_count += 1

        self.current_cell_def = cdname_copy
        # self.cell_type_name.setText(cdname)

        self.add_new_celltype(cdname_copy)  # add to all qcomboboxes that have celltypes (e.g., in interactions)

        #-----  Update this new cell def's widgets' values
        num_items = self.tree.invisibleRootItem().childCount()
        # print("tree has num_items = ",num_items)
        treeitem = QTreeWidgetItem([cdname_copy])
        treeitem.setFlags(treeitem.flags() | QtCore.Qt.ItemIsEditable)
        self.tree.insertTopLevelItem(num_items,treeitem)
        self.tree.setCurrentItem(treeitem)

        self.tree_item_clicked_cb(treeitem, 0)

        
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


    # @QtCore.Slot()
    def delete_cell_def(self):
        num_items = self.tree.invisibleRootItem().childCount()
        # print('------ delete_cell_def: num_items=',num_items)
        if num_items == 1:
            # print("Not allowed to delete all substrates.")
            # QMessageBox.information(self, "Not allowed to delete all substrates")
            self.show_delete_warning()
            return

        item_idx = self.tree.indexFromItem(self.tree.currentItem()).row() 
        # print('------      item_idx=',item_idx)
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
        logging.debug(f'Also delete {self.param_d[self.current_cell_def]} from dicts')
        # print("--- cell_adhesion_affinity= ",self.param_d[cdef]['cell_adhesion_affinity'])
        logging.debug(f'--- cell_adhesion_affinity= {self.param_d[self.current_cell_def]["cell_adhesion_affinity"]}')

        # remove from the widgets

        # for idx in range(len(self.celltypes_list)):
        #     # print("idx,old,new = ",idx, old_name,new_name)
        #     # if old_name in self.motility_substrate_dropdown.itemText(idx):
        #     if old_name == self.live_phagocytosis_dropdown.itemText(idx):
        #         self.live_phagocytosis_dropdown.setItemText(idx, new_name)
        #     if old_name == self.attack_rate_dropdown.itemText(idx):
        #         self.attack_rate_dropdown.setItemText(idx, new_name)
        #     if old_name == self.fusion_rate_dropdown.itemText(idx):
        #         self.fusion_rate_dropdown.setItemText(idx, new_name)
        #     if old_name == self.cell_transformation_dropdown.itemText(idx):
        #         self.cell_transformation_dropdown.setItemText(idx, new_name)

        # rwh: is this safe?
        del self.param_d[self.current_cell_def]

        # for k in self.param_d.keys():
        #     print(" ===>>> ",k, " : ", self.param_d[k])
        #     print()

        # For the remaining cell defs, if any, remove the deleted cell def from certain dicts
        for cdef in self.param_d.keys():
            # print(" ===>>> ",cdef, " : ", self.param_d[cdef])
            # Mechanics
            self.param_d[cdef]['cell_adhesion_affinity'].pop(self.current_cell_def,0)  

            # Interactions
            self.param_d[cdef]['live_phagocytosis_rate'].pop(self.current_cell_def,0)
            self.param_d[cdef]['attack_rate'].pop(self.current_cell_def,0)
            self.param_d[cdef]['fusion_rate'].pop(self.current_cell_def,0)
            self.param_d[cdef]['transformation_rate'].pop(self.current_cell_def,0)


        item_idx = self.tree.indexFromItem(self.tree.currentItem()).row() 
        # print('------      item_idx=',item_idx)
        # self.tree.removeItemWidget(self.tree.currentItem(), 0)
        self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(self.tree.currentItem()))

        # print('------      new name=',self.tree.currentItem().text(0))
        self.current_cell_def = self.tree.currentItem().text(0)

        self.tree_item_clicked_cb(self.tree.currentItem(), 0)

    #--------------------------------------------------------
    def insert_hacky_blank_lines(self, glayout):
        idr = 4
        for idx in range(11):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idr += 1
            glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan

    #--------------------------------------------------------
    def create_cycle_tab(self):
        logging.debug(f'\n====================== create_cycle_tab ===================')
        # self.group_cycle = QGroupBox()
        self.params_cycle = QWidget()
        self.vbox_cycle = QVBoxLayout()
        # glayout = QGridLayout()

        #----------------------------
        self.cycle_rate_duration_hbox = QHBoxLayout()
        # self.cycle_rb1 = QRadioButton("transition rate(s)", self)
        self.cycle_rb1 = QRadioButton("transition rate(s)")
        self.cycle_rb1.toggled.connect(self.cycle_phase_transition_cb)
        self.cycle_rate_duration_hbox.addWidget(self.cycle_rb1)

        # self.cycle_rb2 = QRadioButton("duration(s)", self)
        self.cycle_rb2 = QRadioButton("duration(s)")
        self.cycle_rb2.toggled.connect(self.cycle_phase_transition_cb)
        self.cycle_rate_duration_hbox.addWidget(self.cycle_rb2)

        self.cycle_rate_duration_hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        self.vbox_cycle.addLayout(self.cycle_rate_duration_hbox)

        #----------------------------
        self.cycle_dropdown = QComboBox()
        self.cycle_dropdown.setFixedWidth(300)
        # self.cycle_dropdown.currentIndex.connect(self.cycle_changed_cb)
        self.cycle_dropdown.currentIndexChanged.connect(self.cycle_changed_cb)
        # self.cycle_dropdown.currentIndexChanged.connect(self.cycle_phase_transition_cb)

        # Rf. Section 17 of User Guide and core/PhysiCell_constants.{h,cpp}
        # static const int advanced_Ki67_cycle_model= 0;
        # static const int basic_Ki67_cycle_model=1;
        # static const int flow_cytometry_cycle_model=2;
        # static const int live_apoptotic_cycle_model=3;
        # static const int total_cells_cycle_model=4;
        # static const int live_cells_cycle_model = 5; 
        # static const int flow_cytometry_separated_cycle_model = 6; 
        # static const int cycling_quiescent_model = 7; 
        self.cycle_dropdown.addItem("live cells")   # 0 -> 0
        self.cycle_dropdown.addItem("basic Ki67")   # 0 -> 1, 1 -> 0
        self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
        self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0
        self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0
        self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0
        # self.cycle_dropdown.addItem("live apoptotic")
        # self.cycle_dropdown.addItem("total cells")

        # self.vbox.addWidget(self.cycle_dropdown)
        # self.group_cycle.addWidget(self.cycle_dropdown)
        self.vbox_cycle.addWidget(self.cycle_dropdown)

        self.cycle_label = QLabel("Phenotype: cycle")
        self.cycle_label.setStyleSheet("background-color: orange")
        self.cycle_label.setAlignment(QtCore.Qt.AlignCenter)
        # self.vbox.addWidget(self.cycle_label)


        #-----------------------------
        # We'll create a unique widget to hold different rates or durations, depending
        # on which cycle and method of defining it (transition rates or duration times) is chosen.
        # Then we will only display the relevant one, based on these choices.
        # self.stacked_cycle = QStackedWidget()

        # transition rates
        self.stack_trate_live = QWidget()
        self.stack_trate_Ki67 = QWidget()
        self.stack_trate_advancedKi67 = QWidget()
        self.stack_trate_flowcyto = QWidget()
        self.stack_trate_flowcytosep = QWidget()
        self.stack_trate_quiescent = QWidget()

        # duration times
        self.stack_duration_live = QWidget()
        self.stack_duration_Ki67 = QWidget()
        self.stack_duration_advancedKi67 = QWidget()
        self.stack_duration_flowcyto = QWidget()
        self.stack_duration_flowcytosep = QWidget()
        self.stack_duration_quiescent = QWidget()


        #===========================================================
        #  Naming scheme for sets ("stacks") of cycle widgets:
        #     cycle_<type>_trate<SE>[_changed] (S=start, E=end)
        #     stack_trate_<type>[_idx]
        #
        #     cycle_<type>_duration<SE>[_changed] (S=start, E=end)
        #     stack_duration_<type>[_idx]
        #===========================================================

        #------ Cycle transition rate (live) ----------------------
        # self.cycle_dropdown.addItem("live cells")   # 0 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0->0 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_live_trate00 = QLineEdit()
        self.cycle_live_trate00.textChanged.connect(self.cycle_live_trate00_changed)
        self.cycle_live_trate00.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_live_trate00, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_live_trate00_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_live_trate00_fixed, 0,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_live_trate00_fixed.clicked.connect(self.cycle_live_trate00_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)
        # idr = 4
        # for idx in range(11):  # rwh: hack solution to align rows
        #     blank_line = QLabel("")
        #     idr += 1
        #     glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan
        #---
        #---
        self.stack_trate_live.setLayout(glayout)   

        idx_stacked_widget = 0
        self.stack_trate_live_idx = idx_stacked_widget 
        logging.debug(f' new stacked widget: trate live -------------> {idx_stacked_widget}')
        self.stacked_cycle.addWidget(self.stack_trate_live)  # <------------- stack widget 0


        #------ Cycle transition rates (Ki67) ----------------------
        # self.cycle_dropdown.addItem("basic Ki67")   # 0 -> 1, 1 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0->1 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_Ki67_trate01 = QLineEdit()
        self.cycle_Ki67_trate01.textChanged.connect(self.cycle_Ki67_trate01_changed)
        self.cycle_Ki67_trate01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_Ki67_trate01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_Ki67_trate01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_Ki67_trate01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_Ki67_trate01_fixed.clicked.connect(self.cycle_Ki67_trate01_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1->0 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_Ki67_trate10 = QLineEdit()
        self.cycle_Ki67_trate10.textChanged.connect(self.cycle_Ki67_trate10_changed)
        self.cycle_Ki67_trate10.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_Ki67_trate10, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_Ki67_trate10_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_Ki67_trate10_fixed, 1,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_Ki67_trate10_fixed.clicked.connect(self.cycle_Ki67_trate10_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)
        
        self.stack_trate_Ki67.setLayout(glayout)

        idx_stacked_widget += 1
        self.stack_trate_Ki67_idx = idx_stacked_widget 
        logging.debug(f' new stacked widget: trate Ki67 -------------> {idx_stacked_widget}')
        self.stacked_cycle.addWidget(self.stack_trate_Ki67) # <------------- stack widget 1


        #------ Cycle transition rates (advanced Ki67) ----------------------
        # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0->1 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_advancedKi67_trate01 = QLineEdit()
        self.cycle_advancedKi67_trate01.textChanged.connect(self.cycle_advancedKi67_trate01_changed)
        self.cycle_advancedKi67_trate01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_advancedKi67_trate01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_advancedKi67_trate01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_advancedKi67_trate01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_advancedKi67_trate01_fixed.clicked.connect(self.cycle_advancedKi67_trate01_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1->2 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_advancedKi67_trate12 = QLineEdit()
        self.cycle_advancedKi67_trate12.textChanged.connect(self.cycle_advancedKi67_trate12_changed)
        self.cycle_advancedKi67_trate12.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_advancedKi67_trate12, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_advancedKi67_trate12_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_advancedKi67_trate12_fixed, 1,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_advancedKi67_trate12_fixed.clicked.connect(self.cycle_advancedKi67_trate12_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 2->0 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 2,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_advancedKi67_trate20 = QLineEdit()
        self.cycle_advancedKi67_trate20.textChanged.connect(self.cycle_advancedKi67_trate20_changed)
        self.cycle_advancedKi67_trate20.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_advancedKi67_trate20, 2,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_advancedKi67_trate20_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_advancedKi67_trate20_fixed, 2,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_advancedKi67_trate20_fixed.clicked.connect(self.cycle_advancedKi67_trate20_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 2,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)
        
        self.stack_trate_advancedKi67.setLayout(glayout)
        idx_stacked_widget += 1
        logging.debug(f' new stacked widget: t02 -------------> {idx_stacked_widget}')
        self.stack_trate_advancedKi67_idx = idx_stacked_widget 
        self.stacked_cycle.addWidget(self.stack_trate_advancedKi67)


        #------ Cycle transition rates (flow cytometry) ----------------------
        # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0->1 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcyto_trate01 = QLineEdit()
        self.cycle_flowcyto_trate01.textChanged.connect(self.cycle_flowcyto_trate01_changed)
        self.cycle_flowcyto_trate01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_flowcyto_trate01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcyto_trate01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcyto_trate01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_flowcyto_trate01_fixed.clicked.connect(self.cycle_flowcyto_trate01_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1->2 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcyto_trate12 = QLineEdit()
        self.cycle_flowcyto_trate12.textChanged.connect(self.cycle_flowcyto_trate12_changed)
        self.cycle_flowcyto_trate12.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_flowcyto_trate12, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcyto_trate12_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcyto_trate12_fixed, 1,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_flowcyto_trate12_fixed.clicked.connect(self.cycle_flowcyto_trate12_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 2->0 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 2,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcyto_trate20 = QLineEdit()
        self.cycle_flowcyto_trate20.textChanged.connect(self.cycle_flowcyto_trate20_changed)
        self.cycle_flowcyto_trate20.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_flowcyto_trate20, 2,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcyto_trate20_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcyto_trate20_fixed, 2,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_flowcyto_trate20_fixed.clicked.connect(self.cycle_flowcyto_trate20_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 2,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)
        
        #-----
        self.stack_trate_flowcyto.setLayout(glayout)
        idx_stacked_widget += 1
        logging.debug(f' new stacked widget: trate_flowcyto -------------> {idx_stacked_widget}')
        self.stack_trate_flowcyto_idx = idx_stacked_widget 
        self.stacked_cycle.addWidget(self.stack_trate_flowcyto)


        #------ Cycle transition rates (flow cytometry separated) ----------------------
        # self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0

        glayout = QGridLayout()

        label = QLabel("phase 0->1 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_trate01 = QLineEdit()
        self.cycle_flowcytosep_trate01.textChanged.connect(self.cycle_flowcytosep_trate01_changed)
        self.cycle_flowcytosep_trate01.setValidator(QtGui.QDoubleValidator())
        self.cycle_flowcytosep_trate01.setMaxLength(10)  #rwhtest
        glayout.addWidget(self.cycle_flowcytosep_trate01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_trate01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcytosep_trate01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_flowcytosep_trate01_fixed.clicked.connect(self.cycle_flowcytosep_trate01_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1->2 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_trate12 = QLineEdit()
        self.cycle_flowcytosep_trate12.textChanged.connect(self.cycle_flowcytosep_trate12_changed)
        self.cycle_flowcytosep_trate12.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_flowcytosep_trate12, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_trate12_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcytosep_trate12_fixed, 1,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_flowcytosep_trate12_fixed.clicked.connect(self.cycle_flowcytosep_trate12_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 2->3 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 2,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_trate23 = QLineEdit()
        self.cycle_flowcytosep_trate23.textChanged.connect(self.cycle_flowcytosep_trate23_changed)
        self.cycle_flowcytosep_trate23.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_flowcytosep_trate23, 2,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_trate23_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcytosep_trate23_fixed, 2,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_flowcytosep_trate23_fixed.clicked.connect(self.cycle_flowcytosep_trate23_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 2,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 3->0 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 3,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_trate30 = QLineEdit()
        self.cycle_flowcytosep_trate30.textChanged.connect(self.cycle_flowcytosep_trate30_changed)
        self.cycle_flowcytosep_trate30.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_flowcytosep_trate30, 3,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_trate30_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcytosep_trate30_fixed, 3,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_flowcytosep_trate30_fixed.clicked.connect(self.cycle_flowcytosep_trate30_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 3,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)

        #-----
        self.stack_trate_flowcytosep.setLayout(glayout)
        idx_stacked_widget += 1
        logging.debug(f' new stacked widget: flow cyto sep -------------> {idx_stacked_widget}')
        self.stack_trate_flowcytosep_idx = idx_stacked_widget 
        self.stacked_cycle.addWidget(self.stack_trate_flowcytosep)


        #------ Cycle transition rates (cycling quiescent) ----------------------
        # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0->1 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_quiescent_trate01 = QLineEdit()
        self.cycle_quiescent_trate01.textChanged.connect(self.cycle_quiescent_trate01_changed)
        self.cycle_quiescent_trate01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_quiescent_trate01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_quiescent_trate01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_quiescent_trate01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_quiescent_trate01_fixed.clicked.connect(self.cycle_quiescent_trate01_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1->0 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_quiescent_trate10 = QLineEdit()
        self.cycle_quiescent_trate10.textChanged.connect(self.cycle_quiescent_trate10_changed)
        self.cycle_quiescent_trate10.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_quiescent_trate10, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_quiescent_trate10_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_quiescent_trate10_fixed, 1,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_quiescent_trate10_fixed.clicked.connect(self.cycle_quiescent_trate10_fixed_clicked)

        units = QLabel(self.default_rate_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)
        
        #---
        self.stack_trate_quiescent.setLayout(glayout)

        idx_stacked_widget += 1
        self.stack_trate_quiescent_idx = idx_stacked_widget 
        logging.debug(f' new stacked widget: trate_quiescent -------------> {idx_stacked_widget}')
        self.stacked_cycle.addWidget(self.stack_trate_quiescent) # <------------- stack widget 1


        #===========================================================================
        #------ Cycle duration rates ----------------------
        # self.cycle_dropdown.addItem("live cells")   # 0 -> 0
        glayout = QGridLayout()

        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_live_duration00 = QLineEdit()
        self.cycle_live_duration00.textChanged.connect(self.cycle_live_duration00_changed)
        self.cycle_live_duration00.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_live_duration00, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_live_duration00_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_live_duration00_fixed, 0,3,1,1) # w, row, column, rowspan, colspan
        # NOTE: callbacks to all Fixed checkboxes are below, after the widgets are created.

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)
        
        #---
        self.stack_duration_live.setLayout(glayout)   

        idx_stacked_widget += 1
        self.stack_duration_live_idx = idx_stacked_widget 
        logging.debug(f' new stacked widget: duration live -------------> {idx_stacked_widget}')
        self.stacked_cycle.addWidget(self.stack_duration_live)


        #------ Cycle duration (Ki67) ----------------------
        # self.cycle_dropdown.addItem("basic Ki67")   # 0 -> 1, 1 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_Ki67_duration01 = QLineEdit()
        self.cycle_Ki67_duration01.textChanged.connect(self.cycle_Ki67_duration01_changed)
        self.cycle_Ki67_duration01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_Ki67_duration01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_Ki67_duration01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_Ki67_duration01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_Ki67_duration10 = QLineEdit()
        self.cycle_Ki67_duration10.textChanged.connect(self.cycle_Ki67_duration10_changed)
        self.cycle_Ki67_duration10.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_Ki67_duration10, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_Ki67_duration10_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_Ki67_duration10_fixed, 1,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)
        
        #---
        self.stack_duration_Ki67.setLayout(glayout)

        idx_stacked_widget += 1
        self.stack_duration_Ki67_idx = idx_stacked_widget 
        logging.debug(f' new stacked widget: duration Ki67 -------------> {idx_stacked_widget}')
        self.stacked_cycle.addWidget(self.stack_duration_Ki67) # <------------- stack widget 1


        #------ Cycle duration (advanced Ki67) ----------------------
        # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_advancedKi67_duration01 = QLineEdit()
        self.cycle_advancedKi67_duration01.textChanged.connect(self.cycle_advancedKi67_duration01_changed)
        self.cycle_advancedKi67_duration01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_advancedKi67_duration01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_advancedKi67_duration01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_advancedKi67_duration01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_advancedKi67_duration12 = QLineEdit()
        self.cycle_advancedKi67_duration12.textChanged.connect(self.cycle_advancedKi67_duration12_changed)
        self.cycle_advancedKi67_duration12.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_advancedKi67_duration12, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_advancedKi67_duration12_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_advancedKi67_duration12_fixed, 1,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 2 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 2,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_advancedKi67_duration20 = QLineEdit()
        self.cycle_advancedKi67_duration20.textChanged.connect(self.cycle_advancedKi67_duration20_changed)
        self.cycle_advancedKi67_duration20.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_advancedKi67_duration20, 2,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_advancedKi67_duration20_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_advancedKi67_duration20_fixed, 2,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 2,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)
        
        #-----
        self.stack_duration_advancedKi67.setLayout(glayout)
        idx_stacked_widget += 1
        logging.debug(f' new stacked widget: t02 -------------> {idx_stacked_widget}')
        self.stack_duration_advancedKi67_idx = idx_stacked_widget 
        self.stacked_cycle.addWidget(self.stack_duration_advancedKi67)


        #------ Cycle duration (flow cytometry) ----------------------
        # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcyto_duration01 = QLineEdit()
        self.cycle_flowcyto_duration01.textChanged.connect(self.cycle_flowcyto_duration01_changed)
        self.cycle_flowcyto_duration01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_flowcyto_duration01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcyto_duration01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcyto_duration01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcyto_duration12 = QLineEdit()
        self.cycle_flowcyto_duration12.textChanged.connect(self.cycle_flowcyto_duration12_changed)
        self.cycle_flowcyto_duration12.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_flowcyto_duration12, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcyto_duration12_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcyto_duration12_fixed, 1,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 2 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 2,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcyto_duration20 = QLineEdit()
        self.cycle_flowcyto_duration20.textChanged.connect(self.cycle_flowcyto_duration20_changed)
        self.cycle_flowcyto_duration20.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_flowcyto_duration20, 2,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcyto_duration20_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcyto_duration20_fixed, 2,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 2,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)

        #-----
        self.stack_duration_flowcyto.setLayout(glayout)
        idx_stacked_widget += 1
        logging.debug(f' new stacked widget: duration_flowcyto -------------> {idx_stacked_widget}')
        self.stack_duration_flowcyto_idx = idx_stacked_widget 
        self.stacked_cycle.addWidget(self.stack_duration_flowcyto)


        #------ Cycle duration (flow cytometry separated) ----------------------
        # self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0

        glayout = QGridLayout()

        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_duration01 = QLineEdit()
        self.cycle_flowcytosep_duration01.textChanged.connect(self.cycle_flowcytosep_duration01_changed)
        self.cycle_flowcytosep_duration01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_flowcytosep_duration01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_duration01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcytosep_duration01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_duration12 = QLineEdit()
        self.cycle_flowcytosep_duration12.textChanged.connect(self.cycle_flowcytosep_duration12_changed)
        self.cycle_flowcytosep_duration12.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_flowcytosep_duration12, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_duration12_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcytosep_duration12_fixed, 1,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 2 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 2,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_duration23 = QLineEdit()
        self.cycle_flowcytosep_duration23.textChanged.connect(self.cycle_flowcytosep_duration23_changed)
        self.cycle_flowcytosep_duration23.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_flowcytosep_duration23, 2,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_duration23_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcytosep_duration23_fixed, 2,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 2,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 3 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 3,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_duration30 = QLineEdit()
        self.cycle_flowcytosep_duration30.textChanged.connect(self.cycle_flowcytosep_duration30_changed)
        self.cycle_flowcytosep_duration30.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_flowcytosep_duration30, 3,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_duration30_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcytosep_duration30_fixed, 3,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 3,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)
        
        #-----
        self.stack_duration_flowcytosep.setLayout(glayout)
        idx_stacked_widget += 1
        logging.debug(f' new stacked widget: flow cyto sep -------------> {idx_stacked_widget}')
        self.stack_duration_flowcytosep_idx = idx_stacked_widget 
        self.stacked_cycle.addWidget(self.stack_duration_flowcytosep)


        #------ Cycle duration (cycling quiescent) ----------------------
        # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_quiescent_duration01 = QLineEdit()
        self.cycle_quiescent_duration01.textChanged.connect(self.cycle_quiescent_duration01_changed)
        self.cycle_quiescent_duration01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_quiescent_duration01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_quiescent_duration01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_quiescent_duration01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_quiescent_duration10 = QLineEdit()
        self.cycle_quiescent_duration10.textChanged.connect(self.cycle_quiescent_duration10_changed)
        self.cycle_quiescent_duration10.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_quiescent_duration10, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_quiescent_duration10_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_quiescent_duration10_fixed, 1,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #----- duration Fixed callbacks:
        self.cycle_live_duration00_fixed.clicked.connect(self.cycle_live_duration00_fixed_clicked)
        self.cycle_Ki67_duration01_fixed.clicked.connect(self.cycle_Ki67_duration01_fixed_clicked)
        self.cycle_Ki67_duration10_fixed.clicked.connect(self.cycle_Ki67_duration10_fixed_clicked)
        self.cycle_advancedKi67_duration01_fixed.clicked.connect(self.cycle_advancedKi67_duration01_fixed_clicked)
        self.cycle_advancedKi67_duration12_fixed.clicked.connect(self.cycle_advancedKi67_duration12_fixed_clicked)
        self.cycle_advancedKi67_duration20_fixed.clicked.connect(self.cycle_advancedKi67_duration20_fixed_clicked)
        self.cycle_flowcyto_duration01_fixed.clicked.connect(self.cycle_flowcyto_duration01_fixed_clicked)
        self.cycle_flowcyto_duration12_fixed.clicked.connect(self.cycle_flowcyto_duration12_fixed_clicked)
        self.cycle_flowcyto_duration20_fixed.clicked.connect(self.cycle_flowcyto_duration20_fixed_clicked)
        self.cycle_flowcytosep_duration01_fixed.clicked.connect(self.cycle_flowcytosep_duration01_fixed_clicked)
        self.cycle_flowcytosep_duration12_fixed.clicked.connect(self.cycle_flowcytosep_duration12_fixed_clicked)
        self.cycle_flowcytosep_duration23_fixed.clicked.connect(self.cycle_flowcytosep_duration23_fixed_clicked)
        self.cycle_flowcytosep_duration30_fixed.clicked.connect(self.cycle_flowcytosep_duration30_fixed_clicked)
        self.cycle_quiescent_duration01_fixed.clicked.connect(self.cycle_quiescent_duration01_fixed_clicked)
        self.cycle_quiescent_duration10_fixed.clicked.connect(self.cycle_quiescent_duration10_fixed_clicked)

        #------
        self.insert_hacky_blank_lines(glayout)

        self.stack_duration_quiescent.setLayout(glayout)

        idx_stacked_widget += 1
        self.stack_duration_quiescent_idx = idx_stacked_widget 
        logging.debug(f' new stacked widget: duration_quiescent -------------> {idx_stacked_widget}')
        self.stacked_cycle.addWidget(self.stack_duration_quiescent) # <------------- stack widget 1



        #---------------------------------------------
        # After adding all combos of cycle widgets (groups) to the stacked widget, 
        # add it to this panel.
        self.vbox_cycle.addWidget(self.stacked_cycle)

        self.vbox_cycle.addStretch()

        self.params_cycle.setLayout(self.vbox_cycle)

        return self.params_cycle

    #--------------------------------------------------------
    def create_death_tab(self):
        death_tab = QWidget()
        # self.scroll_params = QScrollArea()
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

        self.apoptosis_death_rate = QLineEdit()
        self.apoptosis_death_rate.textChanged.connect(self.apoptosis_death_rate_changed)
        self.apoptosis_death_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_death_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #-------
        self.apoptosis_group = QButtonGroup(self)

        self.apoptosis_rb1 = QRadioButton("transition rate", self)  # OMG, leave "self" for QButtonGroup
        self.apoptosis_rb1.toggled.connect(self.apoptosis_phase_transition_cb)
        idr += 1
        glayout.addWidget(self.apoptosis_rb1, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_rb2 = QRadioButton("duration", self)
        self.apoptosis_rb2.toggled.connect(self.apoptosis_phase_transition_cb)
        glayout.addWidget(self.apoptosis_rb2, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_group.addButton(self.apoptosis_rb1)
        self.apoptosis_group.addButton(self.apoptosis_rb2)

        #-----
        # 	<model code="100" name="apoptosis"> 
        # 	<death_rate units="1/min">2.1e-4</death_rate>  
        # 	<phase_transition_rates units="1/min">
        # 		<rate start_index="0" end_index="1" fixed_duration="true">0.00193798</rate>
        # 	</phase_transition_rates>

        label = QLabel("phase 0->1 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_trate01 = QLineEdit()
        self.apoptosis_trate01.textChanged.connect(self.apoptosis_trate01_changed)
        self.apoptosis_trate01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_trate01, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_trate01_fixed = QCheckBox("Fixed")
        self.apoptosis_trate01_fixed.toggled.connect(self.apoptosis_trate01_fixed_toggled)
        glayout.addWidget(self.apoptosis_trate01_fixed, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #-----
        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_phase0_duration = QLineEdit()
        self.apoptosis_phase0_duration.textChanged.connect(self.apoptosis_phase0_duration_changed)
        self.apoptosis_phase0_duration.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_phase0_duration, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_phase0_duration_fixed = QCheckBox("Fixed")
        self.apoptosis_phase0_duration_fixed.toggled.connect(self.apoptosis_phase0_duration_fixed_toggled)
        glayout.addWidget(self.apoptosis_phase0_duration_fixed, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan
        # <phase_durations units="min">
        #     <duration index="0" fixed_duration="true">516</duration>

        #-------------------
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,4) # w, row, column, rowspan, colspan

        # <unlysed_fluid_change_rate units="1/min">0.05</unlysed_fluid_change_rate>
        # <lysed_fluid_change_rate units="1/min">0</lysed_fluid_change_rate>
        # <cytoplasmic_biomass_change_rate units="1/min">1.66667e-02</cytoplasmic_biomass_change_rate>
        # <nuclear_biomass_change_rate units="1/min">5.83333e-03</nuclear_biomass_change_rate>
        # <calcification_rate units="1/min">0</calcification_rate>
        # <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>
        label = QLabel("unlysed fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_unlysed_rate = QLineEdit()
        self.apoptosis_unlysed_rate.textChanged.connect(self.apoptosis_unlysed_rate_changed)
        self.apoptosis_unlysed_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_unlysed_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("lysed fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_lysed_rate = QLineEdit()
        self.apoptosis_lysed_rate.textChanged.connect(self.apoptosis_lysed_rate_changed)
        self.apoptosis_lysed_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_lysed_rate, idr,1, 1,1) # w, row, column, rowspan, colspan
        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("cytoplasmic biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_cytoplasmic_biomass_change_rate = QLineEdit()
        self.apoptosis_cytoplasmic_biomass_change_rate.textChanged.connect(self.apoptosis_cytoplasmic_biomass_change_rate_changed)
        self.apoptosis_cytoplasmic_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_cytoplasmic_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.apoptosis_cytoplasmic_hbox.addWidget(units)
        # self.vbox.addLayout(self.apoptosis_cytoplasmic_biomass_change_rate_hbox)

        # <nuclear_biomass_change_rate units="1/min">5.83333e-03</nuclear_biomass_change_rate>
        # <calcification_rate units="1/min">0</calcification_rate>
        # <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>

        label = QLabel("nuclear biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_nuclear_biomass_change_rate = QLineEdit()
        self.apoptosis_nuclear_biomass_change_rate.textChanged.connect(self.apoptosis_nuclear_biomass_change_rate_changed)
        self.apoptosis_nuclear_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_nuclear_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("calcification rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_calcification_rate = QLineEdit()
        self.apoptosis_calcification_rate.textChanged.connect(self.apoptosis_calcification_rate_changed)
        self.apoptosis_calcification_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_calcification_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("relative rupture volume")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_relative_rupture_volume = QLineEdit()
        self.apoptosis_relative_rupture_volume.textChanged.connect(self.apoptosis_relative_rupture_volume_changed)
        self.apoptosis_relative_rupture_volume.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_relative_rupture_volume, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #------------------------------------------------------
        label = QLabel("Necrosis")
        label.setFixedSize(100,20)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet('background-color: orange')
        idr += 1
        glayout.addWidget(label, idr,0, 1,4) # w, row, column, rowspan, colspan

        # <model code="101" name="necrosis">
        # 	<death_rate units="1/min">0.0</death_rate>
        # 	<phase_transition_rates units="1/min">
        # 		<rate start_index="0" end_index="1" fixed_duration="false">9e9</rate>
        # 		<rate start_index="1" end_index="2" fixed_duration="true">1.15741e-5</rate>
        # 	</phase_transition_rates>
        label = QLabel("death rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_death_rate = QLineEdit()
        self.necrosis_death_rate.textChanged.connect(self.necrosis_death_rate_changed)
        self.necrosis_death_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_death_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #-------
        self.necrosis_group = QButtonGroup(self)

        self.necrosis_rb1 = QRadioButton("transition rate", self)  # OMG, leave "self"
        self.necrosis_rb1.toggled.connect(self.necrosis_phase_transition_cb)
        idr += 1
        glayout.addWidget(self.necrosis_rb1, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_rb2 = QRadioButton("duration", self)
        self.necrosis_rb2.toggled.connect(self.necrosis_phase_transition_cb)
        glayout.addWidget(self.necrosis_rb2, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_group.addButton(self.necrosis_rb1)
        self.necrosis_group.addButton(self.necrosis_rb2)

        #-----
        # 	<model code="100" name="apoptosis"> 
        # 	<death_rate units="1/min">2.1e-4</death_rate>  
        # 	<phase_transition_rates units="1/min">
        # 		<rate start_index="0" end_index="1" fixed_duration="true">0.00193798</rate>
        # 	</phase_transition_rates>

        # <model code="101" name="necrosis">
        # 	<death_rate units="1/min">0.0</death_rate>
        # 	<phase_transition_rates units="1/min">
        # 		<rate start_index="0" end_index="1" fixed_duration="false">9e9</rate>
        # 		<rate start_index="1" end_index="2" fixed_duration="true">1.15741e-5</rate>
        # 	</phase_transition_rates>

        label = QLabel("phase 0->1 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_trate01 = QLineEdit()
        self.necrosis_trate01.textChanged.connect(self.necrosis_trate01_changed)
        self.necrosis_trate01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_trate01, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_trate01_fixed = QCheckBox("Fixed")
        self.necrosis_trate01_fixed.toggled.connect(self.necrosis_trate01_fixed_toggled)
        glayout.addWidget(self.necrosis_trate01_fixed, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #-----
        label = QLabel("phase 1->2 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_trate12 = QLineEdit()
        self.necrosis_trate12.textChanged.connect(self.necrosis_trate12_changed)
        self.necrosis_trate12.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_trate12, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_trate12_fixed = QCheckBox("Fixed")
        self.necrosis_trate12_fixed.toggled.connect(self.necrosis_trate12_fixed_toggled)
        glayout.addWidget(self.necrosis_trate12_fixed, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #-----------------
        # self.necrosis_phase0_duration_hbox = QHBoxLayout()
        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
    #    self.necrosis_phase0_duration_hbox.addWidget(label)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_phase0_duration = QLineEdit()
        self.necrosis_phase0_duration.textChanged.connect(self.necrosis_phase0_duration_changed)
        self.necrosis_phase0_duration.setValidator(QtGui.QDoubleValidator())
        # self.necrosis_phase0_duration.textChanged.connect(self.necrosis_phase0_changed)
        # self.necrosis_phase0_duration_hbox.addWidget(self.necrosis_phase0_duration)
        glayout.addWidget(self.necrosis_phase0_duration, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_phase0_duration_fixed = QCheckBox("Fixed")
        self.necrosis_phase0_duration_fixed.toggled.connect(self.necrosis_phase0_duration_fixed_toggled)
        glayout.addWidget(self.necrosis_phase0_duration_fixed, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #----
        label = QLabel("phase 1 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_phase1_duration = QLineEdit()
        self.necrosis_phase1_duration.textChanged.connect(self.necrosis_phase1_duration_changed)
        self.necrosis_phase1_duration.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_phase1_duration, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_phase1_duration_fixed = QCheckBox("Fixed")
        self.necrosis_phase1_duration_fixed.toggled.connect(self.necrosis_phase1_duration_fixed_toggled)
        glayout.addWidget(self.necrosis_phase1_duration_fixed, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #-------------------
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,4) # w, row, column, rowspan, colspan

        # <unlysed_fluid_change_rate units="1/min">0.05</unlysed_fluid_change_rate>
        # <lysed_fluid_change_rate units="1/min">0</lysed_fluid_change_rate>
        # <cytoplasmic_biomass_change_rate units="1/min">1.66667e-02</cytoplasmic_biomass_change_rate>
        # <nuclear_biomass_change_rate units="1/min">5.83333e-03</nuclear_biomass_change_rate>
        # <calcification_rate units="1/min">0</calcification_rate>
        # <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>

        label = QLabel("unlysed fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_unlysed_rate = QLineEdit()
        self.necrosis_unlysed_rate.textChanged.connect(self.necrosis_unlysed_rate_changed)
        self.necrosis_unlysed_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_unlysed_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("lysed fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_lysed_rate = QLineEdit()
        self.necrosis_lysed_rate.textChanged.connect(self.necrosis_lysed_rate_changed)
        self.necrosis_lysed_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_lysed_rate, idr,1, 1,1) # w, row, column, rowspan, colspan
        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        
        label = QLabel("cytoplasmic biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_cytoplasmic_biomass_change_rate = QLineEdit()
        self.necrosis_cytoplasmic_biomass_change_rate.textChanged.connect(self.necrosis_cytoplasmic_biomass_change_rate_changed)
        self.necrosis_cytoplasmic_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_cytoplasmic_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        # <nuclear_biomass_change_rate units="1/min">5.83333e-03</nuclear_biomass_change_rate>
        # <calcification_rate units="1/min">0</calcification_rate>
        # <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>

        label = QLabel("nuclear biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_nuclear_biomass_change_rate = QLineEdit()
        self.necrosis_nuclear_biomass_change_rate.textChanged.connect(self.necrosis_nuclear_biomass_change_rate_changed)
        self.necrosis_nuclear_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_nuclear_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("calcification rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_calcification_rate = QLineEdit()
        self.necrosis_calcification_rate.textChanged.connect(self.necrosis_calcification_rate_changed)
        self.necrosis_calcification_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_calcification_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("relative rupture volume")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_relative_rupture_volume = QLineEdit()
        self.necrosis_relative_rupture_volume.textChanged.connect(self.necrosis_relative_rupture_volume_changed)
        self.necrosis_relative_rupture_volume.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_relative_rupture_volume, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #------
#rwh
        # for idx in range(11):  # rwh: hack solution to align rows
        # for idx in range(0):  # rwh: hack solution to align rows
        #     blank_line = QLabel("")
        #     idr += 1
        #     glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan
        #------

        death_tab_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        death_tab_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        death_tab_scroll.setWidgetResizable(True)
        death_tab_scroll.setWidget(death_tab) 

        death_tab.setLayout(glayout)
        # death_tab.addWidget(death_tab_scroll)
        # scroll_params.setLayout(glayout)
        # death_tab.setLayout(scroll_params)
        # return death_tab
        return death_tab_scroll

    #--------------------------------------------------------
    def apoptosis_phase_transition_cb(self):
        logging.debug(f'\n  ---- apoptosis_phase_transition_cb: ')

        radioBtn = self.sender()
        if radioBtn.isChecked():
            logging.debug(f'apoptosis: ------>> {radioBtn.text()}')

        if "duration" in radioBtn.text():
            logging.debug(f'apoptosis_phase_transition_cb: --> duration')
            self.apoptosis_duration_flag = True
            self.apoptosis_trate01.setReadOnly(True)
            self.apoptosis_trate01.setStyleSheet("background-color: lightgray")  
            self.apoptosis_trate01_fixed.setEnabled(False)

            self.apoptosis_phase0_duration.setReadOnly(False)
            self.apoptosis_phase0_duration.setStyleSheet("background-color: white")
            self.apoptosis_phase0_duration_fixed.setEnabled(True)
        else:  # transition rates
            logging.debug(f'apoptosis_phase_transition_cb: NOT duration')
            self.apoptosis_duration_flag = False
            self.apoptosis_phase0_duration.setReadOnly(True)
            self.apoptosis_phase0_duration.setStyleSheet("background-color: lightgray")  
            self.apoptosis_phase0_duration_fixed.setEnabled(False)

            self.apoptosis_trate01.setReadOnly(False)
            self.apoptosis_trate01.setStyleSheet("background-color: white")  
            self.apoptosis_trate01_fixed.setEnabled(True)

        self.param_d[self.current_cell_def]['apoptosis_duration_flag'] = self.apoptosis_duration_flag

    #------------
    def necrosis_phase_transition_cb(self):
        # rb1.toggled.connect(self.updateLabel)(self, idx_choice):
        # print('self.cycle_rows_vbox.count()=', self.cycle_rows_vbox.count())
        logging.debug(f'\n  ---- necrosis_phase_transition_cb: ')

        radioBtn = self.sender()
        if radioBtn.isChecked():
            logging.debug(f'necrosis: ------>>{radioBtn.text()}')

        # print("self.cycle_dropdown.currentText() = ",self.cycle_dropdown.currentText())
        # print("self.cycle_dropdown.currentIndex() = ",self.cycle_dropdown.currentIndex())

        # self.cycle_rows_vbox.clear()
        # if radioBtn.text().find("duration"):
        if "duration" in radioBtn.text():
            logging.debug(f'necrosis_phase_transition_cb: --> duration')
            self.necrosis_duration_flag = True
            # self.customize_cycle_choices()
            self.necrosis_trate01.setReadOnly(True)
            self.necrosis_trate01.setStyleSheet("background-color: lightgray")
            self.necrosis_trate01_fixed.setEnabled(False)
            self.necrosis_trate12.setReadOnly(True)
            self.necrosis_trate12.setStyleSheet("background-color: lightgray")
            self.necrosis_trate12_fixed.setEnabled(False)

            self.necrosis_phase0_duration.setReadOnly(False)
            self.necrosis_phase0_duration.setStyleSheet("background-color: white")
            self.necrosis_phase0_duration_fixed.setEnabled(True)
            self.necrosis_phase1_duration.setReadOnly(False)
            self.necrosis_phase1_duration.setStyleSheet("background-color: white")
            self.necrosis_phase1_duration_fixed.setEnabled(True)
        else:  # transition rates
            logging.debug(f'necrosis_phase_transition_cb: NOT duration')
            self.necrosis_duration_flag = False
            self.necrosis_phase0_duration.setReadOnly(True)
            self.necrosis_phase0_duration.setStyleSheet("background-color: lightgray")
            self.necrosis_phase0_duration_fixed.setEnabled(False)
            self.necrosis_phase1_duration.setReadOnly(True)
            self.necrosis_phase1_duration.setStyleSheet("background-color: lightgray")
            self.necrosis_phase1_duration_fixed.setEnabled(False)

            self.necrosis_trate01.setReadOnly(False)
            self.necrosis_trate01.setStyleSheet("background-color: white")  
            self.necrosis_trate01_fixed.setEnabled(True)
            self.necrosis_trate12.setReadOnly(False)
            self.necrosis_trate12.setStyleSheet("background-color: white")  
            self.necrosis_trate12_fixed.setEnabled(True)
            # self.customize_cycle_choices()
            # pass

        self.param_d[self.current_cell_def]['necrosis_duration_flag'] = self.necrosis_duration_flag

    #-------

    # def apop_death_rate_changed(self, text):
    #     print("----- apop_death_rate_changed: self.current_cell_def = ",self.current_cell_def)
    #     self.param_d[self.current_cell_def]["apop_death_rate"] = text
    # def apop_phase0_changed(self, text):
    #     self.param_d[self.current_cell_def]["apop_phase0"] = text

    # def apop_unlysed_changed(self, text):
    #     self.param_d[self.current_cell_def]["apop_unlysed"] = text
    # def apop_lysed_changed(self, text):
    #     self.param_d[self.current_cell_def]["apop_lysed"] = text
    # def apop_cyto_changed(self, text):
    #     self.param_d[self.current_cell_def]["apop_cyto"] = text
    # def apop_nuclear_changed(self, text):
    #     self.param_d[self.current_cell_def]["apop_nuclear"] = text
    # def apop_calcif_changed(self, text):
    #     self.param_d[self.current_cell_def]["apop_calcif"] = text
    # def apop_rupture_changed(self, text):
    #     self.param_d[self.current_cell_def]["apop_rupture"] = text

    #--------------------------------------------------------
    def create_volume_tab(self):
        volume_tab = QWidget()
        glayout = QGridLayout()
        # vlayout = QVBoxLayout()

        label = QLabel("Phenotype: volume")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)
        # self.vbox.addWidget(label)

        # <total units="micron^3">2494</total>
        # <fluid_fraction units="dimensionless">0.75</fluid_fraction>
        # <nuclear units="micron^3">540</nuclear>

        label = QLabel("total")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr = 0
        # self.volume_total_hbox.addWidget(label)
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_total = QLineEdit()
        self.volume_total.textChanged.connect(self.volume_total_changed)
        self.volume_total.setValidator(QtGui.QDoubleValidator())
        # self.volume_total_hbox.addWidget(self.volume_total)
        glayout.addWidget(self.volume_total, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("micron^3")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # self.volume_total_hbox.addWidget(units)
        # vlayout.addLayout(self.volume_total_hbox)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("fluid fraction")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_fluid_fraction = QLineEdit()
        self.volume_fluid_fraction.textChanged.connect(self.volume_fluid_fraction_changed)
        self.volume_fluid_fraction.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_fluid_fraction, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("nuclear")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_nuclear = QLineEdit()
        self.volume_nuclear.textChanged.connect(self.volume_nuclear_changed)
        self.volume_nuclear.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_nuclear, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("micron^3")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        
        # <fluid_change_rate units="1/min">0.05</fluid_change_rate>
        # <cytoplasmic_biomass_change_rate units="1/min">0.0045</cytoplasmic_biomass_change_rate>
        # <nuclear_biomass_change_rate units="1/min">0.0055</nuclear_biomass_change_rate>

        #---
        label = QLabel("fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_fluid_change_rate = QLineEdit()
        self.volume_fluid_change_rate.textChanged.connect(self.volume_fluid_change_rate_changed)
        self.volume_fluid_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_fluid_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("cytoplasmic biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_cytoplasmic_biomass_change_rate = QLineEdit()
        self.volume_cytoplasmic_biomass_change_rate.textChanged.connect(self.volume_cytoplasmic_biomass_change_rate_changed)
        self.volume_cytoplasmic_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_cytoplasmic_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("nuclear biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_nuclear_biomass_change_rate = QLineEdit()
        self.volume_nuclear_biomass_change_rate.textChanged.connect(self.volume_nuclear_biomass_change_rate_changed)
        self.volume_nuclear_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_nuclear_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        
        #---
        # <calcified_fraction units="dimensionless">0</calcified_fraction>
        # <calcification_rate units="1/min">0</calcification_rate>
        label = QLabel("calcification fraction")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_calcified_fraction = QLineEdit()
        self.volume_calcified_fraction.textChanged.connect(self.volume_calcified_fraction_changed)
        self.volume_calcified_fraction.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_calcified_fraction, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("calcified rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.volume_calcification_rate = QLineEdit()
        self.volume_calcification_rate.textChanged.connect(self.volume_calcification_rate_changed)
        self.volume_calcification_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.volume_calcification_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        
        #---
        # <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>
        label = QLabel("relative rupture volume")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.relative_rupture_volume = QLineEdit()
        self.relative_rupture_volume.textChanged.connect(self.relative_rupture_volume_changed)
        self.relative_rupture_volume.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.relative_rupture_volume, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #------
        for idx in range(5):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idr += 1
            glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan

        #------
        # vlayout.setVerticalSpacing(10)  # rwh - argh
        volume_tab.setLayout(glayout)
        return volume_tab

    #--------------------------------------------------------
    def create_mechanics_tab(self):
        mechanics_tab = QWidget()
        glayout = QGridLayout()

        label = QLabel("Phenotype: mechanics")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)
        # self.vbox.addWidget(label)

    # <cell_cell_adhesion_strength units="micron/min">0.4</cell_cell_adhesion_strength>
    # <cell_cell_repulsion_strength units="micron/min">10.0</cell_cell_repulsion_strength>
    # <relative_maximum_adhesion_distance units="dimensionless">1.25</relative_maximum_adhesion_distance>
        label = QLabel("cell-cell adhesion strength")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr = 0
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.cell_cell_adhesion_strength = QLineEdit()
        self.cell_cell_adhesion_strength.textChanged.connect(self.cell_cell_adhesion_strength_changed)
        self.cell_cell_adhesion_strength.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cell_cell_adhesion_strength, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("micron/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("cell-cell repulsion strength")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.cell_cell_repulsion_strength = QLineEdit()
        self.cell_cell_repulsion_strength.textChanged.connect(self.cell_cell_repulsion_strength_changed)
        self.cell_cell_repulsion_strength.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cell_cell_repulsion_strength, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("micron/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #-----
        self.new_stuff = False
        label = QLabel("cell-BM adhesion strength")
        label.setEnabled(self.new_stuff)
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.cell_bm_adhesion_strength = QLineEdit()
        self.cell_bm_adhesion_strength.textChanged.connect(self.cell_bm_adhesion_strength_changed)
        self.cell_bm_adhesion_strength.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cell_bm_adhesion_strength, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.cell_bm_adhesion_strength.setEnabled(self.new_stuff)

        units = QLabel("micron/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("cell-BM repulsion strength")
        label.setEnabled(self.new_stuff)
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.cell_bm_repulsion_strength = QLineEdit()
        self.cell_bm_repulsion_strength.textChanged.connect(self.cell_bm_repulsion_strength_changed)
        self.cell_bm_repulsion_strength.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cell_bm_repulsion_strength, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.cell_bm_repulsion_strength.setEnabled(self.new_stuff)

        units = QLabel("micron/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("relative max adhesion distance")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.relative_maximum_adhesion_distance = QLineEdit()
        self.relative_maximum_adhesion_distance.textChanged.connect(self.relative_maximum_adhesion_distance_changed)
        self.relative_maximum_adhesion_distance.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.relative_maximum_adhesion_distance, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("cell adhesion affinity")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.cell_adhesion_affinity_dropdown = QComboBox()
        glayout.addWidget(self.cell_adhesion_affinity_dropdown, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.cell_adhesion_affinity_dropdown.currentIndexChanged.connect(self.cell_adhesion_affinity_dropdown_changed_cb)  # beware: will be triggered on a ".clear" too

        self.cell_adhesion_affinity = QLineEdit()
        self.cell_adhesion_affinity.textChanged.connect(self.cell_adhesion_affinity_changed)
        self.cell_adhesion_affinity.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cell_adhesion_affinity , idr,2, 1,1) # w, row, column, rowspan, colspan
    
        #---
    # <options>
    #     <set_relative_equilibrium_distance enabled="false" units="dimensionless">1.8</set_relative_equilibrium_distance>
    #     <set_absolute_equilibrium_distance enabled="false" units="micron">15.12</set_absolute_equilibrium_distance>
    # </options>
        label = QLabel("Options:")
        label.setFixedSize(80,20)
        label.setStyleSheet("background-color: orange")
        # label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignLeft)
        idr += 1
        glayout.addWidget(label, idr,0, 1,3) # w, row, column, rowspan, colspan

        #--------
        label = QLabel("relative equilibrium distance")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.set_relative_equilibrium_distance = QLineEdit()
        self.set_relative_equilibrium_distance.textChanged.connect(self.set_relative_equilibrium_distance_changed)
        self.set_relative_equilibrium_distance.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.set_relative_equilibrium_distance, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.set_relative_equilibrium_distance_enabled = QCheckBox("enable")
        self.set_relative_equilibrium_distance_enabled.clicked.connect(self.set_relative_equilibrium_distance_enabled_cb)
        glayout.addWidget(self.set_relative_equilibrium_distance_enabled, idr,2, 1,1) # w, row, column, rowspan, colspan

        # units = QLabel("")
        # units.setFixedWidth(self.units_width)
        # units.setAlignment(QtCore.Qt.AlignLeft)
        # glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #--------
        label = QLabel("absolute equilibrium distance")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.set_absolute_equilibrium_distance = QLineEdit()
        self.set_absolute_equilibrium_distance.textChanged.connect(self.set_absolute_equilibrium_distance_changed)
        self.set_absolute_equilibrium_distance.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.set_absolute_equilibrium_distance, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.set_absolute_equilibrium_distance_enabled = QCheckBox("enable")
        self.set_absolute_equilibrium_distance_enabled.clicked.connect(self.set_absolute_equilibrium_distance_enabled_cb)
        glayout.addWidget(self.set_absolute_equilibrium_distance_enabled, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("micron")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #--------------------------------
        # ------ horiz separator -----
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,4) # w, row, column, rowspan, colspan

        label = QLabel("elastic constant")
        label.setEnabled(self.new_stuff)
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.elastic_constant = QLineEdit()
        self.elastic_constant.textChanged.connect(self.elastic_constant_changed)
        self.elastic_constant.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.elastic_constant, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.elastic_constant.setEnabled(self.new_stuff)

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan


        label = QLabel("attachment rate")
        label.setEnabled(self.new_stuff)
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.attachment_rate = QLineEdit()
        self.attachment_rate.textChanged.connect(self.attachment_rate_changed)
        self.attachment_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.attachment_rate, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.attachment_rate.setEnabled(self.new_stuff)

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #--
        label = QLabel("detachment rate")
        label.setEnabled(self.new_stuff)
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.detachment_rate = QLineEdit()
        self.detachment_rate.textChanged.connect(self.detachment_rate_changed)
        self.detachment_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.detachment_rate, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.detachment_rate.setEnabled(self.new_stuff)

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

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
    def create_motility_tab(self):
        motility_tab = QWidget()
        glayout = QGridLayout()

        label = QLabel("Phenotype: motility")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)
        # self.vbox.addWidget(label)
        # self.vbox.addWidget(QHLine())

        #---
        # <speed units="micron/min">1</speed>
        # <persistence_time units="min">1</persistence_time>
        # <migration_bias units="dimensionless">.75</migration_bias>
        label = QLabel("speed")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # label.setStyleSheet("border: 1px solid black;")
        idr = 0
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.speed = QLineEdit()
        self.speed.textChanged.connect(self.speed_changed)
        self.speed.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.speed, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("micron/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # units.setStyleSheet("border: 1px solid black;")
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("persistence time")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.persistence_time = QLineEdit()
        self.persistence_time.textChanged.connect(self.persistence_time_changed)
        self.persistence_time.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.persistence_time, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("migration bias")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.migration_bias = QLineEdit()
        self.migration_bias.textChanged.connect(self.migration_bias_changed)
        self.migration_bias.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.migration_bias, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        
        # <options>
        #     <enabled>false</enabled>
        #     <use_2D>true</use_2D>
        #     <chemotaxis>
        #         <enabled>false</enabled>
        #         <substrate>virus</substrate>
        #         <direction>1</direction>
        #     </chemotaxis>
        # </options>
        #---
        self.motility_enabled = QCheckBox("enable motility")
        self.motility_enabled.clicked.connect(self.motility_enabled_cb)
        # self.motility_enabled.setAlignment(QtCore.Qt.AlignRight)
        # label.setFixedWidth(self.label_width)
        idr += 1
        glayout.addWidget(self.motility_enabled, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.motility_use_2D = QCheckBox("2D")
        self.motility_use_2D.clicked.connect(self.motility_use_2D_cb)
        # self.motility_use_2D.setAlignment(QtCore.Qt.AlignRight)
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

        self.chemotaxis_enabled = QCheckBox("enabled")
        self.chemotaxis_enabled.clicked.connect(self.chemotaxis_enabled_cb)
        glayout.addWidget(self.chemotaxis_enabled, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.motility_substrate_dropdown = QComboBox()
        # self.motility_substrate_dropdown.setFixedWidth(240)
        idr += 1
        glayout.addWidget(self.motility_substrate_dropdown, idr,0, 1,1) # w, row, column, rowspan, colspan
        self.motility_substrate_dropdown.currentIndexChanged.connect(self.motility_substrate_changed_cb)  # beware: will be triggered on a ".clear" too
        # self.motility_substrate_dropdown.addItem("oxygen")

        # self.chemotaxis_direction_positive = QCheckBox("up gradient (+1)")
        # glayout.addWidget(self.chemotaxis_direction_positive, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.chemotaxis_direction_towards = QRadioButton("towards")
        self.chemotaxis_direction_towards.clicked.connect(self.chemotaxis_direction_cb)
        # glayout.addLayout(self.chemotaxis_direction_towards, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.chemotaxis_direction_against = QRadioButton("against")
        self.chemotaxis_direction_against.clicked.connect(self.chemotaxis_direction_cb)
        # glayout.addWidget(self.chemotaxis_direction_against, idr,2, 1,1) # w, row, column, rowspan, colspan

        hbox = QHBoxLayout()
        hbox.addWidget(self.chemotaxis_direction_towards)
        hbox.addWidget(self.chemotaxis_direction_against)
        glayout.addLayout(hbox, idr,1, 1,1) # w, row, column, rowspan, colspan

        #---
            # <advanced_chemotaxis>
            #     <enabled>false</enabled>
            #     <normalize_each_gradient>false</normalize_each_gradient>
            #     <chemotactic_sensitivities>
            #       <chemotactic_sensitivity substrate="resource">0</chemotactic_sensitivity> 
            #       <chemotactic_sensitivity substrate="toxin">0</chemotactic_sensitivity> 
            #       <chemotactic_sensitivity substrate="quorum">0</chemotactic_sensitivity> 
            #       <chemotactic_sensitivity substrate="pro-inflammatory">0</chemotactic_sensitivity> 
            #       <chemotactic_sensitivity substrate="debris">0</chemotactic_sensitivity> 
            #     </chemotactic_sensitivities>
            #   </advanced_chemotaxis>
        idr += 1
        glayout.addWidget(QHLine(), idr,0, 1,2) # w, row, column, rowspan, colspan

        label = QLabel("Advanced Chemotaxis")
        label.setFixedWidth(200)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet('background-color: orange')
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.advanced_chemotaxis_enabled = QCheckBox("enabled")
        self.advanced_chemotaxis_enabled.clicked.connect(self.advanced_chemotaxis_enabled_cb)
        glayout.addWidget(self.advanced_chemotaxis_enabled, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.normalize_each_gradient = QCheckBox("normalize gradient")
        self.normalize_each_gradient.clicked.connect(self.normalize_each_gradient_cb)
        glayout.addWidget(self.normalize_each_gradient, idr,2, 1,1) # w, row, column, rowspan, colspan

        self.motility2_substrate_dropdown = QComboBox()
        # self.motility_substrate_dropdown.setFixedWidth(240)
        idr += 1
        glayout.addWidget(self.motility2_substrate_dropdown, idr,0, 1,1) # w, row, column, rowspan, colspan
        self.motility2_substrate_dropdown.currentIndexChanged.connect(self.motility2_substrate_changed_cb)  # beware: will be triggered on a ".clear" too

        label = QLabel("sensitivity")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.chemo_sensitivity = QLineEdit()
        self.chemo_sensitivity.textChanged.connect(self.chemo_sensitivity_changed)
        self.chemo_sensitivity.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.chemo_sensitivity, idr,2, 1,1) # w, row, column, rowspan, colspan

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
    def create_secretion_tab(self):
        secretion_tab = QWidget()
        glayout = QGridLayout()

        label = QLabel("Phenotype: secretion")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)

        # <substrate name="virus">
        #     <secretion_rate units="1/min">0</secretion_rate>
        #     <secretion_target units="substrate density">1</secretion_target>
        #     <uptake_rate units="1/min">10</uptake_rate>
        #     <net_export_rate units="total substrate/min">0</net_export_rate> 
        # </substrate> 
        
        # <substrate name="interferon">
        #     <secretion_rate units="1/min">0</secretion_rate>
        #     <secretion_target units="substrate density">1</secretion_target>
        #     <uptake_rate units="1/min">0</uptake_rate>
        #     <net_export_rate units="total substrate/min">0</net_export_rate> 
        # </substrate> 

        # cycle_path = ".//cell_definition[" + str(idx_current_cell_def) + "]//phenotype//cycle"
        # phase_transition_path = cycle_path + "//phase_transition_rates"
        # print(' >> phase_transition_path ')
        # pt_uep = uep.find(phase_transition_path)

        # self.secretion_substrate_dropdown = QComboBox()
        # self.secretion_substrate_dropdown.setFixedWidth(300)
        # self.secretion_substrate_dropdown.currentIndexChanged.connect(self.secretion_substrate_changed_cb)  # beware: will be triggered on a ".clear" too


        # self.uep_cell_defs = self.xml_root.find(".//cell_definitions")
        # print('self.uep_cell_defs= ',self.uep_cell_defs)
        # # secretion_path = ".//cell_definition[" + str(idx_current_cell_def) + "]//phenotype//secretion//"
        # uep_secretion = self.xml_root.find(".//cell_definitions//cell_definition[" + str(idx) + "]//phenotype//secretion")
        # print('uep_secretion = ',uep_secretion )
        # # vp = []   # pointers to <variable> nodes
        # if self.uep_cell_defs:
        #     # uep = self.xml_root.find('.//secretion')  # find unique entry point
        #     idx = 0
        #     for sub in uep_secretion.findall('substrate'):
        #         # vp.append(var)
        #         print(idx,") -- secretion substrate = ",sub.attrib['name'])
        #         idx += 1

        # label = QLabel("oxygen")
        # label.setStyleSheet('background-color: lightgreen')
        # label.setFixedWidth(150)
        # self.vbox.addWidget(label)

        self.secretion_substrate_dropdown = QComboBox()
        idr = 0
        glayout.addWidget(self.secretion_substrate_dropdown, idr,0, 1,1) # w, row, column, rowspan, colspan
        self.secretion_substrate_dropdown.currentIndexChanged.connect(self.secretion_substrate_changed_cb)  # beware: will be triggered on a ".clear" too

        label = QLabel("secretion rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # label.setStyleSheet("border: 1px solid black;")
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.secretion_rate = QLineEdit()
        self.secretion_rate.textChanged.connect(self.secretion_rate_changed)
        self.secretion_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.secretion_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
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

        self.secretion_target = QLineEdit()
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

        self.uptake_rate = QLineEdit()
        self.uptake_rate.textChanged.connect(self.uptake_rate_changed)
        self.uptake_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.uptake_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

        #---
        label = QLabel("net export rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.secretion_net_export_rate = QLineEdit()
        self.secretion_net_export_rate.textChanged.connect(self.secretion_net_export_rate_changed)
        self.secretion_net_export_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.secretion_net_export_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("total/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan

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
    def create_interaction_tab(self):
            # <cell_interactions>
            #   <dead_phagocytosis_rate units="1/min">0</dead_phagocytosis_rate>
            #   <live_phagocytosis_rates>
            #     <phagocytosis_rate name="bacteria" units="1/min">0</phagocytosis_rate>
            #     <phagocytosis_rate name="blood vessel" units="1/min">0</phagocytosis_rate>
            #     <phagocytosis_rate name="stem" units="1/min">0</phagocytosis_rate>
            #     <phagocytosis_rate name="differentiated" units="1/min">0</phagocytosis_rate>
            #     <phagocytosis_rate name="macrophage" units="1/min">0</phagocytosis_rate>
            #     <phagocytosis_rate name="CD8+ T cell" units="1/min">0</phagocytosis_rate>
            #     <phagocytosis_rate name="neutrophil" units="1/min">0</phagocytosis_rate>
            #   </live_phagocytosis_rates>
            #   <attack_rates>
            #     <attack_rate name="bacteria" units="1/min">0</attack_rate>
            #     <attack_rate name="blood vessel" units="1/min">0</attack_rate>
            #     <attack_rate name="stem" units="1/min">0</attack_rate>
            #     <attack_rate name="differentiated" units="1/min">0</attack_rate>
            #     <attack_rate name="macrophage" units="1/min">0</attack_rate>
            #     <attack_rate name="CD8+ T cell" units="1/min">0</attack_rate>
            #     <attack_rate name="neutrophil" units="1/min">0</attack_rate>
            #   </attack_rates>
            #   <damage_rate units="1/min">0</damage_rate>
            #   <fusion_rates>
            #     <fusion_rate name="bacteria" units="1/min">0</fusion_rate>
            #     <fusion_rate name="blood vessel" units="1/min">0</fusion_rate>
            #     <fusion_rate name="stem" units="1/min">0</fusion_rate>
            #     <fusion_rate name="differentiated" units="1/min">0</fusion_rate>
            #     <fusion_rate name="macrophage" units="1/min">0</fusion_rate>
            #     <fusion_rate name="CD8+ T cell" units="1/min">0</fusion_rate>
            #     <fusion_rate name="neutrophil" units="1/min">0</fusion_rate>
            #   </fusion_rates>
            # </cell_interactions>
            # <cell_transformations>
            #   <transformation_rates>
            #     <transformation_rate name="bacteria" units="1/min">0</transformation_rate>
            #     <transformation_rate name="blood vessel" units="1/min">0</transformation_rate>
            #     <transformation_rate name="stem" units="1/min">0</transformation_rate>
            #     <transformation_rate name="differentiated" units="1/min">0</transformation_rate>
            #     <transformation_rate name="macrophage" units="1/min">0</transformation_rate>
            #     <transformation_rate name="CD8+ T cell" units="1/min">0</transformation_rate>
            #     <transformation_rate name="neutrophil" units="1/min">0</transformation_rate>
            #   </transformation_rates>
            # </cell_transformations>

        interaction_tab = QWidget()
        glayout = QGridLayout()

        label = QLabel("Phenotype: interaction")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)

            # <cell_interactions>
            #   <dead_phagocytosis_rate units="1/min">0</dead_phagocytosis_rate>
            #   <live_phagocytosis_rates>
            #     <phagocytosis_rate name="bacteria" units="1/min">0</phagocytosis_rate>

        label = QLabel("dead phagocytosis rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr = 0
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.dead_phagocytosis_rate = QLineEdit()
        self.dead_phagocytosis_rate.textChanged.connect(self.dead_phagocytosis_rate_changed)
        self.dead_phagocytosis_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.dead_phagocytosis_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # units.setStyleSheet("border: 1px solid black;")
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("live phagocytosis rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.live_phagocytosis_dropdown = QComboBox()
        glayout.addWidget(self.live_phagocytosis_dropdown, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.live_phagocytosis_dropdown.currentIndexChanged.connect(self.live_phagocytosis_dropdown_changed_cb)  # beware: will be triggered on a ".clear" too

        self.live_phagocytosis_rate = QLineEdit()
        self.live_phagocytosis_rate.textChanged.connect(self.live_phagocytosis_rate_changed)
        self.live_phagocytosis_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.live_phagocytosis_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("attack rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.attack_rate_dropdown = QComboBox()
        glayout.addWidget(self.attack_rate_dropdown, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.attack_rate_dropdown.currentIndexChanged.connect(self.attack_rate_dropdown_changed_cb)  # beware: will be triggered on a ".clear" too

        self.attack_rate = QLineEdit()
        self.attack_rate.textChanged.connect(self.attack_rate_changed)
        self.attack_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.attack_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("damage rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.damage_rate = QLineEdit()
        self.damage_rate.textChanged.connect(self.damage_rate_changed)
        self.damage_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.damage_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("fusion rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.fusion_rate_dropdown = QComboBox()
        glayout.addWidget(self.fusion_rate_dropdown, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.fusion_rate_dropdown.currentIndexChanged.connect(self.fusion_rate_dropdown_changed_cb)  # beware: will be triggered on a ".clear" too

        self.fusion_rate = QLineEdit()
        self.fusion_rate.textChanged.connect(self.fusion_rate_changed)
        self.fusion_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.fusion_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #------
        label = QLabel("transformation rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.cell_transformation_dropdown = QComboBox()
        glayout.addWidget(self.cell_transformation_dropdown, idr,1, 1,1) # w, row, column, rowspan, colspan
        self.cell_transformation_dropdown.currentIndexChanged.connect(self.cell_transformation_dropdown_changed_cb)  # beware: will be triggered on a ".clear" too

        self.transformation_rate = QLineEdit()
        self.transformation_rate.textChanged.connect(self.transformation_rate_changed)
        self.transformation_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.transformation_rate , idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #------
        for idx in range(11):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idr += 1
            glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan

        #------
        # vlayout.setVerticalSpacing(10)  # rwh - argh
        interaction_tab.setLayout(glayout)
        return interaction_tab

    #--------------------------------------------------------
    def cell_adhesion_affinity_changed(self,text):
        # print("cell_adhesion_affinity_changed:  text=",text)
        self.param_d[self.current_cell_def]['cell_adhesion_affinity'][self.cell_adhesion_affinity_celltype] = text

    #--------------------------------------------------------
    def dead_phagocytosis_rate_changed(self,text):
        # print("dead_phagocytosis_rate_changed:  text=",text)
        self.param_d[self.current_cell_def]['dead_phagocytosis_rate'] = text
    #--------------------------------------------------------
    def live_phagocytosis_rate_changed(self,text):
        # print("live_phagocytosis_rate_changed:  text=",text)
        self.param_d[self.current_cell_def]['live_phagocytosis_rate'][self.live_phagocytosis_celltype] = text
    #--------------------------------------------------------
    def attack_rate_changed(self,text):
        # print("attack_rate_changed:  text=",text)
        self.param_d[self.current_cell_def]['attack_rate'][self.attack_rate_celltype] = text
    #--------------------------------------------------------
    def damage_rate_changed(self,text):
        # print("damage_rate_changed:  text=",text)
        self.param_d[self.current_cell_def]['damage_rate'] = text
    #--------------------------------------------------------
    def fusion_rate_changed(self,text):
        # print("fusion_rate_changed:  text=",text)
        self.param_d[self.current_cell_def]['fusion_rate'][self.fusion_rate_celltype] = text
    #--------------------------------------------------------
    def transformation_rate_changed(self,text):
        # print("transformation_rate_changed:  text=",text)
        self.param_d[self.current_cell_def]['transformation_rate'][self.transformation_rate_celltype] = text


    #--------------------------------------------------------
    def create_molecular_tab(self):
        label = QLabel("Phenotype: molecular")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.vbox.addWidget(label)


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

            self.physiboss_signals += ["contact with live cell", "contact with dead cell", "contact with basement membrane", "damage", "dead", "total attack time", "time"]

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
        
                name.currentIndexChanged.connect(lambda index: self.physiboss_inputs_signal_changed(i, index))


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
                self.physiboss_behaviours.append(substrate + " export")
        
            self.physiboss_behaviours += [
                "cycle entry", "exit from cycle phase 1", "exit from cycle phase 2", "exit from cycle phase 3", "exit from cycle phase 4", "exit from cycle phase 5", 
                "apoptosis", "necrosis", "migration speed", "migration bias", "migration persistence time", "chemotactic response to oxygen", 
                "cell-cell adhesion", "cell-cell adhesion elastic constant"
            ]

            for celltype in self.celltypes_list:
                self.physiboss_behaviours.append("adhesive affinity to " + celltype)

            self.physiboss_behaviours += ["relative maximum adhesion distance", "cell-cell repulsion", "cell-BM adhesion", "cell-BM repulsion", "phagocytose dead cell"]

            for celltype in self.celltypes_list:
                self.physiboss_behaviours.append("phagocytose " + celltype)

            for celltype in self.celltypes_list:
                self.physiboss_behaviours.append("attack " + celltype)

            for celltype in self.celltypes_list:
                self.physiboss_behaviours.append("fuse " + celltype)

            for celltype in self.celltypes_list:
                self.physiboss_behaviours.append("transform " + celltype)


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

                name.currentIndexChanged.connect(lambda index: self.physiboss_outputs_behaviour_changed(i, index))


    def physiboss_update_list_nodes(self):

        t_intracellular = self.param_d[self.current_cell_def]["intracellular"]        
        if t_intracellular is not None:

            # Here I started by looking at both the bnd and the cfg
            if (
                t_intracellular is not None 
                and "bnd_filename" in t_intracellular.keys() and t_intracellular['bnd_filename'] is not None and os.path.exists(os.path.join(os.getcwd(), t_intracellular["bnd_filename"])) 
                # and t_intracellular["cfg_filename"] and and os.path.exists(t_intracellular["cfg_filename"])
                ):
                list_nodes = []
                with open(os.path.join(os.getcwd(), t_intracellular["bnd_filename"]), 'r') as bnd_file:
                    list_nodes = [node.split(" ")[1].strip() for node in bnd_file.readlines() if node.strip().lower().startswith("node")]
            
                list_output_nodes = []
                # with open(t_intracellular["cfg_filename"], 'r') as cfg_file:
                #     list_output_nodes = [(node.split(".")[0], node.split("=")[1].split(";")[0]) for node in cfg_file.readlines() if ".is_internal" in node]
                # list_internal_nodes = [node for node, value in list_output_nodes if value.lower() in [1, "true"]]
            
                list_model_nodes = list(set(list_nodes).difference(set(list_output_nodes)))
                self.param_d[self.current_cell_def]["intracellular"]["list_nodes"] = list_model_nodes

                for i, (_, node, _, _, _, _, _, _) in enumerate(self.physiboss_inputs):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_model_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index: self.physiboss_inputs_node_changed(i, index))

                    if (self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["node"] is not None
                        and self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["node"] in list_model_nodes
                    ):
                        node.setCurrentIndex(list_model_nodes.index(self.param_d[self.current_cell_def]["intracellular"]["inputs"][i]["node"]))
                    else:
                        node.setCurrentIndex(-1)
        
                for i, (_, node, _, _, _, _, _, _) in enumerate(self.physiboss_outputs):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_model_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index: self.physiboss_outputs_node_changed(i, index))

                    if (self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["node"] is not None
                        and self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["node"] in list_model_nodes
                    ):
                        node.setCurrentIndex(list_model_nodes.index(self.param_d[self.current_cell_def]["intracellular"]["outputs"][i]["node"]))
                    else:
                        node.setCurrentIndex(-1)
            # else:
            #     for _, node, _, _, _, _, _, _ in self.physiboss_inputs:
            #         node.clear()
                
            #     for _, node, _, _, _, _, _, _ in self.physiboss_outputs:
            #         node.clear()
                
    def physiboss_time_step_changed(self, text):
        if self.param_d[self.current_cell_def]["intracellular"] is not None:
            self.param_d[self.current_cell_def]["intracellular"]['time_step'] = text
    
    def physiboss_scaling_changed(self, text):
        if self.param_d[self.current_cell_def]["intracellular"] is not None:
            self.param_d[self.current_cell_def]["intracellular"]['scaling'] = text
    
    def physiboss_time_stochasticity_changed(self, text):
        if self.param_d[self.current_cell_def]["intracellular"] is not None:
            self.param_d[self.current_cell_def]["intracellular"]['time_stochasticity'] = text
    
    def physiboss_clicked_add_initial_value(self):
        self.physiboss_add_initial_values()
        self.param_d[self.current_cell_def]["intracellular"]["initial_values"].append((None, None))

    def physiboss_add_initial_values(self):

        initial_states_editor = QHBoxLayout()
        initial_states_node = QLineEdit()
        initial_states_value = QLineEdit()
        initial_states_remove = QPushButton("Delete")

        id = len(self.physiboss_initial_states)
        initial_states_node.textChanged.connect(lambda text: self.physiboss_initial_value_node_changed(id, text))
        initial_states_value.textChanged.connect(lambda text: self.physiboss_initial_value_value_changed(id, text))
        initial_states_remove.clicked.connect(lambda: self.physiboss_clicked_remove_initial_values(id))

        initial_states_editor.addWidget(initial_states_node)
        initial_states_editor.addWidget(initial_states_value)
        initial_states_editor.addWidget(initial_states_remove)

        self.physiboss_initial_states_layout.addLayout(initial_states_editor)
        self.physiboss_initial_states.append((initial_states_node, initial_states_value, initial_states_remove, initial_states_editor))

    def physiboss_clicked_remove_initial_values(self, i):
        self.physiboss_remove_initial_values(i)
        del self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i]

    def physiboss_remove_initial_values(self, i):
        self.physiboss_initial_states[i][0].textChanged.disconnect()
        self.physiboss_initial_states[i][0].deleteLater()
        self.physiboss_initial_states[i][1].textChanged.disconnect()
        self.physiboss_initial_states[i][1].deleteLater()
        self.physiboss_initial_states[i][2].clicked.disconnect()
        self.physiboss_initial_states[i][2].deleteLater()
        self.physiboss_initial_states[i][3].deleteLater()
        del self.physiboss_initial_states[i]
        
        # Here we should remap the clicked method to have the proper id
        for i, initial_state in enumerate(self.physiboss_initial_states):
            node, value, button, _ = initial_state
            node.textChanged.disconnect()
            node.textChanged.connect(lambda text: self.physiboss_initial_value_node_changed(i, text))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text: self.physiboss_initial_value_value_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda: self.physiboss_clicked_remove_initial_values(i))

    def physiboss_clear_initial_values(self):
        for i, _ in reversed(list(enumerate(self.physiboss_initial_states))):
            self.physiboss_remove_initial_values(i)
    
    def physiboss_initial_value_node_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i] = (text, self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i][1])

    def physiboss_initial_value_value_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i] = (self.param_d[self.current_cell_def]["intracellular"]["initial_values"][i][0], text)
    
    def physiboss_clicked_add_mutant(self):
        self.physiboss_add_mutant()
        self.param_d[self.current_cell_def]["intracellular"]["mutants"].append(("", ""))

    def physiboss_add_mutant(self):

        mutants_editor = QHBoxLayout()
        mutants_node = QLineEdit()
        mutants_value = QLineEdit()
        mutants_remove = QPushButton("Delete")
        id = len(self.physiboss_mutants)
        mutants_node.textChanged.connect(lambda text: self.physiboss_mutants_node_changed(id, text))
        mutants_value.textChanged.connect(lambda text: self.physiboss_mutants_value_changed(id, text))
        mutants_remove.clicked.connect(lambda: self.physiboss_clicked_remove_mutant(id))

        mutants_editor.addWidget(mutants_node)
        mutants_editor.addWidget(mutants_value)
        mutants_editor.addWidget(mutants_remove)
        self.physiboss_mutants_layout.addLayout(mutants_editor)
        self.physiboss_mutants.append((mutants_node, mutants_value, mutants_remove, mutants_editor))

    def physiboss_clicked_remove_mutant(self, i):
        self.physiboss_remove_mutant(i)
        del self.param_d[self.current_cell_def]["intracellular"]["mutants"][i]

    def physiboss_remove_mutant(self, i):
        self.physiboss_mutants[i][0].textChanged.disconnect()
        self.physiboss_mutants[i][0].deleteLater()
        self.physiboss_mutants[i][1].textChanged.disconnect()
        self.physiboss_mutants[i][1].deleteLater()
        self.physiboss_mutants[i][2].clicked.disconnect()
        self.physiboss_mutants[i][2].deleteLater()
        self.physiboss_mutants[i][3].deleteLater()
        del self.physiboss_mutants[i]
      
        # Here we should remap the clicked method to have the proper id
        for i, mutant in enumerate(self.physiboss_mutants):
            name, value, button, _ = mutant
            name.textChanged.disconnect()
            name.textChanged.connect(lambda text: self.physiboss_mutants_node_changed(i, text))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text: self.physiboss_mutants_value_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda: self.physiboss_clicked_remove_mutant(i))

    def physiboss_clear_mutants(self):
        for i, _ in reversed(list(enumerate(self.physiboss_mutants))):
            self.physiboss_remove_mutant(i)
    
    def physiboss_mutants_node_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["mutants"][i] = (text, self.param_d[self.current_cell_def]["intracellular"]["mutants"][i][1])

    def physiboss_mutants_value_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["mutants"][i] = (self.param_d[self.current_cell_def]["intracellular"]["mutants"][i][0], text)

    def physiboss_clicked_add_parameter(self):
        self.physiboss_add_parameter()
        self.param_d[self.current_cell_def]["intracellular"]["parameters"].append(("", ""))

    def physiboss_add_parameter(self):

        parameters_editor = QHBoxLayout()
        parameters_node = QLineEdit()
        parameters_value = QLineEdit()
        parameters_remove = QPushButton("Delete")
       
        id = len(self.physiboss_parameters)
        parameters_node.textChanged.connect(lambda text: self.physiboss_parameters_node_changed(id, text))
        parameters_value.textChanged.connect(lambda text: self.physiboss_parameters_value_changed(id, text))
        parameters_remove.clicked.connect(lambda: self.physiboss_clicked_remove_parameter(id))

        parameters_editor.addWidget(parameters_node)
        parameters_editor.addWidget(parameters_value)
        parameters_editor.addWidget(parameters_remove)
        self.physiboss_parameters_layout.addLayout(parameters_editor)
        self.physiboss_parameters.append((parameters_node, parameters_value, parameters_remove, parameters_editor))

    def physiboss_clicked_remove_parameter(self, i):
        self.physiboss_remove_parameter(i)
        del self.param_d[self.current_cell_def]["intracellular"]["parameters"][i]

    def physiboss_remove_parameter(self, i):
        self.physiboss_parameters[i][0].textChanged.disconnect()
        self.physiboss_parameters[i][0].deleteLater()
        self.physiboss_parameters[i][1].textChanged.disconnect()
        self.physiboss_parameters[i][1].deleteLater()
        self.physiboss_parameters[i][2].clicked.disconnect()
        self.physiboss_parameters[i][2].deleteLater()
        self.physiboss_parameters[i][3].deleteLater()
        del self.physiboss_parameters[i]

        # Here we should remap the clicked method to have the proper id
        for i, parameter in enumerate(self.physiboss_parameters):
            name, value, button, _ = parameter
            name.textChanged.disconnect()
            name.textChanged.connect(lambda text: self.physiboss_parameters_node_changed(i, text))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text: self.physiboss_parameters_value_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda: self.physiboss_clicked_remove_parameter(i))
        
    def physiboss_clear_parameters(self):
        for i, _ in reversed(list(enumerate(self.physiboss_parameters))):
            self.physiboss_remove_parameter(i)

    def physiboss_parameters_node_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["parameters"][i] = (text, self.param_d[self.current_cell_def]["intracellular"]["parameters"][i][1])

    def physiboss_parameters_value_changed(self, i, text):
        self.param_d[self.current_cell_def]["intracellular"]["parameters"][i] = (self.param_d[self.current_cell_def]["intracellular"]["parameters"][i][0], text)
    
    def physiboss_clicked_add_input(self):
        self.physiboss_add_input()
        self.param_d[self.current_cell_def]["intracellular"]["inputs"].append({
            'name': '',
            'node': '',
            'action': 'activation',
            'threshold': 1.0,
            'inact_threshold': 1.0,
            'smoothing': 0
        })

    def physiboss_add_input(self):

        inputs_editor = QHBoxLayout()
                
        inputs_signal_dropdown = QComboBox()
        inputs_signal_dropdown.setFixedWidth(200)
        for signal in self.physiboss_signals:
            inputs_signal_dropdown.addItem(signal)
        
        inputs_node_dropdown = QComboBox()
        inputs_node_dropdown.setFixedWidth(150)
        if "list_nodes" in self.param_d[self.current_cell_def]["intracellular"]:
            for node in self.param_d[self.current_cell_def]["intracellular"]["list_nodes"]:
                inputs_node_dropdown.addItem(node)
        
        inputs_action = QComboBox()
        inputs_action.setFixedWidth(100)
        inputs_action.addItem("activation")
        inputs_action.addItem("inhibition")
        inputs_remove = QPushButton("Delete")


        id = len(self.physiboss_inputs)
        inputs_node_dropdown.currentIndexChanged.connect(lambda index: self.physiboss_inputs_node_changed(id, index))
        inputs_signal_dropdown.currentIndexChanged.connect(lambda text: self.physiboss_inputs_signal_changed(id, text))
        inputs_action.currentIndexChanged.connect(lambda index: self.physiboss_inputs_action_changed(id, index))
        inputs_remove.clicked.connect(lambda: self.physiboss_clicked_remove_input(id))

        inputs_editor.addWidget(inputs_signal_dropdown)
        inputs_editor.addWidget(inputs_action)
        inputs_editor.addWidget(inputs_node_dropdown)
        
        inputs_threshold = QLineEdit()
        inputs_inact_threshold = QLineEdit()
        inputs_smoothing = QLineEdit()        
        inputs_threshold.textChanged.connect(lambda text: self.physiboss_inputs_threshold_changed(id, text))
        inputs_inact_threshold.textChanged.connect(lambda text: self.physiboss_inputs_inact_threshold_changed(id, text))
        inputs_smoothing.textChanged.connect(lambda text: self.physiboss_inputs_smoothing_changed(id, text))
        
        inputs_editor.addWidget(inputs_threshold)
        inputs_editor.addWidget(inputs_inact_threshold)
        inputs_editor.addWidget(inputs_smoothing)
        
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

    def physiboss_remove_input(self, i):
        self.physiboss_inputs[i][0].currentIndexChanged.disconnect()
        self.physiboss_inputs[i][0].deleteLater()
        self.physiboss_inputs[i][1].currentIndexChanged.disconnect()
        self.physiboss_inputs[i][1].deleteLater()
        self.physiboss_inputs[i][2].currentIndexChanged.disconnect()
        self.physiboss_inputs[i][2].deleteLater()
        self.physiboss_inputs[i][3].textChanged.disconnect()
        self.physiboss_inputs[i][3].deleteLater()
        self.physiboss_inputs[i][4].textChanged.disconnect()
        self.physiboss_inputs[i][4].deleteLater()
        self.physiboss_inputs[i][5].textChanged.disconnect()
        self.physiboss_inputs[i][5].deleteLater()
        self.physiboss_inputs[i][6].clicked.disconnect()
        self.physiboss_inputs[i][6].deleteLater()
        del self.physiboss_inputs[i]

        # Here we should remap the clicked method to have the proper id
        for i, input in enumerate(self.physiboss_inputs):
            signal, node, action, threshold, inact_threshold, smoothing, button, _ = input
            signal.currentIndexChanged.disconnect()
            signal.currentIndexChanged.connect(lambda index: self.physiboss_inputs_signal_changed(i, index))
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index: self.physiboss_inputs_node_changed(i, index))
            action.currentIndexChanged.disconnect()
            action.currentIndexChanged.connect(lambda index: self.physiboss_inputs_action_changed(i, index))
            threshold.textChanged.disconnect()
            threshold.textChanged.connect(lambda text: self.physiboss_inputs_threshold_changed(i, text))
            inact_threshold.textChanged.disconnect()
            inact_threshold.textChanged.connect(lambda text: self.physiboss_inputs_inact_threshold_changed(i, text))
            smoothing.textChanged.disconnect()
            smoothing.textChanged.connect(lambda text: self.physiboss_inputs_smoothing_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda: self.physiboss_clicked_remove_input(i))
        
    def physiboss_clear_inputs(self):
        for i, _ in reversed(list(enumerate(self.physiboss_inputs))):
            self.physiboss_remove_input(i)

    def physiboss_clicked_add_output(self):
        self.physiboss_add_output()
        self.param_d[self.current_cell_def]["intracellular"]["outputs"].append({
            'name': '',
            'node': '',
            'action': 'activation',
            'value': 1.0,
            'basal_value': 1.0,
            'smoothing': 0
        })

    def physiboss_add_output(self):

        outputs_editor = QHBoxLayout()
        outputs_behaviour_dropdown = QComboBox()
        outputs_behaviour_dropdown.setFixedWidth(200)
        for behaviour in self.physiboss_behaviours:
            outputs_behaviour_dropdown.addItem(behaviour)
        
        outputs_node_dropdown = QComboBox()
        outputs_node_dropdown.setFixedWidth(150)
        if "list_nodes" in self.param_d[self.current_cell_def]["intracellular"]:
            for node in self.param_d[self.current_cell_def]["intracellular"]["list_nodes"]:
                outputs_node_dropdown.addItem(node)
        
        outputs_action = QComboBox()
        outputs_action.setFixedWidth(100)
        outputs_action.addItem("activation")
        outputs_action.addItem("inhibition")
        outputs_remove = QPushButton("Delete")


        id = len(self.physiboss_outputs)
        outputs_node_dropdown.currentIndexChanged.connect(lambda index: self.physiboss_outputs_node_changed(id, index))
        outputs_behaviour_dropdown.currentIndexChanged.connect(lambda text: self.physiboss_outputs_behaviour_changed(id, text))
        outputs_action.currentIndexChanged.connect(lambda index: self.physiboss_outputs_action_changed(id, index))
        outputs_remove.clicked.connect(lambda: self.physiboss_clicked_remove_output(id))

        outputs_editor.addWidget(outputs_behaviour_dropdown)
        outputs_editor.addWidget(outputs_action)
        outputs_editor.addWidget(outputs_node_dropdown)
        
        outputs_value = QLineEdit()
        outputs_basal_value = QLineEdit()
        outputs_smoothing = QLineEdit()        
        outputs_value.textChanged.connect(lambda text: self.physiboss_outputs_value_changed(id, text))
        outputs_basal_value.textChanged.connect(lambda text: self.physiboss_outputs_basal_value_changed(id, text))
        outputs_smoothing.textChanged.connect(lambda text: self.physiboss_outputs_smoothing_changed(id, text))
        
        outputs_editor.addWidget(outputs_value)
        outputs_editor.addWidget(outputs_basal_value)
        outputs_editor.addWidget(outputs_smoothing)
        
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

    def physiboss_remove_output(self, i):
        self.physiboss_outputs[i][0].currentIndexChanged.disconnect()
        self.physiboss_outputs[i][0].deleteLater()
        self.physiboss_outputs[i][1].currentIndexChanged.disconnect()
        self.physiboss_outputs[i][1].deleteLater()
        self.physiboss_outputs[i][2].currentIndexChanged.disconnect()
        self.physiboss_outputs[i][2].deleteLater()
        self.physiboss_outputs[i][3].textChanged.disconnect()
        self.physiboss_outputs[i][3].deleteLater()
        self.physiboss_outputs[i][4].textChanged.disconnect()
        self.physiboss_outputs[i][4].deleteLater()
        self.physiboss_outputs[i][5].textChanged.disconnect()
        self.physiboss_outputs[i][5].deleteLater()
        self.physiboss_outputs[i][6].clicked.disconnect()
        self.physiboss_outputs[i][6].deleteLater()
        del self.physiboss_outputs[i]

        # Here we should remap the clicked method to have the proper id
        for i, output in enumerate(self.physiboss_outputs):
            name, node, action, value, basal_value, smoothing, button, _ = output
            name.currentIndexChanged.disconnect()
            name.currentIndexChanged.connect(lambda index: self.physiboss_outputs_behaviour_changed(i, index))
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index: self.physiboss_outputs_node_changed(i, index))
            action.currentIndexChanged.disconnect()
            action.currentIndexChanged.connect(lambda index: self.physiboss_outputs_action_changed(i, index))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text: self.physiboss_outputs_value_changed(i, text))
            basal_value.textChanged.disconnect()
            basal_value.textChanged.connect(lambda text: self.physiboss_outputs_basal_value_changed(i, text))
            smoothing.textChanged.disconnect()
            smoothing.textChanged.connect(lambda text: self.physiboss_outputs_smoothing_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda: self.physiboss_clicked_remove_output(i))
        
    def physiboss_clear_outputs(self):
        for i, _ in reversed(list(enumerate(self.physiboss_outputs))):
            self.physiboss_remove_output(i)


    def intracellular_type_changed(self, index):

        self.physiboss_boolean_frame.hide()
        if index == 0 and self.current_cell_def is not None:
            logging.debug(f'intracellular_type_changed(): {self.current_cell_def}')
            if "intracellular" in self.param_d[self.current_cell_def].keys():
                self.physiboss_bnd_file.setText("")
                self.physiboss_cfg_file.setText("")
                self.physiboss_clear_initial_values()
                self.physiboss_clear_mutants()
                self.physiboss_clear_parameters()
                self.physiboss_clear_inputs()
                self.physiboss_clear_outputs()
                self.physiboss_time_step.setText("12.0")
                self.physiboss_time_stochasticity.setText("0.0")
                self.physiboss_scaling.setText("1.0")
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

            if 'time_step' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.physiboss_time_step.setText("12.0")

            if 'time_stochasticity' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.physiboss_time_stochasticity.setText("0.0")
            
            if 'scaling' not in self.param_d[self.current_cell_def]["intracellular"].keys():
                self.physiboss_scaling.setText("1.0")
                
            self.physiboss_update_list_signals()
            self.physiboss_update_list_behaviours()
            self.physiboss_boolean_frame.show()
        elif index == 2:
            logging.debug(f'intracellular is SBML ODEs')
        elif index == 3:
            logging.debug(f'intracellular is FBA')
        else:
            logging.debug(f'intracellular is Unkown')
        
    #--------------------------------------------------------
    def create_intracellular_tab(self):
        intracellular_tab = QWidget()
        intracellular_tab_scroll = QScrollArea()
        glayout = QVBoxLayout()

        label = QLabel("Phenotype: intracellular")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)

        type_hbox = QHBoxLayout()

        type_label = QLabel("Type")
        type_hbox.addWidget(type_label)

        self.intracellular_type_dropdown = QComboBox()
        self.intracellular_type_dropdown.setFixedWidth(300)
        self.intracellular_type_dropdown.currentIndexChanged.connect(self.intracellular_type_changed)
        self.intracellular_type_dropdown.addItem("none")
        self.intracellular_type_dropdown.addItem("boolean")
        self.intracellular_type_dropdown.addItem("odes")
        self.intracellular_type_dropdown.addItem("fba")
        type_hbox.addWidget(self.intracellular_type_dropdown)

        # glayout.addLayout(type_hbox, idr,0, 1,1) # w, row, column, rowspan, colspan
        glayout.addLayout(type_hbox)#, idr,0, 1,1) # w, row, column, rowspan, colspan


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
        parameters_addbutton.clicked.connect(self.physiboss_clicked_add_parameter)
        ly.addWidget(parameters_addbutton)

        inputs_groupbox = QGroupBox("Inputs")

        self.physiboss_inputs_layout = QVBoxLayout()
        inputs_labels = QHBoxLayout()

        inputs_signal_label = QLabel("Signal")
        inputs_signal_label.setFixedWidth(200)
        inputs_node_label = QLabel("Node")
        inputs_node_label.setFixedWidth(150)
        inputs_action_label = QLabel("Action")
        inputs_node_label.setFixedWidth(100)
        inputs_threshold_label = QLabel("Threshold")
        inputs_inact_threshold_label = QLabel("Inact. Threshold")
        inputs_smoothing_label = QLabel("Smoothing")
        inputs_labels.addWidget(inputs_signal_label)
        inputs_labels.addWidget(inputs_action_label)
        inputs_labels.addWidget(inputs_node_label)
        inputs_labels.addWidget(inputs_threshold_label)
        inputs_labels.addWidget(inputs_inact_threshold_label)
        inputs_labels.addWidget(inputs_smoothing_label)
        self.physiboss_inputs_layout.addLayout(inputs_labels)
        inputs_groupbox.setLayout(self.physiboss_inputs_layout)

        self.physiboss_inputs = []
        ly.addWidget(inputs_groupbox)

        inputs_addbutton = QPushButton("Add new input")
        inputs_addbutton.clicked.connect(self.physiboss_clicked_add_input)
        ly.addWidget(inputs_addbutton)

        outputs_groupbox = QGroupBox("Outputs")

        self.physiboss_outputs_layout = QVBoxLayout()
        outputs_labels = QHBoxLayout()

        outputs_signal_label = QLabel("Signal")
        outputs_signal_label.setFixedWidth(200)
        outputs_node_label = QLabel("Node")
        outputs_node_label.setFixedWidth(150)

        outputs_action_label = QLabel("Action")
        outputs_action_label.setFixedWidth(100)
        outputs_value_label = QLabel("Value")
        outputs_basal_value_label = QLabel("Base_value")
        outputs_smoothing_label = QLabel("Smoothing")
        outputs_labels.addWidget(outputs_signal_label)
        outputs_labels.addWidget(outputs_action_label)
        outputs_labels.addWidget(outputs_node_label)
        outputs_labels.addWidget(outputs_value_label)
        outputs_labels.addWidget(outputs_basal_value_label)
        outputs_labels.addWidget(outputs_smoothing_label)
        self.physiboss_outputs_layout.addLayout(outputs_labels)
        outputs_groupbox.setLayout(self.physiboss_outputs_layout)

        self.physiboss_outputs = []
        ly.addWidget(outputs_groupbox)

        outputs_addbutton = QPushButton("Add new output")
        outputs_addbutton.clicked.connect(self.physiboss_clicked_add_output)
        ly.addWidget(outputs_addbutton)


        glayout.addWidget(self.physiboss_boolean_frame)
        glayout.addStretch()


        intracellular_tab_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        intracellular_tab_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        intracellular_tab_scroll.setWidgetResizable(True)
        intracellular_tab_scroll.setWidget(intracellular_tab) 

        intracellular_tab.setLayout(glayout)

        intracellular_tab.setLayout(glayout)
        return intracellular_tab_scroll

    #--------------------------------------------------------
    # The following (text-based widgets) were (originally) auto-generated by 
    # a mix of sed and Python scripts. See the gen_qline_cb.py script as an early example.
    # --- cycle transition rates
    def cycle_live_trate00_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_live_trate00'] = text

    def cycle_Ki67_trate01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_Ki67_trate01'] = text
    def cycle_Ki67_trate10_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_Ki67_trate10'] = text

    def cycle_advancedKi67_trate01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_trate01'] = text
    def cycle_advancedKi67_trate12_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_trate12'] = text
    def cycle_advancedKi67_trate20_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_trate20'] = text

    def cycle_flowcyto_trate01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcyto_trate01'] = text
    def cycle_flowcyto_trate12_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcyto_trate12'] = text
    def cycle_flowcyto_trate20_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcyto_trate_20'] = text

    def cycle_flowcytosep_trate01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate01'] = text
    def cycle_flowcytosep_trate12_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate12'] = text
    def cycle_flowcytosep_trate23_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate23'] = text
    def cycle_flowcytosep_trate30_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate30'] = text

    def cycle_quiescent_trate01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_quiescent_trate01'] = text
    def cycle_quiescent_trate10_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_quiescent_trate10'] = text

    #--------
    # --- cycle durations
    def cycle_live_duration00_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_live_duration00'] = text

    def cycle_Ki67_duration01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_Ki67_duration01'] = text
    def cycle_Ki67_duration10_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_Ki67_duration10'] = text

    def cycle_advancedKi67_duration01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_duration01'] = text
    def cycle_advancedKi67_duration12_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_duration12'] = text
    def cycle_advancedKi67_duration20_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_duration20'] = text

    def cycle_flowcyto_duration01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcyto_duration01'] = text
    def cycle_flowcyto_duration12_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcyto_duration12'] = text
    def cycle_flowcyto_duration20_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcyto_duration_20'] = text

    def cycle_flowcytosep_duration01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration01'] = text
    def cycle_flowcytosep_duration12_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration12'] = text
    def cycle_flowcytosep_duration23_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration23'] = text
    def cycle_flowcytosep_duration30_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration30'] = text

    def cycle_quiescent_duration01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_quiescent_duration01'] = text
    def cycle_quiescent_duration10_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_quiescent_duration10'] = text

    #------------------------------
    #----- handle all checkboxes for cycle models 'fixed_duration' for 
    # both transition rates and duration times
    def cycle_live_trate00_fixed_clicked(self, bval):
        # print('cycle_live_trate00_fixed_clicked: bval=',bval)
        self.param_d[self.current_cell_def]['cycle_live_trate00_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_live_duration00_fixed'] = bval
        # self.cycle_flowcyto_trate01_fixed_clicked()
        self.cycle_live_duration00_fixed.setChecked(bval)   # sync rate and duration

    def cycle_Ki67_trate01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_Ki67_trate01_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_Ki67_duration01_fixed'] = bval
        self.cycle_Ki67_duration01_fixed.setChecked(bval)   # sync rate and duration
    def cycle_Ki67_trate10_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_Ki67_trate10_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_Ki67_duration10_fixed'] = bval
        self.cycle_Ki67_duration10_fixed.setChecked(bval)   # sync rate and duration

    def cycle_advancedKi67_trate01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_trate01_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_advancedKi67_duration01_fixed'] = bval
        self.cycle_advancedKi67_duration01_fixed.setChecked(bval)   # sync rate and duration
    def cycle_advancedKi67_trate12_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_trate12_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_advancedKi67_duration12_fixed'] = bval
        self.cycle_advancedKi67_duration12_fixed.setChecked(bval)   # sync rate and duration
    def cycle_advancedKi67_trate20_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_trate20_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_advancedKi67_duration20_fixed'] = bval
        self.cycle_advancedKi67_duration20_fixed.setChecked(bval)   # sync rate and duration

    def cycle_flowcyto_trate01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcyto_trate01_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_flowcyto_duration01_fixed'] = bval
        self.cycle_flowcyto_duration01_fixed.setChecked(bval)   # sync rate and duration
    def cycle_flowcyto_trate12_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcyto_trate12_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_flowcyto_duration12_fixed'] = bval
        self.cycle_flowcyto_duration12_fixed.setChecked(bval)   # sync rate and duration
    def cycle_flowcyto_trate20_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcyto_trate20_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_flowcyto_duration20_fixed'] = bval
        self.cycle_flowcyto_duration20_fixed.setChecked(bval)   # sync rate and duration

    def cycle_flowcytosep_trate01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate01_fixed'] = bval
        print("cycle_flowcytosep_trate01_fixed_clicked: set cycle_flowcytosep_duration01_fixed, bval = ",bval)
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration01_fixed'] = bval
        # print("  then call cycle_flowcytosep_duration01_fixed_clicked(bval)")
        # self.cycle_flowcytosep_duration01_fixed_clicked(bval)
        self.cycle_flowcytosep_duration01_fixed.setChecked(bval)   # sync rate and duration
    def cycle_flowcytosep_trate12_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate12_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration12_fixed'] = bval
        self.cycle_flowcytosep_duration12_fixed.setChecked(bval)   # sync rate and duration
    def cycle_flowcytosep_trate23_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate23_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration23_fixed'] = bval
        self.cycle_flowcytosep_duration23_fixed.setChecked(bval)   # sync rate and duration
    def cycle_flowcytosep_trate30_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate30_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration30_fixed'] = bval
        self.cycle_flowcytosep_duration30_fixed.setChecked(bval)   # sync rate and duration

    def cycle_quiescent_trate01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_quiescent_trate01_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_quiescent_duration01_fixed'] = bval
        self.cycle_quiescent_duration01_fixed.setChecked(bval)   # sync rate and duration
    def cycle_quiescent_trate10_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_quiescent_trate10_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_quiescent_duration10_fixed'] = bval
        self.cycle_quiescent_duration10_fixed.setChecked(bval)   # sync rate and duration

    # --- duration
    def cycle_live_duration00_fixed_clicked(self, bval):
        # print('cycle_live_duration00_fixed_clicked: bval=',bval)
        self.param_d[self.current_cell_def]['cycle_live_duration00_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_live_trate00_fixed'] = bval
        self.cycle_live_trate00_fixed.setChecked(bval)   # sync rate and duration

    def cycle_Ki67_duration01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_Ki67_duration01_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_Ki67_trate01_fixed'] = bval
        self.cycle_Ki67_trate01_fixed.setChecked(bval)   # sync rate and duration
    def cycle_Ki67_duration10_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_Ki67_duration10_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_Ki67_trate10_fixed'] = bval
        self.cycle_Ki67_trate10_fixed.setChecked(bval)   # sync rate and duration

    def cycle_advancedKi67_duration01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_duration01_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_advancedKi67_trate01_fixed'] = bval
        self.cycle_advancedKi67_trate01_fixed.setChecked(bval)   # sync rate and duration
    def cycle_advancedKi67_duration12_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_duration12_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_advancedKi67_trate12_fixed'] = bval
        self.cycle_advancedKi67_trate12_fixed.setChecked(bval)   # sync rate and duration
    def cycle_advancedKi67_duration20_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_duration20_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_advancedKi67_trate20_fixed'] = bval
        self.cycle_advancedKi67_trate20_fixed.setChecked(bval)   # sync rate and duration

    def cycle_flowcyto_duration01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcyto_duration01_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_flowcyto_trate01_fixed'] = bval
        self.cycle_flowcyto_trate01_fixed.setChecked(bval)   # sync rate and duration
    def cycle_flowcyto_duration12_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcyto_duration12_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_flowcyto_trate12_fixed'] = bval
        self.cycle_flowcyto_trate12_fixed.setChecked(bval)   # sync rate and duration
    def cycle_flowcyto_duration20_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcyto_duration20_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_flowcyto_trate20_fixed'] = bval
        self.cycle_flowcyto_trate20_fixed.setChecked(bval)   # sync rate and duration

    def cycle_flowcytosep_duration01_fixed_clicked(self, bval):
        # print("cycle_flowcytosep_duration01_fixed_clicked, bval= ",bval)
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration01_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate01_fixed'] = bval
        self.cycle_flowcytosep_trate01_fixed.setChecked(bval)   # sync rate and duration
    def cycle_flowcytosep_duration12_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration12_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate12_fixed'] = bval
        self.cycle_flowcytosep_trate12_fixed.setChecked(bval)   # sync rate and duration
    def cycle_flowcytosep_duration23_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration23_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate23_fixed'] = bval
        self.cycle_flowcytosep_trate23_fixed.setChecked(bval)   # sync rate and duration
    def cycle_flowcytosep_duration30_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration30_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate30_fixed'] = bval
        self.cycle_flowcytosep_trate30_fixed.setChecked(bval)   # sync rate and duration

    def cycle_quiescent_duration01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_quiescent_duration01_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_quiescent_trate01_fixed'] = bval
        self.cycle_quiescent_trate01_fixed.setChecked(bval)   # sync rate and duration
    def cycle_quiescent_duration10_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_quiescent_duration10_fixed'] = bval
        self.param_d[self.current_cell_def]['cycle_quiescent_trate10_fixed'] = bval
        self.cycle_quiescent_trate10_fixed.setChecked(bval)   # sync rate and duration

    #------------------------------
    # --- death
    def apoptosis_death_rate_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_death_rate'] = text

    def apoptosis_phase0_duration_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_phase0_duration'] = text
    def apoptosis_phase0_duration_fixed_toggled(self, bval):
        # sync rate and duration
        self.param_d[self.current_cell_def]['apoptosis_phase0_fixed'] = bval
        self.param_d[self.current_cell_def]['apoptosis_trate01_fixed'] = bval
        self.apoptosis_trate01_fixed.setChecked(bval)   # sync rate and duration

    def apoptosis_trate01_changed(self, text):
        self.param_d[self.current_cell_def]["apoptosis_trate01"] = text
    def apoptosis_trate01_fixed_toggled(self, bval):
        # sync rate and duration
        self.param_d[self.current_cell_def]['apoptosis_trate01_fixed'] = bval
        self.param_d[self.current_cell_def]['apoptosis_phase0_fixed'] = bval
        self.apoptosis_phase0_duration_fixed.setChecked(bval)   # sync rate and duration

    def apoptosis_unlysed_rate_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_unlysed_rate'] = text
    def apoptosis_lysed_rate_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_lysed_rate'] = text
    def apoptosis_cytoplasmic_biomass_change_rate_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_cyto_rate'] = text
    def apoptosis_nuclear_biomass_change_rate_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_nuclear_rate'] = text
    def apoptosis_calcification_rate_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_calcif_rate'] = text
    def apoptosis_relative_rupture_volume_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_rel_rupture_volume'] = text

    #------
    def necrosis_death_rate_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_death_rate'] = text


    def necrosis_phase0_duration_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_phase0_duration'] = text
    def necrosis_phase0_duration_fixed_toggled(self, bval):
        self.param_d[self.current_cell_def]['necrosis_phase0_fixed'] = bval
        self.param_d[self.current_cell_def]['necrosis_trate01_fixed'] = bval
        self.necrosis_trate01_fixed.setChecked(bval)   # sync rate and duration

    def necrosis_phase1_duration_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_phase1_duration'] = text
    def necrosis_phase1_duration_fixed_toggled(self, bval):
        self.param_d[self.current_cell_def]['necrosis_phase1_fixed'] = bval
        self.param_d[self.current_cell_def]['necrosis_trate12_fixed'] = bval
        self.necrosis_trate12_fixed.setChecked(bval)   # sync rate and duration

    def necrosis_trate01_changed(self, text):
        self.param_d[self.current_cell_def]["necrosis_trate01"] = text
    def necrosis_trate01_fixed_toggled(self, bval):
        self.param_d[self.current_cell_def]['necrosis_trate01_fixed'] = bval
        self.param_d[self.current_cell_def]['necrosis_phase0_fixed'] = bval
        self.necrosis_phase0_duration_fixed.setChecked(bval)   # sync rate and duration

    def necrosis_trate12_changed(self, text):
        self.param_d[self.current_cell_def]["necrosis_trate12"] = text
    def necrosis_trate12_fixed_toggled(self, bval):
        self.param_d[self.current_cell_def]['necrosis_trate12_fixed'] = bval
        self.param_d[self.current_cell_def]['necrosis_phase1_fixed'] = bval
        self.necrosis_phase1_duration_fixed.setChecked(bval)   # sync rate and duration

    def necrosis_unlysed_rate_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_unlysed_rate'] = text
    def necrosis_lysed_rate_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_lysed_rate'] = text
    def necrosis_cytoplasmic_biomass_change_rate_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_cyto_rate'] = text
    def necrosis_nuclear_biomass_change_rate_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_nuclear_rate'] = text
    def necrosis_calcification_rate_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_calcif_rate'] = text
    def necrosis_relative_rupture_volume_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_rel_rupture_rate'] = text

    # --- volume
    def volume_total_changed(self, text):
        self.param_d[self.current_cell_def]['volume_total'] = text
    def volume_fluid_fraction_changed(self, text):
        self.param_d[self.current_cell_def]['volume_fluid_fraction'] = text
    def volume_nuclear_changed(self, text):
        self.param_d[self.current_cell_def]['volume_nuclear'] = text
    def volume_fluid_change_rate_changed(self, text):
        self.param_d[self.current_cell_def]['volume_fluid_change_rate'] = text
    def volume_cytoplasmic_biomass_change_rate_changed(self, text):
        # self.param_d[self.current_cell_def]['volume_cytoplasmic_biomass_change_rate'] = text
        self.param_d[self.current_cell_def]['volume_cytoplasmic_rate'] = text
    def volume_nuclear_biomass_change_rate_changed(self, text):
        self.param_d[self.current_cell_def]['volume_nuclear_rate'] = text
    def volume_calcified_fraction_changed(self, text):
        self.param_d[self.current_cell_def]['volume_calcif_fraction'] = text
    def volume_calcification_rate_changed(self, text):
        self.param_d[self.current_cell_def]['volume_calcif_rate'] = text
    def relative_rupture_volume_changed(self, text):
        self.param_d[self.current_cell_def]['volume_rel_rupture_vol'] = text

    # --- mechanics
    def cell_cell_adhesion_strength_changed(self, text):
        self.param_d[self.current_cell_def]['mechanics_adhesion'] = text
    def cell_cell_repulsion_strength_changed(self, text):
        self.param_d[self.current_cell_def]['mechanics_repulsion'] = text

    def cell_bm_adhesion_strength_changed(self, text):
        self.param_d[self.current_cell_def]['mechanics_BM_adhesion'] = text
    def cell_bm_repulsion_strength_changed(self, text):
        self.param_d[self.current_cell_def]['mechanics_BM_repulsion'] = text
    def relative_maximum_adhesion_distance_changed(self, text):
        self.param_d[self.current_cell_def]['mechanics_adhesion_distance'] = text
    def set_relative_equilibrium_distance_changed(self, text):
        self.param_d[self.current_cell_def]['mechanics_relative_equilibrium_distance'] = text
    def set_absolute_equilibrium_distance_changed(self, text):
        self.param_d[self.current_cell_def]['mechanics_absolute_equilibrium_distance'] = text

    def elastic_constant_changed(self, text):
        self.param_d[self.current_cell_def]['mechanics_elastic_constant'] = text
    def attachment_rate_changed(self, text):
        self.param_d[self.current_cell_def]['mechanics_attachment_rate'] = text
    def detachment_rate_changed(self, text):
        self.param_d[self.current_cell_def]['mechanics_detachment_rate'] = text

    # insert callbacks for QCheckBoxes
    def set_relative_equilibrium_distance_enabled_cb(self,bval):
        # print("set_relative_equilibrium_distance_enabled_cb: bval=",bval)
        self.param_d[self.current_cell_def]['mechanics_relative_equilibrium_distance_enabled'] = bval
    def set_absolute_equilibrium_distance_enabled_cb(self,bval):
        # print("set_absolute_equilibrium_distance_enabled_cb: bval=",bval)
        self.param_d[self.current_cell_def]['mechanics_absolute_equilibrium_distance_enabled'] = bval

    # --- motility
    def speed_changed(self, text):
        self.param_d[self.current_cell_def]['speed'] = text
    def persistence_time_changed(self, text):
        self.param_d[self.current_cell_def]['persistence_time'] = text
    def migration_bias_changed(self, text):
        self.param_d[self.current_cell_def]['migration_bias'] = text

    # insert callbacks for QCheckBoxes
    def motility_enabled_cb(self,bval):
        self.param_d[self.current_cell_def]['motility_enabled'] = bval

    def motility_use_2D_cb(self,bval):
        self.param_d[self.current_cell_def]['motility_use_2D'] = bval

    def chemotaxis_enabled_cb(self,bval):
        self.param_d[self.current_cell_def]['motility_chemotaxis'] = bval
        if bval:
            self.motility_substrate_dropdown.setEnabled(True)
            self.chemotaxis_direction_towards.setEnabled(True)
            self.chemotaxis_direction_against.setEnabled(True)

            self.advanced_chemotaxis_enabled.setChecked(False)
            self.param_d[self.current_cell_def]['motility_advanced_chemotaxis'] = False
            self.motility2_substrate_dropdown.setEnabled(False)
            self.chemo_sensitivity.setEnabled(False)
            self.normalize_each_gradient.setEnabled(False)

    def advanced_chemotaxis_enabled_cb(self,bval):
        self.param_d[self.current_cell_def]['motility_advanced_chemotaxis'] = bval
        if bval:
            self.motility_substrate_dropdown.setEnabled(False)
            self.chemotaxis_direction_towards.setEnabled(False)
            self.chemotaxis_direction_against.setEnabled(False)

            self.chemotaxis_enabled.setChecked(False)
            self.param_d[self.current_cell_def]['motility_chemotaxis'] = False
            self.motility2_substrate_dropdown.setEnabled(True)
            self.chemo_sensitivity.setEnabled(True)
            self.normalize_each_gradient.setEnabled(True)

    def normalize_each_gradient_cb(self,bval):
        self.param_d[self.current_cell_def]['normalize_each_gradient'] = bval


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
        # self.param_d[self.current_cell_def]['secretion_rate'] = text

        # self.param_d[cell_def_name]["secretion"][substrate_name]["secretion_rate"] = val
        self.param_d[self.current_cell_def]["secretion"][self.current_secretion_substrate]['secretion_rate'] = text
    def secretion_target_changed(self, text):
        # self.param_d[self.current_cell_def]['secretion_target'] = text
        self.param_d[self.current_cell_def]["secretion"][self.current_secretion_substrate]['secretion_target'] = text
    def uptake_rate_changed(self, text):
        # self.param_d[self.current_cell_def]['uptake_rate'] = text
        self.param_d[self.current_cell_def]["secretion"][self.current_secretion_substrate]['uptake_rate'] = text
    def secretion_net_export_rate_changed(self, text):
        # self.param_d[self.current_cell_def]['secretion_net_export_rate'] = text
        self.param_d[self.current_cell_def]["secretion"][self.current_secretion_substrate]['net_export_rate'] = text

    #--------------------------------------------------------
    # def custom_data_clicked_cb(self, item):
    #     row = self.custom_data_table.currentRow()
    #     col = self.custom_data_table.currentColumn()
    #     if item.checkState() == QtCore.Qt.Checked:
    #         self.custom_var_conserved = True
    #         print('"custom_data_clicked_cb(): %s" clicked/Checked' % item.text())
    #         # self._list.append(item.row())
    #         # print(self._list)
    #     elif item.checkState() == QtCore.Qt.Unchecked:
    #         self.custom_var_conserved = False
    #         print('"custom_data_clicked_cb(): %s" clicked/Unchecked' % item.text())
    #     else:
    #         # print('"custom_data_clicked_cb(): %s" Clicked' % item.text())
    #         print("custom_data_clicked_cb(): %s Clicked" % item.text())
    #     print("     clicked: row,col= ",row,col)

    #     return

        # item = self.custom_data_table.item(row, column)
        # lastState = item.data(LastStateRole)
        # currentState = item.checkState()
        # if currentState != lastState:
        #     print("changed: ")
        #     if currentState == QtCore.Qt.Checked:
        #         print("checked")
        #     else:
        #         print("unchecked")
        #     item.setData(LastStateRole, currentState)

    #--------------------------------------------------------
    # def custom_data_changed_cb(self, item):
    def custom_data_changed_cb_old(self, row,col):
        # row = self.custom_data_table.currentRow()
        # col = self.custom_data_table.currentColumn()
        # if item.checkState() == QtCore.Qt.Checked:
        #     print('"custom_data_changed_cb(): %s" changed/Checked' % item.text())
        #     # self._list.append(item.row())
        #     # print(self._list)
        # elif item.checkState() == QtCore.Qt.Unchecked:
        #     print('"custom_data_changed_cb(): %s" changed/Unchecked' % item.text())
        # else:
        #     # print('"custom_data_changed_cb(): %s" Clicked' % item.text())
        # print("custom_data_changed_cb(): %s changed" % item.text())
        # print(f"custom_data_changed_cb(): item={item}")
        # print("------     changed: row,col= ",row,col)
        # if col == 0:  # Conserve checkbox
        varname = self.custom_data_table.cellWidget(row,self.custom_icol_name).text()
        print("len(varname)=",len(varname))
        if len(varname) == 0:
            self.custom_data_table.item(row, col).setCheckState(0)
            print("HEY! define the variable name first!")
            return

        if col == self.custom_icol_conserved:  # Conserve checkbox
            # if self.custom_data_table.cellWidget(row,0) is None:
            #     print("-- returning")
            #     return
            # if item.checkState() == QtCore.Qt.Checked:
            # print(self.custom_data_table.cellWidget(row,0))

            # checked = self.custom_data_table.cellWidget(row,0).isChecked()
            # if item.checkState() == QtCore.Qt.Checked:
            # if checked:
            #     print("checked")
            # else:
            #     print("unchecked")

            # print("ischecked val= ",self.custom_data_table.cellWidget(row, col).isChecked())
            # print("ischecked val= ",self.custom_data_table.item(row, col).isChecked())
            # print("state val= ",self.custom_data_table.item(row, col).checkState())
            # self.custom_data_table.setItem(irow, 0, item)   # the 0th col is the "Conserve" checkbox

            # OMG, about 3 hrs to figure out how to do this!!!  GUI dev will destroy your soul.
            print("custom_data_changed_cb():  checkState()=", self.custom_data_table.item(row, col).checkState())

            # self.custom_var_conserved = False
            # varname = self.custom_data_table.cellWidget(row,1).text()
            varname = self.custom_data_table.cellWidget(row,self.custom_icol_name).text()
            print("len(varname)=",len(varname))
            if len(varname) == 0:
                self.custom_data_table.item(row, col).setCheckState(0)
                print("HEY! define the variable name first!")
                return
            # print(" varname= ",varname)
            # # print("before:")
            # print(self.param_d[self.current_cell_def]['custom_data'][varname])

            # ...current_cell_def]['custom_data'][vname] = [text, conserved_flag, units_val]

            if self.custom_data_table.item(row, col).checkState() > 0:
                self.param_d[self.current_cell_def]['custom_data'][varname][1] = True
            else:
                self.param_d[self.current_cell_def]['custom_data'][varname][1] = False
            # print(self.param_d[self.current_cell_def]['custom_data'][varname])

            # if item.checkState() == QtCore.Qt.Checked:
            # print('"custom_data_changed_cb(): %s" changed/Checked' % item.text())
            # print("after:")
            # self.param_d[self.current_cell_def]['custom_data'][])
            # print(self.param_d[self.current_cell_def]['custom_data'][varname])


    #--------------------------------------------------------
    def custom_data_search_cb(self, s):
        if not s:
            s = 'thisisadummystring'

        for irow in range(self.max_custom_data_rows):
            if s in self.custom_data_table.cellWidget(irow,self.custom_icol_name).text():
                # print(f"   found {s} at row {irow}")
                self.custom_data_table.cellWidget(irow,self.custom_icol_name).setStyleSheet("background: bisque")
                # self.custom_data_table.selectRow(irow)  # don't do this; keyboard input -> cell 
            else:
                self.custom_data_table.cellWidget(irow,self.custom_icol_name).setStyleSheet("background: white")
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
        row = self.custom_data_table.currentRow()
        # print("------------- delete_custom_data_cb(), row=",row)
        varname = self.custom_data_table.cellWidget(row,self.custom_icol_name).text()
        # print(" custom var name= ",varname)
        # print(" master_custom_var_d= ",self.master_custom_var_d)

        if varname in self.master_custom_var_d.keys():
            self.master_custom_var_d.pop(varname)
            for key in self.master_custom_var_d.keys():
                if self.master_custom_var_d[key][0] > row:   # remember: [row, units, description]
                    self.master_custom_var_d[key][0] -= 1
            # remove (pop) this custom var name from ALL cell types
            for cdef in self.param_d.keys():
                # print(f"   popping {varname} from {cdef}")
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

        self.custom_data_search = QLineEdit()
        self.custom_data_search.setPlaceholderText("Search for Name...")
        self.custom_data_search.textChanged.connect(self.custom_data_search_cb)
        hlayout.addWidget(self.custom_data_search)

        delete_custom_data_btn = QPushButton("Delete row")
        delete_custom_data_btn.clicked.connect(self.delete_custom_data_cb)
        delete_custom_data_btn.setStyleSheet("background-color: yellow")
        hlayout.addWidget(delete_custom_data_btn)

        vlayout.addLayout(hlayout)

        self.custom_data_table = QTableWidget()
        # self.custom_data_table.cellClicked.connect(self.custom_data_cell_was_clicked)
        # self.max_custom_data_rows = 50
        self.max_custom_data_rows = 100
        self.max_custom_data_cols = 5

        # self.max_custom_rows_edited = self.max_custom_data_rows 

        self.custom_data_table.setColumnCount(self.max_custom_data_cols)
        self.custom_data_table.setRowCount(self.max_custom_data_rows)
        # self.custom_data_table.setHorizontalHeaderLabels(['Conserve','Name','Value','Units','Desc'])
        self.custom_data_table.setHorizontalHeaderLabels(['Name','Value','Conserve','Units','Desc'])

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
            # self.custom_data_table.setItem(irow, self.custom_icol_value, item)
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



        # self.custom_data_table.itemClicked.connect(self.custom_data_clicked_cb)
        # self.custom_data_table.cellChanged.connect(self.custom_data_changed_cb)



        vlayout.addWidget(self.custom_data_table)

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
        for irow in range(0,self.max_custom_data_rows):
            for icol in range(5):
                self.custom_data_table.cellWidget(irow,icol).setEnabled(False)
                self.custom_data_table.cellWidget(irow,icol).setStyleSheet("background: lightgray")   # yellow
                # self.sender().setStyleSheet("color: red;")

        if widget:   # enable only(!) the widget that needs to be fixed (because it's a duplicate)
            wrow = widget.wrow
            wcol = widget.wcol
            self.custom_data_table.cellWidget(wrow,wcol).setEnabled(True)
            # self.custom_data_table.setCurrentItem(None)
            self.custom_data_table.cellWidget(wrow,wcol).setStyleSheet("background: white")
            self.custom_data_table.setCurrentCell(wrow,wcol)

        # Also disable the cell type tree
        self.tree.setEnabled(False)

    #----------------------------------------
    def enable_all_custom_data(self):
        # for irow in range(self.max_custom_vars):
        # for irow in range(self.max_custom_rows_edited):
        for irow in range(self.max_custom_data_rows):
            for icol in range(5):
                # if (icol != 2) and (irow != row) and (icol != col):
                # if irow > 47:
                    # print("enable all(): irow,icol=",irow,icol)
                # if self.custom_data_table.cellWidget(irow,icol):
                self.custom_data_table.cellWidget(irow,icol).setEnabled(True)
                self.custom_data_table.cellWidget(irow,icol).setStyleSheet("background: white")
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
            self.custom_table_error(wrow,wcol,"Define Name first!")
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
            self.custom_table_error(wrow,wcol,"Define Name first!")
            self.custom_data_table.cellWidget(wrow,wcol).setChecked(False)
            return

        self.param_d[self.current_cell_def]['custom_data'][vname][1] = bval  # [value, conserved flag]
        # print("custom_data_value_changed(): = self.param_d[self.current_cell_def]['custom_data'][vname][0]",self.param_d[self.current_cell_def]['custom_data'][vname][0])


    #----------------------------------------
    # NOTE: it doesn't matter what cell type is selected; units are the same for ALL. Just unique to custom var name.
    def custom_data_units_changed(self, text):
        # logging.debug(f'\n--------- cell_def_tab.py: custom_data_units_changed() --------')
        # logging.debug(f'   self.current_cell_def = {self.current_cell_def}')
        # print(f'custom_data_units_changed():   self.current_cell_def = {self.current_cell_def}')
        # print(f'custom_data_units_changed(): ----  text= {text}')

        # print("self.sender().wrow = ", self.sender().wrow)
        varname = self.sender().vname.text()
        # print("    varname= ",varname)
        wrow = self.sender().wrow

        # if len(varname == 0):
        #     print("HEY, idiot! sincerely, units")
        #     return

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

        # if len(varname == 0):
        #     print("HEY, idiot! sincerely, desc")
        #     return

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
        
        # self.custom_var_count = 0
        self.custom_data_edit_active = True

    #--------------------------------------------------------
    # @QtCore.Slot()
    def cycle_changed_cb(self, idx):
        # pass
        # print('------ cycle_changed_cb(): idx = ',idx)
        # print('------ cycle_changed_cb(): item = ',str(self.cycle_dropdown.currentText()))
        if self.current_cell_def:
            self.param_d[self.current_cell_def]['cycle_choice_idx'] = idx

        self.customize_cycle_choices()
        # QMessageBox.information(self, "Cycle Changed:",
                #   "Current Cycle Index: %d" % idx )

    # @QtCore.Slot()
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
        # self.advanced_chemotaxis_enabled_cb(self.param_d[self.current_cell_def]["motility_advanced_chemotaxis"])

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
        # print('\n------ cell_adhesion_affinity_dropdown_changed_cb(): idx = ',idx)
        # self.advanced_chemotaxis_enabled_cb(self.param_d[self.current_cell_def]["motility_advanced_chemotaxis"])

        celltype_name = self.cell_adhesion_affinity_dropdown.currentText()
        # self.param_d[self.current_cell_def]['cell_adhesion_affinity_celltype'] = celltype_name
        self.cell_adhesion_affinity_celltype = celltype_name
        # print("   self.cell_adhesion_affinity_celltype = ",celltype_name)

        # print("(dropdown) cell_adhesion_affinity= ",self.param_d[self.current_cell_def]["cell_adhesion_affinity"])
        if self.cell_adhesion_affinity_celltype in self.param_d[self.current_cell_def]["cell_adhesion_affinity"].keys():
            self.cell_adhesion_affinity.setText(self.param_d[self.current_cell_def]["cell_adhesion_affinity"][self.cell_adhesion_affinity_celltype])
        else:
            self.cell_adhesion_affinity.setText(self.default_affinity)

        if idx == -1:
            return

    #---- in interactions subtab
    def live_phagocytosis_dropdown_changed_cb(self, idx):
        # print('\n------ live_phagocytosis_dropdown_changed_cb(): idx = ',idx)
        # self.advanced_chemotaxis_enabled_cb(self.param_d[self.current_cell_def]["motility_advanced_chemotaxis"])

        celltype_name = self.live_phagocytosis_dropdown.currentText()
        # self.param_d[self.current_cell_def]['live_phagocytosis_celltype'] = celltype_name
        self.live_phagocytosis_celltype = celltype_name
        # print("   self.live_phagocytosis_celltype = ",celltype_name)

        if self.live_phagocytosis_celltype in self.param_d[self.current_cell_def]["live_phagocytosis_rate"].keys():
            self.live_phagocytosis_rate.setText(self.param_d[self.current_cell_def]["live_phagocytosis_rate"][self.live_phagocytosis_celltype])
        else:
            self.live_phagocytosis_rate.setText(self.default_sval)
        # self.live_phagocytosis_rate.setText(self.param_d[self.current_cell_def]["live_phagocytosis_rate"]['differentiated'])
        # print("self.param_d[self.current_cell_def]['live_phagocytosis_rate'] = ",self.param_d[self.current_cell_def]['live_phagocytosis_rate'])

        if idx == -1:
            return

    def attack_rate_dropdown_changed_cb(self, idx):
        # print('------ attack_rate_dropdown_changed_cb(): idx = ',idx)
        # self.advanced_chemotaxis_enabled_cb(self.param_d[self.current_cell_def]["motility_advanced_chemotaxis"])

        celltype_name = self.attack_rate_dropdown.currentText()
        # self.param_d[self.current_cell_def]['attack_rate_celltype'] = celltype_name
        self.attack_rate_celltype = celltype_name
        # print("   self.attack_rate_celltype = ",celltype_name)

        if self.attack_rate_celltype in self.param_d[self.current_cell_def]["attack_rate"].keys():
            self.attack_rate.setText(self.param_d[self.current_cell_def]["attack_rate"][self.attack_rate_celltype])
        else:
            self.attack_rate.setText(self.default_sval)

        if idx == -1:
            return

    def fusion_rate_dropdown_changed_cb(self, idx):
        # print('------ fusion_rate_dropdown_changed_cb(): idx = ',idx)
        # self.advanced_chemotaxis_enabled_cb(self.param_d[self.current_cell_def]["motility_advanced_chemotaxis"])

        celltype_name = self.fusion_rate_dropdown.currentText()
        # self.param_d[self.current_cell_def]['fusion_rate_celltype'] = celltype_name
        self.fusion_rate_celltype = celltype_name
        # print("   self.fusion_rate_celltype = ",celltype_name)

        if self.fusion_rate_celltype in self.param_d[self.current_cell_def]["fusion_rate"].keys():
            self.fusion_rate.setText(self.param_d[self.current_cell_def]["fusion_rate"][self.fusion_rate_celltype])
        else:
            self.fusion_rate.setText(self.default_sval)

        if idx == -1:
            return

    def cell_transformation_dropdown_changed_cb(self, idx):
        # print('------ cell_transformation_dropdown_changed_cb(): idx = ',idx)
        # self.advanced_chemotaxis_enabled_cb(self.param_d[self.current_cell_def]["motility_advanced_chemotaxis"])

        celltype_name = self.cell_transformation_dropdown.currentText()
        # self.param_d[self.current_cell_def]['transformation_rate_celltype'] = celltype_name
        self.transformation_rate_celltype = celltype_name
        # print("   self.transformation_rate_celltype= ",celltype_name)

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
        # rb1.toggled.connect(self.updateLabel)(self, idx_choice):
        # print('self.cycle_rows_vbox.count()=', self.cycle_rows_vbox.count())
        # print('cycle_phase_transition_cb: self.stacked_cycle.count()=', self.stacked_cycle.count())

        radioBtn = self.sender()
        # if radioBtn.isChecked():
        #     print("--------- ",radioBtn.text())

        # print("self.cycle_dropdown.currentText() = ",self.cycle_dropdown.currentText())
        # print("self.cycle_dropdown.currentIndex() = ",self.cycle_dropdown.currentIndex())

        # self.cycle_rows_vbox.clear()
        # if radioBtn.text().find("duration"):
        if "duration" in radioBtn.text():
            # print('cycle_phase_transition_cb: --> duration')
            self.cycle_duration_flag = True
            self.customize_cycle_choices()
        else:  # transition rates
            # print('cycle_phase_transition_cb: NOT duration')
            self.cycle_duration_flag = False
            self.customize_cycle_choices()
            # pass

        self.param_d[self.current_cell_def]['cycle_duration_flag'] = self.cycle_duration_flag
        

        # self.cycle_dropdown.addItem("live cells")   # 0 -> 0
        # self.cycle_dropdown.addItem("basic Ki67")   # 0 -> 1, 1 -> 0
        # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
        # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0
        # self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0
        # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0
    # Called whenever there's a toggle between "transition rate(s)" vs. "duration(S)", or if a
    # different cycle model is chosen from the dropdown combobox.
    def customize_cycle_choices(self):

        # print("-- customize_cycle_choices(): index= ",self.cycle_dropdown.currentIndex())

        if self.cycle_duration_flag:  # specifying duration times (radio button)
            if self.cycle_dropdown.currentIndex() == 0:
                # print("customize_cycle_choices():  idx = ",self.stack_duration_live_idx)
                self.stacked_cycle.setCurrentIndex(self.stack_duration_live_idx)
            elif self.cycle_dropdown.currentIndex() == 1:
                self.stacked_cycle.setCurrentIndex(self.stack_duration_Ki67_idx)
            elif self.cycle_dropdown.currentIndex() == 2:
                self.stacked_cycle.setCurrentIndex(self.stack_duration_advancedKi67_idx)
            elif self.cycle_dropdown.currentIndex() == 3:
                self.stacked_cycle.setCurrentIndex(self.stack_duration_flowcyto_idx)
            elif self.cycle_dropdown.currentIndex() == 4:
                self.stacked_cycle.setCurrentIndex(self.stack_duration_flowcytosep_idx)
            elif self.cycle_dropdown.currentIndex() == 5:
                self.stacked_cycle.setCurrentIndex(self.stack_duration_quiescent_idx)

        else:  # specifying transition rates (radio button)
            if self.cycle_dropdown.currentIndex() == 0:
                self.stacked_cycle.setCurrentIndex(self.stack_trate_live_idx)
            elif self.cycle_dropdown.currentIndex() == 1:
                self.stacked_cycle.setCurrentIndex(self.stack_trate_Ki67_idx)
            elif self.cycle_dropdown.currentIndex() == 2:
                self.stacked_cycle.setCurrentIndex(self.stack_trate_advancedKi67_idx)
            elif self.cycle_dropdown.currentIndex() == 3:
                self.stacked_cycle.setCurrentIndex(self.stack_trate_flowcyto_idx)
            elif self.cycle_dropdown.currentIndex() == 4:
                self.stacked_cycle.setCurrentIndex(self.stack_trate_flowcytosep_idx)
            elif self.cycle_dropdown.currentIndex() == 5:
                self.stacked_cycle.setCurrentIndex(self.stack_trate_quiescent_idx)


    def chemotaxis_direction_cb(self):
        # print('chemotaxis_direction_cb: ')

        radioBtn = self.sender()
        if radioBtn.isChecked():
            # print("--------- ",radioBtn.text())  # towards, against
            if "toward" in radioBtn.text():
                self.param_d[self.current_cell_def]["motility_chemotaxis_towards"] = True
            else:
                self.param_d[self.current_cell_def]["motility_chemotaxis_towards"] = False


    #---------------------------------------------
    # @QtCore.Slot()
    # def clear_rows_cb(self):
    #     print("----- clearing all selected rows")

    # @QtCore.Slot()
    # def append_more_cb(self):
    #     for idx in range(5):
    #         # self.main_layout.addLayout(NewUserParam(self))
    #         hbox = QHBoxLayout()
    #         w = QCheckBox("")
    #         w.setReadOnly(True)
    #         self.custom_data_select.append(w)
    #         hbox.addWidget(w)

    #         w = QLineEdit()
    #         self.custom_data_name.append(w)
    #         hbox.addWidget(w)

    #         w = QLineEdit()
    #         self.custom_data_value.append(w)
    #         # w.setValidator(QtGui.QDoubleValidator())
    #         hbox.addWidget(w)

    #         w = QLineEdit()
    #         w.setFixedWidth(self.custom_data_units_width)
    #         self.custom_data_units.append(w)
    #         hbox.addWidget(w)

    #         self.vbox.addLayout(hbox)
    #         # self.main_layout.addLayout(hbox)
    #         self.custom_var_count = self.custom_var_count + 1
    #         print(self.custom_var_count)

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
        # print("self.celltypes_list = ",self.celltypes_list)
        self.celltypes_list.clear()  # rwh/todo: where/why/how is this list maintained?
        self.live_phagocytosis_dropdown.clear()
        self.attack_rate_dropdown.clear()
        self.fusion_rate_dropdown.clear()
        self.cell_transformation_dropdown.clear()

        self.cell_adhesion_affinity_dropdown.clear()
        uep = self.xml_root.find('.//cell_definitions')  # find unique entry point
        # vp = []   # pointers to <variable> nodes
        if uep:
            idx = 0
            for var in uep.findall('cell_definition'):
                # vp.append(var)
                # print(" --> ",var.attrib['name'])
                name = var.attrib['name']
                self.celltypes_list.append(name)
                self.live_phagocytosis_dropdown.addItem(name)
                self.attack_rate_dropdown.addItem(name)
                self.fusion_rate_dropdown.addItem(name)
                self.cell_transformation_dropdown.addItem(name)

                self.cell_adhesion_affinity_dropdown.addItem(name)

                # self.ics_tab.celltype_combobox.addItem(name)

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

        self.cell_adhesion_affinity_dropdown.addItem(name)

        if self.ics_tab:
            self.ics_tab.celltype_combobox.addItem(name)

    #-----------------------------------------------------------------------------------------
    # def delete_substrate(self, item_idx):
    def delete_substrate(self, item_idx, new_substrate):

        # 1) delete it from the comboboxes
        # print("------- delete_substrate: name=",name)
        # print("------- delete_substrate: index=",item_idx)

        # subname = self.motility_substrate_dropdown.itemText(item_idx)
        subname = self.motility2_substrate_dropdown.itemText(item_idx)
        # print("cell_def_tab.py: delete_substrate():    subname = ", subname)
        self.substrate_list.remove(subname)
        # print("self.substrate_list = ",self.substrate_list)

        # update all dropdown/comboboxes
        self.motility_substrate_dropdown.removeItem(item_idx)
        self.motility2_substrate_dropdown.removeItem(item_idx)
        self.secretion_substrate_dropdown.removeItem(item_idx)
        # self.motility_substrate_dropdown.clear()
        # self.secretion_substrate_dropdown.clear()

        # 2) update (delete) in the param_d dict
        # print("\n\n----- before stepping thru all cell defs, self.param_d:")
        # for cdname in self.param_d.keys():  # for all cell defs, rename secretion substrate
            # print(self.param_d[cdname]["secretion"])
            # print()

        # print()
        for cdname in self.param_d.keys():  # for all cell defs, rename secretion substrate
            # print("--- cdname = ",cdname)
            # print("--- old: ",self.param_d[cdname]["secretion"])
            # print(" keys= ",self.param_d[cdname]["secretion"].keys() )
            # if self.param_d[cdname]["secretion"].has_key(subname):
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
        self.physiboss_update_list_signals()
        self.physiboss_update_list_behaviours()

    #-----------------------------------------------------------------------------------------
    # When a user renames a cell type in this tab, we need to update all 
    # data structures (e.g., QComboBox) that reference it.
    def renamed_celltype(self, old_name,new_name):

        self.cell_adhesion_affinity_celltype = new_name

        # 1) update in the comboboxes associated with motility(chemotaxis) and secretion
        logging.debug(f'cell_def_tab.py: ------- renamed_celltype() {old_name} -> {new_name}')
        # print("       old_name = ",old_name)
        # print("       new_name = ",new_name)
        self.celltypes_list = [new_name if x==old_name else x for x in self.celltypes_list]
        logging.debug(f'    self.celltypes_list= {self.celltypes_list}')
        # print()
        logging.debug(f' ')
        for cdname in self.param_d.keys():
            logging.debug(f'{self.param_d[cdname]}')
            logging.debug(f'\n----')

        # 1) update all dropdown widgets containing the cell def names
        for idx in range(len(self.celltypes_list)):
            # print("idx,old,new = ",idx, old_name,new_name)
            # if old_name in self.motility_substrate_dropdown.itemText(idx):
            if old_name == self.live_phagocytosis_dropdown.itemText(idx):
                self.live_phagocytosis_dropdown.setItemText(idx, new_name)
            if old_name == self.attack_rate_dropdown.itemText(idx):
                self.attack_rate_dropdown.setItemText(idx, new_name)
            if old_name == self.fusion_rate_dropdown.itemText(idx):
                self.fusion_rate_dropdown.setItemText(idx, new_name)
            if old_name == self.cell_transformation_dropdown.itemText(idx):
                self.cell_transformation_dropdown.setItemText(idx, new_name)
            if old_name == self.cell_adhesion_affinity_dropdown.itemText(idx):
                self.cell_adhesion_affinity_dropdown.setItemText(idx, new_name)
            if self.ics_tab and (old_name == self.ics_tab.celltype_combobox.itemText(idx)):
                self.ics_tab.celltype_combobox.setItemText(idx, new_name)

        # 2) OMG, also update all param_d dicts that involve cell def names
        logging.debug(f'--- renaming all dicts with cell defs')
        for cdname in self.param_d.keys():  # for all cell defs, rename motility/chemotaxis and secretion substrate
            logging.debug(f'--- cdname = {cdname}')
            self.param_d[cdname]["live_phagocytosis_rate"][new_name] = self.param_d[cdname]["live_phagocytosis_rate"].pop(old_name)
            self.param_d[cdname]["attack_rate"][new_name] = self.param_d[cdname]["attack_rate"].pop(old_name)
            self.param_d[cdname]["fusion_rate"][new_name] = self.param_d[cdname]["fusion_rate"].pop(old_name)
            self.param_d[cdname]["transformation_rate"][new_name] = self.param_d[cdname]["transformation_rate"].pop(old_name)
            self.param_d[cdname]["cell_adhesion_affinity"][new_name] = self.param_d[cdname]["cell_adhesion_affinity"].pop(old_name)
        #     # print("--- new_name: ",new_name)
        #     self.param_d[cdname]["motility_chemotaxis_substrate"] = new_name
        #     self.param_d[cdname]["motility_advanced_chemotaxis_substrate"] = new_name
        #     self.param_d[cdname]["secretion"][new_name] = self.param_d[cdname]["secretion"].pop(old_name)

        #     # print("--- new: ",self.param_d[cdname]["secretion"])

        # if old_name == self.current_secretion_substrate:
        #     self.current_secretion_substrate = new_name
        self.physiboss_update_list_signals()
        self.physiboss_update_list_behaviours()
    #-----------------------------------------------------------------------------------------
    # Use default values found in PhysiCell, e.g., *_standard_models.cpp, etc.
    def new_cycle_params(self, cdname):
        self.param_d[cdname]['cycle_choice_idx'] = 0

        self.param_d[cdname]['cycle_live_trate00'] = '0.00072'

        self.param_d[cdname]['cycle_Ki67_trate01'] = '3.63108e-3'
        self.param_d[cdname]['cycle_Ki67_trate10'] = '1.07527e-3'

        self.param_d[cdname]['cycle_advancedKi67_trate01'] = '4.60405e-3'
        self.param_d[cdname]['cycle_advancedKi67_trate12'] = '1.28205e-3'
        self.param_d[cdname]['cycle_advancedKi67_trate20'] = '6.66666e-3'

        self.param_d[cdname]['cycle_flowcyto_trate01'] = '0.00324'
        self.param_d[cdname]['cycle_flowcyto_trate12'] = '0.00208'
        self.param_d[cdname]['cycle_flowcyto_trate20'] = '0.00333'

        self.param_d[cdname]['cycle_flowcytosep_trate01'] = '0.00335'
        self.param_d[cdname]['cycle_flowcytosep_trate12'] = '0.00208'
        self.param_d[cdname]['cycle_flowcytosep_trate23'] = '0.00417'
        self.param_d[cdname]['cycle_flowcytosep_trate30'] = '0.01667'   # C++ had only 4-digits: 0.0167 ??

        self.param_d[cdname]['cycle_quiescent_trate01'] = '3.63108e-3'
        self.param_d[cdname]['cycle_quiescent_trate10'] = '1.07527e-3'

        # duration times
        self.param_d[cdname]['cycle_live_duration00'] = '1388.88889'

        self.param_d[cdname]['cycle_Ki67_duration01'] = '275.40015'
        self.param_d[cdname]['cycle_Ki67_duration10'] = '929.99898'

        self.param_d[cdname]['cycle_advancedKi67_duration01'] = '217.20007'
        self.param_d[cdname]['cycle_advancedKi67_duration12'] = '780.00078'
        self.param_d[cdname]['cycle_advancedKi67_duration20'] = '150.00015'

        self.param_d[cdname]['cycle_flowcyto_duration01'] = '308.64198'
        self.param_d[cdname]['cycle_flowcyto_duration12'] = '480.76923'
        self.param_d[cdname]['cycle_flowcyto_duration20'] = '300.30030'

        self.param_d[cdname]['cycle_flowcytosep_duration01'] = '298.50746'
        self.param_d[cdname]['cycle_flowcytosep_duration12'] = '480.76923'
        self.param_d[cdname]['cycle_flowcytosep_duration23'] = '239.80815'
        self.param_d[cdname]['cycle_flowcytosep_duration30'] = '59.88024'

        self.param_d[cdname]['cycle_quiescent_duration01'] = '275.40016'
        self.param_d[cdname]['cycle_quiescent_duration10'] = '929.99898'

        #-------------------------
        # transition rates "fixed"
        bval = self.default_bval
        self.param_d[cdname]['cycle_live_trate00_fixed'] = bval

        self.param_d[cdname]['cycle_Ki67_trate01_fixed'] = bval
        self.param_d[cdname]['cycle_Ki67_trate10_fixed'] = True

        self.param_d[cdname]['cycle_advancedKi67_trate01_fixed'] = bval
        self.param_d[cdname]['cycle_advancedKi67_trate12_fixed'] = True
        self.param_d[cdname]['cycle_advancedKi67_trate20_fixed'] = True

        self.param_d[cdname]['cycle_flowcyto_trate01_fixed'] = bval
        self.param_d[cdname]['cycle_flowcyto_trate12_fixed'] = bval
        self.param_d[cdname]['cycle_flowcyto_trate20_fixed'] = bval

        self.param_d[cdname]['cycle_flowcytosep_trate01_fixed'] = bval
        self.param_d[cdname]['cycle_flowcytosep_trate12_fixed'] = bval
        self.param_d[cdname]['cycle_flowcytosep_trate23_fixed'] = bval
        self.param_d[cdname]['cycle_flowcytosep_trate30_fixed'] = bval

        self.param_d[cdname]['cycle_quiescent_trate01_fixed'] = bval
        self.param_d[cdname]['cycle_quiescent_trate10_fixed'] = True

        #------ duration times "fixed"
        self.param_d[cdname]['cycle_live_duration00_fixed'] = bval

        self.param_d[cdname]['cycle_Ki67_duration01_fixed'] = bval
        self.param_d[cdname]['cycle_Ki67_duration10_fixed'] = True

        self.param_d[cdname]['cycle_advancedKi67_duration01_fixed'] = bval
        self.param_d[cdname]['cycle_advancedKi67_duration12_fixed'] = True
        self.param_d[cdname]['cycle_advancedKi67_duration20_fixed'] = True

        self.param_d[cdname]['cycle_flowcyto_duration01_fixed'] = bval
        self.param_d[cdname]['cycle_flowcyto_duration12_fixed'] = bval
        self.param_d[cdname]['cycle_flowcyto_duration20_fixed'] = bval

        self.param_d[cdname]['cycle_flowcytosep_duration01_fixed'] = bval
        self.param_d[cdname]['cycle_flowcytosep_duration12_fixed'] = bval
        self.param_d[cdname]['cycle_flowcytosep_duration23_fixed'] = bval
        self.param_d[cdname]['cycle_flowcytosep_duration30_fixed'] = bval

        self.param_d[cdname]['cycle_quiescent_duration01_fixed'] = bval
        self.param_d[cdname]['cycle_quiescent_duration10_fixed'] = True


    def new_death_params(self, cdname):
        sval = self.default_sval
        duration_sval = '1.e9'
        self.param_d[cdname]["death_rate"] = '5.31667e-05'   # deprecated??
        self.param_d[cdname]["apoptosis_death_rate"] = '5.31667e-05'
        self.param_d[cdname]["apoptosis_phase0_duration"] = '516'
        self.param_d[cdname]["apoptosis_phase0_fixed"] = False

        self.param_d[cdname]["apoptosis_duration_flag"] = False

        self.param_d[cdname]["apoptosis_unlysed_rate"] = '0.05'
        self.param_d[cdname]["apoptosis_lysed_rate"] = '0'
        self.param_d[cdname]["apoptosis_cyto_rate"] = '1.66667e-02'
        self.param_d[cdname]["apoptosis_nuclear_rate"] = '5.83333e-03'
        self.param_d[cdname]["apoptosis_calcif_rate"] = '0'
        self.param_d[cdname]["apoptosis_rel_rupture_volume"] = '2.0'

        #-----
        self.param_d[cdname]["necrosis_death_rate"] = sval

        self.param_d[cdname]["necrosis_trate01"] = '9e.9'
        self.param_d[cdname]['necrosis_trate01_fixed'] = False
        self.param_d[cdname]["necrosis_trate12"] = '1.15741e-05'
        self.param_d[cdname]['necrosis_trate12_fixed'] = True

        self.param_d[cdname]["necrosis_duration_flag"] = False

        self.param_d[cdname]["necrosis_phase0_duration"] = '1.11111e-10'
        self.param_d[cdname]["necrosis_phase0_fixed"] = False
        self.param_d[cdname]["necrosis_phase1_duration"] = '86399.80646'
        self.param_d[cdname]["necrosis_phase1_fixed"] = True

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

    def new_mechanics_params(self, cdname_new):
        sval = self.default_sval
        # use defaults found in phenotype.cpp:Mechanics() instead of 0.0
        self.param_d[cdname_new]["mechanics_adhesion"] = '0.4'
        self.param_d[cdname_new]["mechanics_repulsion"] = '10.0'
        self.param_d[cdname_new]["mechanics_adhesion_distance"] = '1.25'

        self.param_d[cdname_new]["mechanics_relative_equilibrium_distance"] = '1.8'
        self.param_d[cdname_new]["mechanics_absolute_equilibrium_distance"] = '15.12'

        self.param_d[cdname_new]["mechanics_relative_equilibrium_distance_enabled"] = False
        self.param_d[cdname_new]["mechanics_absolute_equilibrium_distance_enabled"] = False

        for cdname in self.param_d.keys():    # for each cell def
            for cdname2 in self.param_d.keys():    # for each cell def
                # print('cdname2= ',cdname2)
                if (cdname == cdname_new) or (cdname2 == cdname_new): 
                    self.param_d[cdname]['live_phagocytosis_rate'][cdname2] = sval
                    self.param_d[cdname]['attack_rate'][cdname2] = sval
                    self.param_d[cdname]['fusion_rate'][cdname2] = sval
                    self.param_d[cdname]['transformation_rate'][cdname2] = sval

                    self.param_d[cdname]['cell_adhesion_affinity'][cdname2] = '1.0'  # default affinity

    def new_motility_params(self, cdname):
        sval = self.default_sval
        self.param_d[cdname]["speed"] = '1.0'
        self.param_d[cdname]["persistence_time"] = '1.0'
        self.param_d[cdname]["migration_bias"] = '0.0'

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
        # print("new_secretion_params(): self.current_secretion_substrate = ",self.current_secretion_substrate)
        # print("        self.param_d[cdname]['secretion'] = ",self.param_d[cdname]["secretion"])
        sval = self.default_sval
        for substrate_name in self.param_d[cdname]["secretion"].keys():
            self.param_d[cdname]["secretion"][substrate_name]["secretion_rate"] = sval
            self.param_d[cdname]["secretion"][substrate_name]["secretion_target"] = '1.0'
            self.param_d[cdname]["secretion"][substrate_name]["uptake_rate"] = sval
            self.param_d[cdname]["secretion"][substrate_name]["net_export_rate"] = sval

    def new_interaction_params(self, cdname_new):
        logging.debug(f'\n--------new_interaction_params(): cdname_new= {cdname_new}')
        sval = self.default_sval
        self.param_d[cdname_new]["dead_phagocytosis_rate"] = sval
        self.param_d[cdname_new]["damage_rate"] = '1.0'

        # self.param_d[cdname]['live_phagocytosis_rate'][self.live_phagocytosis_celltype] = text
        # for cdname2 in self.param_d.keys():  
        #     print('cdname2= ',cdname2)
        #     self.param_d[cdname]['live_phagocytosis_rate'][cdname2] = sval
        #     self.param_d[cdname]['attack_rate'][cdname2] = sval
        #     self.param_d[cdname]['fusion_rate'][cdname2] = sval
        #     self.param_d[cdname]['transformation_rate'][cdname2] = sval

        for cdname in self.param_d.keys():    # for each cell def
            # for cdname2 in self.param_d[cdname]['live_phagocytosis_rate'].keys():    # for each cell def's 
            for cdname2 in self.param_d.keys():    # for each cell def
                # print('cdname2= ',cdname2)
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


    def add_new_substrate(self, sub_name):
        self.add_new_substrate_comboboxes(sub_name)

        sval = self.default_sval

        # for all cell defs: 
        for cdname in self.param_d.keys():  
            # print('cdname = ',cdname)
            # print(self.param_d[cdname]["secretion"])

            # initialize secretion params
            self.param_d[cdname]["secretion"][sub_name] = {}
            self.param_d[cdname]["secretion"][sub_name]["secretion_rate"] = sval
            self.param_d[cdname]["secretion"][sub_name]["secretion_target"] = sval
            self.param_d[cdname]["secretion"][sub_name]["uptake_rate"] = sval
            self.param_d[cdname]["secretion"][sub_name]["net_export_rate"] = sval

            # initialize motility advanced chemotaxis params
            self.param_d[cdname]["chemotactic_sensitivity"][sub_name] = sval
        
        self.physiboss_update_list_signals()
        self.physiboss_update_list_behaviours()

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

    #-----------------------------------------------------------------------------------------
    def update_cycle_params(self):
        # pass
        cdname = self.current_cell_def

        # # if 'live' in self.param_d[cdname]['cycle']:
        # #     self.cycle_dropdown.setCurrentIndex(0)
        # # elif 'separated' in self.param_d[cdname]['cycle']:
        # #     self.cycle_dropdown.setCurrentIndex(4)

        if self.param_d[cdname]['cycle_duration_flag']:
            self.cycle_rb2.setChecked(True)
        else:
            self.cycle_rb1.setChecked(True)

            # self.param_d[self.current_cell_def]['cycle_choice_idx'] = idx
        self.cycle_dropdown.setCurrentIndex(self.param_d[cdname]['cycle_choice_idx'])


        # transition rates
        self.cycle_live_trate00.setText(self.param_d[cdname]['cycle_live_trate00'])

        self.cycle_Ki67_trate01.setText(self.param_d[cdname]['cycle_Ki67_trate01'])
        self.cycle_Ki67_trate10.setText(self.param_d[cdname]['cycle_Ki67_trate10'])

        self.cycle_advancedKi67_trate01.setText(self.param_d[cdname]['cycle_advancedKi67_trate01'])
        self.cycle_advancedKi67_trate12.setText(self.param_d[cdname]['cycle_advancedKi67_trate12'])
        self.cycle_advancedKi67_trate20.setText(self.param_d[cdname]['cycle_advancedKi67_trate20'])

        self.cycle_flowcyto_trate01.setText(self.param_d[cdname]['cycle_flowcyto_trate01'])
        self.cycle_flowcyto_trate12.setText(self.param_d[cdname]['cycle_flowcyto_trate12'])
        self.cycle_flowcyto_trate20.setText(self.param_d[cdname]['cycle_flowcyto_trate20'])

        self.cycle_flowcytosep_trate01.setText(self.param_d[cdname]['cycle_flowcytosep_trate01'])
        # self.cycle_flowcytosep_trate01.setText(f'{self.param_d[cdname]["cycle_flowcytosep_trate01"]:.{self.num_dec}f}')
        # val3.setText(f'{fval:.{number_of_decimals}f}')
        self.cycle_flowcytosep_trate12.setText(self.param_d[cdname]['cycle_flowcytosep_trate12'])
        self.cycle_flowcytosep_trate23.setText(self.param_d[cdname]['cycle_flowcytosep_trate23'])
        self.cycle_flowcytosep_trate30.setText(self.param_d[cdname]['cycle_flowcytosep_trate30'])

        self.cycle_quiescent_trate01.setText(self.param_d[cdname]['cycle_quiescent_trate01'])
        self.cycle_quiescent_trate10.setText(self.param_d[cdname]['cycle_quiescent_trate10'])

        # duration times
        self.cycle_live_duration00.setText(self.param_d[cdname]['cycle_live_duration00'])

        self.cycle_Ki67_duration01.setText(self.param_d[cdname]['cycle_Ki67_duration01'])
        self.cycle_Ki67_duration10.setText(self.param_d[cdname]['cycle_Ki67_duration10'])

        self.cycle_advancedKi67_duration01.setText(self.param_d[cdname]['cycle_advancedKi67_duration01'])
        self.cycle_advancedKi67_duration12.setText(self.param_d[cdname]['cycle_advancedKi67_duration12'])
        self.cycle_advancedKi67_duration20.setText(self.param_d[cdname]['cycle_advancedKi67_duration20'])

        self.cycle_flowcyto_duration01.setText(self.param_d[cdname]['cycle_flowcyto_duration01'])
        self.cycle_flowcyto_duration12.setText(self.param_d[cdname]['cycle_flowcyto_duration12'])
        self.cycle_flowcyto_duration20.setText(self.param_d[cdname]['cycle_flowcyto_duration20'])

        self.cycle_flowcytosep_duration01.setText(self.param_d[cdname]['cycle_flowcytosep_duration01'])
        self.cycle_flowcytosep_duration12.setText(self.param_d[cdname]['cycle_flowcytosep_duration12'])
        self.cycle_flowcytosep_duration23.setText(self.param_d[cdname]['cycle_flowcytosep_duration23'])
        self.cycle_flowcytosep_duration30.setText(self.param_d[cdname]['cycle_flowcytosep_duration30'])

        self.cycle_quiescent_duration01.setText(self.param_d[cdname]['cycle_quiescent_duration01'])
        self.cycle_quiescent_duration10.setText(self.param_d[cdname]['cycle_quiescent_duration10'])


        #-------------------------
        # transition rates "fixed"
        # self.apoptosis_phase0_duration_fixed.setChecked(self.param_d[cdname]["apoptosis_phase0_fixed"])

        self.cycle_live_trate00_fixed.setChecked(self.param_d[cdname]['cycle_live_trate00_fixed'])

        self.cycle_Ki67_trate01_fixed.setChecked(self.param_d[cdname]['cycle_Ki67_trate01_fixed'])
        self.cycle_Ki67_trate10_fixed.setChecked(self.param_d[cdname]['cycle_Ki67_trate10_fixed'])

        self.cycle_advancedKi67_trate01_fixed.setChecked(self.param_d[cdname]['cycle_advancedKi67_trate01_fixed'])
        self.cycle_advancedKi67_trate12_fixed.setChecked(self.param_d[cdname]['cycle_advancedKi67_trate12_fixed'])
        self.cycle_advancedKi67_trate20_fixed.setChecked(self.param_d[cdname]['cycle_advancedKi67_trate20_fixed'])

        self.cycle_flowcyto_trate01_fixed.setChecked(self.param_d[cdname]['cycle_flowcyto_trate01_fixed'])
        self.cycle_flowcyto_trate12_fixed.setChecked(self.param_d[cdname]['cycle_flowcyto_trate12_fixed'])
        self.cycle_flowcyto_trate20_fixed.setChecked(self.param_d[cdname]['cycle_flowcyto_trate20_fixed'])

        self.cycle_flowcytosep_trate01_fixed.setChecked(self.param_d[cdname]['cycle_flowcytosep_trate01_fixed'])
        self.cycle_flowcytosep_trate12_fixed.setChecked(self.param_d[cdname]['cycle_flowcytosep_trate12_fixed'])
        self.cycle_flowcytosep_trate23_fixed.setChecked(self.param_d[cdname]['cycle_flowcytosep_trate23_fixed'])
        self.cycle_flowcytosep_trate30_fixed.setChecked(self.param_d[cdname]['cycle_flowcytosep_trate30_fixed'])

        self.cycle_quiescent_trate01_fixed.setChecked(self.param_d[cdname]['cycle_quiescent_trate01_fixed'])
        self.cycle_quiescent_trate10_fixed.setChecked(self.param_d[cdname]['cycle_quiescent_trate10_fixed'])


        #------ duration times "fixed"
        self.cycle_live_duration00_fixed.setChecked(self.param_d[cdname]['cycle_live_duration00_fixed'])

        self.cycle_Ki67_duration01_fixed.setChecked(self.param_d[cdname]['cycle_Ki67_duration01_fixed'])
        self.cycle_Ki67_duration10_fixed.setChecked(self.param_d[cdname]['cycle_Ki67_duration10_fixed'])

        self.cycle_advancedKi67_duration01_fixed.setChecked(self.param_d[cdname]['cycle_advancedKi67_duration01_fixed'])
        self.cycle_advancedKi67_duration12_fixed.setChecked(self.param_d[cdname]['cycle_advancedKi67_duration12_fixed'])
        self.cycle_advancedKi67_duration20_fixed.setChecked(self.param_d[cdname]['cycle_advancedKi67_duration20_fixed'])

        self.cycle_flowcyto_duration01_fixed.setChecked(self.param_d[cdname]['cycle_flowcyto_duration01_fixed'])
        self.cycle_flowcyto_duration12_fixed.setChecked(self.param_d[cdname]['cycle_flowcyto_duration12_fixed'])
        self.cycle_flowcyto_duration20_fixed.setChecked(self.param_d[cdname]['cycle_flowcyto_duration20_fixed'])

        self.cycle_flowcytosep_duration01_fixed.setChecked(self.param_d[cdname]['cycle_flowcytosep_duration01_fixed'])
        self.cycle_flowcytosep_duration12_fixed.setChecked(self.param_d[cdname]['cycle_flowcytosep_duration12_fixed'])
        self.cycle_flowcytosep_duration23_fixed.setChecked(self.param_d[cdname]['cycle_flowcytosep_duration23_fixed'])
        self.cycle_flowcytosep_duration30_fixed.setChecked(self.param_d[cdname]['cycle_flowcytosep_duration30_fixed'])

        self.cycle_quiescent_duration01_fixed.setChecked(self.param_d[cdname]['cycle_quiescent_duration01_fixed'])
        self.cycle_quiescent_duration10_fixed.setChecked(self.param_d[cdname]['cycle_quiescent_duration10_fixed'])

        #         # if cycle_code == 0:
        #         #     self.cycle_dropdown.setCurrentIndex(2)
        #         #     self.param_d[cell_def_name]['cycle'] = 'advanced Ki67'
        #         # elif cycle_code == 1:
        #         #     self.cycle_dropdown.setCurrentIndex(1)
        #         #     self.param_d[cell_def_name]['cycle'] = 'basic Ki67'
        #         # elif cycle_code == 2:
        #         #     self.cycle_dropdown.setCurrentIndex(3)
        #         #     self.param_d[cell_def_name]['cycle'] = 'flow cytometry'
        #         # elif cycle_code == 5:
        #         #     self.cycle_dropdown.setCurrentIndex(0)
        #         #     self.param_d[cell_def_name]['cycle'] = 'live cells'
        #         # elif cycle_code == 6:
        #         #     self.cycle_dropdown.setCurrentIndex(4)
        #         #     self.param_d[cell_def_name]['cycle'] = 'flow cytometry separated'
        #         # elif cycle_code == 7:
        #         #     self.cycle_dropdown.setCurrentIndex(5)
        #         #     self.param_d[cell_def_name]['cycle'] = 'cycling quiescent'

        # self.cycle_trate00.setText(self.param_d[self.current_cell_def]['cycle_trate00'])
        # self.cycle_trate01.setText(self.param_d[self.current_cell_def]['cycle_trate01'])
        # # self.cycle_flowcyto_trate01.setText(self.param_d[self.current_cell_def]['cycle_flowcyto_trate01'])
        # self.cycle_flowcyto_trate12.setText(self.param_d[self.current_cell_def]['cycle_flowcyto_trate12'])

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
        self.apoptosis_phase0_duration.setText(self.param_d[cdname]["apoptosis_phase0_duration"])
        self.apoptosis_phase0_duration_fixed.setChecked(self.param_d[cdname]["apoptosis_phase0_fixed"])
        # vs.
        self.apoptosis_trate01.setText(self.param_d[cdname]["apoptosis_trate01"])
        self.apoptosis_trate01_fixed.setChecked(self.param_d[cdname]["apoptosis_trate01_fixed"])

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
        self.necrosis_phase0_duration.setText(self.param_d[cdname]["necrosis_phase0_duration"])
        self.necrosis_phase0_duration_fixed.setChecked(self.param_d[cdname]["necrosis_phase0_fixed"])
        self.necrosis_phase1_duration.setText(self.param_d[cdname]["necrosis_phase1_duration"])
        self.necrosis_phase1_duration_fixed.setChecked(self.param_d[cdname]["necrosis_phase1_fixed"])
        # vs.
        self.necrosis_trate01.setText(self.param_d[cdname]["necrosis_trate01"])
        self.necrosis_trate01_fixed.setChecked(self.param_d[cdname]["necrosis_trate01_fixed"])
        self.necrosis_trate12.setText(self.param_d[cdname]["necrosis_trate12"])
        self.necrosis_trate12_fixed.setChecked(self.param_d[cdname]["necrosis_trate12_fixed"])

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
        self.cell_bm_adhesion_strength.setText(self.param_d[cdname]["mechanics_BM_adhesion"])
        self.cell_bm_repulsion_strength.setText(self.param_d[cdname]["mechanics_BM_repulsion"])
        self.relative_maximum_adhesion_distance.setText(self.param_d[cdname]["mechanics_adhesion_distance"])

        # print("update_mechanics_params(): param_d= ",self.param_d)

        # self.param_d[cdname]['cell_adhesion_affinity'][cdname2] = '1.0'  # default affinity
        if self.cell_adhesion_affinity_celltype:
            logging.debug(f'key 0= {self.cell_adhesion_affinity_celltype}')
            logging.debug(f'keys 1= {self.param_d.keys()}')
            logging.debug(f'keys 2= {self.param_d[cdname]["cell_adhesion_affinity"].keys()}')
            self.cell_adhesion_affinity.setText(self.param_d[cdname]["cell_adhesion_affinity"][self.cell_adhesion_affinity_celltype])

        self.set_relative_equilibrium_distance.setText(self.param_d[cdname]["mechanics_relative_equilibrium_distance"])
        self.set_relative_equilibrium_distance_enabled.setChecked(self.param_d[cdname]["mechanics_relative_equilibrium_distance_enabled"])

        self.set_absolute_equilibrium_distance.setText(self.param_d[cdname]["mechanics_absolute_equilibrium_distance"])
        self.set_absolute_equilibrium_distance_enabled.setChecked(self.param_d[cdname]["mechanics_absolute_equilibrium_distance_enabled"])

        self.elastic_constant.setText(self.param_d[cdname]["mechanics_elastic_constant"])
        self.attachment_rate.setText(self.param_d[cdname]["mechanics_attachment_rate"])
        self.detachment_rate.setText(self.param_d[cdname]["mechanics_detachment_rate"])


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
            # self.motility_substrate_dropdown.setEnabled(True)
            # self.chemotaxis_direction_towards.setEnabled(True)
            # self.chemotaxis_direction_against.setEnabled(True)
            # self.advanced_chemotaxis_enabled.setChecked(False)
        else:
            self.chemotaxis_enabled_cb(False)
        #     print("   (simple) chemotaxis motility is NOT enabled:")
        #     print("   motility_enabled=",self.param_d[cdname]["motility_enabled"])
        #     print("--> ",self.param_d[cdname])
        #     print()
        #     self.motility_use_2D.setChecked(False)
        #     self.motility_substrate_dropdown.setEnabled(False)
        #     self.chemotaxis_direction_towards.setEnabled(False)
        #     self.chemotaxis_direction_against.setEnabled(False)


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
            self.normalize_each_gradient_cb(True)
        else:
            self.normalize_each_gradient.setChecked(False)
            self.normalize_each_gradient_cb(False)

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

        self.secretion_rate.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["secretion_rate"])
        self.secretion_target.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["secretion_target"])
        self.uptake_rate.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["uptake_rate"])
        self.secretion_net_export_rate.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["net_export_rate"])

        # rwh: also update the qdropdown to select the substrate

    #-----------------------------------------------------------------------------------------
    def update_interaction_params(self):
        cdname = self.current_cell_def
        self.dead_phagocytosis_rate.setText(self.param_d[cdname]["dead_phagocytosis_rate"])
        self.damage_rate.setText(self.param_d[cdname]["damage_rate"])

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
                self.intracellular_type_dropdown.setCurrentIndex(1)
                if "bnd_filename" in self.param_d[cdname]["intracellular"].keys(): 
                    self.physiboss_bnd_file.setText(self.param_d[cdname]["intracellular"]["bnd_filename"])
                if "cfg_filename" in self.param_d[cdname]["intracellular"].keys():
                    self.physiboss_cfg_file.setText(self.param_d[cdname]["intracellular"]["cfg_filename"])
                self.physiboss_time_step.setText(self.param_d[cdname]["intracellular"]["time_step"])
                self.physiboss_time_stochasticity.setText(self.param_d[cdname]["intracellular"]["time_stochasticity"])
                self.physiboss_scaling.setText(self.param_d[cdname]["intracellular"]["scaling"])

                self.physiboss_clear_initial_values()
                for i, initial_value in enumerate(self.param_d[cdname]["intracellular"]["initial_values"]):
                    self.physiboss_add_initial_values()
                    node, value, _, _ = self.physiboss_initial_states[i]
                    node.setText(initial_value[0])
                    value.setText(initial_value[1])

                self.physiboss_clear_mutants()
                for i, mutant in enumerate(self.param_d[cdname]["intracellular"]["mutants"]):
                    self.physiboss_add_mutant()
                    node, value, _, _ = self.physiboss_mutants[i]
                    node.setText(mutant[0])
                    value.setText(mutant[1])

                self.physiboss_clear_parameters()
                for i, parameter in enumerate(self.param_d[cdname]["intracellular"]["parameters"]):
                    self.physiboss_add_parameter()
                    name, value, _, _ = self.physiboss_parameters[i]
                    name.setText(parameter[0])
                    value.setText(parameter[1])

                self.physiboss_clear_inputs()
                self.physiboss_clear_outputs()      
                self.fill_substrates_comboboxes()
                self.fill_celltypes_comboboxes()
                self.physiboss_update_list_signals()
                self.physiboss_update_list_behaviours()
                self.physiboss_update_list_nodes()
                
                for i, input in enumerate(self.param_d[cdname]["intracellular"]["inputs"]):
                    self.physiboss_add_input()
                    name, node, action, threshold, inact_threshold, smoothing, _, _ = self.physiboss_inputs[i]
                    logging.debug(f'update_intracellular_params(): cdname={cdname},  {input["name"]}={input["name"]}')
                    logging.debug(f'  param_d= {self.param_d[cdname]["intracellular"]}')
                    name.setCurrentIndex(self.physiboss_signals.index(input["name"]))
                    node.setCurrentIndex(self.param_d[cdname]["intracellular"]["list_nodes"].index(input["node"]))
                    action.setCurrentIndex(1 if input["action"] == "inhibition" else 0)
                    threshold.setText(input["threshold"])
                    inact_threshold.setText(input["inact_threshold"])
                    smoothing.setText(input["smoothing"])

                for i, output in enumerate(self.param_d[cdname]["intracellular"]["outputs"]):
                    self.physiboss_add_output()
                    name, node, action, value, basal_value, smoothing, _, _ = self.physiboss_outputs[i]
                    name.setCurrentIndex(self.physiboss_behaviours.index(output["name"]))
                    node.setCurrentIndex(self.param_d[cdname]["intracellular"]["list_nodes"].index(output["node"]))
                    action.setCurrentIndex(1 if output["action"] == "inhibition" else 0)
                    value.setText(output["value"])
                    basal_value.setText(output["basal_value"])
                    smoothing.setText(output["smoothing"])

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

    #-----------------------------------------------------------------------------------------
    # called from pmb.py: load_mode() -> show_sample_model() -> reset_xml_root()
    def clear_custom_data_params(self):
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
        # print('\n\n------------ tree_item_clicked_cb -----------:', it, col, it.text(col) )
        self.current_cell_def = it.text(col)
        # print('--- tree_item_clicked_cb(): self.current_cell_def= ',self.current_cell_def )

        # for k in self.param_d.keys():
        #     print(" ===>>> ",k, " : ", self.param_d[k])
        #     print()

        # fill in the GUI with this cell def's params

        self.update_cycle_params()
        self.update_death_params()
        self.update_volume_params()
        self.update_mechanics_params()
        self.update_motility_params()
        self.update_secretion_params()
        self.update_interaction_params()
        self.update_intracellular_params()
        # self.update_molecular_params()
        self.update_custom_data_params()


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
    def fill_xml_cycle(self,pheno,cdef):
        # ------- cycle ------- 
        # <cycle code="5" name="live">  
        # <cycle code="6" name="Flow cytometry model (separated)">  


        # self.cycle_dropdown.addItem("live cells")   # 0 -> 0
        # self.cycle_dropdown.addItem("basic Ki67")   # 0 -> 1, 1 -> 0
        # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
        # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0
        # self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0
        # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0

        # static const int advanced_Ki67_cycle_model= 0;
        # static const int basic_Ki67_cycle_model=1;
        # static const int flow_cytometry_cycle_model=2;
        # static const int live_apoptotic_cycle_model=3;
        # static const int total_cells_cycle_model=4;
        # static const int live_cells_cycle_model = 5; 
        # static const int flow_cytometry_separated_cycle_model = 6; 
        # static const int cycling_quiescent_model = 7; 

        # self.cycle_combo_idx_code = {0:"5", 1:"1", 2:"0", 3:"2", 4:"6", 5:"7"}
        # TODO: check if these names must be specific in the C++ 
        # self.cycle_combo_idx_name = {0:"live", 1:"basic Ki67", 2:"advanced Ki67", 3:"flow cytometry", 4:"Flow cytometry model (separated)", 5:"cycling quiescent"}

        combo_widget_idx = self.param_d[cdef]["cycle_choice_idx"]
        cycle = ET.SubElement(pheno, "cycle",
            {"code":self.cycle_combo_idx_code[combo_widget_idx],
                "name":self.cycle_combo_idx_name[combo_widget_idx] } )
        cycle.text = self.indent12  # affects self.indent of child, i.e., <phase_transition_rates, for example.
        cycle.tail = "\n" + self.indent10

        #-- duration
        # if self.cycle_duration_flag:
        if self.param_d[cdef]['cycle_duration_flag']:
            subelm = ET.SubElement(cycle, "phase_durations",{"units":self.default_time_units})
            subelm.text = self.indent14
            subelm.tail = self.indent12

            #--- live
            if combo_widget_idx == 0:
                sfix = "false"
                if self.param_d[cdef]['cycle_live_duration00_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_live_duration00']
                subelm2.tail = self.indent12

            elif combo_widget_idx == 1:
                sfix = "false"
                if self.param_d[cdef]['cycle_Ki67_duration01_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_Ki67_duration01']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_Ki67_duration10_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_Ki67_duration01']
                subelm2.tail = self.indent12

            # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
            elif combo_widget_idx == 2:
                sfix = "false"
                if self.param_d[cdef]['cycle_advancedKi67_duration01_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_advancedKi67_duration01']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_advancedKi67_duration12_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_advancedKi67_duration12']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_advancedKi67_duration20_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"2", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_advancedKi67_duration20']
                subelm2.tail = self.indent12

            # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0
            elif combo_widget_idx == 3:
                sfix = "false"
                if self.param_d[cdef]['cycle_flowcyto_duration01_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcyto_duration01']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcyto_duration12_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcyto_duration12']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcyto_duration20_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"2", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcyto_duration20']
                subelm2.tail = self.indent12

            # self.cycle_dropdown.addItem("flow cytometry sepaduration") # 0->1, 1->2, 2->3, 3->0
            elif combo_widget_idx == 4:
                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_duration01_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_duration01']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_duration12_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_duration12']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_duration23_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"2", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_duration23']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_duration30_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"3", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_duration30']
                subelm2.tail = self.indent12

            # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0
            elif combo_widget_idx == 5:
                sfix = "false"
                if self.param_d[cdef]['cycle_quiescent_duration01_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_quiescent_duration01']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_quiescent_duration10_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_quiescent_duration01']
                subelm2.tail = self.indent12



        #-- transition rates
        else:
            subelm = ET.SubElement(cycle, "phase_transition_rates",{"units":self.default_rate_units})
            subelm.text = self.indent14  # affects </cycle>, i.e., its parent
            subelm.tail = self.indent12

            # self.cycle_dropdown.addItem("live cells")   # 0 -> 0
            # self.cycle_dropdown.addItem("basic Ki67")   # 0 -> 1, 1 -> 0
            # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
            # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0
            # self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0
            # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0
            if combo_widget_idx == 0:
                sfix = "false"
                if self.param_d[cdef]['cycle_live_trate00_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0", "end_index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_live_trate00']
                subelm2.tail = self.indent12

            elif combo_widget_idx == 1:
                sfix = "false"
                if self.param_d[cdef]['cycle_Ki67_trate01_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0", "end_index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_Ki67_trate01']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_Ki67_trate10_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"1", "end_index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_Ki67_trate01']
                subelm2.tail = self.indent12

            # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
            elif combo_widget_idx == 2:
                sfix = "false"
                if self.param_d[cdef]['cycle_advancedKi67_trate01_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0", "end_index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_advancedKi67_trate01']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_advancedKi67_trate12_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"1", "end_index":"2", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_advancedKi67_trate12']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_advancedKi67_trate20_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"2", "end_index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_advancedKi67_trate20']
                subelm2.tail = self.indent12

            # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0
            elif combo_widget_idx == 3:
                sfix = "false"
                if self.param_d[cdef]['cycle_flowcyto_trate01_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0", "end_index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcyto_trate01']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcyto_trate12_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"1", "end_index":"2", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcyto_trate12']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcyto_trate20_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"2", "end_index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcyto_trate20']
                subelm2.tail = self.indent12

            # self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0
            elif combo_widget_idx == 4:
                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_trate01_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0", "end_index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_trate01']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_trate12_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"1", "end_index":"2", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_trate12']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_trate23_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"2", "end_index":"3", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_trate23']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_trate30_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"3", "end_index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_trate30']
                subelm2.tail = self.indent12

            # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0
            elif combo_widget_idx == 5:
                sfix = "false"
                if self.param_d[cdef]['cycle_quiescent_trate01_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0", "end_index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_quiescent_trate01']
                subelm2.tail = self.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_quiescent_trate10_fixed']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"1", "end_index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_quiescent_trate01']
                subelm2.tail = self.indent12

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
            if self.param_d[cdname]["apoptosis_phase0_fixed"]:
                bval = "true"
            subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":bval})
            subelm2.text = self.param_d[cdname]["apoptosis_phase0_duration"]
            subelm2.tail = self.indent14
        else:   # transition rate
            subelm = ET.SubElement(model, "phase_transition_rates",{"units":self.default_rate_units})
            subelm.text = self.indent16
            subelm.tail = self.indent14

            bval = "false"
            if self.param_d[cdname]["apoptosis_trate01_fixed"]:
                bval = "true"
            subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0","end_index":"1", "fixed_duration":bval})
            subelm2.text = self.param_d[cdname]["apoptosis_trate01"]
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
            if self.param_d[cdname]["necrosis_phase0_fixed"]:
                bval = "true"
            subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":bval})
            subelm2.text = self.param_d[cdname]["necrosis_phase0_duration"]
            subelm2.tail = self.indent14

            bval = "false"
            if self.param_d[cdname]["necrosis_phase1_fixed"]:
                bval = "true"
            subelm2 = ET.SubElement(subelm, "duration",{"index":"1", "fixed_duration":bval})
            subelm2.text = self.param_d[cdname]["necrosis_phase1_duration"]
            subelm2.tail = self.indent14
        else:   # transition rate
            subelm = ET.SubElement(model, "phase_transition_rates",{"units":self.default_rate_units})
            subelm.text = self.indent16
            subelm.tail = self.indent14

            bval = "false"
            if self.param_d[cdname]["necrosis_trate01_fixed"]:
                bval = "true"
            subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0","end_index":"1", "fixed_duration":bval})
            subelm2.text = self.param_d[cdname]["necrosis_trate01"]
            subelm2.tail = self.indent16

            bval = "false"
            if self.param_d[cdname]["necrosis_trate12_fixed"]:
                bval = "true"
            subelm2 = ET.SubElement(subelm, "rate",{"start_index":"1","end_index":"2", "fixed_duration":bval})
            subelm2.text = self.param_d[cdname]["necrosis_trate12"]
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
        elm = ET.SubElement(mechanics, 'cell_BM_adhesion_strength',{"units":"micron/min"})
        elm.text = self.param_d[cdef]["mechanics_BM_adhesion"]
        elm.tail = self.indent12

        elm = ET.SubElement(mechanics, 'cell_BM_repulsion_strength',{"units":"micron/min"})
        elm.text = self.param_d[cdef]["mechanics_BM_repulsion"]
        elm.tail = self.indent12

        elm = ET.SubElement(mechanics, 'attachment_elastic_constant',{"units":self.default_rate_units})
        elm.text = self.param_d[cdef]["mechanics_elastic_constant"]
        elm.tail = self.indent12

        elm = ET.SubElement(mechanics, 'attachment_rate',{"units":self.default_rate_units})
        elm.text = self.param_d[cdef]["mechanics_attachment_rate"]
        elm.tail = self.indent12

        elm = ET.SubElement(mechanics, 'detachment_rate',{"units":self.default_rate_units})
        elm.text = self.param_d[cdef]["mechanics_detachment_rate"]
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

    #-------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml_interactions(self,pheno,cdef):
        if self.debug_print_fill_xml:
            logging.debug(f'------------------- fill_xml_interactions():  cdef= {cdef}')

        interactions = ET.SubElement(pheno, "cell_interactions")
        interactions.text = self.indent12  # affects indent of child
        interactions.tail = "\n" + self.indent10

        subelm = ET.SubElement(interactions, "dead_phagocytosis_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdef]["dead_phagocytosis_rate"]
        subelm.tail = self.indent12

        #-----
        lpr = ET.SubElement(interactions, "live_phagocytosis_rates")
        lpr.text = self.indent16
        lpr.tail = "\n" + self.indent12

        logging.debug(f'--- live_phagocytosis_rate= {self.param_d[cdef]["live_phagocytosis_rate"]}')
        for key in self.param_d[cdef]['live_phagocytosis_rate'].keys():
            logging.debug(f'  key in live_phagocytosis_rate= {key}')
            if len(key) == 0:
                continue
            val = self.param_d[cdef]['live_phagocytosis_rate'][key]
            logging.debug(f'{key}  --> {val}')
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
        subelm = ET.SubElement(interactions, "damage_rate",{"units":self.default_rate_units})
        subelm.text = self.param_d[cdef]["damage_rate"]
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

    #-------------------------------------------------------------------
    # Get values from the dict and generate/write a new XML
    def fill_xml_intracellular(self, pheno, cdef):
        if self.debug_print_fill_xml:
            logging.debug(f'------------------- fill_xml_intracellular()')
            logging.debug(f'------ ["intracellular"]: for {cdef}')
            logging.debug(f'{self.param_d[cdef]["intracellular"]}')

            if self.param_d[cdef]['intracellular'] is not None:

                if self.param_d[cdef]['intracellular']['type'] == "maboss":
                            
                    # Checking if you should prevent saving because of missing input
                    if 'bnd_filename' not in self.param_d[cdef]['intracellular'] or self.param_d[cdef]['intracellular']['bnd_filename'] in [None, ""]:
                        raise Exception("Missing BND file in the " + cdef + " cell definition ")

                    if 'cfg_filename' not in self.param_d[cdef]['intracellular'] or self.param_d[cdef]['intracellular']['cfg_filename'] in [None, ""]:
                        raise Exception("Missing CFG file in the " + cdef + " cell definition ")

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
                        
                        for node, value in self.param_d[cdef]['intracellular']['initial_values']:
                            if node != "" and value != "":
                                initial_value = ET.SubElement(initial_values, "initial_value", {"intracellular_name": node})
                                initial_value.text = value
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

                    if len(self.param_d[cdef]['intracellular']['mutants']) > 0:
                        scaling.tail = self.indent14
                        mutants = ET.SubElement(settings, "mutations")
                        mutants.text = self.indent16
                        mutants.tail = self.indent14
                        
                        for node, value in self.param_d[cdef]['intracellular']['mutants']:
                            if node != "" and value != "":
                                mutant = ET.SubElement(mutants, "mutation", {"intracellular_name": node})
                                mutant.text = value
                                mutant.tail = self.indent16

                        mutant.tail = self.indent12

                    if len(self.param_d[cdef]['intracellular']['parameters']) > 0:
                        scaling.tail = self.indent14

                        parameters = ET.SubElement(settings, "parameters")
                        parameters.text = self.indent16
                        parameters.tail = self.indent14
                        
                        for name, value in self.param_d[cdef]['intracellular']['parameters']:
                            if name != "" and value != "":
                                parameter = ET.SubElement(parameters, "parameter", {"intracellular_name": name})
                                parameter.text = value
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


                    

        if self.debug_print_fill_xml:
            logging.debug(f'\n')
    #-------------------------------------------------------------------
    # Get values from the dict and generate/write a new XML
    def fill_xml_custom_data(self, custom_data, cdef):
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

        elm.tail = self.indent8   # back up 2 for the very last one

        if self.debug_print_fill_xml:
            logging.debug(f'\n')


    #-------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml(self):
        # pass
        logging.debug(f'\n\n----------- cell_def_tab.py: fill_xml(): ----------')
        # print("self.param_d.keys() = ",self.param_d.keys())
        # print()
        # print("self.param_d['default'] = ",self.param_d['default'])
        # print()
        # print("self.param_d['cell_def02'] = ",self.param_d['cell_def02'])
        # print()
        # print("self.param_d['endothelial'] = ",self.param_d['endothelial'])
        # print("\nself.param_d['endothelial']['cell_ID'] = ",self.param_d['endothelial']['cell_ID'])
        # print("\nself.param_d['mesangial_matrix']['cell_ID'] = ",self.param_d['mesangial_matrix']['cell_ID'])

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


        idx = 0
        for cdef in self.param_d.keys():
            logging.debug(f'\n--- key in param_d.keys() = {cdef}')
            if cdef in cdefs_in_tree:
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
                elm = ET.Element("cell_definition", 
                        {"name":cdef, "ID":str(idx)})  # rwh: renumbering IDs; do we need to retain the original IDs?
                        # {"name":cdef, "ID":self.param_d[cdef]["ID"]})  # rwh: if retaining original IDs.
                elm.tail = '\n' + self.indent6
                elm.text = self.indent8
                pheno = ET.SubElement(elm, 'phenotype')
                pheno.text = self.indent10
                pheno.tail = self.indent8

                self.fill_xml_cycle(pheno,cdef)
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

                uep.insert(idx,elm)
                idx += 1

        logging.debug(f'----------- end cell_def_tab.py: fill_xml(): ----------')