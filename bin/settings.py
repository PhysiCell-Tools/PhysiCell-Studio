from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QGroupBox, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,  QMainWindow,QGridLayout, QPushButton, QFileDialog, QMessageBox, QStackedWidget, QSplitter

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        # self.setFrameShadow(QFrame.Plain)
        # self.setStyleSheet("border:1px solid black")

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


class StudioSettings(QWidget):
    # def __init__(self, output_dir):
    def __init__(self, gui_w, min_size_flag):   # use dict eventually
        super().__init__()

        self.gui_w = gui_w
        self.min_size = min_size_flag
        # self.reset = reset
        # self.vis_tab = vis_tab

        stylesheet = """ 
            QPushButton{ border: 1px solid; border-color: rgb(145, 200, 145); border-radius: 1px;  background-color: lightgreen; color: black; width: 64px; padding-right: 8px; padding-left: 8px; padding-top: 3px; padding-bottom: 3px; } 

            """

        # self.output_dir = output_dir
        self.setStyleSheet(stylesheet)
        
        #-------------------------------------------
        self.scroll = QScrollArea()  # might contain centralWidget

        self.vbox = QVBoxLayout()
        glayout = QGridLayout()

        #------------
        idx_row = 0

        self.min_size_checkbox = QCheckBox_custom('min size (1100x770)')
        self.min_size_checkbox.setChecked(self.min_size)
        self.min_size_checkbox.clicked.connect(self.toggle_min_size_cb)
        idx_row += 1
        glayout.addWidget(self.min_size_checkbox, idx_row,0,1,2) # w, row, column, rowspan, colspan

        self.vbox.addLayout(glayout)

        #----------
        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("background-color: lightgreen;")
        # self.close_button.setFixedWidth(150)
        self.close_button.clicked.connect(self.close_filterUI_cb)

        self.vbox.addWidget(self.close_button)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        self.vbox.addWidget(self.close_button)
        # self.layout.setStretch(0,1000)

        self.setLayout(self.vbox)
        self.resize(200, 120)   # try to fix the size

    #----------
    def close_filterUI_cb(self):
        self.close()

    def toggle_min_size_cb(self):
        # print("toggle")
        if self.min_size_checkbox.isChecked():
            self.gui_w.setMinimumSize(1100, 770)  #width, height of window (avoid hard-coding in future)
        else:
            self.gui_w.setMinimumSize(0, 0)  