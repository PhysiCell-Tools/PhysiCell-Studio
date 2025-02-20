from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QGroupBox, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,  QMainWindow,QGridLayout, QPushButton, QFileDialog, QMessageBox, QStackedWidget, QSplitter
from studio_classes import QCheckBox_custom
# from PyQt5.QtWidgets import QCompleter, QSizePolicy
# from PyQt5.QtCore import QSortFilterProxyModel
# from PyQt5.QtSvg import QSvgWidget
# from PyQt5.QtGui import QPainter
# from PyQt5.QtCore import QRectF, Qt

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        # self.setFrameShadow(QFrame.Plain)
        # self.setStyleSheet("border:1px solid black")


class FilterUI3DWindow(QWidget):
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

        # (checkbox_w,down_w,val_w,up_w) = self.create_row('XY slice: ')
        idx_row = 0
        glayout.addWidget(QLabel('Substrate: (press Enter after value change)'), idx_row,0,1,3) # w, row, column, rowspan, colspan

        self.xy_slice_checkbox = QCheckBox_custom('XY slice:  Z= ')
        self.xy_slice_checkbox.setChecked(self.xy_slice_flag)
        self.xy_slice_checkbox.clicked.connect(self.xy_slice_cb)
        idx_row += 1
        glayout.addWidget(self.xy_slice_checkbox, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.xy_slice_w = QLineEdit()
        self.xy_slice_w.setValidator(QtGui.QDoubleValidator())
        # val.textChanged[str].connect(self.xy_slice_val_cb)
        self.xy_slice_w.returnPressed.connect(self.xy_slice_val_cb)
        self.xy_slice_w.setText(str(self.xy_slice_value))
        glayout.addWidget(self.xy_slice_w, idx_row,1,1,1) # w, row, column, rowspan, colspan

        #--------------------------
        self.yz_slice_checkbox = QCheckBox_custom('YZ slice:  X= ')
        self.yz_slice_checkbox.setChecked(self.yz_slice_flag)
        self.yz_slice_checkbox.clicked.connect(self.yz_slice_cb)
        idx_row += 1
        glayout.addWidget(self.yz_slice_checkbox, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.yz_slice_w = QLineEdit()
        self.yz_slice_w.setValidator(QtGui.QDoubleValidator())
        self.yz_slice_w.returnPressed.connect(self.yz_slice_val_cb)
        self.yz_slice_w.setText(str(self.yz_slice_value))
        glayout.addWidget(self.yz_slice_w, idx_row,1,1,1) # w, row, column, rowspan, colspan

        #--------------------------
        self.xz_slice_checkbox = QCheckBox_custom('XZ slice:  Y= ')
        self.xz_slice_checkbox.setChecked(self.xz_slice_flag)
        self.xz_slice_checkbox.clicked.connect(self.xz_slice_cb)
        idx_row += 1
        glayout.addWidget(self.xz_slice_checkbox, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.xz_slice_w = QLineEdit()
        self.xz_slice_w.setValidator(QtGui.QDoubleValidator())
        self.xz_slice_w.returnPressed.connect(self.xz_slice_val_cb)
        self.xz_slice_w.setText(str(self.xz_slice_value))
        glayout.addWidget(self.xz_slice_w, idx_row,1,1,1) # w, row, column, rowspan, colspan

        #------
        self.voxels_checkbox = QCheckBox_custom('All voxels')
        self.voxels_checkbox.setChecked(self.voxels_flag)
        self.voxels_checkbox.clicked.connect(self.voxels_cb)
        idx_row += 1
        # glayout.addWidget(self.voxels_checkbox, idx_row,0,1,1) # w, row, column, rowspan, colspan
        # voxels_act = view3D_menu.addAction("All voxels")
        # voxels_act.setChecked(False)

        #--------------------------------
        idx_row += 1
        glayout.addWidget(QHLine(), idx_row,0,1,3) # w, row, column, rowspan, colspan

        idx_row += 1
        glayout.addWidget(QLabel('Cells: (press Enter after value change)'), idx_row,0,1,3) # w, row, column, rowspan, colspan

        self.xy_clip_checkbox = QCheckBox_custom('XY clip:  Z=')
        self.xy_clip_checkbox.setChecked(self.xy_clip_flag)
        self.xy_clip_checkbox.clicked.connect(self.xy_clip_cb)
        idx_row += 1
        glayout.addWidget(self.xy_clip_checkbox, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.xy_clip_w = QLineEdit()
        self.xy_clip_w.setValidator(QtGui.QDoubleValidator())
        self.xy_clip_w.returnPressed.connect(self.xy_clip_val_cb)
        self.xy_clip_w.setText('0.0')
        glayout.addWidget(self.xy_clip_w, idx_row,1,1,1) # w, row, column, rowspan, colspan

        self.xy_flip_checkbox = QCheckBox_custom('flip')
        self.xy_flip_checkbox.setChecked(self.xy_flip_flag)
        self.xy_flip_checkbox.clicked.connect(self.xy_flip_cb)
        glayout.addWidget(self.xy_flip_checkbox, idx_row,2,1,1) # w, row, column, rowspan, colspan

        #--------------------------
        self.yz_clip_checkbox = QCheckBox_custom('YZ clip:  X=')
        self.yz_clip_checkbox.setChecked(self.yz_clip_flag)
        self.yz_clip_checkbox.clicked.connect(self.yz_clip_cb)
        idx_row += 1
        glayout.addWidget(self.yz_clip_checkbox, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.yz_clip_w = QLineEdit()
        self.yz_clip_w.setValidator(QtGui.QDoubleValidator())
        self.yz_clip_w.returnPressed.connect(self.yz_clip_val_cb)
        self.yz_clip_w.setText('0.0')
        glayout.addWidget(self.yz_clip_w, idx_row,1,1,1) # w, row, column, rowspan, colspan

        self.yz_flip_checkbox = QCheckBox_custom('flip')
        self.yz_flip_checkbox.setChecked(self.yz_flip_flag)
        self.yz_flip_checkbox.clicked.connect(self.yz_flip_cb)
        glayout.addWidget(self.yz_flip_checkbox, idx_row,2,1,1) # w, row, column, rowspan, colspan

        #--------------------------
        self.xz_clip_checkbox = QCheckBox_custom('XZ clip:  Y=')
        self.xz_clip_checkbox.setChecked(self.xz_clip_flag)
        self.xz_clip_checkbox.clicked.connect(self.xz_clip_cb)
        idx_row += 1
        glayout.addWidget(self.xz_clip_checkbox, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.xz_clip_w = QLineEdit()
        self.xz_clip_w.setValidator(QtGui.QDoubleValidator())
        self.xz_clip_w.returnPressed.connect(self.xz_clip_val_cb)
        self.xz_clip_w.setText('0.0')
        glayout.addWidget(self.xz_clip_w, idx_row,1,1,1) # w, row, column, rowspan, colspan

        self.xz_flip_checkbox = QCheckBox_custom('flip')
        self.xz_flip_checkbox.setChecked(self.xz_flip_flag)
        self.xz_flip_checkbox.clicked.connect(self.xz_flip_cb)
        glayout.addWidget(self.xz_flip_checkbox, idx_row,2,1,1) # w, row, column, rowspan, colspan

        #------
        idx_row += 1
        glayout.addWidget(QHLine(), idx_row,0,1,3) # w, row, column, rowspan, colspan

        self.axes_checkbox = QCheckBox_custom('Axes')
        self.axes_checkbox.setChecked(self.axes_flag)
        self.axes_checkbox.clicked.connect(self.axes_cb)
        idx_row += 1
        glayout.addWidget(self.axes_checkbox, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.boundary_checkbox = QCheckBox_custom('BBox')
        self.boundary_checkbox.setChecked(self.boundary_flag)
        self.boundary_checkbox.clicked.connect(self.boundary_cb)
        glayout.addWidget(self.boundary_checkbox, idx_row,1,1,1) # w, row, column, rowspan, colspan


        #------
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Sphere res(3-42):"))

        self.sphere_res_w = QLineEdit()
        self.sphere_res_w.setValidator(QtGui.QIntValidator(3,42))
        self.sphere_res_w.returnPressed.connect(self.sphere_res_cb)
        self.sphere_res_w.setText('8')   # match what's defined in vis3D_tab
        hbox.addWidget(self.sphere_res_w)
        idx_row += 1
        glayout.addLayout(hbox, idx_row,0,1,2) # w, row, column, rowspan, colspan

        #-----------
        idx_row += 1
        glayout.addWidget(QHLine(), idx_row,0,1,3) # w, row, column, rowspan, colspan

        idx_row += 1
        self.save_png_checkbox = QCheckBox_custom('save frame*.png')
        self.save_png_checkbox.clicked.connect(self.save_png_cb)
        idx_row += 1
        glayout.addWidget(self.save_png_checkbox, idx_row,0,1,2) # w, row, column, rowspan, colspan

        idx_row += 1
        self.cells_csv_button = QPushButton("Save snap.csv")
        self.cells_csv_button.setStyleSheet("background-color: lightgreen;")
        self.cells_csv_button.clicked.connect(self.cells_csv_cb)
        glayout.addWidget(self.cells_csv_button, idx_row,0,1,2) # w, row, column, rowspan, colspan

        idx_row += 1
        glayout.addWidget(QLabel("Keypress j (joystick) vs. t (trackball) "), idx_row,0,1,3) 
        idx_row += 1
        glayout.addWidget(QLabel("Keypress r (reset view)"), idx_row,0,1,3) # w, row, column, rowspan, colspan
        idx_row += 1
        glayout.addWidget(QLabel("(Help menu -> User Guide: Plot 3D for more)"), idx_row,0,1,3)

        #-----------------------
        self.vbox.addLayout(glayout)

        #--------------------
        # axes_act = view3D_menu.addAction("Axes")

        # self.svg_view.setFixedSize(500, 500)
        # self.svgView.setLayout(self.vbox)
        # self.layout.addWidget(self.svg_view)

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
        # self.resize(250, 250)


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
        self.boundary_flag = True

    #--------
    def xy_slice_cb(self):
        # print("vis_base: xy_slice_cb(): self.xy_slice_checkbox.isChecked()= ",self.xy_slice_checkbox.isChecked())
        # self.xy_slice_toggle_cb(self.xy_slice_checkbox.isChecked())
        self.vis_tab.xy_slice_toggle_cb(self.xy_slice_checkbox.isChecked())
        return

    def xy_slice_val_cb(self):
        text = self.xy_slice_w.text()
        # print(f'----- xy_slice_val_cb = {text}')
        try:
            self.vis_tab.xy_slice_value_cb(float(text))
        except:
            pass

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
    def boundary_cb(self):
        self.vis_tab.boundary_toggle_cb(self.boundary_checkbox.isChecked())
    #----------
    def sphere_res_cb(self):
        text = self.sphere_res_w.text()
        # print("vis_base: sphere_res_cb(): = ",int(text))
        self.vis_tab.sphere_res_cb(int(text))

    def save_png_cb(self):
        self.vis_tab.png_frame = 0
        self.vis_tab.save_png = self.save_png_checkbox.isChecked()

    def cells_csv_cb(self):
        self.vis_tab.write_cells_csv_cb()

    #----------
    def close_filterUI_cb(self):
        self.close()

