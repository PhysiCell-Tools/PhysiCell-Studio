from PyQt5 import QtCore
from PyQt5.QtWidgets import QFrame, QCheckBox, QLabel, QLineEdit
from PyQt5.QtGui import QValidator

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

class QLabelSeparator(QLabel):
    def __init__(self, text):
        super(QLabel, self).__init__(text)
        self.setStyleSheet("background-color: orange;")
        self.setAlignment(QtCore.Qt.AlignCenter)

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

class QLineEdit_custom(QLineEdit):
    def __init__(self, **kwargs):
        super(QLineEdit, self).__init__(**kwargs)
        self.validator = None  # Add a validator attribute
        self.textChanged.connect(self.check_validity)
        self.check_validity(self.text())

    def setValidator(self, validator):
        super().setValidator(validator)
        self.validator = validator

    def check_validity(self, text=None):
        if text is None:
            text = self.text()
        if self.validator and self.validator.validate(text, 0)[0] != QValidator.Acceptable:
            self.setStyleSheet(self.invalid_style)
            return False
        else:
            self.setStyleSheet(self.valid_style)
            return True

    valid_style = """
        QLineEdit {
            background-color: rgb(255,255,255);
            border: 1px solid #5A5A5A;
            width : 15px;
            height : 15px;
            border-radius : 3px;
        }
        QLineEdit:disabled
        {
            background-color:lightgray;
            color: black;
        }
        """

    invalid_style = """
        QLineEdit {
            background-color: rgba(255, 0, 0, 0.5);
            border: 1px solid #5A5A5A;
            width : 15px;
            height : 15px;
            border-radius : 3px;
        }
        QLineEdit:disabled
        {
            background-color:lightgray;
            color: black;
        }
        """
