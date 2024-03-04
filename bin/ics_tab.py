"""
ics_tab.py - create initial conditions (ICs) of cells' positions (by cell type)

Authors:
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
Rf. Credits.md
"""

import sys
import os
import logging
import time
import csv
# import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from pathlib import Path

from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection
import matplotlib.colors as mplc
from matplotlib import gridspec
from collections import deque
import glob

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,  QMainWindow,QGridLayout, QPushButton, QFileDialog, QMessageBox, QStackedWidget, QSplitter
from PyQt5.QtGui import QPixmap

from studio_classes import QHLine
from bioinf_import_tab import BioinfImport

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

class QCheckBox_custom(QCheckBox):  # it's insane to have to do this!
    def __init__(self,name):
        super(QCheckBox, self).__init__(name)

        checkbox_style = """
                QCheckBox::indicator:checked {
                    background-color: rgb(255,255,255);
                    border: 1px solid #5A5A5A;
                    width : 15px;
                    height : 15px;
                    border-radius : 3px;
                    image: url(images:checkmark.png);
                }
                QCheckBox::indicator:unchecked
                {
                    background-color: rgb(255,255,255);
                    border: 1px solid #5A5A5A;
                    width : 15px;
                    height : 15px;
                    border-radius : 3px;
                }
                """
        self.setStyleSheet(checkbox_style)

class ICs(QWidget):

    def __init__(self, config_tab, celldef_tab, bioinf_import_flag, bioinf_import_test, bioinf_import_test_spatial):
        super().__init__()
        # global self.config_params

        self.create_point = False

        self.celldef_tab = celldef_tab
        self.config_tab = config_tab

        self.bioinf_import_flag = bioinf_import_flag

        # self.circle_radius = 100  # will be set in run_tab.py using the .xml
        # self.mech_voxel_size = 30

        self.cell_radius = 8.412710547954228   # from PhysiCell_phenotype.cpp
        # self.color_by_celltype = ['gray','red','green','yellow','cyan','magenta','blue','brown','black','orange','seagreen','gold']
        self.color_by_celltype = ['gray','red','yellow','green','blue','magenta','orange','lime','cyan','hotpink','peachpuff','darkseagreen','lightskyblue']
        self.alpha_value = 1.0

        self.csv_array = np.empty([1,4])  # default floats (x,y,z,cell_type_index)
        self.csv_array = np.delete(self.csv_array,0,0)
        # print("--------------- csv_array= ",self.csv_array)

        self.plot_xmin = -500
        self.plot_xmax = 500
        self.plot_ymin = -500
        self.plot_ymax = 500

        # self.nanohub_flag = nanohub_flag

        self.bgcolor = [1,1,1,1]  # all 1.0 for white 

        self.cells_edge_checked_flag = True

        self.fontsize = 9
        self.title_fontsize = 10

        self.use_defaults = True
        self.title_str = ""

        self.show_plot_range = False

        self.numcells_l = []    # list containing # of cells per "Plot" action
        self.cell_radii = []   # master list for *all* cells' (radii) plotted in ICs

        self.x0_value = 0.
        self.y0_value = 0.
        self.z0_value = 0.

        self.r1_value = 50.
        self.r2_value = 100.
        self.r3_value = 0.

        self.o1_value = 0.
        self.o2_value = 360.
        self.odel_value = 0.

        # self.config_file = "mymodel.xml"
        # self.reset_model_flag = True
        # self.xmin = -80
        # self.xmax = 80
        # self.x_range = self.xmax - self.xmin

        # self.ymin = -50
        # self.ymax = 100
        # self.y_range = self.ymax - self.ymin

        # self.aspect_ratio = 0.7

        self.show_grid = False
        self.show_vectors = False

        self.show_nucleus = False
        # self.show_edge = False
        self.show_edge = True
        self.alpha = 0.7

        basic_length = 12.0
        self.figsize_width_substrate = 15.0  # allow extra for colormap
        self.figsize_height_substrate = basic_length

        self.figsize_width_2Dplot = basic_length
        self.figsize_height_2Dplot = basic_length

        # self.width_substrate = basic_length  # allow extra for colormap
        # self.height_substrate = basic_length

        self.figsize_width_svg = basic_length
        self.figsize_height_svg = basic_length

        self.mouse_on_axes = False

        # self.output_dir = "."   # for nanoHUB

        #-------------------------------------------
        # label_width = 110
        # value_width = 60
        # label_height = 20
        # units_width = 70

        self.combobox_stylesheet = """ 
            QComboBox{
                color: #000000;
                background-color: #FFFFFF; 
            }
            """
            # QCheckBox::indicator{
            #     color: #000000;
            #     background-color: #FFFFFF; 
            # }
        
        self.stylesheet = """ 
            QLineEdit:disabled {
                background-color: rgb(236,236,236);
                color: rgb(99,99,99);
            }
            """

        self.tab_widget = QTabWidget()
        self.base_tab_id = self.tab_widget.addTab(self.create_base_ics_tab(),"Base")
        if self.bioinf_import_flag:
            self.bioinf_import_tab = BioinfImport(self.config_tab, self.celldef_tab, self, bioinf_import_test, bioinf_import_test_spatial)
            self.tab_widget.addTab(self.bioinf_import_tab,"Bioinformatics Import")

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tab_widget)
        # if self.show_plot_range:
        #     self.layout.addWidget(self.controls2)
        # self.layout.addWidget(self.my_xmin)
        # self.layout.addWidget(self.scroll_plot)
        # self.layout.addWidget(splitter)
        # self.layout.addStretch()

        # self.create_figure()
        
    def create_base_ics_tab(self):

        self.scroll_plot = QScrollArea()  # might contain centralWidget
        # self.create_figure()

        self.vbox = QVBoxLayout()
        self.vbox.addStretch(1)

        self.ics_params = QWidget()
        # self.ics_params.setStyleSheet(self.combobox_stylesheet)
        self.ics_params.setLayout(self.vbox)

        #----
        hbox = QHBoxLayout()
        label = QLabel("cell type")
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.celltype_combobox = QComboBox()
        self.celltype_combobox.currentIndexChanged.connect(self.celltype_combobox_changed_cb)
        # self.celltype_combobox.setStyleSheet(self.combobox_stylesheet)
        self.celltype_combobox.setFixedWidth(200)  # how wide is sufficient?
        hbox.addWidget(self.celltype_combobox)
        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        self.vbox.addLayout(hbox)

        #----
        hbox = QHBoxLayout()
        self.geom_combobox = QComboBox()
        # self.geom_combobox.setStyleSheet(self.combobox_stylesheet)
        w_width = 150
        self.geom_combobox.addItem("annulus/disk")
        # self.geom_combobox.addItem("annulus(2D)/shell(3D)")
        self.geom_combobox.addItem("box")
        self.geom_combobox.addItem("ring")
        self.geom_combobox.addItem("point")
        self.geom_combobox.setFixedWidth(180)
        self.geom_combobox.currentIndexChanged.connect(self.geom_combobox_changed_cb)
        hbox.addWidget(self.geom_combobox)

        self.fill_combobox = QComboBox()
        self.fill_combobox.setFixedWidth(w_width)
        self.fill_combobox.addItem("random fill")
        self.fill_combobox.addItem("hex fill")
        self.fill_combobox.currentIndexChanged.connect(self.fill_combobox_changed_cb)
        hbox.addWidget(self.fill_combobox)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        self.vbox.addLayout(hbox)

        #----
        hbox = QHBoxLayout()
        label = QLabel("# cells")
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.num_cells = QLineEdit()
        self.num_cells.setStyleSheet(self.stylesheet)
        fixed_width_value = 80
        self.num_cells.setFixedWidth(fixed_width_value)
        self.num_cells.setValidator(QtGui.QIntValidator(1,100000))
        self.num_cells.setEnabled(True)
        self.num_cells.setText('100')
        # self.glayout1.addWidget(self.num_cells, idr,icol,1,1) 
        hbox.addWidget(self.num_cells)

        self.zeq0 = QCheckBox_custom("2D (z=0) (no 3D yet)")
        self.zeq0.setChecked(True)
        self.zeq0.setEnabled(False)
        zeq0_style = """
                QCheckBox::indicator:checked {
                    background-color: rgb(199,199,199);
                    border: 1px solid #5A5A5A;
                    width : 15px;
                    height : 15px;
                    border-radius : 3px;
                    image: url(images:checkmark.png);
                }
                """
        # self.zeq0.setStyleSheet("QCheckBox::indicator {background-color: rgb(199,199,199); image: url(images:checkmark.png);}")
        self.zeq0.setStyleSheet(zeq0_style)
        # self.zeq0.setFixedWidth(50)
        self.zeq0.clicked.connect(self.zeq0_cb)
        hbox.addWidget(self.zeq0)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        self.vbox.addLayout(hbox)

        #----
        hbox = QHBoxLayout()

        cvalue_width = 70
        label = QLabel("x0")
        label.setFixedWidth(30)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.x0val = QLineEdit()
        self.x0val.setFixedWidth(fixed_width_value)
        self.x0val.setEnabled(True)
        self.x0val.setText(str(self.x0_value))
        self.x0val.setValidator(QtGui.QDoubleValidator())
        self.x0val.textChanged.connect(self.x0_cb)
        hbox.addWidget(self.x0val)

        #--------
        label = QLabel("y0")
        label.setFixedWidth(30)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.y0val = QLineEdit()
        self.y0val.setFixedWidth(fixed_width_value)
        self.y0val.setEnabled(True)
        self.y0val.setText(str(self.y0_value))
        self.y0val.setValidator(QtGui.QDoubleValidator())
        self.y0val.textChanged.connect(self.y0_cb)
        hbox.addWidget(self.y0val)

        #--------
        z0_label = QLabel("z0")
        label.setFixedWidth(30)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(z0_label)

        self.z0val = QLineEdit()
        self.z0val.setFixedWidth(fixed_width_value)
        self.z0val.setEnabled(False)
        # self.z0val.setStyleSheet("QLineEdit {background-color: rgb(200,200,200); color: black;}")
        self.z0val.setText(str(self.z0_value))
        self.z0val.setValidator(QtGui.QDoubleValidator())
        self.z0val.textChanged.connect(self.z0_cb)
        hbox.addWidget(self.z0val)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        self.vbox.addLayout(hbox)

        #----
        hbox = QHBoxLayout()

        cvalue_width = 70
        label = QLabel("R1")  # confusing, but let's change the label to "R" (~radius) instead of "D" (distance)
        label.setFixedWidth(30)
        # label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.r1val = QLineEdit()
        self.r1val.setFixedWidth(fixed_width_value)
        self.r1val.setEnabled(True)
        self.r1val.setText(str(self.r1_value))
        # self.cmin.textChanged.connect(self.change_plot_range)
        # self.r1val.returnPressed.connect(self.rval_cb)
        self.r1val.textChanged.connect(self.rval_cb)
        # self.r1val.setFixedWidth(cvalue_width)
        self.r1val.setValidator(QtGui.QDoubleValidator(0.,10000.,2))
        hbox.addWidget(self.r1val)

        #------
        label = QLabel("R2")
        label.setFixedWidth(30)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.r2val = QLineEdit()
        self.r2val.setFixedWidth(fixed_width_value)
        self.r2val.setEnabled(True)
        self.r2val.setText(str(self.r2_value))
        # self.r2val.returnPressed.connect(self.rval_cb)
        self.r2val.textChanged.connect(self.rval_cb)
        # self.r2val.setFixedWidth(cvalue_width)
        self.r2val.setValidator(QtGui.QDoubleValidator(0.,10000.,2))
        hbox.addWidget(self.r2val)

        #------
        label = QLabel("R3")
        label.setFixedWidth(30)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.r3val = QLineEdit()
        self.r3val.setFixedWidth(fixed_width_value)
        self.r3val.setEnabled(False)
        # self.r3val.setStyleSheet("QLineEdit {background-color: rgb(200,200,200); color: black;}")
        self.r3val.setText(str(self.r3_value))
        # self.r3val.returnPressed.connect(self.rval_cb)
        self.r3val.textChanged.connect(self.rval_cb)
        # self.r3val.setFixedWidth(cvalue_width)
        self.r3val.setValidator(QtGui.QDoubleValidator(0.,10000.,2))
        hbox.addWidget(self.r3val)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        self.vbox.addLayout(hbox)

        #----
        hbox = QHBoxLayout()

        cvalue_width = 70
        label = QLabel("o1")  # omega 1: starting angle for a "ring" of cells
        label.setFixedWidth(30)
        # label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.o1val = QLineEdit()
        self.o1val.setFixedWidth(fixed_width_value)
        self.o1val.setEnabled(True)
        self.o1val.setText(str(self.o1_value))
        # self.cmin.textChanged.connect(self.change_plot_range)
        # self.r1val.returnPressed.connect(self.rval_cb)
        self.o1val.textChanged.connect(self.oval_cb)
        # self.r1val.setFixedWidth(cvalue_width)
        self.o1val.setValidator(QtGui.QDoubleValidator(-360.,360.,2))
        hbox.addWidget(self.o1val)

        #------
        label = QLabel("o2")
        label.setFixedWidth(30)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.o2val = QLineEdit()
        self.o2val.setFixedWidth(fixed_width_value)
        self.o2val.setEnabled(True)
        self.o2val.setText(str(self.o2_value))
        # self.r2val.returnPressed.connect(self.rval_cb)
        self.o2val.textChanged.connect(self.oval_cb)
        # self.r2val.setFixedWidth(cvalue_width)
        self.o2val.setValidator(QtGui.QDoubleValidator(-360.,360.,2))
        hbox.addWidget(self.o2val)

        #------
        label = QLabel("mod")
        label.setFixedWidth(30)
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.odelw = QLineEdit()
        self.odelw.setFixedWidth(fixed_width_value)
        # self.r3val.setStyleSheet("QLineEdit {background-color: rgb(200,200,200); color: black;}")
        self.odelw.setText("1")
        # self.r3val.returnPressed.connect(self.rval_cb)
        self.odelw.textChanged.connect(self.odelw_cb)
        # self.r3val.setFixedWidth(cvalue_width)
        self.odelw.setValidator(QtGui.QIntValidator(1,99))
        hbox.addWidget(self.odelw)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        self.vbox.addLayout(hbox)


        #----
        self.enable_3Dwidgets(False)
        self.enable_ring_params(False)

        #----

        hbox = QHBoxLayout()
        btn_width = 80
        self.clear_button = QPushButton("Clear all")
        self.clear_button.setFixedWidth(btn_width)
        self.clear_button.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        self.clear_button.clicked.connect(self.clear_cb)
        hbox.addWidget(self.clear_button)

        self.plot_button = QPushButton("Plot")
        self.plot_button.setFixedWidth(btn_width)
        self.plot_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        # self.plot_button.clicked.connect(self.uniform_random_pts_annulus_cb)
        self.plot_button.clicked.connect(self.plot_cb)
        hbox.addWidget(self.plot_button)

        self.undo_button = QPushButton("Undo last")
        self.undo_button.setFixedWidth(btn_width)
        self.undo_button.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        # self.plot_button.clicked.connect(self.uniform_random_pts_annulus_cb)
        self.undo_button.clicked.connect(self.undo_cb)
        hbox.addWidget(self.undo_button)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left

        self.vbox.addLayout(hbox)

        #---------------------
        # self.vbox.addWidget(QHLine())

        # hbox = QHBoxLayout()
        self.import_button = QPushButton("Import (cell type name syntax only)")
        self.import_button.setFixedWidth(230)
        self.import_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        self.import_button.clicked.connect(self.import_cb)
        self.vbox.addWidget(self.import_button)

        # self.plot_button2 = QPushButton("Plot")
        # self.plot_button2.setFixedWidth(btn_width)
        # self.plot_button2.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        # self.plot_button2.clicked.connect(self.plot_import_cb)
        # hbox.addWidget(self.plot_button2)

        # hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left

        # self.vbox.addLayout(hbox)

        #---------------------
        # Maybe later provide a cute diagram explaining D1,D2
        # diagram = QLabel("pic")
        # pixmap = QPixmap('physicell_logo_200px.png')  # in root by default
        # diagram.setPixmap(pixmap)
        # self.vbox.addWidget(diagram)

        #---------------------
        self.vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.setFixedWidth(btn_width)
        # self.save_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        self.save_button.setStyleSheet("QPushButton {background-color: yellow; color: black;}")
        # self.plot_button.clicked.connect(self.uniform_random_pts_annulus_cb)
        self.save_button.clicked.connect(self.save_cb)
        hbox.addWidget(self.save_button)
        # self.vbox.addWidget(self.save_button)

        self.use_names = QCheckBox_custom("use cell type names")
        self.use_names.setChecked(True)
        hbox.addWidget(self.use_names)

        hbox.addWidget(QLabel(''))

        # self.zeq0 = QCheckBox_custom("z=0")
        # # self.zeq0.setFixedWidth(50)
        # self.zeq0.setChecked(True)
        # self.zeq0.clicked.connect(self.zeq0_cb)
        # hbox.addWidget(self.zeq0)

        self.vbox.addLayout(hbox)

        #---
        hbox = QHBoxLayout()
        label = QLabel("folder")
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.csv_folder = QLineEdit("config")
        # rx_valid_varname = QtCore.QRegExp("^[a-zA-Z][a-zA-Z0-9_]+$")
        # name_validator = QtGui.QRegExpValidator(rx_valid_varname)
        # self.csv_folder.setValidator(name_validator)
        # self.csv_folder.returnPressed.connect(self.csv_folder_cb)
        hbox.addWidget(self.csv_folder)

        #--
        # hbox = QHBoxLayout()
        label = QLabel("file")
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.output_file = QLineEdit("cells.csv")
        # self.output_file.setValidator(name_validator)
        hbox.addWidget(self.output_file)
        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        self.vbox.addLayout(hbox)

        #---------------------
        splitter = QSplitter()
        self.scroll_params = QScrollArea()
        splitter.addWidget(self.scroll_params)
        self.scroll_params.setWidget(self.ics_params)

        #-------------------
        # self.celltype_combobox.currentIndexChanged.connect(self.celltype_combobox_changed_cb)

        # controls_vbox = QVBoxLayout()
        # controls_vbox.addLayout(controls_hbox)
        # controls_vbox.addLayout(controls_hbox2)

        #==================================================================
        self.ics_params.setLayout(self.vbox)

        # self.scroll_params.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        # self.scroll_params.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        # self.scroll_params.setWidgetResizable(True)

        self.scroll_plot.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_plot.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_plot.setWidgetResizable(True)

        # self.scroll_plot.setWidget(self.config_params) # self.config_params = QWidget()
        self.create_figure()
        self.scroll_plot.setWidget(self.canvas) # self.config_params = QWidget()
        splitter.addWidget(self.scroll_plot)
        
        self.show_plot_range = False

        return splitter

    def update_colors_list(self):
        if len(self.celldef_tab.celltypes_list) >= len(self.color_by_celltype):
            # print("ics_tab: update_colors_list(): exceeded # of colors. Grow it.")
            self.color_by_celltype.append('white')  # match what's done in PhysiCell

    def fill_celltype_combobox(self):
        logging.debug(f'ics_tab.py: fill_celltype_combobox(): {self.celldef_tab.celltypes_list}')
        for cdef in self.celldef_tab.celltypes_list:
            self.celltype_combobox.addItem(cdef)

    def reset_plot_range(self):
        self.plot_xmin = float(self.config_tab.xmin.text())
        self.plot_xmax = float(self.config_tab.xmax.text())
        self.plot_ymin = float(self.config_tab.ymin.text())
        self.plot_ymax = float(self.config_tab.ymax.text())
        try:  # due to the initial callback
            # self.my_xmin.setText(str(self.xmin))
            # self.my_xmax.setText(str(self.xmax))
            # self.my_ymin.setText(str(self.ymin))
            # self.my_ymax.setText(str(self.ymax))

            # self.plot_xmin = float(self.xmin)
            # self.plot_xmax = float(self.xmax)
            # self.plot_ymin = float(self.ymin)
            # self.plot_ymax = float(self.ymax)
            logging.debug(f'ics_tab.py: -------- ICs: reset_plot_range(): plot_xmin,xmax=  {self.plot_xmin,self.plot_xmax}')
            logging.debug(f'ics_tab.py: -------- ICs: reset_plot_range(): plot_ymin,ymax=  {self.plot_ymin,self.plot_ymax}')
        except:
            pass

        # self.update_plots()


    def x0_cb(self):
        try:  # due to the initial callback
            self.x0_value = float(self.x0val.text())
        except:
            pass

    def y0_cb(self):
        try:  # due to the initial callback
            self.y0_value = float(self.y0val.text())
        except:
            pass

    def z0_cb(self):
        try:  # due to the initial callback
            self.z0_value = float(self.z0val.text())
        except:
            pass

    def rval_cb(self):
        # print("----- rval_cb:")
        try:  # due to the initial callback
            self.r1_value = float(self.r1val.text())
            self.r2_value = float(self.r2val.text())
            self.r3_value = float(self.r3val.text())
            # print(self.r1_value, self.r2_value)

            # delta_theta = np.arcsin(self.cell_radius / self.r2_value)
            # print("rval_cb(): delta_theta= ",delta_theta)
            # self.odelw.setText(f'{delta_theta:.6f}')
        except:
            pass
        # self.update_plots()

    def odelw_cb(self):
        print("odelw_cb(): ",self.odelw.text())
        try:
            if int(self.odelw.text()) < 1:
                self.odelw.setText("1")
        except:
            # self.odelw.setText("1")
            pass

    def oval_cb(self):
        # print("----- oval_cb:")
        rval = self.cell_radius
        R = self.r2_value
        # delta_theta = np.arcsin(rval / R)
        # print("oval_cb(): delta_theta= ",delta_theta)
        # self.odelw.setText(f'{delta_theta:.6f}')

        try:  # due to the initial callback
            self.o1_value = float(self.o1val.text())
            self.o2_value = float(self.o2val.text())
            # self.odel_value = float(self.odelw.text())
            # print(self.r1_value, self.r2_value)
        except:
            pass
        # self.update_plots()

    def init_plot_range(self, config_tab):
        # print("----- init_plot_range:")
        try:
            # beware of widget callback 
            self.my_xmin.setText(config_tab.xmin.text())
            self.my_xmax.setText(config_tab.xmax.text())
            self.my_ymin.setText(config_tab.ymin.text())
            self.my_ymax.setText(config_tab.ymax.text())
            self.my_zmin.setText(config_tab.zmin.text())
            self.my_zmax.setText(config_tab.zmax.text())
        except:
            pass

    def change_plot_range(self):
        # print("\n----- change_plot_range:")
        # print("----- my_xmin= ",self.my_xmin.text())
        # print("----- my_xmax= ",self.my_xmax.text())
        try:  # due to the initial callback
            self.plot_xmin = float(self.my_xmin.text())
            self.plot_xmax = float(self.my_xmax.text())
            self.plot_ymin = float(self.my_ymin.text())
            self.plot_ymax = float(self.my_ymax.text())
            self.update_plots()
        except:
            pass

        # self.update_plots()

    def update_plots(self):
        self.ax0.cla()
        self.canvas.update()
        self.canvas.draw()

    def fill_cell_types_combobox(self, substrate_list):
        self.cell_types_combobox.clear()
        idx = 0
        for s in substrate_list:
            # print(" --> ",s)
            self.cell_types_combobox.addItem(s)
            self.field_dict[idx] = s   # e.g., self.field_dict = {0:'director signal', 1:'cargo signal'}
            self.field_min_max[s]= [0,1,False]
            # self.field_min_max[s][1] = 1
            # self.field_min_max[s][2] = False
            idx += 1
        # print('field_dict= ',self.field_dict)
        # print('field_min_max= ',self.field_min_max)
        # self.substrates_combobox.setCurrentIndex(2)  # not working; gets reset to oxygen somehow after a Run

    def celltype_combobox_changed_cb(self,idx):
        try:
            # print("----- celltype_combobox_changed_cb: idx = ",idx)
            cdef = self.celltype_combobox.currentText()
            volume = float(self.celldef_tab.param_d[cdef]["volume_total"])
            self.cell_radius = (volume * 0.75 / np.pi) ** (1./3)
            # print("self.cell_radius= ",self.cell_radius)
        except:
            pass
        # self.update_plots()

    def enable_ring_params(self, bval):
        self.o1val.setEnabled(bval)
        self.o2val.setEnabled(bval)
        self.odelw.setEnabled(bval)

        # for now, until 3D even possible
        # self.odelw.setEnabled(False)
        # self.odelw.setStyleSheet("QLineEdit {background-color: rgb(200,200,200); color: black;}")

        if bval:
            self.o1val.setStyleSheet("QLineEdit {background-color: white; color: black;}")
            self.o2val.setStyleSheet("QLineEdit {background-color: white; color: black;}")
            self.odelw.setStyleSheet("QLineEdit {background-color: white; color: black;}")
            # rval = self.cell_radius
            # R = self.r2_value
            # delta_theta = np.arcsin(rval / R)
            # print("delta_theta= ",delta_theta)
            # self.odelw.setText(f'{delta_theta:.6f}')
        else:
            self.o1val.setStyleSheet("QLineEdit {background-color: rgb(200,200,200); color: black;}")
            self.o2val.setStyleSheet("QLineEdit {background-color: rgb(200,200,200); color: black;}")
            self.odelw.setStyleSheet("QLineEdit {background-color: rgb(200,200,200); color: black;}")

    def enable_3Dwidgets(self, bval):
        print("----- enable_3Dwidgets: bval = ",bval)
        self.z0val.setEnabled(bval)
        # self.odelw.setEnabled(bval)

        if self.geom_combobox.currentText() == "box":
            self.r3val.setEnabled(False)
        else:
            self.r3val.setEnabled(bval)
        if bval:
            print("----- enable_3Dwidgets: bval = ",bval)
            self.z0val.setStyleSheet("QLineEdit {background-color: white; color: black;}")
            if self.geom_combobox.currentText() == "box":
                self.r3val.setStyleSheet("QLineEdit {background-color: white; color: black;}")
            else:
                self.r3val.setStyleSheet("QLineEdit {background-color: rgb(200,200,200); color: black;}")
        else:
            print("----- enable_3Dwidgets: bval = ",bval)
            self.z0val.setStyleSheet("QLineEdit {background-color: rgb(200,200,200); color: black;}")
            self.r3val.setStyleSheet("QLineEdit {background-color: rgb(200,200,200); color: black;}")
            self.odelw.setStyleSheet("QLineEdit {background-color: rgb(200,200,200); color: black;}")
        
    def set_to_origin(self):
        self.x0_value = self.y0_value = self.z0_value = 0.
        self.x0val.setText("0.0")
        self.y0val.setText("0.0")
        self.z0val.setText("0.0")

    def zeq0_cb(self,bval):
        print("----- zeq0_cb: bval = ",bval)
        self.enable_3Dwidgets(not bval)

        if not bval:
        # self.z0val.setEnabled(bval)
        # self.z0_label.setEnabled(bval)
            self.set_to_origin()

    def geom_combobox_changed_cb(self,idx):
        # print("----- geom_combobox_changed_cb: idx = ",idx)
        # print("----- geom_combobox_changed_cb: geom_combobox.currentText() = ",self.geom_combobox.currentText())
        sel_str = self.geom_combobox.currentText()
        # if not self.zeq0.isChecked():
        #     self.create_point = False
        #     if sel_str == "point":
        #         self.create_point = True
        #         print("------- setting 3D point")
        #         return
        #     elif sel_str == "box":
        #         self.r3val.setEnabled(True)
        #         self.r3val.setStyleSheet("QLineEdit {background-color: white; color: black;}")
        #         self.enable_ring_params(False)
        #     elif sel_str == "ring":
        #         self.enable_ring_params(True)
        #         # self.r3val.setEnabled(True)
        #         # self.r3val.setStyleSheet("QLineEdit {background-color: white; color: black;}")
        #     else:
        #         self.r3val.setEnabled(False)
        #         self.r3val.setStyleSheet("QLineEdit {background-color: rgb(200,200,200); color: black;}")
        #         self.enable_ring_params(False)

        self.create_point = False
        if self.geom_combobox.currentText().find("point") >= 0:
            self.create_point = True
            # print("------- setting point")
            return
        if self.geom_combobox.currentText().find("ring") >= 0:
            self.enable_ring_params(True)
            # print("got ring!")
            self.num_cells.setEnabled(False)
            self.fill_combobox.setEnabled(False)
            self.r1val.setEnabled(False)
            self.r1val.setStyleSheet("QLineEdit {background-color: rgb(200,200,200); color: black;}")
            return
        else:
            self.enable_ring_params(False)
            self.fill_combobox.setEnabled(True)
            self.r1val.setEnabled(True)
            self.r1val.setStyleSheet("QLineEdit {background-color: white; color: black;}")

        if "hex" in self.fill_combobox.currentText():
            self.num_cells.setEnabled(False)
        else:
            self.num_cells.setEnabled(True)
        # if idx == 0:
        #     self.r2val.setEnabled(False)
        # else:
        #     self.r2val.setEnabled(True)
        # self.update_plots()

    def fill_combobox_changed_cb(self,idx):
        # print("----- fill_combobox_changed_cb: idx = ",idx)
        if "hex" in self.fill_combobox.currentText():
            self.num_cells.setEnabled(False)
        else:
            self.num_cells.setEnabled(True)
        # self.update_plots()


    def open_directory_cb(self):
        dialog = QFileDialog()
        # self.output_dir = dialog.getExistingDirectory(self, 'Select an output directory')
        tmp_dir = dialog.getExistingDirectory(self, 'Select an output directory')
        # print("open_directory_cb:  tmp_dir=",tmp_dir)
        if tmp_dir == "":
            return

        self.output_dir = tmp_dir
        self.output_dir_w.setText(self.output_dir)
        self.reset_model()

    def reset_info(self):
        # print("\nics_tab:  --- reset_info()")
        self.celltype_combobox.clear()
        self.fill_celltype_combobox()
        self.csv_array = np.empty([1,4])
        self.csv_array = np.delete(self.csv_array,0,0)
        self.numcells_l = []
        self.cell_radii = []

        self.plot_xmin = float(self.config_tab.xmin.text())
        self.plot_xmax = float(self.config_tab.xmax.text())
        self.plot_ymin = float(self.config_tab.ymin.text())
        self.plot_ymax = float(self.config_tab.ymax.text())
        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)
        # self.update_plots()
        self.canvas.update()
        self.canvas.draw()


    def button_press(self,event):
        if self.create_point:
            # print("------ button_press()")
            xval = event.xdata  # or "None" if outside plot domain
            yval = event.ydata
            zval = 0.0
            # print("event.inaxes", event.inaxes)  # Axes(0.125,0.146794;0.775x0.696412)
            # print("x", event.x)  # e.g.,750
            # print("y", event.y)  # e.g., 562
            # print("size=",self.canvas.size())

            if self.create_point and (xval is not None):
                xlist = deque()
                ylist = deque()
                rlist = deque()
                rgba_list = deque()
                # cdef = self.celltype_combobox.currentText()
                # volume = float(self.celldef_tab.param_d[cdef]["volume_total"])
                # self.cell_radius = (volume * 0.75 / np.pi) ** (1./3)
                rval = self.cell_radius

                # print("event.xdata (xval)=", xval)
                # print("event.ydata (yval)=", yval)
                cell_type_index = self.celltype_combobox.currentIndex()
                xlist.append(xval)
                ylist.append(yval)
                # self.csv_array = np.append(self.csv_array,[[xval_offset,yval,zval, cell_type_index]],axis=0)
                self.csv_array = np.append(self.csv_array,[[xval,yval,zval, cell_type_index]],axis=0)
                rlist.append(rval)
                self.cell_radii.append(self.cell_radius)

                self.numcells_l.append(1)

                xvals = np.array(xlist)
                yvals = np.array(ylist)
                rvals = np.array(rlist)
                # rgbas = np.array(rgba_list)

                if (self.cells_edge_checked_flag):
                    try:
                        self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
                    except (ValueError):
                        pass
                else:
                    self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], alpha=self.alpha_value)

                self.ax0.set_aspect(1.0)

                self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
                self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)

                # self.update_plots()
                self.canvas.update()
                self.canvas.draw()


    def create_figure(self):
        # print("\nics_tab:  --------- create_figure(): ------- creating figure, canvas, ax0")
        self.figure = plt.figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.mpl_connect("button_press_event", self.button_press)
        self.canvas.mpl_connect("motion_notify_event", self.mouseMoved) # for substrate placement when point not selected
        self.canvas.mpl_connect('axes_enter_event', self.on_enter_axes)
        self.canvas.mpl_connect('axes_leave_event', self.on_leave_axes)
        self.canvas.mpl_connect("motion_notify_event", self.mouseMoved) # for substrate placement when point not selected
        self.canvas.setStyleSheet("background-color:transparent;")

        self.ax0 = self.figure.add_subplot(111, adjustable='box')

        # self.reset_model()

        # print("ics_tab:  create_figure(): ------- creating dummy contourf")
        # xlist = np.linspace(-3.0, 3.0, 50)
        # print("len(xlist)=",len(xlist))
        # ylist = np.linspace(-3.0, 3.0, 50)
        # X, Y = np.meshgrid(xlist, ylist)
        # Z = np.sqrt(X**2 + Y**2) + 10*np.random.rand()

        # self.cmap = plt.cm.get_cmap("viridis")
        # self.mysubstrate = self.ax0.contourf(X, Y, Z, cmap=self.cmap)

        # print("ics_tab:  ------------create_figure():  # axes = ",len(self.figure.axes))

        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)
        self.ax0.set_aspect(1.0)

        # self.update_plots()
        self.canvas.update()
        self.canvas.draw()

    #---------------------------------------------------------------------------
    def getPos(self, event):
        x = event.xdata  # or "None" if outside plot domain
        y = event.ydata
        z = 0.0
        return x, y, z
    
    def circles(self, x, y, s, c='b', vmin=None, vmax=None, **kwargs):
        """
        See https://gist.github.com/syrte/592a062c562cd2a98a83 

        Make a scatter plot of circles. 
        Similar to plt.scatter, but the size of circles are in data scale.
        Parameters
        ----------
        x, y : scalar or array_like, shape (n, )
            Input data
        s : scalar or array_like, shape (n, ) 
            Radius of circles.
        c : color or sequence of color, optional, default : 'b'
            `c` can be a single color format string, or a sequence of color
            specifications of length `N`, or a sequence of `N` numbers to be
            mapped to colors using the `cmap` and `norm` specified via kwargs.
            Note that `c` should not be a single numeric RGB or RGBA sequence 
            because that is indistinguishable from an array of values
            to be colormapped. (If you insist, use `color` instead.)  
            `c` can be a 2-D array in which the rows are RGB or RGBA, however. 
        vmin, vmax : scalar, optional, default: None
            `vmin` and `vmax` are used in conjunction with `norm` to normalize
            luminance data.  If either are `None`, the min and max of the
            color array is used.
        kwargs : `~matplotlib.collections.Collection` properties
            Eg. alpha, edgecolor(ec), facecolor(fc), linewidth(lw), linestyle(ls), 
            norm, cmap, transform, etc.
        Returns
        -------
        paths : `~matplotlib.collections.PathCollection`
        Examples
        --------
        a = np.arange(11)
        circles(a, a, s=a*0.2, c=a, alpha=0.5, ec='none')
        plt.colorbar()
        License
        --------
        This code is under [The BSD 3-Clause License]
        (http://opensource.org/licenses/BSD-3-Clause)
        """

        if np.isscalar(c):
            kwargs.setdefault('color', c)
            c = None

        if 'fc' in kwargs:
            kwargs.setdefault('facecolor', kwargs.pop('fc'))
        if 'ec' in kwargs:
            kwargs.setdefault('edgecolor', kwargs.pop('ec'))
        if 'ls' in kwargs:
            kwargs.setdefault('linestyle', kwargs.pop('ls'))
        if 'lw' in kwargs:
            kwargs.setdefault('linewidth', kwargs.pop('lw'))
        # You can set `facecolor` with an array for each patch,
        # while you can only set `facecolors` with a value for all.

        zipped = np.broadcast(x, y, s)
        patches = [Circle((x_, y_), s_)
                for x_, y_, s_ in zipped]
        collection = PatchCollection(patches, **kwargs)
        if c is not None:
            c = np.broadcast_to(c, zipped.shape).ravel()
            collection.set_array(c)
            collection.set_clim(vmin, vmax)

        # ax = plt.gca()
        # ax.add_collection(collection)
        # ax.autoscale_view()
        self.ax0.add_collection(collection)
        self.ax0.autoscale_view()
        # plt.draw_if_interactive()
        if c is not None:
            # plt.sci(collection)
            self.ax0.sci(collection)
        # return collection


    def annulus_error(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("R2 must be > R1 for annulus/disk")
        #    msgBox.setWindowTitle("Example")
        msgBox.setStandardButtons(QMessageBox.Ok)
        # msgBox.buttonClicked.connect(msgButtonClick)

        returnValue = msgBox.exec()
        # if returnValue == QMessageBox.Ok:
            # print('OK clicked')

    #------------------------------------------------------------
    def plot_cb(self):
        self.reset_plot_range()
        # self.cell_radii = []
        # print("len(self.numcells_l)= ",len(self.numcells_l))
        # print("plot_cb(): self.numcells_l= ",self.numcells_l)

        # if self.create_point:
        #     print("------- plot list of single points")
        #     return

        ncells = int(self.num_cells.text())
        if ncells <= 0:
            msg = "Invalid # of cells."
            print(msg)
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText(msg)
            msgBox.setStandardButtons(QMessageBox.Ok)
            returnValue = msgBox.exec()
            return

        # cdef = self.celltype_combobox.currentText()
        # volume = float(self.celldef_tab.param_d[cdef]["volume_total"])
        # self.cell_radius = (volume * 0.75 / np.pi) ** (1./3)
        # logging.debug(f'ics_tab.py: volume= {volume}, radius= {self.cell_radius}')

        if "annulus" in self.geom_combobox.currentText():
            if self.r2_value <= self.r1_value:
                self.annulus_error()
                return
            if "random" in self.fill_combobox.currentText():
                self.uniform_random_pts_annulus()
            elif "hex" in self.fill_combobox.currentText():
                self.hex_pts_annulus()

        elif "box" in self.geom_combobox.currentText():
            if "random" in self.fill_combobox.currentText():
                self.uniform_random_pts_box()
            elif "hex" in self.fill_combobox.currentText():
                self.hex_pts_box()

        elif "ring" in self.geom_combobox.currentText():
            self.ring()

    #------------------------------------------------------------
    # def plot_import_cb(self):
    #     self.reset_plot_range()
    #     # self.cell_radii = []
    #     print("len(self.numcells_l)= ",len(self.numcells_l))
    #     print("self.numcells_l= ",self.numcells_l)

    #------------------------------------------------------------
    def undo_cb(self):
        # print("----- undo_cb(): self.numcells_l = ",self.numcells_l)
        # nlast = self.numcells_l[-1]
        try:
            nlast = self.numcells_l.pop()
        except:
            print("Error self.numcells_l.pop()")
            return
        ntotal = len(self.csv_array)
        
        self.reset_plot_range()
        # erase everything, redraw below
        self.ax0.cla()

        self.csv_array = self.csv_array[0:ntotal-nlast, :]
        self.cell_radii = self.cell_radii[0:ntotal-nlast]
        # print("---after:")
        # print("csv_array=",self.csv_array)
        # print("csv_array.shape=",self.csv_array.shape)
        xvals = self.csv_array[:, 0]
        yvals = self.csv_array[:, 1]
        zvals = self.csv_array[:, 2]
        cell_colors = []

        # rvals = 8
        rvals = self.cell_radii

        for idx in range(len(xvals)):
            cell_type = int(self.csv_array[idx,3])
            cell_colors.append(self.color_by_celltype[cell_type])
        # print(cell_colors)

        if (self.cells_edge_checked_flag):
            try:
                # self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
                self.circles(xvals,yvals, s=rvals, color=cell_colors, edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
            except (ValueError):
                pass
        else:
            self.circles(xvals,yvals, s=rvals, color=cell_colors, alpha=self.alpha_value)

        self.ax0.set_aspect(1.0)

        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)

        # self.update_plots()
        self.canvas.update()
        self.canvas.draw()

    #----------------------------------
    def hex_pts_box(self):
        xlist = deque()
        ylist = deque()
        rlist = deque()
        rgba_list = deque()

        rval = self.cell_radius

        colors = np.empty((0,4))
        count = 0
        # zval = 0.0
        cell_type_index = self.celltype_combobox.currentIndex()
        
        ncells = int(self.num_cells.text())
        # print("self.r1_value= ", self.r1_value)

        x_min = -self.r1_value
        x_max =  self.r1_value
        y_min = -self.r2_value
        y_max =  self.r2_value
        y_idx = -1
        # hex packing constants
        x_spacing = self.cell_radius * 2
        y_spacing = self.cell_radius * np.sqrt(3)

        cells_x = np.array([])
        cells_y = np.array([])

        cells_x2 = np.array([])
        cells_y2 = np.array([])

        y_idx = 0
        z_idx = 0

        if self.zeq0.isChecked():  # 2D
            zval = 0.0
            for yval in np.arange(y_min,y_max, y_spacing):
                y_idx += 1
                for xval in np.arange(x_min,x_max, x_spacing):
                    # xval_offset = xval + (y_idx%2) * self.cell_radius
                    xval_offset = self.x0_value + xval + (y_idx%2) * self.cell_radius
                    yval_offset = yval + self.y0_value

                    if xval_offset < self.plot_xmin or xval_offset > self.plot_xmax \
                        or yval_offset < self.plot_ymin or yval_offset > self.plot_ymax:
                        continue
                    else:
                        xlist.append(xval_offset)
                        ylist.append(yval_offset)
                        # self.csv_array = np.append(self.csv_array,[[xval,yval,zval, cell_type_index]],axis=0)
                        self.csv_array = np.append(self.csv_array,[[xval_offset,yval_offset, zval, cell_type_index]],axis=0)
                        rlist.append(rval)
                        self.cell_radii.append(self.cell_radius)
                        count+=1
        else:   # 3D

            # for z in np.arange(z_min, z_max, z_spacing):
            #     zc += 1
            #     z_xoffset = (zc % 2) * cell_radius
            #     z_yoffset = (zc % 2) * eq_tri_yctr   # 0.5773502691896256
            #     zsq = z * z
            #     term3 = (z - z0_e) * (z - z0_e)
            #     # print("z_xoffset=",z_xoffset)
            #     # print("z_yoffset=",z_yoffset)
            #     for y in np.arange(y_min, y_max, y_spacing):
            #         yc += 1
            #         y2 = y + z_yoffset 
            #         ysq = y2 * y2
            #         term2 = (y2 - y0_e) * (y2 - y0_e)
            #         # print('--------')
            #         for x in np.arange(x_min, x_max, x_spacing):
            #             x2 = x + (yc%2) * self.cell_radius + z_xoffset
            #             xsq = x2 * x2
            #             term1 = (x2 - x0_e) * (x2 - x0_e)
            #             # print(x2,y2,z)
            #             if ( (z<0.0) and (xsq + ysq + zsq) < sphere_radius2):  # assume centered about origin
            #                 xyz = np.append(xyz, np.array([[x2,y2,z]]), axis=0)
            #                 # val = (xsq + ysq)/a2 + zsq/c2
            #                 val = (term1 + term2)/a2 + term3/c2
            #                 # print(val)

#------
            for yval in np.arange(y_min,y_max, y_spacing):
                y_idx += 1
                for xval in np.arange(x_min,x_max, x_spacing):
                    # xval_offset = xval + (y_idx%2) * self.cell_radius
                    xval_offset = self.x0_value + xval + (y_idx%2) * self.cell_radius

                    xlist.append(xval_offset)
                    yval_offset = yval + self.y0_value
                    ylist.append(yval_offset)
                    # self.csv_array = np.append(self.csv_array,[[xval,yval,zval, cell_type_index]],axis=0)
                    self.csv_array = np.append(self.csv_array,[[xval_offset,yval_offset, zval, cell_type_index]],axis=0)
                    rlist.append(rval)
                    self.cell_radii.append(self.cell_radius)
                    count+=1

        self.numcells_l.append(count)

        xvals = np.array(xlist)
        yvals = np.array(ylist)
        rvals = np.array(rlist)
        # rgbas = np.array(rgba_list)

        if (self.cells_edge_checked_flag):
            try:
                self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
            except (ValueError):
                pass
        else:
            self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], alpha=self.alpha_value)

        self.ax0.set_aspect(1.0)

        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)

        # self.update_plots()
        self.canvas.update()
        self.canvas.draw()

    #----------------------------------
    def hex_pts_annulus(self):
        xlist = deque()
        ylist = deque()
        rlist = deque()
        rgba_list = deque()

        rval = self.cell_radius

        colors = np.empty((0,4))
        count = 0
        zval = 0.0
        cell_type_index = self.celltype_combobox.currentIndex()
        ncells = int(self.num_cells.text())
        # print("self.r1_value= ", self.r1_value)

        # x_min = -self.r1_value
        # x_max =  self.r1_value
        x_min = -self.r2_value
        x_max =  self.r2_value
        y_min = -self.r2_value
        y_max =  self.r2_value
        y_idx = -1
        # hex packing constants
        x_spacing = self.cell_radius * 2
        y_spacing = self.cell_radius * np.sqrt(3)

        cells_x = np.array([])
        cells_y = np.array([])

        cells_x2 = np.array([])
        cells_y2 = np.array([])

        # xctr = 0.0
        # yctr = 40.0
        xctr = 0.0
        yctr = 0.0
        #big_radius = 20.0

        y_idx = 0
        for yval in np.arange(y_min,y_max, y_spacing):
            y_idx += 1
            for xval in np.arange(x_min,x_max, x_spacing):
                xval_offset = xval + (y_idx%2) * self.cell_radius
                # xval_offset = self.x0_value + xval + (y_idx%2) * self.cell_radius

                # ixval = int(xval_offset)
                # print(ixval)
                # idx = np.where(x_values == ixval)
                xdist = xval_offset - xctr
                ydist = yval - yctr
                dist = np.sqrt(xdist*xdist + ydist*ydist)
                if (dist >= self.r1_value) and (dist <= self.r2_value):
                # # if (xval >= xvals[kdx]) and (xval <= xvals[kdx+1]):
                #     xv = xval_offset - big_radius
                #     cells_x = np.append(cells_x, xv)
                #     cells_y = np.append(cells_y, yval)
                #     print(xv,',',yval,',0.0, 2, 101')  # x,y,z, cell type, [sub]cell ID
                #     # plt.plot(xval_offset,yval,'ro',markersize=30)

                    xval_offset += self.x0_value
                    yval_offset = yval + self.y0_value

                    if xval_offset < self.plot_xmin or xval_offset > self.plot_xmax \
                        or yval_offset < self.plot_ymin or yval_offset > self.plot_ymax:
                        continue
                    else:
                        xlist.append(xval_offset)
                        ylist.append(yval_offset)
                        # self.csv_array = np.append(self.csv_array,[[xval_offset,yval,zval, cell_type_index]],axis=0)
                        self.csv_array = np.append(self.csv_array,[[xval_offset,yval_offset,zval, cell_type_index]],axis=0)
                        rlist.append(rval)
                        self.cell_radii.append(self.cell_radius)
                        count+=1

        self.numcells_l.append(count)

        xvals = np.array(xlist)
        yvals = np.array(ylist)
        rvals = np.array(rlist)
        # rgbas = np.array(rgba_list)

        if (self.cells_edge_checked_flag):
            try:
                self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
            except (ValueError):
                pass
        else:
            self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], alpha=self.alpha_value)

        self.ax0.set_aspect(1.0)

        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)

        # self.update_plots()
        self.canvas.update()
        self.canvas.draw()

    #----------------------------------
    def hex_pts_annulus_percentage(self):
        xlist = deque()
        ylist = deque()
        rlist = deque()
        rgba_list = deque()

        rval = self.cell_radius

        colors = np.empty((0,4))
        count = 0
        zval = 0.0
        cell_type_index = self.celltype_combobox.currentIndex()
        ncells = int(self.num_cells.text())
        # print("self.r1_value= ", self.r1_value)

        # x_min = -self.r1_value
        # x_max =  self.r1_value
        x_min = -self.r2_value
        x_max =  self.r2_value
        y_min = -self.r2_value
        y_max =  self.r2_value
        y_idx = -1
        # hex packing constants
        x_spacing = self.cell_radius * 2
        y_spacing = self.cell_radius * np.sqrt(3)

        cells_x = np.array([])
        cells_y = np.array([])

        cells_x2 = np.array([])
        cells_y2 = np.array([])

        # xctr = 0.0
        # yctr = 40.0
        xctr = 0.0
        yctr = 0.0
        #big_radius = 20.0

        y_idx = 0
        for yval in np.arange(y_min,y_max, y_spacing):
            y_idx += 1
            for xval in np.arange(x_min,x_max, x_spacing):
                xval_offset = xval + (y_idx%2) * self.cell_radius
                # xval_offset = self.x0_value + xval + (y_idx%2) * self.cell_radius

                # ixval = int(xval_offset)
                # print(ixval)
                # idx = np.where(x_values == ixval)
                xdist = xval_offset - xctr
                ydist = yval - yctr
                dist = np.sqrt(xdist*xdist + ydist*ydist)
                if (dist >= self.r1_value) and (dist <= self.r2_value):
                # # if (xval >= xvals[kdx]) and (xval <= xvals[kdx+1]):
                #     xv = xval_offset - big_radius
                #     cells_x = np.append(cells_x, xv)
                #     cells_y = np.append(cells_y, yval)
                #     print(xv,',',yval,',0.0, 2, 101')  # x,y,z, cell type, [sub]cell ID
                #     # plt.plot(xval_offset,yval,'ro',markersize=30)

                    xval_offset += self.x0_value
                    xlist.append(xval_offset)
                    yval_offset = yval + self.y0_value
                    ylist.append(yval_offset)
                    # self.csv_array = np.append(self.csv_array,[[xval_offset,yval,zval, cell_type_index]],axis=0)
                    self.csv_array = np.append(self.csv_array,[[xval_offset,yval_offset,zval, cell_type_index]],axis=0)
                    rlist.append(rval)
                    self.cell_radii.append(self.cell_radius)
                    count+=1

        self.numcells_l.append(count)

        xvals = np.array(xlist)
        yvals = np.array(ylist)
        rvals = np.array(rlist)
        # rgbas = np.array(rgba_list)

        if (self.cells_edge_checked_flag):
            try:
                self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
            except (ValueError):
                pass
        else:
            self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], alpha=self.alpha_value)

        self.ax0.set_aspect(1.0)

        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)

        # self.update_plots()
        self.canvas.update()
        self.canvas.draw()

    #----------------------------------
    def uniform_random_pts_box(self):
        xlist = deque()
        ylist = deque()
        zlist = deque()
        rlist = deque()
        rgba_list = deque()

        rval = self.cell_radius

        colors = np.empty((0,4))
        count = 0
        zval = 0.0
        cell_type_index = self.celltype_combobox.currentIndex()
        ncells = int(self.num_cells.text())
        self.numcells_l.append(ncells)
        # print("self.r1_value= ", self.r1_value)
        while True:
            sign = 1
            if np.random.uniform() > 0.5:
                sign = -1
            xval = self.x0_value + sign * np.random.uniform() * self.r1_value

            sign = 1
            if np.random.uniform() > 0.5:
                sign = -1
            yval = self.y0_value + sign * np.random.uniform() * self.r2_value

            sign = 1
            if np.random.uniform() > 0.5:
                sign = -1
            zval = self.z0_value + sign * np.random.uniform() * self.r3_value

            xlist.append(xval)
            ylist.append(yval)
            zlist.append(yval)
            self.csv_array = np.append(self.csv_array,[[xval,yval,zval, cell_type_index]],axis=0)
            rlist.append(rval)
            self.cell_radii.append(self.cell_radius)
            count+=1
            if count == ncells:
                break

        xvals = np.array(xlist)
        yvals = np.array(ylist)
        rvals = np.array(rlist)
        # rgbas = np.array(rgba_list)

        if (self.cells_edge_checked_flag):
            try:
                self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
            except (ValueError):
                pass
        else:
            self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], alpha=self.alpha_value)

        self.ax0.set_aspect(1.0)

        # self.plot_xmin = float(self.xmin)
        # self.plot_xmax = float(self.xmax)
        # self.plot_ymin = float(self.ymin)
        # self.plot_ymax = float(self.ymax)

        # self.plot_xmin = -500
        # self.plot_xmax = 500
        # self.plot_ymin = -500
        # self.plot_ymax = 500
        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)

        # self.update_plots()
        self.canvas.update()
        self.canvas.draw()

    #------------------------------------------------
    def uniform_random_pts_annulus(self):
        xlist = deque()
        ylist = deque()
        rlist = deque()
        rgba_list = deque()

        # V = 4/3 * pi * r^3
        # r = (V * 3/4 / pi) ** 0.3333

        rval = self.cell_radius
        # xyz = np.empty((0,3))
        colors = np.empty((0,4))
        # R1 = 300
        # R1_cbrt = np.cbrt(R1)
        # R2 = 400
        count = 0
        zval = 0.0
        cell_type_index = self.celltype_combobox.currentIndex()

        ncells = int(self.num_cells.text())
        self.numcells_l.append(ncells)

        # R1 = float(self.r1val.text())
        # R1 = self.r1_value
        R1 = self.r1_value - self.x0_value
        # print("R1=",R1)
        R1_sq = R1*R1
        # print("R1_sq=",R1_sq)
        # R2 = float(self.r2val.text())
        R2 = self.r2_value
        # print("R2=",R2)
        # k = 0
        while True:
            # k += 1
            t = 2.0 * np.pi * np.random.uniform()
            u = np.random.uniform() + np.random.uniform()
            if u > 1: 
                r = 2.0 - u 
            else: 
                r = u
            xval = self.x0_value + R2*r * np.cos(t)
            yval = self.y0_value + R2*r * np.sin(t)

            # print("xval,yval= ",xval,yval)
            xval2 = xval - self.x0_value
            yval2 = yval - self.y0_value
            d2 = np.sqrt(xval2*xval2 + yval2*yval2)
            # print(f'{k}) d2= {d2}, R1_sq={R1_sq}')
            # if k > 300:
                # break
            if d2 >= self.r1_value:
                xlist.append(xval)
                ylist.append(yval)
                rlist.append(rval)
                # print(count,xval,yval)
                self.csv_array = np.append(self.csv_array,[[xval,yval,zval, cell_type_index]],axis=0)
                self.cell_radii.append(self.cell_radius)
                count+=1
                if count == ncells:
                    break

        xvals = np.array(xlist)
        yvals = np.array(ylist)
        rvals = np.array(rlist)
        # rgbas = np.array(rgba_list)

        # print("idx, # celltypes=",cell_type_index , len(self.color_by_celltype[cell_type_index]))
        # if cell_type_index >= len(self.color_by_celltype[cell_type_index]):
        #     print("Error: exceeded # of colors. Grow it.")
        #     self.color_by_celltype.append('red')

        if (self.cells_edge_checked_flag):
            try:
                self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
            # except (ValueError):
            except:
                pass
        else:
            self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], alpha=self.alpha_value)

        self.ax0.set_aspect(1.0)

        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)

        # self.update_plots()
        self.canvas.update()
        self.canvas.draw()

    #----------------------------------
    def ring(self):
        xlist = deque()
        ylist = deque()
        rlist = deque()
        rgba_list = deque()


        colors = np.empty((0,4))
        count = 0
        zval = 0.0
        cell_type_index = self.celltype_combobox.currentIndex()
        # ncells = int(self.num_cells.text())
        # print("self.r1_value= ", self.r1_value)

        rval = self.cell_radius
        R = self.r2_value
        delta_theta = np.arcsin(rval / R)

        try:
            rmod = int(self.odelw.text())
        except:
            msg = "Invalid ring modulo value"
            print(msg)
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText(msg)
            msgBox.setStandardButtons(QMessageBox.Ok)
            returnValue = msgBox.exec()
            return
        print("ring(): rmod= ",rmod)

        cells_x = np.array([])
        cells_y = np.array([])

        xctr = 0.0
        yctr = 0.0

        y_idx = 0
        start_radians = self.o1_value * np.pi/180.
        end_radians = self.o2_value * np.pi/180.
        # delta_radians = self.o2_value * np.pi/180.

        # for theta in np.arange(0, max_radians, np.pi/10.):
        # for theta in np.arange(0, max_radians, delta_theta * np.pi/180):
        # for theta in np.arange(start_radians, end_radians, delta_theta):
        for theta in np.arange(start_radians, end_radians, rmod*2*delta_theta):
            # print("theta= ",theta)
            xval = self.x0_value + R * np.cos(theta)
            yval = self.y0_value + R * np.sin(theta)

            if xval < self.plot_xmin or xval > self.plot_xmax \
                or yval < self.plot_ymin or yval > self.plot_ymax:
                continue
            else:
                xlist.append(xval)
                ylist.append(yval)
                # self.csv_array = np.append(self.csv_array,[[xval_offset,yval,zval, cell_type_index]],axis=0)
                self.csv_array = np.append(self.csv_array,[[xval,yval,zval, cell_type_index]],axis=0)
                rlist.append(rval)
                self.cell_radii.append(self.cell_radius)
                count+=1

        self.numcells_l.append(count)

        xvals = np.array(xlist)
        yvals = np.array(ylist)
        rvals = np.array(rlist)
        # rgbas = np.array(rgba_list)

        if (self.cells_edge_checked_flag):
            try:
                self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
            except (ValueError):
                pass
        else:
            self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], alpha=self.alpha_value)

        self.ax0.set_aspect(1.0)

        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)

        # self.update_plots()
        self.canvas.update()
        self.canvas.draw()

    #------------------------------------------------
    def clear_cb(self):
        # self.ax0.clear()
        # update range with whatever is in config_tab
        self.reset_plot_range()

        self.ax0.cla()
        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)
        self.canvas.update()
        self.canvas.draw()

        self.csv_array = np.empty([1,4])  # should probably *just* np.delete, but meh
        self.csv_array = np.delete(self.csv_array,0,0)
        self.cell_radii = []

    def save_cb(self):
        if len(self.csv_array) == 0:
            msg = "No cells created. You must Plot first."
            print(msg)
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText(msg)
            msgBox.setStandardButtons(QMessageBox.Ok)
            returnValue = msgBox.exec()
            return

        # print("\n------- ics_tab.py: save_cb() -------")
        # x = y = z = np.arange(0.0,5.0,1.0)
        # np.savetxt('cells.csv', (x,y,z), delimiter=',')
        # print(self.csv_array)
        dir_name = self.csv_folder.text()
        # print(f'dir_name={dir_name}<end>')
        if len(dir_name) > 0 and not os.path.isdir(dir_name):
            os.makedirs(dir_name)
            time.sleep(1)
        full_fname = os.path.join(dir_name,self.output_file.text())
        print("save_cb(): full_fname=",full_fname)

        # if self.nanohub_flag and os.path.isdir('tmpdir'):
        #     # something on NFS causing issues...
        #     tname = tempfile.mkdtemp(suffix='.bak', prefix='tmpdir_', dir='.')
        #     shutil.move('tmpdir', tname)
        # if self.nanohub_flag:
        #     os.makedirs('tmpdir')

        # if not os.path.isfile(full_fname):
        #     msg = "Invalid filename: " + full_fname
        #     print(msg)
        #     msgBox = QMessageBox()
        #     msgBox.setIcon(QMessageBox.Information)
        #     msgBox.setText(msg)
        #     msgBox.setStandardButtons(QMessageBox.Ok)
        #     returnValue = msgBox.exec()
        # else:
            # np.savetxt('cells.csv', self.csv_array, delimiter=',')


        # Recall: self.csv_array = np.empty([1,4])  # default floats
        if self.use_names.isChecked():
            print("----- Writing v2 (with cell names) .csv file for cells")
            print("----- full_fname=",full_fname)
            # print("self.csv_array.shape= ",self.csv_array.shape)
            # print(self.csv_array)
            cell_name = list(self.celldef_tab.param_d.keys())
            # print("cell_name=",cell_name)
            with open(full_fname, 'w') as f:
                f.write('x,y,z,type,volume,cycle entry,custom:GFP,custom:sample\n')  # PhysiCell checks for "x" or "X"
                for idx in range(len(self.csv_array)):
                    ict = int(self.csv_array[idx,3])  # cell type index
                    f.write(f'{self.csv_array[idx,0]},{self.csv_array[idx,1]},{self.csv_array[idx,2]},{cell_name[ict]}\n')
        else:
            print("----- Writing v1 (with cell indices) .csv file for cells")
            print("----- full_fname=",full_fname)
            np.savetxt(full_fname, self.csv_array, delimiter=',')

    #--------------------------------------------------
    def import_cb(self):
        # filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')
        filePath = QFileDialog.getOpenFileName(self,'',".")
        full_path_rules_name = filePath[0]

        self.import_from_file(full_path_rules_name)

    def import_from_file(self, full_path_rules_name):
        # logging.debug(f'\nimport_cb():  full_path_rules_name ={full_path_rules_name}')
        print(f'\nimport_cb():  full_path_rules_name ={full_path_rules_name}')
        basename = os.path.basename(full_path_rules_name)
        print(f'import_cb():  basename ={basename}')
        dirname = os.path.dirname(full_path_rules_name)
        print(f'import_cb():  dirname ={dirname}')
        # if (len(full_path_rules_name) > 0) and Path(full_path_rules_name):
        if (len(full_path_rules_name) > 0) and Path(full_path_rules_name).is_file():
            print("import_from_file(full_path_rules_name):  filePath is valid")
            # logging.debug(f'     filePath is valid')
            print("len(full_path_rules_name) = ", len(full_path_rules_name) )

            cell_types_l = [self.celltype_combobox.itemText(i) for i in range(self.celltype_combobox.count())]
            print(cell_types_l)

            xlist = deque()
            ylist = deque()
            rlist = deque()
            rgba_list = deque()

            rval = self.cell_radius

            colors = np.empty((0,4))
            count = 0
            # zval = 0.0
            # cell_type_index = self.celltype_combobox.currentIndex()
            # cell_type_name = self.celltype_combobox.currentText()

            # x,y,z,type,volume,cycle entry,custom:GFP,custom:sample
            # -49.52373671227464,-85.42875790157267,0.0,acell
            zval = 0.0   # only doing 2D now
            with open(full_path_rules_name, newline='') as csvfile:
                states_reader = csv.reader(csvfile, delimiter=',')
                count = 0
                for row in states_reader:
                    # print(count,row)
                    if count == 0:
                        # print("skipping header row")
                        # print("row[0]=",row[0])
                        if row[0] != 'x':
                            msgBox = QMessageBox()
                            msgBox.setIcon(QMessageBox.Information)
                            msgBox.setText("Invalid first row. Expecting 'x' in 1st column.")
                            msgBox.setStandardButtons(QMessageBox.Ok)
                            returnValue = msgBox.exec()
                            return
                        # count+=1
                    else:
                        xval = float(row[0])
                        yval = float(row[1])
                        # zval = float(row[2])
                        cell_type_name = row[3]
                        try:
                            cell_type_index = cell_types_l.index(cell_type_name)
                        except:
                            msgBox = QMessageBox()
                            msgBox.setIcon(QMessageBox.Information)
                            msgBox.setText(f"Invalid cell type name: {cell_type_name}")
                            msgBox.setStandardButtons(QMessageBox.Ok)
                            returnValue = msgBox.exec()
                            return

                        # print('xval,yval=',xval,yval)
                        # volume = float(self.celldef_tab.param_d[cdef]["volume_total"])
                        # volume = float(self.celldef_tab.param_d[cell_type_name]["volume_total"])
                        # rval = (volume * 0.75 / np.pi) ** (1./3)
                        rval = self.cell_radius

                        self.csv_array = np.append(self.csv_array,[[xval,yval, zval, cell_type_index]],axis=0)
                        # rlist.append(rval)
                        self.cell_radii.append(rval)
                        # count+=1

                        if (self.cells_edge_checked_flag):
                            try:
                                # print(f"calling self.circles with {xval}, {yval}")
                                self.circles(xval,yval, s=rval, color=self.color_by_celltype[cell_type_index], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
                            except (ValueError):
                                print("Exception:  self.circles")
                                pass
                        else:
                            self.circles(xval,yval, s=rval, color=self.color_by_celltype[cell_type_index], alpha=self.alpha_value)

                        self.numcells_l.append(1)

                    count+=1
                    # self.numcells_l.append(count)

            self.ax0.set_aspect(1.0)

            self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
            self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)

            self.canvas.update()
            self.canvas.draw()

        else:
            print("import_cb():  full_path_model_name is NOT valid")

    def fill_gui(self):
        self.csv_folder.setText(self.config_tab.csv_folder.text())
        self.output_file.setText(self.config_tab.csv_file.text())
        if self.bioinf_import_flag:
            self.bioinf_import_tab.fill_gui()

    def on_enter_axes(self, event):
        self.mouse_on_axes = True
        current_location = self.getPos(event)
        self.ax0.set_title(f"(x,y) = ({round(current_location[0])}, {round(current_location[1])})")
        self.canvas.update()
        self.canvas.draw()

    def on_leave_axes(self, event):
        self.mouse_on_axes = False
        self.ax0.set_title("")
        self.canvas.update()
        self.canvas.draw()

    def mouseMoved(self, event):
        if self.mouse_on_axes is False:
            return
        current_location = self.getPos(event)
        self.ax0.set_title(f"(x,y) = ({round(current_location[0])}, {round(current_location[1])})")
        self.canvas.update()
        self.canvas.draw()

