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
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,  QMainWindow,QGridLayout, QPushButton, QFileDialog, QMessageBox, QStackedWidget

import numpy as np
import scipy.io
# from pyMCDS_cells import pyMCDS_cells
from pyMCDS import pyMCDS

class Vis(QWidget):

    def __init__(self, nanohub_flag):
        super().__init__()
        # global self.config_params

        self.config_tab = None

        self.show_xy_plane = True
        self.show_yz_plane = True
        self.show_xz_plane = True
        self.show_voxels = False

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

        lut_heat = self.get_heat_map()
        self.substrate_mapper = vtkDataSetMapper()
        self.substrate_mapper.SetInputData(self.substrate_data)
        self.substrate_mapper.SetLookupTable(lut_heat)
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
        self.cutterXYMapper.SetLookupTable(lut_heat)
        self.cutterXYMapper.SetScalarModeToUseCellData()
        # self.cutterXYMapper.SetScalarModeToUsePointData()
        #self.cutterMapper.SetScalarRange(0, vmax)

        self.cutterXYActor = vtkActor()
        self.cutterXYActor.SetMapper(self.cutterXYMapper)

        #-----
        self.planeYZ = vtkPlane()
        self.planeYZ.SetOrigin(0,0,0)
        self.planeYZ.SetNormal(1, 0, 0)

        self.cutterYZ = vtkCutter()

        self.cutterYZMapper = vtkPolyDataMapper()
        self.cutterYZMapper.SetInputConnection(self.cutterYZ.GetOutputPort())
        self.cutterYZMapper.ScalarVisibilityOn()
        # lut = self.get_heat_map()
        self.cutterYZMapper.SetLookupTable(lut_heat)
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
        self.cutterXZMapper.SetLookupTable(lut_heat)
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
        self.scalarBar = vtkScalarBarActor()
        self.scalarBar.SetTitle("oxygen")
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

        self.plot_svg_flag = True
        # self.plot_svg_flag = False
        self.field_index = 4  # substrate (0th -> 4 in the .mat)

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


        #-------------------------------------------
        label_width = 110
        domain_value_width = 100
        value_width = 60
        label_height = 20
        units_width = 70

        self.substrates_cbox = QComboBox(self)
        # self.substrates_cbox.setEnabled(self.substrates_checked_flag)

        self.myscroll = QScrollArea()  # might contain centralWidget
        self.create_figure()

        self.config_params = QWidget()

        self.main_layout = QVBoxLayout()

        self.vbox = QVBoxLayout()
        self.vbox.addStretch(0)

        self.stackw = QStackedWidget()

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

        # self.first_button = QPushButton("|<")
        # self.first_button.clicked.connect(self.first_plot_cb)
        # controls_hbox.addWidget(self.first_button)

        # self.back_button = QPushButton("<")
        # self.back_button.clicked.connect(self.back_plot_cb)
        # controls_hbox.addWidget(self.back_button)

        # self.forward_button = QPushButton(">")
        # self.forward_button.clicked.connect(self.forward_plot_cb)
        # controls_hbox.addWidget(self.forward_button)

        # self.last_button = QPushButton(">|")
        # self.last_button.clicked.connect(self.last_plot_cb)
        # controls_hbox.addWidget(self.last_button)

        # self.play_button = QPushButton("Play")
        # self.play_button.setStyleSheet("background-color : lightgreen")
        # # self.play_button.clicked.connect(self.play_plot_cb)
        # self.play_button.clicked.connect(self.animate)
        # controls_hbox.addWidget(self.play_button)

        # # self.prepare_button = QPushButton("Prepare")
        # # self.prepare_button.clicked.connect(self.prepare_plot_cb)
        # # controls_hbox.addWidget(self.prepare_button)

        # self.cells_checkbox = QCheckBox('Cells')
        # self.cells_checkbox.setChecked(True)
        # self.cells_checkbox.clicked.connect(self.cells_toggle_cb)
        # self.cells_checked_flag = True

        # self.substrates_checkbox = QCheckBox('Substrates')
        # self.substrates_checkbox.setEnabled(False)
        # self.substrates_checkbox.setChecked(False)
        # self.substrates_checkbox.clicked.connect(self.substrates_toggle_cb)
        # self.substrates_checked_flag = False
        

        # hbox = QHBoxLayout()
        # hbox.addWidget(self.cells_checkbox)
        # hbox.addWidget(self.substrates_checkbox)
        # controls_hbox.addLayout(hbox)

        #---------------------------------------------------
        self.controls1 = QWidget()
        self.glayout1 = QGridLayout()
        self.controls1.setLayout(self.glayout1)

        arrow_button_width = 50
        self.first_button = QPushButton("|<")
        self.first_button.setFixedWidth(arrow_button_width)
        self.first_button.clicked.connect(self.first_plot_cb)
        # controls_hbox.addWidget(self.first_button)
        icol = 0
        self.glayout1.addWidget(self.first_button, 0,icol,1,1) # w, row, column, rowspan, colspan

        self.back_button = QPushButton("<")
        self.back_button.setFixedWidth(arrow_button_width)
        self.back_button.clicked.connect(self.back_plot_cb)
        # controls_hbox.addWidget(self.back_button)
        icol += 1
        self.glayout1.addWidget(self.back_button, 0,icol,1,1) # w, row, column, rowspan, colspan

        frame_count_width = 40
        self.frame_count = QLineEdit()
        # self.frame_count.textChanged.connect(self.change_frame_count_cb)  # do later to appease the callback gods
        self.frame_count.setFixedWidth(frame_count_width)
        self.frame_count.setValidator(QtGui.QIntValidator(0,10000000))
        self.frame_count.setText('0')
        icol += 1
        self.glayout1.addWidget(self.frame_count, 0,icol,1,1) # w, row, column, rowspan, colspan


        self.forward_button = QPushButton(">")
        self.forward_button.setFixedWidth(arrow_button_width)
        self.forward_button.clicked.connect(self.forward_plot_cb)
        # controls_hbox.addWidget(self.forward_button)
        icol += 1
        self.glayout1.addWidget(self.forward_button, 0,icol,1,1) # w, row, column, rowspan, colspan

        self.last_button = QPushButton(">|")
        self.last_button.setFixedWidth(arrow_button_width)
        self.last_button.clicked.connect(self.last_plot_cb)
        # controls_hbox.addWidget(self.last_button)
        icol += 1
        self.glayout1.addWidget(self.last_button, 0,icol,1,1) # w, row, column, rowspan, colspan

        self.play_button = QPushButton("Play")
        self.play_button.setFixedWidth(70)
        self.play_button.setStyleSheet("background-color : lightgreen")
        # self.play_button.clicked.connect(self.play_plot_cb)
        self.play_button.clicked.connect(self.animate)
        # controls_hbox.addWidget(self.play_button)
        icol += 1
        self.glayout1.addWidget(self.play_button, 0,icol,1,1) # w, row, column, rowspan, colspan

        # self.prepare_button = QPushButton("Prepare")
        # self.prepare_button.clicked.connect(self.prepare_plot_cb)
        # controls_hbox.addWidget(self.prepare_button)

        self.cells_checkbox = QCheckBox('Cells')
        self.cells_checkbox.setChecked(True)
        self.cells_checkbox.clicked.connect(self.cells_toggle_cb)
        self.cells_checked_flag = True
        # self.glayout1.addWidget(self.cells_checkbox, 0,5,1,2) # w, row, column, rowspan, colspan
        icol += 1
        self.glayout1.addWidget(self.cells_checkbox, 0,icol,1,1) # w, row, column, rowspan, colspan

        # self.cells_edge_checkbox = QCheckBox('edge')
        # self.cells_edge_checkbox.setChecked(True)
        # self.cells_edge_checkbox.clicked.connect(self.cells_edge_toggle_cb)
        # self.cells_edge_checked_flag = True
        # icol += 1
        # self.glayout1.addWidget(self.cells_edge_checkbox, 0,icol,1,1) # w, row, column, rowspan, colspan

        self.substrates_checkbox = QCheckBox('Substrates')
        self.substrates_checked_flag = True
        self.substrates_checkbox.setChecked(self.substrates_checked_flag)
        # self.substrates_checkbox.setEnabled(False)
        self.substrates_checkbox.clicked.connect(self.substrates_toggle_cb)
        icol += 1
        self.glayout1.addWidget(self.substrates_checkbox, 0,icol,1,2) # w, row, column, rowspan, colspan

        self.fix_cmap_checkbox = QCheckBox('fix')
        self.fix_cmap_flag = False
        self.fix_cmap_checkbox.setEnabled(self.substrates_checked_flag)
        # self.fix_cmap_checkbox.setEnabled(True)
        self.fix_cmap_checkbox.setChecked(self.fix_cmap_flag)
        self.fix_cmap_checkbox.clicked.connect(self.fix_cmap_toggle_cb)
        icol += 2
        self.glayout1.addWidget(self.fix_cmap_checkbox, 0,icol,1,1) # w, row, column, rowspan, colspan

        cvalue_width = 70
        label = QLabel("cmin")
        # label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.cmin = QLineEdit()
        self.cmin.setEnabled(self.substrates_checked_flag)
        self.cmin.setEnabled(False)
        self.cmin.setText('0.0')
        # self.cmin.textChanged.connect(self.change_plot_range)
        self.cmin.returnPressed.connect(self.cmin_cmax_cb)
        self.cmin.setFixedWidth(cvalue_width)
        self.cmin.setValidator(QtGui.QDoubleValidator())
        self.cmin.setEnabled(False)
        icol += 1
        self.glayout1.addWidget(label, 0,icol,1,1) # w, row, column, rowspan, colspan
        icol += 1
        self.glayout1.addWidget(self.cmin, 0,icol,1,1) # w, row, column, rowspan, colspan

        label = QLabel("cmax")
        # label.setFixedWidth(label_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.cmax = QLineEdit()
        self.cmax.setEnabled(self.substrates_checked_flag)
        self.cmax.setEnabled(False)
        self.cmax.setText('1.0')
        self.cmax.returnPressed.connect(self.cmin_cmax_cb)
        self.cmax.setFixedWidth(cvalue_width)
        self.cmax.setValidator(QtGui.QDoubleValidator())
        self.cmax.setEnabled(False)
        icol += 1
        self.glayout1.addWidget(label, 0,icol,1,1) # w, row, column, rowspan, colspan
        icol += 1
        self.glayout1.addWidget(self.cmax, 0,icol,1,1) # w, row, column, rowspan, colspan

        icol += 1
        self.glayout1.addWidget(self.substrates_cbox, 0,icol,1,2) # w, row, column, rowspan, colspan
        
        #-----------
        self.frame_count.textChanged.connect(self.change_frame_count_cb)

        #-------------------
        # controls_hbox2 = QHBoxLayout()
        # visible_flag = True

        # label = QLabel("xmin")
        # label.setFixedWidth(label_width)
        # label.setAlignment(QtCore.Qt.AlignRight)
        # controls_hbox2.addWidget(label)
        # self.my_xmin = QLineEdit()
        # self.my_xmin.textChanged.connect(self.change_plot_range)
        # self.my_xmin.setFixedWidth(domain_value_width)
        # self.my_xmin.setValidator(QtGui.QDoubleValidator())
        # controls_hbox2.addWidget(self.my_xmin)
        # self.my_xmin.setVisible(visible_flag)

        # label = QLabel("xmax")
        # label.setFixedWidth(label_width)
        # label.setAlignment(QtCore.Qt.AlignRight)
        # controls_hbox2.addWidget(label)
        # self.my_xmax = QLineEdit()
        # self.my_xmax.textChanged.connect(self.change_plot_range)
        # self.my_xmax.setFixedWidth(domain_value_width)
        # self.my_xmax.setValidator(QtGui.QDoubleValidator())
        # controls_hbox2.addWidget(self.my_xmax)
        # self.my_xmax.setVisible(visible_flag)

        # label = QLabel("ymin")
        # label.setFixedWidth(label_width)
        # label.setAlignment(QtCore.Qt.AlignRight)
        # controls_hbox2.addWidget(label)
        # self.my_ymin = QLineEdit()
        # self.my_ymin.textChanged.connect(self.change_plot_range)
        # self.my_ymin.setFixedWidth(domain_value_width)
        # self.my_ymin.setValidator(QtGui.QDoubleValidator())
        # controls_hbox2.addWidget(self.my_ymin)
        # self.my_ymin.setVisible(visible_flag)

        # label = QLabel("ymax")
        # label.setFixedWidth(label_width)
        # label.setAlignment(QtCore.Qt.AlignRight)
        # controls_hbox2.addWidget(label)
        # self.my_ymax = QLineEdit()
        # self.my_ymax.textChanged.connect(self.change_plot_range)
        # self.my_ymax.setFixedWidth(domain_value_width)
        # self.my_ymax.setValidator(QtGui.QDoubleValidator())
        # controls_hbox2.addWidget(self.my_ymax)
        # self.my_ymax.setVisible(visible_flag)

        # w = QPushButton("Reset")
        # w.clicked.connect(self.reset_plot_range)
        # controls_hbox2.addWidget(w)

        # self.my_xmin.setText(str(self.xmin))
        # self.my_xmax.setText(str(self.xmax))
        # self.my_ymin.setText(str(self.ymin))
        # self.my_ymax.setText(str(self.ymax))

        #-------------------
        # self.substrates_cbox = QComboBox(self)
        # self.substrates_cbox.setGeometry(200, 150, 120, 40)
  
        # self.substrates_cbox.addItem("substrate1")
        # self.substrates_cbox.addItem("substrate2")
        self.substrates_cbox.setEnabled(self.substrates_checked_flag)
        self.substrates_cbox.currentIndexChanged.connect(self.substrates_cbox_changed_cb)

        # controls_hbox.addWidget(self.substrates_cbox)

        # self.layout = QVBoxLayout(self)

        self.stackw.addWidget(self.controls1)
        # self.stackw.addWidget(self.controls2)
        # self.stackw.addWidget(self.controls3)

        self.stackw.setCurrentIndex(0)
        self.stackw.setFixedHeight(40)
        # self.stackw.resize(700,100)
        # self.layout.addWidget(self.stackw)

        # controls_vbox = QVBoxLayout()
        # controls_vbox.addLayout(self.stackw)

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
        self.layout.addWidget(self.stackw)
        self.layout.addWidget(self.myscroll)

        # self.create_figure()


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

    def fill_substrates_combobox(self, substrate_list):
        print("vis3D_tab.py: ------- fill_substrates_combobox")
        print("substrate_list = ",substrate_list )
        self.substrates_cbox.clear()
        for s in substrate_list:
            # print(" --> ",s)
            self.substrates_cbox.addItem(s)
        # self.substrates_cbox.setCurrentIndex(2)  # not working; gets reset to oxygen somehow after a Run

    def xy_plane_toggle_cb(self,flag):
        self.show_xy_plane = flag
        if flag:
            self.ren.AddActor(self.cutterXYActor)
        else:
            self.ren.RemoveActor(self.cutterXYActor)

    def yz_plane_toggle_cb(self,flag):
        self.show_yz_plane = flag
        if flag:
            self.ren.AddActor(self.cutterYZActor)
        else:
            self.ren.RemoveActor(self.cutterYZActor)

    def xz_plane_toggle_cb(self,flag):
        self.show_xz_plane = flag
        if flag:
            self.ren.AddActor(self.cutterXZActor)
        else:
            self.ren.RemoveActor(self.cutterXZActor)

    def voxels_toggle_cb(self,flag):
        self.show_voxels = flag
        if flag:
            self.ren.AddActor(self.substrate_actor)
        else:
            self.ren.RemoveActor(self.substrate_actor)


    def substrates_cbox_changed_cb(self,idx):
        print("----- vis3D_tab.py: substrates_cbox_changed_cb: idx = ",idx)
        self.field_index = idx 
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
                self.substrates_cbox.clear()
                print("sub_names = ",sub_names)
                self.substrates_cbox.addItems(sub_names)


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
        field_name = self.substrates_cbox.currentText()
        print("field_name= ",field_name)
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
        print("\n--------- create_figure(): ------- creating figure, canvas, ax0")
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
        self.text_title_actor.GetTextProperty().SetFontSize(10)

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
    def get_heat_map(self):
        table_size = 512
        lut = vtkLookupTable()
        lut.SetNumberOfTableValues(table_size)
        # lut.SetHueRange(0.0, 0.667)  # red-to-blue
        lut.SetHueRange( 0.667, 0.)  # blue-to-red
        lut.Build()
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
        print("plot_cells3D:  frame= ",frame)
        self.frame_count.setText(str(frame))
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
        mcds = pyMCDS(xml_file, self.output_dir)   # will read in BOTH cells and substrates info
        current_time = mcds.get_time()
        print('time=', current_time )

        self.title_str = 'time '+ str(current_time) + ' min'
        # self.text_title_actor.SetInput(self.title_str)

        #-----------
        if self.cells_checked_flag:
            # mcds = pyMCDS_cells(xml_file, 'tmpdir')  
            # mcds = pyMCDS_cells(xml_file, 'output')  
            # mcds = pyMCDS(xml_file, 'output')  

            # print("mcds.data dict_keys= ",mcds.data['discrete_cells'].keys())   # dict_keys(...)

            ncells = len(mcds.data['discrete_cells']['ID'])
            print('ncells=', ncells)
            self.title_str += ", # cells=" + str(ncells)

            global xyz
            xyz = np.zeros((ncells, 3))
            xyz[:, 0] = mcds.data['discrete_cells']['position_x']
            xyz[:, 1] = mcds.data['discrete_cells']['position_y']
            xyz[:, 2] = mcds.data['discrete_cells']['position_z']
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

            cell_type = mcds.data['discrete_cells']['cell_type']
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
                x= mcds.data['discrete_cells']['position_x'][idx]
                y= mcds.data['discrete_cells']['position_y'][idx]
                z= mcds.data['discrete_cells']['position_z'][idx]
                id = mcds.data['discrete_cells']['cell_type'][idx]
                self.points.InsertNextPoint(x, y, z)
                # self.cellVolume.InsertNextValue(30.0 + 2*idx)
                total_volume = mcds.data['discrete_cells']['total_volume'][idx]
                # self.cellVolume.InsertNextValue(1.0 + 2*idx)

                # rval = (total_volume*3/4/pi)**1/3
                rval = (total_volume * 0.2387) ** 0.333333
                # print(idx,") total_volume= ", total_volume, ", rval=",rval )
                # self.cellID.InsertNextValue(id)
                self.radii.InsertNextValue(rval)
                # self.tags.InsertNextValue(float(idx)/ncells)   # multicolored; heatmap across all cells

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

            # actor.GetProperty().SetCoatRoughness (0.5)
            # actor.GetProperty().SetCoatRoughness (0.2)
            # actor.GetProperty().SetCoatRoughness (1.0)

            # renderer = vtkRenderer()
            # amval = 1.0  # default
            # renderer.SetAmbient(amval, amval, amval)

            # renderWindow = vtkRenderWindow()
            # renderWindow.SetPosition(100,100)
            # renderWindow.SetSize(1400,1200)
            # renderWindow.AddRenderer(renderer)
            # renderWindowInteractor = vtkRenderWindowInteractor()
            # renderWindowInteractor.SetRenderWindow(renderWindow)

            # renderer.AddActor(actor)
            # self.cells_actor.GetProperty().SetColor(80, 20, 20)
            self.ren.AddActor(self.cells_actor)
        else:
            self.ren.RemoveActor(self.cells_actor)

        self.text_title_actor.SetInput(self.title_str)
        #-------------------
        if self.substrates_checked_flag:

            print("substrate names= ",mcds.get_substrate_names())
            # sub_name = mcds.get_substrate_names()[0]
            sub_name = mcds.get_substrate_names()[self.field_index]
            self.scalarBar.SetTitle(sub_name)
            sub_dict = mcds.data['continuum_variables'][sub_name]
            sub_concentration = sub_dict['data']
            print("sub_concentration.shape= ",sub_concentration.shape)
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

            # if self.show_voxels or self.show_xy_plane or self.show_yz_plane or self.show_xz_plane:
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


            if self.show_xy_plane:
                # self.ren.RemoveActor(self.substrate_actor)
                self.ren.RemoveActor(self.cutterXYActor)
                # self.ren.RemoveActor2D(self.scalarBar)

                self.cutterXY.SetInputData(self.substrate_data)
                self.planeXY.SetOrigin(x0,y0,0)
                self.cutterXY.SetCutFunction(self.planeXY)
                # self.cutterXY.SetInputData(self.substrate_data.GetCellData())  # error; reqs vtkDO
                self.cutterXY.Update()

                self.cutterXYMapper.SetScalarRange(vmin, vmax)
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


            if self.show_yz_plane:
                self.ren.RemoveActor(self.cutterYZActor)
                # self.ren.RemoveActor2D(self.scalarBar)

                self.cutterYZ.SetInputData(self.substrate_data)
                self.planeYZ.SetOrigin(0,y0,z0)
                self.cutterYZ.SetCutFunction(self.planeYZ)
                # self.cutterXY.SetInputData(self.substrate_data.GetCellData())  # error; reqs vtkDO
                self.cutterYZ.Update()

                self.cutterYZMapper.SetScalarRange(vmin, vmax)
                # self.cutterYZMapper.SetScalarRange(0, vmax)
                self.cutterYZMapper.Update()

                self.cutterYZActor.GetProperty().EdgeVisibilityOn()
                self.cutterYZActor.GetProperty().EdgeVisibilityOff()
                # self.cutterYZActor.GetProperty().SetEdgeColor(0,0,0)

                self.ren.AddActor(self.cutterYZActor)
                self.scalarBar.SetLookupTable(self.cutterYZMapper.GetLookupTable())
                # self.ren.AddActor2D(self.scalarBar)

            if self.show_xz_plane:
                self.ren.RemoveActor(self.cutterXZActor)
                # self.ren.RemoveActor2D(self.scalarBar)

                self.cutterXZ.SetInputData(self.substrate_data)
                self.planeXZ.SetOrigin(x0,0,z0)
                self.cutterXZ.SetCutFunction(self.planeXZ)
                # self.cutterXY.SetInputData(self.substrate_data.GetCellData())  # error; reqs vtkDO
                self.cutterXZ.Update()

                self.cutterXZMapper.SetScalarRange(vmin, vmax)
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
            if self.show_voxels or self.show_xy_plane or self.show_yz_plane or self.show_xz_plane:
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
            self.ren.RemoveActor(self.domain_outline_actor)
            self.ren.RemoveActor2D(self.scalarBar)


        self.vtkWidget.GetRenderWindow().Render()

        # self.ren.ResetCamera()
        # renderer.SetBackground(colors.GetColor3d('SlateGray'))  # Background Slate Gray

    # renderWindow.SetWindowName('PhysiCell model')
    # renderWindow.Render()
    # renderWindowInteractor.Start()
        return
