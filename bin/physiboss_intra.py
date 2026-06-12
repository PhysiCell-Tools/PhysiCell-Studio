""""
physiboss_intra.py - parameters for the Cell Types -> Intracellular -> MaBoSS
Authors:
Vincent Noël (vincent.noel@curie.fr)
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
- also rf. Credits.md
"""

import os, sys, logging
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox, QFileDialog
from PyQt5.QtGui import QIcon
from studio_classes import QCheckBox_custom, QComboBox_custom

class PhysiBoSS_Frame(QWidget):
    def __init__(self, celldef_tab):
        super().__init__()

        self.celldef_tab = celldef_tab

        self.signals = []
        self.behaviours = []
        
        ly = QVBoxLayout()
        self.setLayout(ly)

        bnd_hbox = QHBoxLayout()

        bnd_label = QLabel("MaBoSS BND file")
        bnd_hbox.addWidget(bnd_label)

        self.bnd_file = QLineEdit()
        self.bnd_file.textChanged.connect(self.bnd_filename_changed)
        bnd_hbox.addWidget(self.bnd_file)


        bnd_button = QPushButton("Choose BND file")
        bnd_button.clicked.connect(self.choose_bnd_file)

        bnd_hbox.addWidget(bnd_button)
        ly.addLayout(bnd_hbox)

        cfg_hbox = QHBoxLayout()

        cfg_label = QLabel("MaBoSS CFG file")
        cfg_hbox.addWidget(cfg_label)

        self.cfg_file = QLineEdit()
        self.cfg_file.textChanged.connect(self.cfg_filename_changed)
        cfg_hbox.addWidget(self.cfg_file)

        cfg_button = QPushButton("Choose CFG file")
        cfg_button.clicked.connect(self.choose_cfg_file)

        cfg_hbox.addWidget(cfg_button)
        ly.addLayout(cfg_hbox)

        time_step_hbox = QHBoxLayout()

        time_step_label = QLabel("Time step")
        time_step_hbox.addWidget(time_step_label)

        self.time_step = QLineEdit()
        self.time_step.textChanged.connect(self.time_step_changed)
        # Commenting it because for french, we need to use a comma, which then get written in the XML and might cause problems
        # self.time_step.setValidator(QtGui.QDoubleValidator())

        time_step_hbox.addWidget(self.time_step)

        ly.addLayout(time_step_hbox)

        scaling_hbox = QHBoxLayout()

        scaling_label = QLabel("Scaling")
        scaling_hbox.addWidget(scaling_label)

        self.scaling = QLineEdit()
        self.scaling.textChanged.connect(self.scaling_changed)
        # Commenting it because for french, we need to use a comma, which then get written in the XML and might cause problems
        # self.scaling.setValidator(QtGui.QDoubleValidator())

        scaling_hbox.addWidget(self.scaling)

        ly.addLayout(scaling_hbox)

        time_stochasticity_hbox = QHBoxLayout()

        time_stochasticity_label = QLabel("Time stochasticity")
        time_stochasticity_hbox.addWidget(time_stochasticity_label)

        self.time_stochasticity = QLineEdit()
        self.time_stochasticity.textChanged.connect(self.time_stochasticity_changed)
        # Commenting it because for french, we need to use a comma, which then get written in the XML and might cause problems
        # self.time_stochasticity.setValidator(QtGui.QDoubleValidator())

        time_stochasticity_hbox.addWidget(self.time_stochasticity)

        ly.addLayout(time_stochasticity_hbox)

        starttime_hbox = QHBoxLayout()

        starttime_label = QLabel("Start time")
        starttime_hbox.addWidget(starttime_label)

        self.starttime = QLineEdit()
        self.starttime.textChanged.connect(self.starttime_changed)
        # Commenting it because for french, we need to use a comma, which then get written in the XML and might cause problems
        # self.scaling.setValidator(QtGui.QDoubleValidator())

        starttime_hbox.addWidget(self.starttime)

        ly.addLayout(starttime_hbox)


        initial_states_groupbox = QGroupBox("Initial states")
        self.initial_states_layout = QVBoxLayout()
        initial_states_labels = QHBoxLayout()

        initial_states_node_label = QLabel("Node")
        initial_states_value_label = QLabel("Value")
        initial_states_labels.addWidget(initial_states_node_label)
        initial_states_labels.addWidget(initial_states_value_label)
        self.initial_states_layout.addLayout(initial_states_labels)

        self.initial_states = []
        initial_states_groupbox.setLayout(self.initial_states_layout)

        ly.addWidget(initial_states_groupbox)
        
        initial_states_addbutton = QPushButton("Add new initial value")
        initial_states_addbutton.setStyleSheet("QPushButton { color: black }")
        initial_states_addbutton.clicked.connect(self.clicked_add_initial_value)
        ly.addWidget(initial_states_addbutton)

        
        mutants_groupbox = QGroupBox("Mutants")
        self.mutants_layout = QVBoxLayout()
        mutants_labels = QHBoxLayout()

        mutants_node_label = QLabel("Node")
        mutants_value_label = QLabel("Value")
        mutants_labels.addWidget(mutants_node_label)
        mutants_labels.addWidget(mutants_value_label)
        self.mutants_layout.addLayout(mutants_labels)
        mutants_groupbox.setLayout(self.mutants_layout)
        
        self.mutants = []
        ly.addWidget(mutants_groupbox)
 
        mutants_addbutton = QPushButton("Add new mutant")
        mutants_addbutton.setStyleSheet("QPushButton { color: black }")
        mutants_addbutton.clicked.connect(self.clicked_add_mutant)
        ly.addWidget(mutants_addbutton)

        parameters_groupbox = QGroupBox("Parameters")

        self.parameters_layout = QVBoxLayout()
        parameters_labels = QHBoxLayout()

        parameters_node_label = QLabel("Name")
        parameters_value_label = QLabel("Value")
        parameters_labels.addWidget(parameters_node_label)
        parameters_labels.addWidget(parameters_value_label)
        self.parameters_layout.addLayout(parameters_labels)
        parameters_groupbox.setLayout(self.parameters_layout)

        self.parameters = []
        ly.addWidget(parameters_groupbox)

        parameters_addbutton = QPushButton("Add new parameter")
        parameters_addbutton.setStyleSheet("QPushButton { color: black }")
        parameters_addbutton.clicked.connect(self.clicked_add_parameter)
        ly.addWidget(parameters_addbutton)

        inputs_groupbox = QGroupBox("Inputs")

        self.input_layout = QVBoxLayout()
        self.input_layout.setAlignment(Qt.AlignTop)
        inputs_labels = QHBoxLayout()

        inputs_signal_label = QLabel("Signal")
        inputs_node_label = QLabel("Node")
        inputs_action_label = QLabel("Action")
        inputs_threshold_label = QLabel("Thr")
        inputs_inact_threshold_label = QLabel("Inact. Thr")
        inputs_smoothing_label = QLabel("Smoothing")


        inputs_labels.addWidget(inputs_signal_label)
        inputs_signal_label.setMinimumWidth(240)
        inputs_labels.setStretch(0, 1)
        inputs_labels.addWidget(inputs_action_label)
        inputs_action_label.setMinimumWidth(50)
        inputs_labels.setStretch(1, 1)
        inputs_labels.addWidget(inputs_node_label)
        inputs_node_label.setMinimumWidth(50)
        inputs_labels.setStretch(2, 1)
        inputs_labels.addWidget(inputs_threshold_label)
        inputs_threshold_label.setFixedWidth(70)
        inputs_labels.addWidget(inputs_inact_threshold_label)
        inputs_inact_threshold_label.setFixedWidth(70)
        inputs_labels.addWidget(inputs_smoothing_label)
        inputs_smoothing_label.setFixedWidth(70)
        inputs_labels.addSpacing(35)

        self.input_layout.addLayout(inputs_labels)
        inputs_groupbox.setLayout(self.input_layout)

        self.inputs = []
        ly.addWidget(inputs_groupbox)

        inputs_addbutton = QPushButton("Add new input")
        inputs_addbutton.setStyleSheet("QPushButton { color: black }")
        inputs_addbutton.clicked.connect(self.clicked_add_input)
        ly.addWidget(inputs_addbutton)

        outputs_groupbox = QGroupBox("Outputs")

        self.outputs_layout = QVBoxLayout()
        outputs_labels = QHBoxLayout()

        outputs_signal_label = QLabel("Behavior")
        outputs_node_label = QLabel("Node")
        outputs_action_label = QLabel("Action")
        outputs_value_label = QLabel("Value")
        outputs_basal_value_label = QLabel("Base value")
        outputs_smoothing_label = QLabel("Smoothing")

        outputs_labels.addWidget(outputs_node_label)
        outputs_node_label.setMinimumWidth(50)
        outputs_labels.setStretch(0, 1)
        outputs_labels.addWidget(outputs_action_label)
        outputs_action_label.setMinimumWidth(40)
        outputs_labels.setStretch(1, 1)
        outputs_labels.addWidget(outputs_signal_label)
        outputs_signal_label.setMinimumWidth(250)
        outputs_labels.setStretch(2, 1)
        outputs_labels.addWidget(outputs_value_label)
        outputs_value_label.setFixedWidth(70)
        outputs_labels.addWidget(outputs_basal_value_label)
        outputs_basal_value_label.setFixedWidth(70)
        outputs_labels.addWidget(outputs_smoothing_label)
        outputs_labels.addSpacing(40)

        self.outputs_layout.addLayout(outputs_labels)
        outputs_groupbox.setLayout(self.outputs_layout)

        self.outputs = []
        ly.addWidget(outputs_groupbox)

        outputs_addbutton = QPushButton("Add new output")
        outputs_addbutton.setStyleSheet("QPushButton { color: black }")
        outputs_addbutton.clicked.connect(self.clicked_add_output)
        ly.addWidget(outputs_addbutton)


        inheritance_groupbox = QGroupBox("Inheritance")

        self.inheritance_layout = QVBoxLayout()

        self.global_inheritance = QHBoxLayout()

        self.global_inheritance_checkbox = QCheckBox_custom('Global inheritance')
        self.global_inheritance_flag = False
        self.global_inheritance_checkbox.setEnabled(True)
        self.global_inheritance_checkbox.setChecked(self.global_inheritance_flag)
        self.global_inheritance_checkbox.clicked.connect(self.global_inheritance_checkbox_cb)
        self.global_inheritance.addWidget(self.global_inheritance_checkbox)
        self.inheritance_layout.addLayout(self.global_inheritance)
        
        
        inheritance_labels = QHBoxLayout()
        inheritance_node_label = QLabel("Node")
        inheritance_node_label.setFixedWidth(200)
        inheritance_value_label = QLabel("Value")
        inheritance_value_label.setFixedWidth(150)
        inheritance_labels.addWidget(inheritance_node_label)
        inheritance_labels.addWidget(inheritance_value_label)
        inheritance_labels.addStretch(1)

        self.inheritance_layout.addLayout(inheritance_labels)
        inheritance_groupbox.setLayout(self.inheritance_layout)
        self.node_specific_inheritance = []

        ly.addWidget(inheritance_groupbox)

        inheritance_addbutton = QPushButton("Add node-specific inheritance")
        inheritance_addbutton.clicked.connect(self.clicked_add_node_inheritance)
        ly.addWidget(inheritance_addbutton)



    def choose_bnd_file(self):
        file , check = QFileDialog.getOpenFileName(None, "Please select a MaBoSS BND file",
                                               "", "MaBoSS BND Files (*.bnd)")
        if check:
            self.bnd_file.setText(os.path.relpath(file, os.getcwd()))
            
    def choose_cfg_file(self):
        file , check = QFileDialog.getOpenFileName(None, "Please select a MaBoSS CFG file",
                                               "", "MaBoSS CFG Files (*.cfg)")
        if check:
            self.cfg_file.setText(os.path.relpath(file, os.getcwd()))

    def bnd_filename_changed(self, text):
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]['bnd_filename'] = text
            self.update_list_nodes()
    
    def cfg_filename_changed(self, text):
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]['cfg_filename'] = text
            self.update_list_parameters()

    def update_list_signals(self):

        if self.celldef_tab.current_cell_def == None:
            return
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:

            self.signals = []
            for substrate in self.celldef_tab.substrate_list:
                self.signals.append(substrate)

            for substrate in self.celldef_tab.substrate_list:
                self.signals.append("intracellular " + substrate)
        
            for substrate in self.celldef_tab.substrate_list:
                self.signals.append(substrate + " gradient")
        
            self.signals += ["pressure", "volume"]

            for celltype in self.celldef_tab.celltypes_list:
                self.signals.append("contact with " + celltype)

            for custom_data in self.celldef_tab.master_custom_var_d.keys():
                self.signals.append("custom:" + custom_data)

            self.signals += ["contact with live cell", "contact with dead cell", "contact with basement membrane", "damage", "dead", "attacking", "total attack time", "time", "damage delivered"]

            for i, (name, _, _, _, _, _, _, _) in enumerate(self.inputs):
                name.currentIndexChanged.disconnect()
                name.clear()
                for signal in self.signals:
                    name.addItem(signal)
            
                if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["name"] is not None
                    and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["name"] in self.signals
                ):
                    name.setCurrentIndex(self.signals.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["name"]))
                else:
                    name.setCurrentIndex(-1)
        
                name.currentIndexChanged.connect(lambda index, i=i: self.input_signal_changed(i, index))

    def update_list_behaviours(self):

        if self.celldef_tab.current_cell_def == None:
            return
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:

            self.behaviours = []
            for substrate in self.celldef_tab.substrate_list:
                self.behaviours.append(substrate + " secretion")

            for substrate in self.celldef_tab.substrate_list:
                self.behaviours.append(substrate + " secretion target")
        
            for substrate in self.celldef_tab.substrate_list:
                self.behaviours.append(substrate + " uptake")

            for substrate in self.celldef_tab.substrate_list:
                self.behaviours.append("chemotactic response to " + substrate)

            for substrate in self.celldef_tab.substrate_list:
                self.behaviours.append(substrate + " export")

            for custom_data in self.celldef_tab.master_custom_var_d.keys():
                self.behaviours.append("custom:" + custom_data)
        
            self.behaviours += [
                "cycle entry", "exit from cycle phase 0", "exit from cycle phase 1", "exit from cycle phase 2", "exit from cycle phase 3", "exit from cycle phase 4", "exit from cycle phase 5",
                "apoptosis", "necrosis", "migration speed", "migration bias", "migration persistence time", "chemotactic response to oxygen", 
                "cell-cell adhesion", "cell-cell adhesion elastic constant"
            ]

            for celltype in self.celldef_tab.celltypes_list:
                self.behaviours.append("adhesive affinity to " + celltype)

            self.behaviours += ["relative maximum adhesion distance", "cell-cell repulsion", "cell-BM adhesion", "cell-BM repulsion", "phagocytose apoptotic cell", "phagocytose necrotic cell", "phagocytose other dead cell"]

            for celltype in self.celldef_tab.celltypes_list:
                self.behaviours.append("phagocytose " + celltype)

            for celltype in self.celldef_tab.celltypes_list:
                self.behaviours.append("attack " + celltype)

            for celltype in self.celldef_tab.celltypes_list:
                self.behaviours.append("fuse " + celltype)

            for celltype in self.celldef_tab.celltypes_list:
                self.behaviours.append("transform to " + celltype)


            for i, (name, _, _, _, _, _, _, _) in enumerate(self.outputs):
                name.currentIndexChanged.disconnect()
                name.clear()
                for behaviour in self.behaviours:
                    name.addItem(behaviour)

                if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["name"] is not None
                    and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["name"] in self.behaviours
                ):
                    name.setCurrentIndex(self.behaviours.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["name"]))
                else:
                    name.setCurrentIndex(-1)

                name.currentIndexChanged.connect(lambda index, i=i: self.outputs_behaviour_changed(i, index))

    def update_list_nodes(self):

        t_intracellular = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]
        
        if t_intracellular is not None:

            # Here I started by looking at both the bnd and the cfg
            if (
                t_intracellular is not None 
                and "bnd_filename" in t_intracellular.keys() 
                and t_intracellular['bnd_filename'] is not None 
                and len(t_intracellular['bnd_filename']) > 0
                and os.path.exists(os.path.join(os.getcwd(), t_intracellular["bnd_filename"])) 
                ):
                list_nodes = []
                with open(os.path.join(os.getcwd(), t_intracellular["bnd_filename"]), 'r') as bnd_file:
                    list_nodes = sorted([node.split(" ")[1].strip() for node in bnd_file.readlines() if node.strip().lower().startswith("node")])
            
                if len(list_nodes) > 0:
                    self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"] = list_nodes

                for i, (node, _, _, _) in enumerate(self.initial_states):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index, i=i: self.initial_value_node_changed(i, index))

                    if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"] is not None
                        and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"] in list_nodes
                    ):
                        node.setCurrentIndex(list_nodes.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"]))
                    elif self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"] == "" or self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"] not in list_nodes:
                        node.setCurrentIndex(0)
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"] = list_nodes[0]
                    else:
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"] = ""
                        node.setCurrentIndex(-1)

                for i, (node, _, _, _) in enumerate(self.mutants):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index, i=i: self.mutants_node_changed(i, index))

                    if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] is not None
                        and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] in list_nodes
                    ):
                        node.setCurrentIndex(list_nodes.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"]))
                    elif self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] == "" or self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] not in list_nodes:
                        node.setCurrentIndex(0)
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] = list_nodes[0]
                    else:
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] = ""
                        node.setCurrentIndex(-1)


                for i, (_, node, _, _, _, _, _, _) in enumerate(self.inputs):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index, i=i: self.input_node_changed(i, index))

                    if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] is not None
                        and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] in list_nodes
                    ):
                        node.setCurrentIndex(list_nodes.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"]))
                    elif self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] == "" or self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] not in list_nodes:
                        node.setCurrentIndex(0)
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] = list_nodes[0]
                    else:
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] = ""
                        node.setCurrentIndex(-1)
        
                for i, (_, node, _, _, _, _, _, _) in enumerate(self.outputs):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index, i=i: self.outputs_node_changed(i, index))

                    if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] is not None
                        and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] in list_nodes
                    ):
                        node.setCurrentIndex(list_nodes.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"]))
                    elif self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] == "" or self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] not in list_nodes:
                        node.setCurrentIndex(0)
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] = list_nodes[0]
                    else:
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] = ""
                        node.setCurrentIndex(-1)
          
    def update_list_parameters(self):
        
        t_intracellular = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]        
        if t_intracellular is not None:
            # Here I started by looking at both the bnd and the cfg
            if (
                t_intracellular is not None 
                and "cfg_filename" in t_intracellular.keys() 
                and t_intracellular['cfg_filename'] is not None \
                and len(t_intracellular['cfg_filename']) > 0
                and os.path.exists(os.path.join(os.getcwd(), t_intracellular["cfg_filename"])) 
                # and t_intracellular["cfg_filename"] and and os.path.exists(t_intracellular["cfg_filename"])
                ):
                list_parameters = []
                # list_internal_nodes = []
                with open(os.path.join(os.getcwd(), t_intracellular["cfg_filename"]), 'r') as cfg_file:
                    for line in cfg_file.readlines():
                        if line.strip().startswith("$"):
                            list_parameters.append(line.split("=")[0].strip())
                            
                        # elif ".is_internal" in line:
                        #     tokens = line.split("=")
                        #     value = tokens[1].strip()[:-1].lower() in ["1", "true"]
                        #     node = tokens[0].strip().replace(".is_internal", "")
                        #     if value:
                        #         list_internal_nodes.append(node)
                list_parameters = sorted(list_parameters)
                # list_output_nodes = list(set(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"]).difference(set(list_internal_nodes)))
                if len(list_parameters) > 0:
                    self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_parameters"] = list_parameters
                
                for i, (param, _, _, _) in enumerate(self.parameters):
                    param.currentIndexChanged.disconnect()
                    param.clear()
                    for name in list_parameters:
                        param.addItem(name)
                    param.currentIndexChanged.connect(lambda index, i=i: self.parameters_node_changed(i, index))

                    if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] is not None
                        and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] in list_parameters
                    ):
                        param.setCurrentIndex(list_parameters.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"]))
                    elif self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] == "" or self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] not in list_parameters:
                        param.setCurrentIndex(0)
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] = list_parameters[0]
                    else:
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] = ""
                        param.setCurrentIndex(-1)

    def time_step_changed(self, text):
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]['time_step'] = text
    
    def scaling_changed(self, text):
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]['scaling'] = text
    
    def time_stochasticity_changed(self, text):
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]['time_stochasticity'] = text
    
    def starttime_changed(self, text):
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]['start_time'] = text
    
    def clicked_add_initial_value(self):
        self.add_initial_values()
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"].append({
            'node': self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys() else "",
            'value': "1.0"
        })

    def add_initial_values(self):

        initial_states_editor = QHBoxLayout()
        initial_states_dropdown = QComboBox_custom()
        initial_states_dropdown.setFixedWidth(150)
        if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]:
            for node in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"]:
                initial_states_dropdown.addItem(node)
        initial_states_value = QLineEdit("1.0")
        initial_states_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
        initial_states_remove.setStyleSheet("QPushButton { color: black }")

        id = len(self.initial_states)
        initial_states_dropdown.currentIndexChanged.connect(lambda index, id=id: self.initial_value_node_changed(id, index))
        initial_states_value.textChanged.connect(lambda text, id=id: self.initial_value_value_changed(id, text))
        initial_states_remove.clicked.connect(lambda _, id=id: self.clicked_remove_initial_values(id))

        initial_states_editor.addWidget(initial_states_dropdown)
        initial_states_editor.addWidget(initial_states_value)
        initial_states_editor.addWidget(initial_states_remove)

        self.initial_states_layout.addLayout(initial_states_editor)
        self.initial_states.append((initial_states_dropdown, initial_states_value, initial_states_remove, initial_states_editor))

    def clicked_remove_initial_values(self, i):
        self.remove_initial_values(i)
        del self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]

    def remove_initial_values(self, id):
        self.initial_states[id][0].currentIndexChanged.disconnect()
        self.initial_states[id][0].deleteLater()
        self.initial_states[id][1].textChanged.disconnect()
        self.initial_states[id][1].deleteLater()
        self.initial_states[id][2].clicked.disconnect()
        self.initial_states[id][2].deleteLater()
        self.initial_states[id][3].deleteLater()
        del self.initial_states[id]
        
        # Here we should remap the clicked method to have the proper id
        for i, initial_state in enumerate(self.initial_states):
            node, value, button, _ = initial_state
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index, i=i: self.initial_value_node_changed(i, index))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text, i=i: self.initial_value_value_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.clicked_remove_initial_values(i))

    def clear_initial_values(self):
        for i, _ in reversed(list(enumerate(self.initial_states))):
            self.remove_initial_values(i)
    
    def initial_value_node_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]['node'] = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][index]

    def initial_value_value_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]['value'] = text
    
    def clicked_add_mutant(self):
        self.add_mutant()
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"].append({
            'node': self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys() else "",
            'value': "0",
        })

    def add_mutant(self):

        mutants_editor = QHBoxLayout()        
        
        mutants_node_dropdown = QComboBox_custom()
        mutants_node_dropdown.setFixedWidth(150)
        if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]:
            for node in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"]:
                mutants_node_dropdown.addItem(node)
        
        mutants_value = QLineEdit("0")
        mutants_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
        id = len(self.mutants)
        mutants_node_dropdown.currentIndexChanged.connect(lambda index, id=id: self.mutants_node_changed(id, index))
        mutants_value.textChanged.connect(lambda text, id=id: self.mutants_value_changed(id, text))
        mutants_remove.clicked.connect(lambda _, id=id: self.clicked_remove_mutant(id))

        mutants_editor.addWidget(mutants_node_dropdown)
        mutants_editor.addWidget(mutants_value)
        mutants_editor.addWidget(mutants_remove)
        self.mutants_layout.addLayout(mutants_editor)
        self.mutants.append((mutants_node_dropdown, mutants_value, mutants_remove, mutants_editor))

    def clicked_remove_mutant(self, i):
        self.remove_mutant(i)
        del self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]

    def remove_mutant(self, id):
        self.mutants[id][0].currentIndexChanged.disconnect()
        self.mutants[id][0].deleteLater()
        self.mutants[id][1].textChanged.disconnect()
        self.mutants[id][1].deleteLater()
        self.mutants[id][2].clicked.disconnect()
        self.mutants[id][2].deleteLater()
        self.mutants[id][3].deleteLater()
        del self.mutants[id]
      
        # Here we should remap the clicked method to have the proper id
        for i, mutant in enumerate(self.mutants):
            name, value, button, _ = mutant
            name.currentIndexChanged.disconnect()
            name.currentIndexChanged.connect(lambda index, i=i: self.mutants_node_changed(i, index))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text, i=i: self.mutants_value_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.clicked_remove_mutant(i))

    def clear_mutants(self):
        for i, _ in reversed(list(enumerate(self.mutants))):
            self.remove_mutant(i)
    
    def mutants_node_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][index]

    def mutants_value_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["value"] = text

    def clicked_add_parameter(self):
        self.add_parameter()
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"].append({
            'name': self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_parameters"][0] if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys() else "",
            'value': "1.0"
        })

    def add_parameter(self):

        parameters_editor = QHBoxLayout()
        parameters_dropdown = QComboBox_custom()
        parameters_dropdown.setFixedWidth(150)
        if "list_parameters" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]:
            for parameter in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_parameters"]:
                parameters_dropdown.addItem(parameter)
        parameters_value = QLineEdit("1.0")
        parameters_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
       
        id = len(self.parameters)
        parameters_dropdown.currentIndexChanged.connect(lambda index, id=id: self.parameters_node_changed(id, index))
        parameters_value.textChanged.connect(lambda text, id=id: self.parameters_value_changed(id, text))
        parameters_remove.clicked.connect(lambda _, id=id: self.clicked_remove_parameter(id))

        parameters_editor.addWidget(parameters_dropdown)
        parameters_editor.addWidget(parameters_value)
        parameters_editor.addWidget(parameters_remove)
        self.parameters_layout.addLayout(parameters_editor)
        self.parameters.append((parameters_dropdown, parameters_value, parameters_remove, parameters_editor))

    def clicked_remove_parameter(self, i):
        self.remove_parameter(i)
        del self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]

    def remove_parameter(self, id):
        self.parameters[id][0].currentIndexChanged.disconnect()
        self.parameters[id][0].deleteLater()
        self.parameters[id][1].textChanged.disconnect()
        self.parameters[id][1].deleteLater()
        self.parameters[id][2].clicked.disconnect()
        self.parameters[id][2].deleteLater()
        self.parameters[id][3].deleteLater()
        del self.parameters[id]

        # Here we should remap the clicked method to have the proper id
        for i, parameter in enumerate(self.parameters):
            name, value, button, _ = parameter
            name.currentIndexChanged.disconnect()
            name.currentIndexChanged.connect(lambda index, i=i: self.parameters_node_changed(i, index))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text, i=i: self.parameters_value_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.clicked_remove_parameter(i))
        
    def clear_parameters(self):
        for i, _ in reversed(list(enumerate(self.parameters))):
            self.remove_parameter(i)

    def parameters_node_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_parameters"][index]

    def parameters_value_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["value"] = text
    
    def clicked_add_input(self):
        self.add_input()
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"].append({
            'name': self.signals[0],
            'node': self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys() else "",
            'action': 'activation',
            'threshold': "1.0",
            'inact_threshold': "1.0",
            'smoothing': "0"
        })

    def add_input(self):

        inputs_editor = QHBoxLayout()

        inputs_signal_dropdown = QComboBox_custom()

        for signal in self.signals:
            inputs_signal_dropdown.addItem(signal)
        
        inputs_node_dropdown = QComboBox_custom()

        if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]:
            for node in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"]:
                inputs_node_dropdown.addItem(node)
        
        inputs_action = QComboBox_custom()

        inputs_action.addItem("activation")
        inputs_action.addItem("inhibition")

        inputs_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)

        id = len(self.inputs)
        inputs_node_dropdown.currentIndexChanged.connect(lambda index, id=id: self.input_node_changed(id, index))
        inputs_signal_dropdown.currentIndexChanged.connect(lambda text, id=id: self.input_signal_changed(id, text))
        inputs_action.currentIndexChanged.connect(lambda index, id=id: self.input_action_changed(id, index))
        inputs_remove.clicked.connect(lambda _, id=id: self.clicked_remove_input(id))

        inputs_editor.addWidget(inputs_signal_dropdown)
        inputs_editor.setStretch(0, 1)
        inputs_editor.addWidget(inputs_action)
        inputs_editor.setStretch(1, 1)
        inputs_editor.addWidget(inputs_node_dropdown)
        inputs_editor.setStretch(2, 1)
        
        inputs_threshold = QLineEdit("1.0")
        inputs_inact_threshold = QLineEdit("1.0")
        inputs_smoothing = QLineEdit("0")
        inputs_threshold.textChanged.connect(lambda text, id=id: self.input_threshold_changed(id, text))
        inputs_inact_threshold.textChanged.connect(lambda text, id=id: self.input_inact_threshold_changed(id, text))
        inputs_smoothing.textChanged.connect(lambda text, id=id: self.input_smoothing_changed(id, text))
        
        inputs_editor.addWidget(inputs_threshold)
        inputs_threshold.setFixedWidth(70)
        inputs_editor.addWidget(inputs_inact_threshold)
        inputs_inact_threshold.setFixedWidth(70)
        inputs_editor.addWidget(inputs_smoothing)
        inputs_smoothing.setFixedWidth(70)


        inputs_remove.setFixedWidth(30)
        inputs_editor.addWidget(inputs_remove)


        self.input_layout.addLayout(inputs_editor)
        self.inputs.append((inputs_signal_dropdown, inputs_node_dropdown, inputs_action, inputs_threshold, inputs_inact_threshold, inputs_smoothing, inputs_remove, inputs_editor))#, inputs_editor_2))
    
    def input_signal_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["name"] = self.signals[index]
        
    def input_node_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][index]
        
    def input_action_changed(self, i, index):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["action"] = "activation" if index == 0 else "inhibition"

    def input_threshold_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["threshold"] = text

    def input_inact_threshold_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["inact_threshold"] = text

    def input_smoothing_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["smoothing"] = text

    def clicked_remove_input(self, i):
        self.remove_input(i)
        del self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]

    def remove_input(self, id):
        self.inputs[id][0].currentIndexChanged.disconnect()
        self.inputs[id][0].deleteLater()
        self.inputs[id][1].currentIndexChanged.disconnect()
        self.inputs[id][1].deleteLater()
        self.inputs[id][2].currentIndexChanged.disconnect()
        self.inputs[id][2].deleteLater()
        self.inputs[id][3].textChanged.disconnect()
        self.inputs[id][3].deleteLater()
        self.inputs[id][4].textChanged.disconnect()
        self.inputs[id][4].deleteLater()
        self.inputs[id][5].textChanged.disconnect()
        self.inputs[id][5].deleteLater()
        self.inputs[id][6].clicked.disconnect()
        self.inputs[id][6].deleteLater()
        del self.inputs[id]

        # Here we should remap the clicked method to have the proper id
        for i, input in enumerate(self.inputs):
            signal, node, action, threshold, inact_threshold, smoothing, button, _ = input
            signal.currentIndexChanged.disconnect()
            signal.currentIndexChanged.connect(lambda index, i=i: self.input_signal_changed(i, index))
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index, i=i: self.input_node_changed(i, index))
            action.currentIndexChanged.disconnect()
            action.currentIndexChanged.connect(lambda index, i=i: self.input_action_changed(i, index))
            threshold.textChanged.disconnect()
            threshold.textChanged.connect(lambda text, i=i: self.input_threshold_changed(i, text))
            inact_threshold.textChanged.disconnect()
            inact_threshold.textChanged.connect(lambda text, i=i: self.input_inact_threshold_changed(i, text))
            smoothing.textChanged.disconnect()
            smoothing.textChanged.connect(lambda text, i=i: self.input_smoothing_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.clicked_remove_input(i))
        
    def clear_inputs(self):
        for i, _ in reversed(list(enumerate(self.inputs))):
            self.remove_input(i)

    def clicked_add_output(self):
        self.add_output()
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"].append({
            'name': self.behaviours[0],
            'node': self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys() else "",
            'action': 'activation',
            'value': "1.0",
            'basal_value': "0.0",
            'smoothing': "0"
        })

    def add_output(self):

        outputs_editor = QHBoxLayout()
        outputs_behaviour_dropdown = QComboBox_custom()

        for behaviour in self.behaviours:
            outputs_behaviour_dropdown.addItem(behaviour)
        
        outputs_node_dropdown = QComboBox_custom()

        if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]:
            for node in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"]:
                outputs_node_dropdown.addItem(node)
        
        outputs_action = QComboBox_custom()

        outputs_action.addItem("activation")
        outputs_action.addItem("inhibition")
        outputs_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
        outputs_remove.setFixedWidth(30)


        id = len(self.outputs)
        outputs_node_dropdown.currentIndexChanged.connect(lambda index, id=id: self.outputs_node_changed(id, index))
        outputs_behaviour_dropdown.currentIndexChanged.connect(lambda text, id=id: self.outputs_behaviour_changed(id, text))
        outputs_action.currentIndexChanged.connect(lambda index, id=id: self.outputs_action_changed(id, index))
        outputs_remove.clicked.connect(lambda _, id=id: self.clicked_remove_output(id))

        outputs_editor.addWidget(outputs_node_dropdown)
        outputs_editor.setStretch(0, 1)
        outputs_editor.addWidget(outputs_action)
        outputs_editor.setStretch(1, 1)
        outputs_editor.addWidget(outputs_behaviour_dropdown)
        outputs_editor.setStretch(2, 1)
        
        outputs_value = QLineEdit("1.0")
        outputs_basal_value = QLineEdit("0.0")
        outputs_smoothing = QLineEdit("0")        
        outputs_value.textChanged.connect(lambda text, id=id: self.outputs_value_changed(id, text))
        outputs_basal_value.textChanged.connect(lambda text, id=id: self.outputs_basal_value_changed(id, text))
        outputs_smoothing.textChanged.connect(lambda text, id=id: self.outputs_smoothing_changed(id, text))
        
        outputs_editor.addWidget(outputs_value)
        outputs_editor.addWidget(outputs_basal_value)
        outputs_editor.addWidget(outputs_smoothing)

        outputs_value.setFixedWidth(70)
        outputs_basal_value.setFixedWidth(70)
        outputs_smoothing.setFixedWidth(70)
        
        outputs_editor.addWidget(outputs_remove)

        self.outputs_layout.addLayout(outputs_editor)
        self.outputs.append((outputs_behaviour_dropdown, outputs_node_dropdown, outputs_action, outputs_value, outputs_basal_value, outputs_smoothing, outputs_remove, outputs_editor))#, outputs_editor_2))
    
    def outputs_behaviour_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["name"] = self.behaviours[index]
        
    def outputs_node_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][index]

    def outputs_action_changed(self, i, index):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["action"] = "activation" if index == 0 else "inhibition"

    def outputs_value_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["value"] = text

    def outputs_basal_value_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["basal_value"] = text

    def outputs_smoothing_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["smoothing"] = text

    def clicked_remove_output(self, i):
        self.remove_output(i)
        del self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]

    def remove_output(self, id):
        self.outputs[id][0].currentIndexChanged.disconnect()
        self.outputs[id][0].deleteLater()
        self.outputs[id][1].currentIndexChanged.disconnect()
        self.outputs[id][1].deleteLater()
        self.outputs[id][2].currentIndexChanged.disconnect()
        self.outputs[id][2].deleteLater()
        self.outputs[id][3].textChanged.disconnect()
        self.outputs[id][3].deleteLater()
        self.outputs[id][4].textChanged.disconnect()
        self.outputs[id][4].deleteLater()
        self.outputs[id][5].textChanged.disconnect()
        self.outputs[id][5].deleteLater()
        self.outputs[id][6].clicked.disconnect()
        self.outputs[id][6].deleteLater()
        del self.outputs[id]

        # Here we should remap the clicked method to have the proper id
        for i, output in enumerate(self.outputs):
            name, node, action, value, basal_value, smoothing, button, _ = output
            name.currentIndexChanged.disconnect()
            name.currentIndexChanged.connect(lambda index, i=i: self.outputs_behaviour_changed(i, index))
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index, i=i: self.outputs_node_changed(i, index))
            action.currentIndexChanged.disconnect()
            action.currentIndexChanged.connect(lambda index, i=i: self.outputs_action_changed(i, index))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text, i=i: self.outputs_value_changed(i, text))
            basal_value.textChanged.disconnect()
            basal_value.textChanged.connect(lambda text, i=i: self.outputs_basal_value_changed(i, text))
            smoothing.textChanged.disconnect()
            smoothing.textChanged.connect(lambda text, i=i: self.outputs_smoothing_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.clicked_remove_output(i))
            
    def clear_outputs(self):
        for i, _ in reversed(list(enumerate(self.outputs))):
            self.remove_output(i)

    def global_inheritance_checkbox_cb(self, bval):
        self.global_inheritance_flag = bval
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["global_inheritance"] = str(bval)

    def clicked_add_node_inheritance(self):
        self.add_node_inheritance()
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["node_inheritance"].append({
            'node': self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys() else "",
            'flag': str(not self.global_inheritance),
        })
        
    def add_node_inheritance(self):
        
        node_inheritance_editor = QHBoxLayout()
        node_inheritance_dropdown = QComboBox_custom()
        node_inheritance_dropdown.setFixedWidth(200)
        if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]:
            for node in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"]:
                node_inheritance_dropdown.addItem(node)
        
                
        node_inheritance_checkbox = QCheckBox_custom('Node-specific inheritance')
        node_inheritance_checkbox.setEnabled(True)
        node_inheritance_checkbox.setChecked(not self.global_inheritance_flag)
        
        node_inheritance_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)


        id = len(self.node_specific_inheritance)
        node_inheritance_dropdown.currentIndexChanged.connect(lambda index, id=id: self.node_inheritance_node_changed(id, index))
        node_inheritance_checkbox.clicked.connect(lambda bval, id=id: self.node_inheritance_flag_changed(id, bval))
        node_inheritance_remove.clicked.connect(lambda _, id=id: self.clicked_remove_node_inheritance(id))
        node_inheritance_remove.setFixedWidth(30)
        node_inheritance_editor.addWidget(node_inheritance_dropdown)
        node_inheritance_editor.addWidget(node_inheritance_checkbox)
        node_inheritance_editor.addWidget(node_inheritance_remove)
        node_inheritance_editor.addStretch(1)
        
       
        self.inheritance_layout.addLayout(node_inheritance_editor)
        self.node_specific_inheritance.append((node_inheritance_dropdown, node_inheritance_checkbox, node_inheritance_remove, node_inheritance_editor))
    
    def remove_node_inheritance(self, id):
        self.node_specific_inheritance[id][0].currentIndexChanged.disconnect()
        self.node_specific_inheritance[id][0].deleteLater()
        self.node_specific_inheritance[id][1].clicked.disconnect()
        self.node_specific_inheritance[id][1].deleteLater()
        self.node_specific_inheritance[id][2].clicked.disconnect()
        self.node_specific_inheritance[id][2].deleteLater()
        self.node_specific_inheritance[id][3].deleteLater()
        del self.node_specific_inheritance[id]
    
    
        # Here we should remap the clicked method to have the proper id
        for i, node_inheritance in enumerate(self.node_specific_inheritance):
            node, flag, remove, _ = node_inheritance
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index, i=i: self.node_inheritance_node_changed(i, index))
            flag.clicked.disconnect()
            flag.clicked.connect(lambda bval, i=i: self.node_inheritance_flag_changed(i, bval))
            remove.clicked.disconnect()
            remove.clicked.connect(lambda _, i=i: self.clicked_remove_node_inheritance(i))
      
    def node_inheritance_node_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["node_inheritance"][i]["node"] = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][index]
  
    def node_inheritance_flag_changed(self, i, bval):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["node_inheritance"][i]["flag"] = str(bval)
  
    def clicked_remove_node_inheritance(self, i):
        self.remove_node_inheritance(i)
        del self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["node_inheritance"][i]
        
    def clear_node_inheritance(self):
        for i, _ in reversed(list(enumerate(self.node_specific_inheritance))):
            self.remove_node_inheritance(i)

    def init_defaults(self):
        intracellular = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]

        if 'initial_values' not in intracellular.keys():
            intracellular["initial_values"] = []
            self.clear_initial_values()

        if 'mutants' not in intracellular.keys():
            intracellular["mutants"] = []
            self.clear_mutants()

        if 'parameters' not in intracellular.keys():
            intracellular["parameters"] = []
            self.clear_parameters()

        if 'inputs' not in intracellular.keys():
            intracellular["inputs"] = []
            self.clear_inputs()

        if 'outputs' not in intracellular.keys():
            intracellular["outputs"] = []
            self.clear_outputs()

        if 'node_inheritance' not in intracellular.keys():
            intracellular["node_inheritance"] = []
            self.clear_node_inheritance()

        if 'time_step' not in intracellular.keys():
            self.time_step.setText("12.0")

        if 'time_stochasticity' not in intracellular.keys():
            self.time_stochasticity.setText("0.0")

        if 'scaling' not in intracellular.keys():
            self.scaling.setText("1.0")

        if 'start_time' not in intracellular.keys():
            self.starttime.setText("0.0")

        if 'global_inheritance' not in intracellular.keys():
            intracellular["global_inheritance"] = "False"
            self.global_inheritance_checkbox.setChecked(False)
        self.update_list_signals()
        self.update_list_behaviours()

    def clear_all(self):
        self.bnd_file.setText("")
        self.cfg_file.setText("")
        self.clear_initial_values()
        self.clear_mutants()
        self.clear_parameters()
        self.clear_inputs()
        self.clear_outputs()
        self.clear_node_inheritance()
        self.time_step.setText("")
        self.time_stochasticity.setText("")
        self.scaling.setText("")
        self.starttime.setText("")
        self.global_inheritance_checkbox.setChecked(False)
        
    def fill_gui(self, cdname):
        self.clear_initial_values()
        self.clear_mutants()
        self.clear_parameters()
        self.clear_node_inheritance()
        self.clear_inputs()
        self.clear_outputs()

        self.celldef_tab.intracellular_type_dropdown.setCurrentIndex(1)
        if "bnd_filename" in self.celldef_tab.param_d[cdname]["intracellular"].keys(): 
            self.bnd_file.setText(self.celldef_tab.param_d[cdname]["intracellular"]["bnd_filename"])
        if "cfg_filename" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
            self.cfg_file.setText(self.celldef_tab.param_d[cdname]["intracellular"]["cfg_filename"])

        if "time_step" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
            self.time_step.setText(self.celldef_tab.param_d[cdname]["intracellular"]["time_step"])
        if "time_stochasticity" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
            self.time_stochasticity.setText(self.celldef_tab.param_d[cdname]["intracellular"]["time_stochasticity"])
        if "scaling" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
            self.scaling.setText(self.celldef_tab.param_d[cdname]["intracellular"]["scaling"])
        if "start_time" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
            self.starttime.setText(self.celldef_tab.param_d[cdname]["intracellular"]["start_time"])
        if "global_inheritance" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
            self.global_inheritance_checkbox.setChecked(self.celldef_tab.param_d[cdname]["intracellular"]["global_inheritance"] == "True")

        self.celldef_tab.fill_substrates_comboboxes()
        self.celldef_tab.fill_celltypes_comboboxes()
        self.update_list_signals()
        self.update_list_behaviours()
        self.update_list_nodes()
        self.update_list_parameters()

        for i, node_inheritance in enumerate(self.celldef_tab.param_d[cdname]["intracellular"]["node_inheritance"]):
            self.add_node_inheritance()
            node, flag, _, _ = self.node_specific_inheritance[i]
            node.setCurrentIndex(self.celldef_tab.param_d[cdname]["intracellular"]["list_nodes"].index(node_inheritance["node"]))
            flag.setChecked(node_inheritance["flag"] == "True")

        for i, initial_value in enumerate(self.celldef_tab.param_d[cdname]["intracellular"]["initial_values"]):
            self.add_initial_values()
            node, value, _, _ = self.initial_states[i]
            if "list_nodes" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
                node.setCurrentIndex(self.celldef_tab.param_d[cdname]["intracellular"]["list_nodes"].index(initial_value["node"]))
                value.setText(initial_value["value"])
            else:
                print("----- ERROR(0): update_intracellular_params() has no 'list_nodes' key.")
                break

        for i, mutant in enumerate(self.celldef_tab.param_d[cdname]["intracellular"]["mutants"]):
            self.add_mutant()
            node, value, _, _ = self.mutants[i]
            if "list_nodes" not in self.celldef_tab.param_d[cdname]["intracellular"].keys():
                print("----- ERROR(1): update_intracellular_params() has no 'list_nodes' key.")
                break
            node.setCurrentIndex(self.celldef_tab.param_d[cdname]["intracellular"]["list_nodes"].index(mutant["node"]))
            value.setText(mutant["value"])

        for i, parameter in enumerate(self.celldef_tab.param_d[cdname]["intracellular"]["parameters"]):
            self.add_parameter()
            name, value, _, _ = self.parameters[i]
            if "list_nodes" not in self.celldef_tab.param_d[cdname]["intracellular"].keys():
                print("----- ERROR(2): update_intracellular_params() has no 'list_nodes' key.")
                break
            name.setCurrentIndex(self.celldef_tab.param_d[cdname]["intracellular"]["list_parameters"].index(parameter["name"]))
            value.setText(parameter["value"])


        for i, input in enumerate(self.celldef_tab.param_d[cdname]["intracellular"]["inputs"]):
            self.add_input()
            name, node, action, threshold, inact_threshold, smoothing, _, _ = self.inputs[i]
            logging.debug(f'update_intracellular_params(): cdname={cdname},  {input["name"]}={input["name"]}')
            logging.debug(f'  param_d= {self.celldef_tab.param_d[cdname]["intracellular"]}')
            name.setCurrentIndex(self.signals.index(input["name"]))
            if "list_nodes" not in self.celldef_tab.param_d[cdname]["intracellular"].keys():
                print("----- ERROR(3): update_intracellular_params() has no 'list_nodes' key.")
                break
            node.setCurrentIndex(self.celldef_tab.param_d[cdname]["intracellular"]["list_nodes"].index(input["node"]))
            action.setCurrentIndex(1 if input["action"] == "inhibition" else 0)
            threshold.setText(input["threshold"])
            inact_threshold.setText(input["inact_threshold"])
            smoothing.setText(input["smoothing"])

        for i, output in enumerate(self.celldef_tab.param_d[cdname]["intracellular"]["outputs"]):
            self.add_output()
            name, node, action, value, basal_value, smoothing, _, _ = self.outputs[i]
            name.setCurrentIndex(self.behaviours.index(output["name"]))
            if "list_nodes" not in self.celldef_tab.param_d[cdname]["intracellular"].keys():
                print("----- ERROR(4): update_intracellular_params() has no 'list_nodes' key.")
                break
            node.setCurrentIndex(self.celldef_tab.param_d[cdname]["intracellular"]["list_nodes"].index(output["node"]))
            action.setCurrentIndex(1 if output["action"] == "inhibition" else 0)
            value.setText(output["value"])
            basal_value.setText(output["basal_value"])
            smoothing.setText(output["smoothing"])