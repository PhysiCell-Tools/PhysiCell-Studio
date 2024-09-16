import os
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QLabel, QScrollArea,QPlainTextEdit,QPushButton, QMessageBox
# from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QGroupBox, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,  QMainWindow,QGridLayout,  QFileDialog, QMessageBox, QStackedWidget, QSplitter, QPlainTextEdit


class ModelSummaryUIWindow(QWidget):
    # def __init__(self, output_dir):
    def __init__(self, vis_tab):
        super().__init__()

        self.run_tab = vis_tab.run_tab

        stylesheet = """ 
            QPushButton{ border: 1px solid; border-color: rgb(145, 200, 145); border-radius: 1px;  background-color: lightgreen; color: black; width: 64px; padding-right: 8px; padding-left: 8px; padding-top: 3px; padding-bottom: 3px; } 

            """

        # self.output_dir = output_dir
        self.setStyleSheet(stylesheet)
        
        #-------------------------------------------

        self.scroll = QScrollArea()  # might contain centralWidget

        self.vbox = QVBoxLayout()

        self.title = QLabel(self.run_tab.config_file)
        self.vbox.addWidget(self.title)

        self.plain_text = QPlainTextEdit()  # might contain centralWidget
        self.plain_text.setReadOnly(True)

        self.vbox.addWidget(self.plain_text)

        #----------
        hbox = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("background-color: lightgreen;")
        self.refresh_button.clicked.connect(self.refresh_cb)
        hbox.addWidget(self.refresh_button)

        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("background-color: lightgreen;")
        # self.close_button.setFixedWidth(150)
        self.close_button.clicked.connect(self.close_cb)

        hbox.addWidget(self.close_button)
        self.vbox.addLayout(hbox)

        #----------
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        # self.vbox.addWidget(self.close_button)
        # self.layout.setStretch(0,1000)

        self.setLayout(self.vbox)
        self.resize(300, 320)   # try to fix the size

        self.refresh_cb(self.run_tab.config_file)


    def refresh_cb(self, full_rules_fname):
        # self.run_tab = run_tab
        # current_dir = os.getcwd()
        self.title.setText(self.run_tab.config_file)
        full_rules_fname = self.run_tab.config_file
        # full_rules_fname = os.path.join(current_dir, self.run_tab.config_file)
        print("refresh_cb: full_rules_fname =",full_rules_fname)
        if os.path.isfile(full_rules_fname):
            try:
                # with open("config/rules.csv", 'rU') as f:
                with open(full_rules_fname, 'r') as f:  # vs. 'rU'
                    text = f.read()
                    self.plain_text.setPlainText(text)
            except Exception as e: 
                print(f'model_summary.py: Error opening or reading {full_rules_fname}')
        else:
            print(f'\n\n!!!  WARNING: model_summary.py: refresh_cb(): {full_rules_fname} is not a valid file !!!\n')

        return

    #----------
    def close_cb(self):
        self.close()

