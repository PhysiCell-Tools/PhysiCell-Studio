"""
vis3D_tab.py - provide 3D visualization on Plot tab. Still a work in progress. Requires vtk module (pip installable).

Authors:
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
Rf. Credits.md
"""

import sys
import os
import time
import random
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from pathlib import Path

from vtk import *
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

import glob

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QGroupBox, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,  QMainWindow,QGridLayout, QPushButton, QFileDialog, QMessageBox, QStackedWidget, QSplitter

import numpy as np
import scipy.io
# from pyMCDS_cells import pyMCDS_cells
from pyMCDS import pyMCDS
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
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

        self.config_tab = None
        self.run_tab = run_tab

        self.population_plot = None
        self.celltype_name = []
        self.celltype_color = []

        self.axes_actor = None
        self.show_xy_slice = True
        self.show_yz_slice = True
        self.show_xz_slice = True
        self.show_voxels = False
        self.show_axes = False

        self.show_xy_clip = False
        self.show_yz_clip = False
        self.show_xz_clip = False

        self.substrate_name = ""
        self.lut_jet = self.get_jet_map()
        self.lut_viridis = self.get_viridis_map()
        self.lut_ylorrd = self.get_ylorrd_map()
        # self.lut_substrate = self.get_jet_map()
        self.lut_substrate = self.lut_jet

        # VTK pipeline
        self.points = vtkPoints()

        # self.cellID = vtkFloatArray()
        # self.cellID.SetName("ID")

        # self.cellVolume = vtkFloatArray()
        # self.cellVolume.SetName("volume")

        self.radii = vtkFloatArray()
        # self.radii.InsertNextValue(1.0)
        # self.radii.InsertNextValue(0.1)
        # self.radii.InsertNextValue(0.2)
        self.radii.SetName("radius")

        # define the colours for the spheres
        self.tags = vtkFloatArray()
        # self.tags.InsertNextValue(1.0)
        # self.tags.InsertNextValue(0.5)
        # self.tags.InsertNextValue(0.7)
        self.tags.SetName("tag")

        self.cell_data = vtkFloatArray()
        self.cell_data.SetNumberOfComponents(2)
        # self.cell_data.SetNumberOfComponents(1)
        # self.cell_data.SetNumberOfTuples(3)
        # self.cell_data.CopyComponent(0, self.radii, 0)
        # self.cell_data.CopyComponent(1, self.tags, 0)
        self.cell_data.SetName("cell_data")

        # construct the grid
        self.ugrid = vtkUnstructuredGrid()
        self.ugrid.SetPoints(self.points)
        self.ugrid.GetPointData().AddArray(self.cell_data)
        self.ugrid.GetPointData().SetActiveScalars("cell_data")


        # self.polydata = vtkPolyData()
        # self.colors = vtkUnsignedCharArray()
        # self.colors.SetNumberOfComponents(3)

        # self.polydata.GetPointData().SetScalars(self.colors)
        self.sphereSource = vtkSphereSource()
        nres = 20
        self.sphereSource.SetPhiResolution(nres)
        self.sphereSource.SetThetaResolution(nres)
        self.sphereSource.SetRadius(1.0)  # 0.5, 1.0 ?

        self.glyph = vtkGlyph3D()
        self.glyph.SetSourceConnection(self.sphereSource.GetOutputPort())
        self.glyph.SetInputData(self.ugrid)
        self.glyph.ClampingOff()
        self.glyph.SetScaleModeToScaleByScalar()
        self.glyph.SetScaleFactor(1.0)
        self.glyph.SetColorModeToColorByScalar()

        # self.glyph.SetInputData(self.polydata)
        # self.glyph.SetColorModeToColorByScalar()
        # glyph.SetScaleModeToScaleByScalar()

        # using these 2 results in fixed size spheres
        # self.glyph.SetScaleModeToDataScalingOff()  # results in super tiny spheres without 'ScaleFactor'
        # glyph.SetScaleFactor(170)  # overall (multiplicative) scaling factor
        # self.glyph.SetScaleFactor(100)  # overall (multiplicative) scaling factor

        self.cells_mapper = vtkPolyDataMapper()
        self.cells_mapper.SetInputConnection(self.glyph.GetOutputPort())
        # self.cells_mapper.ScalarVisibilityOff()
        self.cells_mapper.ScalarVisibilityOn()
        self.cells_mapper.ColorByArrayComponent("cell_data", 1)

        self.cells_actor = vtkActor()
        self.cells_actor.SetMapper(self.cells_mapper)
        # self.cells_actor.GetProperty().SetColor(178, 190, 181)  # gray
        # self.cells_actor.GetProperty().SetColor( 255, 0, 0)
        # self.cells_actor.GetProperty().SetColor(178, 190, 181)
        # self.cells_actor.GetProperty().SetInterpolationToPBR()
        # actor.GetProperty().SetColor(colors.GetColor3d('Salmon'))
        print("-- actor defaults:")
        print("-- ambient:",self.cells_actor.GetProperty().GetAmbient())  # 
        print("-- diffuse:",self.cells_actor.GetProperty().GetDiffuse())  # 1.0
        print("-- specular:",self.cells_actor.GetProperty().GetSpecular())  # 0.0
        print("-- roughness:",self.cells_actor.GetProperty().GetCoatRoughness ())  # 0.0
        # self.cells_actor.GetProperty().SetAmbient(0.5)
        # self.cells_actor.GetProperty().SetDiffuse(0.5)
        # self.cells_actor.GetProperty().SetSpecular(0.2)


        #------
        self.substrate_data = vtkStructuredPoints()
        self.field_index = 0 
        # self.substrate_voxel_scalars = vtkFloatArray()
        # self.substrate_data.GetPointData().SetScalars( self.substrate_voxel_scalars )
        # self.substrate_data.GetCellData().SetScalars( self.substrate_voxel_scalars )

        self.substrate_mapper = vtkDataSetMapper()
        self.substrate_mapper.SetInputData(self.substrate_data)
        # self.substrate_mapper.SetLookupTable(lut_heat)
        self.substrate_mapper.SetLookupTable(self.lut_substrate)
        # self.substrate_mapper.SetLookupTable(cmap='viridis')
        self.substrate_mapper.SetScalarModeToUseCellData()
        # self.substrate_mapper.SetScalarRange(0, 33)

        self.substrate_actor = vtkActor()
        self.substrate_actor.SetMapper(self.substrate_mapper)
        # self.substrate_actor.GetProperty().SetAmbient(1.)


        #-----
        self.planeXY = vtkPlane()
        # plane.SetOrigin(input.GetCenter())
        # plane.SetOrigin(0,0,10)
        self.planeXY.SetOrigin(0,0,0)
        # self.planeXY.SetOrigin(-30,-30,0)
        self.planeXY.SetNormal(0, 0, 1)

        # First create the usual cutter
        self.cutterXY = vtkCutter()
        # self.cutterXY.SetInputData(self.substrate_data)
        # self.cutterXY.SetCutFunction(self.planeXY)
        # self.cutterXY.GeneratePolygons = 1

        self.cutterXYMapper = vtkPolyDataMapper()
        self.cutterXYMapper.SetInputConnection(self.cutterXY.GetOutputPort())
        self.cutterXYMapper.ScalarVisibilityOn()
        self.cutterXYMapper.SetLookupTable(self.lut_substrate)
        self.cutterXYMapper.SetScalarModeToUseCellData()
        # self.cutterXYMapper.SetScalarModeToUsePointData()
        #self.cutterMapper.SetScalarRange(0, vmax)

        self.cutterXYActor = vtkActor()
        self.cutterXYActor.SetMapper(self.cutterXYMapper)

        # https://kitware.github.io/vtk-examples/site/Python/VisualizationAlgorithms/Cutter/
        # cutter = vtkCutter()
        # cutter.SetCutFunction(plane)
        # cutter.SetInputConnection(cube.GetOutputPort())
        # cutter.Update()
        # cutterMapper = vtkPolyDataMapper()
        # cutterMapper.SetInputConnection(cutter.GetOutputPort())

        #-----
        self.planeYZ = vtkPlane()
        self.planeYZ.SetOrigin(0,0,0)
        self.planeYZ.SetNormal(1, 0, 0)

        self.cutterYZ = vtkCutter()

        self.cutterYZMapper = vtkPolyDataMapper()
        self.cutterYZMapper.SetInputConnection(self.cutterYZ.GetOutputPort())
        self.cutterYZMapper.ScalarVisibilityOn()
        # lut = self.get_heat_map()
        self.cutterYZMapper.SetLookupTable(self.lut_substrate)
        self.cutterYZMapper.SetScalarModeToUseCellData()

        self.cutterYZActor = vtkActor()
        self.cutterYZActor.SetMapper(self.cutterYZMapper)

        #-----
        self.planeXZ = vtkPlane()
        self.planeXZ.SetOrigin(0,0,0)
        self.planeXZ.SetNormal(0, 1, 0)

        self.cutterXZ = vtkCutter()

        self.cutterXZMapper = vtkPolyDataMapper()
        self.cutterXZMapper.SetInputConnection(self.cutterXZ.GetOutputPort())
        self.cutterXZMapper.ScalarVisibilityOn()
        # lut = self.get_heat_map()
        self.cutterXZMapper.SetLookupTable(self.lut_substrate)
        self.cutterXZMapper.SetScalarModeToUseCellData()

        self.cutterXZActor = vtkActor()
        self.cutterXZActor.SetMapper(self.cutterXZMapper)

        #-----
        # self.cutterXYEdges = vtkFeatureEdges()
        # self.cutterXYEdgesMapper= vtkPolyDataMapper()
        # self.cutterXYEdgesMapper.SetInputConnection(self.cutterXY.GetOutputPort())
        # self.cutterXYEdges.BoundaryEdgesOn()
        # self.cutterXYEdges.FeatureEdgesOn()
        # self.cutterXYEdges.ManifoldEdgesOff()
        # self.cutterXYEdges.NonManifoldEdgesOff()
        # self.cutterXYEdges.ColoringOn()

        # self.cutterXYEdgesActor = vtkActor()
        # self.cutterXYEdgesActor.SetMapper(self.cutterXYEdgesMapper)

        #------------
        # self.contour = vtkContourFilter()
        # self.contMapper = vtkPolyDataMapper()
        # self.contMapper.SetInputConnection(self.contour.GetOutputPort())
        # # self.contMapper.SetScalarRange(0.0, 1.0)
        # self.contMapper.ScalarVisibilityOff()
        # self.contActor = vtkActor()
        # self.contActor.SetMapper(self.contMapper)

        #-----
        self.clipXY = vtkClipPolyData()
        self.clipYZ = vtkClipPolyData()
        self.clipXZ = vtkClipPolyData()

        # self.clipXYMapper = vtkPolyDataMapper()
        # self.clipXYMapper.SetInputConnection(self.clipXY.GetOutputPort())

        # self.clipXYActor = vtkActor()
        # self.clipXYActor.SetMapper(self.clipXYMapper)

        #-----
        self.scalarBar = vtkScalarBarActor()
        # self.scalarBar.SetTitle("oxygen")
        self.scalarBar.SetTitle("substrate")
        self.scalarBar.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        self.scalarBar.GetPositionCoordinate().SetValue(0.1,0.01)
        self.scalarBar.UnconstrainedFontSizeOn()
        self.scalarBar.SetOrientationToHorizontal()
        self.scalarBar.SetWidth(0.8)
        self.scalarBar.SetHeight(0.1)
        # Test the Get/Set Position
        # self.scalarBar.SetPosition(self.scalarBar.GetPosition())
        self.scalarBar.GetProperty().SetColor(0,0,0)
        self.scalarBar.GetTitleTextProperty().SetColor(0,0,0)

        #-----
        self.domain_outline = vtkOutlineFilter()
        self.domain_outline_mapper = vtkPolyDataMapper()
        self.domain_outline_mapper.SetInputConnection(self.domain_outline.GetOutputPort())
        self.domain_outline_actor = vtkActor()
        self.domain_outline_actor.SetMapper(self.domain_outline_mapper)


        #-----------------------------
        self.nanohub_flag = nanohub_flag

        self.animating_flag = False

        self.xml_root = None
        self.current_frame = 0
        self.timer = QtCore.QTimer()
        # self.t.timeout.connect(self.task)
        self.timer.timeout.connect(self.play_plot_cb)

        # self.tab = QWidget()
        # self.tabs.resize(200,5)
        
        self.num_contours = 15
        self.num_contours = 25
        self.num_contours = 50
        self.fontsize = 5

        # self.plot_svg_flag = True
        self.plot_svg_flag = False
        # self.field_index = 4  # substrate (0th -> 4 in the .mat)

        self.use_defaults = True
        self.title_str = ""

        # self.config_file = "mymodel.xml"
        self.reset_model_flag = True
        self.xmin = -80
        self.xmax = 80
        self.x_range = self.xmax - self.xmin

        self.ymin = -50
        self.ymax = 100
        self.y_range = self.ymax - self.ymin

        self.aspect_ratio = 0.7

        self.show_nucleus = False
        self.show_edge = False
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
        self.output_dir = "../tmpdir"   # for nanoHUB
        self.output_dir = "tmpdir"   # for nanoHUB
        self.output_dir = "output"   # for nanoHUB
        # self.output_dir = "."   # for nanoHUB


        # do in create_figure()?
        # xlist = np.linspace(-3.0, 3.0, 50)
        # print("len(xlist)=",len(xlist))
        # ylist = np.linspace(-3.0, 3.0, 50)
        # X, Y = np.meshgrid(xlist, ylist)
        # Z = np.sqrt(X**2 + Y**2) + 10*np.random.rand()
        # self.cmap = plt.cm.get_cmap("viridis")
        # self.cs = self.ax0.contourf(X, Y, Z, cmap=self.cmap)
        # self.cbar = self.figure.colorbar(self.cs, ax=self.ax)

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
            QPushButton:disabled {
                background-color: rgb(199,199,199);
            }
            QPushButton{ border: 1px solid; border-color: rgb(145, 200, 145); border-radius: 1px;  background-color: lightgreen; color: black; width: 64px; padding-right: 8px; padding-left: 8px; padding-top: 3px; padding-bottom: 3px; } 
            QPushButton:hover { border: 1px solid; border-radius: 3px; border-color: rgb(33, 77, 115); } QPushButton:focus { outline-color: transparent; border: 2px solid; border-color: rgb(151, 195, 243); } QPushButton:pressed{ background-color: rgb(145, 255, 145); } 
            QPushButton:disabled { color: black; border-color: grey; background-color: rgb(199,199,199); }
            """

            # QLineEdit:disabled {
            #     background-color: rgb(199,199,199);
            #     color: rgb(99,99,99);
            # }

            # QPushButton{
            #     color:#000000;
            #     background-color:#FFFFFF; 
            #     border-style: outset;
            #     border-radius: 10px;
            #     border-color: black;
            #     padding: 4px;
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
        # self.substrates_combobox.setEnabled(False)
        self.field_dict = {}
        self.field_min_max = {}
        self.cmin_value = 0.0
        self.cmax_value = 1.0
        # self.fixed_contour_levels = MaxNLocator(nbins=self.num_contours).tick_values(self.cmin_value, self.cmax_value)

        self.substrates_cbar_combobox = QComboBox()
        self.substrates_cbar_combobox.addItem("jet")
        self.substrates_cbar_combobox.addItem("viridis")
        self.substrates_cbar_combobox.addItem("YlOrRd")
        # self.substrates_cbar_combobox.setEnabled(False)

        self.scroll_plot = QScrollArea()  # might contain centralWidget

        self.create_figure()

        # Need to have the substrates_combobox before doing create_figure!

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
        # self.play_button.setStyleSheet("background-color : lightgreen")
        # self.play_button.clicked.connect(self.play_plot_cb)
        self.play_button.clicked.connect(self.animate)
        self.vbox.addWidget(self.play_button)

        # self.prepare_button = QPushButton("Prepare")
        # self.prepare_button.clicked.connect(self.prepare_plot_cb)
        # controls_hbox.addWidget(self.prepare_button)

        #------
        self.vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        self.cells_checkbox = QCheckBox_custom('cells')
        self.cells_checkbox.setChecked(True)
        self.cells_checkbox.clicked.connect(self.cells_toggle_cb)
        self.cells_checked_flag = True
        hbox.addWidget(self.cells_checkbox) 

        # groupbox = QGroupBox()
        # groupbox.setStyleSheet("QGroupBox { border: 1px solid black;}")
        # hbox2 = QHBoxLayout()
        # groupbox.setLayout(hbox2)
        self.cells_svg_rb = QRadioButton('.svg')
        self.cells_svg_rb.setChecked(False)
        self.cells_svg_rb.setEnabled(False)
        self.cells_svg_rb.clicked.connect(self.cells_svg_mat_cb)
        # hbox2.addWidget(self.cells_svg_rb)
        hbox.addWidget(self.cells_svg_rb)
        self.cells_mat_rb = QRadioButton('.mat')
        self.cells_mat_rb.setChecked(True)
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


        # Skip this for 3D
        # self.cells_edge_checkbox = QCheckBox('edge')
        # self.cells_edge_checkbox.setChecked(True)
        # self.cells_edge_checkbox.clicked.connect(self.cells_edge_toggle_cb)
        # self.cells_edge_checked_flag = True
        # hbox.addWidget(self.cells_edge_checkbox) 

        self.vbox.addLayout(hbox)
        #------------------
        hbox = QHBoxLayout()
        self.add_default_cell_vars()
        self.disable_cell_scalar_cb = False
        self.cell_scalar_combobox.setEnabled(True)   # for 3D
        hbox.addWidget(self.cell_scalar_combobox)

        self.cell_scalar_cbar_combobox = QComboBox()
        self.cell_scalar_cbar_combobox.addItem("jet")
        self.cell_scalar_cbar_combobox.addItem("viridis")
        self.cell_scalar_cbar_combobox.addItem("YlOrRd")
        # self.cell_scalar_cbar_combobox.setEnabled(False)
        self.cell_scalar_cbar_combobox.setEnabled(True)  # for 3D
        hbox.addWidget(self.cell_scalar_cbar_combobox)
        self.vbox.addLayout(hbox)

        self.custom_button = QPushButton("append custom data")
        self.custom_button.setFixedWidth(150)
        # self.custom_button.setStyleSheet("background-color : lightgreen")
        # self.play_button.clicked.connect(self.play_plot_cb)
        self.custom_button.clicked.connect(self.append_custom_cb)
        self.vbox.addWidget(self.custom_button)

        #------------------
        self.vbox.addWidget(QHLine())

        # hbox = QHBoxLayout()
        self.substrates_checkbox = QCheckBox_custom('substrates')
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

        self.fix_cmap_checkbox = QCheckBox_custom('fix')
        self.fix_cmap_flag = False
        # self.fix_cmap_checkbox.setEnabled(False)
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
        self.cmin.setValidator(QtGui.QDoubleValidator())
        # self.cmin.setEnabled(False)
        hbox.addWidget(self.cmin)

        label = QLabel("cmax")
        # label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        hbox.addWidget(label)
        self.cmax = QLineEdit()
        self.cmax.setText('1.0')
        self.cmax.returnPressed.connect(self.cmin_cmax_cb)
        self.cmax.setFixedWidth(cvalue_width)
        self.cmax.setValidator(QtGui.QDoubleValidator())
        # self.cmax.setEnabled(False)
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
        self.output_folder.returnPressed.connect(self.output_folder_cb)
        hbox.addWidget(self.output_folder)

        # label = QLabel("(then 'Enter')")
        # hbox.addWidget(label)
        output_folder_button = QPushButton("Select")
        output_folder_button.clicked.connect(self.output_folder_cb)
        hbox.addWidget(output_folder_button)

        hbox.addStretch(1)  # not sure about this, but keeps buttons shoved to left
        self.vbox.addLayout(hbox)

        self.vbox.addWidget(QHLine())

        self.cell_counts_button = QPushButton("Population plot")
        # self.cell_counts_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        self.cell_counts_button.setFixedWidth(200)
        self.cell_counts_button.clicked.connect(self.cell_counts_cb)
        self.vbox.addWidget(self.cell_counts_button)

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
        self.frame_count.textChanged.connect(self.change_frame_count_cb)

        #-------------------
        self.substrates_combobox.currentIndexChanged.connect(self.substrates_combobox_changed_cb)
        # self.substrates_cbar_combobox.currentIndexChanged.connect(self.update_plots)
        self.substrates_cbar_combobox.currentIndexChanged.connect(self.substrates_cbar_combobox_changed_cb)

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
                # print("-- ctname (from legend.svg)=",ctname)
                self.celltype_name.append(ctname)
            print("get_cell_types_from_legend(): celltype_name=",self.celltype_name)

            idx = 0
            for var in self.xml_root.findall('{http://www.w3.org/2000/svg}circle'):
                if idx % 2:
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
            # mcds.append(pyMCDS(basename, self.output_dir, microenv=True, graph=False, verbose=True))

        # keys_l = list(mcds[0].data['discrete_cells']['data'])
        # print("keys_l= ",keys_l)

        # xml_files = glob.glob('output*.xml')
        # xml_file_root = "output%08d.xml" % 0
        # xml_file = os.path.join(self.output_dir, xml_file_root)
        # if not Path(xml_file).is_file():
        #     print("append_custom_cb(): ERROR: file not found",xml_file)
        #     return

        # mcds = pyMCDS(xml_file_root, self.output_dir, microenv=False, graph=False, verbose=False)


        # mcds = [pyMCDS(xml_files[i], '.') for i in range(ds_count)]
        tval = np.linspace(0, mcds[-1].get_time(), len(xml_files))
        # print("max tval=",tval)

        # self.yval4 = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['cell_type'] == 4) & (mcds[idx].data['discrete_cells']['cycle_model'] < 100.) == True)) for idx in range(ds_count)] )

        if not self.population_plot:
            self.population_plot = PopulationPlotWindow()

        self.population_plot.ax0.cla()

        # ctype_plot = []
        lw = 2
        # for itype, ctname in enumerate(self.celltypes_list):
        for itype in range(len(self.celltype_name)):
            ctname = self.celltype_name[itype]
            try:
                ctcolor = self.celltype_color[itype]
            except:
                ctcolor = 'C' + str(itype)   # use random colors from matplotlib
            yval = np.array( [(np.count_nonzero((mcds[idx].data['discrete_cells']['data']['cell_type'] == itype) & (mcds[idx].data['discrete_cells']['data']['cycle_model'] < 100.) == True)) for idx in range(len(mcds))] )

            self.population_plot.ax0.plot(tval, yval, label=ctname, linewidth=lw, color=ctcolor)

            # ctype_plot.append(yval)
            # print("yval= ",yval)


        # p1 = self.ax1.plot(self.xval, self.yval4, label='Mac', linewidth=3, color=self.mac_color)
        # p2 = self.ax1.plot(self.xval, self.yval5, linestyle='dashed', label='Neut', linewidth=3, color=self.neut_color)

        # self.population_plot.ax0.plot(tval,yval,'r-')
        # self.population_plot.ax0.plot(tval,yval0,yval1)
        # self.population_plot.ax0.plot(tval, yval1, label='ctype1', linewidth=lw, color="red")
        # self.population_plot.ax0.grid()
        self.population_plot.ax0.set_xlabel('time (mins)')
        self.population_plot.ax0.set_ylabel('# of cells')
        self.population_plot.ax0.set_title("cell populations", fontsize=10)
        # self.population_plot.canvas.update()
        # self.population_plot.canvas.draw()
        self.population_plot.ax0.legend(loc='center right', prop={'size': 8})
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

    def build_physiboss_info(self, config_file):
        pass
        
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
        except:
            pass

        self.update_plots()


    def init_plot_range(self, config_tab):
        print("----- init_plot_range:")
        try:
            # beware of widget callback 
            self.my_xmin.setText(config_tab.xmin.text())
            self.my_xmax.setText(config_tab.xmax.text())
            self.my_ymin.setText(config_tab.ymin.text())
            self.my_ymax.setText(config_tab.ymax.text())
        except:
            pass

    def output_folder_cb(self):
        # print(f"output_folder_cb(): old={self.output_dir}")
        self.output_dir = self.output_folder.text()
        # print(f"                    new={self.output_dir}")

    def cells_svg_mat_cb(self):
        radioBtn = self.sender()
        if "svg" in radioBtn.text():
            self.plot_cells_svg = True
            self.custom_button.setEnabled(False)
            self.cell_scalar_combobox.setEnabled(False)
            self.cell_scalar_cbar_combobox.setEnabled(False)
            # self.fix_cmap_checkbox.setEnabled(bval)

            if self.cax2:
                self.cax2.remove()
                self.cax2 = None

        else:
            self.plot_cells_svg = False
            self.custom_button.setEnabled(True)
            self.cell_scalar_combobox.setEnabled(True)
            self.cell_scalar_cbar_combobox.setEnabled(True)
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
            return

        # mcds = pyMCDS(xml_file_root, self.output_dir, microenv=False, graph=False, verbose=False)
        mcds = pyMCDS(xml_file_root, self.output_dir, microenv=True, graph=False, verbose=True)

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


    def change_plot_range(self):
        print("----- change_plot_range:")
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
        # self.ax0.cla()
        # if self.substrates_checked_flag:
        #     self.plot_substrate(self.current_frame)
        self.plot_cells3D(self.current_frame)
        # if self.cells_checked_flag:
        #     self.plot_svg(self.current_frame)

        # self.canvas.update()
        # self.canvas.draw()
        return

    def update_output_dir(self, dir_path):
        return 
        # if os.path.isdir(dir_path):
        #     print("update_output_dir(): yes, it is a dir path", dir_path)
        # else:
        #     print("update_output_dir(): NO, it is NOT a dir path", dir_path)
        # self.output_dir = dir_path
        # self.output_folder.setText(dir_path)

    def fill_substrates_combobox(self, substrate_list):
        print("vis3D_tab.py: fill_substrates_combobox(): substrate_list =",substrate_list)
        print("substrate_list = ",substrate_list )
        self.substrate_name = substrate_list[0]
        print("\n----------------------- fill_substrates_combobox(): self.substrate_name=",self.substrate_name) # e.g., oxygen
        # sys.exit(1)
        self.substrates_combobox.clear()
        for s in substrate_list:
            print(" --> ",s)
            self.substrates_combobox.addItem(s)
        # self.substrates_combobox.setCurrentIndex(2)  # not working; gets reset to oxygen somehow after a Run

    def xy_slice_toggle_cb(self,flag):
        self.show_xy_slice = flag
        if flag:
            self.ren.AddActor(self.cutterXYActor)
        else:
            self.ren.RemoveActor(self.cutterXYActor)
        self.vtkWidget.GetRenderWindow().Render()

    def yz_slice_toggle_cb(self,flag):
        self.show_yz_slice = flag
        if flag:
            self.ren.AddActor(self.cutterYZActor)
        else:
            self.ren.RemoveActor(self.cutterYZActor)
        self.vtkWidget.GetRenderWindow().Render()

    def xz_slice_toggle_cb(self,flag):
        self.show_xz_slice = flag
        if flag:
            self.ren.AddActor(self.cutterXZActor)
        else:
            self.ren.RemoveActor(self.cutterXZActor)
        self.vtkWidget.GetRenderWindow().Render()

    #---------
    def xy_clip_toggle_cb(self,flag):
        self.show_xy_clip = flag
        print("xy_clip_toggle_cb(): show_xy_clip=",self.show_xy_clip)
        self.update_plots()

    def yz_clip_toggle_cb(self,flag):
        self.show_yz_clip = flag
        print("yz_clip_toggle_cb(): show_yz_clip=",self.show_yz_clip)
        self.update_plots()

    def xz_clip_toggle_cb(self,flag):
        self.show_xz_clip = flag
        print("xz_clip_toggle_cb(): show_xz_clip=",self.show_xz_clip)
        self.update_plots()

    #---------
    def voxels_toggle_cb(self,flag):
        self.show_voxels = flag
        if flag:
            self.ren.AddActor(self.substrate_actor)
        else:
            self.ren.RemoveActor(self.substrate_actor)
        self.vtkWidget.GetRenderWindow().Render()

    def axes_toggle_cb(self,flag):
        self.show_axes = flag
        if flag:
            if self.axes_actor is None:
                print("------- showing axes_actor")
                self.ren.RemoveActor(self.axes_actor)
                self.axes_actor = vtkAxesActor()
                self.axes_actor.SetShaftTypeToCylinder()
                # subjective scaling
                cradius = self.ymax * 0.001
                self.axes_actor.SetCylinderRadius(cradius)
                self.axes_actor.SetConeRadius(cradius*10)
                laxis = self.ymax + self.ymax * 0.2
                self.axes_actor.SetTotalLength(laxis,laxis,laxis)
                # Change the font size to something reasonable
                # Ref: http://vtk.1045678.n5.nabble.com/VtkAxesActor-Problem-td4311250.html
                fsize = 12
                self.axes_actor.GetXAxisCaptionActor2D().GetTextActor().SetTextScaleMode(vtkTextActor.TEXT_SCALE_MODE_NONE)
                self.axes_actor.GetXAxisCaptionActor2D().GetTextActor().GetTextProperty().SetFontSize(fsize)
                self.axes_actor.GetXAxisCaptionActor2D().GetTextActor().GetTextProperty().ShadowOn()

                self.axes_actor.GetYAxisCaptionActor2D().GetTextActor().SetTextScaleMode(vtkTextActor.TEXT_SCALE_MODE_NONE)
                self.axes_actor.GetYAxisCaptionActor2D().GetTextActor().GetTextProperty().SetFontSize(fsize)
                self.axes_actor.GetYAxisCaptionActor2D().GetTextActor().GetTextProperty().ShadowOn()

                self.axes_actor.GetZAxisCaptionActor2D().GetTextActor().SetTextScaleMode(vtkTextActor.TEXT_SCALE_MODE_NONE)
                self.axes_actor.GetZAxisCaptionActor2D().GetTextActor().GetTextProperty().SetFontSize(fsize)
                self.axes_actor.GetZAxisCaptionActor2D().GetTextActor().GetTextProperty().ShadowOn()
                # self.ren.AddActor(self.axes_actor)
            self.ren.AddActor(self.axes_actor)
        else:
            self.ren.RemoveActor(self.axes_actor)
        self.vtkWidget.GetRenderWindow().Render()

    def colorbar_combobox_changed_cb(self,idx):
        self.update_plots()

    def substrates_combobox_changed_cb(self,idx):
        # print("----- vis3D_tab.py: substrates_combobox_changed_cb: idx = ",idx)
        # self.field_index = 4 + idx # substrate (0th -> 4 in the .mat)
        self.field_index = idx # substrate (0th -> 4 in the .mat)
        self.substrate_name = self.substrates_combobox.currentText()
        print("\n>>> substrates_combobox_changed_cb(): self.substrate_name= ", self.substrate_name)
        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()

    def substrates_cbar_combobox_changed_cb(self,idx):
        # print("----- vis3D_tab.py: substrates_combobox_changed_cb: idx = ",idx)
        # self.field_index = 4 + idx # substrate (0th -> 4 in the .mat)
        cbar_name = self.substrates_cbar_combobox.currentText()
        print("\n>---------------->> substrates_cbar_combobox_changed_cb(): cbar_name= ", cbar_name)
        if cbar_name.find("jet") >= 0:
            print(" -------  cbar_name=  jet_map")
            # self.lut_substrate = self.get_jet_map()
            self.lut_substrate = self.lut_jet
        elif cbar_name.find("viridis") >= 0:
            print(" -------  cbar_name=  viridis_map")
            # self.lut_substrate = self.get_viridis_map()
            self.lut_substrate = self.lut_viridis
        elif cbar_name.find("YlOrRd") >= 0:
            print(" -------  cbar_name=  ylorrd")
            # self.lut_substrate = self.get_viridis_map()
            self.lut_substrate = self.lut_ylorrd

        self.update_plots()


    def open_directory_cb(self):
        dialog = QFileDialog()
        # self.output_dir = dialog.getExistingDirectory(self, 'Select an output directory')
        tmp_dir = dialog.getExistingDirectory(self, 'Select an output directory')
        print("open_directory_cb:  tmp_dir=",tmp_dir)
        if tmp_dir == "":
            return

        self.output_dir = tmp_dir
        self.output_dir_w.setText(self.output_dir)
        self.reset_model()

    def reset_model(self):
        print("\n--------- vis3D_tab: reset_model ----------")
        # Verify initial.xml and at least one .svg file exist. Obtain bounds from initial.xml
        # tree = ET.parse(self.output_dir + "/" + "initial.xml")
        xml_file = Path(self.output_dir, "initial.xml")
        if not os.path.isfile(xml_file):
            print("vis3D_tab: Warning: Expecting initial.xml, but does not exist.")
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
        print('bds=',bds)
        self.xmin = float(bds[0])
        self.xmax = float(bds[3])
        print('reset_model(): self.xmin, xmax=',self.xmin, self.xmax)
        self.x_range = self.xmax - self.xmin
        self.plot_xmin = self.xmin
        self.plot_xmax = self.xmax

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
        self.plot_ymin = self.ymin
        self.plot_ymax = self.ymax

        xcoords_str = xml_root.find(".//microenvironment//domain//mesh//x_coordinates").text
        xcoords = xcoords_str.split()
        print('reset_model(): xcoords=',xcoords)
        print('reset_model(): len(xcoords)=',len(xcoords))
        self.numx =  len(xcoords)
        self.numy =  len(xcoords)
        print("reset_model(): self.numx, numy = ",self.numx,self.numy)

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
                    print("substrate: ",substrate_name )
                    sub_names.append(substrate_name)
                self.substrates_combobox.clear()
                print("sub_names = ",sub_names)
                self.substrates_combobox.addItems(sub_names)


        # and plot 1st frame (.svg)
        self.current_frame = 0
        # self.forward_plot_cb("")  

    def reset_axes(self):
        print("--------- vis3D_tab: reset_axes ----------")
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
        print('bds=',bds)
        self.xmin = float(bds[0])
        self.xmax = float(bds[3])
        self.x_range = self.xmax - self.xmin

        self.ymin = float(bds[1])
        self.ymax = float(bds[4])
        self.y_range = self.ymax - self.ymin

        # and plot 1st frame (.svg)
        self.current_frame = 0
        # self.forward_plot_cb("")  


    # def output_dir_changed(self, text):
    #     self.output_dir = text
    #     print(self.output_dir)

    def first_plot_cb(self, text):
        if self.reset_model_flag:
            self.reset_model()
            self.reset_model_flag = False

        self.current_frame = 0
        self.update_plots()

    def last_plot_cb(self, text):
        print("------last_plot_cb()")
        if self.reset_model_flag:
            self.reset_model()
            self.reset_model_flag = False

        print('cwd = ',os.getcwd())
        print('self.output_dir = ',self.output_dir)
        # xml_file = Path(self.output_dir, "initial.xml")
        # xml_files = glob.glob('tmpdir/output*.xml')
        xml_files = glob.glob(self.output_dir+'/output*.xml')  # cross-platform OK?
        # print('xml_files = ',xml_files)
        # xml_files = Path(self.output_dir, "initial.xml")
        if len(xml_files) == 0:
            return
        xml_files.sort()
        # svg_files = glob.glob('snapshot*.svg')
        # svg_files.sort()
        print('xml_files = ',xml_files)
        # num_xml = len(xml_files)
        # print('svg_files = ',svg_files)
        # num_svg = len(svg_files)
        # print('num_xml, num_svg = ',num_xml, num_svg)
        last_xml = int(xml_files[-1][-12:-4])
        # last_svg = int(svg_files[-1][-12:-4])
        # print('last_xml, _svg = ',last_xml,last_svg)
        print('last_xml = ',last_xml)
        self.current_frame = last_xml
        # if last_svg < last_xml:
            # self.current_frame = last_svg
        self.update_plots()

    def back_plot_cb(self, text):
        if self.reset_model_flag:
            self.reset_model()
            self.reset_model_flag = False

        self.current_frame -= 1
        if self.current_frame < 0:
            self.current_frame = 0
        # print('frame # ',self.current_frame)

        self.update_plots()


    def forward_plot_cb(self, text):
        if self.reset_model_flag:
            self.reset_model()
            self.reset_model_flag = False

        self.current_frame += 1
        # print('frame # ',self.current_frame)

        self.update_plots()


    # def task(self):
            # self.dc.update_figure()

    # used by animate
    def play_plot_cb(self):
        for idx in range(1):
            self.current_frame += 1
            # print('frame # ',self.current_frame)

            # fname = "snapshot%08d.svg" % self.current_frame
            fname = "output%08d.xml" % self.current_frame
            full_fname = os.path.join(self.output_dir, fname)
            # print("full_fname = ",full_fname)
            # with debug_view:
                # print("plot_svg:", full_fname) 
            # print("-- plot_svg:", full_fname) 
            if not os.path.isfile(full_fname):
                # print("Once output files are generated, click the slider.")   
                print("play_plot_cb():  Reached the end (or no output files found).")
                # self.timer.stop()
                # self.current_frame -= 1
                self.animating_flag = True
                self.current_frame = 0
                self.animate()
                return

            self.update_plots()


    def cells_toggle_cb(self,bval):
        self.cells_checked_flag = bval
        self.update_plots()

    def substrates_toggle_cb(self,bval):
        self.substrates_checked_flag = bval
        self.update_plots()

    def change_frame_count_cb(self):
        try:  # due to the initial callback
            self.current_svg_frame = int(self.frame_count.text())
        except:
            pass
        # self.update_plots()

    def cmin_cmax_cb(self):
        print("----- cmin_cmax_cb:")
        try:  # due to the initial callback
            self.cmin_value = float(self.cmin.text())
            self.cmax_value = float(self.cmax.text())
            # self.fixed_contour_levels = MaxNLocator(nbins=self.num_contours).tick_values(self.cmin_value, self.cmax_value)
        except:
            pass
        self.update_plots()

    def fix_cmap_toggle_cb(self,bval):
        print("fix_cmap_toggle_cb():")
        self.fix_cmap_flag = bval
        self.cmin.setEnabled(bval)
        self.cmax.setEnabled(bval)

            # self.substrates_combobox.addItem(s)
        # field_name = self.field_dict[self.substrate_choice.value]
        # field_name = self.field_dict[self.substrates_combobox.currentText()]
        field_name = self.substrates_combobox.currentText()
        print("fix_cmap_toggle_cb(): field_name= ",field_name)
        # print(self.cmap_fixed_toggle.value)
        # if (self.colormap_fixed_toggle.value):  # toggle on fixed range
        # if (bval):  # toggle on fixed range
        #     # self.colormap_min.disabled = False
        #     # self.colormap_max.disabled = False
        #     self.field_min_max[field_name][0] = self.cmin.text
        #     self.field_min_max[field_name][1] = self.cmax.text
        #     self.field_min_max[field_name][2] = True
        #     # self.save_min_max.disabled = False
        # else:  # toggle off fixed range
        #     # self.colormap_min.disabled = True
        #     # self.colormap_max.disabled = True
        #     self.field_min_max[field_name][2] = False

        # print("self.field_dict= ",self.field_dict)
        self.update_plots()


    def animate(self):
        if not self.animating_flag:
            self.animating_flag = True
            self.play_button.setText("Halt")
            self.play_button.setStyleSheet("background-color : red")

            if self.reset_model_flag:
                self.reset_model()
                self.reset_model_flag = False

            # self.current_frame = 0
            self.timer.start(1)

        else:
            self.animating_flag = False
            self.play_button.setText("Play")
            self.play_button.setStyleSheet("background-color : lightgreen")
            self.timer.stop()


    # def play_plot_cb0(self, text):
    #     for idx in range(10):
    #         self.current_frame += 1
    #         print('svg # ',self.current_frame)
    #         self.plot_svg(self.current_frame)
    #         self.canvas.update()
    #         self.canvas.draw()
    #         # time.sleep(1)
    #         # self.ax0.clear()
    #         # self.canvas.pause(0.05)

    def prepare_plot_cb(self, text):
        self.current_frame += 1
        print('\n\n   ====>     prepare_plot_cb(): svg # ',self.current_frame)

        self.update_plots()


    def create_figure(self):
        print("\nvis3D_tab.py --------- create_figure(): ------- creating figure, canvas, ax0")
        self.canvas = QWidget()
        self.vl = QVBoxLayout(self.canvas)
        # self.setCentralWidget(self.canvas)
        # self.resize(640, 480)

        self.ren = vtkRenderer()
        # self.ren.GetActiveCamera().ParallelProjectionOn()
        self.ren.SetBackground(255,255,255)
        # self.ren.SetBackground(0,0,0)
        # vtk_widget = QVTKRenderWindowInteractor(rw=render_window)
        # self.vtkWidget = QVTKRenderWindowInteractor(self.ren)
        self.vtkWidget = QVTKRenderWindowInteractor(self.canvas)
        self.vl.addWidget(self.vtkWidget)
        # self.vtkWidget.Initialize()
        # self.vtkWidget.Start()

        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)

        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        self.text_title_actor = vtkTextActor()
        self.text_title_actor.SetInput('Dummy title')
        self.text_title_actor.GetTextProperty().SetColor(0,0,0)
        # self.text_title_actor.GetTextProperty().SetFontSize(6)  # just select the title to resize it

        self.text_representation = vtkTextRepresentation()
        self.text_representation.GetPositionCoordinate().SetValue(0.25, 0.94)
        self.text_representation.GetPosition2Coordinate().SetValue(0.5, 0.03)
        self.text_widget = vtkTextWidget()
        self.text_widget.SetRepresentation(self.text_representation)

        self.text_widget.SetInteractor(self.iren)
        self.text_widget.SetTextActor(self.text_title_actor)
        self.text_widget.SelectableOff()
        self.text_widget.On()


        # Create source
        source = vtkSphereSource()
        source.SetCenter(0, 0, 0)
        source.SetRadius(0.0001)  # tiny, nearly invisible actor

        # Create a mapper
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())

        # Create an actor - temporary hack
        actor = vtkActor()
        actor.SetMapper(mapper)
        self.ren.AddActor(actor)
        self.ren.ResetCamera()
        # self.frame.setLayout(self.vl)
        # self.setCentralWidget(self.frame)
        self.show()
        self.iren.Initialize()
        self.vtkWidget.GetRenderWindow().Render()
        self.iren.Start()

        # self.figure = plt.figure()
        # self.canvas = FigureCanvasQTAgg(self.figure)
        # self.canvas.setStyleSheet("background-color:transparent;")

        # Adding one subplot for image
        # self.ax0 = self.figure.add_subplot(111)
        # self.ax0 = self.figure.add_subplot(111, adjustable='box', aspect=1.2)
        # self.ax0 = self.figure.add_subplot(111, adjustable='box', aspect=self.aspect_ratio)
        # self.ax0 = self.figure.add_subplot(111, adjustable='box')
        
        # self.ax0.get_xaxis().set_visible(False)
        # self.ax0.get_yaxis().set_visible(False)
        # plt.tight_layout()

        self.reset_model()   # rwh - is this necessary??

        # np.random.seed(19680801)  # for reproducibility
        # N = 50
        # x = np.random.rand(N) * 2000
        # y = np.random.rand(N) * 2000
        # colors = np.random.rand(N)
        # area = (30 * np.random.rand(N))**2  # 0 to 15 point radii
        # self.ax0.scatter(x, y, s=area, c=colors, alpha=0.5)

        # if self.plot_svg_flag:
        # if False:
        #     self.plot_svg(self.current_frame)
        # else:
        #     self.plot_substrate(self.current_frame)

        # print("create_figure(): ------- creating dummy contourf")
        # xlist = np.linspace(-3.0, 3.0, 50)
        # print("len(xlist)=",len(xlist))
        # ylist = np.linspace(-3.0, 3.0, 50)
        # X, Y = np.meshgrid(xlist, ylist)
        # Z = np.sqrt(X**2 + Y**2) + 10*np.random.rand()

        # self.cmap = plt.cm.get_cmap("viridis")
        # self.mysubstrate = self.ax0.contourf(X, Y, Z, cmap=self.cmap)
        # # if self.field_index > 4:
        # #     # plt.contour(xgrid, ygrid, M[self.field_index, :].reshape(self.numy,self.numx), [0.0])
        # #     plt.contour(X, Y, Z, [0.0])

        # self.cbar = self.figure.colorbar(self.mysubstrate, ax=self.ax0)
        # self.cbar.ax.tick_params(labelsize=self.fontsize)

        # # substrate_plot = self.ax0.contourf(xgrid, ygrid, M[self.field_index, :].reshape(self.numy,self.numx), num_contours, cmap='viridis')  # self.colormap_dd.value)

        # print("------------create_figure():  # axes = ",len(self.figure.axes))

        # # self.imageInit = [[255] * 320 for i in range(240)]
        # # self.imageInit[0][0] = 0

        # # Init image and add colorbar
        # # self.image = self.ax0.imshow(self.imageInit, interpolation='none')
        # # divider = make_axes_locatable(self.ax0)
        # # cax = divider.new_vertical(size="5%", pad=0.05, pack_start=True)
        # # self.colorbar = self.figure.add_axes(cax)
        # # self.figure.colorbar(self.image, cax=cax, orientation='horizontal')

        # # plt.subplots_adjust(left=0, bottom=0.05, right=1, top=1, wspace=0, hspace=0)

        # # self.plot_substrate(self.current_frame)
        # # self.plot_svg(self.current_frame)

        # rwh - necessary?
        # self.plot_cells3D(self.current_frame)

        # # self.canvas.draw()

    #------------------------------------------------------------
    def get_jet_map(self):
        # table_size = 512
        table_size = 256
        lut = vtkLookupTable()
        lut.SetNumberOfTableValues(table_size)
        # lut.SetHueRange(0.0, 0.667)  # red-to-blue
        lut.SetHueRange( 0.667, 0.)  # blue-to-red
        lut.Build()
        return lut

    #------------------------------------------------------------
    # https://matplotlib.org/3.1.1/tutorials/colors/colormap-manipulation.html
    # >>> viridis = cm.get_cmap('viridis', 32)
    # >>> viridis(np.linspace(0, 1, 32))
    def get_viridis_map(self):
        table_size = 32

        lut = vtkLookupTable()
        # activeRange = self.vtkData.GetPointData().GetArray(self.activeAr).GetRange()
        # lf.lut.SetTableRange(activeRange)
        lut.SetNumberOfTableValues(table_size)

        rgb = np.array([[0.267004, 0.004874, 0.329415, 1.      ],
            [0.277018, 0.050344, 0.375715, 1.      ],
            [0.282327, 0.094955, 0.417331, 1.      ],
            [0.282884, 0.13592 , 0.453427, 1.      ],
            [0.278012, 0.180367, 0.486697, 1.      ],
            [0.269308, 0.218818, 0.509577, 1.      ],
            [0.257322, 0.25613 , 0.526563, 1.      ],
            [0.243113, 0.292092, 0.538516, 1.      ],
            [0.225863, 0.330805, 0.547314, 1.      ],
            [0.210503, 0.363727, 0.552206, 1.      ],
            [0.19586 , 0.395433, 0.555276, 1.      ],
            [0.182256, 0.426184, 0.55712 , 1.      ],
            [0.168126, 0.459988, 0.558082, 1.      ],
            [0.15627 , 0.489624, 0.557936, 1.      ],
            [0.144759, 0.519093, 0.556572, 1.      ],
            [0.133743, 0.548535, 0.553541, 1.      ],
            [0.123463, 0.581687, 0.547445, 1.      ],
            [0.119423, 0.611141, 0.538982, 1.      ],
            [0.12478 , 0.640461, 0.527068, 1.      ],
            [0.143303, 0.669459, 0.511215, 1.      ],
            [0.180653, 0.701402, 0.488189, 1.      ],
            [0.226397, 0.728888, 0.462789, 1.      ],
            [0.281477, 0.755203, 0.432552, 1.      ],
            [0.344074, 0.780029, 0.397381, 1.      ],
            [0.421908, 0.805774, 0.35191 , 1.      ],
            [0.496615, 0.826376, 0.306377, 1.      ],
            [0.575563, 0.844566, 0.256415, 1.      ],
            [0.657642, 0.860219, 0.203082, 1.      ],
            [0.751884, 0.874951, 0.143228, 1.      ],
            [0.83527 , 0.886029, 0.102646, 1.      ],
            [0.916242, 0.896091, 0.100717, 1.      ],
            [0.993248, 0.906157, 0.143936, 1.      ]])
        
       # rgb.shape = (12, 4)
        idxs = np.round(np.linspace(0, table_size-1, table_size)).astype(int)
        for i in range(table_size):
            lut.SetTableValue(i,
                           rgb[i, 0],
                           rgb[i, 1],
                           rgb[i, 2],
                           1)

        # lut.Build()
        return lut

    #------------------------------------------------------------
    def get_ylorrd_map(self):
        table_size = 32

        lut = vtkLookupTable()
        # activeRange = self.vtkData.GetPointData().GetArray(self.activeAr).GetRange()
        # lf.lut.SetTableRange(activeRange)
        lut.SetNumberOfTableValues(table_size)

        rgb = np.array([[1.        , 1.        , 0.8       , 1.        ],
       [1.        , 0.98178368, 0.75547122, 1.        ],
       [1.        , 0.96356736, 0.71094244, 1.        ],
       [1.        , 0.94535104, 0.66641366, 1.        ],
       [0.9998735 , 0.92688172, 0.62213789, 1.        ],
       [0.99886148, 0.90664137, 0.57963314, 1.        ],
       [0.99784946, 0.88640101, 0.5371284 , 1.        ],
       [0.99683744, 0.86616066, 0.49462366, 1.        ],
       [0.99607843, 0.84111322, 0.45211891, 1.        ],
       [0.99607843, 0.80164453, 0.40961417, 1.        ],
       [0.99607843, 0.76217584, 0.36710942, 1.        ],
       [0.99607843, 0.72270715, 0.32460468, 1.        ],
       [0.99569892, 0.68399747, 0.29196711, 1.        ],
       [0.99468691, 0.64655281, 0.27577483, 1.        ],
       [0.99367489, 0.60910816, 0.25958254, 1.        ],
       [0.99266287, 0.5716635 , 0.24339026, 1.        ],
       [0.99165085, 0.52106262, 0.22618596, 1.        ],
       [0.99063884, 0.4573055 , 0.20796964, 1.        ],
       [0.98962682, 0.39354839, 0.18975332, 1.        ],
       [0.9886148 , 0.32979127, 0.171537  , 1.        ],
       [0.97242252, 0.27299178, 0.15585073, 1.        ],
       [0.94712207, 0.22036686, 0.14168248, 1.        ],
       [0.92182163, 0.16774194, 0.12751423, 1.        ],
       [0.89652119, 0.11511701, 0.11334598, 1.        ],
       [0.86135357, 0.08222644, 0.11739405, 1.        ],
       [0.8228969 , 0.05591398, 0.12751423, 1.        ],
       [0.78444023, 0.02960152, 0.13763441, 1.        ],
       [0.74598355, 0.00328906, 0.14775459, 1.        ],
       [0.68716003, 0.        , 0.14901961, 1.        ],
       [0.62542694, 0.        , 0.14901961, 1.        ],
       [0.56369386, 0.        , 0.14901961, 1.        ],
       [0.50196078, 0.        , 0.14901961, 1.        ]])
       # rgb.shape = (12, 4)
        idxs = np.round(np.linspace(0, table_size-1, table_size)).astype(int)
        for i in range(table_size):
            lut.SetTableValue(i,
                           rgb[i, 0],
                           rgb[i, 1],
                           rgb[i, 2],
                           1)

        # lut.Build()
        return lut

    # rf. https://kitware.github.io/vtk-examples/site/Python/PolyData/CurvaturesDemo/
    def get_diverging_lut1(self):
        colors = vtkNamedColors()
        # Colour transfer function.
        ctf = vtkColorTransferFunction()
        ctf.SetColorSpaceToDiverging()
        p1 = [0.0] + list(colors.GetColor3d('MidnightBlue'))
        p2 = [0.5] + list(colors.GetColor3d('Gainsboro'))
        p3 = [1.0] + list(colors.GetColor3d('DarkOrange'))
        ctf.AddRGBPoint(*p1)
        ctf.AddRGBPoint(*p2)
        ctf.AddRGBPoint(*p3)

        table_size = 256
        lut = vtkLookupTable()
        lut.SetNumberOfTableValues(table_size)
        lut.Build()

        for i in range(0, table_size):
            rgba = list(ctf.GetColor(float(i) / table_size))
            rgba.append(1)
            lut.SetTableValue(i, rgba)

        return lut

    def get_cell_type_colors_lut(self, num_cell_types):
        # https://kitware.github.io/vtk-examples/site/Python/Modelling/DiscreteMarchingCubes/
        print("\n---- get_cell_type_colors_lut(): num_cell_types= ",num_cell_types)
        lut = vtkLookupTable()
        lut.SetNumberOfTableValues(num_cell_types)
        lut.Build()

        # ics_tab.py uses:
        # self.color_by_celltype = ['gray','red','green','yellow','cyan','magenta','blue','brown','black','orange','seagreen','gold']

        lut.SetTableValue(0, 0.5, 0.5, 0.5, 1)  # darker gray
        lut.SetTableValue(1, 1, 0, 0, 1)  # red
        np.random.seed(42)
        for idx in range(2,num_cell_types):  # random beyond those hard-coded
            lut.SetTableValue(idx, np.random.uniform(), np.random.uniform(), np.random.uniform(), 1)

        return lut

    #------------------------------------------------------------
    # def plot_svg(self, frame, rdel=''):
    def plot_cells3D(self, frame):
        print("plot_cells3D:  self.output_dir= ",self.output_dir)
        print("plot_cells3D:  self.substrate_name= ",self.substrate_name)
        print("plot_cells3D:  frame= ",frame)
        self.frame_count.setText(str(frame))

        read_microenv_flag = self.substrates_checkbox.isChecked()

        # xml_file = Path(self.output_dir, "output00000000.xml")
        # xml_file = "output00000000.xml"
        xml_file = "output%08d.xml" % frame
        print("plot_cells3D: xml_file = ",xml_file)
        # mcds = pyMCDS_cells(xml_file, '.')  

        # if not os.path.exists("tmpdir/" + xml_file):
        # if not os.path.exists("output/" + xml_file):
        full_fname = os.path.join(self.output_dir, xml_file)
        if not os.path.exists(full_fname):
            return

        print("\n\n------------- plot_cells3D: pyMCDS reading info from ",xml_file)
        # mcds = pyMCDS(xml_file, 'output')   # will read in BOTH cells and substrates info
        # mcds = pyMCDS(xml_file, self.output_dir)   # will read in BOTH cells and substrates info
        # mcds = pyMCDS(xml_file, self.output_dir, microenv=False, graph=False, verbose=False)
        mcds = pyMCDS(xml_file, self.output_dir, microenv=read_microenv_flag, graph=False, verbose=True)
        current_time = mcds.get_time()
        print('time=', current_time )
        print("metadata keys=",mcds.data['metadata'].keys())
        current_time = mcds.data['metadata']['current_time']
        print('time(verbose)=', current_time )

        current_time = round(current_time, 2)
        self.title_str = 'time '+ str(current_time) + ' min'
        # self.text_title_actor.SetInput(self.title_str)

        #-----------
        if self.cells_checked_flag:
            # mcds = pyMCDS_cells(xml_file, 'tmpdir')  
            # mcds = pyMCDS_cells(xml_file, 'output')  
            # mcds = pyMCDS(xml_file, 'output')  

            # print("mcds.data dict_keys= ",mcds.data['discrete_cells'].keys())   # dict_keys(...)

            # ncells = len(mcds.data['discrete_cells']['ID'])
            ncells = len(mcds.data['discrete_cells']['data']['ID'])
            print('ncells=', ncells)
            if ncells == 0:
                return
            self.title_str += ", # cells=" + str(ncells)

            global xyz
            xyz = np.zeros((ncells, 3))
            # xyz[:, 0] = mcds.data['discrete_cells']['position_x']
            # xyz[:, 1] = mcds.data['discrete_cells']['position_y']
            # xyz[:, 2] = mcds.data['discrete_cells']['position_z']
            xyz[:, 0] = mcds.data['discrete_cells']['data']['position_x']
            xyz[:, 1] = mcds.data['discrete_cells']['data']['position_y']
            xyz[:, 2] = mcds.data['discrete_cells']['data']['position_z']
            #xyz = xyz[:1000]
            # print("position_x = ",xyz[:,0])
            xmin = min(xyz[:,0])
            xmax = max(xyz[:,0])
            # print("xmin = ",xmin)
            # print("xmax = ",xmax)

            ymin = min(xyz[:,1])
            ymax = max(xyz[:,1])
            print("ymin = ",ymin)
            print("ymax = ",ymax)

            zmin = min(xyz[:,2])
            zmax = max(xyz[:,2])
            print("zmin = ",zmin)
            print("zmax = ",zmax)

            # cell_type = mcds.data['discrete_cells']['cell_type']
            cell_type = mcds.data['discrete_cells']['data']['cell_type']
            # print(type(cell_type))
            # print(cell_type)
            unique_cell_type = np.unique(cell_type)
            num_cell_types = len(unique_cell_type)
            print("\nunique_cell_type = ",unique_cell_type )
            print("num_cell_types= ",num_cell_types)

            # lut = self.get_diverging_lut1()
            lut = self.get_cell_type_colors_lut(num_cell_types)
            self.cells_mapper.SetLookupTable(lut)
            # mapper_POINT_CLOUD.SetLookupTable(lookupTable)
            # scalarBar.SetLookupTable(lookupTable)

            #------------
            # colors = vtkNamedColors()

            # update VTK pipeline
            self.points.Reset()
            # self.cellID.Reset()
            self.radii.Reset()
            self.cell_data.Reset()
            self.tags.Reset()
            # self.colors.Reset()
            # self.cellVolume.Reset()
            # points.InsertNextPoint(0, 0, 0)
            # points.InsertNextPoint(1, 1, 1)
            # points.InsertNextPoint(2, 2, 2)

            self.cell_data.SetNumberOfTuples(ncells)

            for idx in range(ncells):
                # x= mcds.data['discrete_cells']['position_x'][idx]
                # y= mcds.data['discrete_cells']['position_y'][idx]
                # z= mcds.data['discrete_cells']['position_z'][idx]
                # id = mcds.data['discrete_cells']['cell_type'][idx]
                x= mcds.data['discrete_cells']['data']['position_x'][idx]
                y= mcds.data['discrete_cells']['data']['position_y'][idx]
                z= mcds.data['discrete_cells']['data']['position_z'][idx]
                id = mcds.data['discrete_cells']['data']['cell_type'][idx]
                self.points.InsertNextPoint(x, y, z)
                # self.cellVolume.InsertNextValue(30.0 + 2*idx)
                # total_volume = mcds.data['discrete_cells']['total_volume'][idx]
                total_volume = mcds.data['discrete_cells']['data']['total_volume'][idx]
                # self.cellVolume.InsertNextValue(1.0 + 2*idx)

                # rval = (total_volume*3/4/pi)**1/3
                rval = (total_volume * 0.2387) ** 0.333333
                # print(idx,") total_volume= ", total_volume, ", rval=",rval )
                # self.cellID.InsertNextValue(id)
                self.radii.InsertNextValue(rval)
                # self.tags.InsertNextValue(float(idx)/ncells)   # multicolored; jet/heatmap across all cells

                # self.tags.InsertNextValue(1.0 - cell_type[idx])   # hacky 2-colors based on colormap
                # print("idx, cell_type[idx]= ",idx,cell_type[idx])
                self.tags.InsertNextValue(cell_type[idx])

            self.cell_data.CopyComponent(0, self.radii, 0)
            self.cell_data.CopyComponent(1, self.tags, 0)
            # self.ugrid.SetPoints(self.points)
            # self.ugrid.GetPointData().AddArray(self.cell_data)
            # self.ugrid.GetPointData().SetActiveScalars("cell_data")

            # self.polydata.SetPoints(self.points)
            # self.polydata.GetPointData().SetScalars(self.cellVolume)
            # # self.polydata.GetPointData().SetScalars(self.cellID)
            # # self.polydata.GetPointData().SetScalars(self.colors)

            cellID_color_dict = {}
            # for idx in range(ncells):
            random.seed(42)
            # for utype in unique_cell_type:
            #     # colors.InsertTuple3(0, randint(0,255), randint(0,255), randint(0,255)) # reddish
            #     cellID_color_dict[utype] = [random.randint(0,255), random.randint(0,255), random.randint(0,255)]

            # hardcode colors for now
            # cellID_color_dict[0.0]=[170,170,170]  # cancer cell
            # cellID_color_dict[1.0]=[255,0,0]  # endothelial
            # print("color dict=",cellID_color_dict)

            # self.colors.SetNumberOfTuples(self.polydata.GetNumberOfPoints())  # ncells
            # for idx in range(ncells):
            # # for idx in range(len(unique_cell_type)):
            #     # colors.InsertTuple3(idx, randint(0,255), randint(0,255), randint(0,255)) 
            #     # if idx < 5:
            #         # print(idx,cellID_color_dict[cell_type[idx]])
            #     self.colors.InsertTuple3(idx, cellID_color_dict[cell_type[idx]][0], cellID_color_dict[cell_type[idx]][1], cellID_color_dict[cell_type[idx]][2])


            # self.glyph.SetScaleModeToDataScalingOn()

            # self.glyph.SetScaleModeToScaleByVector ()
            # self.glyph.SetScaleModeToScaleByScalar ()
            # self.glyph.SetColorModeToColorByVector ()
            print("glyph range= ",self.glyph.GetRange())
            print("num_cell_types= ",num_cell_types)
            self.cells_mapper.SetScalarRange(0,num_cell_types)
            # self.glyph.SetRange(0.0, 0.11445075055913652)
            # self.glyph.SetScaleFactor(3.0)

            # glyph.ScalingOn()
            # self.glyph.SetScalarRange(0, vmax)
            self.glyph.Update()

            #----------------------------------------------
            clipped_cells_flag = False
            polydata = self.glyph.GetOutput()
            if self.show_xy_clip:
                clipped_cells_flag = True
                self.clipXY.SetInputData(self.glyph.GetOutput())
                # self.planeXY.SetOrigin(x0,y0,0)
                self.clipXY.SetClipFunction(self.planeXY)
                self.clipXY.Update()
                polydata = self.clipXY.GetOutput()
                self.cells_mapper.SetInputConnection(self.clipXY.GetOutputPort())
            if self.show_yz_clip:
                clipped_cells_flag = True
                self.clipYZ.SetInputData(polydata)
                # self.planeYZ.SetOrigin(0,0,0)
                self.clipYZ.SetClipFunction(self.planeYZ)
                self.clipYZ.Update()
                polydata = self.clipYZ.GetOutput()
                self.cells_mapper.SetInputConnection(self.clipYZ.GetOutputPort())
            if self.show_xz_clip:
                clipped_cells_flag = True
                self.clipXZ.SetInputData(polydata)
                # self.planeXZ.SetOrigin(0,0,0)
                self.clipXZ.SetClipFunction(self.planeXZ)
                # polydata = self.clipXZ.GetOutput()
                self.clipXZ.Update()
                self.cells_mapper.SetInputConnection(self.clipXZ.GetOutputPort())

            if not clipped_cells_flag:
                # self.cells_mapper = vtkPolyDataMapper()
                self.cells_mapper.SetInputConnection(self.glyph.GetOutputPort())

            self.cells_actor.SetMapper(self.cells_mapper)

            self.ren.AddActor(self.cells_actor)
        else:
            self.ren.RemoveActor(self.cells_actor)

        self.text_title_actor.SetInput(self.title_str)

        #-------------------
        if self.substrates_checked_flag:
            print("substrate names= ",mcds.get_substrate_names())

            field_name = self.substrates_combobox.currentText()
            print("plot_cells3D(): field_name= ",field_name)

            print("plot_cells3D(): self.substrate_name= ",self.substrate_name)
            # sub_name = mcds.get_substrate_names()[0]
            # sub_name = mcds.get_substrate_names()[self.field_index]  # NOoo!
            # self.scalarBar.SetTitle(sub_name)
            self.scalarBar.SetTitle(self.substrate_name)
            # sub_dict = mcds.data['continuum_variables'][sub_name]
            if (len(self.substrate_name) == 0) or (self.substrate_name not in mcds.data['continuum_variables']):
                print(f" ---  ERROR: substrate={self.substrate_name} is not valid.")
                return

            sub_dict = mcds.data['continuum_variables'][self.substrate_name]
            sub_concentration = sub_dict['data']
            print("sub_concentration.shape= ",sub_concentration.shape)
            print("np.min(sub_concentration)= ",np.min(sub_concentration))
            print("np.max(sub_concentration)= ",np.max(sub_concentration))
            # print("sub_concentration = ",sub_concentration)

            # update VTK pipeline
            # self.points.Reset()
            # self.cellID.Reset()

            # self.substrate_voxel_scalars.Reset()  # rwh: OMG, why didn't this work? Optimize.
            self.substrate_voxel_scalars = vtkFloatArray()

            # self.cell_data.Reset()
            # self.tags.Reset()

            # print("\n\n---------  doing 3D substrate as vtkStructuredPoints\n")
            # nx,ny,nz = 12,12,12
            # nx,ny,nz = 3,3,3
            nx,ny,nz = sub_concentration.shape
            print("nx,ny,nz = ",nx,ny,nz)
            self.substrate_data.SetDimensions( nx+1, ny+1, nz+1 )
            # self.substrate_data.SetDimensions( nx, ny, nz )
            voxel_size = 20   # rwh: fix
            x0 = -(voxel_size * nx) / 2.0
            y0 = -(voxel_size * ny) / 2.0
            z0 = -(voxel_size * nz) / 2.0
            print("x0,y0,z0 = ",x0,y0,z0)

            # Check to see if the (possible) files in the output dir match that of the Config tab specs
            # rwh: more tests to do though (put all these in a function)
            if x0 != float(self.config_tab.xmin.text()):
                print(f'vis3D_tab.py: Error: x0 {x0} is different than the Config tab {self.config_tab.xmin.text()}.')
                return
            if y0 != float(self.config_tab.ymin.text()):
                print(f'vis3D_tab.py: Error: y0 {y0} is different than the Config tab {self.config_tab.ymin.text()}.')
                return
            if z0 != float(self.config_tab.zmin.text()):
                print(f'vis3D_tab.py: Error: z0 {z0} is different than the Config tab {self.config_tab.zmin.text()}.')
                return

            self.substrate_data.SetOrigin( x0, y0, z0 )
            self.substrate_data.SetSpacing( voxel_size, voxel_size, voxel_size )
            vmin = 1.e30
            vmax = -vmin
            # for z in range( 0, nz+1 ) :  # if point data, not cell data
            kount = 0

            # optimize?
            for z in range( 0, nz ) :   # NOTE: using cell data, not point data
                for y in range( 0, ny ) :
                    for x in range( 0, nx ) :
                        # val = x+y+z + frame    # dummy test
                        # val = sub_concentration[x,y,z] + np.random.uniform()*10
                        # val = sub_concentration[x,y,z] + x

                        # val = sub_concentration[x,y,z]
                        val = sub_concentration[y,x,z]
                        # print(kount,x,y,z,val)
                        # if z==1:
                            # val = 0.0
                        # if z==0:
                        #     val = 1.0
                        if val > vmax:
                            vmax = val
                        if val < vmin:
                            vmin = val
                        self.substrate_voxel_scalars.InsertNextValue( val )
                        kount += 1
            # # self.substrate_data.GetPointData().SetScalars( self.substrate_voxel_scalars )
            # vmin = 10.
            if self.fix_cmap_flag:
                # vmin =  self.field_min_max[field_name][0]
                # vmax =  self.field_min_max[field_name][1]
                # vmin = self.cmin_value
                # vmax = self.cmax_value
                vmin = float(self.cmin.text())
                vmax = float(self.cmax.text())
                print("fixed cmap vmin,vmax = ",vmin,vmax)

            # rwh - so which is correct?
            self.substrate_data.GetCellData().SetScalars( self.substrate_voxel_scalars )

            # apparently, for a contour, we need this:
            # self.substrate_data.GetPointData().SetScalars( self.substrate_voxel_scalars )

            # self.contour.SetInputConnection(self.substrate_data.GetOutputPort())
            # self.contour.SetInputData(self.substrate_data)   # vtkStructuredPoints()
            # cval = 0.9
            # self.contour.SetValue(0, cval)
            # self.contour.Update()
            # self.contMapper.SetScalarModeToUseCellData()
            # self.contMapper.Update()
            # self.contActor.Update()

            # print("vmax= ",vmax)
            print("---vmin,vmax= ",vmin,vmax)
            # if 'internalized_total_substrates' in mcds.data['discrete_cells'].keys():
            #     print("intern_sub= ",mcds.data['discrete_cells']['internalized_total_substrates'])

            # if self.show_voxels or self.show_xy_slice or self.show_yz_slice or self.show_xz_slice:
            #     self.ren.RemoveActor2D(self.scalarBar)
            #     self.ren.AddActor2D(self.scalarBar)
            # else:
            #     self.ren.RemoveActor2D(self.scalarBar)

            if self.show_voxels:
                self.ren.RemoveActor(self.substrate_actor)

                print("----- show_voxels: vmin,vmax= ",vmin,vmax)
                self.substrate_mapper.SetScalarRange(vmin, vmax)
                # self.substrate_mapper.SetScalarModeToUseCellData()
                self.substrate_mapper.Update()

                # self.substrate_actor.GetProperty().SetRepresentationToWireframe()
                self.ren.AddActor(self.substrate_actor)
                self.scalarBar.SetLookupTable(self.substrate_mapper.GetLookupTable())


            if self.show_xy_slice:
                # self.ren.RemoveActor(self.substrate_actor)
                self.ren.RemoveActor(self.cutterXYActor)
                # self.ren.RemoveActor2D(self.scalarBar)

                self.cutterXY.SetInputData(self.substrate_data)
                # self.cutterXY.SetInputData(self.glyph.GetOutput())
                self.planeXY.SetOrigin(x0,y0,0)
                self.cutterXY.SetCutFunction(self.planeXY)
                # self.cutterXY.SetInputData(self.substrate_data.GetCellData())  # error; reqs vtkDO
                self.cutterXY.Update()

                self.cutterXYMapper.SetScalarRange(vmin, vmax)
                self.cutterXYMapper.SetLookupTable(self.lut_substrate)
                # self.cutterXYMapper.SetScalarRange(0, vmax)
                self.cutterXYMapper.Update()
                # cutMapper.SetInputConnection(planeCut.GetOutputPort())
                # cutMapper.SetScalarRange(sg.GetPointData().GetScalars().GetRange())

                # self.cutterXYMapper.SetScalarRange(0, vmax)
                # self.cutterXYMapper.SetScalarModeToUseCellData()
                # self.cutterXYActor.SetMapper(self.cutterXYMapper)

                self.cutterXYActor.GetProperty().EdgeVisibilityOn()
                self.cutterXYActor.GetProperty().EdgeVisibilityOff()
                # self.cutterXYActor.GetProperty().SetEdgeColor(0,0,0)

                self.ren.AddActor(self.cutterXYActor)

                # self.ren.AddActor(self.contActor)

                # self.cutterXYEdges = vtkFeatureEdges()
                # self.cutterXYEdges.SetInputConnection(self.cutterXY.GetOutputPort())
                # self.cutterXYEdges.SetInput(self.cutterXY.GetOutputPort())
                # self.cutterXYEdges.Update()
                # self.ren.AddActor(self.cutterXYEdgesActor)

                #-------------------
                self.scalarBar.SetLookupTable(self.cutterXYMapper.GetLookupTable())
                # self.scalarBar.SetLookupTable(self.cells_mapper.GetLookupTable())  # debug: show cell colors

                # self.scalarBar.SetLookupTable(self.substrate_mapper.GetLookupTable())
                # self.ren.AddActor2D(self.scalarBar)


            if self.show_yz_slice:
                self.ren.RemoveActor(self.cutterYZActor)
                # self.ren.RemoveActor2D(self.scalarBar)

                self.cutterYZ.SetInputData(self.substrate_data)
                self.planeYZ.SetOrigin(0,y0,z0)
                self.cutterYZ.SetCutFunction(self.planeYZ)
                # self.cutterXY.SetInputData(self.substrate_data.GetCellData())  # error; reqs vtkDO
                self.cutterYZ.Update()

                self.cutterYZMapper.SetScalarRange(vmin, vmax)
                self.cutterYZMapper.SetLookupTable(self.lut_substrate)
                # self.cutterYZMapper.SetScalarRange(0, vmax)
                self.cutterYZMapper.Update()

                self.cutterYZActor.GetProperty().EdgeVisibilityOn()
                self.cutterYZActor.GetProperty().EdgeVisibilityOff()
                # self.cutterYZActor.GetProperty().SetEdgeColor(0,0,0)

                self.ren.AddActor(self.cutterYZActor)
                self.scalarBar.SetLookupTable(self.cutterYZMapper.GetLookupTable())
                # self.ren.AddActor2D(self.scalarBar)

            if self.show_xz_slice:
                self.ren.RemoveActor(self.cutterXZActor)
                # self.ren.RemoveActor2D(self.scalarBar)

                self.cutterXZ.SetInputData(self.substrate_data)
                self.planeXZ.SetOrigin(x0,0,z0)
                self.cutterXZ.SetCutFunction(self.planeXZ)
                # self.cutterXY.SetInputData(self.substrate_data.GetCellData())  # error; reqs vtkDO
                self.cutterXZ.Update()

                self.cutterXZMapper.SetScalarRange(vmin, vmax)
                self.cutterXZMapper.SetLookupTable(self.lut_substrate)
                # self.cutterXZMapper.SetScalarRange(0, vmax)
                self.cutterXZMapper.Update()

                self.cutterXZActor.GetProperty().EdgeVisibilityOn()
                self.cutterXZActor.GetProperty().EdgeVisibilityOff()
                # self.cutterXZActor.GetProperty().SetEdgeColor(0,0,0)

                self.ren.AddActor(self.cutterXZActor)
                self.scalarBar.SetLookupTable(self.cutterXZMapper.GetLookupTable())
                # self.ren.AddActor2D(self.scalarBar)


            #-------------------
            # self.domain_outline = vtkOutlineFilter()
            self.domain_outline.SetInputData(self.substrate_data)
            self.domain_outline.Update()
            # self.domain_outline.SetInputConnection(sample.GetOutputPort())
            # self.domain_outline.SetInputConnection(self.substrate_data.GetOutputPort())

            # self.domain_outline_mapper.Update()
            # # self.domain_outline_mapper = vtkPolyDataMapper()
            # self.domain_outline_mapper.SetInputConnection(self.domain_outline.GetOutputPort())

            # # self.domain_outline_actor = vtkActor()
            # self.domain_outline_actor.SetMapper(self.domain_outline_mapper)
            # self.domain_outline_actor.GetProperty().SetColor(0,0,0)
            self.domain_outline_actor.GetProperty().SetColor(0, 0, 0)
            self.ren.AddActor(self.domain_outline_actor)


            self.ren.RemoveActor2D(self.scalarBar)
            if self.show_voxels or self.show_xy_slice or self.show_yz_slice or self.show_xz_slice:
                # self.ren.RemoveActor2D(self.scalarBar)
                self.ren.AddActor2D(self.scalarBar)
            # else:
            #     self.ren.RemoveActor2D(self.scalarBar)
            # self.ren.AddActor2D(self.scalarBar)

        else:
            self.ren.RemoveActor(self.substrate_actor)
            self.ren.RemoveActor(self.cutterXYActor)
            self.ren.RemoveActor(self.cutterYZActor)
            self.ren.RemoveActor(self.cutterXZActor)

            # self.ren.RemoveActor(self.clipXYActor)
            self.ren.RemoveActor(self.domain_outline_actor)
            self.ren.RemoveActor2D(self.scalarBar)



        # if self.axes_actor is None:
        if self.show_axes:
            print("------- showing axes_actor")
            self.ren.RemoveActor(self.axes_actor)
            self.axes_actor = vtkAxesActor()
            self.axes_actor.SetShaftTypeToCylinder()
            # subjective scaling
            cradius = self.ymax * 0.001
            self.axes_actor.SetCylinderRadius(cradius)
            self.axes_actor.SetConeRadius(cradius*10)
            laxis = self.ymax + self.ymax * 0.2
            self.axes_actor.SetTotalLength(laxis,laxis,laxis)
            # Change the font size to something reasonable
            # Ref: http://vtk.1045678.n5.nabble.com/VtkAxesActor-Problem-td4311250.html
            fsize = 12
            self.axes_actor.GetXAxisCaptionActor2D().GetTextActor().SetTextScaleMode(vtkTextActor.TEXT_SCALE_MODE_NONE)
            self.axes_actor.GetXAxisCaptionActor2D().GetTextActor().GetTextProperty().SetFontSize(fsize)
            self.axes_actor.GetXAxisCaptionActor2D().GetTextActor().GetTextProperty().ShadowOn()

            self.axes_actor.GetYAxisCaptionActor2D().GetTextActor().SetTextScaleMode(vtkTextActor.TEXT_SCALE_MODE_NONE)
            self.axes_actor.GetYAxisCaptionActor2D().GetTextActor().GetTextProperty().SetFontSize(fsize)
            self.axes_actor.GetYAxisCaptionActor2D().GetTextActor().GetTextProperty().ShadowOn()

            self.axes_actor.GetZAxisCaptionActor2D().GetTextActor().SetTextScaleMode(vtkTextActor.TEXT_SCALE_MODE_NONE)
            self.axes_actor.GetZAxisCaptionActor2D().GetTextActor().GetTextProperty().SetFontSize(fsize)
            self.axes_actor.GetZAxisCaptionActor2D().GetTextActor().GetTextProperty().ShadowOn()
            self.ren.AddActor(self.axes_actor)

    # renderWindow.SetWindowName('PhysiCell model')
        # renderWindow.Render()
        # self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.vtkWidget.GetRenderWindow().Render()
    # renderWindowInteractor.Start()
        return

    def make_axes_actor(self, scale, xyzLabels):
        axes = vtkAxesActor()
        axes.SetScale(scale[0], scale[1], scale[2])
        axes.SetShaftTypeToCylinder()
        axes.SetXAxisLabelText(xyzLabels[0])
        axes.SetYAxisLabelText(xyzLabels[1])
        axes.SetZAxisLabelText(xyzLabels[2])
        axes.SetCylinderRadius(5. * axes.GetCylinderRadius())
        axes.SetConeRadius(1.025 * axes.GetConeRadius())
        axes.SetSphereRadius(10.5 * axes.GetSphereRadius())
        tprop = axes.GetXAxisCaptionActor2D().GetCaptionTextProperty()
        tprop.ItalicOff()
        tprop.ShadowOn()
        tprop.SetFontFamilyToTimes()
        # Use the same text properties on the other two axes.
        axes.GetYAxisCaptionActor2D().GetCaptionTextProperty().ShallowCopy(tprop)
        axes.GetZAxisCaptionActor2D().GetCaptionTextProperty().ShallowCopy(tprop)
        # return axes
        self.axes_actor = axes