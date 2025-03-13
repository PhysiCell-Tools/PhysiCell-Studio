"""
vis_tab.py - provide visualization on Plot tab. Cells can be plotted on top of substrates/signals.

Authors:
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
Rf. Credits.md
"""

import sys
import os
import time
# import inspect
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from pathlib import Path
# from ipywidgets import Layout, Label, Text, Checkbox, Button, BoundedIntText, HBox, VBox, Box, \
    # FloatText, Dropdown, SelectMultiple, RadioButtons, interactive
# import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle, Ellipse, Rectangle
from matplotlib.collections import PatchCollection
import matplotlib.colors as mplc
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable
from matplotlib import gridspec
from collections import deque
import glob
import csv
import pandas

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QGroupBox, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,  QMainWindow,QGridLayout, QPushButton, QFileDialog, QMessageBox, QStackedWidget, QSplitter
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QRectF
locale_en_US = QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates)

import numpy as np
import scipy.io
from pyMCDS_cells import pyMCDS_cells 
from pyMCDS import pyMCDS
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

# from PyQt5 import QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
# from matplotlib.figure import Figure

class SvgWidget(QSvgWidget):
    def __init__(self, *args):
        QSvgWidget.__init__(self, *args)

    def paintEvent(self, event):
        renderer = self.renderer()
        if renderer != None:
            painter = QPainter(self)
            size = renderer.defaultSize()
            ratio = size.height()/size.width()
            length = min(self.width(), self.height())
            renderer.render(painter, QRectF(0, 0, length, ratio * length))
            painter.end()

class Legend(QWidget):
    # def __init__(self, doc_absolute_path, nanohub_flag):
    def __init__(self, nanohub_flag):
        super().__init__()

        # self.doc_absolute_path = doc_absolute_path

        self.process = None
        self.output_dir = '.'   # set in pmb.py
        self.current_dir = '.'   # reset in pmb.py
        self.pmb_data_dir = ''   # reset in pmb.py
        
        #-------------------------------------------
        self.scroll = QScrollArea()  # might contain centralWidget

        self.svgView = SvgWidget()
        self.vbox = QVBoxLayout()

        self.svgView.setLayout(self.vbox)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)
        # self.scroll.setWidgetResizable(False)

        self.scroll.setWidget(self.svgView) 
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.scroll)

    def clear_legend(self):
        legend_file = os.path.join(self.pmb_data_dir, 'empty_legend.svg')
        self.svgView.load(legend_file)

    def reload_legend(self):
        print('reload_legend(): self.output_dir = ',self.output_dir)
        for idx in range(4):
            print("waiting for creation of legend.svg ...",idx)
            # path = Path("legend.svg")
            path = Path(self.output_dir,"legend.svg")
            # path = Path(self.current_dir,self.output_dir,"legend.svg")
            print("path = ",path)
            if path.is_file():
            # try:
                # self.svgView.load("legend.svg")
                full_fname = os.path.join(self.output_dir, "legend.svg")
                # full_fname = os.path.join(self.current_dir,self.output_dir, "legend.svg")
                print("legend_tab.py: full_fname = ",full_fname)
                self.svgView.load(full_fname)
                break
            # except:
            #     path = Path(self.current_dir,self.output_dir,"legend.svg")
            #     time.sleep(1)
            else:
                path = Path(self.output_dir,"legend.svg")
                # path = Path(self.current_dir,self.output_dir,"legend.svg")
                time.sleep(1)

#------------------------------
class LegendPlotWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        # self.label = QLabel("Cell populations")
        # self.layout.addWidget(self.label)

        self.figure = plt.figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setStyleSheet("background-color:transparent;")
        self.ax0 = self.figure.add_subplot(111, adjustable='box')
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

class PopulationPlotWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.label = QLabel("Cell populations")
        # self.layout.addWidget(self.label)

        self.figure = plt.figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setStyleSheet("background-color:transparent;")
        self.ax0 = self.figure.add_subplot(111, adjustable='box')
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        # self.setFrameShadow(QFrame.Plain)
        # self.setStyleSheet("border:1px solid black")

class Vis(QWidget):

    def __init__(self, nanohub_flag, run_tab):
        super().__init__()
        # global self.config_params

        self.circle_radius = 100  # will be set in run_tab.py using the .xml
        self.mech_voxel_size = 30

        self.nanohub_flag = nanohub_flag
        self.run_tab = run_tab
        self.legend_tab = None

        self.bgcolor = [1,1,1,1]  # all 1.0 for white 

        self.population_plot = None
        self.celltype_name = []
        self.celltype_color = []

        self.animating_flag = False

        self.xml_root = None
        self.current_svg_frame = 0
        self.timer = QtCore.QTimer()
        # self.t.timeout.connect(self.task)
        self.timer.timeout.connect(self.play_plot_cb)

        # self.tab = QWidget()
        # self.tabs.resize(200,5)
        
        self.fix_cmap_flag = False
        self.cells_edge_checked_flag = True

        self.num_contours = 50
        self.shading_choice = 'auto'  # 'auto'(was 'flat') vs. 'gouraud' (smooth)

        self.fontsize = 7
        self.label_fontsize = 6
        self.title_fontsize = 10

        # self.plot_svg_flag = True
        self.plot_cells_svg = True
        # self.plot_svg_flag = False
        self.field_index = 4  # substrate (0th -> 4 in the .mat)
        self.substrate_name = None
        self.plot_xmin = None
        self.plot_xmax = None
        self.plot_ymin = None
        self.plot_ymax = None

        self.use_defaults = True
        self.title_str = ""

        self.show_plot_range = False

        # self.config_file = "mymodel.xml"
        self.physiboss_node_dict = {}
        
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

        self.view_aspect_square = True
        self.view_smooth_shading = False

        self.show_voxel_grid = False
        self.show_mechanics_grid = False
        self.show_vectors = False

        self.show_nucleus = False
        # self.show_edge = False
        self.show_edge = True
        self.alpha = 0.7

        basic_length = 12.0
        self.figsize_width_substrate = 15.0  # allow extra for colormap(s)
        self.figsize_height_substrate = basic_length

        self.cax1 = None
        self.cax2 = None

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

        # temporary debugging plotting without having to Run first
        # if self.nanohub_flag:
        #     self.output_dir = "."   # for nanoHUB
        # else:
        #     self.output_dir = "tmpdir"

        # stop the insanity!
        self.output_dir = "."   # for nanoHUB  (overwritten in studio.py, based on config_tab)
        # self.output_dir = "tmpdir"   # for nanoHUB


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

        # Beware: padding seems to alter the behavior; adding scroll arrows to choices list!
                # padding-right: 8px; padding-left: 8px; padding-top: 3px; padding-bottom: 3px;
                # height: 30px;
        self.stylesheet = """ 
            QComboBox{
                color: #000000;
                background-color: #FFFFFF; 
                height: 20px;
            }
            QComboBox:disabled {
                background-color: rgb(199,199,199);
                color: rgb(99,99,99);
            }
            QPushButton{ border: 1px solid; border-color: rgb(145, 200, 145); border-radius: 1px;  background-color: lightgreen; color: black; width: 64px; padding-right: 8px; padding-left: 8px; padding-top: 3px; padding-bottom: 3px; } 
            QPushButton:hover { border: 1px solid; border-radius: 3px; border-color: rgb(33, 77, 115); } QPushButton:focus { outline-color: transparent; border: 2px solid; border-color: rgb(151, 195, 243); } QPushButton:pressed{ background-color: rgb(145, 255, 145); } 
            QPushButton:disabled { color: black; border-color: grey; background-color: rgb(199,199,199); }

            """
            # QPushButton{ font-family: "Segoe UI"; font-size: 8pt; border: 1px solid; border-color: rgb(46, 103, 156); border-radius: 3px; padding-right: 10px; padding-left: 10px; padding-top: 5px; padding-bottom: 5px; background-color: rgb(77, 138, 201); color: white; font: bold; width: 64px; } 
            # QPushButton{
            #     color:#000000;
            #     background-color: lightgreen; 
            #     border-style: outset;
            #     border-color: black;
            #     padding: 2px;
            # }
            # QLineEdit:disabled {
            #     background-color: rgb(199,199,199);
            #     color: rgb(99,99,99);
            # }
            # QPushButton:disabled {
            #     background-color: rgb(199,199,199);
            # }
                # color: #000000;
                # background-color: #FFFFFF; 
                # border-style: outset;
                # border-width: 2px;
                # border-radius: 10px;
                # border-color: beige;
                # font: bold 14px;
                # min-width: 10em;
                # padding: 6px;
                # padding: 1px 18px 1px 3px;


        self.substrates_combobox = QComboBox()
        # self.substrates_combobox.setStyleSheet(self.stylesheet)
        self.substrates_combobox.setEnabled(False)
        self.field_dict = {}
        self.field_min_max = {}
        self.cmin_value = 0.0
        self.cmax_value = 1.0
        self.fixed_contour_levels = MaxNLocator(nbins=self.num_contours).tick_values(self.cmin_value, self.cmax_value)

        self.substrates_cbar_combobox = QComboBox()
        self.substrates_cbar_combobox.addItem("viridis")
        self.substrates_cbar_combobox.addItem("jet")
        self.substrates_cbar_combobox.addItem("YlOrRd")
        self.substrates_cbar_combobox.setEnabled(False)

        self.scroll_plot = QScrollArea()  # might contain centralWidget

        # Need to have the substrates_combobox before doing create_figure!
        self.create_figure()

        # self.config_params = QWidget()

        # self.main_layout = QVBoxLayout()

        # self.vbox = QVBoxLayout()
        # self.vbox.addStretch(0)
        self.create_vis_UI()


    def create_vis_UI(self):

        splitter = QSplitter()
        self.scroll_params = QScrollArea()
        splitter.addWidget(self.scroll_params)

        #---------------------
        self.stackw = QStackedWidget()
        self.stackw.setStyleSheet(self.stylesheet)  # will/should apply to all children widgets
        # self.stackw.setCurrentIndex(0)

        self.controls1 = QWidget()

        self.vbox = QVBoxLayout()
        self.controls1.setLayout(self.vbox)

        hbox = QHBoxLayout()
        arrow_button_width = 40
        self.first_button = QPushButton("|<")
        self.first_button.setFixedWidth(arrow_button_width)
        self.first_button.clicked.connect(self.first_plot_cb)
        hbox.addWidget(self.first_button)

        self.back_button = QPushButton("<")
        self.back_button.setFixedWidth(arrow_button_width)
        self.back_button.clicked.connect(self.back_plot_cb)
        hbox.addWidget(self.back_button)

        frame_count_width = 40
        self.frame_count = QLineEdit()
        # self.frame_count.textChanged.connect(self.change_frame_count_cb)  # do later to appease the callback gods
        self.frame_count.setFixedWidth(frame_count_width)
        self.frame_count.setValidator(QtGui.QIntValidator(0,10000000))
        self.frame_count.setText('0')
        hbox.addWidget(self.frame_count)


        self.forward_button = QPushButton(">")
        self.forward_button.setFixedWidth(arrow_button_width)
        self.forward_button.clicked.connect(self.forward_plot_cb)
        hbox.addWidget(self.forward_button)

        self.last_button = QPushButton(">|")
        self.last_button.setFixedWidth(arrow_button_width)
        self.last_button.clicked.connect(self.last_plot_cb)
        hbox.addWidget(self.last_button)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left

        self.vbox.addLayout(hbox)

        #------
        self.play_button = QPushButton("Play")
        self.play_button.setFixedWidth(70)
        # self.play_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        # self.play_button.clicked.connect(self.play_plot_cb)
        self.play_button.clicked.connect(self.animate)
        self.vbox.addWidget(self.play_button)

        # self.prepare_button = QPushButton("Prepare")
        # self.prepare_button.clicked.connect(self.prepare_plot_cb)
        # controls_hbox.addWidget(self.prepare_button)

        #------
        self.vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        self.cells_checkbox = QCheckBox('cells')
        self.cells_checkbox.setChecked(True)
        self.cells_checkbox.clicked.connect(self.cells_toggle_cb)
        self.cells_checked_flag = True
        hbox.addWidget(self.cells_checkbox) 

        # groupbox = QGroupBox()
        # groupbox.setStyleSheet("QGroupBox { border: 1px solid black;}")
        # hbox2 = QHBoxLayout()
        # groupbox.setLayout(hbox2)
        self.cells_svg_rb = QRadioButton('.svg')
        self.cells_svg_rb.setChecked(True)
        self.cells_svg_rb.clicked.connect(self.cells_svg_mat_cb)
        # hbox2.addWidget(self.cells_svg_rb)
        hbox.addWidget(self.cells_svg_rb)
        self.cells_mat_rb = QRadioButton('.mat')
        self.cells_mat_rb.clicked.connect(self.cells_svg_mat_cb)
        hbox.addWidget(self.cells_mat_rb)
        # hbox2.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        # hbox.addLayout(hbox2) 

        self.disable_cell_scalar_cb = False
        self.cell_scalar_combobox = QComboBox()
        # self.cell_scalar_combobox.setFixedWidth(300)
        # self.cell_scalar_combobox.currentIndexChanged.connect(self.cell_scalar_changed_cb)

        # e.g., dict_keys(['ID', 'position_x', 'position_y', 'position_z', 'total_volume', 'cell_type', 'cycle_model', 'current_phase', 'elapsed_time_in_phase', 'nuclear_volume', 'cytoplasmic_volume', 'fluid_fraction', 'calcified_fraction', 'orientation_x', 'orientation_y', 'orientation_z', 'polarity', 'migration_speed', 'motility_vector_x', 'motility_vector_y', 'motility_vector_z', 'migration_bias', 'motility_bias_direction_x', 'motility_bias_direction_y', 'motility_bias_direction_z', 'persistence_time', 'motility_reserved', 'chemotactic_sensitivities_x', 'chemotactic_sensitivities_y', 'adhesive_affinities_x', 'adhesive_affinities_y', 'dead_phagocytosis_rate', 'live_phagocytosis_rates_x', 'live_phagocytosis_rates_y', 'attack_rates_x', 'attack_rates_y', 'damage_rate', 'fusion_rates_x', 'fusion_rates_y', 'transformation_rates_x', 'transformation_rates_y', 'oncoprotein', 'elastic_coefficient', 'kill_rate', 'attachment_lifetime', 'attachment_rate', 'oncoprotein_saturation', 'oncoprotein_threshold', 'max_attachment_distance', 'min_attachment_distance'])


        self.cells_edge_checkbox = QCheckBox('edge')
        self.cells_edge_checkbox.setChecked(True)
        self.cells_edge_checkbox.clicked.connect(self.cells_edge_toggle_cb)
        self.cells_edge_checked_flag = True
        hbox.addWidget(self.cells_edge_checkbox) 

        self.vbox.addLayout(hbox)
        #------------------
        hbox = QHBoxLayout()
        self.add_default_cell_vars()
        self.disable_cell_scalar_cb = False
        self.cell_scalar_combobox.setEnabled(False)
        hbox.addWidget(self.cell_scalar_combobox)

        self.cell_scalar_cbar_combobox = QComboBox()
        self.cell_scalar_cbar_combobox.addItem("viridis")
        self.cell_scalar_cbar_combobox.addItem("jet")
        self.cell_scalar_cbar_combobox.addItem("YlOrRd")
        self.cell_scalar_cbar_combobox.setEnabled(False)
        hbox.addWidget(self.cell_scalar_cbar_combobox)
        self.vbox.addLayout(hbox)

        self.custom_button = QPushButton("append custom data")
        self.custom_button.setFixedWidth(150)
        self.custom_button.setEnabled(False)
        # self.custom_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        # self.play_button.clicked.connect(self.play_plot_cb)
        self.custom_button.clicked.connect(self.append_custom_cb)
        self.vbox.addWidget(self.custom_button)

        #------------------
        self.vbox.addWidget(QHLine())

        # hbox = QHBoxLayout()
        self.substrates_checkbox = QCheckBox('substrates')
        self.substrates_checkbox.setChecked(False)
        # self.substrates_checkbox.setEnabled(False)
        self.substrates_checkbox.clicked.connect(self.substrates_toggle_cb)
        self.substrates_checked_flag = False
        # hbox.addWidget(self.substrates_checkbox)
        self.vbox.addWidget(self.substrates_checkbox)

        hbox = QHBoxLayout()
        hbox.addWidget(self.substrates_combobox)
        hbox.addWidget(self.substrates_cbar_combobox)
        # hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left

        self.vbox.addLayout(hbox)

        #------
        hbox = QHBoxLayout()
        groupbox = QGroupBox()
        # groupbox.setTitle("colorbar")
        # vlayout = QVBoxLayout()
        # groupbox.setLayout(hbox)
        groupbox.setStyleSheet("QGroupBox { border: 1px solid black;}")
        # groupbox.setStyleSheet("QGroupBox::title {subcontrol-origin: margin; left: 7px; padding: 0px 5px 0px 5px;}")
        # groupbox.setStyleSheet("QGroupBox { border: 1px solid black; title: }")
#         QGroupBox::title {
#     subcontrol-origin: margin;
#     left: 7px;
#     padding: 0px 5px 0px 5px;
# }

        self.fix_cmap_checkbox = QCheckBox('fix')
        self.fix_cmap_flag = False
        self.fix_cmap_checkbox.setEnabled(False)
        self.fix_cmap_checkbox.setChecked(self.fix_cmap_flag)
        self.fix_cmap_checkbox.clicked.connect(self.fix_cmap_toggle_cb)
        hbox.addWidget(self.fix_cmap_checkbox)

        cvalue_width = 60
        label = QLabel("cmin")
        # label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        # label.setAlignment(QtCore.Qt.AlignLeft)
        hbox.addWidget(label)
        self.cmin = QLineEdit()
        self.cmin.setText('0.0')
        # self.cmin.textChanged.connect(self.change_plot_range)
        self.cmin.returnPressed.connect(self.cmin_cmax_cb)
        self.cmin.setFixedWidth(cvalue_width)
        cmin_validator = QtGui.QDoubleValidator()
        cmin_validator.setLocale(locale_en_US)
        self.cmin.setValidator(cmin_validator)
        self.cmin.setEnabled(False)
        hbox.addWidget(self.cmin)

        label = QLabel("cmax")
        # label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        hbox.addWidget(label)
        self.cmax = QLineEdit()
        self.cmax.setText('1.0')
        self.cmax.returnPressed.connect(self.cmin_cmax_cb)
        self.cmax.setFixedWidth(cvalue_width)
        cmax_validator = QtGui.QDoubleValidator()
        cmax_validator.setLocale(locale_en_US)
        self.cmax.setValidator(cmax_validator)
        self.cmax.setEnabled(False)
        hbox.addWidget(self.cmax)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left

        self.vbox.addLayout(hbox)

        label = QLabel("(press 'Enter' if cmin or cmax changes)")
        self.vbox.addWidget(label)

        #------------------
        self.vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        label = QLabel("folder")
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        # self.output_folder = QLineEdit(self.output_dir)
        self.output_folder = QLineEdit()
        self.output_folder.setEnabled(False)
        # self.output_folder.returnPressed.connect(self.output_folder_cb)
        hbox.addWidget(self.output_folder)

        # label = QLabel("(then 'Enter')")
        # hbox.addWidget(label)
        output_folder_button = QPushButton("Select")
        output_folder_button.clicked.connect(self.output_folder_cb)
        hbox.addWidget(output_folder_button)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        self.vbox.addLayout(hbox)

        # label = QLabel("(press 'Enter' to change)")
        # self.vbox.addWidget(label)

        self.vbox.addWidget(QHLine())

        #------------------
        self.cell_counts_button = QPushButton("Population plot")
        # self.cell_counts_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        self.cell_counts_button.setFixedWidth(200)
        self.cell_counts_button.clicked.connect(self.cell_counts_cb)
        self.vbox.addWidget(self.cell_counts_button)

        self.physiboss_qline = None
        self.physiboss_hbox_1 = None
        
        self.physiboss_vis_checkbox = None
        self.physiboss_vis_flag = False
        self.physiboss_selected_cell_line = None
        self.physiboss_selected_node = None
        self.physiboss_hbox_2 = None

        self.physiboss_cell_type_combobox = None
        self.physiboss_node_combobox = None
        #-----------
        self.frame_count.textChanged.connect(self.change_frame_count_cb)

        #-------------------
        self.substrates_combobox.currentIndexChanged.connect(self.substrates_combobox_changed_cb)
        self.substrates_cbar_combobox.currentIndexChanged.connect(self.update_plots)

        self.cell_scalar_combobox.currentIndexChanged.connect(self.update_plots)
        self.cell_scalar_cbar_combobox.currentIndexChanged.connect(self.update_plots)

        #==================================================================
        self.scroll_plot.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_plot.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_plot.setWidgetResizable(True)

        self.scroll_plot.setWidget(self.canvas) # self.config_params = QWidget()

        self.stackw.addWidget(self.controls1)
        self.stackw.setCurrentIndex(0)

        self.scroll_params.setWidget(self.stackw)
        splitter.addWidget(self.scroll_plot)

        self.show_plot_range = False
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(splitter)


    def get_cell_types_from_config(self):
        config_file = self.run_tab.config_xml_name.text()
        print("get_cell_types():  config_file=",config_file)
        basename = os.path.basename(config_file)
        print("get_cell_types():  basename=",basename)
        out_config_file = os.path.join(self.output_dir, basename)
        print("get_cell_types():  out_config_file=",out_config_file)

        try:
            self.tree = ET.parse(out_config_file)
            self.xml_root = self.tree.getroot()
        except:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Error opening or parsing " + out_config_file)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return False
            # print("get_cell_types_from_config(): Error opening or parsing " + out_config_file)

        try:
            self.celltype_name.clear()
            uep = self.xml_root.find('.//cell_definitions')  # find unique entry point
            if uep:
                idx = 0
                for var in uep.findall('cell_definition'):
                    name = var.attrib['name']
                    self.celltype_name.append(name)
            print("get_cell_types_from_config(): ",self.celltype_name)
        except:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Error parsing " + out_config_file)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return False

        return True


    def get_cell_types_from_legend(self):
        legend_file = os.path.join(self.output_dir, "legend.svg")
        # print("--get_cell_types():  legend=",legend_file)
        self.celltype_name.clear()
        self.celltype_color.clear()

        try:
            self.tree = ET.parse(legend_file)
            self.xml_root = self.tree.getroot()
            print("xml_root=",self.xml_root)
        except:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Error opening or parsing " + legend_file)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return False

        try: 
            for var in self.xml_root.findall('{http://www.w3.org/2000/svg}text'):
                ctname = var.text.strip()
                # print("-- ctname=",ctname)
                self.celltype_name.append(ctname)
            print(self.celltype_name)

            idx = 0
            for var in self.xml_root.findall('{http://www.w3.org/2000/svg}circle'):
                if (idx % 2) == 0:  # some legend.svg only have color on 1st occurrence (e.g., biorobots)
                    cattr = var.attrib
                    # print("-- cattr=",cattr)
                    # print("-- cattr['fill']=",cattr['fill'])
                    self.celltype_color.append(cattr['fill'])
                idx += 1
        except:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Error parsing " + legend_file)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return False

        return True


    def cell_counts_cb(self):
        print("---- cell_counts_cb(): --> window for 2D population plots")
        # self.analysis_data_wait.value = 'compute n of N ...'

        if not self.get_cell_types_from_legend():
            if not self.get_cell_types_from_config():
                return

        xml_pattern = self.output_dir + "/" + "output*.xml"
        xml_files = glob.glob(xml_pattern)
        # print(xml_files)
        num_xml = len(xml_files)
        if num_xml == 0:
            print("last_plot_cb(): WARNING: no output*.xml files present")
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Could not find any " + self.output_dir + "/output*.xml")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return

        xml_files.sort()
        # print("sorted: ",xml_files)

        mcds = []
        for fname in xml_files:
            basename = os.path.basename(fname)
            # print("basename= ",basename)
            # mcds = pyMCDS(basename, self.output_dir, microenv=False, graph=False, verbose=False)
            mcds.append(pyMCDS(basename, self.output_dir, microenv=False, graph=False, verbose=False))

        tval = np.linspace(0, mcds[-1].get_time(), len(xml_files))
        # print("  max tval=",tval)

        # self.yval4 = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['cell_type'] == 4) & (mcds[idx].data['discrete_cells']['cycle_model'] < 100.) == True)) for idx in range(ds_count)] )

        if not self.population_plot:
            self.population_plot = PopulationPlotWindow()

        self.population_plot.ax0.cla()

        # ctype_plot = []
        lw = 2
        # for itype, ctname in enumerate(self.celltypes_list):
        print("  self.celltype_name=",self.celltype_name)
        for itype in range(len(self.celltype_name)):
            ctname = self.celltype_name[itype]
            try:
                ctcolor = self.celltype_color[itype]
            except:
                ctcolor = 'C' + str(itype)   # use random colors from matplotlib
            print("  ctcolor=",ctcolor)
            if 'rgb' in ctcolor:
                rgb = ctcolor.replace('rgb','')
                rgb = rgb.replace('(','')
                rgb = rgb.replace(')','')
                rgb = rgb.split(',')
                print("--- rgb after split=",rgb)
                ctcolor = [float(rgb[0])/255., float(rgb[1])/255., float(rgb[2])/255.]
                print("--- converted rgb=",ctcolor)
            yval = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['data']['cell_type'] == itype) & (mcds[idx].data['discrete_cells']['data']['cycle_model'] < 100.) == True)) for idx in range(len(mcds))] )
            # yval = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['data']['cell_type'] == itype) == True)) for idx in range(len(mcds))] )
            # print("  yval=",yval)

            self.population_plot.ax0.plot(tval, yval, label=ctname, linewidth=lw, color=ctcolor)


        self.population_plot.ax0.set_xlabel('time (mins)')
        self.population_plot.ax0.set_ylabel('# of cells')
        self.population_plot.ax0.set_title("cell populations", fontsize=10)
        self.population_plot.ax0.legend(loc='center right', prop={'size': 8})
        self.population_plot.canvas.update()
        self.population_plot.canvas.draw()
        # self.population_plot.ax0.legend(loc='center right', prop={'size': 8})
        self.population_plot.show()

    def disable_physiboss_info(self):
        print("vis_tab: ------- disable_physiboss_info()")
        if self.physiboss_vis_checkbox is not None:
            print("vis_tab: ------- self.physiboss_vis_checkbox is not None; try disabling")
            try:
                self.physiboss_vis_checkbox.setChecked(False)
                self.physiboss_vis_checkbox.setEnabled(False)
                self.physiboss_cell_type_combobox.setEnabled(False)
                self.physiboss_node_combobox.setEnabled(False)
            except:
                print("ERROR: Exception disabling physiboss widgets")
                pass
        else:
            print("vis_tab: ------- self.physiboss_vis_checkbox is None")

    def build_physiboss_info(self):
        config_file = self.run_tab.config_xml_name.text()
        print("build_physiboss_info(): get_cell_types():  config_file=",config_file)
        basename = os.path.basename(config_file)
        print("get_cell_types():  basename=",basename)
        # out_config_file = os.path.join(self.output_dir, basename)
        out_config_file = config_file
        print("get_cell_types():  out_config_file=",out_config_file)

        try:
            self.tree = ET.parse(out_config_file)
            self.xml_root = self.tree.getroot()
        except:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("build_physiboss_info(): Error opening or parsing " + out_config_file)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return False

        
        # tree = ET.parse(Path(self.config_path))
        # xml_root = tree.getroot()
        cell_defs = self.xml_root.find(".//cell_definitions")
        self.physiboss_node_dict.clear()
        
        if cell_defs is not None:
            for cell_def in cell_defs:
                intracellular = cell_def.find("phenotype//intracellular")
                
                if intracellular is not None and intracellular.get("type").lower() == "maboss":
                    self.physiboss_node_dict[cell_def.get("name")] = []
                    bnd_filename = intracellular.find("bnd_filename").text
                    
                    list_nodes = []
                    full_fname = os.path.join(os.getcwd(), bnd_filename)
                    try:
                        # with open(os.path.join(os.getcwd(), bnd_filename), "r") as bnd_file:
                        with open(full_fname, "r") as bnd_file:
                            for line in bnd_file.readlines():        
                                if line.strip().lower().startswith("node"):
                                    node = line.strip().split(" ")[1]
                                    list_nodes.append(node)
                    except:
                        print("vis_tab:  ERROR opening/reading ",full_fname)
                        msgBox = QMessageBox()
                        msgBox.setIcon(QMessageBox.Information)
                        msgBox.setText("Cannot open or read " + full_fname)
                        msgBox.setStandardButtons(QMessageBox.Ok)
                        msgBox.exec()
                        return


                    cfg_filename = intracellular.find("cfg_filename").text
                    list_internal_nodes = []
                    with open(os.path.join(os.getcwd(), cfg_filename), "r") as cfg_file:
                        for line in cfg_file.readlines():        
                            if "is_internal" in line:
                                tokens = line.split("=")
                                value = tokens[1].strip()[:-1].lower() in ["1", "true"]
                                node = tokens[0].strip().replace(".is_internal", "")
                                if value:
                                    list_internal_nodes.append(node)

                    list_output_nodes = list(set(list_nodes).difference(set(list_internal_nodes)))
                    self.physiboss_node_dict[cell_def.get("name")] = list_output_nodes

          
        if len(self.physiboss_node_dict) > 0:
            self.physiboss_vis_show()
            self.fill_physiboss_cell_types_combobox(list(self.physiboss_node_dict.keys()))
            self.fill_physiboss_nodes_combobox(self.physiboss_node_dict[list(self.physiboss_node_dict.keys())[0]])
        else:
            self.physiboss_vis_hide()
            
            
    def physiboss_vis_show(self):

        if self.physiboss_vis_checkbox is None:
                
            self.physiboss_qline = QHLine()
            self.vbox.addWidget(self.physiboss_qline)
            
            self.physiboss_hbox_1 = QHBoxLayout()
            
            self.physiboss_vis_checkbox = QCheckBox('Color by PhysiBoSS node state')
            self.physiboss_vis_flag = False
            self.physiboss_vis_checkbox.setEnabled(not self.plot_cells_svg)
            self.physiboss_vis_checkbox.setChecked(self.physiboss_vis_flag)
            self.physiboss_vis_checkbox.clicked.connect(self.physiboss_vis_toggle_cb)
            self.physiboss_hbox_1.addWidget(self.physiboss_vis_checkbox)
            
            self.vbox.addLayout(self.physiboss_hbox_1)
            
            self.physiboss_hbox_2 = QHBoxLayout()

            self.physiboss_cell_type_combobox = QComboBox()
            self.physiboss_cell_type_combobox.setEnabled(False)
            self.physiboss_cell_type_combobox.currentIndexChanged.connect(self.physiboss_vis_cell_type_cb)
            self.physiboss_node_combobox = QComboBox()
            self.physiboss_node_combobox.setEnabled(False)
            self.physiboss_node_combobox.currentIndexChanged.connect(self.physiboss_vis_node_cb)
            self.physiboss_hbox_2.addWidget(self.physiboss_cell_type_combobox)
            self.physiboss_hbox_2.addWidget(self.physiboss_node_combobox)

            self.vbox.addLayout(self.physiboss_hbox_2)
        
    def physiboss_vis_hide(self):
        print("\n--------- physiboss_vis_hide()")

        if self.physiboss_vis_checkbox is not None:
            self.physiboss_vis_checkbox.disconnect()
            self.physiboss_cell_type_combobox.disconnect()
            self.physiboss_node_combobox.disconnect()
            self.physiboss_qline.deleteLater()
            
            self.physiboss_vis_checkbox.deleteLater()
            self.physiboss_hbox_1.deleteLater()

            self.physiboss_cell_type_combobox.deleteLater()
            self.physiboss_node_combobox.deleteLater()

            self.physiboss_hbox_2.deleteLater()

    def fill_physiboss_cell_types_combobox(self, cell_types):
        self.physiboss_cell_type_combobox.clear()
        for s in cell_types:
            self.physiboss_cell_type_combobox.addItem(s)
        self.physiboss_selected_cell_line = 0
    
    def fill_physiboss_nodes_combobox(self, nodes):
        self.physiboss_node_combobox.clear()
        for s in nodes:
            self.physiboss_node_combobox.addItem(s)

    def physiboss_vis_toggle_cb(self, bval):
        self.physiboss_vis_flag = bval
        self.physiboss_cell_type_combobox.setEnabled(bval)
        self.physiboss_node_combobox.setEnabled(bval)
        self.cell_scalar_combobox.setEnabled(not bval)
        self.cell_scalar_cbar_combobox.setEnabled(not bval)
        self.update_plots()
        
    def physiboss_vis_cell_type_cb(self, idx):
        if idx > 0:
            self.fill_physiboss_nodes_combobox(self.physiboss_node_dict[list(self.physiboss_node_dict.keys())[idx]])
            self.physiboss_selected_cell_line = idx
            self.update_plots()
            
    def physiboss_vis_node_cb(self, idx):
        self.physiboss_selected_node = self.physiboss_node_dict[list(self.physiboss_node_dict.keys())[self.physiboss_selected_cell_line]][idx]
        self.update_plots()
        
    def output_folder_cb(self):
        print(f"output_folder_cb(): old={self.output_dir}")
        self.output_dir = self.output_folder.text()
        print(f"                    new={self.output_dir}")
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
            # self.vis_tab.update_output_dir(dir_path)
            # self.output_dir(dir_path)
            self.output_dir = dir_path
            self.output_folder.setText(dir_path)
            self.legend_tab.output_dir = dir_path
            legend_file = os.path.join(self.output_dir, 'legend.svg')  # hardcoded filename :(
            if Path(legend_file).is_file():
                self.legend_tab.reload_legend()
            else:
                self.legend_tab.clear_legend()

            self.reset_model()
            self.update_plots()

        else:
            print("vis_tab: output_folder_cb():  full_path_model_name is NOT valid")

    def cells_svg_mat_cb(self):
        radioBtn = self.sender()
        if "svg" in radioBtn.text():
            self.plot_cells_svg = True
            self.custom_button.setEnabled(False)
            self.cell_scalar_combobox.setEnabled(False)
            self.cell_scalar_cbar_combobox.setEnabled(False)
            if self.physiboss_vis_checkbox is not None:
                self.physiboss_vis_checkbox.setEnabled(False)
            # self.fix_cmap_checkbox.setEnabled(bval)

            if self.cax2:
                self.cax2.remove()
                self.cax2 = None

        else:
            self.plot_cells_svg = False
            self.custom_button.setEnabled(True)
            self.cell_scalar_combobox.setEnabled(True)
            self.cell_scalar_cbar_combobox.setEnabled(True)
            if self.physiboss_vis_checkbox is not None:
                self.physiboss_vis_checkbox.setEnabled(True)
        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()


    def update_output_dir(self, dir_path):
        if os.path.isdir(dir_path):
            print("update_output_dir(): yes, it is a dir path", dir_path)
        else:
            print("update_output_dir(): NO, it is NOT a dir path", dir_path)
        self.output_dir = dir_path
        self.output_folder.setText(dir_path)

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
            print("-------- reset_plot_range(): plot_ymin,ymax=  ",self.plot_ymin,self.plot_ymax)
        except:
            pass

        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()


    def show_hide_plot_range(self):
        # print("vis_tab: show_hide_plot_range()")
        print('self.stackw.count()=', self.stackw.count())
        # print('self.show_plot_range= ',self.show_plot_range)
        # print(" # items = ",self.layout.num_items())
        # item = self.layout.itemAt(1)
        # print('item= ',item)

        self.show_plot_range = not self.show_plot_range
        # print('self.show_plot_range= ',self.show_plot_range)
        if self.show_plot_range:
            # self.layout.addWidget(self.controls2)
            # self.controls2.setVisible(True)
            # self.stackw.setCurrentIndex(1)
            # self.stackw.setFixedHeight(80)
            pass
        else:
            self.stackw.setCurrentIndex(0)
            # self.stackw.setFixedHeight(40)
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
        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()

    def cmin_cmax_cb(self):
        # print("----- cmin_cmax_cb:")
        try:  # due to the initial callback
            self.cmin_value = float(self.cmin.text())
            self.cmax_value = float(self.cmax.text())
            self.fixed_contour_levels = MaxNLocator(nbins=self.num_contours).tick_values(self.cmin_value, self.cmax_value)
        except:
            pass
        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()

    def init_plot_range(self, config_tab):
        # print("----- init_plot_range:")
        try:
            # beware of widget callback 
            self.my_xmin.setText(config_tab.xmin.text())
            self.my_xmax.setText(config_tab.xmax.text())
            self.my_ymin.setText(config_tab.ymin.text())
            self.my_ymax.setText(config_tab.ymax.text())
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

        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()

    def update_plots(self):
        self.ax0.cla()
        if self.substrates_checked_flag:  # do first so cells are plotted on top
            self.plot_substrate(self.current_svg_frame)
        if self.cells_checked_flag:
            if self.plot_cells_svg:
                self.plot_svg(self.current_svg_frame)
            else:
                self.plot_cell_scalar(self.current_svg_frame)

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

    def colorbar_combobox_changed_cb(self,idx):
        self.update_plots()

    def substrates_combobox_changed_cb(self,idx):
        # print("----- vis_tab.py: substrates_combobox_changed_cb: idx = ",idx)
        self.field_index = 4 + idx # substrate (0th -> 4 in the .mat)
        self.substrate_name = self.substrates_combobox.currentText()
        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()


    def open_directory_cb(self):
        dialog = QFileDialog()
        # self.output_dir = dialog.getExistingDirectory(self, 'Select an output directory')
        tmp_dir = dialog.getExistingDirectory(self, 'Select an output directory')
        # print("vis_tab.py: open_directory_cb:  tmp_dir=",tmp_dir)
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
            print("vis_tab:reset_model(): Warning: Expecting initial.xml, but does not exist.")
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
        # print('reset_model(): self.xmin, xmax=',self.xmin, self.xmax)
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
            print("Expecting initial.xml, but does not exist.")
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
        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()

    def last_plot_cb(self, text):
        if self.reset_model_flag:
            self.reset_model()
            self.reset_model_flag = False

        # WARNING: do not assume we're in /tmpdir (as )
        # print('vis_tab.py: cwd = ',os.getcwd())
        # print('self.output_dir = ',self.output_dir)
        # xml_file = Path(self.output_dir, "initial.xml")
        # xml_files = glob.glob('tmpdir/output*.xml')

        # stop the insanity (dir structure on nanoHUB vs. local)
        # xml_pattern = "output*.xml"
        xml_pattern = self.output_dir + "/" + "output*.xml"
        xml_files = glob.glob(xml_pattern)
        num_xml = len(xml_files)
        if num_xml == 0:
            print("last_plot_cb(): WARNING: no output*.xml files present")
            return

        xml_files.sort()
        # print('last_plot_cb():xml_files (after sort)= ',xml_files)

        # svg_pattern = "snapshot*.svg"
        svg_pattern = self.output_dir + "/" + "snapshot*.svg"
        svg_files = glob.glob(svg_pattern)   # rwh: problematic with celltypes3 due to snapshot_standard*.svg and snapshot<8digits>.svg
        svg_files.sort()
        # print('last_plot_cb(): svg_files (after sort)= ',svg_files)
        num_xml = len(xml_files)
        # print('svg_files = ',svg_files)
        num_svg = len(svg_files)
        # print('num_xml, num_svg = ',num_xml, num_svg)
        last_xml = int(xml_files[-1][-12:-4])
        last_svg = int(svg_files[-1][-12:-4])
        # print('last_xml, _svg = ',last_xml,last_svg)
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
        print('back_plot_cb(): svg # ',self.current_svg_frame)

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
                # print("play_plot_cb():  Reached the end (or no output files found).")
                # self.timer.stop()
                self.current_svg_frame -= 1
                self.animating_flag = True
                # self.current_svg_frame = 0
                self.animate()
                return

            self.update_plots()

    #----- View menu items
    def view_aspect_toggle_cb(self,bval):
        self.view_aspect_square = bval
        print("vis_tab.py: self.view_aspect_square = ",self.view_aspect_square)
        self.update_plots()

    def shading_toggle_cb(self,bval):
        if bval:
            self.shading_choice = 'gouraud'  # 'auto'(was 'flat') vs. 'gouraud' (smooth)
        else:
            self.shading_choice = 'auto'  # 'auto'(was 'flat') vs. 'gouraud' (smooth)
        self.update_plots()

    def voxel_grid_toggle_cb(self,bval):
        self.show_voxel_grid = bval
        self.update_plots()

    def mechanics_grid_toggle_cb(self,bval):
        self.show_mechanics_grid = bval
        self.update_plots()

    #----------------------------------------------
    def cells_toggle_cb(self,bval):
        self.cells_checked_flag = bval
        self.cells_svg_rb.setEnabled(bval)
        self.cells_mat_rb.setEnabled(bval)
        self.cells_edge_checkbox.setEnabled(bval)

        if not self.cells_checked_flag:
            self.cell_scalar_combobox.setEnabled(False)
            if self.cax2:
                try:
                    self.cax2.remove()
                    self.cax2 = None
                except:
                    pass
            
        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()

    def cells_edge_toggle_cb(self,bval):
        self.cells_edge_checked_flag = bval
        self.update_plots()


    def substrates_toggle_cb(self,bval):
        self.substrates_checked_flag = bval
        self.fix_cmap_checkbox.setEnabled(bval)
        self.cmin.setEnabled(bval)
        self.cmax.setEnabled(bval)
        self.substrates_combobox.setEnabled(bval)
        self.substrates_cbar_combobox.setEnabled(bval)

        # if self.view_shading:
        #     self.view_shading.setEnabled(bval)

        if not self.substrates_checked_flag:
            if self.cax1:
                self.cax1.remove()
                self.cax1 = None

        if not self.plot_xmin:
            self.reset_plot_range()
        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()

    def fix_cmap_toggle_cb(self,bval):
        # print("fix_cmap_toggle_cb():")
        self.fix_cmap_flag = bval
        self.cmin.setEnabled(bval)
        self.cmax.setEnabled(bval)

            # self.substrates_combobox.addItem(s)
        # field_name = self.field_dict[self.substrate_choice.value]
        # print("self.field_dict= ",self.field_dict)
        # field_name = self.field_dict[self.substrates_combobox.currentText()]
        field_name = self.substrates_combobox.currentText()
        # print("field_name= ",field_name)
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

        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()


    def add_default_cell_vars(self):
        self.disable_cell_scalar_cb = True
        self.cell_scalar_combobox.clear()
        default_var_l = ["pressure", "total_volume", "current_phase", "cell_type", "damage"]
        for idx in range(len(default_var_l)):
            self.cell_scalar_combobox.addItem(default_var_l[idx])
        self.cell_scalar_combobox.insertSeparator(len(default_var_l))

    def append_custom_cb(self):
        self.add_default_cell_vars()

        # Add all custom vars. Hack.
        xml_file_root = "output%08d.xml" % 0
        xml_file = os.path.join(self.output_dir, xml_file_root)
        if not Path(xml_file).is_file():
            print("append_custom_cb(): ERROR: file not found",xml_file)
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Could not find file " + xml_file)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return

        mcds = pyMCDS(xml_file_root, self.output_dir, microenv=False, graph=False, verbose=False)

        # # cell_scalar = mcds.get_cell_df()[cell_scalar_name]
        num_keys = len(mcds.data['discrete_cells']['data'].keys())
        # print("plot_tab: append_custom_cb(): num_keys=",num_keys)
        keys_l = list(mcds.data['discrete_cells']['data'])
        # print("plot_tab: append_custom_cb(): keys_l=",keys_l)
        for idx in range(num_keys-1,0,-1):
            if "transformation_rates" in keys_l[idx]:
                # print("found transformation_rates at index=",idx)
                break
        idx1 = idx + 1

        for idx in range(idx1, len(keys_l)):
            # print("------ add: ",keys_l[idx])
            self.cell_scalar_combobox.addItem(keys_l[idx])

        self.disable_cell_scalar_cb = False

        self.update_plots()

    def animate(self):
        if not self.animating_flag:
            self.animating_flag = True
            self.play_button.setText("Pause")
            # self.play_button.setStyleSheet("QPushButton {background-color: red; color: black;}")

            if self.reset_model_flag:
                self.reset_model()
                self.reset_model_flag = False

            # self.current_svg_frame = 0
            self.timer.start(1)

        else:
            self.animating_flag = False
            self.play_button.setText("Play")
            # self.play_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
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
        print('\n\n   ====>     prepare_plot_cb(): svg # ',self.current_svg_frame)

        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()


    def create_figure(self):
        print("\n--------- create_figure(): ------- creating figure, canvas, ax0")
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

        print("create_figure(): ------- creating dummy contourf")
        xlist = np.linspace(-3.0, 3.0, 50)
        print("len(xlist)=",len(xlist))
        ylist = np.linspace(-3.0, 3.0, 50)
        X, Y = np.meshgrid(xlist, ylist)
        Z = np.sqrt(X**2 + Y**2) + 10*np.random.rand()

        cbar_name = self.substrates_cbar_combobox.currentText()
        # self.cmap = plt.cm.get_cmap(cbar_name)  # e.g., 'viridis'
        # self.mysubstrate = self.ax0.contourf(X, Y, Z, cmap=self.cmap)
        self.mysubstrate = self.ax0.contourf(X, Y, Z, cmap=cbar_name)
        # if self.field_index > 4:
        #     # plt.contour(xgrid, ygrid, M[self.field_index, :].reshape(self.numy,self.numx), [0.0])
        #     plt.contour(X, Y, Z, [0.0])

        # levels = MaxNLocator(nbins=self.num_contours).tick_values(self.cmin_value, self.cmax_value)

#rwh - not for this demo
        # self.cbar = self.figure.colorbar(self.mysubstrate, ax=self.ax0)
        # self.cbar.ax.tick_params(labelsize=self.fontsize)

        # substrate_plot = self.ax0.contourf(xgrid, ygrid, M[self.field_index, :].reshape(self.numy,self.numx), num_contours, cmap='viridis')  # self.colormap_dd.value)

        print("------------create_figure():  # axes = ",len(self.figure.axes))

        # self.imageInit = [[255] * 320 for i in range(240)]
        # self.imageInit[0][0] = 0

        # Init image and add colorbar
        # self.image = self.ax0.imshow(self.imageInit, interpolation='none')
        # divider = make_axes_locatable(self.ax0)
        # cax = divider.new_vertical(size="5%", pad=0.05, pack_start=True)
        # self.colorbar = self.figure.add_axes(cax)
        # self.figure.colorbar(self.image, cax=cax, orientation='horizontal')

        # plt.subplots_adjust(left=0, bottom=0.05, right=1, top=1, wspace=0, hspace=0)

        # self.plot_substrate(self.current_svg_frame)
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
            # print("--- circles(): type(c)=",type(c))
            c = c.values
            # print("--- circles() (2): type(c)=",type(c))

            # print("--- circles(): c=",c)
            c = np.broadcast_to(c, zipped.shape).ravel()
            collection.set_array(c)
            # print("--- circles(): vmin,vmax=",vmin,vmax)
            collection.set_clim(vmin, vmax)

        # ax = plt.gca()
        # ax.add_collection(collection)
        # ax.autoscale_view()
        self.ax0.add_collection(collection)
        self.ax0.autoscale_view()
        plt.draw_if_interactive()
        # if c is not None:
        #     try:
        #         print("------ circles(): doing plt.sci(collection), type(collection)=",type(collection))
        #         plt.sci(collection)
        #         # self.ax0.sci(collection)
        #         # self.ax0.sci(collection)
        #     except:
        #         print("--- ERROR in circles() doing plt.sci(collection)")
        return collection

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
            mcds = pyMCDS_cells(fname, self.output_dir)
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
            print("plot_vecs(): ERROR")
            pass

    #------------------------------------------------------------
    # This is primarily used for debugging.
    def plot_voxel_grid(self):
        # print("--------- plot_voxel_grid()")
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
    def plot_mechanics_grid(self):
        numx = int((self.xmax - self.xmin)/self.mech_voxel_size)
        numy = int((self.ymax - self.ymin)/self.mech_voxel_size)
        xs = np.linspace(self.xmin,self.xmax, numx)
        ys = np.linspace(self.ymin,self.ymax, numy)
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
    # def plot_svg(self, frame, rdel=''):
    def plot_svg(self, frame):
        # global current_idx, axes_max
        # global current_frame

        # return

        if self.show_voxel_grid:
            self.plot_voxel_grid()
        if self.show_mechanics_grid:
            self.plot_mechanics_grid()

        # if self.show_vectors:
        #     self.plot_vecs()

        # current_frame = frame
        # self.current_frame = frame
        fname = "snapshot%08d.svg" % frame
        full_fname = os.path.join(self.output_dir, fname)
        # print("-- plot_svg(): full_fname= ",full_fname)
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
            print("vis_tab.py: plot_svg(): Warning: full_fname not found: ",full_fname)
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
        except:
            print("------ plot_svg(): error trying to parse ",full_name)
            return
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
                self.title_str += svals[2] + " days, " + svals[4] + " hrs, " + svals[7][:-3] + " mins"

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
                    print("bogus xval=", xval)
                    break
                yval = float(circle.attrib['cy'])
                # yval = (yval - self.svg_xmin)/self.svg_xrange * self.y_range + self.ymin
                yval = yval/self.y_range * self.y_range + self.ymin
                if (np.fabs(yval) > too_large_val):
                    print("bogus yval=", yval)
                    break

                rval = float(circle.attrib['r'])
                # if (rgb[0] > rgb[1]):
                #     print(num_cells,rgb, rval)
                xlist.append(xval)
                ylist.append(yval)
                rlist.append(rval)
                rgba_list.append(rgba)

                # For .svg files with cells that *have* a nucleus, there will be a 2nd
                if (not self.show_nucleus):
                #if (not self.show_nucleus):
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
                self.circles(xvals,yvals, s=rvals, color=rgbas,  edgecolor='black', linewidth=0.5)
                # cell_circles = self.circles(xvals,yvals, s=rvals, color=rgbs, edgecolor='black', linewidth=0.5)
                # plt.sci(cell_circles)
            except (ValueError):
                pass
        else:
            # plt.scatter(xvals,yvals, s=markers_size, c=rgbs)
            # self.circles(xvals,yvals, s=rvals, color=rgbas, alpha=self.alpha)
            # print("--- plotting circles without edges!!")
            self.circles(xvals,yvals, s=rvals, color=rgbas )

        if self.view_aspect_square:
            self.ax0.set_aspect('equal')
        else:
            self.ax0.set_aspect('auto')
            
        names_observed = ["Active", "Inactive", "Other cell type"]
        boolean_colors = ["green", "red", "grey"]
        
        # Creating empty plots to add the legend
        lp = lambda i: plt.plot([],color=boolean_colors[i], ms=np.sqrt(81), mec="none",
                                label="Feature {:g}".format(i), ls="", marker="o")[0]
        handles = [lp(i) for i in range(3)]
        self.ax0.legend(handles=handles,labels=names_observed, loc='upper center', bbox_to_anchor=(0.5, -0.15),ncols=4)
    
    #-----------------------------------------------------
    def plot_cell_scalar(self, frame):

        if self.disable_cell_scalar_cb:
            return
            
        if self.show_voxel_grid:
            self.plot_voxel_grid()
        if self.show_mechanics_grid:
            self.plot_mechanics_grid()


        xml_file_root = "output%08d.xml" % frame
        xml_file = os.path.join(self.output_dir, xml_file_root)
        # xml_file = os.path.join("tmpdir", xml_file_root)  # temporary hack
        cell_scalar_name = self.cell_scalar_combobox.currentText()
        cbar_name = self.cell_scalar_cbar_combobox.currentText()
        # print(f"\n\n   >>>>--------- plot_cell_scalar(): xml_file={xml_file}, scalar={cell_scalar_name}, cbar={cbar_name}")
        if not Path(xml_file).is_file():
            print("ERROR: file not found",xml_file)
            return

        #   if (os.path.isfile(fname) == False):
        #     print("File does not exist: ",fname)
        #     return

        # mcds = pyMCDS(fname, '../tmpdir', microenv=False, graph=False, verbose=True)
        # temporary hack to debug plotting without doing Run first
        # mcds = pyMCDS(xml_file_root, self.output_dir, microenv=False, graph=False, verbose=True)
        mcds = pyMCDS(xml_file_root, self.output_dir, microenv=False, graph=False, verbose=False)
        # mcds = pyMCDS(xml_file_root, "tmpdir", microenv=False, graph=False, verbose=True)
        total_min = mcds.get_time()
        # print("    time=",total_min)
        
        if self.physiboss_vis_flag:
            try:
                cell_types = mcds.get_cell_df()["cell_type"]
            except:
                print("vis_tab.py: plot_cell_scalar(): error performing mcds.get_cell_df()['cell_type']")
                return
            
            physiboss_state_file = os.path.join(self.output_dir, "states_%08d.csv" % frame)
            
            if not Path(physiboss_state_file).is_file():
                print("vis_tab.py: plot_cell_scalar(): error file not found ",physiboss_state_file)
                return
            
            cell_scalar = {}
            with open(physiboss_state_file, newline='') as csvfile:
                states_reader = csv.reader(csvfile, delimiter=',')
                    
                for row in states_reader:
                    if row[0] != 'ID':
                        ID = int(row[0])
                        if cell_types[ID] == self.physiboss_selected_cell_line:
                            nodes = row[1].split(" -- ")                      
                            if self.physiboss_selected_node in nodes:
                                cell_scalar.update({ID: 2})      
                            else:
                                cell_scalar.update({ID: 0})
                        else:
                            cell_scalar.update({ID: 9})
                            
            cell_scalar = pandas.Series(cell_scalar)
            
            # To plot green/red/grey cells, we use a qualitative cell map called Set1
            cbar_name = "Set1"
            vmin = 0
            vmax = 9
            
        else:
            try:
                cell_scalar = mcds.get_cell_df()[cell_scalar_name]
            except:
                print("vis_tab.py: plot_cell_scalar(): error performing mcds.get_cell_df()[cell_scalar_name]")
                return
        
            vmin = cell_scalar.min()
            vmax = cell_scalar.max()
            
        num_cells = len(cell_scalar)
        # print("  len(cell_scalar) = ",len(cell_scalar))
        # fix_cmap = 0
        # print(f'   cell_scalar.min(), max() = {vmin}, {vmax}')
        cell_vol = mcds.get_cell_df()['total_volume']
        # print(f'   cell_vol.min(), max() = {cell_vol.min()}, {cell_vol.max()}')

        four_thirds_pi =  4.188790204786391
        cell_radii = np.divide(cell_vol, four_thirds_pi)
        cell_radii = np.power(cell_radii, 0.333333333333333333333333333333333333333)

        xvals = mcds.get_cell_df()['position_x']
        yvals = mcds.get_cell_df()['position_y']

        # self.title_str += "   cells: " + svals[2] + "d, " + svals[4] + "h, " + svals[7][:-3] + "m"
        # self.title_str = "(" + str(frame) + ") Current time: " + str(total_min) + "m"

        mins = total_min
        hrs = int(mins/60)
        days = int(hrs/24)
        self.title_str = '%d days, %d hrs, %d mins' % (days, hrs-days*24, mins-hrs*60)
        self.title_str += " (" + str(num_cells) + " agents)"

        axes_min = mcds.get_mesh()[0][0][0][0]
        axes_max = mcds.get_mesh()[0][0][-1][0]

        if (self.cells_edge_checked_flag):
            try:
                cell_plot = self.circles(xvals,yvals, s=cell_radii, c=cell_scalar, edgecolor='black', linewidth=0.5, cmap=cbar_name, vmin=vmin, vmax=vmax)
            except (ValueError):
                print("\n------ ERROR: Exception from circles with edges\n")
                pass
        else:
            cell_plot = self.circles(xvals,yvals, s=cell_radii, c=cell_scalar, cmap=cbar_name)

        # print("------- plot_cell_scalar() -------------")
        num_axes =  len(self.figure.axes)
        # print("# axes = ",num_axes)
        # if num_axes > 1: 
        # if self.axis_id_cellscalar:
        if not self.physiboss_vis_flag:
            if self.cax2:
                try:
                    self.cax2.remove()
                except:
                    pass
                # print("# axes(after cell_scalar remove) = ",len(self.figure.axes))
                # print(" self.figure.axes= ",self.figure.axes)
                #ppp
                ax2_divider = make_axes_locatable(self.ax0)
                self.cax2 = ax2_divider.append_axes("bottom", size="4%", pad="8%")
                self.cbar2 = self.figure.colorbar(cell_plot, cax=self.cax2, orientation="horizontal")
                # print("\n# axes(redraw cell_scalar) = ",len(self.figure.axes))
                # print(" self.figure.axes= ",self.figure.axes)
                # self.axis_id_cellscalar = len(self.figure.axes) - 1
                self.cbar2.ax.tick_params(labelsize=self.fontsize)
                self.cbar2.ax.set_xlabel(cell_scalar_name)
            else:
                ax2_divider = make_axes_locatable(self.ax0)
                self.cax2 = ax2_divider.append_axes("bottom", size="4%", pad="8%")
                self.cbar2 = self.figure.colorbar(cell_plot, cax=self.cax2, orientation="horizontal")
                self.cbar2.ax.tick_params(labelsize=self.fontsize)
                # print(" self.figure.axes= ",self.figure.axes)
                self.cbar2.ax.set_xlabel(cell_scalar_name)
        
        elif self.cax2:
            try:
                    self.cax2.remove()
            except:
                pass
                
        self.ax0.set_title(self.title_str, fontsize=self.title_fontsize)
        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)

        if self.view_aspect_square:
            self.ax0.set_aspect('equal')
        else:
            self.ax0.set_aspect('auto')

    #------------------------------------------------------------
    def plot_substrate(self, frame):

        # f=1/0  # force segfault
        xml_file_root = "output%08d.xml" % frame
        xml_file = os.path.join(self.output_dir, xml_file_root)
        if not Path(xml_file).is_file():
            print("ERROR: file not found",xml_file)
            return

        cbar_name = self.substrates_cbar_combobox.currentText()

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
        # print("\n    ==>>>>> plot_substrate(): full_fname=",full_fname)
        if not Path(full_fname).is_file():
            print("ERROR: file not found",full_fname)
            return

        info_dict = {}
        scipy.io.loadmat(full_fname, info_dict)
        M = info_dict['multiscale_microenvironment']
        # print('plot_substrate: self.field_index=',self.field_index)

        # debug
        # fsub = M[self.field_index,:]   # 
        # print("substrate min,max=",fsub.min(), fsub.max())

        # print("M.shape = ",M.shape)  # e.g.,  (6, 421875)  (where 421875=75*75*75)
        # numx = int(M.shape[1] ** (1./3) + 1)
        # numy = numx
        # self.numx = 50  # for template model
        # self.numy = 50
        # self.numx = 88  # for kidney model
        # self.numy = 75

        # try:
        #     print("plot_substrate(): self.numx, self.numy = ",self.numx, self.numy )
        # except:
        #     print("Error: self.numx, self.numy not defined.")
        #     return
        # nxny = numx * numy

        try:
            xgrid = M[0, :].reshape(self.numy, self.numx)
            ygrid = M[1, :].reshape(self.numy, self.numx)
        except:
            # print("error: cannot reshape ",self.numy, self.numx," for array ",M.shape)
            print("vis_tab.py: unable to reshape substrate array; return")
            return

        zvals = M[self.field_index,:].reshape(self.numy,self.numx)
        # print("zvals.min() = ",zvals.min())
        # print("zvals.max() = ",zvals.max())

        # self.num_contours = 15

        # if (self.colormap_fixed_toggle.value):
        #     try:
        #         # vmin = 0
        #         # vmax = 10
        #         # levels = MaxNLocator(nbins=30).tick_values(vmin, vmax)
        #         num_contours = 15
        #         levels = MaxNLocator(nbins=num_contours).tick_values(self.colormap_min.value, self.colormap_max.value)
        #         substrate_plot = self.ax0.contourf(xgrid, ygrid, M[self.field_index, :].reshape(self.numy, self.numx), levels=levels, extend='both', cmap=self.colormap_dd.value, fontsize=self.fontsize)
        #     except:
        #         contour_ok = False
        #         # print('got error on contourf 1.')
        # else:    
        #     try:
        #         substrate_plot = self.ax0.contourf(xgrid, ygrid, M[self.field_index, :].reshape(self.numy,self.numx), num_contours, cmap=self.colormap_dd.value)
        #     except:
        #         contour_ok = False
        #             # print('got error on contourf 2.')

        contour_ok = True
        # if (self.colormap_fixed_toggle.value):
        # self.field_index = 4

        if (self.fix_cmap_flag):
            try:
                # self.fixed_contour_levels = MaxNLocator(nbins=self.num_contours).tick_values(self.cmin_value, self.cmax_value)
                # substrate_plot = self.ax0.contourf(xgrid, ygrid, M[self.field_index, :].reshape(self.numy, self.numx), levels=levels, extend='both', cmap=self.colormap_dd.value, fontsize=self.fontsize)
                # substrate_plot = self.ax0.contourf(xgrid, ygrid, zvals, self.num_contours, levels=self.fixed_contour_levels, extend='both', cmap=cbar_name)
                substrate_plot = self.ax0.pcolormesh(xgrid,ygrid, zvals, shading=self.shading_choice, cmap=cbar_name, vmin=self.cmin_value, vmax=self.cmax_value)
            except:
                contour_ok = False
                print('\nWARNING: exception with fixed colormap range. Will not update plot.')
        else:    
            try:
                # substrate_plot = self.ax0.contourf(xgrid, ygrid, zvals, self.num_contours, cmap=cbar_name)  # self.colormap_dd.value)
                substrate_plot = self.ax0.pcolormesh(xgrid,ygrid, zvals, shading=self.shading_choice, cmap=cbar_name) #, vmin=Z.min(), vmax=Z.max())
            except:
                contour_ok = False
                print('\nWARNING: exception with dynamic colormap range. Will not update plot.')

        # in case we want to plot a "0.0" contour line
        # if self.field_index > 4:
        #     self.ax0.contour(xgrid, ygrid, M[self.field_index, :].reshape(self.numy,self.numx), [0.0], linewidths=0.5)

        # Do this funky stuff to prevent the colorbar from shrinking in height with each redraw.
        # Except it doesn't seem to work when we use fixed ranges on the colorbar?!
        # print("------- plot_substrate() -------------")
        num_axes =  len(self.figure.axes)
        # print("# axes = ",num_axes)
        if self.cax1:
            self.cax1.remove()  # replace/update the colorbar
            # print("# axes(after substrate remove) = ",len(self.figure.axes))
            # print(" self.figure.axes= ",self.figure.axes)
            #ppp
            ax1_divider = make_axes_locatable(self.ax0)
            self.cax1 = ax1_divider.append_axes("right", size="4%", pad="2%")
            self.cbar1 = self.figure.colorbar(substrate_plot, cax=self.cax1)
            # print("\n# axes(redraw substrate) = ",len(self.figure.axes))
            # print(" self.figure.axes= ",self.figure.axes)
            self.cbar1.ax.tick_params(labelsize=self.fontsize)
        else:
            ax1_divider = make_axes_locatable(self.ax0)
            self.cax1 = ax1_divider.append_axes("right", size="4%", pad="2%")
            self.cbar1 = self.figure.colorbar(substrate_plot, cax=self.cax1)
            self.cbar1.ax.tick_params(labelsize=self.fontsize)
            # print("(init substrate) self.figure.axes= ",self.figure.axes)

        self.cbar1.set_label(self.substrate_name)
        self.ax0.set_title(self.title_str, fontsize=self.title_fontsize)
        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)

        if self.view_aspect_square:
            self.ax0.set_aspect('equal')
        else:
            self.ax0.set_aspect('auto')
