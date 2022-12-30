"""
pmb.py - driving module for the PhysiCell Model Builder GUI to read in a sample PhysiCell config file (.xml), easily edit (e.g., change parameter values, add/delete more "objects", including substrates and cell types), and save the updated config file. In addition, the "Studio" feature adds additional GUI tabs for creating initial conditions for cells (.csv), running a simulation, and visualizing output.

Authors:
Randy Heiland (heiland@iu.edu): lead designer and developer
Vincent Noel, Institut Curie: Cell Types|Intracellular|boolean
Dr. Paul Macklin (macklinp@iu.edu): PI, funding and testing

Macklin Lab members (grads & postdocs): testing, design, code contributions.
Many IU undergraduate students affiliated with the Macklin Lab: testing, design, code contributions.
PhysiCell community: testing, design, code contributions.
Rf. Credits.md

"""

import os
import platform
import sys
import argparse
import logging
# import shutil # for possible copy of file
from pathlib import Path
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from xml.dom import minidom
import numpy as np

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QColor, QIcon, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyleFactory

from config_tab import Config
from cell_def_tab import CellDef 
from microenv_tab import SubstrateDef 
from user_params_tab import UserParams 
# from rules_tab import Rules
from ics_tab import ICs
from populate_tree_cell_defs import populate_tree_cell_defs
from run_tab import RunModel 
from legend_tab import Legend 

try:
    from simulariumio import UnitData, MetaData, DisplayData, DISPLAY_TYPE, ModelMetaData
    from simulariumio.physicell import PhysicellConverter, PhysicellData
    simularium_installed = True
except:
    simularium_installed = False
        
# from sbml_tab import SBMLParams 

def SingleBrowse(self):
        # if len(self.csv) < 2:
    filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')

        #     if filePath != "" and not filePath in self.csv:
        #         self.csv.append(filePath)
        # print(self.csv)

def startup_notice():
    msgBox = QMessageBox()
    msgBox.setIcon(QMessageBox.Information)
    msgBox.setText("Editing the template config file from the PMB /data directory. If you want to edit another, use File->Open or File->Samples")
    msgBox.setStandardButtons(QMessageBox.Ok)

    returnValue = msgBox.exec()
    # if returnValue == QMessageBox.Ok:
    #     print('OK clicked')

def quit_cb():
    global pmb_app
    pmb_app.quit()

  
class PhysiCellXMLCreator(QWidget):
    def __init__(self, config_file, studio_flag, skip_validate_flag, rules_flag, model3D_flag, exec_file, parent = None):
        super(PhysiCellXMLCreator, self).__init__(parent)
        if model3D_flag:
            from vis3D_tab import Vis 
        else:
            from vis_tab import Vis 

        self.studio_flag = studio_flag 
        self.skip_validate_flag = skip_validate_flag 
        self.rules_flag = rules_flag 
        self.model3D_flag = model3D_flag 

        self.ics_tab_index = 4
        self.plot_tab_index = 6
        self.legend_tab_index = 7
        if self.rules_flag:
            self.plot_tab_index += 1
            self.legend_tab_index += 1

        self.dark_mode = False
        # if (platform.system().lower() == 'darwin') and ("ARM64" in platform.uname().version):
        if (platform.system().lower() == 'darwin') and (platform.machine() == 'arm64'):
            self.dark_mode = True

        self.title_prefix = "PhysiCell Model Builder: "
        if studio_flag:
            self.title_prefix = "PhysiCell Studio: "

        self.vis2D_gouraud = False

        self.nanohub_flag = False
        if( 'HOME' in os.environ.keys() ):
            self.nanohub_flag = "home/nanohub" in os.environ['HOME']

        self.p = None # Necessary to download files!

        # Menus
        vlayout = QVBoxLayout(self)
        # vlayout.setContentsMargins(5, 35, 5, 5)
        menuWidget = QWidget(self.menu())
        vlayout.addWidget(menuWidget)

        self.setLayout(vlayout)
        self.resize(1100, 770)  # width, height (height >= Cell Types|Death params)
        self.setMinimumSize(1100, 770)  #width, height of window

        self.current_dir = os.getcwd()
        print("self.current_dir = ",self.current_dir)
        logging.debug(f'self.current_dir = {self.current_dir}')
        self.pmb_root_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        self.pmb_data_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        print("self.pmb_root_dir = ",self.pmb_root_dir)
        logging.debug(f'self.pmb_root_dir = {self.pmb_root_dir}')

        # assume running from a PhysiCell root dir, but change if not
        self.config_dir = os.path.realpath(os.path.join('.', 'config'))

        if self.current_dir == self.pmb_root_dir:  # are we running from PMB root dir?
            self.config_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        print(f'self.config_dir =  {self.config_dir}')
        logging.debug(f'self.config_dir = {self.config_dir}')

        # self.pmb_config_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        # print("pmb.py: self.pmb_config_dir = ",self.pmb_config_dir)
        # sys.exit(1)

        if config_file:
            self.current_xml_file = os.path.join(self.current_dir, config_file)
            print("got config_file=",config_file)
            # sys.exit()
        else:
            # model_name = "interactions"  # for testing latest xml
            model_name = "template"
            # model_name = "test1"
            # model_name = "interactions"

            # bin_dir = os.path.dirname(os.path.abspath(__file__))
            # data_dir = os.path.join(bin_dir,'..','data')
            # data_dir = os.path.normpath(data_dir)
            # data_dir = os.path.join(self.current_dir,'data')

            # self.current_xml_file = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data', 'template.xml'))
            self.current_xml_file = os.path.join(self.pmb_data_dir, model_name + ".xml")


        # NOTE! We operate *directly* on a default .xml file, not a copy.
        self.setWindowTitle(self.title_prefix + self.current_xml_file)
        self.config_file = self.current_xml_file  # to Save

        self.tree = ET.parse(self.config_file)
        self.xml_root = self.tree.getroot()


        self.num_models = 0
        self.model = {}  # key: name, value:[read-only, tree]

        self.config_tab = Config(self.studio_flag)
        self.config_tab.xml_root = self.xml_root
        self.config_tab.fill_gui()

        self.microenv_tab = SubstrateDef()
        self.microenv_tab.xml_root = self.xml_root
        substrate_name = self.microenv_tab.first_substrate_name()
        # print("pmb.py: first_substrate_name=",substrate_name)
        self.microenv_tab.populate_tree()  # rwh: both fill_gui and populate_tree??

        # self.tab2.tree.setCurrentItem(QTreeWidgetItem,0)  # item

        self.celldef_tab = CellDef(self.dark_mode)
        self.celldef_tab.xml_root = self.xml_root

        cd_name = self.celldef_tab.first_cell_def_name()
        # print("pmb.py: first_cell_def_name=",cd_name)
        logging.debug(f'pmb.py: first_cell_def_name= {cd_name}')
        # self.celldef_tab.populate_tree()
        self.celldef_tab.config_path = self.current_xml_file

        self.celldef_tab.fill_substrates_comboboxes() # do before populate? Yes, assuming we check for cell_def != None

        # Beware: this may set the substrate chosen for Motility/[Advanced]Chemotaxis
        populate_tree_cell_defs(self.celldef_tab, self.skip_validate_flag)
        # self.celldef_tab.customdata.param_d = self.celldef_tab.param_d

        # print("\n\n---- pmb: post populate_tree_cell_defs():")
        # print(self.celldef_tab.param_d)

        # self.celldef_tab.fill_substrates_comboboxes() # do before populate?
        self.celldef_tab.fill_celltypes_comboboxes()

        self.microenv_tab.celldef_tab = self.celldef_tab

        self.user_params_tab = UserParams(self.dark_mode)
        self.user_params_tab.xml_root = self.xml_root
        self.user_params_tab.fill_gui()

        print("pmb.py: ",self.xml_root.find(".//cell_definitions//cell_rules"))
        # if self.xml_root.find(".//cell_definitions//cell_rules"):

        # self.sbml_tab = SBMLParams()
        # self.sbml_tab.xml_root = self.xml_root
        # self.sbml_tab.fill_gui()

        # if studio_flag:
        #     self.run_tab = RunModel(self.nanohub_flag, self.tabWidget, self.download_menu)
        #     self.current_dir = os.getcwd()
        #     print("model.py: self.current_dir = ",self.current_dir)
        #     self.run_tab.current_dir = self.current_dir
        #     self.run_tab.config_tab = self.config_tab
        #     self.run_tab.microenv_tab = self.microenv_tab 
        #     self.run_tab.celldef_tab = self.celldef_tab
        #     self.run_tab.user_params_tab = self.user_params_tab
        #     self.run_tab.tree = self.tree

        #------------------
        self.tabWidget = QTabWidget()
        stylesheet = """ 
            QTabBar::tab:selected {background: orange;}  # dodgerblue

            QLabel {
                color: #000000;
                background-color: #FFFFFF; 
            }
            QPushButton {
                color: #000000;
                background-color: #FFFFFF; 
            }
            """

        self.tabWidget.setStyleSheet(stylesheet)
        self.tabWidget.addTab(self.config_tab,"Config Basics")
        self.tabWidget.addTab(self.microenv_tab,"Microenvironment")
        self.tabWidget.addTab(self.celldef_tab,"Cell Types")
        self.tabWidget.addTab(self.user_params_tab,"User Params")

        self.current_dir = os.getcwd()
        # print("pmb.py: self.current_dir = ",self.current_dir)
        logging.debug(f'pmb.py: self.current_dir = {self.current_dir}')

        if self.rules_flag:
            self.rules_tab = Rules(self.microenv_tab, self.celldef_tab)
            # self.rules_tab.fill_gui()
            self.tabWidget.addTab(self.rules_tab,"Rules")
            self.rules_tab.xml_root = self.xml_root
            self.rules_tab.fill_gui()


        if self.studio_flag:
            logging.debug(f'pmb.py: creating ICs, Run, and Plot tabs')
            self.ics_tab = ICs(self.config_tab, self.celldef_tab)
            self.ics_tab.fill_celltype_combobox()
            self.ics_tab.reset_info()
            self.celldef_tab.ics_tab = self.ics_tab
            # self.rules_tab.fill_gui()
            self.tabWidget.addTab(self.ics_tab,"ICs")

            self.run_tab = RunModel(self.nanohub_flag, self.tabWidget, self.rules_flag, self.download_menu)
            # self.run_tab.config_xml_name.setText(current_xml_file)
            self.run_tab.exec_name.setText(exec_file)
            self.run_tab.config_xml_name.setText(self.current_xml_file)
            # self.current_dir = os.getcwd()
            self.run_tab.current_dir = self.current_dir
            self.run_tab.config_tab = self.config_tab
            self.run_tab.microenv_tab = self.microenv_tab 
            self.run_tab.celldef_tab = self.celldef_tab
            self.run_tab.user_params_tab = self.user_params_tab
            if self.rules_flag:
                self.run_tab.rules_tab = self.rules_tab
            self.run_tab.tree = self.tree

            self.run_tab.config_file = self.current_xml_file
            self.run_tab.config_xml_name.setText(self.current_xml_file)

            self.tabWidget.addTab(self.run_tab,"Run")

            self.vis_tab = Vis(self.nanohub_flag)
            self.config_tab.vis_tab = self.vis_tab
            # self.vis_tab.output_dir = self.config_tab.folder.text()
            self.vis_tab.update_output_dir(self.config_tab.folder.text())
            self.vis_tab.config_tab = self.config_tab
            # self.vis_tab.output_dir = self.config_tab.plot_folder.text()

            self.legend_tab = Legend(self.nanohub_flag)
            self.legend_tab.current_dir = self.current_dir
            self.legend_tab.pmb_data_dir = self.pmb_data_dir
            self.run_tab.vis_tab = self.vis_tab
            # self.vis_tab.setEnabled(False)
            # self.vis_tab.nanohub_flag = self.nanohub_flag
            # self.vis_tab.xml_root = self.xml_root
            self.tabWidget.addTab(self.vis_tab,"Plot")
            # self.tabWidget.setTabEnabled(5, False)
            self.enablePlotTab(False)
            self.enablePlotTab(True)

            self.tabWidget.addTab(self.legend_tab,"Legend")
            self.enableLegendTab(False)
            self.enableLegendTab(True)
            self.run_tab.vis_tab = self.vis_tab
            self.run_tab.legend_tab = self.legend_tab
            logging.debug(f'pmb.py: calling vis_tab.substrates_cbox_changed_cb(2)')
            self.vis_tab.fill_substrates_combobox(self.celldef_tab.substrate_list)
            # self.vis_tab.substrates_cbox_changed_cb(2)   # doesn't accomplish it; need to set index, but not sure when
            self.vis_tab.init_plot_range(self.config_tab)

            # self.vis_tab.output_dir = self.config_tab.folder.text()
            self.vis_tab.update_output_dir(self.config_tab.folder.text())
            self.legend_tab.output_dir = self.config_tab.folder.text()
            legend_file = os.path.join(self.vis_tab.output_dir, 'legend.svg')  # hardcoded filename :(
            if Path(legend_file).is_file():
                self.legend_tab.reload_legend()

            self.vis_tab.reset_model()
            


        vlayout.addWidget(self.tabWidget)
        # self.addTab(self.sbml_tab,"SBML")

        self.tabWidget.setCurrentIndex(0)  # Config (default)
        # self.tabWidget.setCurrentIndex(1)  # rwh/debug: select Microenv
        # self.tabWidget.setCurrentIndex(2)  # rwh/debug: select Cell Types


    def about_pyqt(self):
        msgBox = QMessageBox()
        msgBox.setTextFormat(Qt.RichText)
        about_text = """ 
PhysiCell Studio is developed using PyQt5.<br><br>

For licensing information:<br>
<a href="https://github.com/PyQt5/PyQt/blob/master/LICENSE">github.com/PyQt5/PyQt/blob/master/LICENSE</a>

        """
        msgBox.setText(about_text)
        msgBox.setStandardButtons(QMessageBox.Ok)
        returnValue = msgBox.exec()

    def about_studio(self):
        msgBox = QMessageBox()
        # font = QFont()
        # font.setBold(True)
        # msgBox.setFont(font)
        msgBox.setTextFormat(Qt.RichText)
        # msgBox.setIcon(QMessageBox.Information)
        version_file =  os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'VERSION.txt'))
        try:
            with open(version_file) as f:
                v = f.readline()
        except:
            v = "(can't find VERSION.txt)\n"
            print("Unable to open ",version_file)
        about_text = "Version " + v + """ <br><br>
PhysiCell Studio is a tool to provide graphical editing of a PhysiCell model and, optionally, run a model and visualize results. &nbsp; It is lead by the Macklin Lab (Indiana University) with contributions from the PhysiCell community.<br><br>

NOTE: When loading a model (.xml configuration file), it must be a "flat" format for the  cell_definitions, i.e., all parameters need to be defined. &nbsp; Many legacy PhysiCell models used a hierarchical format in which a cell_definition could inherit from a parent. &nbsp; The hierarchical format is not supported in the Studio.<br><br>

For more information:<br>
<a href="https://github.com/PhysiCell-Tools/PhysiCell-model-builder">github.com/PhysiCell-Tools/PhysiCell-model-builder</a><br>
<a href="https://github.com/MathCancer/PhysiCell">https://github.com/MathCancer/PhysiCell</a><br>
<br>
PhysiCell Studio is provided "AS IS" without warranty of any kind. &nbsp; In no event shall the Authors be liable for any damages whatsoever.<br>
        """
        msgBox.setText(about_text)
        # msgBox.setInformativeText(about_text)
        # msgBox.setDetailedText(about_text)
        # msgBox.setText("PhysiCell Studio is a tool to provide easy editing of a PhysiCell model and, optionally, run a model and visualize results.")
        msgBox.setStandardButtons(QMessageBox.Ok)
        # msgBox.buttonClicked.connect(msgButtonClick)

        returnValue = msgBox.exec()

    def enablePlotTab(self, bval):
        # self.tabWidget.setTabEnabled(5, bval)
        self.tabWidget.setTabEnabled(self.plot_tab_index, bval)

    def enableLegendTab(self, bval):
        # self.tabWidget.setTabEnabled(6, bval)   
        # self.tabWidget.setTabEnabled(6, bval)   
        self.tabWidget.setTabEnabled(self.legend_tab_index, bval)


    def menu(self):
        menubar = QMenuBar(self)
        menubar.setNativeMenuBar(False)

        #--------------
        studio_menu = menubar.addMenu('&Studio')
        studio_menu.addAction("About", self.about_studio)
        studio_menu.addAction("About PyQt", self.about_pyqt)
        # studio_menu.addAction("Preferences", self.prefs_cb)
        studio_menu.addSeparator()
        studio_menu.addAction("Quit", quit_cb)

        #--------------
        file_menu = menubar.addMenu('&File')

        # file_menu.addAction("New (template)", self.new_model_cb, QtGui.QKeySequence('Ctrl+n'))
        file_menu.addAction("Open", self.open_as_cb, QtGui.QKeySequence('Ctrl+o'))
        # file_menu.addAction("Save mymodel.xml", self.save_cb, QtGui.QKeySequence('Ctrl+s'))
        file_menu.addAction("Save as", self.save_as_cb)
        file_menu.addAction("Save", self.save_cb, QtGui.QKeySequence('Ctrl+s'))

        #--------------
        export_menu = file_menu.addMenu("Export")

        simularium_act = QAction('Simularium', self)
        export_menu.addAction(simularium_act)
        simularium_act.triggered.connect(self.simularium_cb)
        if not self.studio_flag:
            print("simularium_installed is ",simularium_installed)
            export_menu.setEnabled(False)

        #--------------
        file_menu.addSeparator()
        samples_menu = file_menu.addMenu("Samples")

        template_act = QAction('template', self)
        samples_menu.addAction(template_act)
        template_act.triggered.connect(self.template_cb)

        biorobots_act = QAction('biorobots', self)
        samples_menu.addAction(biorobots_act)
        biorobots_act.triggered.connect(self.biorobots_cb)

        cancer_biorobots_act = QAction('cancer biorobots', self)
        samples_menu.addAction(cancer_biorobots_act)
        cancer_biorobots_act.triggered.connect(self.cancer_biorobots_cb)

        hetero_act = QAction('heterogeneity', self)
        samples_menu.addAction(hetero_act)
        hetero_act.triggered.connect(self.hetero_cb)

        pred_prey_act = QAction('predator-prey-farmer', self)
        samples_menu.addAction(pred_prey_act)
        pred_prey_act.triggered.connect(self.pred_prey_cb)

        virus_mac_act = QAction('virus-macrophage', self)
        samples_menu.addAction(virus_mac_act)
        virus_mac_act.triggered.connect(self.virus_mac_cb)

        worm_act = QAction('worm', self)
        samples_menu.addAction(worm_act)
        worm_act.triggered.connect(self.worm_cb)

        interactions_act = QAction('interactions', self)
        samples_menu.addAction(interactions_act)
        interactions_act.triggered.connect(self.interactions_cb)

        cancer_immune_act = QAction('cancer immune (3D)', self)
        samples_menu.addAction(cancer_immune_act)
        cancer_immune_act.triggered.connect(self.cancer_immune_cb)

        physiboss_cell_lines_act = QAction('PhysiBoSS cell lines', self)
        samples_menu.addAction(physiboss_cell_lines_act)
        physiboss_cell_lines_act.triggered.connect(self.physiboss_cell_lines_cb)

        subcell_act = QAction('subcellular', self)
        # samples_menu.addAction(subcell_act)
        subcell_act.triggered.connect(self.subcell_cb)

        covid19_act = QAction('covid19_v5', self)
        # samples_menu.addAction(covid19_act)
        covid19_act.triggered.connect(self.covid19_cb)

        test_gui_act = QAction('test-gui', self)
        # samples_menu.addAction(test_gui_act)
        test_gui_act.triggered.connect(self.test_gui_cb)

        if self.nanohub_flag:
            self.download_menu = file_menu.addMenu('Download')
            self.download_config_item = self.download_menu.addAction("Download config.xml", self.download_config_cb)
            self.download_svg_item = self.download_menu.addAction("Download SVG", self.download_svg_cb)
            self.download_mat_item = self.download_menu.addAction("Download binary (.mat) data", self.download_full_cb)
            # self.download_menu_item.setEnabled(False)
            self.download_menu.setEnabled(False)
        else:
            self.download_menu = None

        #-------------------------
        if self.model3D_flag:
            view3D_menu = menubar.addMenu('&View')
            view3D_menu.triggered.connect(self.view3D_cb)

        # file_menu.addAction("XY plane", self.open_as_cb, QtGui.QKeySequence('Ctrl+o'))
            # xy_act = view3D_menu.addAction("XY plane", self.xy_plane_cb)
            xy_act = view3D_menu.addAction("XY plane")
            xy_act.setCheckable(True)
            xy_act.setChecked(True)

            yz_act = view3D_menu.addAction("YZ plane")
            yz_act.setCheckable(True)
            yz_act.setChecked(True)

            xz_act = view3D_menu.addAction("XZ plane")
            xz_act.setCheckable(True)
            xz_act.setChecked(True)

            voxels_act = view3D_menu.addAction("All voxels")
            voxels_act.setCheckable(True)
            voxels_act.setChecked(False)

            # contour_act = view3D_menu.addAction("contour")
            # contour_act.setCheckable(True)
            # contour_act.setChecked(False)

        else:  # just 2D view
            if self.studio_flag:
                view_menu = menubar.addMenu('&View')
                view_menu.addAction("toggle shading", self.toggle_2D_shading_cb, QtGui.QKeySequence('Ctrl+g'))
                view_menu.addAction("toggle voxel grid", self.toggle_2D_voxel_grid_cb)
                view_menu.addAction("toggle mech grid", self.toggle_2D_mech_grid_cb)
                view_menu.addSeparator()
                view_menu.addAction("Select output dir", self.select_plot_output_cb)

        menubar.adjustSize()  # Argh. Otherwise, only 1st menu appears, with ">>" to others!

    #-----------------------------------------------------------------
    # Not currently used
    # def add_new_model(self, name, read_only):
    #     # does it already exist? If so, return
    #     if name in self.model.keys():
    #         print("add_new_model: model already exists, just return (dict)= ",self.model)
    #         return
    #     self.model[name] = read_only
    #     self.num_models += 1
    #     print("add_new_model: self.model (dict)= ",self.model)

    #     # models_menu_act = QAction(name, self)
    #     # self.models_menu.addAction(models_menu_act)
    #     # models_menu_act.triggered.connect(self.select_current_model_cb)

    #     print("add_new_model: title suffix= ",name)
    #     self.setWindowTitle(self.title_prefix + name)

    # Probably not used unless we later implement it
    # def select_current_model_cb(self):
    #     # models_menu_act = QtGui.QAction(name, self)
    #     # self.models_menu.addAction(models_menu_act)
    #     model_act = self.models_menu.menuAction()
    #     print('select_current_model_cb: ',model_act)
    #     action = self.sender()
    #     model_name = action.text()
    #     print('select_current_model_cb: title suffix name= ',model_name)

    #     self.setWindowTitle(self.title_prefix + model_name)

    def reset_xml_root(self):
        self.celldef_tab.clear_custom_data_tab()
        self.celldef_tab.param_d.clear()  # seems unnecessary as being done in populate_tree. argh.
        self.celldef_tab.current_cell_def = None
        self.celldef_tab.cell_adhesion_affinity_celltype = None

        # self.microenv_tab.param_d.clear()

        self.xml_root = self.tree.getroot()
        self.config_tab.xml_root = self.xml_root
        self.microenv_tab.xml_root = self.xml_root
        self.celldef_tab.xml_root = self.xml_root
        self.user_params_tab.xml_root = self.xml_root
        if self.rules_flag:
            self.rules_tab.xml_root = self.xml_root
            self.rules_tab.fill_gui()

        self.config_tab.fill_gui()

        self.microenv_tab.clear_gui()
        self.microenv_tab.populate_tree()
        # self.microenv_tab.fill_gui(None)
        # self.microenv_tab.fill_gui()
        # self.celldef_tab.clear_gui()

        # self.celldef_tab.clear_custom_data_params()

        # self.celldef_tab.fill_substrates_comboboxes()
        # self.celldef_tab.populate_tree()
        self.celldef_tab.config_path = self.current_xml_file
        self.celldef_tab.fill_substrates_comboboxes()   # do before populate_tree_cell_defs
        populate_tree_cell_defs(self.celldef_tab, self.skip_validate_flag)
        # self.celldef_tab.fill_gui(None)
        # self.celldef_tab.customize_cycle_choices() #rwh/todo: needed? 
        # self.celldef_tab.fill_substrates_comboboxes()
        self.celldef_tab.fill_celltypes_comboboxes()

        if self.studio_flag:
            self.ics_tab.reset_info()

        self.microenv_tab.celldef_tab = self.celldef_tab

        self.user_params_tab.clear_gui()
        self.user_params_tab.fill_gui()

    def show_sample_model(self):
        logging.debug(f'pmb: show_sample_model(): self.config_file = {self.config_file}')
        print(f'pmb: show_sample_model(): self.config_file = {self.config_file}')
        # self.config_file = "config_samples/biorobots.xml"
        self.tree = ET.parse(self.config_file)
        # self.xml_root = self.tree.getroot()
        self.reset_xml_root()
        self.setWindowTitle(self.title_prefix + self.config_file)
        # self.config_tab.fill_gui(self.xml_root)  # 
        # self.microenv_tab.fill_gui(self.xml_root)  # microenv
        # self.celldef_tab.fill_gui("foobar")  # cell defs
        # self.celldef_tab.fill_motility_substrates()

    def open_as_cb(self):
        # filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')
        filePath = QFileDialog.getOpenFileName(self,'',".")
        # print("\n\nopen_as_cb():  filePath=",filePath)
        full_path_model_name = filePath[0]
        print("\n\nopen_as_cb():  full_path_model_name =",full_path_model_name )
        logging.debug(f'\npmb.py: open_as_cb():  full_path_model_name ={full_path_model_name}')
        # if (len(full_path_model_name) > 0) and Path(full_path_model_name):
        if (len(full_path_model_name) > 0) and Path(full_path_model_name).is_file():
            print("open_as_cb():  filePath is valid")
            logging.debug(f'     filePath is valid')
            print("len(full_path_model_name) = ", len(full_path_model_name) )
            logging.debug(f'     len(full_path_model_name) = {len(full_path_model_name)}' )
            # fname = os.path.basename(full_path_model_name)
            self.current_xml_file = full_path_model_name

            # self.add_new_model(self.current_xml_file, True)
            self.config_file = self.current_xml_file
            if self.studio_flag:
                self.run_tab.config_file = self.current_xml_file
                self.run_tab.config_xml_name.setText(self.current_xml_file)
            self.show_sample_model()

        else:
            print("open_as_cb():  full_path_model_name is NOT valid")


    def indent(elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def prettify(self, elem):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="",  newl="")  # newl="\n"

    def save_as_cb(self):
        # print("------ save_as_cb():")
        # filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')
        filePath = QFileDialog.getSaveFileName(self,'',".")
        # filePath = QFileDialog.getSaveFileName(self,'Save file',".",".xml")
        print("save_as_cb():  filePath=",filePath)
        full_path_model_name = filePath[0]
        print("save_as_cb():  full_path_model_name =",full_path_model_name )
        if (len(full_path_model_name) > 0) and Path(full_path_model_name):
            print("save_as_cb():  filePath is valid")
            print("len(full_path_model_name) = ", len(full_path_model_name) )
            # self.current_save_file = full_path_model_name
            self.current_xml_file = full_path_model_name
        else:
            return

        try:
            # self.celldef_tab.config_path = self.current_save_file
            self.celldef_tab.config_path = self.current_xml_file
            self.config_tab.fill_xml()
            self.microenv_tab.fill_xml()
            self.celldef_tab.fill_xml()
            self.user_params_tab.fill_xml()
            if self.rules_flag:
                self.rules_tab.fill_xml()

            # out_file = "mymodel.xml"
            # out_file = full_path_model_name 
            # out_file = self.current_save_file
            # xml_file = self.current_xml_file
            # print("--- xml_file =",xml_file )
            
            self.setWindowTitle(self.title_prefix + self.current_xml_file)

            # print("\n\n ===================================")
            print("pmb.py:  save_as_cb: writing to: ",self.current_xml_file)

            self.tree.write(self.current_xml_file)

        except Exception as e:
            self.show_error_message(str(e) + " : save_as_cb(): Error: Please finish the definition before saving.")

    def save_cb(self):
        try:
            # self.celldef_tab.config_path = self.current_save_file
            self.celldef_tab.config_path = self.current_xml_file
            self.config_file = self.current_xml_file
            self.config_tab.fill_xml()
            self.microenv_tab.fill_xml()
            self.celldef_tab.fill_xml()
            self.user_params_tab.fill_xml()
            if self.rules_flag:
                self.rules_tab.fill_xml()

            # filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')
            # print("pmb.py:  save_cb: writing to: ",self.config_file)

            # out_file = self.config_file
            # out_file = "mymodel.xml"
            # out_file = self.current_save_file
            # xml_file = self.current_xml_file
            self.setWindowTitle(self.title_prefix + self.current_xml_file)

            # print("\n\n ===================================")
            # print("pmb.py:  save_cb: writing to: ",out_file)
            print("pmb.py:  save_cb: writing to: ",self.current_xml_file)

            # self.tree.write(self.config_file)
            # root = ET.fromstring("<fruits><fruit>banana</fruit><fruit>apple</fruit></fruits>""")
            # tree = ET.ElementTree(root)
            # ET.indent(self.tree)  # ugh, only in 3.9
            # root = ET.tostring(self.tree)
            # self.indent(self.tree)
            # self.indent(root)

            # rwh: ARGH, doesn't work
            # root = self.tree.getroot()
            # out_str = self.prettify(root)
            # print(out_str)


            # self.tree.write(out_file)  # originally
            self.tree.write(self.current_xml_file)

            # # new: pretty print
            # root = self.tree.getroot()
            # # return reparsed.toprettyxml(indent="",  newl="")  # newl="\n"
            # # long_str = ET.tostring(root)
            # # print("len(long_str)= ",len(long_str))
            # # # bstr = bytearray(long_str.replace(" ",""))
            # # # bstr = str.encode(long_str.replace("\n",""))
            # # bstr = str.encode(long_str)
            # # xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent=" ",newl="")
            # # xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(newl="")
            # # xmlstr2 = minidom.parseString(xmlstr).toprettyxml(indent=" ",newl="")
            # xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
            # # xmlstr = minidom.parseString(bstr).toprettyxml(indent=" ")
            # with open(out_file, "w") as f:
            #     f.write(xmlstr)

            # rwh NOTE: after saving the .xml, do we need to read it back in to reflect changes.
            # self.tree = ET.parse(self.config_file)
            # self.xml_root = self.tree.getroot()
            # self.reset_xml_root()
    
        except Exception as e:
            self.show_error_message(str(e) + " : save_cb(): Error: Please finish the definition before saving.")

    def validate_cb(self):  # not used currently
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Validation not yet implemented.")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        returnValue = msgBox.exec()
        # if returnValue == QMessageBox.Ok:
            # print('OK clicked')

    def toggle_2D_shading_cb(self):
        self.vis2D_gouraud = not self.vis2D_gouraud
        if self.vis2D_gouraud:
            self.vis_tab.shading_choice = 'gouraud'
        else:
            self.vis_tab.shading_choice = 'auto'
        self.vis_tab.update_plots()

    def toggle_2D_voxel_grid_cb(self):
        self.vis_tab.show_voxel_grid = not self.vis_tab.show_voxel_grid
        self.vis_tab.update_plots()

    def toggle_2D_mech_grid_cb(self):
        self.vis_tab.show_mech_grid = not self.vis_tab.show_mech_grid
        self.vis_tab.update_plots()

    def select_plot_output_cb(self):
        # filePath = QFileDialog.getOpenFileName(self,'',".")
        dir_path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        print("\n\nselect_plot_output_cb():  dir_path=",dir_path)
        # full_path_model_name = dirPath[0]
        # print("\n\nselect_plot_output_cb():  full_path_model_name =",full_path_model_name )
        # logging.debug(f'\npmb.py: select_plot_output_cb():  full_path_model_name ={full_path_model_name}')
        # if (len(full_path_model_name) > 0) and Path(full_path_model_name).is_dir():
        if dir_path == "":
            return
        if Path(dir_path).is_dir():
            print("select_plot_output_cb():  dir_path is valid")
            logging.debug(f'select_plot_output_cb():  dir_path is valid')
            # print("len(full_path_model_name) = ", len(full_path_model_name) )
            # logging.debug(f'     len(full_path_model_name) = {len(full_path_model_name)}' )
            # fname = os.path.basename(full_path_model_name)
            # self.current_xml_file = full_path_model_name

            # self.add_new_model(self.current_xml_file, True)
            # self.config_file = self.current_xml_file
            # if self.studio_flag:
            #     self.run_tab.config_file = self.current_xml_file
            #     self.run_tab.config_xml_name.setText(self.current_xml_file)
            # self.show_sample_model()

            # self.vis_tab.output_dir = self.config_tab.folder.text()
            # self.legend_tab.output_dir = self.config_tab.folder.text()
            # self.vis_tab.output_dir = dir_path
            self.vis_tab.update_output_dir(dir_path)
            self.legend_tab.output_dir = dir_path
            legend_file = os.path.join(self.vis_tab.output_dir, 'legend.svg')  # hardcoded filename :(
            if Path(legend_file).is_file():
                self.legend_tab.reload_legend()
            else:
                self.legend_tab.clear_legend()

            self.vis_tab.reset_model()
            self.vis_tab.update_plots()

        else:
            print("select_plot_output_cb():  full_path_model_name is NOT valid")


    # -------- relevant to vis3D -----------
    def view3D_cb(self, action):
        logging.debug(f'pmb.py: view3D_cb: {action.text()}, {action.isChecked()}')
        if "XY" in action.text():
            self.vis_tab.xy_plane_toggle_cb(action.isChecked())
        elif "YZ" in action.text():
            self.vis_tab.yz_plane_toggle_cb(action.isChecked())
        elif "XZ" in action.text():
            self.vis_tab.xz_plane_toggle_cb(action.isChecked())
        elif "voxels" in action.text():
            self.vis_tab.voxels_toggle_cb(action.isChecked())
        elif "axes" in action.text():
            pass
        elif "contour" in action.text():
            pass
        return

    def show_error_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.setFixedWidth(500)
        msg.exec_()


    def load_model(self,name):
        if self.studio_flag:
            self.run_tab.cancel_model_cb()  # if a sim is already running, cancel it

        os.chdir(self.current_dir)  # just in case we were in /tmpdir (and it crashed/failed, leaving us there)

        # data_dir = os.path.join(self.current_dir,'data')
        # self.current_xml_file = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data', 'template.xml'))
        # self.current_xml_file = os.path.join(self.pmb_config_dir, name + ".xml")
        # self.current_xml_file = os.path.join(self.config_dir, name + ".xml")
        self.current_xml_file = os.path.join(self.pmb_data_dir, name + ".xml")
        logging.debug(f'pmb.py: load_model(): self.current_xml_file= {self.current_xml_file}')

        logging.debug(f'pmb.py: load_model(): {self.xml_root.find(".//cell_definitions//cell_rules")}')
        print(f'pmb.py: load_model(): {self.xml_root.find(".//cell_definitions//cell_rules")}')

        # if self.xml_root.find(".//cell_definitions//cell_rules"):
        # self.current_save_file = current_xml_file
        if self.studio_flag:
            self.run_tab.config_xml_name.setText(self.current_xml_file)
            self.run_tab.config_file = self.current_xml_file

        self.config_file = self.current_xml_file
        self.show_sample_model()
        if self.nanohub_flag:  # rwh - test if works on nanoHUB
            self.config_tab.folder.setText('.')

    #----------------------
    def simularium_cb(self):
        # print("---- Simularium export coming soon...")
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        # msgBox.setText("Simularium export coming soon." + "simularium_installed is " + str(simularium_installed))
        if not simularium_installed:
            msgBox.setText("The simulariumio module is not installed. You can try to: pip install simulariumio")
            msgBox.setStandardButtons(QMessageBox.Ok)
            # returnValue = msgBox.exec()
            return
        # if returnValue == QMessageBox.Ok:
            # print('OK clicked')
            
        msgBox.setText("Proceed to generate a Simularium object from your output data?")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        returnValue = msgBox.exec()
        if returnValue == QMessageBox.Cancel:
            return

        # self.vis_tab.output_dir = self.config_tab.folder.text()
        sim_output_dir = os.path.realpath(os.path.join('.', self.config_tab.folder.text()))
        print("sim_output_dir = ",sim_output_dir )

        simularium_model_data = PhysicellData(
            timestep=1.0,
            path_to_output_dir=sim_output_dir, 
            meta_data=MetaData(
                box_size=np.array([1000.0, 1000.0, 20.0]),
                scale_factor=0.01,
                trajectory_title="Some parameter set",
                model_meta_data=ModelMetaData(
                    title="worm",
                    version="8.1",
                    authors="A Modeler",
                    description=(
                        "A PhysiCell model run with some parameter set"
                    ),
                    doi="10.1016/j.bpj.2016.02.002",
                    source_code_url="https://github.com/allen-cell-animated/simulariumio",
                    source_code_license_url="https://github.com/allen-cell-animated/simulariumio/blob/main/LICENSE",
                    input_data_url="https://allencell.org/path/to/native/engine/input/files",
                    raw_output_data_url="https://allencell.org/path/to/native/engine/output/files",
                ),
            ),
            nth_timestep_to_read=1,
            display_data={
                0: DisplayData(
                    name="cell type 0",
                    color="#dfdacd",
                ),
                1: DisplayData(
                    name="cell type 1",
                    color="#0080ff",
                ),
            },
            time_units=UnitData("m"),  # minutes
        )

        print("calling Simularium PhysicellConverter...\n")
        PhysicellConverter(simularium_model_data).save("simularium_model")

        print("Load this model at: https://simularium.allencell.org/viewer")


    #----------------------
    def template_cb(self):
        self.load_model("template")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./template')

    def biorobots_cb(self):
        self.load_model("biorobots_flat")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./biorobots')

    def cancer_biorobots_cb(self):
        self.load_model("cancer_biorobots_flat")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./cancer_biorobots')

    def hetero_cb(self):
        self.load_model("heterogeneity")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./heterogeneity')

    def pred_prey_cb(self):
        self.load_model("pred_prey_flat")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./pred_prey')

    def virus_mac_cb(self):
        self.load_model("virus_macrophage_flat")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./virus-sample')

    def worm_cb(self):
        self.load_model("worm")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./worm')

    def interactions_cb(self):
        self.load_model("interactions")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./interaction_demo')

    def cancer_immune_cb(self):
        self.load_model("cancer_immune3D_flat")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./cancer_immune_3D')

    def physiboss_cell_lines_cb(self):
        self.load_model("physiboss_cell_lines_flat")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./PhysiBoSS_Cell_Lines')

    # def template3D_cb(self):
    #     name = "template3D_flat"
    #     self.add_new_model(name, True)
    #     self.config_file = "config_samples/" + name + ".xml"
    #     self.show_sample_model()

    def subcell_cb(self):
        self.load_model("subcellular_flat")

    def covid19_cb(self):
        self.load_model("covid19_v5_flat")

    def test_gui_cb(self):
        self.load_model("test-gui")

    #-----------------------------------------------------------------
    # Used for downloading config file and output files from nanoHUB
    def message(self, s):
        # self.text.appendPlainText(s)
        print('pmb.py: message(): ',s)

    def handle_stderr(self):
        data = self.p.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        self.message(stderr)

    def handle_stdout(self):
        data = self.p.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.message(stdout)

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: 'Not running',
            QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]
        self.message(f"State changed: {state_name}")

    def process_finished(self):
        self.message("Download process finished.")
        print("-- download finished.")
        self.p = None

    def download_config_cb(self):
        if self.nanohub_flag:
            if self.p is None:  # No process running.
                self.p = QProcess()
                self.p.readyReadStandardOutput.connect(self.handle_stdout)
                self.p.readyReadStandardError.connect(self.handle_stderr)
                self.p.stateChanged.connect(self.handle_state)
                self.p.finished.connect(self.process_finished)  # Clean up once complete.

                self.p.start("exportfile config.xml")
        return

    def download_svg_cb(self):
        if self.nanohub_flag:
            if self.p is None:  # No process running.
                self.p = QProcess()
                self.p.readyReadStandardOutput.connect(self.handle_stdout)
                self.p.readyReadStandardError.connect(self.handle_stderr)
                self.p.stateChanged.connect(self.handle_state)
                self.p.finished.connect(self.process_finished)  # Clean up once complete.

                # file_str = os.path.join(self.output_dir, '*.svg')
                file_str = "*.svg"
                print('-------- download_svg_cb(): zip up all ',file_str)
                with zipfile.ZipFile('svg.zip', 'w') as myzip:
                    for f in glob.glob(file_str):
                        myzip.write(f, os.path.basename(f))   # 2nd arg avoids full filename 
                self.p.start("exportfile svg.zip")
        return

    def download_full_cb(self):
        if self.nanohub_flag:
            if self.p is None:  # No process running.
                self.p = QProcess()
                self.p.readyReadStandardOutput.connect(self.handle_stdout)
                self.p.readyReadStandardError.connect(self.handle_stderr)
                self.p.stateChanged.connect(self.handle_state)
                self.p.finished.connect(self.process_finished)  # Clean up once complete.

                # file_xml = os.path.join(self.output_dir, '*.xml')
                # file_mat = os.path.join(self.output_dir, '*.mat')
                file_xml = '*.xml'
                file_mat = '*.mat'
                print('-------- download_full_cb(): zip up all .xml and .mat')
                with zipfile.ZipFile('mcds.zip', 'w') as myzip:
                    for f in glob.glob(file_xml):
                        myzip.write(f, os.path.basename(f)) # 2nd arg avoids full filename path in the archive
                    for f in glob.glob(file_mat):
                        myzip.write(f, os.path.basename(f))
                self.p.start("exportfile mcds.zip")
        return
    #-----------------------------------------------------------------
		
# def main():
#     app = QApplication(sys.argv)
#     ex = PhysiCellXMLCreator()
#     # ex.setGeometry(100,100, 800,600)
#     ex.show()
#     sys.exit(app.exec_())

pmb_app = None
def main():
    global pmb_app
    # inputfile = ''
    config_file = None
    studio_flag = False
    model3D_flag = False
    rules_flag = False
    skip_validate_flag = False
    try:
        parser = argparse.ArgumentParser(description='PhysiCell Model Builder (and optional Studio).')

        parser.add_argument("-s", "--studio", "--Studio", help="include Studio tabs", action="store_true")
        parser.add_argument("-3", "--three", "--3D", help="assume a 3D model" , action="store_true")
        # parser.add_argument("-r", "--rules", "--Rules", help="display Rules tab" , action="store_true")
        parser.add_argument("-x", "--skip_validate", help="do not attempt to validate the config (.xml) file" , action="store_true")
        parser.add_argument("-c", "--config",  type=str, help="config file (.xml)")
        parser.add_argument("-e", "--exec",  type=str, help="executable model")

        exec_file = 'project'  # for template sample

        # args = parser.parse_args()
        args, unknown = parser.parse_known_args()
        if unknown:
            print("invalid argument: ",unknown)
            sys.exit(-1)

        if args.studio:
            logging.debug(f'pmb.py: Studio mode: Run,Plot,Legend tabs')
            studio_flag = True
            # print("done with args.studio")
        if args.three:
            logging.debug(f'pmb.py: Assume a 3D model')
            model3D_flag = True
            # print("done with args.three")
        # if args.rules:
        #     logging.debug(f'pmb.py: Show Rules tab')
        #     rules_flag = True
        if args.skip_validate:
            logging.debug(f'pmb.py: Do not validate the config file (.xml)')
            skip_validate_flag = True
        # print("args.config= ",args.config)
        if args.config:
            logging.debug(f'pmb.py: config file is {args.config}')
            # sys.exit()
            config_file = args.config
            if (len(config_file) > 0) and Path(config_file).is_file():
                logging.debug(f'pmb.py: open_as_cb():  filePath is valid')
                logging.debug(f'len(config_file) = {len(config_file)}')
                logging.debug(f'done with args.config')
            else:
                print(f'config_file is NOT valid: {args.config}')
                logging.error(f'config_file is NOT valid: {args.config}')
                sys.exit()
        if args.exec:
            logging.debug(f'exec pgm is {args.exec}')
            # sys.exit()
            exec_file = args.exec
            if (len(exec_file) > 0) and Path(exec_file).is_file():
                print("exec_file exists")
            else:
                print("exec_file is NOT valid: ", args.exec)
                sys.exit()
    except:
        # print("Error parsing command line args.")
        sys.exit(-1)

    pmb_app = QApplication(sys.argv)

    icon_path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'physicell_logo_200px.png')
    pmb_app.setWindowIcon(QIcon(icon_path))

#    pmb_app.setStyleSheet("")  # affect dark mode?
    # pmb_app.setStyleSheet("Fusion")  # affect dark mode?

    logging.debug(f'QStyleFactory.keys() = {QStyleFactory.keys()}')

    # pmb_app.setStyleSheet(open("pyqt5-dark-theme.stylesheet").read())
    # pmb_app.setStyleSheet(open("darkorange.stylesheet").read())
    # pmb_app.setStyleSheet(open("pmb_dark.stylesheet").read())

    # Now use a palette to switch to dark colors:
    # palette = QPalette()

    # # dark mode
    # palette.setColor(QPalette.Window, QColor(53, 53, 53))
    # palette.setColor(QPalette.WindowText, Qt.white)
    # palette.setColor(QPalette.Base, QColor(25, 25, 25))
    # palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    # palette.setColor(QPalette.ToolTipBase, Qt.black)
    # palette.setColor(QPalette.ToolTipText, Qt.white)
    # palette.setColor(QPalette.Text, Qt.white)
    # palette.setColor(QPalette.Button, QColor(53, 53, 53))
    # palette.setColor(QPalette.ButtonText, Qt.white)
    # palette.setColor(QPalette.BrightText, Qt.red)
    # palette.setColor(QPalette.Link, QColor(42, 130, 218))
    # palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    # palette.setColor(QPalette.HighlightedText, Qt.black)

    # # non dark mode
    # rgb = 250
    # palette.setColor(QPalette.Window, QColor(rgb, rgb, rgb))
    # palette.setColor(QPalette.WindowText, Qt.black)
    # palette.setColor(QPalette.Base, QColor(25, 25, 25))
    # palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    # palette.setColor(QPalette.ToolTipBase, Qt.black)
    # palette.setColor(QPalette.ToolTipText, Qt.white)
    # palette.setColor(QPalette.Text, Qt.white)
    # palette.setColor(QPalette.Button, QColor(53, 53, 53))
    # palette.setColor(QPalette.ButtonText, Qt.white)
    # palette.setColor(QPalette.BrightText, Qt.red)
    # palette.setColor(QPalette.Link, QColor(42, 130, 218))
    # palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    # palette.setColor(QPalette.HighlightedText, Qt.black)

    # pmb_app.setPalette(palette)
    # palette = QtGui.QPalette()
    # print(palette.)

    # pmb_app.setPalette(QtGui.QGuiApplication.palette())

    rules_flag = False
    ex = PhysiCellXMLCreator(config_file, studio_flag, skip_validate_flag, rules_flag, model3D_flag, exec_file)
    ex.show()
    # startup_notice()
    sys.exit(pmb_app.exec_())
    # pmb_app.quit()
	
if __name__ == '__main__':
    # logging.basicConfig(filename='pmb.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
    # logging.basicConfig(filename="pmb_debug.log", level=logging.INFO)
    logfile = "pmb_debug.log"
    logging.basicConfig(filename=logfile, level=logging.DEBUG, filemode='w',)
    # logging.basicConfig(filename=logfile, level=logging.ERROR, filemode='w',)
    main()