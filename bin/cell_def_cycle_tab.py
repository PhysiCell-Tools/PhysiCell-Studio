from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QStackedWidget, QGridLayout, QLineEdit
from studio_classes import QRadioButton_custom, QHLine, QComboBox_custom, CellDefSubTab, QCheckBox_custom, HoverWarning
from cell_def_tab_param_updates import CellDefParamUpdates


class CycleTab(CellDefSubTab):
    def __init__(self, celldef_tab):
        super().__init__(parent=celldef_tab)

        self.celldef_param_updates = CellDefParamUpdates(self)

        self.cycle_duration_flag = False
        self.label_width = 210
        self.fixed_checkbox_column_width = 60
        self.default_time_units = "min"
        self.default_rate_units = "1/min"

        self.stacked_cycle = QStackedWidget()

        self.setStyleSheet("background-color: rgb(236,236,236)")
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

        self.setLayout(self.vbox_cycle)

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

        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]['cycle_duration_flag'] = self.cycle_duration_flag
      
    def cycle_changed_cb(self, idx):
        if self.celldef_tab.current_cell_def:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]['cycle_choice_idx'] = idx
        self.customize_cycle_choices()

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
        self.new_cycle_params(self.current_cell_def, False)
        self.tree_item_clicked_cb(self.tree.currentItem(), 0)

    def update_cycle_params(self):
        # pass
        cdname = self.celldef_tab.current_cell_def
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
