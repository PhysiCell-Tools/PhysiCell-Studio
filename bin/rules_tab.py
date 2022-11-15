"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)
"""

import sys
import os
import logging
from pathlib import Path
# import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QLineEdit, QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,QGridLayout,QPushButton, QPlainTextEdit, QFileDialog
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
        self.add_rule_button.clicked.connect(self.add_rule_cb)
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
        # print("Load button.size= ",self.load_rules_button.size())
        self.load_rules_button.setStyleSheet("background-color: lightgreen")
        self.load_rules_button.clicked.connect(self.load_rules_cb)
        self.rules_tab_layout.addWidget(self.load_rules_button, idx_row,icol,1,1) 

        icol += 1
        self.save_rules_button = QPushButton("Save rules")
        self.save_rules_button.setStyleSheet("background-color: lightgreen")
        self.save_rules_button.clicked.connect(self.save_rules_cb)
        self.rules_tab_layout.addWidget(self.save_rules_button, idx_row,icol,1,1) 

        icol += 1
        label = QLabel("folder")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.rules_tab_layout.addWidget(label, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        self.rules_folder = QLineEdit()
        icol += 1
        self.rules_tab_layout.addWidget(self.rules_folder, idx_row,icol,1,2) # w, row, column, rowspan, colspan

        icol += 2
        label = QLabel("file")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.rules_tab_layout.addWidget(label, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        self.rules_file = QLineEdit()
        icol += 1
        self.rules_tab_layout.addWidget(self.rules_file, idx_row,icol,1,2) # w, row, column, rowspan, colspan

        # idx_row += 1
        self.rules_enabled = QCheckBox("enable")
        icol += 2
        self.rules_tab_layout.addWidget(self.rules_enabled, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        #----------------------
        # try:
        #     # with open("config/cell_rules.csv", 'rU') as f:
        #     with open("config/rules.csv", 'rU') as f:
        #         text = f.read()
        #     self.rules_text.setPlainText(text)
        # except Exception as e:
        #     # self.dialog_critical(str(e))
        #     # print("error opening config/cells_rules.csv")
        #     print("rules_tab.py: error opening config/rules.csv")
        #     logging.error(f'rules_tab.py: Error opening config/rules.csv')
        #     # sys.exit(1)
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

    def fill_rules(self, full_rules_fname):
        if os.path.isfile(full_rules_fname):
            try:
                # with open("config/rules.csv", 'rU') as f:
                with open(full_rules_fname, 'rU') as f:
                    text = f.read()
                    self.rules_text.setPlainText(text)
            except Exception as e:
            # self.dialog_critical(str(e))
            # print("error opening config/cells_rules.csv")
                print(f'rules_tab.py: Error opening or reading {full_rules_fname}')
                logging.error(f'rules_tab.py: Error opening or reading {full_rules_fname}')
                # sys.exit(1)
        else:
            print(f'\n\n!!!  WARNING: fill_rules(): {full_rules_fname} is not a valid file !!!\n')
            logging.error(f'fill_rules(): {full_rules_fname} is not a valid file')

    # else:  # should empty the Rules tab
    #     self.rules_text.setPlainText("")
    #     self.rules_folder.setText("")
    #     self.rules_file.setText("")
        return

    def add_rule_cb(self):
        rule_str = self.celltype_dropdown.currentText()
        rule_str += ','
        rule_str += self.action_dropdown.currentText()
        rule_str += ','
        rule_str += self.rule_val1.text()
        rule_str += ','
        rule_str += self.rule_val2.text()
        rule_str += ','
        rule_str += self.rule_val3.text()
        rule_str += ','
        rule_str += self.substrate_dropdown.currentText()
        rule_str += ','
        rule_str += self.up_down_dropdown.currentText()
        rule_str += ','
        rule_str += self.rule_val4.text()
        rule_str += ','
        rule_str += self.rule_val5.text()

        self.rules_text.appendPlainText(rule_str)
        return

    def load_rules_cb(self):
        # filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')
        filePath = QFileDialog.getOpenFileName(self,'',".")
        full_path_rules_name = filePath[0]
        logging.debug(f'\nload_rules_cb():  full_path_rules_name ={full_path_rules_name}')
        print(f'\nload_rules_cb():  full_path_rules_name ={full_path_rules_name}')
        basename = os.path.basename(full_path_rules_name)
        print(f'load_rules_cb():  basename ={basename}')
        dirname = os.path.dirname(full_path_rules_name)
        print(f'load_rules_cb():  dirname ={dirname}')
        # if (len(full_path_rules_name) > 0) and Path(full_path_rules_name):
        if (len(full_path_rules_name) > 0) and Path(full_path_rules_name).is_file():
            print("load_rules_cb():  filePath is valid")
            logging.debug(f'     filePath is valid')
            print("len(full_path_rules_name) = ", len(full_path_rules_name) )
            logging.debug(f'     len(full_path_rules_name) = {len(full_path_rules_name)}' )
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
            self.fill_rules(full_path_rules_name)

        else:
            print("load_rules_cb():  full_path_model_name is NOT valid")

    def save_rules_cb(self):
        folder_name = self.rules_folder.text()
        file_name = self.rules_file.text()
        full_rules_fname = os.path.join(folder_name, file_name)
        # if os.path.isfile(full_rules_fname):
        try:
            # with open("config/rules.csv", 'rU') as f:
            with open(full_rules_fname, 'w') as f:
                rules_text = self.rules_text.toPlainText()
                f.write(rules_text )
        except Exception as e:
        # self.dialog_critical(str(e))
        # print("error opening config/cells_rules.csv")
            print(f'rules_tab.py: Error writing {full_rules_fname}')
            logging.error(f'rules_tab.py: Error writing {full_rules_fname}')
                # sys.exit(1)
        # else:
            # print(f'\n\n!!!  WARNING: fill_rules(): {full_rules_fname} is not a valid file !!!\n')
            # logging.error(f'fill_rules(): {full_rules_fname} is not a valid file')

    # else:  # should empty the Rules tab
    #     self.rules_text.setPlainText("")
    #     self.rules_folder.setText("")
    #     self.rules_file.setText("")
        return

    def fill_gui(self):
        logging.debug(f'\n\n------------\nrules_tab.py: fill_gui():')
        print("rules_tab.py: fill_gui(): self.microenv_tab.param_d.keys()= ",self.microenv_tab.param_d.keys())
        for key in self.microenv_tab.param_d.keys():
            logging.debug(f'substrate type ---> {key}')
            if key == 'gradients' or key == 'track_in_agents':
                pass
            else:
                self.substrate_dropdown.addItem(key)
            # break
        # self.substrate_dropdown.addItem("aaaaaaaabbbbbbbbbbccccccccccdddddddddd")

        print("rules_tab.py: fill_gui(): self.celldef_tab.param_d.keys()= ",self.celldef_tab.param_d.keys())
        for key in self.celldef_tab.param_d.keys():
            logging.debug(f'cell type ---> {key}')
            self.celltype_dropdown.addItem(key)
            # self.substrate_dropdown.addItem(key)
            # break
        # print("\n\n------------\nrules_tab.py: fill_gui(): self.celldef_tab.param_d = ",self.cell_def_tab.param_d)


    #   <cell_rules type="csv" enabled="true">
    #     <folder>./config</folder>
    #     <filename>dicty_rules.csv</filename>
    # </cell_rules>      
    # </cell_definitions>
        uep = self.xml_root.find(".//cell_definitions//cell_rules")
        logging.debug(f'rules_tab.py: fill_gui(): <cell_rules> = {uep}')
        print(f'rules_tab.py: fill_gui(): <cell_rules> =  {uep}')
        if uep:
            folder_name = self.xml_root.find(".//cell_definitions//cell_rules//folder").text
            self.rules_folder.setText(folder_name)
            file_name = self.xml_root.find(".//cell_definitions//cell_rules//filename").text
            self.rules_file.setText(file_name)
            full_rules_fname = os.path.join(folder_name, file_name)

            if uep.attrib['enabled'].lower() == 'true':
                self.rules_enabled.setChecked(True)
            else:
                self.rules_enabled.setChecked(False)

            self.fill_rules(full_rules_fname)

            # if os.path.isfile(full_rules_fname):
            #     try:
            #         # with open("config/rules.csv", 'rU') as f:
            #         with open(full_rules_fname, 'rU') as f:
            #             text = f.read()
            #             self.rules_text.setPlainText(text)
            #     except Exception as e:
            #     # self.dialog_critical(str(e))
            #     # print("error opening config/cells_rules.csv")
            #         print(f'rules_tab.py: Error opening or reading {full_rules_fname}')
            #         logging.error(f'rules_tab.py: Error opening or reading {full_rules_fname}')
            #         # sys.exit(1)
            # else:
            #     print(f'{full_rules_fname} is not a valid file')
            #     logging.error(f'{full_rules_fname} is not a valid file')

        else:  # should empty the Rules tab
            self.rules_text.setPlainText("")
            self.rules_folder.setText("")
            self.rules_file.setText("")
            self.rules_enabled.setChecked(False)
        return

    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml(self):
        indent8 = '\n        '
        indent10 = '\n          '
        # self.xml_root.find(".//x_min").text = self.xmin.text()

        # <cell_rules type="csv" enabled="true">
        #     <folder>.</folder>
        #     <filename>test_rules.csv</filename>
        # </cell_rules>      
        # </cell_definitions>

        self.xml_root.find(".//cell_rules//folder").text = self.rules_folder.text()
        self.xml_root.find(".//cell_rules//filename").text = self.rules_file.text()

        if self.rules_enabled.isChecked():
            self.xml_root.find(".//cell_definitions//cell_rules").attrib['enabled'] = 'true'
        else:
            self.xml_root.find(".//cell_definitions//cell_rules").attrib['enabled'] = 'false'

        return
    