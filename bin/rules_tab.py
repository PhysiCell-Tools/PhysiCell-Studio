"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)
"""

import sys
# import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QLineEdit, QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,QGridLayout,QPushButton
from PyQt5.QtWidgets import QMessageBox

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

        self.check1 = QCheckBox("")
        idr = 0
        self.rules_tab_layout.addWidget(self.check1, idr,1,1,1)

        self.substrate_dropdown = QComboBox()
        self.rules_tab_layout.addWidget(self.substrate_dropdown, idr,2, 1,1) # w, row, column, rowspan, colspan
        self.substrate_dropdown.currentIndexChanged.connect(self.substrate_dropdown_changed_cb)  

        label = QLabel("")
        # label.setFixedHeight(label_height)
        # label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.rules_tab_layout.addWidget(label, idr,3,1,5) 

        #----------
        self.check2 = QCheckBox("")
        idr += 1
        self.rules_tab_layout.addWidget(self.check2, idr,1,1,1)

        self.celltype_dropdown = QComboBox()
        self.rules_tab_layout.addWidget(self.celltype_dropdown, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.celltype_dropdown.currentIndexChanged.connect(self.celltype_dropdown_changed_cb)  

        label = QLabel("")
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.rules_tab_layout.addWidget(label, idr,3,1,5) 

        # self.rules_tab_layout.addWidget(self.substrate_dropdown, idr,2, 1,1) # w, row, column, rowspan, colspan
        # self.signals_dropdown.currentIndexChanged.connect(self.live_phagocytosis_dropdown_changed_cb)  # beware: will be triggered on a ".clear" too


        # ----- behaviors

        # ----- rules
        self.add_rule_button = QPushButton("Add rule")
        # self.add_rule_button.setStyleSheet("background-color: rgb(250,100,100)")
        self.add_rule_button.setStyleSheet("background-color: green")
        idr += 1
        self.rules_tab_layout.addWidget(self.add_rule_button, idr,1,1,2) 
        # self.add_rule_button.clicked.connect(self.add_rule_cb)

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
        idr = 4
        for idx in range(11):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idr += 1
            glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan

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
        print("\n\n------------\nrules_tab.py: fill_gui():")
        for key in self.microenv_tab.param_d.keys():
            print("substrate type ---> ",key)
            self.substrate_dropdown.addItem(key)
            # break
        # self.substrate_dropdown.addItem("aaaaaaaabbbbbbbbbbccccccccccdddddddddd")
        for key in self.celldef_tab.param_d.keys():
            print("cell type ---> ",key)
            self.celltype_dropdown.addItem(key)
            # self.substrate_dropdown.addItem(key)
            # break
        # print("\n\n------------\nrules_tab.py: fill_gui(): self.celldef_tab.param_d = ",self.cell_def_tab.param_d)
        return

    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml(self):
        return
