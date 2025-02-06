"""
Authors:
Daniel Bergman (dbergma5@jh.edu)
Jeanette Johnson (jjohn450@jhmi.edu)
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
Rf. Credits.md
"""

import sys
import logging
import os
try:
    import anndata
    HAVE_ANNDATA = True
except:
    HAVE_ANNDATA = False

try:
    import anndata2ri
    # import rpy2.robjects as ro
    from rpy2.robjects import pandas2ri, r
    from rpy2.robjects.packages import importr
    HAVE_RPY2 = True
except:
    HAVE_RPY2 = False

BIWT_DEV_MODE = os.getenv('BIWT_DEV_MODE', 'False')
if BIWT_DEV_MODE == 'True':
    from biwt_dev import biwt_dev_mode
BIWT_DEV_MODE = BIWT_DEV_MODE=='True'

import copy
import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Patch, Rectangle, Annulus, Wedge
from matplotlib.collections import PatchCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib import transforms

from pathlib import Path
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication,QWidget,QLineEdit,QHBoxLayout,QVBoxLayout,QRadioButton,QPushButton, QLabel,QCheckBox,QComboBox,QScrollArea,QGridLayout, QFileDialog, QButtonGroup, QSplitter, QSizePolicy, QSpinBox
from PyQt5.QtGui import QIcon

from studio_classes import QHLine, QVLine, QCheckBox_custom, QRadioButton_custom, LegendWindow

class GoBackButton(QPushButton):
    def __init__(self, parent, biwt, pre_cb=None, post_cb=None):
        super().__init__(parent)
        self.setText("\u2190 Go back")
        self.setStyleSheet(f"QPushButton {{background-color: lightgreen; color: black;}}")
        if pre_cb is not None:
            self.clicked.connect(pre_cb)
        self.clicked.connect(biwt.go_back_to_prev_window)
        if post_cb is not None:
            self.clicked.connect(post_cb)

class ContinueButton(QPushButton):
    def __init__(self, parent, cb, text="Continue \u2192",styleSheet="QPushButton {background-color: lightgreen; color: black;}"):
        super().__init__(parent)
        self.setText(text)
        self.setStyleSheet(styleSheet)
        self.clicked.connect(cb)

class BioinformaticsWalkthroughWindow(QWidget):
    def __init__(self, biwt):
        super().__init__()
        self.setWindowTitle(f"Bioinformatics Import Walkthrough: Step {biwt.current_window_idx+1}")
        self.biwt = biwt
        self.biwt.stale_futures = True # initializing a window means that any future windows are stale

class BioinformaticsWalkthroughWindow_WarningWindow(BioinformaticsWalkthroughWindow):
    def __init__(self, biwt, layout, continue_cb):
        super().__init__(biwt)
        vbox = QVBoxLayout()
        vbox.addLayout(layout)

        self.go_back_button = GoBackButton(self, self.biwt)
        self.continue_button = ContinueButton(self, continue_cb)
        hbox_gb_cont = QHBoxLayout()
        hbox_gb_cont.addWidget(self.go_back_button)
        hbox_gb_cont.addWidget(self.continue_button)

        vbox.addLayout(hbox_gb_cont)
        self.setLayout(vbox)
        
class BioinformaticsWalkthroughWindow_ClusterColumn(BioinformaticsWalkthroughWindow):
    def __init__(self, biwt):
        super().__init__(biwt)

        print("------Selecting cell type column------")

        # col_names = list(self.biwt.adata.obs.columns)
        self.biwt.auto_continue = False
        self.column_combobox = QComboBox()
        data_column_keys = list(self.biwt.data_columns.keys())
        data_column_keys.sort()
        for col_name in data_column_keys:
            self.column_combobox.addItem(col_name)
        if self.biwt.column_line_edit.text() in self.biwt.data_columns:
            s = "Select column that contains cell type info:"
            self.biwt.auto_continue = True
            self.column_combobox.setCurrentIndex(self.column_combobox.findText(self.biwt.column_line_edit.text()))
        elif self.biwt.column_line_edit.text() != "":
            s = f"{self.biwt.column_line_edit.text()} not found in the columns of the obs matrix.\nSelect from the following:"
        else:
            s = "Select column that contains cell type info:"

        vbox = QVBoxLayout()
        label = QLabel(s)
        vbox.addWidget(label)

        self.column_combobox.currentIndexChanged.connect(self.column_combobox_changed_cb)
        vbox.addWidget(self.column_combobox)

        hbox = QHBoxLayout()
        continue_button = ContinueButton(self, self.process_window)
        hbox.addWidget(continue_button)

        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def column_combobox_changed_cb(self, idx):
        self.biwt.stale_futures = True

    def process_window(self):
        self.biwt.current_column = self.column_combobox.currentText()
        self.biwt.continue_from_import()

class BioinformaticsWalkthroughWindow_SpatialQuery(BioinformaticsWalkthroughWindow):
    def __init__(self, biwt):
        super().__init__(biwt)

        print("------Asking if you want to use the spatial data found------")

        s = f"It seems this data may contain spatial information in {self.biwt.spatial_data_location}.\n"
        s += "Would you like to use this?"
        label = QLabel(s)

        self.yes_no_group = QButtonGroup()
        self.yes = QRadioButton_custom("Yes")
        self.no = QRadioButton_custom("No")
        self.yes_no_group.addButton(self.yes,0)
        self.yes_no_group.addButton(self.no,1)
        self.yes_no_group.idToggled.connect(self.yn_toggled)
        self.yes.setChecked(True)
        hbox_yn = QHBoxLayout()
        hbox_yn.addWidget(self.yes)
        hbox_yn.addWidget(self.no)

        self.go_back_button = GoBackButton(self, self.biwt)
        self.continue_button = ContinueButton(self, self.process_window)
        hbox_gb_cont = QHBoxLayout()
        hbox_gb_cont.addWidget(self.go_back_button)
        hbox_gb_cont.addWidget(self.continue_button)

        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addLayout(hbox_yn)
        vbox.addLayout(hbox_gb_cont)
        self.setLayout(vbox)

    def yn_toggled(self,id):
        self.biwt.stale_futures = True
        self.biwt.use_spatial_data = id==0

    def process_window(self):
        self.biwt.continue_from_spatial_query()

class BioinformaticsWalkthroughWindow_EditCellTypes(BioinformaticsWalkthroughWindow):
    def __init__(self, biwt):
        super().__init__(biwt)

        print("------Editing cell types------")

        keep_color = "lightgreen"
        merge_color = "yellow"
        delete_color = "#FFCCCB"
        label = QLabel(f"""The following cell types were found.<br>\
                        Choose which to <b style="background-color: {keep_color};">KEEP</b>, \
                        <b style="background-color: {merge_color};">MERGE</b>, and \
                        <b style="background-color: {delete_color};">DELETE</b>.<br>\
                        By default, all are kept.\
                        """)
        checkbox_style_template = lambda x : f"""
                QCheckBox {{
                    color : black;
                    font-weight: bold;
                    background-color: {x};
                }}
                QCheckBox::indicator:checked {{
                    background-color: rgb(255,255,255);
                    border: 1px solid #5A5A5A;
                    width : 15px;
                    height : 15px;
                    border-radius : 3px;
                    image: url(images:checkmark.png);
                }}
                QCheckBox::indicator:unchecked
                {{
                    background-color: {"rgb(255,255,255)" if x==keep_color else "rgb(0,0,0)"};
                    border: 1px solid #5A5A5A;
                    width : 15px;
                    height : 15px;
                    border-radius : 3px;
                }}
                """
        self.checkbox_style = {}
        self.checkbox_style["keep"] = checkbox_style_template(keep_color)
        self.checkbox_style["merge"] = checkbox_style_template(merge_color)
        self.checkbox_style["delete"] = checkbox_style_template(delete_color)
        self.biwt.cell_type_dict_on_edit = {} # dictionary mapping original cell_type to intermediate/final cell type (depending on stage of walkthrough)

        vbox = QVBoxLayout()
        vbox.addWidget(label)
        self.checkbox_dict_edit = {}
        self.keep_button = {}
        self.checkbox_group = QButtonGroup(exclusive=False)
        self.checkbox_group.buttonToggled.connect(self.cell_type_toggled_cb)
        self.merge_id = 0
        rename_button_style_sheet_template = lambda x : f"""
            QPushButton {{
                color : black;
                font-weight : bold;
            }}
            QPushButton:enabled {{
                background-color: {x};
            }}
            QPushButton:disabled {{
                background-color : grey;
            }}
            """
        self.rename_button_style_sheet = {}
        self.rename_button_style_sheet["keep"] = rename_button_style_sheet_template(keep_color)
        self.rename_button_style_sheet["merge"] = rename_button_style_sheet_template(merge_color)
        self.rename_button_style_sheet["delete"] = rename_button_style_sheet_template(delete_color)
        row_height = 30
        self.cell_type_edit_scroll_area = QScrollArea()
        vbox_cell_type_keep = QVBoxLayout()
        for cell_type in self.biwt.cell_types_list_original:
            hbox = QHBoxLayout()
            self.checkbox_dict_edit[cell_type] = QCheckBox(cell_type,styleSheet=self.checkbox_style["keep"])
            self.checkbox_dict_edit[cell_type].setChecked(False)
            self.checkbox_dict_edit[cell_type].setEnabled(True)
            self.checkbox_dict_edit[cell_type].setFixedHeight(row_height)
            self.checkbox_group.addButton(self.checkbox_dict_edit[cell_type])
            
            self.keep_button[cell_type] = QPushButton("Keep",enabled=False,objectName=cell_type)
            self.keep_button[cell_type].setStyleSheet(rename_button_style_sheet_template(keep_color))
            self.keep_button[cell_type].setFixedHeight(row_height)
            self.keep_button[cell_type].clicked.connect(self.keep_cb)

            hbox.addWidget(self.checkbox_dict_edit[cell_type])
            hbox.addStretch(1)
            hbox.addWidget(self.keep_button[cell_type])
            vbox_cell_type_keep.addLayout(hbox)
            self.biwt.cell_type_dict_on_edit[cell_type] = cell_type

        widget_for_scroll_area = QWidget()
        widget_for_scroll_area.setLayout(vbox_cell_type_keep)
        self.cell_type_edit_scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.cell_type_edit_scroll_area.setWidget(widget_for_scroll_area)
        self.cell_type_edit_scroll_area.setWidgetResizable(True)

        vbox.addWidget(self.cell_type_edit_scroll_area)

        hbox = QHBoxLayout()

        self.merge_button = QPushButton("Merge",enabled=False,styleSheet=rename_button_style_sheet_template(merge_color))
        self.merge_button.clicked.connect(self.merge_cb)
        hbox.addWidget(self.merge_button)

        self.delete_button = QPushButton("Delete",enabled=False,styleSheet=rename_button_style_sheet_template(delete_color))
        self.delete_button.clicked.connect(self.delete_cb)
        hbox.addWidget(self.delete_button)

        vbox.addLayout(hbox)
        vbox.addWidget(QHLine())

        hbox = QHBoxLayout()

        go_back_button = GoBackButton(self, self.biwt, pre_cb=self.close_legend)
        continue_button = ContinueButton(self, self.process_window)

        hbox.addWidget(go_back_button)
        hbox.addWidget(continue_button)
        vbox.addLayout(hbox)

        self.dim_red_fig = None
        self.dim_red_canvas = None
        self.legend_window = None

        for key_substring in ["umap","tsne","pca","spatial"]:
            if self.try_to_plot_dim_red(key_substring=key_substring):
                splitter = QSplitter()
                left_side = QWidget()
                left_side.setLayout(vbox)
                splitter.addWidget(left_side)

                right_side = QWidget()
                vbox = QVBoxLayout()
                self.obsm_keys_combobox = QComboBox()
                # for i, k in enumerate(self.biwt.adata.obsm.keys()):
                for i, k in enumerate(self.biwt.data_vis_arrays.keys()):
                    if key_substring in k:
                        id = i
                    self.obsm_keys_combobox.addItem(k)
                self.obsm_keys_combobox.setCurrentIndex(id)
                self.obsm_keys_combobox.currentIndexChanged.connect(self.obsm_keys_combobox_changed_cb)

                label = QLabel("Marker Size")
                self.marker_size_edit = QLineEdit(str(self.marker_size))
                self.marker_size_edit.setValidator(QtGui.QDoubleValidator(bottom=0))
                self.marker_size_edit.textChanged.connect(self.marker_size_changed_cb)

                hbox = QHBoxLayout()
                hbox.addWidget(self.obsm_keys_combobox)
                hbox.addWidget(label)
                hbox.addWidget(self.marker_size_edit)

                vbox.addLayout(hbox)
                vbox.addWidget(self.dim_red_canvas)

                self.legend_button = QPushButton("Show Legend")
                self.legend_button.clicked.connect(self.show_legend)

                hbox = QHBoxLayout()
                hbox.addStretch()
                hbox.addWidget(self.legend_button)
                hbox.addStretch()
                vbox.addLayout(hbox)

                right_side.setLayout(vbox)
                splitter.addWidget(right_side)
                vbox = QVBoxLayout()
                vbox.addWidget(splitter)
                break
        
        self.setLayout(vbox)

    def close_legend(self):
        if self.legend_window is not None:
            self.legend_window.close()

    def show_legend(self):
        self.legend_window.show()

    def create_dim_red_fig(self):
        self.dim_red_fig = plt.figure()
        self.dim_red_canvas = FigureCanvasQTAgg(self.dim_red_fig)
        self.dim_red_canvas.setStyleSheet("background-color:transparent;")
        plt.style.use('ggplot')

        self.dim_red_ax = self.dim_red_fig.add_subplot(111, adjustable='box')
        self.marker_size = 5 # default marker size

    def try_to_plot_dim_red(self, key_substring="umap"):
        found, k, _ = self.biwt.search_vis_arrays_for(key_substring) # (was this found?, the key in adata.obsm, the value of adata.obsm[k])
        if not found:
            return False
        self.plot_dim_red(k)
        return True

    def plot_dim_red(self, k):
        v = self.biwt.data_vis_arrays[k]
        self.n_points = len(v)
        if self.dim_red_fig is None:
            self.create_dim_red_fig()
        
        temp = pd.CategoricalIndex(self.biwt.cell_types_original)
        using_sample = False
        if v.shape[0] > 1e5:
            # 100000 random indices from 0 to v.shape[0] - 1
            indices = np.random.choice(v.shape[0], size=100000, replace=False)
            using_sample = True
        else:
            indices = range(v.shape[0])
        self.scatter = self.dim_red_ax.scatter(v[indices,0],v[indices,1],self.marker_size,c=temp.codes[indices]) # 0.18844459036110225 = 5/sqrt(704) where I found 5 to be a good size when working with 704 points
        scatter_objects, _ = self.scatter.legend_elements()
        self.legend_window = LegendWindow(self, legend_artists=scatter_objects, legend_labels=temp.categories, legend_title="Clusters")
        # self.dim_red_fig.legend(scatter_objects, temp.categories,
        #             loc=8, title="Clusters",ncol=3, mode="expand")
        title_str = f"{k} plot"
        if using_sample:
            title_str += f" (sampling only {len(indices)} points of {v.shape[0]})"
        self.dim_red_ax.set_title(f"{k} plot")
        self.dim_red_ax.set_aspect(1.0)
        self.dim_red_canvas.update()
        self.dim_red_canvas.draw()

    def set_cell_type_to_keep(self, cell_type_to_keep, check_merge_gp=True):
        self.biwt.cell_type_dict_on_edit[cell_type_to_keep] = cell_type_to_keep
        self.checkbox_dict_edit[cell_type_to_keep].setEnabled(True)
        self.checkbox_dict_edit[cell_type_to_keep].setStyleSheet(self.checkbox_style["keep"])
        if  check_merge_gp and ("\u21d2 Merge Gp. #" in self.checkbox_dict_edit[cell_type_to_keep].text()):
            # check for merge group that is no longer merging
            gp_preimage = [cell_type for cell_type, new_name in self.biwt.cell_type_dict_on_edit.items() if (cell_type != cell_type_to_keep and new_name == self.biwt.cell_type_dict_on_edit[cell_type_to_keep])] # get cell types that map into this merge group
            if len(gp_preimage)==1: # then delete this merge gp:
                self.set_cell_type_to_keep(gp_preimage[0], check_merge_gp=False)
            elif cell_type_to_keep == self.biwt.cell_type_dict_on_edit[cell_type_to_keep]: # make sure this current cell type did not set the merge group name
                first_name = None
                for cell_type in gp_preimage:
                    if first_name is None:
                        first_name = cell_type
                    self.biwt.cell_type_dict_on_edit[cell_type] = first_name

        self.biwt.cell_type_dict_on_edit[cell_type_to_keep] = cell_type_to_keep
        self.checkbox_dict_edit[cell_type_to_keep].setText(cell_type_to_keep)
        self.keep_button[cell_type_to_keep].setEnabled(False)

    def keep_cb(self):
        self.biwt.stale_futures = True
        cell_type = self.sender().objectName()
        self.set_cell_type_to_keep(cell_type)

    def delete_cb(self):
        self.biwt.stale_futures = True
        for cell_type in self.checkbox_dict_edit.keys():
            if self.checkbox_dict_edit[cell_type].isChecked():
                self.biwt.cell_type_dict_on_edit[cell_type] = None
                self.checkbox_dict_edit[cell_type].setChecked(False)
                self.checkbox_dict_edit[cell_type].setEnabled(False)
                self.checkbox_dict_edit[cell_type].setStyleSheet(self.checkbox_style["delete"])

                self.keep_button[cell_type].setEnabled(True)

    def merge_cb(self):
        self.biwt.stale_futures = True
        self.merge_id += 1
        first_name = None
        for cell_type in self.checkbox_dict_edit.keys():
            if self.checkbox_dict_edit[cell_type].isChecked():
                if first_name is None:
                    first_name = cell_type
                self.biwt.cell_type_dict_on_edit[cell_type] = first_name
                self.checkbox_dict_edit[cell_type].setChecked(False)
                self.checkbox_dict_edit[cell_type].setEnabled(False)
                self.checkbox_dict_edit[cell_type].setStyleSheet(self.checkbox_style["merge"])
                self.checkbox_dict_edit[cell_type].setText(f"{cell_type} \u21d2 Merge Gp. #{self.merge_id}")

                self.keep_button[cell_type].setEnabled(True)

    def marker_size_changed_cb(self, text):
        if not self.marker_size_edit.hasAcceptableInput():
            return
        self.marker_size = float(text)
        self.scatter.set_sizes(self.marker_size + np.zeros_like(self.scatter.get_sizes()))
        # self.scatter.draw()
        self.dim_red_canvas.update()
        self.dim_red_canvas.draw()
        # for scatter_plot in self.scatter[0]:
        #     scatter_plot.set_sizes

    def obsm_keys_combobox_changed_cb(self, idx):
        key = self.obsm_keys_combobox.currentText()
        self.dim_red_ax.cla()
        self.try_to_plot_dim_red(key_substring=key)

    def cell_type_toggled_cb(self):
        checked_count = 0
        enable_delete_button = False
        enable_merge_button = False
        for checkbox in self.checkbox_dict_edit.values():
            checked_count += checkbox.isChecked()
            if checked_count == 1:
                enable_delete_button = True
            if checked_count == 2:
                enable_merge_button = True
                break
        self.delete_button.setEnabled(enable_delete_button)
        self.merge_button.setEnabled(enable_merge_button)

    def process_window(self):
        if self.legend_window is not None:
            self.legend_window.close()
        self.biwt.continue_from_edit()

class BioinformaticsWalkthroughWindow_RenameCellTypes(BioinformaticsWalkthroughWindow):
    def __init__(self, biwt):
        super().__init__(biwt)

        print("------Renaming cell types------")
        vbox = QVBoxLayout()
        label = QLabel("Rename your chosen cell types if you like:")
        vbox.addWidget(label)
        labels = {}
        self.new_name_line_edit = {}
        vbox_scroll_area = QVBoxLayout()
        for intermediate_type in self.biwt.intermediate_types:
            hbox = QHBoxLayout()
            label_text = ", ".join(self.biwt.intermediate_type_pre_image[intermediate_type])
            label_text += " \u21d2 "
            labels[intermediate_type] = QLabel(label_text)
            self.new_name_line_edit[intermediate_type] = QLineEdit()
            self.new_name_line_edit[intermediate_type].setText(self.biwt.intermediate_type_pre_image[intermediate_type][0])
            self.new_name_line_edit[intermediate_type].textChanged.connect(self.intermediate_type_renamed)
            hbox.addWidget(labels[intermediate_type])
            hbox.addWidget(self.new_name_line_edit[intermediate_type])
            vbox_scroll_area.addLayout(hbox)

        widget_for_scroll_area = QWidget()
        widget_for_scroll_area.setLayout(vbox_scroll_area)
        self.cell_type_rename_scroll_area = QScrollArea()
        self.cell_type_rename_scroll_area.setWidget(widget_for_scroll_area)

        vbox.addWidget(self.cell_type_rename_scroll_area)

        hbox = QHBoxLayout()
        go_back_button = GoBackButton(self, self.biwt)
        continue_button = ContinueButton(self, self.process_window)

        hbox.addWidget(go_back_button)
        hbox.addWidget(continue_button)

        vbox.addLayout(hbox)
        self.setLayout(vbox)

    def intermediate_type_renamed(self):
        self.biwt.stale_futures = True

    def process_window(self):
        
        self.biwt.cell_types_list_final = []
        self.biwt.cell_type_dict_on_rename = {}
        for intermediate_type in self.biwt.intermediate_types:
            self.biwt.cell_types_list_final.append(self.new_name_line_edit[intermediate_type].text())
            for cell_type in self.biwt.intermediate_type_pre_image[intermediate_type]:
                self.biwt.cell_type_dict_on_rename[cell_type] = self.new_name_line_edit[intermediate_type].text()
        self.biwt.continue_from_rename()

class BioinformaticsWalkthroughWindow_CellCounts(BioinformaticsWalkthroughWindow):
    def __init__(self, biwt):
        super().__init__(biwt)
        print("------Setting cell type counts------")
        names_width = 100
        counts_width = 120
        props_width = 120
        manual_width = 120
        confluence_width = 150
        
        vbox = QVBoxLayout()

        vbox.addWidget(QLabel("Set how many of each cell type to place. You may use the counts found in your data, or use proportions or confluence to scale these counts.\nYou may also set the counts manually; these values will track the others, allowing you to adjust from those baselines."))

        vbox_cols = [QVBoxLayout() for i in range(5)]

        label = QLabel("Cell Type")
        label.setFixedWidth(names_width)
        vbox_cols[0].addWidget(label)

        self.counts_button_group = QButtonGroup()
        self.counts_button_group.idToggled.connect(self.counts_button_cb)
        counts_button_group_next_id = 0

        self.use_counts_as_is_radio_button = QRadioButton_custom("Use counts")
        self.use_counts_as_is_radio_button.setFixedWidth(counts_width)
        self.use_counts_as_is_radio_button.setChecked(True)
        self.counts_button_group.addButton(self.use_counts_as_is_radio_button,counts_button_group_next_id)
        counts_button_group_next_id += 1

        self.use_props_radio_button = QRadioButton_custom("Use proportions")
        self.use_props_radio_button.setFixedWidth(props_width)
        self.use_props_radio_button.setChecked(False)
        self.counts_button_group.addButton(self.use_props_radio_button,counts_button_group_next_id)
        counts_button_group_next_id += 1

        self.use_confluence_radio_button = QRadioButton_custom("Set confluence (%)")
        self.use_confluence_radio_button.setFixedWidth(confluence_width)
        self.use_confluence_radio_button.setChecked(False)
        self.counts_button_group.addButton(self.use_confluence_radio_button,counts_button_group_next_id)
        counts_button_group_next_id += 1

        self.use_manual_radio_button = QRadioButton_custom("Set manually")
        self.use_manual_radio_button.setFixedWidth(manual_width)
        self.use_manual_radio_button.setChecked(False)
        self.counts_button_group.addButton(self.use_manual_radio_button,counts_button_group_next_id)
        counts_button_group_next_id += 1

        vbox_cols[1].addWidget(self.use_counts_as_is_radio_button)
        vbox_cols[2].addWidget(self.use_props_radio_button)
        vbox_cols[3].addWidget(self.use_confluence_radio_button)
        vbox_cols[4].addWidget(self.use_manual_radio_button)

        self.cell_type_props = [self.biwt.cell_counts[cell_type]/len(self.biwt.cell_types_final) for cell_type in self.biwt.cell_types_list_final]

        self.type_prop = {}
        self.type_manual = {}
        self.type_confluence = {}

        self.prop_box_callback_paused = False
        self.conf_box_callback_paused = False

        num_validator = QtGui.QIntValidator()
        num_validator.setBottom(0)

        self.setup_confluence_info()

        for idx, cell_type in enumerate(self.biwt.cell_types_list_final):
            hbox = QHBoxLayout()
            label = QLabel(cell_type)
            label.setFixedWidth(names_width)

            type_count = QLineEdit(enabled=False)
            type_count.setText(str(self.biwt.cell_counts[cell_type]))
            type_count.setFixedWidth(counts_width)
            type_count.setStyleSheet(self.biwt.qlineedit_style_sheet)

            self.type_prop[cell_type] = QLineEdit(enabled=False)
            self.type_prop[cell_type].setText(str(self.biwt.cell_counts[cell_type]))
            self.type_prop[cell_type].setFixedWidth(props_width)
            self.type_prop[cell_type].setStyleSheet(self.biwt.qlineedit_style_sheet)
            self.type_prop[cell_type].setValidator(num_validator)
            self.type_prop[cell_type].setObjectName(str(idx))
            self.type_prop[cell_type].textChanged.connect(self.prop_box_changed_cb)

            self.type_confluence[cell_type] = QLineEdit(enabled=False)
            self.type_confluence[cell_type].setFixedWidth(confluence_width)
            self.type_confluence[cell_type].setStyleSheet(self.biwt.qlineedit_style_sheet)
            self.type_confluence[cell_type].setValidator(QtGui.QDoubleValidator(bottom=0))
            self.type_confluence[cell_type].setObjectName(str(idx))
            self.type_confluence[cell_type].textChanged.connect(self.confluence_box_changed_cb)

            self.type_manual[cell_type] = QLineEdit(enabled=False)
            self.type_manual[cell_type].setText(str(self.biwt.cell_counts[cell_type]))
            self.type_manual[cell_type].setFixedWidth(manual_width)
            self.type_manual[cell_type].setStyleSheet(self.biwt.qlineedit_style_sheet)
            self.type_manual[cell_type].setValidator(num_validator)
            self.type_manual[cell_type].setObjectName(str(idx))
            self.type_manual[cell_type].textChanged.connect(self.manual_box_changed_cb)
            
            vbox_cols[0].addWidget(label)
            vbox_cols[1].addWidget(type_count)
            vbox_cols[2].addWidget(self.type_prop[cell_type])
            vbox_cols[3].addWidget(self.type_confluence[cell_type])
            vbox_cols[4].addWidget(self.type_manual[cell_type])

        label = QLabel("Total")
        label.setFixedWidth(names_width)

        type_count = QLineEdit(enabled=False)
        type_count.setText(str(len(self.biwt.cell_types_final)))
        type_count.setFixedWidth(counts_width)
        type_count.setStyleSheet(self.biwt.qlineedit_style_sheet)

        self.total_prop = QLineEdit(enabled=False)
        self.total_prop.setText(str(len(self.biwt.cell_types_final)))
        self.total_prop.setFixedWidth(props_width)
        self.total_prop.setStyleSheet(self.biwt.qlineedit_style_sheet)
        self.total_prop.setValidator(num_validator)
        self.total_prop.textChanged.connect(self.prop_box_changed_cb)
        self.total_prop.setObjectName("total_prop")

        self.total_conf = QLineEdit(enabled=False)
        self.total_conf.setFixedWidth(confluence_width)
        self.total_conf.setStyleSheet(self.biwt.qlineedit_style_sheet)
        self.total_conf.setValidator(QtGui.QDoubleValidator(bottom=0))
        self.total_conf.textChanged.connect(self.confluence_box_changed_cb)
        self.total_conf.setObjectName("total_conf")

        self.total_manual = QLineEdit(enabled=False)
        self.total_manual.setText(str(len(self.biwt.cell_types_final)))
        self.total_manual.setFixedWidth(manual_width)
        self.total_manual.setStyleSheet(self.biwt.qlineedit_style_sheet)
        self.total_manual.setValidator(num_validator)

        self.total_conf.setText("100") # this triggers the cb, which sets the manual column (see below) so force a toggle next
        self.use_manual_radio_button.setChecked(True) 
        self.use_counts_as_is_radio_button.setChecked(True) 

        vbox_cols[0].addWidget(label)
        vbox_cols[1].addWidget(type_count)
        vbox_cols[2].addWidget(self.total_prop)
        vbox_cols[3].addWidget(self.total_conf)
        vbox_cols[4].addWidget(self.total_manual)


        hbox = QHBoxLayout()
        for idx, vb in enumerate(vbox_cols):
            hbox.addLayout(vb)
            if idx != (len(vbox_cols)-1):
                hbox.addWidget(QVLine())
        vbox.addLayout(hbox)

        if len(self.cell_type_props) > 8:
            # add a scroll bar if there are too many cell types to fit on the screen
            widget_for_scroll_area = QWidget()
            widget_for_scroll_area.setLayout(vbox)
            self.cell_count_scroll_area = QScrollArea()
            self.cell_count_scroll_area.setWidget(widget_for_scroll_area)
            vbox = QVBoxLayout()
            vbox.addWidget(self.cell_count_scroll_area)

        hbox = QHBoxLayout()

        go_back_to_rename = GoBackButton(self, self.biwt)
        continue_to_cell_pos = ContinueButton(self, self.process_window)

        hbox.addWidget(go_back_to_rename)
        hbox.addWidget(continue_to_cell_pos)
        
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def setup_confluence_info(self):
        # self.compute_cell_volumes()
        volume_env = (float(self.biwt.config_tab.xmax.text()) - float(self.biwt.config_tab.xmin.text())) * (float(self.biwt.config_tab.ymax.text()) - float(self.biwt.config_tab.ymin.text()))
        self.prop_total_area_one = {}
        self.prop_dot_ratios = 0
        for idx, cell_type in enumerate(self.biwt.cell_types_list_final):
            self.prop_total_area_one[cell_type] = (((9*np.pi*self.biwt.cell_volume[cell_type]**2) / 16) ** (1./3)) / volume_env
            self.prop_dot_ratios += (self.cell_type_props[idx] * self.prop_total_area_one[cell_type])

    def prop_box_changed_cb(self, text):
        self.biwt.stale_futures = True
        if self.prop_box_callback_paused:
            return
        type_prop_sender = self.sender()
        if type_prop_sender.hasAcceptableInput() is False:
            return
        current_name = type_prop_sender.objectName()
        self.prop_box_callback_paused = True
        if current_name=="total_prop":
            mult = int(text)
            self.total_manual.setText(text)
        else:
            mult = int(text) / self.cell_type_props[int(current_name)]
            self.total_prop.setText(str(round(mult)))
            self.total_manual.setText(str(round(mult)))

        for idx, cell_type in enumerate(self.biwt.cell_types_list_final):
            if current_name==str(idx):
                continue
            self.type_prop[cell_type].setText(str(round(mult * self.cell_type_props[idx])))
            self.type_manual[cell_type].setText(str(round(mult * self.cell_type_props[idx])))
        self.prop_box_callback_paused = False

    def confluence_box_changed_cb(self, text):
        self.biwt.stale_futures = True
        if self.conf_box_callback_paused:
            return
        type_conf_sender = self.sender()
        if type_conf_sender.hasAcceptableInput() is False:
            return
        current_name = type_conf_sender.objectName()
        self.conf_box_callback_paused = True
        current_conf = float(text)
        if current_name=="total_conf":
            mult = current_conf
            mult /= self.prop_dot_ratios
        else:
            current_idx = int(current_name)
            mult = current_conf
            mult /= self.prop_total_area_one[self.biwt.cell_types_list_final[current_idx]]
            mult /= self.cell_type_props[current_idx]

        total_conf = 0
        for idx, cell_type in enumerate(self.biwt.cell_types_list_final):
            if current_name==str(idx):
                total_conf += current_conf
                continue
            new_conf = mult * self.cell_type_props[idx] * self.prop_total_area_one[cell_type]
            total_conf += new_conf
            self.type_confluence[cell_type].setText(str(new_conf))
        if current_name!="total_conf":
            self.total_conf.setText(str(total_conf))
        counts, total = self.convert_confluence_to_counts()
        for cell_type, n in counts.items():
            self.type_manual[cell_type].setText(str(n))
        self.total_manual.setText(str(total))
        
        if total_conf > 100:
            self.total_conf.setStyleSheet("QLineEdit {background-color : red; color : black;}")
        else:
            self.total_conf.setStyleSheet(self.biwt.qlineedit_style_sheet)
            
        self.conf_box_callback_paused = False
        
    def manual_box_changed_cb(self, text):
        self.biwt.stale_futures = True
        total_count = 0
        for qle in self.type_manual.values():
            if qle.hasAcceptableInput():
                total_count += int(qle.text())
        self.total_manual.setText(str(total_count))

    def counts_button_cb(self, id):
        self.biwt.stale_futures = True
        enable_props = id==1
        enable_confluence = id==2
        enable_manual = id==3

        current_values = {}

        if id==0:
            current_values = self.biwt.cell_counts
            current_total = len(self.biwt.cell_types_final)

        for qw in self.type_prop.values():
            qw.setEnabled(enable_props)
        self.total_prop.setEnabled(enable_props)
        if enable_props:
            for k, qw in self.type_prop.items():
                current_values[k] = qw.text()
            current_total = self.total_prop.text()
        
        for qw in self.type_confluence.values():
            qw.setEnabled(enable_confluence)
        self.total_conf.setEnabled(enable_confluence)
        if enable_confluence and float(self.total_conf.text()) > 100:
            self.total_conf.setStyleSheet("QLineEdit {background-color : red; color : black;}")
        else:
            self.total_conf.setStyleSheet(self.biwt.qlineedit_style_sheet)
        if enable_confluence:
            current_values, current_total = self.convert_confluence_to_counts()
        
        for qw in self.type_manual.values():
            qw.setEnabled(enable_manual)
        if not enable_manual:
            for k, qw in self.type_manual.items():
                qw.setText(str(current_values[k]))
            self.total_manual.setText(str(current_total))

    def convert_confluence_to_counts(self):
        total = 0
        counts = {}
        for cell_type in self.biwt.cell_types_list_final:
            n = round(0.01 * float(self.type_confluence[cell_type].text()) / self.prop_total_area_one[cell_type])
            counts[cell_type] = n
            total += n
        return counts, total

    def process_window(self):
        id = self.counts_button_group.checkedId()
        if id==1: # use props found in data file
            for cell_type in self.biwt.cell_types_list_final:
                self.biwt.cell_counts[cell_type] = int(self.type_prop[cell_type].text())
        elif id==2: # set by confluence
            self.biwt.cell_counts, _ = self.convert_confluence_to_counts()
        elif id==3: # manually set
            for cell_type in self.biwt.cell_types_list_final:
                self.biwt.cell_counts[cell_type] = int(self.type_manual[cell_type].text())
        self.biwt.continue_from_counts()

class BioinformaticsWalkthroughWindow_PositionsWindow(BioinformaticsWalkthroughWindow):
    def __init__(self, biwt):
        super().__init__(biwt)
        print("------Setting cell type positions------")

        self.biwt_plot_window = None
        self.create_cell_type_scroll_area()
        self.create_pos_scroll_area()

        splitter = QSplitter()
        splitter.addWidget(self.cell_type_scroll_area)
        splitter.addWidget(self.pos_scroll_area)

        vbox = QVBoxLayout()
        vbox.addWidget(splitter)

        top_area = QWidget()
        top_area.setLayout(vbox)

        splitter = QSplitter(QtCore.Qt.Vertical)
        splitter.addWidget(top_area)
        self.biwt_plot_window = BioinformaticsWalkthroughPlotWindow(self, self.biwt, self.biwt.config_tab)
        self.plot_scroll_area = QScrollArea()
        self.plot_scroll_area.setWidget(self.biwt_plot_window)
        splitter.addWidget(self.plot_scroll_area)

        vbox = QVBoxLayout()
        vbox.addWidget(splitter)

        go_back_button = GoBackButton(self, self.biwt, pre_cb=self.close_legend)
        self.continue_to_write_button = ContinueButton(self, self.process_window, styleSheet=self.biwt.qpushbutton_style_sheet)
        self.continue_to_write_button.setEnabled(False)

        hbox_write = QHBoxLayout()
        hbox_write.addWidget(go_back_button)
        hbox_write.addWidget(self.continue_to_write_button)

        vbox.addLayout(hbox_write)

        self.setLayout(vbox)
     
    def close_legend(self):
        if self.biwt_plot_window.legend_window is not None:
            self.biwt_plot_window.legend_window.close()
    
    def create_cell_type_scroll_area(self):
        vbox_main = QVBoxLayout()
        label = QLabel("Select cell type(s) to place.\nGreyed out cell types have already been placed.")
        vbox_main.addWidget(label)

        hbox_mid = QHBoxLayout()
        vbox_mid_checkboxes = QVBoxLayout()
        self.cell_type_button_group = QButtonGroup(exclusive=False)
        self.cell_type_button_group.buttonClicked.connect(self.cell_type_button_group_cb)
        self.checkbox_dict = create_checkboxes_for_cell_types(vbox_mid_checkboxes, self.biwt.cell_types_list_final)
        self.undo_button = {}
        for cbd in self.checkbox_dict.values():
            self.cell_type_button_group.addButton(cbd)
        vbox_mid_undos = QVBoxLayout()
        undo_qpushbutton_style_sheet = """
            QPushButton:enabled {
                background-color : yellow;
            }
            QPushButton:disabled {
                background-color : grey;
            }
            """
        for cell_type in self.biwt.cell_types_list_final:
            self.undo_button[cell_type] = QPushButton("Undo",enabled=False,styleSheet=undo_qpushbutton_style_sheet,objectName=cell_type)
            self.undo_button[cell_type].clicked.connect(self.undo_button_cb)
            vbox_mid_undos.addWidget(self.undo_button[cell_type])
        
        hbox_mid.addLayout(vbox_mid_checkboxes)
        hbox_mid.addLayout(vbox_mid_undos)

        vbox_main.addLayout(hbox_mid)

        self.select_all_button = QPushButton("Select remaining",styleSheet=self.biwt.qpushbutton_style_sheet)
        self.select_all_button.clicked.connect(self.select_all_button_cb)
        
        self.deselect_all_button = QPushButton("Unselect all",styleSheet=self.biwt.qpushbutton_style_sheet)
        self.deselect_all_button.clicked.connect(self.deselect_all_button_cb)
        hbox = QHBoxLayout()
        hbox.addWidget(self.select_all_button)
        hbox.addWidget(self.deselect_all_button)
        
        vbox_main.addLayout(hbox)

        self.undo_all_button = QPushButton("Undo All",enabled=False,styleSheet=undo_qpushbutton_style_sheet)
        self.undo_all_button.clicked.connect(self.undo_all_button_cb)
        vbox_main.addWidget(self.undo_all_button)

        cell_type_scroll_area_widget = QWidget()
        cell_type_scroll_area_widget.setLayout(vbox_main)

        self.cell_type_scroll_area = QScrollArea()
        self.cell_type_scroll_area.setWidget(cell_type_scroll_area_widget)
 
    def create_pos_scroll_area(self):
        self.spatial_plotter_id = None
        self.cell_pos_button_group = QButtonGroup()
        self.cell_pos_button_group.setExclusive(True)
        self.cell_pos_button_group.idToggled.connect(self.cell_pos_button_group_cb)
        next_button_id = 0
        
        button_width = 250
        button_height = 250
        icon_width = round(0.8 * button_width)
        icon_height = round(0.8 * button_height)
        master_vbox = QVBoxLayout()

        qpushbutton_style_sheet = """
            QPushButton {
                background-color : lightblue;
                color : black;
            }
            QPushButton::unchecked {
                background-color : lightblue;
            }
            QPushButton::checked {
                background-color : black;
            }
            """

        label = QLabel("Select an plotter to place the selected cell types:")
        label.setAlignment(QtCore.Qt.AlignLeft)

        master_vbox.addWidget(label)

        # grid_layout = QHBoxLayout()
        grid_layout = QGridLayout()
        rI = 0
        cI = 0
        cmax = 1
        icon_size = QtCore.QSize(icon_width, icon_height) 
            
        vbox = QVBoxLayout()
        full_rectangle_button = QPushButton(icon=QIcon(sys.path[0] + "/icon/scatter_square.svg"), iconSize=icon_size, checkable=True, checked=(not self.biwt.use_spatial_data))
        full_rectangle_button.setFixedSize(button_width,button_height)
        full_rectangle_button.setStyleSheet(qpushbutton_style_sheet) 
        self.cell_pos_button_group.addButton(full_rectangle_button,next_button_id)
        next_button_id += 1
        vbox.addWidget(full_rectangle_button)

        label = QLabel("Everywhere")
        label.setFixedWidth(button_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(label)

        grid_layout.addLayout(vbox,rI,cI,1,1)
        rI, cI = [rI,cI+1] if cI < cmax else [rI+1,0]
            
        vbox = QVBoxLayout()
        partial_rectangle_button = QPushButton(icon=QIcon(sys.path[0] + "/icon/rectangle.svg"), iconSize=icon_size, checkable=True, checked=False)
        partial_rectangle_button.setFixedSize(button_width,button_height)
        partial_rectangle_button.setStyleSheet(qpushbutton_style_sheet) 
        self.cell_pos_button_group.addButton(partial_rectangle_button,next_button_id)
        next_button_id += 1
        vbox.addWidget(partial_rectangle_button)

        label = QLabel("Rectangle")
        label.setFixedWidth(button_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(label)

        grid_layout.addLayout(vbox,rI,cI,1,1)
        rI, cI = [rI,cI+1] if cI < cmax else [rI+1,0]

        vbox = QVBoxLayout()
        disc_button = QPushButton(icon=QIcon(sys.path[0] + "/icon/disc.svg"), iconSize=icon_size, checkable=True, checked=False)
        disc_button.setFixedSize(button_width,button_height)
        disc_button.setStyleSheet(qpushbutton_style_sheet) 
        self.cell_pos_button_group.addButton(disc_button,next_button_id)
        next_button_id += 1
        vbox.addWidget(disc_button)

        label = QLabel("Disc")
        label.setFixedWidth(button_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(label)

        grid_layout.addLayout(vbox,rI,cI,1,1)
        rI, cI = [rI,cI+1] if cI < cmax else [rI+1,0]

        vbox = QVBoxLayout()
        annulus_button = QPushButton(icon=QIcon(sys.path[0] + "/icon/annulus.svg"), iconSize=icon_size, checkable=True, checked=False)
        annulus_button.setFixedSize(button_width,button_height)
        annulus_button.setStyleSheet(qpushbutton_style_sheet) 
        self.cell_pos_button_group.addButton(annulus_button,next_button_id)
        next_button_id += 1
        vbox.addWidget(annulus_button)

        label = QLabel("Annulus")
        label.setFixedWidth(button_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(label)

        grid_layout.addLayout(vbox,rI,cI,1,1)
        rI, cI = [rI,cI+1] if cI < cmax else [rI+1,0]

        vbox = QVBoxLayout()
        wedge_button = QPushButton(icon=QIcon(sys.path[0] + "/icon/wedge.svg"), iconSize=icon_size, checkable=True, checked=False)
        wedge_button.setFixedSize(button_width,button_height)
        wedge_button.setStyleSheet(qpushbutton_style_sheet) 
        self.cell_pos_button_group.addButton(wedge_button,next_button_id)
        next_button_id += 1
        vbox.addWidget(wedge_button)

        label = QLabel("Wedge")
        label.setFixedWidth(button_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(label)

        grid_layout.addLayout(vbox,rI,cI,1,1)
        rI, cI = [rI,cI+1] if cI < cmax else [rI+1,0]

        vbox = QVBoxLayout()
        rainbow_button = QPushButton(icon=QIcon(sys.path[0] + "/icon/rainbow.svg"),enabled=False, iconSize=icon_size, checkable=True, checked=False) # not ready for this yet
        rainbow_button.setFixedSize(button_width,button_height)
        rainbow_button.setStyleSheet(qpushbutton_style_sheet) 
        self.cell_pos_button_group.addButton(rainbow_button,next_button_id)
        next_button_id += 1
        vbox.addWidget(rainbow_button)

        label = QLabel("Rainbow\n(why not?!)\nWork in progess...")
        label.setFixedWidth(button_width)
        label.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(label)

        grid_layout.addLayout(vbox,rI,cI,1,1)
        rI, cI = [rI,cI+1] if cI < cmax else [rI+1,0]
        if self.biwt.use_spatial_data:
            self.spatial_plotter_id = next_button_id
            vbox = QVBoxLayout()
            spatial_button = QPushButton(icon=QIcon(sys.path[0] + "/icon/spatial.png"), enabled=True, checkable=True, iconSize=icon_size)
            spatial_button.setFixedSize(button_width,button_height)
            spatial_button.setStyleSheet(qpushbutton_style_sheet) 
            spatial_button.toggled.connect(self.spatial_button_cb)
            spatial_button.setChecked(True)
            self.cell_pos_button_group.addButton(spatial_button,next_button_id)
            next_button_id += 1
            vbox.addWidget(spatial_button)

            label = QLabel("Spatial Plotter")
            label.setFixedWidth(button_width)
            label.setAlignment(QtCore.Qt.AlignCenter)
            vbox.addWidget(label)

            grid_layout.addLayout(vbox,rI,cI,1,1)
            rI, cI = [rI,cI+1] if cI < cmax else [rI+1,0]

        master_vbox.addLayout(grid_layout)

        pos_scroll_area_widget = QWidget()
        pos_scroll_area_widget.setLayout(master_vbox)

        self.pos_scroll_area = QScrollArea()
        self.pos_scroll_area.setWidget(pos_scroll_area_widget)

    def cell_pos_button_group_cb(self):
        if self.biwt_plot_window:
            self.biwt_plot_window.sync_par_area()
        if self.biwt.use_spatial_data:
            self.biwt_plot_window.num_box.setEnabled(self.cell_pos_button_group.checkedId()==6) # only enable for spatial plotter
         
    def spatial_button_cb(self, checked):
        if not checked:
            return
        for cbd in self.checkbox_dict.values():
            if cbd.isEnabled():
                cbd.setChecked(True)

    def is_any_cell_type_button_group_checked(self):
        bval = self.cell_type_button_group.checkedButton() is not None
        return bval

    def cell_type_button_group_cb(self):
        bval = self.is_any_cell_type_button_group_checked()
        if bval:
            # The plot is created and at least one is checked. See if the parameters are ready
            self.biwt_plot_window.sync_par_area() # this call is overkill, I just want to see if the parameters call for the Plot button being enabled
        else:
            self.biwt_plot_window.plot_cells_button.setEnabled(False)

    def select_all_button_cb(self):
        for cbd in self.checkbox_dict.values():
            if cbd.isEnabled():
                cbd.setChecked(True)
        bval = self.is_any_cell_type_button_group_checked()
        if self.biwt_plot_window:
            self.biwt_plot_window.plot_cells_button.setEnabled(bval)
    
    def deselect_all_button_cb(self):
        for cbd in self.checkbox_dict.values():
            if cbd.isEnabled():
                cbd.setChecked(False)
        if self.biwt_plot_window:
            self.biwt_plot_window.plot_cells_button.setEnabled(False)

    def undo_button_cb(self):
        undone_cell_type = self.sender().objectName()
        self.undo_cell_type(undone_cell_type)
        self.replot_all_cells_after_undo()

    def undo_cell_type(self, undone_cell_type, undo_all_flag=False):
        self.biwt.csv_array[undone_cell_type] = np.empty((0,3))
        self.checkbox_dict[undone_cell_type].setEnabled(True)
        self.checkbox_dict[undone_cell_type].setChecked(False)
        self.undo_button[undone_cell_type].setEnabled(False)
        if undo_all_flag:
            return # if undo all was clicked, don't bother checking this
        for cell_type in self.biwt.csv_array.keys():
            if self.biwt.csv_array[cell_type].shape[0] > 0:
                return
        # if we get here, then all cell types have been removed, turn off undo all
        self.undo_all_button.setEnabled(False)

    def replot_all_cells_after_undo(self):
        self.biwt_plot_window.ax0.cla()
        self.biwt_plot_window.format_axis()
        self.biwt_plot_window.legend_artists = []
        self.biwt_plot_window.legend_labels = []
        for cell_type in self.biwt.csv_array.keys():
            if self.biwt.csv_array[cell_type].shape[0] == 0:
                continue # do not plot cell types with no cells
            if self.biwt_plot_window.plot_is_2d:
                sz = np.sqrt(self.biwt_plot_window.cell_type_micron2_area_dict[cell_type] / np.pi)
                self.biwt_plot_window.circles(self.biwt.csv_array[cell_type], s=sz, color=self.biwt_plot_window.color_by_celltype[cell_type], edgecolor='black', linewidth=0.5, alpha=self.biwt_plot_window.alpha_value)
                legend_patch = Patch(facecolor=self.biwt_plot_window.color_by_celltype[cell_type], edgecolor='black', linewidth=0.5)
                self.biwt_plot_window.legend_artists.append(legend_patch)
            else:
                # sz = self.biwt_plot_window.cell_type_pt_area_dict[cell_type]
                collections = self.biwt_plot_window.ax0.scatter(self.biwt.csv_array[cell_type][:,0],self.biwt.csv_array[cell_type][:,1],self.biwt.csv_array[cell_type][:,2], s=8.0, color=self.biwt_plot_window.color_by_celltype[cell_type], alpha=self.biwt_plot_window.alpha_value)
                scatter_objects, _ = collections.legend_elements()
                self.biwt_plot_window.legend_artists.append(scatter_objects[0])
            self.biwt_plot_window.legend_labels.append(cell_type)

        self.biwt_plot_window.update_legend_window()
        self.biwt_plot_window.sync_par_area() # easy way to redraw the patch for current plotting
        
        self.continue_to_write_button.setEnabled(False)

    def undo_all_button_cb(self):
        for cell_type in self.biwt.csv_array.keys():
            self.undo_cell_type(cell_type, undo_all_flag=True)
        self.replot_all_cells_after_undo()
        self.undo_all_button.setEnabled(False)

    def process_window(self):
        if self.biwt_plot_window.legend_window is not None:
            self.biwt_plot_window.legend_window.close()
        self.biwt.continue_from_positions()
        
class BioinformaticsWalkthroughWindow_WritePositions(BioinformaticsWalkthroughWindow):
    def __init__(self, biwt):
        super().__init__(biwt)

        print("------Writing cell positions to file------")

        vbox = QVBoxLayout()
        
        label = QLabel("Confirm output file and then overwrite or append with these cell positions.")
        vbox.addWidget(label)
        
        folder_label = QLabel("folder")
        self.csv_folder = QLineEdit(self.biwt.csv_folder.text())
        file_label = QLabel("file")
        self.csv_file = QLineEdit(self.biwt.csv_file.text())

        hbox = QHBoxLayout()
        hbox.addWidget(folder_label)
        hbox.addWidget(self.csv_folder)
        hbox.addWidget(file_label)
        hbox.addWidget(self.csv_file)

        vbox.addLayout(hbox)

        self.finish_write_button = QPushButton("Overwrite")
        self.finish_write_button.setStyleSheet("QPushButton {background-color : yellow; font-weight : bold;}")
        self.finish_write_button.clicked.connect(self.finish_write_button_cb)

        self.finish_append_button = QPushButton("Append")
        self.finish_append_button.setStyleSheet("QPushButton {background-color : yellow; font-weight : bold;}")
        self.finish_append_button.clicked.connect(self.finish_append_button_cb)

        hbox = QHBoxLayout()
        hbox.addWidget(self.finish_write_button)
        hbox.addWidget(self.finish_append_button)

        vbox.addLayout(hbox)

        vbox.addWidget(QHLine())

        hbox = QHBoxLayout()
        hbox.addWidget(GoBackButton(self, self.biwt))
        hbox.addWidget(ContinueButton(self, self.process_window, text="Finish"))

        vbox.addLayout(hbox)
        self.setLayout(vbox)

    def finish_write_button_cb(self):
        self.check_for_new_celldefs()
        self.set_file_name()
        with open(self.full_fname, 'w') as f:
            f.write('x,y,z,type\n')
        self.add_cell_positions_to_file()

    def finish_append_button_cb(self):
        self.check_for_new_celldefs()
        self.set_file_name()
        with open(self.full_fname, 'r') as f:
            first_line = f.readline()
            if "x,y,z,type" not in first_line:
                print(f"{self.full_fname} is not properly formatted for appending.\nIt needs to start with 'x,y,z,type,...'")
                return
        self.add_cell_positions_to_file()

    def check_for_new_celldefs(self):
        for cell_type in self.biwt.cell_types_list_final:
            if cell_type in self.biwt.celldef_tab.celltypes_list:
                print(f"BioinformaticsWalkthroughPlotWindow: {cell_type} found in current list of cell types. Not appending {cell_type}...")
            else:
                print(f"BioinformaticsWalkthroughPlotWindow: {cell_type} not found in current list of cell types. Appending {cell_type}...")
                self.biwt.celldef_tab.new_cell_def_named(cell_type)
                self.biwt.ics_tab.update_colors_list()

    def set_file_name(self):
        dir_name = self.csv_folder.text()
        if len(dir_name) > 0 and not os.path.isdir(dir_name):
            os.makedirs(dir_name)
            time.sleep(1)
        self.full_fname = os.path.join(dir_name,self.csv_file.text())
        Path(self.full_fname).touch() # make sure the file exists
        print("save_cb(): self.full_fname=",self.full_fname)
        self.biwt.csv_folder.setText(dir_name)
        self.biwt.csv_file.setText(self.csv_file.text())
        self.biwt.full_fname = self.full_fname

    def add_cell_positions_to_file(self):
        with open(self.full_fname, 'a') as f:
            for cell_type in self.biwt.csv_array.keys():
                for pos in self.biwt.csv_array[cell_type]:
                    f.write(f'{pos[0]},{pos[1]},{pos[2]},{cell_type}\n')

    def process_window(self):
        self.biwt.full_fname = self.full_fname
        self.biwt.close_up()

class BioinformaticsWalkthroughPlotWindow(QWidget):
    def __init__(self, positions_window, biwt, config_tab):
        super().__init__()
        self.pw = positions_window
        self.biwt = biwt
        self.config_tab = config_tab

        self.setup_system_keys()

        self.preview_patch = None
        self.biwt.csv_array = {}
        for cell_type in self.biwt.cell_types_list_final:
            self.biwt.csv_array[cell_type] = np.empty((0,3))

        self.alpha_value = 1.0
        value = ['gray','red','yellow','green','blue','magenta','orange','lime','cyan','hotpink','peachpuff','darkseagreen','lightskyblue']
        if len(self.biwt.cell_types_list_final) <= len(value):
            value = value[0:len(self.biwt.cell_types_list_final)]
        else:
            value = [value[idx % len(value)] for idx in range(len(self.biwt.cell_types_list_final))]
        self.color_by_celltype = dict(zip(self.biwt.cell_types_list_final, value))

        self.plot_xmin = float(self.config_tab.xmin.text())
        self.plot_xmax = float(self.config_tab.xmax.text())
        self.plot_dx = self.plot_xmax - self.plot_xmin
        self.plot_ymin = float(self.config_tab.ymin.text())
        self.plot_ymax = float(self.config_tab.ymax.text())
        self.plot_dy = self.plot_ymax - self.plot_ymin
        self.plot_zmin = float(self.config_tab.zmin.text())
        self.plot_zmax = float(self.config_tab.zmax.text())
        self.plot_zdel = float(self.config_tab.zdel.text())
        self.plot_dz = self.plot_zmax - self.plot_zmin

        self.plot_is_2d = self.plot_zmax - self. plot_zmin <= self.plot_zdel # if the domain height is larger than the voxel height, then we have a 3d simulation

        self.create_patch_history()

        vbox = QVBoxLayout()
       
        grid_layout = self.create_par_area()

        hbox = QHBoxLayout()

        vbox_left = QVBoxLayout()
        vbox_left.addLayout(grid_layout)
        if self.biwt.use_spatial_data:
            vbox_left.addLayout(self.create_spot_num_box())
        self.mouse_keyboard_label = QLabel(f"""
                        Draw with mouse and keyboard:\
                        <html><ul>\
                        <li>Click: set (x0,y0)</li>\
                        <li>{self.shift_key_ucode}-click: set (w,h), r, or r1</li>\
                        <li>{self.ctrl_key_ucode}-click: set r0</li>\
                        <li>{self.alt_and_ctrl}-click: set \u03b81</li>\
                        <li>{self.alt_and_shift}-click: set \u03b82</li>\
                        <li>{self.alt_key_ucode}-click-and-drag: set (\u03b81,\u03b82)</li>\
                        </ul></html>
                        Notes:\
                        <html><ul>\
                        <li>Focus on the plot is necessary for these hotkeys to work!</li>\
                        <li>{self.cmd_z_str}: undo with this plotter</li>\
                        <li>{self.cmd_shift_z_str}: redo with this plotter</li>\
                        </ul></html>
                        """
                        )
        self.mouse_keyboard_label.setStyleSheet("QLabel:enabled {color : black;} QLabel:disabled {color : rgb(150,150,150);} ")

        self.plot_cells_button = QPushButton("Plot", enabled=True)
        self.plot_cells_button.setStyleSheet(self.biwt.qpushbutton_style_sheet)
        self.plot_cells_button.clicked.connect(self.plot_cell_pos)

        self.show_legend_button = QPushButton("Show Legend")
        self.show_legend_button.setStyleSheet(self.biwt.qpushbutton_style_sheet)
        self.show_legend_button.clicked.connect(self.show_legend_button_cb)

        vbox_left.addWidget(self.plot_cells_button)
        vbox_left.addWidget(self.show_legend_button)
        vbox_left.addWidget(self.mouse_keyboard_label)
        vbox_left.addStretch(1)

        self.create_figure()

        hbox.addLayout(vbox_left)

        vbox_right = QVBoxLayout()
        vbox_right.addWidget(self.canvas)

        vbox_right.addWidget(self.canvas)

        hbox.addLayout(vbox_right)
        
        vbox.addLayout(hbox)
        
        self.sync_par_area()

        self.setLayout(vbox)
        self.setFocusPolicy( QtCore.Qt.ClickFocus )
        self.setFocus()

    def create_spot_num_box(self):
        label = QLabel("Num cells per spot:")
        self.num_box = QSpinBox(minimum=1, maximum=10000000, singleStep=1,value=1)
        self.num_box.valueChanged.connect(self.num_box_cb)
        self.num_box.setValue(1)
        self.num_box.setStyleSheet("QSpinBox {color : black; background-color : white} QSpinBox:disabled {background-color : lightgray;}")
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(label)
        hbox.addWidget(self.num_box)
        return hbox

    def num_box_cb(self, v):
        print("------num box changed-------")
        self.scatter_sizes = v * self.single_scatter_sizes
        self.preview_patch.set_sizes(self.scatter_sizes)
        
        self.current_plotter()
        pass

    def default_spatial_pars(self):
        if not self.biwt.use_spatial_data:
            return
        # self.biwt.spatial_data_final[:,0] += self.biwt.spatial_data_final[:,1] # for testing
        # self.biwt.spatial_data_final = np.array([0.5,0.5]).reshape((1,2)) # for testing
        x = self.biwt.spatial_data_final[:,0]
        y = self.biwt.spatial_data_final[:,1]
        if len(x) > 1: # I know, right, what ST data set will have one spot??
            xL = np.min(x)
            xR = np.max(x)
            yL = np.min(y)
            yR = np.max(y)
        else:
            print("Single ST spot?")
            xL, xR = x[0] + [-0.5,0.5]
            yL, yR = y[0] + [-0.5,0.5]

        spatial_factors = [self.plot_dx / (xR-xL),self.plot_dy / (yR-yL)] # factors for scaling each dimension to an interval of length 1
        if not self.plot_is_2d:
            z = self.biwt.spatial_data_final[:,2]
            zL = np.min(z) if len(x) > 1 else z[0] - 0.5
            zR = np.max(z) if len(x) > 1 else z[0] + 0.5
            spatial_factors.append(self.plot_dz / (zR-zL))

        spatial_factor = min(spatial_factors)
        width = (xR-xL)*spatial_factor
        height = (yR-yL)*spatial_factor
        x0 = 0.5*(self.plot_xmin+self.plot_xmax - width)
        y0 = 0.5*(self.plot_ymin+self.plot_ymax - height)

        self.spatial_base_coords = self.biwt.spatial_data_final[:,0:2] - [xL,yL]
        self.spatial_base_coords = self.spatial_base_coords / [xR-xL,yR-yL]

        if self.plot_is_2d:
            return [x0, y0, width, height]
        
        print(f"xL={xL}, xR={xR}, yL={yL}, yR={yR}, zL={zL}, zR={zR}")
        print(f"spatial_factors = {spatial_factors}, spatial_factor = {spatial_factor}\n\n\n")
        self.spatial_base_coords = np.hstack((self.spatial_base_coords, (self.biwt.spatial_data_final[:,2].reshape((-1,1)) - zL)/(zR-zL)))
        depth = (zR-zL)*spatial_factor
        z0 = 0.5*(self.plot_zmin+self.plot_zmax - depth)

        return [x0, y0, z0, width, height, depth]

        # self.spatial_base_coords = np.array([0.5,0.5])

    def setup_system_keys(self):
        is_windows_os = os.name == "nt"
        if is_windows_os:
            self.alt_key_str = "Alt"
            # self.alt_key_ucode = "\u2387"
            self.alt_key_ucode = "Alt" # the ucode for windows alt key is ugly/non-existent. just use "Alt" instead"
            self.ctrl_key_ucode = "Ctrl"
            self.cmd_z_str = "Ctrl-z"
            self.cmd_shift_z_str = "Ctrl-shift-z"
            self.alt_and_ctrl = "Alt-ctrl"
            self.alt_and_shift = "Alt-shift"
            self.shift_key_ucode = "Shift"
            self.lower_par_key_modifier = QtCore.Qt.MetaModifier
        else:
            self.alt_key_str = "Opt"
            self.alt_key_ucode = "\u2325"
            self.ctrl_key_ucode = "\u2303"
            self.cmd_z_str = "\u2318Z"
            self.cmd_shift_z_str = "\u21e7\u2318Z"
            self.alt_and_ctrl = "\u2325\u2303"
            self.alt_and_shift = "\u2325\u21e7"
            self.shift_key_ucode = "\u21e7"
            self.lower_par_key_modifier = QtCore.Qt.MetaModifier

    def show_legend_button_cb(self):
        self.legend_window.show()

    def create_patch_history(self):
        self.patch_history = []
        self.patch_history_idx = []
        self.patch_history.append([])
        self.patch_history.append([self.default_rectangle_pars()])
        self.patch_history.append([self.default_disc_pars()])
        self.patch_history.append([self.default_annulus_pars()])
        self.patch_history.append([self.default_wedge_pars()])
        self.patch_history.append([self.default_wedge_pars()]) # rainbow
        self.patch_history.append([self.default_spatial_pars()]) # spatial
        self.patch_history_idx = len(self.patch_history) * [0]

    def enterEvent(self, event):
        # set focus on this as soon as the cursor enters this region
        self.canvas.setFocus()

    def create_par_area(self):
        par_label_width = 50
        par_text_width = 75
        self.par_label = []
        self.par_text = []
        grid_layout = QGridLayout()
        rI = 0
        cI = 0
        cmax = 2 
        if self.plot_is_2d:
            for i in range(6):
                hbox = QHBoxLayout()
                self.par_label.append(QLabel())
                self.par_label[i].setAlignment(QtCore.Qt.AlignRight)
                self.par_label[i].setFixedWidth(par_label_width)
                self.par_text.append(QLineEdit())
                self.par_text[i].setFixedWidth(par_text_width)
                self.par_text[i].setStyleSheet(self.biwt.qlineedit_style_sheet)
                self.par_text[i].editingFinished.connect(self.par_editing_finished)

                hbox.addWidget(self.par_label[i])
                hbox.addWidget(self.par_text[i])
                grid_layout.addLayout(hbox,rI,cI)
                rI, cI = [rI,cI+1] if cI < cmax else [rI+1,0]


            coord_validator = QtGui.QDoubleValidator()
            self.par_text[0].setValidator(coord_validator)
            self.par_text[1].setValidator(coord_validator)
            self.par_text[4].setValidator(coord_validator) # theta 1
            self.par_text[5].setValidator(coord_validator) # theta 2
            pos_par_validator = QtGui.QDoubleValidator()
            pos_par_validator.setBottom(0)
            for i in range(2,4):
                self.par_text[i].setValidator(pos_par_validator)
        else: # 3d plotting pars
            for i in range(9):
                hbox = QHBoxLayout()
                self.par_label.append(QLabel())
                self.par_label[i].setAlignment(QtCore.Qt.AlignRight)
                self.par_label[i].setFixedWidth(par_label_width)
                self.par_text.append(QLineEdit())
                self.par_text[i].setFixedWidth(par_text_width)
                self.par_text[i].setStyleSheet(self.biwt.qlineedit_style_sheet)
                self.par_text[i].editingFinished.connect(self.par_editing_finished)

                hbox.addWidget(self.par_label[i])
                hbox.addWidget(self.par_text[i])
                grid_layout.addLayout(hbox,rI,cI)
                rI, cI = [rI,cI+1] if cI < cmax else [rI+1,0]


            coord_validator = QtGui.QDoubleValidator()
            self.par_text[0].setValidator(coord_validator)
            self.par_text[1].setValidator(coord_validator)
            self.par_text[2].setValidator(coord_validator)
            self.par_text[6].setValidator(coord_validator) # theta 1
            self.par_text[7].setValidator(coord_validator) # theta 2
            self.par_text[8].setValidator(coord_validator) # theta 2
            pos_par_validator = QtGui.QDoubleValidator()
            pos_par_validator.setBottom(0)
            for i in range(3,6):
                self.par_text[i].setValidator(pos_par_validator)

        return grid_layout
    
    def get_current_pars(self):
        return self.current_pars
    
    def par_editing_finished(self, reset_cursor = True):
        self.read_par_texts()
        if self.current_pars_acceptable:
            self.append_to_history()
        if reset_cursor:
            self.sender().setCursorPosition(0)

    def append_to_history(self):
        id = self.pw.cell_pos_button_group.checkedId()
        if self.patch_history_idx[id] < len(self.patch_history[id])-1:
            # then we are in the middle of the history, delete the future events from here on
            del self.patch_history[id][self.patch_history_idx[id]+1:]
        self.patch_history[id].append(self.get_current_pars())
        self.patch_history_idx[id] += 1

    def sync_par_area(self):
        if self.preview_patch is not None:
            self.preview_patch.remove()
            self.canvas.update()
            self.canvas.draw()
            self.preview_patch = None

        for cid in self.mpl_cid:
            self.canvas.mpl_disconnect(cid) # might throw error if none exist...
        self.mpl_cid = []

        id = self.pw.cell_pos_button_group.checkedId()
        if id==0:
            for pt in self.par_text:
                pt.setEnabled(False)
            for pl in self.par_label:
                pl.setText("")
            self.current_plotter = self.everywhere_plotter
        
        else: # set callbacks common to all
            self.mpl_cid.append(self.canvas.mpl_connect("button_release_event", self.mouse_released_cb)) # only appending to history on release; the motion doesn't add to history because it holds focus and so editingFinished signal not emitted while canvas holds focus
            if id==1:
                self.par_label[0].setText("x0")
                self.par_label[1].setText("y0")
                self.par_label[2].setText("width")
                self.par_label[3].setText("height")
                self.mpl_cid.append(self.canvas.mpl_connect("button_press_event", self.rectangle_mouse_press))
                self.mpl_cid.append(self.canvas.mpl_connect("motion_notify_event", self.rectangle_mouse_motion))
                self.current_plotter = self.rectangle_plotter

            elif id==2:
                self.par_label[0].setText("x0")
                self.par_label[1].setText("y0")
                self.par_label[2].setText("r")
                self.mpl_cid.append(self.canvas.mpl_connect("button_press_event", self.disc_mouse_press))
                self.mpl_cid.append(self.canvas.mpl_connect("motion_notify_event", self.disc_mouse_motion))
                self.current_plotter = self.disc_plotter

            elif id==3:
                self.par_label[0].setText("x0")
                self.par_label[1].setText("y0")
                self.par_label[2].setText("r0")
                self.par_label[3].setText("r1")
                self.mpl_cid.append(self.canvas.mpl_connect("button_press_event", self.annulus_mouse_press))
                self.mpl_cid.append(self.canvas.mpl_connect("motion_notify_event", self.annulus_mouse_motion))
                self.current_plotter = self.annulus_plotter

            elif id==4:
                self.par_label[0].setText("x0")
                self.par_label[1].setText("y0")
                self.par_label[2].setText("r0")
                self.par_label[3].setText("r1")
                self.par_label[4].setText("\u03b81 (\u00b0)")
                self.par_label[5].setText("\u03b82 (\u00b0)")
                self.mpl_cid.append(self.canvas.mpl_connect("button_press_event", self.wedge_mouse_press))
                self.mpl_cid.append(self.canvas.mpl_connect("motion_notify_event", self.wedge_mouse_motion))
                self.current_plotter = self.wedge_plotter

            elif id==5:
                self.par_label[0].setText("x0")
                self.par_label[1].setText("y0")
                self.par_label[2].setText("r0")
                self.par_label[3].setText("r1")
                self.par_label[4].setText("\u03b81 (\u00b0)")
                self.par_label[5].setText("\u03b82 (\u00b0)")
                self.current_plotter = self.wedge_plotter
        
            elif id==6:
                self.par_label[0].setText("x0")
                self.par_label[1].setText("y0")
                if self.plot_is_2d:
                    self.par_label[2].setText("width")
                    self.par_label[3].setText("height")
                else:
                    self.par_label[2].setText("z0")
                    self.par_label[3].setText("width")
                    self.par_label[4].setText("height")
                    self.par_label[5].setText("depth")
                self.mpl_cid.append(self.canvas.mpl_connect("button_press_event", self.rectangle_mouse_press))
                self.mpl_cid.append(self.canvas.mpl_connect("motion_notify_event", self.rectangle_mouse_motion))
                self.current_plotter = self.spatial_plotter

            self.activate_par_texts(id, self.current_plotter)
        self.current_plotter()
    
    def activate_par_texts(self, id, plotter):
        pars = self.patch_history[id][self.patch_history_idx[id]]
        for idx, pt in enumerate(self.par_text):
            enabled = idx < len(pars)
            pt.setEnabled(enabled)
            if enabled:
                try:
                    pt.textChanged.disconnect()
                except:
                    pass
                pt.textChanged.connect(plotter)
        for i in range(len(pars),len(self.par_label)):
            self.par_label[i].setText("")
        self.load_previous_patch_pars(pars)

    def load_previous_patch_pars(self, pars):
        for idx, pt in enumerate(self.par_text):
            if idx == len(pars):
                return
            pt.setText(str(pars[idx]))

    def everywhere_plotter(self):
        if self.plot_is_2d:
            if self.preview_patch is None:
                self.preview_patch = self.ax0.add_patch(Rectangle((self.plot_xmin,self.plot_ymin),self.plot_dx,self.plot_dy,alpha=0.2))
            else:
                self.preview_patch.set_bounds(self.plot_xmin,self.plot_ymin,self.plot_dx,self.plot_dy)
        else:
            faces = rectangular_prism_faces(self.plot_xmin,self.plot_xmax,self.plot_ymin,self.plot_ymax,self.plot_zmin,self.plot_zmax)
            self.preview_patch = self.ax0.add_collection3d(Poly3DCollection(faces, alpha=0.2, facecolors='gray', linewidths=1, edgecolors='black'))
        self.plot_cells_button.setEnabled(self.pw.is_any_cell_type_button_group_checked())

        self.canvas.update()
        self.canvas.draw()

    def get_x0y0(self):
        return float(self.par_text[0].text()), float(self.par_text[1].text())
        
    def set_x0y0(self, event):
        self.assign_par(event.xdata,0)
        self.assign_par(event.ydata,1)

    def mouse_released_cb(self, event):
        if self.mouse_pressed:
            self.par_editing_finished(reset_cursor=False)
        self.mouse_pressed = False
    
    def assign_par(self, value, idx):
        # print(f"par text updated for {idx}")
        self.par_text[idx].setText(str(value))
        self.par_text[idx].setCursorPosition(0)

    def rectangle_mouse_press(self, event):
        self.mouse_pressed = self.standard_mouse_press(event, self.rectangle_helper)

    def standard_mouse_press(self, event, fn_on_shift, modifiers = None):
        if event.inaxes is None:
            return False
        if modifiers is None:
            modifiers = QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            x0y0 = self.get_x0y0()
            self.updater = lambda e : fn_on_shift(e, *x0y0)
        elif modifiers==QtCore.Qt.NoModifier:
            self.updater = lambda e : self.set_x0y0(e)
        else:
            return False
        self.updater(event)
        return True

    def rectangle_mouse_motion(self, event):
        if (event.inaxes is None) or (self.mouse_pressed is False):
            return
        self.updater(event)
 
    def rectangle_helper(self, event, xL, yL):
        xR = event.xdata
        yR = event.ydata
        self.assign_par(np.min([xL,xR]),0)
        self.assign_par(np.min([yL,yR]),1)
        self.assign_par(abs(xR-xL),2)
        self.assign_par(abs(yR-yL),3)

    def default_rectangle_pars(self):
        x0y0 = self.default_x0y0()
        return [*x0y0,*self.default_wh(x0y0 = x0y0)]
    
    def default_x0y0(self):
        return (0.5*(self.plot_xmin+self.plot_xmax),0.5*(self.plot_ymin+self.plot_ymax))
            
    def default_wh(self, x0y0 = None,factor = 0.5):
        if x0y0 is None:
            x0y0 = self.default_x0y0()
        x0, y0 = x0y0
        dL = abs(self.plot_xmin-x0)
        dR = abs(self.plot_xmax-x0)
        if dL > dR:
            w = factor * dL
            x0 -= w
            self.assign_par(x0, 0)
        else:
            w = factor * dR

        dL = abs(self.plot_ymin-y0)
        dR = abs(self.plot_ymax-y0)
        if dL > dR:
            h = factor * dL
            y0 -= h
            self.assign_par(y0, 1)
        else:
            h = factor * dR
        return (w,h)

    def disc_mouse_press(self, event):
        self.mouse_pressed = self.standard_mouse_press(event, lambda e, x0, y0 : self.set_radius_helper(e, x0, y0, 2))

    def disc_mouse_motion(self, event):
        if (event.inaxes is None) or (self.mouse_pressed is False):
            return
        self.updater(event)
    
    def default_disc_pars(self):
        x0y0 = self.default_x0y0()
        return [*x0y0,self.default_radius()]
       
    def default_radius(self, x0y0 = None, factor = 0.9):
        if x0y0 is None:
            x0y0 = self.default_x0y0()
        x0, y0 = x0y0
        return factor * np.min(np.abs([self.plot_xmax-x0,self.plot_xmin-x0,self.plot_ymax-y0,self.plot_ymin-y0]))
            
    def annulus_mouse_press(self, event):
        if event.inaxes is None:
            self.mouse_pressed = False
            return # then mouse is not over axes, move on
        self.annulus_mouse_setup(event, QApplication.keyboardModifiers())

    def annulus_mouse_setup(self, event, modifiers):
        if modifiers == QtCore.Qt.NoModifier:
            self.updater = lambda e : self.set_x0y0(e)
        else:
            if modifiers == QtCore.Qt.ShiftModifier:
                r0 = float(self.par_text[2].text())
            elif modifiers == self.lower_par_key_modifier:
                r0 = float(self.par_text[3].text())
            else:
                self.mouse_pressed = False
                return
            x0y0 = self.get_x0y0()
            self.updater = lambda e : self.radii_motion_helper(e, *x0y0, r0)
        self.mouse_pressed = True
        self.updater(event)

    def annulus_mouse_motion(self, event):
        if (event.inaxes is None) or (self.mouse_pressed is False):
            return
        self.updater(event)

    def default_annulus_pars(self):
        x0, y0, r1 = self.default_disc_pars()
        return [x0, y0, self.default_radius(factor=0.5), r1]

    def compute_radius(self,event, x0, y0):
        x1 = event.xdata
        y1 = event.ydata
        return np.sqrt((x1-x0)**2 + (y1-y0)**2)

    def radii_motion_helper(self, event, x0, y0, r0):
        r1 = self.compute_radius(event, x0, y0)
        r0, r1 = [r0,r1] if r0 < r1 else [r1,r0]
        self.assign_par(r0, 2)
        self.assign_par(r1, 3)

    def set_radius_helper(self, event, x0, y0, idx):
        r = self.compute_radius(event, x0, y0)
        if r is None: # then left axes or something to cause this
            return
        self.assign_par(r, idx)
        return r

    def wedge_mouse_press(self, event):
        if event.inaxes is None:
            self.mouse_pressed = False
            return # then mouse is not over axes, move on
        modifiers = QApplication.keyboardModifiers()
        x0y0 = self.get_x0y0()
        if modifiers == QtCore.Qt.AltModifier: # option-click
            theta = self.get_angle(event, *x0y0)
            self.assign_par(theta, 4) # in this case, fix theta1 and then let theta2 vary
            idx = 5
        elif modifiers == (QtCore.Qt.AltModifier | QtCore.Qt.MetaModifier): # option-ctrl-click
            idx = 4
        elif modifiers == (QtCore.Qt.AltModifier | QtCore.Qt.ShiftModifier): # option-shift-click
            idx = 5
        else:
            self.annulus_mouse_setup(event, modifiers)
            return
        self.mouse_pressed = True
        self.updater = lambda e : self.assign_par(self.get_angle(e, *x0y0), idx)
        self.updater(event)

    def wedge_mouse_motion(self, event):
        if (event.inaxes is None) or (self.mouse_pressed is False):
            return
        self.updater(event)

    def default_wedge_pars(self):
        return [*self.default_annulus_pars(),"0","270"]
        
    def get_angle(self, event, x0, y0):
        x1 = event.xdata
        y1 = event.ydata
        return 57.295779513082323 * np.arctan2(y1-y0,x1-x0) # convert to degrees

    def rectangle_plotter(self):
        if self.plot_is_2d:
            self.read_par_texts()
            if not self.current_pars_acceptable:
                return
            x0, y0, width, height = self.current_pars
            if self.preview_patch is None:
                self.preview_patch = self.ax0.add_patch(Rectangle((x0,y0),width,height,alpha=0.2))
            else:
                self.preview_patch.set_bounds(x0,y0,width,height)

        # check left edge of rect is left of right edge of domain, right edge of rect is right of left edge of domain (similar in y direction)
        bval = (x0 < self.plot_xmax) and (x0+width > self.plot_xmin) and (y0 < self.plot_ymax) and (y0+height > self.plot_ymin) # make sure the rectangle intersects the domain with positive area
        if not self.plot_is_2d: # FIX (this will need a fix once we have 3d plotting fully implemented)
            z0 = self.plot_zmin
            depth = self.plot_zmax - self.plot_zmin
            bval = bval and (z0 < self.plot_zmax) and (z0+depth > self.plot_zmin)

        self.plot_cells_button.setEnabled(bval and self.pw.is_any_cell_type_button_group_checked())

        self.canvas.update()
        self.canvas.draw()

    def disc_plotter(self):
        if self.plot_is_2d:
            self.read_par_texts()
            if not self.current_pars_acceptable:
                return
            x0, y0, r = self.current_pars
            if self.preview_patch is None:
                self.preview_patch = self.ax0.add_patch(Circle((x0,y0),r,alpha=0.2))
            else:
                self.preview_patch.set(center=(x0,y0),radius=r)

            # check the disc intersects the domain in non-trivial manner
            r2 = self.get_distance2_to_domain(x0, y0)[0]
        bval = r2 < r*r # make sure the distance from center of Circle to domain is less than radius of circle
        if not self.plot_is_2d: # FIX (this will need a fix once we have 3d plotting fully implemented)
            z0 = self.plot_zmin
            depth = self.plot_zmax - self.plot_zmin
            bval = bval and (z0 < self.plot_zmax) and (z0+depth > self.plot_zmin)

        self.plot_cells_button.setEnabled(bval and self.pw.is_any_cell_type_button_group_checked())

        self.canvas.update()
        self.canvas.draw()

    def get_distance2_to_domain(self, x0, y0):
        if x0 < self.plot_xmin:
            dx = x0 - self.plot_xmin # negative
        elif x0 <= self.plot_xmax:
            dx = 0
        else:
            dx = x0 - self.plot_xmax # positive

        if y0 < self.plot_ymin:
            dy = y0 - self.plot_ymin # negative
        elif y0 <= self.plot_ymax:
            dy = 0
        else:
            dy = y0 - self.plot_ymax # positive
        return dx*dx + dy*dy, dx, dy
    
    def annulus_plotter(self):
        if self.plot_is_2d:
            self.read_par_texts()
            if not self.current_pars_acceptable:
                return
            x0, y0, r0, r1 = self.current_pars
            if r1==0 or (r1 < r0):
                if self.preview_patch: # probably a way to impose this using validators, but that would require dynamically updating the validators...
                    self.preview_patch.remove()
                    self.canvas.update()
                    self.canvas.draw()
                    self.preview_patch = None
                self.plot_cells_button.setEnabled(False)
                return
            
            r2 = self.get_distance2_to_domain(x0,y0)[0]
            cr2 = self.get_circumscribing_radius(x0, y0)
            # outer_radius_reaches_domain = r2 < r1*r1
            # inner_radius_does_not_contain_entire_domain = cr2 > r0*r0

            width = r1-r0
            try:
                self.annulus_setter(x0,y0,r1,width)
            except:
                # my PR to matplotlib should resolve the need for this check!
                # if width==r1: # hack to address the bug in matplotlib.patches.Annulus which checks if width < r0 rather than <= r0 as the error message suggests it does
                #     width *= 1 - np.finfo(width).eps # reduce width by the littlest bit possible to make sure this bug doesn't hit
                print("\tBIWT WARNING: You likely can use an update to matplotlib to fix a bug in their Annulus plots.\n\tWe'll take care of it for now.")
                self.annulus_setter(x0,y0,r1,width*(1-np.finfo(width).eps))

        bval = (r2 < r1*r1) and (cr2 > r0*r0)
        if not self.plot_is_2d: # FIX (this will need a fix once we have 3d plotting fully implemented)
            z0 = self.plot_zmin
            depth = self.plot_zmax - self.plot_zmin
            bval = bval and (z0 < self.plot_zmax) and (z0+depth > self.plot_zmin)
        self.plot_cells_button.setEnabled(bval and self.pw.is_any_cell_type_button_group_checked())

        self.canvas.update()
        self.canvas.draw()

    def annulus_setter(self, x0, y0, r1, width):
        if self.preview_patch is None:
            self.preview_patch = self.ax0.add_patch(Annulus((x0,y0),r1,width,alpha=0.2))
        else:
            self.preview_patch.set(center=(x0,y0),radii=r1,width=width)

    def get_circumscribing_radius(self,x0,y0):
        if 2*x0 < self.plot_xmin + self.plot_xmax: # if left of midpoint
            dx = self.plot_xmax - x0
        else:
            dx = x0 - self.plot_xmin
        if 2*y0 < self.plot_ymin + self.plot_ymax: # if left of midpoint
            dy = self.plot_ymax - y0
        else:
            dy = y0 - self.plot_ymin
        return dx*dx + dy*dy

    def wedge_plotter(self):
        if self.plot_is_2d:
            self.read_par_texts()
            if not self.current_pars_acceptable:
                return
            x0, y0, r0, r1, th1, th2 = self.current_pars
            if r1 < r0:
                if self.preview_patch: # probably a way to impose this using validators, but that would require dynamically updating the validators...
                    self.preview_patch.remove()
                    self.canvas.update()
                    self.canvas.draw()
                    self.preview_patch = None
                self.plot_cells_button.setEnabled(False)
                return
            
            r2, dx, dy = self.get_distance2_to_domain(x0,y0)
            cr2 = self.get_circumscribing_radius(x0, y0)
            # outer_radius_reaches_domain = r2 < r1*r1
            # inner_radius_does_not_contain_entire_domain = cr2 > r0*r0

            if self.preview_patch is None:
                self.preview_patch = self.ax0.add_patch(Wedge((x0,y0),r1,th1,th2,width=r1-r0,alpha=0.2))
            else:
                self.preview_patch.set(center=(x0,y0),radius=r1,theta1=th1,theta2=th2,width=r1-r0)
        
        bval = (r2 < r1*r1) and (cr2 > r0*r0)

        bval = bval and self.wedge_in_domain(x0,y0,r0,r1,th1,th2,dx,dy,r2)
        if not self.plot_is_2d: # FIX (this will need a fix once we have 3d plotting fully implemented)
            z0 = self.plot_zmin
            depth = self.plot_zmax - self.plot_zmin
            bval = bval and (z0 < self.plot_zmax) and (z0+depth > self.plot_zmin)
        self.plot_cells_button.setEnabled(bval and self.pw.is_any_cell_type_button_group_checked())

        self.canvas.update()
        self.canvas.draw()

    def wedge_in_domain(self,x0,y0,r0,r1,th1,th2,dx,dy,r2):
        th1, th2 = normalize_thetas(th1,th2)
        if r2==0: # then (x0,y0) is in domain
            # first find shortest distances to edge of domain
            r_th1 = self.distance_to_domain_from_within(x0,y0,th1)
            if r_th1 > r0:
                return True
            r_th2 = self.distance_to_domain_from_within(x0,y0,th2)
            if r_th2 > r0:
                return True

            # If the above don't work, then hopefully checking these easy distances may work
            starting_theta_step = 1 + (th1 // 90) # first 90 deg angle that could go to side of domain for shortest distance purposes
            end_theta_step = 1 + (th2 // 90) # first 90 deg angle that could go to side of domain for shortest distance purposes
            mid_thetas_step = np.arange(starting_theta_step,end_theta_step)
            for th in mid_thetas_step:
                if th % 4 == 0: # right
                    d = self.plot_xmax - x0
                elif th % 4 == 1: # up
                    d = self.plot_ymax - y0
                elif th % 4 == 2: # left
                    d = x0 - self.plot_xmin
                elif th % 4 == 3: # down
                   d = y0 - self.plot_ymin
                if d > r0:
                    return True
            
            # If those easy-to-calculate distances fail, then we try the corners, which are our last hope
            r02 = r0*r0
            th1_rad = th1*0.017453292519943
            th2_rad = th2*0.017453292519943
            th = np.arctan2(self.plot_ymax-y0,self.plot_xmax-x0)
            if th > th1_rad and th < th2_rad:
                if  (self.plot_xmax - x0)**2 + (self.plot_ymax-y0)**2 > r02:
                    return True
            th = np.arctan2(self.plot_ymax-y0,self.plot_xmin-x0)
            if th > th1_rad and th < th2_rad:
                if  (self.plot_xmin - x0)**2 + (self.plot_ymax-y0)**2 > r02:
                    return True
            th = np.arctan2(self.plot_ymin-y0,self.plot_xmin-x0)
            if th > th1_rad and th < th2_rad:
                if  (self.plot_xmin - x0)**2 + (self.plot_ymin-y0)**2 > r02:
                    return True
            th = np.arctan2(self.plot_ymin-y0,self.plot_xmax-x0)
            if th > th1_rad and th < th2_rad:
                if  (self.plot_xmax - x0)**2 + (self.plot_ymin-y0)**2 > r02:
                    return True
            return False
        else: # then (x0,y0) is not in the domain
            return self.wedge_in_domain_center_out(x0,y0,r0,r1,th1,th2,dx,dy)

    def wedge_in_domain_center_out(self,x0,y0,r0,r1,th1,th2,dx,dy):
        # check to see if the wedge is at all in the domain when the center is outside the domain
        xL, xR, yL, yR = [self.plot_xmin, self.plot_xmax, self.plot_ymin, self.plot_ymax]
        # WLOG set center on left or bottom-left of domain
        if dx > 0: 
            if dy == 0: # reflect so it is on left
                xL, xR = [-xR,-xL]
                x0 *= -1
                th1, th2 = [180-th2,180-th1] # reflections flip orientation
                dx *= -1
            elif dy > 0: # rotate 180
                xL, xR, yL, yR = [-xR, -xL, -yR, -yL]
                x0 *= -1
                y0 *= -1
                th1 += 180
                th2 += 180
                dx *= -1
                dy *= -1
            else: # dy < 0 rotate 270
                xL, xR, yL, yR = [yL, yR, -xR, -xL]
                x0, y0 = [y0, -x0]
                th1 += 270
                th2 += 270
                dx, dy = [dy, -dx]
        elif dx == 0:
            if dy < 0: # rotate 270
                xL, xR, yL, yR = [yL, yR, -xR, -xL]
                x0, y0 = [y0, -x0]
                th1 += 270
                th2 += 270
                dx, dy = [dy, 0]
            else: # dy > 0 rotate 90
                xL, xR, yL, yR = [-yR, -yL, xL, xR]
                x0, y0 = [-y0, x0]
                th1 += 90
                th2 += 90
                dx, dy = [-dy, 0]
        else: # dx < 0
            if dy > 0: # reflect in y axis so on the bottom
                yL, yR = [-yR,-yL]
                y0 *= -1
                th1, th2 = [-th2,-th1] # reflections flip orientation
                dy *= -1
        th1, th2 = normalize_thetas(th1,th2)

        # now affine shift so (x0,y0) at (0,0)
        xL -= x0
        xR -= x0
        yL -= y0
        yR -= y0
        x0 = 0
        y0 = 0

        # Now I can proceed as if the center is left or bottom-left of domain, i.e. dx<0 and dy<=0
        th1_rad = th1*0.017453292519943
        th2_rad = th2*0.017453292519943

        bounding_th_R = np.arctan2(yR,xL) # top-left corner is always the upper (Right) theta bound in this reference frame
        bounding_d_R2 = xL**2 + yR**2 + np.zeros((2,1))
        inner_th_1 = np.arctan2(yR,xR) # top-right is always interior in this frame of reference
        if dy == 0:
            inner_1_d2 = np.array([(xL/np.cos(inner_th_1))**2,xR**2 + yR**2]).reshape((2,1))
            bounding_th_L = np.arctan2(yL,xL)
            bounding_d_L2 = xL**2 + yL**2 + np.zeros((2,1))
            inner_th_2 = np.arctan2(yL,xR)
            inner_2_d2 = np.array([(xL/np.cos(inner_th_2))**2,xR**2 + yL**2]).reshape((2,1))
            th_right_d2 = np.array([xL**2,xR**2]).reshape((2,1))
            TH = np.array([bounding_th_L,inner_th_2,0,inner_th_1,bounding_th_R])
            D = np.concatenate((bounding_d_L2,inner_2_d2,th_right_d2,inner_1_d2,bounding_d_R2),axis=1)
        else:
            temp_dx = xL/np.cos(inner_th_1)
            temp_dy = yL/np.sin(inner_th_1)
            inner_1_d2 = np.array([(np.max([temp_dx,temp_dy]))**2,xR**2 + yR**2]).reshape((2,1))
            bounding_th_L = np.arctan2(yL,xR)
            bounding_d_L2 = xR**2 + yL**2 + np.zeros((2,1))
            inner_th_2 = np.arctan2(yL,xL)
            temp_dx =  xR/np.cos(inner_th_1)
            temp_dy = yR/np.sin(inner_th_1)
            inner_2_d2 = np.array([xL**2 + yL**2,(np.min([temp_dx,temp_dy]))**2]).reshape((2,1))
            if inner_th_1 > inner_th_2:
                inner_th_1, inner_th_2 = [inner_th_2, inner_th_1]
                inner_1_d2, inner_2_d2 = [inner_2_d2, inner_1_d2]
            TH = np.array([bounding_th_L,inner_th_1,inner_th_2,bounding_th_R])
            D = np.concatenate((bounding_d_L2,inner_1_d2,inner_2_d2,bounding_d_R2),axis=1)

        th1_inbounds = th1_rad > bounding_th_L and th1_rad < bounding_th_R
        if th1_inbounds and (th1_rad not in TH):
            TH, D = compute_theta_intersection_distances(TH,D,th1_rad,x0,y0,xL,xR,yL,yR,dy)
        th2_inbounds = th2_rad > bounding_th_L and th2_rad < bounding_th_R
        th2_inbounds = th2_inbounds or ((th2_rad-2*np.pi) > bounding_th_L and (th2_rad-2*np.pi) < bounding_th_R) # it's possible that th2 being on [th1,th1+360] might not lie between these theta value, but intersect nonetheless
        if th2_inbounds and (th2_rad not in TH):
            TH, D = compute_theta_intersection_distances(TH,D,th2_rad,x0,y0,xL,xR,yL,yR,dy)

        TH_rel = (TH-th1_rad) % (2*np.pi)
        d_old2 = None

        A = np.concatenate((TH_rel.reshape(1,len(TH_rel)),TH.reshape(1,len(TH)),D),axis=0)
        ord = np.argsort(A[0])
        A = A[:,ord]

        r02 = r0*r0
        r12 = r1*r1
        for idx, abs_th in enumerate(A[1]):
            if A[0,idx] > th2_rad - th1_rad: # then we've finished our rotations
                break
            d_new2 = A[2:4,idx]
            # print(f"\tidx = {idx}\n\tabs_th = {abs_th}\n\td_new2 = {d_new2}\n\td_old2 = {d_old2}")
            if d_new2[0] < r12 and d_new2[1] > r02:
                return True
            if d_old2 is not None:
                if (d_old2[0] >= r12 and d_new2[1] <= r02) or (d_old2[1] <= r02 and d_new2[0] >= r12):
                    # then the interval passed through the region
                    return True
            if abs_th == bounding_th_R: # the sweep of the ray is leaving the domain
                d_old2 = None
            else:
                d_old2 = copy.deepcopy(d_new2)
        # if control passes here, then we have found that the wedge does not intersect the domain
        return False

    def distance_to_domain_from_within(self, x0, y0, th):
        v1_x = np.cos(th)
        v1_y = np.sin(th)
        if v1_x > 0:
            r_x = (self.plot_xmax - x0) / v1_x
        elif v1_x < 0:
            r_x = (self.plot_xmin - x0) / v1_x
        else:
            r_x = np.inf
        if v1_y > 0:
            r_y = (self.plot_ymax - y0) / v1_y
        elif v1_y < 0:
            r_y = (self.plot_ymin - y0) / v1_y
        else:
            r_y = np.inf
        return r_x if r_x <= r_y else r_y

    def read_par_texts(self):
        self.current_pars = []
        for pt in self.par_text:
            if not pt.isEnabled():
                break
            if not pt.hasAcceptableInput():
                self.plot_cells_button.setEnabled(False)
                self.current_pars_acceptable = False
                return # do not update unless all are ready
            self.current_pars.append(float(pt.text()))
        self.current_pars_acceptable = True

    def spatial_plotter(self):
        self.read_par_texts()
        if not self.current_pars_acceptable:
            return
        if self.plot_is_2d:
            x0, y0, width, height = self.current_pars
            if self.preview_patch is None:
                print(f"----initializing spatial plotter-----")
                self.initial_x0 = x0
                self.initial_y0 = y0
                self.initial_width = width
                self.initial_height = height
                initial_coords = self.spatial_base_coords * [width, height] + [x0,y0]
                self.preview_patch = self.ax0.scatter(initial_coords[:,0],initial_coords[:,1], self.scatter_sizes, 'gray', alpha=0.5)
                self.initial_offsets = self.preview_patch.get_offsets()
            else:
                print(f"----updating spatial plotter-----")
                offset = self.initial_offsets + (self.spatial_base_coords * [width-self.initial_width, height-self.initial_height] + [x0-self.initial_x0,y0-self.initial_y0])
                self.preview_patch.set_offsets(offset)

            # check left edge of rect is left of right edge of domain, right edge of rect is right of left edge of domain (similar in y direction)
            bval = (x0 < self.plot_xmax) and (x0+width > self.plot_xmin) and (y0 < self.plot_ymax) and (y0+height > self.plot_ymin) # make sure the rectangle intersects the domain with positive area
        else: # FIX (this will need a fix once we have 3d plotting fully implemented)
            x0, y0, z0, width, height, depth = self.current_pars
            bval = (x0 < self.plot_xmax) and (x0+width > self.plot_xmin) and (y0 < self.plot_ymax) and (y0+height > self.plot_ymin) # make sure the rectangle intersects the domain with positive area
            bval = bval and (z0 < self.plot_zmax) and (z0+depth > self.plot_zmin)

        self.plot_cells_button.setEnabled(bval and self.pw.is_any_cell_type_button_group_checked())

        self.canvas.update()
        self.canvas.draw()

    def create_figure(self):
        self.figure = plt.figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        plt.style.use('ggplot')
        self.canvas.setStyleSheet("background-color:transparent;")

        self.canvas.setFocusPolicy( QtCore.Qt.ClickFocus )

        self.plot_is_2d = self.plot_zmax - self. plot_zmin <= self.plot_zdel # if the domain height is larger than the voxel height, then we have a 3d simulation
        if self.plot_is_2d: 
            projection = None
        else:
            projection = '3d'

        self.ax0 = self.figure.add_subplot(111, adjustable='box',projection=projection)
        
        self.format_axis()

        self.mpl_cid = []

        self.mouse_pressed = False

        self.canvas.focusInEvent = lambda e : self.canvas_in_focus(e)
        self.canvas.focusOutEvent = lambda e : self.canvas_out_focus(e)
        self.canvas.keyPressEvent = lambda e : self.canvas_key_press(e)

        self.canvas.update()
        self.canvas.draw()

        self.cell_type_micron2_area_dict = {cell_type: (((9*np.pi*V**2) / 16) ** (1./3)) for cell_type, V in self.biwt.cell_volume.items()}
        if self.biwt.use_spatial_data or (not self.plot_is_2d):
            dx, dy = self.ax0.transData.transform((1,1))-self.ax0.transData.transform((0,0)) # # pixels/ micron
            area_scale_factor = dx*dy  * (72/self.figure.dpi)**2
            fudge_factor = 1.258199089131739 # empirically-defined value to multiply area (in pts) to represent true area in microns on plot
            self.cell_type_pt_area_dict = {cell_type: fudge_factor * area_scale_factor * A for cell_type, A in self.cell_type_micron2_area_dict.items()}
            self.single_scatter_sizes = np.array([self.cell_type_pt_area_dict[ctn] for ctn in self.biwt.cell_types_final])
            if self.biwt.use_spatial_data:
                self.scatter_sizes = self.num_box.value() * self.single_scatter_sizes

        self.legend_artists = []
        self.legend_labels = []
        self.legend_window = None
        self.update_legend_window()
        
    def update_legend_window(self):
        is_hidden = (self.legend_window is None) or (self.legend_window.isHidden()) # doesn't exist yet or is hidden, so don't display after update
        if self.legend_window is not None:
            self.legend_window.close()
        self.legend_window = LegendWindow(self, legend_artists=self.legend_artists, legend_labels=self.legend_labels, legend_title="Cell Types")
        # if the legend window is shown, update and refresh
        if not is_hidden:
            self.legend_window.show()
            
    def canvas_in_focus(self, event):
        self.mouse_keyboard_label.setEnabled(True)

    def canvas_out_focus(self, event):
        self.mouse_keyboard_label.setEnabled(False)

    def canvas_key_press(self, event):
        modifiers = QApplication.keyboardModifiers()
            
        id = self.pw.cell_pos_button_group.checkedId()
        if id==0 or (event.key() != QtCore.Qt.Key_Z):
            return # nothing to do with everywhere plotter or if not z pressed
        elif modifiers == QtCore.Qt.ControlModifier:
            if self.patch_history_idx[id]==0:
                return # already at the beginning
            self.patch_history_idx[id] -= 1
        elif modifiers == (QtCore.Qt.ControlModifier |
                        QtCore.Qt.ShiftModifier):
            if self.patch_history_idx[id]==len(self.patch_history[id])-1:
                return # already at end
            self.patch_history_idx[id] += 1
        self.load_previous_patch_pars(self.patch_history[id][self.patch_history_idx[id]])

    def format_axis(self):
        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)
        if self.plot_is_2d:
            self.ax0.set_aspect(1.0)
        else:
            self.ax0.set_zlim(self.plot_zmin, self.plot_zmax)
            self.ax0.set_box_aspect([1,1,1])

    def plot_cell_pos(self):
        self.preview_constrained_to_axes = False
        if self.pw.cell_pos_button_group.checkedId()==self.pw.spatial_plotter_id:
            if self.plot_is_2d:
                x0, y0, width, height = self.current_pars
            else:
                x0, y0, z0, width, height, depth = self.current_pars
            n_per_spot = self.num_box.value()
            for cell_type in self.pw.checkbox_dict.keys():
                if self.pw.checkbox_dict[cell_type].isChecked():
                    idx_cell_type = [ctn==cell_type for ctn in self.biwt.cell_types_final]
                    cell_radius = np.sqrt(self.cell_type_micron2_area_dict[cell_type] / np.pi)
                    cell_coords = np.hstack((self.spatial_base_coords[idx_cell_type,0:2] * [width, height] + [x0,y0],np.zeros((sum(idx_cell_type),1))))
                    idx_inbounds = [(cc[0]>=self.plot_xmin and cc[0]<=self.plot_xmax and cc[1]>=self.plot_ymin and cc[1]<=self.plot_ymax) for cc in cell_coords]
                    cell_coords = cell_coords[idx_inbounds,:]
                    if n_per_spot==1:
                        self.biwt.csv_array[cell_type] = np.vstack((self.biwt.csv_array[cell_type],cell_coords))
                        if self.plot_is_2d:
                            self.circles(cell_coords, s=cell_radius, color=self.color_by_celltype[cell_type], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
                            legend_patch = Patch(facecolor=self.color_by_celltype[cell_type], edgecolor='black', linewidth=0.5)
                            self.legend_artists.append(legend_patch)
                        else:
                            cell_coords[:,2] = self.spatial_base_coords[idx_cell_type,2] * depth + z0
                            collection = self.ax0.scatter(cell_coords[:,0],cell_coords[:,1],cell_coords[:,2], s=8.0, color=self.color_by_celltype[cell_type], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
                            scatter_objects, _ = collection.legend_elements()
                            self.legend_artists.append(scatter_objects[0])
                    else:
                        r = cell_radius * np.sqrt(n_per_spot)
                        all_new = np.empty((0,3))
                        for cc in cell_coords:
                            self.wedge_sample(n_per_spot, cc[0], cc[1], r)
                            all_new = np.vstack((all_new,self.new_pos))
                        self.biwt.csv_array[cell_type] = np.vstack((self.biwt.csv_array[cell_type],all_new))
                        if self.plot_is_2d:
                            self.circles(all_new, s=cell_radius, color=self.color_by_celltype[cell_type], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
                            legend_patch = Patch(facecolor=self.color_by_celltype[cell_type], edgecolor='black', linewidth=0.5)
                            self.legend_artists.append(legend_patch)
                        else:
                            collection = self.ax0.scatter(all_new[:,0],all_new[:,1],all_new[:,2], s=8.0, color=self.color_by_celltype[cell_type], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
                            scatter_objects, _ = collection.legend_elements()
                            self.legend_artists.append(scatter_objects[0])
                    self.legend_labels.append(cell_type)
                    self.pw.checkbox_dict[cell_type].setEnabled(False)
                    self.pw.checkbox_dict[cell_type].setChecked(False)
                    self.pw.undo_button[cell_type].setEnabled(True)
        else:
            for cell_type in self.pw.checkbox_dict.keys():
                if self.pw.checkbox_dict[cell_type].isChecked():
                    self.plot_cell_pos_single(cell_type)
        self.pw.undo_all_button.setEnabled(True)
        self.canvas.update()
        self.canvas.draw()
        self.update_legend_window()
        self.plot_cells_button.setEnabled(False)

        for b in self.pw.checkbox_dict.values():
            if b.isEnabled() is True:
                return
        # If control passes here, then all the buttons are disabled and the plotting is done
        self.pw.continue_to_write_button.setEnabled(True)

    def max_dist_to_domain(self,x0,y0):
        xL, xR, yL, yR = [self.plot_xmin, self.plot_xmax, self.plot_ymin, self.plot_ymax]
        dx = xL-x0 if (2*x0 > xL+xR) else x0-xR # distance to furtherst vertical edge
        dy = yL-y0 if (2*y0 > yL+yR) else y0-yR # distance to furtherst horizontal edge
        return np.sqrt(dx*dx + dy*dy)
    
    def constrain_rectangle_to_domain(self):
        if self.preview_constrained_to_axes:
            return
        x0, y0, width, height = self.constrain_corners(self.preview_patch.get_corners()[[0,2]])
        self.preview_patch.set_bounds(x0, y0, width, height)
        self.preview_constrained_to_axes = True
        
    def constrain_corners(self, corners):
        corners = np.array([[min(max(x,self.plot_xmin),self.plot_xmax),min(max(y,self.plot_ymin),self.plot_ymax)] for x,y in corners])
        return [corners[0,0],corners[0,1],corners[1,0]-corners[0,0],corners[1,1]-corners[0,1]]
    
    def plot_cell_pos_single(self, cell_type):
        if self.plot_is_2d:
            self.plot_cell_pos_single_2d(cell_type)
        else:
            self.plot_cell_pos_single_3d(cell_type)
            
    def plot_cell_pos_single_2d(self, cell_type):
        N = self.biwt.cell_counts[cell_type]
        if type(self.preview_patch) is Rectangle:
            # first make sure the rectangle is all in bounds
            self.constrain_rectangle_to_domain()
            x0, y0 = self.preview_patch.get_xy()
            width = self.preview_patch.get_width()
            height = self.preview_patch.get_height()
            x = x0 + width * np.random.uniform(size=(N,1))
            y = y0 + height * np.random.uniform(size=(N,1))
            z = np.zeros((N,1))
            self.new_pos = np.concatenate((x,y,z),axis=1)
        elif type(self.preview_patch) is Circle:
            x0, y0 = self.preview_patch.get_center()
            r = self.preview_patch.get_radius()
            if not self.preview_constrained_to_axes:
                r = np.min([r,self.max_dist_to_domain(x0,y0)])
                self.preview_patch.set_radius(r)
                self.preview_constrained_to_axes = True
            self.wedge_sample(N, x0, y0, r)
        elif type(self.preview_patch) is Annulus:
            x0, y0 = self.preview_patch.get_center()
            r1 = self.preview_patch.get_radii()[0] # annulus is technically an ellipse, get_radii returns (semi-major,semi-minor) axis lengths, since I'm using circles, these will be the same
            width = self.preview_patch.get_width()
            r0 = r1 - width
            if not self.preview_constrained_to_axes:
                r1 = np.min([r1,self.max_dist_to_domain(x0,y0)])
                r0 = np.max([r0,np.sqrt(self.get_distance2_to_domain(x0,y0)[0])])
                self.preview_patch.set_radii(r1)
                self.preview_patch.set_width(r1-r0)
                self.preview_constrained_to_axes = True
            self.wedge_sample(N, x0, y0, r1, r0=r0)
        elif type(self.preview_patch) is Wedge:
            x0, y0 = self.preview_patch.center
            r1 = self.preview_patch.r
            width = self.preview_patch.width
            r0 = r1 - width
            th1 = self.preview_patch.theta1  
            th2 = self.preview_patch.theta2
            if not self.preview_constrained_to_axes:
                r1 = np.min([r1,self.max_dist_to_domain(x0,y0)])
                if th2 == th1:
                    pass
                elif ((th2-th1) % 360) == 0:
                    th2 = th1 + 360
                else:
                    th2 -= 360 * ((th2-th1) // 360) # I promise this works if dth=th2-th1 < 0, 0<dth<360, and dth>360. 
                r0 = np.max([r0,np.sqrt(self.get_distance2_to_domain(x0,y0)[0])])
                self.preview_patch.set(center=(x0,y0),radius=r1,theta1=th1,theta2=th2,width=r1-r0)
                self.preview_constrained_to_axes = True
            self.wedge_sample(N, x0, y0, r1, r0=r0, th_lim=(th1*0.017453292519943,th2*0.017453292519943))
        else:
            print("unknown patch")
        self.biwt.csv_array[cell_type] = np.append(self.biwt.csv_array[cell_type],self.new_pos,axis=0)

        self.circles(self.new_pos, s=(0.75*self.biwt.cell_volume[cell_type]/np.pi)**(1/3), color=self.color_by_celltype[cell_type], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
        legend_patch = Patch(facecolor=self.color_by_celltype[cell_type], edgecolor='black', linewidth=0.5)
        self.legend_artists.append(legend_patch)
        self.legend_labels.append(cell_type)

        self.pw.checkbox_dict[cell_type].setEnabled(False)
        self.pw.checkbox_dict[cell_type].setChecked(False)
        self.pw.undo_button[cell_type].setEnabled(True)

    def plot_cell_pos_single_3d(self, cell_type):
        N = self.biwt.cell_counts[cell_type]
        if self.current_plotter == self.everywhere_plotter:
            x0, y0, z0 = [self.plot_xmin, self.plot_ymin, self.plot_zmin]
            width, height, depth = [self.plot_dx, self.plot_dy, self.plot_dz]
            x = x0 + width * np.random.uniform(size=(N,1))
            y = y0 + height * np.random.uniform(size=(N,1))
            z = z0 + depth * np.random.uniform(size=(N,1))
            self.new_pos = np.concatenate((x,y,z),axis=1)
        self.biwt.csv_array[cell_type] = np.append(self.biwt.csv_array[cell_type],self.new_pos,axis=0)

        # sz = self.cell_type_micron2_area_dict[cell_type] * 0.036089556256 # empirically-determined value to scale area to points in 3d (scales typical cell volume's area to be 8pt)
        collection = self.ax0.scatter(self.new_pos[:,0],self.new_pos[:,1],self.new_pos[:,2], s=(0.75*self.biwt.cell_volume[cell_type]/np.pi)**(1/3), color=self.color_by_celltype[cell_type], edgecolor='black', linewidth=0.5, alpha=self.alpha_value)
        scatter_objects, _ = collection.legend_elements()
        self.legend_artists.append(scatter_objects)

        self.pw.checkbox_dict[cell_type].setEnabled(False)
        self.pw.checkbox_dict[cell_type].setChecked(False)
        self.pw.undo_button[cell_type].setEnabled(True)
        self.pw.undo_all_button.setEnabled(True)

    def wedge_sample(self,N,x0,y0,r1, r0=0.0, th_lim=(0,2*np.pi)):
        i_start = 0
        self.new_pos = np.empty((N,3))
        self.new_pos[:,2] = 0
        while i_start < N:
            if r0 == 0:
                d = r1*np.sqrt(np.random.uniform(size=N-i_start))
            else:
                d = np.sqrt(r0*r0 + (r1*r1-r0*r0)*np.random.uniform(size=N-i_start))
            th = th_lim[0] + (th_lim[1]-th_lim[0]) * np.random.uniform(size=N-i_start)
            x = x0 + d * np.cos(th)
            y = y0 + d * np.sin(th)
            xy = np.array([[a,b] for a,b in zip(x,y) if a>=self.plot_xmin and a<=self.plot_xmax and b>=self.plot_ymin and b<=self.plot_ymax])
            if len(xy)==0:
                continue
            self.new_pos[range(i_start,i_start+xy.shape[0]),0:2] = xy
            # z = np.zeros((len(xy),1)) # leave this for if and when we do this in 3d
            # self.new_pos[range(i_start,i_start+xy.shape[0]),2] = z # leave this for if and when we do this in 3d
            i_start += xy.shape[0]

    def circles(self, pos, s, c='b', vmin=None, vmax=None, **kwargs):
        """
        See https://gist.github.com/syrte/592a062c562cd2a98a83 

        Make a scatter plot of circles. 
        Similar to plt.scatter, but the size of circles are in data scale.
        Parameters
        ----------
        x, y : scalar or array_like, shape (n, )
            Input data
        s : scalar or array_like, shape (n, ) 
            Radius of circles.
        c : color or sequence of color, optional, default : 'b'
            `c` can be a single color format string, or a sequence of color
            specifications of length `N`, or a sequence of `N` numbers to be
            mapped to colors using the `cmap` and `norm` specified via kwargs.
            Note that `c` should not be a single numeric RGB or RGBA sequence 
            because that is indistinguishable from an array of values
            to be colormapped. (If you insist, use `color` instead.)  
            `c` can be a 2-D array in which the rows are RGB or RGBA, however. 
        vmin, vmax : scalar, optional, default: None
            `vmin` and `vmax` are used in conjunction with `norm` to normalize
            luminance data.  If either are `None`, the min and max of the
            color array is used.
        kwargs : `~matplotlib.collections.Collection` properties
            Eg. alpha, edgecolor(ec), facecolor(fc), linewidth(lw), linestyle(ls), 
            norm, cmap, transform, etc.
        Returns
        -------
        paths : `~matplotlib.collections.PathCollection`
        Examples
        --------
        a = np.arange(11)
        circles(a, a, s=a*0.2, c=a, alpha=0.5, ec='none')
        plt.colorbar()
        License
        --------
        This code is under [The BSD 3-Clause License]
        (http://opensource.org/licenses/BSD-3-Clause)
        """
        x, y = pos.T[0:2]
        if np.isscalar(c):
            kwargs.setdefault('color', c)
            c = None

        if 'fc' in kwargs:
            kwargs.setdefault('facecolor', kwargs.pop('fc'))
        if 'ec' in kwargs:
            kwargs.setdefault('edgecolor', kwargs.pop('ec'))
        if 'ls' in kwargs:
            kwargs.setdefault('linestyle', kwargs.pop('ls'))
        if 'lw' in kwargs:
            kwargs.setdefault('linewidth', kwargs.pop('lw'))
        # You can set `facecolor` with an array for each patch,
        # while you can only set `facecolors` with a value for all.

        zipped = np.broadcast(x, y, s)
        patches = [Circle((x_, y_), s_)
                for x_, y_, s_ in zipped]
        collection = PatchCollection(patches, **kwargs)
        if c is not None:
            c = np.broadcast_to(c, zipped.shape).ravel()
            collection.set_array(c)
            collection.set_clim(vmin, vmax)

        self.ax0.add_collection(collection)
        if c is not None:
            self.ax0.sci(collection)

        return collection

class BioinformaticsWalkthrough(QWidget):
    def __init__(self, config_tab, celldef_tab, ics_tab):
        super().__init__()
        if HAVE_ANNDATA is False:
            s = "To use this tab to import an anndata object to generate cell initial conditions, you need to have anndata installed."
            s += "\nTo install anndata in your environment, you can do one of the following:"
            s += "\n\t1. pip install anndata\n---or---\n\t2. conda install anndata -c conda-forge"
            s += "\n\nAfter installing, restart studio."
            label = QLabel(s)
            label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        # print_biwt_logo()
        
        self.config_tab = config_tab
        self.celldef_tab = celldef_tab
        self.ics_tab = ics_tab

        self.start_walkthrough()

        self.qlineedit_style_sheet = """
            QLineEdit:disabled {
                background-color: rgb(200,200,200);
                color: black;
            }
            QLineEdit:enabled {
                background-color: white;
                color: black;
            }
            """
        self.qpushbutton_style_sheet = """
            QPushButton:enabled {
                background-color : lightgreen;
            }
            QPushButton:disabled {
                background-color : grey;
            }
            """

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addStretch()
        title_label = QLabel('<p style="font-size:32px; text-decoration:underline;"><b>B</b>io<b>I</b>nformatics <b>W</b>alk<b>T</b>hrough (BIWT)</p>')
        # title_label = QLabel("<b>B</b>io<b>I</b>nformatics <b>W</b>alk<b>T</b>hrough (BIWT)")
        hbox.addWidget(title_label)
        hbox.addStretch()
        vbox.addLayout(hbox)
        if HAVE_ANNDATA is False:
            vbox.addWidget(label)
        vbox.addStretch(1)
        vbox.addWidget(QLabel("Importing",styleSheet="QLabel {background-color : orange;}",alignment=QtCore.Qt.AlignCenter,maximumHeight=20))
        hbox = QHBoxLayout()
        self.import_button = QPushButton("Import")
        self.import_button.setStyleSheet("QPushButton {background-color: lightgreen; color: black;}")
        self.import_button.clicked.connect(self.import_cb)
        hbox.addWidget(self.import_button)

        label = QLabel("Column name with cell type (prompt will follow if left blank): ")
        hbox.addWidget(label)

        self.column_line_edit = QLineEdit()
        self.column_line_edit.setEnabled(True)
        self.column_line_edit.setText('type')
        hbox.addWidget(self.column_line_edit)

        vbox.addLayout(hbox)

        label = QLabel("Currently supported (file format, data type) pairs: (h5ad, anndata), (rds, Seurat/SingleCellExperiment), and (csv, NA)")
        vbox.addWidget(label)

        vbox.addWidget(QHLine())

        vbox.addWidget(QLabel("Cell initial conditions file",styleSheet="QLabel {background-color : orange;}",alignment=QtCore.Qt.AlignCenter,maximumHeight=20))

        hbox = QHBoxLayout()
        label = QLabel("folder")
        hbox.addWidget(label)

        self.csv_folder = QLineEdit("./config")
        hbox.addWidget(self.csv_folder)
        label = QLabel("file")
        hbox.addWidget(label)

        self.csv_file = QLineEdit("cells.csv")
        hbox.addWidget(self.csv_file)

        vbox.addLayout(hbox)

        vbox.addStretch(1)

        base_widget = QWidget()
        base_widget.setLayout(vbox)
        self.layout = QVBoxLayout(self)  # leave this!
        self.layout.addWidget(base_widget)

        self.spatial_data_found = False

        if BIWT_DEV_MODE:
            biwt_dev_mode(self)

    def fill_gui(self):
        self.csv_folder.setText(self.config_tab.csv_folder.text())
        self.csv_file.setText(self.config_tab.csv_file.text())

    def open_next_window(self, window_class, layout=None, show=True):
        if self.window is not None:
            self.window.hide()
            self.current_window_idx += 1
            if self.stale_futures:
                del self.previous_windows[self.current_window_idx-1:]
                if type(self.window) is not BioinformaticsWalkthroughWindow_WarningWindow:
                    self.previous_windows.append(self.window)
                else:
                    self.current_window_idx -= 1 # ok, actually, don't increase the index if the current window is a popup warning window
                self.window = window_class(self)
            else:
                self.window = self.previous_windows[self.current_window_idx]
                self.stale_futures = self.current_window_idx==len(self.previous_windows)-1 # if it's now the last one, mark it as stale
        else: # This is opening the very first window
            self.window = window_class(self)

        if layout:
            self.window.setLayout(layout)

        if show:
            self.window.hide()
            self.window.show()

    def go_back_to_prev_window(self):
        print(f"Going back to previous window")
        if len(self.previous_windows)==self.current_window_idx:
            self.previous_windows.append(self.window)
        if self.stale_futures and self.current_window_idx < len(self.previous_windows)-1:
            print(f"\tFutures are stale. Deleting from {self.current_window_idx+2} to {len(self.previous_windows)}")
            del self.previous_windows[self.current_window_idx+1:]
        elif not self.stale_futures:
            print(f"\tFutures are not stale. Keeping windows {self.current_window_idx+1} to {len(self.previous_windows)}")
        self.stale_futures = False # any remaining future windows are not stale
        self.window.hide()
        self.current_window_idx -= 1
        self.window = self.previous_windows[self.current_window_idx]
        self.window.hide()
        self.window.show()

    def search_vis_arrays_for(self, pattern, exact=False):
        return self.search_for(self.data_vis_arrays, pattern, exact)

    def search_columns_for(self, pattern, exact=False):
        return self.search_for(self.data_columns, pattern, exact)
    
    def search_for(self, array_dict, pattern, exact=False):
        for k, v in array_dict.items():
            if exact:
                if k == pattern:
                    return True, k, v
            else:
                if pattern in k:
                    return True, k, v
        return False, None, None

    def start_walkthrough(self):
        self.window = None
        self.current_window_idx = 0 # reset the window index as this is an entry point for the walkthrough
        self.stale_futures = True # reset the window index as this is an entry point for the walkthrough
        self.previous_windows = []
    
    ### Import data
    def import_cb(self):
        self.start_walkthrough()
        full_file_path = QFileDialog.getOpenFileName(self,'',".")
        print(f"full_file_path = {full_file_path}")
        file_path = full_file_path[0]
        if file_path == "":
            print("BIWT: No file selected.")
            return

        print(f"BIWT: Importing file {file_path}...")
        self.import_file(file_path)

    def import_file(self, file_path):
        if file_path.endswith(".h5ad"):
            import_successful = self.import_file_from_h5ad(file_path)
        elif file_path.endswith(".csv"):
            import_successful = self.import_file_from_csv(file_path)
        elif file_path.lower().endswith(".rds") or file_path.lower().endswith(".rda") or file_path.lower().endswith(".rdata"):
            import_successful = self.import_file_from_r(file_path)

        if not import_successful:
            return
            
        self.open_next_window(BioinformaticsWalkthroughWindow_ClusterColumn, show=False)

        if self.auto_continue: # set in BioinformaticsWalkthroughWindow_ClusterColumn if the line edit is filled with a column name found in the data
            self.current_column = self.column_line_edit.text()
            self.continue_from_import()
        else:
            self.window.hide()
            self.window.show()

    def import_file_from_r(self,file_path):
        if not HAVE_RPY2:
            print("rpy2 not installed. Cannot import R file.")
            return False
        try:
            importr_base = importr('base')
        except Exception as e:
            print(f"r-base not installed. Cannot import R file.\nError: {e}")
            return False
        try:
            rdata = importr_base.readRDS(file_path)
        except Exception as e:
            print(f"Import failed while trying to read {file_path} as an R object.\nError: {e}")
            return False
        
        print("rdata read")
        try:
            anndata2ri.activate()
        except Exception as e:
            print(f"anndata2ri not activated. Cannot import R object.\nError: {e}")
            return False

        classname = tuple(rdata.rclass)[0]
        print(f"rdata class: {classname}")

        reductions_slot_name = None

        ####################
        # another option that could work in these contexts (consider this suggestive rather than definitive):
        # metadata = rdata.slots[slot_name]
        # with (ro.default_converter + pandas2ri.converter).context():
        #     print("Converting to pandas dataframe...")
        #     data_columns = ro.conversion.get_conversion().rpy2py(metadata)
        # with (ro.default_converter + pandas2ri.converter).context():
        #     print("Converting to pandas dataframe...")
        #     dim_reds = ro.conversion.get_conversion().rpy2py(reductions)
        # for key in dim_reds.keys():
        #     val = dim_reds[key]
        #     with (ro.default_converter + pandas2ri.converter).context():
        #         df[key] = ro.conversion.get_conversion().rpy2py(val.slots["cell.embeddings"])
        ####################

        if classname in ["SingleCellExperiment", "SummarizedExperiment"]: # not clear if SummarizedExperiment will work, but fingers crossed?
            conv_adata = anndata2ri.rpy2py(rdata)
            self.import_from_converted_anndata(conv_adata)
        elif classname in ["Seurat"]:
            # there is a way to do this using the rdata object loaded above, but this way works and also funnels it to import_from_converted_anndata
            r("library(Seurat)")
            r(f'x<-readRDS("{file_path}")')
            conv_adata = r("as.SingleCellExperiment(x)")
            self.import_from_converted_anndata(conv_adata)
        else:
            print(f"Class {classname} not recognized. Cannot import R object.")
            return False

        print("------------R data file loaded-------------")
        print(f"Metadata loaded: {self.data_columns.head()}")

        return True # at this point, we will consider the import successful, regardless of what happens below
    
    def import_from_converted_anndata(self, adata):
        self.data_columns = adata.obs
        self.data_vis_arrays = adata.obsm
        self.search_for_h5ad_spatial_data()
        return True
    
    # def search_for_r_spatial_data(self):
    #     self.spatial_data_found = False
    #     return
    #     # the below does not adequately handle the seurat object case
    #     self.spatial_data_found, key, self.spatial_data = self.search_vis_arrays_for("spatial")
    #     if self.spatial_data_found:
    #         self.spatial_data_key = key
    #         self.spatial_data_location = f"rdata@reductions${key}"
    #         return

    def import_file_from_csv(self,file_path):
        self.data_columns = pd.read_csv(file_path)

        print("------------csv file loaded-------------")

        self.data_vis_arrays = {}
        self.search_columns_for_xyz()
        return True

    def import_file_from_h5ad(self,file_path):
        if not HAVE_ANNDATA:
            print("anndata not installed. Cannot import h5ad file.")
            return False
        try:
            adata = anndata.read_h5ad(file_path)
        except Exception as e:
            print(f"Import failed while trying to read {file_path} as an anndata object.\nError: {e}")
            return False
        try:
            self.data_columns = adata.obs
            self.data_vis_arrays = adata.obsm
        except Exception as e:
            print(f"Failed to read either obs or obsm from {file_path}.\nError: {e}")
            return False

        print("------------anndata object loaded-------------")

        self.search_for_h5ad_spatial_data()
        return True

    def continue_from_import(self):
        if not self.spatial_data_found:
            self.use_spatial_data = False
            self.collect_cell_type_data()
            self.edit_cell_types()
        else:
            self.open_next_window(BioinformaticsWalkthroughWindow_SpatialQuery, show=True)

    def search_for_h5ad_spatial_data(self):
        # space ranger for visium data
        self.spatial_data_found, key, self.spatial_data = self.search_vis_arrays_for("spatial")
        if self.spatial_data_found:
            self.spatial_data_key = key
            self.spatial_data_location = f"adata.obsm['{key}']"
            return
        
        # merscope
        self.search_columns_for_xyz()

        # visium data that just has row and col
        self.search_columns_for_rowcol()

    def search_columns_for_coords(self, xdata_colname, ydata_colname, zdata_colname):
        x_data_found, _, x_data = self.search_columns_for(xdata_colname, exact=True)
        if x_data_found:
            self.spatial_data_found, _, y_data = self.search_columns_for(ydata_colname, exact=True)
            if not self.spatial_data_found:
                return
            z_data_found, _, z_data = self.search_columns_for(zdata_colname, exact=True)

            if z_data_found:
                self.spatial_data = np.hstack((x_data.values.reshape(-1,1),y_data.values.reshape(-1,1),z_data.values.reshape(-1,1)))
                self.spatial_data_location = f"columns '{xdata_colname}', '{ydata_colname}', and '{zdata_colname}'"
            else:
                print("\n\n\nz data not found. Assuming 2d data.\n\n\n")
                self.spatial_data = np.hstack((x_data.values.reshape(-1,1),y_data.values.reshape(-1,1), np.zeros((len(x_data),1))))
                self.spatial_data_location = f"columns '{xdata_colname}' and '{ydata_colname}'"

            new_key = "spatial"
            suffix = ""
            n=0
            while f"{new_key}_{suffix}" in self.data_vis_arrays.keys():
                n += 1
                suffix = str(n)
            self.data_vis_arrays[f"{new_key}_{suffix}"] = self.spatial_data
            return
        
    def search_columns_for_xyz(self):
        xdata_colname = "x"
        ydata_colname = "y"
        zdata_colname = "z"
        return self.search_columns_for_coords(xdata_colname, ydata_colname, zdata_colname)

    def search_columns_for_rowcol(self):
        xdata_colname = "imagerow"
        ydata_colname = "imagecol"
        zdata_colname = None # this will be used in an exact match, which should check if key=None which will be false (and not an error)
        self.search_columns_for_coords(xdata_colname, ydata_colname, zdata_colname)

    def collect_cell_type_data(self):
        self.cell_types_original = self.data_columns[self.current_column]
        self.cell_types_list_original = self.cell_types_original.unique().tolist()
        self.cell_types_list_original.sort()
        self.cell_types_original = [str(x) for x in self.cell_types_original] # make sure the names are strings
        self.cell_types_list_original = [str(x) for x in self.cell_types_list_original] # make sure the names are strings

    def continue_from_spatial_query(self):
        self.collect_cell_type_data()
        self.edit_cell_types()

    ### Edit cell types
    def edit_cell_types(self):
        self.open_next_window(BioinformaticsWalkthroughWindow_EditCellTypes, show=True)

    def continue_from_edit(self):
        self.intermediate_types = [] # types used after editing (keep, merge, delete) but before rename
        self.intermediate_type_pre_image = {} # dictionary where keys are intermediate cell types and values are the original cell types that map to them
        original_cell_type_list = list(self.cell_type_dict_on_edit.keys())
        original_cell_type_list.sort()
        for cell_type in original_cell_type_list:
            intermediate_type = self.cell_type_dict_on_edit[cell_type]
            if intermediate_type is not None:
                if intermediate_type not in self.intermediate_types:
                    self.intermediate_types.append(intermediate_type)
                    self.intermediate_type_pre_image[intermediate_type] = [cell_type]
                else:
                    self.intermediate_type_pre_image[intermediate_type].append(cell_type)
        self.rename_cell_types()

    ### Rename cell types
    def rename_cell_types(self):
        self.open_next_window(BioinformaticsWalkthroughWindow_RenameCellTypes, show=True)

    def continue_from_rename(self):
        print("-------Continuing from Rename-------")

        if len(set(self.cell_types_list_final)) != len(self.cell_types_list_final): # this very well could be a suboptimal check for all unique names. coded midflight so no copilot help
            duplicate_names = []
            for idx, cell_type_1 in enumerate(self.cell_types_list_final):
                if (cell_type_1 not in duplicate_names) and (cell_type_1 in self.cell_types_list_final[idx+1:]):
                    duplicate_names.append(cell_type_1)

            s = "The following cell type names were used multiple times:<html><ul>"
            for duplicate_name in duplicate_names:
                s += f"\n\t<li> {duplicate_name}</li>"
            s += "</ul></html>"
            s += "\nThis could cause unexpected behavior. We recommend you go back and Merge these cell types."
            self.pop_up_warning_window(s, self.continue_from_rename_check)
        else:
            self.continue_from_rename_check()
        
    def continue_from_rename_check(self):  
        if self.use_spatial_data:
            self.cell_types_final, self.spatial_data_final = zip(*[(self.cell_type_dict_on_rename[ctn], pos) for ctn, pos in zip(self.cell_types_original, self.spatial_data) if ctn in self.cell_type_dict_on_rename.keys()])
            self.spatial_data_final = np.vstack([*self.spatial_data_final])
        else:
            self.cell_types_final = [self.cell_type_dict_on_rename[ctn] for ctn in self.cell_types_original if ctn in self.cell_type_dict_on_rename.keys()]

        self.count_final_cell_types()
        self.compute_cell_volumes() # used in confluence computations, and in spatial_plotter
        if self.use_spatial_data:
            self.set_cell_positions()
        else:
            self.set_cell_counts()
 
    def pop_up_warning_window(self, s, continue_cb):
        hbox = QHBoxLayout()
        label = QLabel(s)
        hbox.addWidget(label)
        self.open_next_window(lambda biwt : BioinformaticsWalkthroughWindow_WarningWindow(biwt, hbox, continue_cb), show=True)
        
    def count_final_cell_types(self):
        self.cell_counts = {}
        for cell_type in self.cell_types_list_final:
            self.cell_counts[cell_type] = 0
        for ctn in self.cell_types_final:
            self.cell_counts[ctn] += 1

    def compute_cell_volumes(self):
        self.cell_volume = {}
        for cell_type in self.cell_types_list_final:
            if cell_type in self.celldef_tab.param_d.keys():
                self.cell_volume[cell_type] = float(self.celldef_tab.param_d[cell_type]['volume_total'])
            else:
                self.cell_volume[cell_type] = 2494 # use PhysiCell default

    ### Set cell counts
    def set_cell_counts(self):
        self.open_next_window(BioinformaticsWalkthroughWindow_CellCounts, show=True)

    def continue_from_counts(self):
        self.set_cell_positions()

    ### Set cell positions
    def set_cell_positions(self):
        self.open_next_window(BioinformaticsWalkthroughWindow_PositionsWindow, show=True)

    def continue_from_positions(self):
        self.write_to_file()

    ### Write data
    def write_to_file(self):
        self.open_next_window(BioinformaticsWalkthroughWindow_WritePositions, show=True)
        
    ### Finish
    def close_up(self):
        plt.style.use("default")
        self.ics_tab.clear_cb()
        self.ics_tab.import_from_file(self.full_fname)
        self.ics_tab.tab_widget.setCurrentIndex(self.ics_tab.base_tab_id)
        self.ics_tab.csv_folder.setText(self.csv_folder.text())
        self.ics_tab.output_file.setText(self.csv_file.text())
        self.config_tab.cells_csv.setChecked(True)
        self.config_tab.csv_folder.setText(self.csv_folder.text())
        self.config_tab.csv_file.setText(self.csv_file.text())
        self.close()
        self.window.close()
        print("BioinformaticsWalkthroughWindow: Colors will likely change in the ICs tab due to previous cell types being present.")

# helper functions
def create_checkboxes_for_cell_types(vbox, cell_types):
    checkbox_dict = {}
    for cell_type in cell_types:
        checkbox_dict[cell_type] = QCheckBox_custom(cell_type)
        checkbox_dict[cell_type].setChecked(False)
        checkbox_dict[cell_type].setEnabled(True)
        vbox.addWidget(checkbox_dict[cell_type])

    return checkbox_dict

def normalize_thetas(th1,th2):
    th1 = th1 % 360
    th1 = th1 - 360 if th1 >= 180 else th1 # get th1 in [-180,180]
    th2 -= 360 * ((th2-th1) // 360) # get th2 in interval (th1,th1+360)
    return th1, th2

def compute_theta_intersection_distances(TH,D,th,x0,y0,xL,xR,yL,yR,dy):
    if dy == 0:
        ds = (np.array([xL,xR])-x0)/np.cos(th)
        if th > 0:
            ds = np.append(ds, (yR-y0)/np.sin(th))
        else:
            ds = np.append(ds, (yL-y0)/np.sin(th))
        d2 = np.array([(xL-x0)/np.cos(th),np.min(ds)]).reshape((2,1))
    else:
        d2 = np.max([(xL-x0)/np.cos(th),(yL-y0)/np.sin(th)])
        d2 = np.append(d2,np.min([(xR-x0)/np.cos(th),(yR-y0)/np.sin(th)]))
    TH = np.append(TH,th)
    D = np.append(D,d2,axis=1)
    return TH, D

def rectangular_prism_faces(x_min, x_max, y_min, y_max, z_min, z_max):
    # Define the corners of the rectangular prism
    corners = np.array([[x_min, y_min, z_min],
                        [x_max, y_min, z_min],
                        [x_max, y_max, z_min],
                        [x_min, y_max, z_min],
                        [x_min, y_min, z_max],
                        [x_max, y_min, z_max],
                        [x_max, y_max, z_max],
                        [x_min, y_max, z_max]])

    # Define the faces using the corners
    return [[corners[0], corners[1], corners[2], corners[3]],
            [corners[4], corners[5], corners[6], corners[7]],
            [corners[0], corners[1], corners[5], corners[4]],
            [corners[2], corners[3], corners[7], corners[6]],
            [corners[0], corners[3], corners[7], corners[4]],
            [corners[1], corners[2], corners[6], corners[5]]]

def print_biwt_logo():
    print(
    """
     _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _ 
    |_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_|
    |_|                                                                                                                                    |_|
    |_|....................................................................................................................................|_|
    |_|....................................................................................................................................|_|
    |_|....................................................................................................................................|_|
    |_|....................................................................................................................................|_|
    |_|....................................................................................................................................|_|
    |_|.......@@@@@@@@..@@@@..@@@@@@@..@@@@.@@....@@.@@@@@@@@..@@@@@@@..@@@@@@@@..@@.....@@....@@@....@@@@@@@@.@@@@..@@@@@@...@@@@@@.......|_|
    |_|.......@@.....@@..@@..@@.....@@..@@..@@@...@@.@@.......@@.....@@.@@.....@@.@@@...@@@...@@.@@......@@.....@@..@@....@@.@@....@@......|_|
    |_|.......@@.....@@..@@..@@.....@@..@@..@@@@..@@.@@.......@@.....@@.@@.....@@.@@@@.@@@@..@@...@@.....@@.....@@..@@.......@@............|_|
    |_|.......@@@@@@@@...@@..@@.....@@..@@..@@.@@.@@.@@@@@@...@@.....@@.@@@@@@@@..@@.@@@.@@.@@.....@@....@@.....@@..@@........@@@@@@.......|_|
    |_|.......@@.....@@..@@..@@.....@@..@@..@@..@@@@.@@.......@@.....@@.@@...@@...@@.....@@.@@@@@@@@@....@@.....@@..@@.............@@......|_|
    |_|.......@@.....@@..@@..@@.....@@..@@..@@...@@@.@@.......@@.....@@.@@....@@..@@.....@@.@@.....@@....@@.....@@..@@....@@.@@....@@......|_|
    |_|.......@@@@@@@@..@@@@..@@@@@@@..@@@@.@@....@@.@@........@@@@@@@..@@.....@@.@@.....@@.@@.....@@....@@....@@@@..@@@@@@...@@@@@@.......|_|
    |_|....................................................................................................................................|_|
    |_|....................................................................................................................................|_|
    |_|....................................................................................................................................|_|
    |_|....................................................................................................................................|_|
    |_|.......@@......@@....@@@....@@.......@@....@@.@@@@@@@@.@@.....@@.@@@@@@@@...@@@@@@@..@@.....@@..@@@@@@...@@.....@@..................|_|
    |_|.......@@..@@..@@...@@.@@...@@.......@@...@@.....@@....@@.....@@.@@.....@@.@@.....@@.@@.....@@.@@....@@..@@.....@@..................|_|
    |_|.......@@..@@..@@..@@...@@..@@.......@@..@@......@@....@@.....@@.@@.....@@.@@.....@@.@@.....@@.@@........@@.....@@..................|_|
    |_|.......@@..@@..@@.@@.....@@.@@.......@@@@@.......@@....@@@@@@@@@.@@@@@@@@..@@.....@@.@@.....@@.@@...@@@@.@@@@@@@@@..................|_|
    |_|.......@@..@@..@@.@@@@@@@@@.@@.......@@..@@......@@....@@.....@@.@@...@@...@@.....@@.@@.....@@.@@....@@..@@.....@@..................|_|
    |_|.......@@..@@..@@.@@.....@@.@@.......@@...@@.....@@....@@.....@@.@@....@@..@@.....@@.@@.....@@.@@....@@..@@.....@@..................|_|
    |_|........@@@..@@@..@@.....@@.@@@@@@@@.@@....@@....@@....@@.....@@.@@.....@@..@@@@@@@...@@@@@@@...@@@@@@...@@.....@@..................|_|
    |_|....................................................................................................................................|_|
    |_|....................................................................................................................................|_|
    |_|....................................................................................................................................|_|
    |_|....................................................................................................................................|_|
    |_|....................................................................................................................................|_|
    |_| _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _ |_|
    |_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_|
    """
    )
    # print(
    # """
    #  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _ 
    # |_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_|
    # |_|                                             |_|
    # |_|                                             |_|
    # |_|                                             |_|
    # |_|                                             |_|
    # |_|                                             |_|
    # |_|                                             |_|
    # |_|     .@@@@@@@@..@@@@.@@......@@.@@@@@@@@     |_|
    # |_|     .@@.....@@..@@..@@..@@..@@....@@...     |_|
    # |_|     .@@.....@@..@@..@@..@@..@@....@@...     |_|
    # |_|     .@@@@@@@@...@@..@@..@@..@@....@@...     |_|
    # |_|     .@@.....@@..@@..@@..@@..@@....@@...     |_|
    # |_|     .@@.....@@..@@..@@..@@..@@....@@...     |_|
    # |_|     .@@@@@@@@..@@@@..@@@..@@@.....@@...     |_|
    # |_|                                             |_|
    # |_|                                             |_|
    # |_|                                             |_|
    # |_|                                             |_|
    # |_|                                             |_|
    # |_| _  _  _  _  _  _  _  _  _  _  _  _  _  _  _ |_|
    # |_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_||_|
    # """
    # )