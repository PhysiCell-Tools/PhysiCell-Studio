from PyQt5.QtWidgets import QFrame, QCheckBox, QVBoxLayout, QDialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        # self.setFrameShadow(QFrame.Plain)
        self.setStyleSheet("border:1px solid black")

class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)
        # self.setFrameShadow(QFrame.Plain)
        self.setStyleSheet("border:1px solid black")

class QCheckBox_custom(QCheckBox):  # it's insane to have to do this!
    def __init__(self,name):
        super(QCheckBox, self).__init__(name)

        checkbox_style = """
                QCheckBox::indicator:checked {
                    background-color: rgb(255,255,255);
                    border: 1px solid #5A5A5A;
                    width : 15px;
                    height : 15px;
                    border-radius : 3px;
                    image: url(images:checkmark.png);
                }
                QCheckBox::indicator:unchecked
                {
                    background-color: rgb(255,255,255);
                    border: 1px solid #5A5A5A;
                    width : 15px;
                    height : 15px;
                    border-radius : 3px;
                }
                QCheckBox:disabled
                {
                    background-color:lightgray;
                }
                """
        self.setStyleSheet(checkbox_style)

class LegendWindow(QDialog):
    def __init__(self, parent=None, legend_artists=None, legend_labels=None, legend_title=None):
        super(LegendWindow, self).__init__(parent)
        self.setWindowTitle(f"Legend: {legend_title}")
        self.setGeometry(100, 100, 300, 200)

        # Create a figure for the legend
        self.figure = plt.figure()
        self.canvas = FigureCanvasQTAgg(self.figure)

        # Create the legend
        ax = self.figure.add_subplot(111)
        ax.legend(legend_artists, legend_labels)
        ax.axis('off')  # Turn off the axis

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
