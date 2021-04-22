"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)

--- Versions ---
0.1 - initial version
"""

import sys
#from PySide6 import QtCore, QtWidgets, QtGui
#from PySide6 import QtCore, QtGui
from PySide6 import QtCore
#from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import *
from PySide6.QtGui import QDoubleValidator

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class SBMLParams(QWidget):
    def __init__(self):
        super().__init__()

        # self.current_param = None
        self.xml_root = None
        self.count = 0

        #-------------------------------------------
        self.label_width = 150
        self.units_width = 90

        self.scroll_area = QScrollArea()
        # splitter.addWidget(self.scroll)
        # self.cell_def_horiz_layout.addWidget(self.scroll)

        self.user_params = QWidget()
        self.main_layout = QVBoxLayout()
        # self.main_layout.addStretch(0)

        #------------------
        controls_hbox = QHBoxLayout()
        # self.new_button = QPushButton("New")
        self.new_button = QPushButton("Append 5 more rows")
        controls_hbox.addWidget(self.new_button)
        self.new_button.clicked.connect(self.append_more_cb)

        # self.copy_button = QPushButton("Copy")
        # controls_hbox.addWidget(self.copy_button)

        self.clear_button = QPushButton("Clear selected rows")
        controls_hbox.addWidget(self.clear_button)
        self.clear_button.clicked.connect(self.clear_rows_cb)

        #------------------
# https://github.com/furkankurtoglu/CRC-Well/blob/master/CRC_v1.8.0-main/config/PhysiCell_settings.xml#L407-L413
#    		    </secretion>
#               <intracellular type="roadrunner">
# 					<sbml_filename>./config/CRC_Toy_Model.xml</sbml_filename>
#                     <species substrate="oxygen">Oxygen</species>
#                     <species substrate="glucose">Glucose</species>
# 				</intracellular>
# 			</phenotype>

# https://github.com/rheiland/PhysiCell_intracellular/blob/main/config/PhysiCell_settings.xml#L192
		# 		<intracellular type="roadrunner">
		# 			<sbml_filename>./config/Toy_oxy.xml</sbml_filename>
        #             <species substrate="oxygen">Oxy</species>
		# 		</intracellular>
		# 	</phenotype>
		# </cell_definition>

        # Fixed names for columns:
        hbox = QHBoxLayout()
        # self.select = QtWidgets.QCheckBox("")
        col1 = QLabel("SBML Species")
        col1.setAlignment(QtCore.Qt.AlignCenter)
        hbox.addWidget(col1)
        col2 = QLabel("Type")
        col2.setAlignment(QtCore.Qt.AlignCenter)
        hbox.addWidget(col2)
        # label.setFixedWidth(180)
        # self.main_layout.addLayout(hbox)

        #------------------

        # Create lists for the various input boxes
        self.select = []
        self.name = []
        self.type = []
        self.value = []
        self.units = []

        # for idx in range(5):
        #     # self.main_layout.addLayout(NewUserParam(self))
        #     hbox = QHBoxLayout()
        #     w = QCheckBox("")
        #     self.select.append(w)
        #     hbox.addWidget(w)

        #     w = QLineEdit()
        #     self.name.append(w)
        #     # self.name.setValidator(QtGui.QDoubleValidator())
        #     # self.diffusion_coef.enter.connect(self.save_xml)
        #     hbox.addWidget(w)

        #     w = QLineEdit()
        #     self.value.append(w)
        #     # w.setValidator(QtGui.QDoubleValidator())
        #     hbox.addWidget(w)

        #     self.main_layout.addLayout(hbox)
        #     self.count = self.count + 1

        try:
            # path = "./config_samples/crc_v1.8.xml"
            path = "./config_samples/crc_pretty.xml"
            with open(path, 'rU') as f:
                our_model = f.read()
        except Exception as e:
                self.dialog_critical(str(e))
        self.map_sbml = QPlainTextEdit()
        self.map_sbml.setPlainText(our_model)
        self.main_layout.addWidget(QLabel("PhysiCell-SBML map"))
        self.main_layout.addWidget(self.map_sbml)

        try:
            path = "./config_samples/CAF_Toy_Model.xml"
            with open(path, 'rU') as f:
                sbml_text = f.read()
        except Exception as e:
                self.dialog_critical(str(e))

        self.sbml_model = QPlainTextEdit()
        self.sbml_model.setReadOnly(True)
        self.sbml_model.setPlainText(sbml_text)
        self.main_layout.addWidget(QLabel("SBML (read-only)"))
        self.main_layout.addWidget(self.sbml_model)

        #==================================================================
        self.user_params.setLayout(self.main_layout)

        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area.setWidget(self.user_params)

        self.layout = QVBoxLayout(self)

        # self.layout.addLayout(controls_hbox)
        self.layout.addWidget(self.scroll_area)

    @QtCore.Slot()
    def clear_rows_cb(self):
        print("----- clearing all selected rows")

    @QtCore.Slot()
    def append_more_cb(self):
        # print("---- append_more_cb()")
        # self.create_user_param()
        # self.scrollLayout.addRow(NewUserParam(self))
        for idx in range(5):
            # self.main_layout.addLayout(NewUserParam(self))
            hbox = QHBoxLayout()
            w = QCheckBox("")
            self.select.append(w)
            hbox.addWidget(w)

            w = QLineEdit()
            self.name.append(w)
            # self.name.setValidator(QtGui.QDoubleValidator())
            # self.diffusion_coef.enter.connect(self.save_xml)
            hbox.addWidget(w)

            w = QLineEdit()
            self.value.append(w)
            # w.setValidator(QtGui.QDoubleValidator())
            hbox.addWidget(w)

            self.main_layout.addLayout(hbox)
            self.count = self.count + 1
            print(self.count)


    def fill_gui(self):
        # pass
        uep_user_params = self.xml_root.find(".//user_parameters")
        # custom_data_path = ".//cell_definition[" + str(self.idx_current_cell_def) + "]//custom_data//"
        print('uep_user_params=',uep_user_params)

        idx = 0
        # rwh/TODO: if we have more vars than we initially created rows for, we'll need
        # to call 'append_more_cb' for the excess.
        for var in uep_user_params:
            print(idx, ") ",var)
            self.name[idx].setText(var.tag)
            print("tag=",var.tag)
            self.value[idx].setText(var.text)

            if 'units' in var.keys():
                self.units[idx].setText(var.attrib['units'])
            idx += 1

    def fill_xml(self):
        pass
    
    def clear_gui(self):
        pass