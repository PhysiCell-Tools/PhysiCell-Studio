import os
import sys
import glob
import shutil
import zipfile
import time
import traceback
from pathlib import Path
from datetime import datetime

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QListWidget,
)
from PyQt5.QtGui import QIntValidator
# from PyQt5.QtCore import Qt

from studio_classes import DoubleValidatorWidgetBounded, QCheckBox_custom

try:
    from galaxy_ie_helpers import put, find_matching_history_ids, get, get_user_history
except:
    print("----- Note: cannot import from galaxy_ie_helpers")
    pass


def _list_history_datasets(history_id=None, suffixes=None):
    """(hid, name) pairs, sorted by hid, for visible/successful datasets in the
    current Galaxy History -- the names shown to the user in the load windows.

    suffixes: optional tuple/list of lowercase file extensions (e.g. ('.zip',))
    to restrict the listing to; unfiltered when None."""
    entries = get_user_history(history_id=history_id)
    datasets = [
        (d['hid'], d['name'])
        for d in entries
        if d.get('history_content_type', 'dataset') == 'dataset'
        and d.get('state', 'ok') == 'ok'
        and not d.get('deleted', False)
        and (suffixes is None or d['name'].lower().endswith(tuple(suffixes)))
    ]
    datasets.sort(key=lambda t: t[0], reverse=True)
    return datasets

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

        self.file_id = 0   # for the project (.xml, .csv files)
        self.biwt_file_id = 0
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

        self.xml_creator = None    # set by caller
        self.history_datasets = []    # [(hid, name), ...] currently listed

        self.setStyleSheet(stylesheet)

        self.scroll = QScrollArea()
        self.vbox = QVBoxLayout()
        glayout = QGridLayout()
        self.vbox.addLayout(glayout)

        idx_row = 0
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("background-color: lightgreen;")
        self.refresh_button.clicked.connect(self.refresh_history_cb)
        glayout.addWidget(self.refresh_button, idx_row, 0, 1, 1)

        self.load_file_button = QPushButton("Load selected")
        self.load_file_button.setEnabled(True)
        self.load_file_button.setStyleSheet("background-color: lightgreen;")
        self.load_file_button.clicked.connect(self.load_project_cb)
        glayout.addWidget(self.load_file_button, idx_row, 1, 1, 1)

        idx_row += 1
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.load_project_cb)
        glayout.addWidget(self.history_list, idx_row, 0, 1, 2)

        idx_row += 1
        msg = ("Datasets currently in your Galaxy History are listed above by name.\n"
               "Select a previously saved project .zip (or double-click it) then Load.\n"
               "This will unzip those files into your /config directory and update the Studio.")
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

        self.refresh_history_cb()    # best-effort initial population

    def show_info_message(self, message):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    def refresh_history_cb(self):
        self.history_list.clear()
        self.history_datasets = []
        try:
            self.history_datasets = _list_history_datasets(suffixes=('.zip',))
        except Exception:
            return    # leave the list empty; user can hit Refresh again once History is ready
        for hid, name in self.history_datasets:
            self.history_list.addItem(f"{hid}: {name}")

    def load_project_cb(self, sval=None):
        row = self.history_list.currentRow()
        if row < 0 or row >= len(self.history_datasets):
            QMessageBox.warning(self, "No dataset selected", "Select a dataset from the list first.")
            return
        hid, name = self.history_datasets[row]

        msgBox = QMessageBox()
        try:
            zip_file = get(hid)    # galaxy_ie_helpers API; downloads into /import/<hid>
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(path="config")
                msgBox.setText('Successful extractall into /config ...now loading into the Studio')
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec()
            time.sleep(1)
            self.xml_creator.config_file = "config/PhysiCell_settings.xml"
            self.xml_creator.show_sample_model()

        except FileNotFoundError:
            msg = f"Error: The file for '{name}' was not found."
            print(msg)
            msgBox.setText(msg)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
        except zipfile.BadZipFile:
            msg = f"Error: '{name}' is not a valid or supported zip file."
            print(msg)
            msgBox.setText(msg)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
        except Exception as e:
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

#-----------------------------------------------------------------
class ImportBIWTDataWindow(QWidget):
    def __init__(self, biwt_widget):
        super().__init__()

        stylesheet = """
            QPushButton{ border: 1px solid; border-color: rgb(145, 200, 145); border-radius: 1px;  background-color: lightgreen; color: black; width: 64px; padding-right: 8px; padding-left: 8px; padding-top: 3px; padding-bottom: 3px; }
            """

        # Required, and not a Qt parent — this is a top-level window. It is the
        # BioinformaticsWalkthrough instance to import into.
        self.biwt_widget = biwt_widget
        self.history_datasets = []    # [(hid, name), ...] currently listed

        self.setStyleSheet(stylesheet)

        self.scroll = QScrollArea()
        self.vbox = QVBoxLayout()
        glayout = QGridLayout()
        self.vbox.addLayout(glayout)

        idx_row = 0
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("background-color: lightgreen;")
        self.refresh_button.clicked.connect(self.refresh_history_cb)
        glayout.addWidget(self.refresh_button, idx_row, 0, 1, 1)

        self.load_file_button = QPushButton("Load selected")
        self.load_file_button.setEnabled(True)
        self.load_file_button.setStyleSheet("background-color: lightgreen;")
        self.load_file_button.clicked.connect(self.load_biwt_data_cb)
        glayout.addWidget(self.load_file_button, idx_row, 1, 1, 1)

        idx_row += 1
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.load_biwt_data_cb)
        glayout.addWidget(self.history_list, idx_row, 0, 1, 2)

        idx_row += 1
        msg = ("Datasets currently in your Galaxy History are listed above by name.\n"
               "Select a single-cell data file (*.h5ad, *.csv)\n"
               "(or double-click it) then Load.")
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

        self.refresh_history_cb()    # best-effort initial population

    def show_info_message(self, message):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    def refresh_history_cb(self):
        self.history_list.clear()
        self.history_datasets = []
        try:
            self.history_datasets = _list_history_datasets(suffixes=('.csv', '.h5ad'))
        except Exception:
            return    # leave the list empty; user can hit Refresh again once History is ready
        for hid, name in self.history_datasets:
            self.history_list.addItem(f"{hid}: {name}")

    def load_biwt_data_cb(self, sval=None):
        row = self.history_list.currentRow()
        if row < 0 or row >= len(self.history_datasets):
            QMessageBox.warning(self, "No dataset selected", "Select a dataset from the list first.")
            return
        hid, name = self.history_datasets[row]

        try:
            biwt_file = get(hid)    # galaxy_ie_helpers API; downloads into /import/<hid>, no extension
            ext = Path(name).suffix
            if ext:
                # biwt's loader dispatches on file suffix; the bare "/import/<hid>"
                # path from get() has none, so give it a named copy to read instead.
                named_file = f"{biwt_file}{ext}"
                shutil.copyfile(biwt_file, named_file)
                biwt_file = named_file

            self.biwt_widget._import_file(biwt_file)

        except FileNotFoundError:
            msg = f"Error: The file for '{name}' was not found."
            print(msg)
            msgBox = QMessageBox()
            msgBox.setText(msg)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
        except Exception as e:
            msg = traceback.format_exc()
            self.show_error_message(msg)

    def show_error_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.setFixedWidth(500)
        msg.exec_()
