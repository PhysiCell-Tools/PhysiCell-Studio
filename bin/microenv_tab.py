"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)
"""

import sys
import copy
import logging
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
# from ElementTree_pretty import prettify

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDoubleValidator #, QTreeWidgetItemIterator

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class SubstrateDef(QWidget):
    def __init__(self):
        super().__init__()
        # global self.microenv_params

        self.param_d = {}  # a dict of dicts - rwh/todo, used anymore?
        # self.substrate = {}
        self.current_substrate = None
        self.xml_root = None
        self.celldef_tab = None
        self.new_substrate_count = 1

        self.default_rate_units = "1/min"
        self.dirichlet_units = "mmHG"

        # self.stacked_w = QStackedWidget()
        # self.stack_w = []
        # self.stack_w.append(QStackedWidget())
        # self.stacked_w.addWidget(self.stack_w[0])

        #---------------
        # self.cell_defs = CellDefInstances()
        # self.microenv_hbox = QHBoxLayout()

        splitter = QSplitter()
        leftwidth = 150
        # splitter.setSizes([split_leftwidth, self.width() - leftwidth])
        # splitter.setSizes([leftwidth, self.width() - leftwidth])

        tree_widget_width = 240
        tree_widget_height = 400

        self.tree = QTreeWidget() # tree is overkill; list would suffice; Meh.
        self.tree.setFocusPolicy(QtCore.Qt.NoFocus)  # don't allow arrow keys to select
        # self.tree.itemDoubleClicked.connect(self.treeitem_edit_cb)
        # self.tree.setStyleSheet("background-color: lightgray")

        # self.tree.setFixedWidth(tree_widget_width)
        self.tree.setFixedHeight(tree_widget_height)

        # self.tree.currentChanged(self.tree_item_changed_cb)
        self.tree.itemClicked.connect(self.tree_item_clicked_cb)
        # self.tree.itemSelectionChanged.connect(self.tree_item_changed_cb2)
        # self.tree.itemDoubleClicked.connect(self.tree_item_changed_cb2)
        # self.tree.itemSelectionChanged.connect(self.tree_item_changed_cb2)
        self.tree.itemChanged.connect(self.tree_item_changed_cb)   # rename a substrate
        # self.tree.selectionChanged.connect(self.tree_item_sel_changed_cb)
        # self.tree.currentChanged.connect(self.tree_item_sel_changed_cb)
        # self.tree.itemSelectionChanged()
        # self.tree.setColumnCount(1)

        # self.tree.setCurrentItem(0)  # rwh/TODO

        header = QTreeWidgetItem(["---  Substrate ---"])
        self.tree.setHeaderItem(header)

        # cellname = QTreeWidgetItem(["virus"])
        # self.tree.insertTopLevelItem(0,cellname)

        # cellname = QTreeWidgetItem(["interferon"])
        # self.tree.insertTopLevelItem(1,cellname)

        #-------------------------
        # self.name_list = QListWidget() # tree is overkill; list would suffice; meh.

        # self.microenv_hbox.addWidget(self.tree)
        # self.microenv_hbox.addWidget(self.name_list)


        self.scroll_substrate_tree = QScrollArea()
        # self.scroll_substrate_tree.setFixedWidth(tree_widget_width)

        # self.tree_w = QWidget()
        tree_w_vbox = QVBoxLayout()
        tree_w_vbox.addWidget(self.tree)

        # self.scroll_substrate_tree.setWidget(self.tree)
        # self.scroll_substrate_tree.setWidget(self.name_list)

        #---------
        tree_w_hbox = QHBoxLayout()
        self.new_button = QPushButton("New")
        self.new_button.clicked.connect(self.new_substrate)
        self.new_button.setStyleSheet("background-color: lightgreen")
        bwidth = 70
        bheight = 32
        # self.new_button.setFixedWidth(bwidth)
        tree_w_hbox.addWidget(self.new_button)

        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_substrate)
        self.copy_button.setStyleSheet("background-color: lightgreen")
        # self.copy_button.setFixedWidth(bwidth)
        tree_w_hbox.addWidget(self.copy_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_substrate)
        self.delete_button.setStyleSheet("background-color: yellow")
        # self.delete_button.setFixedWidth(bwidth)
        tree_w_hbox.addWidget(self.delete_button)


        #---------
        self.tree_w = QWidget()
        # self.tree_w.setFixedWidth(tree_widget_width)
        # self.tree_w.setFixedHeight(tree_widget_height)
        tree_w_vbox.addLayout(tree_w_hbox)
        self.tree_w.setLayout(tree_w_vbox)
        self.scroll_substrate_tree.setWidget(self.tree_w)
        # self.scroll_substrate_tree.setWidget(self.tree)
        #---------
        # splitter.addWidget(self.tree)
        splitter.addWidget(self.scroll_substrate_tree)

        #-------------------------------------------
        # self.tab = QWidget()
        # self.tabs.resize(200,5)
        
        #-------------------------------------------
        label_width = 150
        units_width = 150

        # self.scroll = QScrollArea()
        self.scroll_area = QScrollArea()
        splitter.addWidget(self.scroll_area)
        # self.microenv_hbox.addWidget(self.scroll_area)

        self.microenv_params = QWidget()
        self.vbox = QVBoxLayout()
        # self.vbox.addStretch(0)

        # self.microenv_hbox.addWidget(self.)

        #------------------

        # self.vbox.addLayout(hbox)
        # self.vbox.addWidget(QHLine())

        #------------------
        # hbox = QHBoxLayout()
        # label = QLabel("Name of substrate:")
        # label.setFixedWidth(180)
        # label.setAlignment(QtCore.Qt.AlignRight)
        # hbox.addWidget(label)

        # self.substrate_name = QLineEdit()
        # self.substrate_name.textChanged.connect(self.substrate_name_cb)  # todo - rename it
        # # Want to validate name, e.g., starts with alpha, no special chars, etc.
        # # self.cycle_trate0_0.setValidator(QtGui.QDoubleValidator())
        # # self.cycle_trate0_1.enter.connect(self.save_xml)
        # hbox.addWidget(self.substrate_name)
        # self.vbox.addLayout(hbox)

        #------------------
        hbox = QHBoxLayout()
        label = QLabel("diffusion coefficient")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.diffusion_coef = QLineEdit()
        self.diffusion_coef.setValidator(QtGui.QDoubleValidator())
        self.diffusion_coef.textChanged.connect(self.diffusion_coef_changed)
        # self.diffusion_coef.enter.connect(self.save_xml)
        hbox.addWidget(self.diffusion_coef)

        units = QLabel("micron^2/min")
        units.setFixedWidth(units_width)
        hbox.addWidget(units)
        self.vbox.addLayout(hbox)

        #----------
        hbox = QHBoxLayout()
        label = QLabel("decay rate")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.decay_rate = QLineEdit()
        self.decay_rate.setValidator(QtGui.QDoubleValidator())
        self.decay_rate.textChanged.connect(self.decay_rate_changed)
        # self.decay_rate.enter.connect(self.save_xml)
        hbox.addWidget(self.decay_rate)

        units = QLabel(self.default_rate_units)
        units.setFixedWidth(units_width)
        hbox.addWidget(units)
        self.vbox.addLayout(hbox)

        #----------
        hbox = QHBoxLayout()
        label = QLabel("initial condition")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.init_cond = QLineEdit()
        self.init_cond.setValidator(QtGui.QDoubleValidator())
        self.init_cond.textChanged.connect(self.init_cond_changed)
        # self.init_cond.enter.connect(self.save_xml)
        hbox.addWidget(self.init_cond)

        self.init_cond_units = QLabel(self.dirichlet_units)
        self.init_cond_units.setFixedWidth(units_width)
        hbox.addWidget(self.init_cond_units)
        self.vbox.addLayout(hbox)
        #----------

        hbox = QHBoxLayout()
        label = QLabel("Dirichlet BC")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.dirichlet_bc = QLineEdit()
        self.dirichlet_bc.setValidator(QtGui.QDoubleValidator())
        self.dirichlet_bc.textChanged.connect(self.dirichlet_bc_changed)
        # self.bdy_cond.enter.connect(self.save_xml)
        hbox.addWidget(self.dirichlet_bc)

        self.dirichlet_bc_units = QLabel(self.dirichlet_units)
        self.dirichlet_bc_units.setFixedWidth(units_width)
        hbox.addWidget(self.dirichlet_bc_units)

# 			<Dirichlet_boundary_condition units="dimensionless" enabled="false">0</Dirichlet_boundary_condition>
        self.dirichlet_bc_enabled = QCheckBox("on")
        self.dirichlet_bc_enabled.stateChanged.connect(self.dirichlet_toggle_cb)
        # self.motility_enabled.setAlignment(QtCore.Qt.AlignRight)
        # label.setFixedWidth(label_width)
        hbox.addWidget(self.dirichlet_bc_enabled)

        self.vbox.addLayout(hbox)

        #--------------------------
# <!--
# 			<Dirichlet_options>
# 				<boundary_value ID="xmin" enabled="false">0</boundary_value>
# 				<boundary_value ID="xmax" enabled="false">0</boundary_value>
# 				<boundary_value ID="ymin" enabled="false">0</boundary_value>
# 				<boundary_value ID="ymax" enabled="false">0</boundary_value>
# 				<boundary_value ID="zmin" enabled="false">1</boundary_value>
# 				<boundary_value ID="zmax" enabled="false">0</boundary_value>
# 			</Dirichlet_options>
# -->			
#  		</variable>
        dirichlet_options_bdy = QLabel("Dirichlet options per boundary:")
        # units.setFixedWidth(units_width)
        self.vbox.addWidget(dirichlet_options_bdy)

        #----
        hbox = QHBoxLayout()
        label = QLabel("xmin:")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.dirichlet_xmin = QLineEdit()
        self.dirichlet_xmin.setValidator(QtGui.QDoubleValidator())
        self.dirichlet_xmin.textChanged.connect(self.dirichlet_xmin_changed)
        hbox.addWidget(self.dirichlet_xmin)

        self.enable_xmin = QCheckBox("on")
        self.enable_xmin.stateChanged.connect(self.enable_xmin_cb)
        # self.motility_enabled.setAlignment(QtCore.Qt.AlignRight)
        # label.setFixedWidth(label_width)
        hbox.addWidget(self.enable_xmin)
        self.vbox.addLayout(hbox)
        #----
        hbox = QHBoxLayout()
        label = QLabel("xmax:")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.dirichlet_xmax = QLineEdit()
        self.dirichlet_xmax.setValidator(QtGui.QDoubleValidator())
        self.dirichlet_xmax.textChanged.connect(self.dirichlet_xmax_changed)
        hbox.addWidget(self.dirichlet_xmax)

        self.enable_xmax = QCheckBox("on")
        self.enable_xmax.stateChanged.connect(self.enable_xmax_cb)
        hbox.addWidget(self.enable_xmax)
        self.vbox.addLayout(hbox)
        #---------
        hbox = QHBoxLayout()
        label = QLabel("ymin:")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.dirichlet_ymin = QLineEdit()
        self.dirichlet_ymin.setValidator(QtGui.QDoubleValidator())
        self.dirichlet_ymin.textChanged.connect(self.dirichlet_ymin_changed)
        hbox.addWidget(self.dirichlet_ymin)

        self.enable_ymin = QCheckBox("on")
        self.enable_ymin.stateChanged.connect(self.enable_ymin_cb)
        # self.motility_enabled.setAlignment(QtCore.Qt.AlignRight)
        # label.setFixedWidth(label_width)
        hbox.addWidget(self.enable_ymin)
        self.vbox.addLayout(hbox)
        #----
        hbox = QHBoxLayout()
        label = QLabel("ymax:")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.dirichlet_ymax = QLineEdit()
        self.dirichlet_ymax.setValidator(QtGui.QDoubleValidator())
        self.dirichlet_ymax.textChanged.connect(self.dirichlet_ymax_changed)
        hbox.addWidget(self.dirichlet_ymax)

        self.enable_ymax = QCheckBox("on")
        self.enable_ymax.stateChanged.connect(self.enable_ymax_cb)
        hbox.addWidget(self.enable_ymax)
        self.vbox.addLayout(hbox)
        #---------
        hbox = QHBoxLayout()
        label = QLabel("zmin:")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.dirichlet_zmin = QLineEdit()
        self.dirichlet_zmin.setValidator(QtGui.QDoubleValidator())
        self.dirichlet_zmin.textChanged.connect(self.dirichlet_zmin_changed)
        hbox.addWidget(self.dirichlet_zmin)

        self.enable_zmin = QCheckBox("on")
        self.enable_zmin.stateChanged.connect(self.enable_zmin_cb)
        # self.motility_enabled.setAlignment(QtCore.Qt.AlignRight)
        # label.setFixedWidth(label_width)
        hbox.addWidget(self.enable_zmin)
        self.vbox.addLayout(hbox)
        #----
        hbox = QHBoxLayout()
        label = QLabel("zmax:")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.dirichlet_zmax = QLineEdit()
        self.dirichlet_zmax.setValidator(QtGui.QDoubleValidator())
        self.dirichlet_zmax.textChanged.connect(self.dirichlet_zmax_changed)
        hbox.addWidget(self.dirichlet_zmax)

        self.enable_zmax = QCheckBox("on")
        self.enable_zmax.stateChanged.connect(self.enable_zmax_cb)
        hbox.addWidget(self.enable_zmax)
        self.vbox.addLayout(hbox)

        #-------------
        # Toggles for overall microenv (all substrates)
        self.vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("For all substrates: "))

        self.gradients = QCheckBox("calculate gradients")
        self.gradients.stateChanged.connect(self.gradients_cb)
        hbox.addWidget(self.gradients)
        # self.vbox.addLayout(hbox)

        # hbox = QHBoxLayout()
        self.track_in_agents = QCheckBox("track in agents")
        self.track_in_agents.stateChanged.connect(self.track_in_agents_cb)
        hbox.addWidget(self.track_in_agents)
        self.vbox.addLayout(hbox)

        #--------------------------
        # Dummy widget for filler??
        # label = QLabel("")
        # label.setFixedHeight(1000)
        # # label.setStyleSheet("background-color: orange")
        # label.setAlignment(QtCore.Qt.AlignCenter)
        # self.vbox.addWidget(label)

        #==================================================================
        # self.vbox.setAlignment(QtCore.Qt.AlignTop)

        # spacerItem = QSpacerItem(20, 237, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        # spacerItem = QSpacerItem(100,500)
        # self.vbox.addItem(spacerItem)
        self.vbox.addStretch()

        self.microenv_params.setLayout(self.vbox)

        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.microenv_params)


        # self.save_button = QPushButton("Save")
        # self.text = QLabel("Hello World",alignment=QtCore.Qt.AlignCenter)

        self.layout = QVBoxLayout(self)

        # self.layout.addLayout(controls_hbox)
 
        # self.layout.addWidget(self.tabs)
        # self.layout.addWidget(QHLine())
        # self.layout.addWidget(self.params)

        # self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(splitter)

        # self.layout.addWidget(self.vbox)

        # self.layout.addWidget(self.text)
        # self.layout.addWidget(self.save_button)
        # self.save_button.clicked.connect(self.save_xml)


    # def treeitem_edit_cb(self, *args):
    #     itm = self.tree.itemFromIndex(self.tree.selectedIndexes()[0])
    #     column = self.tree.currentColumn()
    #     edit = QLineEdit()
    #     edit.returnPressed.connect(lambda*_:self.project.setData(column, edit.text(), itm, column, self.tree))
    #     edit.returnPressed.connect(lambda*_:self.update())
    #     print(edit.text())
    #     self.tree.setItemWidget(itm,column,edit)

    # def substrate_name_cb(self, text):
    #     print("Text: %s", text)
    #     self.param_d[self.current_substrate]["name"] = text

    #     treeitem = QTreeWidgetItem([text])  # todo - figure out how to rename it in the tree!
    #     column = self.tree.currentColumn()
    #     # self.tree.setCurrentItem(treeitem)
    #     self.tree.setItemWidget(treeitem,column,None)


    def diffusion_coef_changed(self, text):
        # print("Text: %s", text)
        self.param_d[self.current_substrate]["diffusion_coef"] = text
        # log.info("diffusion_coef changed: %s", text)

    def decay_rate_changed(self, text):
        self.param_d[self.current_substrate]["decay_rate"] = text
    def init_cond_changed(self, text):
        self.param_d[self.current_substrate]["init_cond"] = text

    def dirichlet_bc_changed(self, text):
        self.param_d[self.current_substrate]["dirichlet_bc"] = text
        if self.dirichlet_bc_enabled.isChecked():
            self.dirichlet_xmin.setText(text)
            self.dirichlet_xmax.setText(text)
            self.dirichlet_ymin.setText(text)
            self.dirichlet_ymax.setText(text)
            self.dirichlet_zmin.setText(text)
            self.dirichlet_zmax.setText(text)

    def dirichlet_toggle_cb(self):
        return  # until we determine a more logical way to deal with this

        # print("dirichlet_toggle_cb()")
        # self.param_d[self.current_substrate]["dirichlet_enabled"] = self.dirichlet_bc_enabled.isChecked()
        # if self.dirichlet_bc_enabled.isChecked():
        #     options_flag = True
        # else:
        #     options_flag = False
        # self.enable_xmin.setChecked(options_flag)
        # self.enable_xmax.setChecked(options_flag)
        # self.enable_ymin.setChecked(options_flag)
        # self.enable_ymax.setChecked(options_flag)
        # self.enable_zmin.setChecked(options_flag)
        # self.enable_zmax.setChecked(options_flag)

        # if options_flag:
        #     sval = self.dirichlet_bc.text() 
        #     self.dirichlet_xmin.setText(sval)
        #     self.dirichlet_xmax.setText(sval)
        #     self.dirichlet_ymin.setText(sval)
        #     self.dirichlet_ymax.setText(sval)
        #     self.dirichlet_zmin.setText(sval)
        #     self.dirichlet_zmax.setText(sval)


    # global to all substrates
    def gradients_cb(self):
        # self.param_d[self.current_substrate]["gradients"] = self.gradients.isChecked()
        self.param_d["gradients"] = self.gradients.isChecked()
    def track_in_agents_cb(self):
        self.param_d["track_in_agents"] = self.track_in_agents.isChecked()

    def dirichlet_xmin_changed(self, text):
        # print("\n\n------> def dirichlet_xmin_changed(self, text)  called!!!")
        self.param_d[self.current_substrate]["dirichlet_xmin"] = text
    def dirichlet_xmax_changed(self, text):
        self.param_d[self.current_substrate]["dirichlet_xmax"] = text
    def dirichlet_ymin_changed(self, text):
        self.param_d[self.current_substrate]["dirichlet_ymin"] = text
    def dirichlet_ymax_changed(self, text):
        self.param_d[self.current_substrate]["dirichlet_ymax"] = text
    def dirichlet_zmin_changed(self, text):
        self.param_d[self.current_substrate]["dirichlet_zmin"] = text
    def dirichlet_zmax_changed(self, text):
        self.param_d[self.current_substrate]["dirichlet_zmax"] = text

    def enable_xmin_cb(self):
        self.param_d[self.current_substrate]["enable_xmin"] = self.enable_xmin.isChecked()
    def enable_xmax_cb(self):
        self.param_d[self.current_substrate]["enable_xmax"] = self.enable_xmax.isChecked()
    def enable_ymin_cb(self):
        self.param_d[self.current_substrate]["enable_ymin"] = self.enable_ymin.isChecked()
    def enable_ymax_cb(self):
        self.param_d[self.current_substrate]["enable_ymax"] = self.enable_ymax.isChecked()
    def enable_zmin_cb(self):
        self.param_d[self.current_substrate]["enable_zmin"] = self.enable_zmin.isChecked()
    def enable_zmax_cb(self):
        self.param_d[self.current_substrate]["enable_zmax"] = self.enable_zmax.isChecked()

    #----------------------------------------------------------------------
    # @QtCore.Slot()
    def new_substrate(self):
        # print('------ new_substrate')
        subname = "substrate%02d" % self.new_substrate_count
        # Make a new substrate (that's a copy of the currently selected one)
        # self.param_d[subname] = self.param_d[self.current_substrate].copy()  #rwh - "copy()" is critical

        self.param_d[subname] = copy.deepcopy(self.param_d[self.current_substrate])

        # self.param_d[subname]["name"] = subname
        # for k in self.param_d.keys():
        #     print(" (pre-new vals)===>>> ",k, " : ", self.param_d[k])
        # print()

        # Then "zero out" all entries(?)
        text = "0.0"
        self.param_d[subname]["diffusion_coef"] = text
        self.param_d[subname]["decay_rate"] = text
        self.param_d[subname]["init_cond"] = text
        self.param_d[subname]["init_cond_units"] = "dimensionless"
        self.param_d[subname]["dirichlet_bc"] = text
        self.param_d[subname]["dirichlet_bc_units"] = "dimensionless"
        bval = False
        self.param_d[subname]["dirichlet_enabled"] = bval

        text = ""
        self.param_d[subname]["dirichlet_xmin"] = text
        self.param_d[subname]["dirichlet_xmax"] = text
        self.param_d[subname]["dirichlet_ymin"] = text
        self.param_d[subname]["dirichlet_ymax"] = text
        self.param_d[subname]["dirichlet_zmin"] = text
        self.param_d[subname]["dirichlet_zmax"] = text

        bval = False
        self.param_d[subname]["enable_xmin"] = bval
        self.param_d[subname]["enable_xmax"] = bval
        self.param_d[subname]["enable_ymin"] = bval
        self.param_d[subname]["enable_ymax"] = bval
        self.param_d[subname]["enable_zmin"] = bval
        self.param_d[subname]["enable_zmax"] = bval

        self.param_d["gradients"] = bval
        self.param_d["track_in_agents"] = bval

        # print("\n ----- new dict:")
        # for k in self.param_d.keys():
        #     print(" ===>>> ",k, " : ", self.param_d[k])

        self.new_substrate_count += 1

        self.celldef_tab.add_new_substrate(subname)
        # self.celldef_tab.add_new_substrate_comboboxes(subname)
        # self.param_d[cell_def_name]["secretion"][substrate_name] = {}

        # sval = "0.0"
        # print("cdnames (keys) = ",self.celldef_tab.param_d.keys())
        # for cdname in self.celldef_tab.param_d.keys():  # for all cell defs, initialize secretion params
        #     # self.param_d[cdname]["secretion"][self.current_secretion_substrate]["secretion_rate"] = sval
        #     print('cdname = ',cdname)
        #     print(self.celldef_tab.param_d[cdname]["secretion"])
        #     self.celldef_tab.param_d[cdname]["secretion"][subname]["secretion_rate"] = sval
        #     self.celldef_tab.param_d[cdname]["secretion"][subname]["secretion_target"] = sval
        #     self.celldef_tab.param_d[cdname]["secretion"][subname]["uptake_rate"] = sval
        #     self.celldef_tab.param_d[cdname]["secretion"][subname]["net_export_rate"] = sval

        self.current_substrate = subname
        # self.substrate_name.setText(subname)

        # item_idx = self.tree.indexFromItem(self.tree.currentItem()).row() 

        num_items = self.tree.invisibleRootItem().childCount()
        # print("tree has num_items = ",num_items)
        treeitem = QTreeWidgetItem([subname])
        treeitem.setFlags(treeitem.flags() | QtCore.Qt.ItemIsEditable)
        self.tree.insertTopLevelItem(num_items,treeitem)
        self.tree.setCurrentItem(treeitem)

        self.tree_item_clicked_cb(treeitem, 0)

    #----------------------------------------------------------------------
    # @QtCore.Slot()
    def copy_substrate(self):
        # print('------ copy_substrate')
        subname = "substrate%02d" % self.new_substrate_count
        # Make a new substrate (that's a copy of the currently selected one)
        # self.param_d[subname] = self.param_d[self.current_substrate].copy()  #rwh - "copy()" is critical
        self.param_d[subname] = copy.deepcopy(self.param_d[self.current_substrate])
        self.param_d[subname]["name"] = subname


        # for k in self.param_d.keys():
        #     print(" ===>>> ",k, " : ", self.param_d[k])

        self.new_substrate_count += 1

        # self.celldef_tab.add_new_substrate_comboboxes(subname)

        self.celldef_tab.add_new_substrate(subname)

        self.current_substrate = subname
        # self.substrate_name.setText(subname)

        # item_idx = self.tree.indexFromItem(self.tree.currentItem()).row() 

        num_items = self.tree.invisibleRootItem().childCount()
        # print("tree has num_items = ",num_items)
        treeitem = QTreeWidgetItem([subname])
        treeitem.setFlags(treeitem.flags() | QtCore.Qt.ItemIsEditable)
        self.tree.insertTopLevelItem(num_items,treeitem)
        self.tree.setCurrentItem(treeitem)

        self.tree_item_clicked_cb(treeitem, 0)
        
    #----------------------------------------------------------------------
    def show_delete_warning(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Not allowed to delete all substrates.")
        #    msgBox.setWindowTitle("Example")
        # msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msgBox.setStandardButtons(QMessageBox.Ok)
        # msgBox.buttonClicked.connect(msgButtonClick)

        returnValue = msgBox.exec()
        # if returnValue == QMessageBox.Ok:
            # print('OK clicked')

    #----------------------------------------------------------------------
    # @QtCore.Slot()
    def delete_substrate(self):
        num_items = self.tree.invisibleRootItem().childCount()
        logging.debug(f'------ delete_substrate: num_items= {num_items}')
        if num_items == 1:
            # print("Not allowed to delete all substrates.")
            # QMessageBox.information(self, "Not allowed to delete all substrates")
            self.show_delete_warning()
            return

        # rwh: BEWARE of mutating the dict?
        del self.param_d[self.current_substrate]

        # may need to make a copy instead??
        # new_dict = {key:val for key, val in self.param_d.items() if key != 'Mani'}
        # self.param_d = new_dict


        # for k in self.param_d.keys():
        #     print(" ===>>> ",k, " : ", self.param_d[k])

        item_idx = self.tree.indexFromItem(self.tree.currentItem()).row() 
        # print('------      item_idx=',item_idx)
        self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(self.tree.currentItem()))

        # self.celldef_tab.delete_substrate(item_idx)
        # print('------      new name=',self.tree.currentItem().text(0))
        self.current_substrate = self.tree.currentItem().text(0)

        # do this last
        self.celldef_tab.delete_substrate(item_idx, self.current_substrate)


    #----------------------------------------------------------------------
    # @QtCore.Slot()
    # def save_xml(self):
    #     # self.text.setText(random.choice(self.hello))
    #     pass

    # When a substrate is selected(via double-click) and renamed
    def tree_item_changed_cb(self, it,col):
        # print('--------- tree_item_changed_cb():', it, col, it.text(col) )  # col=0 always

        prev_name = self.current_substrate
        # print('prev_name= ',prev_name)
        self.current_substrate = it.text(col)
        self.param_d[self.current_substrate] = self.param_d.pop(prev_name)  # sweet

        # print('self.current_substrate= ',self.current_substrate )
        # for k in self.param_d.keys():
        #     print(" ===>>> ",k, " : ", self.param_d[k])
        # print()

        self.celldef_tab.renamed_substrate(prev_name, self.current_substrate)

    #----------------------------------------------------------------------
    def tree_item_sel_changed_cb(self, it,col):
        # print('--------- tree_item_sel_changed_cb():', it, col, it.text(col) )  # col=0 always

        prev_current_substrate = self.current_substrate
        self.current_substrate = it.text(col)
        self.param_d[self.current_substrate] = self.param_d.pop(prev_current_substrate)  # sweet
        # print('self.current_substrate= ',self.current_substrate )
        # for k in self.param_d.keys():
        #     print(" ===>>> ",k, " : ", self.param_d[k])
        # print()

    # def tree_item_changed_cb2(self, it,col):
    #     print('--------- tree_item_changed_cb2():', it, col, it.text(col) )  # col=0 always

    #     self.current_substrate = it.text(col)
    #     print('self.current_substrate= ',self.current_substrate )


    #----------------------------------------------------------------------
    # Update the widget values with values from param_d
    def tree_item_clicked_cb(self, it,col):
        # print('--------- tree_item_clicked_cb():', it, col, it.text(col) )  # col=0 always
        self.current_substrate = it.text(col)
        # print('self.current_substrate= ',self.current_substrate )
        # print('self.= ',self.tree.indexFromItem )

        # self.param.clear()

        # fill in the GUI with this one's params
        # self.fill_gui(self.current_substrate)

        # self.substrate_name.setText(self.param_d[self.current_substrate]["name"])
        self.diffusion_coef.setText(self.param_d[self.current_substrate]["diffusion_coef"])
        self.decay_rate.setText(self.param_d[self.current_substrate]["decay_rate"])
        self.init_cond.setText(self.param_d[self.current_substrate]["init_cond"])
        self.init_cond_units.setText(self.param_d[self.current_substrate]["init_cond_units"])
        self.dirichlet_bc.setText(self.param_d[self.current_substrate]["dirichlet_bc"])
        self.dirichlet_bc_units.setText(self.param_d[self.current_substrate]["dirichlet_bc_units"])
        self.dirichlet_bc_enabled.setChecked(self.param_d[self.current_substrate]["dirichlet_enabled"])

        # xmin = self.param_d[self.current_substrate]["dirichlet_xmin"]
        # print("    xmin=",xmin)
        if self.dirichlet_options_exist:
            val = self.param_d[self.current_substrate]["dirichlet_xmin"]
            # print('--------- tree_item_clicked_cb(): dirichlet_xmin=', val)
            self.dirichlet_xmin.setText(val)
            self.dirichlet_xmax.setText(self.param_d[self.current_substrate]["dirichlet_xmax"])
            self.dirichlet_ymin.setText(self.param_d[self.current_substrate]["dirichlet_ymin"])
            self.dirichlet_ymax.setText(self.param_d[self.current_substrate]["dirichlet_ymax"])
            self.dirichlet_zmin.setText(self.param_d[self.current_substrate]["dirichlet_zmin"])
            self.dirichlet_zmax.setText(self.param_d[self.current_substrate]["dirichlet_zmax"])

            # QCheckBoxs
            self.enable_xmin.setChecked(self.param_d[self.current_substrate]["enable_xmin"])
            self.enable_xmax.setChecked(self.param_d[self.current_substrate]["enable_xmax"])
            self.enable_ymin.setChecked(self.param_d[self.current_substrate]["enable_ymin"])
            self.enable_ymax.setChecked(self.param_d[self.current_substrate]["enable_ymax"])
            self.enable_zmin.setChecked(self.param_d[self.current_substrate]["enable_zmin"])
            self.enable_zmax.setChecked(self.param_d[self.current_substrate]["enable_zmax"])


        # global to all substrates
        self.gradients.setChecked(self.param_d["gradients"])
        self.track_in_agents.setChecked(self.param_d["track_in_agents"])


    #----------------------------------------------------------------------
# 		<variable name="substrate" units="dimensionless" ID="0">
# 			<physical_parameter_set>
# 				<diffusion_coefficient units="micron^2/min">100000.0</diffusion_coefficient>
# 				<decay_rate units="1/min">10</decay_rate>  
# 			</physical_parameter_set>
# 			<initial_condition units="mmHg">0</initial_condition>
# 			<Dirichlet_boundary_condition units="mmHg" enabled="true">0</Dirichlet_boundary_condition>
# <!-- use this block to set Dirichlet boundary conditions on individual boundaries --> 
# <!--
# 			<Dirichlet_options>
# 				<boundary_value ID="xmin" enabled="false">0</boundary_value>
# 				<boundary_value ID="xmax" enabled="false">0</boundary_value>
# 				<boundary_value ID="ymin" enabled="false">0</boundary_value>
# 				<boundary_value ID="ymax" enabled="false">0</boundary_value>
# 				<boundary_value ID="zmin" enabled="false">1</boundary_value>
# 				<boundary_value ID="zmax" enabled="false">0</boundary_value>
# 			</Dirichlet_options>
# -->
#  		</variable>
    def populate_tree(self):
        logging.debug(f'=======================  microenv populate_tree  ======================= ')
        uep = self.xml_root.find(".//microenvironment_setup")
        if uep:
            # self.substrate.clear()
            # self.param[substrate_name] = {}  # a dict of dicts

            self.tree.clear()
            idx = 0
            # <microenvironment_setup>
		    #   <variable name="food" units="dimensionless" ID="0">
            for var in uep:
                # print(cell_def.attrib['name'])
                if var.tag == 'variable':
                    substrate_name = var.attrib['name']
                    self.current_substrate = substrate_name  # do this for the callback methods (rf. BEWARE below)
                    if idx == 0:
                        # self.current_substrate = substrate_name
                        substrate_0th = substrate_name
                    self.param_d[substrate_name] = {}

                    # self.param_d[substrate_name]["name"] = substrate_name

                    treeitem = QTreeWidgetItem([substrate_name])
                    treeitem.setFlags(treeitem.flags() | QtCore.Qt.ItemIsEditable)

                    # self.substrate[var_name] = {}  # a dict of dicts
                    self.tree.insertTopLevelItem(idx,treeitem)
                    if idx == 0:  # select the 1st (0th) entry
                        self.tree.setCurrentItem(treeitem)

                    # Now fill the param dict for each substrate and the Qt widget values for the 0th

                    idx += 1

                    var_param_path = self.xml_root.find(".//microenvironment_setup//variable[" + str(idx) + "]//physical_parameter_set")
                    var_path = self.xml_root.find(".//microenvironment_setup//variable[" + str(idx) + "]")

                    # self.substrate_name.setText(var.attrib['name'])
                    diffusion_coef = var_param_path.find('.//diffusion_coefficient').text
                    # self.substrate["diffusion_coef"] = diffusion_coef
                    self.param_d[substrate_name]["diffusion_coef"] = diffusion_coef
                    if idx == 1:
                        self.diffusion_coef.setText(diffusion_coef)

                    decay_rate = var_param_path.find('.//decay_rate').text
                    # self.substrate["decay_rate"] = decay_rate
                    self.param_d[substrate_name]["decay_rate"] = decay_rate
                    if idx == 1:
                        self.decay_rate.setText(decay_rate)

                    init_cond = var_path.find('.//initial_condition').text
                    # self.substrate["init_cond"] = init_cond
                    self.param_d[substrate_name]["init_cond"] = init_cond
                    if idx == 1:
                        self.init_cond.setText(init_cond)
                    
                    dc_ic_units = var_path.find('.//initial_condition').attrib['units']  # omg
                    logging.debug(f'dc_ic_units =  {dc_ic_units}')
                    self.param_d[substrate_name]["init_cond_units"] = dc_ic_units
                    # sys.exit(1)

			# <Dirichlet_boundary_condition units="dimensionless" enabled="false">1</Dirichlet_boundary_condition>
                    dirichlet_bc_path = var_path.find('.//Dirichlet_boundary_condition')
                    dirichlet_bc = dirichlet_bc_path.text
                    # self.substrate["init_cond"] = init_cond
                    self.param_d[substrate_name]["dirichlet_bc"] = dirichlet_bc
                    # if idx == 1:
                    #     self.dirichlet_bc.setText(dirichlet_bc)

                    dc_bc_units = dirichlet_bc_path.attrib['units']  # omg
                    logging.debug(f'dc_bc_units = {dc_bc_units}')
                    self.param_d[substrate_name]["dirichlet_bc_units"] = dc_bc_units

                    if dirichlet_bc_path.attrib['enabled'].lower() == "false":
                        self.param_d[substrate_name]["dirichlet_enabled"] = False
                        # if idx == 1:
                        #     self.dirichlet_bc_enabled.setChecked(False)
                    else:
                        self.param_d[substrate_name]["dirichlet_enabled"] = True
                        # if idx == 1:
                        #     self.dirichlet_bc_enabled.setChecked(True)
                        # self.dirichlet_bc_enabled.setChecked(self.param_d[self.current_substrate]["dirichlet_enabled"])

                    # 			<Dirichlet_options>
                    # 				<boundary_value ID="xmin" enabled="false">0</boundary_value>
                    # 				<boundary_value ID="xmax" enabled="false">0</boundary_value>

                    self.param_d[substrate_name]["dirichlet_xmin"] = "0"
                    self.param_d[substrate_name]["dirichlet_xmax"] = "0"
                    self.param_d[substrate_name]["dirichlet_ymin"] = "0"
                    self.param_d[substrate_name]["dirichlet_ymax"] = "0"
                    self.param_d[substrate_name]["dirichlet_zmin"] = "0"
                    self.param_d[substrate_name]["dirichlet_zmax"] = "0"
                    self.param_d[substrate_name]["enable_xmin"] = False
                    self.param_d[substrate_name]["enable_xmax"] = False
                    self.param_d[substrate_name]["enable_ymin"] = False
                    self.param_d[substrate_name]["enable_ymax"] = False
                    self.param_d[substrate_name]["enable_zmin"] = False
                    self.param_d[substrate_name]["enable_zmax"] = False

                    self.dirichlet_options_exist = True  # rwh/todo - how to handle this?
                    options_path = var_path.find('.//Dirichlet_options')
                    if options_path:
                        # self.dirichlet_options_exist = True
                        for bv in options_path:
                            logging.debug(f'bv = {bv}')
                            if "xmin" in bv.attrib['ID'].lower():
                                self.param_d[substrate_name]["dirichlet_xmin"] = bv.text
                                logging.debug(f'   -------- {substrate_name}:  dirichlet_xmin = {bv.text}')

                                # BEWARE: doing a 'setText' here will invoke the callback associated with
                                # the widget (e.g., self.dirichlet_xmin.textChanged.connect(self.dirichlet_xmin_changed))
                                # if idx == 1:
                                #     self.dirichlet_xmin.setText(bv.text)

                                if "true" in bv.attrib['enabled'].lower():
                                    # self.param_d[self.current_substrate]["enable_xmin"] = True
                                    self.param_d[substrate_name]["enable_xmin"] = True
                            elif "xmax" in bv.attrib['ID']:
                                self.param_d[substrate_name]["dirichlet_xmax"] = bv.text
                                # if idx == 1:
                                #     self.dirichlet_xmax.setText(bv.text)
                                if "true" in bv.attrib['enabled'].lower():
                                    self.param_d[substrate_name]["enable_xmax"] = True
                            elif "ymin" in bv.attrib['ID']:
                                self.param_d[substrate_name]["dirichlet_ymin"] = bv.text
                                # if idx == 1:
                                #     self.dirichlet_ymin.setText(bv.text)
                                if "true" in bv.attrib['enabled'].lower():
                                    self.param_d[substrate_name]["enable_ymin"] = True
                            elif "ymax" in bv.attrib['ID']:
                                self.param_d[substrate_name]["dirichlet_ymax"] = bv.text
                                # self.dirichlet_ymax.setText(bv.text)
                                if "true" in bv.attrib['enabled'].lower():
                                    self.param_d[substrate_name]["enable_ymax"] = True
                            elif "zmin" in bv.attrib['ID']:
                                self.param_d[substrate_name]["dirichlet_zmin"] = bv.text
                                # self.dirichlet_zmin.setText(bv.text)
                                if "true" in bv.attrib['enabled'].lower():
                                    self.param_d[substrate_name]["enable_zmin"] = True
                            elif "zmax" in bv.attrib['ID']:
                                self.param_d[substrate_name]["dirichlet_zmax"] = bv.text
                                # self.dirichlet_zmax.setText(bv.text)
                                if "true" in bv.attrib['enabled'].lower():
                                    self.param_d[substrate_name]["enable_zmax"] = True
                    else:
                        # self.dirichlet_options_exist = False
                        self.param_d[substrate_name]["enable_xmin"] = False
                        self.param_d[substrate_name]["enable_xmax"] = False
                        self.param_d[substrate_name]["enable_ymin"] = False
                        self.param_d[substrate_name]["enable_ymax"] = False
                        self.param_d[substrate_name]["enable_zmin"] = False
                        self.param_d[substrate_name]["enable_zmax"] = False

            # </variable>
            # <options>
            # 	<calculate_gradients>true</calculate_gradients>
            # 	<track_internalized_substrates_in_each_agent>false</track_internalized_substrates_in_each_agent>
                elif var.tag == 'options':
                    self.param_d["gradients"] = False
                    self.param_d["track_in_agents"] = False
                    # self.gradients.setChecked(False)
                    # self.track_in_agents.setChecked(False)
                    for opt in var:
                        logging.debug(f'------- options: {opt}')
                        if "calculate_gradients" in opt.tag:
                            if "true" in opt.text.lower():
                                # self.gradients.setChecked(True)
                                self.param_d["gradients"] = True
                        elif "track_internalized_substrates_in_each_agent" in opt.tag:
                            if "true" in opt.text.lower():
                                # self.track_in_agents.setChecked(True)
                                self.param_d["track_in_agents"] = True

            # options_path = uep.find(".//options")
            # print(" ---- options_path = ", options_path)
            # gradients_path = options_path.find(".//calculate_gradients")
            # # gradients_path = options_path.find("calculate_gradients")
            # print(" ---- gradients_path = ", gradients_path)
            # print(" ---- gradients_path.tag = ", gradients_path.tag)
            # print(" ---- gradients_path.text = ", gradients_path.text)
            # if "true" in gradients_path.text.lower():
            #     print(" found: gradients_path ...//calculate_gradients = true")
            #     self.param_d[self.current_substrate]["gradients"] = True

            # track_path = options_path.find(".//track_internalized_substrates_in_each_agent")
            # print(" ---- track_path.text = ", track_path.text)
            # print(" ---- track_path = ", track_path)
            # if track_path:
            #     print(" found: track_path ...//track_internalized_substrates_in_each_agent")
            # if "true" in track_path.text.lower():
            #     print(" found: track_path  = true")
            #     self.param_d[self.current_substrate]["track_in_agents"] = True

        self.current_substrate = substrate_0th
        self.tree.setCurrentItem(self.tree.topLevelItem(0))  # select the top (0th) item
        self.tree_item_clicked_cb(self.tree.topLevelItem(0), 0)  # and invoke its callback to fill widget values

        logging.debug(f'\n\n=======================  leaving microenv populate_tree  =====================')
        # for k in self.param_d.keys():
        #     print(" ===>>> ",k, " : ", self.param_d[k])

#        ---- populate_tree(): self.param_d =  {'director signal': {'diffusion_coef': '1000', 'decay_rate': '.4', 'init_cond': '0', 'dirichlet_bc': '1', 'dirichlet_enabled': False, 'enable_xmin': False, 'enable_xmax': False, 'enable_ymin': False, 'enable_ymax': False, 'enable_zmin': False, 'enable_zmax': False, 'dirichlet_xmin': '-11', 'dirichlet_xmax': '11', 'dirichlet_ymin': '-12', 'dirichlet_ymax': '12', 'dirichlet_zmin': '-13', 'dirichlet_zmax': '13'}, 'cargo signal': {'diffusion_coef': '1000', 'decay_rate': '.4', 'init_cond': '0', 'dirichlet_bc': '1', 'dirichlet_enabled': False, 'enable_xmin': False, 'enable_xmax': False, 'enable_ymin': False, 'enable_ymax': False, 'enable_zmin': False, 'enable_zmax': False, 'dirichlet_xmin': '-11', 'dirichlet_xmax': '11', 'dirichlet_ymin': '-12', 'dirichlet_ymax': '12', 'dirichlet_zmin': '-13', 'dirichlet_zmax': '13'}}


    #----------------------------------------------------------------------------
    def first_substrate_name(self):
        uep = self.xml_root.find(".//microenvironment_setup//variable")
        if uep:
                return(uep.attrib['name'])


            #----------------------------------------------------------------------------
            # Read values from the params_d and generate XML

            # 	<microenvironment_setup>
            # 	<variable name="director signal" units="dimensionless" ID="0">
            # 		<physical_parameter_set>
            # 			<diffusion_coefficient units="micron^2/min">1000</diffusion_coefficient>
            # 			<decay_rate units="1/min">.1</decay_rate>  
            # 		</physical_parameter_set>
            # 		<initial_condition units="dimensionless">0</initial_condition>
            # 		<Dirichlet_boundary_condition units="dimensionless" enabled="false">1</Dirichlet_boundary_condition>
            # 	</variable>
                
            # 	<variable name="cargo signal" units="dimensionless" ID="1">
            # 		<physical_parameter_set>
            # 			<diffusion_coefficient units="micron^2/min">1000</diffusion_coefficient>
            # 			<decay_rate units="1/min">.4</decay_rate>  
            # 		</physical_parameter_set>
            # 		<initial_condition units="dimensionless">0</initial_condition>
            # 		<Dirichlet_boundary_condition units="dimensionless" enabled="false">1</Dirichlet_boundary_condition>
            # 	</variable>
                
            # 	<options>
            # 		<calculate_gradients>true</calculate_gradients>
            # 		<track_internalized_substrates_in_each_agent>false</track_internalized_substrates_in_each_agent>
                    
            # 		<initial_condition type="matlab" enabled="false">
            # 			<filename>./config/initial.mat</filename>
            # 		</initial_condition>
                    
            # 		<dirichlet_nodes type="matlab" enabled="false">
            # 			<filename>./config/dirichlet.mat</filename>
            # 		</dirichlet_nodes>
            # 	</options>
            # </microenvironment_setup>


    # <microenvironment_setup>
	# 	<variable name="oxygen" units="mmHg" ID="0">
	# 		<physical_parameter_set>
	# 			<diffusion_coefficient units="micron^2/min">421.0</diffusion_coefficient>
	# 			<decay_rate units="1/min">.41</decay_rate>  
	# 		</physical_parameter_set>
	# 		<initial_condition units="mmHg">41.0</initial_condition>
	# 		<Dirichlet_boundary_condition units="mmHg" enabled="true">41.1</Dirichlet_boundary_condition>
    #         <Dirichlet_options>
 	# 			<boundary_value ID="xmin" enabled="false">1</boundary_value>
 	# 			<boundary_value ID="xmax" enabled="true">2</boundary_value>
 	# 			<boundary_value ID="ymin" enabled="false">3</boundary_value>
 	# 			<boundary_value ID="ymax" enabled="true">4</boundary_value>
 	# 			<boundary_value ID="zmin" enabled="false">5</boundary_value>
 	# 			<boundary_value ID="zmax" enabled="true">6</boundary_value>
 	# 		</Dirichlet_options>
	# 	</variable>
	
	# 	<variable name="glue" units="dimensionless" ID="1">
	# 		<physical_parameter_set>
	# 			<diffusion_coefficient units="micron^2/min">422.0</diffusion_coefficient>
	# 			<decay_rate units="1/min">.42</decay_rate>  
	# 		</physical_parameter_set>
	# 		<initial_condition units="mmHg">42.0</initial_condition>
	# 		<Dirichlet_boundary_condition units="mmHg" enabled="false">42.1</Dirichlet_boundary_condition>
	# 	</variable>
		
	# 	<options>
	# 		<calculate_gradients>true</calculate_gradients>
	# 		<track_internalized_substrates_in_each_agent>false</track_internalized_substrates_in_each_agent>
			 
	# 		<initial_condition type="matlab" enabled="false">
	# 			<filename>./config/initial.mat</filename>
	# 		</initial_condition>
			 
	# 		<dirichlet_nodes type="matlab" enabled="false">
	# 			<filename>./config/dirichlet.mat</filename>
	# 		</dirichlet_nodes>
	# 	</options>
	# </microenvironment_setup>	

    def iterate_tree(self, node, count, subs):
        for idx in range(count):
            item = node.child(idx)
            # print('******* State: %s, Text: "%s"' % (Item.checkState(3), Item.text(0)))
            subs.append(item.text(0))
            child_count = item.childCount()
            if child_count > 0:
                self.iterate_tree(item, child_count)
                
    def fill_xml(self):
        logging.debug(f'----------- microenv_tab.py: fill_xml(): ----------')
        uep = self.xml_root.find('.//microenvironment_setup') # guaranteed to exist since we start with a valid model
        vp = []   # pointers to <variable> nodes
        if uep:
            # Begin by removing all previously defined substrates in the .xml
            for var in uep.findall('variable'):
                uep.remove(var)
                # vp.append(var)
        # self.tree_status()

        # Obtain a list of all substrates in self.tree (QTreeWidget()). Used below.
        substrates_in_tree = []
        num_subs = self.tree.invisibleRootItem().childCount()  # rwh: get number of items in tree
        logging.debug(f'microenv_tab.py: fill_xml(): num subtrates = {num_subs}')
        self.iterate_tree(self.tree.invisibleRootItem(), num_subs, substrates_in_tree)
        logging.debug(f'substrates_in_tree ={substrates_in_tree}')

        uep = self.xml_root.find('.//microenvironment_setup')
        indent1 = '\n'
        indent6 = '\n      '
        indent8 = '\n        '
        indent10 = '\n          '

        idx = 0
        for substrate in self.param_d.keys():
            logging.debug(f'microrenv_tab.py: key in param_d.keys() = {substrate}')
            if substrate in substrates_in_tree:
                logging.debug(f'matched! {substrate}')
	# 	<variable name="glue" units="dimensionless" ID="1">
	# 		<physical_parameter_set>
	# 			<diffusion_coefficient units="micron^2/min">422.0</diffusion_coefficient>
	# 			<decay_rate units="1/min">.42</decay_rate>  
	# 		</physical_parameter_set>
	# 		<initial_condition units="mmHg">42.0</initial_condition>
	# 		<Dirichlet_boundary_condition units="mmHg" enabled="false">42.1</Dirichlet_boundary_condition>
                # elm = ET.Element(substrate)
                # elm = ET.Element(substrate+'\n', {'foo':'bar'})


        # self.param_d[self.current_substrate]["diffusion_coef"] = text
        # self.param_d[self.current_substrate]["decay_rate"] = text
        # self.param_d[self.current_substrate]["init_cond"] = text
        # self.param_d[self.current_substrate]["dirichlet_bc"] = text
        # self.param_d[self.current_substrate]["dirichlet_enabled"] = self.dirichlet_bc_enabled.isChecked()
                elm = ET.Element("variable", 
                        {"name":substrate, "units":"dimensionless", "ID":str(idx)})
                elm.tail = '\n' + indent6
                elm.text = indent8

                subelm = ET.SubElement(elm, 'physical_parameter_set')
                subelm.text = indent10
                subelm.tail = indent8

                subelm2 = ET.SubElement(subelm, "diffusion_coefficient",{"units":"micron^2/min"})
                subelm2.text = self.param_d[substrate]["diffusion_coef"]
                subelm2.tail = indent10
                subelm2 = ET.SubElement(subelm, "decay_rate",{"units":self.default_rate_units})
                subelm2.text = self.param_d[substrate]["decay_rate"]
                subelm2.tail = indent8

                    # self.param_d[substrate_name]["init_cond_units"] = dc_ic_units
                # subelm = ET.SubElement(elm, 'initial_condition', {"units":"mmHg"})
                subelm = ET.SubElement(elm, 'initial_condition', {"units":self.param_d[substrate]["init_cond_units"]})
                subelm.text = self.param_d[substrate]["init_cond"]
                subelm.tail = indent8
                    # self.param_d[substrate_name]["dirichlet_bc_units"] = dc_bc_units
                subelm = ET.SubElement(elm, "Dirichlet_boundary_condition",
                        {"units":self.param_d[substrate]["dirichlet_bc_units"], 
                         "enabled":str(self.param_d[substrate]["dirichlet_enabled"]) })
                        # {"units":"mmHg", "enabled":str(self.param_d[substrate]["dirichlet_enabled"])})
                subelm.text = self.param_d[substrate]["dirichlet_bc"]
                subelm.tail = indent8

#dirichlet_xmin 
                subelm = ET.SubElement(elm, "Dirichlet_options")
                subelm.text = indent10
                subelm.tail = indent8
                subelm2 = ET.SubElement(subelm, "boundary_value",{"ID":"xmin", 
                    "enabled":str(self.param_d[substrate]["enable_xmin"])} )
                subelm2.text = self.param_d[substrate]["dirichlet_xmin"]
                subelm2.tail = indent10
                subelm2 = ET.SubElement(subelm, "boundary_value",{"ID":"xmax", 
                    "enabled":str(self.param_d[substrate]["enable_xmax"])} )
                subelm2.text = self.param_d[substrate]["dirichlet_xmax"]
                subelm2.tail = indent10

                subelm2 = ET.SubElement(subelm, "boundary_value",{"ID":"ymin", 
                    "enabled":str(self.param_d[substrate]["enable_ymin"])} )
                subelm2.text = self.param_d[substrate]["dirichlet_ymin"]
                subelm2.tail = indent10
                subelm2 = ET.SubElement(subelm, "boundary_value",{"ID":"ymax", 
                    "enabled":str(self.param_d[substrate]["enable_ymax"])} )
                subelm2.text = self.param_d[substrate]["dirichlet_ymax"]
                subelm2.tail = indent10

                subelm2 = ET.SubElement(subelm, "boundary_value",{"ID":"zmin", 
                    "enabled":str(self.param_d[substrate]["enable_zmin"])} )
                subelm2.text = self.param_d[substrate]["dirichlet_zmin"]
                subelm2.tail = indent10
                subelm2 = ET.SubElement(subelm, "boundary_value",{"ID":"zmax", 
                    "enabled":str(self.param_d[substrate]["enable_zmax"])} )
                subelm2.text = self.param_d[substrate]["dirichlet_zmax"]
                subelm2.tail = indent8
                        
                #              {'text':"foo",
                #               'xmlUrl':"bar",
                #               'htmlUrl':"grrr",
                #               })
                # uep.append(elm)
                uep.insert(idx,elm)
                idx += 1

        # print(prettify(self.xml_root))

	# 	<variable name="oxygen" units="mmHg" ID="0">
	# 		<physical_parameter_set>
	# 			<diffusion_coefficient units="micron^2/min">421.0</diffusion_coefficient>
	# 			<decay_rate units="1/min">.41</decay_rate>  
	# 		</physical_parameter_set>
	# 		<initial_condition units="mmHg">41.0</initial_condition>
	# 		<Dirichlet_boundary_condition units="mmHg" enabled="true">41.1</Dirichlet_boundary_condition>
    #         <Dirichlet_options>
 	# 			<boundary_value ID="xmin" enabled="false">1</boundary_value>
 	# 			<boundary_value ID="xmax" enabled="true">2</boundary_value>
 	# 			<boundary_value ID="ymin" enabled="false">3</boundary_value>
 	# 			<boundary_value ID="ymax" enabled="true">4</boundary_value>
 	# 			<boundary_value ID="zmin" enabled="false">5</boundary_value>
 	# 			<boundary_value ID="zmax" enabled="true">6</boundary_value>
 	# 		</Dirichlet_options>
	# 	</variable>


        # ------ Finally, append the flags that apply to all substrates
        if self.gradients.isChecked():
            self.xml_root.find(".//options//calculate_gradients").text = 'true'
        else:
            self.xml_root.find(".//options//calculate_gradients").text = 'false'

        if self.track_in_agents.isChecked():
            self.xml_root.find(".//options//track_internalized_substrates_in_each_agent").text = 'true'
        else:
            self.xml_root.find(".//options//track_internalized_substrates_in_each_agent").text = 'false'
    
    def clear_gui(self):
        pass