import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QScrollArea, QVBoxLayout,QHBoxLayout, QSlider, QLabel, QMainWindow, QComboBox, QCheckBox, QPushButton, QFileDialog, QFrame
from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

def Multivariate_hillFunc(signals_U, halfmaxs_U, hillpowers_U, signals_D, halfmaxs_D, hillpowers_D):
    sum_U = 0; sum_D = 0 
    for id_Up in range(len(signals_U)):
        if ( type(signals_U[id_Up]) == np.ndarray):
            proj_signal = signals_U[id_Up]
        sum_U += (signals_U[id_Up]/halfmaxs_U[id_Up])**hillpowers_U[id_Up]
    for id_Dw in range(len(signals_D)):
        if ( type(signals_D[id_Dw]) == np.ndarray): 
            proj_signal = signals_D[id_Dw]
        sum_D += (signals_D[id_Dw]/halfmaxs_D[id_Dw])**hillpowers_D[id_Dw]
    H_U = sum_U/(1+sum_U)
    H_D = sum_D/(1+sum_D)
    return proj_signal, H_U, H_D

class LabeledSlider(QWidget):
    def __init__(self, description, categories, parent=None):
        super().__init__(parent)
        self.categories = categories
        self.slider = QSlider(Qt.Horizontal)
        self.label = QLabel()
        self.description = description
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        # Set up the slider
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(self.categories) - 1)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self.update_label)
        # Initial label update
        self.update_label()
        # Add widgets to the layout
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        self.setLayout(layout)
    def tickValue(self, index):
        if 0 <= index < len(self.categories):
            return self.categories[index]
        return None
    def tickIndex(self, value):
        for index, val in enumerate(self.categories):
            if value == val: return index
        return None
    def update_label(self):
        value = self.tickValue( self.slider.value() )
        self.label.setText(f"{self.description}: {value}")

class MyWidget_behavior(QWidget):
    def __init__(self, name, base_v, max_up , max_down):
        super().__init__()
        self.name = name
        frac_var = 1.0 # percentage of variation -/+ in the base, up, down sliders of behaviors
        self.base_min = base_v*(1-frac_var)
        self.base_max = base_v*(1+frac_var)
        self.max_up_min = max_up*(1-frac_var)
        self.max_up_max = max_up*(1+frac_var)
        self.max_down_min = max_down*(1-frac_var)
        self.max_down_max = max_down*(1-frac_var)
        self.init_ui()
    def init_ui(self):
        layout = QHBoxLayout()
        Base_behavior_values = ["%e" % x for x in np.linspace(self.base_min, self.base_max, num=11, endpoint=True)]
        Max_behavior_values = ["%e" % x for x in np.linspace(self.max_up_min,self.max_up_max, num=11, endpoint=True)]
        Min_behavior_values = ["%e" % x for x in np.linspace(self.max_down_min, self.max_down_max, num=11, endpoint=True)]
        self.slider_base_behavior = LabeledSlider("Base behavior", Base_behavior_values)
        self.slider_up_behavior = LabeledSlider("Max up regularion", Max_behavior_values)
        self.slider_down_behavior = LabeledSlider("Max down regulation", Min_behavior_values)
        # Set initial value
        self.slider_base_behavior.slider.setValue(round(0.5*len(Base_behavior_values)) -1 ) # start in the center of the bar
        self.slider_up_behavior.slider.setValue(round(0.5*len(Max_behavior_values)) -1 ) # start in the center of the bar
        self.slider_down_behavior.slider.setValue(round(0.5*len(Min_behavior_values)) -1 ) # start in the center of the bar
        layout.addWidget(self.slider_base_behavior)
        layout.addWidget(self.slider_up_behavior)
        layout.addWidget(self.slider_down_behavior)
        self.setLayout(layout)

class MyWidget_signal(QWidget):
    def __init__(self, sig_name, sig_direction , sig_halfmax, sig_hillpower):
        super().__init__()
        self.sig_name = sig_name
        self.sig_direction = sig_direction
        frac_var = 1.0 # percentage of variation -/+ in signal and halfmax
        self.sig_min = sig_halfmax*(1-frac_var)
        self.sig_max = sig_halfmax*(1+frac_var)
        self.sig_halfmax_min = sig_halfmax*(1-(frac_var-0.1)) # min halfmax cannot be 0.
        self.sig_halfmax_max = sig_halfmax*(1+(frac_var-0.1))
        self.sig_hillpower = sig_hillpower
        self.sig_hillpower_min = 0
        self.sig_hillpower_max = round(sig_hillpower*(1+frac_var))
        if ( self.sig_hillpower_max < 20 ): self.sig_hillpower_max = 20
        self.init_ui()
    def init_ui(self):
        layout = QHBoxLayout()
        Signal_values = ["%e" % x for x in np.linspace(self.sig_min, self.sig_max, num=11, endpoint=True)]
        HalfMax_signal_values = ["%e" % x for x in np.linspace(self.sig_halfmax_min, self.sig_halfmax_max, num=11, endpoint=True)]
        HillPower_values = ["%d" % x for x in range(self.sig_hillpower_min, self.sig_hillpower_max+1)]
        self.slider_signal = LabeledSlider(self.sig_name,  Signal_values)
        self.slider_halfmax_signal = LabeledSlider("Half max", HalfMax_signal_values) 
        self.slider_hillpower = LabeledSlider("Hill power", HillPower_values)
        # Set initial value
        self.slider_signal.slider.setValue(round(0.5*len(Signal_values)) - 1)
        self.slider_halfmax_signal.slider.setValue(round(0.5*len(HalfMax_signal_values)) - 1) 
        self.slider_hillpower.slider.setValue( self.slider_hillpower.tickIndex(str(self.sig_hillpower)) )
        layout.addWidget(self.slider_signal)
        layout.addWidget(self.slider_halfmax_signal)
        layout.addWidget(self.slider_hillpower)
        layout.addWidget(QLabel(f'Direction: {self.sig_direction}'))
        self.setLayout(layout)

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)

class MainPlot(QMainWindow):
    def __init__(self, combobox_cell, combobox_behavior, combobox_behaviorplot, layout_behavior_sliders, layout_signals, checkbox):
        super(MainPlot, self).__init__()
        self.combobox_cell = combobox_cell
        self.combobox_behavior = combobox_behavior
        self.combobox_behaviorplot = combobox_behaviorplot
        self.layout_behavior_sliders = layout_behavior_sliders
        self.layout_signals = layout_signals
        self.checkbox = checkbox
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.setCentralWidget(self.canvas)
        self.update_plot()
        self.show()
        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()
    def update_plot(self):
        self.canvas.axes.cla()  # Clear the canvas.
        listSigUpReg = [];  listHalfMaxUpReg = []; listHillPowerUpReg = []
        listSigDownReg = [];  listHalfMaxDownReg = []; listHillPowerDownReg = []
        AxesFixed = True
        Selected_sig = self.combobox_behaviorplot.currentText()
        # Layout of behavior sliders (Only one)
        for i in range(self.layout_behavior_sliders.layout().count()):
            widget = self.layout_behavior_sliders.layout().itemAt(i).widget()
            behavior_name = widget.name
            b_0 = float( widget.slider_base_behavior.tickValue( widget.slider_base_behavior.slider.value() ) )
            b_M = float( widget.slider_up_behavior.tickValue( widget.slider_up_behavior.slider.value() ) )
            b_m = float( widget.slider_down_behavior.tickValue( widget.slider_down_behavior.slider.value() ) )
        # Layout of signals sliders (Dynamic quantity)
        for i in range(self.layout_signals.layout().count()):
            widget = self.layout_signals.layout().itemAt(i).widget()
            sig_halfmax = float( widget.slider_halfmax_signal.tickValue( widget.slider_halfmax_signal.slider.value() ) )
            sig_hillpower = float( widget.slider_hillpower.tickValue( widget.slider_hillpower.slider.value() ) )
            if (Selected_sig == widget.sig_name):
                sig_value = np.linspace(widget.sig_min, widget.sig_max, num=1000)
                widget.slider_signal.slider.setEnabled(False)
                halfMax_value = sig_halfmax
            else:
                widget.slider_signal.slider.setEnabled(True)
                sig_value = float( widget.slider_signal.tickValue( widget.slider_signal.slider.value() ) ) 
            if ( widget.sig_direction == 'increases' ):
                listSigUpReg.append(sig_value); listHalfMaxUpReg.append(sig_halfmax); listHillPowerUpReg.append(sig_hillpower)
            elif( widget.sig_direction == 'decreases' ):
                listSigDownReg.append(sig_value); listHalfMaxDownReg.append(sig_halfmax); listHillPowerDownReg.append(sig_hillpower)
            else:
                print(f"Error: signal increases or decreases the behaviour! Check typo in {widget.sig_direction}.")
                sys.exit(-1)
        # checkbox is unchecked.
        if (self.checkbox.checkState() == 0): 
            AxesFixed = False
        # Calculate the hill fucntion
        if (len(listSigUpReg) > 0):
            signal, H_U, H_D = Multivariate_hillFunc(listSigUpReg, listHalfMaxUpReg, listHillPowerUpReg, listSigDownReg, listHalfMaxDownReg, listHillPowerDownReg)
            self.canvas.axes.set_title(f"Behavior: {behavior_name}")
            self.canvas.axes.plot(signal, (b_0 + (b_M - b_0)*H_U)*(1-H_D) + H_D*b_m, 'r')
            self.canvas.axes.axvline(halfMax_value, ls='--', color = 'k')
            self.canvas.axes.set_ylabel('b(U,D)')
            self.canvas.axes.set_xlabel(Selected_sig)
            if (AxesFixed):  self.canvas.axes.set_ylim(b_m, b_M)
        # Trigger the canvas to update and redraw.
        self.canvas.fig.tight_layout()
        self.canvas.draw()

class CSVLoader(QWidget):
    def __init__(self, csvFile=None, dataframe=None, parent=None):
        super().__init__()
        layout = QHBoxLayout()
        self.file_label = QLabel("No file loaded")
        self.dataframe = None
        if csvFile: self.file_label.setText(f"{csvFile}")
        if isinstance(dataframe, pd.DataFrame): self.dataframe = dataframe
        # Button to load
        self.load_button = QPushButton("Load CSV")
        layout.addWidget(self.load_button)
        # Label
        layout.addWidget(self.file_label)
        self.setLayout(layout)

class Window_plot_rules(QMainWindow):
    def __init__(self, csvFile=None, dataframe=None):
        super().__init__()

        self.setWindowTitle("Plot multivariate rules")
        self.setGeometry(100, 100, 600, 800)  # Set the initial size of the main window

        # Create a central widget and set a layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        # Create a scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # Allow the scroll area to resize its contents
        # Create a widget to contain the widgets of signals
        self.scroll_widget = QWidget()
        self.layout_signals = QVBoxLayout(self.scroll_widget)

        # Button to load CSV file
        self.CSV_loader = CSVLoader(csvFile=csvFile, dataframe=dataframe)
        self.layout.addWidget(self.CSV_loader)
        self.CSV_loader.load_button.clicked.connect(self.load_csv_file)
       
        # ComboBox of cell
        behavior_hbox = QHBoxLayout()
        self.combobox_cell = QComboBox()
        self.combobox_cell.currentIndexChanged.connect(self.update_cells)
        behavior_hbox.addWidget(QLabel('Cell type:')); behavior_hbox.addWidget( self.combobox_cell )
        # ComboBox of behavior
        self.combobox_behavior = QComboBox()
        self.combobox_behavior.currentIndexChanged.connect(self.update_rules)
        behavior_hbox.addWidget(QLabel('\tBehavior:')); behavior_hbox.addWidget( self.combobox_behavior )
        self.layout.addLayout(behavior_hbox)
        # Add a divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)  # Set horizontal line shape
        divider.setFrameShadow(QFrame.Sunken)  # Set sunken shadow effect
        self.layout.addWidget(divider)

        # Behaviors sliders
        self.layout_behavior_sliders = QVBoxLayout()
        self.layout.addLayout(self.layout_behavior_sliders)
        # Combox of signals to plot
        signal_hbox_plot = QHBoxLayout()
        signal_hbox_plot.addWidget(QLabel('Plot the signal:'))
        self.combobox_signal_plot = QComboBox()
        signal_hbox_plot.addWidget( self.combobox_signal_plot )
        # Set the scroll widget as the widget inside the scroll area
        self.scroll_area.setWidget(self.scroll_widget)
        # Add the scroll area to the layout
        self.layout.addWidget(self.scroll_area)
        # Check box of axes
        self.checkbox = QCheckBox('Fixed y-axis (min and max)')
        self.checkbox.setCheckState(2)  # 2 corresponds to Checked state
        self.layout.addWidget( self.checkbox )
        # Add the plot
        self.Figure = MainPlot(self.combobox_cell,self.combobox_behavior,self.combobox_signal_plot,self.layout_behavior_sliders, self.layout_signals, self.checkbox)
        self.layout.addWidget( self.Figure )

    def load_csv_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self.CSV_loader, "Open CSV File", "", "CSV Files (*.csv)", options=options)
        if file_name:
            try:
                self.CSV_loader.dataframe = pd.read_csv(file_name, header=None)
                self.CSV_loader.file_label.setText(file_name)
            except pd.errors.EmptyDataError:
                self.CSV_loader.file_label.setText("CSV files is empty!")
                return
            self.CSV_loader.dataframe = self.CSV_loader.dataframe.rename(columns={0: "cell", 1: "signal", 2: "direction", 
                                           3: "behavior", 4: "saturation", 5: "half_max",
                                           6: "hill_power", 7: "dead"}) # version 2 of rules
            # Add the base
            self.CSV_loader.dataframe["base_behavior"] = 0
            # print(self.CSV_loader.dataframe)
            # Clear the combo box of cells and populate
            self.combobox_cell.clear()
            self.combobox_cell.addItems(self.CSV_loader.dataframe["cell"].unique().tolist())
    def update_cells(self):
        # Clear the combo box of behaviors and populate
        self.combobox_behavior.clear()
        list_behaviors = self.CSV_loader.dataframe.loc[self.CSV_loader.dataframe["cell"] == self.combobox_cell.currentText()]['behavior'].tolist()
        self.combobox_behavior.addItems(list_behaviors)
    def update_rules(self):
        # Remove the behavior widgets from layout
        while self.layout_behavior_sliders.count():
            widget = self.layout_behavior_sliders.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()

        # Get the behavior values
        list_baseValue = self.CSV_loader.dataframe.loc[(self.CSV_loader.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                 (self.CSV_loader.dataframe['behavior'] == self.combobox_behavior.currentText()) &
                                                 (self.CSV_loader.dataframe['direction'] == "decreases")]['base_behavior'].tolist()
        list_UpReg = self.CSV_loader.dataframe.loc[(self.CSV_loader.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                 (self.CSV_loader.dataframe['behavior'] == self.combobox_behavior.currentText()) &
                                                 (self.CSV_loader.dataframe['direction'] == "increases")]['saturation'].tolist()
        list_DownReg = self.CSV_loader.dataframe.loc[(self.CSV_loader.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                 (self.CSV_loader.dataframe['behavior'] == self.combobox_behavior.currentText()) &
                                                 (self.CSV_loader.dataframe['direction'] == "decreases")]['saturation'].tolist()
        # Using the max and min of saturation to define UP and Down regulation
        try: baseBehavior = list_baseValue[0]
        except IndexError: baseBehavior = 0.0
        try: minBehavior = min(list_DownReg) 
        except ValueError: minBehavior = 0.0
        try: maxBehavior = max(list_UpReg) 
        except ValueError: maxBehavior = 0.0
        # Sliders of behavior
        self.sliders_behavior = MyWidget_behavior( self.combobox_behavior.currentText(), baseBehavior, maxBehavior, minBehavior )
        self.layout_behavior_sliders.addWidget( self.sliders_behavior )

        # Get the signals list
        list_signals = self.CSV_loader.dataframe.loc[(self.CSV_loader.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                       (self.CSV_loader.dataframe['behavior'] == self.combobox_behavior.currentText())]['signal'].tolist()

        # Clear the combo box of signals to plot
        self.combobox_signal_plot.clear()
        self.combobox_signal_plot.addItems(list_signals)
        
        # Remove the signals widgets from layout
        while self.layout_signals.count():
            widget = self.layout_signals.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()

        # Label and Sliders of signals
        for signal in list_signals:
            signal_direction = self.CSV_loader.dataframe.loc[(self.CSV_loader.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                       (self.CSV_loader.dataframe['behavior'] == self.combobox_behavior.currentText()) &
                                                       (self.CSV_loader.dataframe['signal'] == signal)]['direction'].item()
            signal_halfmax = self.CSV_loader.dataframe.loc[(self.CSV_loader.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                       (self.CSV_loader.dataframe['behavior'] == self.combobox_behavior.currentText()) &
                                                       (self.CSV_loader.dataframe['signal'] == signal)]['half_max'].item()
            signal_hillpower = self.CSV_loader.dataframe.loc[(self.CSV_loader.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                       (self.CSV_loader.dataframe['behavior'] == self.combobox_behavior.currentText()) &
                                                       (self.CSV_loader.dataframe['signal'] == signal)]['hill_power'].item()
            self.layout_signals.addWidget( MyWidget_signal( signal, signal_direction, signal_halfmax, signal_hillpower) ) 
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window_plot_rules() 
    win.show()
    sys.exit(app.exec_())