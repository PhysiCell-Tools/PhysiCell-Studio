"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)

"""

import sys
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDoubleValidator

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class UserParams(QtWidgets.QWidget):
    def __init__(self, dark_mode):
        super().__init__()

        # self.current_param = None
        self.xml_root = None
        self.count = 0
        self.max_rows = 100  # initially

        # rf. https://www.w3.org/TR/SVG11/types.html#ColorKeywords   - well, but not true on Mac?
        self.row_color1 = "background-color: Tan"
        self.row_color2 =  "background-color: LightGreen"
        if dark_mode:
            self.row_color1 = "background-color: darkslategray"  # = rgb( 47, 79, 79)
            self.row_color2 =  "background-color: rgb( 99, 99, 10)"

        #-------------------------------------------
        self.label_width = 150
        self.units_width = 190

        self.scroll_area = QtWidgets.QScrollArea()
        # splitter.addWidget(self.scroll)
        # self.cell_def_horiz_layout.addWidget(self.scroll)

        self.user_params = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QVBoxLayout()
        # self.main_layout.addStretch(0)

        #------------------
        controls_hbox = QtWidgets.QHBoxLayout()
        # self.new_button = QPushButton("New")
        self.new_button = QPushButton("Append 10 more rows")
        controls_hbox.addWidget(self.new_button)
        self.new_button.clicked.connect(self.append_more_cb)

        # self.copy_button = QPushButton("Copy")
        # controls_hbox.addWidget(self.copy_button)

        self.clear_button = QPushButton("Clear selected rows")
        controls_hbox.addWidget(self.clear_button)
        self.clear_button.clicked.connect(self.clear_rows_cb)

        #------------------
		# <random_seed type="int" units="dimensionless">0</random_seed> 
		# <cargo_signal_D type="double" units="micron/min^2">1e3</cargo_signal_D>

        # Fixed names for columns:
        hbox = QtWidgets.QHBoxLayout()
        # self.select = QtWidgets.QCheckBox("")
        col1 = QtWidgets.QLabel("Name")
        col1.setAlignment(QtCore.Qt.AlignCenter)
        hbox.addWidget(col1)
        col2 = QtWidgets.QLabel("Type")
        col2.setAlignment(QtCore.Qt.AlignCenter)
        hbox.addWidget(col2)
        col3 = QtWidgets.QLabel("Value")
        col3.setAlignment(QtCore.Qt.AlignCenter)
        col3.setAlignment(QtCore.Qt.AlignLeft)
        hbox.addWidget(col3)
        col4 = QtWidgets.QLabel("Units")
        col4.setFixedWidth(self.units_width)
        col4.setAlignment(QtCore.Qt.AlignCenter)
        hbox.addWidget(col4)
        # label.setFixedWidth(180)
        self.main_layout.addLayout(hbox)

        #------------------

        # Create lists for the various input boxes
        self.select = []
        self.name = []
        self.type = []
        self.value = []
        self.units = []
        self.description = []

        self.type_dropdown = QComboBox()
        self.type_dropdown.setFixedWidth(300)
        # self.type_dropdown.currentIndexChanged.connect(self.cycle_changed_cb)
        self.type_dropdown.addItem("int")
        self.type_dropdown.addItem("double")
        self.type_dropdown.addItem("bool")
        self.type_dropdown.addItem("text")

        for idx in range(self.max_rows):
            # self.main_layout.addLayout(NewUserParam(self))
            hbox = QHBoxLayout()
            #-----
            w_check = QCheckBox("")
            self.select.append(w_check)
            hbox.addWidget(w_check)

            #-----
            w_varname = QLineEdit()
            self.name.append(w_varname)
            # self.name.setValidator(QtGui.QDoubleValidator())
            # self.diffusion_coef.enter.connect(self.save_xml)
            hbox.addWidget(w_varname)
            if idx == 0:
                w_varname.setText("random_seed")   # Why?
            
            #-----
            # w = QLineEdit()
            w_cbox = QComboBox()
            # xml2jupyter: {"double":"FloatText", "int":"IntText", "bool":"Checkbox", "string":"Text", "divider":""}
            w_cbox.addItem("double")
            w_cbox.addItem("int")
            w_cbox.addItem("bool")
            w_cbox.addItem("string")
            if idx == 0:
                w_cbox.setCurrentIndex(1)
            self.type.append(w_cbox)
            hbox.addWidget(w_cbox)

            #-----
            w_val = QLineEdit()
            self.value.append(w_val)
            # w.setValidator(QtGui.QDoubleValidator())
            if idx == 0:
                w_val.setText("0")  # Why?
            hbox.addWidget(w_val)

            #-----
            w_units = QLineEdit()
            w_units.setFixedWidth(self.units_width)
            self.units.append(w_units)
            hbox.addWidget(w_units)

            # units = QtWidgets.QLabel("micron^2/min")
            # units.setFixedWidth(units_width)
            # hbox.addWidget(units)
            self.main_layout.addLayout(hbox)


            #-----
            hbox = QHBoxLayout()
            # w = QLabel("Desc:")
            w_desc = QLabel("      Description:")
            hbox.addWidget(w_desc)

            w_desc = QLineEdit()
            self.description.append(w_desc)
            hbox.addWidget(w_desc)

            if idx % 2 == 0:
                w_varname.setStyleSheet(self.row_color1)  
                w_val.setStyleSheet(self.row_color1)  
                w_units.setStyleSheet(self.row_color1)
                w_desc.setStyleSheet(self.row_color1)
            else:
                w_varname.setStyleSheet(self.row_color2)  
                w_val.setStyleSheet(self.row_color2)  
                w_units.setStyleSheet(self.row_color2)
                w_desc.setStyleSheet(self.row_color2)

            # w.setStyleSheet("background-color: lightgray")
            # w.setStyleSheet("background-color: #e4e4e4")
            self.main_layout.addLayout(hbox)

            self.count = self.count + 1
            # print(self.count)


        #==================================================================
        self.user_params.setLayout(self.main_layout)

        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area.setWidget(self.user_params)

        self.layout = QVBoxLayout(self)

        self.layout.addLayout(controls_hbox)
        self.layout.addWidget(self.scroll_area)

    def set_colors(self, color1, color2):
        self.row_color1 = color1 
        self.row_color2 = color2 
        for idx in range(self.max_rows):
            if idx % 2 == 0:
                w_varname.setStyleSheet(self.row_color1)  
                w_val.setStyleSheet(self.row_color1)  
                w_units.setStyleSheet(self.row_color1)
                w_desc.setStyleSheet(self.row_color1)
            else:
                w_varname.setStyleSheet(self.row_color2)  
                w_val.setStyleSheet(self.row_color2)  
                w_units.setStyleSheet(self.row_color2)
                w_desc.setStyleSheet(self.row_color2)

    # @QtCore.Slot()
    def clear_rows_cb(self):
        print("----- clearing all selected rows")
        for idx in range(self.count):
            if self.select[idx].isChecked():
                self.name[idx].clear()
                self.type[idx].setCurrentIndex(0)  # double
                self.value[idx].clear()
                self.units[idx].clear()
                self.description[idx].clear()
                self.select[idx].setChecked(False)

    # @QtCore.Slot()
    def append_more_cb(self):
        # print("---- append_more_cb()")
        # self.create_user_param()
        # self.scrollLayout.addRow(NewUserParam(self))
        for idx in range(10):
            # self.main_layout.addLayout(NewUserParam(self))
            hbox = QHBoxLayout()

            w = QCheckBox("")
            self.select.append(w)
            hbox.addWidget(w)

            w_varname = QLineEdit()
            self.name.append(w_varname)
            # self.name.setValidator(QtGui.QDoubleValidator())
            # self.diffusion_coef.enter.connect(self.save_xml)
            hbox.addWidget(w_varname)

            w = QComboBox()
            # xml2jupyter: {"double":"FloatText", "int":"IntText", "bool":"Checkbox", "string":"Text", "divider":""}
            w.addItem("double")
            w.addItem("int")
            w.addItem("bool")
            w.addItem("string")
            self.type.append(w)
            hbox.addWidget(w)

            w_val = QLineEdit()
            self.value.append(w_val)
            # w.setValidator(QtGui.QDoubleValidator())
            hbox.addWidget(w_val)

            w_units = QLineEdit()
            w_units.setFixedWidth(self.units_width)
            self.units.append(w_units)
            hbox.addWidget(w_units)

            self.main_layout.addLayout(hbox)

            hbox = QHBoxLayout()
            w = QLabel("Desc:")
            hbox.addWidget(w)

            w_desc = QLineEdit()
            self.description.append(w_desc)
            hbox.addWidget(w_desc)
            # w.setStyleSheet("background-color: lightgray")

            if idx % 2 == 0:
                w_varname.setStyleSheet(self.color1)  
                w_val.setStyleSheet(self.color1)  
                w_units.setStyleSheet(self.color1)  
                w_desc.setStyleSheet(self.color1)  
            else:
                w_varname.setStyleSheet(self.color2)  
                w_val.setStyleSheet(self.color2)  
                w_units.setStyleSheet(self.color2)  
                w_desc.setStyleSheet(self.color2)  

            self.main_layout.addLayout(hbox)

            self.count = self.count + 1
            print(self.count)
    #     # self.text.setText(random.choice(self.hello))
    #     pass


    def clear_gui(self):
        # pass
        for idx in range(self.count):
            self.name[idx].setText("")
            # self.type[idx].setText("")
            self.value[idx].setText("0.0")
            self.units[idx].setText("")
            self.description[idx].setText("")
        # self.count = 0

        # self.name.clear()
        # self.value.clear()
        # self.units.clear()
        # self.description.clear()


    # populate the GUI tab with what is in the .xml
    def fill_gui(self):
        print("\n\n------------  user_params_tab: fill_gui --------------")
        # pass
        uep_user_params = self.xml_root.find(".//user_parameters")
        # custom_data_path = ".//cell_definition[" + str(self.idx_current_cell_def) + "]//custom_data//"
        print('uep_user_params=',uep_user_params)

        idx = 0
        # rwh/TODO: if we have more vars than we initially created rows for, we'll need
        # to call 'append_more_cb' for the excess.
        for var in uep_user_params:
            # type_cast = {"double":"float", "int":"int", "bool":"bool", "string":"", "divider":"Text"}
            if 'type' in var.keys():
                # print("\n------------  var.attrib['type'] = ", var.attrib['type'])
                if "divider" in var.attrib['type']:  # just for visual separation in Jupyter notebook
                    continue
                # select appropriate dropdown/combobox item (double, int, bool, text)
                elif "double" in var.attrib['type']:
                    self.type[idx].setCurrentIndex(0)
                elif "int" in var.attrib['type']:
                    self.type[idx].setCurrentIndex(1)
                elif "bool" in var.attrib['type']:
                    self.type[idx].setCurrentIndex(2)
                else:
                    self.type[idx].setCurrentIndex(3)
            else:  # default 'double'
                self.type[idx].setCurrentIndex(1)

            # print(idx, ") ",var)
            self.name[idx].setText(var.tag)
            # print("tag=",var.tag)
            self.value[idx].setText(var.text)

            if 'units' in var.keys():
                self.units[idx].setText(var.attrib['units'])
            if 'description' in var.keys():
                # print("----- found description: ",var.attrib['description'])
                self.description[idx].setText(var.attrib['description'])
            # else:
            #     print("----- no description found. ")

            idx += 1

    # Generate the .xml to reflect changes in the GUI
    def fill_xml(self):
        print("--------- user_params_tab.py:  fill_xml(): self.count = ",self.count)
        uep = self.xml_root.find('.//user_parameters')
        if uep:
            print("--------- found //user_parameters")
            # Begin by removing all previously defined user params in the .xml
            # weird, this only removes the 1st child
            for var in list(uep):
                # print("------ remove ",var)
                uep.remove(var)
    
    # <user_parameters>
	# 	<random_seed type="int" units="dimensionless">13</random_seed> 
	# 	<glue_stickiness type="double" units="min">42.0</glue_stickiness>
	# </user_parameters>

        uep = self.xml_root.find('.//user_parameters')
        knt = 0
        for idx in range(self.count):
            vname = self.name[idx].text()
            if vname:  # only deal with rows having names
                print(vname)
                elm = ET.Element(vname, 
                    {"type":self.type[idx].currentText(), 
                     "units":self.units[idx].text(),
                     "description":self.description[idx].text()})
                # elm = ET.Element(vname, { "units":self.units[idx]})
                # elm = ET.Element(vname)
                elm.text = self.value[idx].text()
                elm.tail = '\n        '
                uep.insert(knt,elm)
                knt += 1
        elm.tail = '\n    '
        print("found ",knt)