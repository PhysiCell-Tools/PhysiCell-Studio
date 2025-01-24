"""
Authors:
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
and rf. Credits.md

"""

import sys
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
import logging
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtGui import QDoubleValidator

from studio_classes import StudioTab, QCheckBox_custom

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class MyQComboBox(QComboBox):
    vname = None
    # idx = None  # index
    wrow = 0  # widget's row in a table
    wcol = 0  # widget's column in a table

# Overloading the QLineEdit widget to let us map it to its variable name. Ugh.
class MyQLineEdit(QLineEdit):
    vname = None
    # idx = None  # index
    wrow = 0
    wcol = 0
    prev = None

class UserParams(StudioTab):
    def __init__(self, xml_creator):
        super().__init__(xml_creator)
        self.xml_root = None
        self.count = 100

        # rf. https://www.w3.org/TR/SVG11/types.html#ColorKeywords   - well, but not true on Mac?
        self.row_color1 = "background-color: Tan"
        self.row_color2 =  "background-color: LightGreen"

        #-------------------------------------------
        self.label_width = 150
        self.units_width = 190

        self.combobox_width = 90

        self.scroll_area = QScrollArea()

        self.user_params = QWidget()

        self.utable = QTableWidget()
        self.max_rows = 100
        self.max_cols = 5

        self.utable.setColumnCount(self.max_cols)
        self.utable.setRowCount(self.max_rows)
        self.utable.setHorizontalHeaderLabels(['Name','Type','Value','Units','Description'])

        self.main_layout = QVBoxLayout()

        #------------------
        # button_width = 200
        controls_hbox = QHBoxLayout()

        hlayout = QHBoxLayout()
        self.name_search = QLineEdit()
        self.name_search.setFixedWidth(400)
        self.name_search.setPlaceholderText("Search for Name...")
        self.name_search.textChanged.connect(self.search_user_param_cb)
        hlayout.addWidget(self.name_search)

        # delete_row_btn = QPushButton("Delete row")
        # delete_row_btn.setFixedWidth(100)
        # delete_row_btn.clicked.connect(self.delete_user_param_cb)
        # delete_row_btn.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        # hlayout.addWidget(delete_row_btn)

        # hlayout.addWidget(QLabel("(after selecting a row #)"))

        hlayout.addStretch()
        self.main_layout.addLayout(hlayout)

        self.var_icol_name = 0  # Name
        self.var_icol_type = 1  # type combobox
        self.var_icol_value = 2  # Value
        self.var_icol_units = 3  # Units
        self.var_icol_desc = 4  # Description

        # Create lists for the various input boxes
        # self.select = []
        # self.name = []
        # self.type = []
        # self.value = []
        # self.units = []
        # self.description = []

        for irow in range(self.max_rows):
            # ------- name
            w_varname = MyQLineEdit()
            w_varname.setFrame(False)
            rx_valid_varname = QtCore.QRegExp("^[a-zA-Z][a-zA-Z0-9_]+$")
            name_validator = QtGui.QRegExpValidator(rx_valid_varname )
            w_varname.setValidator(name_validator)

            self.utable.setCellWidget(irow, self.var_icol_name, w_varname)   # 1st col
            w_varname.vname = w_varname  
            w_varname.wrow = irow
            w_varname.wcol = self.var_icol_name
            w_varname.textChanged[str].connect(self.name_changed_cb)  # being explicit about passing a string 
            w_varname.editingFinished.connect(self.name_change_finished_cb) 

            # ------- type
            w_var_type = MyQComboBox()
            # w_var_type.setStyleSheet(self.checkbox_style)
            # w_var_type.setFrame(False)
            w_var_type.vname = w_varname  
            w_var_type.wrow = irow
            w_var_type.wcol = self.var_icol_type
            # w_var_type.clicked.connect(self.var_type_clicked)

            # w_var_type.setStyleSheet("color: #000000; background-color: #FFFFFF;")
            # w_var_type.setFixedWidth(450)
            # w_var_type.currentIndexChanged.connect(self.cycle_changed_cb)
            w_var_type.addItem("double")
            w_var_type.addItem("int")
            w_var_type.addItem("bool")
            w_var_type.addItem("string")

            self.utable.setCellWidget(irow, self.var_icol_type, w_var_type)
            # self.type.append(w_var_type)

            # ------- value
            # w_varval = MyQLineEdit('0.0')
            w_varval = MyQLineEdit()
            w_varval.setFrame(False)
            # item = QTableWidgetItem('')
            w_varval.vname = w_varname  
            w_varval.wrow = irow
            w_varval.wcol = self.var_icol_value
            # w_varval.idx = irow   # rwh: is .idx used?
            # w_varval.setValidator(QtGui.QDoubleValidator())
            # self.utable.setItem(irow, self.var_icol_value, item)
            self.utable.setCellWidget(irow, self.var_icol_value, w_varval)
            # w_varval.textChanged[str].connect(self.value_changed_cb)  # being explicit about passing a string 

            # ------- units
            w_var_units = MyQLineEdit()
            w_var_units.setFrame(False)
            w_var_units.setFrame(False)
            w_var_units.vname = w_varname  
            w_var_units.wrow = irow
            w_var_units.wcol = self.var_icol_units
            self.utable.setCellWidget(irow, self.var_icol_units, w_var_units)
            # w_var_units.textChanged[str].connect(self.units_changed_cb)  # being explicit about passing a string 

            # ------- description
            w_var_desc = MyQLineEdit()
            w_var_desc.setFrame(False)
            w_var_desc.vname = w_varname  
            w_var_desc.wrow = irow
            w_var_desc.wcol = self.var_icol_desc
            self.utable.setCellWidget(irow, self.var_icol_desc, w_var_desc)
            # w_var_desc.textChanged[str].connect(self.custom_data_desc_changed)  # being explicit about passing a string 

        # self.main_layout.addWidget(QLabel("(Note: we do not currently validate Type and Value)"))
        self.main_layout.addWidget(QLabel("(Note: validation check performed at Save or Run)"))
        self.main_layout.addWidget(self.utable)


        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("click row # to "))
        delete_row_btn = QPushButton("Delete")
        delete_row_btn.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        delete_row_btn.setFixedWidth(100)
        delete_row_btn.clicked.connect(self.delete_user_param_cb)
        hlayout.addWidget(delete_row_btn)
        hlayout.addStretch()
        self.main_layout.addLayout(hlayout)


        #==================================================================
        self.user_params.setLayout(self.main_layout)

        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area.setWidget(self.user_params)

        self.layout = QVBoxLayout(self)

        self.layout.addLayout(controls_hbox)
        self.layout.addWidget(self.scroll_area)

    #--------------------------------------------------------
    def add_row_utable(self, row_num):
        self.utable.insertRow(row_num)

        # self.var_icol_name = 0  # Name
        # self.var_icol_type = 1  # type combobox
        # self.var_icol_value = 2  # Value
        # self.var_icol_units = 3  # Units
        # self.var_icol_desc = 4  # Description
        for irow in [row_num]:
            # print("=== add_row_custom_table(): irow=",irow)
            # ------- name
            w_varname = MyQLineEdit()
            w_varname.setFrame(False)
            rx_valid_varname = QtCore.QRegExp("^[a-zA-Z][a-zA-Z0-9_]+$")
            name_validator = QtGui.QRegExpValidator(rx_valid_varname )
            w_varname.setValidator(name_validator)

            self.utable.setCellWidget(irow, self.var_icol_name, w_varname)   # 1st col
            w_varname.vname = w_varname  
            w_varname.wrow = irow
            w_varname.wcol = self.var_icol_name
            # w_varname.textChanged[str].connect(self.name_changed_cb)  # being explicit about passing a string 

            # ------- type
            w_var_type = MyQComboBox()
            # w_var_type.setStyleSheet(self.checkbox_style)
            # w_var_type.setFrame(False)
            w_var_type.vname = w_varname  
            w_var_type.wrow = irow
            w_var_type.wcol = self.var_icol_type
            # w_var_type.clicked.connect(self.var_type_clicked)

            # w_var_type.setStyleSheet("color: #000000; background-color: #FFFFFF;")
            # w_var_type.setFixedWidth(450)
            # w_var_type.currentIndexChanged.connect(self.cycle_changed_cb)
            w_var_type.addItem("double")
            w_var_type.addItem("int")
            w_var_type.addItem("bool")
            w_var_type.addItem("string")

            self.utable.setCellWidget(irow, self.var_icol_type, w_var_type)
            # self.type.append(w_var_type)

            # ------- value
            w_varval = MyQLineEdit()
            w_varval.setFrame(False)
            w_varval.vname = w_varname  
            w_varval.wrow = irow
            w_varval.wcol = self.var_icol_value
            # w_varval.setValidator(QtGui.QDoubleValidator())
            self.utable.setCellWidget(irow, self.var_icol_value, w_varval)
            # w_varval.textChanged[str].connect(self.value_changed_cb)  # being explicit about passing a string 

            # ------- units
            w_var_units = MyQLineEdit()
            w_var_units.setFrame(False)
            w_var_units.setFrame(False)
            w_var_units.vname = w_varname  
            w_var_units.wrow = irow
            w_var_units.wcol = self.var_icol_units
            self.utable.setCellWidget(irow, self.var_icol_units, w_var_units)
            # w_var_units.textChanged[str].connect(self.units_changed_cb)  # being explicit about passing a string 

            # ------- description
            w_var_desc = MyQLineEdit()
            w_var_desc.setFrame(False)
            w_var_desc.vname = w_varname  
            w_var_desc.wrow = irow
            w_var_desc.wcol = self.var_icol_desc
            self.utable.setCellWidget(irow, self.var_icol_desc, w_var_desc)
            # w_var_desc.textChanged[str].connect(self.desc_changed_cb)  # being explicit about passing a string 

    #--------------------------------------------------------
    # rf. def delete_custom_data_cb(self):
    def delete_user_param_cb(self, s):
        debug_me = True
        row = self.utable.currentRow()
        # print("------------- delete_user_param_cb(), row=",row)  # = -1

        try:
            varname = self.utable.cellWidget(row,self.var_icol_name).text()
        except:
            return
        if debug_me:
            print("------------- delete_user_param_cb(), row=",row)
            print("    var name= ",varname)

        # Since each widget in each row had an associated row #, we need to decrement all those following
        # the row that was just deleted.
        for irow in range(row, self.max_rows):
            # print("---- decrement wrow in irow=",irow)
            self.utable.cellWidget(irow,self.var_icol_name).wrow -= 1  # sufficient to only decr the "name" column

        self.utable.removeRow(row)

        # self.add_row_utable(self.max_rows - 1)
        self.add_row_utable(self.count - 1)

        # self.enable_all_custom_data()
        if varname == "random_seed":
            self.xml_creator.config_tab.random_seed_warning_label.hide_icon()
    #----------------------------------------
    # Not currently used
    def disable_table_cells_for_duplicate_name(self, widget=None):
        backcolor = "background: lightgray"
        for irow in range(0,self.max_rows):
            for icol in range(self.max_cols):
                self.utable.cellWidget(irow,icol).setEnabled(False)
                self.utable.cellWidget(irow,icol).setStyleSheet(backcolor)   # yellow
                # self.sender().setStyleSheet("color: red;")

        if widget:   # enable only(!) the widget that needs to be fixed (because it's a duplicate)
            wrow = widget.wrow
            wcol = widget.wcol
            self.utable.cellWidget(wrow,wcol).setEnabled(True)
            # self.custom_data_table.setCurrentItem(None)
            backcolor = "background: white"
            self.utable.cellWidget(wrow,wcol).setStyleSheet(backcolor)
            self.utable.setCurrentCell(wrow,wcol)

        # Also disable the cell type tree
        # self.tree.setEnabled(False)

    #----------------------------------------
    # Not currently used
    def enable_entire_table(self):
        # for irow in range(self.max_custom_vars):
        # for irow in range(self.max_custom_rows_edited):
        backcolor = "background: white"
        print("------ enable_entire_table() for ",self.max_rows,self.max_cols)
        for irow in range(self.max_rows):
            for icol in range(self.max_cols):
                # if (icol != 2) and (irow != row) and (icol != col):
                # if irow > 47:
                    # print("enable all(): irow,icol=",irow,icol)
                # if self.custom_data_table.cellWidget(irow,icol):
                self.utable.cellWidget(irow,icol).setEnabled(True)
                self.utable.cellWidget(irow,icol).setStyleSheet(backcolor)
                # if icol == 2:
                #     self.utable.cellWidget(irow,icol).setStyleSheet(self.checkbox_style)
                # else:
                    # print("oops!  self.custom_data_table.cellWidget(irow,icol) is None")
                # self.sender().setStyleSheet("color: red;")

        # self.custom_data_table.cellWidget(self.max_custom_rows_edited+1,0).setEnabled(True)
        # self.custom_data_table.cellWidget(self.max_custom_rows_edited+1,0).setStyleSheet("background: white")

        # self.tree.setEnabled(True)

    #--------------------------------------------------------
    def search_user_param_cb(self, s):
        if not s:
            s = 'thisisadummystring'

        # print("---search_user_param_cb()")
        for irow in range(self.max_rows):
            if s in self.utable.cellWidget(irow,self.var_icol_name).text():
                # print(f"   found {s} at row {irow}")
                backcolor = "background: bisque"
                self.utable.cellWidget(irow,self.var_icol_name).setStyleSheet(backcolor)
                # self.custom_data_table.selectRow(irow)  # don't do this; keyboard input -> cell 
            else:
                backcolor = "background: white"
                self.utable.cellWidget(irow,self.var_icol_name).setStyleSheet(backcolor)
            # self.custom_data_table.setCurrentItem(item)d


    #----------------------------------------------------------------------
    def utable_error(self,row,col,msg):
        # if self.custom_data_table.cellWidget(row,col).text()  == '0':
            # return
        msgBox = QMessageBox()
        msgBox.setTextFormat(Qt.RichText)
        msgBox.setText(msg)
        msgBox.setStandardButtons(QMessageBox.Ok)
        returnValue = msgBox.exec()

    #----------------------------------------
    def validate_utable(self):

        # check for duplicate names
        found = set()
        # dupes = [x for x in self.param_d.keys() if x in found or found.add(x)]
        dupes = []
        for idx in range(self.max_rows):
            vname = self.utable.cellWidget(idx,self.var_icol_name).text()
            if len(vname) == 0:
                continue
            if vname in found:
                dupes.append(vname)
            else:
                found.add(vname)
        # print("------validate_utable(): Error: duplicate names=",dupes)

        if dupes:
            msg = f"Error: Duplicate User Params: {dupes}.<br><br>XML will not be saved. Please fix before continuing."
            self.utable_error(0,0,msg)
            return False

        #--------------------------
        # validate doubles
        bad_val = []
        for idx in range(self.max_rows):
            vname = self.utable.cellWidget(idx,self.var_icol_name).text()
            if len(vname) == 0:
                continue
            v_type = self.utable.cellWidget(idx,self.var_icol_type).currentText()
            # print("v_type= ",v_type)
            if v_type == "double":
                val_str = self.utable.cellWidget(idx,self.var_icol_value).text()
                try:
                    float(val_str)
                except ValueError:
                    bad_val.append([vname,val_str])
                    # pass

        if bad_val:
            msg = f"Error: Invalid [user param, double value]: {bad_val}.<br><br>XML will not be saved. Please fix User Params before continuing."
            self.utable_error(0,0,msg)
            return False

        #--------------------------
        # validate int values
        # print("---- validate ints")
        bad_val = []
        for idx in range(self.max_rows):
            vname = self.utable.cellWidget(idx,self.var_icol_name).text()
            if len(vname) == 0:
                continue
            v_type = self.utable.cellWidget(idx,self.var_icol_type).currentText()
            # print("v_type= ",v_type)
            if v_type == "int":
                val_str = self.utable.cellWidget(idx,self.var_icol_value).text()
                # print("  val_str=",val_str)
                try:
                    if float(val_str).is_integer():
                        continue
                    else:
                        bad_val.append([vname,val_str])
                except:
                    bad_val.append([vname,val_str])

        if bad_val:
            msg = f"Error: Invalid [user param, int value]: {bad_val}.<br><br>XML will not be saved. Please fix User Params before continuing."
            self.utable_error(0,0,msg)
            return False

        #--------------------------
        # validate bool values
        # print("---- validate bools")
        bad_val = []
        for idx in range(self.max_rows):
            vname = self.utable.cellWidget(idx,self.var_icol_name).text()
            if len(vname) == 0:
                continue
            v_type = self.utable.cellWidget(idx,self.var_icol_type).currentText()
            # print("v_type= ",v_type)
            if v_type == "bool":
                # continue
                val_str = self.utable.cellWidget(idx,self.var_icol_value).text()
                # print("  val_str=",val_str)
                if (val_str.lower() == "true")  or (val_str.lower() == "false"):
                    continue
                else:
                    bad_val.append([vname,val_str])
                    # print("  bad_val=",bad_val)
                    # pass

        if bad_val:
            msg = f"Error: Invalid [user param, bool value]: {bad_val}.<br><br>XML will not be saved. Please fix User Params before continuing. A bool value is either True or False."
            self.utable_error(0,0,msg)
            return False



        return True

    #----------------------------------------
    def name_changed_cb(self, text):
        wrow = self.sender().wrow
        # print(f"----- name_changed_cb():  wrow={wrow}, self.count={self.count}, text={text}")

        # check for duplicate name
        # for idx in range(self.max_rows):
        #     vname = self.utable.cellWidget(idx,self.var_icol_name).text()
        #     if text == vname:
        #         print("duplicate name  ",idx, ") ",self.utable.cellWidget(idx,self.var_icol_name).text())
        #         # self.disable_table_cells_for_duplicate_name()
        #         # self.disable_table_cells_for_duplicate_name(self.sender())
        #         # self.table_disabled = True
        #         # print("--------- 1) leave function")
        #         return  # --------- leave function


        # self.enable_entire_table()

        N = 10
        # If we're at the last row, add N(=10) more rows to the table.
        if wrow == self.count - 1:
            # print("       at last row, add more")
            # print("add 10 rows")
            for ival in range(N):
                self.add_row_utable(self.count + ival)
            self.count += N

    def name_change_finished_cb(self):
        if self.sender().text()=="random_seed":
            self.xml_creator.config_tab.random_seed_warning_label.show_icon()

    #----------------------------------------
    def units_changed_cb(self, text):
        debug_me = False
        # logging.debug(f'\n--------- units_changed_cb: -------')
        if debug_me:
            print(f'units_changed_cb(): ----  text= {text}')

        # print("self.sender().wrow = ", self.sender().wrow)
        varname = self.sender().vname.text()
        if debug_me:
            print("    varname= ",varname)
        wrow = self.sender().wrow
        wcol = self.sender().wcol

        # self.user_params_edit_active = True
        # if len(varname) == 0 and self.user_params_edit_active:
        #     self.utable_error(wrow,wcol,"(#3) Define Name first!")
        #     # for line in traceback.format_stack():
        #     #     print(line.strip())
        #     # self.custom_data_table.cellWidget(wrow,wcol).setText(self.custom_var_value_str_default)
        #     return

        # print(f"-------   its varname is {varname}")
        # if varname not in self.master_custom_var_d.keys():
        #     self.master_custom_var_d[varname] = [wrow, '', '']   # [wrow, units, desc]
        # self.master_custom_var_d[varname][1] = text   # hack, hard-coded
        # print("self.master_custom_var_d[varname]= ",self.master_custom_var_d[varname])

    #--------------------------------------------------------
    # @QtCore.Slot()
    # def clear_rows_cb(self):
    #     # print("----- clearing all selected rows")
    #     for idx in range(self.count):
    #         if self.select[idx].isChecked():
    #             self.name[idx].clear()
    #             self.type[idx].setCurrentIndex(0)  # double
    #             self.value[idx].clear()
    #             self.units[idx].clear()
    #             self.description[idx].clear()
    #             self.select[idx].setChecked(False)

    #--------------------------------------------------------
    def clear_gui(self):
        for idx in range(self.max_rows):
            self.utable.cellWidget(idx,self.var_icol_name).setText('')
            self.utable.cellWidget(idx,self.var_icol_type).setCurrentIndex(0)   # hard-code: "double" combobox item
            self.utable.cellWidget(idx,self.var_icol_value).setText('')
            self.utable.cellWidget(idx,self.var_icol_units).setText('')
            self.utable.cellWidget(idx,self.var_icol_desc).setText('')

    #--------------------------------------------------------
    # populate the GUI tab with what is in the .xml
    def fill_gui(self):
        logging.debug(f'\n\n------------  user_params_tab: fill_gui --------------')
        # print(f'\n\n------------  user_params_tab: fill_gui --------------')
        # pass
        uep_user_params = self.xml_root.find(".//user_parameters")

        if uep_user_params is None:
            return

        idx = 0
        # rwh/TODO: if we have more vars than we initially created rows for, we'll need
        # to call 'append_more_cb' for the excess.

        for var in uep_user_params:
            self.utable.cellWidget(idx,self.var_icol_name).setText(var.tag)
            self.utable.cellWidget(idx,self.var_icol_value).setText(var.text)

            if 'type' in var.keys():
                if "divider" in var.attrib['type']:  # just for visual separation in Jupyter notebook
                    continue

                # select appropriate dropdown/combobox item (double, int, bool, text)
                elif "double" in var.attrib['type']:
                    self.utable.cellWidget(idx,self.var_icol_type).setCurrentIndex(0)
                elif "int" in var.attrib['type']:
                    self.utable.cellWidget(idx,self.var_icol_type).setCurrentIndex(1)
                elif "bool" in var.attrib['type']:
                    self.utable.cellWidget(idx,self.var_icol_type).setCurrentIndex(2)
                else:
                    self.utable.cellWidget(idx,self.var_icol_type).setCurrentIndex(3)
            else:  # default 'double'
                self.utable.cellWidget(idx,self.var_icol_type).setCurrentIndex(0)

            if 'units' in var.keys():
                self.utable.cellWidget(idx,self.var_icol_units).setText(var.attrib['units'])
            if 'description' in var.keys():
                self.utable.cellWidget(idx,self.var_icol_desc).setText(var.attrib['description'])

            idx += 1

    #--------------------------------------------------------
    # Generate the .xml to reflect changes in the GUI
    def fill_xml(self):
        logging.debug(f'\n--------- user_params_tab.py:  fill_xml(): self.count = {self.count}')
        print(f'\n--------- user_params_tab.py:  fill_xml(): self.count = {self.count}')
        uep = self.xml_root.find('.//user_parameters')
        if uep:
            logging.debug(f'--------- found //user_parameters')
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
        elm = None
        try:
            for idx in range(self.count):
                # vname = self.name[idx].text()
                v_name = self.utable.cellWidget(idx,self.var_icol_name).text()
                # print(idx,")", v_name)
                v_type = self.utable.cellWidget(idx,self.var_icol_type).currentText()
                v_value = self.utable.cellWidget(idx,self.var_icol_value).text()
                v_units = self.utable.cellWidget(idx,self.var_icol_units).text()
                v_desc = self.utable.cellWidget(idx,self.var_icol_desc).text()
                if v_name:  # only deal with rows having names
                    logging.debug(f'{v_name}')
                    # elm = ET.Element(vname, 
                    #     {"type":self.type[idx].currentText(), 
                    #      "units":self.units[idx].text(),
                    #      "description":self.description[idx].text()})
                    elm = ET.Element(v_name, 
                        {"type":v_type, 
                        "units":v_units,
                        "description":v_desc})
                    # elm = ET.Element(vname, { "units":self.units[idx]})
                    # elm = ET.Element(vname)
                    # elm.text = self.value[idx].text()
                    elm.text = v_value
                    elm.tail = '\n        '
                    uep.insert(knt,elm)
                    knt += 1
            if elm:
                elm.tail = '\n    '
            logging.debug(f'found {knt}')

        except:
            msg = f"Error saving user params: idx={idx}, w(col 0)={self.utable.cellWidget(idx,self.var_icol_name)}"
            self.utable_error(idx,0,msg)