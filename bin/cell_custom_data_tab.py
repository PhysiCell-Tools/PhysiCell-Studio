"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)

"""

import sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDoubleValidator

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

# Overloading the QLineEdit widget to let us map it to its variable name. Ugh.
class MyQLineEdit(QLineEdit):
    # prev_vname = None  # previous variable name (before changed)
    vname = None  # variable name
    idx = None  # index

class CellCustomData(QWidget):
    def __init__(self):
        super().__init__()

        # self.current_param = None
        self.xml_root = None
        self.celldef_tab = None
        self.count = 0
        self.max_rows = 99  # initially
        self.max_entries = self.max_rows
        # self.max_entries = -1
        # self.custom_vars_to_delete = []
        # self.prev_cd = {}  # previous (backup) copy of name:value (where value = [idx,val])
        self.prev_cd = []  # previous (backup) copy of [name,value] (access via list index)
        self.num_var = 0

        #-------------------------------------------
        self.label_width = 150
        self.units_width = 90

        self.scroll_area = QScrollArea()
        # splitter.addWidget(self.scroll)
        # self.cell_def_horiz_layout.addWidget(self.scroll)

        self.custom_data_params = QWidget()
        self.main_layout = QVBoxLayout()
        # self.main_layout.addStretch(0)

        #------------------
        controls_hbox = QHBoxLayout()

        self.update_button = QPushButton("Update Cell Types")
        controls_hbox.addWidget(self.update_button)
        self.update_button.clicked.connect(self.update_cb)

        # self.clear_button = QPushButton("Clear selected rows")
        # controls_hbox.addWidget(self.clear_button)
        # self.clear_button.clicked.connect(self.clear_rows_cb)

        # self.new_button = QPushButton("New")
        self.new_button = QPushButton("Append 5 more rows")
        controls_hbox.addWidget(self.new_button)
        self.new_button.clicked.connect(self.append_more_cb)

        # self.copy_button = QPushButton("Copy")
        # controls_hbox.addWidget(self.copy_button)

        #------------------
		# <random_seed type="int" units="dimensionless">0</random_seed> 
		# <cargo_signal_D type="double" units="micron/min^2">1e3</cargo_signal_D>

        # Fixed names for columns:
        hbox = QHBoxLayout()

        col1 = QLabel("Name (required)")
        col1.setAlignment(QtCore.Qt.AlignCenter)
        hbox.addWidget(col1)
        # col2 = QLabel("Type")
        # col2.setAlignment(QtCore.Qt.AlignCenter)
        # hbox.addWidget(col2)
        col3 = QLabel("Default Value (floating point)")
        col3.setAlignment(QtCore.Qt.AlignCenter)
        hbox.addWidget(col3)
        col4 = QLabel("Units")
        col4.setFixedWidth(self.units_width)
        col4.setAlignment(QtCore.Qt.AlignCenter)
        hbox.addWidget(col4)
        # label.setFixedWidth(180)
        self.main_layout.addLayout(hbox)

        #------------------

        # Create lists for the various input boxes
        # self.select = []
        self.name = []
        # self.type = []
        self.value = []
        self.units = []
        self.description = []

        # self.type_dropdown = QComboBox()
        # self.type_dropdown.setFixedWidth(300)
        # # self.type_dropdown.currentIndexChanged.connect(self.cycle_changed_cb)
        # self.type_dropdown.addItem("int")
        # self.type_dropdown.addItem("double")
        # self.type_dropdown.addItem("bool")
        # self.type_dropdown.addItem("text")

        for idx in range(self.max_rows):  # TODO: mismatch with # rows in Cell Types|Custom Data may cause problems.
            # self.main_layout.addLayout(NewUserParam(self))
            hbox = QHBoxLayout()

            # w = QCheckBox("")
            # w.setEnabled(False)
            # self.select.append(w)
            # hbox.addWidget(w)

            # Need to distinguish between editing an existing name, read in from .xml, and creating a new one.
            w_varname = MyQLineEdit()
            # rx_valid_varname = QtCore.QRegExp("^[a-zA-Z0-9_]+$")
            rx_valid_varname = QtCore.QRegExp("^[a-zA-Z][a-zA-Z0-9_]+$")
            name_validator = QtGui.QRegExpValidator(rx_valid_varname )
            w_varname.setValidator(name_validator)

            self.name.append(w_varname)
            w_varname.vname = w_varname  # ??
            w_varname.idx = idx

            # crucial/warning: this "connect" callback can be tricky
            w_varname.textChanged[str].connect(self.custom_data_name_changed)  # being explicit about passing a string 
            # self.diffusion_coef.enter.connect(self.save_xml)
            hbox.addWidget(w_varname)
            # if idx == 0:
            #     w.setText("random_seed")

            # w = QComboBox()
            # # xml2jupyter: {"double":"FloatText", "int":"IntText", "bool":"Checkbox", "string":"Text", "divider":""}
            # w.addItem("double")
            # w.addItem("int")
            # w.addItem("bool")
            # w.addItem("string")
            # if idx == 0:
            #     w.setCurrentIndex(1)
            # self.type.append(w)
            # hbox.addWidget(w)

            w = MyQLineEdit()
            w.setReadOnly(True)
            w.setValidator(QtGui.QDoubleValidator())
            w.setText("0.0")
            w.vname = w_varname
            w.idx = idx
            w.textChanged[str].connect(self.custom_data_value_changed)  # being explicit about passing a string 
            self.value.append(w)
            # if idx == 0:
            #     w.setText("0")
            hbox.addWidget(w)

            w = QLineEdit()
            w.setReadOnly(True)
            w.setFixedWidth(self.units_width)
            self.units.append(w)
            hbox.addWidget(w)

            # units = QLabel("micron^2/min")
            # units.setFixedWidth(units_width)
            # hbox.addWidget(units)
            self.main_layout.addLayout(hbox)

            #-----
            hbox = QHBoxLayout()
            w = QLabel("      Description:")
            hbox.addWidget(w)

            w = QLineEdit()
            self.description.append(w)
            w.setReadOnly(True)
            hbox.addWidget(w)
            # w.setStyleSheet("background-color: lightgray")
            # w.setStyleSheet("background-color: #e4e4e4")
            self.main_layout.addLayout(hbox)

            #-----
            # self.vbox.addLayout(hbox)
            self.count = self.count + 1
            # print(self.count)


        #==================================================================
        self.custom_data_params.setLayout(self.main_layout)

        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area.setWidget(self.custom_data_params)

        self.layout = QVBoxLayout(self)

        self.layout.addLayout(controls_hbox)

        warning1 = QLabel("                                        After making edits, click Update Cell Types.")
        warning1.setStyleSheet('color: red;')  # “background-color: cyan”
        self.layout.addWidget(warning1)
        warning2 = QLabel("                                        Changing a default value here will also change it in each Cell Type.")
        warning2.setStyleSheet('color: red;')  # “background-color: cyan”
        self.layout.addWidget(warning2)
        self.layout.addWidget(self.scroll_area)

    # --- (rf. Release 1.3 for fancier/buggier approach)
    def custom_data_name_changed(self, text):
        # print("--------- (master) custom_data tab: custom_data_name_changed() --------")

        # # print("self.sender() = ", self.sender())
        vname = self.sender().vname.text()
        idx = self.sender().idx
        # prev_vname = self.celldef_tab.custom_data_name[idx].text()
        # print("custom_data_name_changed(): prev_vname = ",prev_vname)
        # # print("(master) prev_vname = ", self.sender().prev_vname)
        # print("(master) vname = ", vname)
        # print("(master) idx = ", idx)
        # print("(master) custom_data_name_changed(): text = ", text)
        # print()

        # New, manual way (Sep 2021): once a user enters a new name for a custom var, enable its other fields.
        # self.select[idx].setEnabled(True)
        # print("len(vname) = ",len(vname))
        if len(vname) > 0:
            self.value[idx].setReadOnly(False)
            self.units[idx].setReadOnly(False)
            self.description[idx].setReadOnly(False)

            self.name[idx+1].setReadOnly(False)   # Crucial: enable the *next* var name slot as writable!
            # print("\n------- Enabling row (name) # ",idx+1, "as editable.")
            if idx > self.max_entries:
                self.max_entries = idx
                # print("\n------- resetting max_entries = ",self.max_entries)
        else:
            # print("len(vname) = 0, setting fields readonly")
            self.value[idx].setReadOnly(True)
            self.units[idx].setReadOnly(True)
            self.description[idx].setReadOnly(True)

            # self.name[idx+1].setReadOnly(True)

        # # Update the value in all Cell Types|Custom Data
        # num_cell_defs = self.celldef_tab.tree.invisibleRootItem().childCount()
        # # print("  num_cell_defs =",num_cell_defs )
        # for k in self.celldef_tab.param_d.keys():   # for all cell types
        #     # mydict[k_new] = mydict.pop(k_old)

        #     # rwh - debug overwriting var names with shared root, e.g.: foo, foo2
        #     if len(prev_vname) > 0:
        #         print("updating: prev_vname=",prev_vname,", vname=",vname)
        #         if prev_vname in self.celldef_tab.param_d[k]['custom_data']:
        #             self.celldef_tab.param_d[k]['custom_data'][vname] = self.celldef_tab.param_d[k]['custom_data'].pop(prev_vname)
        #         print("post-updating: ",self.celldef_tab.param_d[k]['custom_data'])
        #     else:  # adding a new one
        #         self.celldef_tab.param_d[k]['custom_data'][vname] = "0.0"
        #         self.celldef_tab.custom_data_value[idx].setText("0.0")
        #         self.celldef_tab.custom_data_count += 1

        #     # NO! will create a new var for *each* character as it's entered, ugh.
        #     # self.celldef_tab.param_d[k]['custom_data'][vname] = "0.0"
        #     # self.celldef_tab.custom_data_value[idx].setText("0.0")
        #     # self.celldef_tab.custom_data_count += 1

        # #     self.celldef_tab.param_d[k]['custom_data'][vname] = text
        # #     print(" ===>>> ",k, " : ", self.celldef_tab.param_d[k])

        #     self.celldef_tab.custom_data_name[idx].setText(vname)
        # #     print()

        # for k in self.celldef_tab.param_d.keys():   # for all cell types
        #     if '' in self.celldef_tab.param_d[k]['custom_data']:
        #         self.celldef_tab.param_d[k]['custom_data'].pop('')


    # --- custom data (rwh: OMG, this took a lot of time to solve!)
    def custom_data_value_changed(self, text):
        # print("--------- (master) custom_data tab: custom_data_value_changed() --------")
        # print("self.sender() = ", self.sender())
        vname = self.sender().vname.text()
        idx = self.sender().idx
        # print("(master) vname = ", vname)
        # print("(master) idx = ", idx)
        # print("(master) custom_data_value_changed(): text = ", text)
        # print()

        # Update the value in all Cell Types|Custom Data
        # num_cell_defs = self.celldef_tab.tree.invisibleRootItem().childCount()
        # # print("  num_cell_defs =",num_cell_defs )
        # for k in self.celldef_tab.param_d.keys():   # for all cell types
        #     self.celldef_tab.param_d[k]['custom_data'][vname] = text
        #     # print(" ===>>> ",k, " : ", self.celldef_tab.param_d[k])

        #     self.celldef_tab.custom_data_value[idx].setText(text)
        #     # print()


        # populate: self.param_d[cell_def_name]['custom_data'] =  {'cvar1': '42.0', 'cvar2': '0.42', 'cvar3': '0.042'}
        # self.param_d[self.current_cell_def]['custom_data']['cvar1'] = text
        # self.param_d[self.current_cell_def]['custom_data'][vname] = text
        # print(self.param_d[self.current_cell_def]['custom_data'])


    # Keep a copy of the previous custom data entries to compare againts newly edited ones
    def update_prev_cd(self):
        # self.prev_cd = {}  # previous (backup) copy of name:value
        print(">>>> ------- entering update_prev_cd():  --------------------------")
        # print("     original self.prev_cd = :",self.prev_cd)
        # print("prev vals:")
        # for k in self.prev_cd.keys():
            # print(k,self.prev_cd[k])
        # idx = 0
        # for elm in self.prev_cd:
        #     print(idx,elm)
        #     idx += 1

        # print("   (update_prev_cd())        new vals:")
        self.num_var = 0
        for idx in range(self.max_entries):
            # crucial/warning: this triggers custom_data_name_changed()
            var_name = self.name[idx].text()
            if len(var_name) > 0:
                self.num_var += 1
                var_val = self.value[idx].text()
                # print('idx = ',idx)
                # print(var_name,' = ',var_val)
                # self.prev_cd[var_name] = var_val
                # self.prev_cd[var_name] = [idx,var_val]
                if idx < len(self.prev_cd):
                    self.prev_cd[idx] = [var_name,var_val]
                else:
                    var_name_exists = False
                    # for jdx in range(0,self.max_entries):
                    for jdx in range(len(self.prev_cd)):
                        # print("jdx = ",jdx, ", max_entries=",self.max_entries)
                        # print("jdx = ",jdx)
                        # if jdx+1 > len(self.prev_cd):
                        # # if jdx+1 > self.max_entries:
                        #     break
                        # print("compare ",var_name, " against ",self.prev_cd[jdx][0])
                        if self.prev_cd[jdx][0] == var_name:
                            var_name_exists = True
                            # print(" FOUND IT!!")

                    if not var_name_exists:
                        self.prev_cd.append([var_name,var_val])
                        # print("     appended new val, self.prev_cd = :",self.prev_cd)

                    # print("\n update_prev_cd():")
                    # print("     idx= ",idx, ", self.max_entries= ",self.max_entries)
                    # print("     appended new val, self.prev_cd = :",self.prev_cd)
        # print("        self.num_var = ",self.num_var)

        # Disable all rows after the last one + 1
        # for idx in range(self.num_var+1,self.count):
        row_start = self.num_var + 1
        if self.max_entries != self.max_rows:
            row_start = self.max_entries + 1
        # row_start = self.num_var + 1
        # print("update_prev_cd():  going to disable rows in range(",row_start, ",",self.count,")")
        # print("update_prev_cd():  and max_entries = ",self.max_entries)
        for idx in range(row_start,self.count):
            self.name[idx].setReadOnly(True)  # Crucial/beware...
            self.value[idx].setReadOnly(True)
            self.units[idx].setReadOnly(True)
            self.description[idx].setReadOnly(True)

        # print("\n\n>>>> ------- leaving update_prev_cd():  --------------------------")


    def find_duplicates(self,listOfElems):
        name_dict = dict()
        for elem in listOfElems:
            if elem in name_dict:
                name_dict[elem] += 1
            else:
                name_dict[elem] = 1    
    
        name_dict = { key:value for key, value in name_dict.items() if value > 1}
        return name_dict


    def duplicate_names_popup(self, dups_dict):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("You have duplicate names and need to resolve them: "+ str(dups_dict))
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        returnValue = msgBox.exec()
        if returnValue == QMessageBox.Ok:
            print('OK clicked')


#------------------------------
    # Update all Cell Types(tab):Custom Data(subtab) entries with changes made in this tab
    # @QtCore.Slot()
    def update_cb(self):
        print("===========  update_cb(): self.max_entries = ",self.max_entries, "  ============")

        # check for duplicate names
        names = []
        for idx in range(self.count):
            var_name = self.name[idx].text()
            if len(var_name) > 0:
                names.append(var_name)

        dups_d = self.find_duplicates(names)
        # print("len(dups_d) = ", len(dups_d))
        # print("dups_d = ", dups_d)
        if len(dups_d) > 0:
            print("\n\n==========  You have duplicate named custom data and need to fix.\n\n ")
            self.duplicate_names_popup(dups_d)
            return

        # for idx in range(self.count):
        for idx in range(self.max_entries+1):
            # crucial/warning: this triggers custom_data_name_changed()
            var_name = self.name[idx].text()

            if len(var_name) > 0:
                var_val = self.value[idx].text()
                # print(var_name,' = ',var_val)
                # print("    self.prev_cd= ",self.prev_cd)
                # print("    var_name = ",var_name,", self.prev_cd.keys()= ",self.prev_cd.keys())
                # print("    var_val = ",var_val)

                if (idx+1) > len(self.prev_cd):
                    # print("\n======= handling: idx+1 = ",idx+1, " > len(self.prev_cd): ",self.prev_cd)
                    var_name_exists = False
                    for jdx in range(0,self.max_entries):
                        # print("jdx = ",jdx)
                        if jdx+1 > len(self.prev_cd):
                            break
                        if self.prev_cd[jdx][0] == var_name:
                            var_name_exists = True
                    if not var_name_exists:
                        # print("    ------------ handle brand new var_val (ALL cell types are changed): ",var_name)
                        self.prev_cd.append([var_name, var_val])
                        # print("    -- after append: self.prev_cd= ",self.prev_cd)
                        self.max_entries = idx+1  # let's NOT do this?
                    # print("    --  self.max_entries",self.max_entries)

                    for k in self.celldef_tab.param_d.keys():   # for each cell type (in Cell Types tab)
                        # print("     (1) changing k: ",k,": ",var_name, ", now --> ",var_val)
                        # change var name to be new one
                        if var_name in self.celldef_tab.param_d[k]['custom_data'].keys():
                            pass
                        else:
                            self.celldef_tab.param_d[k]['custom_data'][var_name] = var_val    # BEWARE! FIX this!

                # if the var_name and var_val is unchanged from prev_cd, do nothing. 
                # if (var_name in self.prev_cd.keys()) and (var_val == self.prev_cd[var_name]):
                elif (var_name == self.prev_cd[idx][0]) and (var_val == self.prev_cd[idx][1]):
                    continue
                elif (var_name != self.prev_cd[idx][0]) and (var_val == self.prev_cd[idx][1]):
                    # print("    -- handle (only) edited var_name: ",var_name)
                    for k in self.celldef_tab.param_d.keys():   # for each cell type (in Cell Types tab)
                        # change var name to be new one, i.e., replace key in dict
                        self.celldef_tab.param_d[k]['custom_data'][var_name] = self.celldef_tab.param_d[k]['custom_data'].pop(self.prev_cd[idx][0])
                    continue

                # elif (var_name == self.prev_cd[idx][0]):
                # if (var_val != self.prev_cd[idx][1]):
                if idx < len(self.prev_cd) and (var_val != self.prev_cd[idx][1]):
                    # print("\n    -- DEBUG THIS!!  idx=",idx,", var_val=",var_val,", self.prev_cd = ",self.prev_cd) 
                    # print("\n    -- self.prev_cd[idx][1]=",self.prev_cd[idx][1]) 
                    # print("    -- handle edited prev var_val (ALL cell types are changed): ",var_name)
                    # print("    --  update all cell types: ")
                    for k in self.celldef_tab.param_d.keys():   # for each cell type (in Cell Types tab)
                        # change var name to be new one
                        self.celldef_tab.param_d[k]['custom_data'][var_name] = var_val   # Beware! Possible bug!
                        # print("     (2) changing k: ",k,": ",var_name, ", now --> ",var_val)
                    continue

                # otherwise:
                for k in self.celldef_tab.param_d.keys():   # for each cell type (in Cell Types tab)
                    # print("\n  otherwise (for each cell def):")
                    # print("    -- key in celldef_tab.param_d = ",k)
                    # print("    -- self.prev_cd= ",self.prev_cd)

                    # Is the variable name (in each cell def) already in the prev_cd list, and
                    #  is its value unchanged?
                    # if (k in self.prev_cd.keys()) and (self.prev_cd[k] == var_val):
                    # NO! prev_cd is no longer a dict!
                    # if (k in self.prev_cd.keys()) and (self.prev_cd[k] == var_val):
                    #     pass
                    # else:
                    #     print("    !!! -- updating celldef_tab.param_d: ",var_name," -> ",var_val)
                    #     self.celldef_tab.param_d[k]['custom_data'][var_name] = var_val

                    for jdx in range(0,self.max_entries):
                        # print("jdx = ",jdx)
                        if jdx+1 > len(self.prev_cd):
                            break
                        if (self.prev_cd[jdx][0] == var_name) and (self.prev_cd[jdx][1] != var_val):
                            # var_name_exists = True
                            # print(" ~~~~~~   beware: (idx=",idx,") updating celldef_tab.param_d: ",var_name," -> ",var_val)
                            self.celldef_tab.param_d[k]['custom_data'][var_name] = var_val

                    # print(" ~~~~~~   beware: (idx=",idx,") updating celldef_tab.param_d: ",var_name," -> ",var_val)
                    # self.celldef_tab.param_d[k]['custom_data'][var_name] = var_val

            #-------------------------------
            else:   # have 0-length var_name (it was deleted)
                # print("\n\n  0-length var_name:  doing else branch (0-length var_name)")
                # print("    -- idx, len(self.prev_cd) = ", idx, len(self.prev_cd) )
                if idx >= len(self.prev_cd):
                    break
                else:
                    # print("    -- del name off each cell type dict: idx=",idx,", (prev)var_name=",self.prev_cd[idx][0])
                    for k in self.celldef_tab.param_d.keys():  # for each cell type
                        # print("    ---> ", k, ":", self.celldef_tab.param_d[k]['custom_data'])
                        # print("   pre del: ------> ", k, ":", self.celldef_tab.param_d[k]['custom_data'])
                        # self.celldef_tab.param_d[k]['custom_data'].pop(self.prev_cd[0])
                        del self.celldef_tab.param_d[k]['custom_data'][self.prev_cd[idx][0]]
                        # print("     post del: ------> ", k, ":", self.celldef_tab.param_d[k]['custom_data'])

                    self.prev_cd.pop(idx)
                    # print("    -- post popping entry off,  self.prev_cd=",self.prev_cd)


            # self.value[idx].clear()
            # self.value[idx].setText("0.0")
            # self.units[idx].clear()   
            # self.description[idx].clear()
            # self.select[idx].setChecked(False)

        # print("\n======= just before calling  celldef_tab.update_custom_data_params:")
        # for k in self.celldef_tab.param_d.keys():  # for each cell type
        #     print("    ---> ", k, ":", self.celldef_tab.param_d[k]['custom_data'])
        self.celldef_tab.update_custom_data_params()

        self.update_prev_cd()
        # print("\n======= after calling  update_prev_cd():, max_entries=",self.max_entries)
        # self.name[self.max_entries].setReadOnly(False)

        # print("------ update custom vars for each cell def:")
        # for k in self.celldef_tab.param_d.keys():   # for all cell types
        #     # print(self.celldef_tab.param_d[k])
        #     print("--- key: ",k,"\n")
        #     print(self.celldef_tab.param_d[k]['custom_data'])


#   Deprecated (Sep 2021)
    # @QtCore.Slot()
    # def clear_rows_cb(self):
    #     print("\n-------- clear_rows_cb():")
    #     self.custom_vars_to_delete.clear()

    #     # 1st pass
    #     for idx in range(self.count):
    #         if self.select[idx].isChecked():
    #             self.custom_vars_to_delete.append(self.name[idx].text())

    #             # crucial/warning: this triggers custom_data_name_changed()
    #             # self.name[idx].clear()
    #             # # self.value[idx].clear()
    #             # self.value[idx].setText("0.0")
    #             # self.units[idx].clear()   
    #             # self.description[idx].clear()
    #             # self.select[idx].setChecked(False)

    #     print("clear_rows_cb(): self.custom_vars_to_delete = ",self.custom_vars_to_delete)

    #     # rwh/todo: also update all cell types custom data
    #     for k in self.celldef_tab.param_d.keys():   # for all cell types
    #         print("-- celldef custom_data:  ",self.celldef_tab.param_d[k]['custom_data'])
    #         for item in self.custom_vars_to_delete:
    #             print("> delete: ",item)
    #             self.celldef_tab.param_d[k]['custom_data'].pop(item)
    #         # if '' in self.celldef_tab.param_d[k]['custom_data']:
    #             # self.celldef_tab.param_d[k]['custom_data'].pop('')

    #     print("-- celldef custom_data:  ",self.celldef_tab.param_d[k]['custom_data'])

    #     # 2nd pass
    #     for idx in range(self.count):
    #         if self.select[idx].isChecked():
    #             # self.custom_vars_to_delete.append(self.name[idx].text())

    #             # crucial/warning: this triggers custom_data_name_changed()
    #             self.name[idx].clear()
    #             # self.value[idx].clear()
    #             self.value[idx].setText("0.0")
    #             self.units[idx].clear()   
    #             self.description[idx].clear()
    #             self.select[idx].setChecked(False)
    #         # mydict[k_new] = mydict.pop(k_old)

    #     for k in self.celldef_tab.param_d.keys():   # for all cell types
    #         if '' in self.celldef_tab.param_d[k]['custom_data']:
    #             self.celldef_tab.param_d[k]['custom_data'].pop('')

    #         # rwh - debug overwriting var names with shared root, e.g.: foo, foo2
    #         # if len(prev_vname) > 0:
    #         #     print("updating: prev_vname=",prev_vname,", vname=",vname)
    #         #     self.celldef_tab.param_d[k]['custom_data'][vname] = self.celldef_tab.param_d[k]['custom_data'].pop(prev_vname)
    #         #     print("post-updating: ",self.celldef_tab.param_d[k]['custom_data'])
    #         # else:  # adding a new one
    #         #     self.celldef_tab.param_d[k]['custom_data'][vname] = "0.0"
    #         #     self.celldef_tab.custom_data_value[idx].setText("0.0")
    #         #     self.celldef_tab.custom_data_count += 1

    #     # print("post-updating: ",self.celldef_tab.param_d[k]['custom_data'])


    # @QtCore.Slot()
    def append_more_cb(self):
        # print("---- append_more_cb()")
        # self.create_user_param()
        # self.scrollLayout.addRow(NewUserParam(self))
        for idx in range(5):
            # self.main_layout.addLayout(NewUserParam(self))
            hbox = QHBoxLayout()

            # w = QCheckBox("")
            # w.setEnabled(False)
            # self.select.append(w)
            # hbox.addWidget(w)

            w = QLineEdit()
            # rx_valid_varname = QRegExp("('^[ A-Za-z]{1,16}$')")
            rx_valid_varname = QtCore.QRegExp("^[a-zA-Z0-9_]+$")
            name_validator = QtGui.QRegExpValidator(rx_valid_varname )
            w.setValidator(name_validator)
            self.name.append(w)
            hbox.addWidget(w)

            w = QLineEdit()
            w.setReadOnly(True)
            self.value.append(w)
            w.setValidator(QtGui.QDoubleValidator())
            hbox.addWidget(w)

            w = QLineEdit()
            w.setReadOnly(True)
            w.setFixedWidth(self.units_width)
            self.units.append(w)
            hbox.addWidget(w)

            self.main_layout.addLayout(hbox)

            hbox = QHBoxLayout()
            w = QLabel("Desc:")
            hbox.addWidget(w)

            w = QLineEdit()
            w.setReadOnly(True)
            self.description.append(w)
            hbox.addWidget(w)
            # w.setStyleSheet("background-color: lightgray")


            # units = QLabel("micron^2/min")
            # units.setFixedWidth(units_width)
            # hbox.addWidget(units)
            self.main_layout.addLayout(hbox)

            self.count = self.count + 1
            print(self.count)
    #     # self.text.setText(random.choice(self.hello))
    #     pass

    def clear_gui(self, celldef_tab):
        # pass
        for idx in range(self.count):
            self.name[idx].setText("")
            self.value[idx].setText("0.0")
            self.units[idx].setText("")
            self.description[idx].setText("")
        # self.count = 0

        # self.name.clear()
        # self.value.clear()
        # self.units.clear()
        # self.description.clear()

        celldef_tab.clear_custom_data_tab()


    def fill_gui(self, celldef_tab):   # == populate()
        # pass
        uep_custom_data = self.xml_root.find(".//cell_definitions//cell_definition[1]//custom_data")
        print('fill_gui(): uep_custom_data=',uep_custom_data)

        idx = 0
        # rwh/TODO: if we have more vars than we initially created rows for, we'll need
        # to call 'append_more_cb' for the excess.

        # Should we also update the Cell Types | Custom Data tab entries?

        # for idx in range(self.custom_data_count):
        #     self.custom_data_name[idx].setReadOnly(False)
        #     self.custom_data_name[idx].setText("")
        #     self.custom_data_name[idx].setReadOnly(True)

        #     self.custom_data_value[idx].setText("")

        #     self.custom_data_units[idx].setReadOnly(False)
        #     self.custom_data_units[idx].setText("")
        #     self.custom_data_units[idx].setReadOnly(True)

        for var in uep_custom_data:
            # self.select[idx].setEnabled(True)   # enable checkbox

            # print(idx, ") ",var)
            self.name[idx].setText(var.tag)
            # w.setEnabled(False)
            self.name[idx].setEnabled(True)
            # print("tag=",var.tag)

            self.value[idx].setText(var.text)
            self.value[idx].setEnabled(True)

            if 'units' in var.keys():
                self.units[idx].setText(var.attrib['units'])
                self.units[idx].setEnabled(True)

            if 'description' in var.keys():
                self.description[idx].setText(var.attrib['description'])
                self.description[idx].setEnabled(True)
            idx += 1

            self.prev_cd.append([var.tag,var.text])

            # print("custom_data:  fill_gui(): idx=",idx,", count=",self.count)
            if idx > self.count:
                self.append_more_cb()

        self.max_entries = idx
        print('fill_gui(): self.max_entries=',self.max_entries)
        # self.update_prev_cd()

        for idx in range(self.max_entries+1,self.count):
            self.name[idx].setReadOnly(True)  # Crucial/beware...
            self.value[idx].setReadOnly(True)
            self.units[idx].setReadOnly(True)
            self.description[idx].setReadOnly(True)

    # doesn't make sense for this tab; custom_data is saved in XML for each cell type
    # def fill_xml(self):
        # pass
    