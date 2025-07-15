"""
run_tab.py - Run tab: execute a simulation and see terminal text output

Authors:
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
Rf. Credits.md

"""

import sys
import os
import time
import logging
import shutil
from pathlib import Path
from pretty_print_xml import pretty_print
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea, QPushButton,QPlainTextEdit
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QProcess
from cell_def_tab import CellDefException
from studio_classes import StudioTab

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class RunModel(StudioTab):
    def __init__(self, xml_creator):
        super().__init__(xml_creator)

        # self.nanohub_flag = self.xml_creator.nanohub_flag
        # self.tab_widget = self.xml_creator.tab_widget
        # self.celldef_tab = self.xml_creator.celldef_tab
        self.rules_flag = self.xml_creator.rules_flag
        self.download_menu = self.xml_creator.download_menu

        #-------------------------------------------
        # used with nanoHUB app
        # self.nanohub = True
        # following set in pmb.py
        self.current_dir = ''   
        self.config_file = None

        # these get set in pmb.py
        # self.config_tab = None
        self.microenv_tab = None
        # self.celldef_tab = None
        self.user_params_tab = None
        self.rules_tab = None
        # self.vis_tab = None
        # self.legend_tab = None

        # self.tree = None

        self.output_dir = 'output'

        #-----
        self.sim_output = QWidget()

        self.main_layout = QVBoxLayout()

        self.scroll = QScrollArea()

        self.p = None
        # self.xmin = 0.0
        # self.xmax = 1.0
        # self.ymin = 0.0
        # self.ymax = 1.0

        self.control_w = QWidget()

        self.vbox = QVBoxLayout()

        #------------------
        hbox = QHBoxLayout()

        self.run_button = QPushButton("Run Simulation")
        self.run_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        hbox.addWidget(self.run_button)
        self.run_button.clicked.connect(self.run_model_cb)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("QPushButton {background-color: tomato; color: black;}")
        # self.cancel_button.setStyleSheet("background-color: rgb(250,50,50)")
        hbox.addWidget(self.cancel_button)
        self.cancel_button.clicked.connect(self.cancel_model_cb)

        # self.cancel_button = QPushButton("Cancel")
        # hbox.addWidget(self.cancel_button)
        # self.new_button.clicked.connect(self.append_more_cb)

        hbox.addWidget(QLabel("Exec:"))
        self.exec_name = QLineEdit()
        if self.xml_creator.nanohub_flag:
            self.exec_name.setText('myproj')
            # self.exec_name.setEnabled(False)
        else:
            # self.exec_name.setText('../myproj')
            self.exec_name.setText('template')
        hbox.addWidget(self.exec_name)

        hbox.addWidget(QLabel("Config:"))
        self.config_xml_name = QLineEdit()
        # self.config_xml_name.setText('mymodel.xml')
        # self.config_xml_name.setText('copy_PhysiCell_settings.xml')
        self.config_xml_name.setText('config.xml')
        hbox.addWidget(self.config_xml_name)

        # self.vbox.addStretch()

        self.vbox.addLayout(hbox)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.resize(400,900)  # nope

        self.vbox.addWidget(self.text)

        #==================================================================
        self.control_w.setLayout(self.vbox)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        self.scroll.setWidget(self.control_w) 
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.scroll)

        
    def message(self, s):
        self.text.appendPlainText(s)

    def run_model_cb(self):
        logging.debug(f'===========  run_model_cb():  ============')

        exec_file = self.exec_name.text()
        # print("run_model_cb(): exec_file=",exec_file)
        # if not os.path.is_file(Path(exec_file)):
        if not Path(exec_file).is_file():
            self.show_error_message(f"Exec file {exec_file} does not exist.")
            return

        self.xml_creator.celldef_tab.check_valid_cell_defs()

        if self.xml_creator.config_tab.save_svg.isChecked() and self.xml_creator.config_tab.save_full.isChecked():
            if float(self.xml_creator.config_tab.svg_interval.text()) != float(self.xml_creator.config_tab.full_interval.text()):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Warning")
                msg.setInformativeText('The output intervals for SVG and full (in Config Basics) do not match.')
                msg.setWindowTitle("Warning")
                msg.exec_()

        self.run_button.setEnabled(False)

        try:
            # if self.nanohub_flag: # copy normal workflow of an app, strange as it is
            if True: # copy normal workflow of an app, strange as it is
                # make sure we are where we started (app's root dir)
                # logging.debug(f'\n------>>>> doing os.chdir to {self.current_dir}')
                os.chdir(self.xml_creator.current_dir)
                # remove any previous data
                # NOTE: this dir name needs to match the <folder>  in /data/<config_file.xml>
                if self.xml_creator.nanohub_flag:
                    os.system('rm -rf tmpdir*')
                    time.sleep(1)
                    if os.path.isdir('tmpdir'):
                        # something on NFS causing issues...
                        tname = tempfile.mkdtemp(suffix='.bak', prefix='tmpdir_', dir='.')
                        shutil.move('tmpdir', tname)
                    os.makedirs('tmpdir')

                    # write the default config file to tmpdir
                    # new_config_file = "tmpdir/config.xml"  # use Path; work on Windows?
                    tdir = os.path.abspath('tmpdir')
                    new_config_file = Path(tdir,"config.xml")
                    self.output_dir = '.'
                else:
                    self.output_dir = self.xml_creator.config_tab.folder.text()
                    os.system('rm -rf ' + self.output_dir)
                    logging.debug(f'run_tab.py:  doing: mkdir {self.output_dir}')
                    try:
                        os.makedirs(self.output_dir)  # do 'mkdir output_dir'
                    except:
                        pass
                    time.sleep(1)
                    tdir = os.path.abspath(self.output_dir)

                if not self.xml_creator.update_xml_from_gui():   # if there was a problem, e.g., missing params
                    # self.run_button.setEnabled(True)
                    self.enable_run(True)
                    return

                # logging.debug(f'run_tab.py: ----> writing modified model to {self.config_file}')
                # print("run_tab.py: ----> new_config_file = ",new_config_file)
                # print("run_tab.py: ----> self.config_file = ",self.config_file)
                self.xml_creator.tree.write(self.config_file)
                # print("run_tab.py: ----> here 5")
                pretty_print(self.config_file, self.config_file)

                default_config_file = os.path.join(self.output_dir,"PhysiCell_settings.xml")
                abs_default_config_file = os.path.abspath(default_config_file )
                print(f"run_tab.py:  also copy to {abs_default_config_file }")
                shutil.copy(self.config_file, default_config_file)

                # nanoHUB: Operate from tmpdir. XML: <folder>,</folder>; temporary output goes here.  May be copied to cache later.
                if self.xml_creator.nanohub_flag:
                    tdir = os.path.abspath('tmpdir')
                    os.chdir(tdir)   # run exec from here on nanoHUB
                # sub.update(tdir)
                # subprocess.Popen(["../bin/myproj", "config.xml"])


            auto_load_params = True
            # if auto_load_params:

            if self.vis_tab:
                self.xml_creator.vis_tab.reset_domain_box()
                # self.xml_creator.vis_tab.reset_axes()
                self.xml_creator.vis_tab.reset_model_flag = True
                self.xml_creator.vis_tab.reset_plot_range()
                self.xml_creator.vis_tab.init_plot_range(self.xml_creator.config_tab) # heaven help the person who needs to understand this
                self.xml_creator.vis_tab.output_folder.setText(self.output_dir) 

                self.xml_creator.vis_tab.output_dir = self.output_dir
                # self.legend_tab.output_dir = self.output_dir
                self.xml_creator.vis_tab.reset_model()
                self.xml_creator.vis_tab.update_plots()

                # Problem with this is that it only looks at the currently selected cell type
                # Also, build_physiboss_info will look into all cell types, and if they are no boolean network, will hide everything
                print("\n--- run_tab:  calling vis_tab.build_physiboss_info()")
                self.xml_creator.vis_tab.build_physiboss_info()              

            if self.p is None:  # No process running.
                self.enable_run(False)
                # self.tab_widget.setTabEnabled(6, True)   # enable (allow to be selected) the Plot tab
                # self.tab_widget.setTabEnabled(7, True)   # enable Legend tab
                self.message("Executing process")
                self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
                self.p.errorOccurred.connect(self.error_cb)
                self.p.readyReadStandardOutput.connect(self.handle_stdout)
                self.p.readyReadStandardError.connect(self.handle_stderr)
                self.p.stateChanged.connect(self.handle_state)
                self.p.finished.connect(self.process_finished)  # Clean up once complete.
                # self.p.start("mymodel", ['biobots.xml'])
                exec_str = self.exec_name.text()
                xml_str = self.config_xml_name.text()
                print("\n--- run_tab:  xml_str before run is ",xml_str)
                print("--- run_tab:  exec_str before run is ",exec_str)
                if self.xml_creator.nanohub_flag:
                    self.p.start("submit",["--local",exec_str,xml_str])
                else:
                    # logging.debug(f'\nrun_tab.py: running: {exec_str}, {xml_str}')
                    self.p.start(exec_str, [xml_str])

                    # print("\n\nrun_tab.py: running: ",exec_str," output/config.xml")
                    # self.p.start(exec_str, ["output/config.xml"])
                # self.p = None  # No, don't do this

                # self.legend_tab.reload_legend()  # new, not sure about timing - creation vs. display

            else:
                # logging.debug(f'self.p is not None???')
                print(f'self.p is not None???')
                
        except CellDefException as e:
            self.show_error_message(str(e) + " : run_cb(): Error: Please finish the definition before running.")
            self.run_button.setEnabled(True)

    def error_cb(self, error):
        print("\n\nERROR : QProcess failed !")
        errorMessage = {
            QProcess.FailedToStart: "The process failed to start",
            QProcess.Crashed: "The process crashed some time after starting successfully.",
            QProcess.Timedout: "The last waitFor…() function timed out. The state of QProcess is unchanged, and you can try calling waitFor…() again.",
            QProcess.WriteError: "An error occurred when attempting to write to the process. For example, the process may not be running, or it may have closed its input channel.",
            QProcess.ReadError: "An error occurred when attempting to read from the process. For example, the process may not be running.",
            QProcess.UnknownError: "An unknown error occurred. This is the default return value of error()"
        }
        print(errorMessage[error])
        print("Detailed logs : ", self.p.errorString())
        print("\n\n")
        
    def cancel_model_cb(self):
        # logging.debug(f'===========  cancel_model_cb():  ============')
        if self.p:  # process running.
            if self.xml_creator.nanohub_flag:
                self.p.terminate()
            else:
                self.p.kill()   # I *think* this worked better for Windows (but still worked for other OSes, on the desktop)
            # self.run_button.setEnabled(True)
            self.enable_run(True)

    def handle_stderr(self):
        data = self.p.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        self.message(stderr)

    def handle_stdout(self):
        data = self.p.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.message(stdout)

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: 'Not running',
            QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]
        self.message(f"State changed: {state_name}")
        # self.message(f"Starting in a few secs...")   # only for "Starting"

    def process_finished(self):
        self.message("Process finished.")
        self.enable_run(True)
        # print("-- process finished.")
        self.xml_creator.vis_tab.first_plot_cb("foo")
        if self.xml_creator.nanohub_flag:
            self.download_menu.setEnabled(True)
        self.p = None
        self.run_button.setEnabled(True)
        
    def show_error_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.setFixedWidth(500)
        msg.exec_()

    def enable_run(self, flag):
        self.run_button.setEnabled(flag)
        if flag:
            self.run_button.setText("Run simulation")
            self.run_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        else:
            self.run_button.setText("...")
            self.run_button.setStyleSheet("QPushButton {background-color: yellow; color: black;}")