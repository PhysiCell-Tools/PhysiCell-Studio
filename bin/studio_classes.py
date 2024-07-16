from PyQt5 import QtCore
from PyQt5.QtWidgets import QFrame, QCheckBox, QLabel, QComboBox, QCompleter, QLineEdit, QWidget, QToolTip
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QEvent
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

class ExtendedCombo( QComboBox ):
    def __init__( self,  parent = None):
        super( ExtendedCombo, self ).__init__( parent )

        self.setFocusPolicy( Qt.StrongFocus )
        self.setEditable( True )
        self.completer = QCompleter( self )

        # always show all completions
        self.completer.setCompletionMode( QCompleter.UnfilteredPopupCompletion )
        self.pFilterModel = QSortFilterProxyModel( self )
        self.pFilterModel.setFilterCaseSensitivity( Qt.CaseInsensitive )

        self.completer.setPopup( self.view() )

        self.setCompleter( self.completer )

        self.lineEdit().textEdited[str].connect( self.pFilterModel.setFilterFixedString )
        self.completer.activated.connect(self.setTextIfCompleterIsClicked)

    def setModel( self, model ):
        super(ExtendedCombo, self).setModel( model )
        self.pFilterModel.setSourceModel( model )
        self.completer.setModel(self.pFilterModel)

    def setModelColumn( self, column ):
        self.completer.setCompletionColumn( column )
        self.pFilterModel.setFilterKeyColumn( column )
        super(ExtendedCombo, self).setModelColumn( column )

    def view( self ):
        return self.completer.popup()

    def index( self ):
        return self.currentIndex()

    def setTextIfCompleterIsClicked(self, text):
      if text:
        index = self.findText(text)
        self.setCurrentIndex(index)

class QLineEdit_custom(QLineEdit):
    def __init__(self, **kwargs):
        super(QLineEdit, self).__init__(**kwargs)
        self.validator = None  # Add a validator attribute
        self.textChanged.connect(self.check_validity)
        self.check_validity(self.text())

    def setValidator(self, validator):
        super().setValidator(validator)
        self.validator = validator

    def check_validity(self, text):
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

# create a validator that checks the text is either empty or a valid double
class OptionalDoubleValidator(QDoubleValidator):
    def __init__(self, **kwargs):
        super().__init__()
        self.qdouble_validator = QDoubleValidator(**kwargs)

    def validate(self, text, pos):
        if text == "":
            return QValidator.Acceptable, text, pos
        return self.qdouble_validator.validate(text, pos)

class HoverWidget(QWidget):
    def __init__(self, hover_text: str, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)  # Enable mouse tracking
        self.hover_text = hover_text

    def event(self, event):
        if event.type() == QEvent.Enter:
            # Display tooltip when the mouse enters the widget
            self.setToolTip(self.hover_text)
        elif event.type() == QEvent.Leave:
            # Clear tooltip when the mouse leaves the widget
            self.setToolTip('')
        return super().event(event)

class HoverCheckBox(QCheckBox):
    def __init__(self, text, hover_text, parent=None):
        super().__init__(text, parent)
        self.setMouseTracking(True)  # Enable mouse tracking
        self.hover_text = hover_text

    def event(self, event):
        if event.type() == QEvent.Enter:
            # Display tooltip when the mouse enters the checkbox
            QToolTip.showText(event.globalPos(), self.hover_text, self)
        elif event.type() == QEvent.Leave:
            # Hide tooltip when the mouse leaves the checkbox
            QToolTip.hideText()
        return super().event(event)
    
class QDoubleValidatorOpenInterval(QDoubleValidator):
    def __init__(self, bottom=float('-inf'), top=float('inf'), decimals=1000, parent=None):
        super().__init__(bottom, top, decimals, parent)
        self.bottom = bottom
        self.top = top

    def validate(self, input, pos):
        state, value, pos = super().validate(input, pos)

        if state == QDoubleValidator.Acceptable:
            if float(value) <= self.bottom or float(value) >= self.top:
                state = QDoubleValidator.Intermediate

        return state, value, pos