"""
Authors:
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
- also rf. Credits.md
"""

import sys
import os
import csv
# import logging

import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from pathlib import Path
# import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QLineEdit, QGroupBox,QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,QGridLayout,QPushButton,QFileDialog,QTableWidget,QTableWidgetItem,QHeaderView
from PyQt5.QtWidgets import QMessageBox, QCompleter, QSizePolicy
from PyQt5.QtCore import QSortFilterProxyModel, Qt, QRect
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QRegExpValidator
# from PyQt5.QtGui import QTextEdit
from PyQt5 import QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from multivariate_rules import Window_plot_rules
from studio_classes import ExtendedCombo, HoverWarning, QVLine, QLineEdit_custom, HoverQuestion
from studio_functions import show_studio_warning_window

class RulesPlotWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.label = QLabel("Rule Plot")
        # self.layout.addWidget(self.label)

        self.figure = plt.figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setStyleSheet("background-color:transparent;")
        self.ax0 = self.figure.add_subplot(111, adjustable='box')
        self.layout.addWidget(self.canvas)

        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("background-color: lightgreen;")
        # self.close_button.setFixedWidth(150)
        self.close_button.clicked.connect(self.close_plot_cb)
        self.layout.addWidget(self.close_button)

        self.setLayout(self.layout)

    def close_plot_cb(self):
        self.close()
#---------------------

# Overloading the QCheckBox widget 
class MyQCheckBox(QCheckBox):  # leaving this here since (and not replacing with QCheckBox_custom since this also introduces new fields)
    def __init__(self,name=""):
        super(QCheckBox, self).__init__(name)

        checkbox_style = """
                QCheckBox::indicator:checked {
                    background-color: rgb(255,255,255);
                    border: 1px solid #5A5A5A;
                    width : 15px;
                    height : 15px;
                    border-radius : 3px;
                    image: url(images:checkmark.png);
                }
                QCheckBox::indicator:unchecked
                {
                    background-color: rgb(255,255,255);
                    border: 1px solid #5A5A5A;
                    width : 15px;
                    height : 15px;
                    border-radius : 3px;
                }
                """
        self.setStyleSheet(checkbox_style)

        self.vname = None
        # self.idx = None  # index
        self.wrow = 0  # widget's row in a table
        self.wcol = 0  # widget's column in a table


# Overloading the QLineEdit widget to let us map it to its variable name. Ugh.
class MyQLineEdit(QLineEdit):
    vname = None
    # idx = None  # index
    wrow = 0
    wcol = 0
    prev = None

#----------------------------------------------------------------------
class Rules(QWidget):
    # def __init__(self, nanohub_flag):
    def __init__(self, nanohub_flag, microenv_tab, celldef_tab):
        super().__init__()

        self.rules_plot = None

        self.nanohub_flag = nanohub_flag
        self.homedir = '.'  # reset in studio.py
        self.absolute_data_dir = None   # updated in studio.py

        self.microenv_tab = microenv_tab
        self.celldef_tab = celldef_tab

        self.celltype_name = None
        self.signal = None
        self.behavior = None
        self.scale_base_for_max = 10.0
        self.scale_base_for_min = 0.1

        self.max_rule_table_rows = 99

        self.update_rules_for_custom_data = True

        self.max_rule_table_cols = 9   # v2: cell type, signal, direction, behavior, max, half-max, Hill power, apply to dead, baseval

        # table columns' indices
        icol = 0
        self.rules_celltype_idx = icol
        icol += 1
        self.rules_signal_idx = icol
        icol += 1
        self.rules_direction_idx = icol
        icol += 1
        self.rules_response_idx = icol   # behavior
        icol += 1
        # self.rules_minval_idx = icol
        # icol += 1
        self.rules_maxval_idx = icol
        icol += 1
        self.rules_halfmax_idx = icol
        icol += 1
        self.rules_hillpower_idx = icol
        icol += 1
        self.rules_applydead_idx = icol
        icol += 1
        self.rules_baseval_idx = icol
        icol += 1

        self.num_cols = icol
        print("self.num_cols = ",self.num_cols)

        self.num_rules = 0

        # self.studio_flag = studio_flag
        self.studio_flag = None
        self.vis_tab = None

        self.xml_root = None

        # self.tab = QWidget()
        # self.tabs.resize(200,5)
        
        #-------------------------------------------
        label_width = 110
        value_width = 60
        label_height = 20
        units_width = 170

        self.scroll = QScrollArea()  # might contain centralWidget

        self.rules_params = QWidget()

        # self.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Expanding)  # horiz, vert
        # self.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Fixed)  # horiz, vert
        # self.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Fixed)

        # self.rules_tab_layout = QGridLayout()
        self.rules_tab_layout = QVBoxLayout()

        self.substrates = []

        # ----- signals:
        # -- <ubstrates>
        # -- intracellular <substrate>
        # -- <substrate> <radient>
        # -- pressure
        # -- volume
        # -- contact with <cell type>
        # -- damage
        # -- dead
        # -- total attack time
        # -- damage delivered
        # -- time
        self.signal_l = []

        self.response_l = []

        top_half_hbox = QHBoxLayout()
        top_left_half_vbox = QVBoxLayout()
        top_right_half_vbox = QVBoxLayout()
        top_half_hbox.addLayout(top_left_half_vbox)
        top_half_hbox.addWidget(QVLine())
        top_half_hbox.addLayout(top_right_half_vbox)
        self.rules_tab_layout.addLayout(top_half_hbox)

        hlayout = QHBoxLayout()

        label = QLabel("Cell Type")
        label.setFixedWidth(60)
        label.setAlignment(QtCore.Qt.AlignCenter)

        hlayout.addWidget(label)

        self.celltype_combobox = QComboBox()
        self.celltype_combobox.setFixedWidth(200)
        self.celltype_combobox.currentIndexChanged.connect(self.celltype_combobox_changed_cb)  
        hlayout.addWidget(self.celltype_combobox) # w, expand, align

        self.add_rule_button = QPushButton("Add rule")
        self.add_rule_button.setStyleSheet("background-color: lightgreen")
        self.add_rule_button.clicked.connect(self.add_rule_cb)
        hlayout.addWidget(self.add_rule_button,0) 

        self.plot_new_rule_button = QPushButton("Plot")
        self.plot_new_rule_button.setStyleSheet("background-color: lightgreen")
        self.plot_new_rule_button.clicked.connect(self.plot_new_rule_cb)
        hlayout.addWidget(self.plot_new_rule_button,0) 

        self.reuse_plot_flag = True
        self.reuse_plot_w = MyQCheckBox("reuse plot window")
        self.reuse_plot_w.setChecked(self.reuse_plot_flag)
        self.reuse_plot_w.setEnabled(False)

        #------------
        hlayout.addStretch(1)
        top_left_half_vbox.addLayout(hlayout) 

        #--------------
        hlayout = QHBoxLayout()

        lwidth = 250
        label = QLabel("----- Signal -----")
        label.setFixedWidth(lwidth)
        label.setAlignment(QtCore.Qt.AlignCenter)
        hlayout.addWidget(label) 

        label = QLabel("")
        label.setFixedWidth(50)
        hlayout.addWidget(label) 

        label = QLabel("----- Behavior -----")
        label.setFixedWidth(lwidth)
        label.setFixedWidth(150)
        label.setAlignment(QtCore.Qt.AlignCenter)
        hlayout.addWidget(label) 

        self.up_down_combobox = QComboBox()
        self.up_down_combobox.setFixedWidth(110)
        self.up_down_combobox.addItem("increases")
        self.up_down_combobox.addItem("decreases")
        self.up_down_combobox.currentIndexChanged.connect(self.up_down_combobox_changed_cb)
        hlayout.addWidget(self.up_down_combobox)

        hlayout.addStretch(1)
        top_left_half_vbox.addLayout(hlayout) 

        #----------------------------
        hlayout = QHBoxLayout()

        wwidth = 300
        self.signal_model = QStandardItemModel()
        self.signal_combobox = ExtendedCombo()
        self.signal_combobox.setFixedWidth(wwidth)
        self.signal_combobox.setModel(self.signal_model)
        self.signal_combobox.setModelColumn(0)

        self.signal_combobox.currentIndexChanged.connect(self.signal_combobox_changed_cb)  
        hlayout.addWidget(self.signal_combobox)

        #----
        # Behavior combobox
        self.response_model = QStandardItemModel()
        self.response_combobox = ExtendedCombo()
        self.response_combobox.setFixedWidth(wwidth)
        self.response_combobox.setModel(self.response_model)
        self.response_combobox.setModelColumn(0)
        self.response_combobox.currentIndexChanged.connect(self.response_combobox_changed_cb)  

        hlayout.addWidget(self.response_combobox) 

        hlayout.addStretch(1)
        top_left_half_vbox.addLayout(hlayout)

        top_right_half_vbox.addStretch(1)
        hlayout = QHBoxLayout()
        hlayout.addStretch(1)
        rules_enabled_label = QLabel("Enable rules:")
        hlayout.addWidget(rules_enabled_label)
        self.rules_enabled = MyQCheckBox()
        hlayout.addWidget(self.rules_enabled)
        hlayout.addStretch(1)
        top_right_half_vbox.addLayout(hlayout)

        label = QLabel("Make sure to save rules below before running simulations!")
        hlayout = QHBoxLayout()
        hlayout.addStretch(1)
        hlayout.addWidget(label)
        hlayout.addStretch(1)
        top_right_half_vbox.addLayout(hlayout)

        hlayout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        if self.nanohub_flag:
            self.save_button.setEnabled(True)
        self.save_button.setFixedWidth(100)
        self.save_button.setStyleSheet("background-color: yellow")
        self.save_button.clicked.connect(self.save_rules_cb)
        hlayout.addWidget(self.save_button)

        hlayout.addWidget(QLabel("to:"))

        self.rules_folder = QLineEdit()
        self.rules_folder.setPlaceholderText("folder")
        if self.nanohub_flag:
            self.rules_folder.setEnabled(False)
        # self.rules_folder.setFixedWidth(200)
        hlayout.addWidget(self.rules_folder)

        hlayout.addWidget(QLabel(os.path.sep))

        self.rules_file = QLineEdit_custom()
        csv_validator = QRegExpValidator(QtCore.QRegExp(r'^.+\.csv$'))
        self.rules_file.setValidator(csv_validator)
        self.rules_file.setPlaceholderText("file.csv")
        if self.nanohub_flag:
            self.rules_file.setEnabled(True)
        # self.rules_file.setFixedWidth(200)
        hlayout.addWidget(self.rules_file) 

        top_right_half_vbox.addLayout(hlayout)

        hlayout = QHBoxLayout()
        hlayout.addStretch(1)

        self.import_rules_button = QPushButton("Import")
        if self.nanohub_flag:
            self.import_rules_button.setEnabled(True)
        self.import_rules_button.setFixedWidth(100)
        self.import_rules_button.setStyleSheet("background-color: yellow")
        self.import_rules_button.clicked.connect(self.import_rules_cb)
        hlayout.addWidget(self.import_rules_button) 

        self.import_rules_question_label = HoverQuestion("Open a file dialog to select a new rules file to import.")
        self.import_rules_question_label.show_icon()
        hlayout.addWidget(self.import_rules_question_label)
        
        hlayout.addStretch(1)

        top_right_half_vbox.addLayout(hlayout)

        top_right_half_vbox.addStretch(1)
        #------------
        lwidth = 30

        #----------------------------------
        hlayout = QHBoxLayout()

        label = QLabel("")
        lwidth = 300
        label.setFixedWidth(lwidth)
        hlayout.addWidget(label) 

        label = QLabel("Base value")
        lwidth = 72
        label.setFixedWidth(lwidth)
        label.setAlignment(QtCore.Qt.AlignCenter)
        hlayout.addWidget(label) 

        self.rule_base_val = QLineEdit()
        self.rule_base_val.setEnabled(False)
        self.rule_base_val.setStyleSheet("background-color: lightgray")
        self.rule_base_val.setText('0.1')
        self.rule_base_val.setValidator(QtGui.QDoubleValidator())
        self.rule_base_val.textChanged.connect(self.rule_base_or_max_val_cb)
        hlayout.addWidget(self.rule_base_val)

        hlayout.addStretch(1)
        top_left_half_vbox.addLayout(hlayout)

        #-------------------------------------
        hlayout = QHBoxLayout()
        lwidth = 60
        label = QLabel("Half-max")
        label.setFixedWidth(lwidth)
        label.setAlignment(QtCore.Qt.AlignCenter)
        hlayout.addWidget(label) 

        self.rule_half_max = QLineEdit()
        self.rule_half_max.setText('0.5')
        self.rule_half_max.setFixedWidth(100)
        self.rule_half_max.setValidator(QtGui.QDoubleValidator())
        hlayout.addWidget(self.rule_half_max)

        #---
        label = QLabel("")
        lwidth = 95
        label.setFixedWidth(lwidth)
        hlayout.addWidget(label) 

        #---
        label = QLabel("Saturation value")
        label.setFixedWidth(100)
        label.setAlignment(QtCore.Qt.AlignCenter)
        hlayout.addWidget(label) 

        self.rule_max_val = QLineEdit()  # saturation value for behavior
        self.rule_max_val.setText('1.0')
        self.rule_max_val.setValidator(QtGui.QDoubleValidator())
        self.rule_max_val.textChanged.connect(self.rule_base_or_max_val_cb)
        hlayout.addWidget(self.rule_max_val)

        self.rule_max_val_warning_label = HoverWarning("")
        hlayout.addWidget(self.rule_max_val_warning_label)

        hlayout.addStretch(1)
        top_left_half_vbox.addLayout(hlayout) 

        #---------------------
        hlayout = QHBoxLayout()

        label = QLabel("Hill power")
        label.setFixedWidth(60)
        label.setAlignment(QtCore.Qt.AlignCenter)
        hlayout.addWidget(label) 

        self.rule_hill_power = QLineEdit()
        self.rule_hill_power.setText('4')
        self.rule_hill_power.setFixedWidth(30)
        self.rule_hill_power.setValidator(QtGui.QIntValidator())
        hlayout.addWidget(self.rule_hill_power)

        #---
        label = QLabel()
        label.setFixedWidth(210)
        label.setAlignment(QtCore.Qt.AlignCenter)
        hlayout.addWidget(label) 

        #---
        self.dead_cells_rule = False
        self.dead_cells_checkbox = MyQCheckBox("apply to dead")
        hlayout.addWidget(self.dead_cells_checkbox)

        top_left_half_vbox.addLayout(hlayout)


        #----------------------
        rules_table_vbox = self.create_rules_table()

        self.rules_tab_layout.addLayout(rules_table_vbox) 

        #----------------------
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Select a row to:"))

        groupbox = QGroupBox()
        groupbox.setStyleSheet("QGroupBox { border: 1px solid black;}")
        groupbox.setLayout(hlayout)
        groupbox.setFixedWidth(450)  # omg

        delete_rule_btn = QPushButton("Delete rule")
        delete_rule_btn.setFixedWidth(150)
        delete_rule_btn.clicked.connect(self.delete_rule_cb)
        delete_rule_btn.setStyleSheet("background-color: yellow")
        hlayout.addWidget(delete_rule_btn)

        plot_rule_btn = QPushButton("Plot rule")
        plot_rule_btn.setFixedWidth(150)
        plot_rule_btn.clicked.connect(self.plot_rule_cb)
        plot_rule_btn.setStyleSheet("background-color: lightgreen")
        hlayout.addWidget(plot_rule_btn)

        hlayout.addStretch(1)
        #-------
        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(groupbox) 

        self.plot_rules_button = QPushButton("Plot rules")
        self.plot_rules_button.setFixedWidth(150)
        self.plot_rules_button.setStyleSheet("background-color: lightgreen")
        self.plot_rules_button.clicked.connect(self.plot_rules)
        hlayout2.addWidget(self.plot_rules_button) 

        self.clear_button = QPushButton("Clear table")
        self.clear_button.setFixedWidth(150)
        self.clear_button.setStyleSheet("background-color: yellow")
        self.clear_button.clicked.connect(self.clear_rules)
        hlayout2.addWidget(self.clear_button) 

        self.rules_tab_layout.addLayout(hlayout2) 
        #----------------------
        self.insert_hacky_blank_lines(self.rules_tab_layout)

        #==================================================================
        self.rules_params.setLayout(self.rules_tab_layout)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        self.scroll.setWidget(self.rules_params) 

        self.layout = QVBoxLayout(self)  # leave this!
        self.layout.addWidget(self.scroll)


    #--------------------------------------------------------
    def validate_saturation_value(self):
        max_val = float(self.rule_max_val.text())
        try:
            base_val = float(self.rule_base_val.text())
        except:
            return
        show_warning = False
        text = ''
        if self.up_down_combobox.currentText() == "increases":
            if max_val < base_val:
                show_warning = True
                text = "Max value must be >= base value"
        else:
            if max_val > base_val:
                show_warning = True
                text = "Max value must be <= base value"
        if show_warning:
            self.rule_max_val_warning_label.setHoverText(text)
            self.rule_max_val_warning_label.show_icon()
        else:
            self.rule_max_val_warning_label.hide_icon()
    
    def up_down_combobox_changed_cb(self, idx):
        if self.rule_max_val.validator().validate(self.rule_max_val.text(), 0)[0] != QtGui.QValidator.Acceptable:
            self.rule_max_val_warning_label.hide_icon()
            return
        self.validate_saturation_value()

    def rule_base_or_max_val_cb(self, text):
        if self.sender().validator().validate(text, 0)[0] != QtGui.QValidator.Acceptable:
            self.rule_max_val_warning_label.hide_icon()
            return
        self.validate_saturation_value()

    #--------------------------------------------------------
    def create_rules_table(self):
        rules_table_w = QWidget()
        rules_table_scroll = QScrollArea()
        vlayout = QVBoxLayout()
        self.rules_table = QTableWidget()

        self.rules_table.setColumnCount(9)
        self.rules_table.setRowCount(self.max_rule_table_rows)
        self.rules_table.setColumnHidden(8, True) # hidden column base value

        header = self.rules_table.horizontalHeader()       

        self.rules_table.setHorizontalHeaderLabels(['CellType','Signal','Direction','Behavior', 'Saturation value','Half-max','Hill power','Apply to dead','Base value'])

        # Don't like the behavior these offer, e.g., locks down width of 0th column :/
        # header = self.rules_table.horizontalHeader()       
        # header.setSectionResizeMode(0, QHeaderView.Stretch)
        # header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            
        for irow in range(self.max_rule_table_rows):
            # print("------------ rules table row # ",irow)

            # ------- CellType
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            rx_valid_varname = QtCore.QRegExp("^[a-zA-Z][a-zA-Z0-9_ ]+$")
            name_validator = QtGui.QRegExpValidator(rx_valid_varname )
            w_me.setValidator(name_validator)

            self.rules_table.setCellWidget(irow, self.rules_celltype_idx, w_me)

            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_celltype_idx

            # ------- Signal
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_signal_idx
            self.rules_table.setCellWidget(irow, self.rules_signal_idx, w_me)
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- Direction
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_direction_idx
            self.rules_table.setCellWidget(irow, self.rules_direction_idx, w_me)
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- response  (behavior)
            # w_varval = MyQLineEdit('0.0')
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            # item = QTableWidgetItem('')
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_response_idx
            # w_me.idx = irow   # rwh: is .idx used?
            # w_me.setValidator(QtGui.QDoubleValidator())
            # self.rules_table.setItem(irow, self.custom_icol_value, item)
            self.rules_table.setCellWidget(irow, self.rules_response_idx, w_me)
            # w_varval.textChanged[str].connect(self.custom_data_value_changed)  # being explicit about passing a string 

            # ------- Min val
            # w_me = MyQLineEdit()
            # w_me.setValidator(QtGui.QDoubleValidator())
            # w_me.setFrame(False)
            # w_me.vname = w_me  
            # w_me.wrow = irow
            # w_me.wcol = self.rules_minval_idx
            # self.rules_table.setCellWidget(irow, self.rules_minval_idx, w_me)
            # # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- Base val
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            # item = QTableWidgetItem('')
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_baseval_idx
            # w_var_desc.idx = irow
            # w_varval.setValidator(QtGui.QDoubleValidator())
            # self.rules_table.setItem(irow, self.custom_icol_desc, item)
            self.rules_table.setCellWidget(irow, self.rules_baseval_idx, w_me)
            # w_var_desc.textChanged[str].connect(self.custom_data_desc_changed)  # being explicit about passing a string 

            # ------- Max val
            w_me = MyQLineEdit()
            w_me.setValidator(QtGui.QDoubleValidator())
            w_me.setFrame(False)
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_maxval_idx
            self.rules_table.setCellWidget(irow, self.rules_maxval_idx, w_me)
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- Half-max
            w_me = MyQLineEdit()
            w_me.setValidator(QtGui.QDoubleValidator())
            w_me.setFrame(False)
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_halfmax_idx
            self.rules_table.setCellWidget(irow, self.rules_halfmax_idx, w_me)
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- Hill power
            w_me = MyQLineEdit()
            w_me.setValidator(QtGui.QIntValidator())
            w_me.setFrame(False)
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_hillpower_idx
            self.rules_table.setCellWidget(irow, self.rules_hillpower_idx, w_me)
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 


            # ------- Apply to dead
            w_me = MyQCheckBox()
            # w_var_conserved.setFrame(False)
            w_me.vname = "foobar"  
            w_me.wrow = irow
            w_me.wcol = self.rules_applydead_idx
            # w_me.clicked.connect(self.custom_var_conserved_clicked)

            # rwh NB! Leave these lines in (for less confusing clicking/coloring of cell)
            item = QTableWidgetItem('')
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            self.rules_table.setItem(irow, self.rules_applydead_idx, item)

            self.rules_table.setCellWidget(irow, self.rules_applydead_idx, w_me)

        # self.rules_table.itemClicked.connect(self.custom_data_clicked_cb)
        # self.rules_table.cellChanged.connect(self.custom_data_changed_cb)

        vlayout.addWidget(self.rules_table)

        # self.layout = QVBoxLayout(self)
        # # self.layout.addLayout(self.controls_hbox)

        # self.layout.addWidget(self.splitter)

        # rules_table_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        # rules_table_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        # rules_table_scroll.setWidgetResizable(True)
        # rules_table_scroll.setWidget(rules_table_w) 


        # custom_data_tab.setLayout(glayout)
        # custom_data_tab.setLayout(vlayout)
        # return rules_table_scroll
        return vlayout

        #--------------------------------------------------------
    def sizeHint(self):
        return QtCore.QSize(300,80) 

        #--------------------------------------------------------
    def insert_hacky_blank_lines(self, glayout):
        idx_row = 4
        for idx in range(11):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idx_row += 1
            # glayout.addWidget(blank_line, idx_row,0, 1,1) # w, row, column, rowspan, colspan

    #-----------------------------------------------------------
    def substrate_rename(self,idx,old_name,new_name):
        # make a possible_superstrings list of the current cell types and substrates to check if the one being changed is a substring of any of these 
        possible_superstrings = [self.celltype_combobox.itemText(i) for i in range(self.celltype_combobox.count())]
        possible_superstrings += self.substrates
        idx = self.substrates.index(old_name)
        self.substrates[idx] = new_name
        self.fill_signals_widget()
        self.fill_responses_widget()
        self.find_and_replace_rules_table(old_name, new_name, possible_superstrings) # drb 24-05-20: not sure if find_and_replace_rules_table must come after the fill calls, but it works here so I'm just leaving it and recording the superstrings above

    #-----------------------------------------------------------
    def delete_substrate(self,name):
        self.substrates.remove(name)
        self.fill_signals_widget()
        self.fill_responses_widget()

    #-----------------------------------------------------------
    def add_new_substrate(self,name):
        self.substrates.append(name)
        self.fill_signals_widget()
        self.fill_responses_widget()

    #-----------------------------------------------------------
    def add_new_celltype(self,name):
        self.celltype_combobox.addItem(name)
        self.fill_signals_widget()
        self.fill_responses_widget()

    #-----------------------------------------------------------
    def delete_celltype(self,idx):
        self.celltype_combobox.removeItem(idx)
        self.fill_signals_widget()
        self.fill_responses_widget()


    #-----------------------------------------------------------
    def cell_def_rename(self,idx,old_name,new_name):
        # make a possible_superstrings list of the current cell types and substrates to check if the one being changed is a substring of any of these 
        possible_superstrings = [self.celltype_combobox.itemText(i) for i in range(self.celltype_combobox.count())]
        possible_superstrings += self.substrates

        self.celltype_combobox.setItemText(idx, new_name)
        self.fill_signals_widget()
        self.fill_responses_widget()
        self.find_and_replace_rules_table(old_name, new_name, possible_superstrings) # drb 24-05-20: not sure if find_and_replace_rules_table must come after the fill calls, but it works here so I'm just leaving it and recording the superstrings above


    #-----------------------------------------------------------
    def celltype_combobox_changed_cb(self, idx):
        self.celltype_name = self.celltype_combobox.currentText()
        if self.signal:
            print("        signal= ", self.signal)
        print("          ", self.celldef_tab.param_d.keys())

    #-----------------------------------------------------------
    def custom_data_rename(self, old_name, new_name):
        possible_superstrings = [self.celltype_combobox.itemText(i) for i in range(self.celltype_combobox.count())]
        possible_superstrings += self.substrates
        self.fill_signals_widget()
        self.fill_responses_widget()
        self.find_and_replace_rules_table(old_name, new_name, possible_superstrings)

    #-----------------------------------------------------------
    # ---- Behaviors:
    # [s + " secretion”], [s + " secretion target”], [s + " uptake"], [s + " export"], where s = substrate/signal name
    # ["cycle entry”]
    # ["exit from cycle phase " + str(idx)], idx=0,1,…,5   (isn’t “smart” to match cell type’s cycle)
    # ["apoptosis", "necrosis", "migration speed", "migration bias", "migration persistence time"]
    # ["chemotactic response to " + s]
    # ["cell-cell adhesion", "cell-cell adhesion elastic constant"]
    # Each ct = cell type name: ["adhesive affinity to " + ct]
    # ["relative maximum adhesion distance", "cell-cell repulsion", "cell-BM adhesion", "cell-BM repulsion", "phagocytose dead cell"]
    # [verb + ct] where verb=["phagocytose ","attack ","fuse to ","transform to ","immunogenicity to "]
    # ["is_movable", "cell attachment rate", "cell detachment rate", "maximum number of cell attachments"]
    # Each cv = custom var name: ["custom:" + cv]

    def update_base_value(self):
        behavior = self.response_combobox.currentText()
        self.update_base_value_by_name(behavior, True)

    def update_base_value_by_name(self, behavior, update_widgets):
        key0 = self.celltype_combobox.currentText()
        btokens = behavior.split()
        if len(btokens) == 0:
            return

        base_val = '??'
        if btokens[0] in ["cycle", "exit"]:
            cycle_model_idx = self.celldef_tab.param_d[key0]['cycle_choice_idx']
            # print(behavior, cycle_model_idx )
            #{0:"live", 1:"basic Ki67", 2:"advanced Ki67", 3:"flow cytometry", 4:"Flow cytometry model (separated)", 5:"cycling quiescent"}
            if (behavior == 'cycle entry' or behavior == 'exit from cycle phase 0'):
                if cycle_model_idx == 0 : base_val = self.celldef_tab.param_d[key0]['cycle_live_00_trate']
                elif cycle_model_idx == 1 : base_val = self.celldef_tab.param_d[key0]['cycle_Ki67_01_trate']
                elif cycle_model_idx == 2 : base_val = self.celldef_tab.param_d[key0]['cycle_advancedKi67_01_trate']
                elif cycle_model_idx == 3 : base_val = self.celldef_tab.param_d[key0]['cycle_flowcyto_01_trate']
                elif cycle_model_idx == 4 : base_val = self.celldef_tab.param_d[key0]['cycle_flowcytosep_01_trate']
                elif cycle_model_idx == 5 : base_val = self.celldef_tab.param_d[key0]['cycle_quiescent_01_trate']
            elif (behavior == 'exit from cycle phase 1'):
                if cycle_model_idx == 1 : base_val = self.celldef_tab.param_d[key0]['cycle_Ki67_10_trate']
                elif cycle_model_idx == 2 : base_val = self.celldef_tab.param_d[key0]['cycle_advancedKi67_12_trate']
                elif cycle_model_idx == 3 : base_val = self.celldef_tab.param_d[key0]['cycle_flowcyto_12_trate']
                elif cycle_model_idx == 4 : base_val = self.celldef_tab.param_d[key0]['cycle_flowcytosep_12_trate']
                elif cycle_model_idx == 5 : base_val = self.celldef_tab.param_d[key0]['cycle_quiescent_10_trate']
            elif (behavior == 'exit from cycle phase 2'):
                if cycle_model_idx == 2 : base_val = self.celldef_tab.param_d[key0]['cycle_advancedKi67_20_trate']
                elif cycle_model_idx == 3 : base_val = self.celldef_tab.param_d[key0]['cycle_flowcyto_20_trate']
                elif cycle_model_idx == 4 : base_val = self.celldef_tab.param_d[key0]['cycle_flowcytosep_23_trate']
            elif (behavior == 'exit from cycle phase 3'):
                if cycle_model_idx == 4 : base_val = self.celldef_tab.param_d[key0]['cycle_flowcytosep_30_trate']
                        
        elif btokens[0] in self.substrates:
            key1 = 'secretion'
            key2 = btokens[0]
            if 'target' in btokens:
                key3 = "secretion_target"
            elif 'uptake' in btokens:
                key3 = "uptake_rate"
            elif 'export' in btokens:
                key3 = "net_export_rate"
            else:  # just "<substrate> secretion" which mean its rate
                key3 = "secretion_rate"
            try:
                base_val = self.celldef_tab.param_d[key0][key1][key2][key3]
            except:
                print("update_base_value(): ---- got exception")
                return
        elif btokens[0] == 'apoptosis':
            base_val = self.celldef_tab.param_d[key0]['apoptosis_death_rate']
        elif btokens[0] == 'necrosis':
            base_val = self.celldef_tab.param_d[key0]['necrosis_death_rate']
        elif btokens[0] == 'migration':
            if btokens[1] == 'speed':
                base_val = self.celldef_tab.param_d[key0]['speed']
            elif btokens[1] == 'bias':
                base_val = self.celldef_tab.param_d[key0]['migration_bias']
            elif btokens[1] == 'persistence':
                base_val = self.celldef_tab.param_d[key0]['persistence_time']
        elif btokens[0] == 'cell-cell':
            if btokens[1] == 'adhesion':
                if len(btokens)==2:
                    base_val = self.celldef_tab.param_d[key0]['mechanics_adhesion']
                elif btokens[2] == 'elastic':
                    base_val = self.celldef_tab.param_d[key0]['mechanics_elastic_constant']
            elif btokens[1] == 'repulsion':
                base_val = self.celldef_tab.param_d[key0]['mechanics_repulsion']
        elif btokens[0] == 'cell-BM':
            if btokens[1] == 'adhesion':
                base_val = self.celldef_tab.param_d[key0]['mechanics_BM_adhesion']
            elif btokens[1] == 'repulsion':
                base_val = self.celldef_tab.param_d[key0]['mechanics_BM_repulsion']
        elif behavior == "relative maximum adhesion distance":
            base_val = self.celldef_tab.param_d[key0]['mechanics_relative_equilibrium_distance']
        elif behavior == "cell attachment rate":
            base_val = self.celldef_tab.param_d[key0]['attachment_rate']
        elif behavior == "cell detachment rate":
            base_val = self.celldef_tab.param_d[key0]['detachment_rate']
        elif behavior == "maximum number of cell attachments":
            base_val = self.celldef_tab.param_d[key0]['mechanics_max_num_attachments']

        elif btokens[0] == "phagocytose":
            print("--- handling phagocytose as token 0")
            print(btokens)
            if len(btokens)==3 and btokens[2] == "cell" and btokens[1] in ["apoptotic","necrotic"]:
                if btokens[1] == "apoptotic":
                    print("--- handling phagocytose apoptotic cell")
                    base_val = self.celldef_tab.param_d[key0]['apoptotic_phagocytosis_rate']
                elif btokens[1] == "necrotic":
                    print("--- handling phagocytose necrotic cell")
                    base_val = self.celldef_tab.param_d[key0]['necrotic_phagocytosis_rate']
            elif len(btokens)==4 and btokens[1] == "other" and btokens[2] == "dead" and btokens[3] == "cell":
                print("--- handling phagocytose other dead cell")
                base_val = self.celldef_tab.param_d[key0]['other_dead_phagocytosis_rate']
            else:
                cell_type = behavior[12:]   # length of "phagocytose" 
                print("      cell_type (for phagocytose)=",cell_type)
                base_val = self.celldef_tab.param_d[key0]['live_phagocytosis_rate'][cell_type]
        elif behavior == "attack damage rate":
            base_val = self.celldef_tab.param_d[key0]["attack_damage_rate"]
        elif behavior == "attack duration":
            base_val = self.celldef_tab.param_d[key0]["attack_duration"]
        elif btokens[0] == "attack":
            cell_type = behavior[7:]
            base_val = self.celldef_tab.param_d[key0]['attack_rate'][cell_type]
        elif behavior[0:len("fuse to")] == "fuse to":
            cell_type = behavior[len("fuse to")+1:]
            base_val = self.celldef_tab.param_d[key0]['fusion_rate'][cell_type]
        elif btokens[0] == "immunogenicity":
            base_val = '1.0'
        elif btokens[0] == "is_movable":
            base_val = '1.0'
        elif behavior[0:len("transform to")] == "transform to":
            cell_type = behavior[len("transform to")+1:]
            base_val = self.celldef_tab.param_d[key0]['transformation_rate'][cell_type]
        elif behavior == "damage rate":
            base_val = self.celldef_tab.param_d[key0]["damage_rate"]
        elif behavior == "damage repair rate":
            base_val = self.celldef_tab.param_d[key0]["damage_repair_rate"]
        elif "asymmetric" == behavior.split()[0]:
            cell_type = behavior.split()[-1]
            base_val = self.celldef_tab.param_d[key0]["asymmetric_division_probability"][cell_type]
        elif "custom:" in btokens[0]:
            custom_data_name = btokens[0].split(':')[-1] # return string after colon
            print(custom_data_name, self.celldef_tab.param_d[key0]['custom_data'][custom_data_name])
            base_val = self.celldef_tab.param_d[key0]['custom_data'][custom_data_name][0]

        #---------------------
        # Set the base value 
        self.base_val = base_val

        if not update_widgets:
            return

        self.rule_base_val.setText(base_val)

        # Compute/set the saturation value
        if base_val == '??':
            if "decreases" in self.up_down_combobox.currentText(): saturation_val = 0.0
            else: saturation_val = 1.0
        else:
            # Silliness to avoid numerical noise appearing in computed saturation_val
            base_val_p = np.format_float_positional(float(base_val))
            lbv = len(base_val_p)

            if "decreases" in self.up_down_combobox.currentText(): 
                saturation_val = self.scale_base_for_min * float(base_val_p)
                sat_val_p = np.format_float_positional(saturation_val)
                saturation_val = float(sat_val_p[:lbv+1])
            else: 
                saturation_val = self.scale_base_for_max * float(base_val_p)
                sat_val_p = np.format_float_positional(saturation_val)
                saturation_val = round(float(sat_val_p), lbv)

            # behaviors with max response
            if ( behavior == 'migration bias' and saturation_val > 1 ): saturation_val = 1.0
            if ( behavior == 'is_movable' and saturation_val > 1 ): saturation_val = 1.0

        self.rule_max_val.setText(np.format_float_positional(saturation_val))

        # print(self.celldef_tab.param_d.keys())
        # for ct in self.celldef_tab.param_d.keys():
            # print(self.celldef_tab.param_d[ct])

        # rwh: create this list once.  EDIT: Not sure what I was thinking here...
        # static_names = []
        # static_names = ["cycle entry"]

        # static_names += ["apoptosis", "necrosis", "migration speed", "migration bias", "migration persistence time"]
        # # static_names += ["chemotactic response to " + s]
        # static_names += ["cell-cell adhesion", "cell-cell adhesion elastic constant"]
        # # Each ct = cell type name: ["adhesive affinity to " + ct]
        # static_names += ["relative maximum adhesion distance", "cell-cell repulsion", "cell-BM adhesion", "cell-BM repulsion", "phagocytose dead cell"]
        # static_names += ["is_movable", "cell attachment rate", "cell detachment rate", "maximum number of cell attachments"]

        # static_names = ["exit from cycle phase " + str(idx)], idx=0,1,…,5   (isn’t “smart” to match cell type’s cycle)
        # [verb + ct] where verb=["phagocytose ","attack ","fuse to ","transform to ","immunogenicity to "]

        # if self.signal in self.substrates:
        #     print("--- signal is substrate")
        # if self.behavior in static_names:
        #     print("--- behavior is static: ",self.behavior)

    #-----------------------------------------------------------
    def signal_combobox_changed_cb(self, idx):
        self.signal = self.signal_combobox.currentText()

    #-----------------------------------------------------------
    def response_combobox_changed_cb(self, idx):
        self.update_base_value()

    #-----------------------------------------------------------
    def plot_rules(self):
        dataframe = pd.DataFrame(columns=['cell', 'signal', 'direction', 'behavior', 'saturation', 'half_max', 'hill_power', 'dead', 'base_behavior'])
        dataframe = dataframe.astype({'cell':str, 'signal':str, 'direction':str, 'behavior':str, 'saturation':float, 'half_max':float, 'hill_power':int,  'dead':int,  'base_behavior':float})
        for irow in range(self.max_rule_table_rows):
            cell_irow = self.rules_table.cellWidget(irow, self.rules_celltype_idx).text()
            if (cell_irow == ''): 
                if irow == 0: return # No rules
                else: break # empty line
            signal_irow = self.rules_table.cellWidget(irow, self.rules_signal_idx).text()
            direction_irow = self.rules_table.cellWidget(irow, self.rules_direction_idx).text()
            behavior_irow = self.rules_table.cellWidget(irow, self.rules_response_idx).text()
            saturation_irow = float(self.rules_table.cellWidget(irow, self.rules_maxval_idx).text())
            halfmax_irow = float(self.rules_table.cellWidget(irow, self.rules_halfmax_idx).text())
            hillpower_irow = int(self.rules_table.cellWidget(irow, self.rules_hillpower_idx).text())
            if self.rules_table.cellWidget(irow,self.rules_applydead_idx).isChecked():
                dead_irow = 1
            else:
                dead_irow = 0
            # base value
            self.update_base_value_by_name(behavior_irow, False) # It's not the better approach
            base_behavior_irow = self.base_val

            if base_behavior_irow == '??':  # don't think we ever have this now
                if "decreases" in direction_irow: base_behavior_irow = 1.0
                else: base_behavior_irow = 0.0
            else: 
                base_behavior_irow = float(base_behavior_irow)
            # print({'cell':cell_irow, 'signal':signal_irow, 'direction':direction_irow, 'behavior':behavior_irow, 'saturation':saturation_irow, 
            #                   'half_max':halfmax_irow, 'hill_power':hillpower_irow, 'dead':dead_irow, 'base_behavior':base_behavior_irow})
            dataframe = dataframe._append({'cell':cell_irow, 'signal':signal_irow, 'direction':direction_irow, 'behavior':behavior_irow, 'saturation':saturation_irow, 
                              'half_max':halfmax_irow, 'hill_power':hillpower_irow, 'dead':dead_irow, 'base_behavior':base_behavior_irow}, ignore_index = True)
        # print(dataframe)
        self.RulesWindow = Window_plot_rules(dataframe=dataframe)
        self.RulesWindow.show()

    #-----------------------------------------------------------
    def clear_rules(self):
        # print("\n---------------- clear_rules():")
        for irow in range(self.num_rules):
            for idx in range(self.num_cols):
                self.rules_table.cellWidget(irow, idx).setText('')

            self.rules_table.cellWidget(irow,self.rules_applydead_idx).setChecked(False)

        self.num_rules = 0

    #-----------------------------------------------------------
    def strip_comments(self, csvfile):
        for row in csvfile:
            # raw = row.split('#')[0].strip()
            # if raw: yield raw
            # print(row)
            raw = row.split('/')[0].strip()
            # print("rules_tab.py: strip_comments(): raw=",raw)
            if raw: yield raw

    #-----------------------------------------------------------
    def fill_rules(self, full_rules_fname):
        # print("\n---------------- fill_rules():  full_rules_fname=",full_rules_fname)
        self.clear_rules()

        if os.path.isfile(full_rules_fname):
            try:
                with open(full_rules_fname) as csvfile:
                    csv_reader = csv.reader(self.strip_comments(csvfile))
                    # print("     fill_rules():  past csv.reader")
                    for elm in csv_reader:
                        print("elm #0 = ",elm)
            except:
                print("argh, exception opening or reading")
                msg = "fill_rules(): " + full_rules_fname + " is using v1 syntax. Please upgrade."
                show_studio_warning_window(msg)
                return
                # sys.exit(1)

        # return

        if os.path.isfile(full_rules_fname):
            try:
                with open(full_rules_fname, 'r') as csvfile:
                    csv_reader = csv.reader(self.strip_comments(csvfile))
                    # print("     fill_rules():  past csv.reader")
                    irow = self.num_rules  # append
                    for elm in csv_reader:
                        # csv_reader_obj = csv.reader(f)
                        # irow = 0
                        print("elm= ",elm)
                        print("len(elm)= ",len(elm))
                        if len(elm)+1 == self.max_rule_table_cols:   # v2 [plus base value == 9 colummns, but the rules has 8 columns]

                            cell_type = elm[0]
                            if cell_type not in self.celldef_tab.param_d.keys():
                                print(f'ERROR: {cell_type} is not a valid cell type name')
                                show_studio_warning_window(f'ERROR: {cell_type} is not a valid cell type name')
                                return

                                # self.rules_table.setCellWidget(irow, self.custom_icol_name, w_varname)   # 1st col
                            self.fill_rule_row(irow, elm)

                        elif len(elm) == 9:   # v1
                            print(f'\n\n  WARNING: fill_rules(): {full_rules_fname} is using v1 syntax. Please upgrade\n')
                            msg = "fill_rules(): " + full_rules_fname + " is using v1 syntax. Please upgrade."
                            show_studio_warning_window(msg)
                            return
                        else:
                            print(f'\n\n  WARNING: fill_rules(): {full_rules_fname} has unknown syntax\n')
                            msg = f"fill_rules(): {full_rules_fname} has unknown syntax. len(elm)={len(elm)}"
                            show_studio_warning_window(msg)
                            return

                        if elm[self.rules_response_idx] == "phagocytose dead cell":
                            # apply this rule to all new phagocytosis rates of dead cells
                            self.rules_table.cellWidget(irow, self.rules_response_idx).setText("phagocytose apoptotic cell")

                            irow += 1
                            elm[self.rules_response_idx] = "phagocytose necrotic cell"
                            self.fill_rule_row(irow, elm)

                            irow += 1
                            elm[self.rules_response_idx] = "phagocytose other dead cell"
                            self.fill_rule_row(irow, elm)

                        if elm[self.rules_response_idx] == "damage rate" and hasattr(self.celldef_tab, "pre_v1_14_0_damage_rate") and self.celldef_tab.pre_v1_14_0_damage_rate:
                            self.rules_table.cellWidget(irow, self.rules_response_idx).setText("attack damage rate")
                            msg = "\"damage rate\" no longer refers to the rate of damage dealt, but rather the rate at which damage accumulates in the given cell type."
                            msg += f"\n{elm[0]} had a rule affecting \"damage rate\" that has been replaced with \"attack damage rate\" to fit the new version."
                            msg += "\nThis is because \"damage rate\" was found in the config file where \"attack damage rate\" is now used."
                            self.show_warning(msg)

                        irow += 1

                    self.num_rules = irow
                    print("fill_rules():  num_rules=",self.num_rules)

                    # self.rules_text.setPlainText(text)
            except Exception as e:
            # self.dialog_critical(str(e))
            # print("error opening config/cells_rules.csv")
                print(f'rules_tab.py: Error opening or reading {full_rules_fname}')
                show_studio_warning_window(f'rules_tab.py: Error opening or reading {full_rules_fname}')
                # logging.error(f'rules_tab.py: Error opening or reading {full_rules_fname}')
                # sys.exit(1)
        else:
            if self.rules_enabled_attr:
                print(f'\n\n!!!  WARNING: fill_rules(): {full_rules_fname} is not a valid file !!!\n')
                msg = "fill_rules(): " + full_rules_fname + " not valid"
                show_studio_warning_window(msg)
            # logging.error(f'fill_rules(): {full_rules_fname} is not a valid file')

    # else:  # should empty the Rules tab
    #     self.rules_text.setPlainText("")
    #     self.rules_folder.setText("")
    #     self.rules_file.setText("")
        return

    def fill_rule_row(self, irow, elm):
        for icol in range(self.max_rule_table_cols-2): 
            # print("icol=",icol)
            self.rules_table.cellWidget(irow, icol).setText(elm[icol])
        self.rules_table.cellWidget(irow, 8).setText('??') # load base value

        # if int(elm[7]) == 0:  # hard-code
        if int(elm[self.max_rule_table_cols-2]) == 0:
            print("setting dead checkbox False")
            self.rules_table.cellWidget(irow,self.rules_applydead_idx).setChecked(False)
        else:
            print("setting dead checkbox True")
            self.rules_table.cellWidget(irow,self.rules_applydead_idx).setChecked(True)
    #-----------------------------------------------------------
    def hill(self, x, base_val = 0.0, saturation_val = 1.0, half_max = 0.5 , hill_power = 2 ):
        z = (x / half_max)** hill_power; 
        return base_val + (saturation_val-base_val)*(z/(1.0 + z)); 

    #--------------------------------------------------------
    # plot a new rule being defined
    def plot_new_rule_cb(self):
        try:
            # print("\n------------- plot_new_rule_cb()")
            signal = self.signal_combobox.currentText()
            # print("------------- plot_new_rule_cb(): signal= ",signal)
            if not self.valid_signal(signal):
                show_studio_warning_window( "Invalid signal: " + signal)
                return
            behavior = self.response_combobox.currentText()
            # print("n------------- plot_new_rule_cb(): behavior= ",behavior)
            if not self.valid_behavior(behavior):
                show_studio_warning_window("Invalid behavior: " + behavior)
                return
            # Check if saturation value is compatible with increase/decrease behaviour
            direction = self.up_down_combobox.currentText()
            base_val = self.rule_base_val.text()
            if base_val == '??':
                if "decreases" in self.up_down_combobox.currentText(): base_val = 1.0
                else: base_val = 0.0
            else: base_val = float(base_val)
            saturation_val = float(self.rule_max_val.text())
            # print(base_val,saturation_val, direction)            
            if ( (saturation_val < base_val) and "increases" in self.up_down_combobox.currentText() ): 
                show_studio_warning_window(f"Error: Behavior {behavior} cannot be increased with the given [Saturation value]. [Saturation value] must be greater than [Base value].")
                return
            if ( (saturation_val > base_val) and "decreases" in self.up_down_combobox.currentText() ): 
                show_studio_warning_window(f"Error: Behavior {behavior} cannot be decreased with the given [Saturation value]. [Saturation value] must be lower than [Base value].")
                return  
        except:
            print("\n------------- plot_new_rule_cb(): got exception validating signal, behavior. Return.")
            return

        if not self.rules_plot:
            self.rules_plot = RulesPlotWindow()
        # if not self.reuse_plot_w.isChecked():
            # self.rules_plot = RulesPlotWindow()
        self.rules_plot.ax0.cla()

        # min_val = float(self.rule_min_val.text())
        # if False:  # TODO: fix
        #     # base_val = float(self.rule_base_val.text())
        #     min_val = float(self.rule_base_val.text())
        # else:
        #     # min_val = 0.1
        #     min_val = 0.0
        # max_val = float(self.rule_max_val.text())
        # X = np.linspace(base_val,max_val, 101) 
        # X = np.linspace(min_val,max_val, 101) 

        half_max = float(self.rule_half_max.text())
        hill_power = int(self.rule_hill_power.text())
        base_val = self.rule_base_val.text()
        if base_val == '??':
            if "decreases" in self.up_down_combobox.currentText(): base_val = 1.0
            else: base_val = 0.0
        else: 
            base_val = float(base_val)
        saturation_val = float(self.rule_max_val.text())

        X = np.linspace(0.0, 2.0 * half_max, 101)   # guess max = 2 * half-max

        Y = self.hill(X, base_val=base_val, saturation_val=saturation_val, half_max=half_max, hill_power=hill_power)

        self.rules_plot.ax0.plot(X,Y,'r-')
        self.rules_plot.ax0.grid()
        title = "[New rule] cell type: " + self.celltype_combobox.currentText()
        self.rules_plot.ax0.set_xlabel('signal: ' + self.signal_combobox.currentText())
        self.rules_plot.ax0.set_ylabel('response: ' + self.response_combobox.currentText())
        self.rules_plot.ax0.set_title(title, fontsize=10)
        self.rules_plot.ax0.ticklabel_format(style='sci', axis='y', scilimits=[-2,2], useOffset=False)
        self.rules_plot.canvas.update()
        self.rules_plot.canvas.draw()

        # hack to bring to foreground
        self.rules_plot.hide()
        self.rules_plot.show()

        # self.myscroll.setWidget(self.canvas) # self.config_params = QWidget()
        # self.rules_plot.ax0.plot([0,1,2,3,4], [10,1,20,3,40])
        # self.rules_plot.layout.addWidget(self.canvas)
        return


    #-----------------------------------------------------------
    def valid_signal(self, signal):
        if signal in self.signal_l:
            return True
        else:
            return False
    #-----------------------------------------------------------
    def valid_behavior(self, behavior):
        if behavior in self.response_l:
            return True
        else:
            return False

    #-----------------------------------------------------------
    def check_for_duplicate(self, cell_type_new,signal_new,behavior_new,direction_new):
        print("check_for_duplicate(): num_rules=",self.num_rules)
        # for irow in range(self.max_rule_table_rows):
        for irow in range(self.num_rules):
        # self.rules_celltype_idx = 0
        # self.rules_response_idx = 1
        # self.rules_minval_idx = 2
        # self.rules_baseval_idx = 3
        # self.rules_maxval_idx = 4
        # self.rules_signal_idx = 5
        # self.rules_direction_idx = 6
        # self.rules_halfmax_idx = 7
        # self.rules_hillpower_idx = 8
        # self.rules_applydead_idx = 9
            cell_type = self.rules_table.cellWidget(irow, self.rules_celltype_idx).text()
            # if cell_type == '':
                # break
            if cell_type == cell_type_new:
                signal = self.rules_table.cellWidget(irow, self.rules_signal_idx).text()
                if signal == signal_new:
                    behavior = self.rules_table.cellWidget(irow, self.rules_response_idx).text()
                    if behavior == behavior_new:
                        direction = self.rules_table.cellWidget(irow, self.rules_direction_idx).text()
                        if direction == direction_new:
                            return irow

        return -1

    #-----------------------------------------------------------
    def add_rule_cb(self):
        try:
            signal = self.signal_combobox.currentText()
            if not self.valid_signal(signal):
                show_studio_warning_window( "Invalid signal: " + signal)
                return
            behavior = self.response_combobox.currentText()
            if not self.valid_behavior(behavior):
                show_studio_warning_window("Invalid behavior: " + behavior)
                return
            direction = self.up_down_combobox.currentText()
            # Avoid this in PhysiCell: "Warning! Signal substrate was already part of the rule. Ignoring input."
            dup_rule = self.check_for_duplicate(self.celltype_combobox.currentText(), signal, behavior, direction)
            if dup_rule >= 0:
                show_studio_warning_window(f"Error: You already have this signal-behavior defined for this cell type (row {dup_rule}). Either delete the rule in the table first or edit it manually.")
                return


            base_val = self.rule_base_val.text()
            if base_val == '??':
                if "decreases" in self.up_down_combobox.currentText(): base_val = 1.0
                else: base_val = 0.0
            else: base_val = float(base_val)
            saturation_val = float(self.rule_max_val.text())

            # Check if saturation value is compatible with increase/decrease behaviour
            if ( (saturation_val < base_val) and "increases" in self.up_down_combobox.currentText() ): 
                show_studio_warning_window(f"Error: Behavior {behavior} cannot be increased with the given [Saturation value]. [Saturation value] must be greater than [Base value].")
                return
            if ( (saturation_val > base_val) and "decreases" in self.up_down_combobox.currentText() ): 
                show_studio_warning_window(f"Error: Behavior {behavior} cannot be decreased with the given [Saturation value]. [Saturation value] must be lower than [Base value].")
                return  
        except:
            print("\n------------- add_rule_cb(): got exception validating signal, behavior. Return.")
            return


        # old: create csv string

        # v2 syntax: cell type, signal,increases/decreases, behavior, param value at max response, half max, hill power, applies to dead?

        rule_str = self.celltype_combobox.currentText()
        rule_str += ','
        rule_str += self.signal_combobox.currentText()
        rule_str += ','
        rule_str += self.up_down_combobox.currentText()
        rule_str += ','
        rule_str += self.response_combobox.currentText()
        rule_str += ','
        rule_str += self.rule_max_val.text()
        rule_str += ','
        rule_str += self.rule_half_max.text()
        rule_str += ','
        rule_str += self.rule_hill_power.text()
        rule_str += ','
        if self.dead_cells_checkbox.isChecked():
            rule_str += '1'
        else:
            rule_str += '0'
        print("add_rule_cb():---> ",rule_str)

        irow = self.num_rules

        # v2 synax:
        # cell type, signal, increases/decreases,behavior, param value at max response, half max, hill power, applies to dead?

        try:
            self.rules_table.cellWidget(irow, self.rules_celltype_idx).setText( self.celltype_combobox.currentText() )
        except:
            msg = f'add_rule_cb() Error: irow={irow}, idx={self.rules_celltype_idx}, widget={self.rules_table.cellWidget(irow, self.rules_celltype_idx)}.'
            show_studio_warning_window(msg)
            return 

        self.rules_table.cellWidget(irow, self.rules_signal_idx).setText( self.signal_combobox.currentText() )
        self.rules_table.cellWidget(irow, self.rules_direction_idx).setText( self.up_down_combobox.currentText() )
        self.rules_table.cellWidget(irow, self.rules_response_idx).setText( self.response_combobox.currentText() )  # behavior
        self.rules_table.cellWidget(irow, self.rules_baseval_idx).setText( self.rule_base_val.text() )
        self.rules_table.cellWidget(irow, self.rules_maxval_idx).setText( self.rule_max_val.text() )
        self.rules_table.cellWidget(irow, self.rules_halfmax_idx).setText( self.rule_half_max.text() )
        self.rules_table.cellWidget(irow, self.rules_hillpower_idx).setText( self.rule_hill_power.text() )
        if self.dead_cells_checkbox.isChecked():
            self.rules_table.cellWidget(irow,self.rules_applydead_idx).setChecked(True)
        else:
            self.rules_table.cellWidget(irow,self.rules_applydead_idx).setChecked(False)

        self.num_rules += 1

        self.rules_enabled.setChecked(True)
        return

    #--------------------------------------------------------
    def add_row_rules_table(self, row_num):
        # row_num = self.max_custom_data_rows - 1
        self.rules_table.insertRow(row_num)
        for irow in [row_num]:
            # print("=== add_row_rules_table(): irow=",irow)
            # ------- CellType
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            rx_valid_varname = QtCore.QRegExp("^[a-zA-Z][a-zA-Z0-9_]+$")
            name_validator = QtGui.QRegExpValidator(rx_valid_varname )
            w_me.setValidator(name_validator)

            self.rules_table.setCellWidget(irow, self.rules_celltype_idx, w_me)

            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_celltype_idx

            # ------- Signal
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_signal_idx
            self.rules_table.setCellWidget(irow, self.rules_signal_idx, w_me)
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- Direction
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_direction_idx
            self.rules_table.setCellWidget(irow, self.rules_direction_idx, w_me)
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- response  (behavior)
            # w_varval = MyQLineEdit('0.0')
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            # item = QTableWidgetItem('')
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_response_idx
            # w_me.idx = irow   # rwh: is .idx used?
            # w_me.setValidator(QtGui.QDoubleValidator())
            # self.rules_table.setItem(irow, self.custom_icol_value, item)
            self.rules_table.setCellWidget(irow, self.rules_response_idx, w_me)
            # w_varval.textChanged[str].connect(self.custom_data_value_changed)  # being explicit about passing a string 

            # # ------- Min val
            # w_me = MyQLineEdit()
            # w_me.setValidator(QtGui.QDoubleValidator())
            # w_me.setFrame(False)
            # w_me.vname = w_me  
            # w_me.wrow = irow
            # w_me.wcol = self.rules_minval_idx
            # self.rules_table.setCellWidget(irow, self.rules_minval_idx, w_me)
            # # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- Base val
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            # item = QTableWidgetItem('')
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_baseval_idx
            # w_var_desc.idx = irow
            # w_varval.setValidator(QtGui.QDoubleValidator())
            # self.rules_table.setItem(irow, self.custom_icol_desc, item)
            self.rules_table.setCellWidget(irow, self.rules_baseval_idx, w_me)
            # w_var_desc.textChanged[str].connect(self.custom_data_desc_changed)  # being explicit about passing a string 

            # ------- Max val
            w_me = MyQLineEdit()
            w_me.setValidator(QtGui.QDoubleValidator())
            w_me.setFrame(False)
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_maxval_idx
            self.rules_table.setCellWidget(irow, self.rules_maxval_idx, w_me)
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- Half-max
            w_me = MyQLineEdit()
            w_me.setValidator(QtGui.QDoubleValidator())
            w_me.setFrame(False)
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_halfmax_idx
            self.rules_table.setCellWidget(irow, self.rules_halfmax_idx, w_me)
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- Hill power
            w_me = MyQLineEdit()
            w_me.setValidator(QtGui.QIntValidator())
            w_me.setFrame(False)
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.rules_hillpower_idx
            self.rules_table.setCellWidget(irow, self.rules_hillpower_idx, w_me)
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- Apply to dead
            w_me = MyQCheckBox()
            # w_var_conserved.setFrame(False)
            w_me.vname = "foobar"  
            w_me.wrow = irow
            w_me.wcol = self.rules_applydead_idx
            # w_me.clicked.connect(self.custom_var_conserved_clicked)

            # rwh NB! Leave these lines in (for less confusing clicking/coloring of cell)
            item = QTableWidgetItem('')
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            self.rules_table.setItem(irow, self.rules_applydead_idx, item)

            self.rules_table.setCellWidget(irow, self.rules_applydead_idx, w_me)


    #--------------------------------------------------------
    # Delete an entire rule. 
    def delete_rule_cb(self):
        row = self.rules_table.currentRow()
        # print(f'------------- delete_rule_cb(), row={row}, self.num_rules={self.num_rules}')
        # if row < 0:
        if (row < 0) or (row+1 > self.num_rules) or (self.num_rules <= 0):
            msg = f'Error: Select a row with a rule before deleting.'
            show_studio_warning_window(msg)
            return
        # varname = self.custom_data_table.cellWidget(row,self.custom_icol_name).text()
        # print(" custom var name= ",varname)
        # print(" master_custom_var_d= ",self.master_custom_var_d)

        # if varname in self.master_custom_var_d.keys():
        #     self.master_custom_var_d.pop(varname)
        #     for key in self.master_custom_var_d.keys():
        #         if self.master_custom_var_d[key][0] > row:   # remember: [row, units, description]
        #             self.master_custom_var_d[key][0] -= 1
        #     # remove (pop) this custom var name from ALL cell types
        #     for cdef in self.param_d.keys():
        #         # print(f"   popping {varname} from {cdef}")
        #         self.param_d[cdef]['custom_data'].pop(varname)

        # Since each widget in each row had an associated row #, we need to decrement all those following
        # the row that was just deleted.
        # for irow in range(row, self.max_custom_data_rows):
        for irow in range(row, self.max_rule_table_rows):
            # print("---- decrement wrow in irow=",irow)
            # self.rules_celltype_idx = 0
            # self.rules_response_idx = 1
            try:
                self.rules_table.cellWidget(irow,self.rules_celltype_idx).wrow -= 1  # sufficient to only decr the "name" column
            except:
                msg = f'Warning: could not decrement row {irow} from the Rules table. Select a row before deleting.'
                show_studio_warning_window(msg)
                return

            # print(f"   after removing {varname}, master_custom_var_d= ",self.master_custom_var_d)

        self.rules_table.removeRow(row)

        self.add_row_rules_table(self.max_rule_table_rows - 1)
        # self.enable_all_custom_data()

        self.num_rules -= 1
        # print("---- num_rules=",self.num_rules)

        # print(" 2)master_custom_var_d= ",self.master_custom_var_d)
        # print("------------- LEAVING  delete_custom_data_cb")

    #--------------------------------------------------------
    # plot the selected rule in the table
    def plot_rule_cb(self):

        irow = self.rules_table.currentRow()
        if irow < 0:
            show_studio_warning_window( "Select (click on) a row to plot.")
            return

        try:
            # print("\n------------- plot_rule_cb():  irow=",irow)
            signal = self.rules_table.cellWidget(irow, self.rules_signal_idx).text()
            # print("\n------------- plot_rule_cb():  signal=",signal)
            # print("------------- plot_rule_cb(): signal= ",signal)
            if not self.valid_signal(signal):
                show_studio_warning_window( "Invalid signal: " + signal)
                return
            behavior = self.rules_table.cellWidget(irow, self.rules_response_idx).text()
            # print("\n------------- plot_rule_cb():  behavior=",behavior)
            # print("n------------- plot_rule_cb(): behavior= ",behavior)
            if not self.valid_behavior(behavior):
                show_studio_warning_window("Invalid behavior: " + behavior)
                return
        except:
            print("\n------------- plot_rule_cb(): got exception validating signal, behavior. Return.")
            return


        
        if (irow < 0) or (self.num_rules == 0):
            msg = "You need to select a row in the table"
            show_studio_warning_window(msg)
            return

        # print("------------- plot_rule_cb(), irow=",irow)
        # rule_str = self.rules_table.cellWidget(irow, self.rules_celltype_idx).text()
        # rule_str += self.rules_table.cellWidget(irow, self.rules_response_idx).text()
        # rule_str += self.rules_table.cellWidget(irow, self.rules_minval_idx).text()
        # rule_str += self.rules_table.cellWidget(irow, self.rules_baseval_idx).text()
        # rule_str += self.rules_table.cellWidget(irow, self.rules_maxval_idx).text()
        # rule_str += self.rules_table.cellWidget(irow, self.rules_signal_idx).text()
        # rule_str += self.rules_table.cellWidget(irow, self.rules_direction_idx).text()
        # rule_str += self.rules_table.cellWidget(irow, self.rules_halfmax_idx).text()
        # rule_str += self.rules_table.cellWidget(irow, self.rules_hillpower_idx).text()
        if not self.rules_plot:
            self.rules_plot = RulesPlotWindow()
        self.rules_plot.ax0.cla()
        # min_val = float(self.rules_table.cellWidget(irow, self.rules_minval_idx).text())
        
        half_max = float(self.rules_table.cellWidget(irow, self.rules_halfmax_idx).text())

        # NO! Use the actual base value in the appropriate subtab for behavior
        # base_val = self.rules_table.cellWidget(irow, self.rules_baseval_idx).text()
        hill_power = int(self.rules_table.cellWidget(irow, self.rules_hillpower_idx).text())

        behavior = self.rules_table.cellWidget(irow, self.rules_response_idx).text()
        self.update_base_value_by_name(behavior, False)
        base_val = self.base_val

        if base_val == '??':  # don't think we ever have this now
            if "decreases" in self.rules_table.cellWidget(irow, self.rules_direction_idx).text(): base_val = 1.0
            else: base_val = 0.0
        else: 
            base_val = float(base_val)
        saturation_val = float(self.rules_table.cellWidget(irow, self.rules_maxval_idx).text())

        # rwh: reading the user's mind
        direction_str = self.rules_table.cellWidget(irow, self.rules_direction_idx).text()
        if (saturation_val > base_val) and direction_str == "decreases":
            msg = f'saturation ({saturation_val}) is > base {base_val}, so we will change the Direction to "increases"'
            show_studio_warning_window(msg)
            self.rules_table.cellWidget(irow, self.rules_direction_idx).setText( "increases" )
        elif (saturation_val < base_val) and direction_str == "increases": 
            msg = f'saturation ({saturation_val}) is < base {base_val}, so we will change the Direction to "decreases"'
            show_studio_warning_window(msg)
            self.rules_table.cellWidget(irow, self.rules_direction_idx).setText( "decreases" )

        
        X = np.linspace(0.0, 2.0 * half_max, 101)   # guess max = 2 * half-max

        Y = self.hill(X, base_val=base_val, saturation_val=saturation_val, half_max=half_max, hill_power=hill_power)
        # Y = self.hill(X, base_val=self.base_val, saturation_val=saturation_val, half_max=half_max, hill_power=hill_power)
    
        self.rules_plot.ax0.plot(X,Y,'r-')
        self.rules_plot.ax0.grid()
        title = "Rule " + str(irow+1) + ": cell type: " + self.rules_table.cellWidget(irow, self.rules_celltype_idx).text()
        self.rules_plot.ax0.set_xlabel('signal: ' + self.rules_table.cellWidget(irow, self.rules_signal_idx).text())
        self.rules_plot.ax0.set_ylabel('response: ' + self.rules_table.cellWidget(irow, self.rules_response_idx).text())
        self.rules_plot.ax0.set_title(title, fontsize=10)
        self.rules_plot.ax0.ticklabel_format(style='sci', axis='y', scilimits=[-2,2], useOffset=False)
        self.rules_plot.canvas.update()
        self.rules_plot.canvas.draw()

        # self.rules_plot.show()

        # hack to bring to foreground
        self.rules_plot.hide()
        self.rules_plot.show()

        return

    #-----------------------------------------------------------
    def import_rules_cb(self):
        # filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')
        filePath = QFileDialog.getOpenFileName(self,'',".")
        full_path_rules_name = filePath[0]
        # logging.debug(f'\nimport_rules_cb():  full_path_rules_name ={full_path_rules_name}')
        print(f'\nimport_rules_cb():  full_path_rules_name ={full_path_rules_name}')
        basename = os.path.basename(full_path_rules_name)
        print(f'import_rules_cb():  basename ={basename}')
        dirname = os.path.dirname(full_path_rules_name)
        print(f'import_rules_cb():  dirname ={dirname}')
        # if (len(full_path_rules_name) > 0) and Path(full_path_rules_name):
        if (len(full_path_rules_name) > 0) and Path(full_path_rules_name).is_file():
            print("import_rules_cb():  filePath is valid")
            # logging.debug(f'     filePath is valid')
            print("len(full_path_rules_name) = ", len(full_path_rules_name) )
            # logging.debug(f'     len(full_path_rules_name) = {len(full_path_rules_name)}' )
            self.rules_folder.setText(dirname)
            self.rules_file.setText(basename)
            # fname = os.path.basename(full_path_rules_name)
            # self.current_xml_file = full_path_rules_name

            # self.add_new_model(self.current_xml_file, True)
            # self.config_file = self.current_xml_file
            # if self.studio_flag:
            #     self.run_tab.config_file = self.current_xml_file
            #     self.run_tab.config_xml_name.setText(self.current_xml_file)
            # self.show_sample_model()
            # self.fill_gui()

            # arg! how does it not catch this as an invalid file above??
            # in fill_rules():  full_rules_fname= /Users/heiland/git/data/tumor_rules.csv
            print(f'import_rules_cb():  (guess) calling fill_rules() with ={full_path_rules_name}')
            # if not self.nanohub_flag:
            #     full_path_rules_name = os.path.abspath(os.path.join(self.homedir,'tmpdir',folder_name, file_name))
            #     print(f'import_rules_cb():  NOW calling fill_rules() with ={full_path_rules_name}')

            self.fill_rules(full_path_rules_name)

        else:
            print("import_rules_cb():  full_path_model_name is NOT valid")

    #-----------------------------------------------------------
    # load/append more
    def load_rules_cb(self):
        try:
            cwd = os.getcwd()
            print("load_rules_cb():  os.getcwd()=",cwd)
            # full_rules_fname = os.path.join(cwd, folder_name, file_name)
            full_path_rules_name = os.path.join(cwd, self.rules_folder.text(), self.rules_file.text())
            print(f'\nload_rules_cb():  full_path_rules_name ={full_path_rules_name}')
        # if (len(full_path_rules_name) > 0) and Path(full_path_rules_name):
            if (len(full_path_rules_name) > 0) and Path(full_path_rules_name).is_file():
                print(f'load_rules_cb():  calling fill_rules() with ={full_path_rules_name}')

            self.fill_rules(full_path_rules_name)
        except:
            print("load_rules_cb():  full_path_model_name is NOT valid")

    #-----------------------------------------------------------
    def validate_rules_cb(self):
        return

    #-----------------------------------------------------------
    def save_rules_cb(self):
        folder_name = self.rules_folder.text()
        file_name = self.rules_file.text()
        print("rules_tab: save_rules_cb(): folder, file=",folder_name, file_name)
        # full_rules_fname = os.path.join(folder_name, file_name)
        full_rules_fname = os.path.abspath(os.path.join(".",folder_name, file_name))
        # if os.path.isfile(full_rules_fname):
        try:
            with open(full_rules_fname, 'w') as f:
                # rules_text = self.rules_text.toPlainText()
                # f.write(rules_text )
                # print("rules_tab.py: save_rules_cb(): self.num_rules= ",self.num_rules)
                # for irow in range(self.num_rules):
                for irow in range(self.max_rule_table_rows):
        # self.rules_celltype_idx = 0
        # self.rules_response_idx = 1
        # self.rules_minval_idx = 2
        # self.rules_baseval_idx = 3
        # self.rules_maxval_idx = 4
        # self.rules_signal_idx = 5
        # self.rules_direction_idx = 6
        # self.rules_halfmax_idx = 7
        # self.rules_hillpower_idx = 8
        # self.rules_applydead_idx = 9
                    rule_str = self.rules_table.cellWidget(irow, self.rules_celltype_idx).text()
                    print("   irow=",irow, ", col 1 text=",rule_str)
                    if rule_str == '':
                        break
                    rule_str += ','
                    rule_str += self.rules_table.cellWidget(irow, self.rules_signal_idx).text()
                    rule_str += ','
                    rule_str += self.rules_table.cellWidget(irow, self.rules_direction_idx).text()
                    rule_str += ','
                    rule_str += self.rules_table.cellWidget(irow, self.rules_response_idx).text()
                    rule_str += ','
                    # rule_str += self.rules_table.cellWidget(irow, self.rules_minval_idx).text()
                    # rule_str += ','
                    # rule_str += self.rules_table.cellWidget(irow, self.rules_baseval_idx).text()
                    # rule_str += ','
                    rule_str += self.rules_table.cellWidget(irow, self.rules_maxval_idx).text()
                    rule_str += ','
                    rule_str += self.rules_table.cellWidget(irow, self.rules_halfmax_idx).text()
                    rule_str += ','
                    rule_str += self.rules_table.cellWidget(irow, self.rules_hillpower_idx).text()
                    rule_str += ','
                    if self.rules_table.cellWidget(irow,self.rules_applydead_idx).isChecked():
                        rule_str += '1'
                    else:
                        rule_str += '0'

                    # rule_str = self.celltype_combobox.currentText()
                    # rule_str += ','
                    # rule_str += self.response_combobox.currentText()
                    # rule_str += ','
                    # rule_str += self.rule_min_val.text()
                    # rule_str += ','
                    # rule_str += self.rule_base_val.text()
                    # rule_str += ','
                    # rule_str += self.rule_max_val.text()
                    # rule_str += ','
                    # rule_str += self.signal_combobox.currentText()
                    # rule_str += ','
                    # rule_str += self.up_down_combobox.currentText()
                    # rule_str += ','
                    # rule_str += self.rule_half_max.text()
                    # rule_str += ','
                    # rule_str += self.rule_hill_power.text()
                    # rule_str += ','
                    # if self.dead_cells_checkbox.isChecked():
                    #     rule_str += '1'
                    # else:
                    #     rule_str += '0'
                    # print(rule_str)
                    f.write(rule_str + '\n')
                f.close()
                print(f'rules_tab.py: Wrote rules to {full_rules_fname}')

        except Exception as e:
        # self.dialog_critical(str(e))
        # print("error opening config/cells_rules.csv")
            print(f'rules_tab.py: Error writing {full_rules_fname}')
            # logging.error(f'rules_tab.py: Error writing {full_rules_fname}')
                # sys.exit(1)
        # else:
            # print(f'\n\n!!!  WARNING: fill_rules(): {full_rules_fname} is not a valid file !!!\n')
            # logging.error(f'fill_rules(): {full_rules_fname} is not a valid file')

    # else:  # should empty the Rules tab
    #     self.rules_text.setPlainText("")
    #     self.rules_folder.setText("")
    #     self.rules_file.setText("")
        return

    #-----------------------------------------------------------
    def clear_comboboxes(self):
        # self.substrates.clear()
        self.signal_l.clear()
        self.response_l.clear()

        self.celltype_combobox.clear()
        self.signal_combobox.clear()
        self.response_combobox.clear()

    #-----------------------------------------------------------
    def fill_signals_widget(self):
        # print("\n rules_tab:-------------------fill_signals_widget()")
        self.signal_l.clear()
        self.signal_combobox.clear()

        self.signal_l = self.create_signal_list()

        self.signal_combobox.addItems(self.signal_l)

        self.signal_combobox.setCurrentIndex(0)

    def create_signal_list(self):
        signal_l = []
        for s in self.substrates:
            signal_l.append(s)
        for s in self.substrates:
            signal_l.append("intracellular " + s)
        for s in self.substrates:
            signal_l.append(s + " gradient")

        signal_l += ["pressure","volume"]

        # print("       self.celldef_tab.param_d.keys()= ",self.celldef_tab.param_d.keys())
        for ct in self.celldef_tab.param_d.keys():
            signal_l.append("contact with " + ct)

        # special
        signal_l += ["contact with live cell","contact with dead cell","contact with BM","damage","dead","total attack time","damage delivered","time","apoptotic","necrotic"]

        # append all custom data (but *only* for a single cell_def!)
        cell_def0 = list(self.celldef_tab.param_d.keys())[0]
        for custom_var in list(self.celldef_tab.param_d[cell_def0]['custom_data'].keys()):
            signal_name = "custom:" + custom_var
            signal_l.append(signal_name)

        return signal_l

    #-----------------------------------------------------------
    def fill_responses_widget(self):
        self.response_l.clear()
        self.response_combobox.clear()

        self.response_l = self.create_response_list()
        #---- finally, use the self.response_l list to create the combobox entries
        #     self.response_model.setItem(idx, 0, item)
        self.response_combobox.addItems(self.response_l)

        self.response_combobox.setCurrentIndex(0)
        self.celldef_tab.par_dist_fill_responses_widget(self.response_l + ["Volume"]) # everything else is lowercase, but this can stand out because it's not a true behavior, but rather the unique non-behavior that can be set by ICs

    def create_response_list(self):
        # TODO: figure out how best to organize these responses
        response_l = []
        for s in self.substrates:
            response_l.append(s + " secretion")
        for s in self.substrates:
            response_l.append(s + " secretion target")
        for s in self.substrates:
            response_l.append(s + " uptake")
        for s in self.substrates:
            response_l.append(s + " export")
        response_l.append("cycle entry")
        response_l.append("attack damage rate")
        response_l.append("attack duration")
        response_l.append("damage rate")
        response_l.append("damage repair rate")
        for idx in range(6):  # TODO: hardwired
            response_l.append("exit from cycle phase " + str(idx))

        response_l += ["apoptosis","necrosis","migration speed","migration bias","migration persistence time"]

        for s in self.substrates:
            response_l.append("chemotactic response to " + s)

        response_l += ["cell-cell adhesion", "cell-cell adhesion elastic constant"]

        for ct in self.celldef_tab.param_d.keys():
            response_l.append("adhesive affinity to " + ct)

        # special
        response_l += ["relative maximum adhesion distance","cell-cell repulsion","cell-BM adhesion","cell-BM repulsion","phagocytose apoptotic cell","phagocytose necrotic cell","phagocytose other dead cell"]

        for verb in ["phagocytose ","attack ","fuse to ","transform to ","immunogenicity to ","asymmetric division to "]:  # verb
            for ct in self.celldef_tab.param_d.keys():
                response_l.append(verb + ct)

        # more special
        response_l += ["is_movable","cell attachment rate","cell detachment rate","maximum number of cell attachments"]

        # append all custom data (but *only* for a single cell_def!)
        cell_def0 = list(self.celldef_tab.param_d.keys())[0]
        for custom_var in self.celldef_tab.param_d[cell_def0]['custom_data'].keys():
            response_name = "custom:" + custom_var
            response_l.append(response_name)
        return response_l

    #-----------------------------------------------------------
    def fill_gui(self):
        # logging.debug(f'\n\n------------\nrules_tab.py: fill_gui():')
        print(f'\n\n------------\nrules_tab.py: fill_gui():')

        self.clear_comboboxes()

        # print("rules_tab.py: fill_gui(): self.celldef_tab.param_d.keys()= ",self.celldef_tab.param_d.keys())
        for key in self.celldef_tab.param_d.keys():
            # logging.debug(f'cell type ---> {key}')
            print(f'cell type ---> {key}')
            self.celltype_combobox.addItem(key)
            # self.signal_combobox.addItem(key)
            # break
        # print("\n\n------------\nrules_tab.py: fill_gui(): self.celldef_tab.param_d = ",self.cell_def_tab.param_d)

        # print("rules_tab.py: fill_gui(): self.microenv_tab.param_d.keys()= ",self.microenv_tab.param_d.keys())
        self.substrates.clear()
        for key in self.microenv_tab.param_d.keys():
            # logging.debug(f'substrate type ---> {key}')
            print(f'substrate type ---> {key}')
            if key == 'gradients' or key == 'track_in_agents':
                pass
            else:
                self.substrates.append(key)

        #----- (rwh TODO: add dict for default params for each entry)
        self.fill_signals_widget()

        self.fill_responses_widget()

        #----------------------------------
        uep = self.xml_root.find(".//cell_rules//rulesets//ruleset")
        print(f'rules_tab.py: fill_gui(): <cell_rules> =  {uep}')
        if uep:
            folder_name = uep.find(".//folder").text
            print(f'rules_tab.py: fill_gui():  folder_name =  {folder_name}')
            self.rules_folder.setText(folder_name)
            file_name = uep.find(".//filename").text
            print(f'rules_tab.py: fill_gui():  file_name =  {file_name}')
            if folder_name == None or file_name == None:
                msg = "rules_tab.py: "
                if folder_name == None:
                    msg += "rules folder "
                if folder_name == None:
                    msg += " rules file "
                msg += " missing from .xml"
                # show_studio_warning_window(msg)

                self.rules_folder.setText("")
                self.rules_file.setText("")
                self.rules_enabled.setChecked(False)
                return

            self.rules_file.setText(file_name)
            cwd = os.getcwd()
            print("fill_rules():  os.getcwd()=",cwd)
            full_rules_fname = os.path.join(cwd, folder_name, file_name)

            self.rules_enabled_attr = False
            if uep.attrib['enabled'].lower() == 'true':
                self.rules_enabled.setChecked(True)
                self.rules_enabled_attr = True
            else:
                self.rules_enabled.setChecked(False)

            print(f'rules_tab.py: fill_gui()----- calling fill_rules() with  full_rules_fname=  {full_rules_fname}')
            # if not self.nanohub_flag:
            #     full_path_rules_name = os.path.abspath(os.path.join(self.homedir,'tmpdir',folder_name, file_name))
            #     print(f'import_rules_cb():  fill_gui()-- NOW calling fill_rules() with ={full_path_rules_name}')
            #     self.fill_rules(full_path_rules_name)
            # else:
            #     self.fill_rules(full_rules_fname)

            if self.nanohub_flag:  # sigh
                # full_rules_fname = os.path.join(self.absolute_data_dir, file_name)
                full_rules_fname = os.path.join('.', file_name)
                self.fill_rules(full_rules_fname)
            else:
                self.fill_rules(full_rules_fname)

        # if no rules are defined in the .xml, set default folder, file and enable them in the tab
        else:  # should empty the Rules tab
            # self.rules_text.setPlainText("")
            self.rules_folder.setText("config")
            self.rules_file.setText("rules.csv")
            # self.rules_enabled.setChecked(True)   # Sep 2024: comment out; error w/ physiboss model with no rules block provided in xml 

            self.clear_rules()
        return

    #-----------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    # Also, save the Rules into their specified .csv file.
    def fill_xml(self):

        self.save_rules_cb()   # NB! update/save the rules .csv file also

        indent8 = '\n        '
        indent10 = '\n          '

        # ---- v3
        uep = self.xml_root.find(".")
        if not self.xml_root.find(".//cell_rules"):
            enabled_flag = "false"
            if self.rules_enabled.isChecked():
                enabled_flag = "true"

            elm = ET.Element("cell_rules")
            elm.tail = '\n' + indent8
            elm.text = indent8

            rulesets = ET.SubElement(elm,"rulesets") 
            rulesets.tail = '\n' + indent8
            rulesets.text = indent8

            ruleset = ET.SubElement(rulesets,"ruleset", 
                        {"protocol":"CBHG", "version":"3.0", "format":"csv", "enabled":enabled_flag })
            ruleset.tail = '\n' + indent8
            ruleset.text = indent8

            rfolder = ET.SubElement(ruleset, 'folder')
            rfolder.text = self.rules_folder.text()
            print(f"-------- rules_tab:  fill_xml(): rules folder={rfolder.text}")
            rfolder.tail = indent8

            rfile = ET.SubElement(ruleset, 'filename')
            rfile.text = self.rules_file.text()
            print(f"-------- rules_tab:  fill_xml(): rules file={rfile.text}")
            rfile.tail = indent8

            uep.insert(0,elm)

        else:
            self.xml_root.find(".//cell_rules//rulesets//ruleset//folder").text = self.rules_folder.text()
            self.xml_root.find(".//cell_rules//rulesets//ruleset//filename").text = self.rules_file.text()

            if self.rules_enabled.isChecked():
                self.xml_root.find(".//cell_rules//rulesets//ruleset").attrib['enabled'] = 'true'
            else:
                self.xml_root.find(".//cell_rules//rulesets//ruleset").attrib['enabled'] = 'false'
                
            # force version update for users
            self.xml_root.find(".//cell_rules//rulesets//ruleset").attrib['version'] = '3.0'
        return
    
    #-------------------------
    def find_and_replace_rules_table(self, old_name, new_name, possible_superstrings):
        reserved_words = create_reserved_words()
        possible_superstrings += reserved_words
        super_strings = [x for x in possible_superstrings if (old_name in x) and (old_name != x)] # the other elements in the list that contain the old_name
        print(f"\n      Finding instances of {old_name} and replacing with {new_name}.")
        print(f"      Looking out for the following super strings: {super_strings}")
        for irow in range(self.num_rules):
            self.find_and_replace_rule_row(old_name, new_name, irow, super_strings)
        return
    
    def find_and_replace_rule_row(self, old_name, new_name, irow, super_strings):
        column_indices = [self.rules_celltype_idx, self.rules_signal_idx, self.rules_response_idx]
        for icol in column_indices:
            old_text = self.rules_table.cellWidget(irow, icol).text()
            new_text = find_and_replace_rule_cell(old_name, new_name, super_strings, old_text)
            self.rules_table.cellWidget(irow, icol).setText(new_text)
        return
    
def find_and_replace_rule_cell(old_name, new_name, super_strings, s):
    if s==old_name:
        return new_name
    
    # there is a possibility that the old_name is a substring of some other element in the list (e.g. "mac" is being changed to "TAM" and "macrophage" is also in the list)
    # in this case, we need to be careful to only replace the old_name and not the other element containing it (e.g. "macrophage" should not be changed to "TAMrophage")
    # so first check if any of the super strings are in the given string
    for super_string in super_strings:
        if find_isolated_string(s, super_string) != -1:
            print(f"      skipping {s} because it contains {super_string}")
            return s
    
    ind = find_isolated_string(s, old_name)
    if ind != -1:
        print(f"      replacing {old_name} with {new_name} in {s}")
        return s[0:ind] + new_name + s[(ind+len(old_name)):]
    return s

def find_isolated_string(s, name, start=0):
    # now make sure that neither side of the old_name is a non-space character. this will protect against simple substrate names like "a" from changing the "a" in "intracellular", for example
    while start < len(s):
        ind = s.find(name, start)
        start = ind+1 # update for next time through the loop (if there is a next time)
        if ind == -1:
            return -1 # got to the end of s without finding a good match, no replacements needed

        if ind>0 and not (s[ind-1].isspace()):
            continue # previous character was not a space, so this was not a good match
        
        if ind < len(s)-len(name) and not (s[ind+len(name)].isspace()):
            continue # next character was not a space, so this was not a good match

        # if we get here, then we've found a good match starting at ind
        return ind

def create_reserved_words():
    reserved_words_signals = ["contact with", "contact with live cell","contact with dead cell","contact with BM", "total attack time", "damage delivered"]
    reserved_words_behaviors = ["secretion target","cycle entry","attack damage rate","attack duration","damage rate","damage repair rate","migration speed","migration bias","migration persistence time","chemotactic response to","cell-cell adhesion","cell-cell adhesion elastic constant","adhesive affinity to","relative maximum adhesion distance","cell-cell repulsion","cell-BM adhesion","cell-BM repulsion","phagocytose apoptotic cell","phagocytose necrotic cell","phagocytose other dead cell","fuse to","transform to","asymmetric division to","immunogenicity to","cell attachment rate","cell detachment rate","maximum number of cell attachments"]
    reserved_words_cycle_phases = [f"exit from cycle phase {i}" for i in range(6)]
    reserved_words = reserved_words_signals + reserved_words_behaviors + reserved_words_cycle_phases
    return reserved_words