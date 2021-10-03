"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)
"""

import sys
import copy
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDoubleValidator


class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

# Overloading the QLineEdit widget to let us map it to its variable name. Ugh.
class MyQLineEdit(QLineEdit):
    vname = None

class CellDef(QWidget):
    def __init__(self):
        super().__init__()
        # global self.params_cell_def

        # primary key = cell def name
        # secondary keys: cycle_rate_choice, cycle_dropdown, 
        self.param_d = {}  # a dict of dicts
        self.default_sval = '0.0'
        self.default_bval = False
        self.default_time_units = "min"
        self.default_rate_units = "1/min"

        self.current_cell_def = None
        self.new_cell_def_count = 1
        self.label_width = 210
        self.units_width = 70
        self.idx_current_cell_def = 1    # 1-offset for XML (ElementTree, ET)
        self.xml_root = None
        self.custom_data_count = 0
        self.max_custom_data_rows = 99
        # self.custom_data_units_width = 90
        self.cycle_duration_flag = False

        self.substrate_list = []

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
        # self.tree.setStyleSheet("background-color: lightgray")
        self.tree.setFixedWidth(tree_widget_width)
        self.tree.setFixedHeight(tree_widget_height)
        # self.tree.setColumnCount(1)
        self.tree.itemClicked.connect(self.tree_item_clicked_cb)
        self.tree.itemChanged.connect(self.tree_item_changed_cb)   # rename a substrate

        header = QTreeWidgetItem(["---  Cell Type  ---"])
        self.tree.setHeaderItem(header)

        items = []
        model = QtCore.QStringListModel()
        model.setStringList(["aaa","bbb"])

        self.cell_def_horiz_layout.addWidget(self.tree)

        self.scroll_cell_def_tree = QScrollArea()
        self.scroll_cell_def_tree.setWidget(self.tree)

        # splitter.addWidget(self.tree)
        self.splitter.addWidget(self.scroll_cell_def_tree)

        #------------------
        self.controls_hbox = QHBoxLayout()
        self.new_button = QPushButton("New")
        self.new_button.clicked.connect(self.new_cell_def)
        self.controls_hbox.addWidget(self.new_button)

        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_cell_def)
        self.controls_hbox.addWidget(self.copy_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_cell_def)
        self.controls_hbox.addWidget(self.delete_button)

        #------------------
        self.cycle_tab = QWidget()
        self.death_tab = QWidget()
        self.volume_tab = QWidget()
        self.mechanics_tab = QWidget()
        self.motility_tab = QWidget()
        self.secretion_tab = QWidget()
        self.custom_data_tab = QWidget()

        self.scroll_params = QScrollArea()

        self.tab_widget = QTabWidget()
        self.splitter.addWidget(self.scroll_params)

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
        self.tab_widget.addTab(self.create_custom_data_tab(),"Custom Data")

        self.cell_types_tabs_layout = QGridLayout()
        self.cell_types_tabs_layout.addWidget(self.tab_widget, 0,0,1,1) # w, row, column, rowspan, colspan

    #----------------------------------------------------------------------
    # @QtCore.Slot()
    def new_cell_def(self):
        # print('------ new_cell_def')
        cdname = "cell_def%02d" % self.new_cell_def_count
        # Make a new substrate (that's a copy of the currently selected one)
        self.param_d[cdname] = copy.deepcopy(self.param_d[self.current_cell_def])

        # for k in self.param_d.keys():
        #     print(" (pre-new vals)===>>> ",k, " : ", self.param_d[k])
        #     print()
        # print()

        # Then "zero out" all entries and uncheck checkboxes
        self.new_cycle_params(cdname)
        self.new_death_params(cdname)
        self.new_volume_params(cdname)
        self.new_mechanics_params(cdname)
        self.new_motility_params(cdname)
        # self.new_secretion_params(cdname)  # todo: fix this method
        # self.new_custom_data_params(cdname)

        # print("\n ----- new dict:")
        # for k in self.param_d.keys():
        #     print(" ===>>> ",k, " : ", self.param_d[k])
        #     print()

        self.new_cell_def_count += 1
        self.current_cell_def = cdname

        #-----  Update this new cell def's widgets' values
        num_items = self.tree.invisibleRootItem().childCount()
        # print("tree has num_items = ",num_items)
        treeitem = QTreeWidgetItem([cdname])
        treeitem.setFlags(treeitem.flags() | QtCore.Qt.ItemIsEditable)
        self.tree.insertTopLevelItem(num_items,treeitem)
        self.tree.setCurrentItem(treeitem)

        self.tree_item_clicked_cb(treeitem, 0)

    #----------------------
    # When a substrate is selected(via double-click) and renamed
    def tree_item_changed_cb(self, it,col):
        # print('--------- tree_item_changed_cb():', it, col, it.text(col) )  # col=0 always

        prev_name = self.current_cell_def
        # print('prev_name= ',prev_name)
        self.current_cell_def = it.text(col)
        self.param_d[self.current_cell_def] = self.param_d.pop(prev_name)  # sweet

    #----------------------------------------------------------------------
    # @QtCore.Slot()
    def copy_cell_def(self):
        # print('------ copy_cell_def')
        celldefname = "cell_def%02d" % self.new_cell_def_count
        # print('------ self.current_cell_def = ', self.current_cell_def)
        # Make a new cell_def (that's a copy of the currently selected one)
        self.param_d[celldefname] = copy.deepcopy(self.param_d[self.current_cell_def])

        # for k in self.param_d.keys():
        #     print(" (pre-new vals)===>>> ",k, " : ", self.param_d[k])
        #     print()
        # print()

        self.new_cell_def_count += 1

        self.current_cell_def = celldefname
        # self.cell_type_name.setText(celldefname)

        #-----  Update this new cell def's widgets' values
        num_items = self.tree.invisibleRootItem().childCount()
        # print("tree has num_items = ",num_items)
        treeitem = QTreeWidgetItem([celldefname])
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
        if returnValue == QMessageBox.Ok:
            print('OK clicked')


    # @QtCore.Slot()
    def delete_cell_def(self):
        num_items = self.tree.invisibleRootItem().childCount()
        print('------ delete_cell_def: num_items=',num_items)
        if num_items == 1:
            # print("Not allowed to delete all substrates.")
            # QMessageBox.information(self, "Not allowed to delete all substrates")
            self.show_delete_warning()
            return

        # rwh: is this safe?
        del self.param_d[self.current_cell_def]

        # for k in self.param_d.keys():
        #     print(" ===>>> ",k, " : ", self.param_d[k])
        #     print()

        item_idx = self.tree.indexFromItem(self.tree.currentItem()).row() 
        print('------      item_idx=',item_idx)
        # self.tree.removeItemWidget(self.tree.currentItem(), 0)
        self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(self.tree.currentItem()))

        print('------      new name=',self.tree.currentItem().text(0))
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
        print("\n====================== create_cycle_tab ===================")
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

        units = QLabel("1/min")
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
        print(" new stacked widget: trate live -------------> ",idx_stacked_widget)
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)
        
        self.stack_trate_Ki67.setLayout(glayout)

        idx_stacked_widget += 1
        self.stack_trate_Ki67_idx = idx_stacked_widget 
        print(" new stacked widget: trate Ki67 -------------> ",idx_stacked_widget)
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 2,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)
        
        self.stack_trate_advancedKi67.setLayout(glayout)
        idx_stacked_widget += 1
        print(" new stacked widget: t02 -------------> ",idx_stacked_widget)
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 2,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)
        
        #-----
        self.stack_trate_flowcyto.setLayout(glayout)
        idx_stacked_widget += 1
        print(" new stacked widget: trate_flowcyto -------------> ",idx_stacked_widget)
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
        glayout.addWidget(self.cycle_flowcytosep_trate01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_flowcytosep_trate01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_flowcytosep_trate01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan
        self.cycle_flowcytosep_trate01_fixed.clicked.connect(self.cycle_flowcytosep_trate01_fixed_clicked)

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 3,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)

        #-----
        self.stack_trate_flowcytosep.setLayout(glayout)
        idx_stacked_widget += 1
        print(" new stacked widget: flow cyto sep -------------> ",idx_stacked_widget)
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #------
        self.insert_hacky_blank_lines(glayout)
        
        #---
        self.stack_trate_quiescent.setLayout(glayout)

        idx_stacked_widget += 1
        self.stack_trate_quiescent_idx = idx_stacked_widget 
        print(" new stacked widget: trate_quiescent -------------> ",idx_stacked_widget)
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
        print(" new stacked widget: duration live -------------> ",idx_stacked_widget)
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
        print(" new stacked widget: duration Ki67 -------------> ",idx_stacked_widget)
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
        print(" new stacked widget: t02 -------------> ",idx_stacked_widget)
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
        print(" new stacked widget: duration_flowcyto -------------> ",idx_stacked_widget)
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
        print(" new stacked widget: flow cyto sep -------------> ",idx_stacked_widget)
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
        print(" new stacked widget: duration_quiescent -------------> ",idx_stacked_widget)
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
        glayout = QGridLayout()

        #----------------
        label = QLabel("Apoptosis")
        label.setFixedSize(100,20)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet('background-color: yellow')
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

        units = QLabel("1/min")
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

        self.apoptosis_trate01 = QLineEdit()
        self.apoptosis_trate01.textChanged.connect(self.apoptosis_trate01_changed)
        self.apoptosis_trate01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.apoptosis_trate01, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_trate01_fixed = QCheckBox("Fixed")
        self.apoptosis_trate01_fixed.toggled.connect(self.apoptosis_trate01_fixed_toggled)
        glayout.addWidget(self.apoptosis_trate01_fixed, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel(self.default_time_units)
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

        units = QLabel("1/min")
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
        units = QLabel("1/min")
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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
        label.setStyleSheet('background-color: yellow')
        idr += 1
        glayout.addWidget(label, idr,0, 1,4) # w, row, column, rowspan, colspan

        label = QLabel("death rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_death_rate = QLineEdit()
        self.necrosis_death_rate.textChanged.connect(self.necrosis_death_rate_changed)
        self.necrosis_death_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_death_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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
        units = QLabel("1/min")
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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
        for idx in range(11):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idr += 1
            glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan
        #------

        # glayout.setVerticalSpacing(10)  # rwh - argh
        death_tab.setLayout(glayout)
        return death_tab

    #--------------------------------------------------------
    def apoptosis_phase_transition_cb(self):
        print('\n  ---- apoptosis_phase_transition_cb: ')

        radioBtn = self.sender()
        if radioBtn.isChecked():
            print("apoptosis: ------>>",radioBtn.text())

        if "duration" in radioBtn.text():
            print('apoptosis_phase_transition_cb: --> duration')
            self.apoptosis_duration_flag = True
            self.apoptosis_trate01.setReadOnly(True)
            self.apoptosis_trate01.setStyleSheet("background-color: lightgray")  
            self.apoptosis_trate01_fixed.setEnabled(False)

            self.apoptosis_phase0_duration.setReadOnly(False)
            self.apoptosis_phase0_duration.setStyleSheet("background-color: white")
            self.apoptosis_phase0_duration_fixed.setEnabled(True)
        else:  # transition rates
            print('apoptosis_phase_transition_cb: NOT duration')
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
        print('\n  ---- necrosis_phase_transition_cb: ')

        radioBtn = self.sender()
        if radioBtn.isChecked():
            print("necrosis: ------>>",radioBtn.text())

        # print("self.cycle_dropdown.currentText() = ",self.cycle_dropdown.currentText())
        # print("self.cycle_dropdown.currentIndex() = ",self.cycle_dropdown.currentIndex())

        # self.cycle_rows_vbox.clear()
        # if radioBtn.text().find("duration"):
        if "duration" in radioBtn.text():
            print('necrosis_phase_transition_cb: --> duration')
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
            print('necrosis_phase_transition_cb: NOT duration')
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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
    
        #---
    # <options>
    #     <set_relative_equilibrium_distance enabled="false" units="dimensionless">1.8</set_relative_equilibrium_distance>
    #     <set_absolute_equilibrium_distance enabled="false" units="micron">15.12</set_absolute_equilibrium_distance>
    # </options>
        label = QLabel("Options:")
        label.setFixedSize(80,20)
        label.setStyleSheet("background-color: yellow")
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

        #------
        for idx in range(11):  # rwh: hack solution to align rows
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
        label.setStyleSheet('background-color: yellow')
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


        #------
        for idx in range(11):  # rwh: hack solution to align rows
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

        units = QLabel("1/min")
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

        units = QLabel("1/min")
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
    def create_molecular_tab(self):
        label = QLabel("Phenotype: molecular")
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.vbox.addWidget(label)

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

    def cycle_Ki67_trate01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_Ki67_trate01_fixed'] = bval
    def cycle_Ki67_trate10_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_Ki67_trate10_fixed'] = bval

    def cycle_advancedKi67_trate01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_trate01_fixed'] = bval
    def cycle_advancedKi67_trate12_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_trate12_fixed'] = bval
    def cycle_advancedKi67_trate20_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_trate20_fixed'] = bval

    def cycle_flowcyto_trate01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcyto_trate01_fixed'] = bval
    def cycle_flowcyto_trate12_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcyto_trate12_fixed'] = bval
    def cycle_flowcyto_trate20_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcyto_trate20_fixed'] = bval

    def cycle_flowcytosep_trate01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate01_fixed'] = bval
    def cycle_flowcytosep_trate12_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate12_fixed'] = bval
    def cycle_flowcytosep_trate23_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate23_fixed'] = bval
    def cycle_flowcytosep_trate30_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_trate30_fixed'] = bval

    def cycle_quiescent_trate01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_quiescent_trate01_fixed'] = bval
    def cycle_quiescent_trate10_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_quiescent_trate10_fixed'] = bval

    # --- duration
    def cycle_live_duration00_fixed_clicked(self, bval):
        # print('cycle_live_duration00_fixed_clicked: bval=',bval)
        self.param_d[self.current_cell_def]['cycle_live_duration00_fixed'] = bval

    def cycle_Ki67_duration01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_Ki67_duration01_fixed'] = bval
    def cycle_Ki67_duration10_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_Ki67_duration10_fixed'] = bval

    def cycle_advancedKi67_duration01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_duration01_fixed'] = bval
    def cycle_advancedKi67_duration12_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_duration12_fixed'] = bval
    def cycle_advancedKi67_duration20_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_advancedKi67_duration20_fixed'] = bval

    def cycle_flowcyto_duration01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcyto_duration01_fixed'] = bval
    def cycle_flowcyto_duration12_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcyto_duration12_fixed'] = bval
    def cycle_flowcyto_duration20_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcyto_duration20_fixed'] = bval

    def cycle_flowcytosep_duration01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration01_fixed'] = bval
    def cycle_flowcytosep_duration12_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration12_fixed'] = bval
    def cycle_flowcytosep_duration23_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration23_fixed'] = bval
    def cycle_flowcytosep_duration30_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_flowcytosep_duration30_fixed'] = bval

    def cycle_quiescent_duration01_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_quiescent_duration01_fixed'] = bval
    def cycle_quiescent_duration10_fixed_clicked(self, bval):
        self.param_d[self.current_cell_def]['cycle_quiescent_duration10_fixed'] = bval

    #------------------------------
    # --- death
    def apoptosis_death_rate_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_death_rate'] = text

    def apoptosis_phase0_duration_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_phase0_duration'] = text
    def apoptosis_phase0_duration_fixed_toggled(self, b):
        self.param_d[self.current_cell_def]['apoptosis_phase0_fixed'] = b
    def apoptosis_trate01_changed(self, text):
        self.param_d[self.current_cell_def]["apoptosis_trate01"] = text
    def apoptosis_trate01_fixed_toggled(self, b):
        self.param_d[self.current_cell_def]['apoptosis_trate01_fixed'] = b

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
    def necrosis_phase0_duration_fixed_toggled(self, b):
        self.param_d[self.current_cell_def]['necrosis_phase0_fixed'] = b

    def necrosis_phase1_duration_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_phase1_duration'] = text
    def necrosis_trate01_changed(self, text):
        self.param_d[self.current_cell_def]["necrosis_trate01"] = text
    def necrosis_trate01_fixed_toggled(self, b):
        self.param_d[self.current_cell_def]['necrosis_trate01_fixed'] = b
    def necrosis_trate12_changed(self, text):
        self.param_d[self.current_cell_def]["necrosis_trate12"] = text
    def necrosis_trate12_fixed_toggled(self, b):
        self.param_d[self.current_cell_def]['necrosis_trate12_fixed'] = b

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
    def relative_maximum_adhesion_distance_changed(self, text):
        self.param_d[self.current_cell_def]['mechanics_adhesion_distance'] = text
    def set_relative_equilibrium_distance_changed(self, text):
        self.param_d[self.current_cell_def]['mechanics_relative_equilibrium_distance'] = text
    def set_absolute_equilibrium_distance_changed(self, text):
        self.param_d[self.current_cell_def]['mechanics_absolute_equilibrium_distance'] = text

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

    # --- custom data (rwh: OMG, this took a lot of time to solve!)
    def custom_data_value_changed(self, text):
        if not self.current_cell_def:
            return
        # print("self.sender() = ", self.sender())
        vname = self.sender().vname.text()
        # print("custom_data_value_changed(): vname = ", vname)
        if len(vname) == 0:
            return
        # print("\n THIS! ~~~~~~~~~~~ cell_def_tab.py: custom_data_value_changed(): vname = ",vname,", val = ", text)
        # populate: self.param_d[cell_def_name]['custom_data'] =  {'cvar1': '42.0', 'cvar2': '0.42', 'cvar3': '0.042'}
        # self.param_d[self.current_cell_def]['custom_data']['cvar1'] = text
        self.param_d[self.current_cell_def]['custom_data'][vname] = text
        # print(self.param_d[self.current_cell_def]['custom_data'])

    #--------------------------------------------------------
    def create_custom_data_tab(self):
        custom_data_tab = QWidget()
        glayout = QGridLayout()

        #=====  Custom data 
        # label = QLabel("Custom data")
        # label.setStyleSheet("background-color: cyan")

        #-------------------------
        # self.custom_data_controls_hbox = QHBoxLayout()
        # # self.new_button = QPushButton("New")
        # self.new_button = QPushButton("Append 5 more rows")
        # self.custom_data_controls_hbox.addWidget(self.new_button)
        # self.new_button.clicked.connect(self.append_more_cb)

        # self.clear_button = QPushButton("Clear selected rows")
        # self.custom_data_controls_hbox.addWidget(self.clear_button)
        # self.clear_button.clicked.connect(self.clear_rows_cb)

        #-------------------------
        # Fixed names for columns:
        hbox = QHBoxLayout()
        w = QLabel("Name(read only)")
        w.setAlignment(QtCore.Qt.AlignCenter)
        w.setStyleSheet("color: Salmon")  # PaleVioletRed")
        # hbox.addWidget(w)
        idr = 0
        glayout.addWidget(w, idr,0, 1,1) # w, row, column, rowspan, colspan

        # col2 = QtWidgets.QLabel("Type")
        # col2.setAlignment(QtCore.Qt.AlignCenter)
        # hbox.addWidget(col2)
        w = QLabel("Value (floating point)")
        w.setAlignment(QtCore.Qt.AlignCenter)
        # hbox.addWidget(w)
        glayout.addWidget(w, idr,1, 1,1) # w, row, column, rowspan, colspan
        
        # w = QLabel("Units(r/o)")
        # w.setAlignment(QtCore.Qt.AlignCenter)
        # w.setStyleSheet("color: Salmon")  # PaleVioletRed")
        # glayout.addWidget(w, idr,2, 1,1) # w, row, column, rowspan, colspan

        # glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan
        # idx = 0
        # glayout.addLayout(hbox, idx,0, 1,1) # w, row, column, rowspan, colspan

        # label.setFixedWidth(180)

        # self.vbox.addWidget(label)
        # self.vbox.addLayout(self.custom_data_controls_hbox)
        # self.vbox.addLayout(hbox)

        # Create lists for the various input boxes
        # TODO! Need lists for each cell type too.
        # self.custom_data_select = []
        self.custom_data_name = []
        self.custom_data_value = []
        # self.custom_data_units = []

        for idx in range(self.max_custom_data_rows):   # rwh/TODO - this should depend on how many in the .xml
            # self.main_layout.addLayout(NewUserParam(self))
            # hbox = QHBoxLayout()
            # w = QCheckBox("")
            # self.custom_data_select.append(w)
            # hbox.addWidget(w)

            w_varname = QLineEdit()
            w_varname.setStyleSheet("background-color: Salmon")  # PaleVioletRed")
            w_varname.setReadOnly(True)
            self.custom_data_name.append(w_varname)
            idr += 1
            glayout.addWidget(w_varname, idr,0, 1,1) # w, row, column, rowspan, colspan

            w = MyQLineEdit()  # using an overloaded class to allow the connection to the custom data variable name!!!
            w.setValidator(QtGui.QDoubleValidator())
            w.vname = w_varname
            w.textChanged[str].connect(self.custom_data_value_changed)  # being explicit about passing a string 
            self.custom_data_value.append(w)
            glayout.addWidget(w, idr,1, 1,1) # w, row, column, rowspan, colspan

            # w = QLineEdit()
            # w.setStyleSheet("background-color: Salmon")  # PaleVioletRed")
            # w.setReadOnly(True)
            # w.setFixedWidth(self.custom_data_units_width)
            # self.custom_data_units.append(w)
            # glayout.addWidget(w, idr,2, 1,1) # w, row, column, rowspan, colspan

            # glayout.addLayout(hbox, idx,0, 1,1) # w, row, column, rowspan, colspan

            # units = QtWidgets.QLabel("micron^2/min")
            # units.setFixedWidth(self.units_width)
            # hbox.addWidget(units)

#            self.vbox.addLayout(hbox)

            # self.vbox.addLayout(hbox)
            # self.vbox.addLayout(hbox)
            self.custom_data_count = self.custom_data_count + 1


        #==================================================================
        # compare with config_tab.py
        # self.config_params.setLayout(self.vbox)

        # self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        # self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        # self.scroll.setWidgetResizable(True)

        # self.scroll.setWidget(self.config_params) # self.config_params = QWidget()

        # self.layout = QVBoxLayout(self)

        # self.layout.addWidget(self.scroll)

        #===============
        # self.params_cell_def.setLayout(self.vbox)

        self.scroll_params.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_params.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_params.setWidgetResizable(True)

        # self.scroll_params.setWidget(self.params_cell_def)
        self.scroll_params.setWidget(self.tab_widget) # self.tab_widget = QTabWidget()


        # self.save_button = QPushButton("Save")
        # self.text = QLabel("Hello World",alignment=QtCore.Qt.AlignCenter)

        self.layout = QVBoxLayout(self)
        # self.layout.addStretch(1)

        # self.layout.addWidget(self.tabs)
        # self.layout.addWidget(self.params)

        self.layout.addLayout(self.controls_hbox)
        # self.layout.addLayout(self.name_hbox)
        # self.layout.addLayout(self.cell_types_tabs_layout)
        # self.layout.addWidget(self.tab_widget)

        # self.layout.addWidget(self.scroll)
        self.layout.addWidget(self.splitter)

        # self.layout.addWidget(self.vbox)
        # self.layout.addWidget(self.text)

        # self.layout.addWidget(self.save_button)
        # self.save_button.clicked.connect(self.save_xml)

        #------
        for idx in range(5):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idr += 1
            glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan

        #------
        # vlayout.setVerticalSpacing(10)  # rwh - argh
        custom_data_tab.setLayout(glayout)
        return custom_data_tab

    #--------------------------------------------------------
    # TODO: fix this; not working yet (and not called)
    def append_more_custom_data(self):
        print("---- append_more_custom_data()")
        for idx in range(5):
            w_varname = QLineEdit()
            w_varname.setStyleSheet("background-color: Salmon")  # PaleVioletRed")
            w_varname.setReadOnly(True)
            self.custom_data_name.append(w_varname)
            idr += 1
            glayout.addWidget(w_varname, idr,0, 1,1) # w, row, column, rowspan, colspan

            w = MyQLineEdit()  # using an overloaded class to allow the connection to the custom data variable name!!!
            w.setValidator(QtGui.QDoubleValidator())
            w.vname = w_varname
            w.textChanged[str].connect(self.custom_data_value_changed)  # being explicit about passing a string 
            self.custom_data_value.append(w)
            glayout.addWidget(w, idr,1, 1,1) # w, row, column, rowspan, colspan

            # self.main_layout.addLayout(hbox)

            self.custom_data_count = self.custom_data_count + 1
            print("self.custom_data_count = ",self.custom_data_count)

    #--------------------------------------------------------
    def clear_custom_data_tab(self):
        print("\n\n------- cell_def_tab.py: clear_custom_data_tab(self):  self.custom_data_count = ",self.custom_data_count)
        for idx in range(self.custom_data_count):
            self.custom_data_name[idx].setReadOnly(False)  # turn off read-only so we can change it. ugh.
            self.custom_data_name[idx].setText("")  # beware this triggering a callback
            self.custom_data_name[idx].setReadOnly(True)

            self.custom_data_value[idx].setText("") # triggering a callback)  # beware thiis 

            # self.custom_data_units[idx].setReadOnly(False)
            # self.custom_data_units[idx].setText("")
            # self.custom_data_units[idx].setReadOnly(True)
        
        self.custom_data_count = 0

    #--------------------------------------------------------
    # This is done in cell_custom_data_tab.py: fill_gui() 
    def fill_custom_data_tab(self):
    #     pass
        # uep_custom_data = self.xml_root.find(".//cell_definitions//cell_definition[1]//custom_data")
        uep_cell_defs = self.xml_root.find(".//cell_definitions")
        # print('--- cell_def_tab.py: fill_custom_data_tab(): uep_cell_defs= ',uep_cell_defs )

        idx = 0
        # rwh/TODO: if we have more vars than we initially created rows for, we'll need
        # to call 'append_more_cb' for the excess.

        # Should we also update the Cell Types | Custom Data tab entries?

        # for idx in range(self.custom_data_count):
        #     self.custom_data_name[idx].setReadOnly(False)
        #     self.custom_data_name[idx].setText("")
        #     self.custom_data_name[idx].setReadOnly(True)

        #     self.custom_data_value[idx].setText("")

        #     self.custom_data_units[idx].setReadOnly(False)
        #     self.custom_data_units[idx].setText("")
        #     self.custom_data_units[idx].setReadOnly(True)

        idx_cell_def = 0
        for cell_def in uep_cell_defs:
            uep_custom_data = uep_cell_defs.find(".//cell_definition[" + str(idx_cell_def+1) + "]//custom_data")  # 1-offset
            for var in uep_custom_data:
                # print(idx, ") ",var)
                self.custom_data_name[idx].setText(var.tag)
                # print("tag=",var.tag)
                self.custom_data_value[idx].setText(var.text)

                # if 'units' in var.keys():
                #     self.custom_data_units[idx].setText(var.attrib['units'])
                idx += 1
            idx_cell_def += 1
            break


    #-----------------------------------------------------------
    # @QtCore.Slot()
    # def save_xml(self):
    #     # self.text.setText(random.choice(self.hello))
    #     pass


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
        # print('------ motility_substrate_changed_cb(): idx = ',idx)
        val = self.motility_substrate_dropdown.currentText()
        # print("   text = ",val)
        self.param_d[self.current_cell_def]["motility_chemotaxis_substrate"] = val
        # self.param_d[cell_def_name]["motility_chemotaxis_idx"] = idx

        if idx == -1:
            return

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
        print('cycle_phase_transition_cb: self.stacked_cycle.count()=', self.stacked_cycle.count())

        radioBtn = self.sender()
        if radioBtn.isChecked():
            print("--------- ",radioBtn.text())

        print("self.cycle_dropdown.currentText() = ",self.cycle_dropdown.currentText())
        # print("self.cycle_dropdown.currentIndex() = ",self.cycle_dropdown.currentIndex())

        # self.cycle_rows_vbox.clear()
        # if radioBtn.text().find("duration"):
        if "duration" in radioBtn.text():
            print('cycle_phase_transition_cb: --> duration')
            self.cycle_duration_flag = True
            self.customize_cycle_choices()
        else:  # transition rates
            print('cycle_phase_transition_cb: NOT duration')
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

        print("-- customize_cycle_choices(): index= ",self.cycle_dropdown.currentIndex())

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
        print('chemotaxis_direction_cb: ')

        radioBtn = self.sender()
        if radioBtn.isChecked():
            print("--------- ",radioBtn.text())  # towards, against
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
    #         self.custom_data_count = self.custom_data_count + 1
    #         print(self.custom_data_count)

    #-----------------------------------------------------------------------------------------
    # Fill them using the given model (the .xml)
    def fill_substrates_comboboxes(self):
        print("cell_def_tab.py: ------- fill_substrates_comboboxes")
        print("self.substrate_list = ",self.substrate_list)
        self.substrate_list.clear()  # rwh/todo: where/why/how is this list maintained?
        self.motility_substrate_dropdown.clear()
        self.secretion_substrate_dropdown.clear()
        uep = self.xml_root.find('.//microenvironment_setup')  # find unique entry point
        # vp = []   # pointers to <variable> nodes
        if uep:
            idx = 0
            for var in uep.findall('variable'):
                # vp.append(var)
                print(" --> ",var.attrib['name'])
                name = var.attrib['name']
                self.substrate_list.append(name)
                self.motility_substrate_dropdown.addItem(name)
                self.secretion_substrate_dropdown.addItem(name)
        print("cell_def_tab.py: ------- fill_substrates_comboboxes:  self.substrate_list = ",self.substrate_list)

    #-----------------------------------------------------------------------------------------
    # def delete_substrate_from_comboboxes(self, item_idx):
    def delete_substrate(self, item_idx):

        # 1) delete it from the comboboxes
        # print("------- delete_substrate_from_comboboxes: name=",name)
        # print("------- delete_substrate: index=",item_idx)
        subname = self.motility_substrate_dropdown.itemText(item_idx)
        print("        name = ", subname)
        self.substrate_list.remove(subname)
        # print("self.substrate_list = ",self.substrate_list)
        self.motility_substrate_dropdown.removeItem(item_idx)
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
            if subname in self.param_d[cdname]["secretion"]:
                del_key = self.param_d[cdname]["secretion"].pop(subname)
        # print("--- after deletion, param_d=  ",self.param_d[cdname]["secretion"])
        # print("\n--- after deletion, self.current_secretion_substrate=  ",self.current_secretion_substrate)

        # if old_name == self.current_secretion_substrate:
        #     self.current_secretion_substrate = new_name

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
        self.secretion_substrate_dropdown.addItem(substrate_name)

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
            if old_name == self.secretion_substrate_dropdown.itemText(idx):
                self.secretion_substrate_dropdown.setItemText(idx, new_name)

        # 2) update in the param_d dict
        for cdname in self.param_d.keys():  # for all cell defs, rename motility/chemotaxis and secretion substrate
            # print("--- cdname = ",cdname)
            # print("--- old: ",self.param_d[cdname]["secretion"])
            # print("--- new_name: ",new_name)
            self.param_d[cdname]["motility_chemotaxis_substrate"] = new_name
            self.param_d[cdname]["secretion"][new_name] = self.param_d[cdname]["secretion"].pop(old_name)
            # print("--- new: ",self.param_d[cdname]["secretion"])

        if old_name == self.current_secretion_substrate:
            self.current_secretion_substrate = new_name

    #-----------------------------------------------------------------------------------------
    def new_cycle_params(self, cdname):
        # cdname = self.current_cell_def
        sval = self.default_sval
        self.param_d[cdname]['cycle_choice_idx'] = 0

        self.param_d[cdname]['cycle_live_trate00'] = sval

        self.param_d[cdname]['cycle_Ki67_trate01'] = sval
        self.param_d[cdname]['cycle_Ki67_trate10'] = sval

        self.param_d[cdname]['cycle_advancedKi67_trate01'] = sval
        self.param_d[cdname]['cycle_advancedKi67_trate12'] = sval
        self.param_d[cdname]['cycle_advancedKi67_trate20'] = sval

        self.param_d[cdname]['cycle_flowcyto_trate01'] = sval
        self.param_d[cdname]['cycle_flowcyto_trate12'] = sval
        self.param_d[cdname]['cycle_flowcyto_trate20'] = sval

        self.param_d[cdname]['cycle_flowcytosep_trate01'] = sval
        self.param_d[cdname]['cycle_flowcytosep_trate12'] = sval
        self.param_d[cdname]['cycle_flowcytosep_trate23'] = sval
        self.param_d[cdname]['cycle_flowcytosep_trate30'] = sval

        self.param_d[cdname]['cycle_quiescent_trate01'] = sval
        self.param_d[cdname]['cycle_quiescent_trate10'] = sval

        # duration times
        self.param_d[cdname]['cycle_live_duration00'] = sval

        self.param_d[cdname]['cycle_Ki67_duration01'] = sval
        self.param_d[cdname]['cycle_Ki67_duration10'] = sval

        self.param_d[cdname]['cycle_advancedKi67_duration01'] = sval
        self.param_d[cdname]['cycle_advancedKi67_duration12'] = sval
        self.param_d[cdname]['cycle_advancedKi67_duration20'] = sval

        self.param_d[cdname]['cycle_flowcyto_duration01'] = sval
        self.param_d[cdname]['cycle_flowcyto_duration12'] = sval
        self.param_d[cdname]['cycle_flowcyto_duration20'] = sval

        self.param_d[cdname]['cycle_flowcytosep_duration01'] = sval
        self.param_d[cdname]['cycle_flowcytosep_duration12'] = sval
        self.param_d[cdname]['cycle_flowcytosep_duration23'] = sval
        self.param_d[cdname]['cycle_flowcytosep_duration30'] = sval

        self.param_d[cdname]['cycle_quiescent_duration01'] = sval
        self.param_d[cdname]['cycle_quiescent_duration10'] = sval


        #-------------------------
        # transition rates "fixed"

        bval = self.default_bval
        self.param_d[cdname]['cycle_live_trate00_fixed'] = bval

        self.param_d[cdname]['cycle_Ki67_trate01_fixed'] = bval
        self.param_d[cdname]['cycle_Ki67_trate10_fixed'] = bval

        self.param_d[cdname]['cycle_advancedKi67_trate01_fixed'] = bval
        self.param_d[cdname]['cycle_advancedKi67_trate12_fixed'] = bval
        self.param_d[cdname]['cycle_advancedKi67_trate20_fixed'] = bval

        self.param_d[cdname]['cycle_flowcyto_trate01_fixed'] = bval
        self.param_d[cdname]['cycle_flowcyto_trate12_fixed'] = bval
        self.param_d[cdname]['cycle_flowcyto_trate20_fixed'] = bval

        self.param_d[cdname]['cycle_flowcytosep_trate01_fixed'] = bval
        self.param_d[cdname]['cycle_flowcytosep_trate12_fixed'] = bval
        self.param_d[cdname]['cycle_flowcytosep_trate23_fixed'] = bval
        self.param_d[cdname]['cycle_flowcytosep_trate30_fixed'] = bval

        self.param_d[cdname]['cycle_quiescent_trate01_fixed'] = bval
        self.param_d[cdname]['cycle_quiescent_trate10_fixed'] = bval


        #------ duration times "fixed"
        self.param_d[cdname]['cycle_live_duration00_fixed'] = bval

        self.param_d[cdname]['cycle_Ki67_duration01_fixed'] = bval
        self.param_d[cdname]['cycle_Ki67_duration10_fixed'] = bval

        self.param_d[cdname]['cycle_advancedKi67_duration01_fixed'] = bval
        self.param_d[cdname]['cycle_advancedKi67_duration12_fixed'] = bval
        self.param_d[cdname]['cycle_advancedKi67_duration20_fixed'] = bval

        self.param_d[cdname]['cycle_flowcyto_duration01_fixed'] = bval
        self.param_d[cdname]['cycle_flowcyto_duration12_fixed'] = bval
        self.param_d[cdname]['cycle_flowcyto_duration20_fixed'] = bval

        self.param_d[cdname]['cycle_flowcytosep_duration01_fixed'] = bval
        self.param_d[cdname]['cycle_flowcytosep_duration12_fixed'] = bval
        self.param_d[cdname]['cycle_flowcytosep_duration23_fixed'] = bval
        self.param_d[cdname]['cycle_flowcytosep_duration30_fixed'] = bval

        self.param_d[cdname]['cycle_quiescent_duration01_fixed'] = bval
        self.param_d[cdname]['cycle_quiescent_duration10_fixed'] = bval


    def new_death_params(self, cdname):
        sval = self.default_sval
        self.param_d[cdname]["death_rate"] = sval
        self.param_d[cdname]["apoptosis_death_rate"] = sval
        self.param_d[cdname]["apoptosis_phase0_duration"] = sval
        self.param_d[cdname]["apoptosis_phase0_fixed"] = False

        self.param_d[cdname]["apoptosis_unlysed_rate"] = sval
        self.param_d[cdname]["apoptosis_lysed_rate"] = sval
        self.param_d[cdname]["apoptosis_cyto_rate"] = sval
        self.param_d[cdname]["apoptosis_nuclear_rate"] = sval
        self.param_d[cdname]["apoptosis_calcif_rate"] = sval
        self.param_d[cdname]["apoptosis_rel_rupture_volume"] = sval

        #-----
        self.param_d[cdname]["necrosis_death_rate"] = sval
        self.param_d[cdname]["necrosis_phase0_duration"] = sval
        self.param_d[cdname]["necrosis_phase0_fixed"] = False
        self.param_d[cdname]["necrosis_phase1_duration"] = sval
        self.param_d[cdname]["necrosis_phase1_fixed"] = False

        self.param_d[cdname]["necrosis_unlysed_rate"] = sval
        self.param_d[cdname]["necrosis_lysed_rate"] = sval
        self.param_d[cdname]["necrosis_cyto_rate"] = sval
        self.param_d[cdname]["necrosis_nuclear_rate"] = sval
        self.param_d[cdname]["necrosis_calcif_rate"] = sval
        self.param_d[cdname]["necrosis_rel_rupture_rate"] = sval

    def new_volume_params(self, cdname):
        sval = self.default_sval
        self.param_d[cdname]["volume_total"] = sval
        self.param_d[cdname]["volume_fluid_fraction"] = sval
        self.param_d[cdname]["volume_nuclear"] = sval
        self.param_d[cdname]["volume_fluid_change_rate"] = sval
        self.param_d[cdname]["volume_cytoplasmic_rate"] = sval
        self.param_d[cdname]["volume_nuclear_rate"] = sval
        self.param_d[cdname]["volume_calcif_fraction"] = sval
        self.param_d[cdname]["volume_calcif_rate"] = sval
        self.param_d[cdname]["volume_rel_rupture_vol"] = sval

    def new_mechanics_params(self, cdname):
        sval = self.default_sval
        self.param_d[cdname]["mechanics_adhesion"] = sval
        self.param_d[cdname]["mechanics_repulsion"] = sval
        self.param_d[cdname]["mechanics_adhesion_distance"] = sval

        self.param_d[cdname]["mechanics_relative_equilibrium_distance"] = sval
        self.param_d[cdname]["mechanics_absolute_equilibrium_distance"] = sval

        self.param_d[cdname]["mechanics_relative_equilibrium_distance_enabled"] = False
        self.param_d[cdname]["mechanics_absolute_equilibrium_distance_enabled"] = False

    def new_motility_params(self, cdname):
        sval = self.default_sval
        self.param_d[cdname]["speed"] = sval
        self.param_d[cdname]["persistence_time"] = sval
        self.param_d[cdname]["migration_bias"] = sval

        self.param_d[cdname]["motility_enabled"] = False
        self.param_d[cdname]["motility_use_2D"] = True
        self.param_d[cdname]["motility_chemotaxis"] = False

        # self.motility_substrate_dropdown.setCurrentText(self.param_d[self.current_cell_def]["motility_chemotaxis_substrate"])
        # self.param_d[self.current_cell_def]["motility_chemotaxis_substrate"] = sval

        self.param_d[cdname]["motility_chemotaxis_towards"] = True

    # todo: fix this (currently we don't call it because it clears the previously selected cell def's values)
    # def new_secretion_params(self, cdname):
    #     sval = self.default_sval
    #     self.param_d[cdname]["secretion"][self.current_secretion_substrate]["secretion_rate"] = sval
    #     self.param_d[cdname]["secretion"][self.current_secretion_substrate]["secretion_target"] = sval
    #     self.param_d[cdname]["secretion"][self.current_secretion_substrate]["uptake_rate"] = sval
    #     self.param_d[cdname]["secretion"][self.current_secretion_substrate]["net_export_rate"] = sval


    def add_new_substrate(self, sub_name):
        self.add_new_substrate_comboboxes(sub_name)


        sval = self.default_sval
        for cdname in self.param_d.keys():  # for all cell defs, initialize secretion params
            # print('cdname = ',cdname)
            # # print(self.param_d[cdname]["secretion"])
            self.param_d[cdname]["secretion"][sub_name] = {}
            self.param_d[cdname]["secretion"][sub_name]["secretion_rate"] = sval
            self.param_d[cdname]["secretion"][sub_name]["secretion_target"] = sval
            self.param_d[cdname]["secretion"][sub_name]["uptake_rate"] = sval
            self.param_d[cdname]["secretion"][sub_name]["net_export_rate"] = sval


    def new_custom_data_params(self, cdname):
        print("------- new_custom_data_params() -----")
        sval = self.default_sval
        num_vals = len(self.param_d[cdname]['custom_data'].keys())
        print("num_vals =", num_vals)
        idx = 0
        for key in self.param_d[cdname]['custom_data'].keys():
            print(key,self.param_d[cdname]['custom_data'][key])
            # self.custom_data_name[idx].setText(key)
            self.param_d[cdname]['custom_data'][key] = sval
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
        self.relative_maximum_adhesion_distance.setText(self.param_d[cdname]["mechanics_adhesion_distance"])

        self.set_relative_equilibrium_distance.setText(self.param_d[cdname]["mechanics_relative_equilibrium_distance"])
        self.set_absolute_equilibrium_distance.setText(self.param_d[cdname]["mechanics_absolute_equilibrium_distance"])

        self.set_relative_equilibrium_distance_enabled.setChecked(self.param_d[cdname]["mechanics_relative_equilibrium_distance_enabled"])
        self.set_absolute_equilibrium_distance_enabled.setChecked(self.param_d[cdname]["mechanics_absolute_equilibrium_distance_enabled"])


    #-----------------------------------------------------------------------------------------
    def update_motility_params(self):
        cdname = self.current_cell_def
        self.speed.setText(self.param_d[cdname]["speed"])
        self.persistence_time.setText(self.param_d[cdname]["persistence_time"])
        self.migration_bias.setText(self.param_d[cdname]["migration_bias"])

        self.motility_enabled.setChecked(self.param_d[cdname]["motility_enabled"])
        self.motility_use_2D.setChecked(self.param_d[cdname]["motility_use_2D"])
        self.chemotaxis_enabled.setChecked(self.param_d[cdname]["motility_chemotaxis"])
        self.motility_substrate_dropdown.setCurrentText(self.param_d[self.current_cell_def]["motility_chemotaxis_substrate"])

        if self.param_d[cdname]["motility_chemotaxis_towards"]:
            self.chemotaxis_direction_towards.setChecked(True)
        else:
            self.chemotaxis_direction_against.setChecked(True)

    #-----------------------------------------------------------------------------------------
    def update_secretion_params(self):
        cdname = self.current_cell_def
        self.secretion_rate.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["secretion_rate"])
        self.secretion_target.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["secretion_target"])
        self.uptake_rate.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["uptake_rate"])
        self.secretion_net_export_rate.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["net_export_rate"])

    #-----------------------------------------------------------------------------------------
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
            # idx += 1

    #-----------------------------------------------------------------------------------------
    def update_custom_data_params(self):
        cdname = self.current_cell_def
        # print("\n--------- cell_def_tab.py: update_custom_data_params():  cdname= ",cdname)
        # print("\n--------- cell_def_tab.py: update_custom_data_params():  self.param_d[cdname]['custom_data'] = ",self.param_d[cdname]['custom_data'])
        num_vals = len(self.param_d[cdname]['custom_data'].keys())
        # print("num_vals =", num_vals)
        idx = 0
        for key in self.param_d[cdname]['custom_data'].keys():
            # print("cell_def_tab.py: update_custom_data_params(): ",key,self.param_d[cdname]['custom_data'][key])
            if len(key) > 0:  # probably not necessary anymore
                self.custom_data_name[idx].setText(key)
                self.custom_data_value[idx].setText(self.param_d[cdname]['custom_data'][key])
                # print("\n THIS~~~~~~~~~ cell_def_tab.py: update_custom_data_params(): ",key,self.param_d[cdname]['custom_data'][key])
            idx += 1

        # print('idx=',idx)
        for jdx in range(idx,self.max_custom_data_rows):
            self.custom_data_name[jdx].setText('')
            self.custom_data_value[jdx].setText('')
        # jdx = 0
        # for var in uep_custom_data:
        #     print(jdx, ") ",var)
        #     self.custom_data_name[jdx].setText(var.tag)

    #-----------------------------------------------------------------------------------------
    # User selects a cell def from the tree on the left. We need to fill in ALL widget values from param_d
    def tree_item_clicked_cb(self, it,col):
        # print('\n\n------------ tree_item_clicked_cb -----------:', it, col, it.text(col) )
        self.current_cell_def = it.text(col)
        # print('--- self.current_cell_def= ',self.current_cell_def )

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
        # self.update_molecular_params()
        self.update_custom_data_params()


    #-------------------------------------------------------------------
    # Parse the .xml, populate the dict of params (self.param_d) and self.tree
    def populate_tree(self):
        print("=======================  cell_def populate_tree  ======================= ")
        uep = self.xml_root.find(".//cell_definitions")
        if uep:
            self.tree.clear()
            idx = 0
            for cell_def in uep:
                # print(cell_def.attrib['name'])
                cell_def_name = cell_def.attrib['name']
                if idx == 0:
                    cell_def_0th = cell_def_name

                self.param_d[cell_def_name] = {}
                # self.param_d[cell_def_name]["name"] = cell_def_name
                self.current_cell_def = cell_def_name  # do this for the callback methods?

                cellname = QTreeWidgetItem([cell_def_name])
                cellname.setFlags(cellname.flags() | QtCore.Qt.ItemIsEditable)
                self.tree.insertTopLevelItem(idx,cellname)
                if idx == 0:  # select the 1st (0th) entry
                    self.tree.setCurrentItem(cellname)

                idx += 1

                # Now fill the param dict for each substrate and the Qt widget values for the 0th

                print("\n===== populate():  cycle")

                cycle_path = ".//cell_definition[" + str(idx) + "]//phenotype//cycle"
                print(" >> cycle_path=",cycle_path)
                cycle_code = int(uep.find(cycle_path).attrib['code'])
                print("   cycle code=",cycle_code)

                # NOTE: we don't seem to use 3 or 4
                # static const int advanced_Ki67_cycle_model= 0;
                # static const int basic_Ki67_cycle_model=1;
                # static const int flow_cytometry_cycle_model=2;
                # static const int live_apoptotic_cycle_model=3;
                # static const int total_cells_cycle_model=4;
                # static const int live_cells_cycle_model = 5; 
                # static const int flow_cytometry_separated_cycle_model = 6; 
                # static const int cycling_quiescent_model = 7; 

                # self.cycle_dropdown.addItem("live cells")  # 5
                # self.cycle_dropdown.addItem("basic Ki67")  # 1
                # self.cycle_dropdown.addItem("advanced Ki67")  # 0
                # self.cycle_dropdown.addItem("flow cytometry")  # 2
                # self.cycle_dropdown.addItem("flow cytometry separated")  # 6
                # self.cycle_dropdown.addItem("cycling quiescent")  # 7

                if cycle_code == 0:
                    self.cycle_dropdown.setCurrentIndex(2)
                    self.param_d[cell_def_name]['cycle'] = 'advanced Ki67'
                elif cycle_code == 1:
                    self.cycle_dropdown.setCurrentIndex(1)
                    self.param_d[cell_def_name]['cycle'] = 'basic Ki67'
                elif cycle_code == 2:
                    self.cycle_dropdown.setCurrentIndex(3)
                    self.param_d[cell_def_name]['cycle'] = 'flow cytometry'
                elif cycle_code == 5:
                    self.cycle_dropdown.setCurrentIndex(0)
                    self.param_d[cell_def_name]['cycle'] = 'live cells'
                elif cycle_code == 6:
                    self.cycle_dropdown.setCurrentIndex(4)
                    self.param_d[cell_def_name]['cycle'] = 'flow cytometry separated'
                elif cycle_code == 7:
                    self.cycle_dropdown.setCurrentIndex(5)
                    self.param_d[cell_def_name]['cycle'] = 'cycling quiescent'

                self.param_d[cell_def_name]['cycle_choice_idx'] = self.cycle_dropdown.currentIndex()

            # rwh: We only use cycle code=5 or 6 in ALL sample projs?!
                # <cell_definition name="cargo cell" ID="2" visible="true">
                # 	<phenotype>
                # 		<cycle code="5" name="live">  
                # 			<phase_transition_rates units="1/min"> 
                # 				<rate start_index="0" end_index="0" fixed_duration="false">0.0</rate>
                # 			</phase_transition_rates>

                # <cycle code="6" name="Flow cytometry model (separated)">  
				# 	<phase_transition_rates units="1/min"> 
				# 		<rate start_index="0" end_index="1" fixed_duration="false">0</rate>
				# 		<rate start_index="1" end_index="2" fixed_duration="true">0.00208333</rate>
				# 		<rate start_index="2" end_index="3" fixed_duration="true">0.00416667</rate>
				# 		<rate start_index="3" end_index="0" fixed_duration="true">0.0166667</rate>


                #  transition rates: set default values for all params
                default_sval = '0.0'
                self.param_d[cell_def_name]['cycle_live_trate00'] = default_sval

                self.param_d[cell_def_name]['cycle_Ki67_trate01'] = default_sval
                self.param_d[cell_def_name]['cycle_Ki67_trate10'] = default_sval

                self.param_d[cell_def_name]['cycle_advancedKi67_trate01'] = default_sval
                self.param_d[cell_def_name]['cycle_advancedKi67_trate12'] = default_sval
                self.param_d[cell_def_name]['cycle_advancedKi67_trate20'] = default_sval

                self.param_d[cell_def_name]['cycle_flowcyto_trate01'] = default_sval
                self.param_d[cell_def_name]['cycle_flowcyto_trate12'] = default_sval
                self.param_d[cell_def_name]['cycle_flowcyto_trate20'] = default_sval

                self.param_d[cell_def_name]['cycle_flowcytosep_trate01'] = default_sval
                self.param_d[cell_def_name]['cycle_flowcytosep_trate12'] = default_sval
                self.param_d[cell_def_name]['cycle_flowcytosep_trate23'] = default_sval
                self.param_d[cell_def_name]['cycle_flowcytosep_trate30'] = default_sval

                self.param_d[cell_def_name]['cycle_quiescent_trate01'] = default_sval
                self.param_d[cell_def_name]['cycle_quiescent_trate10'] = default_sval


                #  transition rates: set default values for all "fixed_duration" checkboxes
                default_bval = False
                self.param_d[cell_def_name]['cycle_live_trate00_fixed'] = default_bval

                self.param_d[cell_def_name]['cycle_Ki67_trate01_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_Ki67_trate10_fixed'] = default_bval

                self.param_d[cell_def_name]['cycle_advancedKi67_trate01_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_advancedKi67_trate12_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_advancedKi67_trate20_fixed'] = default_bval

                self.param_d[cell_def_name]['cycle_flowcyto_trate01_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_flowcyto_trate12_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_flowcyto_trate20_fixed'] = default_bval

                self.param_d[cell_def_name]['cycle_flowcytosep_trate01_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_flowcytosep_trate12_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_flowcytosep_trate23_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_flowcytosep_trate30_fixed'] = default_bval

                self.param_d[cell_def_name]['cycle_quiescent_trate01_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_quiescent_trate10_fixed'] = default_bval

                phase_transition_path = cycle_path + "//phase_transition_rates"
                print(' >> phase_transition_path ')
                pt_uep = uep.find(phase_transition_path)
                if pt_uep:
                    self.cycle_rb1.setChecked(True)
                    self.param_d[cell_def_name]['cycle_duration_flag'] = False
                    self.cycle_duration_flag = False
                    self.customize_cycle_choices()

                    for rate in pt_uep: 
                        print(rate)
                        # print("start_index=",rate.attrib["start_index"])
                        # We only use cycle code=5 or 6 in ALL sample projs?

                        # if cycle_code == 0: #'advanced Ki67'
                        # elif cycle_code == 1: # 'basic Ki67'
                        # elif cycle_code == 2: # 'flow cytometry'
                        # elif cycle_code == 5: # 'live cells'
                        # elif cycle_code == 6: # 'flow cytometry separated'
                        # elif cycle_code == 7: # 'cycling quiescent'

                        sval = rate.text
                        if (rate.attrib['start_index'] == "0"): 
                            if (rate.attrib['end_index'] == "0"): #  Must be 'live'
                                print('--  cycle_live_trate00',  sval)
                                self.param_d[cell_def_name]['cycle_live_trate00'] = rate.text
                                if (rate.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_live_trate00_fixed'] = True
                            elif (rate.attrib['end_index'] == "1"): 
                                if cycle_code == 0: #'advanced Ki67'
                                    self.param_d[cell_def_name]['cycle_advancedKi67_trate01'] = sval
                                    if (rate.attrib['fixed_duration'].lower() == "true"): 
                                        self.param_d[cell_def_name]['cycle_advancedKi67_trate01_fixed'] = True
                                elif cycle_code == 1: # 'basic Ki67'
                                    self.param_d[cell_def_name]['cycle_Ki67_trate01'] = sval
                                    if (rate.attrib['fixed_duration'].lower() == "true"): 
                                        self.param_d[cell_def_name]['cycle_Ki67_trate01_fixed'] = True
                                elif cycle_code == 2: # 'flow cytometry'
                                    self.param_d[cell_def_name]['cycle_flowcyto_trate01'] = sval
                                    if (rate.attrib['fixed_duration'].lower() == "true"): 
                                        self.param_d[cell_def_name]['cycle_flowcyto_trate01_fixed'] = True
                                elif cycle_code == 6: # 'flow cytometry separated'
                                    self.param_d[cell_def_name]['cycle_flowcytosep_trate01'] = sval
                                    if (rate.attrib['fixed_duration'].lower() == "true"): 
                                        self.param_d[cell_def_name]['cycle_flowcytosep_trate01_fixed'] = True
                                elif cycle_code == 7: # 'cycling quiescent'
                                    self.param_d[cell_def_name]['cycle_quiescent_trate01'] = sval
                                    if (rate.attrib['fixed_duration'].lower() == "true"): 
                                        self.param_d[cell_def_name]['cycle_quiescent_trate01_fixed'] = True

                        elif (rate.attrib['start_index'] == "1"):
                            if (rate.attrib['end_index'] == "0"):  # must be 'basic Ki67'
                                self.param_d[cell_def_name]['cycle_Ki67_trate10'] = sval
                                if (rate.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_Ki67_trate10_fixed'] = True

                            elif (rate.attrib['end_index'] == "2"):
                                if cycle_code == 0: #'advanced Ki67'
                                    self.param_d[cell_def_name]['cycle_advancedKi67_trate12'] = sval
                                    if (rate.attrib['fixed_duration'].lower() == "true"): 
                                        self.param_d[cell_def_name]['cycle_advancedKi67_trate12_fixed'] = True
                                elif cycle_code == 2: # 'flow cytometry'
                                    self.param_d[cell_def_name]['cycle_flowcyto_trate12'] = sval
                                    if (rate.attrib['fixed_duration'].lower() == "true"): 
                                        self.param_d[cell_def_name]['cycle_flowcyto_trate12_fixed'] = True
                                elif cycle_code == 6: # 'flow cytometry separated'
                                    self.param_d[cell_def_name]['cycle_flowcytosep_trate12'] = sval
                                    if (rate.attrib['fixed_duration'].lower() == "true"): 
                                        self.param_d[cell_def_name]['cycle_flowcytosep_trate12_fixed'] = True
                                elif cycle_code == 7: # 'cycling quiescent'
                                    self.param_d[cell_def_name]['cycle_quiescent_trate12'] = sval
                                    if (rate.attrib['fixed_duration'].lower() == "true"): 
                                        self.param_d[cell_def_name]['cycle_quiescent_trate12_fixed'] = True

                        elif (rate.attrib['start_index'] == "2"):
                            if (rate.attrib['end_index'] == "0"):
                                if cycle_code == 0: #'advanced Ki67'
                                    self.param_d[cell_def_name]['cycle_advancedKi67_trate20'] = sval
                                    if (rate.attrib['fixed_duration'].lower() == "true"): 
                                        self.param_d[cell_def_name]['cycle_advancedKi67_trate20_fixed'] = True
                                elif cycle_code == 2: # 'flow cytometry'
                                    self.param_d[cell_def_name]['cycle_flowcyto_trate20'] = sval
                                    if (rate.attrib['fixed_duration'].lower() == "true"): 
                                        self.param_d[cell_def_name]['cycle_flowcyto_trate20_fixed'] = True

                            elif (rate.attrib['end_index'] == "3"):
                                # if cycle_code == 6: # 'flow cytometry separated'
                                self.param_d[cell_def_name]['cycle_flowcytosep_trate23'] = sval
                                if (rate.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_flowcytosep_trate23_fixed'] = True

                        elif (rate.attrib['start_index'] == "3") and (rate.attrib['end_index'] == "0"):
                            # self.cycle_flowcytosep_trate30.setText(rate.text)
                            self.param_d[cell_def_name]['cycle_flowcytosep_trate30'] = rate.text
                            if (rate.attrib['fixed_duration'].lower() == "true"): 
                                self.param_d[cell_def_name]['cycle_flowcytosep_trate30_fixed'] = True


                # template.xml:
                # <cycle code="6" name="Flow cytometry model (separated)">  
                #     <phase_durations units="min"> 
                #         <duration index="0" fixed_duration="false">300.0</duration>
                #         <duration index="1" fixed_duration="true">480</duration>
                #         <duration index="2" fixed_duration="true">240</duration>
                #         <duration index="3" fixed_duration="true">60</duration>
                #     </phase_durations>
                #
                # self.phase0_duration = QLineEdit()
                default_sval = '0.0'

                #  duration times: set default values for all params
                        # self.cycle_live_duration00 = QLineEdit()
                        # self.cycle_Ki67_duration01 = QLineEdit()
                        # self.cycle_Ki67_duration10 = QLineEdit()
                        # self.cycle_advancedKi67_duration01 = QLineEdit()
                        # self.cycle_advancedKi67_duration12 = QLineEdit()
                        # self.cycle_advancedKi67_duration20 = QLineEdit()
                        # self.cycle_flowcyto_duration01 = QLineEdit()
                        # self.cycle_flowcyto_duration12 = QLineEdit()
                        # self.cycle_flowcyto_duration20 = QLineEdit()
                        # self.cycle_flowcytosep_duration01 = QLineEdit()
                        # self.cycle_flowcytosep_duration12 = QLineEdit()
                        # self.cycle_flowcytosep_duration23 = QLineEdit()
                        # self.cycle_flowcytosep_duration30 = QLineEdit()
                        # self.cycle_quiescent_duration01 = QLineEdit()
                        # self.cycle_quiescent_duration10 = QLineEdit()

                self.param_d[cell_def_name]['cycle_live_duration00'] = default_sval

                self.param_d[cell_def_name]['cycle_Ki67_duration01'] = default_sval
                self.param_d[cell_def_name]['cycle_Ki67_duration10'] = default_sval

                self.param_d[cell_def_name]['cycle_advancedKi67_duration01'] = default_sval
                self.param_d[cell_def_name]['cycle_advancedKi67_duration12'] = default_sval
                self.param_d[cell_def_name]['cycle_advancedKi67_duration20'] = default_sval

                self.param_d[cell_def_name]['cycle_flowcyto_duration01'] = default_sval
                self.param_d[cell_def_name]['cycle_flowcyto_duration12'] = default_sval
                self.param_d[cell_def_name]['cycle_flowcyto_duration20'] = default_sval

                self.param_d[cell_def_name]['cycle_flowcytosep_duration00'] = default_sval
                self.param_d[cell_def_name]['cycle_flowcytosep_duration01'] = default_sval
                self.param_d[cell_def_name]['cycle_flowcytosep_duration12'] = default_sval
                self.param_d[cell_def_name]['cycle_flowcytosep_duration23'] = default_sval
                self.param_d[cell_def_name]['cycle_flowcytosep_duration30'] = default_sval

                self.param_d[cell_def_name]['cycle_quiescent_duration01'] = default_sval
                self.param_d[cell_def_name]['cycle_quiescent_duration10'] = default_sval

                #  duration: set default values for all "fixed_duration" checkboxes
                default_bval = False
                self.param_d[cell_def_name]['cycle_live_duration00_fixed'] = default_bval

                self.param_d[cell_def_name]['cycle_Ki67_duration01_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_Ki67_duration10_fixed'] = default_bval

                self.param_d[cell_def_name]['cycle_advancedKi67_duration01_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_advancedKi67_duration12_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_advancedKi67_duration20_fixed'] = default_bval

                self.param_d[cell_def_name]['cycle_flowcyto_duration01_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_flowcyto_duration12_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_flowcyto_duration20_fixed'] = default_bval

                self.param_d[cell_def_name]['cycle_flowcytosep_duration01_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_flowcytosep_duration12_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_flowcytosep_duration23_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_flowcytosep_duration30_fixed'] = default_bval

                self.param_d[cell_def_name]['cycle_quiescent_duration01_fixed'] = default_bval
                self.param_d[cell_def_name]['cycle_quiescent_duration10_fixed'] = default_bval

                phase_durations_path = cycle_path + "//phase_durations"
                print(' >> phase_durations_path =',phase_durations_path )
                pd_uep = uep.find(phase_durations_path)
                print(' >> pd_uep =',pd_uep )
                if pd_uep:
                    self.cycle_rb2.setChecked(True)
                    self.param_d[cell_def_name]['cycle_duration_flag'] = True
                    self.cycle_duration_flag = True   # rwh: TODO - why do this??
                    self.customize_cycle_choices()

                # if cycle_code == 0: #'advanced Ki67'
                # elif cycle_code == 1: # 'basic Ki67'
                # elif cycle_code == 2: # 'flow cytometry'
                # elif cycle_code == 5: # 'live cells'
                # elif cycle_code == 6: # 'flow cytometry separated'
                # elif cycle_code == 7: # 'cycling quiescent'

                    for pd in pd_uep:   # phase_duration
                        print(pd)
                        # print("index=",pd.attrib["index"])
                        sval = pd.text

                        if (pd.attrib['index'] == "0"): 
                            if cycle_code == 0: #'advanced Ki67'
                                self.param_d[cell_def_name]['cycle_advancedKi67_duration01'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_advancedKi67_duration01_fixed'] = True
                            elif cycle_code == 1: # 'basic Ki67'
                                self.param_d[cell_def_name]['cycle_Ki67_duration01'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_Ki67_duration01_fixed'] = True
                            elif cycle_code == 2: # 'flow cytometry'
                                self.param_d[cell_def_name]['cycle_flowcyto_duration01'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_flowcyto_duration01_fixed'] = True
                            elif cycle_code == 5: # 'live'
                                self.param_d[cell_def_name]['cycle_live_duration00'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_live_duration00_fixed'] = True
                            elif cycle_code == 6: # 'flow cytometry separated'
                                self.param_d[cell_def_name]['cycle_flowcytosep_duration01'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_flowcytosep_duration01_fixed'] = True
                            elif cycle_code == 7: # 'cycling quiescent'
                                self.param_d[cell_def_name]['cycle_quiescent_duration01'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_quiescent_duration01_fixed'] = True

                        elif (pd.attrib['index'] == "1"):
                            if cycle_code == 0: #'advanced Ki67'
                                self.param_d[cell_def_name]['cycle_advancedKi67_duration12'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_advancedKi67_duration12_fixed'] = True
                            elif cycle_code == 1: #'basic Ki67'
                                self.param_d[cell_def_name]['cycle_Ki67_duration10'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_Ki67_duration10_fixed'] = True
                            elif cycle_code == 2: # 'flow cytometry'
                                self.param_d[cell_def_name]['cycle_flowcyto_duration12'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_flowcyto_duration12_fixed'] = True
                            elif cycle_code == 6: # 'flow cytometry separated'
                                self.param_d[cell_def_name]['cycle_flowcytosep_duration12'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_flowcytosep_duration12_fixed'] = True
                            elif cycle_code == 7: # 'cycling quiescent'
                                self.param_d[cell_def_name]['cycle_quiescent_duration10'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_quiescent_duration10_fixed'] = True

                        elif (pd.attrib['index'] == "2"):
                            if cycle_code == 0: #'advanced Ki67'
                                self.param_d[cell_def_name]['cycle_advancedKi67_duration20'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_advancedKi67_duration20_fixed'] = True
                            elif cycle_code == 2: # 'flow cytometry'
                                self.param_d[cell_def_name]['cycle_flowcyto_duration20'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_flowcyto_duration20_fixed'] = True
                            elif cycle_code == 6: # 'flow cytometry separated'
                                self.param_d[cell_def_name]['cycle_flowcytosep_duration23'] = sval
                                if (pd.attrib['fixed_duration'].lower() == "true"): 
                                    self.param_d[cell_def_name]['cycle_flowcytosep_duration23_fixed'] = True

                        elif (pd.attrib['index'] == "3"):
                            self.param_d[cell_def_name]['cycle_flowcytosep_duration30'] = sval
                            if (pd.attrib['fixed_duration'].lower() == "true"): 
                                self.param_d[cell_def_name]['cycle_flowcytosep_duration30_fixed'] = True


                # rf. microenv:
                # self.cell_type_name.setText(var.attrib['name'])
                # self.diffusion_coef.setText(vp[0].find('.//diffusion_coefficient').text)

                # ------------------ cell_definition: default
                # ---------  cycle (live)
                # self.float0.value = float(uep.find('.//cell_definition[1]//phenotype//cycle//phase_transition_rates//rate[1]').text)

                self.param_d[cell_def_name]['cycle_live_duration00'] = default_sval

                # ---------  death 
                print("\n===== populate():  death")

                        #------ using transition_rates
                        # <death> 
                        #   <model code="100" name="apoptosis"> 
                            #     <death_rate units="1/min">0</death_rate>  
                            #     <phase_transition_rates units="1/min">
                            #         <rate start_index="0" end_index="1" fixed_duration="true">0.00193798</rate>
                            #     </phase_transition_rates>
                            #     <parameters>
                            #         <unlysed_fluid_change_rate units="1/min">0.05</unlysed_fluid_change_rate>
                            #         <lysed_fluid_change_rate units="1/min">0</lysed_fluid_change_rate>
                            #         <cytoplasmic_biomass_change_rate units="1/min">1.66667e-02</cytoplasmic_biomass_change_rate>
                            #         <nuclear_biomass_change_rate units="1/min">5.83333e-03</nuclear_biomass_change_rate>
                            #         <calcification_rate units="1/min">0</calcification_rate>
                            #         <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>
                            #     </parameters>
                            # </model> 
                        #   <model code="101" name="necrosis">

                        #------ using durations
                        # <death>  
                        # 	<model code="100" name="apoptosis"> 
                        # 		<death_rate units="1/min">5.1e-05</death_rate>
                        # 		<phase_durations units="min">
                        # 			<duration index="0" fixed_duration="true">511</duration>
                        # 		</phase_durations>
                        # 		<parameters>
                        # 			<unlysed_fluid_change_rate units="1/min">0.01</unlysed_fluid_change_rate>
                        # 			<lysed_fluid_change_rate units="1/min">1.e-99</lysed_fluid_change_rate>
                        # 			<cytoplasmic_biomass_change_rate units="1/min">1.61e-02</cytoplasmic_biomass_change_rate>
                        # 			<nuclear_biomass_change_rate units="1/min">5.81e-03</nuclear_biomass_change_rate>
                        # 			<calcification_rate units="1/min">0</calcification_rate>
                        # 			<relative_rupture_volume units="dimensionless">2.1</relative_rupture_volume>
                        # 		</parameters>
                        # 	</model> 

                        # 	<model code="101" name="necrosis">
                        # 		<death_rate units="1/min">0.1</death_rate>
                        # 		<phase_durations units="min">
                        # 			<duration index="0" fixed_duration="true">0.1</duration>
                        # 			<duration index="1" fixed_duration="true">86400.1</duration>
                        # 		</phase_durations>


                death_path = ".//cell_definition[" + str(idx) + "]//phenotype//death//"

                self.param_d[cell_def_name]['apoptosis_duration_flag'] = False
                self.param_d[cell_def_name]["apoptosis_phase0_duration"] = "0.0"
                self.param_d[cell_def_name]["apoptosis_phase0_fixed"] = False
                self.param_d[cell_def_name]["apoptosis_trate01"] = "0.0"
                self.param_d[cell_def_name]["apoptosis_trate01_fixed"] = False

                self.param_d[cell_def_name]['necrosis_duration_flag'] = False
                self.param_d[cell_def_name]["necrosis_phase0_duration"] = "0.0"
                self.param_d[cell_def_name]["necrosis_phase0_fixed"] = False
                self.param_d[cell_def_name]["necrosis_phase1_duration"] = "0.0"
                self.param_d[cell_def_name]["necrosis_phase1_fixed"] = False
                self.param_d[cell_def_name]["necrosis_trate01"] = "0.0"
                self.param_d[cell_def_name]["necrosis_trate01_fixed"] = False
                self.param_d[cell_def_name]["necrosis_trate12"] = "0.0"
                self.param_d[cell_def_name]["necrosis_trate12_fixed"] = False

                # uep = self.xml_root.find('.//microenvironment_setup')  # find unique entry point
                death_uep = uep.find(".//cell_definition[" + str(idx) + "]//phenotype//death")
                print('death_uep=',death_uep)

                for death_model in death_uep.findall('model'):
                    if "apoptosis" in death_model.attrib["name"].lower():
                        print("-------- parsing apoptosis!")
                        self.param_d[cell_def_name]["apoptosis_death_rate"] = death_model.find('death_rate').text

                        # 	<model code="100" name="apoptosis"> 
                        # 		<death_rate units="1/min">5.1e-05</death_rate>
                        # 		<phase_durations units="min">
                        # 			<duration index="0" fixed_duration="true">511</duration>
                        # 		</phase_durations>
                        # 		<parameters>
                        # 			<unlysed_fluid_change_rate units="1/min">0.01</unlysed_fluid_change_rate>
                        pd_uep = death_model.find("phase_durations")
                        if pd_uep is not None:
                            print(' >> pd_uep =',pd_uep )
                            self.param_d[cell_def_name]['apoptosis_duration_flag'] = True
                            # self.apoptosis_rb2.setChecked(True)  # duration

                            for pd in pd_uep:   # <duration index= ... >
                                print(pd)
                                print("index=",pd.attrib["index"])
                                if  pd.attrib['index'] == "0":
                                    self.param_d[cell_def_name]["apoptosis_phase0_duration"] = pd.text
                                    if  pd.attrib['fixed_duration'].lower() == "true":
                                        self.param_d[cell_def_name]["apoptosis_phase0_fixed"] = True
                                    else:
                                        self.param_d[cell_def_name]["apoptosis_phase0_fixed"] = False

                        else:  #  transition rates
                            #     <phase_transition_rates units="1/min">
                            #         <rate start_index="0" end_index="1" fixed_duration="true">0.00193798</rate>
                            #     </phase_transition_rates>
                            tr_uep = death_model.find("phase_transition_rates")
                            if tr_uep is not None:
                                print(' >> tr_uep =',tr_uep )
                                # self.apoptosis_rb1.setChecked(True)  # trate01

                                for tr in tr_uep:   # <duration index= ... >
                                    print(tr)
                                    print("start_index=",tr.attrib["start_index"])

                                    if  tr.attrib['start_index'] == "0":
                                        self.param_d[cell_def_name]["apoptosis_trate01"] = tr.text
                                        if  tr.attrib['fixed_duration'].lower() == "true":
                                            self.param_d[cell_def_name]["apoptosis_trate01_fixed"] = True
                                        else:
                                            self.param_d[cell_def_name]["apoptosis_trate01_fixed"] = False

                        # apoptosis_params_path = apoptosis_path + "parameters//"
                        params_uep = death_model.find("parameters")
                        # apoptosis_params_path = apoptosis_path + "parameters//"

                        # self.param_d[cell_def_name]["apoptosis_unlysed_rate"] = params_uep.find("unlysed_fluid_change_rate").text
                        self.param_d[cell_def_name]["apoptosis_unlysed_rate"] = params_uep.find("unlysed_fluid_change_rate").text
                        self.param_d[cell_def_name]["apoptosis_lysed_rate"] = params_uep.find("lysed_fluid_change_rate").text
                        self.param_d[cell_def_name]["apoptosis_cyto_rate"] = params_uep.find("cytoplasmic_biomass_change_rate").text
                        self.param_d[cell_def_name]["apoptosis_nuclear_rate"] = params_uep.find("nuclear_biomass_change_rate").text
                        self.param_d[cell_def_name]["apoptosis_calcif_rate"] = params_uep.find("calcification_rate").text
                        self.param_d[cell_def_name]["apoptosis_rel_rupture_volume"] = params_uep.find("relative_rupture_volume").text

                #--------------
                # necrosis_params_path = necrosis_path + "parameters//"
                    elif "necrosis" in death_model.attrib["name"].lower():
                        print("-------- parsing necrosis!")
                        self.param_d[cell_def_name]["necrosis_death_rate"] = death_model.find('death_rate').text

                        pd_uep = death_model.find("phase_durations")
                        if pd_uep is not None:
                            print(' >> pd_uep =',pd_uep )
                            # self.necrosis_rb2.setChecked(True)  # duration
                            self.param_d[cell_def_name]['necrosis_duration_flag'] = True

                            for pd in pd_uep:   # <duration index= ... >
                                print(pd)
                                print("index=",pd.attrib["index"])
                                if  pd.attrib['index'] == "0":
                                    self.param_d[cell_def_name]["necrosis_phase0_duration"] = pd.text
                                    if  pd.attrib['fixed_duration'].lower() == "true":
                                        self.param_d[cell_def_name]["necrosis_phase0_fixed"] = True
                                    else:
                                        self.param_d[cell_def_name]["necrosis_phase0_fixed"] = False
                                elif  pd.attrib['index'] == "1":
                                    self.param_d[cell_def_name]["necrosis_phase1_duration"] = pd.text
                                    if  pd.attrib['fixed_duration'].lower() == "true":
                                        self.param_d[cell_def_name]["necrosis_phase1_fixed"] = True
                                    else:
                                        self.param_d[cell_def_name]["necrosis_phase1_fixed"] = False

                        else:  # transition rates
                            #     <phase_transition_rates units="1/min">
                            #         <rate start_index="0" end_index="1" fixed_duration="true">0.00193798</rate>
                            #     </phase_transition_rates>
                            tr_uep = death_model.find("phase_transition_rates")
                            if tr_uep is not None:
                                print(' >> tr_uep =',tr_uep )
                                # self.necrosis_rb1.setChecked(True)  
                                for tr in tr_uep:  # transition rate 
                                    print(tr)
                                    print("start_index=",tr.attrib["start_index"])
                                    if  tr.attrib['start_index'] == "0":
                                        rate = float(tr.text)
                                        print(" --- transition rate (float) = ",rate)
                                        if abs(rate) < 1.e-6:
                                            dval = 9.e99
                                        else:
                                            dval = rate * 60.0
                                        print(" --- transition rate (float) = ",rate)
                                        # self.param_d[cell_def_name]["necrosis_phase0_duration"] = tr.text
                                        self.param_d[cell_def_name]["necrosis_phase0_duration"] = str(dval)
                                        if  tr.attrib['fixed_duration'].lower() == "true":
                                            self.param_d[cell_def_name]["necrosis_phase0_fixed"] = True
                                        else:
                                            self.param_d[cell_def_name]["necrosis_phase0_fixed"] = False
                                    elif  tr.attrib['start_index'] == "1":
                                        self.param_d[cell_def_name]["necrosis_phase1_duration"] = tr.text
                                        if  tr.attrib['fixed_duration'].lower() == "true":
                                            self.param_d[cell_def_name]["necrosis_phase1_fixed"] = True
                                        else:
                                            self.param_d[cell_def_name]["necrosis_phase1_fixed"] = False


                        params_uep = death_model.find("parameters")

                        self.param_d[cell_def_name]["necrosis_unlysed_rate"] = params_uep.find("unlysed_fluid_change_rate").text
                        self.param_d[cell_def_name]["necrosis_lysed_rate"] = params_uep.find("lysed_fluid_change_rate").text
                        self.param_d[cell_def_name]["necrosis_cyto_rate"] = params_uep.find("cytoplasmic_biomass_change_rate").text
                        self.param_d[cell_def_name]["necrosis_nuclear_rate"] = params_uep.find("nuclear_biomass_change_rate").text
                        self.param_d[cell_def_name]["necrosis_calcif_rate"] = params_uep.find("calcification_rate").text
                        self.param_d[cell_def_name]["necrosis_rel_rupture_rate"] = params_uep.find("relative_rupture_volume").text


                # # ---------  volume 
                        # <volume>  
                        # 	<total units="micron^3">2494</total>
                        # 	<fluid_fraction units="dimensionless">0.75</fluid_fraction>
                        # 	<nuclear units="micron^3">540</nuclear>
                            
                        # 	<fluid_change_rate units="1/min">0.05</fluid_change_rate>
                        # 	<cytoplasmic_biomass_change_rate units="1/min">0.0045</cytoplasmic_biomass_change_rate>
                        # 	<nuclear_biomass_change_rate units="1/min">0.0055</nuclear_biomass_change_rate>
                            
                        # 	<calcified_fraction units="dimensionless">0</calcified_fraction>
                        # 	<calcification_rate units="1/min">0</calcification_rate>
                            
                        # 	<relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>

                volume_path = ".//cell_definition[" + str(idx) + "]//phenotype//volume//"
                print('volume_path=',volume_path)

                # self.volume_total.setText(uep.find(volume_path+"total").text)
                # self.volume_fluid_fraction.setText(uep.find(volume_path+"fluid_fraction").text)
                # self.volume_nuclear.setText(uep.find(volume_path+"nuclear").text)
                # self.volume_fluid_change_rate.setText(uep.find(volume_path+"fluid_change_rate").text)
                # self.volume_cytoplasmic_biomass_change_rate.setText(uep.find(volume_path+"cytoplasmic_biomass_change_rate").text)
                # self.volume_nuclear_biomass_change_rate.setText(uep.find(volume_path+"nuclear_biomass_change_rate").text)
                # self.volume_calcified_fraction.setText(uep.find(volume_path+"calcified_fraction").text)
                # self.volume_calcification_rate.setText(uep.find(volume_path+"calcification_rate").text)
                # self.relative_rupture_volume.setText(uep.find(volume_path+"relative_rupture_volume").text)

                self.param_d[cell_def_name]["volume_total"] = uep.find(volume_path+"total").text
                self.param_d[cell_def_name]["volume_fluid_fraction"] = uep.find(volume_path+"fluid_fraction").text
                self.param_d[cell_def_name]["volume_nuclear"] = uep.find(volume_path+"nuclear").text
                self.param_d[cell_def_name]["volume_fluid_change_rate"] = uep.find(volume_path+"fluid_change_rate").text
                self.param_d[cell_def_name]["volume_cytoplasmic_rate"] = uep.find(volume_path+"cytoplasmic_biomass_change_rate").text
                self.param_d[cell_def_name]["volume_nuclear_rate"] = uep.find(volume_path+"nuclear_biomass_change_rate").text
                self.param_d[cell_def_name]["volume_calcif_fraction"] = uep.find(volume_path+"calcified_fraction").text
                self.param_d[cell_def_name]["volume_calcif_rate"] = uep.find(volume_path+"calcification_rate").text
                self.param_d[cell_def_name]["volume_rel_rupture_vol"] = uep.find(volume_path+"relative_rupture_volume").text


                # # ---------  mechanics 
                print("\n===== populate():  mechanics")
                        # <mechanics> 
                        # 	<cell_cell_adhesion_strength units="micron/min">0.4</cell_cell_adhesion_strength>
                        # 	<cell_cell_repulsion_strength units="micron/min">10.0</cell_cell_repulsion_strength>
                        # 	<relative_maximum_adhesion_distance units="dimensionless">1.25</relative_maximum_adhesion_distance>
                            
                        # 	<options>
                        # 		<set_relative_equilibrium_distance enabled="false" units="dimensionless">1.8</set_relative_equilibrium_distance>
                        # 		<set_absolute_equilibrium_distance enabled="false" units="micron">15.12</set_absolute_equilibrium_distance>
                        # 	</options>

                mechanics_path = ".//cell_definition[" + str(idx) + "]//phenotype//mechanics//"
                print('mechanics_path=',mechanics_path)

                # self.cell_cell_adhesion_strength.setText(uep.find(mechanics_path+"cell_cell_adhesion_strength").text)
                # self.cell_cell_repulsion_strength.setText(uep.find(mechanics_path+"cell_cell_repulsion_strength").text)
                val =  uep.find(mechanics_path+"cell_cell_adhesion_strength").text
                self.param_d[cell_def_name]["mechanics_adhesion"] = val

                val =  uep.find(mechanics_path+"cell_cell_repulsion_strength").text
                self.param_d[cell_def_name]["mechanics_repulsion"] = val

                val =  uep.find(mechanics_path+"relative_maximum_adhesion_distance").text
                self.param_d[cell_def_name]["mechanics_adhesion_distance"] = val

                # self.relative_maximum_adhesion_distance.setText(uep.find(mechanics_path+"relative_maximum_adhesion_distance").text)

                mechanics_options_path = ".//cell_definition[" + str(idx) + "]//phenotype//mechanics//options//"
                # self.set_relative_equilibrium_distance.setText(uep.find(mechanics_options_path+"set_relative_equilibrium_distance").text)

                # self.set_absolute_equilibrium_distance.setText(uep.find(mechanics_options_path+"set_absolute_equilibrium_distance").text)

                val =  uep.find(mechanics_options_path+"set_relative_equilibrium_distance").text
                self.param_d[cell_def_name]["mechanics_relative_equilibrium_distance"] = val

                val =  uep.find(mechanics_options_path+"set_absolute_equilibrium_distance").text
                self.param_d[cell_def_name]["mechanics_absolute_equilibrium_distance"] = val

                if uep.find(mechanics_options_path+"set_relative_equilibrium_distance").attrib['enabled'].lower() == 'true':
                    self.param_d[cell_def_name]["mechanics_relative_equilibrium_distance_enabled"] = True
                else:
                    self.param_d[cell_def_name]["mechanics_relative_equilibrium_distance_enabled"] = False

                if uep.find(mechanics_options_path+"set_absolute_equilibrium_distance").attrib['enabled'].lower() == 'true':
                    self.param_d[cell_def_name]["mechanics_absolute_equilibrium_distance_enabled"] = True
                else:
                    self.param_d[cell_def_name]["mechanics_absolute_equilibrium_distance_enabled"] = False


                # # ---------  motility 
                print("\n===== populate():  motility")
                        # <motility>  
                        # 	<speed units="micron/min">5.0</speed>
                        # 	<persistence_time units="min">5.0</persistence_time>
                        # 	<migration_bias units="dimensionless">0.5</migration_bias>
                            
                        # 	<options>
                        # 		<enabled>true</enabled>
                        # 		<use_2D>true</use_2D>
                        # 		<chemotaxis>
                        # 			<enabled>false</enabled>
                        # 			<substrate>director signal</substrate>
                        # 			<direction>1</direction>
                        # 		</chemotaxis>
                        # 	</options>

                motility_path = ".//cell_definition[" + str(idx) + "]//phenotype//motility//"
                print('motility_path=',motility_path)

                val = uep.find(motility_path+"speed").text
                self.param_d[cell_def_name]["speed"] = val

                val = uep.find(motility_path+"persistence_time").text
                self.param_d[cell_def_name]["persistence_time"] = val

                val = uep.find(motility_path+"migration_bias").text
                self.param_d[cell_def_name]["migration_bias"] = val

                motility_options_path = ".//cell_definition[" + str(idx) + "]//phenotype//motility//options//"

                # print(' motility options enabled', uep.find(motility_options_path +'enabled').text)
                if uep.find(motility_options_path +'enabled').text.lower() == 'true':
                    self.param_d[cell_def_name]["motility_enabled"] = True
                else:
                    self.param_d[cell_def_name]["motility_enabled"] = False

                if uep.find(motility_options_path +'use_2D').text.lower() == 'true':
                    self.param_d[cell_def_name]["motility_use_2D"] = True
                else:
                    self.param_d[cell_def_name]["motility_use_2D"] = False

                        # 		<chemotaxis>
                        # 			<enabled>false</enabled>
                        # 			<substrate>director signal</substrate>
                        # 			<direction>1</direction>
                        # 		</chemotaxis>
                motility_chemotaxis_path = motility_options_path + "chemotaxis//"
                if uep.find(motility_chemotaxis_path) is None:
                    self.param_d[cell_def_name]["motility_chemotaxis"] = False
                    self.param_d[cell_def_name]["motility_chemotaxis_substrate"] = ""
                    self.param_d[cell_def_name]["motility_chemotaxis_towards"] = True
                else:
                    if uep.find(motility_chemotaxis_path +'enabled').text.lower() == 'true':
                        self.param_d[cell_def_name]["motility_chemotaxis"] = True
                    else:
                        self.param_d[cell_def_name]["motility_chemotaxis"] = False

                    val = uep.find(motility_chemotaxis_path +'substrate').text
                    self.param_d[cell_def_name]["motility_chemotaxis_substrate"] = val

                    val = uep.find(motility_chemotaxis_path +'direction').text
                    if val == '1':
                        self.param_d[cell_def_name]["motility_chemotaxis_towards"] = True
                    else:
                        self.param_d[cell_def_name]["motility_chemotaxis_towards"] = False


                # # ---------  secretion 
                print("\n===== populate():  secretion")

                # <substrate name="virus">
                #     <secretion_rate units="1/min">0</secretion_rate>
                #     <secretion_target units="substrate density">1</secretion_target>
                #     <uptake_rate units="1/min">10</uptake_rate>
                #     <net_export_rate units="total substrate/min">0</net_export_rate> 
                # </substrate> 

                secretion_path = ".//cell_definition[" + str(idx) + "]//phenotype//secretion//"
                print('secretion_path =',secretion_path)
                secretion_sub1_path = ".//cell_definition[" + str(idx) + "]//phenotype//secretion//substrate[1]//"

                uep_secretion = self.xml_root.find(".//cell_definitions//cell_definition[" + str(idx) + "]//phenotype//secretion")
                print('uep_secretion = ',uep_secretion )
                

                # e.g.: param_d["cancer cell"]["oxygen"]["secretion_rate"] = 0.0
                # or,   param_d["cancer cell"]["oxygen"]["secretion_rate"] = 0.0
                # or,   param_d["cancer cell"]["secretion"] = {"oxygen" : { "secretion_rate" : 42.0 } }
                self.param_d[cell_def_name]["secretion"] = {}  # a dict for these params

                # Initialize (set to 0.0) all substrates' secretion params
                # val = "0.0"
                # print('----- populate: self.substrate_list = ',self.substrate_list )
                # for substrate_name in self.substrate_list:
                #     print('----- populate: substrate_name = ',substrate_name )
                #     self.param_d[cell_def_name]["secretion"][substrate_name]["secretion_rate"] = val
                #     self.param_d[cell_def_name]["secretion"][substrate_name]["secretion_target"] = val
                #     self.param_d[cell_def_name]["secretion"][substrate_name]["uptake_rate"] = val
                #     self.param_d[cell_def_name]["secretion"][substrate_name]["net_export_rate"] = val
                # foo = 1/0


                jdx = 0
                for sub in uep_secretion.findall('substrate'):
                    substrate_name = sub.attrib['name']
                    if jdx == 0:
                        self.current_secretion_substrate = substrate_name

                    print(jdx,") -- secretion substrate = ",substrate_name)
                    # self.param_d[self.current_cell_def]["secretion"][substrate_name]["secretion_rate"] = {}
                    self.param_d[cell_def_name]["secretion"][substrate_name] = {}

                    tptr = sub.find("secretion_rate")
                    if tptr is not None:
                        val = tptr.text
                    else:
                        val = "0.0"
                    self.param_d[cell_def_name]["secretion"][substrate_name]["secretion_rate"] = val
                    # print(self.param_d[cell_def_name]["secretion"][substrate_name] )

                    tptr = sub.find("secretion_target")
                    if tptr is not None:
                        val = tptr.text
                    else:
                        val = "0.0"
                    self.param_d[cell_def_name]["secretion"][substrate_name]["secretion_target"] = val

                    tptr = sub.find("uptake_rate")
                    if tptr is not None:
                        val = tptr.text
                    else:
                        val = "0.0"
                    self.param_d[cell_def_name]["secretion"][substrate_name]["uptake_rate"] = val

                    tptr = sub.find("net_export_rate")
                    if tptr is not None:
                        val = tptr.text
                    else:
                        val = "0.0"
                    self.param_d[cell_def_name]["secretion"][substrate_name]["net_export_rate"] = val

                    jdx += 1

                print("------ done parsing secretion:")
                # print("------ self.param_d = ",self.param_d)
                

                # # ---------  molecular 
                print("\n===== populate():  molecular")


                # # ---------  custom data 
                print("\n===== populate():  custom data")
                # <custom_data>  
                # 	<receptor units="dimensionless">0.0</receptor>
                # 	<cargo_release_o2_threshold units="mmHg">10</cargo_release_o2_threshold>

                uep_custom_data = self.xml_root.find(".//cell_definitions//cell_definition[" + str(idx) + "]//custom_data")
                # custom_data_path = ".//cell_definition[" + str(self.idx_current_cell_def) + "]//custom_data//"
                print('uep_custom_data=',uep_custom_data)

                # for jdx in range(self.custom_data_count):
                #     self.custom_data_name[jdx].setText('')
                #     self.custom_data_value[jdx].setText('')
                    

                jdx = 0
                # rwh/TODO: if we have more vars than we initially created rows for, we'll need
                # to call 'append_more_cb' for the excess.
                self.custom_data_count = 0
                if uep_custom_data:
                    # print("--------------- populate: custom_dat for cell_def_name= ",cell_def_name)
                    self.param_d[cell_def_name]['custom_data'] = {}
                    for var in uep_custom_data:
                        # print(jdx, ") ",var)
                        # val = sub.find("secretion_rate").text
                        val = var.text
                        # print("tag= ",var.tag)
                        # print("val= ",val)
                        # self.param_d[cell_def_name]["secretion"][substrate_name]["secretion_rate"] = val
                        self.param_d[cell_def_name]['custom_data'][var.tag] = val
                        self.custom_data_count += 1
                #     self.custom_data_name[jdx].setText(var.tag)
                #     print("tag=",var.tag)
                #     self.custom_data_value[jdx].setText(var.text)

                #     if 'units' in var.keys():
                #         self.custom_data_units[jdx].setText(var.attrib['units'])
                #     jdx += 1

                    # print("--------- populate: self.param_d[cell_def_name]['custom_data'] = ",self.param_d[cell_def_name]['custom_data'])


        self.current_cell_def = cell_def_0th
        self.tree.setCurrentItem(self.tree.topLevelItem(0))  # select the top (0th) item
        self.tree_item_clicked_cb(self.tree.topLevelItem(0), 0)  # and have its params shown

        # print("\n\n=======================  leaving cell_def populate_tree  ======================= ")
        # print()
        # for k in self.param_d.keys():
        #     print(" ===>>> ",k, " : ", self.param_d[k])
        #     print()

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
            subelm = ET.SubElement(cycle, "phase_transition_rates",{"units":"1/min"})
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
        # <model code="100" name="apoptosis"> 
        death = ET.SubElement(pheno, "death")
        death.text = self.indent12  # affects indent of child
        death.tail = "\n" + self.indent10

					# <model code="100" name="apoptosis"> 
					# 	<death_rate units="1/min">5.31667e-05</death_rate>
					# 	<!-- use phase_transition_rates OR phase_durations -->
					# 	<!--
					# 	<phase_transition_rates units="1/min">
					# 		<rate start_index="0" end_index="1" fixed_duration="true">0.00193798</rate>
					# 	</phase_transition_rates>
					# 	-->
					# 	<phase_durations units="min">
					# 		<duration index="0" fixed_duration="true">516</duration>
					# 	</phase_durations>
					# 	<parameters>
					# 		<unlysed_fluid_change_rate units="1/min">0.05</unlysed_fluid_change_rate>
					# 		<lysed_fluid_change_rate units="1/min">0</lysed_fluid_change_rate>
					# 		<cytoplasmic_biomass_change_rate units="1/min">1.66667e-02</cytoplasmic_biomass_change_rate>
					# 		<nuclear_biomass_change_rate units="1/min">5.83333e-03</nuclear_biomass_change_rate>
					# 		<calcification_rate units="1/min">0</calcification_rate>
					# 		<relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>
					# 	</parameters>
					# </model> 
        model = ET.SubElement(death, "model",{"code":"100", "name":"apoptosis"})
        model.text = self.indent14  # affects indent of child
        model.tail = self.indent12

        subelm = ET.SubElement(model, "death_rate",{"units":"1/min"})
        subelm.text = self.param_d[cdname]["apoptosis_death_rate"]
        subelm.tail = self.indent14

        # (self.param_d[cdname]["apoptosis_phase0_duration"])
        # (self.param_d[cdname]["apoptosis_phase0_fixed"])
						# <phase_durations units="min">
							# <duration index="0" fixed_duration="true">511</duration>
						# </phase_durations>
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
            # 	<phase_transition_rates units="1/min">
            # 		<rate start_index="0" end_index="1" fixed_duration="true">0.00193798</rate>
            # 	</phase_transition_rates>
            subelm = ET.SubElement(model, "phase_transition_rates",{"units":self.default_rate_units})
            subelm.text = self.indent16
            subelm.tail = self.indent14

            bval = "false"
            if self.param_d[cdname]["apoptosis_trate01_fixed"]:
                bval = "true"
            subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0","end_index":"1", "fixed_duration":bval})
            subelm2.text = self.param_d[cdname]["apoptosis_trate01"]
            subelm2.tail = self.indent14

        # (self.param_d[cdname]["apoptosis_unlysed_rate"])
        # (self.param_d[cdname]["apoptosis_lysed_rate"])
        # (self.param_d[cdname]["apoptosis_cyto_rate"])
        # (self.param_d[cdname]["apoptosis_nuclear_rate"])
        # (self.param_d[cdname]["apoptosis_calcif_rate"])
        # (self.param_d[cdname]["apoptosis_rel_rupture_volume"])
					# 		<unlysed_fluid_change_rate units="1/min">0.05</unlysed_fluid_change_rate>
					# 		<lysed_fluid_change_rate units="1/min">0</lysed_fluid_change_rate>
					# 		<cytoplasmic_biomass_change_rate units="1/min">1.66667e-02</cytoplasmic_biomass_change_rate>
					# 		<nuclear_biomass_change_rate units="1/min">5.83333e-03</nuclear_biomass_change_rate>
					# 		<calcification_rate units="1/min">0</calcification_rate>
					# 		<relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>
        # (self.param_d[cdname]["apoptosis_unlysed_rate"])
        # (self.param_d[cdname]["apoptosis_lysed_rate"])
        # (self.param_d[cdname]["apoptosis_cyto_rate"])
        # (self.param_d[cdname]["apoptosis_nuclear_rate"])
        # (self.param_d[cdname]["apoptosis_calcif_rate"])
        # (self.param_d[cdname]["apoptosis_rel_rupture_volume"])
        elm = ET.SubElement(model, "parameters")
        elm.text = self.indent16  # affects indent of child
        elm.tail = self.indent12

        subelm = ET.SubElement(elm, "unlysed_fluid_change_rate",{"units":"1/min"})
        subelm.text = self.param_d[cdname]["apoptosis_unlysed_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "lysed_fluid_change_rate",{"units":"1/min"})
        subelm.text = self.param_d[cdname]["apoptosis_lysed_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "cytoplasmic_biomass_change_rate",{"units":"1/min"})
        subelm.text = self.param_d[cdname]["apoptosis_cyto_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "nuclear_biomass_change_rate",{"units":"1/min"})
        subelm.text = self.param_d[cdname]["apoptosis_nuclear_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "calcification_rate",{"units":"1/min"})
        subelm.text = self.param_d[cdname]["apoptosis_calcif_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "relative_rupture_volume",{"units":"dimensionless"})
        subelm.text = self.param_d[cdname]["apoptosis_rel_rupture_volume"]
        subelm.tail = self.indent14

        #---------------------------------
        # <model code="101" name="necrosis"> 
                        # <phase_durations units="min">
						# 	<duration index="0" fixed_duration="true">0</duration>
						# 	<duration index="1" fixed_duration="true">86400</duration>
						# </phase_durations>
						
						# <parameters>
        model = ET.SubElement(death, "model",{"code":"101", "name":"necrosis"})
        model.text = self.indent14  # affects indent of child
        model.tail = self.indent10

        subelm = ET.SubElement(model, "death_rate",{"units":"1/min"})
        subelm.text = self.param_d[cdname]["necrosis_death_rate"]
        subelm.tail = self.indent14

        # subelm = ET.SubElement(model, "phase_durations",{"units":self.default_time_units})
        # subelm.text = self.indent16
        # subelm.tail = self.indent14

        # bval = "false"
        # if self.param_d[cdname]["necrosis_phase0_fixed"]:
        #     bval = "true"
        # subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":bval})
        # subelm2.text = self.param_d[cdname]["necrosis_phase0_duration"]
        # subelm2.tail = self.indent16

        # bval = "false"
        # if self.param_d[cdname]["necrosis_phase1_fixed"]:
        #     bval = "true"
        # subelm2 = ET.SubElement(subelm, "duration",{"index":"1", "fixed_duration":bval})
        # subelm2.text = self.param_d[cdname]["necrosis_phase1_duration"]
        # subelm2.tail = self.indent14
    

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
            subelm2.text = self.param_d[cdname]["necrosis_phase0_duration"]
            subelm2.tail = self.indent14
        else:   # transition rate
            # 	<phase_transition_rates units="1/min">
            # 		<rate start_index="0" end_index="1" fixed_duration="true">0.00193798</rate>
            # 	</phase_transition_rates>
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


        # (self.param_d[cdname]["necrosis_phase0_duration"])
        # (self.param_d[cdname]["necrosis_phase0_fixed"])
        # (self.param_d[cdname]["necrosis_phase1_duration"])
        # (self.param_d[cdname]["necrosis_phase1_fixed"])

        # (self.param_d[cdname]["necrosis_unlysed_rate"])
        # (self.param_d[cdname]["necrosis_lysed_rate"])
        # (self.param_d[cdname]["necrosis_cyto_rate"])
        # (self.param_d[cdname]["necrosis_nuclear_rate"])
        # (self.param_d[cdname]["necrosis_calcif_rate"])
        # (self.param_d[cdname]["necrosis_rel_rupture_rate"])
        elm = ET.SubElement(model, "parameters")
        elm.text = self.indent16  # affects indent of child
        elm.tail = self.indent12

        subelm = ET.SubElement(elm, "unlysed_fluid_change_rate",{"units":"1/min"})
        subelm.text = self.param_d[cdname]["necrosis_unlysed_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "lysed_fluid_change_rate",{"units":"1/min"})
        subelm.text = self.param_d[cdname]["necrosis_lysed_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "cytoplasmic_biomass_change_rate",{"units":"1/min"})
        subelm.text = self.param_d[cdname]["necrosis_cyto_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "nuclear_biomass_change_rate",{"units":"1/min"})
        subelm.text = self.param_d[cdname]["necrosis_nuclear_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "calcification_rate",{"units":"1/min"})
        subelm.text = self.param_d[cdname]["necrosis_calcif_rate"]
        subelm.tail = self.indent16

        subelm = ET.SubElement(elm, "relative_rupture_volume",{"units":"dimensionless"})
        subelm.text = self.param_d[cdname]["necrosis_rel_rupture_rate"]
        subelm.tail = self.indent14


    #-------------------------------------------------------------------
                # <volume>  
				# 	<total units="micron^3">2494</total>
				# 	<fluid_fraction units="dimensionless">0.75</fluid_fraction>
				# 	<nuclear units="micron^3">540</nuclear>
					
				# 	<fluid_change_rate units="1/min">0.05</fluid_change_rate>
				# 	<cytoplasmic_biomass_change_rate units="1/min">0.0045</cytoplasmic_biomass_change_rate>
				# 	<nuclear_biomass_change_rate units="1/min">0.0055</nuclear_biomass_change_rate>
					
				# 	<calcified_fraction units="dimensionless">0</calcified_fraction>
				# 	<calcification_rate units="1/min">0</calcification_rate>
					
				# 	<relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>
				# </volume> 				
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml_volume(self,pheno,cdef):
        volume = ET.SubElement(pheno, "volume")
        volume.text = self.indent12  # affects indent of child
        volume.tail = "\n" + self.indent10

        elm = ET.SubElement(volume, 'total')
        elm.text = self.param_d[cdef]['volume_total']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'fluid_fraction')
        elm.text = self.param_d[cdef]['volume_fluid_fraction']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'nuclear')
        elm.text = self.param_d[cdef]['volume_nuclear']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'fluid_change_rate')
        elm.text = self.param_d[cdef]['volume_fluid_change_rate']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'cytoplasmic_biomass_change_rate')
        # elm.text = self.param_d[cdef]['volume_cytoplasmic_biomass_change_rate']
        elm.text = self.param_d[cdef]['volume_cytoplasmic_rate']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'nuclear_biomass_change_rate')
        elm.text = self.param_d[cdef]['volume_nuclear_rate']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'calcified_fraction')
        elm.text = self.param_d[cdef]['volume_calcif_fraction']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'calcification_rate')
        elm.text = self.param_d[cdef]['volume_calcif_rate']
        elm.tail = self.indent12

        elm = ET.SubElement(volume, 'relative_rupture_volume')
        elm.text = self.param_d[cdef]['volume_rel_rupture_vol']
        elm.tail = self.indent10

    #-------------------------------------------------------------------
            # <mechanics> 
            # 	<cell_cell_adhesion_strength units="micron/min">1.1</cell_cell_adhesion_strength>
            # 	<cell_cell_repulsion_strength units="micron/min">11.0</cell_cell_repulsion_strength>
            # 	<relative_maximum_adhesion_distance units="dimensionless">1.11</relative_maximum_adhesion_distance>
                
            # 	<options>
            # 		<set_relative_equilibrium_distance enabled="false" units="dimensionless">1.111</set_relative_equilibrium_distance>
            # 		<set_absolute_equilibrium_distance enabled="false" units="micron">11.111</set_absolute_equilibrium_distance>
            # 	</options>
            # </mechanics>

        # # insert callbacks for QCheckBoxes
        # self.param_d[self.current_cell_def]['mechanics_absolute_equilibrium_distance_enabled'] = bval

    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml_mechanics(self,pheno,cdef):
        mechanics = ET.SubElement(pheno, "mechanics")
        mechanics.text = self.indent12  # affects indent of child
        mechanics.tail = "\n" + self.indent10
            # 	<cell_cell_adhesion_strength units="micron/min">1.1</cell_cell_adhesion_strength>
            # 	<cell_cell_repulsion_strength units="micron/min">11.0</cell_cell_repulsion_strength>
            # 	<relative_maximum_adhesion_distance units="dimensionless">1.11</relative_maximum_adhesion_distance>
                
            # 	<options>
            # 		<set_relative_equilibrium_distance enabled="false" units="dimensionless">1.111</set_relative_equilibrium_distance>
            # 		<set_absolute_equilibrium_distance enabled="false" units="micron">11.111</set_absolute_equilibrium_distance>


        # self.cell_cell_adhesion_strength.setText(self.param_d[cdname]["mechanics_adhesion"])
        # self.cell_cell_repulsion_strength.setText(self.param_d[cdname]["mechanics_repulsion"])
        # self.relative_maximum_adhesion_distance.setText(self.param_d[cdname]["mechanics_adhesion_distance"])

        # self.set_relative_equilibrium_distance.setText(self.param_d[cdname]["mechanics_relative_equilibrium_distance"])
        # self.set_absolute_equilibrium_distance.setText(self.param_d[cdname]["mechanics_absolute_equilibrium_distance"])

        # self.set_relative_equilibrium_distance_enabled.setChecked(self.param_d[cdname]["mechanics_relative_equilibrium_distance_enabled"])
        # self.set_absolute_equilibrium_distance_enabled.setChecked(self.param_d[cdname]["mechanics_absolute_equilibrium_distance_enabled"])

        elm = ET.SubElement(mechanics, 'cell_cell_adhesion_strength',{"units":"micron/min"})
        elm.text = self.param_d[cdef]['mechanics_adhesion']
        elm.tail = self.indent12

        elm = ET.SubElement(mechanics, 'cell_cell_repulsion_strength',{"units":"micron/min"})
        elm.text = self.param_d[cdef]['mechanics_repulsion']
        elm.tail = self.indent12

        elm = ET.SubElement(mechanics, 'relative_maximum_adhesion_distance',{"units":"dimensionless"})
        elm.text = self.param_d[cdef]['mechanics_adhesion_distance']
        elm.tail = self.indent12

            # 	<options>
            # 		<set_relative_equilibrium_distance enabled="false" units="dimensionless">1.111</set_relative_equilibrium_distance>
            # 		<set_absolute_equilibrium_distance enabled="false" units="micron">11.111</set_absolute_equilibrium_distance>
            # 	</options>
        elm = ET.SubElement(mechanics, 'options')
        elm.text = self.indent14
        elm.tail = self.indent10

        # self.param_d[self.current_cell_def]['set_relative_equilibrium_distance'] = text
        # self.param_d[self.current_cell_def]['set_absolute_equilibrium_distance'] = text
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

    #-------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml_motility(self,pheno,cdef):
        motility = ET.SubElement(pheno, "motility")
        motility.text = self.indent12  # affects indent of child
        motility.tail = "\n" + self.indent10

                    # <speed units="micron/min">1.1</speed>
					# <persistence_time units="min">1.2</persistence_time>
					# <migration_bias units="dimensionless">1.3</migration_bias>
					# <options>
					# 	<enabled>false</enabled>
					# 	<use_2D>true</use_2D>
					# 	<chemotaxis>
					# 		<enabled>false</enabled>
					# 		<substrate>oxygen</substrate>
					# 		<direction>-1</direction>
					# 	</chemotaxis>
					# </options>
        # self.speed.setText(self.param_d[cdname]["speed"])
        # self.persistence_time.setText(self.param_d[cdname]["persistence_time"])
        # self.migration_bias.setText(self.param_d[cdname]["migration_bias"])

        # self.motility_enabled.setChecked(self.param_d[cdname]["motility_enabled"])
        # self.motility_use_2D.setChecked(self.param_d[cdname]["motility_use_2D"])
        # self.chemotaxis_enabled.setChecked(self.param_d[cdname]["motility_chemotaxis"])
        # self.motility_substrate_dropdown.setCurrentText(self.param_d[self.current_cell_def]["motility_chemotaxis_substrate"])

        # if self.param_d[cdname]["motility_chemotaxis_towards"]:
        #     self.chemotaxis_direction_towards.setChecked(True)
        # else:
        #     self.chemotaxis_direction_against.setChecked(True)

        elm = ET.SubElement(motility, 'speed')
        elm.text = self.param_d[cdef]['speed']
        elm.tail = self.indent12

        elm = ET.SubElement(motility, 'persistence_time')
        elm.text = self.param_d[cdef]['persistence_time']
        elm.tail = self.indent12
        
        elm = ET.SubElement(motility, 'migration_bias')
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
        taxis.tail = self.indent12

        bval = "false"
        if self.param_d[cdef]['motility_chemotaxis']:
            bval = "true"
        elm = ET.SubElement(taxis, 'enabled')
        elm.text = bval
        elm.tail = self.indent16

        # self.motility_substrate_dropdown.setCurrentText(self.param_d[self.current_cell_def]["motility_chemotaxis_substrate"])
        elm = ET.SubElement(taxis, 'substrate')
        print("\n\n ====================> fill_xml_motility(): self.param_d[cdef]['motility_chemotaxis_substrate'] = ", self.param_d[cdef]['motility_chemotaxis_substrate'], "\n\n")
        elm.text = self.param_d[cdef]['motility_chemotaxis_substrate']
        elm.tail = self.indent16
        # if self.param_d[cdname]["motility_chemotaxis_towards"]:
        #     self.chemotaxis_direction_towards.setChecked(True)
        # else:
        #     self.chemotaxis_direction_against.setChecked(True)
        direction = "-1"
        if self.param_d[cdef]["motility_chemotaxis_towards"]:
            direction = "1"
        elm = ET.SubElement(taxis, 'direction')
        elm.text = direction
        elm.tail = self.indent14

    #-------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml_secretion(self,pheno,cdef):
        secretion = ET.SubElement(pheno, "secretion")
        secretion.text = self.indent12  # affects indent of child
        secretion.tail = "\n" + self.indent10

                    # <substrate name="oxygen">
					# 	<secretion_rate units="1/min">21.0</secretion_rate>
					# 	<secretion_target units="substrate density">21.1</secretion_target>
					# 	<uptake_rate units="1/min">21.2</uptake_rate>
					# 	<net_export_rate units="total substrate/min">21.3</net_export_rate> 
					# </substrate> 
					# <substrate name="glue">
					# 	<secretion_rate units="1/min">22.0</secretion_rate>
					# 	<secretion_target units="substrate density">22.1</secretion_target>
					# 	<uptake_rate units="1/min">22.2</uptake_rate>
					# 	<net_export_rate units="total substrate/min">22.3</net_export_rate> 
					# </substrate> 

        for substrate in self.substrate_list:
            elm = ET.SubElement(secretion, "substrate",{"name":substrate})
            elm.text = self.indent14
            elm.tail = self.indent12

            subelm = ET.SubElement(elm, "secretion_rate",{"units":"1/min"})
            subelm.text = self.param_d[cdef]["secretion"][substrate]["secretion_rate"]
            subelm.tail = self.indent14

            subelm = ET.SubElement(elm, "secretion_target",{"units":"substrate density"})
            subelm.text = self.param_d[cdef]["secretion"][substrate]["secretion_target"]
            subelm.tail = self.indent14

            subelm = ET.SubElement(elm, "uptake_rate",{"units":"1/min"})
            subelm.text = self.param_d[cdef]["secretion"][substrate]["uptake_rate"]
            subelm.tail = self.indent14

            subelm = ET.SubElement(elm, "net_export_rate",{"units":"total substrate/min"})
            subelm.text = self.param_d[cdef]["secretion"][substrate]["net_export_rate"]
            subelm.tail = self.indent12

        # self.secretion_rate.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["secretion_rate"])
        # self.secretion_target.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["secretion_target"])
        # self.uptake_rate.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["uptake_rate"])
        # self.secretion_net_export_rate.setText(self.param_d[cdname]["secretion"][self.current_secretion_substrate]["net_export_rate"])


    #-------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml_custom_data(self,custom_data,cdef):
        print("------------------- fill_xml_custom_data():  self.custom_data_count = ", self.custom_data_count)
				# <receptor units="dimensionless">1.0</receptor>
				# <cargo_release_o2_threshold units="mmHg">10</cargo_release_o2_threshold>

                # --------- update_custom_data_params():  self.param_d[cdname]['custom_data'] =  {'receptor': '1.0', 'cargo_release_o2_threshold': '10', 'damage_rate': '0.03333', 'repair_rate': '0.004167', 'drug_death_rate': '0.004167', 'damage': '0.0'}

        # for idx in range(self.custom_data_count):
        for key in self.param_d[cdef]['custom_data'].keys():
            print("    key=",key,",  len(key)=",len(key))
            # vname = self.custom_data_name[idx].text()
            # if vname:
            if len(key) > 0:
                # elm = ET.SubElement(custom_data, self.custom_data_name[idx].text())
                # elm = ET.SubElement(custom_data, self.param_d[cdef][custom_data_name[idx].text())
                elm = ET.SubElement(custom_data, key)
                elm.text = self.param_d[cdef]['custom_data'][key]
                # elm.text = self.custom_data_value[idx].text()
                elm.tail = self.indent10

        # for idx in range(5):
        #     elm = ET.SubElement(cdata, "foo")
        #     elm.text = "42.0"
        #     elm.tail = self.indent10

    #-------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml(self):
        # pass
        print("----------- cell_def_tab.py: fill_xml(): ----------")
        uep = self.xml_root.find('.//cell_definitions') # guaranteed to exist since we start with a valid model
        if uep:
            # Begin by removing all previously defined cell defs in the .xml
            for cell_def in uep.findall('cell_definition'):
                uep.remove(cell_def)

        # Obtain a list of all cell defs in self.tree (QTreeWidget()). Used below.
        cdefs_in_tree = []
        num_cdefs = self.tree.invisibleRootItem().childCount()  # rwh: get number of items in tree
        print('num cell defs = ',num_cdefs)
        self.iterate_tree(self.tree.invisibleRootItem(), num_cdefs, cdefs_in_tree)
        print("cdefs_in_tree =",cdefs_in_tree)

        uep = self.xml_root.find('.//cell_definitions')


        idx = 0
        for cdef in self.param_d.keys():
            print('key in param_d.keys() = ',cdef)
            if cdef in cdefs_in_tree:
                print("matched! ",cdef)

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
                elm = ET.Element("cell_definition", 
                        {"name":cdef, "ID":str(idx)})
                elm.tail = '\n' + self.indent6
                elm.text = self.indent8
                pheno = ET.SubElement(elm, 'phenotype')
                pheno.text = self.indent10
                pheno.tail = self.indent8

                self.fill_xml_cycle(pheno,cdef)
                    # subelm2.tail = '\n' + self.indent10
                    # <phase_transition_rates units="1/min"> 
					# 	<rate start_index="0" end_index="0" fixed_duration="true">0.000072</rate>
					# </phase_transition_rates>
                    # vs.
                    # <phase_durations units="min"> 
					# 	<duration index="0" fixed_duration="false">300.0</duration>
					# 	<duration index="1" fixed_duration="true">480</duration>
					# 	<duration index="2" fixed_duration="true">240</duration>
					# 	<duration index="3" fixed_duration="true">60</duration>
					# </phase_durations>

                # cycle.text = self.param_d[cdef]["diffusion_coef"]

                # ------- death ------- 
                self.fill_xml_death(pheno,cdef)
                # ------- volume ------- 
                self.fill_xml_volume(pheno,cdef)
                # ------- mechanics ------- 
                self.fill_xml_mechanics(pheno,cdef)
                # ------- motility ------- 
                self.fill_xml_motility(pheno,cdef)
                # ------- secretion ------- 
                self.fill_xml_secretion(pheno,cdef)


                # ------- custom data ------- 
                customdata = ET.SubElement(elm, 'custom_data')
                customdata.text = self.indent10
                customdata.tail = self.indent10
                self.fill_xml_custom_data(customdata,cdef)


                uep.insert(idx,elm)
                idx += 1

        print("----------- end cell_def_tab.py: fill_xml(): ----------")