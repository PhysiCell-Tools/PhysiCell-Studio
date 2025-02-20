"""
Authors:
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
Rf. Credits.md
"""

import sys
import logging
import os
from math import floor, log10
from pathlib import Path
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from PyQt5 import QtCore, QtGui
# from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QLineEdit,QHBoxLayout,QVBoxLayout,QRadioButton,QPushButton, QLabel,QComboBox,QScrollArea,QGridLayout, QFileDialog,QSpinBox,QDoubleSpinBox, QButtonGroup    # , QMessageBox
# from PyQt5.QtWidgets import QMessageBox

from studio_classes import QLabelSeparator, QLineEdit_custom, QCheckBox_custom, QRadioButton_custom, HoverWarning, StudioTab
from studio_functions import style_sheet_template

class RandomSeedIntValidator(QtGui.QValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate(self, text, pos):
        # see if text is an integer
        if text == "" or text.isdigit():
            return QtGui.QValidator.Acceptable, text, pos
        else:
            return QtGui.QValidator.Invalid, text, pos

class RandomSeedIntValidator(QtGui.QValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate(self, text, pos):
        # see if text is an integer
        if text == "" or text.isdigit():
            return QtGui.QValidator.Acceptable, text, pos
        else:
            return QtGui.QValidator.Invalid, text, pos

class Config(StudioTab):
    # def __init__(self, nanohub_flag):
    def __init__(self, xml_creator):
        super().__init__(xml_creator)
        # global self.config_params

        self.default_time_units = "min"

        # self.nanohub_flag = nanohub_flag
        self.nanohub_flag = False

        self.vis_tab = None
        self.ics_tab = None

        self.xml_root = None

        self.sync_output = True

        self.substrate_list = []

        self.update_max_time_flag = True # flag to stop recursive QSpinBox updates
        
        # self.tab = QWidget()
        # self.tabs.resize(200,5)

        #-------------------------------------------
        label_width = 110
        domain_value_width = 100
        value_width = 60
        label_height = 20
        units_width = 170

        self.scroll = QScrollArea()  # might contain centralWidget

        self.config_params = QWidget()

        self.config_tab_layout = QGridLayout()
        # self.config_tab_layout.addWidget(self.tab_widget, 0,0,1,1) # w, row, column, rowspan, colspan

        #============  Domain ================================
        label = QLabelSeparator("Domain (micron)")
        label.setFixedHeight(label_height)
        idx_row = 0
        self.config_tab_layout.addWidget(label, idx_row,0,1,20) # w, row, column, rowspan, colspan

        domain_enabled = True

        label = QLabel("Xmin")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.xmin = QLineEdit()
        self.xmin.setEnabled(domain_enabled)
        self.xmin.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.xmin, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel("Xmax")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        self.xmax = QLineEdit()
        self.xmax.setEnabled(domain_enabled)
        self.xmax.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.xmax, idx_row,3,1,1) # w, row, column, rowspan, colspan

        label = QLabel("dx")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.config_tab_layout.addWidget(label, idx_row,4,1,1) # w, row, column, rowspan, colspan

        self.xdel = QLineEdit()
        self.xdel.setEnabled(domain_enabled)
        self.xdel.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.xdel, idx_row,5,1,1) # w, row, column, rowspan, colspan

        #----------
        label = QLabel("Ymin")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.ymin = QLineEdit()
        self.ymin.setEnabled(domain_enabled)
        self.ymin.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.ymin, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel("Ymax")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        self.ymax = QLineEdit()
        self.ymax.setEnabled(domain_enabled)
        self.ymax.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.ymax, idx_row,3,1,1) # w, row, column, rowspan, colspan

        label = QLabel("dy")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.config_tab_layout.addWidget(label, idx_row,4,1,1) # w, row, column, rowspan, colspan

        self.ydel = QLineEdit()
        self.ydel.setEnabled(domain_enabled)
        self.ydel.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.ydel, idx_row,5,1,1) # w, row, column, rowspan, colspan

        #----------
        label = QLabel("Zmin")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.zmin = QLineEdit()
        self.zmin.setEnabled(domain_enabled)
        self.zmin.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.zmin, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel("Zmax")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        self.zmax = QLineEdit()
        self.zmax.setEnabled(domain_enabled)
        self.zmax.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.zmax, idx_row,3,1,1) # w, row, column, rowspan, colspan

        label = QLabel("dz")
        label.setAlignment(QtCore.Qt.AlignRight)
        self.config_tab_layout.addWidget(label, idx_row,4,1,1) # w, row, column, rowspan, colspan

        self.zdel = QLineEdit()
        self.zdel.setEnabled(domain_enabled)
        self.zdel.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.zdel, idx_row,5,1,1) # w, row, column, rowspan, colspan

        #============  Misc ================================
        label = QLabelSeparator("Times")
        label.setFixedHeight(label_height)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,20) # w, row, column, rowspan, colspan

        label = QLabel("Max Time")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.max_time = QLineEdit()
        self.max_time.setValidator(QtGui.QDoubleValidator(bottom=0))
        self.max_time.textChanged.connect(self.max_time_changed_cb)
        self.config_tab_layout.addWidget(self.max_time, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel(self.default_time_units)
        label.setAlignment(QtCore.Qt.AlignLeft)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        self.day_spin_box = QSpinBox()

        self.day_spin_box.setMinimum(0)
        self.day_spin_box.setMaximum(int(1e6))

        self.day_spin_box.setSuffix(" d")
        self.day_spin_box.setSingleStep(1)  # Or e.g. 0.5 for QDoubleSpinBox
        self.day_spin_box.textChanged.connect(self.day_value_changed_str)

        self.config_tab_layout.addWidget(self.day_spin_box,idx_row,3,1,1)

        self.hour_spin_box = QSpinBox()

        self.hour_spin_box.setMinimum(-1) # allow it to roll over to a new day
        self.hour_spin_box.setMaximum(24) # allow it to roll over to a new day

        self.hour_spin_box.setSuffix(" h")
        self.hour_spin_box.setSingleStep(1)  # Or e.g. 0.5 for QDoubleSpinBox
        self.hour_spin_box.textChanged.connect(self.hour_value_changed_str)

        self.config_tab_layout.addWidget(self.hour_spin_box,idx_row,4,1,1)

        self.minute_spin_box = QSpinBox()

        self.minute_spin_box.setMinimum(-1)
        self.minute_spin_box.setMaximum(60)

        self.minute_spin_box.setSuffix(" min")
        self.minute_spin_box.setSingleStep(1)  # Or e.g. 0.5 for QDoubleSpinBox
        self.minute_spin_box.textChanged.connect(self.minute_value_changed_str)

        self.config_tab_layout.addWidget(self.minute_spin_box,idx_row,5,1,1)

        self.minute_fraction_spin_box = QDoubleSpinBox()

        self.minute_fraction_spin_box.setMinimum(-1)
        self.minute_fraction_spin_box.setMaximum(1)

        self.minute_fraction_spin_box.setDecimals(2) # set to 2 by default, but listen to diffusion_dt

        self.minute_fraction_spin_box.setSuffix(" min")
        self.minute_fraction_spin_box.setSingleStep(0.01)  # Or e.g. 0.5 for QDoubleSpinBox
        self.minute_fraction_spin_box.textChanged.connect(self.minute_fraction_value_changed_str)

        self.config_tab_layout.addWidget(self.minute_fraction_spin_box,idx_row,6,1,1)

        label = QLabel("Diffusion dt")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.diffusion_dt = QLineEdit()
        self.diffusion_dt.setValidator(QtGui.QDoubleValidator())
        self.diffusion_dt.textChanged.connect(self.diffusion_dt_changed_cb)
        self.config_tab_layout.addWidget(self.diffusion_dt, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel(self.default_time_units)
        label.setAlignment(QtCore.Qt.AlignLeft)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        label = QLabel("Mechanics dt")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.mechanics_dt = QLineEdit()
        self.mechanics_dt.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.mechanics_dt, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel(self.default_time_units)
        label.setAlignment(QtCore.Qt.AlignLeft)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        label = QLabel("Phenotype dt")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.phenotype_dt = QLineEdit()
        self.phenotype_dt.setValidator(QtGui.QDoubleValidator())
        self.config_tab_layout.addWidget(self.phenotype_dt, idx_row,1,1,1) # w, row, column, rowspan, colspan

        label = QLabel(self.default_time_units)
        label.setAlignment(QtCore.Qt.AlignLeft)
        self.config_tab_layout.addWidget(label, idx_row,2,1,1) # w, row, column, rowspan, colspan

        #============  Misc ================================
        label = QLabelSeparator("Misc runtime parameters")
        label.setFixedHeight(label_height)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,20) # w, row, column, rowspan, colspan

        #----------
        label = QLabel("# threads")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.num_threads = QLineEdit()
        self.num_threads.setValidator(QtGui.QIntValidator())
        self.config_tab_layout.addWidget(self.num_threads, idx_row,1,1,1) # w, row, column, rowspan, colspan

        #----------

        label = QLabel("output folder")
        label.setAlignment(QtCore.Qt.AlignRight)
        idx_row += 1
        self.config_tab_layout.addWidget(label, idx_row,0,1,1) # w, row, column, rowspan, colspan

        self.folder = QLineEdit()
        if self.nanohub_flag:
            self.folder.setEnabled(False)
        self.config_tab_layout.addWidget(self.folder, idx_row,1,1,1) # w, row, column, rowspan, colspan

        #---------------------------------------------------------------------------
        # Use a vbox/hbox instead of the grid for better alignment :/
        vbox = QVBoxLayout()
        vbox.addLayout(self.config_tab_layout)

        #----------
        hbox = QHBoxLayout()
        label = QLabel("Random seed:")
        label.setAlignment(QtCore.Qt.AlignRight)

        vbox_temp = QVBoxLayout()
        vbox_temp.addStretch()
        vbox_temp.addWidget(label)
        vbox_temp.addStretch()
        hbox.addLayout(vbox_temp)

        self.random_seed_gp = QButtonGroup()
        self.random_seed_gp.idToggled.connect(self.random_seed_gp_cb)
        random_seed_gp_next_id = 0

        self.random_seed_random_button = QRadioButton_custom("system clock")
        self.random_seed_gp.addButton(self.random_seed_random_button, random_seed_gp_next_id)
        hbox.addWidget(self.random_seed_random_button)
        random_seed_gp_next_id += 1

        self.random_seed_integer_button = QRadioButton_custom("integer \u2192")
        self.random_seed_gp.addButton(self.random_seed_integer_button, random_seed_gp_next_id)
        hbox.addWidget(self.random_seed_integer_button)
        random_seed_gp_next_id += 1

        label = QLabel("seed")
        # align label vertically in bottom of hbox
        label.setAlignment(QtCore.Qt.AlignBottom)
        label.setAlignment(QtCore.Qt.AlignLeft)

        vbox_temp = QVBoxLayout()
        vbox_temp.addStretch()
        vbox_temp.addWidget(label)
        vbox_temp.addStretch()
        hbox.addLayout(vbox_temp)

        self.random_seed_integer = QLineEdit_custom()
        self.random_seed_integer.setPlaceholderText("system_clock")
        self.random_seed_integer.setFixedWidth(100)
        self.random_seed_integer.setEnabled(False)
        self.random_seed_integer.textChanged.connect(self.random_seed_integer_cb)
        self.random_seed_integer.setValidator(RandomSeedIntValidator())
        hbox.addWidget(self.random_seed_integer)

        self.random_seed_warning_label = HoverWarning("WARNING: random_seed in user_parameters will take precedence if it remains.")
        hbox.addWidget(self.random_seed_warning_label)

        hbox.addStretch()

        vbox.addLayout(hbox)

        #------------------
        hbox = QHBoxLayout()

        label = QLabel("Save data (intervals):")
        label.setFixedWidth(150)
        idx_row += 1
        icol = 0
        # self.config_tab_layout.addWidget(label, idx_row,icol,1,1) # w, row, column, rowspan, colspan
        hbox.addWidget(label)

        #------
        cbox_width = 60
        self.save_svg = QCheckBox_custom("SVG")
        self.save_svg.setFixedWidth(cbox_width)
        self.save_svg.setChecked(True)
        self.save_svg.clicked.connect(self.svg_clicked)
        hbox.addWidget(self.save_svg)

        self.svg_interval = QLineEdit()
        self.svg_interval.setFixedWidth(100)
        self.svg_interval.setValidator(QtGui.QDoubleValidator())
        self.svg_interval.textChanged.connect(self.svg_interval_changed)
        self.svg_interval.setStyleSheet(style_sheet_template(QLineEdit))
        hbox.addWidget(self.svg_interval)

        label = QLabel(self.default_time_units)
        label.setFixedWidth(100)
        hbox.addWidget(label)

        #------
        self.save_full = QCheckBox_custom("Full")
        self.save_full.setFixedWidth(cbox_width)
        self.save_full.clicked.connect(self.full_clicked)
        hbox.addWidget(self.save_full)

        self.full_interval = QLineEdit()
        self.full_interval.setFixedWidth(100)
        self.full_interval.setValidator(QtGui.QDoubleValidator())
        self.full_interval.textChanged.connect(self.full_interval_changed)
        self.full_interval.setStyleSheet(style_sheet_template(QLineEdit))
        hbox.addWidget(self.full_interval)

        label = QLabel(self.default_time_units)
        hbox.addWidget(label)

        #------
        label = QLabel("      ")
        hbox.addWidget(label)

        self.sync_svg_mat = QCheckBox_custom("Sync")
        self.sync_svg_mat.setFixedWidth(cbox_width)
        self.sync_svg_mat.setChecked(self.sync_output)
        self.sync_svg_mat.clicked.connect(self.sync_clicked)
        hbox.addWidget(self.sync_svg_mat)

        #------
        hbox.addStretch()
        vbox.addLayout(hbox)

        #------

        hbox = QHBoxLayout()

        label = QLabel("Plot SVG substrate:")
        label.setFixedWidth(120)
        idx_row += 10
        icol = 0
        # self.config_tab_layout.addWidget(label, idx_row,icol,1,1) # w, row, column, rowspan, colspan
        hbox.addWidget(label)

        self.plot_substrate_svg = QCheckBox_custom("enable")
        self.plot_substrate_svg.setFixedWidth(80)
        self.plot_substrate_svg.setChecked(True)
        self.plot_substrate_svg.clicked.connect(self.plot_substrate_svg_clicked)
        hbox.addWidget(self.plot_substrate_svg) # w, row, column, rowspan, colspan

        self.svg_substrate_to_plot_dropdown = QComboBox()
        self.svg_substrate_to_plot_dropdown.setFixedWidth(200)
        self.svg_substrate_to_plot_dropdown.setStyleSheet(style_sheet_template(QComboBox))
        hbox.addWidget(self.svg_substrate_to_plot_dropdown)

        self.plot_substrate_limits = QCheckBox_custom("Limits enabled")
        self.plot_substrate_limits.setFixedWidth(130)
        self.plot_substrate_limits.setChecked(True)
        self.plot_substrate_limits.clicked.connect(self.plot_substrate_limits_clicked)
        hbox.addWidget(self.plot_substrate_limits) # w, row, column, rowspan, colspan

        label = QLabel("min")
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label) # w, row, column, rowspan, colspan

        self.svg_substrate_min = QLineEdit()
        self.svg_substrate_min.setFixedWidth(100)
        self.svg_substrate_min.setValidator(QtGui.QDoubleValidator())
        self.svg_substrate_min.textChanged.connect(self.svg_substrate_min_changed)
        self.svg_substrate_min.setStyleSheet(style_sheet_template(QLineEdit))
        hbox.addWidget(self.svg_substrate_min)

        label = QLabel("max")
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label) # w, row, column, rowspan, colspan

        self.svg_substrate_max = QLineEdit()
        self.svg_substrate_max.setFixedWidth(100)
        self.svg_substrate_max.setValidator(QtGui.QDoubleValidator())
        self.svg_substrate_max.textChanged.connect(self.svg_substrate_max_changed)
        self.svg_substrate_max.setStyleSheet(style_sheet_template(QLineEdit))
        hbox.addWidget(self.svg_substrate_max)

        label = QLabel("colormap")
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label) # w, row, column, rowspan, colspan

        self.svg_substrate_colormap_dropdown = QComboBox()
        self.svg_substrate_colormap_dropdown.setFixedWidth(100)
        self.svg_substrate_colormap_dropdown.setStyleSheet(style_sheet_template(QComboBox))
        hbox.addWidget(self.svg_substrate_colormap_dropdown)


        #------
        hbox.addStretch()
        vbox.addLayout(hbox)

        #============  Cells IC ================================
        label = QLabelSeparator("Initial conditions of cells (x,y,z, type)")
        label.setFixedHeight(label_height)
        vbox.addWidget(label)


        filename_width = 200
        hbox = QHBoxLayout()
        self.cells_csv = QCheckBox_custom("enable")
        self.cells_csv.setFixedWidth(100)
        self.cells_csv.setEnabled(True)
        self.cells_csv.clicked.connect(self.cells_csv_clicked)
        hbox.addWidget(self.cells_csv)

        label = QLabel("folder")
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)
        self.csv_folder = QLineEdit()
        self.csv_folder.setFixedWidth(filename_width)
        self.csv_folder.setStyleSheet(style_sheet_template(QLineEdit))
        if self.nanohub_flag:
            self.folder.setEnabled(False)
        hbox.addWidget(self.csv_folder)

        label = QLabel("file")
        label.setAlignment(QtCore.Qt.AlignRight)
        hbox.addWidget(label)

        self.csv_file = QLineEdit()
        self.csv_file.setFixedWidth(filename_width)
        self.csv_file.setStyleSheet(style_sheet_template(QLineEdit))
        hbox.addWidget(self.csv_file)

        self.import_seeding_button = QPushButton("Import")
        self.import_seeding_button.setFixedWidth(100)
        self.import_seeding_button.setStyleSheet("background-color: lightgreen; color: black")
        self.import_seeding_button.clicked.connect(self.import_seeding_cb)
        hbox.addWidget(self.import_seeding_button)

        hbox.addStretch()

        vbox.addLayout(hbox)

        #============  Cell behavior flags ================================
        label = QLabelSeparator("Cells' global behaviors")
        label.setFixedHeight(label_height)
        vbox.addWidget(label)
        vbox.addLayout(hbox)
        idx_row += 1
        icol = 0
        # self.config_tab_layout.addLayout(hbox, idx_row,icol,1,20) # w, row, column, rowspan, colspan


        #----------
        hbox = QHBoxLayout()

        cbox_width = 200
        self.virtual_walls = QCheckBox_custom("virtual walls (nudge cells away from domain boundaries)")
        self.virtual_walls.setFixedWidth(400)
        self.virtual_walls.setChecked(True)
        hbox.addWidget(self.virtual_walls)

        # self.disable_auto_springs = QCheckBox_custom("disable springs")
        # self.disable_auto_springs.setFixedWidth(cbox_width)
        # self.disable_auto_springs.setChecked(True)
        # hbox.addWidget(self.disable_auto_springs)

        vbox.addLayout(hbox)


        #------
        # self.insert_hacky_blank_lines(self.config_tab_layout)
        for idx in range(5):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            vbox.addWidget(blank_line)

        #==================================================================
        # self.config_params.setLayout(self.config_tab_layout)
        self.config_params.setLayout(vbox)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)

        self.scroll.setWidget(self.config_params) # self.config_params = QWidget()

        self.layout = QVBoxLayout(self)  # leave this!
        self.layout.addWidget(self.scroll)

    def random_seed_gp_cb(self, id):
        if id == 0:
            self.random_seed_integer.setEnabled(False)
        else:
            self.random_seed_integer.setEnabled(True)
            self.random_seed_integer.check_validity() # set color based on current validity

        # see if random_seed remains in user_parameters
        if hasattr(self.xml_creator, 'user_params_tab'):
            # this is called before user_params_tab is created one time, so make sure it exists
            for idx in range(self.xml_creator.user_params_tab.count):
                v_name = self.xml_creator.user_params_tab.utable.cellWidget(idx,self.xml_creator.user_params_tab.var_icol_name).text()
                if v_name=="random_seed":
                    self.random_seed_warning_label.show_icon()
                    return
        self.random_seed_warning_label.hide_icon()
        

    def random_seed_integer_cb(self, text):
        if text == "":
            self.random_seed_integer.setPlaceholderText("system_clock") # warn the user that this will set the seed to system_clock

    def add_day_cb(self):
        if not self.max_time.text():
            max_time = float(0.0)
        else:
            max_time = float(self.max_time.text())
        print("max_time=", max_time)
        max_time += 1440
        self.max_time.setText(f"{max_time}")

    # def plot_folder_name_cb(self):   # allow plotting data from *any* output dir
    #     try:  # due to the initial callback
    #         self.vis_tab.output_dir = self.plot_folder.text()
    #     except:
    #         pass

        #--------------------------------------------------------
    def insert_hacky_blank_lines(self, glayout):
        idr = 4
        for idx in range(11):  # rwh: hack solution to align rows
            blank_line = QLabel("")
            idr += 1
            glayout.addWidget(blank_line, idr,0, 1,1) # w, row, column, rowspan, colspan

    def svg_clicked(self, bval):
        self.svg_interval.setEnabled(bval)
        self.plot_substrate_svg.setEnabled(bval)
        if bval:
            if self.plot_substrate_svg.isChecked():
                self.svg_substrate_to_plot_dropdown.setEnabled(True)
                self.svg_substrate_colormap_dropdown.setEnabled(True)
        else:
            self.svg_substrate_to_plot_dropdown.setEnabled(False)
            self.svg_substrate_colormap_dropdown.setEnabled(False)
            self.plot_substrate_svg.setChecked(False)
            self.plot_substrate_limits.setEnabled(False)
            self.plot_substrate_limits.setChecked(False)
            self.svg_substrate_min.setEnabled(False)
            self.svg_substrate_max.setEnabled(False)

    def plot_substrate_svg_clicked(self, bval):
        self.svg_substrate_to_plot_dropdown.setEnabled(bval)
        self.svg_substrate_colormap_dropdown.setEnabled(bval)
        self.plot_substrate_limits.setEnabled(bval)
        if not bval:
            self.plot_substrate_limits.setChecked(False)
            self.svg_substrate_min.setEnabled(False)
            self.svg_substrate_max.setEnabled(False)

    def plot_substrate_limits_clicked(self, bval):
        self.svg_substrate_min.setEnabled(bval)
        self.svg_substrate_max.setEnabled(bval)

    def svg_interval_changed(self, val):
        if self.sync_output:
            self.full_interval.setText(val)

    def svg_substrate_min_changed(self, val):
        if self.sync_output:
            self.svg_substrate_min.setText(val)

    def svg_substrate_max_changed(self, val):
        if self.sync_output:
            self.svg_substrate_max.setText(val)

    def full_clicked(self, bval):
        self.full_interval.setEnabled(bval)

    def full_interval_changed(self, val):
        if self.sync_output:
            self.svg_interval.setText(val)


    def sync_clicked(self, bval):
        self.sync_output = bval

        if bval:
            if self.save_svg.isChecked():
                self.full_interval.setText(self.svg_interval.text())
            else:
                self.svg_interval.setText(self.full_interval.text())

    def cells_csv_clicked(self, bval):
        self.csv_folder.setEnabled(bval)
        self.csv_file.setEnabled(bval)

    def fill_gui(self):
        self.fill_substrates_comboboxes()
        self.fill_substrate_colormap_comboboxes()

        self.xmin.setText(self.xml_root.find(".//x_min").text)
        self.xmax.setText(self.xml_root.find(".//x_max").text)
        self.xdel.setText(self.xml_root.find(".//dx").text)

        self.ymin.setText(self.xml_root.find(".//y_min").text)
        self.ymax.setText(self.xml_root.find(".//y_max").text)
        self.ydel.setText(self.xml_root.find(".//dy").text)
    
        self.zmin.setText(self.xml_root.find(".//z_min").text)
        self.zmax.setText(self.xml_root.find(".//z_max").text)
        self.zdel.setText(self.xml_root.find(".//dz").text)

        if self.xml_root.find(".//virtual_wall_at_domain_edge") is not None:
            # print("\n\n---------virtual_wall text.lower()=",self.xml_root.find(".//virtual_wall_at_domain_edge").text.lower())
            check = self.xml_root.find(".//virtual_wall_at_domain_edge").text.lower()
            # print("---------virtual_wall check=",check)
            # print("---------type(check)=",type(check))
            # print("---------check.find('true')=",check.find('true'))
            if self.xml_root.find(".//virtual_wall_at_domain_edge").text.lower() == "true":
                # print("--------- doing self.virtual_walls.setChecked(True)")
                self.virtual_walls.setChecked(True)
            else:
                self.virtual_walls.setChecked(False)
        else:
            print("\n\n---------virtual_wall_at_domain_edge is None !!!!!!!!!!!!1")

        if self.xml_root.find(".//random_seed") is not None:
            # this intentionally will read in the user_parameter random_seed if it exists. this will facilitate the user using this new placement (importantly, the default custom.cpp will still use the user_parameter to override the value placed here)
            text = self.xml_root.find(".//random_seed").text
            print("\n------------------ config_tab: random_seed = ",text)
            if text in  ["system_clock","random","",None]:
                self.random_seed_random_button.setChecked(True)
            else:
                self.random_seed_integer_button.setChecked(True)
                self.random_seed_integer.setText(self.xml_root.find(".//random_seed").text)
        else:
            self.random_seed_random_button.setChecked(True)

        if self.xml_root.find(".//user_parameters//random_seed") is not None:
            self.random_seed_warning_label.show_icon()

        # self.disable_auto_springs.setChecked(False)
        # if self.xml_root.find(".//disable_automated_spring_adhesions") is not None:
        #     if self.xml_root.find(".//disable_automated_spring_adhesions").text.lower() == "true":
        #         self.disable_auto_springs.setChecked(True)

        # No, let's not do this
        # if self.xml_root.find(".//disable_automated_spring_adhesions") is not None:
        #     msg = f"NOTE: disable_automated_spring_adhesions in .xml is deprecated."
        #     print(msg)
        #     msgBox = QMessageBox()
        #     msgBox.setTextFormat(Qt.RichText)
        #     msgBox.setText(msg)
        #     msgBox.setStandardButtons(QMessageBox.Ok)
        #     returnValue = msgBox.exec()
        
        self.max_time.setText(self.xml_root.find(".//max_time").text)
        self.diffusion_dt.setText(self.xml_root.find(".//dt_diffusion").text)
        self.mechanics_dt.setText(self.xml_root.find(".//dt_mechanics").text)
        self.phenotype_dt.setText(self.xml_root.find(".//dt_phenotype").text)
        
        self.num_threads.setText(self.xml_root.find(".//omp_num_threads").text)

        self.folder.setText(self.xml_root.find(".//save//folder").text)
        
        self.svg_interval.setText(self.xml_root.find(".//SVG//interval").text)
        # NOTE: do this *after* filling the mcds_interval, directly above, due to the callback/constraints on them??
        is_plotting_svg = False
        if self.xml_root.find(".//SVG//enable").text.lower() == 'true':
            is_plotting_svg = True
        self.save_svg.setChecked(is_plotting_svg)
        self.svg_clicked(is_plotting_svg)

        is_plotting_substrate_on_svg = False
        if self.xml_root.find(".//SVG//plot_substrate//substrate") is not None:
            self.svg_substrate_to_plot_dropdown.setCurrentText(self.xml_root.find(".//SVG//plot_substrate//substrate").text)
            # NOTE: do this *after* filling the mcds_interval, directly above, due to the callback/constraints on them??
            if is_plotting_svg:
                uep = self.xml_root.find(".//SVG//plot_substrate")
                if uep.attrib['enabled'].lower() == 'true':
                    is_plotting_substrate_on_svg = True
                self.plot_substrate_svg.setChecked(is_plotting_substrate_on_svg)
                self.plot_substrate_svg_clicked(is_plotting_substrate_on_svg)
        else:
            self.svg_substrate_to_plot_dropdown.itemText(0)
            self.plot_substrate_svg.setChecked(False)
            self.plot_substrate_svg_clicked(False)

        if self.xml_root.find(".//SVG//plot_substrate//colormap") is not None:
            self.svg_substrate_colormap_dropdown.setCurrentText(self.xml_root.find(".//SVG//plot_substrate//colormap").text)
        else:
            self.svg_substrate_colormap_dropdown.itemText(0)

        limits_included = False
        uep = self.xml_root.find(".//SVG//plot_substrate")
        if (uep is not None) and (uep.attrib['limits'].lower() == 'true'):
            limits_included = True

        if limits_included:
            if self.xml_root.find(".//SVG//plot_substrate//min_conc") is not None:
                self.svg_substrate_min.setText(self.xml_root.find(".//SVG//plot_substrate//min_conc").text)
            else:
                limits_included = False
            if self.xml_root.find(".//SVG//plot_substrate//max_conc") is not None:
                self.svg_substrate_max.setText(self.xml_root.find(".//SVG//plot_substrate//max_conc").text)
            else:
                limits_included = False
        self.plot_substrate_limits.setChecked(limits_included)
        self.plot_substrate_limits_clicked(limits_included)

        self.full_interval.setText(self.xml_root.find(".//full_data//interval").text)
        bval = False
        if self.xml_root.find(".//full_data//enable").text.lower() == 'true':
            bval = True
        self.save_full.setChecked(bval)
        self.full_clicked(bval)

        uep = self.xml_root.find(".//initial_conditions//cell_positions")
        if uep == None:  # not present
            return
        self.csv_folder.setText(self.xml_root.find(".//initial_conditions//cell_positions//folder").text)
        self.csv_file.setText(self.xml_root.find(".//initial_conditions//cell_positions//filename").text)
        bval = False
        if uep.attrib['enabled'].lower() == 'true':
            bval = True
        self.cells_csv.setChecked(bval)
        self.cells_csv_clicked(bval)



    # Read values from the GUI widgets and generate/write a new XML
    def fill_xml(self):
        indent1 = '\n'
        indent6 = '\n      '
        indent8 = '\n        '
        indent10 = '\n          '

        # print(f"\nconfig_tab: fill_xml: =self.xml_root = {self.xml_root}" )
        # print("config_tab: fill_xml: xmin=",self.xmin.text() )
        self.xml_root.find(".//x_min").text = self.xmin.text()
        self.xml_root.find(".//x_max").text = self.xmax.text()
        self.xml_root.find(".//dx").text = self.xdel.text()

        self.xml_root.find(".//y_min").text = self.ymin.text()
        self.xml_root.find(".//y_max").text = self.ymax.text()
        self.xml_root.find(".//dy").text = self.ydel.text()

        self.xml_root.find(".//z_min").text = self.zmin.text()
        self.xml_root.find(".//z_max").text = self.zmax.text()
        self.xml_root.find(".//dz").text = self.zdel.text()

        # is this model 2D or 3D?
        zmax = float(self.zmax.text())
        zmin = float(self.zmin.text())
        zdel = float(self.zdel.text())
        if (zmax-zmin) > zdel:
            self.xml_root.find(".//domain//use_2D").text = 'false'
        else:
            self.xml_root.find(".//domain//use_2D").text = 'true'
        
        # may want to check for (max-min) being an integer multiple of delta spacings:
            # msg = QMessageBox()
            # msg.setIcon(QMessageBox.Critical)
            # msg.setText("Warning")
            # msg.setInformativeText('The output intervals for SVG and full (in Config Basics) do not match.')
            # msg.setWindowTitle("Warning")
            # msg.exec_()


        # if not self.xml_root.find(".//virtual_wall_at_domain_edge"):
        # opts = self.xml_root.find(".//options")
        # if not opts:
        #     print("------ Missing <options> in config .xml.  HALT.")
        #     sys.exit(1)

                # subelm = ET.SubElement(elm, 'physical_parameter_set')
                # subelm.text = indent10
                # subelm.tail = indent8

                # subelm2 = ET.SubElement(subelm, "diffusion_coefficient",{"units":"micron^2/min"})
                # subelm2.text = self.param_d[substrate]["diffusion_coef"]
                # subelm2.tail = indent10

        # do not *require* the input .xml to have these tags; insert them if missing
        bval = "false"
        if self.virtual_walls.isChecked():
            bval = "true"
        if self.xml_root.find(".//virtual_wall_at_domain_edge") is not None:
            self.xml_root.find(".//virtual_wall_at_domain_edge").text = bval
        else:  # missing in original; insert it (happens at write)
            uep = self.xml_root.find('.//options')
            subelm = ET.SubElement(uep, "virtual_wall_at_domain_edge")
            subelm.text = bval

        if self.xml_root.find(".//options//random_seed") is None:
            uep = self.xml_root.find('.//options')
            subelm = ET.SubElement(uep, "random_seed")

        if self.random_seed_random_button.isChecked():
            self.xml_root.find(".//options//random_seed").text = "system_clock"
        else:
            self.xml_root.find(".//options//random_seed").text = self.random_seed_integer.text()

        # bval = "false"
        # if self.disable_auto_springs.isChecked():
        #     bval = "true"
        # if self.xml_root.find(".//disable_automated_spring_adhesions") is not None:
        #     self.xml_root.find(".//disable_automated_spring_adhesions").text = bval
        # else:  # missing in original; insert it (happens at write)
        #     uep = self.xml_root.find('.//options')
        #     subelm = ET.SubElement(uep, "disable_automated_spring_adhesions")
        #     subelm.text = bval


        # rwh: Not sure why I couldn't get this to work, i.e., to *insert* the element (just one time) if it didn't exist.
        # vwall = self.xml_root.find(".//virtual_wall_at_domain_edge")
        # # if self.xml_root.find(".//virtual_wall_at_domain_edge"):
        # if False:
        #     print("\n------ FOUND virtual_wall_at_domain_edge.")
        # # if not opts.find(".//virtual_wall_at_domain_edge"):
        # # if not opts.find("virtual_wall_at_domain_edge"):
        #     if self.virtual_walls.isChecked():
        #         # self.xml_root.find(".//virtual_wall_at_domain_edge").text = 'true'
        #         vwall.text = 'true'
        #     else:
        #         vwall.text = 'false'
        #         # self.xml_root.find(".//virtual_wall_at_domain_edge").text = 'false'
        # else:
        #     print("\n------ virtual_wall_at_domain_edge NOT found.  Create it.")
        #     # todo: create it?  Child of root.
        #     print("------config_tab.py: no virtual_wall_at_domain_edge tag")
        #     # <options>
        #     #     <legacy_random_points_on_sphere_in_divide>false</legacy_random_points_on_sphere_in_divide>
        #     #     <virtual_wall_at_domain_edge>true</virtual_wall_at_domain_edge>		
        #     # </options>	
        #     # elm = ET.Element("options") 
        #     # # elm.tail = '\n' + indent6
        #     # elm.tail = indent6
        #     # elm.text = indent6
        #     opts = self.xml_root.find(".//options")
        #     bval = "false"
        #     if self.virtual_walls.isChecked():
        #         bval = "true"
        #     subelm = ET.SubElement(opts, 'virtual_wall_at_domain_edge')
        #     subelm.text = bval
        #     subelm.tail = indent8
        #     opts.insert(0,subelm)

        self.xml_root.find(".//max_time").text = self.max_time.text()
        # print(f'------- config_tab.py: fill_xml(): update max_time = {self.max_time.text()}')
        self.xml_root.find(".//dt_diffusion").text = self.diffusion_dt.text()
        self.xml_root.find(".//dt_mechanics").text = self.mechanics_dt.text()
        self.xml_root.find(".//dt_phenotype").text = self.phenotype_dt.text()
        self.xml_root.find(".//omp_num_threads").text = self.num_threads.text()
        self.xml_root.find(".//save//folder").text = self.folder.text()
        print(f'------- config_tab.py: fill_xml(): setting folder = {self.folder.text()}')

        if self.save_svg.isChecked():
            self.xml_root.find(".//SVG//enable").text = 'true'
        else:
            self.xml_root.find(".//SVG//enable").text = 'false'
        self.xml_root.find(".//SVG//interval").text = self.svg_interval.text()

        if self.xml_root.find(".//SVG//plot_substrate") is None:
            # add this eleement if it does not exist
            elm = ET.Element("plot_substrate",
                                {"enabled":'false', "limits":'false'})
            ET.SubElement(elm, 'substrate')
            ET.SubElement(elm, 'min_conc')
            ET.SubElement(elm, 'max_conc')
            ET.SubElement(elm, 'colormap')
            self.xml_root.find('.//save//SVG').insert(2,elm) # [interval, enable, plot_substrate]

        if self.plot_substrate_svg.isChecked():
            self.xml_root.find(".//SVG//plot_substrate").attrib['enabled'] = 'true'
        else:
            self.xml_root.find(".//SVG//plot_substrate").attrib['enabled'] = 'false'
        if self.plot_substrate_limits.isChecked():
            self.xml_root.find(".//SVG//plot_substrate").attrib['limits'] = 'true'
        else:
            self.xml_root.find(".//SVG//plot_substrate").attrib['limits'] = 'false'
        self.xml_root.find(".//SVG//plot_substrate//substrate").text = self.svg_substrate_to_plot_dropdown.currentText()
        if self.plot_substrate_limits.isChecked():
            if self.xml_root.find(".//SVG//plot_substrate//min_conc") is None:
                elm = ET.Element("min_conc")
                self.xml_root.find('.//save//SVG//plot_substrate').insert(1,elm)
            self.xml_root.find(".//SVG//plot_substrate//min_conc").text = self.svg_substrate_min.text()
            if self.xml_root.find(".//SVG//plot_substrate//max_conc") is None:
                elm = ET.Element("max_conc")
                self.xml_root.find('.//save//SVG//plot_substrate').insert(2,elm)
            self.xml_root.find(".//SVG//plot_substrate//max_conc").text = self.svg_substrate_max.text()
        
        if self.plot_substrate_svg.isChecked():
            if self.xml_root.find(".//SVG//plot_substrate//colormap") is None:
                elm = ET.Element("colormap")
                self.xml_root.find('.//save//SVG//plot_substrate').insert(1,elm)
            self.xml_root.find(".//SVG//plot_substrate//colormap").text = self.svg_substrate_colormap_dropdown.currentText()


        if self.save_full.isChecked():
            self.xml_root.find(".//full_data//enable").text = 'true'
        else:
            self.xml_root.find(".//full_data//enable").text = 'false'
        self.xml_root.find(".//full_data//interval").text = self.full_interval.text()
        # self.xml_root.find(".//full_data//interval").text = self.svg_interval.text()

        if self.xml_root.find(".//initial_conditions") is None: 
            print("\n ===  Warning: Original XML is missing <initial_conditions> block.")
            print("        Will not insert into saved file.\n")
            return

        if self.cells_csv.isChecked():
            self.xml_root.find(".//initial_conditions//cell_positions").attrib['enabled'] = 'true'
        else:
            self.xml_root.find(".//initial_conditions//cell_positions").attrib['enabled'] = 'false'


        # self.xml_root.find(".//initial_conditions//cell_positions/folder").text = './data'
        self.xml_root.find(".//initial_conditions//cell_positions/folder").text = self.csv_folder.text()
        # print(f'------- config_tab.py: fill_xml(): setting csv folder = {self.csv_folder.text()}')

        self.xml_root.find(".//initial_conditions//cell_positions/filename").text = self.csv_file.text()
        # print(f'------- config_tab.py: fill_xml(): setting csv filename = {self.csv_file.text()}')
        # if self.csv_rb1.isChecked():
        #     self.xml_root.find(".//initial_conditions//cell_positions/filename").text = 'all_cells.csv'
        # else:
        #     self.xml_root.find(".//initial_conditions//cell_positions/filename").text = 'all_cells_above_y0.csv'


        # TODO: verify valid type (numeric) and range?
        # xml_root.find(".//x_min").text = str(self.xmin.value)
        # xml_root.find(".//x_max").text = str(self.xmax.value)
        # xml_root.find(".//dx").text = str(self.xdelta.value)
        # xml_root.find(".//y_min").text = str(self.ymin.value)
        # xml_root.find(".//y_max").text = str(self.ymax.value)
        # xml_root.find(".//dy").text = str(self.ydelta.value)
        # xml_root.find(".//z_min").text = str(self.zmin.value)
        # xml_root.find(".//z_max").text = str(self.zmax.value)
        # xml_root.find(".//dz").text = str(self.zdelta.value)

        # xml_root.find(".//max_time").text = str(self.tmax.value)

        # xml_root.find(".//omp_num_threads").text = str(self.omp_threads.value)

        # xml_root.find(".//SVG").find(".//enable").text = str(self.toggle_svg.value)
        # xml_root.find(".//SVG").find(".//interval").text = str(self.svg_interval.value)
        # xml_root.find(".//full_data").find(".//enable").text = str(self.toggle_mcds.value)
        # xml_root.find(".//full_data").find(".//interval").text = str(self.mcds_interval.value)

            #-----------------------------------------------------------
    def import_seeding_cb(self):
        # filePath = QFileDialog.getOpenFileName(self,'',".",'*.xml')
        filePath = QFileDialog.getOpenFileName(self,'',".")
        full_path_rules_name = filePath[0]
        # logging.debug(f'\nimport_seeding_cb():  full_path_rules_name ={full_path_rules_name}')
        print(f'\nimport_seeding_cb():  full_path_rules_name ={full_path_rules_name}')
        basename = os.path.basename(full_path_rules_name)
        print(f'import_seeding_cb():  basename ={basename}')
        dirname = os.path.dirname(full_path_rules_name)
        print(f'import_seeding_cb():  dirname ={dirname}')
        # if (len(full_path_rules_name) > 0) and Path(full_path_rules_name):
        if (len(full_path_rules_name) > 0) and Path(full_path_rules_name).is_file():
            print("import_seeding_cb():  filePath is valid")
            # logging.debug(f'     filePath is valid')
            print("len(full_path_rules_name) = ", len(full_path_rules_name) )
            # logging.debug(f'     len(full_path_rules_name) = {len(full_path_rules_name)}' )
            self.csv_folder.setText(dirname)
            self.csv_file.setText(basename)
            # fname = os.path.basename(full_path_rules_name)
            # self.current_xml_file = full_path_rules_name

            # self.add_new_model(self.current_xml_file, True)
            # self.config_file = self.current_xml_file
            # if self.xml_creator.studio_flag:
            #     self.run_tab.config_file = self.current_xml_file
            #     self.run_tab.config_xml_name.setText(self.current_xml_file)
            # self.show_sample_model()
            # self.fill_gui()

            # arg! how does it not catch this as an invalid file above??
            # in fill_rules():  full_rules_fname= /Users/heiland/git/data/tumor_rules.csv
            print(f'import_seeding_cb():  (guess) calling fill_rules() with ={full_path_rules_name}')
            # if not self.nanohub_flag:
            #     full_path_rules_name = os.path.abspath(os.path.join(self.homedir,'tmpdir',folder_name, file_name))
            #     print(f'import_seeding_cb():  NOW calling fill_rules() with ={full_path_rules_name}')

        else:
            print("import_seeding_cb():  full_path_model_name is NOT valid")

    def fill_substrates_comboboxes(self):
        logging.debug(f'cell_def_tab.py: ------- fill_substrates_comboboxes')
        self.substrate_list.clear()  # rwh/todo: where/why/how is this list maintained?
        self.svg_substrate_to_plot_dropdown.clear()
        uep = self.xml_root.find('.//microenvironment_setup')  # find unique entry point
        if uep:
            idx = 0
            for var in uep.findall('variable'):
                logging.debug(f' --> {var.attrib["name"]}')
                name = var.attrib['name']
                self.substrate_list.append(name)
                self.svg_substrate_to_plot_dropdown.addItem(name)

    def fill_substrate_colormap_comboboxes(self):
        logging.debug(f'cell_def_tab.py: ------- fill_substrate_colormap_comboboxes')
        self.svg_substrate_colormap_dropdown.addItem("YlOrRd")
        self.svg_substrate_colormap_dropdown.addItem("YlOrRd_r")
        self.svg_substrate_colormap_dropdown.addItem("viridis")
        self.svg_substrate_colormap_dropdown.addItem("viridis_r")
        self.svg_substrate_colormap_dropdown.addItem("turbo")
        self.svg_substrate_colormap_dropdown.addItem("turbo_r")
        self.svg_substrate_colormap_dropdown.addItem("plasma")
        self.svg_substrate_colormap_dropdown.addItem("plasma_r")
        self.svg_substrate_colormap_dropdown.addItem("jet")
        self.svg_substrate_colormap_dropdown.addItem("jet_r")

    def add_new_substrate(self, sub_name):
        self.substrate_list.append(sub_name)
        self.svg_substrate_to_plot_dropdown.addItem(sub_name)

    def delete_substrate(self, item_idx):
        subname = self.svg_substrate_to_plot_dropdown.itemText(item_idx)
        self.substrate_list.remove(subname)
        self.svg_substrate_to_plot_dropdown.removeItem(item_idx)

    def renamed_substrate(self, old_name,new_name):
        self.substrate_list = [new_name if x==old_name else x for x in self.substrate_list]
        for idx in range(len(self.substrate_list)):
            if old_name == self.svg_substrate_to_plot_dropdown.itemText(idx):
                self.svg_substrate_to_plot_dropdown.setItemText(idx, new_name)
                
    def count_substrates(self):
        return len(self.substrate_list)
    def day_value_changed_str(self, s):
        self.update_max_time()
                
    def hour_value_changed_str(self,s):
        self.update_max_time()
                
    def minute_value_changed_str(self,s):
        self.update_max_time()

    def minute_fraction_value_changed_str(self,s):
        self.update_max_time()

    def update_max_time(self):
        if self.update_max_time_flag:
            new_time = self.day_spin_box.value()*1440 + self.hour_spin_box.value()*60 + self.minute_spin_box.value() + self.minute_fraction_spin_box.value()
            new_time = max(0,new_time)
            force_update = str(new_time) == self.max_time.text() # sometimes the value is the same, but the spinboxes have changes (like hour=-1 after max time at 0)
            self.max_time.setText(str(new_time))
            if force_update:
                self.max_time_changed_cb()

    def max_time_changed_cb(self):
        self.update_max_time_flag = False # disable QSpinBox cbs to update max time while setting these
        try:
            time = floor(float(self.max_time.text()))
            fraction_minutes = float(self.max_time.text()) - time
        except:
            time = 0
            fraction_minutes = 0
        minutes = time % 60
        time -= minutes
        time = int(time/60)
        hours = time % 24
        time -= hours
        time = int(time/24)
        days = time
        self.minute_fraction_spin_box.setValue(fraction_minutes)
        self.minute_spin_box.setValue(minutes)
        self.hour_spin_box.setValue(hours)
        self.day_spin_box.setValue(days)
        self.update_max_time_flag = True

    def diffusion_dt_changed_cb(self):
        try:
            diffusion_dt = float(self.diffusion_dt.text())
            if diffusion_dt > 0:
                new_num_decimals = -floor(log10(diffusion_dt))
                self.minute_fraction_spin_box.setDecimals(new_num_decimals)
                self.minute_fraction_spin_box.setSingleStep(10**(-new_num_decimals))
            else:
                self.minute_fraction_spin_box.setDecimals(2)
        except:
            self.minute_fraction_spin_box.setDecimals(2)
    #-----------------------------------------------------------------------------------------
    