"""
Plot simulations stored in a UQ-PhysiCell database: ``studio.py --uq`` adds File -> Import UQ-PhysiCell
database, ``studio.py -c <config> --uq <database>`` also opens one at startup, and the Plot tab's folder
Select offers the databases of a folder without PhysiCell output.

Optional: requires the uq_physicell package (pip install uq-physicell), which is imported
only when a database is opened.
A dialog summarizes the database (model INI and XML, sampling, parameters) for confirmation;
the Plot tab then shows its first run. Each (SampleID, ReplicateID) is exposed to the Plot tab
as a temporary output folder of index .xml files; the cell and substrate data are served from
the database through pyMCDS.set_frame_loader(). A panel below the movie controls of the Plot
tab steps through samples/replicates and shows the sample's input parameters.

(Not named uq_physicell.py: that would shadow the uq_physicell package on sys.path.)
"""
import atexit
import glob
import math
import os
import shutil
import tempfile

from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAbstractItemView, QDialog, QDialogButtonBox, QFileDialog,
                             QFormLayout, QFrame, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QWidget)

from pyMCDS import set_frame_loader

_current_dir = None   # temporary output folder currently registered with pyMCDS
_restore_svg = False  # cells were plotted from .svg before the database was opened


def _message(text, icon=QMessageBox.Information):
    msgBox = QMessageBox()
    msgBox.setIcon(icon)
    msgBox.setText(text)
    msgBox.setStandardButtons(QMessageBox.Ok)
    msgBox.exec()


def _release_current():
    global _current_dir
    if _current_dir is not None:
        set_frame_loader(_current_dir, None)
        shutil.rmtree(_current_dir, ignore_errors=True)
        _current_dir = None

atexit.register(_release_current)


def unload(vis_tab):
    """Forget the database run: unregister its loader, delete its folder, hide the panel and
    give back .svg cell plotting if that was in use before."""
    _release_current()
    panel = getattr(vis_tab, "uq_panel", None)
    if panel is not None:
        panel.hide()
    vis_tab.output_folder.setToolTip("")
    if _restore_svg and hasattr(vis_tab, "cells_svg_rb"):
        vis_tab.cells_svg_rb.setChecked(True)
        vis_tab.plot_cells_svg = True
        vis_tab.disable_cell_scalar_widgets()


def _fmt(value):
    if hasattr(value, '__len__') and not isinstance(value, str):
        return ", ".join(_fmt(v) for v in value)
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "" if value is None else str(value)
    return "" if math.isnan(value) else f"{value:.6g}"


GREEN, AMBER, RED, GRAY = "darkgreen", "#b36b00", "#b00020", "gray"

# config status (uq_physicell.utils.pc_studio.verify_config) -> (message, color, panel flag)
CONFIG_STATUS = {
    'match': ("Same XML the database was created with (XML_Hash verified).", GREEN, ""),
    'differs': ("{n} of this XML's settings differ from what the stored output records.", AMBER, "config differs"),
    'mismatch': ("Cell types or substrates of this XML differ from the stored output: plot labels may be "
                 "wrong.", RED, "config mismatch"),
    'edited': ("This XML changed since the database was created (XML_Hash differs), but every setting the "
               "stored output records (domain, output times, substrates, cell types) matches.", GRAY, ""),
    'unverifiable': ("The database has no XML_Hash to identify its XML exactly; every setting the stored output "
                     "records (domain, output times, substrates, cell types) matches this XML.", GRAY, ""),
    'not_found': ("Config not found: choose the model's PhysiCell settings XML "
                  "(needed for cell type names).", RED, "no config"),
}


def _status_text(status, differences=()):
    """(message, color, panel flag) describing the model config used for a database."""
    text, color, flag = CONFIG_STATUS[status]
    return text.format(n=len(differences)), color, flag


def show_differences(parent, differences, files, text, headers):
    """Table of differing settings. files: [(label, path)] shown on top; headers: titles of the
    two value columns."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Model XML differences")
    vbox = QVBoxLayout(dialog)
    form = QFormLayout()
    for label, path in files:
        form.addRow(label, QLineEdit(path, readOnly=True))
    vbox.addLayout(form)
    label = QLabel(text)
    label.setWordWrap(True)
    label.setMinimumHeight(2 * label.fontMetrics().lineSpacing() + 4)
    vbox.addWidget(label)
    table = QTableWidget(len(differences), 3)
    table.setHorizontalHeaderLabels(["Setting", *headers])
    table.setWordWrap(False)
    table.setTextElideMode(Qt.ElideMiddle)   # keep both ends of long setting paths visible
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    for i, (setting, first, second) in enumerate(differences):
        for j, value in enumerate((setting, "(absent)" if first is None else first,
                                   "(absent)" if second is None else second)):
            item = QTableWidgetItem(value)
            item.setToolTip(value)
            table.setItem(i, j, item)
    table.resizeColumnsToContents()
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    vbox.addWidget(table)
    buttons = QDialogButtonBox(QDialogButtonBox.Close)
    buttons.rejected.connect(dialog.reject)
    vbox.addWidget(buttons)
    dialog.resize(900, min(210 + 30 * len(differences), 650))
    dialog.exec()


def show_output_differences(parent, differences, xml_file, db_file):
    """Settings of xml_file that disagree with what db_file's stored output recorded."""
    show_differences(parent, differences, [("XML:", xml_file), ("Database:", db_file)],
                     f"{_plural(len(differences), 'setting')} of the XML differ from what the database recorded "
                     f"(INI settings applied to every run are taken into account):",
                     ("XML", "Database (stored output)"))


def compare_studio_config(db_xml, studio_xml, xml_differences, verified=True):
    """Compare the config loaded in Studio with the database's model XML.

    Returns:
        tuple: (differences, message, color); differences as returned by xml_differences.
    """
    if not db_xml or not os.path.isfile(db_xml):
        return [], "Cannot compare: the database's model XML was not found.", GRAY
    note = "" if verified else " (the database's XML itself is not verified by its XML_Hash)"
    try:
        if os.path.samefile(db_xml, studio_xml):
            return [], f"Same model as the database's XML{note}.", GREEN if verified else GRAY
        differences = xml_differences(db_xml, studio_xml)
    except Exception as e:
        return [], f"Cannot compare with the database's model XML: {e}", GRAY
    if not differences:
        return [], f"Same model as the database's XML{note}.", GREEN if verified else GRAY
    return differences, (f"Studio's loaded model differs from the database's model XML in "
                         f"{_plural(len(differences), 'setting')}{note}. The editing tabs show this file; "
                         f"plots use the database's XML."), AMBER


def show_studio_differences(parent, differences, db_xml, studio_xml):
    show_differences(parent, differences, [("Database XML:", db_xml), ("Studio config:", studio_xml)],
                     f"{_plural(len(differences), 'setting')} differ between the database's model XML and the "
                     f"config loaded in Studio:", ("Database XML", "Studio config"))


def _ini_text(info):
    """'path [section]' of the model INI recorded in the database."""
    ini = info.get('ini_path') or info.get('ini_file') or "(not recorded)"
    text = f"{ini}  [{info.get('section') or '?'}]"
    return text if info.get('ini_path') or not info.get('ini_file') else text + "  (not found)"


def _plural(n, word):
    return f"{n} {word}" + ("" if str(n) == "1" else "s")


def _sampling_text(summary):
    """'LHS: 20 samples, 200 simulations (10 replicates per sample)'."""
    reps = summary['replicates']
    reps_text = f"{reps[0]}" if reps[0] == reps[1] else f"{reps[0]}-{reps[1]}"
    samples = summary['n_samples_run']
    if summary.get('n_samples') and summary['n_samples'] != samples:
        samples = f"{samples} of {summary['n_samples']}"
    plural = _plural
    return (f"{summary.get('sampler') or 'unknown sampler'}: {plural(samples, 'sample')}, "
            f"{plural(summary['n_runs'], 'simulation')} ({plural(reps_text, 'replicate')} per sample)")


class UQOpenDialog(QDialog):
    """Summary of a database to confirm before loading it: database, model INI and settings XML,
    sampling and parameters. The XML is fixed when it is found and matches the database's
    XML_Hash; otherwise another file can be chosen (and is verified the same way)."""

    PARAM_COLUMNS = (("lower_bound", "Lower"), ("upper_bound", "Upper"),
                     ("ref_value", "Reference"), ("perturbation", "Perturbation"))

    def __init__(self, db_file, info, summary, verify, xml_differences=None, studio_config=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UQ-PhysiCell database")
        self.info = info   # pc_studio.model_config_info(db_file)
        self.verify = verify   # verify(config_file) -> (status, differences), see pc_studio.verify_config
        self.db_file = db_file
        self.xml_differences = xml_differences   # pc_studio.xml_differences
        self.studio_config = studio_config if studio_config and os.path.isfile(studio_config) else None
        self.studio_differences = []
        self.status, self.differences = info['status'], info.get('differences', [])

        self.config_edit = QLineEdit(info.get('config_file') or "", readOnly=True)
        self.config_edit.setPlaceholderText(info.get('config_ref') or "PhysiCell_settings.xml of the model")
        self.config_button = QPushButton("Browse")
        self.config_button.clicked.connect(self.config_browse_cb)
        self.config_button.setVisible(self.status != 'match')
        self.diff_button = QPushButton("Show differences")
        self.diff_button.clicked.connect(
            lambda: show_output_differences(self, self.differences, self.config_file(), self.db_file))
        config_row = QWidget()
        hbox = QHBoxLayout(config_row)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.config_edit)
        hbox.addWidget(self.config_button)
        hbox.addWidget(self.diff_button)
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(2 * self.status_label.fontMetrics().lineSpacing() + 4)
        self.show_status()

        # parameters: only the columns this sampler defines
        params = summary['parameters']
        columns = [(key, title) for key, title in self.PARAM_COLUMNS if any(_fmt(p.get(key)) for p in params)]
        table = QTableWidget(len(params), 1 + len(columns))
        table.setHorizontalHeaderLabels(["Parameter"] + [title for _, title in columns])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i, p in enumerate(params):
            table.setItem(i, 0, QTableWidgetItem(str(p['name'])))
            for j, (key, _) in enumerate(columns, start=1):
                item = QTableWidgetItem(_fmt(p.get(key)))
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(i, j, item)
        table.resizeColumnsToContents()
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        height = table.horizontalHeader().height() + 4 + sum(table.rowHeight(i) for i in range(len(params)))
        table.setFixedHeight(min(height, 300))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Load")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        form = QFormLayout(self)
        form.addRow("Database:", QLineEdit(db_file, readOnly=True))
        form.addRow("Model INI:", QLineEdit(_ini_text(info), readOnly=True))
        form.addRow("Config XML:", config_row)
        form.addRow("", self.status_label)
        # the model loaded in Studio (-c / File -> Open): its editing tabs show that file
        self.studio_diff_button = QPushButton("Show differences")
        self.studio_diff_button.clicked.connect(self.show_studio_differences)
        self.studio_label = QLabel()
        self.studio_label.setWordWrap(True)
        self.studio_label.setMinimumHeight(2 * self.studio_label.fontMetrics().lineSpacing() + 4)
        if self.studio_config:
            studio_row = QWidget()
            hbox = QHBoxLayout(studio_row)
            hbox.setContentsMargins(0, 0, 0, 0)
            hbox.addWidget(QLineEdit(self.studio_config, readOnly=True))
            hbox.addWidget(self.studio_diff_button)
            form.addRow("Studio config:", studio_row)
            form.addRow("", self.studio_label)
            self.compare_studio_config()
        form.addRow("Sampling:", QLabel(_sampling_text(summary)))
        form.addRow(f"Parameters ({len(params)}):", table)
        form.addRow(buttons)
        self.setMinimumWidth(700)

    def show_status(self):
        text, color, _ = _status_text(self.status, self.differences)
        self.diff_button.setVisible(bool(self.differences))
        self.status_label.setText(f'<span style="color:{color}">{text}</span>')

    def config_browse_cb(self):
        start = os.path.dirname(self.info.get('ini_path') or "")
        path, _ = QFileDialog.getOpenFileName(self, "Model config", start, "XML (*.xml)")
        if path:
            self.config_edit.setText(path)
            self.status, self.differences = self.verify(path)
            self.show_status()
            self.compare_studio_config()

    def config_file(self):
        return self.config_edit.text().strip() or None

    def compare_studio_config(self):
        """Compare the config loaded in Studio with the database's model XML."""
        self.studio_differences = []
        if not self.studio_config:
            return
        self.studio_differences, text, color = compare_studio_config(
            self.config_file(), self.studio_config, self.xml_differences, verified=self.status == 'match')
        self.studio_label.setText(f'<span style="color:{color}">{text}</span>')
        self.studio_diff_button.setVisible(bool(self.studio_differences))

    def show_studio_differences(self):
        show_studio_differences(self, self.studio_differences, self.config_file(), self.studio_config)


class UQRunPanel(QWidget):
    """Plot tab controls: step through SampleID / ReplicateID and show the sample's inputs."""

    def __init__(self, vis_tab):
        super().__init__()
        self.vis_tab = vis_tab
        self.db_file = None
        self.config_file = None
        self.runs = None          # DataFrame: SampleID, ReplicateID[, Seed]
        self.parameters = {}      # {SampleID: [(name, value, lower, upper), ...]}
        self.sample_id = None
        self.replicate_id = None

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        vbox.addWidget(line)

        hbox = QHBoxLayout()
        self.title_label = QLabel()
        self.title_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        hbox.addWidget(self.title_label)
        hbox.addStretch(1)
        close_button = QPushButton("Close")
        close_button.setFixedWidth(70)
        close_button.setToolTip("Unload the database and plot the model's output folder again")
        close_button.clicked.connect(self.close_cb)
        hbox.addWidget(close_button)
        vbox.addLayout(hbox)

        self.sampling_label = QLabel()
        vbox.addWidget(self.sampling_label)
        hbox = QHBoxLayout()
        self.model_label = QLabel()
        self.model_label.setWordWrap(True)
        hbox.addWidget(self.model_label, 1)
        self.diff_button = QPushButton("Differences")
        self.diff_button.setFixedWidth(100)
        self.diff_button.setToolTip("Settings of the model XML that differ from what the database recorded")
        self.diff_button.clicked.connect(
            lambda: show_output_differences(self, self.differences, self.config_file, self.db_file))
        self.diff_button.hide()
        hbox.addWidget(self.diff_button)
        vbox.addLayout(hbox)
        self.differences = []

        # shown while the config loaded in Studio differs from the database's model XML
        self.studio_row = QWidget()
        hbox = QHBoxLayout(self.studio_row)
        hbox.setContentsMargins(0, 0, 0, 0)
        self.studio_label = QLabel()
        self.studio_label.setWordWrap(True)
        hbox.addWidget(self.studio_label, 1)
        studio_button = QPushButton("Differences")
        studio_button.setFixedWidth(100)
        studio_button.setToolTip("Settings that differ between the database's model XML and the config loaded in Studio")
        studio_button.clicked.connect(lambda: show_studio_differences(
            self, self.studio_differences, self.config_file, self.studio_config))
        hbox.addWidget(studio_button)
        vbox.addWidget(self.studio_row)
        self.studio_row.hide()
        self.studio_differences, self.studio_config = [], None
        self.xml_differences, self.config_verified = None, False

        self.seed_label = QLabel()
        self.seed_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.sample_edit = self._stepper_row(vbox, "Sample", self.step_sample)
        self.replicate_edit = self._stepper_row(vbox, "Replicate", self.step_replicate, extra=self.seed_label)
        self.sample_edit.returnPressed.connect(lambda: self.goto_sample(self.sample_edit.text()))
        self.replicate_edit.returnPressed.connect(lambda: self.goto_replicate(self.replicate_edit.text()))

        self.params_table = QTableWidget(0, 3)
        self.params_table.setHorizontalHeaderLabels(["Parameter", "Value", "Range"])
        self.params_table.verticalHeader().setVisible(False)
        self.params_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.params_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        header = self.params_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        vbox.addWidget(self.params_table)

    def _stepper_row(self, vbox, label_text, step_cb, extra=None):
        """'label  |<  <  [id]  >  >|  [extra]', same as the frame controls."""
        hbox = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(70)
        hbox.addWidget(label)
        edit = QLineEdit()
        edit.setFixedWidth(60)
        edit.setValidator(QtGui.QIntValidator(0, 10000000))
        for text, step in (("|<", "first"), ("<", -1), (None, None), (">", 1), (">|", "last")):
            if text is None:
                hbox.addWidget(edit)
                continue
            button = QPushButton(text)
            button.setFixedWidth(40)
            button.clicked.connect(lambda _, s=step: step_cb(s))
            hbox.addWidget(button)
        if extra is not None:
            hbox.addWidget(extra)
        hbox.addStretch(1)
        vbox.addLayout(hbox)
        return edit

    # ---- data ----
    def sample_ids(self):
        return sorted(int(s) for s in self.runs['SampleID'].unique())

    def replicate_ids(self, sample_id):
        return sorted(int(r) for r in self.runs.loc[self.runs['SampleID'] == sample_id, 'ReplicateID'])

    def set_database(self, db_file, config_file, runs, parameters, info=None, status=None, summary=None,
                     differences=(), xml_differences=None):
        self.db_file, self.config_file, self.runs, self.parameters = db_file, config_file, runs, parameters
        self.title_label.setText(f"<b>UQ-PhysiCell:</b> {os.path.basename(db_file)}")
        self.title_label.setToolTip(db_file)
        summary = summary or {}
        self.ref_values = {p['name']: p.get('ref_value') for p in summary.get('parameters', [])}
        self.sampling_label.setText(f"{summary.get('sampler') or 'unknown sampler'} \u00b7 "
                                    f"{_plural(summary.get('n_samples_run', len(self.sample_ids())), 'sample')} \u00b7 "
                                    f"{_plural(summary.get('n_runs', len(runs)), 'simulation')}")
        self.sampling_label.setToolTip(_sampling_text(summary) if summary else "")
        info = info or {}
        ini = info.get('ini_path') or info.get('ini_file') or "?"
        status = status or info.get('status', 'not_found')
        self.differences = list(differences)
        self.xml_differences, self.config_verified = xml_differences, status == 'match'
        text, color, flag = _status_text(status, self.differences)
        flag = f' <span style="color:{color}">({flag})</span>' if flag else ""
        self.model_label.setText(f"Model: {os.path.basename(ini)} [{info.get('section') or '?'}]{flag}")
        self.model_label.setToolTip(f"INI: {_ini_text(info)}\nConfig: {config_file or '(none)'}\n{text}")
        self.diff_button.setVisible(bool(self.differences))

    def is_loaded(self):
        """A database run is currently shown in the Plot tab."""
        return _current_dir is not None

    def output_dir_changed(self, output_dir):
        """Called from the Plot tab's reset_model(): unload once it plots another folder
        (a new simulation from the Run tab, File -> Open, Plot tab folder Select, ...)."""
        if _current_dir is not None and os.path.realpath(output_dir) != os.path.realpath(_current_dir):
            unload(self.vis_tab)

    def close_cb(self):
        vis_tab = self.vis_tab
        config_tab = getattr(vis_tab, "config_tab", None)
        vis_tab.update_output_dir(config_tab.folder.text() if config_tab is not None else "output")
        vis_tab.reset_model()   # unloads through output_dir_changed()
        vis_tab.update_plots()

    def check_studio_config(self):
        """Show the warning line if Studio's loaded config differs from the database's model XML."""
        self.studio_config = _studio_config(self.vis_tab)
        self.studio_differences = []
        if self.studio_config and os.path.isfile(self.studio_config) and self.xml_differences:
            self.studio_differences, text, _ = compare_studio_config(
                self.config_file, self.studio_config, self.xml_differences, self.config_verified)
            self.studio_row.setToolTip(text)
        if self.studio_differences:
            self.studio_label.setText(
                f'<span style="color:{AMBER}"><b>Studio config differs</b> from the database\'s model: '
                f'{os.path.basename(self.studio_config)} ({_plural(len(self.studio_differences), "setting")})</span>')
        self.studio_row.setVisible(bool(self.studio_differences))

    def show_current(self, sample_id, replicate_id):
        self.show()
        self.check_studio_config()
        self.sample_id, self.replicate_id = sample_id, replicate_id
        self.sample_edit.setText(str(sample_id))
        self.replicate_edit.setText(str(replicate_id))

        row = self.runs[(self.runs['SampleID'] == sample_id) & (self.runs['ReplicateID'] == replicate_id)]
        seed = row['Seed'].iloc[0] if 'Seed' in row.columns and len(row) else None
        recorded = seed is not None and str(seed) not in ('<NA>', 'nan', 'None')
        self.seed_label.setText(f"seed {seed}" if recorded else "seed n/a")
        self.seed_label.setToolTip(f"{len(self.replicate_ids(sample_id))} replicates of sample {sample_id}"
                                   + ("" if recorded else "; this database does not record seeds"))

        rows = self.parameters.get(sample_id, [])
        self.params_table.setRowCount(len(rows))
        for i, (name, value, lower, upper) in enumerate(rows):
            ref = _fmt(getattr(self, 'ref_values', {}).get(name))
            rng = f"[{_fmt(lower)}, {_fmt(upper)}]" if _fmt(lower) and _fmt(upper) else (f"ref {ref}" if ref else "")
            for j, text in enumerate((name, _fmt(value), rng)):
                item = QTableWidgetItem(text)
                if j > 0:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.params_table.setItem(i, j, item)
        height = self.params_table.horizontalHeader().height() + 4
        height += sum(self.params_table.rowHeight(i) for i in range(len(rows)))
        self.params_table.setFixedHeight(min(height, 300))

    # ---- navigation ----
    @staticmethod
    def _stepped(ids, current, step):
        if step == "first":
            return ids[0]
        if step == "last":
            return ids[-1]
        i = ids.index(current) if current in ids else 0
        return ids[min(max(i + step, 0), len(ids) - 1)]

    def step_sample(self, step):
        self.goto_sample(self._stepped(self.sample_ids(), self.sample_id, step))

    def step_replicate(self, step):
        self.goto_replicate(self._stepped(self.replicate_ids(self.sample_id), self.replicate_id, step))

    def goto_sample(self, sample_id):
        try:
            sample_id = int(sample_id)
        except ValueError:
            sample_id = None
        if sample_id not in self.sample_ids():
            self.sample_edit.setText(str(self.sample_id))
            return
        if sample_id == self.sample_id:
            return
        replicates = self.replicate_ids(sample_id)
        replicate_id = self.replicate_id if self.replicate_id in replicates else replicates[0]
        show_run(self.vis_tab, self.db_file, sample_id, replicate_id, self.config_file, keep_view=True)

    def goto_replicate(self, replicate_id):
        try:
            replicate_id = int(replicate_id)
        except ValueError:
            replicate_id = None
        if replicate_id not in self.replicate_ids(self.sample_id):
            self.replicate_edit.setText(str(self.replicate_id))
            return
        if replicate_id == self.replicate_id:
            return
        show_run(self.vis_tab, self.db_file, self.sample_id, replicate_id, self.config_file, keep_view=True)


def show_run(vis_tab, db_file, sample_id, replicate_id, config_file, keep_view=False):
    """Load one (SampleID, ReplicateID) into the Plot tab. With keep_view, stay on the same
    frame (clamped to the run's last frame), substrate and cell scalar."""
    global _current_dir, _restore_svg
    from uq_physicell.utils.pc_studio import StudioFrameLoader
    try:
        loader = StudioFrameLoader.from_database(db_file, sample_id, replicate_id)
        out_dir = tempfile.mkdtemp(prefix=f"uq_S{sample_id}_R{replicate_id}_")
        loader.write_index_folder(out_dir, config_file=config_file)
    except Exception as e:
        _message(f"Unable to load SampleID={sample_id}, ReplicateID={replicate_id}:\n{e}", QMessageBox.Warning)
        return False

    frame = vis_tab.current_frame if keep_view else 0
    substrate = vis_tab.substrates_combobox.currentText() if keep_view else ""
    cell_scalar = vis_tab.cell_scalar_combobox.currentText() if keep_view else ""

    if _current_dir is None:   # first run from a database: remember the cell plotting mode
        _restore_svg = bool(getattr(vis_tab, "plot_cells_svg", False))
    _release_current()
    set_frame_loader(out_dir, loader)
    _current_dir = out_dir

    # same sequence as Plot tab -> output folder selection (vis_base.output_folder_cb)
    # there are no .svg snapshots: plot cells from (loader-backed) .mat data
    vis_tab.plot_cells_svg = False
    vis_tab.update_output_dir(out_dir)
    vis_tab.reset_model()
    if config_file:
        vis_tab.initialize_cell_dict(os.path.join(out_dir, "PhysiCell_settings.xml"))
    if hasattr(vis_tab, "cells_mat_rb"):
        vis_tab.cells_mat_rb.click()   # also fills the cell scalar list

    for combobox, text in ((vis_tab.substrates_combobox, substrate), (vis_tab.cell_scalar_combobox, cell_scalar)):
        idx = combobox.findText(text) if text else -1
        if idx >= 0:
            combobox.blockSignals(True)
            combobox.setCurrentIndex(idx)
            combobox.blockSignals(False)
    vis_tab.field_index = 4 + max(vis_tab.substrates_combobox.currentIndex(), 0)
    vis_tab.substrate_name = vis_tab.substrates_combobox.currentText()
    vis_tab.current_frame = min(frame, max(len(glob.glob(os.path.join(out_dir, "output*.xml"))) - 1, 0))
    vis_tab.update_plots()
    # folder field: name the run instead of the temporary folder
    vis_tab.output_folder.setText(f"{os.path.basename(db_file)} [Sample {sample_id}, Replicate {replicate_id}]")
    vis_tab.output_folder.setToolTip(f"{db_file}\n(temporary folder {out_dir})")

    panel = getattr(vis_tab, "uq_panel", None)
    if panel is not None:
        panel.show_current(sample_id, replicate_id)
    return True


def _import_pc_studio():
    """uq_physicell's Studio adapter, or None (with a message) if the package is missing."""
    try:
        from uq_physicell.utils import pc_studio
        return pc_studio
    except ImportError as e:
        _message(f"Plotting UQ-PhysiCell databases requires the uq_physicell package "
                 f"(pip install uq-physicell).\n\n{e}", QMessageBox.Warning)
        return None


def _studio_config(vis_tab):
    """Config file currently loaded in Studio (-c or File -> Open), or None."""
    run_tab = getattr(vis_tab, "run_tab", None)
    try:
        path = run_tab.config_xml_name.text().strip()
    except AttributeError:
        return None
    return os.path.abspath(path) if path else None


def _show_plot_tab(vis_tab):
    """Bring the Plot tab to the front (it lives in Studio's main QTabWidget)."""
    widget = vis_tab.parentWidget()
    while widget is not None and not isinstance(widget, QTabWidget):
        widget = widget.parentWidget()
    if widget is not None:
        widget.setCurrentWidget(vis_tab)


def open_database(vis_tab, db_file, parent=None):
    """Check a database, show its summary for confirmation, then plot its first run in the
    Plot tab. Returns True if it was loaded."""
    pc_studio = _import_pc_studio()
    if pc_studio is None:
        return False
    ok, reason = pc_studio.check_database(db_file)
    if not ok:
        _message(f"Cannot plot {os.path.basename(db_file)}:\n\n{reason}", QMessageBox.Warning)
        return False
    try:
        runs = pc_studio.list_runs(db_file)
        summary = pc_studio.database_summary(db_file, runs)
    except Exception as e:
        _message(f"Unable to read simulations from {db_file}:\n{e}", QMessageBox.Warning)
        return False

    info = pc_studio.model_config_info(db_file)
    dialog = UQOpenDialog(db_file, info, summary,
                          lambda path: pc_studio.verify_config(db_file, path, info.get('xml_hash'),
                                                               info.get('fixed_parameters')),
                          pc_studio.xml_differences, _studio_config(vis_tab), parent)
    if dialog.exec() != QDialog.Accepted:
        return False
    config_file = dialog.config_file()
    if config_file and not os.path.isfile(config_file):
        _message(f"Config file not found: {config_file}", QMessageBox.Warning)
        return False
    try:
        parameters = pc_studio.sample_parameters(db_file)
    except Exception:
        parameters = {}

    # panel below the movie controls (vis_base.uq_panel_vbox), created on first use
    if getattr(vis_tab, "uq_panel", None) is None and hasattr(vis_tab, "uq_panel_vbox"):
        vis_tab.uq_panel = UQRunPanel(vis_tab)
        vis_tab.uq_panel.hide()   # shown by show_run() once a run is loaded
        vis_tab.uq_panel_vbox.addWidget(vis_tab.uq_panel)
    if getattr(vis_tab, "uq_panel", None) is not None:
        vis_tab.uq_panel.set_database(db_file, config_file, runs, parameters, info, dialog.status, summary, dialog.differences,
                                     pc_studio.xml_differences)

    first = runs.sort_values(['SampleID', 'ReplicateID']).iloc[0]
    if not show_run(vis_tab, db_file, int(first['SampleID']), int(first['ReplicateID']), config_file):
        return False
    _show_plot_tab(vis_tab)
    return True


def open_database_in_folder(vis_tab, folder):
    """Plot tab folder selection: offer the databases of a folder without PhysiCell output.
    Returns False (Studio handles the folder as usual) if there are none."""
    db_files = sorted(f for ext in ("*.db", "*.sqlite", "*.sqlite3") for f in glob.glob(os.path.join(folder, ext)))
    if not db_files:
        return False
    pc_studio = _import_pc_studio()
    if pc_studio is None:
        return True
    checks = {db: pc_studio.check_database(db) for db in db_files}
    usable = [db for db, (ok, _) in checks.items() if ok]
    if not usable:
        details = "\n".join(f"- {os.path.basename(db)}: {reason}" for db, (_, reason) in checks.items())
        _message(f"No PhysiCell output in {folder}, and none of its databases store the raw "
                 f"simulation output (MCDS objects):\n\n{details}", QMessageBox.Warning)
        return True
    db_file = usable[0]
    if len(usable) > 1:
        name, ok = QInputDialog.getItem(vis_tab, "UQ-PhysiCell database",
                                        "This folder has several databases with simulation output:",
                                        [os.path.basename(db) for db in usable], 0, False)
        if not ok:
            return True
        db_file = os.path.join(folder, name)
    open_database(vis_tab, db_file, vis_tab)
    return True


def open_database_at_startup(studio, db_file):
    """``studio.py -c <config> --uq <database>``: open the database once the main window is up."""
    vis_tab = getattr(studio, "vis_tab", None)
    if vis_tab is None:
        _message("The Plot tab is not available (Studio was started in bare mode).")
        return
    open_database(vis_tab, db_file, studio)


def open_uq_database_cb(studio):
    """File -> Import UQ-PhysiCell database (shown with ``studio.py --uq``): choose a database,
    then show it in the Plot tab."""
    vis_tab = getattr(studio, "vis_tab", None)
    if vis_tab is None:
        _message("The Plot tab is not available (Studio was started in bare mode).")
        return
    if _import_pc_studio() is None:
        return
    db_file, _ = QFileDialog.getOpenFileName(studio, "Import UQ-PhysiCell database", "",
                                             "Database (*.db *.sqlite *.sqlite3);;All files (*)")
    if db_file:
        open_database(vis_tab, db_file, studio)
