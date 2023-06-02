"""
vis_base.py - parent class of shared variables and methods for both vis 2D and 3D modules.

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
# import matplotlib.colors as mplc
from matplotlib.colors import BoundaryNorm, rgb2hex
from matplotlib.ticker import MaxNLocator
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle, Ellipse, Rectangle
from matplotlib.collections import PatchCollection
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable
from matplotlib import gridspec
from collections import deque
import glob
import csv
import pandas

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QGroupBox, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,  QMainWindow,QGridLayout, QPushButton, QFileDialog, QMessageBox, QStackedWidget, QSplitter
from PyQt5.QtWidgets import QCompleter, QSizePolicy
from PyQt5.QtCore import QSortFilterProxyModel
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QRectF, Qt
locale_en_US = QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates)

import numpy as np
import scipy.io
# from pyMCDS_cells import pyMCDS_cells 
from pyMCDS import pyMCDS
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

# from PyQt5 import QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
# from matplotlib.figure import Figure

try:
    from simulariumio import UnitData, MetaData, DisplayData, DISPLAY_TYPE, ModelMetaData
    from simulariumio.physicell import PhysicellConverter, PhysicellData
    simularium_installed = True
except:
    simularium_installed = False

from filters3D import FilterUI3DWindow
from filters2D import FilterUI2DWindow

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

#---------------------------
class ExtendedComboBox(QComboBox):
    def __init__(self, parent=None):
        super(ExtendedComboBox, self).__init__(parent)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)  # necessary to use lineEdit().textEdited filter below; can't be False

        # add a filter model to filter matching items
        self.pFilterModel = QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

        # add a completer, which uses the filter model
        self.completer = QCompleter(self.pFilterModel, self)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)

        # connect signals
        self.lineEdit().textEdited.connect(self.pFilterModel.setFilterFixedString)  # necessary to show filtered items
        self.completer.activated.connect(self.on_completer_activated)


    # Tried/failed to override this method to avoid adding a bogus variable name in search bar at top of combobox
    # def addItem(self, text):
    #     print("addItem():  avoid adding text=",text)
        # items = [self.itemText(i) for i in range(self.count())]  # argh, there's really no method for this?
            # super().addItem(text)

    # on selection of an item from the completer, select the corresponding item from combobox 
    def on_completer_activated(self, text):
        print("\n--- on_completer_activated():  text= ",text)
        if text:
            index = self.findText(text)
            print("on_completer_activated(): index= ",index)
            self.setCurrentIndex(index)
            self.activated[str].emit(self.itemText(index))


    # on model change, update the models of the filter and completer as well 
    # def setModel(self, model):
    #     super(ExtendedComboBox, self).setModel(model)
    #     self.pFilterModel.setSourceModel(model)
    #     self.completer.setModel(self.pFilterModel)


    # on model column change, update the model column of the filter and completer as well
    # def setModelColumn(self, column):
    #     self.completer.setCompletionColumn(column)
    #     self.pFilterModel.setFilterKeyColumn(column)
    #     super(ExtendedComboBox, self).setModelColumn(column)    

#------------------------------
#---------------------------
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

# class Legend(QWidget):  # the tab version; instanced in studio.py
#     # def __init__(self, doc_absolute_path, nanohub_flag):
#     def __init__(self, nanohub_flag):
#         super().__init__()

#         # self.doc_absolute_path = doc_absolute_path

#         self.process = None
#         self.output_dir = '.'   # set in pmb.py
#         self.current_dir = '.'   # reset in pmb.py
#         self.pmb_data_dir = ''   # reset in pmb.py
        
#         #-------------------------------------------
#         self.scroll = QScrollArea()  # might contain centralWidget

#         self.svgView = SvgWidget()
#         self.vbox = QVBoxLayout()

#         self.svgView.setLayout(self.vbox)

#         self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
#         self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
#         self.scroll.setWidgetResizable(True)
#         # self.scroll.setWidgetResizable(False)

#         self.scroll.setWidget(self.svgView) 
#         self.layout = QVBoxLayout(self)
#         self.layout.addWidget(self.scroll)

#     def clear_legend(self):  # tab version
#         legend_file = os.path.join(self.pmb_data_dir, 'empty_legend.svg')
#         self.svgView.load(legend_file)

#     def reload_legend(self):  # tab version
#         print('reload_legend(): self.output_dir = ',self.output_dir)
#         for idx in range(4):
#             print("waiting for creation of legend.svg ...",idx)
#             # path = Path("legend.svg")
#             path = Path(self.output_dir,"legend.svg")
#             # path = Path(self.current_dir,self.output_dir,"legend.svg")
#             print("path = ",path)
#             if path.is_file():
#             # try:
#                 # self.svgView.load("legend.svg")
#                 full_fname = os.path.join(self.output_dir, "legend.svg")
#                 # full_fname = os.path.join(self.current_dir,self.output_dir, "legend.svg")
#                 print("legend_tab.py: full_fname = ",full_fname)
#                 self.svgView.load(full_fname)
#                 break
#             # except:
#             #     path = Path(self.current_dir,self.output_dir,"legend.svg")
#             #     time.sleep(1)
#             else:
#                 path = Path(self.output_dir,"legend.svg")
#                 # path = Path(self.current_dir,self.output_dir,"legend.svg")
#                 time.sleep(1)

#------------------------------
class LegendPlotWindow(QWidget):
    def __init__(self, output_dir):
        super().__init__()

        self.output_dir = output_dir
        
        #-------------------------------------------
        self.scroll = QScrollArea()  # might contain centralWidget

        self.svg_view = SvgWidget()
        # self.svg_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        try:
            full_fname = os.path.join(self.output_dir, "legend.svg")
            # full_fname = os.path.join(self.current_dir,self.output_dir, "legend.svg")
            # print("LegendPlotWindow: full_fname = ",full_fname)
            self.svg_view.load(full_fname)
            self.svg_view.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
        except:
            # path = Path(self.current_dir,self.output_dir,"legend.svg")
            # time.sleep(1)
            print("LegendPlotWindow: error trying to load legend.svg ")

        self.layout = QVBoxLayout()

        self.svg_view.setFixedSize(500, 500)
        # self.svgView.setLayout(self.vbox)
        # self.layout.addWidget(self.svg_view)

        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("background-color: lightgreen;")
        # self.close_button.setFixedWidth(150)
        self.close_button.clicked.connect(self.close_legend_cb)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)
        # self.scroll.setFixedWidth(self.scroll.scrollAreaWidgetContents.minimumSizeHint().width())

        # self.scroll.setWidgetResizable(False)

        self.scroll.setWidget(self.svg_view) 
        # self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.scroll)
        self.layout.addWidget(self.close_button)
        # self.layout.setStretch(0,1000)


        self.setLayout(self.layout)
        self.resize(250, 250)

    def close_legend_cb(self):
        self.close()


#------------------------------
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

        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("background-color: lightgreen;")
        # self.close_button.setFixedWidth(150)
        self.close_button.clicked.connect(self.close_plot_cb)
        self.layout.addWidget(self.close_button)

        self.setLayout(self.layout)

    def close_plot_cb(self):
        self.close()

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        # self.setFrameShadow(QFrame.Plain)
        # self.setStyleSheet("border:1px solid black")

#---------------------------------------------------------------
class VisBase():

    def __init__(self, nanohub_flag, config_tab, run_tab, model3D_flag, tensor_flag, **kw):
        # super().__init__()
        # global self.config_params
        super(VisBase,self).__init__(**kw)


        self.vis_filter_init_flag = True

        # self.vis2D = True
        self.model3D_flag = model3D_flag 
        print("--- VisBase: model3D_flag=",model3D_flag)
        self.tensor_flag = tensor_flag 

        if not self.model3D_flag:
            # self.discrete_cell_scalars = ['cell_type', 'cycle_model', 'current_phase','is_motile','current_death_model','dead', 'number_of_nuclei']
            self.discrete_cell_scalars = ['cell_type', 'cycle_model', 'current_phase','is_motile','current_death_model','dead']
        else:
            # self.discrete_cell_scalars = ['cell_type', 'is_motile','current_death_model','dead','number_of_nuclei']
            # self.discrete_cell_scalars = ['cell_type', 'cycle_model', 'current_phase','is_motile','current_death_model','dead', 'number_of_nuclei']
            self.discrete_cell_scalars = ['cell_type', 'cycle_model', 'current_phase','is_motile','current_death_model','dead']

        self.circle_radius = 100  # will be set in run_tab.py using the .xml
        self.mech_voxel_size = 30

        self.nanohub_flag = nanohub_flag
        self.config_tab = config_tab
        self.run_tab = run_tab
        # self.legend_tab = None

        self.bgcolor = [1,1,1,1]  # all 1.0 for white 

        # self.discrete_scalar_len = {"cell_type":0, "cycle_model":6, "current_phase":4, "is_motile":2,"current_death_model":2, "dead":2, "number_of_nuclei":0 }

# 	// currently recognized cell cycle models 
# 	static const int advanced_Ki67_cycle_model= 0;
# 	static const int basic_Ki67_cycle_model=1;
# 	static const int flow_cytometry_cycle_model=2;
# 	static const int live_apoptotic_cycle_model=3;
# 	static const int total_cells_cycle_model=4;
# 	static const int live_cells_cycle_model = 5; 
# 	static const int flow_cytometry_separated_cycle_model = 6; 
# 	static const int cycling_quiescent_model = 7; 
        cycle_model_l = [ival for ival in range(0, 8)]

# // cycle phases
# static const int Ki67_positive_premitotic=0;
# static const int Ki67_positive_postmitotic=1;
# static const int Ki67_positive=2;
# static const int Ki67_negative=3;
# static const int G0G1_phase=4;
# static const int G0_phase=5;
# static const int G1_phase=6;
# static const int G1a_phase=7;
# static const int G1b_phase=8;
# static const int G1c_phase=9;
# static const int S_phase=10;
# static const int G2M_phase=11;
# static const int G2_phase=12;
# static const int M_phase=13;
# static const int live=14;
# static const int G1pm_phase = 15;
# static const int G1ps_phase = 16;
# static const int cycling = 17;
# static const int quiescent = 18;
# static const int custom_phase = 9999;
        cycle_phase_l = [ival for ival in range(0, 19)]

    #     	// currently recognized death models 
	# static const int apoptosis_death_model = 100; 
	# static const int necrosis_death_model = 101; 
	# static const int autophagy_death_model = 102; 

# double polarity is a dimensionless number between 0 and 1 to indicate how polarized the cell is
# along its basal-to-apical axis. If the polarity is zero, the cell has no discernible polarity. Note that
# polarity should be set to one for 2-D simulations.
        # self.discrete_scalar_vals = {"cell_type":0, "cycle_model":cycle_model_l, "current_phase":cycle_phase_l, "is_motile":[0,1],"current_death_model":[100,101,102], "dead":[0,1], "number_of_nuclei":0}
        self.discrete_scalar_vals = {"cell_type":0, "cycle_model":cycle_model_l, "current_phase":cycle_phase_l, "is_motile":[0,1],"current_death_model":[100,101,102], "dead":[0,1]}

        # self.population_plot = None
        # self.population_plot = {"cell_type":None, "cycle_model":None, "current_phase":None, "is_motile":None,"current_death_model":None, "dead":None, "number_of_nuclei":None }
        self.population_plot = {"cell_type":None, "cycle_model":None, "current_phase":None, "is_motile":None,"current_death_model":None, "dead":None}

        self.discrete_scalar = 'cell_type'
        self.legend_svg_plot = None
        self.filterUI = None

        self.celltype_name = []
        self.celltype_color = []

        # hard-coding colors (as is done in PhysiCell for "paint by cell type")
        # self.cell_colors = list( [0.5,0.5,0.5], [1,0,0], [1,1,0], [0,1,0], [0,0,1], 
        # self.cell_colors = ( [0.5,0.5,0.5], [1,0,0], [1,0.84,0], [0,1,0], [0,0,1], 
        # self.cell_colors = ( [0.5,0.5,0.5], [1,0,0], [0.80,0.80,0], [0,1,0], [0,0,1], 
        self.cell_colors = ( [0.5,0.5,0.5], [1,0,0], [0.10,0.10,0], [0,1,0], [0,0,1], 
                        [1,0,1], [1,0.65,0], [0.2,0.8,0.2], [0,1,1], [1, 0.41, 0.71],
                        [1, 0.85, 0.73], [143/255.,188/255.,143/255.], [135/255.,206/255.,250/255.])
        # print("# hard-coded cell type colors= ",len(self.self.cell_colors))
        self.cell_colors = list(self.cell_colors)
        # print("# (post convert to list)= ",len(self.cell_colors))
        np.random.seed(42)
        for idx in range(200):  # TODO: avoid hard-coding max # of cell types
            rgb = [np.random.uniform(), np.random.uniform(), np.random.uniform()]
            self.cell_colors.append(rgb)
        # print("with appended random colors= ",self.cell_colors)


        self.animating_flag = False

        self.called_from_update = False

        self.xml_root = None
        self.current_svg_frame = 0
        self.current_frame = 0   # used in vis3D_tab.py
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.play_plot_cb)

        
        self.fix_cmap_flag = False
        self.cells_edge_checked_flag = True

        self.contour_mesh = True
        self.contour_lines = False
        self.num_contours = 50
        # self.shading_choice = 'auto'  # 'auto'(was 'flat') vs. 'gouraud' (smooth)
        self.shading_choice = 'gouraud'  # 'auto'(was 'flat') vs. 'gouraud' (smooth)

        self.fontsize = 7
        self.label_fontsize = 6
        self.title_fontsize = 10

        # self.plot_svg_flag = True
        self.plot_cells_svg = True

        self.cell_scalars_l = []

        self.cell_scalars_filled = False

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

        self.zmin = -10
        self.zmax = 10
        self.xdel = 20
        self.z_range = self.zmax - self.zmin

        self.aspect_ratio = 0.7

        self.view_aspect_square = True
        # self.view_smooth_shading = False

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

        self.figsize_width_svg = basic_length
        self.figsize_height_svg = basic_length

        # stop the insanity!
        self.output_dir = "."   # for nanoHUB  (overwritten in studio.py, based on config_tab)
        # self.output_dir = "tmpdir"   # for nanoHUB

        #-------------------------------------------
        label_width = 110
        value_width = 60
        label_height = 20
        units_width = 70

        # Beware: padding seems to alter the behavior; adding scroll arrows to choices list!
                # padding-right: 8px; padding-left: 8px; padding-top: 3px; padding-bottom: 3px;
                # height: 30px;
            # QComboBox{
            #     color: #000000;
            #     background-color: #FFFFFF; 
            #     height: 20px;
            # }
            # QComboBox:disabled {
            #     background-color: rgb(199,199,199);
            #     color: rgb(99,99,99);
            # }
        self.stylesheet = """ 
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

        # substrates min/max colorbar
        self.cmin_value = 0.0
        self.cmax_value = 1.0
        self.fixed_contour_levels = MaxNLocator(nbins=self.num_contours).tick_values(self.cmin_value, self.cmax_value)

        # cells' scalars min/max colorbar
        self.cells_cmin_value = 0.0
        self.cells_cmax_value = 1.0


        self.substrates_cbar_combobox = QComboBox()
        self.substrates_cbar_combobox.addItem("jet")
        self.substrates_cbar_combobox.addItem("jet_r")
        self.substrates_cbar_combobox.addItem("viridis")
        self.substrates_cbar_combobox.addItem("viridis_r")
        self.substrates_cbar_combobox.addItem("YlOrRd")
        self.substrates_cbar_combobox.addItem("YlOrRd_r")
        self.substrates_cbar_combobox.setEnabled(False)

        self.scroll_plot = QScrollArea()  # might contain centralWidget


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
        self.play_button.clicked.connect(self.animate)
        self.vbox.addWidget(self.play_button)

        #------
        self.vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        self.cells_checkbox = QCheckBox_custom('cells')
        self.cells_checkbox.setChecked(True)
        self.cells_checkbox.clicked.connect(self.cells_toggle_cb)
        self.cells_checked_flag = True
        hbox.addWidget(self.cells_checkbox) 

        # Need to create the following regardless of 2D/3D
        self.cells_svg_rb = QRadioButton('.svg')
        self.cells_svg_rb.setChecked(True)

        self.cells_mat_rb = QRadioButton('.mat')
        # self.cell_edge_checkbox = QCheckBox_custom('edge')

        if not self.model3D_flag:  # 2D vis

            # Apparently, the physiboss UI causes the radio btns to disappear in a QFrame, so skip for now.
            # hbox2 = QHBoxLayout()
            self.cells_svg_rb.clicked.connect(self.cells_svg_mat_cb)
            # hbox2.addWidget(self.cells_svg_rb)
            hbox.addWidget(self.cells_svg_rb)

            self.cells_mat_rb.clicked.connect(self.cells_svg_mat_cb)
            # hbox2.addWidget(self.cells_mat_rb)
            hbox.addWidget(self.cells_mat_rb)
            # hbox2.addStretch(1)  # not sure about this, but keeps buttons shoved to left

            # radio_frame = QFrame()
            # # radio_frame.setStyleSheet("QFrame{ border : 1px solid black; }")
            # radio_frame.setLayout(hbox2)
            # radio_frame.setFixedWidth(130)  # omg
            # hbox.addWidget(radio_frame) 

            # hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left

            # self.cell_edge_checkbox.setChecked(True)
            # self.cell_edge_checkbox.clicked.connect(self.cells_edge_toggle_cb)
            # self.cells_edge_checked_flag = True
            # hbox.addWidget(self.cell_edge_checkbox) 


        self.disable_cell_scalar_cb = False
        # self.cell_scalar_combobox = QComboBox()
        self.cell_scalar_combobox = ExtendedComboBox()
        self.cell_scalar_combobox.setFixedWidth(270)
        self.cell_scalar_combobox.addItem('cell_type')
        # self.cell_scalar_combobox.currentIndexChanged.connect(self.cell_scalar_changed_cb)

        # e.g., dict_keys(['ID', 'position_x', 'position_y', 'position_z', 'total_volume', 'cell_type', 'cycle_model', 'current_phase', 'elapsed_time_in_phase', 'nuclear_volume', 'cytoplasmic_volume', 'fluid_fraction', 'calcified_fraction', 'orientation_x', 'orientation_y', 'orientation_z', 'polarity', 'migration_speed', 'motility_vector_x', 'motility_vector_y', 'motility_vector_z', 'migration_bias', 'motility_bias_direction_x', 'motility_bias_direction_y', 'motility_bias_direction_z', 'persistence_time', 'motility_reserved', 'chemotactic_sensitivities_x', 'chemotactic_sensitivities_y', 'adhesive_affinities_x', 'adhesive_affinities_y', 'dead_phagocytosis_rate', 'live_phagocytosis_rates_x', 'live_phagocytosis_rates_y', 'attack_rates_x', 'attack_rates_y', 'damage_rate', 'fusion_rates_x', 'fusion_rates_y', 'transformation_rates_x', 'transformation_rates_y', 'oncoprotein', 'elastic_coefficient', 'kill_rate', 'attachment_lifetime', 'attachment_rate', 'oncoprotein_saturation', 'oncoprotein_threshold', 'max_attachment_distance', 'min_attachment_distance'])

        self.vbox.addLayout(hbox)

        #------------------
        hbox = QHBoxLayout()
        self.disable_cell_scalar_cb = False
        # self.cell_scalar_combobox.setEnabled(True)   # for 3D
        self.cell_scalar_combobox.setEnabled(self.model3D_flag)   # for 3D
        hbox.addWidget(self.cell_scalar_combobox)
        self.vbox.addLayout(hbox)

        hbox = QHBoxLayout()
        self.full_list_button = QPushButton("full list")   # old: refresh
        self.full_list_button.setFixedWidth(100)
        self.full_list_button.setEnabled(self.model3D_flag)
        self.full_list_button.clicked.connect(self.add_default_cell_vars)
        hbox.addWidget(self.full_list_button)

        self.partial_button = QPushButton("partial")
        self.partial_button.setFixedWidth(100)
        self.partial_button.setEnabled(self.model3D_flag)
        self.partial_button.clicked.connect(self.add_partial_cell_vars)
        hbox.addWidget(self.partial_button)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left

        self.vbox.addLayout(hbox)

        #-------
        hbox = QHBoxLayout()
        self.cell_scalar_cbar_combobox = QComboBox()
        self.cell_scalar_cbar_combobox .setFixedWidth(120)
        self.cell_scalar_cbar_combobox.addItem("jet")
        self.cell_scalar_cbar_combobox.addItem("jet_r")
        self.cell_scalar_cbar_combobox.addItem("viridis")
        self.cell_scalar_cbar_combobox.addItem("viridis_r")
        self.cell_scalar_cbar_combobox.addItem("YlOrRd")
        self.cell_scalar_cbar_combobox.addItem("YlOrRd_r")
        # self.cell_scalar_cbar_combobox.setEnabled(False)
        self.cell_scalar_cbar_combobox.setEnabled(self.model3D_flag)  # for 3D
        # self.cell_scalar_cbar_combobox.setEnabled(self.vis.cell_scalar_cbar_combobox_changed_cb)  # for 3D
        hbox.addWidget(self.cell_scalar_cbar_combobox)
        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        self.vbox.addLayout(hbox)

        #------
        hbox = QHBoxLayout()
        groupbox = QGroupBox()
        groupbox.setStyleSheet("QGroupBox { border: 1px solid black;}")

        self.fix_cells_cmap_checkbox = QCheckBox_custom('fix: ')
        self.fix_cells_cmap_flag = False
        if not self.model3D_flag:
            self.fix_cells_cmap_checkbox.setEnabled(False)
        self.fix_cells_cmap_checkbox.setChecked(self.fix_cells_cmap_flag)
        self.fix_cells_cmap_checkbox.clicked.connect(self.fix_cells_cmap_toggle_cb)
        hbox.addWidget(self.fix_cells_cmap_checkbox)

        cvalue_width = 60
        label = QLabel("cmin")
        label.setAlignment(QtCore.Qt.AlignCenter)
        hbox.addWidget(label)
        self.cells_cmin = QLineEdit()
        self.cells_cmin.setText('0.0')
        if not self.model3D_flag:
            self.cells_cmin.setEnabled(False)
        self.cells_cmin.returnPressed.connect(self.cells_cmin_cmax_cb)
        self.cells_cmin.setFixedWidth(cvalue_width)
        self.cells_cmin.setValidator(QtGui.QDoubleValidator())
        # self.cmin.setEnabled(False)
        hbox.addWidget(self.cells_cmin)

        label = QLabel("cmax")
        label.setAlignment(QtCore.Qt.AlignCenter)
        hbox.addWidget(label)
        self.cells_cmax = QLineEdit()
        self.cells_cmax.setText('1.0')
        if not self.model3D_flag:
            self.cells_cmax.setEnabled(False)
        self.cells_cmax.returnPressed.connect(self.cells_cmin_cmax_cb)
        self.cells_cmax.setFixedWidth(cvalue_width)
        self.cells_cmax.setValidator(QtGui.QDoubleValidator())
        hbox.addWidget(self.cells_cmax)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left

        self.vbox.addLayout(hbox)

        label = QLabel("(press 'Enter' if cmin or cmax changes)")
        label.setStyleSheet("border: 0px solid black; font: 11px; padding: 0px 5px 0px 5px; top: 0px")
        self.vbox.addWidget(label)

        #------------------
        self.vbox.addWidget(QHLine())

        self.substrates_checkbox = QCheckBox_custom('substrates')
        self.substrates_checkbox.setChecked(False)
        self.substrates_checkbox.clicked.connect(self.substrates_toggle_cb)
        self.substrates_checked_flag = False
        self.vbox.addWidget(self.substrates_checkbox)

        hbox = QHBoxLayout()
        hbox.addWidget(self.substrates_combobox)
        hbox.addWidget(self.substrates_cbar_combobox)

        self.vbox.addLayout(hbox)

        #------
        hbox = QHBoxLayout()
        # groupbox = QGroupBox()
        # groupbox.setStyleSheet("QGroupBox { border: 1px solid black;}")

        self.fix_cmap_checkbox = QCheckBox_custom('fix: ')
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
        self.cmin.setEnabled(False)
        # self.cmin.textChanged.connect(self.change_plot_range)
        self.cmin.returnPressed.connect(self.cmin_cmax_cb)
        self.cmin.setFixedWidth(cvalue_width)
        self.cmin.setValidator(QtGui.QDoubleValidator())
        # self.cmin.setEnabled(False)
        hbox.addWidget(self.cmin)

        label = QLabel("cmax")
        # label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        hbox.addWidget(label)
        self.cmax = QLineEdit()
        self.cmax.setText('1.0')
        self.cmax.setEnabled(False)
        self.cmax.returnPressed.connect(self.cmin_cmax_cb)
        self.cmax.setFixedWidth(cvalue_width)
        self.cmax.setValidator(QtGui.QDoubleValidator())
        # self.cmax.setEnabled(False)
        hbox.addWidget(self.cmax)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left

        self.vbox.addLayout(hbox)

        label = QLabel("(press 'Enter' if cmin or cmax changes)")
        # label.setStyleSheet("border: 1px solid black; font: 11px; padding: 0px 5px 0px 5px")
        label.setStyleSheet("border: 0px solid black; font: 11px; padding: 0px 5px 0px 5px; top: 0px")
                # font: bold 14px;
                # min-width: 10em;
                # padding: 6px;
#     left: 7px;
#     padding: 0px 5px 0px 5px;
        self.vbox.addWidget(label)

        #------------------
        self.vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        label = QLabel("folder")
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        # self.output_folder = QLineEdit(self.output_dir)
        self.output_folder = QLineEdit()
        self.output_folder.returnPressed.connect(self.output_folder_cb)
        hbox.addWidget(self.output_folder)

        # label = QLabel("(then 'Enter')")
        # hbox.addWidget(label)
        self.output_folder_button = QPushButton("Select")
        self.output_folder_button.clicked.connect(self.output_folder_cb)
        hbox.addWidget(self.output_folder_button)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        self.vbox.addLayout(hbox)

        self.vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        self.cell_counts_button = QPushButton("Population plot")
        # self.cell_counts_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        bwidth = 120
        self.cell_counts_button.setFixedWidth(bwidth)
        self.cell_counts_button.clicked.connect(self.cell_counts_cb)
        hbox.addWidget(self.cell_counts_button)
        # self.vbox.addWidget(self.cell_counts_button)

        # self.discrete_cell_scalars = [‘cell_type’, ‘cycle_model’, ‘current_phase’,‘is_motile’,‘current_death_model’,‘dead’,‘number_of_nuclei’,‘polarity’,‘dead’]  # check for discrete type scalar, ugh.

        self.discrete_cells_combobox = QComboBox()

        # self.discrete_scalar_len = {"cell_type":0, "cycle_model":6, "current_phase":4, "is_motile":2,"current_death_model":2, "dead":2, "number_of_nuclei":0 , "polarity":2}
        # self.discrete_cells_combobox.addItems(self.discrete_cell_scalars)
        # self.discrete_cells_combobox.addItems(list(self.discrete_scalar_len.keys()) )
        self.discrete_cells_combobox.addItems(list(self.discrete_scalar_vals.keys()) )
        # self.discrete_cells_combobox.setEnabled(False)
        self.discrete_cells_combobox.currentIndexChanged.connect(self.population_choice_cb)
        hbox.addWidget(self.discrete_cells_combobox)

        self.vbox.addLayout(hbox)


        self.legend_svg_button = QPushButton("Legend (.svg)")
        self.legend_svg_button.setFixedWidth(bwidth)
        self.legend_svg_button.clicked.connect(self.legend_svg_plot_cb)
        self.vbox.addWidget(self.legend_svg_button)

        #-----------
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
        # self.frame_count.textChanged.connect(self.change_frame_count_cb)   # too annoying
        self.frame_count.returnPressed.connect(self.change_frame_count_cb)

        #-------------------
        self.substrates_combobox.currentIndexChanged.connect(self.substrates_combobox_changed_cb)
        # self.substrates_cbar_combobox.currentIndexChanged.connect(self.update_plots)
        self.substrates_cbar_combobox.currentIndexChanged.connect(self.substrates_cbar_combobox_changed_cb)

        self.cell_scalar_combobox.currentIndexChanged.connect(self.update_plots)
        # self.cell_scalar_cbar_combobox.currentIndexChanged.connect(self.vis.cell_scalar_cbar_combobox_changed_cb)
        self.cell_scalar_cbar_combobox.currentIndexChanged.connect(self.cell_scalar_cbar_combobox_changed_cb)

        #==================================================================
        self.scroll_plot.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_plot.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_plot.setWidgetResizable(True)

        # done in subclasses now
        # self.scroll_plot.setWidget(self.canvas) # self.config_params = QWidget()

        self.stackw.addWidget(self.controls1)
        self.stackw.setCurrentIndex(0)

        self.scroll_params.setWidget(self.stackw)
        splitter.addWidget(self.scroll_plot)

        self.show_plot_range = False
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(splitter)


    def filterUI_cb(self):
        print("---- vis_base: filterUI_cb()")
        # self.filterUI = FilterUIWindow()
        if self.vis_filter_init_flag:
            if self.model3D_flag:
                self.filterUI = FilterUI3DWindow(self.vis_filter_init_flag, self)
            else:
                self.filterUI = FilterUI2DWindow(self.vis_filter_init_flag, self)
                pass

            self.vis_filter_init_flag = False
        self.filterUI.show()


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
            msg = "get_cell_types_from_config(): Error opening or parsing " + out_config_file
            msg += ". Either the file has not been created yet or something else is wrong."
            msgBox.setText(msg)
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


    def get_cell_types_from_legend(self):   # used by cell_counts_cb()
        # print("--get_cell_types_from_legend():  assumes legend.svg")
        legend_file = os.path.join(self.output_dir, "legend.svg")
        self.celltype_name.clear()
        self.celltype_color.clear()

        try:
            self.tree = ET.parse(legend_file)
            self.xml_root = self.tree.getroot()
            # print("xml_root=",self.xml_root)
        except:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msg = "get_cell_types_from_legend(): Error opening or parsing " + legend_file
            msg += ". Either the file has not been created yet or something else is wrong."
            # msg += "If you are doing a Population plot, we will try to parse the config file instead and use random colors."
            msgBox.setText(msg)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return False

        try: 
            for var in self.xml_root.findall('{http://www.w3.org/2000/svg}text'):
                ctname = var.text.strip()
                # print("-- ctname=",ctname)
                self.celltype_name.append(ctname)
            # print("      self.celltype_name= ",self.celltype_name)

            idx = 0
            for var in self.xml_root.findall('{http://www.w3.org/2000/svg}circle'):
                if (idx % 2) == 0:  # some legend.svg only have color on 1st occurrence (e.g., biorobots)
                    cattr = var.attrib
                    # print("-- cattr=",cattr)
                    # print("-- cattr['fill']=",cattr['fill'])
                    self.celltype_color.append(cattr['fill'])
                idx += 1
            # print("      self.celltype_color= ",self.celltype_color)
        except:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Error parsing " + legend_file)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return False

        return True


    def legend_svg_plot_cb(self):
        # print("---- legend_svg_plot_cb():")
        if not self.get_cell_types_from_legend():
            return

        # if not self.legend_svg_plot:
        self.legend_svg_plot = LegendPlotWindow(self.output_dir)

        # self.legend_svg_plot.ax0.cla()
        self.legend_svg_plot.show()


    def population_choice_cb(self):
        self.discrete_scalar = self.discrete_cells_combobox.currentText()
        # print("vis_base: population_choice_cb()  discrete_scalar= ",self.discrete_scalar)


    def cell_counts_cb(self):
        # print("---- cell_counts_cb(): --> window for 2D population plots")
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

        if self.discrete_scalar not in mcds[0].data['discrete_cells']['data'].keys():
            print(f"\ncell_counts_cb(): {self.discrete_scalar} is not saved in the output. See the Full list above. Exiting.")
            return

        tval = np.linspace(0, mcds[-1].get_time(), len(xml_files))
        # print("  max tval=",tval)

        # self.yval4 = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['cell_type'] == 4) & (mcds[idx].data['discrete_cells']['cycle_model'] < 100.) == True)) for idx in range(ds_count)] )

        #--------
        if self.discrete_scalar == 'cell_type':   # number not known until run time
            # if not self.population_plot[self.discrete_scalar]:
            if self.population_plot[self.discrete_scalar] is None:
                self.population_plot[self.discrete_scalar] = PopulationPlotWindow()

            self.population_plot[self.discrete_scalar].ax0.cla()

            # ctype_plot = []
            lw = 2
            # for itype, ctname in enumerate(self.celltypes_list):
            # print("  self.celltype_name=",self.celltype_name)
            for itype in range(len(self.celltype_name)):
                ctname = self.celltype_name[itype]
                try:
                    ctcolor = self.celltype_color[itype]
                    # print("  cell_counts_cb(): ctcolor (1)=",ctcolor)
                    if ctcolor == "yellow":   # can't see yellow on white
                        ctcolor = "gold"
                        # print("  now cell_counts_cb(): ctcolor (1)=",ctcolor)
                except:
                    ctcolor = 'C' + str(itype)   # use random colors from matplotlib; rwh TODO: avoid yellow, etc
                    # print("  cell_counts_cb(): ctcolor (2)=",ctcolor)
                if 'rgb' in ctcolor:
                    rgb = ctcolor.replace('rgb','')
                    rgb = rgb.replace('(','')
                    rgb = rgb.replace(')','')
                    rgb = rgb.split(',')
                    # print("--- rgb after split=",rgb)
                    ctcolor = [float(rgb[0])/255., float(rgb[1])/255., float(rgb[2])/255.]
                    # print("--- converted rgb=",ctcolor)
                yval = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['data']['cell_type'] == itype) & (mcds[idx].data['discrete_cells']['data']['cycle_model'] < 100.) == True)) for idx in range(len(mcds))] )
                # yval = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['data']['cell_type'] == itype) == True)) for idx in range(len(mcds))] )
                # print("  yval=",yval)

                self.population_plot[self.discrete_scalar].ax0.plot(tval, yval, label=ctname, linewidth=lw, color=ctcolor)


            self.population_plot[self.discrete_scalar].ax0.set_xlabel('time (mins)')
            self.population_plot[self.discrete_scalar].ax0.set_ylabel('# of cells')
            self.population_plot[self.discrete_scalar].ax0.set_title("cell_type", fontsize=10)
            self.population_plot[self.discrete_scalar].ax0.legend(loc='center right', prop={'size': 8})
            self.population_plot[self.discrete_scalar].canvas.update()
            self.population_plot[self.discrete_scalar].canvas.draw()
            # self.population_plot[self.discrete_scalar].ax0.legend(loc='center right', prop={'size': 8})
            self.population_plot[self.discrete_scalar].show()

        #--------
        elif self.discrete_scalar == '"number_of_nuclei"':   # is it used yet?
            pass
        #--------
        else:  # number is fixed for these (cycle_model, current_phase, is_motile, current_death_model, dead)

            # [‘cell_type’, ‘cycle_model’, ‘current_phase’,‘is_motile’,‘current_death_model’,‘dead’,‘number_of_nuclei’,‘polarity’]
            # self.discrete_scalar_len = {"cell_type":0, "cycle_model":6, "current_phase":4, "is_motile":2,"current_death_model":2, "dead":2, "number_of_nuclei":0 }

            self.population_plot[self.discrete_scalar] = PopulationPlotWindow()
            self.population_plot[self.discrete_scalar].ax0.cla()

            # print("---- generate plot for ",self.discrete_scalar)
            # ctype_plot = []
            lw = 2
            # for itype, ctname in enumerate(self.celltypes_list):
            # print("  self.celltype_name=",self.celltype_name)
            # for itype in range(self.discrete_scalar_len[self.discrete_scalar]):
            for itype in self.discrete_scalar_vals[self.discrete_scalar]:
                # print("  cell_counts_cb(): itype= ",itype)
                ctcolor = 'C' + str(itype)   # use random colors from matplotlib
                # print("  ctcolor=",ctcolor)
                # yval = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['data']['cell_type'] == itype) & (mcds[idx].data['discrete_cells']['data']['cycle_model'] < 100.) == True)) for idx in range(len(mcds))] )

                # yval = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['data'][self.discrete_scalar] == itype) ) for idx in range(len(mcds))) ] )

                # yval = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['data'][self.discrete_scalar] == itype) & (mcds[idx].data['discrete_cells']['data']['cycle_model'] < 100.) == True)) for idx in range(len(mcds))] )
                # yval = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['data'][self.discrete_scalar] == itype) ) for idx in range(len(mcds)))] )
                # yval = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['data'][self.discrete_scalar] == itype) & True) for idx in range(len(mcds)))] )

                # TODO: fix this hackiness. Do we want to avoid counting dead cells??
                yval = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['data'][self.discrete_scalar] == itype) & (mcds[idx].data['discrete_cells']['data']['cycle_model'] < 999.) == True)) for idx in range(len(mcds))] )
                # print("  yval=",yval)

                mylabel = str(itype)
                self.population_plot[self.discrete_scalar].ax0.plot(tval, yval, label=mylabel, linewidth=lw, color=ctcolor)
                # self.population_plot[self.discrete_scalar].ax0.plot(tval, yval, linewidth=lw, color=ctcolor)


            self.population_plot[self.discrete_scalar].ax0.set_xlabel('time (mins)')
            self.population_plot[self.discrete_scalar].ax0.set_ylabel('# of cells')
            self.population_plot[self.discrete_scalar].ax0.set_title(self.discrete_scalar, fontsize=10)
            self.population_plot[self.discrete_scalar].ax0.legend(loc='center right', prop={'size': 8})
            self.population_plot[self.discrete_scalar].canvas.update()
            self.population_plot[self.discrete_scalar].canvas.draw()
            self.population_plot[self.discrete_scalar].show()


    def disable_physiboss_info(self):
        print("vis_tab: ------- disable_physiboss_info()")
        if self.physiboss_vis_checkbox is not None:
            print("vis_tab: ------- self.physiboss_vis_checkbox is not None; try disabling")
            try:
                self.physiboss_vis_checkbox.setChecked(False)
                self.physiboss_vis_checkbox.setEnabled(False)
                self.physiboss_cell_type_combobox.setEnabled(False)
                self.physiboss_node_combobox.setEnabled(False)
                self.physiboss_vis_hide()

            except:
                print("ERROR: Exception disabling physiboss widgets")
                pass
        else:
            print("vis_tab: ------- self.physiboss_vis_checkbox is None")


    # ------ overridden for 3D (vis3D_tab.py)
    def build_physiboss_info(self):
        config_file = self.run_tab.config_xml_name.text()
        print("build_physiboss_info(): get_cell_types():  config_file=",config_file)
        basename = os.path.basename(config_file)
        print("get_cell_types():  basename=",basename)
        # out_config_file = os.path.join(self.output_dir, basename)
        out_config_file = config_file
        print("get_cell_types():  out_config_file=",out_config_file)

        try:
            self.tree = ET.parse(config_file)
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

          
        print("physiboss_node_dict :",self.physiboss_node_dict)
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
            
            self.physiboss_vis_checkbox = QCheckBox_custom('Color by PhysiBoSS node state')
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
        
    #-------------------------------------
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
            self.output_dir = dir_path
            self.output_folder.setText(dir_path)
            # self.legend_tab.output_dir = dir_path
            legend_file = os.path.join(self.output_dir, 'legend.svg')  # hardcoded filename :(
            # if Path(legend_file).is_file():
            #     self.legend_tab.reload_legend()
            # else:
            #     self.legend_tab.clear_legend()

            self.reset_model()
            self.update_plots()

        else:
            print("vis_tab: output_folder_cb():  full_path_model_name is NOT valid")


    def disable_cell_scalar_widgets(self):
        self.cell_scalar_combobox.setEnabled(False)
        self.cell_scalar_cbar_combobox.setEnabled(False)
        self.full_list_button.setEnabled(False)
        self.partial_button.setEnabled(False)

        self.fix_cells_cmap_checkbox.setEnabled(False)
        self.cells_cmin.setEnabled(False)
        self.cells_cmax.setEnabled(False)
        if self.physiboss_vis_checkbox is not None:
            self.physiboss_vis_checkbox.setEnabled(False)
        # self.fix_cmap_checkbox.setEnabled(bval)

        if self.cax2:
            try:   # otherwise, physiboss UI can crash
                self.cax2.remove()
            except:
                pass
            self.cax2 = None

    def cells_svg_mat_cb(self):
        # print("\n---------cells_svg_mat_cb(self)")
        radioBtn = self.sender()
        if "svg" in radioBtn.text():
            self.plot_cells_svg = True
            self.disable_cell_scalar_widgets()

            # self.cell_scalar_combobox.setEnabled(False)
            # self.cell_scalar_cbar_combobox.setEnabled(False)
            # self.full_list_button.setEnabled(False)
            # self.partial_button.setEnabled(False)

            # self.fix_cells_cmap_checkbox.setEnabled(False)
            # self.cells_cmin.setEnabled(False)
            # self.cells_cmax.setEnabled(False)
            # if self.physiboss_vis_checkbox is not None:
            #     self.physiboss_vis_checkbox.setEnabled(False)
            # # self.fix_cmap_checkbox.setEnabled(bval)

            # if self.cax2:
            #     try:   # otherwise, physiboss UI can crash
            #         self.cax2.remove()
            #     except:
            #         pass
            #     self.cax2 = None

        else:
            if not self.cell_scalars_filled: 
                # self.add_default_cell_vars()   # rwh: just do once? 
                # print("\nvis_base:---------cells_svg_mat_cb(self):  calling add_partial_cell_vars()")
                self.add_partial_cell_vars()   # rwh: just do once? 
                self.cell_scalars_filled = True

            self.plot_cells_svg = False
            self.cell_scalar_combobox.setEnabled(True)
            self.cell_scalar_cbar_combobox.setEnabled(True)
            self.full_list_button.setEnabled(True)
            self.partial_button.setEnabled(True)

            self.fix_cells_cmap_checkbox.setEnabled(True)
            self.cells_cmin.setEnabled(True)
            self.cells_cmax.setEnabled(True)
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


    def reset_domain_box(self):
        print("\n------ vis_base: reset_domain_box()")
        self.lut_discrete = None

        self.xmin = float(self.config_tab.xmin.text())
        self.xmax = float(self.config_tab.xmax.text())

        self.ymin = float(self.config_tab.ymin.text())
        self.ymax = float(self.config_tab.ymax.text())

        self.zmin = float(self.config_tab.zmin.text())
        self.zmax = float(self.config_tab.zmax.text())

        if self.model3D_flag:
            # self.domain_diagonal = vtkLineSource()
            self.domain_diagonal.SetPoint1(self.xmin, self.ymin, self.zmin)
            self.domain_diagonal.SetPoint2(self.xmax, self.ymax, self.zmax)

            self.outline.Update()
            # self.outline = vtkOutlineFilter()
            # self.outline.SetInputConnection(self.domain_diagonal.GetOutputPort())

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
            print("--------vis_base() reset_plot_range(): plot_ymin,ymax=  ",self.plot_ymin,self.plot_ymax)
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
        # print("vis_base >>> change_frame_count_cb()")
        try:  # due to the initial callback
            self.current_svg_frame = int(self.frame_count.text())
            self.current_frame = self.current_svg_frame
            # print("           self.current_svg_frame= ",self.current_svg_frame)
        except:
            # print("vis_base >>> change_frame_count_cb(): got exception")
            pass
        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()

    def cells_cmin_cmax_cb(self):
        # print("----- cells_cmin_cmax_cb:")
        try:  # due to the initial callback
            self.cells_cmin_value = float(self.cells_cmin.text())
            self.cells_cmax_value = float(self.cells_cmax.text())
        except:
            pass
        self.update_plots()

    def cmin_cmax_cb(self):
        # print("----- cmin_cmax_cb:")
        try:  # due to the initial callback
            self.cmin_value = float(self.cmin.text())
            self.cmax_value = float(self.cmax.text())
            if not self.model3D_flag:
                self.fixed_contour_levels = MaxNLocator(nbins=self.num_contours).tick_values(self.cmin_value, self.cmax_value)
        except:
            pass
        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()

    #------------------------------------------------------------
    # Not exactly sure if we need this or what it should do. Overridden in vis3D_tab?
    def get_domain_params(self):
        # xml_file = "output%08d.xml" % frame
        xml_file = "initial.xml"
        full_fname = os.path.join(self.output_dir, xml_file)
        if not os.path.exists(full_fname):
            print(f"vis3D_tab.py: get_domain_params(): full_fname {full_fname} does not exist, leaving!")
            return

        # print("------------- get_domain_params(): pyMCDS reading info from ",full_fname)
        mcds = pyMCDS(xml_file, self.output_dir, microenv=True, graph=False, verbose=False)
        # print("         mcds.data.keys()= ",mcds.data.keys())
        # print("\n         mcds.data['continuum_variables'].keys()= ",mcds.data['continuum_variables'].keys())

        # field_name = self.substrates_combobox.currentText()
        # if (len(self.substrate_name) == 0) or (self.substrate_name not in mcds.data['continuum_variables']):
        #     print(f" ---  ERROR: substrate={self.substrate_name} is not valid.")
        #     return


        # sub_dict = mcds.data['continuum_variables'][self.substrate_name]
        # print("get_domain_params(): sub_dict.keys() = ",sub_dict.keys())
        # sub_concentration = sub_dict['data']
        # self.nx,self.ny,self.nz = sub_concentration.shape
        # print("get_domain_params(): nx,ny,nz = ",self.nx,self.ny,self.nz)
        # self.substrate_data.SetDimensions( self.nx+1, self.ny+1, self.nz+1 )

        # rwh ??
        # self.voxel_size = 20   # rwh: fix hard-coded
        # self.x0 = -(self.voxel_size * self.nx) / 2.0
        # self.y0 = -(self.voxel_size * self.ny) / 2.0
        # self.z0 = -(self.voxel_size * self.nz) / 2.0

        self.x0 = 0.
        self.y0 = 0.
        self.z0 = 0.


    def init_plot_range(self, config_tab):
        print("vis_base:----- init_plot_range:")
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

        print("      call get_domain_params()")
        self.get_domain_params()

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

    # def update_plots(self):
    #     print("------ vis_base.py: update_plots()")
    #     self.ax0.cla()
    #     if self.substrates_checked_flag:  # do first so cells are plotted on top
    #         self.plot_substrate(self.current_svg_frame)
    #     if self.cells_checked_flag:
    #         if self.plot_cells_svg:
    #             self.plot_svg(self.current_svg_frame)
    #         else:
    #             self.plot_cell_scalar(self.current_svg_frame)

    #     self.frame_count.setText(str(self.current_svg_frame))

    #     self.canvas.update()
    #     self.canvas.draw()

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

    def substrates_cbar_combobox_changed_cb(self,idx):
        self.update_plots()

    def cell_scalar_cbar_combobox_changed_cb(self,idx):
        # print("\n>vis_base---------------->> cell_scalar_cbar_combobox_changed_cb():")
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
        print("--------- vis_base: reset_model ----------")
        self.cell_scalars_filled = False

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

        self.zmin = float(bds[2])
        self.zmax = float(bds[5])

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

        self.reset_domain_box()

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

        # self.cmin_value = 0.0
        # self.cmax_value = 1.0

        # and plot 1st frame (.svg)
        self.current_svg_frame = 0
        self.current_frame = 0
        # self.forward_plot_cb("")  

        # print("         sub_names= ",sub_names)
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
        self.current_frame = 0
        # self.forward_plot_cb("")  


    # def output_dir_changed(self, text):
    #     self.output_dir = text
    #     print(self.output_dir)

    def first_plot_cb(self, text):
        if self.reset_model_flag:
            self.reset_model()
            self.reset_model_flag = False

        self.current_svg_frame = 0
        self.current_frame = 0
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
        if num_svg == 0:
            print("Missing .svg file in output dir: ",self.output_dir)
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Missing .svg file in output dir " + self.output_dir)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return

    #    print('num_xml, num_svg = ',num_xml, num_svg)
        last_xml = int(xml_files[-1][-12:-4])
        last_svg = int(svg_files[-1][-12:-4])
        # print('last_xml, _svg = ',last_xml,last_svg)
        self.current_svg_frame = last_xml
        if last_svg < last_xml:
            self.current_svg_frame = last_svg

        self.current_frame = self.current_svg_frame
        self.update_plots()


    def back_plot_cb(self, text):
        if self.reset_model_flag:
            self.reset_model()
            self.reset_model_flag = False

        self.current_svg_frame -= 1
        if self.current_svg_frame < 0:
           self.current_svg_frame = 0

        self.current_frame = self.current_svg_frame
        # print('back_plot_cb(): svg # ',self.current_svg_frame)

        self.update_plots()


    def forward_plot_cb(self, text):
        if self.reset_model_flag:
            self.reset_model()
            self.reset_model_flag = False

        self.current_svg_frame+= 1
        self.current_frame = self.current_svg_frame
        # print('svg # ',self.current_svg_frame)

        self.update_plots()


    # def task(self):
            # self.dc.update_figure()

    # used by animate
    def play_plot_cb(self):
        for idx in range(1):
            self.current_svg_frame += 1
            self.current_frame = self.current_svg_frame
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
                self.current_frame -= 1

                self.animating_flag = True
                # self.current_svg_frame = 0
                self.animate()
                return

            self.update_plots()

    #----- View menu: Plot options 
    def cell_edge_cb(self,bval):
        self.cell_edge = bval
        self.update_plots()

    def cell_fill_cb(self,bval):
        self.cell_fill = bval
        self.update_plots()

    #----
    # def shading_cb(self,bval):
    def contour_mesh_cb(self,bval):
        self.contour_mesh = bval
        self.update_plots()

    def contour_smooth_cb(self,bval):
        if bval:
            self.shading_choice = 'gouraud'  # 'auto'(was 'flat') vs. 'gouraud' (smooth)
        else:
            self.shading_choice = 'auto'  # 'auto'(was 'flat') vs. 'gouraud' (smooth)
        self.update_plots()

    def contour_lines_cb(self,bval):
        self.contour_lines = bval
        self.update_plots()


    #----
    def view_aspect_cb(self,bval):
        self.view_aspect_square = bval
        print("vis_tab.py: self.view_aspect_square = ",self.view_aspect_square)
        self.update_plots()

    def voxel_grid_cb(self,bval):
        self.show_voxel_grid = bval
        self.update_plots()

    def mech_grid_cb(self,bval):
        self.show_mechanics_grid = bval
        self.update_plots()


    #----------------------------------------------
    def cells_toggle_cb(self,bval):
        self.cells_checked_flag = bval

        # these widgets reflect the toggle
        self.cells_svg_rb.setEnabled(bval)
        self.cells_mat_rb.setEnabled(bval)
        # self.cell_edge_checkbox.setEnabled(bval)

        # these widgets depend on whether we're using .mat (scalars)
        if bval:
            # print("--- cells_toggle_cb:  conditional block 1")
            self.cell_scalar_combobox.setEnabled(not self.plot_cells_svg)
            self.cell_scalar_cbar_combobox.setEnabled(not self.plot_cells_svg)
            self.full_list_button.setEnabled(not self.plot_cells_svg)
            self.partial_button.setEnabled(not self.plot_cells_svg)
            self.fix_cells_cmap_checkbox.setEnabled(not self.plot_cells_svg)
            self.cells_cmin.setEnabled(not self.plot_cells_svg)
            self.cells_cmax.setEnabled(not self.plot_cells_svg)
        else:
            # print("--- cells_toggle_cb:  conditional block 2")
            self.cell_scalar_combobox.setEnabled(False)
            self.cell_scalar_cbar_combobox.setEnabled(False)
            self.full_list_button.setEnabled(False)
            self.partial_button.setEnabled(False)
            self.fix_cells_cmap_checkbox.setEnabled(False)
            self.cells_cmin.setEnabled(False)
            self.cells_cmax.setEnabled(False)


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


    def fix_cells_cmap_toggle_cb(self,bval):
        # print("fix_cells_cmap_toggle_cb():")
        self.fix_cells_cmap_flag = bval
        self.cells_cmin.setEnabled(bval)
        self.cells_cmax.setEnabled(bval)

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
        # print("\n-------  add_default_cell_vars():   self.output_dir= ",self.output_dir)
        xml_file_root = "output%08d.xml" % 0
        xml_file = os.path.join(self.output_dir, xml_file_root)
        if not Path(xml_file).is_file():
            print("add_default_cell_vars(): ERROR: file not found",xml_file)
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Could not find file " + xml_file)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return

        self.disable_cell_scalar_cb = True
        self.cell_scalar_combobox.clear()

        # -- old way (limit choices)
        # default_var_l = ["pressure", "total_volume", "current_phase", "cell_type", "damage"]
        # for idx in range(len(default_var_l)):
        #     self.cell_scalar_combobox.addItem(default_var_l[idx])
        # self.cell_scalar_combobox.insertSeparator(len(default_var_l))

        mcds = pyMCDS(xml_file_root, self.output_dir, microenv=False, graph=False, verbose=False)

        # # cell_scalar = mcds.get_cell_df()[cell_scalar_name]
        # num_keys = len(mcds.data['discrete_cells']['data'].keys())
        # print("plot_tab: add_default_cell_vars(): num_keys=",num_keys)
        # keys_l = list(mcds.data['discrete_cells']['data'])
        self.cell_scalars_l.clear()
        self.cell_scalars_l = list(mcds.data['discrete_cells']['data'])
        # for idx in range(num_keys-1,0,-1):
        #     if "transformation_rates" in keys_l[idx]:
        #         print("found transformation_rates at index=",idx)
        #         break
        # idx1 = idx + 1

        # Let's remove the ID which seems to be problematic. And reverse the order of vars so custom vars are at the top.
        self.cell_scalars_l.remove('ID')
        # self.cell_scalars_l.reverse()
        self.cell_scalars_l.sort()
        # print("plot_tab: add_default_cell_vars(): self.cell_scalars_l =",self.cell_scalars_l)

        # for idx in range(0, len(keys_l)):
        #     # print("------ add: ",keys_l[idx])
        #     if keys_l[idx] == "ID":
        #         continue
        #     # self.cell_scalar_combobox.addItem(keys_l[idx])
        #     self.cell_scalars_l.append(keys_l[idx])

        self.cell_scalar_combobox.addItems(self.cell_scalars_l)
        # items = [self.cell_scalar_combobox.itemText(i) for i in range(self.cell_scalar_combobox.count())]
        # print(items)

        self.disable_cell_scalar_cb = False

        self.update_plots()


    def add_partial_cell_vars(self):
        print("\n-------  vis_base:  add_partial_cell_vars():   self.output_dir= ",self.output_dir)

        xml_file_root = "output%08d.xml" % 0
        xml_file = os.path.join(self.output_dir, xml_file_root)
        if not Path(xml_file).is_file():
            print("add_partial_cell_vars(): ERROR: file not found",xml_file)
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Could not find file " + xml_file)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return

        self.disable_cell_scalar_cb = True
        self.cell_scalar_combobox.clear()


        mcds = pyMCDS(xml_file_root, self.output_dir, microenv=False, graph=False, verbose=False)
        self.cell_scalars_l.clear()
        # print("   post clear(): cell_scalars_l= ",self.cell_scalars_l)

        self.cell_scalars_l = list(mcds.data['discrete_cells']['data'])

        # Let's remove the ID which seems to be problematic. And reverse the order of vars so custom vars are at the top.
        self.cell_scalars_l.remove('ID')
        self.cell_scalars_l.reverse()

        # determine how to just extract the custom data vars
        for idx in range(len(self.cell_scalars_l)):
            if self.cell_scalars_l[idx].find("transformation_rates") >= 0:
                break
        # print("   post: idx=",idx)
        self.cell_scalars_l = self.cell_scalars_l[0:idx]
        # print("\n   post only custom data: ",self.cell_scalars_l)

        # then append some preferred scalar values, alphabetically
        self.cell_scalars_l.extend(['cell_type','current_phase','cycle_model','damage','elapsed_time_in_phase','pressure'])
        # print("   post append typical: ",self.cell_scalars_l)

        self.cell_scalar_combobox.addItems(self.cell_scalars_l)
        self.cell_scalar_combobox.insertSeparator(idx)

        self.disable_cell_scalar_cb = False
        # print("\n-------  vis_base:  add_partial_cell_vars():   calling update_plots()")
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


    def prepare_plot_cb(self, text):
        self.current_svg_frame += 1
        self.current_frame += 1
        print('\n\n   ====>     prepare_plot_cb(): svg # ',self.current_svg_frame)

        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()


#     def create_figure(self):
#         print("\n        ---------       vis_base.py:--------- create_figure(): ------- creating figure, canvas, ax0")
#         self.figure = plt.figure()
#         self.canvas = FigureCanvasQTAgg(self.figure)
#         self.canvas.setStyleSheet("background-color:transparent;")

#         # Adding one subplot for image
#         # self.ax0 = self.figure.add_subplot(111)
#         # self.ax0 = self.figure.add_subplot(111, adjustable='box', aspect=1.2)
#         # self.ax0 = self.figure.add_subplot(111, adjustable='box', aspect=self.aspect_ratio)
#         self.ax0 = self.figure.add_subplot(111, adjustable='box')
        
#         # self.ax0.get_xaxis().set_visible(False)
#         # self.ax0.get_yaxis().set_visible(False)
#         # plt.tight_layout()

#         self.reset_model()

#         # np.random.seed(19680801)  # for reproducibility
#         # N = 50
#         # x = np.random.rand(N) * 2000
#         # y = np.random.rand(N) * 2000
#         # colors = np.random.rand(N)
#         # area = (30 * np.random.rand(N))**2  # 0 to 15 point radii
#         # self.ax0.scatter(x, y, s=area, c=colors, alpha=0.5)

#         # if self.plot_svg_flag:
#         # if False:
#         #     self.plot_svg(self.current_svg_frame)
#         # else:
#         #     self.plot_substrate(self.current_svg_frame)

#         print("create_figure(): ------- creating dummy contourf")
#         xlist = np.linspace(-3.0, 3.0, 50)
#         print("len(xlist)=",len(xlist))
#         ylist = np.linspace(-3.0, 3.0, 50)
#         X, Y = np.meshgrid(xlist, ylist)
#         Z = np.sqrt(X**2 + Y**2) + 10*np.random.rand()

#         cbar_name = self.substrates_cbar_combobox.currentText()
#         # self.cmap = plt.cm.get_cmap(cbar_name)  # e.g., 'viridis'
#         # self.mysubstrate = self.ax0.contourf(X, Y, Z, cmap=self.cmap)
#         self.mysubstrate = self.ax0.contourf(X, Y, Z, cmap=cbar_name)
#         # if self.field_index > 4:
#         #     # plt.contour(xgrid, ygrid, M[self.field_index, :].reshape(self.numy,self.numx), [0.0])
#         #     plt.contour(X, Y, Z, [0.0])

#         # levels = MaxNLocator(nbins=self.num_contours).tick_values(self.cmin_value, self.cmax_value)

# #rwh - not for this demo
#         # self.cbar = self.figure.colorbar(self.mysubstrate, ax=self.ax0)
#         # self.cbar.ax.tick_params(labelsize=self.fontsize)

#         # substrate_plot = self.ax0.contourf(xgrid, ygrid, M[self.field_index, :].reshape(self.numy,self.numx), num_contours, cmap='viridis')  # self.colormap_dd.value)

#         print("------------create_figure():  # axes = ",len(self.figure.axes))

#         # self.imageInit = [[255] * 320 for i in range(240)]
#         # self.imageInit[0][0] = 0

#         # Init image and add colorbar
#         # self.image = self.ax0.imshow(self.imageInit, interpolation='none')
#         # divider = make_axes_locatable(self.ax0)
#         # cax = divider.new_vertical(size="5%", pad=0.05, pack_start=True)
#         # self.colorbar = self.figure.add_axes(cax)
#         # self.figure.colorbar(self.image, cax=cax, orientation='horizontal')

#         # plt.subplots_adjust(left=0, bottom=0.05, right=1, top=1, wspace=0, hspace=0)

#         # self.plot_substrate(self.current_svg_frame)
#         self.plot_svg(self.current_svg_frame)
#         # self.canvas.draw()

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


    #  for Simularium, among other reasons later
    def get_simularium_info(self):
        print("--------- vis_base: get_simularium_info----------")
        xml_file = Path(self.output_dir, "initial.xml")
        if not os.path.isfile(xml_file):
            print("vis_base: get_simularium_info(): Warning: Expecting initial.xml, but does not exist.")
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Error: Missing 'initial.xml' in " + self.output_dir)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return None

        tree = ET.parse(Path(self.output_dir, "initial.xml"))
        xml_root = tree.getroot()

        bds_str = xml_root.find(".//microenvironment//domain//mesh//bounding_box").text
        bds = bds_str.split()
        print('bds=',bds)
        self.xmin = float(bds[0])
        self.xmax = float(bds[3])
        print(' self.xmin, xmax=',self.xmin, self.xmax)
        self.x_range = self.xmax - self.xmin
        # self.plot_xmin = self.xmin
        # self.plot_xmax = self.xmax
        # print("--------- self.plot_xmax = ",self.plot_xmax)

        self.ymin = float(bds[1])
        self.ymax = float(bds[4])
        self.y_range = self.ymax - self.ymin
        print(' self.ymin, ymax=',self.ymin, self.ymax)
        # self.plot_ymin = self.ymin
        # self.plot_ymax = self.ymax

        self.zmin = float(bds[2])
        self.zmax = float(bds[5])
        self.z_range = self.zmax - self.zmin
        print(' self.zmin, zmax=',self.zmin, self.zmax)

        #-------
        my_display_data = {}
        basename = "output00000000.xml"
        try:
            mcds = pyMCDS(basename, self.output_dir, microenv=False, graph=False, verbose=True)
            print(mcds.data['discrete_cells']['data'].keys())

            # TODO: find better way to determine the cell types. Could parse the config file, 
            # but that assumes we know the config file name in the output dir :/

            # uep = xml_root.find(".//cell_definitions")  # need to know config file name. Arg.
            # id_cell = 0
            # for cell_def in uep:

            cell_types = mcds.data['discrete_cells']['data']['cell_type']
            # print("--- ALL cell_type=",cell_types)  # --- cell_type= [0. 0. 0. 0. 0. 1. 1. 1. 1. 1.]

            # NOTE! this only gets us the cell types in the 0th file! May be more types appear later.
            unique_cell_types = np.unique(cell_types)
            print("--- unique cell_type=",unique_cell_types)  # --- [0. 1.]
            # NOTE: this *should* be sequential integers, starting with 0. We'll convert to ints below.

        except:
            print("Error reading ",basename, "in ",self.output_dir)
            return None
        
        # # hard-coding colors (as is done in PhysiCell for "paint by cell type")
        # # self.self.cell_colors = list( [0.5,0.5,0.5], [1,0,0], [1,1,0], [0,1,0], [0,0,1], 
        # self.cell_colors = ( [0.5,0.5,0.5], [1,0,0], [1,1,0], [0,1,0], [0,0,1], 
        #                 [1,0,1], [1,0.65,0], [0.2,0.8,0.2], [0,1,1], [1, 0.41, 0.71],
        #                 [1, 0.85, 0.73], [143/255.,188/255.,143/255.], [135/255.,206/255.,250/255.])
        # # print("# hard-coded cell type colors= ",len(self.self.cell_colors))
        # self.cell_colors = list(self.cell_colors)
        # # print("# (post convert to list)= ",len(self.cell_colors))
        # np.random.seed(42)
        # for idx in range(200):  # TODO: avoid hard-coding max # of cell types
        #     rgb = [np.random.uniform(), np.random.uniform(), np.random.uniform()]
        #     self.cell_colors.append(rgb)
        # # print("with appended random colors= ",self.cell_colors)

        # lut.SetTableValue(0, 0.5, 0.5, 0.5, 1)  # darker gray
        # lut.SetTableValue(1, 1, 0, 0, 1)  # red
        # lut.SetTableValue(2, 1, 1, 0, 1)  # yellow
        # lut.SetTableValue(3, 0, 1, 0, 1)  # green
        # lut.SetTableValue(4, 0, 0, 1, 1)  # blue
        # lut.SetTableValue(5, 1, 0, 1, 1)  # magenta
        # lut.SetTableValue(6, 1, 0.65, 0, 1)  # orange
        # lut.SetTableValue(7, 0.2, 0.8, 0.2, 1)  # lime
        # lut.SetTableValue(8, 0, 0, 1, 1)  # cyan
        # lut.SetTableValue(9, 1, 0.41, 0.71, 1)  # hotpink
        # lut.SetTableValue(10, 1, 0.85, 0.73, 1)  # peachpuff
        # lut.SetTableValue(11, 143/255.,188/255.,143/255., 1)  # darkseagreen
        # lut.SetTableValue(12, 135/255.,206/255.,250/255., 1)  # lightskyblue
        # np.random.seed(42)
        # for idx in range(13,num_cell_types):  # random beyond those hard-coded
        #     lut.SetTableValue(idx, np.random.uniform(), np.random.uniform(), np.random.uniform(), 1)
        my_display_data = {}
        icell = 0   # want ints
        for cellID in unique_cell_types:
            my_display_data[icell] = DisplayData(name="cell"+str(icell),color=rgb2hex(self.cell_colors[icell]),display_type=DISPLAY_TYPE.SPHERE,)
            icell += 1

        # uep = xml_root.find(".//cell_definitions")  # need to know config file name. Arg.
        # id_cell = 0
        # for cell_def in uep:
        #     print(f'----- cell_def.tag= {cell_def.tag}')
        #     my_display_data[id_cell] = DisplayData(name=cell_def.tag, display_type=DISPLAY_TYPE.SPHERE,)
        #     id_cell += 1


        return my_display_data 


    def convert_to_simularium(self, xml_file):
        print("\n-------------vis_base.py:  convert_to_simularium()")

        # hex_color = rgb2hex((0.1, 0.1, 0.1, 0.1), keep_alpha=True)

        # sim_output_dir = os.path.realpath(os.path.join('.', self.config_tab.folder.text()))
        print("sim_output_dir = ",self.output_dir )

        my_display_data = self.get_simularium_info()
        if my_display_data is None:
            return

        my_xrange = self.xmax - self.xmin
        my_yrange = self.ymax - self.ymin
        my_zrange = self.zmax - self.zmin

        # my_display_data = {
        #         0: DisplayData(
        #             name="ctype1",
        #             color=rgb2hex([0.8, 0.8, 0.8]),
        #             display_type=DISPLAY_TYPE.SPHERE,
        #         ),
        #         1: DisplayData(
        #             name="ctype2",
        #             color=rgb2hex([1.0, 0.0, 0.0]),
        #             display_type=DISPLAY_TYPE.SPHERE,
        #         ),
        #         2: DisplayData(
        #             name="ctype3",
        #             color=rgb2hex([1.0, 1.0, 0.0]),
        #             display_type=DISPLAY_TYPE.SPHERE,
        #         ),
        #     }

        simularium_model_data = PhysicellData(
            timestep=1.0,
            path_to_output_dir=self.output_dir, 
            meta_data=MetaData(
                box_size=np.array([my_xrange, my_yrange, my_zrange]),
                scale_factor=0.01,
                trajectory_title="PhysiCell trajectory",
                model_meta_data=ModelMetaData(
                    title="PhysiCell_model",
                    version="8.1",
                    authors="PhysiCell modeler",
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
            display_data = my_display_data,
            #     0: DisplayData(
            #         name="ctype1",
            #         color=rgb2hex([1.0, 1.0, 1.0]),
            #         display_type=DISPLAY_TYPE.SPHERE,
            #     ),
            #     1: DisplayData(
            #         name="ctype2",
            #         color=rgb2hex([1.0, 0.0, 0.0]),
            #         display_type=DISPLAY_TYPE.SPHERE,
            #     ),
            # },
            time_units=UnitData("m"),  # minutes; trying to just use "frame" --> undefined error, 
        )

        # lut.SetTableValue(0, 0.5, 0.5, 0.5, 1)  # darker gray
        # lut.SetTableValue(1, 1, 0, 0, 1)  # red
        # lut.SetTableValue(2, 1, 1, 0, 1)  # yellow
        # lut.SetTableValue(3, 0, 1, 0, 1)  # green
        # lut.SetTableValue(4, 0, 0, 1, 1)  # blue
        # lut.SetTableValue(5, 1, 0, 1, 1)  # magenta
        # lut.SetTableValue(6, 1, 0.65, 0, 1)  # orange
        # lut.SetTableValue(7, 0.2, 0.8, 0.2, 1)  # lime
        # lut.SetTableValue(8, 0, 0, 1, 1)  # cyan
        # lut.SetTableValue(9, 1, 0.41, 0.71, 1)  # hotpink
        # lut.SetTableValue(10, 1, 0.85, 0.73, 1)  # peachpuff
        # lut.SetTableValue(11, 143/255.,188/255.,143/255., 1)  # darkseagreen
        # lut.SetTableValue(12, 135/255.,206/255.,250/255., 1)  # lightskyblue
        # np.random.seed(42)
        # for idx in range(13,num_cell_types):  # random beyond those hard-coded
        #     lut.SetTableValue(idx, np.random.uniform(), np.random.uniform(), np.random.uniform(), 1)

            # nth_timestep_to_read=1,
            # display_data={
            #     0: DisplayData(
            #         name="ctype1",
            #         color=rgb2hex([1.0, 1.0, 1.0]),
            #         display_type=DISPLAY_TYPE.SPHERE,
            #     ),
            #     1: DisplayData(
            #         name="ctype2",
            #         color=rgb2hex([1.0, 0.0, 0.0]),
            #         display_type=DISPLAY_TYPE.SPHERE,
            #     ),
            # },

        print("calling Simularium PhysicellConverter...\n")
        # model_name = os.path.basename(self.current_xml_file)
        model_name = os.path.basename(xml_file)
        model_name = model_name[:-4]   # strip off .xml suffix
        PhysicellConverter(simularium_model_data).save(model_name)
        print(f"--> {model_name}.simularium")

        print("Load this model at: https://simularium.allencell.org/viewer")
