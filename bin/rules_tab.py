"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)
"""

import sys
import logging
# import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QLineEdit, QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,QGridLayout,QPushButton, QPlainTextEdit
from PyQt5.QtWidgets import QMessageBox
# from PyQt5.QtGui import QTextEdit

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class Rules(QWidget):
    # def __init__(self, nanohub_flag):
    def __init__(self, microenv_tab, celldef_tab):
        super().__init__()

        # self.nanohub_flag = nanohub_flag
        self.nanohub_flag = False

        self.microenv_tab = microenv_tab
        self.celldef_tab = celldef_tab

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

        self.rules_tab_layout = QGridLayout()

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
        # -- time

        idx_row = 0
        # self.check1 = QCheckBox("")
        # self.rules_tab_layout.addWidget(self.check1, idx_row,1,1,1)
        icol = 0
        self.celltype_dropdown = QComboBox()
        self.rules_tab_layout.addWidget(self.celltype_dropdown, idx_row,icol, 1,1) # w, row, column, rowspan, colspan

        # label = QLabel("")
        # # label.setFixedHeight(label_height)
        # # label.setStyleSheet("background-color: orange")
        # label.setAlignment(QtCore.Qt.AlignCenter)
        # self.rules_tab_layout.addWidget(label, idx_row,3,1,5) 

        icol += 1
        self.action_dropdown = QComboBox()
        self.action_dropdown.addItem("cycle entry")
        self.rules_tab_layout.addWidget(self.action_dropdown, idx_row,icol, 1,1) # w, row, column, rowspan, colspan
        # self.action_dropdown.currentIndexChanged.connect(self.substrate_dropdown_changed_cb)  

        self.rule_val1 = QLineEdit()
        self.rule_val1.setValidator(QtGui.QDoubleValidator())
        icol += 1
        self.rules_tab_layout.addWidget(self.rule_val1, idx_row,icol,1,1) # w, row, column, rowspan, 

        self.rule_val2 = QLineEdit()
        self.rule_val2.setValidator(QtGui.QDoubleValidator())
        icol += 1
        self.rules_tab_layout.addWidget(self.rule_val2, idx_row,icol,1,1) # w, row, column, rowspan, 

        self.rule_val3 = QLineEdit()
        self.rule_val3.setValidator(QtGui.QDoubleValidator())
        icol += 1
        self.rules_tab_layout.addWidget(self.rule_val3, idx_row,icol,1,1) # w, row, column, rowspan, 

        # idx_row += 1
        # self.check2 = QCheckBox("")
        # self.rules_tab_layout.addWidget(self.check2, idx_row,1,1,1)

        icol += 1
        self.substrate_dropdown = QComboBox()
        self.rules_tab_layout.addWidget(self.substrate_dropdown, idx_row,icol, 1,1) # w, row, column, rowspan, colspan
        self.substrate_dropdown.currentIndexChanged.connect(self.substrate_dropdown_changed_cb)  

        # self.celltype_dropdown.currentIndexChanged.connect(self.celltype_dropdown_changed_cb)  

        icol += 1
        self.up_down_dropdown = QComboBox()
        self.up_down_dropdown.addItem("increases")
        self.up_down_dropdown.addItem("decreases")
        self.rules_tab_layout.addWidget(self.up_down_dropdown, idx_row,icol, 1,1) # w, row, column, rowspan, colspan

        self.rule_val4 = QLineEdit()
        self.rule_val4.setValidator(QtGui.QDoubleValidator())
        icol += 1
        self.rules_tab_layout.addWidget(self.rule_val4, idx_row,icol,1,1) # w, row, column, rowspan, 

        self.rule_val5 = QLineEdit()
        self.rule_val5.setValidator(QtGui.QDoubleValidator())
        icol += 1
        self.rules_tab_layout.addWidget(self.rule_val5, idx_row,icol,1,1) # w, row, column, rowspan, 

        label = QLabel("")
        label.setAlignment(QtCore.Qt.AlignCenter)
        # self.rules_tab_layout.addWidget(label, idx_row,3,1,5) 

        # self.rules_tab_layout.addWidget(self.substrate_dropdown, idx_row,2, 1,1) # w, row, column, rowspan, colspan
        # self.signals_dropdown.currentIndexChanged.connect(self.live_phagocytosis_dropdown_changed_cb)  # beware: will be triggered on a ".clear" too
        # ----- behaviors

        # ----- rules
        self.add_rule_button = QPushButton("Add rule")
        # self.add_rule_button.setStyleSheet("background-color: rgb(250,100,100)")
        self.add_rule_button.setStyleSheet("background-color: lightgreen")
        idx_row += 1
        self.rules_tab_layout.addWidget(self.add_rule_button, idx_row,0,1,1) 
        # self.add_rule_button.clicked.connect(self.add_rule_cb)

        #----------------------
        self.rules_text = QPlainTextEdit()  # config/cell_rules.csv
        self.rules_text.setReadOnly(False)

        idx_row += 1
        self.rules_tab_layout.addWidget(self.rules_text, idx_row,0,1,9)  # w, row, col, rowspan, colspan
        # self.text.resize(400,900)  # nope

        #----------------------
        idx_row += 1
        icol = 0
        self.load_rules_button = QPushButton("Load")
        print("Load button.size= ",self.load_rules_button.size())
        self.load_rules_button.setStyleSheet("background-color: lightgreen")
        self.rules_tab_layout.addWidget(self.load_rules_button, idx_row,icol,1,1) 

        icol += 1
        self.load_rules_button = QPushButton("Save")
        self.load_rules_button.setStyleSheet("background-color: lightgreen")
        self.rules_tab_layout.addWidget(self.load_rules_button, idx_row,icol,1,1) 

        icol += 1
        label = QLabel("folder")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.rules_tab_layout.addWidget(label, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        self.csv_folder = QLineEdit()
        # self.csv_folder.setEnabled(False)
        icol += 1
        self.rules_tab_layout.addWidget(self.csv_folder, idx_row,icol,1,2) # w, row, column, rowspan, colspan

        icol += 2
        label = QLabel("file")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.rules_tab_layout.addWidget(label, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        self.csv_file = QLineEdit()
        icol += 1
        self.rules_tab_layout.addWidget(self.csv_file, idx_row,icol,1,2) # w, row, column, rowspan, colspan

        #----------------------
        try:
            # with open("config/cell_rules.csv", 'rU') as f:
            with open("config/rules.csv", 'rU') as f:
                text = f.read()
            self.rules_text.setPlainText(text)
        except Exception as e:
            # self.dialog_critical(str(e))
            # print("error opening config/cells_rules.csv")
            print("rules_tab.py: error opening config/rules.csv")
            logging.error(f'rules_tab.py: Error opening config/rules.csv')
            # sys.exit(1)
        # else
        # else:
            # update path value
            # self.path = path

            # update the text
        # self.rules_text.setPlainText(text)
            # self.update_title()


        # self.vbox.addWidget(self.text)

        #---------
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
    def insert_hacky_blank_lines(self, glayout):
        idx_row = 4
        for idx in range(11):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idx_row += 1
            glayout.addWidget(blank_line, idx_row,0, 1,1) # w, row, column, rowspan, colspan

    def substrate_dropdown_changed_cb(self, idx):
        celltype_name = self.substrate_dropdown.currentText()
        self.substrate = celltype_name

        # print("(dropdown) cell_adhesion_affinity= ",self.param_d[self.current_cell_def]["cell_adhesion_affinity"])
        # if self.cell_adhesion_affinity_celltype in self.param_d[self.current_cell_def]["cell_adhesion_affinity"].keys():
        #     self.cell_adhesion_affinity.setText(self.param_d[self.current_cell_def]["cell_adhesion_affinity"][self.cell_adhesion_affinity_celltype])
        # else:
        #     self.cell_adhesion_affinity.setText(self.default_affinity)

        # if idx == -1:
        #     return


    def fill_gui(self):
        logging.debug(f'\n\n------------\nrules_tab.py: fill_gui():')
        for key in self.microenv_tab.param_d.keys():
            logging.debug(f'substrate type ---> {key}')
            self.substrate_dropdown.addItem(key)
            # break
        # self.substrate_dropdown.addItem("aaaaaaaabbbbbbbbbbccccccccccdddddddddd")
        for key in self.celldef_tab.param_d.keys():
            logging.debug(f'cell type ---> {key}')
            self.celltype_dropdown.addItem(key)
            # self.substrate_dropdown.addItem(key)
            # break
        # print("\n\n------------\nrules_tab.py: fill_gui(): self.celldef_tab.param_d = ",self.cell_def_tab.param_d)
        return

    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml(self):
        return
