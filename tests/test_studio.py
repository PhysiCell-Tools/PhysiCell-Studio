#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import filecmp

import pytest
from PyQt5 import QtCore, QtGui, QtTest, QtWidgets
from PyQt5.QtCore import QCoreApplication, QObject, Qt
from PyQt5.QtWidgets import *
from pytestqt.plugin import QtBot

# GUI = __import__("studio")
sys.path.append('../bin')
import studio_for_pytest as studio


@pytest.fixture(scope="module")
def qtbot_session(qapp, request):
    print("  SETUP qtbot")
    result = QtBot(qapp)
    with capture_exceptions() as exceptions:
        yield result
    print("  TEARDOWN qtbot")


@pytest.fixture(scope="module")
def Viewer(request):
    print("  SETUP GUI")

    # app, imageViewer = GUI.main_GUI()
    # app, imageViewer = GUI.studio_app
    # app, imageViewer = GUI.main()
    app, imageViewer = studio.main()
    # imageViewer.setAttribute(Qt.WA_DontShowOnScreen, True)
    qtbotbis = QtBot(app)
    # QtTest.QTest.qWait(0.5 * 1000)
    # QtTest.QTest.qWait(1000)

    return  app, imageViewer, qtbotbis
    # return  app, qtbotbis

def test_default_ctype(Viewer):
    print("  test_default_ctype")
    app, viewer_w, qtbot = Viewer
    assert list(viewer_w.celldef_tab.param_d.keys()) == ['default']

def test_rename_default(Viewer):
    # print("  test_rename_cancer")
    app, viewer_w, qtbot = Viewer
    # # viewer_w.celldef_tab.renamed_celltype("default","cancer")

    # copy/pasted from cell_def_tab.py module:  def tree_item_changed_cb(self, it,col):
    new_name = "cancer"
    viewer_w.celldef_tab.current_cell_def = new_name
    # viewer_w.celldef_tab.param_d[viewer_w.celldef_tab.current_cell_def] = viewer_w.celldef_tab.param_d.pop("default")  # sweet
    viewer_w.celldef_tab.param_d["cancer"] = viewer_w.celldef_tab.param_d.pop("default")  # sweet

    viewer_w.celldef_tab.live_phagocytosis_celltype = new_name
    viewer_w.celldef_tab.attack_rate_celltype = new_name
    viewer_w.celldef_tab.fusion_rate_celltype = new_name
    viewer_w.celldef_tab.transformation_rate_celltype = new_name

    # call the method that completes the rename
    viewer_w.celldef_tab.renamed_celltype("default", new_name)

    # This didn't seem to fix the original cell_def_tab.py code, so we modified for pytest (search for "pytest", in that module, in /tests)
    # # treeitem = QTreeWidgetItem([cdname, viewer_w.celldef_tab.param_d[cdname]["ID"]])
    # treeitem = QTreeWidgetItem([new_name, "0"])
    # treeitem.setFlags(treeitem.flags() | QtCore.Qt.ItemIsEditable)
    # # viewer_w.celldef_tab.tree.insertTopLevelItem(num_items,treeitem)
    # viewer_w.celldef_tab.tree.setCurrentItem(treeitem)

    out_file = "rename_default_cancer.xml"
    viewer_w.current_xml_file = out_file
    viewer_w.save_cb()

    # assert list(viewer_w.celldef_tab.param_d.keys()) == ['cancer']
    assert filecmp.cmp(out_file, os.path.join("groundtruth",out_file))


# NOTE!  tests need to be ordered if they involve the generation of random suffixes on [cell def] names
def test_new_cell_def(Viewer):
    app, viewer_w, qtbot = Viewer
    viewer_w.celldef_tab.new_cell_def()
    out_file = "new_cell_def1.xml"
    viewer_w.current_xml_file = out_file
    viewer_w.save_cb()
    # assert filecmp.cmp(out_file, "groundtruth/"+out_file)
    assert filecmp.cmp(out_file, os.path.join("groundtruth",out_file))

def test_copy_cell_def(Viewer):
    app, viewer_w, qtbot = Viewer
    # viewer_w.celldef_tab.current_cell_def = "cancer"
    viewer_w.celldef_tab.copy_cell_def()
    out_file = "copy_cell_def1.xml"
    viewer_w.current_xml_file = out_file
    viewer_w.save_cb()
    assert filecmp.cmp(out_file, os.path.join("groundtruth",out_file))

def test_threads(Viewer):
    print("  test_threads")
    app, viewer_w, qtbot = Viewer

    assert viewer_w.config_tab.num_threads.text() == '4'
    # assert viewer_w.config_tab.num_threads.text() == '5'

# def test_save(Viewer):
#     app, viewer_w, qtbot = Viewer
#     viewer_w.current_xml_file = "foobar.xml"
#     viewer_w.save_cb()
#     assert True