"""
vis3D_tab.py - provide 3D visualization on Plot tab. Still a work in progress. Requires vtk module (pip installable).

    This module uses (Python-wrapped) VTK to perform visualization. If you want to contribute and are 
    unfamiliar with VTK, just approach it as you would any library - read intro docs, find some simple tutorials, 
    and build up your knowledge. In a nutshell, it uses pipelines: data -> filter -> mapper -> actor -> vis.
    The Python API makes things much easier than C++. Also, reach out to the vast VTK community on discourse.
    

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
import glob
import inspect

from vis_base import VisBase

from vtk import *
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QWidget,QCheckBox,QComboBox,QVBoxLayout,QLabel,QMessageBox

import numpy as np
import scipy.io
from pyMCDS import pyMCDS

#----------------------------------------------------------------------
class Vis(VisBase, QWidget):

    def __init__(self, studio_flag, rules_flag, nanohub_flag, config_tab, microenv_tab, celldef_tab, user_params_tab, rules_tab, ics_tab, run_tab, model3D_flag, tensor_flag, ecm_flag):

        super(Vis,self).__init__(studio_flag=studio_flag, rules_flag=rules_flag,  nanohub_flag=nanohub_flag, config_tab=config_tab, microenv_tab=microenv_tab, celldef_tab=celldef_tab, user_params_tab=user_params_tab, rules_tab=rules_tab, ics_tab=ics_tab, run_tab=run_tab, model3D_flag=model3D_flag,tensor_flag=tensor_flag, ecm_flag=ecm_flag)

        self.figure = None

        # self.model3D_flag = model3D_flag

        self.voxel_size = None

        self.plot_cells_svg = False  # used for PhysiBoSS checkbox

        # self.config_tab = None
        # self.run_tab = run_tab

        # self.population_plot = None
        self.celltype_name = []
        self.celltype_color = []
        self.lut_discrete = None

        self.cell_scalars_l = []
        self.cell_scalar_min = 0.0
        self.cell_scalar_max = 1.0

        self.boundary_checked_flag = True

        self.axes_actor = None
        self.show_xy_slice = True
        self.show_yz_slice = True
        self.show_xz_slice = True
        self.show_voxels = False
        self.show_contour = False
        self.show_axes = False
        self.sphere_res = 8

        self.show_xy_clip = False
        self.show_yz_clip = False
        self.show_xz_clip = False

        self.xy_flip = False
        self.xz_flip = False
        self.yz_flip = False

        # TODO: assumes centroid is at origin; fix
        self.xy_slice_z0 = 0.
        self.yz_slice_x0 = 0.
        self.xz_slice_y0 = 0.

        self.xy_clip_z0 = 0.
        self.yz_clip_x0 = 0.
        self.xz_clip_y0 = 0.

        self.contour_value = 1.0

        self.line_width = 3

        self.colors = vtkNamedColors()

        self.substrate_name = ""
        # self.lut_jet = self.get_jet_map(False)
        # self.lut_jet_r = self.get_jet_map(True)

        # self.lut_viridis = self.get_viridis_map(False)
        # self.lut_viridis_r = self.get_viridis_map(True)

        # self.lut_ylorrd = self.get_ylorrd_map(False)
        # self.lut_ylorrd_r = self.get_ylorrd_map(True)
        # # self.lut_substrate = self.get_jet_map()

        #------------
        self.lut_substrate_jet = self.get_jet_map(False)
        self.lut_substrate_jet_r = self.get_jet_map(True)

        self.lut_substrate_viridis = self.get_viridis_map(False)
        self.lut_substrate_viridis_r = self.get_viridis_map(True)

        self.lut_substrate_ylorrd = self.get_ylorrd_map(False)
        self.lut_substrate_ylorrd_r = self.get_ylorrd_map(True)

        # default
        # self.lut_substrate = self.lut_substrate_jet
        self.lut_substrate = self.lut_substrate_ylorrd

        #------------
        # self.lut_cells = self.get_jet_map(False)
        self.lut_cells_jet = self.get_jet_map(False)
        # self.lut_cells = self.lut_substrate_jet
        self.lut_cells_jet_r = self.get_jet_map(True)

        self.lut_cells_viridis = self.get_viridis_map(False)
        self.lut_cells_viridis_r = self.get_viridis_map(True)

        self.lut_cells_ylorrd = self.get_ylorrd_map(False)
        self.lut_cells_ylorrd_r = self.get_ylorrd_map(True)

        # default
        # self.lut_cells = self.lut_cells_jet
        self.lut_cells = self.lut_cells_viridis

        # -------------  VTK pipeline  --------------
        #------  Setup for the cells (rendered as 3D glyphs (spheres))
        # self.outline = vtkOutlineFilter()
        # self.outline.SetInputConnection(source.GetOutputPort())  # self.substrate_data
        # self.outline_mapper = vtkPolyDataMapper()
        # self.outline_mapper.SetInputConnection(self.outline.GetOutputPort())

        # self.show_domain_outline()

        xmax = float(self.config_tab.xmax.text())
        xmin = -xmax
        ymax = float(self.config_tab.ymax.text())
        ymin = -ymax
        zmax = float(self.config_tab.zmax.text())
        zmin = -zmax
        self.domain_diagonal = vtkLineSource()
        self.domain_diagonal.SetPoint1(xmin, ymin, zmin)
        self.domain_diagonal.SetPoint2(xmax, ymax, zmax)

        self.outline = vtkOutlineFilter()
        self.outline.SetInputConnection(self.domain_diagonal.GetOutputPort())

        # Now we'll look at it.
        self.domain_boundary_mapper = vtkPolyDataMapper()
        self.domain_boundary_mapper.SetInputConnection(self.outline.GetOutputPort())
        self.domain_boundary_actor = vtkActor()
        self.domain_boundary_actor.SetMapper(self.domain_boundary_mapper)
        self.domain_boundary_actor.GetProperty().SetColor(0, 0, 0)
        self.domain_boundary_actor.GetProperty().SetLineWidth(self.line_width)


        self.png_writer = vtkPNGWriter()

        #-------------
        self.points = vtkPoints()

        if not self.tensor_flag:
            self.radii = vtkFloatArray()
            self.radii.SetName("radius")
        else:
            self.tensors = vtkFloatArray()
            self.tensors.SetNumberOfComponents(9)
            # self.tensors.SetNumberOfTuples(2)
            # tensors.InsertTuple9(0,  1,0,0,  0,1,0,  0,0,1)
            # tensors.InsertTuple9(1,  1,0,0,  0,2,0,  0,0,3)


        # define the colors for the spheres
        self.tags = vtkFloatArray()
        self.tags.SetName("tag")

        self.cell_data = vtkFloatArray()
        if not self.tensor_flag:
            self.cell_data.SetNumberOfComponents(2)  # (radius, tag)
        else:
            self.cell_data.SetNumberOfComponents(1)  # (tag)
        self.cell_data.SetName("cell_data")

        # construct the unstruct "grid" to contain the cell info
        self.ugrid = vtkUnstructuredGrid()
        self.ugrid.SetPoints(self.points)
        self.ugrid.GetPointData().AddArray(self.cell_data)
        self.ugrid.GetPointData().SetActiveScalars("cell_data")
        if self.tensor_flag:
            self.ugrid.GetPointData().SetTensors(self.tensors)

        self.ugrid_clipped = None

        self.sphereSource = vtkSphereSource()
        self.sphereSource.SetPhiResolution(self.sphere_res)
        self.sphereSource.SetThetaResolution(self.sphere_res)
        self.sphereSource.SetRadius(1.0)

        self.extract_cells_XY = vtkExtractPoints()
        self.extract_cells_YZ = vtkExtractPoints()
        self.extract_cells_XZ = vtkExtractPoints()

        if not self.tensor_flag:
            self.glyph = vtkGlyph3D()
            self.glyph.ClampingOff()
            self.glyph.SetScaleModeToScaleByScalar()
            self.glyph.SetColorModeToColorByScalar()
        else:
            self.glyph = vtkTensorGlyph()
            self.glyph.ColorGlyphsOn()
            self.glyph.ThreeGlyphsOff()
            # if you disable ExtractEigenvalues, the columns of the tensor are taken to be the major/minor axes.
            self.glyph.ExtractEigenvaluesOff()

        self.glyph.SetSourceConnection(self.sphereSource.GetOutputPort())
        self.glyph.SetInputData(self.ugrid)
        self.glyph.SetScaleFactor(1.0)

        self.cells_mapper = vtkPolyDataMapper()
        if not self.tensor_flag:
            self.cells_mapper.SetInputConnection(self.glyph.GetOutputPort())
        else:
            self.normals = vtkPolyDataNormals()
            self.normals.SetInputConnection(self.glyph.GetOutputPort())
            self.cells_mapper.SetInputConnection(self.normals.GetOutputPort())

        # self.cells_mapper.ScalarVisibilityOff()
        self.cells_mapper.ScalarVisibilityOn()
        self.cells_mapper.SetLookupTable(self.lut_cells)
        # self.cells_mapper.SetScalarRange(0., 1.)
        self.cells_mapper.ColorByArrayComponent("cell_data", 1)

        self.cells_actor = vtkActor()
        self.cells_actor.SetMapper(self.cells_mapper)
        print("-- actor defaults:")
        print("-- ambient:",self.cells_actor.GetProperty().GetAmbient())  # 
        print("-- diffuse:",self.cells_actor.GetProperty().GetDiffuse())  # 1.0
        print("-- specular:",self.cells_actor.GetProperty().GetSpecular())  # 0.0
        print("-- roughness:",self.cells_actor.GetProperty().GetCoatRoughness ())  # 0.0
        # self.cells_actor.GetProperty().SetAmbient(0.5)
        # self.cells_actor.GetProperty().SetDiffuse(0.5)
        # self.cells_actor.GetProperty().SetSpecular(0.2)


        #-----------  Now setup for the substrate ----------------
        self.substrate_data = vtkStructuredPoints()
        self.field_index = 0 

        self.substrate_mapper = vtkDataSetMapper()
        self.substrate_mapper.SetInputData(self.substrate_data)
        self.substrate_mapper.SetLookupTable(self.lut_substrate)
        self.substrate_mapper.SetScalarModeToUseCellData()

        self.substrate_actor = vtkActor()
        self.substrate_actor.SetMapper(self.substrate_mapper)

        #-----
        # for substrate slicing
        self.planeXY = vtkPlane()
        self.planeXY.SetOrigin(0,0,0)
        self.planeXY.SetNormal(0, 0, 1)

        # First create the usual cutter
        self.cutterXY = vtkCutter()

        self.cutterXYMapper = vtkPolyDataMapper()
        self.cutterXYMapper.SetInputConnection(self.cutterXY.GetOutputPort())
        self.cutterXYMapper.ScalarVisibilityOn()
        self.cutterXYMapper.SetLookupTable(self.lut_substrate)
        self.cutterXYMapper.SetScalarModeToUseCellData()

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
        self.cutterXZMapper.SetLookupTable(self.lut_substrate)
        self.cutterXZMapper.SetScalarModeToUseCellData()

        self.cutterXZActor = vtkActor()
        self.cutterXZActor.SetMapper(self.cutterXZMapper)

        #-----
        # for substrate isosurface (contour)
        self.c2p = vtkCellDataToPointData()

        self.contour = vtkContourFilter()
        self.contour.SetInputData(self.c2p.GetOutput())
        # self.contour.SetInputData(self.c2p.GetOutput())
        # self.contour.SetValue(0, self.contour_value)

        # self.contour_mapper = vtkDataSetMapper()
        self.contour_mapper = vtkPolyDataMapper()
        self.contour_mapper.SetInputConnection(self.contour.GetOutputPort())
        self.contour_mapper.ScalarVisibilityOn()
        self.contour_mapper.SetLookupTable(self.lut_substrate)
        # self.contour_mapper.SetScalarModeToUseCellData()
        self.contour_mapper.SetScalarModeToUsePointData()

        self.contour_actor = vtkActor()
        self.contour_actor.SetMapper(self.contour_mapper)

        #-----
        self.writer = vtkStructuredPointsWriter()

        #------------------------
        # for cells (glyphs) extraction/clipping/cropping (but leaving entire spherical glyph intact, not cut)
        self.planeXY_clip = vtkPlane()
        self.planeXY_clip.SetOrigin(0,0,0)
        self.planeXY_clip.SetNormal(0, 0, 1)

        self.planeYZ_clip = vtkPlane()
        self.planeYZ_clip.SetOrigin(0,0,0)
        self.planeYZ_clip.SetNormal(1, 0, 0)

        self.planeXZ_clip = vtkPlane()
        self.planeXZ_clip.SetOrigin(0,0,0)
        self.planeXZ_clip.SetNormal(0, 1, 0)

        #-----
        # self.clipXY = vtkClipPolyData()
        # self.clipYZ = vtkClipPolyData()
        # self.clipXZ = vtkClipPolyData()



        #-----
        # -- For substrate
        self.scalar_bar_substrate = vtkScalarBarActor()
        self.scalar_bar_substrate.SetTitle("substrate")
        self.scalar_bar_substrate.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        self.scalar_bar_substrate.GetPositionCoordinate().SetValue(0.01,0.10)
        self.scalar_bar_substrate.UnconstrainedFontSizeOn()
        self.scalar_bar_substrate.SetOrientationToVertical()
        self.scalar_bar_substrate.SetWidth(0.08)
        self.scalar_bar_substrate.SetHeight(0.8)
        self.scalar_bar_substrate.GetProperty().SetColor(0,0,0)
        self.scalar_bar_substrate.GetTitleTextProperty().SetColor(0,0,0)

        #-----
        # -- For cells' scalars
        self.scalar_bar_cells = vtkScalarBarActor()
        self.scalar_bar_cells.SetTitle("substrate")
        self.scalar_bar_cells.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        self.scalar_bar_cells.GetPositionCoordinate().SetValue(0.10,0.01)
        self.scalar_bar_cells.UnconstrainedFontSizeOn()
        self.scalar_bar_cells.SetOrientationToHorizontal()
        self.scalar_bar_cells.SetWidth(0.8)
        self.scalar_bar_cells.SetHeight(0.08)
        self.scalar_bar_cells.GetProperty().SetColor(0,0,0)
        self.scalar_bar_cells.GetTitleTextProperty().SetColor(0,0,0)

        #-----
        # self.domain_outline = vtkOutlineFilter()
        # self.domain_outline_mapper = vtkPolyDataMapper()
        # self.domain_outline_mapper.SetInputConnection(self.domain_outline.GetOutputPort())
        # self.domain_outline_actor = vtkActor()
        # self.domain_outline_actor.SetMapper(self.domain_outline_mapper)


        #--------------------------------------------------
        self.nanohub_flag = nanohub_flag

        self.animating_flag = False

        self.xml_root = None
        self.current_frame = 0
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.play_plot_cb)

        self.use_defaults = True
        self.title_str = ""

        self.reset_model_flag = True
        self.xmin = -80
        self.xmax = 80
        self.x_range = self.xmax - self.xmin

        self.ymin = -50
        self.ymax = 100
        self.y_range = self.ymax - self.ymin

        self.alpha = 0.7

        # self.output_dir = "../tmpdir"   # for nanoHUB
        # self.output_dir = "tmpdir"   # for nanoHUB
        self.output_dir = "output"   # for nanoHUB
        # self.output_dir = "."   # for nanoHUB

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



        self.canvas = None
        self.create_figure()
        self.scroll_plot.setWidget(self.canvas) # self.config_params = QWidget()
        # self.scroll_plot.resize(800,800)
        self.scroll_plot.setMinimumSize(700, 600)  #width, height of window

    # def reset_domain_box_3D(self):
    #     print("\n------ vis3D: reset_domain_box()")
    #     self.lut_discrete = None

    #     self.xmin = float(self.config_tab.xmin.text())
    #     self.xmax = float(self.config_tab.xmax.text())

    #     self.ymin = float(self.config_tab.ymin.text())
    #     self.ymax = float(self.config_tab.ymax.text())

    #     self.zmin = float(self.config_tab.zmin.text())
    #     self.zmax = float(self.config_tab.zmax.text())

    #     # self.domain_diagonal = vtkLineSource()
    #     self.domain_diagonal.SetPoint1(self.xmin, self.ymin, self.zmin)
    #     self.domain_diagonal.SetPoint2(self.xmax, self.ymax, self.zmax)

    #     self.outline.Update()
    #     # self.outline = vtkOutlineFilter()
    #     # self.outline.SetInputConnection(self.domain_diagonal.GetOutputPort())

    #-------------------------------
    # def show_domain_outline(self):
    #     # array of 8 3-tuples of float representing the vertices of a cube:
    #     xmax = 100
    #     xmin = -xmax
    #     ymax = 100
    #     ymin = -ymax
    #     zmax = 100
    #     zmin = -zmax
    #     corner_pts = [ (xmin, ymin, zmin), (xmax, ymin, zmin),  (xmin, ymax, zmin), (xmax, ymax, zmin),  
    #                     (xmin, ymin, zmax), (xmax, ymin, zmax),  (xmin, ymax, zmax), (xmax, ymax, zmax) ] 

    #     # We'll create the building blocks of polydata including data attributes.
    #     self.domain_boundary_pd = vtkPolyData()
    #     self.domain_boundary_pts = vtkPoints()

    #     # Load the point, cell, and data attributes.
    #     for i, xi in enumerate(corner_pts):
    #         self.domain_boundary_pts.InsertPoint(i, xi)

    #     # We now assign the pieces to the vtkPolyData.
    #     self.domain_boundary_pd.SetPoints(self.domain_boundary_pts)

    #     # Now we'll look at it.
    #     self.domain_boundary_mapper = vtkPolyDataMapper()
    #     self.domain_boundary_mapper.SetInputData(self.domain_boundary_pd)
    #     self.domain_boundary_actor = vtkActor()
    #     self.domain_boundary_actor.SetMapper(self.domain_boundary_mapper)
    #     self.domain_boundary_actor.GetProperty().SetColor(0, 0, 0)

    #---------------------------------------
    # Dependent on 2D/3D
    def update_plots(self):
        # self.ax0.cla()
        # if self.substrates_checked_flag:
        #     self.plot_substrate(self.current_frame)
        # print("vis3D_tab: ------- update_plots() - just calling plot_cells3D()")
        self.plot_cells3D(self.current_frame)
        # if self.cells_checked_flag:
        #     self.plot_svg(self.current_frame)

        # self.canvas.update()
        # self.canvas.draw()

        if self.save_png:
            self.png_frame += 1
            png_file = os.path.join(self.output_dir, f"frame{self.png_frame:04d}.png")
            print("---->  ", png_file)
            windowto_image_filter = vtkWindowToImageFilter()
            windowto_image_filter.SetInput(self.vtkWidget.GetRenderWindow())
            windowto_image_filter.SetScale(1)  # image quality
            # if rgba:
            if False:
                windowto_image_filter.SetInputBufferTypeToRGBA()
            else:
                windowto_image_filter.SetInputBufferTypeToRGB()
                # Read from the front buffer.
                windowto_image_filter.ReadFrontBufferOff()
                windowto_image_filter.Update()

            self.png_writer.SetFileName(png_file)
            self.png_writer.SetInputConnection(windowto_image_filter.GetOutputPort())
            self.png_writer.Write()

        return


    # def update_output_dir(self, dir_path):
    #     self.output_dir = dir_path
    #     return 
    #     # if os.path.isdir(dir_path):
    #     #     print("update_output_dir(): yes, it is a dir path", dir_path)
    #     # else:
    #     #     print("update_output_dir(): NO, it is NOT a dir path", dir_path)
    #     # self.output_dir = dir_path
    #     # self.output_folder.setText(dir_path)


    #------------------------------------------------
    def xy_slice_toggle_cb(self,flag):
        self.show_xy_slice = flag
        if flag:
            self.ren.AddActor(self.cutterXYActor)
        else:
            self.ren.RemoveActor(self.cutterXYActor)
        self.vtkWidget.GetRenderWindow().Render()

    def xy_slice_value_cb(self,val):
        print("vis3D_tab: xy_slice_value_cb: val=",val)
        self.xy_slice_z0 = val
        self.update_plots()

    #--------
    def yz_slice_toggle_cb(self,flag):
        self.show_yz_slice = flag
        if flag:
            self.ren.AddActor(self.cutterYZActor)
        else:
            self.ren.RemoveActor(self.cutterYZActor)
        self.vtkWidget.GetRenderWindow().Render()

    def yz_slice_value_cb(self,val):
        print("vis3D_tab: yz_slice_value_cb: val=",val)
        self.yz_slice_x0 = val
        self.update_plots()

    #--------
    def xz_slice_toggle_cb(self,flag):
        self.show_xz_slice = flag
        if flag:
            self.ren.AddActor(self.cutterXZActor)
        else:
            self.ren.RemoveActor(self.cutterXZActor)
        self.vtkWidget.GetRenderWindow().Render()

    def xz_slice_value_cb(self,val):
        print("vis3D_tab: xz_slice_value_cb: val=",val)
        self.xz_slice_y0 = val
        self.update_plots()

    #--------
    def contour_toggle_cb(self,flag):
        self.show_contour = flag
        # if flag:
        #     self.ren.AddActor(self.contour_actor)
        # else:
        #     self.ren.RemoveActor(self.contour_actor)
        # self.vtkWidget.GetRenderWindow().Render()
        self.update_plots()

    def contour_value_cb(self,val):
        print("vis3D_tab: contour_value_cb: val=",val)
        self.contour_value = val
        self.update_plots()

    #--------------------------------
    def xy_clip_toggle_cb(self,flag):
        self.show_xy_clip = flag
        print("xy_clip_toggle_cb(): show_xy_clip=",self.show_xy_clip)
        self.update_plots()

    def xy_clip_value_cb(self,val):
        print("vis3D_tab: xy_clip_value_cb: val=",val)
        self.xy_clip_z0 = val
        self.update_plots()

    def xy_flip_toggle_cb(self,flag):
        self.xy_flip = flag
        self.update_plots()

    #--------
    def yz_clip_toggle_cb(self,flag):
        self.show_yz_clip = flag
        print("yz_clip_toggle_cb(): show_yz_clip=",self.show_yz_clip)
        self.update_plots()

    def yz_clip_value_cb(self,val):
        print("vis3D_tab: yz_clip_value_cb: val=",val)
        self.yz_clip_x0 = val
        self.update_plots()

    def yz_flip_toggle_cb(self,flag):
        self.yz_flip = flag
        self.update_plots()

    #--------
    def xz_clip_toggle_cb(self,flag):
        self.show_xz_clip = flag
        print("xz_clip_toggle_cb(): show_xz_clip=",self.show_xz_clip)
        self.update_plots()

    def xz_clip_value_cb(self,val):
        print("vis3D_tab: xz_clip_value_cb: val=",val)
        self.xz_clip_y0 = val
        self.update_plots()

    def xz_flip_toggle_cb(self,flag):
        self.xz_flip = flag
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
            self.reset_domain_box()
            if self.axes_actor is None:
                print("------- showing axes_actor")
                self.ren.RemoveActor(self.axes_actor)
                self.axes_actor = vtkAxesActor()
                # self.axes_actor.SetShaftTypeToCylinder()
                # subjective scaling
                # cradius = self.ymax * 0.001
                cradius = self.ymax * 0.0005
                print("\n-----  axes cradius= ",cradius)
                # self.axes_actor.SetCylinderRadius(cradius)
                # self.axes_actor.SetConeRadius(cradius*9)
                # laxis = self.ymax + self.ymax * 0.2
                laxis = self.ymax + self.ymax * 0.05
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

                # self.axes_actor.GetProperty().SetLineWidth(self.line_width)
                # self.axes_actor.SetShaftType(vtkAxesActor.CYLINDER_SHAFT)
                # self.axes_actor.SetCylinderRadius(0.01)
                # self.ren.AddActor(self.axes_actor)
            self.ren.AddActor(self.axes_actor)
        else:
            self.ren.RemoveActor(self.axes_actor)
        self.vtkWidget.GetRenderWindow().Render()


    def boundary_toggle_cb(self,flag):
        self.show_boundary = flag
        if flag:
            self.ren.AddActor(self.domain_boundary_actor)
        else:
            self.ren.RemoveActor(self.domain_boundary_actor)
        self.vtkWidget.GetRenderWindow().Render()


    def sphere_res_cb(self,res_ival):
        # print("----- sphere_res_cb: res=",res_ival)
        self.sphere_res = res_ival
        self.sphereSource.SetPhiResolution(self.sphere_res)
        self.sphereSource.SetThetaResolution(self.sphere_res)
        self.update_plots()

    #--------------------------------------
    def write_cells_csv_cb(self):
        print("vis3D_tab.py: write_cells_csv_cb")

        xml_file_root = "output%08d.xml" % self.current_frame
        xml_file = os.path.join(self.output_dir, xml_file_root)
        print("write_cells_csv_cb(): xml_file= ",xml_file)
        # xml_file = os.path.join("tmpdir", xml_file_root)  # temporary hack

        # cell_scalar_name = self.cell_scalar_combobox.currentText()
        if not Path(xml_file).is_file():
            print("ERROR: file not found",xml_file)
            return

        mcds = pyMCDS(xml_file_root, self.output_dir, microenv=False, graph=False, verbose=False)
        # total_min = mcds.get_time()  # warning: can return float that's epsilon from integer value
    
        xvals = mcds.get_cell_df()['position_x']
        # print("len(xvals)=",len(xvals))
        yvals = mcds.get_cell_df()['position_y']
        zvals = mcds.get_cell_df()['position_z']
        cell_types = mcds.get_cell_df()["cell_type"]
        self.get_cell_types_from_config()
        print("self.celltype_name=",self.celltype_name)
        csv_file = open("snap.csv", "w")
        csv_file.write("x,y,z,type,volume,cycle entry,custom:GFP,custom:sample\n")
        try:
            for xv, yv, zv, ct in zip(xvals, yvals, zvals, cell_types):  # DON'T do sequential idx
                csv_file.write(f'{xv},{yv},{zv},{self.celltype_name[int(ct)]}\n')
        except:
            print("\nvis3D_tab.py-------- Error writing snap.csv file")
        csv_file.close()

    # def colorbar_combobox_changed_cb(self,idx):
    #     self.update_plots()

    def substrates_combobox_changed_cb(self,idx):
        # print("----- vis3D_tab.py: substrates_combobox_changed_cb: idx = ",idx)
        # self.field_index = 4 + idx # substrate (0th -> 4 in the .mat)
        self.field_index = idx # substrate (0th -> 4 in the .mat)
        self.substrate_name = self.substrates_combobox.currentText()
        # print("\n>>> substrates_combobox_changed_cb(): self.substrate_name= ", self.substrate_name)
        # print("\n>>> calling update_plots() from "+ inspect.stack()[0][3])
        self.update_plots()

    def substrates_cbar_combobox_changed_cb(self,idx):
        # print("----- vis3D_tab.py: substrates_combobox_changed_cb: idx = ",idx)
        # self.field_index = 4 + idx # substrate (0th -> 4 in the .mat)
        cbar_name = self.substrates_cbar_combobox.currentText()
        # print("\n>vis3D  ---------------->> substrates_cbar_combobox_changed_cb(): cbar_name= ", cbar_name)

        if cbar_name.find("_r") >= 0:   # reverse (inverted)
            if cbar_name.find("jet") >= 0:
                self.lut_substrate = self.lut_substrate_jet_r
            elif cbar_name.find("viridis") >= 0:
                self.lut_substrate = self.lut_substrate_viridis_r
            elif cbar_name.find("YlOrRd") >= 0:
                self.lut_substrate = self.lut_substrate_ylorrd_r
        else:
            if cbar_name.find("jet") >= 0:
                self.lut_substrate = self.lut_substrate_jet
            elif cbar_name.find("viridis") >= 0:
                self.lut_substrate = self.lut_substrate_viridis
            elif cbar_name.find("YlOrRd") >= 0:
                self.lut_substrate = self.lut_substrate_ylorrd

        self.update_plots()

    #-----------
    # def cell_scalar_range(self):
    #     print("   cell_scalar_range():  -----")
    #     xml_pattern = self.output_dir + "/" + "output*.xml"
    #     xml_files = glob.glob(xml_pattern)
    #     # print(xml_files)
    #     num_xml = len(xml_files)
    #     print("   num_xml= ",num_xml)
    #     if num_xml == 0:
    #         print("last_plot_cb(): WARNING: no output*.xml files present")
    #         msgBox = QMessageBox()
    #         msgBox.setIcon(QMessageBox.Information)
    #         msgBox.setText("Could not find any " + self.output_dir + "/output*.xml")
    #         msgBox.setStandardButtons(QMessageBox.Ok)
    #         msgBox.exec()
    #         return

    #     xml_files.sort()
    #     # print("sorted: ",xml_files)

    #     mcds = []
    #     for fname in xml_files:
    #         basename = os.path.basename(fname)
    #         # print("basename= ",basename)
    #         # mcds = pyMCDS(basename, self.output_dir, microenv=False, graph=False, verbose=False)
    #         mcds.append(pyMCDS(basename, self.output_dir, microenv=False, graph=False, verbose=False))


    #-----------
    def cell_scalar_combobox_changed_cb(self,idx):
        print("----- vis3D_tab.py: cell_scalar_combobox_changed_cb: idx = ",idx)
        # self.field_index = 4 + idx # substrate (0th -> 4 in the .mat)
        choice = self.cell_scalar_combobox.currentText()
        print("    choice= ", choice)
        if len(choice) == 0:
            return
        if choice in self.cell_scalar_human2mcds_dict.keys():
            choice = self.cell_scalar_human2mcds_dict[choice]

        xml_files = glob.glob(self.output_dir+'/output*.xml')  # cross-platform OK?
        # print('xml_files = ',xml_files)
        # xml_files = Path(self.output_dir, "initial.xml")
        if len(xml_files) == 0:
            return
        # xml_files.sort()
        # svg_files = glob.glob('snapshot*.svg')
        # svg_files.sort()

        # xml_file = "output%08d.xml" % frame
        # print("plot_cells3D: xml_file = ",xml_file)
        # full_fname = os.path.join(self.output_dir, xml_file)
        # if not os.path.exists(full_fname):
        #     return

        print("  pyMCDS reading info from ",xml_files)

        self.cell_scalar_min = 1.e9
        self.cell_scalar_max = -self.cell_scalar_min
        for frame in range(len(xml_files)):
            xml_file = "output%08d.xml" % frame
            mcds = pyMCDS(xml_file, self.output_dir, microenv=False, graph=False, verbose=False)
            scalar_data = mcds.data['discrete_cells']['data'][choice]
            smin = scalar_data.min()
            smax = scalar_data.max()
            if smin < self.cell_scalar_min:
                self.cell_scalar_min = smin
            if smax > self.cell_scalar_max:
                self.cell_scalar_max = smax

        print("cell_scalar_combobox_changed_cb():    min,max= ",self.cell_scalar_min,', ',self.cell_scalar_max)
        self.update_plots()


    def cell_scalar_cbar_combobox_changed_cb(self,idx):
        # self.field_index = 4 + idx # substrate (0th -> 4 in the .mat)
        cbar_name = self.cell_scalar_cbar_combobox.currentText()
        # print("\n>vis3D: ---------------->> cell_scalar_cbar_combobox_changed_cb(): cbar_name= ", cbar_name)
        if cbar_name.find("_r") >= 0:   # reversed map
            if cbar_name.find("jet") >= 0:
                self.lut_cells = self.lut_cells_jet_r
            elif cbar_name.find("viridis") >= 0:
                self.lut_cells = self.lut_cells_viridis_r
            elif cbar_name.find("YlOrRd") >= 0:
                self.lut_cells = self.lut_cells_ylorrd_r
        else:
            if cbar_name.find("jet") >= 0:
                self.lut_cells = self.lut_cells_jet
            elif cbar_name.find("viridis") >= 0:
                self.lut_cells = self.lut_cells_viridis
            elif cbar_name.find("YlOrRd") >= 0:
                self.lut_cells = self.lut_cells_ylorrd

        self.update_plots()


    #--------------------------
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


        self.zmin = float(bds[2])
        self.zmax = float(bds[5])

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
        # print('xml_files = ',xml_files)
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
                self.current_frame -= 1
                self.animating_flag = True
                # self.current_frame = 0
                self.animate()
                return

            self.update_plots()


    # overriden method from vis_base
    def change_frame_count_cb(self):
        # print("vis3D (override)>>> change_frame_count_cb()")
        try:  # due to the initial callback
            self.current_frame = int(self.frame_count.text())
            # print("           self.current_frame= ",self.current_frame)
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

        # self.vtkWidget.GetRenderWindow().SetSize(1200,1200)  # has no visible effect
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        self.text_title_actor = vtkTextActor()
        self.text_title_actor.SetInput('Welcome to PhysiCell Studio (3D)')
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

        if self.boundary_checked_flag:
            self.ren.AddActor(self.domain_boundary_actor)

        self.ren.ResetCamera()
        # self.frame.setLayout(self.vl)
        # self.setCentralWidget(self.frame)
        self.show()
        self.iren.Initialize()
        self.vtkWidget.GetRenderWindow().Render()
        self.iren.Start()

        # self.reset_model()   # rwh - is this necessary??


    #------------------------------------------------------------
    def get_jet_map(self, invert_flag):
        # table_size = 512
        table_size = 256
        lut = vtkLookupTable()
        lut.SetNumberOfTableValues(table_size)
        if invert_flag:
            lut.SetHueRange(0.0, 0.667)  # red-to-blue
        else:
            lut.SetHueRange( 0.667, 0.)  # blue-to-red
        lut.Build()
        return lut

    #------------------------------------------------------------
    # https://matplotlib.org/3.1.1/tutorials/colors/colormap-manipulation.html
    # >>> viridis = cm.get_cmap('viridis', 32)
    # >>> viridis(np.linspace(0, 1, 32))
    def get_viridis_map(self, invert_flag):
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
        # idxs = np.round(np.linspace(0, table_size-1, table_size)).astype(int)
        # print(f"get_viridis_map(): invert_flag={invert_flag}, idxs={idxs} ")
        if invert_flag:
            kdx = table_size - 1
            for i in range(table_size):
                lut.SetTableValue(kdx-i,rgb[i,0], rgb[i,1], rgb[i,2], 1)
        else:
            for i in range(table_size):
                lut.SetTableValue(i,rgb[i,0], rgb[i,1], rgb[i,2], 1)

        # lut.Build()
        return lut

    #------------------------------------------------------------
    def get_ylorrd_map(self, invert_flag):
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
        # idxs = np.round(np.linspace(0, table_size-1, table_size)).astype(int)
        if invert_flag:
            kdx = table_size - 1
            for i in range(table_size):
                lut.SetTableValue(kdx-i,rgb[i,0], rgb[i,1], rgb[i,2], 1)
        else:
            for i in range(table_size):
                lut.SetTableValue(i,rgb[i,0], rgb[i,1], rgb[i,2], 1)

        # lut.Build()
        return lut

    # rf. https://kitware.github.io/vtk-examples/site/Python/PolyData/CurvaturesDemo/
    def get_diverging_lut1(self):
        colors = vtkNamedColors()
        # self.colors = vtkNamedColors()
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

    # discrete color map
    def get_cell_type_colors_lut(self, num_cell_types):
        # https://kitware.github.io/vtk-examples/site/Python/Modelling/DiscreteMarchingCubes/
        print("---- get_cell_type_colors_lut(): num_cell_types= ",num_cell_types)
        lut = vtkLookupTable()
        lut.SetNumberOfTableValues(num_cell_types)
        lut.Build()

        # ics_tab.py uses:
        # self.color_by_celltype = ['gray','red','green','yellow','cyan','magenta','blue','brown','black','orange','seagreen','gold']

        # rf. PhysiCell modules/P*_pathology.cpp: std::vector<std::string> paint_by_number_cell_coloring( Cell* pCell )

        colors = vtkNamedColors()
        # cell_colors = [ list(colors.GetColor3d('Gray'))+[1], list(colors.GetColor3d('Red'))+[1]], list(colors.GetColor3d('Yellow'))+[1] ]

        # cf. vis_base:
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

            #    cell_colors = ( [0.5,0.5,0.5], [1,0,0], [1,1,0], [0,1,0], [0,0,1], 
            #             [1,0,1], [1,0.65,0], [0.2,0.8,0.2], [0,1,1], [1, 0.41, 0.71],
            #             [1, 0.85, 0.73], [143/255.,188/255.,143/255.], [135/255.,206/255.,250/255.])

        # But VTK requires 4th (opacity) value too.
        cell_colors = [list(colors.GetColor3d('Gray'))+[1], list(colors.GetColor3d('Red'))+[1], list(colors.GetColor3d('Yellow'))+[1], list(colors.GetColor3d('Green'))+[1], list(colors.GetColor3d('Blue'))+[1], list(colors.GetColor3d('Magenta'))+[1], list(colors.GetColor3d('Orange'))+[1], list(colors.GetColor3d('Lime'))+[1], list(colors.GetColor3d('Cyan'))+[1], list(colors.GetColor3d('HotPink'))+[1], list(colors.GetColor3d('PeachPuff'))+[1], list(colors.GetColor3d('DarkSeaGreen'))+[1], list(colors.GetColor3d('LightSkyBlue'))+[1] ]
        
        # list(colors.GetColor3d('Cyan'))+[1], list(colors.GetColor3d('Magenta'))+[1], list(colors.GetColor3d('Blue'))+[1], list(colors.GetColor3d('Brown'))+[1], list(colors.GetColor3d('Black'))+[1], list(colors.GetColor3d('Orange'))+[1], list(colors.GetColor3d('SeaGreen'))+[1], list(colors.GetColor3d('Gold'))+[1]  ]
        # print("cell_colors = ",cell_colors)
        # lut.SetTableValue(0, [0.5, 0.5, 0.5, 1])  # darker gray
        # Colour transfer function.
        # lut.SetTableValue(0, 0.5, 0.5, 0.5, 1)  # darker gray
        # lut.SetTableValue(0,   # darker gray; append opacity=1 to tuple
        # print("Gray=",colors.GetColor3d('Gray'))
        # print("type=",type(colors.GetColor3d('Gray')))

        # lut.SetTableValue(1, 1, 0, 0, 1)  # red

        for idx in range(13):
            # print(" idx=",idx)
            lut.SetTableValue(idx, cell_colors[idx])
            if idx >= num_cell_types-1:
                break

        np.random.seed(42)
        for idx in range(13,num_cell_types):  # random beyond those hard-coded
            lut.SetTableValue(idx, np.random.uniform(), np.random.uniform(), np.random.uniform(), 1)

        return lut

    #------------------------------------------------------------
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

    #------------------------------------------------------------
    def plot_cells3D(self, frame):
        # print("plot_cells3D:  self.output_dir= ",self.output_dir)
        # print("plot_cells3D:  self.substrate_name= ",self.substrate_name)
        # print("plot_cells3D:  frame= ",frame)
        self.frame_count.setText(str(frame))

        read_microenv_flag = self.substrates_checkbox.isChecked()

        # xml_file = Path(self.output_dir, "output00000000.xml")
        # xml_file = "output00000000.xml"
        xml_file = "output%08d.xml" % frame
        # print("plot_cells3D: xml_file = ",xml_file)
        # mcds = pyMCDS_cells(xml_file, '.')  

        # if not os.path.exists("tmpdir/" + xml_file):
        # if not os.path.exists("output/" + xml_file):
        full_fname = os.path.join(self.output_dir, xml_file)
        if not os.path.exists(full_fname):
            print(f"vis3D_tab.py: plot_cells3D(): full_fname {full_fname} does not exist, leaving!")
            return

        # print("------------- plot_cells3D: pyMCDS reading info from ",full_fname)
        # mcds = pyMCDS(xml_file, 'output')   # will read in BOTH cells and substrates info
        # mcds = pyMCDS(xml_file, self.output_dir)   # will read in BOTH cells and substrates info
        # mcds = pyMCDS(xml_file, self.output_dir, microenv=False, graph=False, verbose=False)
        mcds = pyMCDS(xml_file, self.output_dir, microenv=read_microenv_flag, graph=False, verbose=False)
        current_time = mcds.get_time()
        # print('time=', current_time )
        # print("metadata keys=",mcds.data['metadata'].keys())
        current_time = mcds.data['metadata']['current_time']
        # print('time(verbose)=', current_time )

        current_time = round(current_time, 2)
        self.title_str = 'time '+ str(current_time) + ' min'
        # self.text_title_actor.SetInput(self.title_str)

        if self.boundary_checked_flag:
            self.ren.RemoveActor(self.domain_boundary_actor)
            self.ren.AddActor(self.domain_boundary_actor)
        else:
            self.ren.RemoveActor(self.domain_boundary_actor)

        #-----------
        if self.cells_checked_flag:
            # mcds = pyMCDS_cells(xml_file, 'tmpdir')  
            # mcds = pyMCDS_cells(xml_file, 'output')  
            # mcds = pyMCDS(xml_file, 'output')  

            # print("mcds.data dict_keys= ",mcds.data['discrete_cells'].keys())   # dict_keys(...)

            # ncells = len(mcds.data['discrete_cells']['ID'])
            ncells = len(mcds.data['discrete_cells']['data']['ID'])
            # print('ncells=', ncells)
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
            # print("ymin = ",ymin)
            # print("ymax = ",ymax)

            zmin = min(xyz[:,2])
            zmax = max(xyz[:,2])
            # print("zmin = ",zmin)
            # print("zmax = ",zmax)

            # cell_type = mcds.data['discrete_cells']['cell_type']
            cell_scalar_str = self.cell_scalar_combobox.currentText()
            if len(cell_scalar_str) == 0:
                cell_scalar_str = 'cell_type'
            if cell_scalar_str in self.cell_scalar_human2mcds_dict.keys():
                cell_scalar_str = self.cell_scalar_human2mcds_dict[cell_scalar_str]
            # print("\n------- cell_scalar_str= ",cell_scalar_str)
            self.scalar_bar_cells.SetTitle(cell_scalar_str)
            # cell_type = mcds.data['discrete_cells']['data']['cell_type']
            cell_scalar_val = mcds.data['discrete_cells']['data'][cell_scalar_str]
            # print(type(cell_type))
            # print(cell_type)

            # self.discrete_cell_scalars = ['cell_type', 'cycle_model', 'current_phase','is_motile','current_death_model','dead','number_of_nuclei','polarity']  # check for discrete type scalar, ugh.
            if cell_scalar_str in self.discrete_cell_scalars:  # check for discrete type scalar, ugh.
                # print("------------- plot_cells3D: have discrete cell scalars")
                unique_cell_type = np.unique(cell_scalar_val)
                self.num_discrete_cell_val = len(unique_cell_type)
                # print("\nunique_cell_type = ",unique_cell_type )
                # print("self.num_discrete_cell_val= ",self.num_discrete_cell_val)

                # lut = self.get_diverging_lut1()
                if self.lut_discrete is None:
                    self.lut_discrete = self.get_cell_type_colors_lut(self.num_discrete_cell_val)  # TODO: only call when necessary
                    self.cells_mapper.SetLookupTable(self.lut_discrete)
            else:
                # self.cells_mapper.SetLookupTable(self.lut_viridis)
                # print("------------- plot_cells3D: have continuous (non-discrete) cell scalars. lut_cells=",self.lut_cells)
                self.cells_mapper.SetLookupTable(self.lut_cells)

            #------------
            # colors = vtkNamedColors()

            # update VTK pipeline
            self.points.Reset()
            # self.cellID.Reset()
            if not self.tensor_flag:
                self.radii.Reset()
            else:
                self.tensors.Reset()

            self.cell_data.Reset()
            self.tags.Reset()
            # self.colors.Reset()
            # self.cellVolume.Reset()
            # points.InsertNextPoint(0, 0, 0)
            # points.InsertNextPoint(1, 1, 1)
            # points.InsertNextPoint(2, 2, 2)

            self.cell_data.SetNumberOfTuples(ncells)

            self.cell_scalar_min = 1.e9
            self.cell_scalar_max = -self.cell_scalar_min

            try:
                xval = mcds.data['discrete_cells']['data']['position_x']
                yval = mcds.data['discrete_cells']['data']['position_y']
                zval = mcds.data['discrete_cells']['data']['position_z']
                total_vol = mcds.data['discrete_cells']['data']['total_volume']
                # cid = mcds.data['discrete_cells']['data']['ID']
            except:
                print("vis3D_tab: Error: trying to access position_x,_y,_z, or total_volume vectors.")
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setText("Error: Unable to access position_x,_y,_z, or total_volume vectors.")
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec()
                sys.exit(1)

            if not self.tensor_flag:   # typical spheres
                # self.points.SetNumberOfTuples(ncells)   # faster?
                for idx in range(ncells):
                    # x= mcds.data['discrete_cells']['data']['position_x'][idx]
                    # y= mcds.data['discrete_cells']['data']['position_y'][idx]
                    # z= mcds.data['discrete_cells']['data']['position_z'][idx]
                    x = xval[idx]
                    y = yval[idx]
                    z = zval[idx]
                    # id = mcds.data['discrete_cells']['data']['cell_type'][idx]
                    # id_type = mcds.data['discrete_cells']['data']['cell_type'][idx]
                    self.points.InsertNextPoint(x, y, z)
                    # self.points.InsertPoint(idx, x, y, z)  # faster?
                    # total_volume = mcds.data['discrete_cells']['data']['total_volume'][idx]
                    total_volume = total_vol[idx]

                    rval = (total_volume * 0.2387) ** 0.333333
                    # print(idx,") total_volume= ", total_volume, ", rval=",rval )
                    # self.cellID.InsertNextValue(id)
                    self.radii.InsertNextValue(rval)   # probably faster ways to do this; alloc/fill full array 
                    # self.tags.InsertNextValue(float(idx)/ncells)   # multicolored; jet/heatmap across all cells

                    # self.tags.InsertNextValue(1.0 - cell_type[idx])   # hacky 2-colors based on colormap
                    # print("idx, cell_type[idx]= ",idx,cell_type[idx])
                    # self.tags.InsertNextValue(cell_type[idx])
                    sval = cell_scalar_val[idx]
                    if sval < self.cell_scalar_min:
                        self.cell_scalar_min = sval
                    if sval > self.cell_scalar_max:
                        self.cell_scalar_max = sval
                    # self.tags.InsertNextValue(cell_scalar_val[idx])  # analogous to "plot_cell_scalar" in 2D plotting
                    self.tags.InsertNextValue(sval)  # analogous to "plot_cell_scalar" in 2D plotting

                self.cell_data.CopyComponent(0, self.radii, 0)
                self.cell_data.CopyComponent(1, self.tags, 0)
                # self.ugrid.SetPoints(self.points)
                # self.ugrid.GetPointData().AddArray(self.cell_data)
                # self.ugrid.GetPointData().SetActiveScalars("cell_data")

            else:   # ellipsoids  ----------------------------------------
                self.tensors.SetNumberOfTuples(ncells)
                try:
                    axis_a = mcds.get_cell_df()['axis_a']  # these are req'd in <custom_data>
                    axis_b = mcds.get_cell_df()['axis_b']
                    axis_c = mcds.get_cell_df()['axis_c']
                except:
                    print("vis3D_tab: Error: trying to access axis_a,axis_b,axis_c custom data vars.")
                    msgBox = QMessageBox()
                    msgBox.setIcon(QMessageBox.Information)
                    msgBox.setText("Error: Unable to access axis_a (_b,_c) as custom data. Perhaps you are trying to run the Studio with --tensor, but there are no tensors saved by the model.")
                    msgBox.setStandardButtons(QMessageBox.Ok)
                    msgBox.exec()
                    sys.exit(1)

                for idx in range(ncells):
                    x = xval[idx]
                    y = yval[idx]
                    z = zval[idx]
                    # x= mcds.data['discrete_cells']['data']['position_x'][idx]
                    # y= mcds.data['discrete_cells']['data']['position_y'][idx]
                    # z= mcds.data['discrete_cells']['data']['position_z'][idx]
                    # id_type = mcds.data['discrete_cells']['data']['cell_type'][idx]
                    # cell_id = mcds.data['discrete_cells']['data']['ID'][idx]
                    # self.points.InsertNextPoint(x, y, z)
                    self.points.InsertNextPoint(xval[idx], yval[idx], zval[idx])

                    total_volume = mcds.data['discrete_cells']['data']['total_volume'][idx]
                    rval = (total_volume * 0.2387) ** 0.333333

                    # self.tensors.InsertTuple9(idx,  axis_a[idx]*rval,0,0,  0,axis_b[idx]*rval,0,  0,0,axis_c[idx]*rval) 
                    self.tensors.InsertTuple9(idx,  axis_a[idx],0,0,  0,axis_b[idx],0,  0,0,axis_c[idx]) 
                    # print(f"cell_id={cell_id}, cell_type={id_type}, volume={total_volume}, rval={rval},axis_a={axis_a[idx]},axis_b={axis_b[idx]},axis_c={axis_c[idx]}")

                    sval = cell_scalar_val[idx]
                    if sval < self.cell_scalar_min:
                        self.cell_scalar_min = sval
                    if sval > self.cell_scalar_max:
                        self.cell_scalar_max = sval
                    self.tags.InsertNextValue(cell_scalar_val[idx])  # analogous to "plot_cell_scalar" in 2D plotting

                self.cell_data.CopyComponent(0, self.tags, 0)


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

            if not self.tensor_flag:   # typical spheres
                # self.glyph.SetScaleModeToScaleByVector ()
                self.glyph.SetScaleModeToScaleByScalar ()
                # self.glyph.SetColorModeToColorByVector ()
                # print("glyph range= ",self.glyph.GetRange())
                # print("self.num_discrete_cell_val= ",self.num_discrete_cell_val)

            # self.cells_mapper.SetScalarRange(0,num_cell_types)
            if self.fix_cells_cmap_checkbox.isChecked():
                self.cells_mapper.SetScalarRange(self.cells_cmin_value, self.cells_cmax_value)
            else:
                self.cells_mapper.SetScalarRange(self.cell_scalar_min, self.cell_scalar_max)
            # print(inspect.stack()[0][3],"--- cells_mapper.SetScalarRange = ",self.cell_scalar_min, ', ',self.cell_scalar_max)
            # self.glyph.SetRange(0.0, 0.11445075055913652)
            # self.glyph.SetScaleFactor(3.0)

            # print("self.cells_mapper.GetLookupTable()= ",self.cells_mapper.GetLookupTable())
            self.scalar_bar_cells.SetLookupTable(self.cells_mapper.GetLookupTable())

            # glyph.ScalingOn()
            # self.glyph.SetScalarRange(0, vmax)
            self.glyph.Update()

            #----------------------------------------------
            # if we are clipping (extracting) the cells using a clip plane
            clipped_cells_flag = False
            # polydata = self.glyph.GetOutput()

            if self.voxel_size is None:
                self.get_domain_params()
            # self.voxel_size = 20   # rwh: fix hard-coded
            # x0 = -(self.voxel_size * self.nx) / 2.0
            # y0 = -(self.voxel_size * self.ny) / 2.0
            # z0 = -(self.voxel_size * self.nz) / 2.0
            # print(f"---- vis3D: plot_cells3D(): self.x0,self.y0,self.z0= {self.x0},{self.y0},{self.z0}")

            self.ugrid_clipped = self.ugrid   # original

            if self.show_xy_clip:
                self.planeXY_clip.SetOrigin(self.x0,self.y0, self.xy_clip_z0)
                if self.xy_flip:
                    self.planeXY_clip.SetNormal(0,0, -1)
                else:
                    self.planeXY_clip.SetNormal(0,0, 1)

                self.extract_cells_XY.SetInputData(self.ugrid_clipped)
                self.extract_cells_XY.SetImplicitFunction(self.planeXY_clip)
                self.extract_cells_XY.Update()
                self.ugrid_clipped = self.extract_cells_XY.GetOutput()   # update ugrid

            if self.show_yz_clip:
                self.planeYZ_clip.SetOrigin(self.yz_clip_x0,self.y0,self.z0)
                if self.yz_flip:
                    self.planeYZ_clip.SetNormal(-1,0,0)
                else:
                    self.planeYZ_clip.SetNormal(1,0,0)
                    
                self.extract_cells_YZ.SetInputData(self.ugrid_clipped)
                self.extract_cells_YZ.SetImplicitFunction(self.planeYZ_clip)
                self.extract_cells_YZ.Update()
                self.ugrid_clipped = self.extract_cells_YZ.GetOutput()   # update ugrid

            if self.show_xz_clip:
                self.planeXZ_clip.SetOrigin(self.x0,self.xz_clip_y0,self.z0)
                if self.xz_flip:
                    self.planeXZ_clip.SetNormal(0,-1,0)
                else:
                    self.planeXZ_clip.SetNormal(0,1,0)
                    
                self.extract_cells_XZ.SetInputData(self.ugrid_clipped)
                self.extract_cells_XZ.SetImplicitFunction(self.planeXZ_clip)
                self.extract_cells_XZ.Update()
                self.ugrid_clipped = self.extract_cells_XZ.GetOutput()   # update ugrid


            self.glyph.SetInputData(self.ugrid_clipped)
            self.cells_mapper.SetInputConnection(self.glyph.GetOutputPort())
            self.cells_actor.SetMapper(self.cells_mapper)

            #-------
            self.scalar_bar_cells.SetLookupTable(self.cells_mapper.GetLookupTable())

            self.ren.AddActor(self.cells_actor)
            self.ren.AddActor2D(self.scalar_bar_cells)
        else:
            self.ren.RemoveActor(self.cells_actor)
            self.ren.RemoveActor2D(self.scalar_bar_cells)


        self.text_title_actor.SetInput(self.title_str)

        #-------------------------------------------------------------------
        if self.substrates_checked_flag:
            # print("substrate names= ",mcds.get_substrate_names())

            field_name = self.substrates_combobox.currentText()
            # print("plot_cells3D(): field_name= ",field_name)
            # print("plot_cells3D(): self.substrate_name= ",self.substrate_name)
            # sub_name = mcds.get_substrate_names()[0]
            # sub_name = mcds.get_substrate_names()[self.field_index]  # NOoo!
            # self.scalar_bar_substrate.SetTitle(sub_name)
            self.scalar_bar_substrate.SetTitle(self.substrate_name)
            # sub_dict = mcds.data['continuum_variables'][sub_name]
            if (len(self.substrate_name) == 0) or (self.substrate_name not in mcds.data['continuum_variables']):
                print(f" ---  ERROR: substrate={self.substrate_name} is not valid.")
                return

            sub_dict = mcds.data['continuum_variables'][self.substrate_name]
            sub_concentration = sub_dict['data']
            # print("sub_concentration.shape= ",sub_concentration.shape)
            # print("np.min(sub_concentration)= ",np.min(sub_concentration))
            # print("np.max(sub_concentration)= ",np.max(sub_concentration))
            # print("sub_concentration = ",sub_concentration)

            # update VTK pipeline
            # self.points.Reset()
            # self.cellID.Reset()

            # self.substrate_voxel_scalars.Reset()  # rwh: OMG, why didn't this work? Optimize.
            self.substrate_voxel_scalars = vtkFloatArray()

            # self.cell_data.Reset()
            # self.tags.Reset()

            # print("\n\n---------  doing 3D substrate as vtkStructuredPoints\n")

            # Can/should probably just do this once, at the approp place...
            # nx,ny,nz = 12,12,12
            # nx,ny,nz = 3,3,3

            # Ugh. this is confusing. Swap x,y shapes
            # nx,ny,nz = sub_concentration.shape
            ny,nx,nz = sub_concentration.shape
            # print("nx,ny,nz = ",nx,ny,nz)
            self.substrate_data.SetDimensions( nx+1, ny+1, nz+1 )
            # self.substrate_data.SetDimensions( nx, ny, nz )


            # TODO: Hard-coded voxel_size, plus assuming centered at origin!
            x_voxel_size = mcds.get_mesh_spacing()[0]
            y_voxel_size = mcds.get_mesh_spacing()[1]
            z_voxel_size = mcds.get_mesh_spacing()[2]
            # x0 = -(voxel_size * nx) / 2.0
            # y0 = -(voxel_size * ny) / 2.0
            # z0 = -(voxel_size * nz) / 2.0

            # rf. reset_model() in vis_base
            x0 = self.xmin
            y0 = self.ymin
            z0 = self.zmin
            # print("plot_cells3D(): x0,y0,z0 = ",x0,y0,z0)

            # Use this info in initial.xml instead!
            # <microenvironment>
            # <domain name="microenvironment">
			# <mesh type="Cartesian" uniform="true" regular="true" units="micron">
			# 	<bounding_box type="axis-aligned" units="micron">-300.000000 -100.000000 -50.000000 200.000000 100.000000 50.000000</bounding_box>

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

            self.substrate_data.SetOrigin( x0, y0, z0 )  # lower-left-front point of domain bounding box
            self.substrate_data.SetSpacing( x_voxel_size, y_voxel_size, z_voxel_size )
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
                        val = sub_concentration[y,x,z]   # yes, it's confusingly swapped :/
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
                # print("fixed cmap vmin,vmax = ",vmin,vmax)

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

            # print("---vmin,vmax= ",vmin,vmax)
            # if 'internalized_total_substrates' in mcds.data['discrete_cells'].keys():
            #     print("intern_sub= ",mcds.data['discrete_cells']['internalized_total_substrates'])

            # if self.show_voxels or self.show_xy_slice or self.show_yz_slice or self.show_xz_slice:
            #     self.ren.RemoveActor2D(self.scalar_bar_substrate)
            #     self.ren.AddActor2D(self.scalar_bar_substrate)
            # else:
            #     self.ren.RemoveActor2D(self.scalar_bar_substrate)

            # if self.show_voxels:
            #     self.ren.RemoveActor(self.substrate_actor)

            #     # print("----- show_voxels: vmin,vmax= ",vmin,vmax)
            #     self.substrate_mapper.SetScalarRange(vmin, vmax)
            #     # self.substrate_mapper.SetScalarModeToUseCellData()
            #     self.substrate_mapper.Update()

            #     # self.substrate_actor.GetProperty().SetRepresentationToWireframe()
            #     self.ren.AddActor(self.substrate_actor)
            #     self.scalar_bar_substrate.SetLookupTable(self.substrate_mapper.GetLookupTable())


            if self.show_xy_slice:
                # self.ren.RemoveActor(self.substrate_actor)
                self.ren.RemoveActor(self.cutterXYActor)
                # self.ren.RemoveActor2D(self.scalar_bar_substrate)

                self.cutterXY.SetInputData(self.substrate_data)
                # self.cutterXY.SetInputData(self.glyph.GetOutput())
                # self.planeXY.SetOrigin(x0,y0,0)
                self.planeXY.SetOrigin(x0,y0, self.xy_slice_z0)
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

                # self.cutterXYActor.GetProperty().SetInterpolationToFlat()
                # self.cutterXYActor.GetProperty().EdgeVisibilityOn()
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
                self.scalar_bar_substrate.SetLookupTable(self.cutterXYMapper.GetLookupTable())
                # self.scalar_bar_substrate.SetLookupTable(self.cells_mapper.GetLookupTable())  # debug: show cell colors

                # self.scalar_bar_substrate.SetLookupTable(self.substrate_mapper.GetLookupTable())
                # self.ren.AddActor2D(self.scalar_bar_substrate)


            if self.show_yz_slice:
                self.ren.RemoveActor(self.cutterYZActor)
                # self.ren.RemoveActor2D(self.scalar_bar_substrate)

                self.cutterYZ.SetInputData(self.substrate_data)
                # self.planeYZ.SetOrigin(0,y0,z0)
                self.planeYZ.SetOrigin(self.yz_slice_x0,y0,z0)
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
                self.scalar_bar_substrate.SetLookupTable(self.cutterYZMapper.GetLookupTable())
                # self.ren.AddActor2D(self.scalar_bar_substrate)

            if self.show_xz_slice:
                self.ren.RemoveActor(self.cutterXZActor)
                # self.ren.RemoveActor2D(self.scalar_bar_substrate)

                self.cutterXZ.SetInputData(self.substrate_data)
                # self.planeXZ.SetOrigin(x0,0,z0)
                self.planeXZ.SetOrigin(x0,self.xz_slice_y0,z0)
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
                self.scalar_bar_substrate.SetLookupTable(self.cutterXZMapper.GetLookupTable())
                # self.ren.AddActor2D(self.scalar_bar_substrate)


            if self.show_contour:
                print("------- show_contour!")
                self.c2p.SetInputData(self.substrate_data)  # contour filter *requires* point (not VTK cell) data
                self.c2p.Update()

                self.contour.SetInputData(self.c2p.GetOutput())
                self.contour.SetValue(0, self.contour_value)
                self.contour.Update()

                self.contour_mapper.SetInputConnection(self.contour.GetOutputPort())
                self.contour_mapper.SetScalarRange(vmin, vmax)
                self.contour_mapper.SetLookupTable(self.lut_substrate)

                # substrate_actor.GetProperty().SetAmbient(1.)
                # self.contour_mapper.SetScalarRange(0, vmax)
                # hmm, seems to be no difference in either of these
                # self.contour_mapper.SetScalarModeToUseCellData()
                self.contour_mapper.SetScalarModeToUsePointData()

                self.ren.RemoveActor(self.contour_actor)
                self.ren.AddActor(self.contour_actor)

                # self.writer.SetInputData(self.substrate_data)
                # self.writer.SetInputData(self.substrate_data.GetPointData())
                # self.writer.SetInputData(self.substrate_data.GetData())
                # fname = 'sp_data_cells.vtk'
                # print("--> ",fname)
                # self.writer.SetFileName(fname)
                # self.writer.Update()

            else:
                self.ren.RemoveActor(self.contour_actor)

            #-------------------
            self.ren.RemoveActor2D(self.scalar_bar_substrate)
            if self.show_voxels or self.show_xy_slice or self.show_yz_slice or self.show_xz_slice:
                # self.ren.RemoveActor2D(self.scalar_bar_substrate)
                self.ren.AddActor2D(self.scalar_bar_substrate)
            # else:
            #     self.ren.RemoveActor2D(self.scalar_bar_substrate)
            # self.ren.AddActor2D(self.scalar_bar_substrate)

        else:
            self.ren.RemoveActor(self.substrate_actor)
            self.ren.RemoveActor(self.cutterXYActor)
            self.ren.RemoveActor(self.cutterYZActor)
            self.ren.RemoveActor(self.cutterXZActor)

            # self.ren.RemoveActor(self.clipXYActor)
            # self.ren.RemoveActor(self.domain_outline_actor)
            self.ren.RemoveActor2D(self.scalar_bar_substrate)


        # if self.axes_actor is None:
        if self.show_axes:
            # print("------- showing axes_actor")
            self.ren.RemoveActor(self.axes_actor)
            self.axes_actor = vtkAxesActor()
            # self.axes_actor.SetShaftTypeToCylinder()
            # subjective scaling
            # cradius = self.ymax * 0.001
            cradius = self.ymax * 0.0005
            # self.axes_actor.SetCylinderRadius(cradius)
            # self.axes_actor.SetConeRadius(cradius*10)

            # laxis = self.ymax + self.ymax * 0.2
            laxis = self.ymax + self.ymax * 0.05
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

            # self.axes_actor.SetShaftType(vtkAxesActor.CYLINDER_SHAFT)
            # self.axes_actor.SetCylinderRadius(5.0)
            # self.axes_actor.SetCylinderRadius(0.01)
            self.ren.AddActor(self.axes_actor)

    # renderWindow.SetWindowName('PhysiCell model')
        # renderWindow.Render()
        # self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.vtkWidget.GetRenderWindow().Render()
    # renderWindowInteractor.Start()
        return
