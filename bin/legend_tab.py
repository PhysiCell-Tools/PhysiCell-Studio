"""
Authors:
Randy Heiland (heiland@iu.edu)
Adam Morrow, Grant Waldrow, Drew Willis, Kim Crevecoeur
Dr. Paul Macklin (macklinp@iu.edu)
"""

import os
import time
from pathlib import Path
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QFormLayout,QLineEdit, QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QRectF


class SvgWidget(QSvgWidget):

    def __init__(self, *args):
        QSvgWidget.__init__(self, *args)

    def paintEvent(self, event):
        renderer = self.renderer()
        if renderer != None:
            painter = QPainter(self)
            size = renderer.defaultSize()
            ratio = size.height()/size.width()
            length = min(self.width(), self.height())
            renderer.render(painter, QRectF(0, 0, length, ratio * length))
            painter.end()

class Legend(QWidget):
    # def __init__(self, doc_absolute_path, nanohub_flag):
    def __init__(self, nanohub_flag):
        super().__init__()

        # self.doc_absolute_path = doc_absolute_path

        self.process = None
        self.output_dir = '.'   # set in pmb.py
        self.current_dir = '.'   # reset in pmb.py
        self.pmb_data_dir = ''   # reset in pmb.py
        
        #-------------------------------------------
        self.scroll = QScrollArea()  # might contain centralWidget

        self.svgView = SvgWidget()
        # self.svgView.renderer().setAspectRatioMode(Qt.KeepAspectRatio)  # for new version of PyQt5

        # self.svg.load("tmpdir/legend.svg")
        # if nanohub_flag:
        #     self.text.setOpenLinks(False)
        #     self.text.anchorClicked.connect(self.followLink)
        # else:
        #     self.text.setOpenExternalLinks(True)

        # fname = os.path.join(self.doc_absolute_path,"about.html")
        # f = QtCore.QFile(fname)
        # f.open(QtCore.QFile.ReadOnly|QtCore.QFile.Text)
        # istream = QtCore.QTextStream(f)
        # self.text.setHtml(istream.readAll())
        # f.close()

        self.vbox = QVBoxLayout()
        # self.vbox.addStretch(0)
        # self.vbox.addStretch()

        #==================================================================
        self.svgView.setLayout(self.vbox)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)
        # self.scroll.setWidgetResizable(False)

        self.scroll.setWidget(self.svgView) 
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.scroll)

    def clear_legend(self):
        legend_file = os.path.join(self.pmb_data_dir, 'empty_legend.svg')
        self.svgView.load(legend_file)

    def reload_legend(self):
        # print('reload_legend(): cwd = self.output_dir = ',os.getcwd())
        # self.output_dir = os.getcwd()
        print('reload_legend(): self.output_dir = ',self.output_dir)

        for idx in range(4):
            print("waiting for creation of legend.svg ...",idx)
            # path = Path("legend.svg")
            path = Path(self.output_dir,"legend.svg")
            # path = Path(self.current_dir,self.output_dir,"legend.svg")
            print("path = ",path)
            if path.is_file():
            # try:
                # self.svgView.load("legend.svg")
                full_fname = os.path.join(self.output_dir, "legend.svg")
                # full_fname = os.path.join(self.current_dir,self.output_dir, "legend.svg")
                print("legend_tab.py: full_fname = ",full_fname)
                self.svgView.load(full_fname)
                break
            # except:
            #     path = Path(self.current_dir,self.output_dir,"legend.svg")
            #     time.sleep(1)
            else:
                path = Path(self.output_dir,"legend.svg")
                # path = Path(self.current_dir,self.output_dir,"legend.svg")
                time.sleep(1)
        # try:
        #     self.svg.load("legend.svg")
        # except:
        #     print("cannot open legend.svg")
        #     sys.exit(1)
        # self.svg.load("legend.svg")
