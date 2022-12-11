import sys
#from PyQt4.QtGui import *
from PyQt5 import QtGui
# from PyQt5.QtGui import QDoubleValidator
#from PyQt5.QtCore import QString
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton,QLabel,QLineEdit,QTextEdit,QGridLayout

app = QApplication(sys.argv) #ignore()
window = QWidget()
window.setWindowTitle("numfields")
window.show()

fval = 123456.789123
val1Label = QLabel("val")
val1 = QLineEdit()
val1.setValidator(QtGui.QDoubleValidator())
val1.setText(str(fval))

val2Label = QLabel("val (MaxLength=10)")
val2 = QLineEdit()
val2.setValidator(QtGui.QDoubleValidator())
val2.setMaxLength(10)
val2.setText(str(fval))

val3Label = QLabel("val (6 dec places)")
val3 = QLineEdit()
val3.setValidator(QtGui.QDoubleValidator())
val3.setText(f'{fval:.6f}')

val4Label = QLabel("val (6 sig digits)")
val4 = QLineEdit()
val4.setValidator(QtGui.QDoubleValidator())
val4.setText(f'{fval:.6}')

# Put the widgets in a layout (now they start to appear):
layout = QGridLayout(window)
layout.addWidget(val1Label, 0, 0)  # row,col
layout.addWidget(val1, 0, 1)

layout.addWidget(val2Label, 1, 0)
layout.addWidget(val2, 1, 1)

layout.addWidget(val3Label, 2, 0)
layout.addWidget(val3, 2, 1)

layout.addWidget(val4Label, 3, 0)
layout.addWidget(val4, 3, 1)

layout.setRowStretch(3, 1)



# [Resizing the window]
# Let's resize the window:
#window.resize(480, 160)
# The widgets are managed by the layout...
window.resize(320, 180)

# Start the event loop...
sys.exit(app.exec_())
