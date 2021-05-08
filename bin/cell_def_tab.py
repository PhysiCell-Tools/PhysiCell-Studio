"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)

--- Versions ---
0.1 - initial version
"""

import sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDoubleValidator

class CellDef(QWidget):
    def __init__(self):
        super().__init__()
        # global self.params_cell_def

        # primary key = cell def name
        # secondary keys: cycle_rate_choice, cycle_dropdown, 
        self.param_d = {}  # a dict of dicts

        self.current_cell_def = None
        self.new_cell_def_count = 1
        self.label_width = 210
        self.units_width = 70
        self.idx_current_cell_def = 1  # 1-offset for XML
        self.xml_root = None
        self.custom_data_count = 0
        self.custom_data_units_width = 90
        self.cycle_duration_flag = False

        self.stacked_cycle = QStackedWidget()
        # transition rates
        self.stack_idx_t00 = -1
        self.stack_idx_t01 = -1
        self.stack_idx_t02 = -1
        self.stack_idx_t03 = -1

        # duration rates
        self.stack_idx_d00 = -1
        self.stack_idx_d01 = -1
        self.stack_idx_d02 = -1
        self.stack_idx_d03 = -1

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

        tree_widget_width = 160
        tree_widget_height = 400
        # tree_widget_height = 1200

        self.tree = QTreeWidget() # tree is overkill; list would suffice; meh.
        # self.tree.setStyleSheet("background-color: lightgray")
        self.tree.setFixedWidth(tree_widget_width)
        self.tree.setFixedHeight(tree_widget_height)
        # self.tree.setColumnCount(1)
        self.tree.itemClicked.connect(self.tree_item_clicked_cb)

        header = QTreeWidgetItem(["---  Cell Type  ---"])
        self.tree.setHeaderItem(header)

        # cellname = QTreeWidgetItem(["epi cell"])
        # self.tree.insertTopLevelItem(0,cellname)

        # cellname = QTreeWidgetItem(["macrophage"])
        # self.tree.insertTopLevelItem(1,cellname)

        # cities =  QTreeWidgetItem(treeWidget)

        # titem = QTreeWidgetItem
        # titem.setText(0,'ttt')

        # header.setText(0,"epithelial cell")
        # header.setText(1,"macrophage")
        # self.tree.addTopLevelItem(QTreeWidgetItem("foo"))

        items = []
        model = QtCore.QStringListModel()
        model.setStringList(["aaa","bbb"])
        # self.tree.insertTopLevelItems(None, model)
        # slist = QtCore.QStringList()
        # for i in range(10):
        #     items.append(QTreeWidgetItem(None, QtGui.QStringList(QString("item: %1").arg(i))))
        # self.tree.insertTopLevelItems(None, items)

        # self.log_widget.setHeaderItem(QTreeWidgetItem(["date", "origin", "type", "message"]))


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
        # self.name_hbox = QHBoxLayout()
        # label = QLabel("Name of cell type:")
        # label.setFixedWidth(180)
        # label.setAlignment(QtCore.Qt.AlignRight)
        # self.name_hbox.addWidget(label)

        # self.cell_type_name = QLineEdit()
        # # Want to validate name, e.g., starts with alpha, no special chars, etc.
        # # self.cycle_trate0_0.setValidator(QtGui.QDoubleValidator())
        # # self.cycle_trate0_1.enter.connect(self.save_xml)
        # self.name_hbox.addWidget(self.cell_type_name)
        # # self.vbox.addLayout(hbox)

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
        self.tab_widget.addTab(self.create_motility_tab(),"Motlity")
        self.tab_widget.addTab(self.create_secretion_tab(),"Secretion")
        self.tab_widget.addTab(self.create_custom_data_tab(),"Custom Data")
        # self.tab_widget.tabBarClicked.connect(self.tabbar_clicked_cb)

        # lay = QVBoxLayout(self)
        # lay.setContentsMargins(5, 35, 5, 5)
        self.cell_types_tabs_layout = QGridLayout()
        self.cell_types_tabs_layout.addWidget(self.tab_widget, 0,0,1,1) # w, row, column, rowspan, colspan
        # self.setLayout(lay)
        # self.setMinimumSize(400, 320)

        # self.tab_widget.addTab(self.celldef_tab,"Cell Types")
        # self.tab_widget.addTab(self.user_params_tab,"User Params")
        # self.cell_types_tabs_hbox.addWidget(self.tab_widget)


        # self.vbox.addLayout(hbox)
        # self.vbox.addWidget(QHLine())

        #------------------
        # hbox = QHBoxLayout()
        # label = QLabel("Name of cell type:")
        # label.setFixedWidth(110)
        # label.setAlignment(QtCore.Qt.AlignRight)
        # hbox.addWidget(label)

        # self.cell_type_name = QLineEdit()
        # # Want to validate name, e.g., starts with alpha, no special chars, etc.
        # # self.cycle_trate0_0.setValidator(QtGui.QDoubleValidator())
        # # self.cycle_trate0_1.enter.connect(self.save_xml)
        # hbox.addWidget(self.cell_type_name)
        # self.vbox.addLayout(hbox)

        # self.create_cycle_tab()
        # self.create_death_tab()
        # self.create_volume_tab()
        # self.create_mechanics_tab()
        # self.create_motility_tab()
        # self.create_secretion_tab()
        # self.create_custom_data_tab()

        # # self.vbox.hide()
        # self.show_cycle_tab()

    #--------------------------------------------------------
    # def tabbar_clicked_cb(self,idx):
    #     print('tabbar_clicked_cb: idx=',idx)  # 0-indexed
    #     if idx==0:
    #         self.show_cycle_tab()
    #     elif idx==1:
    #         self.show_death_tab()
    #     elif idx==2:
    #         self.show_volume_tab()
    #     elif idx==3:
    #         self.show_mechanics_tab()
    #     elif idx==4:
    #         self.show_motility_tab()
    #     elif idx==5:
    #         self.show_secretion_tab()
    #     elif idx==6:
    #         self.show_custom_data_tab()

    #----------------------------------------------------------------------
    # @QtCore.Slot()
    def new_cell_def(self):
        print('------ new_cell_def')
        celldefname = "cell_def%02d" % self.new_cell_def_count
        # Make a new substrate (that's a copy of the currently selected one)
        self.param_d[celldefname] = self.param_d[self.current_cell_def].copy()

        for k in self.param_d.keys():
            print(" (pre-new vals)===>>> ",k, " : ", self.param_d[k])
        print()


        # Then "zero out" all entries(?)
        text = "0.0"
        self.param_d[celldefname]["death_rate"] = text

        self.param_d[celldefname]["volume_total"] = text

        print("\n ----- new dict:")
        for k in self.param_d.keys():
            print(" ===>>> ",k, " : ", self.param_d[k])

        self.new_cell_def_count += 1
        self.current_cell_def = celldefname

        #-----  Update this new cell def's widgets' values
        num_items = self.tree.invisibleRootItem().childCount()
        # print("tree has num_items = ",num_items)
        treeitem = QTreeWidgetItem([celldefname])
        treeitem.setFlags(treeitem.flags() | QtCore.Qt.ItemIsEditable)
        self.tree.insertTopLevelItem(num_items,treeitem)
        self.tree.setCurrentItem(treeitem)

        self.tree_item_clicked_cb(treeitem, 0)


    #----------------------------------------------------------------------
    # @QtCore.Slot()
    def copy_cell_def(self):
        print('------ copy_cell_def')
        celldefname = "cell_def%02d" % self.new_cell_def_count
        # Make a new cell_def (that's a copy of the currently selected one)
        self.param_d[celldefname] = self.param_d[self.current_cell_def].copy()

        for k in self.param_d.keys():
            print(" (pre-new vals)===>>> ",k, " : ", self.param_d[k])
        print()

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
    # @QtCore.Slot()
    def delete_cell_def(self):
        print('------ delete_cell_def')

        # rwh: is this safe?
        del self.param_d[self.current_cell_def]

        for k in self.param_d.keys():
            print(" ===>>> ",k, " : ", self.param_d[k])

        item_idx = self.tree.indexFromItem(self.tree.currentItem()).row() 
        print('------      item_idx=',item_idx)
        # self.tree.removeItemWidget(self.tree.currentItem(), 0)
        self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(self.tree.currentItem()))

        print('------      new name=',self.tree.currentItem().text(0))
        self.current_cell_def = self.tree.currentItem().text(0)


    #--------------------------------------------------------
    def create_cycle_tab(self):
        # self.group_cycle = QGroupBox()
        self.params_cycle = QWidget()
        self.vbox_cycle = QVBoxLayout()
        # glayout = QGridLayout()

        #----------------------------
        self.cycle_rate_duration_hbox = QHBoxLayout()
        self.rb1 = QRadioButton("transition rate(s)", self)
        # self.rb1.clicked.connect(self.cycle_phase_transition_cb)
        self.rb1.toggled.connect(self.cycle_phase_transition_cb)
        self.cycle_rate_duration_hbox.addWidget(self.rb1)
        self.rb2 = QRadioButton("duration(s)", self)
        # self.rb2.clicked.connect(self.cycle_phase_transition_cb)
        self.rb2.toggled.connect(self.cycle_phase_transition_cb)
        self.cycle_rate_duration_hbox.addWidget(self.rb2)
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
        self.stack_t00 = QWidget()
        self.stack_t01 = QWidget()
        self.stack_t02 = QWidget()
        self.stack_t03 = QWidget()

        # duration times
        self.stack_d00 = QWidget()
        self.stack_d01 = QWidget()
        self.stack_d02 = QWidget()
        self.stack_d03 = QWidget()


        #------ Cycle transition rate (1 node) ----------------------
        # self.cycle_dropdown.addItem("live cells")   # 0 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0->0 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # glayout.addWidget(*Widget, row, column, rowspan, colspan)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_trate00 = QLineEdit()
        self.cycle_trate00.textChanged.connect(self.cycle_trate00_changed)
        self.cycle_trate00.setValidator(QtGui.QDoubleValidator())
        # self.cycle_trate0_0.enter.connect(self.save_xml)
        glayout.addWidget(self.cycle_trate00, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_trate00_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_trate00_fixed, 0,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan
        # hbox.addWidget(units_1min)
        self.stack_t00.setLayout(glayout)   

        idx_stacked_widget = 0
        self.stack_idx_t00 = idx_stacked_widget 
        print(" new stacked widget: t00 -------------> ",idx_stacked_widget)
        self.stacked_cycle.addWidget(self.stack_t00)  # <------------- stack widget 0


        #------ Cycle transition rates (2 nodes) ----------------------
        # self.cycle_dropdown.addItem("basic Ki67")   # 0 -> 1, 1 -> 0
        # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0->1 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_trate01 = QLineEdit()
        self.cycle_trate01.textChanged.connect(self.cycle_trate01_changed)
        self.cycle_trate01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_trate01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_trate01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_trate01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1->0 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_trate10 = QLineEdit()
        self.cycle_trate10.textChanged.connect(self.cycle_trate10_changed)
        self.cycle_trate10.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_trate10, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_trate10_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_trate10_fixed, 1,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #-------
        # glayout.addWidget(QLabel("rwh-------------------------------AAAAAAAAAAAAAAAAAAAAAaa"), 2,0,4,4) # w, row, column, rowspan, colspan
        # glayout.addWidget(QLabel(""), 2,0,3,4) # w, row, column, rowspan, colspan
        # glayout.addStretch(0)

        #---
        self.stack_t01.setLayout(glayout)

        idx_stacked_widget += 1
        self.stack_idx_t01 = idx_stacked_widget 
        print(" new stacked widget: t01 -------------> ",idx_stacked_widget)
        self.stacked_cycle.addWidget(self.stack_t01) # <------------- stack widget 1


        #------ Cycle transition rates (3 nodes) ----------------------
        # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
        # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0->1 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_trate_02_01 = QLineEdit()
        self.cycle_trate_02_01.textChanged.connect(self.cycle_trate_02_01_changed)
        self.cycle_trate_02_01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_trate_02_01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_trate_02_01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_trate_02_01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1->2 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_trate_02_12 = QLineEdit()
        self.cycle_trate_02_12.textChanged.connect(self.cycle_trate_02_12_changed)
        self.cycle_trate_02_12.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_trate_02_12, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_trate_02_12_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_trate_02_12_fixed, 1,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 2->0 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 2,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_trate_02_20 = QLineEdit()
        self.cycle_trate_02_20.textChanged.connect(self.cycle_trate_02_20_changed)
        self.cycle_trate_02_20.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_trate_02_20, 2,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_trate_02_20_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_trate_02_20_fixed, 2,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 2,4,1,1) # w, row, column, rowspan, colspan

        #-----
        self.stack_t02.setLayout(glayout)
        idx_stacked_widget += 1
        print(" new stacked widget: t02 -------------> ",idx_stacked_widget)
        self.stack_idx_t02 = idx_stacked_widget 
        self.stacked_cycle.addWidget(self.stack_t02)


        #------ Cycle transition rates (4 nodes) ----------------------
        # self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0

        glayout = QGridLayout()

        label = QLabel("phase 0->1 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_trate_03_01 = QLineEdit()
        self.cycle_trate_03_01.textChanged.connect(self.cycle_trate_03_01_changed)
        self.cycle_trate_03_01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_trate_03_01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_trate_03_01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_trate_03_01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1->2 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_trate_03_12 = QLineEdit()
        self.cycle_trate_03_12.textChanged.connect(self.cycle_trate_03_12_changed)
        self.cycle_trate_03_12.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_trate_03_12, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_trate_03_12_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_trate_03_12_fixed, 1,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 2->3 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 2,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_trate_03_23 = QLineEdit()
        self.cycle_trate_03_23.textChanged.connect(self.cycle_trate_03_23_changed)
        self.cycle_trate_03_23.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_trate_03_23, 2,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_trate_03_23_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_trate_03_23_fixed, 2,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 2,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 3->0 transition rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 3,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_trate_03_30 = QLineEdit()
        self.cycle_trate_03_30.textChanged.connect(self.cycle_trate_03_30_changed)
        self.cycle_trate_03_30.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_trate_03_30, 3,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_trate_03_30_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_trate_03_30_fixed, 3,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 3,4,1,1) # w, row, column, rowspan, colspan

        #-----
        self.stack_t03.setLayout(glayout)
        idx_stacked_widget += 1
        print(" new stacked widget: t03 -------------> ",idx_stacked_widget)
        self.stack_idx_t03 = idx_stacked_widget 
        self.stacked_cycle.addWidget(self.stack_t03)


        #===========================================================================
        #------ Cycle duration rates ----------------------
        # self.cycle_dropdown.addItem("live cells")   # 0 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1)
        # glayout.addWidget(*Widget, row, column, rowspan, colspan)

        self.cycle_duration00 = QLineEdit()
        self.cycle_duration00.textChanged.connect(self.cycle_duration00_changed)
        self.cycle_duration00.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_duration00, 0,1,1,2)

        self.cycle_duration00_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_duration00_fixed, 0,3,1,1)

        units = QLabel("min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, 0,4,1,1)

        #-----
        self.stack_d00.setLayout(glayout)
        idx_stacked_widget += 1
        print(" new stacked widget: d00 -------------> ",idx_stacked_widget)
        self.stack_idx_d00 = idx_stacked_widget 
        self.stacked_cycle.addWidget(self.stack_d00)


        #------ Cycle duration rates (2 nodes) ----------------------
        # self.cycle_dropdown.addItem("basic Ki67")   # 0 -> 1, 1 -> 0
        # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_duration01 = QLineEdit()
        self.cycle_duration01.textChanged.connect(self.cycle_duration01_changed)
        self.cycle_duration01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_duration01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_duration01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_duration01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_duration10 = QLineEdit()
        self.cycle_duration10.textChanged.connect(self.cycle_duration10_changed)
        self.cycle_duration10.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_duration10, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_duration10_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_duration10_fixed, 1,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        # glayout.addWidget(QLabel(""), 2,0,1,1) # w, row, column, rowspan, colspan

        #-------
        self.stack_d01.setLayout(glayout)

        idx_stacked_widget += 1
        print(" new stacked widget: d01 -------------> ",idx_stacked_widget)
        self.stack_idx_d01 = idx_stacked_widget 
        self.stacked_cycle.addWidget(self.stack_d01)


        #------ Cycle duration (3 nodes) ----------------------
        # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
        # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0

        glayout = QGridLayout()

        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_duration_02_01 = QLineEdit()
        self.cycle_duration_02_01.textChanged.connect(self.cycle_duration_02_01_changed)
        self.cycle_duration_02_01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_duration_02_01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_duration_02_01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_duration_02_01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_duration_02_12 = QLineEdit()
        self.cycle_duration_02_12.textChanged.connect(self.cycle_duration_02_12_changed)
        self.cycle_duration_02_12.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_duration_02_12, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_duration_02_12_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_duration_02_12_fixed, 1,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 2 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 2,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_duration_02_20 = QLineEdit()
        self.cycle_duration_02_20.textChanged.connect(self.cycle_duration_02_20_changed)
        self.cycle_duration_02_20.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_duration_02_20, 2,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_duration_02_20_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_duration_02_20_fixed, 2,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 2,4,1,1) # w, row, column, rowspan, colspan

        #-----
        self.stack_d02.setLayout(glayout)

        idx_stacked_widget += 1
        print(" new stacked widget: d02 -------------> ",idx_stacked_widget)
        self.stack_idx_d02 = idx_stacked_widget 
        self.stacked_cycle.addWidget(self.stack_d02) 


        #------ Cycle duration (4 nodes) ----------------------
        # self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0

        glayout = QGridLayout()

        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_duration_03_01 = QLineEdit()
        self.cycle_duration_03_01.textChanged.connect(self.cycle_duration_03_01_changed)
        self.cycle_duration_03_01.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_duration_03_01, 0,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_duration_03_01_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_duration_03_01_fixed, 0,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 0,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 1 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 1,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_duration_03_12 = QLineEdit()
        self.cycle_duration_03_12.textChanged.connect(self.cycle_duration_03_12_changed)
        self.cycle_duration_03_12.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_duration_03_12, 1,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_duration_03_12_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_duration_03_12_fixed, 1,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 1,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 2 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 2,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_duration_03_23 = QLineEdit()
        self.cycle_duration_03_23.textChanged.connect(self.cycle_duration_03_23_changed)
        self.cycle_duration_03_23.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_duration_03_23, 2,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_duration_03_23_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_duration_03_23_fixed, 2,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 2,4,1,1) # w, row, column, rowspan, colspan

        #-------
        label = QLabel("phase 3 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        glayout.addWidget(label, 3,0,1,1) # w, row, column, rowspan, colspan

        self.cycle_duration_03_30 = QLineEdit()
        self.cycle_duration_03_30.textChanged.connect(self.cycle_duration_03_30_changed)
        self.cycle_duration_03_30.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.cycle_duration_03_30, 3,1,1,2) # w, row, column, rowspan, colspan

        self.cycle_duration_03_30_fixed = QCheckBox("Fixed")
        glayout.addWidget(self.cycle_duration_03_30_fixed, 3,3,1,1) # w, row, column, rowspan, colspan

        units = QLabel("min")
        units.setAlignment(QtCore.Qt.AlignCenter)
        units.setFixedWidth(self.units_width)
        glayout.addWidget(units, 3,4,1,1) # w, row, column, rowspan, colspan

        #-----
        self.stack_d03.setLayout(glayout)
        idx_stacked_widget += 1
        print(" new stacked widget: d03 -------------> ",idx_stacked_widget)
        self.stack_idx_d03 = idx_stacked_widget 
        self.stacked_cycle.addWidget(self.stack_d03)


        #---------------------------------------------
        # After adding all combos of cycle widgets (groups) to the stacked widget, 
        # add it to this panel.
        # self.vbox.addWidget(self.stacked)
        self.vbox_cycle.addWidget(self.stacked_cycle)

        # spacerItem = QSpacerItem(100,500)
        # self.vbox.addItem(spacerItem)
        self.vbox_cycle.addStretch()

        self.params_cycle.setLayout(self.vbox_cycle)

        return self.params_cycle
        # return cycle_tab

    #--------------------------------------------------------
    def create_death_tab(self):
        death_tab = QWidget()
        # layout = QVBoxLayout()
        glayout = QGridLayout()

        # label = QLabel("Phenotype: death")
        # label.setStyleSheet("background-color: orange")
        # label.setAlignment(QtCore.Qt.AlignCenter)
        # self.vbox.addWidget(label)
        # self.vbox.addWidget(QHLine())

        #----------------
        label = QLabel("Apoptosis")
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet('background-color: yellow')
        # layout.addWidget(apoptosis_label)
        idr = 0
        glayout.addWidget(label, idr,0, 1,4) # w, row, column, rowspan, colspan

        # hbox = QHBoxLayout()
        label = QLabel("death rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # hbox.addWidget(label)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_death_rate = QLineEdit()
        self.apoptosis_death_rate.textChanged.connect(self.apoptosis_death_rate_changed)
        self.apoptosis_death_rate.setValidator(QtGui.QDoubleValidator())
        # self.apoptosis_death_rate.textChanged.connect(self.apop_death_rate_changed)
        # hbox.addWidget(self.apoptosis_death_rate)
        glayout.addWidget(self.apoptosis_death_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # hbox.addWidget(units)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # layout.addLayout(hbox)

        # <cycle code="6" name="Flow cytometry model (separated)">  
        #     <phase_durations units="min"> 
        #         <duration index="0" fixed_duration="false">300.0</duration>
        #         <duration index="1" fixed_duration="true">480</duration>
        #         <duration index="2" fixed_duration="true">240</duration>
        #         <duration index="3" fixed_duration="true">60</duration>
        #     </phase_durations>

        # self.apoptosis_phase0_duration_hbox = QHBoxLayout()
        label = QLabel("phase 0 duration")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
    #    self.apoptosis_phase0_duration_hbox.addWidget(label)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_phase0_duration = QLineEdit()
        self.apoptosis_phase0_duration.textChanged.connect(self.apoptosis_phase0_duration_changed)
        self.apoptosis_phase0_duration.setValidator(QtGui.QDoubleValidator())
        # self.apoptosis_phase0_duration.textChanged.connect(self.apop_phase0_changed)
        # self.apoptosis_phase0_duration_hbox.addWidget(self.apoptosis_phase0_duration)
        glayout.addWidget(self.apoptosis_phase0_duration, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_phase0_duration_fixed = QCheckBox("Fixed")
        self.apoptosis_phase0_duration_fixed.toggled.connect(self.apoptosis_phase0_duration_fixed_toggled)
        # self.apoptosis_phase0_duration_hbox.addWidget(self.apoptosis_phase0_duration_fixed)
        glayout.addWidget(self.apoptosis_phase0_duration_fixed, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan
        # self.apoptosis_phase0_duration_hbox.addWidget(units)
        #-------
        # <phase_durations units="min">
        #     <duration index="0" fixed_duration="true">516</duration>

        # <unlysed_fluid_change_rate units="1/min">0.05</unlysed_fluid_change_rate>
        # <lysed_fluid_change_rate units="1/min">0</lysed_fluid_change_rate>
        # <cytoplasmic_biomass_change_rate units="1/min">1.66667e-02</cytoplasmic_biomass_change_rate>
        # <nuclear_biomass_change_rate units="1/min">5.83333e-03</nuclear_biomass_change_rate>
        # <calcification_rate units="1/min">0</calcification_rate>
        # <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>
        # self.apoptosis_unlysed_rate_hbox = QHBoxLayout()
        label = QLabel("unlysed fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        # self.apoptosis_unlysed_rate_hbox.addWidget(label)
        self.apoptosis_unlysed_rate = QLineEdit()
        self.apoptosis_unlysed_rate.textChanged.connect(self.apoptosis_unlysed_rate_changed)
        self.apoptosis_unlysed_rate.setValidator(QtGui.QDoubleValidator())
        # self.apoptosis_unlysed_rate.textChanged.connect(self.apop_unlysed_changed)
        # self.apoptosis_unlysed_rate_hbox.addWidget(self.apoptosis_unlysed_rate)
        glayout.addWidget(self.apoptosis_unlysed_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.apoptosis_unlysed_rate_hbox.addWidget(units)
        # self.vbox.addLayout(self.apoptosis_unlysed_rate_hbox)

        # self.apoptosis_lysed_rate_hbox = QHBoxLayout()
        label = QLabel("lysed fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan
        # self.apoptosis_lysed_rate_hbox.addWidget(label)

        self.apoptosis_lysed_rate = QLineEdit()
        self.apoptosis_lysed_rate.textChanged.connect(self.apoptosis_lysed_rate_changed)
        self.apoptosis_lysed_rate.setValidator(QtGui.QDoubleValidator())
        # self.apoptosis_lysed_rate.textChanged.connect(self.apop_lysed_changed)
        glayout.addWidget(self.apoptosis_lysed_rate, idr,1, 1,1) # w, row, column, rowspan, colspan
        # self.apoptosis_lysed_rate_hbox.addWidget(self.apoptosis_lysed_rate)
        units = QLabel("1/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.apoptosis_lysed_rate_hbox.addWidget(units)
        # self.vbox.addLayout(self.apoptosis_lysed_rate_hbox)

        # self.apoptosis_cytoplasmic_hbox = QHBoxLayout()
        label = QLabel("cytoplasmic biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan
        # self.apoptosis_cytoplasmic_hbox.addWidget(label)

        self.apoptosis_cytoplasmic_biomass_change_rate = QLineEdit()
        self.apoptosis_cytoplasmic_biomass_change_rate.textChanged.connect(self.apoptosis_cytoplasmic_biomass_change_rate_changed)
        self.apoptosis_cytoplasmic_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        # self.apoptosis_cytoplasmic_biomass_change_rate.textChanged.connect(self.apop_cyto_changed)
        glayout.addWidget(self.apoptosis_cytoplasmic_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan
        # self.apoptosis_cytoplasmic_hbox.addWidget(self.apoptosis_cytoplasmic_biomass_change_rate)

        units = QLabel("1/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.apoptosis_cytoplasmic_hbox.addWidget(units)
        # self.vbox.addLayout(self.apoptosis_cytoplasmic_biomass_change_rate_hbox)

        # <nuclear_biomass_change_rate units="1/min">5.83333e-03</nuclear_biomass_change_rate>
        # <calcification_rate units="1/min">0</calcification_rate>
        # <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>

        # self.apoptosis_nuclear_hbox = QHBoxLayout()
        label = QLabel("nuclear biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # self.apoptosis_nuclear_hbox.addWidget(label)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_nuclear_biomass_change_rate = QLineEdit()
        self.apoptosis_nuclear_biomass_change_rate.textChanged.connect(self.apoptosis_nuclear_biomass_change_rate_changed)
        self.apoptosis_nuclear_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        # self.apoptosis_nuclear_biomass_change_rate.textChanged.connect(self.apop_nuclear_changed)
        # self.apoptosis_nuclear_hbox.addWidget(self.apoptosis_nuclear_biomass_change_rate)
        glayout.addWidget(self.apoptosis_nuclear_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # self.apoptosis_nuclear_hbox.addWidget(units)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.vbox.addLayout(hbox)

        # self.apoptosis_calcification_hbox = QHBoxLayout()
        label = QLabel("calcification rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # self.apoptosis_calcification_hbox.addWidget(label)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_calcification_rate = QLineEdit()
        self.apoptosis_calcification_rate.textChanged.connect(self.apoptosis_calcification_rate_changed)
        self.apoptosis_calcification_rate.setValidator(QtGui.QDoubleValidator())
        # self.apoptosis_calcification_rate.textChanged.connect(self.apop_calcif_changed)
        # self.apoptosis_calcification_hbox.addWidget(self.apoptosis_calcification_rate)
        glayout.addWidget(self.apoptosis_calcification_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # self.apoptosis_calcification_hbox.addWidget(units)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.vbox.addLayout(hbox)

        # self.apoptosis_rel_rupture_volume_hbox = QHBoxLayout()
        label = QLabel("relative rupture volume")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # self.apoptosis_rel_rupture_volume_hbox.addWidget(label)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.apoptosis_relative_rupture_volume = QLineEdit()
        self.apoptosis_relative_rupture_volume.textChanged.connect(self.apoptosis_relative_rupture_volume_changed)
        self.apoptosis_relative_rupture_volume.setValidator(QtGui.QDoubleValidator())
        # self.apoptosis_relative_rupture_volume.textChanged.connect(self.apop_rupture_changed)
        # self.apoptosis_rel_rupture_volume_hbox.addWidget(self.apoptosis_relative_rupture_volume)
        glayout.addWidget(self.apoptosis_relative_rupture_volume, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # self.apoptosis_rel_rupture_volume_hbox.addWidget(units)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.vbox.addLayout(hbox)

        #----------------
        label = QLabel("Necrosis")
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet('background-color: yellow')
        idr += 1
        glayout.addWidget(label, idr,0, 1,4) # w, row, column, rowspan, colspan

        label = QLabel("death rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # hbox.addWidget(label)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_death_rate = QLineEdit()
        self.necrosis_death_rate.textChanged.connect(self.necrosis_death_rate_changed)
        self.necrosis_death_rate.setValidator(QtGui.QDoubleValidator())
        # hbox.addWidget(self.necrosis_death_rate)
        glayout.addWidget(self.necrosis_death_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # hbox.addWidget(units)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # layout.addLayout(hbox)

        # <cycle code="6" name="Flow cytometry model (separated)">  
        #     <phase_durations units="min"> 
        #         <duration index="0" fixed_duration="false">300.0</duration>
        #         <duration index="1" fixed_duration="true">480</duration>
        #         <duration index="2" fixed_duration="true">240</duration>
        #         <duration index="3" fixed_duration="true">60</duration>
        #     </phase_durations>

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
        # self.necrosis_phase0_duration_hbox.addWidget(self.necrosis_phase0_duration)
        glayout.addWidget(self.necrosis_phase0_duration, idr,1, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_phase0_duration_fixed = QCheckBox("Fixed")
        # self.necrosis_phase0_duration_hbox.addWidget(self.necrosis_phase0_duration_fixed)
        glayout.addWidget(self.necrosis_phase0_duration_fixed, idr,2, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan
        # self.necrosis_phase0_duration_hbox.addWidget(units)

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

        units = QLabel("min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignCenter)
        glayout.addWidget(units, idr,3, 1,1) # w, row, column, rowspan, colspan

        #-------
        # <phase_durations units="min">
        #     <duration index="0" fixed_duration="true">516</duration>

        # <unlysed_fluid_change_rate units="1/min">0.05</unlysed_fluid_change_rate>
        # <lysed_fluid_change_rate units="1/min">0</lysed_fluid_change_rate>
        # <cytoplasmic_biomass_change_rate units="1/min">1.66667e-02</cytoplasmic_biomass_change_rate>
        # <nuclear_biomass_change_rate units="1/min">5.83333e-03</nuclear_biomass_change_rate>
        # <calcification_rate units="1/min">0</calcification_rate>
        # <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>
        # self.necrosis_unlysed_rate_hbox = QHBoxLayout()
        label = QLabel("unlysed fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        # self.necrosis_unlysed_rate_hbox.addWidget(label)
        self.necrosis_unlysed_rate = QLineEdit()
        self.necrosis_unlysed_rate.textChanged.connect(self.necrosis_unlysed_rate_changed)
        self.necrosis_unlysed_rate.setValidator(QtGui.QDoubleValidator())
        # self.necrosis_unlysed_rate_hbox.addWidget(self.necrosis_unlysed_rate)
        glayout.addWidget(self.necrosis_unlysed_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.necrosis_unlysed_rate_hbox.addWidget(units)
        # self.vbox.addLayout(self.necrosis_unlysed_rate_hbox)

        # self.necrosis_lysed_rate_hbox = QHBoxLayout()
        label = QLabel("lysed fluid change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan
        # self.necrosis_lysed_rate_hbox.addWidget(label)

        self.necrosis_lysed_rate = QLineEdit()
        self.necrosis_lysed_rate.textChanged.connect(self.necrosis_lysed_rate_changed)
        self.necrosis_lysed_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_lysed_rate, idr,1, 1,1) # w, row, column, rowspan, colspan
        # self.necrosis_lysed_rate_hbox.addWidget(self.necrosis_lysed_rate)
        units = QLabel("1/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.necrosis_lysed_rate_hbox.addWidget(units)
        # self.vbox.addLayout(self.necrosis_lysed_rate_hbox)

        # self.necrosis_cytoplasmic_hbox = QHBoxLayout()
        label = QLabel("cytoplasmic biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan
        # self.necrosis_cytoplasmic_hbox.addWidget(label)

        self.necrosis_cytoplasmic_biomass_change_rate = QLineEdit()
        self.necrosis_cytoplasmic_biomass_change_rate.textChanged.connect(self.necrosis_cytoplasmic_biomass_change_rate_changed)
        self.necrosis_cytoplasmic_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        glayout.addWidget(self.necrosis_cytoplasmic_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan
        # self.necrosis_cytoplasmic_hbox.addWidget(self.necrosis_cytoplasmic_biomass_change_rate)

        units = QLabel("1/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.necrosis_cytoplasmic_hbox.addWidget(units)
        # self.vbox.addLayout(self.necrosis_cytoplasmic_biomass_change_rate_hbox)

        # <nuclear_biomass_change_rate units="1/min">5.83333e-03</nuclear_biomass_change_rate>
        # <calcification_rate units="1/min">0</calcification_rate>
        # <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>

        # self.necrosis_nuclear_hbox = QHBoxLayout()
        label = QLabel("nuclear biomass change rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # self.necrosis_nuclear_hbox.addWidget(label)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_nuclear_biomass_change_rate = QLineEdit()
        self.necrosis_nuclear_biomass_change_rate.textChanged.connect(self.necrosis_nuclear_biomass_change_rate_changed)
        self.necrosis_nuclear_biomass_change_rate.setValidator(QtGui.QDoubleValidator())
        # self.necrosis_nuclear_hbox.addWidget(self.necrosis_nuclear_biomass_change_rate)
        glayout.addWidget(self.necrosis_nuclear_biomass_change_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # self.necrosis_nuclear_hbox.addWidget(units)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.vbox.addLayout(hbox)

        # self.necrosis_calcification_hbox = QHBoxLayout()
        label = QLabel("calcification rate")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # self.necrosis_calcification_hbox.addWidget(label)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_calcification_rate = QLineEdit()
        self.necrosis_calcification_rate.textChanged.connect(self.necrosis_calcification_rate_changed)
        self.necrosis_calcification_rate.setValidator(QtGui.QDoubleValidator())
        # self.necrosis_calcification_hbox.addWidget(self.necrosis_calcification_rate)
        glayout.addWidget(self.necrosis_calcification_rate, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("1/min")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # self.necrosis_calcification_hbox.addWidget(units)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.vbox.addLayout(hbox)

        # self.necrosis_rel_rupture_volume_hbox = QHBoxLayout()
        label = QLabel("relative rupture volume")
        label.setFixedWidth(self.label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        # self.necrosis_rel_rupture_volume_hbox.addWidget(label)
        idr += 1
        glayout.addWidget(label, idr,0, 1,1) # w, row, column, rowspan, colspan

        self.necrosis_relative_rupture_volume = QLineEdit()
        self.necrosis_relative_rupture_volume.textChanged.connect(self.necrosis_relative_rupture_volume_changed)
        self.necrosis_relative_rupture_volume.setValidator(QtGui.QDoubleValidator())
        # self.necrosis_rel_rupture_volume_hbox.addWidget(self.necrosis_relative_rupture_volume)
        glayout.addWidget(self.necrosis_relative_rupture_volume, idr,1, 1,1) # w, row, column, rowspan, colspan

        units = QLabel("")
        units.setFixedWidth(self.units_width)
        units.setAlignment(QtCore.Qt.AlignLeft)
        # self.necrosis_rel_rupture_volume_hbox.addWidget(units)
        glayout.addWidget(units, idr,2, 1,1) # w, row, column, rowspan, colspan



        glayout.setVerticalSpacing(10)  # rwh - argh
        death_tab.setLayout(glayout)
        return death_tab

    #--------------------------------------------------------
    def apop_death_rate_changed(self, text):
        print("----- apop_death_rate_changed: self.current_cell_def = ",self.current_cell_def)
        self.param_d[self.current_cell_def]["apop_death_rate"] = text
    def apop_phase0_changed(self, text):
        self.param_d[self.current_cell_def]["apop_phase0"] = text
    def apop_unlysed_changed(self, text):
        self.param_d[self.current_cell_def]["apop_unlysed"] = text
    def apop_lysed_changed(self, text):
        self.param_d[self.current_cell_def]["apop_lysed"] = text
    def apop_cyto_changed(self, text):
        self.param_d[self.current_cell_def]["apop_cyto"] = text
    def apop_nuclear_changed(self, text):
        self.param_d[self.current_cell_def]["apop_nuclear"] = text
    def apop_calcif_changed(self, text):
        self.param_d[self.current_cell_def]["apop_calcif"] = text
    def apop_rupture_changed(self, text):
        self.param_d[self.current_cell_def]["apop_rupture"] = text

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
        label.setFixedWidth(self.label_width)
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

        units = QLabel("min")
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
        self.motility_enabled = QCheckBox("enable")
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
        # self.cycle_dropdown.currentIndex.connect(self.cycle_changed_cb)
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
        # self.cycle_dropdown.currentIndex.connect(self.cycle_changed_cb)
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
        units = QLabel("sub density")
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
    # The following (text-based widgets) were auto-generated by the gen_qline_cb.py script
    # --- cycle
    def cycle_trate00_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_trate00'] = text
    def cycle_trate01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_trate01'] = text
    def cycle_trate10_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_trate10'] = text
    def cycle_trate_02_01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_trate_02_01'] = text
    def cycle_trate_02_12_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_trate_02_12'] = text
    def cycle_trate_02_20_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_trate_02_20'] = text
    def cycle_trate_03_01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_trate_03_01'] = text
    def cycle_trate_03_12_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_trate_03_12'] = text
    def cycle_trate_03_23_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_trate_03_23'] = text
    def cycle_trate_03_30_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_trate_03_30'] = text
    def cycle_duration00_changed(self, text):
        print("---- cycle_duration00_changed(self, text): self.current_cell_def = ",self.current_cell_def)
        print("---- self.param_d = ",self.param_d)
        self.param_d[self.current_cell_def]['cycle_duration00'] = text
    def cycle_duration01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_duration01'] = text
    def cycle_duration10_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_duration10'] = text
    def cycle_duration_02_01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_duration_02_01'] = text
    def cycle_duration_02_12_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_duration_02_12'] = text
    def cycle_duration_02_20_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_duration_02_20'] = text
    def cycle_duration_03_01_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_duration_03_01'] = text
    def cycle_duration_03_12_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_duration_03_12'] = text
    def cycle_duration_03_23_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_duration_03_23'] = text
    def cycle_duration_03_30_changed(self, text):
        self.param_d[self.current_cell_def]['cycle_duration_03_30'] = text

    # --- death
    def apoptosis_death_rate_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_death_rate'] = text
    def apoptosis_phase0_duration_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_phase0_duration'] = text
    def apoptosis_phase0_duration_fixed_toggled(self, b):
        self.param_d[self.current_cell_def]['apoptosis_phase0_fixed'] = b

    def apoptosis_unlysed_rate_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_unlysed_rate'] = text
    def apoptosis_lysed_rate_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_lysed_rate'] = text
    def apoptosis_cytoplasmic_biomass_change_rate_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_cytoplasmic_biomass_change_rate'] = text
    def apoptosis_nuclear_biomass_change_rate_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_nuclear_biomass_change_rate'] = text
    def apoptosis_calcification_rate_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_calcification_rate'] = text
    def apoptosis_relative_rupture_volume_changed(self, text):
        self.param_d[self.current_cell_def]['apoptosis_relative_rupture_volume'] = text
    def necrosis_death_rate_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_death_rate'] = text
    def necrosis_phase0_duration_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_phase0_duration'] = text
    def necrosis_phase1_duration_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_phase1_duration'] = text
    def necrosis_unlysed_rate_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_unlysed_rate'] = text
    def necrosis_lysed_rate_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_lysed_rate'] = text
    def necrosis_cytoplasmic_biomass_change_rate_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_cytoplasmic_biomass_change_rate'] = text
    def necrosis_nuclear_biomass_change_rate_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_nuclear_biomass_change_rate'] = text
    def necrosis_calcification_rate_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_calcification_rate'] = text
    def necrosis_relative_rupture_volume_changed(self, text):
        self.param_d[self.current_cell_def]['necrosis_relative_rupture_volume'] = text

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
        self.param_d[self.current_cell_def]['volume_cytoplasmic_biomass_change_rate'] = text
    def volume_nuclear_biomass_change_rate_changed(self, text):
        self.param_d[self.current_cell_def]['volume_nuclear_biomass_change_rate'] = text
    def volume_calcified_fraction_changed(self, text):
        self.param_d[self.current_cell_def]['volume_calcified_fraction'] = text
    def volume_calcification_rate_changed(self, text):
        self.param_d[self.current_cell_def]['volume_calcification_rate'] = text
    def relative_rupture_volume_changed(self, text):
        self.param_d[self.current_cell_def]['relative_rupture_volume'] = text

    # --- mechanics
    def cell_cell_adhesion_strength_changed(self, text):
        self.param_d[self.current_cell_def]['cell_cell_adhesion_strength'] = text
    def cell_cell_repulsion_strength_changed(self, text):
        self.param_d[self.current_cell_def]['cell_cell_repulsion_strength'] = text
    def relative_maximum_adhesion_distance_changed(self, text):
        self.param_d[self.current_cell_def]['relative_maximum_adhesion_distance'] = text
    def set_relative_equilibrium_distance_changed(self, text):
        self.param_d[self.current_cell_def]['set_relative_equilibrium_distance'] = text
    def set_absolute_equilibrium_distance_changed(self, text):
        self.param_d[self.current_cell_def]['set_absolute_equilibrium_distance'] = text

    # insert callbacks for QCheckBoxes
    def set_absolute_equilibrium_distance_enabled_cb(self,bval):
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

        # self.param_d[cell_def_name]['secretion'][substrate_name]["secretion_rate"] = val
        self.param_d[self.current_cell_def]['secretion'][self.current_secretion_substrate]['secretion_rate'] = text
    def secretion_target_changed(self, text):
        self.param_d[self.current_cell_def]['secretion_target'] = text
    def uptake_rate_changed(self, text):
        self.param_d[self.current_cell_def]['uptake_rate'] = text
    def secretion_net_export_rate_changed(self, text):
        self.param_d[self.current_cell_def]['secretion_net_export_rate'] = text

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
        
        w = QLabel("Units(r/o)")
        w.setAlignment(QtCore.Qt.AlignCenter)
        w.setStyleSheet("color: Salmon")  # PaleVioletRed")
        # hbox.addWidget(w)
        glayout.addWidget(w, idr,2, 1,1) # w, row, column, rowspan, colspan

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
        self.custom_data_units = []

        for idx in range(10):   # rwh/TODO - this should depend on how many in the .xml
            # self.main_layout.addLayout(NewUserParam(self))
            # hbox = QHBoxLayout()
            # w = QCheckBox("")
            # self.custom_data_select.append(w)
            # hbox.addWidget(w)

            w = QLineEdit()
            w.setStyleSheet("background-color: Salmon")  # PaleVioletRed")
            w.setReadOnly(True)
            self.custom_data_name.append(w)
            # self.name.setValidator(QtGui.QDoubleValidator())
            # self.diffusion_coef.enter.connect(self.save_xml)
            # hbox.addWidget(w)
            idr += 1
            glayout.addWidget(w, idr,0, 1,1) # w, row, column, rowspan, colspan
            # if idx == 0:
            #     w.setText("random_seed")

            w = QLineEdit()
            w.setValidator(QtGui.QDoubleValidator())
            self.custom_data_value.append(w)
            # w.setValidator(QtGui.QDoubleValidator())
            # if idx == 0:
            #     w.setText("0")
            # hbox.addWidget(w)
            glayout.addWidget(w, idr,1, 1,1) # w, row, column, rowspan, colspan

            w = QLineEdit()
            w.setStyleSheet("background-color: Salmon")  # PaleVioletRed")
            w.setReadOnly(True)
            w.setFixedWidth(self.custom_data_units_width)
            self.custom_data_units.append(w)
            # hbox.addWidget(w)
            glayout.addWidget(w, idr,2, 1,1) # w, row, column, rowspan, colspan

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
    def clear_custom_data_tab(self):
        # pass
        for idx in range(self.custom_data_count):
            self.custom_data_name[idx].setReadOnly(False)
            self.custom_data_name[idx].setText("")
            self.custom_data_name[idx].setReadOnly(True)

            self.custom_data_value[idx].setText("")

            self.custom_data_units[idx].setReadOnly(False)
            self.custom_data_units[idx].setText("")
            self.custom_data_units[idx].setReadOnly(True)
        
        self.custom_data_count = 0

    #--------------------------------------------------------
    # This is done in cell_custom_data_tab.py: fill_gui() 
    def fill_custom_data_tab(self):
    #     pass
        # uep_custom_data = self.xml_root.find(".//cell_definitions//cell_definition[1]//custom_data")
        uep_cell_defs = self.xml_root.find(".//cell_definitions")
        print('--- cell_def_tab.py: fill_custom_data_tab(): uep_cell_defs= ',uep_cell_defs )

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
                print(idx, ") ",var)
                self.custom_data_name[idx].setText(var.tag)
                print("tag=",var.tag)
                self.custom_data_value[idx].setText(var.text)

                if 'units' in var.keys():
                    self.custom_data_units[idx].setText(var.attrib['units'])
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
        print('------ cycle_changed_cb(): idx = ',idx)
        # self.param_d[self.current_cell_def]['cycle'] = 
        self.customize_cycle_choices()
        # QMessageBox.information(self, "Cycle Changed:",
                #   "Current Cycle Index: %d" % idx )

    # @QtCore.Slot()
    def motility_substrate_changed_cb(self, idx):
        print('------ motility_substrate_changed_cb(): idx = ',idx)
        print(self.motility_substrate_dropdown.currentText())
        if idx == -1:
            return

    # @QtCore.Slot()
    def secretion_substrate_changed_cb(self, idx):
        print('------ secretion_substrate_changed_cb(): idx = ',idx)
        self.current_secretion_substrate = self.secretion_substrate_dropdown.currentText()
        print("    self.current_secretion_substrate = ",self.current_secretion_substrate)
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
        print("self.cycle_dropdown.currentIndex() = ",self.cycle_dropdown.currentIndex())

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
        

        # self.cycle_dropdown.addItem("live cells")   # 0 -> 0
        # self.cycle_dropdown.addItem("basic Ki67")   # 0 -> 1, 1 -> 0
        # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
        # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0
        # self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0
        # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0
    def customize_cycle_choices(self):

        if self.cycle_duration_flag:  # specifying duration times (radio button)
            if self.cycle_dropdown.currentIndex() == 0:  # live
                print("customize_cycle_choices():  idx = ",self.stack_idx_d00)
                self.stacked_cycle.setCurrentIndex(self.stack_idx_d00)
            elif (self.cycle_dropdown.currentIndex() == 1) or (self.cycle_dropdown.currentIndex() == 5):  # basic Ki67 or cycling quiescent
                print("customize_cycle_choices():  idx = ",self.stack_idx_d01)
                self.stacked_cycle.setCurrentIndex(self.stack_idx_d01)
            elif (self.cycle_dropdown.currentIndex() == 2) or (self.cycle_dropdown.currentIndex() == 3):  # advanced Ki67 or flow cytometry
                print("customize_cycle_choices():  idx = ",self.stack_idx_d02)
                self.stacked_cycle.setCurrentIndex(self.stack_idx_d02)
            elif (self.cycle_dropdown.currentIndex() == 4):  # flow cytometry separated
                print("customize_cycle_choices():  idx = ",self.stack_idx_d03)
                self.stacked_cycle.setCurrentIndex(self.stack_idx_d03)

        else:  # specifying transition rates (radio button)
            if self.cycle_dropdown.currentIndex() == 0:  # live
                print("customize_cycle_choices():  idx = ",self.stack_idx_t00)
                self.stacked_cycle.setCurrentIndex(self.stack_idx_t00)
            elif (self.cycle_dropdown.currentIndex() == 1) or (self.cycle_dropdown.currentIndex() == 5):  # basic Ki67 or cycling quiescent
                print("customize_cycle_choices():  idx = ",self.stack_idx_t01)
                self.stacked_cycle.setCurrentIndex(self.stack_idx_t01)
            elif (self.cycle_dropdown.currentIndex() == 2) or (self.cycle_dropdown.currentIndex() == 3):  # advanced Ki67 or flow cytometry
                print("customize_cycle_choices():  idx = ",self.stack_idx_t02)
                self.stacked_cycle.setCurrentIndex(self.stack_idx_t02)
            elif (self.cycle_dropdown.currentIndex() == 4):  # flow cytometry separated
                print("customize_cycle_choices():  idx = ",self.stack_idx_t03)
                self.stacked_cycle.setCurrentIndex(self.stack_idx_t03)

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

    #---------------------------------
    # def fill_motility_substrates(self):
    def fill_substrates_comboboxes(self):
        print("cell_def_tab.py: ------- fill_substrates_comboboxes")
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
                self.motility_substrate_dropdown.addItem(name)
                self.secretion_substrate_dropdown.addItem(name)

    # def delete_substrate_from_comboboxes(self, name):
    def delete_substrate_from_comboboxes(self, item_idx):
        # print("------- delete_substrate_from_comboboxes: name=",name)
        print("------- delete_substrate_from_comboboxes: name=",item_idx)
        self.motility_substrate_dropdown.removeItem(item_idx)
        self.secretion_substrate_dropdown.removeItem(item_idx)
        # self.motility_substrate_dropdown.clear()
        # self.secretion_substrate_dropdown.clear()

    #-----------------------------------------------------------------------------------------
    def update_cycle_params(self):
        # pass
        cdname = self.current_cell_def
        if 'live' in self.param_d[cdname]['cycle']:
            self.cycle_dropdown.setCurrentIndex(0)
        elif 'separated' in self.param_d[cdname]['cycle']:
            self.cycle_dropdown.setCurrentIndex(4)

                # if cycle_code == 0:
                #     self.cycle_dropdown.setCurrentIndex(2)
                #     self.param_d[cell_def_name]['cycle'] = 'advanced Ki67'
                # elif cycle_code == 1:
                #     self.cycle_dropdown.setCurrentIndex(1)
                #     self.param_d[cell_def_name]['cycle'] = 'basic Ki67'
                # elif cycle_code == 2:
                #     self.cycle_dropdown.setCurrentIndex(3)
                #     self.param_d[cell_def_name]['cycle'] = 'flow cytometry'
                # elif cycle_code == 5:
                #     self.cycle_dropdown.setCurrentIndex(0)
                #     self.param_d[cell_def_name]['cycle'] = 'live cells'
                # elif cycle_code == 6:
                #     self.cycle_dropdown.setCurrentIndex(4)
                #     self.param_d[cell_def_name]['cycle'] = 'flow cytometry separated'
                # elif cycle_code == 7:
                #     self.cycle_dropdown.setCurrentIndex(5)
                #     self.param_d[cell_def_name]['cycle'] = 'cycling quiescent'

    #     self.cycle_trate00.setText(rate.text)
    #     self.cycle_trate01.setText(rate.text)
    #     self.cycle_trate_02_12.setText(rate.text)
    #     self.cycle_trate_03_23.setText(rate.text)
    #     self.cycle_trate_03_30.setText(rate.text)

    #     self.rb2.setChecked(True)
    #     self.cycle_duration_flag = True
    #     self.customize_cycle_choices()

    #     self.cycle_duration00.setText(self.param_d[self.current_cell_def]['cycle_duration00'])
    #     self.cycle_duration01.setText(self.param_d[self.current_cell_def]['cycle_duration01'])

    #     self.cycle_duration_02_01.setText(self.param_d[cell_def_name]['cycle_duration_02_01'])
    #     self.cycle_duration_03_01.setText(self.param_d[cell_def_name]['cycle_duration_03_01'])
    #     print("--> handling duration index=1")
    #     self.cycle_duration10.setText(pd.text)
    #     self.cycle_duration_02_12.setText(pd.text)
    #     self.cycle_duration_03_12.setText(pd.text)
    # elif  pd.attrib['index'] == "2":
    #     print("--> handling duration index=2")
    #     self.cycle_duration_02_20.setText(pd.text)
    #     self.cycle_duration_03_23.setText(pd.text)
    # elif  pd.attrib['index'] == "3":
    #     print("--> handling duration index=3")
    #     self.cycle_duration_03_30.setText(pd.text)

    #-----------------------------------------------------------------------------------------
    def update_death_params(self):
        cdname = self.current_cell_def
        self.apoptosis_death_rate.setText(self.param_d[cdname]["apoptosis_death_rate"])
        self.apoptosis_phase0_duration.setText(self.param_d[cdname]["apoptosis_phase0_duration"])
        self.apoptosis_phase0_duration_fixed.setChecked(self.param_d[cdname]["apoptosis_phase0_fixed"])

        self.apoptosis_unlysed_rate.setText(self.param_d[cdname]["apoptosis_unlysed_rate"])
        self.apoptosis_lysed_rate.setText(self.param_d[cdname]["apoptosis_lysed_rate"])
        self.apoptosis_cytoplasmic_biomass_change_rate.setText(self.param_d[cdname]["apoptosis_cyto_rate"])
        self.apoptosis_nuclear_biomass_change_rate.setText(self.param_d[cdname]["apoptosis_nuclear_rate"])
        self.apoptosis_calcification_rate.setText(self.param_d[cdname]["apoptosis_calcif_rate"])
        self.apoptosis_relative_rupture_volume.setText(self.param_d[cdname]["apoptosis_rel_rupture_rate"])

        #-----
        self.necrosis_death_rate.setText(self.param_d[cdname]["necrosis_death_rate"])
        self.necrosis_phase0_duration.setText(self.param_d[cdname]["necrosis_phase0_duration"])
        self.necrosis_phase0_duration_fixed.setChecked(self.param_d[cdname]["necrosis_phase0_fixed"])
        self.necrosis_phase1_duration.setText(self.param_d[cdname]["necrosis_phase1_duration"])
        self.necrosis_phase1_duration_fixed.setChecked(self.param_d[cdname]["necrosis_phase1_fixed"])

        self.necrosis_unlysed_rate.setText(self.param_d[cdname]["necrosis_unlysed_rate"])
        self.necrosis_lysed_rate.setText(self.param_d[cdname]["necrosis_lysed_rate"])
        self.necrosis_cytoplasmic_biomass_change_rate.setText(self.param_d[cdname]["necrosis_cyto_rate"])
        self.necrosis_nuclear_biomass_change_rate.setText(self.param_d[cdname]["necrosis_nuclear_rate"])
        self.necrosis_calcification_rate.setText(self.param_d[cdname]["necrosis_calcif_rate"])
        self.necrosis_relative_rupture_volume.setText(self.param_d[cdname]["necrosis_rel_rupture_rate"])

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
    def update_custom_data_params(self):
        pass
        # jdx = 0
        # for var in uep_custom_data:
        #     print(jdx, ") ",var)
        #     self.custom_data_name[jdx].setText(var.tag)

    #-----------------------------------------------------------------------------------------
    # User selects a cell def from the tree on the left. We need to fill in ALL widget values from param_d
    def tree_item_clicked_cb(self, it,col):
        print('\n\n------------ tree_item_clicked_cb -----------:', it, col, it.text(col) )
        self.current_cell_def = it.text(col)
        print('--- self.current_cell_def= ',self.current_cell_def )

        for k in self.param_d.keys():
            print(" ===>>> ",k, " : ", self.param_d[k])

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
                self.tree.insertTopLevelItem(idx,cellname)
                if idx == 0:  # select the 1st (0th) entry
                    self.tree.setCurrentItem(cellname)

                idx += 1

                # Now fill the param dict for each substrate and the Qt widget values for the 0th

                # death_path = ".//cell_definition[" + str(idx) + "]//phenotype//death//"
                # print('death_path=',death_path)

                # # rwh/TODO: validate we've got apoptosis or necrosis since order is not required in XML?
                # apoptosis_path = death_path + "model[1]//"
                # self.apoptosis_death_rate.setText(uep.find('.//cell_definition[1]//phenotype//death//model[1]//death_rate').text)
                # val = uep.find(apoptosis_path + 'death_rate').text
                # self.param_d[cell_def_name]["apop_death_rate"] = val
                # self.apoptosis_death_rate.setText(val)


                cycle_path = ".//cell_definition[" + str(idx) + "]//phenotype//cycle"
                print(" >> cycle_path=",cycle_path)
                cycle_code = int(uep.find(cycle_path).attrib['code'])
                print("   cycle code=",cycle_code)
                # static const int advanced_Ki67_cycle_model= 0;
                # static const int basic_Ki67_cycle_model=1;
                # static const int flow_cytometry_cycle_model=2;
                # static const int live_apoptotic_cycle_model=3;
                # static const int total_cells_cycle_model=4;
                # static const int live_cells_cycle_model = 5; 
                # static const int flow_cytometry_separated_cycle_model = 6; 
                # static const int cycling_quiescent_model = 7; 

                # self.cycle_dropdown.addItem("live cells")
                # self.cycle_dropdown.addItem("basic Ki67")
                # self.cycle_dropdown.addItem("advanced Ki67")
                # self.cycle_dropdown.addItem("flow cytometry")
                # self.cycle_dropdown.addItem("flow cytometry separated")
                # self.cycle_dropdown.addItem("cycling quiescent")

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

                phase_transition_path = cycle_path + "//phase_transition_rates"
                print(' >> phase_transition_path ')
                pt_uep = uep.find(phase_transition_path)
                if pt_uep:
                    # self.rb1 = QRadioButton("transition rate(s)", self)
                    self.rb1.setChecked(True)
                    self.cycle_duration_flag = False
                    self.customize_cycle_choices()

                    for rate in pt_uep: 
                        print(rate)
                        print("start_index=",rate.attrib["start_index"])
                        # todo? aren't there more? 1->0, 2->0?
                        # We only use cycle code=5 or 6 in ALL sample projs?!
                        if (rate.attrib['start_index'] == "0") and (rate.attrib['end_index'] == "0"):
                            # self.cycle_trate00.setText(rate.text)
                            self.param_d[cell_def_name]['cycle_trate00'] = rate.text
                        elif (rate.attrib['start_index'] == "0") and (rate.attrib['end_index'] == "1"):
                            # self.cycle_trate01.setText(rate.text)
                            self.param_d[cell_def_name]['cycle_trate01'] = rate.text
                        elif (rate.attrib['start_index'] == "1") and (rate.attrib['end_index'] == "2"):
                            # self.cycle_trate_02_12.setText(rate.text)
                            self.param_d[cell_def_name]['cycle_trate_02_12'] = rate.text
                        elif (rate.attrib['start_index'] == "2") and (rate.attrib['end_index'] == "3"):
                            # self.cycle_trate_03_23.setText(rate.text)
                            self.param_d[cell_def_name]['cycle_trate_03_23'] = rate.text
                        elif (rate.attrib['start_index'] == "3") and (rate.attrib['end_index'] == "0"):
                            # self.cycle_trate_03_30.setText(rate.text)
                            self.param_d[cell_def_name]['cycle_trate_03_30'] = rate.text


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
                phase_durations_path = cycle_path + "//phase_durations"
                print(' >> phase_durations_path =',phase_durations_path )
                pd_uep = uep.find(phase_durations_path)
                print(' >> pd_uep =',pd_uep )
                if pd_uep:
                    self.rb2.setChecked(True)
                    self.cycle_duration_flag = True
                    self.customize_cycle_choices()

                    for pd in pd_uep:   # phase_duration
                        print(pd)
                        print("index=",pd.attrib["index"])
                        sval = pd.text
                        if  pd.attrib['index'] == "0":
                            print("--> handling duration index=0")

                            # if idx == 1:  
                            # self.cycle_duration00.setText(sval)
                            # self.cycle_duration01.setText(sval)
                            # self.cycle_duration_02_01.setText(sval)
                            # self.cycle_duration_03_01.setText(sval)
                            self.param_d[cell_def_name]['cycle_duration00'] = sval
                            self.param_d[cell_def_name]['cycle_duration01'] = sval
                            self.param_d[cell_def_name]['cycle_duration_02_01'] = sval
                            self.param_d[cell_def_name]['cycle_duration_03_01'] = sval
                        elif  pd.attrib['index'] == "1":
                            print("--> handling duration index=1")
                            # self.cycle_duration10.setText(pd.text)
                            # self.cycle_duration_02_12.setText(pd.text)
                            # self.cycle_duration_03_12.setText(pd.text)
                            self.param_d[cell_def_name]['cycle_duration10'] = sval
                            self.param_d[cell_def_name]['cycle_duration_02_12'] = sval
                            self.param_d[cell_def_name]['cycle_duration_03_12'] = sval
                        elif  pd.attrib['index'] == "2":
                            print("--> handling duration index=2")
                            # self.cycle_duration_02_20.setText(pd.text)
                            # self.cycle_duration_03_23.setText(pd.text)
                            self.param_d[cell_def_name]['cycle_duration_02_20'] = sval
                            self.param_d[cell_def_name]['cycle_duration_03_23'] = sval
                        elif  pd.attrib['index'] == "3":
                            print("--> handling duration index=3")
                            # self.cycle_duration_03_30.setText(pd.text)
                            self.param_d[cell_def_name]['cycle_duration_03_30'] = sval

                # rf. microenv:
                # self.cell_type_name.setText(var.attrib['name'])
                # self.diffusion_coef.setText(vp[0].find('.//diffusion_coefficient').text)

                # ------------------ cell_definition: default
                # ---------  cycle (live)
                # self.float0.value = float(uep.find('.//cell_definition[1]//phenotype//cycle//phase_transition_rates//rate[1]').text)

                        # <death> 
                        #   <model code="100" name="apoptosis"> 
                        #    ...
                        #   <model code="101" name="necrosis">



                # ---------  death 

                death_path = ".//cell_definition[" + str(idx) + "]//phenotype//death//"
                print('death_path=',death_path)

                # rwh/TODO: validate we've got apoptosis or necrosis since order is not required in XML.
                apoptosis_path = death_path + "model[1]//"
                # self.apoptosis_death_rate.setText(uep.find('.//cell_definition[1]//phenotype//death//model[1]//death_rate').text)
                # self.apoptosis_death_rate.setText(
                self.param_d[cell_def_name]["apoptosis_death_rate"] = uep.find(apoptosis_path + 'death_rate').text

        # self.apoptosis_death_rate.setText(self.param_d[self.current_cell_def]["apoptosis_death_rate"])
        # self.apoptosis_phase0_duration.setText(
        # #-----
        # self.necrosis_death_rate.setText(
        # self.necrosis_phase0_duration.setText(pd.text)
        # self.necrosis_phase1_duration.setText(pd.text)

        # #---- 
        # self.apoptosis_unlysed_rate.setText(
        # self.apoptosis_lysed_rate.setText(u
        # self.apoptosis_cytoplasmic_biomass_change_rate.setText(
        # self.apoptosis_nuclear_biomass_change_rate.setText(
        # self.apoptosis_calcification_rate.setText(
        # self.apoptosis_relative_rupture_volume.setText(
        # #---- 
        # self.necrosis_unlysed_rate.setText(
        # self.necrosis_lysed_rate.setText(
        # self.necrosis_cytoplasmic_biomass_change_rate.setText(
        # self.necrosis_nuclear_biomass_change_rate.setText(
        # self.necrosis_calcification_rate.setText(
        # self.necrosis_relative_rupture_volume.setText(

                phase_durations_path = apoptosis_path + "phase_durations"
                print(' >> phase_durations_path =',phase_durations_path )
                pd_uep = uep.find(phase_durations_path)
                print(' >> pd_uep =',pd_uep )
                if pd_uep:
                    for pd in pd_uep:   # <duration index= ... >
                        print(pd)
                        print("index=",pd.attrib["index"])
                        if  pd.attrib['index'] == "0":
                            self.param_d[cell_def_name]["apoptosis_phase0_duration"] = pd.text
                            if  pd.attrib['fixed_duration'].lower() == "true":
                                self.param_d[cell_def_name]["apoptosis_phase0_fixed"] = True
                            else:
                                self.param_d[cell_def_name]["apoptosis_phase0_fixed"] = False

                apoptosis_params_path = apoptosis_path + "parameters//"

                self.param_d[cell_def_name]["apoptosis_unlysed_rate"] = uep.find(apoptosis_params_path+"unlysed_fluid_change_rate").text
                self.param_d[cell_def_name]["apoptosis_lysed_rate"] = uep.find(apoptosis_params_path+"lysed_fluid_change_rate").text
                self.param_d[cell_def_name]["apoptosis_cyto_rate"] = uep.find(apoptosis_params_path+"cytoplasmic_biomass_change_rate").text
                self.param_d[cell_def_name]["apoptosis_nuclear_rate"] = uep.find(apoptosis_params_path+"nuclear_biomass_change_rate").text
                self.param_d[cell_def_name]["apoptosis_calcif_rate"] = uep.find(apoptosis_params_path+"calcification_rate").text
                self.param_d[cell_def_name]["apoptosis_rel_rupture_rate"] = uep.find(apoptosis_params_path+"relative_rupture_volume").text

                #-----
                necrosis_path = death_path + "model[2]//"
                # self.necrosis_death_rate.setText(uep.find(necrosis_path + 'death_rate').text)
                self.param_d[cell_def_name]["necrosis_death_rate"] = uep.find(necrosis_path + 'death_rate').text

                phase_durations_path = necrosis_path + "phase_durations"
                print(' >> necrosis phase_durations_path =',phase_durations_path )
                pd_uep = uep.find(phase_durations_path)
                print(' >> pd_uep =',pd_uep )
                if pd_uep:
                    for pd in pd_uep: 
                        print(pd)
                        print("index=",pd.attrib["index"])
                        if  pd.attrib['index'] == "0":
                            # self.necrosis_phase0_duration.setText(pd.text)
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

                necrosis_params_path = necrosis_path + "parameters//"

                self.param_d[cell_def_name]["necrosis_unlysed_rate"] = uep.find(necrosis_params_path+"unlysed_fluid_change_rate").text
                self.param_d[cell_def_name]["necrosis_lysed_rate"] = uep.find(necrosis_params_path+"lysed_fluid_change_rate").text
                self.param_d[cell_def_name]["necrosis_cyto_rate"] = uep.find(necrosis_params_path+"cytoplasmic_biomass_change_rate").text
                self.param_d[cell_def_name]["necrosis_nuclear_rate"] = uep.find(necrosis_params_path+"nuclear_biomass_change_rate").text
                self.param_d[cell_def_name]["necrosis_calcif_rate"] = uep.find(necrosis_params_path+"calcification_rate").text
                self.param_d[cell_def_name]["necrosis_rel_rupture_rate"] = uep.find(necrosis_params_path+"relative_rupture_volume").text


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
                self.param_d[cell_def_name]['secretion'] = {}  # a dict for these params

                jdx = 0
                for sub in uep_secretion.findall('substrate'):
                    substrate_name = sub.attrib['name']
                    if jdx == 0:
                        self.current_secretion_substrate = substrate_name

                    print(jdx,") -- secretion substrate = ",substrate_name)
                    # self.param_d[self.current_cell_def]['secretion'][substrate_name]["secretion_rate"] = {}
                    self.param_d[cell_def_name]['secretion'][substrate_name] = {}

                    val = sub.find("secretion_rate").text
                    self.param_d[cell_def_name]['secretion'][substrate_name]["secretion_rate"] = val

                    val = sub.find("secretion_target").text
                    self.param_d[cell_def_name]['secretion'][substrate_name]["secretion_target"] = val

                    val = sub.find("uptake_rate").text
                    self.param_d[cell_def_name]['secretion'][substrate_name]["uptake_rate"] = val

                    val = sub.find("net_export_rate").text
                    self.param_d[cell_def_name]['secretion'][substrate_name]["net_export_rate"] = val

                    jdx += 1

                print("------ after parsing secretion:")
                print("------ self.param_d = ",self.param_d)
                

                # # ---------  molecular 


                # # ---------  custom data 
                # <custom_data>  
                # 	<receptor units="dimensionless">0.0</receptor>
                # 	<cargo_release_o2_threshold units="mmHg">10</cargo_release_o2_threshold>

                uep_custom_data = self.xml_root.find(".//cell_definitions//cell_definition[" + str(idx) + "]//custom_data")
                # custom_data_path = ".//cell_definition[" + str(self.idx_current_cell_def) + "]//custom_data//"
                print('uep_custom_data=',uep_custom_data)

                jdx = 0
                # rwh/TODO: if we have more vars than we initially created rows for, we'll need
                # to call 'append_more_cb' for the excess.
                # for var in uep_custom_data:
                #     print(jdx, ") ",var)
                #     self.custom_data_name[jdx].setText(var.tag)
                #     print("tag=",var.tag)
                #     self.custom_data_value[jdx].setText(var.text)

                #     if 'units' in var.keys():
                #         self.custom_data_units[jdx].setText(var.attrib['units'])
                #     jdx += 1



        self.current_cell_def = cell_def_0th
        self.tree.setCurrentItem(self.tree.topLevelItem(0))  # select the top (0th) item
        self.tree_item_clicked_cb(self.tree.topLevelItem(0), 0)  # and have its params shown

        print("\n\n=======================  leaving cell_def populate_tree  ======================= ")
        for k in self.param_d.keys():
            print(" ===>>> ",k, " : ", self.param_d[k])

    #-------------------------------------------------------------------
    def first_cell_def_name(self):
        uep = self.xml_root.find(".//cell_definitions//cell_definition")
        if uep:
                return(uep.attrib['name'])

    #-------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml(self):
        pass
        # TODO: verify valid type (numeric) and range?
        # xml_root.find(".//x_min").text = str(self.xmin.value)
        # xml_root.find(".//x_max").text = str(self.xmax.value)

    #-------------------------------------------------------------------
    # rwh: ever called?
    def clear_gui(self):
        # self.cell_type_name.setText('')
        self.cycle_trate00.setText('')
        self.cycle_trate01.setText('')
        self.cycle_trate10.setText('')
        self.cycle_trate_02_01.setText('')
        self.cycle_trate_02_12.setText('')
        self.cycle_trate_02_20.setText('')
        self.cycle_trate_03_01.setText('')
        self.cycle_trate_03_12.setText('')
        self.cycle_trate_03_23.setText('')
        self.cycle_trate_03_30.setText('')

        self.cycle_duration00.setText('')
        self.cycle_duration01.setText('')
        self.cycle_duration10.setText('')
        self.cycle_duration_02_01.setText('')
        self.cycle_duration_02_12.setText('')
        self.cycle_duration_02_20.setText('')
        self.cycle_duration_03_01.setText('')
        self.cycle_duration_03_12.setText('')
        self.cycle_duration_03_23.setText('')
        self.cycle_duration_03_30.setText('')

        self.apoptosis_death_rate.setText('')
        self.apoptosis_phase0_duration.setText('')
        # self.apoptosis_phase1_duration.setText('')
        # self.apoptosis_phase2_duration.setText('')
        # self.apoptosis_phase3_duration.setText('')
        self.apoptosis_unlysed_rate.setText('')
        self.apoptosis_lysed_rate.setText('')
        self.apoptosis_cytoplasmic_biomass_change_rate.setText('')
        self.apoptosis_nuclear_biomass_change_rate.setText('')
        self.apoptosis_calcification_rate.setText('')
        self.apoptosis_relative_rupture_volume.setText('')
        self.necrosis_death_rate.setText('')
        self.necrosis_phase0_duration.setText('')
        self.necrosis_phase1_duration.setText('')
        # self.necrosis_phase2_duration.setText('')
        # self.necrosis_phase3_duration.setText('')
        self.necrosis_unlysed_rate.setText('')
        self.necrosis_lysed_rate.setText('')
        self.necrosis_cytoplasmic_biomass_change_rate.setText('')
        self.necrosis_nuclear_biomass_change_rate.setText('')
        self.necrosis_calcification_rate.setText('')
        self.necrosis_relative_rupture_volume.setText('')
        self.volume_total.setText('')
        self.volume_fluid_fraction.setText('')
        self.volume_nuclear.setText('')
        self.volume_fluid_change_rate.setText('')
        self.volume_cytoplasmic_biomass_change_rate.setText('')
        self.volume_nuclear_biomass_change_rate.setText('')
        self.volume_calcified_fraction.setText('')
        self.volume_calcification_rate.setText('')
        self.relative_rupture_volume.setText('')
        self.cell_cell_adhesion_strength.setText('')
        self.cell_cell_repulsion_strength.setText('')
        self.relative_maximum_adhesion_distance.setText('')
        self.set_relative_equilibrium_distance.setText('')
        self.set_absolute_equilibrium_distance.setText('')
        self.speed.setText('')
        self.persistence_time.setText('')
        self.migration_bias.setText('')
        self.secretion_rate.setText('')
        self.secretion_target.setText('')
        self.uptake_rate.setText('')
        self.secretion_net_export_rate.setText('')
