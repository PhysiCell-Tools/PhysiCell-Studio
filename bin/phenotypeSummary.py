from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QGroupBox, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,  QMainWindow,QGridLayout, QPushButton, QFileDialog, QMessageBox, QStackedWidget, QSplitter, QPlainTextEdit
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


class PhenotypeWindow(QWidget):
    def __init__(self, celldef_tab):   
        super().__init__()

        # self.reset = reset
        self.celldef_tab = celldef_tab

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
        # if reset:
        #     self.reset_filters()

        #------------
        idx_row = 0
        glayout.addWidget(QLabel("Phenotype summary:"), idx_row,0,1,3) # w, row, column, rowspan, colspan

        self.text = QPlainTextEdit()
        self.text.resize(300,400)
        self.text.setReadOnly(True)
        # self.text.appendPlainText("mary had a liittle lamb\nhis fleece was white.")
        # QLabel('This is label', self)
        self.vbox.addWidget(self.text)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("background-color: lightgreen;")
        self.refresh_button.clicked.connect(self.refresh_phenotypeUI_cb)
        self.vbox.addWidget(self.refresh_button)

        #----------
        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("background-color: lightgreen;")
        # self.close_button.setFixedWidth(150)
        self.close_button.clicked.connect(self.close_phenotypeUI_cb)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        self.vbox.addWidget(self.close_button)
        # self.layout.setStretch(0,1000)

        self.setLayout(self.vbox)
        self.resize(200, 220)   # try to fix the size


    #----------
    def refresh_phenotypeUI_cb(self):
        print(self.celldef_tab.param_d)
        self.celldef_tab.summary(self.text)

    #----------
    def close_phenotypeUI_cb(self):
        self.close()

