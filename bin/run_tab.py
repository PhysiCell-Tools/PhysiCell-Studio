"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Michael Siler, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)

"""

import sys
import os
import time
from pathlib import Path
from PyQt5 import QtCore, QtGui
# from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea, QPushButton,QPlainTextEdit
from PyQt5.QtWidgets import QMessageBox

from PyQt5.QtCore import QProcess

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class RunModel(QWidget):
    def __init__(self, nanohub_flag, tab_widget, download_menu):
        super().__init__()

        self.nanohub_flag = nanohub_flag
        self.tab_widget = tab_widget
        self.download_menu = download_menu

        #-------------------------------------------
        # used with nanoHUB app
        # self.nanohub = True
        # following set in pmb.py
        self.current_dir = ''   
        self.config_file = None
        self.tree = None

        # these get set in pmb.py
        self.config_tab = None
        self.microenv_tab = None
        self.celldef_tab = None
        self.user_params_tab = None
        self.vis_tab = None
        self.legend_tab = None

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
        self.run_button.setStyleSheet("background-color: lightgreen")
        hbox.addWidget(self.run_button)
        self.run_button.clicked.connect(self.run_model_cb)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("background-color: red")
        # self.cancel_button.setStyleSheet("background-color: rgb(250,50,50)")
        hbox.addWidget(self.cancel_button)
        self.cancel_button.clicked.connect(self.cancel_model_cb)

        # self.cancel_button = QPushButton("Cancel")
        # hbox.addWidget(self.cancel_button)
        # self.new_button.clicked.connect(self.append_more_cb)

        hbox.addWidget(QLabel("Exec:"))
        self.exec_name = QLineEdit()
        if self.nanohub_flag:
            self.exec_name.setText('myproj')
            self.exec_name.setEnabled(False)
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

#------------------------------
    def update_xml_from_gui(self):
        self.xml_root = self.tree.getroot()
        print("\n\n =================================== run_tab.py: update_xml_from_gui(): self.xml_root = ",self.xml_root)
        self.config_tab.xml_root = self.xml_root
        self.microenv_tab.xml_root = self.xml_root
        self.celldef_tab.xml_root = self.xml_root
        self.user_params_tab.xml_root = self.xml_root
        # sys.exit(1)

        self.config_tab.fill_xml()
        self.microenv_tab.fill_xml()
        self.celldef_tab.fill_xml()
        self.user_params_tab.fill_xml()

        # self.vis_tab.circle_radius = ET.parse(self.xml_root)
        # tree = ET.parse(xml_file)
        # root = tree.getroot()
        # rwh - warning: assumes "R_circle" name won't change
        # self.vis_tab.mech_voxel_size = float(self.xml_root.find(".//user_parameters//mechanics_voxel_size").text)
        # print("\n\n------------- run_tab(): self.vis_tab.mech_voxel_size = ",self.vis_tab.mech_voxel_size)
        
    def message(self, s):
        self.text.appendPlainText(s)

    def run_model_cb(self):
        print("===========  run_model_cb():  ============")

        if float(self.config_tab.svg_interval.text()) != float(self.config_tab.full_interval.text()):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Warning")
            msg.setInformativeText('The output intervals for SVG and full (in Config Basics) do not match.')
            msg.setWindowTitle("Warning")
            msg.exec_()

        self.run_button.setEnabled(False)

        # if self.nanohub_flag: # copy normal workflow of an app, strange as it is
        if True: # copy normal workflow of an app, strange as it is

            # make sure we are where we started (app's root dir)
            print("\n\n------>>>> doing os.chdir to ", self.current_dir)
            os.chdir(self.current_dir)

            # remove any previous data
            # NOTE: this dir name needs to match the <folder>  in /data/<config_file.xml>
            if self.nanohub_flag:
                os.system('rm -rf tmpdir*')
            # else:
                # os.system('rm -rf output*')
            time.sleep(1)
            if self.nanohub_flag and s.path.isdir('tmpdir'):
                # something on NFS causing issues...
                tname = tempfile.mkdtemp(suffix='.bak', prefix='tmpdir_', dir='.')
                shutil.move('tmpdir', tname)
            if self.nanohub_flag:
                os.makedirs('tmpdir')
            else:
                # os.makedirs('output')
                self.output_dir = self.config_tab.folder.text()
                # os.system('rm -rf tmpdir*')
                os.system('rm -rf ' + self.output_dir)
                print("run_tab.py:  doing: mkdir ",self.output_dir)
                os.makedirs(self.output_dir)  # do 'mkdir output_dir'
                time.sleep(1)

            # write the default config file to tmpdir
            # new_config_file = "tmpdir/config.xml"  # use Path; work on Windows?
            if self.nanohub_flag:
                tdir = os.path.abspath('tmpdir')
            else:
                # tdir = os.path.abspath('.')
                tdir = os.path.abspath(self.output_dir)

            new_config_file = Path(tdir,"config.xml")
            self.celldef_tab.config_path = new_config_file
            self.update_xml_from_gui()

            # write_config_file(new_config_file)  
            # update the .xml config file
            # self.config_tab.fill_xml()
            # self.microenv_tab.fill_xml()
            # self.celldef_tab.fill_xml()
            # self.user_params_tab.fill_xml()
            # print("\n\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("run_tab.py: ----> writing modified model to ",self.config_file)
            # print("run_tab.py: ----> writing modified model to ",new_config_file)
            self.tree.write(self.config_file)
            # self.tree.write(new_config_file)  # saves modified XML to <output_dir>/config.xml 
            # sys.exit(1)

            # Operate from tmpdir. XML: <folder>,</folder>; temporary output goes here.  May be copied to cache later.
            if self.nanohub_flag:
                tdir = os.path.abspath('tmpdir')
                os.chdir(tdir)   # run exec from here on nanoHUB
            # sub.update(tdir)
            # subprocess.Popen(["../bin/myproj", "config.xml"])


        auto_load_params = True
        # if auto_load_params:

        if self.vis_tab:
            # self.vis_tab.reset_axes()
            self.vis_tab.reset_model_flag = True
            self.vis_tab.reset_plot_range()
            self.vis_tab.init_plot_range(self.config_tab) # heaven help the person who needs to understand this

        # for f in Path('./output').glob('*.*'):
        #     try:
        #         f.unlink()
        #     except OSError as e:
        #         print("Error: %s : %s" % (f, e.strerror))
        # print("  rm -rf tmpdir/*")
        # os.system('rm -rf tmpdir/*')

        # if os.path.isdir('tmpdir'):
        #     # something on NFS causing issues...
        #     tname = tempfile.mkdtemp(suffix='.bak', prefix='output_', dir='.')
        #     shutil.move('output', tname)
        # os.makedirs('output')

        # update axes ranges on Plots


        if self.p is None:  # No process running.
            # self.vis_tab.setEnabled(True)
            # self.pStudio.enablePlotTab(True)
            # self.pStudio.enableLegendTab(True)
            self.tab_widget.setTabEnabled(6, True)   # enable (allow to be selected) the Plot tab
            self.tab_widget.setTabEnabled(7, True)   # enable Legend tab
            self.message("Executing process")
            self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
            self.p.readyReadStandardOutput.connect(self.handle_stdout)
            self.p.readyReadStandardError.connect(self.handle_stderr)
            self.p.stateChanged.connect(self.handle_state)
            self.p.finished.connect(self.process_finished)  # Clean up once complete.
            # self.p.start("mymodel", ['biobots.xml'])
            exec_str = self.exec_name.text()
            xml_str = self.config_xml_name.text()
            if self.nanohub_flag:
                self.p.start("submit",["--local",exec_str,xml_str])
            else:
                print("\n\nrun_tab.py: running: ",exec_str,xml_str)
                self.p.start(exec_str, [xml_str])

                # print("\n\nrun_tab.py: running: ",exec_str," output/config.xml")
                # self.p.start(exec_str, ["output/config.xml"])
            # self.p = None  # No, don't do this

            self.legend_tab.reload_legend()  # new, not sure about timing - creation vs. display
        else:
            print("self.p is not None???")

    def cancel_model_cb(self):
        print("===========  cancel_model_cb():  ============")
        if self.p:  # process running.
            self.p.kill()
            # self.p.terminate()
            self.run_button.setEnabled(True)

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
        print("-- process finished.")
        self.vis_tab.first_plot_cb("foo")
        if self.nanohub_flag:
            self.download_menu.setEnabled(True)
        self.p = None
        self.run_button.setEnabled(True)