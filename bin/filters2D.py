from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QGroupBox, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,  QMainWindow,QGridLayout, QPushButton, QFileDialog, QMessageBox, QStackedWidget, QSplitter
from studio_classes import DoubleValidatorWidgetBounded, HoverQuestion, QCheckBox_custom
# from PyQt5.QtWidgets import QCompleter, QSizePolicy
# from PyQt5.QtCore import QSortFilterProxyModel
# from PyQt5.QtSvg import QSvgWidget
# from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QDoubleValidator
# from PyQt5.QtCore import QRectF, Qt

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class FilterUI2DWindow(QWidget):
    # def __init__(self, output_dir):
    def __init__(self, reset, vis_tab):   # we use vis_tab for some of the methods called
        super().__init__()

        self.reset = reset
        self.vis_tab = vis_tab

        stylesheet = """ 
            QPushButton{ border: 1px solid; border-color: rgb(145, 200, 145); border-radius: 1px;  background-color: lightgreen; color: black; width: 64px; padding-right: 8px; padding-left: 8px; padding-top: 3px; padding-bottom: 3px; } 

            """

        # self.output_dir = output_dir
        self.setStyleSheet(stylesheet)
        
        #-------------------------------------------
        self.scroll = QScrollArea()  # might contain centralWidget

        self.vbox = QVBoxLayout()
        glayout = QGridLayout()

        # hbox = QHBoxLayout()

        #-------------------------------------------
        if reset:
            self.reset_filters()

        #------------
        idx_row = 0
        glayout.addWidget(QLabel("Cells:"), idx_row,0,1,2) # w, row, column, rowspan, colspan
        # glayout.addWidget(QLabel("Cells:"), idx_row,0,1,4) # w, row, column, rowspan, colspan

        idx_row += 1
        self.cell_edge_checkbox = QCheckBox_custom('edge')
        self.cell_edge_checkbox.setChecked(True)
        self.cell_edge_checkbox.clicked.connect(self.cell_edge_cb)
        idx_row += 1
        glayout.addWidget(self.cell_edge_checkbox, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.cell_fill_checkbox = QCheckBox_custom('fill')
        self.cell_fill_checkbox.setChecked(True)
        self.cell_fill_checkbox.clicked.connect(self.cell_fill_cb)
        glayout.addWidget(self.cell_fill_checkbox, idx_row,1,1,1) # w, row, column, rowspan, colspan

        self.cell_nucleus_checkbox = QCheckBox_custom('nucleus')
        self.cell_nucleus_checkbox.setChecked(False)
        self.cell_nucleus_checkbox.clicked.connect(self.cell_nucleus_cb)
        glayout.addWidget(self.cell_nucleus_checkbox, idx_row,2,1,1) # w, row, column, rowspan, colspan

        idx_row += 1
        self.cells_csv_button = QPushButton("Save snap.csv")
        self.cells_csv_button.setStyleSheet("background-color: lightgreen;")
        self.cells_csv_button.clicked.connect(self.cells_csv_cb)
        glayout.addWidget(self.cells_csv_button, idx_row,0,1,2) # w, row, column, rowspan, colspan
        #--------------------------------

        #----------
        idx_row += 1
        glayout.addWidget(QHLine(), idx_row,0,1,4) # w, row, column, rowspan, colspan
        idx_row += 1
        self.attachments_checkbox = QCheckBox_custom('attachments')
        self.attachments_checkbox.setChecked(self.vis_tab.attachments_checked_flag)
        self.attachments_checkbox.clicked.connect(self.attachments_toggle_cb)
        glayout.addWidget(self.attachments_checkbox)

        msg = """
Note: only for .mat cell plots (not .svg)
        """
        self.attachments_question_label = HoverQuestion(msg)
        self.attachments_question_label.show_icon()
        glayout.addWidget(self.attachments_question_label, idx_row,1,1,4) # w, row, column, rowspan, colspan

        idx_row += 1
        glayout.addWidget(QHLine(), idx_row,0,1,4) # w, row, column, rowspan, colspan
        idx_row += 1
        glayout.addWidget(QLabel("Substrate contours:"), idx_row,0,1,2) # w, row, column, rowspan, colspan

        #----------
        idx_row += 1
        # self.shading_checkbox = QCheckBox_custom('shading')
        self.contour_mesh_checkbox = QCheckBox_custom('mesh')
        self.contour_mesh_checkbox.setChecked(True)
        self.contour_mesh_checkbox.clicked.connect(self.contour_mesh_cb)
        glayout.addWidget(self.contour_mesh_checkbox, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.contour_smooth_checkbox = QCheckBox_custom('smooth')
        self.contour_smooth_checkbox.setChecked(True)
        self.contour_smooth_checkbox.clicked.connect(self.contour_smooth_cb)
        glayout.addWidget(self.contour_smooth_checkbox, idx_row,1,1,1) # w, row, column, rowspan, colspan

        self.contour_lines_checkbox = QCheckBox_custom('lines')
        self.contour_lines_checkbox.setChecked(False)
        self.contour_lines_checkbox.clicked.connect(self.contour_lines_cb)
        glayout.addWidget(self.contour_lines_checkbox, idx_row,2,1,1) # w, row, column, rowspan, colspan

        #-----------------------
        idx_row += 1
        glayout.addWidget(QHLine(), idx_row,0,1,4) # w, row, column, rowspan, colspan
        self.vbox.addLayout(glayout)

        idx_row += 1
        self.aspect_11_checkbox = QCheckBox_custom('1:1 aspect')
        self.aspect_11_checkbox.setChecked(True)
        self.aspect_11_checkbox.clicked.connect(self.aspect_11_cb)
        glayout.addWidget(self.aspect_11_checkbox, idx_row,0,1,3) # w, row, column, rowspan, colspan

        idx_row += 1
        glayout.addWidget(QHLine(), idx_row,0,1,4) # w, row, column, rowspan, colspan
        self.vbox.addLayout(glayout)

        # idx_row += 1
        # glayout.addWidget(QLabel("Axes zoom:"), idx_row,0,1,4) # w, row, column, rowspan, colspan
        idx_row += 1
        label = QLabel("xCenter")
        glayout.addWidget(label, idx_row,0, 1,1) # w, row, column, rowspan, colspan
        self.axes_xc = QLineEdit(str(self.vis_tab.axes_x_center))
        self.axes_xc.setFixedWidth(70)
        self.axes_xc.setValidator(QDoubleValidator())
        self.axes_xc.textChanged.connect(self.axes_xc_changed)
        glayout.addWidget(self.axes_xc , idx_row,1, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("yCenter")
        glayout.addWidget(label, idx_row,2, 1,1) # w, row, column, rowspan, colspan
        self.axes_yc = QLineEdit(str(self.vis_tab.axes_y_center))
        self.axes_yc.setFixedWidth(70)
        self.axes_yc.setValidator(QDoubleValidator())
        self.axes_yc.textChanged.connect(self.axes_yc_changed)
        glayout.addWidget(self.axes_yc , idx_row,3, 1,1) # w, row, column, rowspan, colspan

        idx_row += 1
        label = QLabel("xRadius")
        glayout.addWidget(label, idx_row,0, 1,1) # w, row, column, rowspan, colspan
        self.axes_xr = QLineEdit(str(self.vis_tab.axes_x_radius))
        self.axes_xr.setFixedWidth(70)
        self.axes_xr.setValidator(QDoubleValidator())
        self.axes_xr.textChanged.connect(self.axes_xr_changed)
        glayout.addWidget(self.axes_xr , idx_row,1, 1,1) # w, row, column, rowspan, colspan

        label = QLabel("yRadius")
        glayout.addWidget(label, idx_row,2, 1,1) # w, row, column, rowspan, colspan
        self.axes_yr = QLineEdit(str(self.vis_tab.axes_y_radius))
        self.axes_yr.setFixedWidth(70)
        self.axes_yr.setValidator(QDoubleValidator())
        self.axes_yr.textChanged.connect(self.axes_yr_changed)
        glayout.addWidget(self.axes_yr , idx_row,3, 1,1) # w, row, column, rowspan, colspan

        idx_row += 1
        self.reset_axes_button = QPushButton("Update axes")
        self.reset_axes_button.setStyleSheet("background-color: lightgreen;")
        self.reset_axes_button.clicked.connect(self.reset_axes_cb)
        glayout.addWidget(self.reset_axes_button, idx_row,0,1,2) # w, row, column, rowspan, colspan

        #--------------------------
        idx_row += 1
        glayout.addWidget(QHLine(), idx_row,0,1,4) # w, row, column, rowspan, colspan
        idx_row += 1
        glayout.addWidget(QLabel("Grids:"), idx_row,0,1,2) # w, row, column, rowspan, colspan

        self.voxel_grid_checkbox = QCheckBox_custom('voxel')
        self.voxel_grid_checkbox.clicked.connect(self.voxel_grid_cb)
        idx_row += 1
        glayout.addWidget(self.voxel_grid_checkbox, idx_row,0,1,1) # w, row, column, rowspan, colspan

        #------
        self.mech_grid_checkbox = QCheckBox_custom('mech')
        self.mech_grid_checkbox.clicked.connect(self.mech_grid_cb)
        glayout.addWidget(self.mech_grid_checkbox, idx_row,1,1,1) # w, row, column, rowspan, colspan

        # self.mech_grid_size = QLineEdit_custom()
        self.mech_grid_size = QLineEdit("30")
        self.mech_grid_size.setFixedWidth(30)
        self.mech_grid_size.textChanged.connect(self.mech_grid_size_changed)
        self.mech_grid_size.setValidator(DoubleValidatorWidgetBounded(bottom=1, top=999))
        glayout.addWidget(self.mech_grid_size , idx_row,2, 1,1) # w, row, column, rowspan, colspan

        #--------------------------
        self.save_png_checkbox = QCheckBox_custom('save frame*.png')
        self.save_png_checkbox.clicked.connect(self.save_png_cb)
        idx_row += 1
        glayout.addWidget(self.save_png_checkbox, idx_row,0,1,2) # w, row, column, rowspan, colspan

        #--------------------
        # axes_act = view3D_menu.addAction("Axes")

        # self.svg_view.setFixedSize(500, 500)
        # self.svgView.setLayout(self.vbox)
        # self.layout.addWidget(self.svg_view)

        #--------------------------------

        # self.phenotype_button = QPushButton("Phenotype summary")
        # self.phenotype_button.clicked.connect(self.phenotype_cb)
        # idx_row += 1
        # glayout.addWidget(QHLine(), idx_row,0,1,4) # w, row, column, rowspan, colspan
        # idx_row += 1
        # glayout.addWidget(self.phenotype_button, idx_row,0,1,3) # w, row, column, rowspan, colspan

        #----------
        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("background-color: lightgreen;")
        # self.close_button.setFixedWidth(150)
        self.close_button.clicked.connect(self.close_filterUI_cb)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        self.vbox.addWidget(self.close_button)
        # self.layout.setStretch(0,1000)

        self.setLayout(self.vbox)
        self.resize(200, 220)   # try to fix the size
        # self.resize(250, 220)   # try to fix the size


    #--------
    def reset_filters(self):
        self.xy_slice_flag = True
        self.xy_slice_value = 0.0
        self.xz_slice_flag = True
        self.xz_slice_value = 0.0
        self.yz_slice_flag = True
        self.yz_slice_value = 0.0
        self.voxels_flag = False

        self.xy_clip_flag = False
        self.xy_clip_value = 0.0
        self.xy_flip_flag = False

        self.xz_clip_flag = False
        self.xz_clip_value = 0.0
        self.xz_flip_flag = False

        self.yz_clip_flag = False
        self.yz_clip_value = 0.0
        self.yz_flip_flag = False

        self.axes_flag = False

    #--------
    def cell_edge_cb(self):
        self.vis_tab.cell_edge_cb(self.cell_edge_checkbox.isChecked())

    def cell_fill_cb(self):
        self.vis_tab.cell_fill_cb(self.cell_fill_checkbox.isChecked())

    def cell_nucleus_cb(self):
        self.vis_tab.cell_nucleus_cb(self.cell_nucleus_checkbox.isChecked())

    def cells_csv_cb(self):
        self.vis_tab.write_cells_csv_cb()

    def phenotype_cb(self):
        # self.vis_tab.write_cells_csv_cb()
        self.vis_tab.phenotype_cb()
        pass

    def attachments_toggle_cb(self, bval):
        self.vis_tab.attachments_checked_flag = bval
        self.vis_tab.update_plots()
    

    def contour_mesh_cb(self):
        bval = self.contour_mesh_checkbox.isChecked()
        if bval:
            self.contour_smooth_checkbox.setEnabled(True)
        else:
            self.contour_smooth_checkbox.setEnabled(False)

        self.vis_tab.contour_mesh_cb(bval)

    def contour_smooth_cb(self):
        # self.vis_tab.shading_cb(self.contour_smooth_checkbox.isChecked())
        self.vis_tab.contour_smooth_cb(self.contour_smooth_checkbox.isChecked())

    def contour_lines_cb(self):
        self.vis_tab.contour_lines_cb(self.contour_lines_checkbox.isChecked())

    def aspect_11_cb(self):
        # print("filters2D: aspect_11_cb()  self.aspect_11_checkbox.isChecked()= ",self.aspect_11_checkbox.isChecked())
        self.vis_tab.view_aspect_cb(self.aspect_11_checkbox.isChecked())   # vis_base

    def axes_xc_changed(self,sval):
        try:
            self.vis_tab.axes_x_center = float(sval)
        except:
            pass
    def axes_yc_changed(self,sval):
        try:
            self.vis_tab.axes_y_center = float(sval)
        except:
            pass

    def axes_xr_changed(self,sval):
        try:
            self.vis_tab.axes_x_radius = float(sval)
        except:
            pass
    def axes_yr_changed(self,sval):
        try:
            self.vis_tab.axes_y_radius = float(sval)
        except:
            pass
    def reset_axes_cb(self):
        self.vis_tab.reset_axes_cb()


    def voxel_grid_cb(self):
        self.vis_tab.voxel_grid_cb(self.voxel_grid_checkbox.isChecked())

    def mech_grid_cb(self):
        self.vis_tab.mech_grid_cb(self.mech_grid_checkbox.isChecked())

    def mech_grid_size_changed(self,sval):
        # print("size=",sval)
        try:
            self.vis_tab.mech_voxel_size = float(sval)
        except:
            pass

    def save_png_cb(self):
        self.vis_tab.png_frame = 0
        self.vis_tab.save_png = self.save_png_checkbox.isChecked()
        
    #--------
    def yz_slice_cb(self):
        self.vis_tab.yz_slice_toggle_cb(self.yz_slice_checkbox.isChecked())
        return

    def yz_slice_val_cb(self):
        text = self.yz_slice_w.text()
        # print(f'----- yz_slice_val_cb= {text}')
        try:
            self.vis_tab.yz_slice_value_cb(float(text))
        except:
            pass

    #--------
    def xz_slice_cb(self):
        # print("vis_base: xz_slice_cb(): self.xz_slice_checkbox.isChecked()= ",self.xz_slice_checkbox.isChecked())
        self.vis_tab.xz_slice_toggle_cb(self.xz_slice_checkbox.isChecked())
        # self.xy_slice_toggle_cb(self.xy_slice_checkbox.isChecked())
        return

    def xz_slice_val_cb(self):
        text = self.xz_slice_w.text()
        # print(f'----- xz_slice_val_cb = {text}')
        try:
            self.vis_tab.xz_slice_value_cb(float(text))
        except:
            pass

    #------
    def voxels_cb(self):
        print("vis_base: voxels_cb(): self.voxels_checkbox.isChecked()= ",self.voxels_checkbox.isChecked())
        # self.vis_tab.show_voxels = self.voxels_checkbox.isChecked()
        self.vis_tab.voxels_toggle_cb(self.voxels_checkbox.isChecked())
        return

    #---------------------
    def xy_clip_cb(self):
        # print("vis_base: xy_clip_cb(): self.xy_clip_checkbox.isChecked()= ",self.xy_clip_checkbox.isChecked())
        self.vis_tab.xy_clip_toggle_cb(self.xy_clip_checkbox.isChecked())

    def xy_clip_val_cb(self):
        text = self.xy_clip_w.text()
        # print(f'----- xy_clip_val_cb = {text}')
        try:
            self.vis_tab.xy_clip_value_cb(float(text))
        except:
            print(f'----- xy_clip_val_cb  Error!')
            pass
    def xy_flip_cb(self):
        # print("vis_base: xy_flip_cb(): self.xy_flip_checkbox.isChecked()= ",self.xy_flip_checkbox.isChecked())
        self.vis_tab.xy_flip_toggle_cb(self.xy_flip_checkbox.isChecked())
    #----------
    def yz_clip_cb(self):
        print("vis_base: yz_clip_cb(): self.yz_clip_checkbox.isChecked()= ",self.yz_clip_checkbox.isChecked())
        self.vis_tab.yz_clip_toggle_cb(self.yz_clip_checkbox.isChecked())

    def yz_clip_val_cb(self):
        text = self.yz_clip_w.text()
        # print(f'----- yz_clip_val_cb = {text}')
        try:
            self.vis_tab.yz_clip_value_cb(float(text))
        except:
            print(f'----- yz_clip_val_cb  Error!')
            pass
    def yz_flip_cb(self):
        print("vis_base: yz_flip_cb(): self.yz_flip_checkbox.isChecked()= ",self.yz_flip_checkbox.isChecked())
        self.vis_tab.yz_flip_toggle_cb(self.yz_flip_checkbox.isChecked())
    #----------
    def xz_clip_cb(self):
        # print("vis_base: xz_clip_cb(): self.xz_clip_checkbox.isChecked()= ",self.xz_clip_checkbox.isChecked())
        self.vis_tab.xz_clip_toggle_cb(self.xz_clip_checkbox.isChecked())

    def xz_clip_val_cb(self):
        text = self.xz_clip_w.text()
        # print(f'----- xz_clip_val_cb = {text}')
        try:
            self.vis_tab.xz_clip_value_cb(float(text))
        except:
            pass
    def xz_flip_cb(self):
        # print("vis_base: xz_flip_cb(): self.xz_flip_checkbox.isChecked()= ",self.xz_flip_checkbox.isChecked())
        self.vis_tab.xz_flip_toggle_cb(self.xz_flip_checkbox.isChecked())

    #----------
    def axes_cb(self):
        # print("vis_base: axes_cb(): self.axes_checkbox.isChecked()= ",self.axes_checkbox.isChecked())
        self.vis_tab.axes_toggle_cb(self.axes_checkbox.isChecked())
    #----------
    def sphere_res_cb(self):
        text = self.sphere_res_w.text()
        # print("vis_base: sphere_res_cb(): = ",int(text))
        self.vis_tab.sphere_res_cb(int(text))

    #----------
    def close_filterUI_cb(self):
        self.close()

