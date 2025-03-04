from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QStackedWidget, QGridLayout, QLineEdit, QTabWidget, QTableWidget, QTableWidgetItem, QMessageBox
from studio_classes import QRadioButton_custom, QHLine, QComboBox_custom, CellDefSubTab, QCheckBox_custom, HoverWarning, QLineEdit_custom
from cell_def_tab_param_updates import CellDefParamUpdates

import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html

class CycleTab(CellDefSubTab):
    def __init__(self, celldef_tab):
        super().__init__(parent=celldef_tab)

        self.setStyleSheet("background-color: rgb(236,236,236)")
        self.celldef_param_updates = CellDefParamUpdates(self)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabWidget::pane {border: 0;}")
        # self.tab_widget.setStyleSheet("QTabWidget::pane {background-color: rgb(236,0,0)}")
        # self.tab_widget.setStyleSheet("background-color: rgb(236,0,0)")
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tab_widget)
        self.create_base_cycle_tab()
        self.create_division_function_tab()

        self.tab_widget.addTab(self.base_cycle_widget, "Base")
        self.tab_widget.addTab(self.division_function_widget, "Division Function")

    def create_base_cycle_tab(self):
        self.cycle_duration_flag = False
        self.label_width = 210
        self.fixed_checkbox_column_width = 60
        self.default_time_units = "min"
        self.default_rate_units = "1/min"

        self.stacked_cycle = QStackedWidget()

        self.vbox_cycle = QVBoxLayout()

        #----------------------------
        hbox = QHBoxLayout()
        hbox.setSpacing(0)
        hbox.setContentsMargins(0, 0, 0, 0)
        self.cycle_rb1 = QRadioButton_custom("transition rate(s)      ")
        self.cycle_rb1.toggled.connect(self.cycle_phase_transition_cb)
        hbox.addWidget(self.cycle_rb1)

        self.cycle_rb2 = QRadioButton_custom("duration(s)")
        self.cycle_rb2.toggled.connect(self.cycle_phase_transition_cb)
        hbox.addWidget(self.cycle_rb2)

        hbox.addStretch(1)  # keeps buttons shoved to left (but border still too wide!)
        radio_frame = QFrame()
        radio_frame.setGeometry(QRect(10,10,100,20))
        radio_frame.setStyleSheet("QFrame{ border : 1px solid black; }")
        radio_frame.setLayout(hbox)
        radio_frame.setFixedWidth(250)
        self.vbox_cycle.addWidget(radio_frame)

        # transition rates
        self.stack_trate_live_idx = -1 
        self.stack_trate_Ki67_idx = -1 
        self.stack_trate_advancedKi67_idx = -1 
        self.stack_trate_flowcyto_idx = -1 
        self.stack_trate_flowcytosep_idx = -1 
        self.stack_trate_quiescent_idx = -1 

        # duration rates
        self.stack_duration_live_idx = -1 
        self.stack_duration_Ki67_idx = -1 
        self.stack_duration_advancedKi67_idx = -1 
        self.stack_duration_flowcyto_idx = -1 
        self.stack_duration_flowcytosep_idx = -1 
        self.stack_duration_quiescent_idx = -1 

        #----------------------------
        self.cycle_dropdown = QComboBox_custom()
        self.cycle_dropdown.setFixedWidth(300)
        self.cycle_dropdown.currentIndexChanged.connect(self.cycle_changed_cb)

        self.cycle_dropdown.addItem("live cells")   # 0 -> 0
        self.cycle_dropdown.addItem("basic Ki67")   # 0 -> 1, 1 -> 0
        self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
        self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0
        self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0
        self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0

        self.vbox_cycle.addWidget(self.cycle_dropdown)

        self.cycle_label = QLabel("Phenotype: cycle")
        self.cycle_label.setStyleSheet("background-color: orange")
        self.cycle_label.setAlignment(QtCore.Qt.AlignCenter)

        #-----------------------------
        # We'll create a unique widget to hold different rates or durations, depending
        # on which cycle and method of defining it (transition rates or duration times) is chosen.
        # Then we will only display the relevant one, based on these choices.
        # self.stacked_cycle = QStackedWidget()

        # transition rates
        self.stack_trate_live = QWidget()
        self.stack_trate_Ki67 = QWidget()
        self.stack_trate_advancedKi67 = QWidget()
        self.stack_trate_flowcyto = QWidget()
        self.stack_trate_flowcytosep = QWidget()
        self.stack_trate_quiescent = QWidget()

        # duration times
        self.stack_duration_live = QWidget()
        self.stack_duration_Ki67 = QWidget()
        self.stack_duration_advancedKi67 = QWidget()
        self.stack_duration_flowcyto = QWidget()
        self.stack_duration_flowcytosep = QWidget()
        self.stack_duration_quiescent = QWidget()


        #===========================================================
        #  Naming scheme for sets ("stacks") of cycle widgets:
        #     cycle_<type>_trate<SE>[_changed] (S=start, E=end)
        #     stack_trate_<type>[_idx]
        #
        #     cycle_<type>_duration<SE>[_changed] (S=start, E=end)
        #     stack_duration_<type>[_idx]
        #===========================================================

        #------ Cycle transition rate (live) ----------------------
        self.idx_stacked_widget = 0
        self.build_cycle_layouts("live", 1)
        self.build_cycle_layouts("Ki67", 2)
        self.build_cycle_layouts("advancedKi67", 3)
        self.build_cycle_layouts("flowcyto", 3)
        self.build_cycle_layouts("flowcytosep", 4)
        self.build_cycle_layouts("quiescent", 2)
        self.stacked_cycle.setStyleSheet("QLineEdit { background-color: white }")

        #---------------------------------------------
        # After adding all combos of cycle widgets (groups) to the stacked widget, 
        # add it to this panel.
        self.vbox_cycle.addWidget(self.stacked_cycle)

        self.vbox_cycle.addWidget(QHLine())

        self.reset_cycle_button = QPushButton("Reset to PhysiCell defaults")
        self.reset_cycle_button.setFixedWidth(200)
        self.reset_cycle_button.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        self.reset_cycle_button.clicked.connect(self.reset_cycle_cb)
        self.vbox_cycle.addWidget(self.reset_cycle_button)

        self.vbox_cycle.addStretch()

        self.base_cycle_widget = QWidget()
        self.base_cycle_widget.setLayout(self.vbox_cycle)

    # Called whenever there's a toggle between "transition rate(s)" vs. "duration(S)", or if a
    # different cycle model is chosen from the dropdown combobox.
    def customize_cycle_choices(self):
        if self.cycle_duration_flag:  # specifying duration times (radio button)
            if self.cycle_dropdown.currentIndex() == 0:
                self.stacked_cycle.setCurrentIndex(self.stack_duration_live_idx)
            elif self.cycle_dropdown.currentIndex() == 1:
                self.stacked_cycle.setCurrentIndex(self.stack_duration_Ki67_idx)
            elif self.cycle_dropdown.currentIndex() == 2:
                self.stacked_cycle.setCurrentIndex(self.stack_duration_advancedKi67_idx)
            elif self.cycle_dropdown.currentIndex() == 3:
                self.stacked_cycle.setCurrentIndex(self.stack_duration_flowcyto_idx)
            elif self.cycle_dropdown.currentIndex() == 4:
                self.stacked_cycle.setCurrentIndex(self.stack_duration_flowcytosep_idx)
            elif self.cycle_dropdown.currentIndex() == 5:
                self.stacked_cycle.setCurrentIndex(self.stack_duration_quiescent_idx)

        else:  # specifying transition rates (radio button)
            if self.cycle_dropdown.currentIndex() == 0:
                self.stacked_cycle.setCurrentIndex(self.stack_trate_live_idx)
            elif self.cycle_dropdown.currentIndex() == 1:
                self.stacked_cycle.setCurrentIndex(self.stack_trate_Ki67_idx)
            elif self.cycle_dropdown.currentIndex() == 2:
                self.stacked_cycle.setCurrentIndex(self.stack_trate_advancedKi67_idx)
            elif self.cycle_dropdown.currentIndex() == 3:
                self.stacked_cycle.setCurrentIndex(self.stack_trate_flowcyto_idx)
            elif self.cycle_dropdown.currentIndex() == 4:
                self.stacked_cycle.setCurrentIndex(self.stack_trate_flowcytosep_idx)
            elif self.cycle_dropdown.currentIndex() == 5:
                self.stacked_cycle.setCurrentIndex(self.stack_trate_quiescent_idx)

    def cycle_phase_transition_cb(self):
        radioBtn = self.sender()
        if "duration" in radioBtn.text():
            self.cycle_duration_flag = True
            self.customize_cycle_choices()
        else:  # transition rates
            self.cycle_duration_flag = False
            self.customize_cycle_choices()

        self.celldef_tab.param_d[self.get_current_celldef()]['cycle_duration_flag'] = self.cycle_duration_flag
      
    def cycle_changed_cb(self, idx):
        if self.get_current_celldef() is not None:
            self.celldef_tab.param_d[self.get_current_celldef()]['cycle_choice_idx'] = idx
        self.customize_cycle_choices()

    def build_cycle_layouts(self, base_name, n_phases):
        self.build_cycle_layout(base_name, n_phases, "trate")
        self.build_cycle_layout(base_name, n_phases, "duration")

    def build_cycle_layout(self, base_name, n_phases, suffix):
        units_width = 35
        cycle_base_name = f"cycle_{base_name}" # prepend "cycle_" to match previous name convention
        glayout = QGridLayout()
        for start_phase_index in range(n_phases):
            if start_phase_index == n_phases-1:
                end_phase_index = 0
            else:
                end_phase_index = start_phase_index+1

            base_label_str = f"phase {start_phase_index}->{end_phase_index}"
            label_end_str = "transition rate" if suffix=="trate" else "duration"
            label_str = f"{base_label_str} {label_end_str}"
            label = QLabel(label_str)
            label.setFixedWidth(self.label_width)
            label.setAlignment(QtCore.Qt.AlignRight)
            glayout.addWidget(label, start_phase_index, 0, 1, 1) # w, row, column, rowspan, colspan

            phases_name = f"{cycle_base_name}_{start_phase_index}{end_phase_index}"
            name = f"{phases_name}_{suffix}"
            qle = QLineEdit(objectName=name)
            cb_fn = self.cell_def_pheno_rate_changed if suffix=="trate" else self.cell_def_pheno_duration_changed
            qle.textChanged.connect(cb_fn)
            qle.setValidator(QtGui.QDoubleValidator(bottom=0.0))
            glayout.addWidget(qle, start_phase_index, 1, 1, 2) # w, row, column, rowspan, colspan
            setattr(self, name, qle)

            name_for_cb = f"{phases_name}_fixed"
            fixed_attr_name= f"{name_for_cb}_{suffix}"
            qcb = QCheckBox_custom("Fixed", maximumWidth=self.fixed_checkbox_column_width, objectName=name_for_cb)
            qcb.clicked.connect(self.cell_def_fixed_clicked)
            glayout.addWidget(qcb, start_phase_index, 3, 1, 1) # w, row, column, rowspan, colspan
            setattr(self, fixed_attr_name, qcb)

            units_str = self.default_rate_units if suffix=="trate" else self.default_time_units
            units = QLabel(units_str)
            units.setAlignment(QtCore.Qt.AlignCenter)
            units.setFixedWidth(units_width)
            glayout.addWidget(units, start_phase_index, 4, 1, 1) # w, row, column, rowspan, colspan

            hover_warning = HoverWarning("")
            glayout.addWidget(hover_warning, start_phase_index, 5, 1, 1) # w, row, column, rowspan, colspan
            setattr(self, f"{name}_warning_label", hover_warning)

        vbox = QVBoxLayout()
        w = QWidget()
        w.setLayout(glayout)
        vbox.addWidget(w)
        vbox.addStretch()

        base_name_stack = f"stack_trate_{base_name}" if suffix=="trate" else f"stack_duration_{base_name}"
        getattr(self, base_name_stack).setLayout(vbox)
        setattr(self, f"{base_name_stack}_idx", self.idx_stacked_widget)
        self.idx_stacked_widget += 1

        self.stacked_cycle.addWidget(getattr(self, base_name_stack))
            
    def reset_cycle_cb(self):   # new_cycle_params
        # print("--- reset_cycle_cb:  self.current_cell_def= ",self.current_cell_def)
        self.celldef_tab.new_cycle_params(self.get_current_celldef(), False)
        self.celldef_tab.tree_item_clicked_cb(self.celldef_tab.tree.currentItem(), 0)

    def update_cycle_params(self):
        # pass
        cdname = self.get_current_celldef()
        if self.param_d[cdname]['cycle_duration_flag']:
            self.cycle_rb2.setChecked(True)
        else:
            self.cycle_rb1.setChecked(True)

        self.cycle_dropdown.setCurrentIndex(self.param_d[cdname]['cycle_choice_idx'])

        for k, v in self.param_d[cdname].items():
            if not k.startswith("cycle_"):
                # not a cycle parameter
                continue
            if (not k.endswith("_trate")) and (not k.endswith("_duration")) and (not k.endswith("_fixed")):
                # only updating those that end with these strings
                continue
            if isinstance(v, bool):
                getattr(self, k).setChecked(v)
            else:
                getattr(self, k).setText(v)

        self.update_division_function_params()

    def create_division_function_tab(self):
        self.asym_div_standard_table = QTableWidget()
        nrows = len(self.celldef_tab.celltypes_list)
        self.asym_div_standard_table.setRowCount(nrows)
        self.asym_div_standard_table.setColumnCount(2)
        self.asym_div_standard_table.setHorizontalHeaderLabels(["Cell Type", "Probability"])

        self.asym_div_enabled_checkbox = QCheckBox_custom("Asymmetric Division")
        self.asym_div_enabled_checkbox.toggled.connect(self.asym_div_enabled_cb)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.asym_div_standard_table)
        hbox.addStretch()
        layout = QVBoxLayout()
        layout.addWidget(self.asym_div_enabled_checkbox)
        layout.addLayout(hbox)
        layout.addStretch()
        self.division_function_widget = QWidget()
        self.division_function_widget.setLayout(layout)

    def asym_div_enabled_cb(self, bval):
        self.asym_div_standard_table.setEnabled(bval)
        self.param_d[self.get_current_celldef()]['asymmetric_division_enabled'] = bval

    def update_division_function_params(self):
        cdname = self.get_current_celldef()
        try:
            for row_idx in range(self.asym_div_standard_table.rowCount()):
                row_name = self.asym_div_standard_table.item(row_idx, 0).text()
                new_val = self.param_d[cdname]['asymmetric_division_probability'][row_name]
                item = self.asym_div_standard_table.cellWidget(row_idx, 1)
                item.blockSignals(True) # when changing cell types, do not impose the condition that probs sum to 1
                item.setText(new_val)
                item.check_validity(new_val)
                item.format_text()
                item.blockSignals(False)
                if row_name == cdname:
                    item.setEnabled(False)
                else:
                    item.setEnabled(True)
        except:
            print("cell_def_cycle_tab.py: update_division_function_params() - exception!")
            pass
        self.asym_div_normalize_probabilities()
        if self.asym_div_enabled_checkbox.isChecked() == self.param_d[cdname]['asymmetric_division_enabled']:
            # force the emission of the signal (necessary at studio startup)
            self.asym_div_enabled_checkbox.toggled.emit(self.param_d[cdname]['asymmetric_division_enabled'])
        else:
            self.asym_div_enabled_checkbox.setChecked(self.param_d[cdname]['asymmetric_division_enabled'])

    def cell_def_rename(self, old_name, new_name):
        for row_idx in range(self.asym_div_standard_table.rowCount()):
            row_name = self.asym_div_standard_table.item(row_idx, 0).text()
            if row_name == old_name:
                self.asym_div_standard_table.item(row_idx, 0).setText(new_name)
                break
            
    def add_row_to_asym_div_table(self, cdname, val='0'):
        row_idx = self.asym_div_standard_table.rowCount()
        item = QTableWidgetItem(cdname)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.asym_div_standard_table.insertRow(row_idx)
        self.asym_div_standard_table.setItem(row_idx, 0, item)
        item = QLineEdit_custom()
        item.setText(val)
        item.invalid_style = """
            QLineEdit {
                color: black;
                background-color: rgba(255, 0, 0, 0.5);
            }
            """
        item.setValidator(QtGui.QDoubleValidator(bottom=0.0, top=1.0))
        item.set_formatter()
        item.format_text()
        item.row = row_idx
        if cdname == self.get_current_celldef():
            item.setEnabled(False)
        else:
            item.setEnabled(True)
        self.asym_div_standard_table.setCellWidget(row_idx, 1, item)
        item.textEdited.connect(self.asym_div_cb)

    def asym_div_cb(self, text):
        item = self.sender()
        if item.check_validity(text) is False:
            return
        row_idx = item.row
        cdname = self.asym_div_standard_table.item(row_idx, 0).text()
        self.param_d[self.get_current_celldef()]['asymmetric_division_probability'][cdname] = text
        self.asym_div_normalize_probabilities()

    def asym_div_normalize_probabilities(self):
        total = 0
        for row_idx in range(self.asym_div_standard_table.rowCount()):
            item = self.asym_div_standard_table.cellWidget(row_idx, 1)
            text = item.text()
            next_val = float(text)
            if next_val < 0:
                item.check_validity(text)
            total += float(next_val)
        if total != 1.0:
            # find row with current cell def name
            for row_idx in range(self.asym_div_standard_table.rowCount()):
                row_name = self.asym_div_standard_table.item(row_idx, 0).text()
                if row_name == self.get_current_celldef():
                    item = self.asym_div_standard_table.cellWidget(row_idx, 1)
                    new_val = float(item.text()) + 1.0 - total
                    item.blockSignals(True) # do not reissue the signal when changing this here
                    item.setText(str(new_val))
                    item.check_validity(str(new_val))
                    item.format_text()
                    item.blockSignals(False)
                    self.param_d[row_name]['asymmetric_division_probability'][row_name] = str(new_val)
                    break

    def delete_celltype(self, cdname):
        for row_idx in range(self.asym_div_standard_table.rowCount()):
            row_name = self.asym_div_standard_table.item(row_idx, 0).text()
            if row_name == cdname:
                self.asym_div_standard_table.removeRow(row_idx)
                break

    def reset_asym_div_table(self):
        self.asym_div_standard_table.clear()
        self.asym_div_standard_table.setRowCount(0)
        self.asym_div_standard_table.setColumnCount(2)
        self.asym_div_standard_table.setHorizontalHeaderLabels(["Cell Type", "Probability"])

    def fill_xml(self,pheno,cdef):
        combo_widget_idx = self.param_d[cdef]["cycle_choice_idx"]
        self.cycle_combo_idx_code = {0:"5", 1:"1", 2:"0", 3:"2", 4:"6", 5:"7"}
        self.cycle_combo_idx_name = {0:"live", 1:"basic Ki67", 2:"advanced Ki67", 3:"flow cytometry", 4:"Flow cytometry model (separated)", 5:"cycling quiescent"}
        cycle = ET.SubElement(pheno, "cycle",
            {"code":self.cycle_combo_idx_code[combo_widget_idx],
                "name":self.cycle_combo_idx_name[combo_widget_idx] } )
        cycle.text = self.celldef_tab.indent12  # affects self.indent of child, i.e., <phase_transition_rates, for example.
        cycle.tail = "\n" + self.celldef_tab.indent10

        #-- duration
        # if self.cycle_duration_flag:
        if self.param_d[cdef]['cycle_duration_flag']:
            subelm = ET.SubElement(cycle, "phase_durations",{"units":self.default_time_units})
            subelm.text = self.celldef_tab.indent14
            subelm.tail = self.celldef_tab.indent12

            #--- live
            if combo_widget_idx == 0:
                sfix = "false"
                if self.param_d[cdef]['cycle_live_00_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_live_00_duration']
                live_duration = float(self.param_d[cdef]['cycle_live_00_duration'])
                if abs(live_duration) < 1.e-6:
                    msg = f"WARNING: {cdef} has Cycle=live with duration ~= 0 which will result in unrealistically high proliferation!"
                    print(msg)
                    msgBox = QMessageBox()
                    msgBox.setTextFormat(Qt.RichText)
                    msgBox.setText(msg)
                    msgBox.setStandardButtons(QMessageBox.Ok)
                    returnValue = msgBox.exec()
                    # sys.exit(-1)
                subelm2.tail = self.celldef_tab.indent12

            elif combo_widget_idx == 1:
                sfix = "false"
                if self.param_d[cdef]['cycle_Ki67_01_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_Ki67_01_duration']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_Ki67_10_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_Ki67_10_duration']
                subelm2.tail = self.celldef_tab.indent12

            # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
            elif combo_widget_idx == 2:
                sfix = "false"
                if self.param_d[cdef]['cycle_advancedKi67_01_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_advancedKi67_01_duration']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_advancedKi67_12_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_advancedKi67_12_duration']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_advancedKi67_20_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"2", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_advancedKi67_20_duration']
                subelm2.tail = self.celldef_tab.indent12

            # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0
            elif combo_widget_idx == 3:
                sfix = "false"
                if self.param_d[cdef]['cycle_flowcyto_01_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcyto_01_duration']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcyto_12_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcyto_12_duration']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcyto_20_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"2", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcyto_20_duration']
                subelm2.tail = self.celldef_tab.indent12

            # self.cycle_dropdown.addItem("flow cytometry sepaduration") # 0->1, 1->2, 2->3, 3->0
            elif combo_widget_idx == 4:
                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_01_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_01_duration']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_12_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_12_duration']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_23_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"2", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_23_duration']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_30_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"3", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_30_duration']
                subelm2.tail = self.celldef_tab.indent12

            # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0
            elif combo_widget_idx == 5:
                sfix = "false"
                if self.param_d[cdef]['cycle_quiescent_01_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_quiescent_01_duration']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_quiescent_10_fixed_duration']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "duration",{"index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_quiescent_10_duration']
                subelm2.tail = self.celldef_tab.indent12



        #-- transition rates
        else:
            subelm = ET.SubElement(cycle, "phase_transition_rates",{"units":self.default_rate_units})
            subelm.text = self.celldef_tab.indent14  # affects </cycle>, i.e., its parent
            subelm.tail = self.celldef_tab.indent12

            # self.cycle_dropdown.addItem("live cells")   # 0 -> 0
            # self.cycle_dropdown.addItem("basic Ki67")   # 0 -> 1, 1 -> 0
            # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
            # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0
            # self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0
            # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0
            if combo_widget_idx == 0:
                sfix = "false"
                if self.param_d[cdef]['cycle_live_00_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0", "end_index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_live_00_trate']
                subelm2.tail = self.celldef_tab.indent12

            elif combo_widget_idx == 1:
                sfix = "false"
                if self.param_d[cdef]['cycle_Ki67_01_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0", "end_index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_Ki67_01_trate']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_Ki67_10_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"1", "end_index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_Ki67_10_trate']
                subelm2.tail = self.celldef_tab.indent12

            # self.cycle_dropdown.addItem("advanced Ki67")  # 0 -> 1, 1 -> 2, 2 -> 0
            elif combo_widget_idx == 2:
                sfix = "false"
                if self.param_d[cdef]['cycle_advancedKi67_01_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0", "end_index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_advancedKi67_01_trate']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_advancedKi67_12_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"1", "end_index":"2", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_advancedKi67_12_trate']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_advancedKi67_20_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"2", "end_index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_advancedKi67_20_trate']
                subelm2.tail = self.celldef_tab.indent12

            # self.cycle_dropdown.addItem("flow cytometry") # 0 -> 1, 1 -> 2, 2 -> 0
            elif combo_widget_idx == 3:
                sfix = "false"
                if self.param_d[cdef]['cycle_flowcyto_01_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0", "end_index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcyto_01_trate']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcyto_12_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"1", "end_index":"2", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcyto_12_trate']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcyto_20_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"2", "end_index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcyto_20_trate']
                subelm2.tail = self.celldef_tab.indent12

            # self.cycle_dropdown.addItem("flow cytometry separated") # 0->1, 1->2, 2->3, 3->0
            elif combo_widget_idx == 4:
                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_01_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0", "end_index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_01_trate']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_12_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"1", "end_index":"2", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_12_trate']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_23_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"2", "end_index":"3", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_23_trate']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_flowcytosep_30_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"3", "end_index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_flowcytosep_30_trate']
                subelm2.tail = self.celldef_tab.indent12

            # self.cycle_dropdown.addItem("cycling quiescent") # 0 -> 1, 1 -> 0
            elif combo_widget_idx == 5:
                sfix = "false"
                if self.param_d[cdef]['cycle_quiescent_01_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"0", "end_index":"1", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_quiescent_01_trate']
                subelm2.tail = self.celldef_tab.indent14

                sfix = "false"
                if self.param_d[cdef]['cycle_quiescent_10_fixed_trate']:
                    sfix = "true"
                subelm2 = ET.SubElement(subelm, "rate",{"start_index":"1", "end_index":"0", "fixed_duration":sfix} )
                subelm2.text = self.param_d[cdef]['cycle_quiescent_10_trate']
                subelm2.tail = self.celldef_tab.indent12

        # asymmetric division
        asym_div = ET.SubElement(cycle, "standard_asymmetric_division", {"enabled":str(self.param_d[cdef]['asymmetric_division_enabled'])})
        for other_cdname in self.param_d[cdef]['asymmetric_division_probability'].keys():
            asym_div_probability = ET.SubElement(asym_div, "asymmetric_division_probability", {"name":other_cdname, "units":"dimensionless"})
            asym_div_probability.text = self.param_d[cdef]['asymmetric_division_probability'][other_cdname]
