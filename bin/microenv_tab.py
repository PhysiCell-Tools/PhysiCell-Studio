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
from PyQt5.QtGui import QIcon, QDoubleValidator
from studio_classes import QCheckBox_custom

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class SubstrateDef(QWidget):
    def __init__(self, config_tab):
        super().__init__()
        # global self.microenv_params

        self.param_d = {}  # a dict of dicts - rwh/todo, used anymore?
        # self.substrate = {}
        self.current_substrate = None
        self.xml_root = None
        self.config_tab = config_tab
        self.new_substrate_count = 1

        self.is_3D = False

        self.default_rate_units = "1/min"
        self.dirichlet_units = "mmHG"

        self.ics_tab = None   # update in studio.py
        self.rules_tab = None   # update in studio.py

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
        stylesheet = """
        QTreeWidget::item:selected{
            background-color: rgb(236,236,236);
            color: black;
        }
        """
        self.tree.setStyleSheet(stylesheet)  # don't allow arrow keys to select
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
        self.new_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        bwidth = 70
        bheight = 32
        # self.new_button.setFixedWidth(bwidth)
        tree_w_hbox.addWidget(self.new_button)

        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_substrate)
        self.copy_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        # self.copy_button.setFixedWidth(bwidth)
        tree_w_hbox.addWidget(self.copy_button)

        self.delete_button = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
        self.delete_button.clicked.connect(self.delete_substrate)
        self.delete_button.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        del_btn_width = 50
        self.delete_button.setFixedWidth(del_btn_width)
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
        stylesheet = """ 
            QPushButton {
                color: #000000;
            }
            """

        self.vbox = QVBoxLayout()
        #------------------
        hbox = QHBoxLayout()
        label = QLabel("diffusion coefficient")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.diffusion_coef = QLineEdit()
        self.diffusion_coef.setValidator(QtGui.QDoubleValidator())
        self.diffusion_coef.textChanged.connect(self.diffusion_coef_changed)
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
        hbox.addWidget(self.dirichlet_bc)

        self.dirichlet_bc_units = QLabel(self.dirichlet_units)
        self.dirichlet_bc_units.setFixedWidth(units_width)
        hbox.addWidget(self.dirichlet_bc_units)

        self.apply_dc_button = QPushButton("Apply to all")
        # self.apply_dc_button.setFixedWidth(btn_width)
        self.apply_dc_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        self.apply_dc_button.clicked.connect(self.apply_dc_cb)
        hbox.addWidget(self.apply_dc_button)


        self.vbox.addLayout(hbox)

        #--------------------------
        dirichlet_options_bdy = QLabel("Dirichlet options per boundary:")
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

        self.enable_xmin = QCheckBox_custom("on")
        self.enable_xmin.stateChanged.connect(self.enable_xmin_cb)
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

        self.enable_xmax = QCheckBox_custom("on")
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

        self.enable_ymin = QCheckBox_custom("on")
        self.enable_ymin.stateChanged.connect(self.enable_ymin_cb)
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

        self.enable_ymax = QCheckBox_custom("on")
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

        self.enable_zmin = QCheckBox_custom("on")
        self.enable_zmin.stateChanged.connect(self.enable_zmin_cb)
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

        self.enable_zmax = QCheckBox_custom("on")
        self.enable_zmax.stateChanged.connect(self.enable_zmax_cb)
        hbox.addWidget(self.enable_zmax)
        self.vbox.addLayout(hbox)

        #-------------
        # Toggles for overall microenv (all substrates)
        self.vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("For all substrates: "))

        self.gradients = QCheckBox_custom("calculate gradients")
        self.gradients.stateChanged.connect(self.gradients_cb)
        hbox.addWidget(self.gradients)

        self.track_in_agents = QCheckBox_custom("track in agents")
        self.track_in_agents.stateChanged.connect(self.track_in_agents_cb)
        hbox.addWidget(self.track_in_agents)
        self.vbox.addLayout(hbox)

        #==================================================================
        self.vbox.addStretch()

        self.microenv_params.setLayout(self.vbox)

        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.microenv_params)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(splitter)

        self.new_substrate_count = self.config_tab.count_substrates()

    def apply_dc_cb(self):
        text = self.dirichlet_bc.text()
        self.dirichlet_xmin.setText(text)
        self.dirichlet_xmax.setText(text)
        self.dirichlet_ymin.setText(text)
        self.dirichlet_ymax.setText(text)
        self.dirichlet_zmin.setText(text)
        self.dirichlet_zmax.setText(text)


    def update_3D(self):
        zmax = float(self.config_tab.zmax.text())
        zmin = float(self.config_tab.zmin.text())
        zdel = float(self.config_tab.zdel.text())
        self.is_3D = False
        if (zmax-zmin) > zdel:
            self.is_3D = True
        self.dirichlet_zmin.setEnabled(self.is_3D)
        self.enable_zmin.setEnabled(self.is_3D)
        self.dirichlet_zmax.setEnabled(self.is_3D)
        self.enable_zmax.setEnabled(self.is_3D)

    def diffusion_coef_changed(self, text):
        self.param_d[self.current_substrate]["diffusion_coef"] = text

    def decay_rate_changed(self, text):
        self.param_d[self.current_substrate]["decay_rate"] = text
    def init_cond_changed(self, text):
        self.param_d[self.current_substrate]["init_cond"] = text

    def dirichlet_bc_changed(self, text):
        self.param_d[self.current_substrate]["dirichlet_bc"] = text

    def dirichlet_toggle_cb(self):
        return  # until we determine a more logical way to deal with this

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
    def new_substrate(self):
        while True:
            subname = "substrate%02d" % self.new_substrate_count
            if subname in self.config_tab.substrate_list:
                self.new_substrate_count += 1
            else:
                break
            
        # Make a new substrate (that's a copy of the currently selected one)
        # self.param_d[subname] = self.param_d[self.current_substrate].copy()  #rwh - "copy()" is critical

        self.param_d[subname] = copy.deepcopy(self.param_d[self.current_substrate])

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

        # NOooo!
        # self.param_d["gradients"] = bval
        # self.param_d["track_in_agents"] = bval

        # print("\n ----- new dict:")
        # for k in self.param_d.keys():
        #     print(" ===>>> ",k, " : ", self.param_d[k])

        self.new_substrate_count += 1

        self.celldef_tab.add_new_substrate(subname)
        self.config_tab.add_new_substrate(subname)
        self.ics_tab.add_new_substrate(subname)
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
        self.config_tab.add_new_substrate(subname)
        self.ics_tab.add_new_substrate(subname)

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

        # do *after* removing from param_d keys.
        if self.rules_tab:
            # self.rules_tab.delete_substrate(item_idx)
            self.rules_tab.delete_substrate(self.current_substrate)

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
        self.config_tab.delete_substrate(item_idx)
        self.ics_tab.delete_substrate(item_idx)


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
        self.config_tab.renamed_substrate(prev_name, self.current_substrate)
        self.ics_tab.renamed_substrate(prev_name, self.current_substrate)

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
        # self.dirichlet_bc_enabled.setChecked(self.param_d[self.current_substrate]["dirichlet_enabled"])
        # self.dirichlet_bc_enabled.setChecked(True)

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
    def populate_tree(self):
        logging.debug(f'=======================  microenv populate_tree  ======================= ')
        uep = self.xml_root.find(".//microenvironment_setup")
        if uep:

            self.tree.clear()
            idx = 0
            for var in uep:
                if var.tag == 'variable':
                    substrate_name = var.attrib['name']
                    self.current_substrate = substrate_name  # do this for the callback methods (rf. BEWARE below)
                    if idx == 0:
                        substrate_0th = substrate_name
                    self.param_d[substrate_name] = {}

                    treeitem = QTreeWidgetItem([substrate_name])
                    treeitem.setFlags(treeitem.flags() | QtCore.Qt.ItemIsEditable)

                    self.tree.insertTopLevelItem(idx,treeitem)
                    if idx == 0:  # select the 1st (0th) entry
                        self.tree.setCurrentItem(treeitem)

                    # Now fill the param dict for each substrate and the Qt widget values for the 0th

                    idx += 1

                    var_param_path = self.xml_root.find(".//microenvironment_setup//variable[" + str(idx) + "]//physical_parameter_set")
                    var_path = self.xml_root.find(".//microenvironment_setup//variable[" + str(idx) + "]")

                    diffusion_coef = var_param_path.find('.//diffusion_coefficient').text
                    self.param_d[substrate_name]["diffusion_coef"] = diffusion_coef
                    if idx == 1:
                        self.diffusion_coef.setText(diffusion_coef)

                    decay_rate = var_param_path.find('.//decay_rate').text
                    self.param_d[substrate_name]["decay_rate"] = decay_rate
                    if idx == 1:
                        self.decay_rate.setText(decay_rate)

                    init_cond = var_path.find('.//initial_condition').text
                    self.param_d[substrate_name]["init_cond"] = init_cond
                    if idx == 1:
                        self.init_cond.setText(init_cond)
                    
                    dc_ic_units = var_path.find('.//initial_condition').attrib['units']  # omg
                    logging.debug(f'dc_ic_units =  {dc_ic_units}')
                    self.param_d[substrate_name]["init_cond_units"] = dc_ic_units

                    dirichlet_bc_path = var_path.find('.//Dirichlet_boundary_condition')
                    dirichlet_bc = dirichlet_bc_path.text
                    self.param_d[substrate_name]["dirichlet_bc"] = dirichlet_bc  # always make it True??

                    dc_bc_units = dirichlet_bc_path.attrib['units']  # omg
                    logging.debug(f'dc_bc_units = {dc_bc_units}')
                    self.param_d[substrate_name]["dirichlet_bc_units"] = dc_bc_units

                    if dirichlet_bc_path.attrib['enabled'].lower() == "false":
                        self.param_d[substrate_name]["dirichlet_enabled"] = False
                    else:
                        self.param_d[substrate_name]["dirichlet_enabled"] = True

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
                        for bv in options_path:
                            logging.debug(f'bv = {bv}')
                            if "xmin" in bv.attrib['ID'].lower():
                                self.param_d[substrate_name]["dirichlet_xmin"] = bv.text
                                logging.debug(f'   -------- {substrate_name}:  dirichlet_xmin = {bv.text}')

                                # BEWARE: doing a 'setText' here will invoke the callback associated with
                                # the widget (e.g., self.dirichlet_xmin.textChanged.connect(self.dirichlet_xmin_changed))

                                if "true" in bv.attrib['enabled'].lower():
                                    self.param_d[substrate_name]["enable_xmin"] = True
                            elif "xmax" in bv.attrib['ID']:
                                self.param_d[substrate_name]["dirichlet_xmax"] = bv.text
                                if "true" in bv.attrib['enabled'].lower():
                                    self.param_d[substrate_name]["enable_xmax"] = True
                            elif "ymin" in bv.attrib['ID']:
                                self.param_d[substrate_name]["dirichlet_ymin"] = bv.text
                                if "true" in bv.attrib['enabled'].lower():
                                    self.param_d[substrate_name]["enable_ymin"] = True
                            elif "ymax" in bv.attrib['ID']:
                                self.param_d[substrate_name]["dirichlet_ymax"] = bv.text
                                if "true" in bv.attrib['enabled'].lower():
                                    self.param_d[substrate_name]["enable_ymax"] = True
                            elif "zmin" in bv.attrib['ID']:
                                self.param_d[substrate_name]["dirichlet_zmin"] = bv.text
                                if "true" in bv.attrib['enabled'].lower():
                                    self.param_d[substrate_name]["enable_zmin"] = True
                            elif "zmax" in bv.attrib['ID']:
                                self.param_d[substrate_name]["dirichlet_zmax"] = bv.text
                                if "true" in bv.attrib['enabled'].lower():
                                    self.param_d[substrate_name]["enable_zmax"] = True
                    else:
                        default_dc_enabled = self.param_d[substrate_name]["dirichlet_enabled"]
                        self.param_d[substrate_name]["enable_xmin"] = default_dc_enabled
                        self.param_d[substrate_name]["enable_xmax"] = default_dc_enabled
                        self.param_d[substrate_name]["enable_ymin"] = default_dc_enabled
                        self.param_d[substrate_name]["enable_ymax"] = default_dc_enabled
                        self.param_d[substrate_name]["enable_zmin"] = default_dc_enabled
                        self.param_d[substrate_name]["enable_zmax"] = default_dc_enabled

                elif var.tag == 'options':
                    self.param_d["gradients"] = False
                    self.param_d["track_in_agents"] = False
                    for opt in var:
                        logging.debug(f'------- options: {opt}')
                        if "calculate_gradients" in opt.tag:
                            if "true" in opt.text.lower():
                                self.param_d["gradients"] = True
                        elif "track_internalized_substrates_in_each_agent" in opt.tag:
                            if "true" in opt.text.lower():
                                self.param_d["track_in_agents"] = True

        self.current_substrate = substrate_0th
        self.tree.setCurrentItem(self.tree.topLevelItem(0))  # select the top (0th) item
        self.tree_item_clicked_cb(self.tree.topLevelItem(0), 0)  # and invoke its callback to fill widget values

        logging.debug(f'\n\n=======================  leaving microenv populate_tree  =====================')

    #----------------------------------------------------------------------------
    def first_substrate_name(self):
        uep = self.xml_root.find(".//microenvironment_setup//variable")
        if uep:
                return(uep.attrib['name'])

            #----------------------------------------------------------------------------
            # Read values from the params_d and generate XML

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

                subelm = ET.SubElement(elm, 'initial_condition', {"units":self.param_d[substrate]["init_cond_units"]})
                subelm.text = self.param_d[substrate]["init_cond"]
                subelm.tail = indent8
                    # self.param_d[substrate_name]["dirichlet_bc_units"] = dc_bc_units
                dirichlet_BC_flag = False
                if self.param_d[substrate]["enable_xmin"] or self.param_d[substrate]["enable_xmax"] or self.param_d[substrate]["enable_ymin"]  or self.param_d[substrate]["enable_ymax"]: 
                    dirichlet_BC_flag = True
                if not dirichlet_BC_flag and self.is_3D:
                    if self.param_d[substrate]["enable_zmin"] or self.param_d[substrate]["enable_zmax"]:
                        dirichlet_BC_flag = True
                subelm = ET.SubElement(elm, "Dirichlet_boundary_condition",
                        {"units":self.param_d[substrate]["dirichlet_bc_units"], 
                         "enabled":str(dirichlet_BC_flag) })
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
                        
                uep.insert(idx,elm)
                idx += 1

        # ------ Finally, append the flags that apply to all substrates
        if self.gradients.isChecked():
            self.xml_root.find(".//options//calculate_gradients").text = 'true'
        else:
            self.xml_root.find(".//options//calculate_gradients").text = 'false'

        if self.track_in_agents.isChecked():
            self.xml_root.find(".//options//track_internalized_substrates_in_each_agent").text = 'true'
        else:
            self.xml_root.find(".//options//track_internalized_substrates_in_each_agent").text = 'false'
    
        if self.ics_tab.ic_substrates_enabled.isChecked():
            if self.xml_root.find(".//microenvironment_setup//options//initial_condition") is None:
                # add this eleement if it does not exist
                elm = ET.Element("initial_condition", {"type":"csv", "enabled":'True'})
                ET.SubElement(elm, 'filename')
                self.xml_root.find('.//microenvironment_setup//options').insert(2,elm) # [calculate_gradients, track_internalized_substrates_in_each_agent, initial_condition]
            self.xml_root.find(".//microenvironment_setup//options//initial_condition").attrib['type'] = 'csv'
            self.xml_root.find(".//microenvironment_setup//options//initial_condition").attrib['enabled'] = 'true'
            self.xml_root.find(".//microenvironment_setup//options//initial_condition//filename").text = self.ics_tab.full_substrate_ic_fname
        elif (self.xml_root.find(".//microenvironment_setup//options//initial_condition") is not None) and (self.xml_root.find(".//microenvironment_setup//options//initial_condition").attrib['type'].lower()=="csv"): # then make sure this is disabled
            self.xml_root.find(".//microenvironment_setup//options//initial_condition").attrib['enabled'] = 'false'
    def clear_gui(self):
        pass