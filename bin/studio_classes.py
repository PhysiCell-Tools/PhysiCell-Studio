import sys

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QFrame, QCheckBox, QWidget, QLineEdit, QComboBox, QLabel, QCompleter, QToolTip, QRadioButton, QVBoxLayout, QDialog
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QValidator, QDoubleValidator
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QEvent, QByteArray

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

class StudioTab(QWidget):
    def __init__(self, xml_creator):
        super().__init__()
        self.xml_creator = xml_creator

class CellDefSubTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.celldef_tab = parent
        self.xml_creator = parent.xml_creator
        self.param_d = self.celldef_tab.param_d # make this dict easily accessible here as well
        setattr(self.celldef_tab, self.type_to_name(), self) # set this object as an attribute of the parent celldef_tab
        
    def type_to_name(self):
        # take the name of the object class, e.g. CycleTab, and convert it to a lowercase string with underscores, e.g. cycle_tab
        name = type(self).__name__
        name = name[0].lower() + name[1:]
        for i, letter in enumerate(name):
            if letter.isupper():
                name = name[:i] + '_' + letter.lower() + name[i+1:]
        return name

    def get_current_celldef(self):
        return self.celldef_tab.current_cell_def

# organizers
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

# custom widgets
class QCheckBox_custom(QCheckBox):  # it's insane to have to do this!
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

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
                QCheckBox:indicator:disabled
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

    def check_current_validity(self):
        self.check_validity(self.text())
        
    valid_style = """
            QLineEdit {
                color: black;
                background-color: white;
            }
            QLineEdit:disabled
            {
                color: black;
                background-color:gray;
            }
            """

    invalid_style = """
            QLineEdit {
                color: black;
                background-color: rgba(255, 0, 0, 0.5);
            }
            QLineEdit:disabled {
                color: black;
                background-color:gray;
            }
            """

    def set_formatter(self, bval: bool=True, ndigits: int=5):
        if bval:
            self.editingFinished.connect(lambda: self.format_text(ndigits=ndigits))
        else:
            self.editingFinished.disconnect()

    def format_text(self, ndigits: int=5):
        try:
            self.full_value = self.text()
            value = float(self.full_value)
            if value == 0:
                formatted_text = "0"
            elif abs(value) < 10**-ndigits:
                formatted_text = f"{value:.{ndigits}e}"
            else:
                formatted_text = f"{value:.{ndigits}f}".rstrip('0').rstrip('.')
            self.blockSignals(True)
            self.setText(formatted_text)
            self.blockSignals(False)
        except ValueError:
            pass

radiobutton_style = """
QRadioButton {
    spacing: 4px; /* Space between indicator and text */
    padding-left: 4px;
}
QRadioButton::indicator {
    width: 12;
    height: 12;
}
QRadioButton::indicator:unchecked {
    image: url(images:RadioButtonUnchecked.svg);
}
QRadioButton::indicator:checked {
    image: url(images:RadioButtonChecked.svg);
}
QRadioButton::indicator:disabled:checked {
    image: url(images:RadioButtonDisabledChecked.svg);
}
"""
class QRadioButton_custom(QRadioButton):
    def __init__(self, text, **kwargs):
        super(QRadioButton, self).__init__(text, **kwargs)
        self.setStyleSheet(radiobutton_style)

class QComboBox_custom(QComboBox):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("QComboBox{color: #000000; background-color: #FFFFFF;}")
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

# hover widgets
class HoverWidget(QWidget):
    hover_enabled = True
    def __init__(self, hover_text=None, parent=None, hover_enabled=True):
        super().__init__(parent)
        self.setMouseTracking(True)  # Enable mouse tracking
        self.hover_text = hover_text
        self.setStyleSheet("QToolTip { \
                            background-color: black; \
                            color: white; \
                            border: 1px solid black; \
                            border-radius: 5px; \
                            padding: 5px; \
                            }")
        self.hover_enabled = hover_enabled

    def setHoverText(self, hover_text):
        self.hover_text = hover_text

    def event(self, event):
        if not self.hover_enabled:
            return super().event(event)
        if event.type() == QEvent.Enter:
            # Display tooltip when the mouse enters the checkbox
            QToolTip.showText(event.globalPos(), self.hover_text, self)
        elif event.type() == QEvent.Leave:
            # Hide tooltip when the mouse leaves the checkbox
            QToolTip.hideText()
        return super().event(event)

class HoverCheckBox(QCheckBox, HoverWidget):
    def __init__(self, text, hover_text, parent=None):
        super().__init__(text, parent)
        self.setText(text)
        self.setHoverText(hover_text)

class HoverCombobox(QComboBox, HoverWidget):
    def __init__(self, hover_text: str, parent=None):
        super().__init__(parent)
        self.setHoverText(hover_text)

class HoverLabel(QLabel, HoverWidget):
    def __init__(self, label_text, hover_text, parent=None):
        super().__init__(parent)
        self.setText(label_text)
        self.setHoverText(hover_text)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #333;
                background-color: #f0f0f0;
                border: 2px solid #333333;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
        """)
      
class HoverSvgWidget(QSvgWidget, HoverWidget):
    def __init__(self, hover_text, parent=None):
        super().__init__(parent)
        self.setHoverText(hover_text)

class HoverHelp(HoverSvgWidget):
    icon = None
    def __init__(self, hover_text, parent=None, width=15, height=15):
        super().__init__(hover_text, parent)
        self.setFixedSize(width, height)

    def show_icon(self):
        self.load(self.icon)
        self.hover_enabled = True

    def hide_icon(self):
        self.load(QByteArray()) # passing in an empty file path (self.load("")) works, but prints endless warnings about not being able to load the file
        self.hover_enabled = False
class HoverWarning(HoverHelp):
    def __init__(self, hover_text, parent=None, width=15, height=15):
        super().__init__(hover_text, parent)
        self.setFixedSize(width, height)
        self.icon = "images:warning.svg"
class HoverQuestion(HoverHelp):
    def __init__(self, hover_text, parent=None, width=15, height=15):
        super().__init__(hover_text, parent)
        self.setFixedSize(width, height)
        self.icon = "images:info.svg"

# validators
class DoubleValidatorWidgetBounded(QValidator):
    # a validator that uses other widgets to set the bounds of a QDoubleValidator
    def __init__(self, bottom=None, top=None, bottom_transform=lambda x: x, top_transform=lambda x: x):
        super().__init__()
        # check if bottom is widget or double
        self.qdouble_validator = QDoubleValidator()
        if isinstance(bottom, QWidget):
            # then just record the info so the validator can access later
            self.bottom = bottom
            self.bottom_fn = bottom_transform
        else:
            # then just a normal bottom bound: transform if desired and set. then reset bottom and bottom_fn to None so they are not used later
            if bottom_transform is not None:
                bottom = bottom_transform(bottom)
            self.qdouble_validator.setBottom(bottom)
            self.bottom = None
            self.bottom_fn = None
        if isinstance(top, QWidget):
            # then just record the info so the validator can access later
            self.top = top
            self.top_fn = top_transform
        elif top != None:
            # then just a normal top bound: transform if desired and set. then reset top and top_fn to None so they are not used later
            if top_transform is not None:
                top = top_transform(top)
            self.qdouble_validator.setTop(top)
            self.top = None
            self.top_fn = None

    
    def validate(self, text, pos):
        if text == "":
            return QValidator.Intermediate, text, pos

        result_bottom = self.validate_bound('bottom', text, pos)
        if result_bottom is not None:
            return result_bottom
        result_top = self.validate_bound('top', text, pos)
        if result_top is not None:
            return result_top

        return self.qdouble_validator.validate(text, pos)

    def validate_bound(self, bound_name, text, pos):
        bound = getattr(self, bound_name, None)
        if bound is None:
            return
        
        bound_text = bound.text()
        if bound_text == "":
            return
        
        try:
            # if bound is a widget, then call the transform function on the text
            new_bound = getattr(self, f'{bound_name}_fn')(float(bound_text))
        except Exception as e:
            print(f"Invalid value for {bound_name} in DoubleValidatorWidgetBounded: {e}")
            return QValidator.Intermediate, text, pos

        if new_bound != new_bound:
            # then new_bound is nan
            print(f"Invalid value for {bound_name} in DoubleValidatorWidgetBounded: {new_bound}")
            return QValidator.Intermediate, text, pos

        getattr(self.qdouble_validator, f'set{bound_name.capitalize()}')(new_bound)
        
class AttackRateValidator(QValidator):
    def __init__(self, cell_def_tab):
        super().__init__()
        self.cell_def_tab = cell_def_tab
        self.qdouble_validator = QDoubleValidator(bottom=0.0)

    def validate(self, text, pos):
        if text == "":
            return QValidator.Intermediate, text, pos

        dt = self.cell_def_tab.config_tab.mechanics_dt.text()
        if dt == "" or float(dt) == 0:
            return QValidator.Intermediate, text, pos
        dt = float(dt)

        attacking_cell_def = self.cell_def_tab.current_cell_def
        defending_cell_def = self.cell_def_tab.attack_rate_dropdown.currentText()
        try:
            immunogenicity = float(self.cell_def_tab.param_d[attacking_cell_def]['immunogenicity'][defending_cell_def])
        except Exception as e:
            print(f"Error in AttackRateValidator: {e}")
            return QValidator.Intermediate, text, pos
        
        # get machine precision for float
        top_val = 1/(dt*immunogenicity)
        top_val *= 1 + sys.float_info.epsilon
        self.qdouble_validator.setTop(top_val)
        return self.qdouble_validator.validate(text, pos)
  
class OptionalDoubleValidator(QDoubleValidator):
    def __init__(self, **kwargs):
        super().__init__()
        self.qdouble_validator = QDoubleValidator(**kwargs)

    def validate(self, text, pos):
        if text == "":
            return QValidator.Acceptable, text, pos
        return self.qdouble_validator.validate(text, pos)

class DoubleValidatorOpenInterval(QDoubleValidator):
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