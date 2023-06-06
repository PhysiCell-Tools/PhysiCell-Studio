"""
studio.py - driving module for the PhysiCell Model Builder GUI to read in a sample PhysiCell config file (.xml), easily edit (e.g., change parameter values, add/delete more "objects", including substrates and cell types), and save the updated config file. In addition, the "Studio" feature adds additional GUI tabs for creating initial conditions for cells (.csv), running a simulation, and visualizing output.

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
import traceback
import shutil # for possible copy of file
from pathlib import Path
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
# from xml.dom import minidom   # possibly explore later if we want to access/update *everything* in the DOM
import numpy as np

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QColor, QIcon, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyleFactory

from pretty_print_xml import pretty_print
from config_tab import Config
from cell_def_tab import CellDef, CellDefException
from microenv_tab import SubstrateDef 
from user_params_tab import UserParams 
try:
    from rules_tab import Rules
except:
    pass
from ics_tab import ICs
from populate_tree_cell_defs import populate_tree_cell_defs
from run_tab import RunModel 
# from legend_tab import Legend 

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
    msgBox.setText("Editing the template config file from the Studio's /config directory. If you want to edit another, use File->Open or File->Samples")
    msgBox.setStandardButtons(QMessageBox.Ok)

    returnValue = msgBox.exec()
    # if returnValue == QMessageBox.Ok:
    #     print('OK clicked')

def quit_cb():
    global studio_app
    studio_app.quit()

  
class PhysiCellXMLCreator(QWidget):
    def __init__(self, config_file, studio_flag, skip_validate_flag, rules_flag, model3D_flag, tensor_flag, exec_file, nanohub_flag, is_movable_flag, parent = None):
        super(PhysiCellXMLCreator, self).__init__(parent)
        if model3D_flag:
            try:
                import vtk
            except:
                print("\nError: Unable to `import vtk` for 3D visualization. \nYou can try to do `pip install vtk` from the command line and then and re-run the Studio, or run the Studio without the 3D visualization argument and settle for 2D vis.\n")
                sys.exit(-1)
            from vis3D_tab import Vis 

            # if tensor3D_flag:
            #     try:
            #         if tensor3D_flag:
            #     except:
        else:
            from vis_tab import Vis 

        self.studio_flag = studio_flag 
        # self.view_shading = None
        self.skip_validate_flag = skip_validate_flag 
        self.rules_flag = rules_flag 
        self.model3D_flag = model3D_flag 
        self.tensor_flag = tensor_flag 
        self.nanohub_flag = nanohub_flag 
        print("PhysiCellXMLCreator(): self.nanohub_flag= ",self.nanohub_flag)

        self.rules_tab_index = None

        # Hardcode tab indices for now
        # self.ics_tab_index = 4
        self.plot_tab_index = 6
        # self.legend_tab_index = 7
        if self.rules_flag:
            self.rules_tab_index = 4
            self.plot_tab_index = 7
            # self.legend_tab_index += 1

        # self.dark_mode = False
        # if (platform.system().lower() == 'darwin') and ("ARM64" in platform.uname().version):
        # if (platform.system().lower() == 'darwin') and (platform.machine() == 'arm64'):  # vs. machine()=x86_64
            # self.dark_mode = True
        print(f"  platform.system().lower()={platform.system().lower()}, platform.machine()={platform.machine()}")
        # print("PhysiCellXMLCreator(): self.dark_mode= ",self.dark_mode)

        self.title_prefix = "PhysiCell Model Builder: "
        if studio_flag:
            self.title_prefix = "PhysiCell Studio: "

        self.vis2D_gouraud = False

        # self.nanohub_flag = False
        if( 'HOME' in os.environ.keys() ):
            if "home/nanohub" in os.environ['HOME']:
                self.nanohub_flag = True

        if self.nanohub_flag:
            try:
                tool_dir = os.environ['TOOLPATH']
                dataDirectory = os.path.join(tool_dir,'data')
            except:
                binDirectory = os.path.dirname(os.path.abspath(__file__))
                dataDirectory = os.path.join(binDirectory,'..','data')
                print("-------- dataDirectory (relative) =",dataDirectory)
            self.absolute_data_dir = os.path.abspath(dataDirectory)
            print("-------- absolute_data_dir =",self.absolute_data_dir)

            # NOTE: if your C++ needs to also have an absolute path to data dir, do so via an env var
            # os.environ['KIDNEY_DATA_PATH'] = self.absolute_data_dir

            # docDirectory = os.path.join(binDirectory,'..','doc')
            # self.absolute_doc_dir = os.path.abspath(docDirectory)
            # print("-------- absolute_doc_dir =",self.absolute_doc_dir)
            # read_file = os.path.join(self.absolute_data_dir, model_name + ".xml")

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
        self.studio_root_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        if self.nanohub_flag:
            # self.studio_data_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
            self.studio_config_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        else:
            self.studio_config_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'config'))
        print("self.studio_root_dir = ",self.studio_root_dir)
        logging.debug(f'self.studio_root_dir = {self.studio_root_dir}')

        # assume running from a PhysiCell root dir, but change if not
        self.config_dir = os.path.realpath(os.path.join('.', 'config'))

        running_from_physicell_root = True
        if self.current_dir == self.studio_root_dir:  # are we running from studio root dir?
            # self.config_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
            self.config_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'config'))
            running_from_physicell_root = False
        print(f'self.config_dir =  {self.config_dir}')
        logging.debug(f'self.config_dir = {self.config_dir}')

        # print("\n------ running_from_physicell_root = ",running_from_physicell_root)

        # self.studio_config_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        # print("studio.py: self.studio_config_dir = ",self.studio_config_dir)
        # sys.exit(1)

        if config_file:
            self.current_xml_file = os.path.join(self.current_dir, config_file)
            print("got config_file=",config_file)
            # sys.exit()
        elif running_from_physicell_root:
            self.current_xml_file = os.path.join(self.current_dir, "config","PhysiCell_settings.xml")
            if not os.path.isfile(self.current_xml_file):
                print("\n-- Error: cannot load default config/PhysiCell_settings.xml, you should try to use the -c argument (rf. --help argument).\n")
                sys.exit(1)
        else:
            model_name = "interactions"  # for testing latest xml
            # model_name = "rules"
            if self.nanohub_flag:
                # model_name = "rules"
                model_name = "template"
            self.current_xml_file = os.path.join(self.studio_config_dir, model_name + ".xml")


        # NOTE! We operate *directly* on a default .xml file, not a copy.
        self.setWindowTitle(self.title_prefix + self.current_xml_file)
        self.config_file = self.current_xml_file  # to Save
        print(f"studio: (default) self.config_file = {self.config_file}")

        self.tree = ET.parse(self.config_file)
        print(f"studio: (default) self.tree = {self.tree}")
        self.xml_root = self.tree.getroot()
        print(f"studio: (default) self.xml_root = {self.xml_root}")   #rwh


        self.num_models = 0
        self.model = {}  # key: name, value:[read-only, tree]

        self.config_tab = Config(self.studio_flag)
        self.config_tab_index = 0
        self.config_tab.xml_root = self.xml_root
        self.config_tab.fill_gui()

        # Trying/failing to force the proper display of (default) checkboxes
        self.config_tab.save_svg.update()
        self.config_tab.save_svg.repaint()

        if self.nanohub_flag:  # rwh - test if works on nanoHUB
            print("studio.py: ---- TRUE nanohub_flag: updating config_tab folder")
            # self.config_tab.folder.setText('tmpdir')
            self.config_tab.folder.setText('.')
            # self.config_tab.folder.setEnabled(False)
            # self.config_tab.csv_folder.setText('')
            self.config_tab.csv_folder.setEnabled(False)
        else:
            print("studio.py: ---- FALSE nanohub_flag: NOT updating config_tab folder")

        self.microenv_tab = SubstrateDef(self.config_tab)
        self.microenv_tab_index = 1
        self.microenv_tab.xml_root = self.xml_root
        substrate_name = self.microenv_tab.first_substrate_name()
        # print("studio.py: first_substrate_name=",substrate_name)
        self.microenv_tab.populate_tree()  # rwh: both fill_gui and populate_tree??

        # self.tab2.tree.setCurrentItem(QTreeWidgetItem,0)  # item

        self.celldef_tab = CellDef()
        self.celldef_tab.xml_root = self.xml_root
        if is_movable_flag:
            self.celldef_tab.is_movable_w.setEnabled(True)

        cd_name = self.celldef_tab.first_cell_def_name()
        # print("studio.py: first_cell_def_name=",cd_name)
        logging.debug(f'studio.py: first_cell_def_name= {cd_name}')
        # self.celldef_tab.populate_tree()
        self.celldef_tab.config_path = self.current_xml_file

        self.celldef_tab.fill_substrates_comboboxes() # do before populate? Yes, assuming we check for cell_def != None

        # Beware: this may set the substrate chosen for Motility/[Advanced]Chemotaxis
        populate_tree_cell_defs(self.celldef_tab, self.skip_validate_flag)
        # self.celldef_tab.customdata.param_d = self.celldef_tab.param_d

        # print("\n\n---- studio: post populate_tree_cell_defs():")
        # print(self.celldef_tab.param_d)

        # self.celldef_tab.fill_substrates_comboboxes() # do before populate?
        self.celldef_tab.fill_celltypes_comboboxes()

        self.microenv_tab.celldef_tab = self.celldef_tab

        self.user_params_tab = UserParams()
        self.user_params_tab.xml_root = self.xml_root
        self.user_params_tab.fill_gui()

        print("studio.py: ",self.xml_root.find(".//cell_definitions//cell_rules"))
        # if self.xml_root.find(".//cell_definitions//cell_rules"):

        #------------------
        self.tabWidget = QTabWidget()
        # stylesheet = """ 
        #     QTabBar::tab:selected {background: orange;}  # dodgerblue

        #     QLabel {
        #         color: #000000;
        #         background-color: #FFFFFF; 
        #     }
        #     QPushButton {
        #         color: #000000;
        #         background-color: #FFFFFF; 
        #     }
        #     QTabWidget::tab-bar {
        #         alignment: center;
        #     }
        #     """

        # self.tabWidget.setStyleSheet(stylesheet)
        self.tabWidget.setStyleSheet('''
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab:selected {background: orange;}
        ''')
        self.tabWidget.addTab(self.config_tab,"Config Basics")
        self.tabWidget.addTab(self.microenv_tab,"Microenvironment")
        self.tabWidget.addTab(self.celldef_tab,"Cell Types")
        self.tabWidget.addTab(self.user_params_tab,"User Params")
        self.tabWidget.currentChanged.connect(self.tab_change_cb)

        self.current_dir = os.getcwd()
        # print("studio.py: self.current_dir = ",self.current_dir)
        logging.debug(f'studio.py: self.current_dir = {self.current_dir}')

        if self.rules_flag:
            self.rules_tab = Rules(self.nanohub_flag, self.microenv_tab, self.celldef_tab)
            # self.rules_tab.fill_gui()
            self.tabWidget.addTab(self.rules_tab,"Rules")
            self.rules_tab.xml_root = self.xml_root
            self.celldef_tab.rules_tab = self.rules_tab
            if self.nanohub_flag:
                self.rules_tab.absolute_data_dir = self.absolute_data_dir
            self.rules_tab.fill_gui()

            if self.nanohub_flag:
                self.rules_tab.rules_folder.setText(self.absolute_data_dir)

        if self.studio_flag:
            logging.debug(f'studio.py: creating ICs, Run, and Plot tabs')
            self.ics_tab = ICs(self.config_tab, self.celldef_tab)
            self.ics_tab.fill_celltype_combobox()
            self.ics_tab.reset_info()

            if self.nanohub_flag:  # rwh - test if works on nanoHUB
                print("studio.py: ---- TRUE nanohub_flag: updating ics_tab folder")
                # self.ics_tab.csv_folder.setText('')
                self.config_tab.csv_folder.setText(self.absolute_data_dir)
                self.config_tab.csv_folder.setEnabled(False)
                self.config_tab.csv_file.setText("mycells.csv")

                self.ics_tab.csv_folder.setText(self.absolute_data_dir)
                self.ics_tab.output_file.setText("mycells.csv")
                self.ics_tab.csv_folder.setEnabled(False)
            else:
                print("studio.py: ---- FALSE nanohub_flag: NOT updating ics_tab folder")

            self.celldef_tab.ics_tab = self.ics_tab
            # self.rules_tab.fill_gui()
            self.tabWidget.addTab(self.ics_tab,"ICs")

            self.run_tab = RunModel(self.nanohub_flag, self.tabWidget, self.celldef_tab, self.rules_flag, self.download_menu)

            self.homedir = os.getcwd()
            print("studio.py: self.homedir = ",self.homedir)
            if self.nanohub_flag:
                try:
                    # cachedir = os.environ['CACHEDIR']
                    toolpath = os.environ['TOOLPATH']
                    print("studio.py: toolpath= ",toolpath)
                    # full_path = os.path.join(toolpath, "data")
                    self.homedir = os.path.join(toolpath, "data")
                except:
                    print("studio.py: exception doing os.environ('TOOLPATH')")

            self.run_tab.homedir = self.homedir

            # self.run_tab.config_xml_name.setText(current_xml_file)
            # self.run_tab.exec_name.setText(exec_file)
            # self.run_tab.exec_name.setText(str(Path(exec_file)))
            if not self.nanohub_flag:
                self.run_tab.exec_name.setText(os.path.join(self.homedir, exec_file))
            else:
                # self.run_tab.exec_name.setText(os.path.join(self.homedir, "bin", exec_file))
                self.run_tab.exec_name.setText(os.path.join(exec_file))

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

            # config_tab needed for 3D domain boundary outline
            self.vis_tab = Vis(self.nanohub_flag, self.config_tab, self.run_tab, self.model3D_flag, self.tensor_flag)
            # if not self.nanohub_flag:
            self.vis_tab.output_folder.setText(self.config_tab.folder.text())
            self.vis_tab.update_output_dir(self.config_tab.folder.text())
            self.config_tab.vis_tab = self.vis_tab
            if self.nanohub_flag:  # rwh - test if works on nanoHUB
                # self.vis_tab.output_folder.setText('tmpdir')
                self.vis_tab.output_folder.setText('.')
                # self.vis_tab.output_folder.setEnabled(False)
                self.vis_tab.output_folder_button.setEnabled(False)

            self.vis_tab.config_tab = self.config_tab
            # self.vis_tab.output_dir = self.config_tab.plot_folder.text()
            # self.vis_tab.view_shading = self.view_shading

            # self.legend_tab = Legend(self.nanohub_flag)
            # self.vis_tab.legend_tab = self.legend_tab
            # self.legend_tab.current_dir = self.current_dir
            # self.legend_tab.studio_config_dir = self.studio_config_dir
            self.run_tab.vis_tab = self.vis_tab
            self.tabWidget.addTab(self.vis_tab,"Plot")
            # self.tabWidget.setTabEnabled(5, False)
            self.enablePlotTab(False)
            self.enablePlotTab(True)

            # self.tabWidget.addTab(self.legend_tab,"Legend")
            # self.enableLegendTab(False)
            # self.enableLegendTab(True)
            self.run_tab.vis_tab = self.vis_tab
            # self.run_tab.legend_tab = self.legend_tab
            logging.debug(f'studio.py: calling vis_tab.substrates_cbox_changed_cb(2)')
            self.vis_tab.fill_substrates_combobox(self.celldef_tab.substrate_list)
            # self.vis_tab.substrates_cbox_changed_cb(2)   # doesn't accomplish it; need to set index, but not sure when
            self.vis_tab.init_plot_range(self.config_tab)

            # self.vis_tab.output_dir = self.config_tab.folder.text()
            self.vis_tab.update_output_dir(self.config_tab.folder.text())
            # self.legend_tab.output_dir = self.config_tab.folder.text()
            # legend_file = os.path.join(self.vis_tab.output_dir, 'legend.svg')  # hardcoded filename :(
            # if Path(legend_file).is_file():
            #     self.legend_tab.reload_legend()

            self.vis_tab.reset_model()
            


        vlayout.addWidget(self.tabWidget)
        # self.addTab(self.sbml_tab,"SBML")

        if self.model3D_flag:
            self.tabWidget.setCurrentIndex(self.plot_tab_index)
        else:
            self.tabWidget.setCurrentIndex(self.config_tab_index)  # Config (default)
        # self.tabWidget.repaint()  # Config (default)
        # self.config_tab.config_params.update()  # 
        # self.tabWidget.setCurrentIndex(1)  # rwh/debug: select Microenv
        # self.tabWidget.setCurrentIndex(2)  # rwh/debug: select Cell Types

    def tab_change_cb(self,index: int):
        # print("\n-------- tab index=",index)
        # if index == 0:
        #     studio_app.resize(1101,770) # recall: print("size=",ex.size())  # = PyQt5.QtCore.QSize(1100, 770)
        #     studio_app.resize(1101,970) # recall: print("size=",ex.size())  # = PyQt5.QtCore.QSize(1100, 770)
        if index == self.microenv_tab_index: # microenv_tab
            self.microenv_tab.update_3D()

        elif self.rules_tab_index and (index == self.rules_tab_index): 
            if self.rules_tab.update_rules_for_custom_data:
                print("studio.py: need to update Rules comboboxes for changed custom data")
                self.rules_tab.fill_signals_widget()
                self.rules_tab.fill_responses_widget()
                self.rules_tab.update_rules_for_custom_data = False

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
PhysiCell Studio is a tool to provide graphical editing of a PhysiCell model and, optionally, run a model and visualize results. &nbsp; It is led by the Macklin Lab (Indiana University) with contributions from the PhysiCell community.<br><br>

NOTE: When loading a model (.xml configuration file), it must be a "flat" format for the  cell_definitions, i.e., all parameters need to be defined. &nbsp; Many legacy PhysiCell models used a hierarchical format in which a cell_definition could inherit from a parent. &nbsp; The hierarchical format is not supported in the Studio.<br><br>

For more information:<br>
<a href="https://github.com/PhysiCell-Tools/PhysiCell-Studio">github.com/PhysiCell-Tools/PhysiCell-Studio</a><br>
<a href="https://github.com/rheiland/PhysiCell-Studio/blob/main/user-guide/README.md">Studio User Guide (draft)</a><br>
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

    # def enableLegendTab(self, bval):
    #     # self.tabWidget.setTabEnabled(6, bval)   
    #     # self.tabWidget.setTabEnabled(6, bval)   
    #     self.tabWidget.setTabEnabled(self.legend_tab_index, bval)

    def filterUI_cb(self):
        print("studio.py: filterUI_cb")
        self.vis_tab.filterUI_cb()

    def menu(self):
        menubar = QMenuBar(self)
        menubar.setNativeMenuBar(False)

        stylesheet = """ 
            QMenuBar {color: black;}
            QMenuBar::item:selected {background: white;}  # dodgerblue
            QMenuBar::item:pressed {background: white;}  # dodgerblue
            """
        # QString style = "QMenuBar::item:selected { background: white; } QMenuBar::item:pressed {  background: white; }"
        menubar.setStyleSheet("color: black")
        # menubar.setStyleSheet(stylesheet)

        #--------------
        studio_menu = menubar.addMenu('&Studio')
        studio_menu.addAction("About", self.about_studio)
        # studio_menu.addAction("About PyQt", self.about_pyqt)
        # studio_menu.addAction("Preferences", self.prefs_cb)
        if not self.nanohub_flag:
            studio_menu.addSeparator()
            studio_menu.addAction("Quit", quit_cb)

        #-----
        file_menu = menubar.addMenu('&File')
        if self.nanohub_flag:
            model_menu = menubar.addMenu('&Model')
            model_menu.addAction("template", self.template_cb)
            model_menu.addAction("biorobots", self.biorobots_cb)
            model_menu.addAction("tumor_immune", self.tumor_immune_cb)   # was "rules"

            # model_menu.addAction("celltypes3", self.celltypes3_nanohub_cb)
            # model_menu.addAction("pred_prey_farmer", self.pred_prey_nanohub_cb)
            # model_menu.addAction("biorobots", self.biorobots_nanohub_cb)
            # model_menu.addAction("celltypes3", self.celltypes3_nanohub_cb)
            # model_menu.addAction("pred_prey_farmer", self.pred_prey_nanohub_cb)
            # pass

        #--------------
        else:
            # file_menu = menubar.addMenu('&File')
            # file_menu.addAction("New (template)", self.new_model_cb, QtGui.QKeySequence('Ctrl+n'))
            file_menu.addAction("Open", self.open_as_cb, QtGui.QKeySequence('Ctrl+o'))
            # file_menu.addAction("Save mymodel.xml", self.save_cb, QtGui.QKeySequence('Ctrl+s'))
            file_menu.addAction("Save as", self.save_as_cb)
            file_menu.addAction("Save", self.save_cb, QtGui.QKeySequence('Ctrl+s'))
            #------
            export_menu = file_menu.addMenu("Export")

            simularium_act = QAction('Simularium', self)
            export_menu.addAction(simularium_act)
            simularium_act.triggered.connect(self.simularium_cb)
            if not self.studio_flag:
                print("simularium_installed is ",simularium_installed)
                export_menu.setEnabled(False)

            #------
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

            mechano_act = QAction('mechano', self)
            samples_menu.addAction(mechano_act)
            mechano_act.triggered.connect(self.mechano_cb)

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

        # else:
            # file_menu.addAction("Save as mymodel.xml", self.save_as_cb)


        if self.nanohub_flag:
            self.download_menu = file_menu.addMenu('Download')
            self.download_config_item = self.download_menu.addAction("Download config.xml", self.download_config_cb)
            self.download_csv_item = self.download_menu.addAction("Download cells,rules (.csv) data", self.download_csv_cb)
            self.download_rules_item = self.download_menu.addAction("Download rules.txt", self.download_rules_cb)
            self.download_svg_item = self.download_menu.addAction("Download cell (.svg) data", self.download_svg_cb)
            self.download_mat_item = self.download_menu.addAction("Download full (.mat) data", self.download_full_cb)
            self.download_graph_item = self.download_menu.addAction("Download cell graph (.txt) data", self.download_graph_cb)
            # self.download_menu_item.setEnabled(False)
            # self.download_menu.setEnabled(False)
        else:
            self.download_menu = None

        #-------------------------
        if self.model3D_flag:
            view3D_menu = menubar.addMenu('&View')
            view3D_menu.triggered.connect(self.view3D_cb)

            vis3D_filterUI_act = view3D_menu.addAction("Plot options", self.filterUI_cb)

            # axes_act = view3D_menu.addAction("Axes")
            # axes_act.setCheckable(True)
            # axes_act.setChecked(False)

        else:  # just 2D view
            if self.studio_flag:
                view_menu = menubar.addMenu('&View')
                view_menu.triggered.connect(self.view2D_cb)

                vis2D_filterUI_act = view_menu.addAction("Plot options", self.filterUI_cb)



        help_menu = menubar.addMenu('&Help')
        help_menu.triggered.connect(self.open_help_url)
        guide_act = help_menu.addAction("User Guide (link)", self.open_help_url)

        menubar.adjustSize()  # Argh. Otherwise, only 1st menu appears, with ">>" to others!

    def open_help_url(self):
        url = QtCore.QUrl('https://github.com/rheiland/PhysiCell-Studio/blob/main/user-guide/README.md')
        if not QtGui.QDesktopServices.openUrl(url):
            QtGui.QMessageBox.warning(self, 'Open Url', 'Could not open URL')

    def reset_xml_root(self):
        self.celldef_tab.clear_custom_data_tab()
        self.celldef_tab.param_d.clear()  # seems unnecessary as being done in populate_tree. argh.
        self.celldef_tab.current_cell_def = None
        self.celldef_tab.cell_adhesion_affinity_celltype = None

        self.microenv_tab.param_d.clear()

        print(f"\nreset_xml_root() self.tree = {self.tree}")
        self.xml_root = self.tree.getroot()
        print(f"reset_xml_root() self.xml_root = {self.xml_root}")
        self.config_tab.xml_root = self.xml_root
        self.microenv_tab.xml_root = self.xml_root
        self.celldef_tab.xml_root = self.xml_root
        self.user_params_tab.xml_root = self.xml_root

        self.config_tab.fill_gui()
        if self.model3D_flag and self.xml_root.find(".//domain//use_2D").text.lower() == 'true':
            print("You're running a 3D Studio, but the model is 2D")
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText('The model has been loaded; however, it is 2D and you are running the 3D (plotting) Studio. You may want to run a new Studio without 3D, i.e., no "-3", for this 2D model.')
            msgBox.setStandardButtons(QMessageBox.Ok)
            returnValue = msgBox.exec()

        self.microenv_tab.clear_gui()
        self.microenv_tab.populate_tree()

        self.celldef_tab.config_path = self.current_xml_file
        self.celldef_tab.fill_substrates_comboboxes()   # do before populate_tree_cell_defs
        populate_tree_cell_defs(self.celldef_tab, self.skip_validate_flag)

        self.celldef_tab.fill_celltypes_comboboxes()

        if self.rules_flag:
            self.rules_tab.xml_root = self.xml_root
            self.rules_tab.clear_rules()
            self.rules_tab.fill_gui()   # do *after* populate_cell_defs() 

        if self.studio_flag:
            self.ics_tab.reset_info()

        self.microenv_tab.celldef_tab = self.celldef_tab

        self.user_params_tab.clear_gui()
        self.user_params_tab.fill_gui()


    def show_sample_model(self):
        logging.debug(f'studio: show_sample_model(): self.config_file = {self.config_file}')
        print(f'\nstudio: show_sample_model(): self.config_file = {self.config_file}')
        self.tree = ET.parse(self.config_file)
        print(f'studio: show_sample_model(): self.tree = {self.tree}')
        if self.studio_flag:
            self.run_tab.tree = self.tree  #rwh
        # self.xml_root = self.tree.getroot()
        self.reset_xml_root()
        self.setWindowTitle(self.title_prefix + self.config_file)
        if self.model3D_flag:
            self.vis_tab.reset_domain_box()

    def open_as_cb(self):
        # filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')
        filePath = QFileDialog.getOpenFileName(self,'',".")
        # print("\n\nopen_as_cb():  filePath=",filePath)
        full_path_model_name = filePath[0]
        print("\n\nopen_as_cb():  full_path_model_name =",full_path_model_name )
        logging.debug(f'\nstudio.py: open_as_cb():  full_path_model_name ={full_path_model_name}')
        # if (len(full_path_model_name) > 0) and Path(full_path_model_name):
        if (len(full_path_model_name) > 0) and Path(full_path_model_name).is_file():
            print("open_as_cb():  filePath is valid")
            logging.debug(f'     filePath is valid')
            print("           len(full_path_model_name) = ", len(full_path_model_name) )
            logging.debug(f'     len(full_path_model_name) = {len(full_path_model_name)}' )
            # fname = os.path.basename(full_path_model_name)
            self.current_xml_file = full_path_model_name

            self.config_file = self.current_xml_file
            print("open_as_cb():  self.config_file = ",self.config_file)
            if self.studio_flag:
                self.run_tab.config_file = self.current_xml_file
                print("open_as_cb():  setting run_tab.config_file = ",self.run_tab.config_file)
                self.run_tab.config_xml_name.setText(self.current_xml_file)

            self.show_sample_model()
            self.vis_tab.update_output_dir(self.config_tab.folder.text())
            # self.reset_xml_root()   #rwh - done in show_sample_model

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


    def save_as_cb(self):
        # print("------ save_as_cb():")
        self.celldef_tab.check_valid_cell_defs()
        
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
            print("save_as_cb():  doing config_tab.fill_xml")
            self.config_tab.fill_xml()
            print("save_as_cb():  doing microenv_tab.fill_xml")
            self.microenv_tab.fill_xml()
            print("save_as_cb():  doing celldef_tab.fill_xml")
            self.celldef_tab.fill_xml()
            print("save_as_cb():  doing user_params_tab.fill_xml")
            self.user_params_tab.fill_xml()
            if self.rules_flag:
                self.rules_tab.fill_xml()
            
            self.setWindowTitle(self.title_prefix + self.current_xml_file)

            # print("\n\n ===================================")
            print("studio.py:  save_as_cb: writing to: ",self.current_xml_file)

            self.tree.write(self.current_xml_file)
            print("studio.py:  save_as_cb: doing pretty_print ")
            pretty_print(self.current_xml_file, self.current_xml_file)

            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Note: this will not change the config file in the Run tab.")
            msgBox.setStandardButtons(QMessageBox.Ok)
            returnValue = msgBox.exec()

        except CellDefException as e:
            self.show_error_message(str(e) + " : save_as_cb(): Error: Please finish the definition before saving.")


    def save_cb(self):
        self.celldef_tab.check_valid_cell_defs()

        if not self.user_params_tab.validate_utable():
            return

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

            self.setWindowTitle(self.title_prefix + self.current_xml_file)

            # print("\n\n ===================================")
            # print("studio.py:  save_cb: writing to: ",out_file)
            print("studio.py:  save_cb: writing to: ",self.current_xml_file)

            # self.tree.write(out_file)  # originally
            self.tree.write(self.current_xml_file)
            pretty_print(self.current_xml_file, self.current_xml_file)
    
        except CellDefException as e:
            self.show_error_message(str(e) + " : save_cb(): Error: Please finish the definition before saving.")


    def validate_cb(self):  # not used currently
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Validation not yet implemented.")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        returnValue = msgBox.exec()
        # if returnValue == QMessageBox.Ok:
            # print('OK clicked')


    def view2D_cb(self, action):
        print("view2D_cb(): ",action.text())
        if action.text().find("aspect") >= 0:
            self.vis_tab.view_aspect_toggle_cb(action.isChecked())
        elif action.text().find("shading") >= 0:
             self.vis_tab.shading_toggle_cb(action.isChecked())
        elif action.text().find("voxel") >= 0:
             self.vis_tab.voxel_grid_toggle_cb(action.isChecked())
        elif action.text().find("mechanics") >= 0:
             self.vis_tab.mechanics_grid_toggle_cb(action.isChecked())
        return

    def view3D_cb(self, action):
        # logging.debug(f'studio.py: view3D_cb: {action.text()}, {action.isChecked()}')
        if "XY slice" in action.text():
            self.vis_tab.xy_slice_toggle_cb(action.isChecked())
        elif "YZ slice" in action.text():
            self.vis_tab.yz_slice_toggle_cb(action.isChecked())
        elif "XZ slice" in action.text():
            self.vis_tab.xz_slice_toggle_cb(action.isChecked())

        elif "XY clip" in action.text():
            self.vis_tab.xy_clip_toggle_cb(action.isChecked())
        elif "YZ clip" in action.text():
            self.vis_tab.yz_clip_toggle_cb(action.isChecked())
        elif "XZ clip" in action.text():
            self.vis_tab.xz_clip_toggle_cb(action.isChecked())

        elif "voxels" in action.text():
            self.vis_tab.voxels_toggle_cb(action.isChecked())
        elif "Axes" in action.text():
            self.vis_tab.axes_toggle_cb(action.isChecked())
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
            self.vis_tab.physiboss_vis_checkbox = None    # default: assume a non-boolean intracellular model
            self.vis_tab.physiboss_vis_flag = False
            if self.vis_tab.physiboss_vis_checkbox:
                self.vis_tab.physiboss_vis_checkbox.setChecked(False)


        os.chdir(self.current_dir)  # just in case we were in /tmpdir (and it crashed/failed, leaving us there)

        self.current_xml_file = os.path.join(self.studio_config_dir, name + ".xml")
        logging.debug(f'studio.py: load_model(): self.current_xml_file= {self.current_xml_file}')
        print(f'studio.py: load_model(): self.current_xml_file= {self.current_xml_file}')

        logging.debug(f'studio.py: load_model(): {self.xml_root.find(".//cell_definitions//cell_rules")}')
        print(f'studio.py: load_model(): {self.xml_root.find(".//cell_definitions//cell_rules")}')

        # if self.xml_root.find(".//cell_definitions//cell_rules"):
        # self.current_save_file = current_xml_file
        if self.studio_flag:
            self.run_tab.config_xml_name.setText(self.current_xml_file)
            self.run_tab.config_file = self.current_xml_file

        self.config_file = self.current_xml_file
        self.show_sample_model()
        # if self.nanohub_flag:  # rwh - test if works on nanoHUB
        #     print("studio.py: load_model(): ---- TRUE nanohub_flag: updating config_tab and ics_tab folder")
        #     self.config_tab.folder.setText('.')
        #     self.ics_tab.folder.setText('.')
        # else:
        #     print("studio.py: load_model():  ---- FALSE nanohub_flag: NOT updating config_tab and ics_tab folder")

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

        self.vis_tab.convert_to_simularium(self.current_xml_file)
        return


        # sim_output_dir = os.path.realpath(os.path.join('.', self.config_tab.folder.text()))
        # print("sim_output_dir = ",sim_output_dir )

        # simularium_model_data = PhysicellData(
        #     timestep=1.0,
        #     path_to_output_dir=sim_output_dir, 
        #     meta_data=MetaData(
        #         box_size=np.array([200.0, 200.0, 200.0]),
        #         scale_factor=0.01,
        #         trajectory_title="Some parameter set",
        #         model_meta_data=ModelMetaData(
        #             title="worm",
        #             version="8.1",
        #             authors="PhysiCell modeler",
        #             description=(
        #                 "A PhysiCell model run with some parameter set"
        #             ),
        #             doi="10.1016/j.bpj.2016.02.002",
        #             source_code_url="https://github.com/allen-cell-animated/simulariumio",
        #             source_code_license_url="https://github.com/allen-cell-animated/simulariumio/blob/main/LICENSE",
        #             input_data_url="https://allencell.org/path/to/native/engine/input/files",
        #             raw_output_data_url="https://allencell.org/path/to/native/engine/output/files",
        #         ),
        #     ),
        #     nth_timestep_to_read=1,
        #     display_data={
        #         0: DisplayData(
        #             name="ctype1",
        #             color="#dfdacd",
        #             display_type=DISPLAY_TYPE.SPHERE,
        #         ),
        #         1: DisplayData(
        #             name="ctype2",
        #             color="#0080ff",
        #             display_type=DISPLAY_TYPE.SPHERE,
        #         ),
        #     },
        #     time_units=UnitData("m"),  # minutes
        # )

        # print("calling Simularium PhysicellConverter...\n")
        # model_name = os.path.basename(self.current_xml_file)
        # model_name = model_name[:-4]   # strip off .xml suffix
        # PhysicellConverter(simularium_model_data).save(model_name)
        # print(f"--> {model_name}.simularium")

        # print("Load this model at: https://simularium.allencell.org/viewer")


    #----------------------
    def template_cb(self):
        self.load_model("template")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./project')

    def biorobots_cb(self):
        # self.load_model("biorobots")
        # self.load_model("biorobots_flat")
        self.load_model("biorobots")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./biorobots')

    def tumor_immune_cb(self):
        self.load_model("tumor_immune")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./project')

    def cancer_biorobots_cb(self):
        self.load_model("cancer_biorobots")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./cancer_biorobots')

    def hetero_cb(self):
        self.load_model("heterogeneity")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./heterogeneity')

    def pred_prey_cb(self):
        self.load_model("pred_prey_farmer")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./pred_prey')

    def virus_mac_cb(self):
        self.load_model("virus_macrophage")
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

    def mechano_cb(self):
        self.load_model("mechano")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./mechano')

    def cancer_immune_cb(self):
        self.load_model("cancer_immune3D_flat")
        if self.studio_flag:
            self.run_tab.exec_name.setText('./cancer_immune_3D')

    def physiboss_cell_lines_cb(self):
        self.load_model("physiboss")
        # self.vis_tab.physiboss_vis_checkbox = None    # done in load_model
        if self.studio_flag:
            self.run_tab.exec_name.setText('./PhysiBoSS_Cell_Lines')

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
        print('studio.py: message(): ',s)

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
            try:
                if self.p is None:  # No process running.
                    self.debug_tab.add_msg("   self.p is None; create QProcess()")
                    self.debug_tab.add_msg("  cwd= " + os.getcwd())
                    self.debug_tab.add_msg("doing: exportfile config.xml")
                    self.p = QProcess()
                    self.p.readyReadStandardOutput.connect(self.handle_stdout)
                    self.p.readyReadStandardError.connect(self.handle_stderr)
                    self.p.stateChanged.connect(self.handle_state)
                    self.p.finished.connect(self.process_finished)  # Clean up once complete.
                    self.p.start("exportfile config.xml")
                else:
                    self.debug_tab.add_msg("   self.p is NOT None; just return!")
            except:
                self.message("Unable to download config.xml")
                print("Unable to download config.xml")
                self.p = None
        return

    def download_rules_cb(self):
        if self.nanohub_flag:
            try:
                if self.p is None:  # No process running.
                    self.p = QProcess()
                    self.p.readyReadStandardOutput.connect(self.handle_stdout)
                    self.p.readyReadStandardError.connect(self.handle_stderr)
                    self.p.stateChanged.connect(self.handle_state)
                    self.p.finished.connect(self.process_finished)  # Clean up once complete.

                    self.p.start("exportfile rules.csv")
                else:
                    self.debug_tab.add_msg(" download_rules_cb():  self.p is NOT None; just return!")
            except:
                self.message("Unable to download rules.csv")
                print("Unable to download rules.csv")
                self.p = None
        return

    def download_svg_cb(self):
        if self.nanohub_flag:
            try:
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
                else:
                    # self.debug_tab.add_msg(" download_svg_cb():  self.p is NOT None; just return!")
                    print(" download_svg_cb():  self.p is NOT None; just return!")
            except:
                self.message("Unable to download svg.zip")
                print("Unable to download svg.zip")
                self.p = None
        return

    def download_full_cb(self):
        if self.nanohub_flag:
            try:
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
                else:
                    # self.debug_tab.add_msg(" download_full_cb():  self.p is NOT None; just return!")
                    print(" download_full_cb():  self.p is NOT None; just return!")
            except:
                self.message("Unable to download mcds.zip")
                print("Unable to download mcds.zip")
                self.p = None
        return

    def biorobots_nanohub_cb(self):
        print("\n\n\n================ copy/load sample ======================================")
        os.chdir(self.homedir)
        name = "biorobots_flat"
        # sample_file = Path("data", name + ".xml")
        # sample_file = Path(self.absolute_data_dir, name + ".xml")
        sample_file = Path(self.pmb_data_dir, name + ".xml")
        copy_file = "copy_" + name + ".xml"
        shutil.copy(sample_file, copy_file)

        # self.add_new_model(copy_file, True)
        # self.config_file = "config_samples/" + name + ".xml"
        self.config_file = copy_file
        # self.show_sample_model()
        # self.run_tab.exec_name.setText('../biorobots')

        try:
            print("biorobots_nanohub_cb():------------- copying ",sample_file," to ",copy_file)
            shutil.copy(sample_file, copy_file)
        except:
            print("biorobots_nanohub_cb(): Unable to copy file(1).")
            sys.exit(1)

        try:
            print("biorobots_nanohub_cb():------------- copying ",sample_file," to config.xml")
            shutil.copy(sample_file, "config.xml")
        except:
            print("biorobots_nanohub_cb(): Unable to copy file(2).")
            sys.exit(1)

        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        print("biorobots_nanohub_cb:   self.config_file = ",self.config_file)

        self.show_sample_model()
        if self.nanohub_flag:
            self.run_tab.exec_name.setText('biorobots')
        else:
            self.run_tab.exec_name.setText('../biorobots')
        self.vis_tab.show_edge = False
        self.vis_tab.bgcolor = [1,1,1,1]

    #-----------------------------------------------------------------

studio_app = None
def main():
    global studio_app
    # inputfile = ''
    config_file = None
    studio_flag = True
    model3D_flag = False
    tensor_flag = False
    rules_flag = False
    skip_validate_flag = False
    nanohub_flag = False
    is_movable_flag = False
    try:
        parser = argparse.ArgumentParser(description='PhysiCell Studio.')

        parser.add_argument("-b", "--bare", "--basic", help="no plotting, etc ", action="store_true")
        parser.add_argument("-3", "--three", "--3D", help="assume a 3D model", action="store_true")
        parser.add_argument("-t", "--tensor",  help="for 3D ellipsoid cells", action="store_true")
        # parser.add_argument("-r", "--rules", "--Rules", help="display Rules tab" , action="store_true")
        parser.add_argument("-x", "--skip_validate", help="do not attempt to validate the config (.xml) file" , action="store_true")
        parser.add_argument("--nanohub", help="run as if on nanoHUB", action="store_true")
        # parser.add_argument("--is_movable", help="checkbox for mechanics is_movable", action="store_true")
        parser.add_argument("-c", "--config", type=str, help="config file (.xml)")
        parser.add_argument("-e", "--exec", type=str, help="executable model")

        exec_file = 'project'  # for template sample

        # args = parser.parse_args()
        args, unknown = parser.parse_known_args()
        print("args=",args)
        print("unknown=",unknown)
        if unknown:
            print("len(unknown)= ",len(unknown))
            if unknown[0] == "--rules" and len(unknown)==1:
                print("studio.py: setting rules_flag = True")
                rules_flag = True
            else:
                print("Invalid argument(s): ",unknown)
                print("Use '--help' to see options.")
                sys.exit(-1)

        # print("-- continue after if unknown...")
        if args.three:
            logging.debug(f'studio.py: Assume a 3D model')
            model3D_flag = True
            # print("done with args.three")
        if args.tensor:
            logging.debug(f'studio.py: Assume tensors (e.g., ellipsoid 3D cells)')
            tensor_flag = True
        if args.bare:
            logging.debug(f'studio.py: bare model editing, no ICs,Run,Plot tabs')
            studio_flag = False
            model3D_flag = False
            # print("done with args.studio")
        # if args.rules:
        #     logging.debug(f'studio.py: Show Rules tab')
        #     rules_flag = True
        if args.nanohub:
            logging.debug(f'studio.py: nanoHUB mode')
            nanohub_flag = True
        # if args.is_movable:
        #     is_movable_flag = True
        if args.skip_validate:
            logging.debug(f'studio.py: Do not validate the config file (.xml)')
            skip_validate_flag = True
        # print("args.config= ",args.config)
        if args.config:
            logging.debug(f'studio.py: config file is {args.config}')
            # sys.exit()
            config_file = args.config
            if (len(config_file) > 0) and Path(config_file).is_file():
                logging.debug(f'studio.py: open_as_cb():  filePath is valid')
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

    root = os.path.dirname(os.path.abspath(__file__))        
    # QDir.addSearchPath('themes', os.path.join(root, 'themes'))
    QtCore.QDir.addSearchPath('images', os.path.join(root, 'images'))

    studio_app = QApplication(sys.argv)

    icon_path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'physicell_logo_200px.png')
    studio_app.setWindowIcon(QIcon(icon_path))

    # print(f'QStyleFactory.keys() = {QStyleFactory.keys()}')   # ['macintosh', 'Windows', 'Fusion']

    # Use a palette to help force light-mode (not dark) style
    # Not all seem to be used, but beware/test(!) if changed.
    palette = QPalette()
    rgb = 236
    palette.setColor(QPalette.Window, QColor(rgb, rgb, rgb))
    palette.setColor(QPalette.WindowText, Qt.black)

    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    rgb = 100
    palette.setColor(QPalette.Base, QColor(rgb, rgb, rgb))
    palette.setColor(QPalette.AlternateBase, QColor(rgb, rgb, rgb))

    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)

    # for QLineEdit()
    palette.setColor(QPalette.Base, Qt.white)
    palette.setColor(QPalette.Text, Qt.black)

    # palette.setColor(QPalette.Button, QColor(230, 230, 0))  # light yellow: affects tree widget header and table headers
    palette.setColor(QPalette.Button, QColor(255, 255, 255))  # white: affects tree widget header and table headers

    # palette.setColor(QPalette.ButtonText, Qt.white)  # e.g., header for tree widgets??
    # palette.setColor(QPalette.ButtonText, Qt.green)  # e.g., header for tree widgets??
    palette.setColor(QPalette.ButtonText, Qt.black)  # e.g., header for tree widget too?!

    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(236, 236, 236))   # background when user tabs through QLineEdits
    palette.setColor(QPalette.Highlight, QColor(210, 210, 210))   # background when user tabs through QLineEdits
    palette.setColor(QPalette.HighlightedText, Qt.black)

    studio_app.setPalette(palette)
    # studio_app.setStyleSheet("QCheckBox { background-color: red }")
    # studio_app.setStyleSheet("QLineEdit { background-color: white }; QComboBox { height: 34 } ")  # doesn't seem to always work, forcing us to take different approach in, e.g., Cell Types sub-tabs

    studio_app.setStyleSheet("QLineEdit { background-color: white };")  # doesn't seem to always work, forcing us to take different approach in, e.g., Cell Types sub-tabs

    # studio_app.setStyleSheet("QLineEdit { background-color: white };QPushButton { background-color: green } ")  # doesn't seem to always work, forcing us to take different approach in, e.g., Cell Types sub-tabs


    # rules_flag = False
    if rules_flag:
        try:
            from rules_tab import Rules
        except ImportError as ie:
            print("importerror ",ie)
            traceback.print_exc()
        except:
            rules_flag = False
            traceback.print_exc()
            # for line in traceback.format_stack():
            #     print(line.strip())
            sys.exit(1)
            # print("Warning: Rules module not found.\n")

    # print("calling PhysiCellXMLCreator with rules_flag= ",rules_flag)
    ex = PhysiCellXMLCreator(config_file, studio_flag, skip_validate_flag, rules_flag, model3D_flag, tensor_flag, exec_file, nanohub_flag, is_movable_flag)
    print("size=",ex.size())  # = PyQt5.QtCore.QSize(1100, 770)
    # ex.setFixedWidth(1101)  # = PyQt5.QtCore.QSize(1100, 770)
    # print("width=",ex.size())


    # -- Insanity. Trying/failing to force the proper display of (default) checkboxes
    # ex.config_tab.config_params.update()  # attempt to refresh, to show checkboxes!
    # ex.config_tab.scroll.update()  # attempt to refresh, to show checkboxes!
    # ex.config_tab.repaint()  # attempt to refresh, to show checkboxes!
    # ex.tabWidget.repaint()  # Config (default)
    # ex.repaint()  # Config (default)

    ex.show()

    # -- Insanity. Just trying to refresh the initial Config tab so the checkboxes will render properly :/
    # ex.config_tab.update()  # attempt to refresh, to show checkboxes!
    # ex.config_tab.repaint()  # attempt to refresh, to show checkboxes!
    # ex.resize(1101,770)
    # ex.update()
    # ex.repaint()
    # ex.show()
    # print("size 2=",ex.size())  # = PyQt5.QtCore.QSize(1100, 770)

    # startup_notice()
    sys.exit(studio_app.exec_())
    # studio_app.quit()
	
if __name__ == '__main__':
    # logging.basicConfig(filename='studio.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
    # logging.basicConfig(filename="studio_debug.log", level=logging.INFO)
    logfile = "studio_debug.log"
    logging.basicConfig(filename=logfile, level=logging.DEBUG, filemode='w',)
    # logging.basicConfig(filename=logfile, level=logging.ERROR, filemode='w',)
    main()