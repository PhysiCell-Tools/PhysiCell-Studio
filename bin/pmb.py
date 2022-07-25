"""
pmb.py - a PhysiCell Model Builder GUI to read in a sample PhysiCell config file (.xml), allow easy editing 
            (e.g., change parameter values, add/delete more "objects", including substrates and cell types),
             and then save the new config file. 

Authors:
Randy Heiland (heiland@iu.edu)
Students: Michael Siler, Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)

"""

import os
import platform
import sys
import getopt
# import shutil # for possible copy of file
from pathlib import Path
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from xml.dom import minidom

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyleFactory

from config_tab import Config
from cell_def_tab import CellDef 
from microenv_tab import SubstrateDef 
from user_params_tab import UserParams 
from rules_tab import Rules
from populate_tree_cell_defs import populate_tree_cell_defs
from run_tab import RunModel 
from vis_tab import Vis 
from legend_tab import Legend 
        
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
    #    msgBox.setWindowTitle("Example")
    msgBox.setStandardButtons(QMessageBox.Ok)
    # msgBox.buttonClicked.connect(msgButtonClick)

    returnValue = msgBox.exec()
    if returnValue == QMessageBox.Ok:
        print('OK clicked')

  
class PhysiCellXMLCreator(QWidget):
    def __init__(self, studio_flag, rules_flag, parent = None):
        super(PhysiCellXMLCreator, self).__init__(parent)

        self.studio_flag = studio_flag 
        self.rules_flag = rules_flag 

        self.plot_tab_index = 5
        self.legend_tab_index = 6
        if self.rules_flag:
            self.plot_tab_index = 6
            self.legend_tab_index = 7

        self.dark_mode = False
        # if (platform.system().lower() == 'darwin') and ("ARM64" in platform.uname().version):
        if (platform.system().lower() == 'darwin') and (platform.machine() == 'arm64'):
            self.dark_mode = True

        self.title_prefix = "PhysiCell Model Builder: "
        self.setWindowTitle(self.title_prefix)

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
        print("model.py: self.current_dir = ",self.current_dir)

        # model_name = "interactions"  # for testing latest xml
        model_name = "template"
        # model_name = "test1"
        # model_name = "interactions"

        # bin_dir = os.path.dirname(os.path.abspath(__file__))
        # data_dir = os.path.join(bin_dir,'..','data')
        # data_dir = os.path.normpath(data_dir)
        # data_dir = os.path.join(self.current_dir,'data')

        # self.current_xml_file = os.path.join(data_dir, model_name + ".xml")
        self.data_dir = self.current_xml_file = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        # self.current_xml_file = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data', 'template.xml'))
        # self.current_xml_file = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data', 'template.xml'))
        self.current_xml_file = os.path.join(self.data_dir, model_name + ".xml")

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
        print("pmb.py: substrate_name=",substrate_name)
        self.microenv_tab.populate_tree()  # rwh: both fill_gui and populate_tree??

        # self.tab2.tree.setCurrentItem(QTreeWidgetItem,0)  # item

        self.celldef_tab = CellDef(self.dark_mode)
        self.celldef_tab.xml_root = self.xml_root

        cd_name = self.celldef_tab.first_cell_def_name()
        print("pmb.py: cd_name=",cd_name)
        # self.celldef_tab.populate_tree()
        self.celldef_tab.config_path = self.current_xml_file
        populate_tree_cell_defs(self.celldef_tab)
        self.celldef_tab.fill_substrates_comboboxes() # do before populate?
        self.celldef_tab.fill_celltypes_comboboxes()
        self.microenv_tab.celldef_tab = self.celldef_tab

        self.user_params_tab = UserParams(self.dark_mode)
        self.user_params_tab.xml_root = self.xml_root
        self.user_params_tab.fill_gui()

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
        print("model.py: self.current_dir = ",self.current_dir)

        if self.rules_flag:
            self.rules_tab = Rules(self.microenv_tab,self.celldef_tab)
            self.rules_tab.fill_gui()
            self.tabWidget.addTab(self.rules_tab,"Rules")

        if self.studio_flag:
            print("studio.py: creating Run and Plot tabs")
            self.run_tab = RunModel(self.nanohub_flag, self.tabWidget, self.download_menu)
            # self.run_tab.config_xml_name.setText(current_xml_file)
            self.run_tab.config_xml_name.setText(self.current_xml_file)
            # self.current_dir = os.getcwd()
            self.run_tab.current_dir = self.current_dir
            self.run_tab.config_tab = self.config_tab
            self.run_tab.microenv_tab = self.microenv_tab 
            self.run_tab.celldef_tab = self.celldef_tab
            self.run_tab.user_params_tab = self.user_params_tab
            self.run_tab.tree = self.tree

            self.run_tab.config_file = self.current_xml_file
            self.run_tab.config_xml_name.setText(self.current_xml_file)

            self.tabWidget.addTab(self.run_tab,"Run")

            self.vis_tab = Vis(self.nanohub_flag)
            self.config_tab.vis_tab = self.vis_tab

            self.legend_tab = Legend(self.nanohub_flag)
            self.run_tab.vis_tab = self.vis_tab
            # self.vis_tab.setEnabled(False)
            # self.vis_tab.nanohub_flag = self.nanohub_flag
            # self.vis_tab.xml_root = self.xml_root
            self.tabWidget.addTab(self.vis_tab,"Plot")
            # self.tabWidget.setTabEnabled(5, False)
            self.enablePlotTab(False)

            self.tabWidget.addTab(self.legend_tab,"Legend")
            self.enableLegendTab(False)
            self.run_tab.vis_tab = self.vis_tab
            self.run_tab.legend_tab = self.legend_tab
            print("studio.py: calling vis_tab.substrates_cbox_changed_cb(2)")
            self.vis_tab.fill_substrates_combobox(self.celldef_tab.substrate_list)
            # self.vis_tab.substrates_cbox_changed_cb(2)   # doesn't accomplish it; need to set index, but not sure when
            self.vis_tab.init_plot_range(self.config_tab)

            self.vis_tab.output_dir = self.config_tab.folder.text()
            self.legend_tab.output_dir = self.config_tab.folder.text()
            


        vlayout.addWidget(self.tabWidget)
        # self.addTab(self.sbml_tab,"SBML")

        # tabWidget.setCurrentIndex(1)  # rwh/debug: select Microenv
        # tabWidget.setCurrentIndex(2)  # rwh/debug: select Cell Types
        self.tabWidget.setCurrentIndex(0)  # Config (default)


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
        file_menu = menubar.addMenu('&File')

        # file_menu.addAction("New (template)", self.new_model_cb, QtGui.QKeySequence('Ctrl+n'))
        file_menu.addAction("Open", self.open_as_cb, QtGui.QKeySequence('Ctrl+o'))
        # file_menu.addAction("Save mymodel.xml", self.save_cb, QtGui.QKeySequence('Ctrl+s'))
        file_menu.addAction("Save as", self.save_as_cb)
        file_menu.addAction("Save", self.save_cb, QtGui.QKeySequence('Ctrl+s'))

        #--------------
        samples_menu = file_menu.addMenu("Samples (copy of)")

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
        # self.microenv_tab.param_d.clear()

        self.xml_root = self.tree.getroot()
        self.config_tab.xml_root = self.xml_root
        self.microenv_tab.xml_root = self.xml_root
        self.celldef_tab.xml_root = self.xml_root
        self.user_params_tab.xml_root = self.xml_root

        self.config_tab.fill_gui()

        self.microenv_tab.clear_gui()
        self.microenv_tab.populate_tree()
        # self.microenv_tab.fill_gui(None)
        # self.microenv_tab.fill_gui()
        # self.celldef_tab.clear_gui()
        self.celldef_tab.clear_custom_data_params()
        # self.celldef_tab.fill_substrates_comboboxes()
        # self.celldef_tab.populate_tree()
        self.celldef_tab.config_path = self.current_xml_file
        populate_tree_cell_defs(self.celldef_tab)
        # self.celldef_tab.fill_gui(None)
        # self.celldef_tab.customize_cycle_choices() #rwh/todo: needed? 
        self.celldef_tab.fill_substrates_comboboxes()
        self.celldef_tab.fill_celltypes_comboboxes()

        self.microenv_tab.celldef_tab = self.celldef_tab

        self.user_params_tab.clear_gui()
        self.user_params_tab.fill_gui()

    def show_sample_model(self):
        print("show_sample_model: self.config_file = ", self.config_file)
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
        if (len(full_path_model_name) > 0) and Path(full_path_model_name):
            print("open_as_cb():  filePath is valid")
            print("len(full_path_model_name) = ", len(full_path_model_name) )
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
        print("------ save_as_cb():")
        # filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')
        filePath = QFileDialog.getSaveFileName(self,'',".")
        # filePath = QFileDialog.getSaveFileName(self,'Save file',".",".xml")
        print("\n\n save_as_cb():  filePath=",filePath)
        full_path_model_name = filePath[0]
        print("\n\n save_as_cb():  full_path_model_name =",full_path_model_name )
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

            # out_file = "mymodel.xml"
            # out_file = full_path_model_name 
            # out_file = self.current_save_file
            out_file = self.current_xml_file
            self.setWindowTitle(self.title_prefix + out_file)

            print("\n\n ===================================")
            print("pmb.py:  save_as_cb: writing to: ",out_file)

            self.tree.write(out_file)

        except Exception as e:
            self.show_error_message(str(e) + " : Please finish the definition before saving.")

    def save_cb(self):
        
        try:
            # self.celldef_tab.config_path = self.current_save_file
            self.celldef_tab.config_path = self.current_xml_file
            self.config_file = self.current_xml_file
            self.config_tab.fill_xml()
            self.microenv_tab.fill_xml()
            self.celldef_tab.fill_xml()
            self.user_params_tab.fill_xml()

            # filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')
            # print("pmb.py:  save_cb: writing to: ",self.config_file)

            # out_file = self.config_file
            # out_file = "mymodel.xml"
            # out_file = self.current_save_file
            out_file = self.current_xml_file
            self.setWindowTitle(self.title_prefix + out_file)

            print("\n\n ===================================")
            print("pmb.py:  save_cb: writing to: ",out_file)

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


            self.tree.write(out_file)  # originally

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
            self.show_error_message(str(e) + " : Please finish the definition before saving.")

    def validate_cb(self):  # not used currently
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Validation not yet implemented.")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        returnValue = msgBox.exec()
        if returnValue == QMessageBox.Ok:
            print('OK clicked')

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
        self.current_xml_file = os.path.join(self.data_dir, name + ".xml")
        print("load_model: self.current_xml_file= ",self.current_xml_file)

        # self.current_save_file = current_xml_file
        if self.studio_flag:
            self.run_tab.config_xml_name.setText(self.current_xml_file)
            self.run_tab.config_file = self.current_xml_file

        self.config_file = self.current_xml_file
        self.show_sample_model()
        if self.nanohub_flag:  # rwh - test if works on nanoHUB
            self.config_tab.folder.setText('.')


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
        print(s)

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

def main():
    # inputfile = ''
    studio_flag = False
    rules_flag = False
    try:
        # opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
        opts, args = getopt.getopt(sys.argv[1:],"hv:",["studio", "rules"])
    except getopt.GetoptError:
        # print 'test.py -i <inputfile> -o <outputfile>'
        print('\ngetopt exception - usage:')
        print('bin/pmb.py [--studio]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('bin/pmb.py [--studio]')
            sys.exit(1)
    #   elif opt in ("-i", "--ifile"):
        elif opt in ("--studio"):
            studio_flag = True
        elif opt in ("--rules"):
            rules_flag = True

    # print 'Input file is "', inputfile
    # print("show_vis_tab = ",show_vis_tab)
    # sys.exit()

    pmb_app = QApplication(sys.argv)
#    pmb_app.setStyleSheet("")  # affect dark mode?
    # pmb_app.setStyleSheet("Fusion")  # affect dark mode?

    print("---> ",QStyleFactory.keys())

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

    ex = PhysiCellXMLCreator(studio_flag, rules_flag)
    ex.show()
    startup_notice()
    sys.exit(pmb_app.exec_())
	
if __name__ == '__main__':
    main()