"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)

--- Versions ---
0.1 - initial version
"""
# https://doc.qt.io/qtforpython/gettingstarted.html

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
# from sbml_tab import SBMLParams 

def SingleBrowse(self):
        # if len(self.csv) < 2:
    filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')

        #     if filePath != "" and not filePath in self.csv:
        #         self.csv.append(filePath)
        # print(self.csv)
  
#class PhysiCellXMLCreator(QTabWidget):
class PhysiCellXMLCreator(QWidget):
    def __init__(self, parent = None):
    # def __init__(self, show_vis_flag, parent = None):
        super(PhysiCellXMLCreator, self).__init__(parent)

        self.title_prefix = "PhysiCell Model Builder: "
        self.setWindowTitle(self.title_prefix)

        # Menus
        vlayout = QVBoxLayout(self)
        # vlayout.setContentsMargins(5, 35, 5, 5)
        menuWidget = QWidget(self.menu())
        vlayout.addWidget(menuWidget)
        # self.setWindowIcon(self.style().standardIcon(getattr(QStyle, 'SP_DialogNoButton')))
        # self.setWindowIcon(QtGui.QIcon('physicell_logo_25pct.png'))
        # self.grid = QGridLayout()
        # lay.addLayout(self.grid)
        self.setLayout(vlayout)
        # self.setMinimumSize(400, 790)  # width, height (height >= Cell Types|Death params)
        # self.setMinimumSize(400, 500)  # width, height (height >= Cell Types|Death params)
        # self.setMinimumSize(800, 620)  # width, height (height >= Cell Types|Death params)
        # self.setMinimumSize(800, 660)  # width, height (height >= Cell Types|Death params)
        self.setMinimumSize(850, 700)  # works for Zoe; otherwise User Params are scrolled out of sight
        # self.setMinimumSize(800, 800)  # width, height (height >= Cell Types|Death params)
        # self.setMinimumSize(700, 770)  # width, height (height >= Cell Types|Death params)
        # self.setMinimumSize(600, 600)  # width, height (height >= Cell Types|Death params)
        # self.resize(400, 790)  # width, height (height >= Cell Types|Death params)

        # self.menubar = QtWidgets.QMenuBar(self)
        # self.file_menu = QtWidgets.QMenu('File')
        # self.file_menu.insertAction("Open")
        # self.menubar.addMenu(self.file_menu)

        # GUI tabs

        # By default, let's startup the app with a default of template2D (a copy)
        # self.new_model_cb()  # default on startup
        # read_file = "../data/subcellular_flat.xml"
        # read_file = "../data/cancer_biorobots_flat.xml"
        # read_file = "../data/pred_prey_flat.xml"

        model_name = "pred_prey_flat"
        model_name = "biorobots_flat"
        model_name = "cancer_biorobots_flat"
        model_name = "test1"
        model_name = "test-gui"
        model_name = "covid19_v5_flat"
        model_name = "template"
        # model_name = "test"
        # model_name = "randy_test"  #rwh
        # read_file = "data/" + model_name + ".xml"

        # then what??
        # binDirectory = os.path.realpath(os.path.abspath(__file__))
        binDirectory = os.path.dirname(os.path.abspath(__file__))
        dataDirectory = os.path.join(binDirectory,'..','data')

        # read_file = model_name + ".xml"
        read_file = os.path.join(dataDirectory, model_name + ".xml")
        # self.setWindowTitle(self.title_prefix + model_name)


        # NOTE! We create a *copy* of the .xml sample model and will save to it.
        copy_file = "copy_" + model_name + ".xml"
        try:
            shutil.copy(read_file, copy_file)
        except:
            print("Warning: unable to copy ",read_file," to ",copy_file, "(it may already exist)")

        self.setWindowTitle(self.title_prefix + copy_file)
        # self.add_new_model(copy_file, True)
        # self.config_file = "config_samples/" + name + ".xml"
        self.config_file = copy_file  # to Save

        # self.config_file = read_file  # nanoHUB... to Save
        self.tree = ET.parse(self.config_file)
        # tree = ET.parse(read_file)
        # self.tree = ET.parse(read_file)
        self.xml_root = self.tree.getroot()

        # self.template_cb()

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
        self.celldef_tab.populate_tree()
        self.celldef_tab.fill_substrates_comboboxes()
        self.microenv_tab.celldef_tab = self.celldef_tab

        self.cell_customdata_tab = CellCustomData()
        self.cell_customdata_tab.xml_root = self.xml_root
        self.cell_customdata_tab.celldef_tab = self.celldef_tab
        self.cell_customdata_tab.fill_gui(self.celldef_tab)
        self.celldef_tab.fill_custom_data_tab()
        
        self.user_params_tab = UserParams()
        self.user_params_tab.xml_root = self.xml_root
        self.user_params_tab.fill_gui()

        # self.sbml_tab = SBMLParams()
        # self.sbml_tab.xml_root = self.xml_root
        # self.sbml_tab.fill_gui()

        #------------------
        tabWidget = QTabWidget()
        stylesheet = """ 
            QTabBar::tab:selected {background: dodgerblue;}
            """
        tabWidget.setStyleSheet(stylesheet)
        tabWidget.addTab(self.config_tab,"Config Basics")
        tabWidget.addTab(self.microenv_tab,"Microenvironment")
        tabWidget.addTab(self.celldef_tab,"Cell Types")
        tabWidget.addTab(self.cell_customdata_tab,"Cell Custom Data")
        tabWidget.addTab(self.user_params_tab,"User Params")

        vlayout.addWidget(tabWidget)
        # self.addTab(self.sbml_tab,"SBML")

        # tabWidget.setCurrentIndex(1)  # rwh/debug: select Microenv
        # tabWidget.setCurrentIndex(2)  # rwh/debug: select Cell Types
        tabWidget.setCurrentIndex(0)  # Config (default)


    def menu(self):
        menubar = QMenuBar(self)
        menubar.setNativeMenuBar(False)

        #--------------
        file_menu = menubar.addMenu('&File')

        # open_act = QtGui.QAction('Open', self, checkable=True)
        # open_act = QtGui.QAction('Open', self)
        # open_act.triggered.connect(self.open_as_cb)
        file_menu.addAction("New (template)", self.new_model_cb, QtGui.QKeySequence('Ctrl+n'))
        file_menu.addAction("Open", self.open_as_cb, QtGui.QKeySequence('Ctrl+o'))
        file_menu.addAction("Save mymodel.xml", self.save_cb, QtGui.QKeySequence('Ctrl+s'))
        # file_menu.addAction("Save as", self.save_as_cb)
        # file_menu.addAction("Save as mymodel.xml", self.save_as_cb)
        # recent_act = QtGui.QAction('Recent', self)
        # save_act = QtGui.QAction('Save', self)
        # save_act.triggered.connect(self.save_cb)
        # saveas_act = QtGui.QAction('Save As my.xml', self)

        # file_menu.setStatusTip('enable/disable Dark mode')
        # new_model_act = QtGui.QAction('', self)
        # file_menu.addAction(new_model_act)
        # new_model_act.triggered.connect(self.new_model_cb)

        #--------------
        samples_menu = file_menu.addMenu("Samples (copy of)")
        # biorobots_act = QtGui.QAction('biorobots', self)
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

        cancer_immune_act = QAction('cancer immune (3D)', self)
        samples_menu.addAction(cancer_immune_act)
        cancer_immune_act.triggered.connect(self.cancer_immune_cb)

        template_act = QAction('template', self)
        samples_menu.addAction(template_act)
        template_act.triggered.connect(self.template_cb)

        subcell_act = QAction('subcellular', self)
        samples_menu.addAction(subcell_act)
        subcell_act.triggered.connect(self.subcell_cb)

        covid19_act = QAction('covid19_v5', self)
        samples_menu.addAction(covid19_act)
        covid19_act.triggered.connect(self.covid19_cb)

        test_gui_act = QAction('test-gui', self)
        samples_menu.addAction(test_gui_act)
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
        tools_menu = menubar.addMenu('&Tools')
        validate_act = QAction('Validate', self)
        tools_menu.addAction(validate_act)
        validate_act.triggered.connect(self.validate_cb)

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
        self.cell_customdata_tab.xml_root = self.xml_root
        self.user_params_tab.xml_root = self.xml_root

        self.config_tab.fill_gui()

        self.microenv_tab.clear_gui()
        self.microenv_tab.populate_tree()
        # self.microenv_tab.fill_gui(None)
        # self.microenv_tab.fill_gui()

        # Do this before the celldef_tab
        self.cell_customdata_tab.clear_gui(self.celldef_tab)
        self.cell_customdata_tab.fill_gui(self.celldef_tab)

        # self.celldef_tab.clear_gui()
        self.celldef_tab.clear_custom_data_params()
        self.celldef_tab.populate_tree()
        # self.celldef_tab.fill_gui(None)
        # self.celldef_tab.customize_cycle_choices() #rwh/todo: needed? 
        self.celldef_tab.fill_substrates_comboboxes()
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

    def save_cb(self):
        # self.config_file = copy_file
        self.config_tab.fill_xml()
        self.microenv_tab.fill_xml()
        self.celldef_tab.fill_xml()
        self.user_params_tab.fill_xml()

        # filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')
        # print("gui4xml:  save_cb: writing to: ",self.config_file)

        # out_file = self.config_file
        out_file = "mymodel.xml"
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

        self.tree.write(out_file)

        # rwh NOTE: after saving the .xml, do we need to read it back in to reflect changes.
        # self.tree = ET.parse(self.config_file)
        # self.xml_root = self.tree.getroot()
        # self.reset_xml_root()


    def validate_cb(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Validation not yet implemented.")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        returnValue = msgBox.exec()
        if returnValue == QMessageBox.Ok:
            print('OK clicked')

    def save_as_cb(self):
        # save_as_file = QFileDialog.getSaveFileName(self,'',".")
        # if save_as_file:
        #     print(save_as_file)
        #     print(" save_as_file: ",save_as_file) # writing to:  ('/Users/heiland/git/PhysiCell-model-builder/rwh.xml', 'All Files (*)')

        self.config_tab.fill_xml()
        self.microenv_tab.fill_xml()
        self.celldef_tab.fill_xml()
        self.user_params_tab.fill_xml()

        save_as_file = "mymodel.xml"
        print("gui4xml:  save_as_cb: writing to: ",save_as_file) # writing to:  ('/Users/heiland/git/PhysiCell-model-builder/rwh.xml', 'All Files (*)')
        self.tree.write(save_as_file)


    def new_model_cb(self):
        # name = "copy_template"
        # self.add_new_model(name, False)
        # self.config_file = "config_samples/template.xml"
        # self.show_sample_model()
        name = "template"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
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
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def hetero_cb(self):
        name = "heterogeneity"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def pred_prey_cb(self):
        name = "pred_prey_flat"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def virus_mac_cb(self):
        name = "virus_macrophage_flat"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def worm_cb(self):
        name = "worm"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def cancer_immune_cb(self):
        name = "cancer_immune3D_flat"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def template_cb(self):
        name = "template"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
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
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def covid19_cb(self):
        name = "covid19_v5_flat"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

    def test_gui_cb(self):
        name = "test-gui"
        sample_file = Path("data", name + ".xml")
        copy_file = "copy_" + name + ".xml"
        shutil.copy(sample_file, copy_file)
        self.add_new_model(copy_file, True)
        self.config_file = copy_file
        self.show_sample_model()

		
# def main():
#     app = QApplication(sys.argv)
#     ex = PhysiCellXMLCreator()
#     # ex.setGeometry(100,100, 800,600)
#     ex.show()
#     sys.exit(app.exec_())

def main():
    # inputfile = ''
    # try:
    #     # opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    #     opts, args = getopt.getopt(sys.argv[1:],"hv:",["vis"])
    # except getopt.GetoptError:
    #     # print 'test.py -i <inputfile> -o <outputfile>'
    #     print('getopt exception')
    #     sys.exit(2)
    # for opt, arg in opts:
    #     if opt == '-h':
    #     #  print 'test.py -i <inputfile> -o <outputfile>'
    #         print('bin/gui4xml.py [--vis]')
    #         sys.exit(1)
    # #   elif opt in ("-i", "--ifile"):
    #     elif opt in ("--vis"):
    #         show_vis_tab = True

    # print 'Input file is "', inputfile
    # print("show_vis_tab = ",show_vis_tab)
    # sys.exit()

    app = QApplication(sys.argv)
    ex = PhysiCellXMLCreator()
    # ex = PhysiCellXMLCreator(show_vis_tab)
    # ex.setGeometry(100,100, 800,600)
    ex.show()
    sys.exit(app.exec_())
	
if __name__ == '__main__':
    main()