# from PyQt5 import QtCore
# from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QGridLayout, QPushButton
import traceback
from studio_classes import QCheckBox_custom
from PyQt5 import QtCore  #, QtGui
from PyQt5.QtWidgets import (
    QFrame, QWidget, QScrollArea, QVBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QMessageBox,
)
from PyQt5.QtGui import QIntValidator
# from vis_tab import MainPlotWindow   # later maybe
try:
    import galaxy_ie_helpers as gh
except:
    print("----- cannot import from galaxy_ie_helpers ")
    pass
try:
    import keyring
except:
    print("----- cannot import keyring (for GitHub PAT)")
    pass

#APP_NAME = "my_github_desktop_app"
APP_NAME = "physicell_studio"
TOKEN_KEY = "github_token"

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class StudioSettings(QWidget):
    def __init__(self, gui_w, min_size_flag, vis_tab, galaxy_flag):   # use dict eventually
        super().__init__()

        self.gui_w = gui_w
        self.min_size = min_size_flag
        self.fixed_plot_flag = True
        self.vis_tab = vis_tab
        self.galaxy_flag = galaxy_flag

        self.file_id = None
        self.github_pat = None

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
        self.min_size_checkbox = QCheckBox_custom('Studio min size (1100x790)')
        self.min_size_checkbox.setChecked(self.min_size)
        self.min_size_checkbox.clicked.connect(self.toggle_min_size_cb)
        # idx_row += 1
        glayout.addWidget(self.min_size_checkbox, idx_row,0,1,3) # w, row, column, rowspan, colspan

        #  future possibility of a floating Plot window
        # self.fixed_plot_checkbox = QCheckBox_custom('Fixed Plot window')
        # self.fixed_plot_checkbox.setChecked(self.fixed_plot_flag)
        # self.fixed_plot_checkbox.clicked.connect(self.toggle_fixed_plot_cb)
        # idx_row += 1
        # glayout.addWidget(self.fixed_plot_checkbox, idx_row,0,1,2) # w, row, column, rowspan, colspan


        idx_row += 1
        glayout.addWidget(QHLine(), idx_row,0,1,3) # w, row, column, rowspan, colspan

        if self.galaxy_flag:
            idx_row += 1
            self.get_github_PAT_button = QPushButton("get GitHub PAT: History ID=")
            self.get_github_PAT_button.setFixedWidth(200)
            self.get_github_PAT_button.setEnabled(True)
            self.get_github_PAT_button.setStyleSheet("background-color: lightgreen;")
            self.get_github_PAT_button.clicked.connect(self.galaxy_github_pat_cb)
            glayout.addWidget(self.get_github_PAT_button, idx_row, 0, 1, 2)

            self.file_id_w = QLineEdit("0")
            self.file_id_w.setEnabled(True)
            self.file_id_w.setFixedWidth(70)
            self.file_id_w.setValidator(QIntValidator())
            self.file_id_w.textChanged.connect(self.file_id_changed)
            glayout.addWidget(self.file_id_w, idx_row, 2, 1, 1)
        else:
            idx_row += 1
            self.get_github_PAT_button = QPushButton("Enter/Save GitHub PAT")
            self.get_github_PAT_button.setFixedWidth(170)
            self.get_github_PAT_button.setEnabled(True)
            self.get_github_PAT_button.setStyleSheet("background-color: lightgreen;")
            self.get_github_PAT_button.clicked.connect(self.github_pat_changed_cb)
            glayout.addWidget(self.get_github_PAT_button, idx_row, 0, 1, 2)

            self.pat_w = QLineEdit()
            self.pat_w.setEnabled(True)
            self.pat_w.setFixedWidth(170)
            # self.pat_w.setValidator(QIntValidator())
            self.pat_w.textChanged.connect(self.github_pat_changed_cb)
            glayout.addWidget(self.pat_w, idx_row, 2, 1, 1)


            idx_row += 1
            self.release_github_PAT_button = QPushButton("Release GitHub PAT")
            self.release_github_PAT_button.setFixedWidth(170)
            self.release_github_PAT_button.setEnabled(True)
            self.release_github_PAT_button.setStyleSheet("background-color: lightgreen;")
            self.release_github_PAT_button.clicked.connect(self.release_github_pat_cb)
            glayout.addWidget(self.release_github_PAT_button, idx_row, 0, 1, 2)

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
            self.gui_w.setMinimumSize(1100, 790)  #width, height of window (avoid hard-coding in future)
        else:
            self.gui_w.setMinimumSize(0, 0)  

    def toggle_fixed_plot_cb(self):
        self.fixed_plot_flag = not self.fixed_plot_flag
        if self.fixed_plot_flag:
            # self.plot_win = MainPlotWindow(self.canvas)
            # self.vis_tab.plot_win.show()
            # self.cells_physiboss_rb.disconnect()
            # self.cells_physiboss_rb.deleteLater()

            # self.scroll_plot.disconnect()
            # self.scroll_plot.deleteLater()
            self.scroll_plot.setWidget(self.canvas) # for an embedded Plot window (not floating)
        else:
            # self.vis_tab.scroll_plot.setWidget(self.vis_tab.canvas) # self.config_params = QWidget()
            if self.vis_tab.plot_win is None:
                self.vis_tab.plot_win = MainPlotWindow(self.vis_tab.canvas)
                self.vis_tab.plot_win.show()
            # self.vis_tab.plot_win.show()


    def github_pat_changed_cb(self):
        token = self.pat_w.text().strip()
        print("token=",token)
        if not token:
            QMessageBox.warning(self, "Error", "Token cannot be empty.")
            return

        try:
            keyring.set_password(APP_NAME, TOKEN_KEY, token)
            QMessageBox.information(self, "Success", "Token securely saved on your computer.")
            self.on_success_callback(token)
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save token: {str(e)}")


    def release_github_pat_cb(self):
        print("release_github_pat_cb")
        reply = QMessageBox.question(self, 'Confirm release', 
                                     "This will remove your token from this device.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                # Remove the token completely from the OS vault
                keyring.delete_password(APP_NAME, TOKEN_KEY)
                QMessageBox.information(self, "Your token has been deleted.")
                
                # Close dashboard and trigger app reset
                self.close()
                self.on_disconnect_callback()
            except keyring.errors.PasswordDeleteError:
                QMessageBox.warning(self, "Error", "No token found to delete, resetting application.")
                self.close()
                self.on_disconnect_callback()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to safely delete token: {str(e)}")

    def galaxy_github_pat_cb(self):
        self.file_id = int(self.file_id_w.text())
        # zip_file = "my_model.zip"
        msgBox = QMessageBox()
        from_filename = "/import/"

        try:
            msgBox.setText('Copying the requested data from the Galaxy History')
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()

            # path = gh.get(self.file_id)  # Galaxy I/O function
            gh.get(self.file_id)  # Galaxy I/O function
            # if path and os.path.exists(path):
                # pass
            # else:
                # self.show_error_message("Error retrieving data from History. Confirm the ID exists.")
                # return

            from_filename += str(self.file_id)
            try:
                print("reading PAT...")
                with open(from_filename, "r", encoding="utf-8") as file:
                    self.github_pat = file.read()
                print(self.github_pat)

                # print(f"load_project_cb(): attempting to copy {from_filename} to {zip_file}")
                # shutil.copy(from_filename, zip_file)
                # os.remove(from_filename)
            except:
                msg = f"Error: unable to read your GitHub personal access token."
                print(msg)
                msgBox.setText(msg)
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec()
                return
            # time.sleep(1)
        except FileNotFoundError:
            msg = f"Error: The file {from_filename} was not found."
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

    def on_success_callback(self, token):
        self.github_pat = token
        masked = f"{token[:8]}..." if len(token) > 8 else "***"
        self.get_github_PAT_button.setText("GitHub PAT saved")
        self.get_github_PAT_button.setEnabled(False)
        self.pat_w.setEnabled(False)
        self.release_github_PAT_button.setEnabled(True)
        QMessageBox.information(self, "Authenticated", f"Token saved: {masked}")

    def on_disconnect_callback(self):
        self.github_pat = None
        self.get_github_PAT_button.setText("Enter/Save GitHub PAT")
        self.get_github_PAT_button.setEnabled(True)
        self.pat_w.clear()
        self.pat_w.setEnabled(True)
        self.release_github_PAT_button.setEnabled(False)

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
