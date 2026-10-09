import os
import glob
import base64
import zipfile

import time
import shutil # for possible copy of file
import traceback
from datetime import datetime
from pathlib import Path
import urllib.request
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from github import Github

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QListWidget,
)
# from PyQt5.QtGui import QIntValidator

from studio_classes import QCheckBox_custom

class ExportProjectWindow(QWidget):
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
        self.export_file_button = QPushButton("Export .zip")
        self.export_file_button.setFixedWidth(90)
        self.export_file_button.setEnabled(True)
        self.export_file_button.setStyleSheet("background-color: lightgreen;")
        self.export_file_button.clicked.connect(self.export_project_cb)
        glayout.addWidget(self.export_file_button, idx_row, 0, 1, 1) # w, row, column, rowspan, colspan

        self.project_name_w = QLineEdit("my_model")
        # self.project_name_w.setFixedWidth(200)
        self.project_name_w.setEnabled(True)
        glayout.addWidget(self.project_name_w, idx_row, 1, 1, 1)


        self.timestamp_w = QCheckBox_custom("time-stamp")
        glayout.addWidget(self.timestamp_w, idx_row, 2, 1, 1)

        idx_row += 1
        glayout.addWidget(QLabel("Export project (.zip) to GitHub:"), idx_row, 0, 1, 1)
        # upload_binary_file(..., repo_name, local_path, github_path, commit_message, branch_name):
        glayout.addWidget(QLabel("username"), idx_row, 1, 1, 1)
        glayout.addWidget(QLabel("repo"), idx_row, 2, 1, 1)

        idx_row += 1
        # self.github_user_name = "user"
        self.github_user_name = None
        self.github_user_w = QLineEdit(self.github_user_name)
        # self.github_user_w.setFixedWidth(200)
        self.github_user_w.setEnabled(True)
        glayout.addWidget(self.github_user_w, idx_row, 1, 1, 1)

        # self.github_repo_name = "repo"
        self.github_repo_name = None
        self.github_repo_w = QLineEdit(self.github_repo_name)
        # self.github_user_w.setFixedWidth(200)
        self.github_repo_w.setEnabled(True)
        glayout.addWidget(self.github_repo_w, idx_row, 2, 1, 1)

        idx_row += 1
        msg = ("Click Export to have your project zipped and copied to your GitHub repo.\n"
               "Rename the base filename if you wish.\n"
               "It may take a few seconds to appear in your repo.")
        glayout.addWidget(QLabel(msg), idx_row, 0, 1, 3)

        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("background-color: lightgreen;")
        self.close_button.clicked.connect(self.close)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        self.vbox.addWidget(self.close_button)
        self.setLayout(self.vbox)

    def show_info_message(self, message):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    def export_project_cb(self):
        self.github_user_name = self.github_user_w.text()
        self.github_repo_name = self.github_repo_w.text()

        print(f"export_project_cb():  self.github_user_name = {self.github_user_name}")
        print(f"export_project_cb():  len(self.github_user_name) = {len(self.github_user_name)}")
        if len(self.github_user_name) == 0:
            self.show_error_message("Must provide a valid GitHub username")
            return

        print(f"export_project_cb():  self.github_repo_name = {self.github_repo_name}")
        print(f"export_project_cb():  len(self.github_repo_name) = {len(self.github_repo_name)}")
        if len(self.github_repo_name) == 0:
            self.show_error_message("Must provide a valid GitHub repo")
            return

        fname = self.project_name_w.text()
        if self.timestamp_w.isChecked():
            ts = datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S")
            fname = f"{fname}_{ts}.zip"
        else:
            fname = f"{fname}.zip"

        msgBox = QMessageBox()
        msgBox.setText(f"This will bundle your current model's config file, its cells/substrates ICs, and rules, "
                   f"then copy '{fname}' to the specified GitHub repo.")
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        if msgBox.exec() == QMessageBox.Cancel:
            return

        # self.show_info_message(f"export_project_cb(): zipping proj into {fname}")
        self.show_info_message(f"zipping project into {fname}")
        file_str = os.path.join(os.getcwd(), "config/*.csv")
        # print('-------- export_project_cb(): zip up all', file_str)
        try:
            with zipfile.ZipFile(fname, 'w') as myzip:
                myzip.write(self.xml_creator.current_xml_file,
                            os.path.basename(self.xml_creator.current_xml_file))
                for f in glob.glob(file_str):
                    myzip.write(f, os.path.basename(f))

            # put(fname)
            # self.upload_binary_file(repo_name, local_path, github_path, commit_message, branch_name)
            # repo_name = self.github_user_w.text() + "/" + self.github_repo_w.text()
            repo_name = os.path.join(self.github_user_name, self.github_repo_name)
            # self.show_info_message(f"repo_name is {repo_name}")

            # print("repo_name= ",repo_name)
            github_pat_str = self.xml_creator.project_io.github_pat # token (PAT)
            if github_pat_str is None:
                # pass
                # self.show_error_message("github_pat_str is None")
                self.show_error_message("Your GitHub Personal Access Token is unknown.\nUse the Studio->Settings panel to get it.")
                return
            else:
                github_pat_str = github_pat_str.rstrip("\r\n")

            # self.show_info_message(f"github_pat_str is {github_pat_str}. Calling upload_binary_file: repo={repo_name}, fname={fname}")
            self.upload_binary_file(github_pat_str, repo_name, fname, fname, "update project", "main")
            self.show_info_message("If successful, your .zip project should appear in your repo soon.")
        except KeyError:
            msg = traceback.format_exc()
            self.show_error_message(msg)


    def upload_binary_file(self, pa_token, repo_name, local_path, github_path, commit_message, branch_name):
        """Upload a binary file to a GitHub repository using a GitHub personal access token"""
        try:
            g = Github(pa_token)
            repo = g.get_repo(repo_name)
        except Exception:
            self.show_error_message(f"Error connecting to {repo_name}")
            return

        with open(local_path, 'rb') as f:
            content = f.read()

        try:
            contents = repo.get_contents(github_path, ref=branch_name)
            repo.update_file(
                contents.path,
                commit_message,
                content,
                contents.sha,
                branch=branch_name
            )
            print(f"File '{github_path}' updated successfully.")
        except Exception:
            repo.create_file(
                github_path,
                commit_message,
                content,
                branch=branch_name
            )
            print(f"File '{github_path}' created successfully.")

    def show_error_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.setFixedWidth(500)
        msg.exec_()

#--------------------------------------
class ImportProjectWindow(QWidget):
    def __init__(self):
        super().__init__()

        stylesheet = """
            QPushButton{ border: 1px solid; border-color: rgb(145, 200, 145); border-radius: 1px;  background-color: lightgreen; color: black; width: 64px; padding-right: 8px; padding-left: 8px; padding-top: 3px; padding-bottom: 3px; }
            """

        self.xml_creator = None    # set by caller
        self.zip_names = []    # .zip filenames currently listed, parallel to self.zip_list rows

        self.setStyleSheet(stylesheet)

        self.scroll = QScrollArea()
        self.vbox = QVBoxLayout()
        glayout = QGridLayout()
        self.vbox.addLayout(glayout)

        idx_row = 0
        glayout.addWidget(QLabel("Import project (.zip) from github.com:"), idx_row, 0, 1, 2)

        idx_row += 1
        glayout.addWidget(QLabel("path:"), idx_row, 0, 1, 1)
        self.path_name = None
        self.path_name_w = QLineEdit(self.path_name)
        self.path_name_w.setPlaceholderText("owner/repo or owner/repo/subdir")
        self.path_name_w.setToolTip("owner/repo, optionally followed by a path within the repo, e.g.\nPhysiCell-Tools/PhysiCell-Studio/samples")
        self.path_name_w.setEnabled(True)
        glayout.addWidget(self.path_name_w, idx_row, 1, 1, 1)

        idx_row += 1
        glayout.addWidget(QLabel("branch:"), idx_row, 0, 1, 1)
        self.branch_name = "main"
        self.branch_name_w = QLineEdit(self.branch_name)
        self.branch_name_w.setEnabled(True)
        glayout.addWidget(self.branch_name_w, idx_row, 1, 1, 1)

        idx_row += 1
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("background-color: lightgreen;")
        self.refresh_button.clicked.connect(self.refresh_zip_list_cb)
        glayout.addWidget(self.refresh_button, idx_row, 0, 1, 1)

        self.import_file_button = QPushButton("Import selected")
        self.import_file_button.setEnabled(True)
        self.import_file_button.setStyleSheet("background-color: lightgreen;")
        self.import_file_button.clicked.connect(self.import_project_cb)
        glayout.addWidget(self.import_file_button, idx_row, 1, 1, 1)

        idx_row += 1
        self.zip_list = QListWidget()
        self.zip_list.itemDoubleClicked.connect(self.import_project_cb)
        glayout.addWidget(self.zip_list, idx_row, 0, 1, 2)

        idx_row += 1
        msg = ("Enter a GitHub path (owner/repo, optionally /subdir) and branch, then click Refresh.\n"
               ".zip files found there are listed above by name.\n"
               "Select one (or double-click it) then Import selected.\n"
               "The Studio should be refreshed with that model's parameters.\n"
               "It may take a few seconds to update.")
        glayout.addWidget(QLabel(msg), idx_row, 0, 1, 2)

        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("background-color: lightgreen;")
        self.close_button.clicked.connect(self.close)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        self.vbox.addWidget(self.close_button)
        self.setLayout(self.vbox)

        # Not refreshed here, unlike galaxy_functions.LoadProjectWindow's "best-effort
        # initial population": there's no sensible default path to list yet, so it
        # would just be a wasted GitHub API call. User fills in the fields, then
        # clicks Refresh.

    def show_info_message(self, message):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    def _split_path_name(self):
        """self.path_name is 'owner/repo' or 'owner/repo/sub/dir'. Returns
        (owner, repo, subpath), with subpath == "" when none was given, or
        (None, None, None) if it doesn't even have an owner/repo."""
        parts = [p for p in self.path_name.strip("/").split("/") if p]
        if len(parts) < 2:
            return None, None, None
        return parts[0], parts[1], "/".join(parts[2:])

    def refresh_zip_list_cb(self):
        self.zip_list.clear()
        self.zip_names = []

        self.path_name = self.path_name_w.text().strip()
        self.branch_name = self.branch_name_w.text().strip() or "main"
        owner, repo, subpath = self._split_path_name()
        if not owner or not repo:
            return

        try:
            github_pat_str = None
            if self.xml_creator is not None:
                github_pat_str = self.xml_creator.project_io.github_pat
            g = Github(github_pat_str) if github_pat_str else Github()
            repo_obj = g.get_repo(f"{owner}/{repo}")
            contents = repo_obj.get_contents(subpath, ref=self.branch_name)
            if not isinstance(contents, list):
                contents = [contents]
            self.zip_names = sorted(c.name for c in contents if c.name.lower().endswith(".zip"))
        except Exception:
            return    # leave the list empty; user can hit Refresh again once path/branch are valid

        for name in self.zip_names:
            self.zip_list.addItem(name)

    def import_project_cb(self, sval=None):
        row = self.zip_list.currentRow()
        if row < 0 or row >= len(self.zip_names):
            QMessageBox.warning(self, "No file selected", "Select a .zip file from the list first.")
            return
        project_name = self.zip_names[row]

        owner, repo, subpath = self._split_path_name()
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{self.branch_name}"
        if subpath:
            url += f"/{subpath}"
        url += f"/{project_name}"

        msgBox = QMessageBox()
        msgBox.setText(f"This will attempt to retrieve {url}")
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        if msgBox.exec() == QMessageBox.Cancel:
            return

        try:
            print(f"--- attempting to retrieve {url}")
            urllib.request.urlretrieve(url, project_name)

            # If the downloaded file is base64-encoded, decode it to recover the real zip.
            if not zipfile.is_zipfile(project_name):
                with open(project_name, "rb") as f:
                    raw = f.read()
                try:
                    decoded = base64.b64decode(raw)
                    with open(project_name, "wb") as f:
                        f.write(decoded)
                    if not zipfile.is_zipfile(project_name):
                        self.show_error_message("Downloaded file is not a valid zip file.")
                        return
                except Exception:
                    self.show_error_message("Downloaded file is not a valid zip file.")
                    return

            # just extract the <project>/config  into /config
            project_name_base = project_name[:-4]
            print(f"--- project_name_base= {project_name_base}")
            print(f"--- calling extract_subdir with {project_name}, {project_name_base}/config, config")
            self.extract_subdir(project_name, f"{project_name_base}/config", "config")
        except:
            self.show_error_message(f"There was a problem retrieving {url}. Please check that it is accessible and try again.")
            return

        try:
            time.sleep(1)
            self.xml_creator.load_model("PhysiCell_settings")
        except:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Error loading config/PhysiCell_settings.xml.")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            returnValue = msgBox.exec()


    def show_error_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.setFixedWidth(500)
        msg.exec_()

    #---------------------------------
    def extract_subdir(self, zip_path, subdir, dest):
        print(f"---- extract_subdir(): zip_path={zip_path} ")
        os.makedirs(dest, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            has_dirs = any('/' in n for n in names)
            if not has_dirs:
                # Flat zip — copy every file directly into dest
                for member in names:
                    if not member.endswith('/'):
                        target = os.path.join(dest, os.path.basename(member))
                        print(f"-- extracting {member} to {target}")
                        with zf.open(member) as src, open(target, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
            else:
                # Zip contains directories — extract only the config/ subtree into dest
                prefix = subdir.rstrip('/') + '/'
                for member in names:
                    if member.startswith(prefix) and not member.endswith('/'):
                        relative = member[len(prefix):]
                        target = os.path.join(dest, relative)
                        os.makedirs(os.path.dirname(target), exist_ok=True)
                        print(f"-- extracting {member} to {target}")
                        with zf.open(member) as src, open(target, 'wb') as dst:
                            shutil.copyfileobj(src, dst)

#--------------------------------------
class ProjectIO:
    def __init__(self, studio):
        self.studio = studio
        self.zip_basename = "my_project"
        self.import_project_UI = None
        self.export_project_UI = None

    @property
    def github_pat(self):
        settings = getattr(self.studio, 'studio_settings', None)
        return settings.github_pat if settings is not None else None

    @github_pat.setter
    def github_pat(self, value):
        settings = getattr(self.studio, 'studio_settings', None)
        if settings is not None:
            settings.github_pat = value

    def export_project_github(self):
        """Zip config/, custom_modules/, and root project files to a user-chosen .zip."""
        self.studio.save_cb()

        self.export_project_github_ui()

        try:
            zip_path = self.zip_basename + ".zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for fname in ["main.cpp", "Makefile", "VERSION.txt"]:
                    fpath = os.path.join(self.studio.current_dir, fname)
                    if os.path.isfile(fpath):
                        zf.write(fpath, fname)

                for subdir in ["config", "custom_modules"]:
                    for fpath in glob.glob(os.path.join(self.studio.current_dir, subdir, "*")):
                        if os.path.isfile(fpath):
                            zf.write(fpath, os.path.join(subdir, os.path.basename(fpath)))

            print(f"project_io.py - export_project_github(): exported project to {zip_path}")

        except Exception as e:
            self._show_error(f"Export failed: {e}")


    def import_project_github(self):
        """Import a project (.zip) into the current project directory and reload."""
        # zip_path, _ = QFileDialog.getOpenFileName(
        #     self.studio, "Import project", "", "Zip files (*.zip)"
        # )
        # if not zip_path:
        #     return

        self.import_project_github_ui()

        # zip_file = "my_model.zip"
        # msgBox = QMessageBox()
        # # from_filename = "/import/"

        # try:
        #     with zipfile.ZipFile(zip_file, "r") as zf:
        #         for member in zf.namelist():
        #             dest = Path(self.studio.current_dir) / member
        #             dest.parent.mkdir(parents=True, exist_ok=True)
        #             if not member.endswith("/"):
        #                 dest.write_bytes(zf.read(member))

        #     print(f"project_io: imported project from {zip_file}")

        #     try:
        #         self.studio.load_model("PhysiCell_settings")
        #     except Exception as e:
        #         self._show_error(
        #             f"Project files extracted but could not reload config: {e}\n"
        #             "Use File > Open to load your .xml manually."
        #         )

        # except Exception as e:
        #     self._show_error(f"Import failed: {e}")


    def _show_error(self, msg):
        box = QMessageBox(self.studio)
        box.setIcon(QMessageBox.Warning)
        box.setText(msg)
        box.exec()


    def export_project_github_ui(self):
        if self.export_project_UI is None:
            self.export_project_UI = ExportProjectWindow()
            self.export_project_UI.xml_creator = self.studio

        # hack to bring to foreground
        self.export_project_UI.hide()
        self.export_project_UI.show()
        self.export_project_UI.raise_()

    def import_project_github_ui(self):
        if self.import_project_UI is None:
            self.import_project_UI = ImportProjectWindow()
            self.import_project_UI.xml_creator = self.studio
        self.import_project_UI.hide()
        self.import_project_UI.show()
        self.import_project_UI.raise_()
