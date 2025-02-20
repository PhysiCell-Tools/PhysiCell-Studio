"""
sbml_intra.py - parameters for the Cell Types -> Intracellular -> ODEs tab

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
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QLineEdit, QGroupBox,QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,QGridLayout,QPushButton,QFileDialog,QTableWidget,QTableWidgetItem,QHeaderView
from PyQt5.QtWidgets import QMessageBox, QCompleter, QSizePolicy
from PyQt5.QtCore import QSortFilterProxyModel, Qt, QRect
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtGui import QPixmap
from PyQt5 import QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

# from multivariate_rules import Window_plot_rules
from studio_classes import ExtendedCombo
from studio_functions import show_studio_warning_window
from xml_constants import *

# Overloading the QLineEdit widget to let us map it to its variable name. Ugh.
class MyQLineEdit(QLineEdit):
    vname = None
    wrow = 0
    wcol = 0
    prev = None

#----------------------------------------------------------------------
class SBML_ODEs(QWidget):
    def __init__(self, nanohub_flag, microenv_tab, celldef_tab):
        super().__init__()

        print("\n---------- creating SBML_ODEs(QWidget)")
        self.nanohub_flag = nanohub_flag
        self.homedir = '.'  # reset in studio.py
        self.absolute_data_dir = None   # updated in studio.py

        self.microenv_tab = microenv_tab
        self.celldef_tab = celldef_tab

        self.celltype_name = None

        self.sbml_filename = ""
        # self.intracellular_dt = ""

        self.signal = None
        self.behavior = None
        self.scale_base_for_max = 10.0
        self.scale_base_for_min = 0.1

        self.max_map_table_rows = 50

        self.update_maps_for_custom_data = True

        self.max_map_table_cols = 3

        # table columns' indices
        icol = 0
        self.maps_substrate_idx = icol
        icol += 1
        self.maps_phenotype_idx = icol
        icol += 1
        self.maps_custom_data_idx = icol
        icol += 1
        self.maps_species_idx = icol
        icol += 1

        self.num_cols = icol
        print("self.num_cols = ",self.num_cols)

        self.num_maps = 0

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

        self.sbml_params = QWidget()

        # self.sbml_tab_layout = QGridLayout()
        self.sbml_tab_layout = QVBoxLayout()

        self.substrates = []
        self.signal_l = []
        self.response_l = []

        idx_row = 0
        hlayout = QHBoxLayout()

        self.ode_sbml_frame = QFrame()

        #----------------------------
        # insanity.
        # myhints = QLabel()
        # pixmap = QPixmap("images/sbml_phenotype_hints.png")
        # pixmap = QPixmap("./images/foo.jpg")
        # pixmap = QPixmap(":/images/foo.jpg")
        # myhints.setPixmap(pixmap)
        # myhints.resize(pixmap.width(), pixmap.height())
        # self.sbml_tab_layout.addWidget(myhints)

        s = f"The syntax in the table below applies to PhysiCell >= 1.13.0.\n \
For each row, you are allowed only one entry in columns 1-3. The other two columns' entries\n \
must be empty. The 1st, 3rd, and 4th columns are straightforward:\n \
  col 1) the 'substrate' will be one in your Microenvironment\n \
  col 3) the 'custom_data' will be one in your Custom Data table\n \
  col 4) the 'SBML species' will be one in your SBML file.\n \n \
The entry in column 2), 'phenotype', needs more explanation:\n\n"

        # insanity
        # h_col1 = ['Phase transition rate','Death rate']
        # h_col2 = ['c','d']
        # h_col3 = ['ctr_*_*','da,dn']
        # h_col4 = ['ctr_0_1','da,dn']
        # s += f"{'PhysiCell Phenotype Param | ' : <30}{'1st char | ' : <12}{'token | ' : ^8}{'example' : >9}" + '\n'
        # for i in range(0, 2): 
        #     s += f"{h_col1[i] : <30}{h_col2[i] : <12}{h_col3[i] : ^8}{h_col4[i] : >9}" + "\n"

        s += f"PhysiCell Phenotype Param | 1st char| token   | example\n \
--------------------------------------------------------\n \
    Phase Transition Rate          c          ctr_*_*    ctr_0_1\n \
    Death Rate                            d           da,dn      da,dn\n \
    Persistence Time                 m          mpt         mpt\n \
    Migration Speed                  m          mms        mms\n \
    Migration Bias                     m           mmb        mmb\n \
    Uptake Rate                         s           sur_*         sur_oxygen\n \
    Secretion Rate                     s           ssr_*         ssr_glucose\n \
    Saturation density               s           ssd_*         ssd_oxygen\n \
    Export rate                           s           ser_*         ser_lactate\n \
    Target solid cytoplasmic     v          vtsc           vtsc\n \
    Target solid nuclear             v          vtsn           vtsn\n \
    Target fluid fraction             v          vff             vff\n \
(SCROLL DOWN to see the table of mappings)"

# PhysiCell Phenotype Param | 1st char | token   | example\n \
# --------------------------------------------------------\n \
# Phase Transition Rate          c       ctr_*_*   ctr_0_1\n \
# Death Rate                     d       da,dn     da,dn\n \
# Persistence Time               m       mpt       mpt\n \
# Migration Speed                m       mms       mms\n \
# Migration Bias                 m       mmb       mmb\n \
# Uptake Rate                    s       sur_*     sur_oxygen\n \
# Secretion Rate                 s       ssr_*     ssr_glucose\n \
# Saturation density             s       ssd_*     ssd_oxygen\n \
# Export rate                    s       ser_*     ser_lactate\n \
# Target solid cytoplasmic       v       vtsc      vtsc\n \
# Target solid nuclear           v       vtsn      vtsn\n \
# Target fluid fraction          v       vff       vff\n"

        # explain_syntax = QLabel("The syntax in the table below applies to PhysiCell 1.14.0. ")
        explain_syntax = QLabel(s)
        self.sbml_tab_layout.addWidget(explain_syntax)


        ly = QVBoxLayout()
        # self.physiboss_boolean_frame.setLayout(ly)

        hbox = QHBoxLayout()
        label = QLabel("SBML file")
        hbox.addWidget(label)

        self.sbml_file = QLineEdit()
        # self.sbml_file.setFixedWidth(250)
        self.sbml_file.setMinimumWidth(250)
        self.sbml_file.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # ??
        self.sbml_file.textChanged.connect(self.sbml_filename_changed)
        hbox.addWidget(self.sbml_file)

        sbml_button = QPushButton("Choose SBML file")
        sbml_button.setStyleSheet("background-color: lightgreen;")
        sbml_button.setFixedWidth(120)
        sbml_button.clicked.connect(self.choose_sbml_file)

        hbox.addWidget(sbml_button)
        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        ly.addLayout(hbox)

        hbox = QHBoxLayout()
        label = QLabel("Intracellular dt")
        hbox.addWidget(label)

        self.dt_w = QLineEdit()
        self.dt_w.setFixedWidth(70)
        self.dt_w.setValidator(QtGui.QDoubleValidator(bottom=1.e-6))
        hbox.addWidget(self.dt_w)
        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        ly.addLayout(hbox)

        self.sbml_tab_layout.addLayout(ly)

        #------------------------------
        # hbox = QHBoxLayout()
        # ode_label = QLabel("ODEs via SBML in preparation...")
        # ode_label.setFont(QFont('Arial', 30))
        # hbox.addWidget(ode_label)
        # vbox.addLayout(hbox)
        # self.sbml_tab_layout.addWidget(ode_label) 

        self.sbml_tab_layout.addWidget(self.ode_sbml_frame)
        # self.sbml_tab_layout.addStretch()


        #==================================================================
        # self.maps_params.setLayout(self.maps_tab_layout)

        # self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        # self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        # self.scroll.setWidgetResizable(True)

        # self.scroll.setWidget(self.maps_params) 

        # self.layout = QVBoxLayout(self)  # leave this!
        # self.layout.addWidget(self.scroll)

        #---------------------------------------------------------
        print("\n---------- calling create_mapping_table")
        mapping_table_vbox = self.create_mapping_table()
        print("\n---------- back from create_mapping_table")
        self.sbml_tab_layout.addLayout(mapping_table_vbox) 
        # print("\n---------- at 1")
        # self.ode_sbml_frame.setLayout(self.sbml_tab_layout)
        # print("\n---------- at 2")
        #---------
        # self.insert_hacky_blank_lines(self.sbml_tab_layout)


        #==================================================================
        self.sbml_params.setLayout(self.sbml_tab_layout)
        # print("\n---------- at 3")

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)
        # print("\n---------- at 4")

        self.scroll.setWidget(self.sbml_params) 
        # print("\n---------- at 5")

        self.layout = QVBoxLayout(self)  # leave this!
        print("\n---------- at 6")
        self.layout.addWidget(self.scroll)
        print("\n---------- end of SBML_ODEs")


    #--------------------------------------------------------
    def sbml_filename_changed(self, text):
        print("sbml_filename_changed: text= ",text)
        self.sbml_filename = text
        # print(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"])
        # self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["sbml_filename"] = text
        # print(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"])
        # if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
        #     self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]['sbml_filename'] = text
        #     print("sbml_filename_changed: self.celldef_tab.current_cell_def= ",self.celldef_tab.current_cell_def)
            # self.physiboss_update_list_nodes()

    #--------------------------------------------------------
    def create_mapping_table(self):
        maps_table_w = QWidget()
        maps_table_scroll = QScrollArea()
        vlayout = QVBoxLayout()
        self.maps_table = QTableWidget()
        # self.maps_table.cellClicked.connect(self.maps_cell_was_clicked)

        self.maps_table.setColumnCount(4)
        self.maps_table.setRowCount(self.max_map_table_rows)
        self.maps_table.setMinimumHeight(400)
        # self.maps_table.setColumnHidden(8, True) # hidden column base value

        header = self.maps_table.horizontalHeader()       
        # header.setSectionResizeMode(0, QHeaderView.Stretch)
        # header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # arg, don't work as expected
        # header.setSectionResizeMode(9, QHeaderView.ResizeToContents)

        # self.maps_table.setHorizontalHeaderLabels(['CellType','Response','Min','Base','Max', 'Signal','Direction','Half-max','Hill power','Apply to dead'])
        self.maps_table.setHorizontalHeaderLabels(['substrate','phenotype','custom_data','SBML species'])

        # Don't like the behavior these offer, e.g., locks down width of 0th column :/
        # header = self.maps_table.horizontalHeader()       
        # header.setSectionResizeMode(0, QHeaderView.Stretch)
        # header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            
        for irow in range(self.max_map_table_rows):
            # print("------------ rules table row # ",irow)

            # ------- substrate
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            rx_valid_varname = QtCore.QRegExp("^[a-zA-Z][a-zA-Z0-9_]+$")
            name_validator = QtGui.QRegExpValidator(rx_valid_varname )
            w_me.setValidator(name_validator)

            self.maps_table.setCellWidget(irow, self.maps_substrate_idx, w_me)

            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.maps_substrate_idx

            # ------- phenotype
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.maps_phenotype_idx
            self.maps_table.setCellWidget(irow, self.maps_phenotype_idx, w_me)
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- custom_data
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.maps_custom_data_idx
            self.maps_table.setCellWidget(irow, self.maps_custom_data_idx, w_me)
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

            # ------- species
            w_me = MyQLineEdit()
            w_me.setFrame(False)
            w_me.vname = w_me  
            w_me.wrow = irow
            w_me.wcol = self.maps_species_idx
            self.maps_table.setCellWidget(irow, self.maps_species_idx, w_me)
            # w_var_units.textChanged[str].connect(self.custom_data_units_changed)  # being explicit about passing a string 

        # self.maps_table.addStretch(1)  # not sure about this, but keeps buttons shoved to left

        vlayout.addWidget(self.maps_table)
        return vlayout

        #--------------------------------------------------------
    def sizeHint(self):
        return QtCore.QSize(550,650)   # 650

        #--------------------------------------------------------
    def insert_hacky_blank_lines(self, layout):
        idx_row = 4
        for idx in range(11):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idx_row += 1
            # glayout.addWidget(blank_line, idx_row,0, 1,1) # w, row, column, rowspan, colspan
            layout.addWidget(blank_line) # w, row, column, rowspan, colspan

    #-----------------------------------------------------------
    def choose_sbml_file(self):
        file , check = QFileDialog.getOpenFileName(None, "Please select a SBML file",
                                               "", "SBML Files (*.xml)")
        if check:
            self.sbml_file.setText(os.path.relpath(file, os.getcwd()))

    #-----------------------------------------------------------
    def clear_map(self):
        # print("\n---------------- clear_map():")
        for irow in range(self.num_maps):
            for idx in range(self.num_cols):
                self.maps_table.cellWidget(irow, idx).setText('')

        self.num_maps = 0

    #-----------------------------------------------------------
    # fill the PhysiCell-SBML mappings from the XML
    def fill_map(self):
        print("\n----------------sbml_intra.py:  fill_map():")
        self.clear_map()
        irow = 0
        icol = 0
        # cell_def_tab.param_d[cell_def_name]["intracellular"]["sbml_maps"] = 
        # [['PC_substrate', 'oxygen', 'Oxygen'], ['PC_substrate', 'lactate', 'Lactate'], ['PC_substrate', 'glucose', 'Glucose'], ['PC_phenotype', 'da', 'apoptosis_rate'], ['PC_phenotype', 'mms', 'migration_speed'], ['PC_phenotype', 'ssr_lactate', 'Lac_Secretion_Rate'], ['PC_phenotype', 'ctr_0_0', 'Transition_Rate']]
        for sbml_map in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["sbml_maps"]:
            print("sbml_map=",sbml_map)
            if sbml_map[0] == "PC_substrate":
                self.maps_table.cellWidget(irow, 0).setText(sbml_map[1])
            elif sbml_map[0] == "PC_phenotype":
                self.maps_table.cellWidget(irow, 1).setText(sbml_map[1])
            elif sbml_map[0] == "PC_custom_data":
                self.maps_table.cellWidget(irow, 2).setText(sbml_map[1])

            self.maps_table.cellWidget(irow, 3).setText(sbml_map[2])
            irow += 1

        self.num_maps = irow
        print("fill_map():  num_maps=",self.num_maps)
        print("     --> ",self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["sbml_maps"])

        return

    #-----------------------------------------------------------
    # Read the existing mappings in the table, called by validate_params() before fill_xml()
    def read_map(self):
        print("\n\n----------------sbml_intra.py:  read_map():")

        if "sbml_maps" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys():
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["sbml_maps"].clear()
        else:
             self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["sbml_maps"] = []

        # cell_def_tab.param_d[cell_def_name]["intracellular"]["sbml_maps"] = 
        # [['PC_substrate', 'oxygen', 'Oxygen'], ['PC_substrate', 'lactate', 'Lactate'], ['PC_substrate', 'glucose', 'Glucose'], ['PC_phenotype', 'da', 'apoptosis_rate'], ['PC_phenotype', 'mms', 'migration_speed'], ['PC_phenotype', 'ssr_lactate', 'Lac_Secretion_Rate'], ['PC_phenotype', 'ctr_0_0', 'Transition_Rate']]

        self.num_maps = 0
        for irow in range(self.max_map_table_rows):
            # self.maps_substrate_idx = 0
            # self.maps_phenotype_idx = 1
            # self.maps_custom_data_idx = 2
            # self.maps_species_idx = 3
            substrate = self.maps_table.cellWidget(irow, 0).text()
            pheno = self.maps_table.cellWidget(irow, 1).text()
            custom_var = self.maps_table.cellWidget(irow, 2).text()
            species = self.maps_table.cellWidget(irow, 3).text()

            if len(species) > 0:
                if len(substrate) > 0:
                    self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["sbml_maps"].append(["PC_substrate",substrate, species])
                    self.num_maps += 1
                elif len(pheno) > 0:
                    self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["sbml_maps"].append(["PC_phenotype",pheno, species])
                    self.num_maps += 1
                elif len(custom_var) > 0:
                    self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["sbml_maps"].append(["PC_custom_data",custom_var, species])
                    self.num_maps += 1
                else:
                    pass

        print("---------- read_map():  num_maps=",self.num_maps)
        print("           sbml_maps= ", self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["sbml_maps"])

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
        print("check_for_duplicate(): num_maps=",self.num_maps)
        # for irow in range(self.max_map_table_rows):
        for irow in range(self.num_maps):
        # self.maps_celltype_idx = 0
        # self.maps_response_idx = 1
        # self.maps_minval_idx = 2
        # self.maps_baseval_idx = 3
        # self.maps_maxval_idx = 4
        # self.maps_signal_idx = 5
        # self.maps_direction_idx = 6
        # self.maps_halfmax_idx = 7
        # self.maps_hillpower_idx = 8
        # self.maps_applydead_idx = 9
            cell_type = self.maps_table.cellWidget(irow, self.maps_celltype_idx).text()
            # if cell_type == '':
                # break
            if cell_type == cell_type_new:
                signal = self.maps_table.cellWidget(irow, self.maps_signal_idx).text()
                if signal == signal_new:
                    behavior = self.maps_table.cellWidget(irow, self.maps_response_idx).text()
                    if behavior == behavior_new:
                        direction = self.maps_table.cellWidget(irow, self.maps_direction_idx).text()
                        if direction == direction_new:
                            return irow

        return -1

    #--------------------------------------------------------
    # Delete an entire map. 
    def delete_map_cb(self):
        row = self.maps_table.currentRow()
        # print(f'------------- delete_map_cb(), row={row}, self.num_maps={self.num_maps}')
        # if row < 0:
        if (row < 0) or (row+1 > self.num_maps) or (self.num_maps <= 0):
            msg = f'Error: Select a row with a map before deleting.'
            show_studio_warning_window(msg)
            return
        for irow in range(row, self.max_map_table_rows):
            try:
                self.maps_table.cellWidget(irow,self.maps_celltype_idx).wrow -= 1  # sufficient to only decr the "name" column
            except:
                msg = f'Warning: could not decrement row {irow} from the Maps table. Select a row before deleting.'
                show_studio_warning_window(msg)
                return

        self.maps_table.removeRow(row)
        self.add_row_maps_table(self.max_map_table_rows - 1)
        self.num_maps -= 1

    #-----------------------------------------------------------
    def validate_maps_cb(self):
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
        # print("\n maps_tab:-------------------fill_signals_widget()")
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

        for verb in ["phagocytose ","attack ","fuse to ","transform to ","immunogenicity to "]:  # verb
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
    def fill_gui(self, cdname):
        print(f'\n\n------------sbml_intra.py: fill_gui():')

        if "sbml_filename" in self.celldef_tab.param_d[cdname]["intracellular"].keys(): 
            self.sbml_file.setText(self.celldef_tab.param_d[cdname]["intracellular"]["sbml_filename"])

        if "intracellular_dt" in self.celldef_tab.param_d[cdname]["intracellular"].keys(): 
            self.dt_w.setText(self.celldef_tab.param_d[cdname]["intracellular"]["intracellular_dt"])

        self.fill_map()

        # self.clear_comboboxes()

        print("sbml_intra_tab.py: fill_gui(): self.celldef_tab.param_d.keys()= ",self.celldef_tab.param_d.keys())
        # for key in self.celldef_tab.param_d.keys():
        #     print(f'cell type ---> {key}')
        #     self.celltype_combobox.addItem(key)
        #     # self.signal_combobox.addItem(key)
        #     # break
        # # print("\n\n------------\nmaps_tab.py: fill_gui(): self.celldef_tab.param_d = ",self.cell_def_tab.param_d)
        return

    #-----------------------------------------------------------
    def validate_params(self,cdef):
        print("\n--- validate_params(): keys()= ", self.celldef_tab.param_d[cdef]["intracellular"].keys())
        if "type" not in self.celldef_tab.param_d[cdef]["intracellular"].keys():
            print("---- sbml_intra.py: validate_params(): missing 'type'")
            msg = f'Error: Missing "type" in intracellular subtab for ODEs. Please provide before saving the XML.'
            show_studio_warning_window(msg)
            return False

        if len(self.sbml_filename) == 0:
            print("---- sbml_intra.py: validate_params(): missing 'sbml_filename'")
            msg = f'Error: Missing "SBML file" in intracellular subtab for ODEs. Please provide before saving the XML.'
            show_studio_warning_window(msg)
            return False
        self.celldef_tab.param_d[cdef]["intracellular"]["sbml_filename"] = self.sbml_filename

        # if len(self.intracellular_dt) == 0:
        print("self.dt_w.text() = ",self.dt_w.text())
        try:
            if float(self.dt_w.text()) <= 0.0: 
                print("---- sbml_intra.py: validate_params(): missing 'intracellular_dt'")
                msg = f'Error: Invalid "intracellular_dt" in intracellular subtab for ODEs. Please provide before saving the XML.'
                show_studio_warning_window(msg)
                return False
        except:
            msg = f'Error: Invalid "intracellular_dt" in intracellular subtab for ODEs. Please provide before saving the XML.'
            show_studio_warning_window(msg)
            return False
        # self.celldef_tab.param_d[cdef]["intracellular"]["intracellular_dt"] = self.intracellular_dt

        # self.celldef_tab.param_d[cdef]["intracellular"]["intracellular_dt"] = float(self.dt_w.text())
        self.celldef_tab.param_d[cdef]["intracellular"]["intracellular_dt"] = self.dt_w.text()

        self.read_map()    # read the current mappings in the table; refilling the "sbml_maps" dict

        if "sbml_maps" not in self.celldef_tab.param_d[cdef]["intracellular"].keys():
            print("---- sbml_intra.py: validate_params(): missing 'sbml_maps'")
            msg = f'Error: Invalid "sbml_maps" in intracellular subtab for ODEs. Please provide before saving the XML.'
            show_studio_warning_window(msg)
            return False

        return True

        # if "sbml_filename" not in self.celldef_tab.param_d[cdef]["intracellular"].keys():
        #     print("---- sbml_intra.py: validate_params(): missing 'sbml_filename'")
        #     msg = f'Error: Missing "SBML file" in intracellular subtab for ODEs. Please provide before saving the XML.'
        #     show_studio_warning_window(msg)
        #     return False
        # if "intracellular_dt" not in self.celldef_tab.param_d[cdef]["intracellular"].keys():
        #     print("---- sbml_intra.py: validate_params(): missing 'intracellular_dt'")
        #     msg = f'Error: Missing "intracellular_dt" in intracellular subtab for ODEs. Please provide before saving the XML.'
        #     show_studio_warning_window(msg)
        #     return False
        # if "sbml_maps" not in self.celldef_tab.param_d[cdef]["intracellular"].keys():
        #     print("---- sbml_intra.py: validate_params(): missing 'sbml_maps'")
        #     msg = f'Error: Missing "sbml_maps" in intracellular subtab for ODEs. Please provide before saving the XML.'
        #     show_studio_warning_window(msg)
        #     return False        

    #-----------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml(self,pheno,cdef):
        print("\n\n\n--------------sbml_intra.py:  fill_xml() -----------------------")
            # <intracellular type="roadrunner">
            #     <sbml_filename>./config/demo.xml</sbml_filename>
            #     <intracellular_dt>0.01</intracellular_dt>
            #     <map PC_substrate="oxygen" sbml_species="Oxygen"/>
            #     <map PC_substrate="NADH" sbml_species="NADH"/>
            #     <map PC_phenotype="da" sbml_species="apoptosis_rate"/>
            #     <map PC_phenotype="mms" sbml_species="migration_speed"/>
            #     <map PC_phenotype="ssr_lactate" sbml_species="Lac_Secretion_Rate"/>
            #     <map PC_phenotype="ctr_0_0" sbml_species="Transition_Rate"/>
        # self.save_maps_cb()  

        if not self.validate_params(cdef):
            print("\n--------------sbml_intra.py:  fill_xml() - not valid; returning without writing XML")
            return

        # if self.celldef_tab.debug_print_fill_xml:
        #     logging.debug(f'------------------- sbml_intra: fill_xml():  cdef= {cdef}')
        #     print(f'------------------- sbml_intra: fill_xml():  cdef= {cdef}')

        print("--------- sbml_intra: fill_xml(): ['intracellular']=",self.celldef_tab.param_d[cdef]["intracellular"] )
        # ---------- sbml_intra: fill_xml(): ['intracellular']= {'type': 'roadrunner', 'sbml_filename': './config/Toy_Metabolic_Model.xml', 'intracellular_dt': '0.01', 'sbml_maps': [['PC_substrate', 'oxygen', 'Oxygen'], ['PC_substrate', 'lactate', 'Lactate'], ['PC_substrate', 'glucose', 'Glucose'], ['PC_phenotype', 'da', 'apoptosis_rate'], ['PC_phenotype', 'mms', 'migration_speed'], ['PC_phenotype', 'ssr_lactate', 'Lac_Secretion_Rate'], ['PC_phenotype', 'ctr_0_0', 'Transition_Rate']]}


        # interactions = ET.SubElement(pheno, "intracellular",{"type":"roadrunner"})
        intracell = ET.SubElement(pheno, "intracellular",{"type":self.celldef_tab.param_d[cdef]["intracellular"]["type"]})
        intracell.text = indent12  # affects indent of child
        intracell.tail = "\n" + indent12

        elm = ET.SubElement(intracell, "sbml_filename")
        # self.sbml_filename_changed()
        elm.text = self.celldef_tab.param_d[cdef]["intracellular"]["sbml_filename"]
        elm.tail = "\n" + indent12

        elm = ET.SubElement(intracell, "intracellular_dt")
        # elm.text = self.celldef_tab.param_d[cdef]["intracellular"]["intracellular_dt"]
        # elm.text = str(self.celldef_tab.param_d[cdef]["intracellular"]["intracellular_dt"])
        elm.text = self.celldef_tab.param_d[cdef]["intracellular"]["intracellular_dt"]
        elm.tail = "\n" + indent12

        maps = self.celldef_tab.param_d[cdef]["intracellular"]["sbml_maps"]
        for mymap in maps:
            print("        mymap= ",mymap)
        #     <map PC_substrate="oxygen" sbml_species="Oxygen"/>
            elm = ET.SubElement(intracell, "map",{mymap[0]:mymap[1], "sbml_species":mymap[2]})
            elm.text = ""
            elm.tail = "\n" + indent12

        # elm = ET.SubElement(custom_data, key_name, 
        #             { "conserved":conserved,
        #               "units":units,
        #               "description":desc } )

            # elm.text = self.param_d[cdef]['custom_data'][key_name]  # value for this var for this cell def
            # elm.text = self.param_d[cdef]['custom_data'][key_name][0]  # value for this var for this cell def
            # elm.tail = self.indent10
        # subelm.text = self.param_d[cdef]["apoptotic_phagocytosis_rate"]
        # subelm.tail = indent12

        return
    