"""
model.py - a PhysiCell model builder GUI to read in a sample PhysiCell config file (.xml), allow easy editing 
            (e.g., change parameter values, add/delete more "objects", including substrates and cell types),
             and then save the new config file. 

Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)

"""

import os
import sys
import getopt
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from xml.dom import minidom

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *

from config_tab import Config
from cell_def_tab import CellDef 
from cell_custom_data_tab import CellCustomData 
from microenv_tab import SubstrateDef 
from user_params_tab import UserParams 
from populate_tree_cell_defs import populate_tree_cell_defs
from run_tab import RunModel 
from vis_tab import Vis 
        
# from sbml_tab import SBMLParams 

def SingleBrowse(self):
        # if len(self.csv) < 2:
    filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')

        #     if filePath != "" and not filePath in self.csv:
        #         self.csv.append(filePath)
        # print(self.csv)
  
#class PhysiCellXMLCreator(QTabWidget):
class PhysiCellXMLCreator(QWidget):
    # def __init__(self, parent = None):
    def __init__(self, studio_flag, parent = None):
        super(PhysiCellXMLCreator, self).__init__(parent)

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
        self.setMinimumSize(1100, 700)  #width, height of window

        # model_name = "interactions"  # for testing latest xml
        model_name = "template"

        # then what??
        # binDirectory = os.path.realpath(os.path.abspath(__file__))
        binDirectory = os.path.dirname(os.path.abspath(__file__))
        dataDirectory = os.path.join(binDirectory,'..','data')

        # read_file = model_name + ".xml"
        read_file = os.path.join(dataDirectory, model_name + ".xml")
        # self.setWindowTitle(self.title_prefix + model_name)


        # NOTE! We create a *copy* of the .xml sample model and will save to it.
        copy_file = "copy_" + model_name + ".xml"
        self.current_save_file = copy_file
        try:
            shutil.copy(read_file, copy_file)
        except:
            print("Warning: unable to copy ",read_file," to ",copy_file, "(it may already exist)")

        self.setWindowTitle(self.title_prefix + copy_file)
        self.config_file = copy_file  # to Save

        self.tree = ET.parse(self.config_file)
        self.xml_root = self.tree.getroot()


        self.num_models = 0
        self.model = {}  # key: name, value:[read-only, tree]

        self.config_tab = Config()
        self.config_tab.xml_root = self.xml_root
        self.config_tab.fill_gui()

        self.microenv_tab = SubstrateDef()
        self.microenv_tab.xml_root = self.xml_root
        substrate_name = self.microenv_tab.first_substrate_name()
        print("gui4xml: substrate_name=",substrate_name)
        self.microenv_tab.populate_tree()  # rwh: both fill_gui and populate_tree??

        # self.tab2.tree.setCurrentItem(QTreeWidgetItem,0)  # item

        self.celldef_tab = CellDef()
        self.celldef_tab.xml_root = self.xml_root
        cd_name = self.celldef_tab.first_cell_def_name()
        print("gui4xml: cd_name=",cd_name)
        # self.celldef_tab.populate_tree()
        populate_tree_cell_defs(self.celldef_tab)
        self.celldef_tab.fill_substrates_comboboxes() # do before populate?
        self.celldef_tab.fill_celltypes_comboboxes()
        self.microenv_tab.celldef_tab = self.celldef_tab

        self.user_params_tab = UserParams()
        self.user_params_tab.xml_root = self.xml_root
        self.user_params_tab.fill_gui()

        # self.sbml_tab = SBMLParams()
        # self.sbml_tab.xml_root = self.xml_root
        # self.sbml_tab.fill_gui()

        # if studio_flag:
        #     self.run_tab = RunModel(self.nanohub_flag, self.tabWidget, self.download_menu)
        #     self.homedir = os.getcwd()
        #     print("model.py: self.homedir = ",self.homedir)
        #     self.run_tab.homedir = self.homedir
        #     self.run_tab.config_tab = self.config_tab
        #     self.run_tab.microenv_tab = self.microenv_tab 
        #     self.run_tab.celldef_tab = self.celldef_tab
        #     self.run_tab.user_params_tab = self.user_params_tab
        #     self.run_tab.tree = self.tree

        #------------------
        self.tabWidget = QTabWidget()
        stylesheet = """ 
            QTabBar::tab:selected {background: orange;}  # dodgerblue
            """
        self.tabWidget.setStyleSheet(stylesheet)
        self.tabWidget.addTab(self.config_tab,"Config Basics")
        self.tabWidget.addTab(self.microenv_tab,"Microenvironment")
        self.tabWidget.addTab(self.celldef_tab,"Cell Types")
        # self.tabWidget.addTab(self.cell_customdata_tab,"Cell Custom Data")
        self.tabWidget.addTab(self.user_params_tab,"User Params")

        if studio_flag:
            print("studio.py: creating Run and Plot tabs")
            self.run_tab = RunModel(self.nanohub_flag, self.tabWidget, self.download_menu)
            self.homedir = os.getcwd()
            print("model.py: self.homedir = ",self.homedir)
            self.run_tab.homedir = self.homedir
            self.run_tab.config_tab = self.config_tab
            self.run_tab.microenv_tab = self.microenv_tab 
            self.run_tab.celldef_tab = self.celldef_tab
            self.run_tab.user_params_tab = self.user_params_tab
            self.run_tab.tree = self.tree
            self.tabWidget.addTab(self.run_tab,"Run")

            self.vis_tab = Vis(self.nanohub_flag)
            self.run_tab.vis_tab = self.vis_tab
            # self.vis_tab.setEnabled(False)
            # self.vis_tab.nanohub_flag = self.nanohub_flag
            # self.vis_tab.xml_root = self.xml_root
            self.tabWidget.addTab(self.vis_tab,"Plot")
            # self.tabWidget.setTabEnabled(5, False)
            self.enablePlotTab(False)

            self.run_tab.vis_tab = self.vis_tab
            print("studio.py: calling vis_tab.substrates_cbox_changed_cb(2)")
            self.vis_tab.fill_substrates_combobox(self.celldef_tab.substrate_list)
            # self.vis_tab.substrates_cbox_changed_cb(2)   # doesn't accomplish it; need to set index, but not sure when
            self.vis_tab.init_plot_range(self.config_tab)


        vlayout.addWidget(self.tabWidget)
        # self.addTab(self.sbml_tab,"SBML")

        # tabWidget.setCurrentIndex(1)  # rwh/debug: select Microenv
        # tabWidget.setCurrentIndex(2)  # rwh/debug: select Cell Types
        self.tabWidget.setCurrentIndex(0)  # Config (default)


    def enablePlotTab(self, bval):
        self.tabWidget.setTabEnabled(5, bval)

    def menu(self):
        menubar = QMenuBar(self)
        menubar.setNativeMenuBar(False)

        #--------------
        file_menu = menubar.addMenu('&File')

        file_menu.addAction("New (template)", self.new_model_cb, QtGui.QKeySequence('Ctrl+n'))
        file_menu.addAction("Open", self.open_as_cb, QtGui.QKeySequence('Ctrl+o'))
        # file_menu.addAction("Save mymodel.xml", self.save_cb, QtGui.QKeySequence('Ctrl+s'))
        file_menu.addAction("Save as", self.save_as_cb)
        file_menu.addAction("Save", self.save_cb, QtGui.QKeySequence('Ctrl+s'))

        #--------------
        samples_menu = file_menu.addMenu("Samples (copy of)")
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

        template_act = QAction('template', self)
        samples_menu.addAction(template_act)
        template_act.triggered.connect(self.template_cb)

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

        #--------------
        # file_menu.addAction(open_act)
        # file_menu.addAction(recent_act)
        # file_menu.addAction(save_act)
        # file_menu.addAction(save_act, self.save_act, QtGui.QKeySequence("Ctrl+s"))
        # file_menu.addAction(saveas_act)


        #--------------
        # self.models_menu = menubar.addMenu('&Models')
        # models_menu_act = QAction('-----', self)
        # self.models_menu.addAction(models_menu_act)
        # models_menu_act.triggered.connect(self.select_current_model_cb)
        # # self.models_menu.addAction('Load sample', self.select_current_model_cb)

        #--------------
        # self.tools_menu = menubar.addMenu('&Tools')
        # validate_act = QAction('Validate', self)
        # self.tools_menu.addAction(validate_act)
        # validate_act.triggered.connect(self.validate_cb)
        # self.tools_menu.setEnabled(False)

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
    def add_new_model(self, name, read_only):
        # does it already exist? If so, return
        if name in self.model.keys():
            return
        self.model[name] = read_only
        self.num_models += 1
        print("add_new_model: self.model (dict)= ",self.model)

        # models_menu_act = QAction(name, self)
        # self.models_menu.addAction(models_menu_act)
        # models_menu_act.triggered.connect(self.select_current_model_cb)

        print("add_new_model: title suffix= ",name)
        self.setWindowTitle(self.title_prefix + name)

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
        # self.cell_customdata_tab.xml_root = self.xml_root
        self.user_params_tab.xml_root = self.xml_root

        self.config_tab.fill_gui()

        self.microenv_tab.clear_gui()
        self.microenv_tab.populate_tree()
        # self.microenv_tab.fill_gui(None)
        # self.microenv_tab.fill_gui()

        # Do this before the celldef_tab
        # self.cell_customdata_tab.clear_gui(self.celldef_tab)
        # self.cell_customdata_tab.fill_gui(self.celldef_tab)

        # self.celldef_tab.clear_gui()
        self.celldef_tab.clear_custom_data_params()
        # self.celldef_tab.fill_substrates_comboboxes()
        # self.celldef_tab.populate_tree()
        populate_tree_cell_defs(self.celldef_tab)
        # self.celldef_tab.fill_gui(None)
        # self.celldef_tab.customize_cycle_choices() #rwh/todo: needed? 
        self.celldef_tab.fill_substrates_comboboxes()
        self.celldef_tab.fill_celltypes_comboboxes()

        self.microenv_tab.celldef_tab = self.celldef_tab

        # self.cell_customdata_tab.clear_gui(self.celldef_tab)
        # self.cell_customdata_tab.fill_gui(self.celldef_tab)

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
            # sample_file = Path("data", name + ".xml")
            # copy_file = "copy_" + name + ".xml"
            copy_file = "mymodel.xml"

            # shutil.copy(sample_file, copy_file)
            try:
                shutil.copy(full_path_model_name, copy_file)
            except:
                print("Warning: unable to copy: ",full_path_model_name, copy_file)
            self.add_new_model(copy_file, True)
            # self.config_file = "config_samples/" + name + ".xml"
            self.config_file = copy_file
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

    def show_error_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.setFixedWidth(500)
        msg.exec_()

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
            self.current_save_file = full_path_model_name
        else:
            return

        try:
            self.celldef_tab.config_path = self.current_save_file
            self.config_tab.fill_xml()
            self.microenv_tab.fill_xml()
            self.celldef_tab.fill_xml()
            self.user_params_tab.fill_xml()

            # out_file = "mymodel.xml"
            # out_file = full_path_model_name 
            out_file = self.current_save_file
            self.setWindowTitle(self.title_prefix + out_file)

            print("\n\n ===================================")
            print("gui4xml:  save_as_cb: writing to: ",out_file)

            self.tree.write(out_file)
        except Exception as e:
            self.show_error_message(str(e) + " : Please finish the definition before saving.")

    def save_cb(self):
        try:
            self.celldef_tab.config_path = self.current_save_file
            # self.config_file = copy_file
            self.config_tab.fill_xml()
            self.microenv_tab.fill_xml()
            self.celldef_tab.fill_xml()
            self.user_params_tab.fill_xml()

            # filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')
            # print("gui4xml:  save_cb: writing to: ",self.config_file)

            # out_file = self.config_file
            # out_file = "mymodel.xml"
            out_file = self.current_save_file
            self.setWindowTitle(self.title_prefix + out_file)

            print("\n\n ===================================")
            print("gui4xml:  save_cb: writing to: ",out_file)

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

    # def save_cb(self):
    #     # save_as_file = QFileDialog.getSaveFileName(self,'',".")
    #     # if save_as_file:
    #     #     print(save_as_file)
    #     #     print(" save_as_file: ",save_as_file) # writing to:  ('/Users/heiland/git/PhysiCell-model-builder/rwh.xml', 'All Files (*)')

    #     self.config_tab.fill_xml()
    #     self.microenv_tab.fill_xml()
    #     self.celldef_tab.fill_xml()
    #     self.user_params_tab.fill_xml()

    #     save_as_file = "mymodel.xml"
    #     print("gui4xml:  save_as_cb: writing to: ",save_as_file) # writing to:  ('/Users/heiland/git/PhysiCell-model-builder/rwh.xml', 'All Files (*)')
    #     self.tree.write(save_as_file)


    def new_model_cb(self):
        # name = "copy_template"
        # self.add_new_model(name, False)
        # self.config_file = "config_samples/template.xml"
        # self.show_sample_model()
        name = "template"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        # self.config_file = "config_samples/" + name + ".xml"
        self.config_file = copy_file
        self.show_sample_model()

    def biorobots_cb(self):
        print("\n\n\n================ copy/load sample ======================================")
        name = "biorobots_flat"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        # self.config_file = "config_samples/" + name + ".xml"
        self.config_file = copy_file
        self.show_sample_model()

        # self.tree = ET.parse(self.config_file)
        # self.xml_root = self.tree.getroot()
        # self.celldef_tab.xml_root = self.xml_root
        # self.config_tab.fill_gui(self.xml_root)
        # self.microenv_tab.fill_gui(self.xml_root)
        # self.celldef_tab.fill_gui(self.xml_root)

    def cancer_biorobots_cb(self):
        name = "cancer_biorobots_flat"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def hetero_cb(self):
        name = "heterogeneity"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def pred_prey_cb(self):
        name = "pred_prey_flat"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def virus_mac_cb(self):
        name = "virus_macrophage_flat"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def worm_cb(self):
        name = "worm"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def interactions_cb(self):
        name = "interactions"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def cancer_immune_cb(self):
        name = "cancer_immune3D_flat"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def template_cb(self):
        name = "template"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def physiboss_cell_lines_cb(self):
        name = "physiboss_cell_lines"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    # def template3D_cb(self):
    #     name = "template3D_flat"
    #     self.add_new_model(name, True)
    #     self.config_file = "config_samples/" + name + ".xml"
    #     self.show_sample_model()

    def subcell_cb(self):
        name = "subcellular_flat"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def covid19_cb(self):
        name = "covid19_v5_flat"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def test_gui_cb(self):
        name = "test-gui"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        self.current_save_file = copy_file
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

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
    try:
        # opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
        opts, args = getopt.getopt(sys.argv[1:],"hv:",["studio"])
    except getopt.GetoptError:
        # print 'test.py -i <inputfile> -o <outputfile>'
        print('getopt exception')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('bin/model.py [--studio]')
            sys.exit(1)
    #   elif opt in ("-i", "--ifile"):
        elif opt in ("--studio"):
            studio_flag = True

    # print 'Input file is "', inputfile
    # print("show_vis_tab = ",show_vis_tab)
    # sys.exit()

    app = QApplication(sys.argv)
    # ex = PhysiCellXMLCreator()
    ex = PhysiCellXMLCreator(studio_flag)
    # ex.setGeometry(100,100, 800,600)
    ex.show()
    sys.exit(app.exec_())
	
if __name__ == '__main__':
    main()