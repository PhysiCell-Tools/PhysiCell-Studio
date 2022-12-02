"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)

"""

import sys
import os
import logging
import time
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from pathlib import Path
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle, Ellipse, Rectangle
from matplotlib.collections import PatchCollection
import matplotlib.colors as mplc
from matplotlib import gridspec
from collections import deque
import glob

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,  QMainWindow,QGridLayout, QPushButton, QFileDialog, QMessageBox, QStackedWidget

import numpy as np
import scipy.io
from pyMCDS_cells import pyMCDS_cells 
# from pyMCDS_rwh import pyMCDS
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

# from PyQt5 import QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
# from matplotlib.figure import Figure

class Vis(QWidget):

    def __init__(self, nanohub_flag):
        super().__init__()
        # global self.config_params

        self.circle_radius = 100  # will be set in run_tab.py using the .xml
        self.mech_voxel_size = 30 # kinda weird this is essentially hard-coded in PhysiCell

        self.voxel_dx = 20 # updated based on Config params of domain
        self.voxel_dy = 20 

        self.nanohub_flag = nanohub_flag
        self.config_tab = None

        self.bgcolor = [1,1,1,1]  # all 1.0 for white 

        self.animating_flag = False

        self.xml_root = None
        self.current_svg_frame = 0
        self.timer = QtCore.QTimer()
        # self.t.timeout.connect(self.task)
        self.timer.timeout.connect(self.play_plot_cb)

        # self.tab = QWidget()
        # self.tabs.resize(200,5)
        
        self.num_contours = 50
        self.shading_choice = 'auto'  # 'auto'(was 'flat') vs. 'gouraud' (smooth)

        self.fontsize = 9
        self.title_fontsize = 10

        self.plot_svg_flag = True
        # self.plot_svg_flag = False
        self.field_index = 4  # substrate (0th -> 4 in the .mat)

        self.use_defaults = True
        self.title_str = ""

        self.show_plot_range = False

        # self.config_file = "mymodel.xml"
        self.reset_model_flag = True
        self.xmin = -80
        self.xmax = 80
        self.xdel = 20
        self.x_range = self.xmax - self.xmin

        self.ymin = -50
        self.ymax = 100
        self.ydel = 20
        self.y_range = self.ymax - self.ymin

        self.aspect_ratio = 0.7

        self.show_voxel_grid = False
        self.show_mech_grid = False
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


        # self.output_dir = "/Users/heiland/dev/PhysiCell_V.1.8.0_release/output"
        # self.output_dir = "output"
        # self.output_dir = "../tmpdir"   # for nanoHUB
        # self.output_dir = "tmpdir"   # for nanoHUB
        self.output_dir = "."   # for nanoHUB


        # do in create_figure()?
        # xlist = np.linspace(-3.0, 3.0, 50)
        # print("len(xlist)=",len(xlist))
        # ylist = np.linspace(-3.0, 3.0, 50)
        # X, Y = np.meshgrid(xlist, ylist)
        # Z = np.sqrt(X**2 + Y**2) + 10*np.random.rand()
        # self.cmap = plt.cm.get_cmap("viridis")
        # self.cs = self.ax0.contourf(X, Y, Z, cmap=self.cmap)
        # self.cbar = self.figure.colorbar(self.cs, ax=self.ax)


        #-------------------------------------------
        label_width = 110
        value_width = 60
        label_height = 20
        units_width = 70

        # self.substrates_combobox = QComboBox(self)
        self.substrates_combobox = QComboBox()
        self.substrates_combobox.setEnabled(False)
        self.field_dict = {}
        self.field_min_max = {}
        self.cmin_value = 0.0
        self.cmax_value = 1.0
        self.fixed_contour_levels = MaxNLocator(nbins=self.num_contours).tick_values(self.cmin_value, self.cmax_value)

        self.myscroll = QScrollArea()  # might contain centralWidget
        self.create_figure()

        self.config_params = QWidget()

        # self.main_layout = QVBoxLayout()

        self.vbox = QVBoxLayout()
        self.vbox.addStretch(0)

        self.stackw = QStackedWidget()
        # self.stackw.setCurrentIndex(0)

        #------------------
        # controls_hbox = QHBoxLayout()
        # w = QPushButton("Directory")
        # w.clicked.connect(self.open_directory_cb)
        # # if self.nanohub_flag:
        # if self.nanohub_flag:
        #     w.setEnabled(False)  # for nanoHUB
        # controls_hbox.addWidget(w)

        # # self.output_dir = "/Users/heiland/dev/PhysiCell_V.1.8.0_release/output"
        # self.output_dir_w = QLineEdit()
        # self.output_dir_w.setFixedWidth(domain_value_width)
        # # w.setText("/Users/heiland/dev/PhysiCell_V.1.8.0_release/output")
        # self.output_dir_w.setText(self.output_dir)
        # if self.nanohub_flag:
        #     self.output_dir_w.setEnabled(False)  # for nanoHUB
        # # w.textChanged[str].connect(self.output_dir_changed)
        # # w.textChanged.connect(self.output_dir_changed)
        # controls_hbox.addWidget(self.output_dir_w)

        self.controls1 = QWidget()
        self.glayout1 = QGridLayout()
        self.controls1.setLayout(self.glayout1)

        arrow_button_width = 50
        self.first_button = QPushButton("|<")
        self.first_button.setFixedWidth(arrow_button_width)
        self.first_button.clicked.connect(self.first_plot_cb)
        # controls_hbox.addWidget(self.first_button)
        icol = 0
        irow = 0
        self.glayout1.addWidget(self.first_button, irow,icol,1,1) # w, row, column, rowspan, colspan

        self.back_button = QPushButton("<")
        self.back_button.setFixedWidth(arrow_button_width)
        self.back_button.clicked.connect(self.back_plot_cb)
        # controls_hbox.addWidget(self.back_button)
        icol += 1
        self.glayout1.addWidget(self.back_button, irow,icol,1,1) # w, row, column, rowspan, colspan

        frame_count_width = 40
        self.frame_count = QLineEdit()
        # self.frame_count.textChanged.connect(self.change_frame_count_cb)  # do later to appease the callback gods
        self.frame_count.setFixedWidth(frame_count_width)
        self.frame_count.setValidator(QtGui.QIntValidator(0,10000000))
        self.frame_count.setText('0')
        icol += 1
        self.glayout1.addWidget(self.frame_count, irow,icol,1,1) # w, row, column, rowspan, colspan


        self.forward_button = QPushButton(">")
        self.forward_button.setFixedWidth(arrow_button_width)
        self.forward_button.clicked.connect(self.forward_plot_cb)
        # controls_hbox.addWidget(self.forward_button)
        icol += 1
        self.glayout1.addWidget(self.forward_button, irow,icol,1,1) # w, row, column, rowspan, colspan

        self.last_button = QPushButton(">|")
        self.last_button.setFixedWidth(arrow_button_width)
        self.last_button.clicked.connect(self.last_plot_cb)
        # controls_hbox.addWidget(self.last_button)
        icol += 1
        self.glayout1.addWidget(self.last_button, irow,icol,1,1) # w, row, column, rowspan, colspan

        self.play_button = QPushButton("Play")
        self.play_button.setFixedWidth(70)
        self.play_button.setStyleSheet("background-color : lightgreen")
        # self.play_button.clicked.connect(self.play_plot_cb)
        self.play_button.clicked.connect(self.animate)
        # controls_hbox.addWidget(self.play_button)
        icol += 1
        self.glayout1.addWidget(self.play_button, irow,icol,1,1) # w, row, column, rowspan, colspan

        # self.prepare_button = QPushButton("Prepare")
        # self.prepare_button.clicked.connect(self.prepare_plot_cb)
        # controls_hbox.addWidget(self.prepare_button)

        self.cells_checkbox = QCheckBox('Cells')
        self.cells_checkbox.setChecked(True)
        self.cells_checkbox.clicked.connect(self.cells_toggle_cb)
        self.cells_checked_flag = True
        # self.glayout1.addWidget(self.cells_checkbox, 0,5,1,2) # w, row, column, rowspan, colspan
        icol += 1
        self.glayout1.addWidget(self.cells_checkbox, irow,icol,1,1) # w, row, column, rowspan, colspan

        self.cells_edge_checkbox = QCheckBox('edge')
        self.cells_edge_checkbox.setChecked(True)
        self.cells_edge_checkbox.clicked.connect(self.cells_edge_toggle_cb)
        self.cells_edge_checked_flag = True
        icol += 1
        self.glayout1.addWidget(self.cells_edge_checkbox, irow,icol,1,1) # w, row, column, rowspan, colspan

        self.cells_nucleus_checkbox = QCheckBox('nuclei')
        self.cells_nucleus_checkbox.setChecked(self.show_nucleus)
        self.cells_nucleus_checkbox.clicked.connect(self.cells_nucleus_toggle_cb)
        icol += 1
        self.glayout1.addWidget(self.cells_nucleus_checkbox, irow,icol,1,1) # w, row, column, rowspan, colspan

        self.substrates_checkbox = QCheckBox('Substrates')
        self.substrates_checkbox.setChecked(False)
        # self.substrates_checkbox.setEnabled(False)
        self.substrates_checkbox.clicked.connect(self.substrates_toggle_cb)
        self.substrates_checked_flag = False
        icol += 1
        self.glayout1.addWidget(self.substrates_checkbox, irow,icol,1,2) # w, row, column, rowspan, colspan

        self.fix_cmap_checkbox = QCheckBox('fix')
        self.fix_cmap_flag = False
        self.fix_cmap_checkbox.setEnabled(False)
        self.fix_cmap_checkbox.setChecked(self.fix_cmap_flag)
        self.fix_cmap_checkbox.clicked.connect(self.fix_cmap_toggle_cb)
        icol += 2
        self.glayout1.addWidget(self.fix_cmap_checkbox, irow,icol,1,1) # w, row, column, rowspan, colspan

        cvalue_width = 70
        label = QLabel("cmin")
        # label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.cmin = QLineEdit()
        self.cmin.setEnabled(False)
        self.cmin.setText('0.0')
        # self.cmin.textChanged.connect(self.change_plot_range)
        self.cmin.returnPressed.connect(self.cmin_cmax_cb)
        self.cmin.setFixedWidth(cvalue_width)
        self.cmin.setValidator(QtGui.QDoubleValidator())
        self.cmin.setEnabled(False)
        icol += 1
        self.glayout1.addWidget(label, irow,icol,1,1) # w, row, column, rowspan, colspan
        icol += 1
        self.glayout1.addWidget(self.cmin, irow,icol,1,1) # w, row, column, rowspan, colspan

        label = QLabel("cmax")
        # label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.cmax = QLineEdit()
        self.cmin.setEnabled(False)
        self.cmax.setText('1.0')
        self.cmax.returnPressed.connect(self.cmin_cmax_cb)
        self.cmax.setFixedWidth(cvalue_width)
        self.cmax.setValidator(QtGui.QDoubleValidator())
        self.cmax.setEnabled(False)
        icol += 1
        self.glayout1.addWidget(label, irow,icol,1,1) # w, row, column, rowspan, colspan
        icol += 1
        self.glayout1.addWidget(self.cmax, irow,icol,1,1) # w, row, column, rowspan, colspan

        icol += 1
        self.glayout1.addWidget(self.substrates_combobox, irow,icol,1,2) # w, row, column, rowspan, colspan
        
        #-----------
        self.frame_count.textChanged.connect(self.change_frame_count_cb)


        #-----------
        self.output_dir_name = QLineEdit()
        # self.frame_count.textChanged.connect(self.change_frame_count_cb)  # do later to appease the callback gods
        # self.output_dir_name.setFixedWidth(frame_count_width)
        self.output_dir_name.setText('')
        irow += 1
        icol = 0
        self.glayout1.addWidget(self.output_dir_name, irow,icol,1,10) # w, row, column, rowspan, colspan

        # self.controls1.setGeometry(QRect(20, 40, 601, 501))
        # self.controls1.resize(500,30)
        # self.stackw.addWidget(self.controls1)  # rwh: crap, just doing this causes it to disappear, even though we never add the stackw below!

        # hbox = QHBoxLayout()
        # hbox.addWidget(self.cells_checkbox)
        # hbox.addWidget(self.substrates_checkbox)
        # controls_hbox.addLayout(hbox)

        #-------------------
        self.controls2 = QWidget()
        self.glayout2 = QGridLayout()
        self.controls2.setLayout(self.glayout2)
        # controls_hbox2 = QHBoxLayout()
        visible_flag = True

        label = QLabel("xmin")
        label.setFixedWidth(label_width)
        # label.setAlignment(QtCore.Qt.AlignRight)
        label.setAlignment(QtCore.Qt.AlignCenter)
        # controls_hbox2.addWidget(label)


        domain_value_width = 60
        self.my_xmin = QLineEdit()
        self.my_xmin.textChanged.connect(self.change_plot_range)
        self.my_xmin.setFixedWidth(domain_value_width)
        self.my_xmin.setValidator(QtGui.QDoubleValidator())
        # controls_hbox2.addWidget(self.my_xmin)
        self.my_xmin.setVisible(visible_flag)
        # controls_hbox2.addWidget(label)
        self.glayout2.addWidget(label, 0,0,1,1) # w, row, column, rowspan, colspan
        self.glayout2.addWidget(self.my_xmin, 0,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel("xmax")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        # controls_hbox2.addWidget(label)
        self.my_xmax = QLineEdit()
        self.my_xmax.textChanged.connect(self.change_plot_range)
        self.my_xmax.setFixedWidth(domain_value_width)
        self.my_xmax.setValidator(QtGui.QDoubleValidator())
        # controls_hbox2.addWidget(self.my_xmax)
        self.my_xmax.setVisible(visible_flag)
        self.glayout2.addWidget(label, 0,2,1,1) # w, row, column, rowspan, colspan
        self.glayout2.addWidget(self.my_xmax, 0,3,1,1) # w, row, column, rowspan, colspan

        label = QLabel("ymin")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        # controls_hbox2.addWidget(label)
        self.my_ymin = QLineEdit()
        self.my_ymin.textChanged.connect(self.change_plot_range)
        self.my_ymin.setFixedWidth(domain_value_width)
        self.my_ymin.setValidator(QtGui.QDoubleValidator())
        # controls_hbox2.addWidget(self.my_ymin)
        self.my_ymin.setVisible(visible_flag)
        self.glayout2.addWidget(label, 0,4,1,1) # w, row, column, rowspan, colspan
        self.glayout2.addWidget(self.my_ymin, 0,5,1,1) # w, row, column, rowspan, colspan

        label = QLabel("ymax")
        label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        # controls_hbox2.addWidget(label)
        self.my_ymax = QLineEdit()
        self.my_ymax.textChanged.connect(self.change_plot_range)
        self.my_ymax.setFixedWidth(domain_value_width)
        self.my_ymax.setValidator(QtGui.QDoubleValidator())
        # controls_hbox2.addWidget(self.my_ymax)
        self.my_ymax.setVisible(visible_flag)
        self.glayout2.addWidget(label, 0,6,1,1) # w, row, column, rowspan, colspan
        self.glayout2.addWidget(self.my_ymax, 0,7,1,1) # w, row, column, rowspan, colspan

        w = QPushButton("Reset")
        w.clicked.connect(self.reset_plot_range)
        self.glayout2.addWidget(w, 0,8,1,1) # w, row, column, rowspan, colspan
        # controls_hbox2.addWidget(w)

        self.my_xmin.setText(str(self.xmin))
        self.my_xmax.setText(str(self.xmax))
        self.my_ymin.setText(str(self.ymin))
        self.my_ymax.setText(str(self.ymax))

        #-------------------
        # arg, Qt layouts drive me insane. This doesn't work - trying to combine both rows of controls!
        # self.controls3 = QWidget()
        # self.controls3_layout = QVBoxLayout()
        # # self.controls3_layout = QGridLayout()
        # # doing this shows nothing!
        # # self.controls3_layout.addLayout(self.glayout2)
        # # self.controls3_layout.addLayout(self.glayout1)
        # # self.controls3_layout.addWidget(self.controls1, 0,0,1,8) # w, row, column, rowspan, colspan
        # # self.controls3_layout.addWidget(self.controls2, 1,0,1,8) # w, row, column, rowspan, colspan

        # # doing this shows only the controls2!
        # self.controls3_layout.addWidget(self.controls2, alignment=QtCore.Qt.AlignCenter) 
        # self.controls3_layout.addWidget(self.controls1, alignment=QtCore.Qt.AlignCenter)

        # self.controls3.setLayout(self.controls3_layout)

        #-------------------
        self.substrates_combobox.currentIndexChanged.connect(self.substrates_combobox_changed_cb)

        # controls_vbox = QVBoxLayout()
        # controls_vbox.addLayout(controls_hbox)
        # controls_vbox.addLayout(controls_hbox2)

        #==================================================================
        self.config_params.setLayout(self.vbox)

        self.myscroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.myscroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.myscroll.setWidgetResizable(True)

        # self.myscroll.setWidget(self.config_params) # self.config_params = QWidget()
        self.myscroll.setWidget(self.canvas) # self.config_params = QWidget()
        self.layout = QVBoxLayout(self)
        # self.layout.addLayout(controls_hbox)
        # self.layout.addLayout(controls_hbox2)
        # self.layout.addLayout(controls_vbox)
        # self.layout.addLayout(self.glayout)

        # self.layout.addWidget(self.controls1)

        self.stackw.addWidget(self.controls1)
        # self.stackw.addWidget(self.controls2)
        # self.stackw.addWidget(self.controls3)

        self.stackw.setCurrentIndex(0)
        # self.stackw.setFixedHeight(40)  # if we don't specify a fixed height, these controls take up ~50% of window
        self.stackw.setFixedHeight(80)  # if we don't specify a fixed height, these controls take up ~50% of window
        # self.stackw.setFixedHeight(35)  # weird effects
        # self.stackw.resize(700,100)
        self.layout.addWidget(self.stackw)
        self.show_plot_range = False
        # if self.show_plot_range:
        #     self.layout.addWidget(self.controls2)
        # self.layout.addWidget(self.my_xmin)
        self.layout.addWidget(self.myscroll)
        # self.layout.addStretch()

        # self.create_figure()


    def update_output_dir(self, dir_path):
        if os.path.isdir(dir_path):
            print("update_output_dir(): yes, it is a dir path", dir_path)
        else:
            print("update_output_dir(): NO, it is NOT a dir path", dir_path)
        self.output_dir = dir_path
        self.output_dir_name.setText(dir_path)

    def reset_plot_range(self):
        try:  # due to the initial callback
            self.my_xmin.setText(str(self.xmin))
            self.my_xmax.setText(str(self.xmax))
            self.my_ymin.setText(str(self.ymin))
            self.my_ymax.setText(str(self.ymax))

            self.plot_xmin = float(self.xmin)
            self.plot_xmax = float(self.xmax)
            self.plot_ymin = float(self.ymin)
            self.plot_ymax = float(self.ymax)
            logging.debug(f'------ reset_plot_range(): plot_ymin,ymax=  {self.plot_ymin},{self.plot_ymax}')
        except:
            pass

        self.update_plots()


    def show_hide_plot_range(self):
        # print("vis_tab: show_hide_plot_range()")
        logging.debug(f'show_hide_plot_range(): self.stackw.count()= {self.stackw.count()}')
        # print('self.show_plot_range= ',self.show_plot_range)
        # print(" # items = ",self.layout.num_items())
        # item = self.layout.itemAt(1)
        # print('item= ',item)

        self.show_plot_range = not self.show_plot_range
        # print('self.show_plot_range= ',self.show_plot_range)
        if self.show_plot_range:
            # self.glayout2.addWidget(self.controls2)
            # self.layout.addWidget(self.controls2)
            # self.controls2.setVisible(True)
            self.stackw.setCurrentIndex(1)
            # self.stackw.setFixedHeight(80)
        else:
            self.stackw.setCurrentIndex(0)
            # self.stackw.setFixedHeight(40)
            # self.glayout2.removeWidget(self.controls2)
            # self.controls2.setVisible(False)
            # self.layout.removeWidget(self.controls2)
            # self.self.controls2.deleteLater()
            # self.controls2.deleteLater()
            # if item != None :
            #     widget = item.widget()
            #     print('widget= ',widget)
            #     if widget != None:
            #         self.layout.removeWidget(widget)
            #         widget.deleteLater()

    def change_frame_count_cb(self):
        try:  # due to the initial callback
            self.current_svg_frame = int(self.frame_count.text())
        except:
            pass
        self.update_plots()

    def cmin_cmax_cb(self):
        # print("----- cmin_cmax_cb:")
        try:  # due to the initial callback
            self.cmin_value = float(self.cmin.text())
            self.cmax_value = float(self.cmax.text())
            self.fixed_contour_levels = MaxNLocator(nbins=self.num_contours).tick_values(self.cmin_value, self.cmax_value)
        except:
            pass
        self.update_plots()

    def init_plot_range(self, config_tab):
        # print("----- init_plot_range:")
        try:
            # beware of widget callback 
            self.my_xmin.setText(config_tab.xmin.text())
            self.my_xmax.setText(config_tab.xmax.text())
            self.my_ymin.setText(config_tab.ymin.text())
            self.my_ymax.setText(config_tab.ymax.text())
            self.my_dx.setText(config_tab.xdel.text())
            self.my_dy.setText(config_tab.ydel.text())
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
        except:
            pass

        self.update_plots()

    def update_plots(self):
        self.ax0.cla()
        if self.substrates_checked_flag:  # do first so cells are plotted on top
            self.plot_substrate(self.current_svg_frame)
        if self.cells_checked_flag:
            self.plot_svg(self.current_svg_frame)

        if self.show_voxel_grid:
            self.plot_voxel_grid()
        if self.show_mech_grid:
            self.plot_mechanics_grid()
        # if self.show_vectors:
            # self.plot_vecs()

        self.frame_count.setText(str(self.current_svg_frame))

        self.canvas.update()
        self.canvas.draw()

    def fill_substrates_combobox(self, substrate_list):
        # print("vis_tab.py: ------- fill_substrates_combobox")
        # print("substrate_list = ",substrate_list )
        self.substrates_combobox.clear()
        idx = 0
        for s in substrate_list:
            # print(" --> ",s)
            self.substrates_combobox.addItem(s)
            self.field_dict[idx] = s   # e.g., self.field_dict = {0:'director signal', 1:'cargo signal'}
            self.field_min_max[s]= [0,1,False]
            # self.field_min_max[s][1] = 1
            # self.field_min_max[s][2] = False
            idx += 1
        # print('field_dict= ',self.field_dict)
        # print('field_min_max= ',self.field_min_max)
        # self.substrates_combobox.setCurrentIndex(2)  # not working; gets reset to oxygen somehow after a Run

    def substrates_combobox_changed_cb(self,idx):
        # print("----- vis_tab.py: substrates_combobox_changed_cb: idx = ",idx)
        self.field_index = 4 + idx # substrate (0th -> 4 in the .mat)
        self.update_plots()


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

    def reset_model(self):
        # print("\n--------- vis_tab: reset_model ----------")
        # Verify initial.xml and at least one .svg file exist. Obtain bounds from initial.xml
        # tree = ET.parse(self.output_dir + "/" + "initial.xml")
        xml_file = Path(self.output_dir, "initial.xml")
        if not os.path.isfile(xml_file):
            logging.debug(f'vis_tab:reset_model(): Warning: Expecting initial.xml, but does not exist.')
            # msgBox = QMessageBox()
            # msgBox.setIcon(QMessageBox.Information)
            # msgBox.setText("Did not find 'initial.xml' in the output directory. Will plot a dummy substrate until you run a simulation.")
            # msgBox.setStandardButtons(QMessageBox.Ok)
            # msgBox.exec()
            return

        tree = ET.parse(Path(self.output_dir, "initial.xml"))
        xml_root = tree.getroot()

        bds_str = xml_root.find(".//microenvironment//domain//mesh//bounding_box").text
        bds = bds_str.split()
        # print('bds=',bds)
        self.xmin = float(bds[0])
        self.xmax = float(bds[3])
        # self.xdel = 
        logging.debug(f'vis_tab.py: reset_model(): self.xmin, xmax= {self.xmin}, {self.xmax}')
        self.x_range = self.xmax - self.xmin
        self.plot_xmin = self.xmin
        self.plot_xmax = self.xmax
        # print("--------- self.plot_xmax = ",self.plot_xmax)

        try:
            self.my_xmin.setText(str(self.plot_xmin))
            self.my_xmax.setText(str(self.plot_xmax))
            self.my_ymin.setText(str(self.plot_ymin))
            self.my_ymax.setText(str(self.plot_ymax))
        except:
            pass

        self.ymin = float(bds[1])
        self.ymax = float(bds[4])
        # self.ydel = 
        self.y_range = self.ymax - self.ymin
        # print('reset_model(): self.ymin, ymax=',self.ymin, self.ymax)
        self.plot_ymin = self.ymin
        self.plot_ymax = self.ymax

        xcoords_str = xml_root.find(".//microenvironment//domain//mesh//x_coordinates").text
        xcoords = xcoords_str.split()
        # print('reset_model(): xcoords=',xcoords)
        # print('reset_model(): len(xcoords)=',len(xcoords))
        self.numx =  len(xcoords)

        ycoords_str = xml_root.find(".//microenvironment//domain//mesh//y_coordinates").text
        ycoords = ycoords_str.split()
        # print('reset_model(): ycoords=',ycoords)
        # print('reset_model(): len(ycoords)=',len(ycoords))
        self.numy =  len(ycoords)
        # print("-------------- vis_tab.py: reset_model() -------------------")
        # print("reset_model(): self.numx, numy = ",self.numx,self.numy)

        #-------------------
        vars_uep = xml_root.find(".//microenvironment//domain//variables")
        if vars_uep:
            sub_names = []
            for var in vars_uep:
            # self.substrate.clear()
            # self.param[substrate_name] = {}  # a dict of dicts

            # self.tree.clear()
                idx = 0
            # <microenvironment_setup>
		    #   <variable name="food" units="dimensionless" ID="0">
                # print(cell_def.attrib['name'])
                if var.tag == 'variable':
                    substrate_name = var.attrib['name']
                    # print("substrate: ",substrate_name )
                    sub_names.append(substrate_name)
                self.substrates_combobox.clear()
                # print("sub_names = ",sub_names)
                self.substrates_combobox.addItems(sub_names)

        self.cmin_value = 0.0
        self.cmax_value = 1.0

        # and plot 1st frame (.svg)
        self.current_svg_frame = 0
        # self.forward_plot_cb("")  

        self.fill_substrates_combobox(sub_names)


    def reset_axes(self):
        # print("--------- vis_tab: reset_axes ----------")
        # Verify initial.xml and at least one .svg file exist. Obtain bounds from initial.xml
        # tree = ET.parse(self.output_dir + "/" + "initial.xml")
        xml_file = Path(self.output_dir, "initial.xml")
        if not os.path.isfile(xml_file):
            print("vis_tab.py: reset_axes(): Expecting initial.xml, but does not exist.")
            logging.debug(f'vis_tab.py: reset_axes(): Expecting initial.xml, but does not exist.')
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Did not find 'initial.xml' in this directory.")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return

        tree = ET.parse(Path(self.output_dir, "initial.xml"))
        xml_root = tree.getroot()

        bds_str = xml_root.find(".//microenvironment//domain//mesh//bounding_box").text
        bds = bds_str.split()
        # print('bds=',bds)
        self.xmin = float(bds[0])
        self.xmax = float(bds[3])
        self.x_range = self.xmax - self.xmin

        self.ymin = float(bds[1])
        self.ymax = float(bds[4])
        self.y_range = self.ymax - self.ymin

        # and plot 1st frame (.svg)
        self.current_svg_frame = 0
        # self.forward_plot_cb("")  


    # def output_dir_changed(self, text):
    #     self.output_dir = text
    #     print(self.output_dir)

    def first_plot_cb(self, text):
        if self.reset_model_flag:
            self.reset_model()
            self.reset_model_flag = False

        self.current_svg_frame = 0
        self.update_plots()

    def last_plot_cb(self, text):
        if self.reset_model_flag:
            self.reset_model()
            self.reset_model_flag = False

        logging.debug(f'last_plot_cb(): cwd = {os.getcwd()}')
        logging.debug(f'last_plot_cb(): self.output_dir = {self.output_dir}')
        # xml_file = Path(self.output_dir, "initial.xml")
        # xml_files = glob.glob('tmpdir/output*.xml')

        # full_fname = os.path.join(self.output_dir, fname)
        xml_files = glob.glob(self.output_dir + '/output*.xml')
        logging.debug(f'xml_files = {xml_files}')
        if len(xml_files) == 0:
            logging.debug(f'last_plot_cb(): no xml_files, returning')
            return
        xml_files.sort()
        # rwh: problematic with celltypes3 due to snapshot_standard*.svg and snapshot<8digits>.svg
        svg_files = glob.glob(self.output_dir + '/snapshot*.svg')
        svg_files.sort()
        # print('xml_files = ',xml_files)
        num_xml = len(xml_files)
        # print('svg_files = ',svg_files)
        num_svg = len(svg_files)
        logging.debug(f'num_xml, num_svg = {num_xml}, {num_svg}')
        last_xml = int(xml_files[-1][-12:-4])
        last_svg = int(svg_files[-1][-12:-4])
        logging.debug(f'last_xml, _svg = {last_xml}, {last_svg}')
        self.current_svg_frame = last_xml
        if last_svg < last_xml:
            self.current_svg_frame = last_svg
        self.update_plots()

    def back_plot_cb(self, text):
        if self.reset_model_flag:
            self.reset_model()
            self.reset_model_flag = False

        self.current_svg_frame -= 1
        if self.current_svg_frame < 0:
            self.current_svg_frame = 0
        logging.debug(f'back_plot_cb(): svg # {self.current_svg_frame}')

        self.update_plots()


    def forward_plot_cb(self, text):
        if self.reset_model_flag:
            self.reset_model()
            self.reset_model_flag = False

        self.current_svg_frame += 1
        # print('svg # ',self.current_svg_frame)

        self.update_plots()


    # def task(self):
            # self.dc.update_figure()

    # used by animate
    def play_plot_cb(self):
        for idx in range(1):
            self.current_svg_frame += 1
            # print('svg # ',self.current_svg_frame)

            fname = "snapshot%08d.svg" % self.current_svg_frame
            full_fname = os.path.join(self.output_dir, fname)
            # print("full_fname = ",full_fname)
            # with debug_view:
                # print("plot_svg:", full_fname) 
            # print("-- plot_svg:", full_fname) 
            if not os.path.isfile(full_fname):
                # print("Once output files are generated, click the slider.")   
                logging.debug(f'play_plot_cb():  Reached the end (or no output files found).')
                # self.timer.stop()
                self.current_svg_frame -= 1
                self.animating_flag = True
                # self.current_svg_frame = 0
                self.animate()
                return

            self.update_plots()


    def cells_toggle_cb(self,bval):
        self.cells_checked_flag = bval
        self.cells_edge_checkbox.setEnabled(bval)
        self.cells_nucleus_checkbox.setEnabled(bval)
        self.update_plots()

    def cells_edge_toggle_cb(self,bval):
        self.cells_edge_checked_flag = bval
        self.update_plots()

    def cells_nucleus_toggle_cb(self,bval):
        self.show_nucleus = bval
        self.update_plots()


    def substrates_toggle_cb(self,bval):
        self.substrates_checked_flag = bval
        self.fix_cmap_checkbox.setEnabled(bval)
        self.substrates_combobox.setEnabled(bval)

        self.update_plots()

    def fix_cmap_toggle_cb(self,bval):
        logging.debug(f'fix_cmap_toggle_cb():')
        self.fix_cmap_flag = bval
        self.cmin.setEnabled(bval)
        self.cmax.setEnabled(bval)

            # self.substrates_combobox.addItem(s)
        # field_name = self.field_dict[self.substrate_choice.value]
        logging.debug(f'self.field_dict= {self.field_dict}')
        # field_name = self.field_dict[self.substrates_combobox.currentText()]
        field_name = self.substrates_combobox.currentText()
        logging.debug(f'field_name= {field_name}')
        # print(self.cmap_fixed_toggle.value)
        # if (self.colormap_fixed_toggle.value):  # toggle on fixed range
        if (bval):  # toggle on fixed range
            # self.colormap_min.disabled = False
            # self.colormap_max.disabled = False
            self.field_min_max[field_name][0] = self.cmin.text
            self.field_min_max[field_name][1] = self.cmax.text
            self.field_min_max[field_name][2] = True
            # self.save_min_max.disabled = False
        else:  # toggle off fixed range
            # self.colormap_min.disabled = True
            # self.colormap_max.disabled = True
            self.field_min_max[field_name][2] = False

        self.update_plots()


    def animate(self):
        if not self.animating_flag:
            self.animating_flag = True
            self.play_button.setText("Pause")
            self.play_button.setStyleSheet("background-color : red")

            if self.reset_model_flag:
                self.reset_model()
                self.reset_model_flag = False

            # self.current_svg_frame = 0
            self.timer.start(1)

        else:
            self.animating_flag = False
            self.play_button.setText("Play")
            self.play_button.setStyleSheet("background-color : lightgreen")
            self.timer.stop()


    # def play_plot_cb0(self, text):
    #     for idx in range(10):
    #         self.current_svg_frame += 1
    #         print('svg # ',self.current_svg_frame)
    #         self.plot_svg(self.current_svg_frame)
    #         self.canvas.update()
    #         self.canvas.draw()
    #         # time.sleep(1)
    #         # self.ax0.clear()
    #         # self.canvas.pause(0.05)

    def prepare_plot_cb(self, text):
        self.current_svg_frame += 1
        logging.debug(f'\n   ====>     prepare_plot_cb(): svg # {self.current_svg_frame}')
        self.update_plots()


    def create_figure(self):
        logging.debug(f'vis_tab.py: --------- create_figure(): ------- creating figure, canvas, ax0')
        self.figure = plt.figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setStyleSheet("background-color:transparent;")

        # Adding one subplot for image
        # self.ax0 = self.figure.add_subplot(111)
        # self.ax0 = self.figure.add_subplot(111, adjustable='box', aspect=1.2)
        # self.ax0 = self.figure.add_subplot(111, adjustable='box', aspect=self.aspect_ratio)
        self.ax0 = self.figure.add_subplot(111, adjustable='box')
        
        # self.ax0.get_xaxis().set_visible(False)
        # self.ax0.get_yaxis().set_visible(False)
        # plt.tight_layout()

        self.reset_model()

        # np.random.seed(19680801)  # for reproducibility
        # N = 50
        # x = np.random.rand(N) * 2000
        # y = np.random.rand(N) * 2000
        # colors = np.random.rand(N)
        # area = (30 * np.random.rand(N))**2  # 0 to 15 point radii
        # self.ax0.scatter(x, y, s=area, c=colors, alpha=0.5)

        # if self.plot_svg_flag:
        # if False:
        #     self.plot_svg(self.current_svg_frame)
        # else:
        #     self.plot_substrate(self.current_svg_frame)

        logging.debug(f'vis_tab.py: create_figure(): ------- creating dummy contourf')
        xlist = np.linspace(-3.0, 3.0, 50)
        logging.debug(f'vis_tab.py: len(xlist)= {len(xlist)}')
        ylist = np.linspace(-3.0, 3.0, 50)
        X, Y = np.meshgrid(xlist, ylist)
        Z = np.sqrt(X**2 + Y**2) + 10*np.random.rand()

        self.cmap = plt.cm.get_cmap("viridis")
        self.mysubstrate = self.ax0.contourf(X, Y, Z, cmap=self.cmap)
        # if self.field_index > 4:
        #     # plt.contour(xgrid, ygrid, M[self.field_index, :].reshape(self.numy,self.numx), [0.0])
        #     plt.contour(X, Y, Z, [0.0])

        # levels = MaxNLocator(nbins=self.num_contours).tick_values(self.cmin_value, self.cmax_value)

#rwh - not for this demo
        # self.cbar = self.figure.colorbar(self.mysubstrate, ax=self.ax0)
        # self.cbar.ax.tick_params(labelsize=self.fontsize)

        # substrate_plot = self.ax0.contourf(xgrid, ygrid, M[self.field_index, :].reshape(self.numy,self.numx), num_contours, cmap='viridis')  # self.colormap_dd.value)

        logging.debug(f'vis_tab.py: ------------create_figure():  # axes = {len(self.figure.axes)}')

        # self.imageInit = [[255] * 320 for i in range(240)]
        # self.imageInit[0][0] = 0

        # Init image and add colorbar
        # self.image = self.ax0.imshow(self.imageInit, interpolation='none')
        # divider = make_axes_locatable(self.ax0)
        # cax = divider.new_vertical(size="5%", pad=0.05, pack_start=True)
        # self.colorbar = self.figure.add_axes(cax)
        # self.figure.colorbar(self.image, cax=cax, orientation='horizontal')

        # plt.subplots_adjust(left=0, bottom=0.05, right=1, top=1, wspace=0, hspace=0)

        self.plot_substrate(self.current_svg_frame)
        self.plot_svg(self.current_svg_frame)
        # self.canvas.draw()

    #---------------------------------------------------------------------------
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

    #------------------------------------------------------------
    # not currently used, but maybe useful
    def plot_vecs(self):
        # global current_frame

        fname = "output%08d.xml" % self.current_svg_frame
        # print("plot_vecs(): fname = ",fname)
        # full_fname = os.path.join(self.output_dir, fname)
        # mcds=pyMCDS_cells("output00000049.xml")
        try:
            # mcds = pyMCDS_cells(fname)
            # print("plot_vecs(): self.output_dir= ",self.output_dir)

            # mcds = pyMCDS_cells(fname, self.output_dir)
            mcds = pyMCDS(fname, self.output_dir)

            # print(mcds.get_cell_variables())

            xpos = mcds.data['discrete_cells']['position_x']
            ypos = mcds.data['discrete_cells']['position_y']
            # print("------- plot_vecs(): xpos=", xpos)

            xvec = mcds.data['discrete_cells']['xvec']
            yvec = mcds.data['discrete_cells']['yvec']
            # # print("------- plot_vecs(): xvals=", mcds.data['discrete_cells']['position_x'])
            # # print("------- plot_vecs(): yvals=", mcds.data['discrete_cells']['position_y'])
            # # print("------- plot_vecs(): xvec=", mcds.data['discrete_cells']['xvec'])
            # # print("------- plot_vecs(): yvec=", mcds.data['discrete_cells']['yvec'])

            # # lines = [[(0, 1), (1, 1)], [(2, 3), (3, 3)], [(1, 2), (1, 3)]]
            sfact = 30
            vlines = []
            for idx in range(len(xpos)):
                x0 = xpos[idx]
                y0 = ypos[idx]
                x1 = xpos[idx] + xvec[idx]*sfact
                y1 = ypos[idx] + yvec[idx]*sfact
                vlines.append( [(x0,y0), (x1,y1)] )
            # print("vlines = ",vlines)
            # ax = plt.gca()
            self.line_collection = LineCollection(vlines, color="black", linewidths=0.5)
            self.ax0.add_collection(self.line_collection)
        except:
            logging.debug(f'vis_tab.py: plot_vecs(): ERROR')
            pass

    #------------------------------------------------------------
    # This is primarily used for debugging.
    def plot_voxel_grid(self):
        #  Should we actually parse/use coords in initial.xml, e.g.:
        #      <x_coordinates delimiter=" ">-490.000000 -470.000000
        # xoffset = self.xdel / 2.0
        # yoffset = self.ydel / 2.0
        # xmax = self.xmax - xoffset
        # xmin = self.xmin + xoffset
        # ymax = self.ymax - yoffset
        # ymin = self.ymin + yoffset

        xs = np.arange(self.xmin,self.xmax+1,self.xdel)  # DON'T try to use np.linspace!
        # print("xs= ",xs)
        ys = np.arange(self.ymin,self.ymax+1,self.ydel)
        # print("ys= ",ys)
        hlines = np.column_stack(np.broadcast_arrays(xs[0], ys, xs[-1], ys))
        vlines = np.column_stack(np.broadcast_arrays(xs, ys[0], xs, ys[-1]))
        grid_lines = np.concatenate([hlines, vlines]).reshape(-1, 2, 2)
        line_collection = LineCollection(grid_lines, color="gray", linewidths=0.5)
        self.ax0.add_collection(line_collection)

    #------------------------------------------------------------
    # This is primarily used for debugging tricky mechanics dynamics; probably hardly ever used.
    def plot_mechanics_grid(self):
        # numx = int((self.xmax - self.xmin)/self.mech_voxel_size)
        # numy = int((self.ymax - self.ymin)/self.mech_voxel_size)
        # xs = np.linspace(self.xmin,self.xmax, numx)
        # ys = np.linspace(self.ymin,self.ymax, numy)
        xs = np.arange(self.xmin,self.xmax+1,self.mech_voxel_size)  # DON'T try to use np.linspace!
        # print("xs= ",xs)
        ys = np.arange(self.ymin,self.ymax+1,self.mech_voxel_size)
        hlines = np.column_stack(np.broadcast_arrays(xs[0], ys, xs[-1], ys))
        vlines = np.column_stack(np.broadcast_arrays(xs, ys[0], xs, ys[-1]))
        grid_lines = np.concatenate([hlines, vlines]).reshape(-1, 2, 2)
        line_collection = LineCollection(grid_lines, color="red", linewidths=0.7)
        # ax = plt.gca()
        # ax.add_collection(line_collection)
        self.ax0.add_collection(line_collection)
        # ax.set_xlim(xs[0], xs[-1])
        # ax.set_ylim(ys[0], ys[-1])

    #------------------------------------------------------------
    # For debugging.
    # def plot_voxel_grid(self):
    #     numx = int((self.xmax - self.xmin)/self.xdel)
    #     numy = int((self.ymax - self.ymin)/self.ydel)
    #     xs = np.linspace(self.xmin,self.xmax, numx)
    #     ys = np.linspace(self.ymin,self.ymax, numy)
    #     hlines = np.column_stack(np.broadcast_arrays(xs[0], ys, xs[-1], ys))
    #     vlines = np.column_stack(np.broadcast_arrays(xs, ys[0], xs, ys[-1]))
    #     grid_lines = np.concatenate([hlines, vlines]).reshape(-1, 2, 2)
    #     line_collection = LineCollection(grid_lines, color="gray", linewidths=0.5)
    #     # ax = plt.gca()
    #     # ax.add_collection(line_collection)
    #     self.ax0.add_collection(line_collection)

    #------------------------------------------------------------
    # def plot_svg(self, frame, rdel=''):
    def plot_svg(self, frame):
        # global current_idx, axes_max
        # global current_frame

        # return

        # if self.show_voxel_grid:
        #     self.plot_voxel_grid()
        # if self.show_mech_grid:
        #     self.plot_mechanics_grid()

        # if self.show_vectors:
        #     self.plot_vecs()

        # current_frame = frame
        # self.current_frame = frame
        fname = "snapshot%08d.svg" % frame
        full_fname = os.path.join(self.output_dir, fname)
        # try:
        #     print("   ==>>>>> plot_svg(): full_fname=",full_fname)
        # except:
        #     print("plot_svg(): ERROR:  full_name invalid")   
        #     return
        # with debug_view:
            # print("plot_svg:", full_fname) 
        # print("-- plot_svg:", full_fname) 
        if not os.path.isfile(full_fname):
            # print("Once output files are generated, click the slider.")   
            logging.debug(f'vis_tab.py: plot_svg(): Warning: filename not found: {full_fname}')
            return

        # self.ax0.cla()
        self.title_str = ""

# https://stackoverflow.com/questions/5263034/remove-colorbar-from-figure-in-matplotlib
# def foo(self):
#    self.subplot.clear()
#    hb = self.subplot.hexbin(...)
#    if self.cb:
#       self.figure.delaxes(self.figure.axes[1])
#       self.figure.subplots_adjust(right=0.90)  #default right padding
#    self.cb = self.figure.colorbar(hb)

        # if self.cbar:
            # self.cbar.remove()

        # bgcolor = self.bgcolor;  # 1.0 for white 
        # bgcolor = [0,0,0,1]  # dark mode

        xlist = deque()
        ylist = deque()
        rlist = deque()
        rgba_list = deque()

        #  print('\n---- ' + fname + ':')
#        tree = ET.parse(fname)
        try:
            tree = ET.parse(full_fname)
        except:  # might arrive here if user cancels a Run then tries to go to last frame (>|) in Plot tab
            logging.debug(f'vis_tab.py: ------ plot_svg(): error trying to parse {fname}. Will try previous file.')
            if frame > 0:
                frame -= 1
                fname = "snapshot%08d.svg" % frame
                full_fname = os.path.join(self.output_dir, fname)
                try:
                    tree = ET.parse(full_fname)
                except:  # might arrive here if user cancels a Run then tries to go to last frame (>|) in Plot tab
                    logging.debug(f'vis_tab.py: ------ plot_svg(): error trying to parse {fname}')
                    return
            # return
        root = tree.getroot()
        #  print('--- root.tag ---')
        #  print(root.tag)
        #  print('--- root.attrib ---')
        #  print(root.attrib)
        #  print('--- child.tag, child.attrib ---')
        numChildren = 0
        for child in root:
            #    print(child.tag, child.attrib)
            #    print("keys=",child.attrib.keys())
            # if self.use_defaults and ('width' in child.attrib.keys()):
            #     self.axes_max = float(child.attrib['width'])
                # print("debug> found width --> axes_max =", axes_max)
            if child.text and "Current time" in child.text:
                svals = child.text.split()
                # remove the ".00" on minutes
                self.title_str += "   cells: " + svals[2] + "d, " + svals[4] + "h, " + svals[7][:-3] + "m"

                # self.cell_time_mins = int(svals[2])*1440 + int(svals[4])*60 + int(svals[7][:-3])
                # self.title_str += "   cells: " + str(self.cell_time_mins) + "m"   # rwh

            # print("width ",child.attrib['width'])
            # print('attrib=',child.attrib)
            # if (child.attrib['id'] == 'tissue'):
            if ('id' in child.attrib.keys()):
                # print('-------- found tissue!!')
                tissue_parent = child
                break

        # print('------ search tissue')
        cells_parent = None

        for child in tissue_parent:
            # print('attrib=',child.attrib)
            if (child.attrib['id'] == 'cells'):
                # print('-------- found cells, setting cells_parent')
                cells_parent = child
                break
            numChildren += 1

        num_cells = 0
        #  print('------ search cells')
        for child in cells_parent:
            #    print(child.tag, child.attrib)
            #    print('attrib=',child.attrib)
            for circle in child:  # two circles in each child: outer + nucleus
                #  circle.attrib={'cx': '1085.59','cy': '1225.24','fill': 'rgb(159,159,96)','r': '6.67717','stroke': 'rgb(159,159,96)','stroke-width': '0.5'}
                #      print('  --- cx,cy=',circle.attrib['cx'],circle.attrib['cy'])
                xval = float(circle.attrib['cx'])

                # map SVG coords into comp domain
                # xval = (xval-self.svg_xmin)/self.svg_xrange * self.x_range + self.xmin
                xval = xval/self.x_range * self.x_range + self.xmin

                s = circle.attrib['fill']
                # print("s=",s)
                # print("type(s)=",type(s))
                if( s[0:4] == "rgba" ):
                    # background = bgcolor[0] * 255.0; # coudl also be 255.0 for white
                    rgba_float =list(map(float,s[5:-1].split(",")))
                    r = rgba_float[0]
                    g = rgba_float[1]
                    b = rgba_float[2]                    
                    alpha = rgba_float[3]
                    alpha *= 2.0; # cell_alpha_toggle
                    if( alpha > 1.0 ):
                    # if( alpha > 1.0 or self.cell_alpha_toggle.value == False ):
                        alpha = 1.0
                    # if( self.cell_alpha_toggle.value == False ):
                    #     alpha = 1.0;  

#                        if( self.substrates_toggle.value and 1 == 2 ):
#                            r = background * (1-alpha) + alpha*rgba_float[0];
#                            g = background * (1-alpha) + alpha*rgba_float[1];
#                            b = background * (1-alpha) + alpha*rgba_float[2];
                    rgba = [1,1,1,alpha]
                    rgba[0:3] = [ np.round(r), np.round(g), np.round(b) ]
                    rgba[0:3] = [x / 255. for x in rgba[0:3] ]  
                    # rgba = [rgba_float[0]/255.0, rgba_float[1]/255.0, rgba_float[2]/255.0,alpha];
                    # rgba[0:3] = rgb; 
                    # rgb = list(map(int, s[5:-1].split(",")))
                elif (s[0:3] == "rgb"):  # if an rgb string, e.g. "rgb(175,175,80)" 
                    rgba = [1,1,1,1.0]
                    rgba[0:3] = list(map(int, s[4:-1].split(",")))  
                    rgba[0:3] = [x / 255. for x in rgba[0:3] ]
                else:     # otherwise, must be a color name
                    rgb_tuple = mplc.to_rgb(mplc.cnames[s])  # a tuple
                    rgba = [1,1,1,1.0]
                    rgba[0:3] = [x for x in rgb_tuple]

                # test for bogus x,y locations (rwh TODO: use max of domain?)
                too_large_val = 10000.
                if (np.fabs(xval) > too_large_val):
                    logging.debug(f'bogus xval= {xval}')
                    break
                yval = float(circle.attrib['cy'])
                # yval = (yval - self.svg_xmin)/self.svg_xrange * self.y_range + self.ymin
                yval = yval/self.y_range * self.y_range + self.ymin
                if (np.fabs(yval) > too_large_val):
                    logging.debug(f'bogus yval= {yval}')
                    break

                rval = float(circle.attrib['r'])
                # if (rgb[0] > rgb[1]):
                #     print(num_cells,rgb, rval)
                xlist.append(xval)
                ylist.append(yval)
                rlist.append(rval)
                rgba_list.append(rgba)

                # For .svg files with cells that *have* a nucleus, there will be a 2nd pass
                if (not self.show_nucleus):
                    break

            num_cells += 1

            # if num_cells > 3:   # for debugging
            #   print(fname,':  num_cells= ',num_cells," --- debug exit.")
            #   sys.exit(1)
            #   break

            # print(fname,':  num_cells= ',num_cells)

        xvals = np.array(xlist)
        yvals = np.array(ylist)
        rvals = np.array(rlist)
        # rgbs = np.array(rgb_list)
        rgbas = np.array(rgba_list)
        # print("xvals[0:5]=",xvals[0:5])
        # print("rvals[0:5]=",rvals[0:5])
        # print("rvals.min, max=",rvals.min(),rvals.max())

        # rwh - is this where I change size of render window?? (YES - yipeee!)
        #   plt.figure(figsize=(6, 6))
        #   plt.cla()
        # if (self.substrates_toggle.value):
        self.title_str += " (" + str(num_cells) + " agents)"
            # title_str = " (" + str(num_cells) + " agents)"
        # else:
            # mins= round(int(float(root.find(".//current_time").text)))  # TODO: check units = mins
            # hrs = int(mins/60)
            # days = int(hrs/24)
            # title_str = '%dd, %dh, %dm' % (int(days),(hrs%24), mins - (hrs*60))
        # plt.title(self.title_str)
        self.ax0.set_title(self.title_str, fontsize=self.title_fontsize)
        # self.ax0.set_title(self.title_str, prop={'size':'small'})

        # plt.xlim(self.xmin, self.xmax)
        # plt.ylim(self.ymin, self.ymax)

        # print("plot_svg(): plot_xmin,xmax, ymin,ymax= ",self.plot_xmin,self.plot_xmax,self.plot_ymin,self.plot_ymax)
        # set xrange & yrange of plots
        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        # self.ax0.set_xlim(-450, self.xmax)

        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)
        # self.ax0.set_ylim(0.0, self.ymax)
        self.ax0.tick_params(labelsize=self.fontsize)

        self.ax0.set_facecolor(self.bgcolor)

        # self.ax0.colorbar(collection)

        #   plt.xlim(axes_min,axes_max)
        #   plt.ylim(axes_min,axes_max)
        #   plt.scatter(xvals,yvals, s=rvals*scale_radius, c=rgbs)

        # TODO: make figsize a function of plot_size? What about non-square plots?
        # self.fig = plt.figure(figsize=(9, 9))

#        axx = plt.axes([0, 0.05, 0.9, 0.9])  # left, bottom, width, height
#        axx = fig.gca()
#        print('fig.dpi=',fig.dpi) # = 72

        #   im = ax.imshow(f.reshape(100,100), interpolation='nearest', cmap=cmap, extent=[0,20, 0,20])
        #   ax.xlim(axes_min,axes_max)
        #   ax.ylim(axes_min,axes_max)

        # convert radii to radii in pixels
        # ax1 = self.fig.gca()
        # N = len(xvals)
        # rr_pix = (ax1.transData.transform(np.vstack([rvals, rvals]).T) -
        #             ax1.transData.transform(np.vstack([np.zeros(N), np.zeros(N)]).T))
        # rpix, _ = rr_pix.T

        # markers_size = (144. * rpix / self.fig.dpi)**2   # = (2*rpix / fig.dpi * 72)**2
        # markers_size = markers_size/4000000.
        # print('max=',markers_size.max())

        #rwh - temp fix - Ah, error only occurs when "edges" is toggled on
        # if (self.show_edge):
        if (self.cells_edge_checked_flag):
            try:
                # plt.scatter(xvals,yvals, s=markers_size, c=rgbs, edgecolor='black', linewidth=0.5)
                # self.circles(xvals,yvals, s=rvals, color=rgbas, alpha=self.alpha, edgecolor='black', linewidth=0.5)
                # print("--- plotting circles with edges!!")
                self.circles(xvals,yvals, s=rvals, color=rgbas, edgecolor='black', linewidth=0.5)  # alpha=0.5
                # cell_circles = self.circles(xvals,yvals, s=rvals, color=rgbs, edgecolor='black', linewidth=0.5)
                # plt.sci(cell_circles)
            except (ValueError):
                pass
        else:
            # plt.scatter(xvals,yvals, s=markers_size, c=rgbs)
            # self.circles(xvals,yvals, s=rvals, color=rgbas, alpha=self.alpha)
            # print("--- plotting circles without edges!!")
            self.circles(xvals,yvals, s=rvals, color=rgbas)

        self.ax0.set_aspect(1.0)

    #------------------------------------------------------------
    def plot_substrate(self, frame):
        # global current_idx, axes_max
        global current_frame

        xml_file_root = "output%08d.xml" % frame
        xml_file = os.path.join(self.output_dir, xml_file_root)
        if not Path(xml_file).is_file():
            logging.debug(f'vis_tab.py: ERROR: file not found {xml_file}')
            return

        # xml_file = os.path.join(self.output_dir, xml_file_root)
        tree = ET.parse(xml_file)
        root = tree.getroot()
    #    print('time=' + root.find(".//current_time").text)
        mins = float(root.find(".//current_time").text)
        hrs = int(mins/60)
        days = int(hrs/24)
        self.title_str = '%d days, %d hrs, %d mins' % (days,hrs-days*24, mins-hrs*60)
        # print(self.title_str)

        fname = "output%08d_microenvironment0.mat" % frame
        full_fname = os.path.join(self.output_dir, fname)
        # print("vis_tab.py:    ==>>>>> plot_substrate(): full_fname=",full_fname)
        if not Path(full_fname).is_file():
            print("vis_tab.py: ERROR: file not found",full_fname)
            logging.debug(f'vis_tab.py: ERROR: file not found {full_fname}')
            return

        info_dict = {}
        scipy.io.loadmat(full_fname, info_dict)
        M = info_dict['multiscale_microenvironment']
        logging.debug(f'vis_tab.py: plot_substrate: self.field_index= {self.field_index}')

        # debug
        # fsub = M[self.field_index,:]   # 
        # print("substrate min,max=",fsub.min(), fsub.max())

        # print("M.shape = ",M.shape)  # e.g.,  (6, 421875)  (where 421875=75*75*75)

        # numx = int(M.shape[1] ** (1./3) + 1)
        # numy = numx
        # self.numx = 50  # for template model
        # self.numy = 50

        # try:
        #     logging.debug(f'self.numx, self.numy = {self.numx}, {self.numy}')
        #     # print(f'vis_tab.py: self.numx, self.numy = {self.numx}, {self.numy}')
        # except:
        #     logging.debug(f'Error: self.numx, self.numy not defined.')
        #     return
        # nxny = numx * numy

        try:
            xgrid = M[0, :].reshape(self.numy, self.numx)
            ygrid = M[1, :].reshape(self.numy, self.numx)
        except:
            print("error: cannot reshape ",self.numy, self.numx," for array ",M.shape)
            logging.debug(f'error: cannot reshape {self.numy}, {self.numx} for array {M.shape}')
            return

        zvals = M[self.field_index,:].reshape(self.numy,self.numx)

        contour_ok = True

        if (self.fix_cmap_flag):
            try:
                # self.fixed_contour_levels = MaxNLocator(nbins=self.num_contours).tick_values(self.cmin_value, self.cmax_value)
                # substrate_plot = self.ax0.contourf(xgrid, ygrid, M[self.field_index, :].reshape(self.numy, self.numx), levels=levels, extend='both', cmap=self.colormap_dd.value, fontsize=self.fontsize)

                # substrate_plot = self.ax0.contourf(xgrid, ygrid, zvals, self.num_contours, levels=self.fixed_contour_levels, extend='both', cmap='viridis')

                substrate_plot = self.ax0.pcolormesh(xgrid,ygrid, zvals, shading=self.shading_choice, cmap='viridis', vmin=self.cmin_value, vmax=self.cmax_value)
            except:
                contour_ok = False
                print('\nWARNING: exception with fixed colormap range. Will not update plot.')
                return
        else:    
            try:
                # substrate_plot = self.ax0.contourf(xgrid, ygrid, zvals, self.num_contours, cmap='viridis')  # self.colormap_dd.value)
                # substrate_plot = self.ax0.pcolormesh(xgrid,ygrid, zvals, shading='gouraud', cmap='viridis') #, vmin=Z.min(), vmax=Z.max())
                # substrate_plot = self.ax0.pcolormesh(xgrid,ygrid, zvals, cmap='viridis') #, vmin=Z.min(), vmax=Z.max())

                # substrate_plot = self.ax0.pcolormesh(xgrid,ygrid, zvals, shading='flat', cmap='viridis') #, vmin=Z.min(), vmax=Z.max())
                substrate_plot = self.ax0.pcolormesh(xgrid,ygrid, zvals, shading=self.shading_choice, cmap='viridis') #, vmin=Z.min(), vmax=Z.max())

            except:
                contour_ok = False
                print('\nWARNING: exception with dynamic colormap range. Will not update plot.')
                return

        # in case we want to plot a "0.0" contour line
        # if self.field_index > 4:
        #     self.ax0.contour(xgrid, ygrid, M[self.field_index, :].reshape(self.numy,self.numx), [0.0], linewidths=0.5)

        # Do this funky stuff to prevent the colorbar from shrinking in height with each redraw.
        # Except it doesn't seem to work when we use fixed ranges on the colorbar?!
        logging.debug(f'# axes = {len(self.figure.axes)}')
        if len(self.figure.axes) > 1: 
            pts = self.figure.axes[-1].get_position().get_points()
            # print("type(pts) = ",type(pts))
            # pts = [[0.78375, 0.11][0.81037234, 0.88]]
            pts = np.array([[0.78375, 0.11],[0.81037234, 0.88]])

            # print("figure.axes pts = ",pts)
            label = self.figure.axes[-1].get_ylabel()
            self.figure.axes[-1].remove()  # replace/update the colorbar
            cax = self.figure.add_axes([pts[0][0],pts[0][1],pts[1][0]-pts[0][0],pts[1][1]-pts[0][1]  ])
            self.cbar = self.figure.colorbar(substrate_plot, cax=cax)
            self.cbar.ax.set_ylabel(label)
            self.cbar.ax.tick_params(labelsize=self.fontsize)

            # unfortunately the aspect is different between the initial call to colorbar 
            #   without cax argument. Try to reset it (but still it's somehow different)
            # self.cbar.ax.set_aspect(20)
        else:
            # plt.colorbar(im)
            self.figure.colorbar(substrate_plot)

        self.ax0.set_title(self.title_str, fontsize=self.title_fontsize)

        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)

        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)
        self.ax0.set_aspect(1.0)
