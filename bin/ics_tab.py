"""
Authors:
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)

"""

import sys
import os
import logging
import time
# import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
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
# from pyMCDS_cells import pyMCDS_cells 
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

# from PyQt5 import QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
# from matplotlib.figure import Figure

class ICs(QWidget):

    def __init__(self, config_tab, celldef_tab):
        super().__init__()
        # global self.config_params

        self.celldef_tab = celldef_tab
        self.config_tab = config_tab

        # self.circle_radius = 100  # will be set in run_tab.py using the .xml
        # self.mech_voxel_size = 30

        self.cell_radius = 8.412710547954228   # from PhysiCell_phenotype.cpp
        self.color_by_celltype = ['gray','red','green','yellow','cyan','magenta','blue','brown','black','orange','seagreen','gold']
        self.alpha_value = 1.0

        self.csv_array = np.empty([1,4])  # default floats
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

        self.l1_value = 10.
        self.l2_value = 30.

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

        # self.output_dir = "."   # for nanoHUB

        #-------------------------------------------
        label_width = 110
        value_width = 60
        label_height = 20
        units_width = 70

        self.myscroll = QScrollArea()  # might contain centralWidget
        # self.create_figure()

        self.config_params = QWidget()

        # self.main_layout = QVBoxLayout()

        self.vbox = QVBoxLayout()
        self.vbox.addStretch(0)

        self.stackw = QStackedWidget()
        # self.stackw.setCurrentIndex(0)


        self.controls1 = QWidget()
        self.glayout1 = QGridLayout()
        self.controls1.setLayout(self.glayout1)

        idr = 0
        icol = 0
        self.celltype_combobox = QComboBox()
        self.glayout1.addWidget(self.celltype_combobox, idr,icol, 1,2) # w, row, column, rowspan, colspan
        # self.celltype_combobox.addItem("dummy celltype")
        # for var in uep.findall('cell_definition'):
        #     self.celltypes_list.append(name)
        #     self.live_phagocytosis_dropdown.addItem(name)
        # self.celltype_combobox.addItem("default")
        # self.celltype_combobox.addItem("celltype 2")
        # self.celltype_dropdown.currentIndexChanged.connect(self.celltype_dropdown_changed_cb)  # later

        icol += 2
        self.geom_combobox = QComboBox()
        self.glayout1.addWidget(self.geom_combobox, idr,icol, 1,1) # w, row, column, rowspan, colspan
        self.geom_combobox.addItem("annulus/disk")
        self.geom_combobox.addItem("rectangle")
        self.geom_combobox.currentIndexChanged.connect(self.geom_combobox_changed_cb)

        icol += 1
        self.fill_combobox = QComboBox()
        self.glayout1.addWidget(self.fill_combobox, idr,icol, 1,1) # w, row, column, rowspan, colspan
        self.fill_combobox.addItem("random fill")
        self.fill_combobox.addItem("hex fill")
        self.fill_combobox.currentIndexChanged.connect(self.fill_combobox_changed_cb)

        icol += 1
        self.num_cells = QLineEdit()
        fixed_width_value = 80
        self.num_cells.setFixedWidth(fixed_width_value)
        self.num_cells.setValidator(QtGui.QIntValidator(1,100000))
        self.num_cells.setEnabled(True)
        self.num_cells.setText('100')
        self.glayout1.addWidget(self.num_cells, idr,icol,1,1) 

        btn_width = 80
        icol += 1
        self.clear_button = QPushButton("Clear")
        # self.clear_button.setFixedWidth(btn_width)
        self.clear_button.setStyleSheet("background-color: yellow")
        self.clear_button.clicked.connect(self.clear_cb)
        self.glayout1.addWidget(self.clear_button, idr,icol,1,1) 

        icol += 1
        self.plot_button = QPushButton("Plot")
        # self.plot_button.setFixedWidth(btn_width)
        self.plot_button.setStyleSheet("background-color: lightgreen")
        # self.plot_button.clicked.connect(self.uniform_random_pts_annulus_cb)
        self.plot_button.clicked.connect(self.plot_cb)
        self.glayout1.addWidget(self.plot_button, idr,icol,1,1) 

        icol += 1
        self.csv_button = QPushButton("->cells.csv")
        # self.csv_button.setFixedWidth(btn_width)
        self.csv_button.setStyleSheet("background-color: lightgreen")
        # self.plot_button.clicked.connect(self.uniform_random_pts_annulus_cb)
        self.csv_button.clicked.connect(self.csv_cb)
        self.glayout1.addWidget(self.csv_button, idr,icol,1,1) 


        cvalue_width = 70
        label = QLabel("L1")
        label.setFixedWidth(30)
        # label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignRight)
        self.l1val = QLineEdit()
        self.l1val.setFixedWidth(fixed_width_value)
        self.l1val.setEnabled(True)
        self.l1val.setText(str(self.l1_value))
        # self.cmin.textChanged.connect(self.change_plot_range)
        # self.l1val.returnPressed.connect(self.l1_l2_cb)
        self.l1val.textChanged.connect(self.l1_l2_cb)
        # self.l1val.setFixedWidth(cvalue_width)
        self.l1val.setValidator(QtGui.QDoubleValidator(0.,10000.,2))
        icol += 1
        self.glayout1.addWidget(label, idr,icol,1,1) # w, row, column, rowspan, colspan
        icol += 1
        self.glayout1.addWidget(self.l1val, idr,icol,1,1) # w, row, column, rowspan, colspan

        label = QLabel("L2")
        label.setFixedWidth(30)
        label.setAlignment(QtCore.Qt.AlignRight)
        self.l2val = QLineEdit()
        self.l2val.setFixedWidth(fixed_width_value)
        self.l2val.setEnabled(True)
        self.l2val.setText(str(self.l2_value))
        # self.l2val.returnPressed.connect(self.l1_l2_cb)
        self.l2val.textChanged.connect(self.l1_l2_cb)
        # self.l2val.setFixedWidth(cvalue_width)
        self.l2val.setValidator(QtGui.QDoubleValidator(0.,10000.,2))
        icol += 1
        self.glayout1.addWidget(label, idr,icol,1,1) # w, row, column, rowspan, colspan
        icol += 1
        self.glayout1.addWidget(self.l2val, idr,icol,1,1) # w, row, column, rowspan, colspan

        #-------------------
        # self.celltype_combobox.currentIndexChanged.connect(self.celltype_combobox_changed_cb)

        # controls_vbox = QVBoxLayout()
        # controls_vbox.addLayout(controls_hbox)
        # controls_vbox.addLayout(controls_hbox2)

        #==================================================================
        self.config_params.setLayout(self.vbox)

        self.myscroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.myscroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.myscroll.setWidgetResizable(True)

        # self.myscroll.setWidget(self.config_params) # self.config_params = QWidget()
        self.create_figure()
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
        self.stackw.setFixedHeight(50)
        # self.stackw.resize(700,100)
        self.layout.addWidget(self.stackw)
        self.show_plot_range = False
        # if self.show_plot_range:
        #     self.layout.addWidget(self.controls2)
        # self.layout.addWidget(self.my_xmin)
        self.layout.addWidget(self.myscroll)
        # self.layout.addStretch()

        # self.create_figure()


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


    def show_hide_plot_range(self):
        # print("vis_tab: show_hide_plot_range()")
        logging.debug(f'ics_tab.py: self.stackw.count()= {self.stackw.count()}')
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


    def l1_l2_cb(self):
        # print("----- l1_l2_cb:")
        try:  # due to the initial callback
            self.l1_value = float(self.l1val.text())
            self.l2_value = float(self.l2val.text())
            # print(self.l1_value, self.l2_value)
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
        # if self.substrates_checked_flag:  # do first so cells are plotted on top
        #     self.plot_substrate(self.current_svg_frame)
        # if self.cells_checked_flag:
        #     self.plot_svg(self.current_svg_frame)

        # self.frame_count.setText(str(self.current_svg_frame))

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

    # def celltype_combobox_changed_cb(self,idx):
        # print("----- celltype_combobox_changed_cb: idx = ",idx)
        # self.update_plots()

    def geom_combobox_changed_cb(self,idx):
        # print("----- geom_combobox_changed_cb: idx = ",idx)
        # if "rect" in self.geom_combobox.currentText() and "hex" in self.fill_combobox.currentText():
        if "hex" in self.fill_combobox.currentText():
            self.num_cells.setEnabled(False)
        else:
            self.num_cells.setEnabled(True)
        # if idx == 0:
        #     self.l2val.setEnabled(False)
        # else:
        #     self.l2val.setEnabled(True)
        # self.update_plots()

    def fill_combobox_changed_cb(self,idx):
        # print("----- fill_combobox_changed_cb: idx = ",idx)
        # if "rect" in self.geom_combobox.currentText() and "hex" in self.fill_combobox.currentText():
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

        self.plot_xmin = float(self.config_tab.xmin.text())
        self.plot_xmax = float(self.config_tab.xmax.text())
        self.plot_ymin = float(self.config_tab.ymin.text())
        self.plot_ymax = float(self.config_tab.ymax.text())
        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)
        # self.update_plots()
        self.canvas.update()
        self.canvas.draw()


    def create_figure(self):
        # print("\nics_tab:  --------- create_figure(): ------- creating figure, canvas, ax0")
        self.figure = plt.figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
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

        # self.plot_cb()

        # self.plot_svg(self.current_svg_frame)

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
            logging.debug(f'ics_tab.py: plot_vecs(): ERROR')
            pass

    #------------------------------------------------------------
    # def plot_svg(self, frame, rdel=''):
    def plot_svg(self, frame):
        # global current_idx, axes_max
        # global current_frame

        # return

        if self.show_grid:
            self.plot_mechanics_grid()

        if self.show_vectors:
            self.plot_vecs()

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
            logging.debug(f'ics_tab.py: plot_svg(): Warning: filename not found: {full_fname}')
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
            logging.debug(f'------ plot_svg(): error trying to parse {full_name}')
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
                    logging.debug(f'ics_tab.py: bogus xval= {xval}')
                    break
                yval = float(circle.attrib['cy'])
                # yval = (yval - self.svg_xmin)/self.svg_xrange * self.y_range + self.ymin
                yval = yval/self.y_range * self.y_range + self.ymin
                if (np.fabs(yval) > too_large_val):
                    logging.debug(f'ics_tab.py: bogus yval= {yval}')
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
                self.circles(xvals,yvals, s=rvals, color=rgbas, edgecolor='black', alpha=self.alpha_value, linewidth=0.5)
            except (ValueError):
                pass
        else:
            self.circles(xvals,yvals, s=rvals, color=rgbas, alpha=self.alpha_value)

        self.ax0.set_aspect(1.0)


    def annulus_error(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("L2 must be > L1")
        #    msgBox.setWindowTitle("Example")
        msgBox.setStandardButtons(QMessageBox.Ok)
        # msgBox.buttonClicked.connect(msgButtonClick)

        returnValue = msgBox.exec()
        # if returnValue == QMessageBox.Ok:
            # print('OK clicked')

    #------------------------------------------------------------
    def plot_cb(self):
        self.reset_plot_range()

        cdef = self.celltype_combobox.currentText()
        volume = float(self.celldef_tab.param_d[cdef]["volume_total"])
        self.cell_radius = (volume * 0.75 / np.pi) ** (1./3)
        logging.debug(f'ics_tab.py: volume= {volume}, radius= {self.cell_radius}')

        if "annulus" in self.geom_combobox.currentText():
            if self.l2_value <= self.l1_value:
                self.annulus_error()
                return
            if "random" in self.fill_combobox.currentText():
                self.uniform_random_pts_annulus()
            elif "hex" in self.fill_combobox.currentText():
                self.hex_pts_annulus()

        else:  # rectangle
            if "random" in self.fill_combobox.currentText():
                self.uniform_random_pts_rect()
            elif "hex" in self.fill_combobox.currentText():
                self.hex_pts_rect()

    #----------------------------------
    def hex_pts_rect(self):
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
        # print("self.l1_value= ", self.l1_value)

        x_min = -self.l1_value
        x_max =  self.l1_value
        y_min = -self.l2_value
        y_max =  self.l2_value
        y_idx = -1
        # hex packing constants
        x_spacing = self.cell_radius * 2
        y_spacing = self.cell_radius * np.sqrt(3)

        cells_x = np.array([])
        cells_y = np.array([])

        cells_x2 = np.array([])
        cells_y2 = np.array([])

        y_idx = 0
        for yval in np.arange(y_min,y_max, y_spacing):
            y_idx += 1
            for xval in np.arange(x_min,x_max, x_spacing):
                xval_offset = xval + (y_idx%2) * self.cell_radius

                xlist.append(xval_offset)
                ylist.append(yval)
                self.csv_array = np.append(self.csv_array,[[xval,yval,zval, cell_type_index]],axis=0)
                rlist.append(rval)
                count+=1

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
        # print("self.l1_value= ", self.l1_value)

        # x_min = -self.l1_value
        # x_max =  self.l1_value
        x_min = -self.l2_value
        x_max =  self.l2_value
        y_min = -self.l2_value
        y_max =  self.l2_value
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

                # ixval = int(xval_offset)
                # print(ixval)
                # idx = np.where(x_values == ixval)
                xdist = xval_offset - xctr
                ydist = yval - yctr
                dist = np.sqrt(xdist*xdist + ydist*ydist)
                if (dist >= self.l1_value) and (dist <= self.l2_value):
                # # if (xval >= xvals[kdx]) and (xval <= xvals[kdx+1]):
                #     xv = xval_offset - big_radius
                #     cells_x = np.append(cells_x, xv)
                #     cells_y = np.append(cells_y, yval)
                #     print(xv,',',yval,',0.0, 2, 101')  # x,y,z, cell type, [sub]cell ID
                #     # plt.plot(xval_offset,yval,'ro',markersize=30)

                    xlist.append(xval_offset)
                    ylist.append(yval)
                    self.csv_array = np.append(self.csv_array,[[xval_offset,yval,zval, cell_type_index]],axis=0)
                    rlist.append(rval)
                    count+=1

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
    def uniform_random_pts_rect(self):
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
        # print("self.l1_value= ", self.l1_value)
        while True:
            sign1 = 1
            if np.random.uniform() > 0.5:
                sign1 = -1
            xval = sign1 * np.random.uniform() * self.l1_value
            sign2 = 1
            if np.random.uniform() > 0.5:
                sign2 = -1
            yval = sign2 * np.random.uniform() * self.l2_value

            xlist.append(xval)
            ylist.append(yval)
            self.csv_array = np.append(self.csv_array,[[xval,yval,zval, cell_type_index]],axis=0)
            rlist.append(rval)
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
        R1 = float(self.l1val.text())
        R1_sq = R1*R1
        R2 = float(self.l2val.text())
        while True:
            t = 2.0 * np.pi * np.random.uniform()
            u = np.random.uniform() + np.random.uniform()
            if u > 1: 
                r = 2.0 - u 
            else: 
                r = u
            xval = R2*r * np.cos(t)
            yval = R2*r * np.sin(t)

            # print("xval,yval= ",xval,yval)
            d2 = xval*xval + yval*yval
            # print("d2= ",d2)
            if d2 >= R1_sq:
                xlist.append(xval)
                ylist.append(yval)
                rlist.append(rval)
                self.csv_array = np.append(self.csv_array,[[xval,yval,zval, cell_type_index]],axis=0)
                # print(count,xval,yval)
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

    def csv_cb(self):
        # print("\n------- NOT WORKING YET -------")
        # x = y = z = np.arange(0.0,5.0,1.0)
        # np.savetxt('cells.csv', (x,y,z), delimiter=',')
        # print(self.csv_array)
        np.savetxt('cells.csv', self.csv_array, delimiter=',')