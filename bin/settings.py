from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QGridLayout, QPushButton
from studio_classes import QCheckBox_custom

class StudioSettings(QWidget):
    def __init__(self, gui_w, min_size_flag):   # use dict eventually
        super().__init__()

        self.gui_w = gui_w
        self.min_size = min_size_flag

        stylesheet = """ 
            QPushButton{ border: 1px solid; border-color: rgb(145, 200, 145); border-radius: 1px;  background-color: lightgreen; color: black; width: 64px; padding-right: 8px; padding-left: 8px; padding-top: 3px; padding-bottom: 3px; } 

            """

        self.setStyleSheet(stylesheet)
        
        #-------------------------------------------
        self.scroll = QScrollArea()
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
        self.close_button.clicked.connect(self.close_settings_cb)

        self.vbox.addWidget(self.close_button)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        self.vbox.addWidget(self.close_button)
        # self.layout.setStretch(0,1000)

        self.setLayout(self.vbox)
        self.resize(200, 120)   # try to fix the size

    #----------
    def close_settings_cb(self):
        self.close()

    def toggle_min_size_cb(self):
        if self.min_size_checkbox.isChecked():
            self.gui_w.setMinimumSize(1100, 770)  #width, height of window (avoid hard-coding in future)
        else:
            self.gui_w.setMinimumSize(0, 0)  