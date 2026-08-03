import os
import sys
import glob
import zipfile
import shutil
import time
import traceback
from pathlib import Path
from datetime import datetime

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
)
from PyQt5.QtGui import QIntValidator
# from PyQt5.QtCore import Qt

from studio_classes import DoubleValidatorWidgetBounded, QCheckBox_custom

try:
    from galaxy_ie_helpers import put, find_matching_history_ids, get
except:
    print("----- Note: cannot import from galaxy_ie_helpers")
    pass

#-----------------------------------------------------------------
# UI helper widget used by GalaxyHistoryWindow
class ScrollLabel(QScrollArea):
    def __init__(self, *args, **kwargs):
        QScrollArea.__init__(self, *args, **kwargs)
        self.setWidgetResizable(True)
        content = QWidget(self)
        self.setWidget(content)
        lay = QVBoxLayout(content)
        self.label = QLabel(content)
        self.label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.label.setWordWrap(True)
        lay.addWidget(self.label)

    def setText(self, text):
        self.label.setText(text)


#-----------------------------------------------------------------
class GalaxyHistoryWindow(QWidget):
    def __init__(self, xml_creator):
        super().__init__()

        stylesheet = """
            QPushButton{ border: 1px solid; border-color: rgb(145, 200, 145); border-radius: 1px;  background-color: lightgreen; color: black; width: 64px; padding-right: 8px; padding-left: 8px; padding-top: 3px; padding-bottom: 3px; }
            """

        self.file_id = 0
        self.xml_creator = xml_creator

        self.setStyleSheet(stylesheet)

        self.scroll = QScrollArea()
        self.vbox = QVBoxLayout()
        glayout = QGridLayout()
        self.vbox.addLayout(glayout)

        idx_row = 0
        self.get_file_button = QPushButton("get file with ID=")
        self.get_file_button.setEnabled(True)
        self.get_file_button.setStyleSheet("background-color: lightgreen;")
        self.get_file_button.clicked.connect(self.load_file_cb)
        glayout.addWidget(self.get_file_button, idx_row, 0, 1, 2)

        self.file_id_w = QLineEdit("0")
        self.file_id_w.setEnabled(True)
        self.file_id_w.setFixedWidth(70)
        self.file_id_w.setValidator(QIntValidator())
        self.file_id_w.textChanged.connect(self.file_id_changed)
        glayout.addWidget(self.file_id_w, idx_row, 2, 1, 1)

        idx_row += 1
        glayout.addWidget(QLabel(f"pwd: {Path.cwd()}"), idx_row, 0, 1, 2)

        idx_row += 1
        self.show_files_button = QPushButton("dir")
        self.show_files_button.setStyleSheet("background-color: lightgreen;")
        self.show_files_button.clicked.connect(self.show_files_cb)
        glayout.addWidget(self.show_files_button, idx_row, 0, 1, 1)

        self.relative_path = QLineEdit(".")
        self.relative_path.setFixedWidth(80)
        glayout.addWidget(self.relative_path, idx_row, 1, 1, 1)

        self.dir_files = ScrollLabel(self)
        self.dir_files.setGeometry(100, 100, 200, 80)
        self.vbox.addWidget(self.dir_files)

        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("background-color: lightgreen;")
        self.close_button.clicked.connect(self.close_galaxy_history_cb)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        self.vbox.addWidget(self.close_button)
        self.setLayout(self.vbox)
        self.resize(200, 200)

    def load_file_cb(self, sval):
        self.file_id = int(self.file_id_w.text())
        try:
            msgBox = QMessageBox()
            msgBox.setText('Copying the requested data from the Galaxy History')
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            get(self.file_id)
        except:
            print("Unable to get the file from History")
            msgBox = QMessageBox()
            msgBox.setText(f'load_file_cb: Unable to get file with History ID {self.file_id}. Perhaps you got it previously.')
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()

    def file_id_changed(self, sval):
        try:
            self.file_id = int(sval)
        except:
            pass

    def show_files_cb(self):
        self.dir_files.setText(str(os.listdir(self.relative_path.text())))

    def close_galaxy_history_cb(self):
        self.close()


#-----------------------------------------------------------------
class LoadProjectWindow(QWidget):
    def __init__(self):
        super().__init__()

        stylesheet = """
            QPushButton{ border: 1px solid; border-color: rgb(145, 200, 145); border-radius: 1px;  background-color: lightgreen; color: black; width: 64px; padding-right: 8px; padding-left: 8px; padding-top: 3px; padding-bottom: 3px; }
            """

        self.file_id = 0
        self.xml_creator = None    # set by caller

        self.setStyleSheet(stylesheet)

        self.scroll = QScrollArea()
        self.vbox = QVBoxLayout()
        glayout = QGridLayout()
        self.vbox.addLayout(glayout)

        idx_row = 0
        self.load_file_button = QPushButton("Load project with ID=")
        self.load_file_button.setFixedWidth(270)
        self.load_file_button.setEnabled(True)
        self.load_file_button.setStyleSheet("background-color: lightgreen;")
        self.load_file_button.clicked.connect(self.load_project_cb)
        # glayout.addWidget(self.load_file_button, idx_row, 0, 1, 2) # w, row, column, rowspan, colspan
        glayout.addWidget(self.load_file_button, idx_row, 0, 1, 1) # w, row, column, rowspan, colspan

        self.file_id_w = QLineEdit("0")
        self.file_id_w.setEnabled(True)
        self.file_id_w.setFixedWidth(70)
        self.file_id_w.setValidator(QIntValidator())
        self.file_id_w.textChanged.connect(self.file_id_changed)
        glayout.addWidget(self.file_id_w, idx_row, 1, 1, 1)

        idx_row += 1
        msg = ("Enter the integer ID value of a previously saved project on the\n"
               "Galaxy History then press the Load button above.\n"
               "This will unzip those files into your /config directory and update the Studio.")
        # glayout.addWidget(QLabel(msg), idx_row, 0, 1, 3)
        glayout.addWidget(QLabel(msg), idx_row, 0, 1, 2)

        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("background-color: lightgreen;")
        self.close_button.clicked.connect(self.close)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        self.vbox.addWidget(self.close_button)
        self.setLayout(self.vbox)
        # self.resize(190, 200)

    def show_info_message(self, message):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    def load_project_cb(self, sval):
        self.file_id = int(self.file_id_w.text())
        zip_file = "my_model.zip"
        msgBox = QMessageBox()
        from_filename = "/import/"

        try:
            msgBox.setText('Copying the requested data from the Galaxy History')
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            get(self.file_id)
            from_filename += str(self.file_id)
            try:
                print(f"load_project_cb(): attempting to copy {from_filename} to {zip_file}")
                shutil.copy(from_filename, zip_file)
                os.remove(from_filename)
            except:
                msg = f"Error: unable to copy {from_filename} to {zip_file}"
                print(msg)
                msgBox.setText(msg)
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec()
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(path="config")
                msgBox.setText('Successful extractall into /config ...now loading into the Studio')
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec()
            time.sleep(1)
            self.xml_creator.config_file = "config/PhysiCell_settings.xml"
            self.xml_creator.show_sample_model()

        except FileNotFoundError:
            msg = f"Error: The file {zip_file} was not found."
            print(msg)
            msgBox.setText(msg)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
        except zipfile.BadZipFile:
            msg = f"Error: The file {zip_file} is not a valid or supported zip file."
            print(msg)
            msgBox.setText(msg)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
        except Exception as e:
            # msg = f'load_project_cb(): There was a problem getting or unzipping {from_filename} with History ID {self.file_id}.'
            msg = traceback.format_exc()
            self.show_error_message(msg)
            # print(msg)
            # msgBox.setText(msg)
            # msgBox.setStandardButtons(QMessageBox.Ok)
            # msgBox.exec()

    def show_error_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.setFixedWidth(500)
        msg.exec_()

    def file_id_changed(self, sval):
        try:
            self.file_id = int(sval)
        except:
            pass


#-----------------------------------------------------------------
class SaveProjectWindow(QWidget):
    def __init__(self):
        super().__init__()

        stylesheet = """
            QPushButton{ border: 1px solid; border-color: rgb(145, 200, 145); border-radius: 1px;  background-color: lightgreen; color: black; width: 64px; padding-right: 8px; padding-left: 8px; padding-top: 3px; padding-bottom: 3px; }
            """

        self.xml_creator = None    # set by caller

        self.setStyleSheet(stylesheet)

        self.scroll = QScrollArea()
        self.vbox = QVBoxLayout()
        glayout = QGridLayout()
        self.vbox.addLayout(glayout)

        idx_row = 0
        self.save_file_button = QPushButton("Save .zip")
        self.save_file_button.setFixedWidth(90)
        self.save_file_button.setEnabled(True)
        self.save_file_button.setStyleSheet("background-color: lightgreen;")
        self.save_file_button.clicked.connect(self.save_project_cb)
        glayout.addWidget(self.save_file_button, idx_row, 0, 1, 1) # w, row, column, rowspan, colspan

        # self.project_name_w = QLineEdit("my_model.zip")
        self.project_name_w = QLineEdit("my_model")
        # self.project_name_w.setFixedWidth(200)
        self.project_name_w.setEnabled(True)
        glayout.addWidget(self.project_name_w, idx_row, 1, 1, 1)


        self.timestamp_w = QCheckBox_custom("time-stamp")
        glayout.addWidget(self.timestamp_w, idx_row, 2, 1, 1)

        idx_row += 1
        msg = ("Click Save to have your project zipped and copied to the Galaxy History.\n"
               "Rename the base filename if you wish.\n"
               "It may take several seconds to appear in your History.")
        glayout.addWidget(QLabel(msg), idx_row, 0, 1, 3)

        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("background-color: lightgreen;")
        self.close_button.clicked.connect(self.close)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        self.vbox.addWidget(self.close_button)
        self.setLayout(self.vbox)

    def save_project_cb(self):
        fname = self.project_name_w.text()
        if self.timestamp_w.isChecked():
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            fname = f"{fname}_{ts}.zip"
        else:
            fname = f"{fname}.zip"

        msgBox = QMessageBox()
        msgBox.setText(f"This will bundle your current model's config file, its cells/substrates ICs, and rules, "
                   f"then copy '{fname}' to the Galaxy History.")
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        if msgBox.exec() == QMessageBox.Cancel:
            return

        self.xml_creator.save_cb()

        file_str = os.path.join(os.getcwd(), "config/*.csv")
        # print('-------- save_project_cb(): zip up all', file_str)
        try:
            with zipfile.ZipFile(fname, 'w') as myzip:
                myzip.write(self.xml_creator.current_xml_file,
                            os.path.basename(self.xml_creator.current_xml_file))
                for f in glob.glob(file_str):
                    myzip.write(f, os.path.basename(f))
            put(fname)
        except KeyError:
            msg = traceback.format_exc()
            self.show_error_message(msg)

    def show_error_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.setFixedWidth(500)
        msg.exec_()


#-----------------------------------------------------------------
# Studio-level helper functions (called as save_project_galaxy(self), etc.)

def save_project_galaxy(self):
    # fname = "my_model.zip"
    fname = "my_model"
    file_str = os.path.join(os.getcwd(), "config/*.csv")
    print('-------- save_project_galaxy(): zip up all', file_str)

    msgBox = QMessageBox()
    msgBox.setText(f"This will bundle your current model's config file, its cells/substrates ICs, and rules, "
                   f"then copy that file to the Galaxy History.")
                #    f"then copy '{fname}' to the Galaxy History.")
    msgBox.setIcon(QMessageBox.Information)
    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    if msgBox.exec() == QMessageBox.Cancel:
        return

    try:
        with zipfile.ZipFile(fname, 'w') as myzip:
            myzip.write(self.current_xml_file, os.path.basename(self.current_xml_file))
            for f in glob.glob(file_str):
                myzip.write(f, os.path.basename(f))
        put(fname)
    except KeyError:
        self.show_error_message(traceback.format_exc())


def save_project_galaxy_ui(self):
    self.galaxy_save_project_UI = SaveProjectWindow()
    self.galaxy_save_project_UI.xml_creator = self
    self.galaxy_save_project_UI.hide()
    self.galaxy_save_project_UI.show()


def load_project_galaxy_history(self):
    self.project_historyUI = LoadProjectWindow()
    self.project_historyUI.xml_creator = self
    self.project_historyUI.hide()
    self.project_historyUI.show()


def get_galaxy_history(self):
    self.galaxy_historyUI = GalaxyHistoryWindow(self)
    self.galaxy_historyUI.hide()
    self.galaxy_historyUI.show()


def download_config_galaxy(self):
    fname = self.current_xml_file
    msgBox = QMessageBox()
    msgBox.setText("This will copy your current model's config file to the Galaxy History.")
    msgBox.setIcon(QMessageBox.Information)
    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    if msgBox.exec() == QMessageBox.Cancel:
        return
    try:
        put(fname)
    except:
        self.show_error_message(f"Error: put({fname})")


def download_zipped_csv_galaxy(self):
    msgBox = QMessageBox()
    msgBox.setText("This will copy a zip file of all output/*.csv to the Galaxy History.")
    msgBox.setIcon(QMessageBox.Information)
    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    if msgBox.exec() == QMessageBox.Cancel:
        return
    fname = "all_csv.zip"
    file_str = os.path.join(os.getcwd(), "output/*.csv")
    print('-------- download_zipped_csv_galaxy(): zip up all', file_str)
    try:
        with zipfile.ZipFile(fname, 'w') as myzip:
            for f in glob.glob(file_str):
                myzip.write(f, os.path.basename(f))
    except:
        self.show_error_message("Error zipping all output/*.csv")
        return
    try:
        put(fname)
    except:
        self.show_error_message(f"Error: put({fname})")


def download_all_zipped_galaxy(self):
    msgBox = QMessageBox()
    msgBox.setText("This will copy a zip file of all output/* to the Galaxy History. "
                   "It runs in the background and will not affect your ability to continue using the Studio.")
    msgBox.setIcon(QMessageBox.Information)
    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    if msgBox.exec() == QMessageBox.Cancel:
        return
    fname = "all_output.zip"
    file_str = os.path.join(os.getcwd(), "output/*")
    print('-------- download_all_zipped_galaxy(): zip up all', file_str)
    try:
        with zipfile.ZipFile(fname, 'w') as myzip:
            for f in glob.glob(file_str):
                myzip.write(f, os.path.basename(f))
    except:
        self.show_error_message("Error zipping all output/*")
        return
    try:
        put(fname)
    except:
        self.show_error_message(f"Error: put({fname})")
