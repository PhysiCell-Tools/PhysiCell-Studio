from PyQt5.QtWidgets import QFrame, QCheckBox, QWidget, QLineEdit
from PyQt5.QtGui import QValidator, QDoubleValidator

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


class QLineEdit_custom(QLineEdit):
    def __init__(self):
        super(QLineEdit, self).__init__()
        self.validator = None  # Add a validator attribute
        self.textChanged.connect(self.check_validity)

    def setValidator(self, validator):
        super().setValidator(validator)
        self.validator = validator

    def check_validity(self, text):
        if self.validator and self.validator.validate(text, 0)[0] != QValidator.Acceptable:
            self.setStyleSheet(self.invalid_style)
        else:
            self.setStyleSheet(self.valid_style)

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

class DoubleValidatorWidgetBounded(QValidator):
    def __init__(self, bottom=None, top=None, bottom_transform=lambda x: x, top_transform=lambda x: x):
        super().__init__()
        # check if bottom is widget or double
        self.qdouble_validator = QDoubleValidator()
        if isinstance(bottom, QWidget):
            self.bottom = bottom
            self.bottom_fn = bottom_transform
        else:
            if bottom_transform is not None:
                bottom = bottom_transform(bottom)
            self.qdouble_validator.setBottom(bottom)
            self.bottom = None
            self.bottom_fn = None
        if isinstance(top, QWidget):
            self.top = top
            self.top_fn = top_transform
        else:
            if top_transform is not None:
                top = top_transform(top)
            self.qdouble_validator.setTop(top)
            self.top = None
            self.top_fn = None

    
    def validate(self, text, pos):
        if text == "":
            return QValidator.Intermediate, text, pos

        self.validate_bound('bottom', text, pos)
        self.validate_bound('top', text, pos)

        return self.qdouble_validator.validate(text, pos)

    def validate_bound(self, bound_name, text, pos):
        bound = getattr(self, bound_name, None)
        if bound is not None:
            bound_text = bound.text()
            if bound_text != "":
                try:
                    new_bound = getattr(self, f'{bound_name}_fn')(float(bound_text))
                except Exception as e:
                    print(f"Invalid value for {bound_name} in DoubleValidatorWidgetBounded: {e}")
                    return QValidator.Intermediate, text, pos
                if new_bound != new_bound:
                    print(f"Invalid value for {bound_name} in DoubleValidatorWidgetBounded: {new_bound}")
                    return QValidator.Intermediate, text, pos
                getattr(self.qdouble_validator, f'set{bound_name.capitalize()}')(new_bound)
