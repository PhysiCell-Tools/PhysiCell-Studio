import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QScrollArea, QVBoxLayout,QHBoxLayout, QSlider, QLabel, QMainWindow, QComboBox, QCheckBox, QPushButton, QDoubleSpinBox, QFrame, QSpinBox, QMessageBox
from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from studio_classes import QCheckBox_custom

def Multivariate_hillFunc(signals_U, halfmaxs_U, hillpowers_U, signals_D, halfmaxs_D, hillpowers_D):
    sum_U = 0; sum_D = 0 
    for id_Up in range(len(signals_U)):
        sum_U += (signals_U[id_Up]/halfmaxs_U[id_Up])**hillpowers_U[id_Up]
        if ( type(signals_U[id_Up]) == np.ndarray):
            proj_signal = signals_U[id_Up]
    for id_Dw in range(len(signals_D)):
        sum_D += (signals_D[id_Dw]/halfmaxs_D[id_Dw])**hillpowers_D[id_Dw]
        if ( type(signals_D[id_Dw]) == np.ndarray):
            proj_signal = signals_D[id_Dw]
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

class BehaviorWidget(QWidget):
    def __init__(self, name, base_v, max_up , max_down, frac_var):
        super().__init__()
        self.name = name
        # frac_var is the fraction of variation -/+ in the base, up, down sliders of behaviors
        self.base_min = base_v*(1.0-frac_var)
        self.base_max = base_v*(1.0+frac_var)
        self.max_up_min = max_up*(1.0-frac_var)
        self.max_up_max = max_up*(1.0+frac_var)
        self.max_down_min = max_down*(1.0-frac_var)
        self.max_down_max = max_down*(1.0+frac_var)
        self.init_ui()
    def init_ui(self):
        layout = QHBoxLayout()
        Base_behavior_values = ["%e" % x for x in np.linspace(self.base_min, self.base_max, num=11, endpoint=True)]
        Max_behavior_values = ["%e" % x for x in np.linspace(self.max_up_min,self.max_up_max, num=11, endpoint=True)]
        Min_behavior_values = ["%e" % x for x in np.linspace(self.max_down_min, self.max_down_max, num=11, endpoint=True)]
        self.slider_base_behavior = LabeledSlider("Base behavior", Base_behavior_values)
        self.slider_up_behavior = LabeledSlider("Up regulation", Max_behavior_values)
        self.slider_down_behavior = LabeledSlider("Down regulation", Min_behavior_values)
        # Set initial value
        self.slider_base_behavior.slider.setValue(round(0.5*len(Base_behavior_values)) -1 ) # start in the center of the bar
        self.slider_up_behavior.slider.setValue(round(0.5*len(Max_behavior_values)) -1 ) # start in the center of the bar
        self.slider_down_behavior.slider.setValue(round(0.5*len(Min_behavior_values)) -1 ) # start in the center of the bar
        layout.addWidget(self.slider_base_behavior)
        layout.addWidget(self.slider_up_behavior)
        layout.addWidget(self.slider_down_behavior)
        self.setLayout(layout)

class SignalWidget(QWidget):
    def __init__(self, sig_name, sig_direction , sig_halfmax, sig_hillpower, frac_var):
        super().__init__()
        self.sig_name = sig_name
        self.sig_direction = sig_direction
        # frac_var is the percentage of variation -/+ in signal and halfmax
        self.sig_min = sig_halfmax*(1-frac_var)
        self.sig_max = sig_halfmax*(1+frac_var)
        self.sig_halfmax_min = sig_halfmax*(1-frac_var)
        self.sig_halfmax_max = sig_halfmax*(1+frac_var)
        self.sig_hillpower = sig_hillpower
        self.sig_hillpower_min = round(sig_hillpower*(1-frac_var))
        self.sig_hillpower_max = round(sig_hillpower*(1+frac_var))
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
    def __init__(self, combobox_cell, combobox_behavior, combobox_behaviorplot, layout_behavior_sliders, layout_signals, checkbox, min_signal, max_signal):
        super(MainPlot, self).__init__()
        self.combobox_cell = combobox_cell
        self.combobox_behavior = combobox_behavior
        self.combobox_behaviorplot = combobox_behaviorplot
        self.layout_behavior_sliders = layout_behavior_sliders
        self.layout_signals = layout_signals
        self.checkbox = checkbox
        self.min_signal = min_signal
        self.max_signal = max_signal
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
        halfMax_value = None; halfMax_value2 = None
        for i in range(self.layout_signals.layout().count()):
            widget = self.layout_signals.layout().itemAt(i).widget()
            sig_halfmax = float( widget.slider_halfmax_signal.tickValue( widget.slider_halfmax_signal.slider.value() ) )
            if ( sig_halfmax == 0): # halfmax cannot be 0.
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setText("Half max of signal cannot be: " + str(sig_halfmax))
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec()
                # Set to the default value
                widget.slider_halfmax_signal.slider.setValue(5) # it is 5 because the slider is discretized to 11 values. 
                return
            sig_hillpower = float( widget.slider_hillpower.tickValue( widget.slider_hillpower.slider.value() ) )
            if (Selected_sig == widget.sig_name):
                sig_value = np.linspace(self.min_signal.value(), self.max_signal.value(), num=1000)
                widget.slider_signal.slider.setEnabled(False)
                # If have two rules to same signal and behavior with different directions (increase and decrease)
                if (halfMax_value): halfMax_value2 = sig_halfmax # If it is the second rule
                else: halfMax_value = sig_halfmax # If it is the first rules
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
        # Calculate the hill function
        if ((len(listSigUpReg) > 0) | (len(listSigDownReg) > 0)):
            signal, H_U, H_D = Multivariate_hillFunc(listSigUpReg, listHalfMaxUpReg, listHillPowerUpReg, listSigDownReg, listHalfMaxDownReg, listHillPowerDownReg)
            self.canvas.axes.set_title(f"Behavior: {behavior_name}")
            self.canvas.axes.plot(signal, (b_0 + (b_M - b_0)*H_U)*(1-H_D) + H_D*b_m, 'r')
            # self.canvas.axes.plot(signal, b_0 + H_U*(b_M-b_0) + H_D*(b_m - b_0), 'r')
            self.canvas.axes.axvline(halfMax_value, ls='--', color = 'k')
            if (halfMax_value2): self.canvas.axes.axvline(halfMax_value2, ls='--', color = 'k') # If have two rules to same signal and behavior with different directions (increase and decrease)
            self.canvas.axes.set_ylabel('b(U,D)')
            self.canvas.axes.set_xlabel(Selected_sig)
            if (  (AxesFixed) and (b_M > b_m) ): self.canvas.axes.set_ylim(b_m, b_M)
        # Trigger the canvas to update and redraw.
        self.canvas.fig.tight_layout()
        self.canvas.draw()
    
class CSVLoader(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        layout = QHBoxLayout()
        self.file_label = QLabel("No file loaded")
        # Button to load
        self.load_button = QPushButton("Load CSV")
        layout.addWidget(self.load_button)
        # Label
        layout.addWidget(self.file_label)
        self.setLayout(layout)

class Window_plot_rules(QMainWindow):
    def __init__(self, dataframe=None):
        super().__init__()
        self.dataframe = dataframe
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

        if not isinstance(dataframe, pd.DataFrame): 
            # Button to load CSV file
            self.CSV_loader = CSVLoader()
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
        # Variance of behavior
        behavior_hbox.addWidget(QLabel('\t +/- Behavior input variation +/- (%):'))
        self.behavior_variation = QSpinBox()
        self.behavior_variation.setMinimum(1)
        self.behavior_variation.setMaximum(500)
        self.behavior_variation.setSingleStep(1)
        self.behavior_variation.valueChanged.connect(self.update_rules)
        behavior_hbox.addWidget( self.behavior_variation )
        
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
        # Variance of signals to plot
        signal_hbox_plot.addWidget(QLabel('\t Signal input variation +/- (%):'))
        self.signal_variation = QSpinBox()
        self.signal_variation.setMinimum(1)
        self.signal_variation.setMaximum(500)
        self.signal_variation.setSingleStep(1)
        self.signal_variation.valueChanged.connect(self.update_rules)
        signal_hbox_plot.addWidget( self.signal_variation )
        self.layout.addLayout(signal_hbox_plot)

        # Set the scroll widget as the widget inside the scroll area
        self.scroll_area.setWidget(self.scroll_widget)
        # Add the scroll area to the layout
        self.layout.addWidget(self.scroll_area)
        # Check box of axes
        signal_hbox_plot_options = QHBoxLayout()
        self.checkbox = QCheckBox_custom('Fixed y-axis (min and max)')
        self.checkbox.setCheckState(2)  # 2 corresponds to Checked state
        signal_hbox_plot_options.addWidget( self.checkbox )
        # Float to min and max signal
        signal_hbox_plot_options.addWidget(QLabel('\t Signal range - Min:'))
        self.float_min_signal = QDoubleSpinBox()
        self.float_min_signal.setMinimum(-float('inf'))
        signal_hbox_plot_options.addWidget( self.float_min_signal )
        signal_hbox_plot_options.addWidget(QLabel('Max:'))
        self.float_max_signal = QDoubleSpinBox()
        self.float_max_signal.setMaximum(float('inf'))
        signal_hbox_plot_options.addWidget( self.float_max_signal )
        self.layout.addLayout(signal_hbox_plot_options)
        # Add the plot
        self.Figure = MainPlot(self.combobox_cell,self.combobox_behavior,self.combobox_signal_plot,self.layout_behavior_sliders, self.layout_signals, self.checkbox, self.float_min_signal, self.float_max_signal)
        self.layout.addWidget( self.Figure )
        # Initialize if the daframae is defiend
        if isinstance(dataframe, pd.DataFrame): 
            # Clear the combo box of cells and populate
            self.combobox_cell.clear()
            self.combobox_cell.addItems(self.dataframe["cell"].unique().tolist())

    def load_csv_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self.CSV_loader, "Open CSV File", "", "CSV Files (*.csv)", options=options)
        if file_name:
            try:
                self.dataframe = pd.read_csv(file_name, header=None)
                self.CSV_loader.file_label.setText(file_name)
            except pd.errors.EmptyDataError:
                self.CSV_loader.file_label.setText("CSV file is empty!")
                return
            self.dataframe = self.dataframe.rename(columns={0: "cell", 1: "signal", 2: "direction", 
                                           3: "behavior", 4: "saturation", 5: "half_max",
                                           6: "hill_power", 7: "dead"}) # version 2 of rules
            # Add the base
            self.dataframe["base_behavior"] = 0
            # print(self.dataframe)
            
            # Clear the combo box of cells and populate
            self.combobox_cell.clear()
            self.combobox_cell.addItems(self.dataframe["cell"].unique().tolist())
    
    def update_cells(self):
        # Clear the combo box of behaviors and populate
        self.combobox_behavior.clear()
        list_behaviors = self.dataframe.loc[self.dataframe["cell"] == self.combobox_cell.currentText()]['behavior'].unique().tolist()
        self.combobox_behavior.addItems(list_behaviors)
        # Behavior variation initial value
        self.behavior_variation.setValue(100)
        self.signal_variation.setValue(100)
    
    def update_rules(self):
        # Remove the behavior widgets from layout
        while self.layout_behavior_sliders.count():
            widget = self.layout_behavior_sliders.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()

        # Get the behavior values
        list_baseValue = self.dataframe.loc[(self.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                 (self.dataframe['behavior'] == self.combobox_behavior.currentText()) &
                                                 (self.dataframe['direction'] == "decreases")]['base_behavior'].tolist()
        list_UpReg = self.dataframe.loc[(self.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                 (self.dataframe['behavior'] == self.combobox_behavior.currentText()) &
                                                 (self.dataframe['direction'] == "increases")]['saturation'].tolist()
        list_DownReg = self.dataframe.loc[(self.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                 (self.dataframe['behavior'] == self.combobox_behavior.currentText()) &
                                                 (self.dataframe['direction'] == "decreases")]['saturation'].tolist()
        # Using the max and min of saturation to define UP and Down regulation
        try: baseBehavior = list_baseValue[0]
        except IndexError: baseBehavior = 0.0
        try: minBehavior = min(list_DownReg) 
        except ValueError: minBehavior = 0.0
        try: maxBehavior = max(list_UpReg) 
        except ValueError: maxBehavior = 0.0
        # print(self.combobox_behavior.currentText(), baseBehavior, maxBehavior, minBehavior)

        # Sliders of behavior
        self.sliders_behavior = BehaviorWidget( self.combobox_behavior.currentText(), baseBehavior, maxBehavior, minBehavior, 0.01*self.behavior_variation.value() )
        self.layout_behavior_sliders.addWidget( self.sliders_behavior )
        # Disable sliders
        if len(list_DownReg) == 0: self.sliders_behavior.slider_down_behavior.setEnabled(False)
        if len(list_UpReg) == 0: self.sliders_behavior.slider_up_behavior.setEnabled(False)

        # Get the signals list
        list_signals = self.dataframe.loc[(self.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                       (self.dataframe['behavior'] == self.combobox_behavior.currentText())]['signal'].unique().tolist()

        # Clear the combo box of signals to plot
        self.combobox_signal_plot.clear()
        self.combobox_signal_plot.addItems(list_signals)
        
        # Remove the signals widgets from layout
        while self.layout_signals.count():
            widget = self.layout_signals.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()

        # Label and Sliders of signals
        halfmax_max = -np.inf
        # Signal variation input
        frac_var = 0.01*self.signal_variation.value()
        for signal in list_signals:
            signal_direction = self.dataframe.loc[(self.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                       (self.dataframe['behavior'] == self.combobox_behavior.currentText()) &
                                                       (self.dataframe['signal'] == signal)]['direction'].to_numpy()
            signal_halfmax = self.dataframe.loc[(self.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                       (self.dataframe['behavior'] == self.combobox_behavior.currentText()) &
                                                       (self.dataframe['signal'] == signal)]['half_max'].to_numpy()
            signal_hillpower = self.dataframe.loc[(self.dataframe["cell"] == self.combobox_cell.currentText()) &
                                                       (self.dataframe['behavior'] == self.combobox_behavior.currentText()) &
                                                       (self.dataframe['signal'] == signal)]['hill_power'].to_numpy()
            
            if ( len(signal_direction) > 1): # two rules with same signal and different directions
                # Add the signal sliders
                self.layout_signals.addWidget( SignalWidget( signal, signal_direction[0], signal_halfmax[0], signal_hillpower[0], frac_var= frac_var) ) 
                self.layout_signals.addWidget( SignalWidget( signal, signal_direction[1], signal_halfmax[1], signal_hillpower[1], frac_var= frac_var) ) 
                # Check maximum half max of signal
                halfmax_max_temp = max([signal_halfmax[0], signal_halfmax[1]]) # the signal discretization based on the max halfmax
                if (halfmax_max < halfmax_max_temp): halfmax_max = halfmax_max_temp
                
            else:
                 # Add the signal sliders
                self.layout_signals.addWidget( SignalWidget( signal, signal_direction[0], signal_halfmax[0], signal_hillpower[0], frac_var= frac_var) ) 
                # Check maximum half max of signal
                if (halfmax_max < signal_halfmax[0]): halfmax_max = signal_halfmax[0]
        
        # Set initial value of plot signal (customizable)
        self.float_min_signal.setValue(halfmax_max*(1-frac_var))
        self.float_max_signal.setValue(halfmax_max*(1+frac_var))
    

if __name__ == "__main__":
    df_test1 = pd.DataFrame(np.array([["cancer", 'pO2', 'increases', 'cycle entry', 0.042, 21.5, 4, 0, 0.001],
                                      ["cancer", 'estrogen', 'increases', 'cycle entry', 0.042, 0.5, 3, 0, 0.001],
                                      ["cancer", 'pressure', 'decreases', 'cycle entry', 0.0, 0.25, 3, 0, 0.001]]),
                   columns=['cell', 'signal', 'direction', 'behavior', 'saturation', 'half_max', 'hill_power', 'dead', 'base_behavior'])
    df_test1 = df_test1.astype({'cell':str, 'signal':str, 'direction':str, 'behavior':str, 'saturation':float, 'half_max':float, 'hill_power':int,  'dead':int,  'base_behavior':float})
    df_test2 = pd.DataFrame(np.array([["default", 'substrate', 'increases', 'substrate secretion', 1.0, 0.5, 4, 0, 0.0],
                                      ["default", 'pressure', 'increases', 'substrate secretion', 1.0, 0.5, 4, 0, 0.0]]),
                   columns=['cell', 'signal', 'direction', 'behavior', 'saturation', 'half_max', 'hill_power', 'dead', 'base_behavior'])
    df_test2 = df_test2.astype({'cell':str, 'signal':str, 'direction':str, 'behavior':str, 'saturation':float, 'half_max':float, 'hill_power':int,  'dead':int,  'base_behavior':float})
    # Rules hill
    df_hill = pd.DataFrame(np.array([["default", 'substrate', 'increases', 'cycle entry', 0.0033, 0.2, 10, 0, 0.003],
                                      ["default", 'substrate', 'decreases', 'cycle entry', 0, 0.5, 10, 0, 0.003]]),
                   columns=['cell', 'signal', 'direction', 'behavior', 'saturation', 'half_max', 'hill_power', 'dead', 'base_behavior'])
    df_hill = df_hill.astype({'cell':str, 'signal':str, 'direction':str, 'behavior':str, 'saturation':float, 'half_max':float, 'hill_power':int,  'dead':int,  'base_behavior':float})
    # Rules valley
    df_valley = pd.DataFrame(np.array([["default", 'substrate', 'decreases', 'cycle entry', 0.001, 0.2, 8, 0, 0.003],
                                       ["default", 'substrate', 'increases', 'cycle entry', 0.005, 0.5, 12, 0, 0.003]]),
                   columns=['cell', 'signal', 'direction', 'behavior', 'saturation', 'half_max', 'hill_power', 'dead', 'base_behavior'])
    df_valley = df_valley.astype({'cell':str, 'signal':str, 'direction':str, 'behavior':str, 'saturation':float, 'half_max':float, 'hill_power':int,  'dead':int,  'base_behavior':float})

    app = QApplication(sys.argv)
    # win = Window_plot_rules()
    # win = Window_plot_rules(dataframe=df_test1)
    # win = Window_plot_rules(dataframe=df_test2)
    win = Window_plot_rules(dataframe=df_valley)
    win.show()
    sys.exit(app.exec_())