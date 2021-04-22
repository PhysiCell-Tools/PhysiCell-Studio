"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)

--- Versions ---
0.1 - initial version
"""

import sys
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import *
from PySide6.QtGui import QDoubleValidator

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class SubstrateDef(QWidget):
    def __init__(self):
        super().__init__()
        # global self.microenv_params

        self.current_substrate = None
        self.xml_root = None
        self.celldef_tab = None

        #---------------
        # self.cell_defs = CellDefInstances()
        self.microenv_hbox = QHBoxLayout()

        splitter = QSplitter()

        tree_widget_width = 160

        self.tree = QTreeWidget()
        # self.tree.setStyleSheet("background-color: lightgray")
        self.tree.setFixedWidth(tree_widget_width)
        # self.tree.currentChanged(self.tree_item_changed_cb)
        self.tree.itemClicked.connect(self.tree_item_changed_cb)
        # self.tree.itemSelectionChanged()
        # self.tree.setColumnCount(1)

        # self.tree.setCurrentItem(0)  # rwh/TODO

        header = QTreeWidgetItem(["---  Substrate ---"])
        self.tree.setHeaderItem(header)

        # cellname = QTreeWidgetItem(["virus"])
        # self.tree.insertTopLevelItem(0,cellname)

        # cellname = QTreeWidgetItem(["interferon"])
        # self.tree.insertTopLevelItem(1,cellname)


        self.microenv_hbox.addWidget(self.tree)

        self.scroll_cell_def_tree = QScrollArea()
        self.scroll_cell_def_tree.setWidget(self.tree)

        # splitter.addWidget(self.tree)
        splitter.addWidget(self.scroll_cell_def_tree)

        #-------------------------------------------
        # self.tab = QWidget()
        # self.tabs.resize(200,5)
        
        #-------------------------------------------
        label_width = 150
        units_width = 70

        # self.scroll = QScrollArea()
        self.scroll_area = QScrollArea()
        splitter.addWidget(self.scroll_area)
        # self.microenv_hbox.addWidget(self.scroll_area)

        self.microenv_params = QWidget()
        self.vbox = QVBoxLayout()
        self.vbox.addStretch(0)

        # self.microenv_hbox.addWidget(self.)

        #------------------
        controls_hbox = QHBoxLayout()
        self.new_button = QPushButton("New")
        controls_hbox.addWidget(self.new_button)

        self.copy_button = QPushButton("Copy")
        controls_hbox.addWidget(self.copy_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_substrate)
        controls_hbox.addWidget(self.delete_button)

        # self.vbox.addLayout(hbox)
        # self.vbox.addWidget(QHLine())

        #------------------
        hbox = QHBoxLayout()
        label = QLabel("Name of substrate:")
        label.setFixedWidth(180)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.substrate_name = QLineEdit()
        # Want to validate name, e.g., starts with alpha, no special chars, etc.
        # self.cycle_trate0_0.setValidator(QtGui.QDoubleValidator())
        # self.cycle_trate0_1.enter.connect(self.save_xml)
        hbox.addWidget(self.substrate_name)
        self.vbox.addLayout(hbox)

        #------------------
        hbox = QHBoxLayout()
        label = QLabel("diffusion coefficient")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.diffusion_coef = QLineEdit()
        self.diffusion_coef.setValidator(QtGui.QDoubleValidator())
        # self.diffusion_coef.enter.connect(self.save_xml)
        hbox.addWidget(self.diffusion_coef)

        units = QLabel("micron^2/min")
        units.setFixedWidth(units_width)
        hbox.addWidget(units)
        self.vbox.addLayout(hbox)

        #----------
        hbox = QHBoxLayout()
        label = QLabel("decay rate")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.decay_rate = QLineEdit()
        self.decay_rate.setValidator(QtGui.QDoubleValidator())
        # self.decay_rate.enter.connect(self.save_xml)
        hbox.addWidget(self.decay_rate)

        units = QLabel("1/min")
        units.setFixedWidth(units_width)
        hbox.addWidget(units)
        self.vbox.addLayout(hbox)

        #----------
        hbox = QHBoxLayout()
        label = QLabel("initial condition")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.init_cond = QLineEdit()
        self.init_cond.setValidator(QtGui.QDoubleValidator())
        # self.init_cond.enter.connect(self.save_xml)
        hbox.addWidget(self.init_cond)

        units = QLabel("mmol")
        units.setFixedWidth(units_width)
        hbox.addWidget(units)
        self.vbox.addLayout(hbox)
        #----------

        hbox = QHBoxLayout()
        label = QLabel("Dirichlet BC")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.dirichlet_bc = QLineEdit()
        self.dirichlet_bc.setValidator(QtGui.QDoubleValidator())
        # self.bdy_cond.enter.connect(self.save_xml)
        hbox.addWidget(self.dirichlet_bc)

        units = QLabel("mmol")
        units.setFixedWidth(units_width)
        hbox.addWidget(units)

        self.dirichlet_bc_enabled = QCheckBox("on/off")
        # self.motility_enabled.setAlignment(QtCore.Qt.AlignRight)
        # label.setFixedWidth(label_width)
        hbox.addWidget(self.dirichlet_bc_enabled)

        self.vbox.addLayout(hbox)
        #-------------

        hbox = QHBoxLayout()
        self.gradients = QCheckBox("calculate gradients")
        hbox.addWidget(self.gradients)
        self.vbox.addLayout(hbox)

        hbox = QHBoxLayout()
        self.track_in_agents = QCheckBox("track in agents")
        hbox.addWidget(self.track_in_agents)
        self.vbox.addLayout(hbox)

        #--------------------------
# 			<Dirichlet_boundary_condition units="dimensionless" enabled="false">0</Dirichlet_boundary_condition>
# <!--
# 			<Dirichlet_options>
# 				<boundary_value ID="xmin" enabled="false">0</boundary_value>
# 				<boundary_value ID="xmax" enabled="false">0</boundary_value>
# 				<boundary_value ID="ymin" enabled="false">0</boundary_value>
# 				<boundary_value ID="ymax" enabled="false">0</boundary_value>
# 				<boundary_value ID="zmin" enabled="false">1</boundary_value>
# 				<boundary_value ID="zmax" enabled="false">0</boundary_value>
# 			</Dirichlet_options>
# -->			
#  		</variable>


        #--------------------------
        # Dummy widget for filler??
        # label = QLabel("")
        # label.setFixedHeight(1000)
        # # label.setStyleSheet("background-color: orange")
        # label.setAlignment(QtCore.Qt.AlignCenter)
        # self.vbox.addWidget(label)

        #==================================================================
        # self.vbox.setAlignment(QtCore.Qt.AlignTop)

        # spacerItem = QSpacerItem(20, 237, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        # spacerItem = QSpacerItem(100,500)
        # self.vbox.addItem(spacerItem)
        self.vbox.addStretch()

        self.microenv_params.setLayout(self.vbox)

        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.microenv_params)


        # self.save_button = QPushButton("Save")
        # self.text = QLabel("Hello World",alignment=QtCore.Qt.AlignCenter)

        self.layout = QVBoxLayout(self)

        self.layout.addLayout(controls_hbox)

        # self.layout.addWidget(self.tabs)
        # self.layout.addWidget(QHLine())
        # self.layout.addWidget(self.params)

        # self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(splitter)

        # self.layout.addWidget(self.vbox)
        # self.layout.addWidget(self.text)
        # self.layout.addWidget(self.save_button)
        # self.save_button.clicked.connect(self.save_xml)


    @QtCore.Slot()
    def delete_substrate(self):
        print('------ delete_substrate')
        item_idx = self.tree.indexFromItem(self.tree.currentItem()).row() 
        print('------      item_idx=',item_idx)
        # self.tree.removeItemWidget(self.tree.currentItem(), 0)
        self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(self.tree.currentItem()))

        self.celldef_tab.delete_substrate_from_comboboxes(item_idx)
        print('------      new name=',self.tree.currentItem().text(0))
        self.current_substrate = self.tree.currentItem().text(0)

        self.fill_gui(self.current_substrate)
        

    # @QtCore.Slot()
    # def save_xml(self):
    #     # self.text.setText(random.choice(self.hello))
    #     pass

    # def tree_item_changed(self,idx1,idx2):
    def tree_item_changed_cb(self, it,col):
        print('tree_item_changed:', it, col, it.text(col) )
        self.current_substrate = it.text(col)
        print('self.current_substrate= ',self.current_substrate )
        # print('self.= ',self.tree.indexFromItem )

        # fill in the GUI with this one's params
        self.fill_gui(self.current_substrate)

    def populate_tree(self):
        uep = self.xml_root.find(".//microenvironment_setup")
        if uep:
            self.tree.clear()
            idx = 0
            # <microenvironment_setup>
		    #   <variable name="food" units="dimensionless" ID="0">
            for var in uep:
                # print(cell_def.attrib['name'])
                if var.tag == 'variable':
                    var_name = var.attrib['name']
                    subname = QTreeWidgetItem([var_name])
                    self.tree.insertTopLevelItem(idx,subname)
                    idx += 1

    def first_substrate_name(self):
        uep = self.xml_root.find(".//microenvironment_setup//variable")
        if uep:
                return(uep.attrib['name'])

    def fill_gui(self, substrate_name):
        # <microenvironment_setup>
		#   <variable name="food" units="dimensionless" ID="0">
        uep = self.xml_root.find('.//microenvironment_setup')  # find unique entry point

        if substrate_name == None:
            substrate_name = self.xml_root.find(".//microenvironment_setup//variable").attrib['name']

        self.substrate_name.setText(substrate_name)

        vp = []   # pointers to <variable> nodes
        if uep:
            # self.tree.clear()
            idx = 0
            for var in uep.findall('variable'):
                vp.append(var)
                # print(var.attrib['name'])
                name = var.attrib['name']
                subname = QTreeWidgetItem([name])
                # self.tree.insertTopLevelItem(idx,substrate_name)
                if subname.text(0) == substrate_name:
                    print("break out of substrate (variable) name loop with idx=",idx)
                    break
                idx += 1

        # self.tree.setCurrentItem(substrate_name,0)  # RWH/TODO: select 1st (0th?) item upon startup or loading new model

        idx += 1  # we use 1-offset indices below 

        var_param_path = self.xml_root.find(".//microenvironment_setup//variable[" + str(idx) + "]//physical_parameter_set")
        var_path = self.xml_root.find(".//microenvironment_setup//variable[" + str(idx) + "]")
        # uep = self.xml_root.find('.//microenvironment_setup')  # find unique entry point

		# <variable name="oxygen" units="mmHg" ID="0">
		# 	<physical_parameter_set>
		# 		<diffusion_coefficient units="micron^2/min">100000.0</diffusion_coefficient>
		# 		<decay_rate units="1/min">0.1</decay_rate>  
		# 	</physical_parameter_set>
		# 	<initial_condition units="mmHg">38.0</initial_condition>
		# 	<Dirichlet_boundary_condition units="mmHg" enabled="true">38.0</

        # self.substrate_name.setText(var.attrib['name'])
        self.diffusion_coef.setText(var_param_path.find('.//diffusion_coefficient').text)
        self.decay_rate.setText(var_param_path.find('.//decay_rate').text)

        self.init_cond.setText(var_path.find('.initial_condition').text)
        self.dirichlet_bc.setText(var_path.find('.Dirichlet_boundary_condition').text)

        # self.chemical_A_decay_rate.value = float(vp[0].find('.//decay_rate').text)
        # self.chemical_A_initial_condition.value = float(vp[0].find('.//initial_condition').text)
        # self.chemical_A_Dirichlet_boundary_condition.value = float(vp[0].find('.//Dirichlet_boundary_condition').text)
        # if vp[0].find('.//Dirichlet_boundary_condition').attrib['enabled'].lower() == 'true':
        #   self.chemical_A_Dirichlet_boundary_condition_toggle.value = True
        # else:
        #   self.chemical_A_Dirichlet_boundary_condition_toggle.value = False

        # self.chemical_B_diffusion_coefficient.value = float(vp[1].find('.//diffusion_coefficient').text)
        # self.chemical_B_decay_rate.value = float(vp[1].find('.//decay_rate').text)
        # self.chemical_B_initial_condition.value = float(vp[1].find('.//initial_condition').text)
        # self.chemical_B_Dirichlet_boundary_condition.value = float(vp[1].find('.//Dirichlet_boundary_condition').text)
        # if vp[1].find('.//Dirichlet_boundary_condition').attrib['enabled'].lower() == 'true':
        #   self.chemical_B_Dirichlet_boundary_condition_toggle.value = True
        # else:
        #   self.chemical_B_Dirichlet_boundary_condition_toggle.value = False

        # self.chemical_C_diffusion_coefficient.value = float(vp[2].find('.//diffusion_coefficient').text)
        # self.chemical_C_decay_rate.value = float(vp[2].find('.//decay_rate').text)
        # self.chemical_C_initial_condition.value = float(vp[2].find('.//initial_condition').text)
        # self.chemical_C_Dirichlet_boundary_condition.value = float(vp[2].find('.//Dirichlet_boundary_condition').text)
        # if vp[2].find('.//Dirichlet_boundary_condition').attrib['enabled'].lower() == 'true':
        #   self.chemical_C_Dirichlet_boundary_condition_toggle.value = True
        # else:
        #   self.chemical_C_Dirichlet_boundary_condition_toggle.value = False

        # if uep.find('.//options//calculate_gradients').text.lower() == 'true':
        #   self.calculate_gradient.value = True
        # else:
        #   self.calculate_gradient.value = False
        # if uep.find('.//options//track_internalized_substrates_in_each_agent').text.lower() == 'true':
        #   self.track_internal.value = True
        # else:
        #   self.track_internal.value = False


    #----------------------------------------------------------------------------
    # Read values from the GUI widgets and generate/write a new XML

    # 	<microenvironment_setup>
	# 	<variable name="director signal" units="dimensionless" ID="0">
	# 		<physical_parameter_set>
	# 			<diffusion_coefficient units="micron^2/min">1000</diffusion_coefficient>
	# 			<decay_rate units="1/min">.1</decay_rate>  
	# 		</physical_parameter_set>
	# 		<initial_condition units="dimensionless">0</initial_condition>
	# 		<Dirichlet_boundary_condition units="dimensionless" enabled="false">1</Dirichlet_boundary_condition>
	# 	</variable>
		
	# 	<variable name="cargo signal" units="dimensionless" ID="1">
	# 		<physical_parameter_set>
	# 			<diffusion_coefficient units="micron^2/min">1000</diffusion_coefficient>
	# 			<decay_rate units="1/min">.4</decay_rate>  
	# 		</physical_parameter_set>
	# 		<initial_condition units="dimensionless">0</initial_condition>
	# 		<Dirichlet_boundary_condition units="dimensionless" enabled="false">1</Dirichlet_boundary_condition>
	# 	</variable>
		
	# 	<options>
	# 		<calculate_gradients>true</calculate_gradients>
	# 		<track_internalized_substrates_in_each_agent>false</track_internalized_substrates_in_each_agent>
			 
	# 		<initial_condition type="matlab" enabled="false">
	# 			<filename>./config/initial.mat</filename>
	# 		</initial_condition>
			 
	# 		<dirichlet_nodes type="matlab" enabled="false">
	# 			<filename>./config/dirichlet.mat</filename>
	# 		</dirichlet_nodes>
	# 	</options>
	# </microenvironment_setup>

    def fill_xml(self):
        # pass

        uep = self.xml_root.find('.//microenvironment_setup')
        vp = []   # pointers to <variable> nodes
        if uep:
            for var in uep.findall('variable'):
                vp.append(var)

        uep = self.xml_root.find('.//microenvironment_setup')  

        # self.diffusion_coef.setText(var_param_path.find('.//diffusion_coefficient').text)
        # self.decay_rate.setText(var_param_path.find('.//decay_rate').text)

        # self.init_cond.setText(var_path.find('.initial_condition').text)
        # self.dirichlet_bc.setText(var_path.find('.Dirichlet_boundary_condition').text)

        vp[0].find('.//diffusion_coefficient').text = str(self.diffusion_coef.text)

        # vp[0].find('.//diffusion_coefficient').text = str(self.director_signal_diffusion_coefficient.value)
        # vp[0].find('.//decay_rate').text = str(self.director_signal_decay_rate.value)
        # vp[0].find('.//initial_condition').text = str(self.director_signal_initial_condition.value)
        # vp[0].find('.//Dirichlet_boundary_condition').text = str(self.director_signal_Dirichlet_boundary_condition.value)
        # vp[0].find('.//Dirichlet_boundary_condition').attrib['enabled'] = str(self.director_signal_Dirichlet_boundary_condition_toggle.value).lower()

        # vp[1].find('.//diffusion_coefficient').text = str(self.cargo_signal_diffusion_coefficient.value)
        # vp[1].find('.//decay_rate').text = str(self.cargo_signal_decay_rate.value)
        # vp[1].find('.//initial_condition').text = str(self.cargo_signal_initial_condition.value)
        # vp[1].find('.//Dirichlet_boundary_condition').text = str(self.cargo_signal_Dirichlet_boundary_condition.value)
        # vp[1].find('.//Dirichlet_boundary_condition').attrib['enabled'] = str(self.cargo_signal_Dirichlet_boundary_condition_toggle.value).lower()

        # uep.find('.//options//calculate_gradients').text = str(self.calculate_gradient.value)
        # uep.find('.//options//track_internalized_substrates_in_each_agent').text = str(self.track_internal.value)
    
    def clear_gui(self):
        pass