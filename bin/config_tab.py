"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)
"""

import sys
import logging
# import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QLineEdit, QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,QGridLayout
from PyQt5.QtWidgets import QMessageBox

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class Config(QWidget):
    # def __init__(self, nanohub_flag):
    def __init__(self, studio_flag):
        super().__init__()
        # global self.config_params

        self.default_time_units = "min"

        # self.nanohub_flag = nanohub_flag
        self.nanohub_flag = False

        self.studio_flag = studio_flag
        self.vis_tab = None

        self.xml_root = None

        # self.tab = QWidget()
        # self.tabs.resize(200,5)
        
        #-------------------------------------------
        label_width = 110
        domain_value_width = 100
        value_width = 60
        label_height = 20
        units_width = 170

        self.scroll = QScrollArea()  # might contain centralWidget

        self.config_params = QWidget()

        self.config_tab_layout = QGridLayout()
        # self.config_tab_layout.addWidget(self.tab_widget, 0,0,1,1) # w, row, column, rowspan, colspan

        #============  Domain ================================
        label = QLabel("Domain (micron)")
        label.setFixedHeight(label_height)
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)
        idx_row = 0
        self.config_tab_layout.addWidget(label, idx_row,0,1,20) # w, row, column, rowspan, colspan

        domain_enabled = True

        label = QLabel("Xmin")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.xmin = QLineEdit()
        self.xmin.setEnabled(domain_enabled)
        self.xmin.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.xmin, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel("Xmax")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        self.xmax = QLineEdit()
        self.xmax.setEnabled(domain_enabled)
        self.xmax.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.xmax, idx_row,3,1,1) # w, row, column, rowspan, colspan

        label = QLabel("dx")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.config_tab_layout.addWidget(label, idx_row,4,1,1) # w, row, column, rowspan, colspan

        self.xdel = QLineEdit()
        self.xdel.setEnabled(domain_enabled)
        self.xdel.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.xdel, idx_row,5,1,1) # w, row, column, rowspan, colspan

        #----------
        label = QLabel("Ymin")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.ymin = QLineEdit()
        self.ymin.setEnabled(domain_enabled)
        self.ymin.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.ymin, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel("Ymax")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        self.ymax = QLineEdit()
        self.ymax.setEnabled(domain_enabled)
        self.ymax.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.ymax, idx_row,3,1,1) # w, row, column, rowspan, colspan

        label = QLabel("dy")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.config_tab_layout.addWidget(label, idx_row,4,1,1) # w, row, column, rowspan, colspan

        self.ydel = QLineEdit()
        self.ydel.setEnabled(domain_enabled)
        self.ydel.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.ydel, idx_row,5,1,1) # w, row, column, rowspan, colspan

        #----------
        label = QLabel("Zmin")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.zmin = QLineEdit()
        self.zmin.setEnabled(domain_enabled)
        self.zmin.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.zmin, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel("Zmax")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        self.zmax = QLineEdit()
        self.zmax.setEnabled(domain_enabled)
        self.zmax.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.zmax, idx_row,3,1,1) # w, row, column, rowspan, colspan

        label = QLabel("dz")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.config_tab_layout.addWidget(label, idx_row,4,1,1) # w, row, column, rowspan, colspan

        self.zdel = QLineEdit()
        self.zdel.setEnabled(domain_enabled)
        self.zdel.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.zdel, idx_row,5,1,1) # w, row, column, rowspan, colspan

        #----------
        self.virtual_walls = QCheckBox("Virtual walls")
        idx_row += 1
        self.config_tab_layout.addWidget(self.virtual_walls, idx_row,1,1,1) # w, row, column, rowspan, colspan

        #============  Misc ================================
        label = QLabel("Times")
        label.setFixedHeight(label_height)
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,20) # w, row, column, rowspan, colspan

        label = QLabel("Max Time")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.max_time = QLineEdit()
        self.max_time.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.max_time, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel(self.default_time_units)
        label.setAlignment(QtCore.Qt.AlignLeft)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        label = QLabel("Diffusion dt")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.diffusion_dt = QLineEdit()
        self.diffusion_dt.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.diffusion_dt, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel(self.default_time_units)
        label.setAlignment(QtCore.Qt.AlignLeft)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        label = QLabel("Mechanics dt")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.mechanics_dt = QLineEdit()
        self.mechanics_dt.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.mechanics_dt, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel(self.default_time_units)
        label.setAlignment(QtCore.Qt.AlignLeft)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        label = QLabel("Phenotype dt")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.phenotype_dt = QLineEdit()
        self.phenotype_dt.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.phenotype_dt, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel(self.default_time_units)
        label.setAlignment(QtCore.Qt.AlignLeft)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        #============  Misc ================================
        label = QLabel("Misc runtime parameters")
        label.setFixedHeight(label_height)
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,20) # w, row, column, rowspan, colspan

        # label = QLabel("Max Time")
        # label.setAlignment(QtCore.Qt.AlignRight)
        # idx_row += 1
        # self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        # self.max_time = QLineEdit()
        # self.max_time.setValidator(QtGui.QDoubleValidator())
        # self.config_tab_layout.addWidget(self.max_time, idx_row,1,1,1) # w, row, column, rowspan, colspan

        # label = QLabel("min")
        # label.setAlignment(QtCore.Qt.AlignLeft)
        # self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        #----------
        label = QLabel("# threads")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.num_threads = QLineEdit()
        self.num_threads.setValidator(QtGui.QIntValidator())
        self.config_tab_layout.addWidget(self.num_threads, idx_row,1,1,1) # w, row, column, rowspan, colspan
        #----------

        label = QLabel("output folder")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.folder = QLineEdit()
        if self.nanohub_flag:
            self.folder.setEnabled(False)
        self.config_tab_layout.addWidget(self.folder, idx_row,1,1,1) # w, row, column, rowspan, colspan
        # self.folder.textChanged.connect(self.folder_name_cb)

        # if self.studio_flag:
        #     label = QLabel("Plot/Legend folder")
        #     label.setAlignment(QtCore.Qt.AlignRight)
        #     self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        #     self.plot_folder = QLineEdit()
        #     self.config_tab_layout.addWidget(self.plot_folder, idx_row,3,1,1) # w, row, column, rowspan, colspan
        #     self.plot_folder.textChanged.connect(self.plot_folder_name_cb)

        #------------------
        label = QLabel("Save data (intervals):")
        idx_row += 1
        icol = 0
        self.config_tab_layout.addWidget(label, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        #------
        self.save_svg = QCheckBox("SVG")
        icol += 2
        self.config_tab_layout.addWidget(self.save_svg, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        # label = QLabel("every")
        # label.setAlignment(QtCore.Qt.AlignRight)
        # label.setAlignment(QtCore.Qt.AlignLeft)
        # label_width = 110
        # label_width = 60
        # icol += 1
        # self.config_tab_layout.addWidget(label, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        self.svg_interval = QLineEdit()
        self.svg_interval.setValidator(QtGui.QDoubleValidator())
        icol += 1
        self.config_tab_layout.addWidget(self.svg_interval, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        label = QLabel(self.default_time_units)
        # self.config_tab_layout.addWidget(label, idx_row,4,1,2) # w, row, column, rowspan, colspan
        icol += 1
        self.config_tab_layout.addWidget(label, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        #------
        self.save_full = QCheckBox("Full")
        icol += 1
        self.config_tab_layout.addWidget(self.save_full, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        # label = QLabel("every")
        # label.setAlignment(QtCore.Qt.AlignRight)
        # icol += 1
        # self.config_tab_layout.addWidget(label, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        self.full_interval = QLineEdit()
        self.full_interval.setValidator(QtGui.QDoubleValidator())
        icol += 1
        self.config_tab_layout.addWidget(self.full_interval, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        label = QLabel(self.default_time_units)
        icol += 1
        self.config_tab_layout.addWidget(label, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        #============  Cells IC ================================
        label = QLabel("Initial conditions of cells (x,y,z, type)")
        label.setFixedHeight(label_height)
        label.setStyleSheet("background-color: orange")
        label.setAlignment(QtCore.Qt.AlignCenter)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,20) # w, row, column, rowspan, colspan

        idx_row += 1
        self.cells_csv = QCheckBox("enable")
        self.cells_csv.setEnabled(True)
        icol = 1
        self.config_tab_layout.addWidget(self.cells_csv, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        label = QLabel("folder")
        label.setAlignment(QtCore.Qt.AlignRight)
        icol += 1
        self.config_tab_layout.addWidget(label, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        self.csv_folder = QLineEdit()
        if self.nanohub_flag:
            self.folder.setEnabled(False)
        icol += 1
        self.config_tab_layout.addWidget(self.csv_folder, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        label = QLabel("file")
        label.setAlignment(QtCore.Qt.AlignRight)
        icol += 1
        self.config_tab_layout.addWidget(label, idx_row,icol,1,1) # w, row, column, rowspan, colspan

        self.csv_file = QLineEdit()
        icol += 1
        self.config_tab_layout.addWidget(self.csv_file, idx_row,icol,1,2) # w, row, column, rowspan, colspan


        self.insert_hacky_blank_lines(self.config_tab_layout)

        #==================================================================
        self.config_params.setLayout(self.config_tab_layout)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        self.scroll.setWidget(self.config_params) # self.config_params = QWidget()

        self.layout = QVBoxLayout(self)  # leave this!
        self.layout.addWidget(self.scroll)


    # def folder_name_cb(self):
    #     try:  # due to the initial callback
    #         self.plot_folder.setText(self.folder.text())
    #     except:
    #         pass

    # def plot_folder_name_cb(self):   # allow plotting data from *any* output dir
    #     try:  # due to the initial callback
    #         self.vis_tab.output_dir = self.plot_folder.text()
    #     except:
    #         pass

        #--------------------------------------------------------
    def insert_hacky_blank_lines(self, glayout):
        idr = 4
        for idx in range(11):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idr += 1
            glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan

    def fill_gui(self):

        self.xmin.setText(self.xml_root.find(".//x_min").text)
        self.xmax.setText(self.xml_root.find(".//x_max").text)
        self.xdel.setText(self.xml_root.find(".//dx").text)

        self.ymin.setText(self.xml_root.find(".//y_min").text)
        self.ymax.setText(self.xml_root.find(".//y_max").text)
        self.ydel.setText(self.xml_root.find(".//dy").text)
    
        self.zmin.setText(self.xml_root.find(".//z_min").text)
        self.zmax.setText(self.xml_root.find(".//z_max").text)
        self.zdel.setText(self.xml_root.find(".//dz").text)

        self.virtual_walls.setChecked(False)
        if self.xml_root.find(".//virtual_wall_at_domain_edge") is not None:
            if self.xml_root.find(".//virtual_wall_at_domain_edge").text.lower() == "true":
                self.virtual_walls.setChecked(True)
        
        self.max_time.setText(self.xml_root.find(".//max_time").text)
        self.diffusion_dt.setText(self.xml_root.find(".//dt_diffusion").text)
        self.mechanics_dt.setText(self.xml_root.find(".//dt_mechanics").text)
        self.phenotype_dt.setText(self.xml_root.find(".//dt_phenotype").text)
        
        self.num_threads.setText(self.xml_root.find(".//omp_num_threads").text)

        self.folder.setText(self.xml_root.find(".//folder").text)
        # if self.studio_flag:
        #     self.plot_folder.setText(self.xml_root.find(".//folder").text)
        
        self.svg_interval.setText(self.xml_root.find(".//SVG//interval").text)
        # NOTE: do this *after* filling the mcds_interval, directly above, due to the callback/constraints on them??
        if self.xml_root.find(".//SVG//enable").text.lower() == 'true':
            self.save_svg.setChecked(True)
        else:
            self.save_svg.setChecked(False)

        self.full_interval.setText(self.xml_root.find(".//full_data//interval").text)
        if self.xml_root.find(".//full_data//enable").text.lower() == 'true':
            self.save_full.setChecked(True)
        else:
            self.save_full.setChecked(False)

        uep = self.xml_root.find(".//initial_conditions//cell_positions")
        if uep == None:  # not present
            return
        self.csv_folder.setText(self.xml_root.find(".//initial_conditions//cell_positions//folder").text)
        self.csv_file.setText(self.xml_root.find(".//initial_conditions//cell_positions//filename").text)
        if uep.attrib['enabled'].lower() == 'true':
            self.cells_csv.setChecked(True)
        else:
            self.cells_csv.setChecked(False)



    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml(self):
        indent1 = '\n'
        indent6 = '\n      '
        indent8 = '\n        '
        indent10 = '\n          '

        # print("config_tab: fill_xml: xmin=",self.xmin.text() )
        self.xml_root.find(".//x_min").text = self.xmin.text()
        self.xml_root.find(".//x_max").text = self.xmax.text()
        self.xml_root.find(".//dx").text = self.xdel.text()

        self.xml_root.find(".//y_min").text = self.ymin.text()
        self.xml_root.find(".//y_max").text = self.ymax.text()
        self.xml_root.find(".//dy").text = self.ydel.text()

        self.xml_root.find(".//z_min").text = self.zmin.text()
        self.xml_root.find(".//z_max").text = self.zmax.text()
        self.xml_root.find(".//dz").text = self.zdel.text()

        # is this model 2D or 3D?
        zmax = float(self.zmax.text())
        zmin = float(self.zmin.text())
        zdel = float(self.zdel.text())
        if (zmax-zmin) > zdel:
            self.xml_root.find(".//domain//use_2D").text = 'false'
        else:
            self.xml_root.find(".//domain//use_2D").text = 'true'
        
        # may want to check for (max-min) being an integer multiple of delta spacings:
            # msg = QMessageBox()
            # msg.setIcon(QMessageBox.Critical)
            # msg.setText("Warning")
            # msg.setInformativeText('The output intervals for SVG and full (in Config Basics) do not match.')
            # msg.setWindowTitle("Warning")
            # msg.exec_()


        # if not self.xml_root.find(".//virtual_wall_at_domain_edge"):
        # opts = self.xml_root.find(".//options")
        # if not opts:
        #     print("------ Missing <options> in config .xml.  HALT.")
        #     sys.exit(1)


        # rwh: I ended up *requiring* the original .xml (which is copied) have the <virtual_wall_at_domain_edge...> element.
        bval = "false"
        if self.virtual_walls.isChecked():
            bval = "true"
        self.xml_root.find(".//virtual_wall_at_domain_edge").text = bval

        # rwh: Not sure why I couldn't get this to work, i.e., to *insert* the element (just one time) if it didn't exist.
        # vwall = self.xml_root.find(".//virtual_wall_at_domain_edge")
        # # if self.xml_root.find(".//virtual_wall_at_domain_edge"):
        # if False:
        #     print("\n------ FOUND virtual_wall_at_domain_edge.")
        # # if not opts.find(".//virtual_wall_at_domain_edge"):
        # # if not opts.find("virtual_wall_at_domain_edge"):
        #     if self.virtual_walls.isChecked():
        #         # self.xml_root.find(".//virtual_wall_at_domain_edge").text = 'true'
        #         vwall.text = 'true'
        #     else:
        #         vwall.text = 'false'
        #         # self.xml_root.find(".//virtual_wall_at_domain_edge").text = 'false'
        # else:
        #     print("\n------ virtual_wall_at_domain_edge NOT found.  Create it.")
        #     # todo: create it?  Child of root.
        #     print("------config_tab.py: no virtual_wall_at_domain_edge tag")
        #     # <options>
        #     #     <legacy_random_points_on_sphere_in_divide>false</legacy_random_points_on_sphere_in_divide>
        #     #     <virtual_wall_at_domain_edge>true</virtual_wall_at_domain_edge>		
        #     # </options>	
        #     # elm = ET.Element("options") 
        #     # # elm.tail = '\n' + indent6
        #     # elm.tail = indent6
        #     # elm.text = indent6
        #     opts = self.xml_root.find(".//options")
        #     bval = "false"
        #     if self.virtual_walls.isChecked():
        #         bval = "true"
        #     subelm = ET.SubElement(opts, 'virtual_wall_at_domain_edge')
        #     subelm.text = bval
        #     subelm.tail = indent8
        #     opts.insert(0,subelm)

        self.xml_root.find(".//max_time").text = self.max_time.text()
        self.xml_root.find(".//dt_diffusion").text = self.diffusion_dt.text()
        self.xml_root.find(".//dt_mechanics").text = self.mechanics_dt.text()
        self.xml_root.find(".//dt_phenotype").text = self.phenotype_dt.text()
        self.xml_root.find(".//omp_num_threads").text = self.num_threads.text()
        self.xml_root.find(".//folder").text = self.folder.text()
        logging.debug(f'------- config_tab.py: fill_xml(): setting folder = {self.folder.text()}')

        if self.save_svg.isChecked():
            self.xml_root.find(".//SVG//enable").text = 'true'
        else:
            self.xml_root.find(".//SVG//enable").text = 'false'
        self.xml_root.find(".//SVG//interval").text = self.svg_interval.text()

        if self.save_full.isChecked():
            self.xml_root.find(".//full_data//enable").text = 'true'
        else:
            self.xml_root.find(".//full_data//enable").text = 'false'
        self.xml_root.find(".//full_data//interval").text = self.full_interval.text()
        # self.xml_root.find(".//full_data//interval").text = self.svg_interval.text()

        if self.cells_csv.isChecked():
            self.xml_root.find(".//initial_conditions//cell_positions").attrib['enabled'] = 'true'
        else:
            self.xml_root.find(".//initial_conditions//cell_positions").attrib['enabled'] = 'false'

        # self.xml_root.find(".//initial_conditions//cell_positions/folder").text = './data'
        self.xml_root.find(".//initial_conditions//cell_positions/folder").text = self.csv_folder.text()
        logging.debug(f'------- config_tab.py: fill_xml(): setting csv folder = {self.csv_folder.text()}')

        self.xml_root.find(".//initial_conditions//cell_positions/filename").text = self.csv_file.text()
        logging.debug(f'------- config_tab.py: fill_xml(): setting csv filename = {self.csv_file.text()}')
        # if self.csv_rb1.isChecked():
        #     self.xml_root.find(".//initial_conditions//cell_positions/filename").text = 'all_cells.csv'
        # else:
        #     self.xml_root.find(".//initial_conditions//cell_positions/filename").text = 'all_cells_above_y0.csv'


        # TODO: verify valid type (numeric) and range?
        # xml_root.find(".//x_min").text = str(self.xmin.value)
        # xml_root.find(".//x_max").text = str(self.xmax.value)
        # xml_root.find(".//dx").text = str(self.xdelta.value)
        # xml_root.find(".//y_min").text = str(self.ymin.value)
        # xml_root.find(".//y_max").text = str(self.ymax.value)
        # xml_root.find(".//dy").text = str(self.ydelta.value)
        # xml_root.find(".//z_min").text = str(self.zmin.value)
        # xml_root.find(".//z_max").text = str(self.zmax.value)
        # xml_root.find(".//dz").text = str(self.zdelta.value)

        # xml_root.find(".//max_time").text = str(self.tmax.value)

        # xml_root.find(".//omp_num_threads").text = str(self.omp_threads.value)

        # xml_root.find(".//SVG").find(".//enable").text = str(self.toggle_svg.value)
        # xml_root.find(".//SVG").find(".//interval").text = str(self.svg_interval.value)
        # xml_root.find(".//full_data").find(".//enable").text = str(self.toggle_mcds.value)
        # xml_root.find(".//full_data").find(".//interval").text = str(self.mcds_interval.value)