"""
biwt_bridge_ui.py - what Studio asks and does when BIWT finishes.

BIWT hands back cell positions and a set of cell definitions. The positions go to a .csv;
the cell definitions merge into the model that is open, become a new config file, or are
dropped. This module runs that conversation and the writes that follow. The rules it applies
are in biwt_bridge.py, which has no Qt in it.

Two dialogs: one to decide, one to report. The first asks only where things should go -- what
happens to each cell type was settled inside BIWT and is shown, not asked. Nothing is written
until it is accepted, because _biwt_complete is a one-shot callback whose window is already
gone: a Cancel here discards the whole walkthrough, so every warning has to arrive while
backing out is still free.

Authors:
Dr. Daniel Bergman
Rf. Credits.md
"""

import os
import shutil
from html import escape as _escape
import xml.etree.ElementTree as ET
from datetime import datetime

from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QRadioButton, QButtonGroup, QWidget,
    QFileDialog, QMessageBox, QScrollArea, QFrame, QSpacerItem, QSizePolicy,
)

import biwt_bridge as bridge
import physicell_xml_defaults as pcdefaults
from studio_classes import QLabelSeparator, QCheckBox_custom
from pretty_print_xml import pretty_print


DEST_MERGE = "merge"
DEST_NEW_FILE = "new_file"
DEST_SKIP = "skip"



def _timestamp():
    return datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S")


# Plain wording for DomainSpec.source, shown in the dialog in place of the raw marker.
#
# DEFAULT means BIWT fell back to its own bounds because the host gave it nothing usable.
# Studio always sends a domain unless this model's own is malformed (see
# ICs._domain_from_config_tab), so DEFAULT means the domain describes neither the model nor
# the data -- the one case where adopting it is wrong.
try:  # biwt may be absent or may not export DomainSource; fall back to the raw strings
    from biwt.types import DomainSource as _DomainSource
    _DOMAIN_SOURCE_LABELS = {
        _DomainSource.HOST: "from Studio",
        _DomainSource.DATA: "from data",
        _DomainSource.USER: "user-edited",
        _DomainSource.DEFAULT: "BIWT default",
    }
except Exception:
    _DOMAIN_SOURCE_LABELS = {
        "host": "from Studio",
        "data": "from data",
        "user": "user-edited",
        "default": "BIWT default",
    }


def _domain_source_label(source):
    """Plain wording for a DomainSpec.source, or the raw marker if it is unfamiliar.

    BIWT's DomainSource docstring and its code disagree on which values exist, so an
    unrecognised marker is shown as-is rather than mapped onto the nearest known label.
    """
    if not source:
        return ""
    return _DOMAIN_SOURCE_LABELS.get(source, source.replace("_", " "))


def _csv_types_without_definitions(result, prospective_cell_types):
    """Cell types the .csv places but the model will have no definition for.

    See BiwtCompletionFlow._add_requests_for_csv_types for why these matter.
    """
    coordinates = getattr(result, "coordinates", None)
    if coordinates is None:
        return []
    try:
        placed = [str(name).strip() for name in coordinates["type"].unique()]
    except (KeyError, TypeError, AttributeError):
        return []
    # Through classify_names() so this uses the same "is it the same name?" rule as the cell
    # definitions do, rather than a second copy of it that could drift.
    _matched, added = bridge.classify_names(placed, prospective_cell_types)
    return sorted(set(name for name in added if name))


def _rules_note(findings, subject):
    """Warning about rules naming cell types that will not exist, or "" if there are none.

    *subject* completes "refers to cell types ...", because which types survive depends on
    where the cell definitions are going. findings come from scan_rules_for_missing_types().
    """
    if not findings:
        return ""
    shown = ", ".join(sorted({name for _row, _column, name in findings}))
    # Rows, not findings: one rule can name a cell type in its subject and again inside its
    # signal or behavior, and counting those separately overstates how many rules break.
    rules = len({row for row, _column, _name in findings})
    return ("! The rules file refers to cell types %s: %s (%d rule%s). Those rules will not "
            "load." % (subject, shown, rules, "" if rules == 1 else "s"))


def _new_file_rules_note(rule_count):
    """Warning that a new config leaves this model's rules behind, or "" if it has none."""
    if not rule_count:
        return ""
    return ("! The new config gets no rules - the %d in this model stay%s with it."
            % (rule_count, "s" if rule_count == 1 else ""))


def _biwt_version():
    """The installed BIWT's version, for the receipt. Empty if it does not publish one."""
    try:
        import biwt
        return getattr(biwt, "__version__", "") or ""
    except Exception:
        return ""


def backup_config(path):
    """Copy *path* aside before it is overwritten. Returns the backup path.

    Suffixed .bak rather than .xml so backups do not turn up in Studio's own file dialogs
    looking like models to open.
    """
    stamp = _timestamp()
    candidate = "%s.%s.bak" % (path, stamp)
    counter = 2
    while os.path.exists(candidate):
        candidate = "%s.%s_%d.bak" % (path, stamp, counter)
        counter += 1
    shutil.copy2(path, candidate)
    return candidate


def _is_writable(path):
    """(ok, reason) for overwriting *path* -- checked before anything is mutated."""
    folder = os.path.dirname(os.path.abspath(path)) or "."
    if not os.path.isdir(folder):
        return False, "the folder %s does not exist" % folder
    if os.path.exists(path):
        if not os.access(path, os.W_OK):
            return False, "the file is read-only"
    elif not os.access(folder, os.W_OK):
        return False, "the folder %s is read-only" % folder
    return True, ""


class TypeRow:
    """One incoming cell type and what is going to happen to it.

    Nothing to decide here. Every choice that matters was made at BIWT's parameters step; this
    reports what those choices mean for the model, and what Studio had to fill in where a
    choice could not be honoured.
    """

    def __init__(self, request, replaces):
        self.request = request
        self.name = request.name
        self.replaces = replaces   # True when the model already has a cell type by this name

    def unchanged(self):
        """True when this comes out as the definition the model already holds.

        The model has the cell type, and the template chosen for it is that type's own
        definition, so it is copied from itself.
        """
        return (self.replaces
                and self.request.origin == bridge.ORIGIN_HOST
                and self.request.template_name == self.name)

    def brings_own_substrate_values(self):
        """True when it arrives with secretion values rather than needing them set.

        A definition copied out of this model carries whatever the user already set there. One
        built from a template library, or from Studio's defaults, does not.
        """
        return self.request.origin == bridge.ORIGIN_HOST

    def outcome(self):
        if self.unchanged():
            return "unchanged"
        return "replaces this model's definition" if self.replaces else "added as a new cell type"

    def note(self):
        """Where this definition came from, and anything Studio had to supply itself."""
        request = self.request
        bits = []

        if self.unchanged():
            pass                    # the outcome column has said everything there is to say
        elif request.origin == bridge.ORIGIN_HOST:
            bits.append("copied from %s" % request.describe_template())
        elif request.origin == bridge.ORIGIN_TEMPLATE:
            bits.append(request.describe_template())
        elif request.chose_template():
            # A template was chosen and could not be used. Say which and why -- reporting this
            # as "no template was chosen" would blame the user for Studio's fallback.
            bits.append("%s %s, so Studio's default phenotype was used"
                        % (request.describe_template(), request.error or "could not be used"))
        else:
            bits.append("Studio's default phenotype")

        if request.filled:
            bits.append("filled in: "
                        + ", ".join(p.rpartition("/")[2] for p in request.filled))
        return "; ".join(bits)


class BiwtSaveDialog(QDialog):
    """Everything the user decides, in one form. Writes nothing."""

    def __init__(self, parent, context):
        super().__init__(parent)
        self.ctx = context
        self.setWindowTitle("BIWT - Save Results")
        self.setMinimumWidth(640)

        outer = QVBoxLayout(self)
        outer.addWidget(QLabel(context["headline"]))

        # ---- cell positions -------------------------------------------------
        outer.addWidget(QLabelSeparator("Cell positions (.csv)"))
        path_row = QHBoxLayout()
        self.path_edit = QLineEdit(context["csv_path"])
        browse = QPushButton("Browse...")
        browse.clicked.connect(self._browse_csv)
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse)
        outer.addLayout(path_row)

        self.mode_widget = QWidget()
        mode_row = QHBoxLayout(self.mode_widget)
        mode_row.setContentsMargins(0, 0, 0, 0)
        mode_row.addWidget(QLabel("File exists - "))
        self.overwrite_rb = QRadioButton("Overwrite")
        self.append_rb = QRadioButton("Append to existing")
        self.overwrite_rb.setChecked(True)
        mode_row.addWidget(self.overwrite_rb)
        mode_row.addWidget(self.append_rb)
        mode_row.addStretch()
        outer.addWidget(self.mode_widget)

        self.point_ics = QCheckBox_custom("Point this model's initial conditions at this file")
        self.point_ics.setChecked(True)
        self._point_ics_pref = True
        self.point_ics.toggled.connect(self._point_ics_toggled)
        # Offered only when there is something to save anyway. With no cell definitions the
        # model is left exactly as it was, and pointing <cell_positions> somewhere new would
        # be a config edit the user did not ask for.
        self.point_ics.setVisible(bool(context["requests"]))
        outer.addWidget(self.point_ics)

        self.path_edit.textChanged.connect(self._update_mode)
        self._update_mode()

        if context["requests"]:
            self._build_cell_def_section(outer)
        else:
            outer.addWidget(QLabelSeparator("Cell definitions"))
            outer.addWidget(QLabel(
                "BIWT did not assign phenotypes to any cell type, so there is nothing to\n"
                "add to the model. Only the .csv will be written; the model is unchanged."))

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    # ------------------------------------------------------------------
    def _build_cell_def_section(self, outer):
        ctx = self.ctx
        outer.addWidget(QLabelSeparator("Cell definitions"))

        self.merge_rb = QRadioButton("Merge into the current model")
        self.new_file_rb = QRadioButton("Write a new config file:")
        self.skip_rb = QRadioButton("Don't save cell definitions (keep the .csv only)")

        # An explicit group rather than relying on auto-exclusivity: these three sit in
        # different layout rows, and without the group checking one does not reliably
        # uncheck the others -- which would leave destination() reading a stale answer.
        self.destination_group = QButtonGroup(self)
        for index, button in enumerate((self.merge_rb, self.new_file_rb, self.skip_rb)):
            self.destination_group.addButton(button, index)

        self.merge_rb.setChecked(True)
        outer.addWidget(self.merge_rb)

        detail = QLabel("        %s\n        Saves your current edits there first, and copies "
                        "the original aside as <name>.xml.<timestamp>.bak" % ctx["config_path"])
        detail.setStyleSheet("color: gray;")
        outer.addWidget(detail)

        outer.addWidget(self.new_file_rb)
        new_row = QHBoxLayout()
        new_row.addSpacing(20)
        self.new_path_edit = QLineEdit(ctx["new_file_default"])
        new_browse = QPushButton("Browse...")
        new_browse.clicked.connect(self._browse_xml)
        new_row.addWidget(self.new_path_edit, 1)
        new_row.addWidget(new_browse)
        outer.addLayout(new_row)
        outer.addWidget(self.skip_rb)

        # ---- domain ---------------------------------------------------
        if ctx["domain_rows"]:
            outer.addWidget(QLabelSeparator("Domain"))
            grid = QGridLayout()
            for r, (label, text) in enumerate(ctx["domain_rows"]):
                grid.addWidget(QLabel(label), r, 0)
                grid.addWidget(QLabel(text), r, 1)
            # Keep the extents next to the labels they belong to. Without a column that
            # takes up the slack, the value column stretches and the numbers drift off to
            # the far side of the dialog.
            grid.setColumnStretch(0, 0)
            grid.setColumnStretch(1, 0)
            grid.setColumnStretch(2, 1)
            outer.addLayout(grid)
            self.adopt_domain = QCheckBox_custom("Adopt BIWT's domain")
            self._adopt_domain_pref = (
                ctx["domain_differs"] and not ctx["dimensionality_flip"])
            self.adopt_domain.setChecked(self._adopt_domain_pref)
            self.adopt_domain.toggled.connect(self._adopt_domain_toggled)
            outer.addWidget(self.adopt_domain)
            if ctx["dimensionality_flip"]:
                warn = QLabel("        Warning: adopting this domain makes the model %s." %
                              ctx["dimensionality_flip"])
                warn.setStyleSheet("color: red;")
                outer.addWidget(warn)
            self.domain_default_note = QLabel(
                "        Unticked, the new file gets Studio's default domain, not this one.")
            self.domain_default_note.setStyleSheet("color: gray;")
            self.domain_default_note.setVisible(False)
            outer.addWidget(self.domain_default_note)
        else:
            self.adopt_domain = None
            self.domain_default_note = None

        # ---- what will happen -----------------------------------------
        self.outcome_header = QLabelSeparator("What will happen")
        outer.addWidget(self.outcome_header)
        area = self.outcome_area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setMinimumHeight(140)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)

        # The consequences live in their own widget so they can be swapped out wholesale.
        # Disabling the scroll area is not enough on its own: these labels carry explicit
        # stylesheet colours, which override the disabled palette, so the section would keep
        # its normal appearance and merely stop responding.
        self.outcome_body = QWidget()
        grid = QVBoxLayout(self.outcome_body)
        grid.setContentsMargins(0, 0, 0, 0)

        # Only the cell types something happens to; unchanged types get no row at all, and
        # the "nothing changes" line below covers the case where that is all of them.
        changing = [row for row in ctx["rows"] if not row.unchanged()]
        for row in changing:
            line = QHBoxLayout()
            name = QLabel(row.name)
            name.setMinimumWidth(160)
            line.addWidget(name)
            outcome = QLabel(row.outcome())
            outcome.setMinimumWidth(220)
            line.addWidget(outcome)
            note = QLabel(row.note())
            note.setStyleSheet("color: gray;")
            line.addWidget(note, 1)
            grid.addLayout(line)

        if ctx["rows"] and not changing:
            nothing = QLabel("No cell definitions change - every cell type BIWT returned is "
                             "already defined this way in the model.")
            nothing.setWordWrap(True)
            nothing.setStyleSheet("color: gray;")
            grid.addWidget(nothing)

        for text in ctx["notes"]:
            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet("color: #a05000;")
            grid.addWidget(label)

        # Merge only. A new file gets these substrates too, but as part of a microenvironment
        # built from scratch, which self.new_file_substrates reports instead.
        self.substrates_added = QLabel(
            "! These substrates will be added to the model, with diffusion, decay and initial "
            "condition all 0: %s. Set them in the Microenvironment tab."
            % ", ".join(ctx["substrates_to_add"]))
        self.substrates_added.setWordWrap(True)
        self.substrates_added.setStyleSheet("color: #a05000;")
        self.substrates_added.setVisible(False)
        grid.addWidget(self.substrates_added)

        # Cell types arriving with no secretion values. Its own label because whether there is
        # anything to connect them to depends on the destination -- see _destination_changed.
        self.substrate_setup_note = QLabel(
            "No secretion or uptake values came with %s - set them in Cell Types > Secretion."
            % ", ".join(ctx["needs_substrate_setup"]))
        self.substrate_setup_note.setWordWrap(True)
        self.substrate_setup_note.setStyleSheet("color: #a05000;")
        self.substrate_setup_note.setVisible(False)
        grid.addWidget(self.substrate_setup_note)

        # Rules naming cell types that will not exist. Its own label because what it says
        # depends on the destination -- see _destination_changed.
        self.rules_note = QLabel()
        self.rules_note.setWordWrap(True)
        self.rules_note.setStyleSheet("color: #a05000;")
        self.rules_note.setVisible(False)
        grid.addWidget(self.rules_note)

        # A new file gets its own microenvironment -- Studio's default plus whatever the
        # incoming cell types use -- so it is not the substrate list showing in the tabs
        # behind this dialog. Shown only for that destination, where it is the answer to
        # "what happened to my substrates".
        self.new_file_substrates = QLabel(
            "The new file's substrates: %s." % ", ".join(ctx["new_file_substrates"]))
        self.new_file_substrates.setWordWrap(True)
        self.new_file_substrates.setStyleSheet("color: gray;")
        self.new_file_substrates.setVisible(False)
        grid.addWidget(self.new_file_substrates)

        inner_layout.addWidget(self.outcome_body)

        self.outcome_placeholder = QLabel(
            "Nothing - only the cell positions .csv is being written.")
        self.outcome_placeholder.setStyleSheet("color: gray;")
        self.outcome_placeholder.setVisible(False)
        inner_layout.addWidget(self.outcome_placeholder)

        inner_layout.addStretch()
        area.setWidget(inner)
        outer.addWidget(area)

        self.reload_after = QCheckBox_custom("Reload the model in Studio when done")
        self.reload_after.setChecked(True)
        # What the user last asked for, so a trip through a destination that forces the box
        # one way or the other does not lose their answer.
        self._reload_pref = True
        self.reload_after.toggled.connect(self._reload_toggled)
        outer.addWidget(self.reload_after)

        for button in (self.merge_rb, self.new_file_rb, self.skip_rb):
            button.toggled.connect(self._destination_changed)
        self._destination_changed()

    # ------------------------------------------------------------------
    def _reload_toggled(self, checked):
        if self.reload_after.isEnabled():   # ignore the forced settings below
            self._reload_pref = checked

    def _adopt_domain_toggled(self, checked):
        if self.adopt_domain.isEnabled():
            self._adopt_domain_pref = checked
        self._destination_changed()

    def _point_ics_toggled(self, checked):
        if self.point_ics.isEnabled():
            self._point_ics_pref = checked

    def _destination_changed(self):
        merging = self.merge_rb.isChecked()
        saving = merging or self.new_file_rb.isChecked()

        self.new_path_edit.setEnabled(self.new_file_rb.isChecked())

        # Whichever config is being written is the one that gets pointed at the .csv. With no
        # config being written there is nothing to point, so the box is cleared rather than
        # left ticked over something that will not happen.
        self.point_ics.setEnabled(saving)
        self.point_ics.setChecked(self._point_ics_pref if saving else False)
        self.point_ics.setToolTip(
            "" if saving else
            "Only the .csv is being written, so no config's initial conditions are changed.")
        if self.adopt_domain is not None:
            # The domain only ever reaches a file alongside the cell definitions, so with
            # those dropped it is not adopted either.
            self.adopt_domain.setEnabled(saving)
            self.adopt_domain.setChecked(self._adopt_domain_pref if saving else False)
            self.adopt_domain.setToolTip(
                "" if saving else
                "Only the .csv is being written, so this model's domain is left alone.")

        # None of those consequences follow if the cell definitions are being dropped, so the
        # list is replaced by a line saying so rather than left standing.
        self.outcome_body.setVisible(saving)
        self.outcome_placeholder.setVisible(not saving)
        self.new_file_substrates.setVisible(self.new_file_rb.isChecked())
        self.substrates_added.setVisible(bool(merging and self.ctx["substrates_to_add"]))
        if self.domain_default_note is not None:
            self.domain_default_note.setVisible(
                self.new_file_rb.isChecked() and not self.adopt_domain.isChecked())

        # Which substrates those cell types come out at 0 for is whichever set the file they
        # are going into has - the open model's for a merge, and a new file's own, which is
        # built from Studio's defaults and owes nothing to the model. With no substrates
        # either way there is nothing to connect and nothing to say.
        have = (self.ctx["new_file_substrates"] if self.new_file_rb.isChecked()
                else self.ctx["model_substrates"])
        self.substrate_setup_note.setVisible(
            bool(saving and have and self.ctx["needs_substrate_setup"]))

        # A new file gets Studio's default <cell_rules>, so this model's ruleset is left
        # behind wholesale. A merge keeps it and only adds or replaces cell types, so a
        # finding there means the ruleset already named something this model does not define.
        if self.new_file_rb.isChecked():
            text = _new_file_rules_note(self.ctx["model_rule_count"])
        else:
            text = _rules_note(self.ctx["rules_findings"], "this model does not have")
        self.rules_note.setText(text)
        self.rules_note.setVisible(bool(text))

        # A merge writes cell definitions into the file behind Studio's back: param_d still
        # holds the old ones, and the next File > Save rebuilds <cell_definitions> from it,
        # undoing the merge. So the reload is not optional there.
        if merging:
            self.reload_after.setEnabled(False)
            self.reload_after.setChecked(True)
            self.reload_after.setToolTip(
                "A merge always reloads - the Cell Types tab has to be rebuilt from the "
                "merged file, or the next Save would undo the merge.")
        elif saving:
            self.reload_after.setEnabled(True)
            self.reload_after.setChecked(self._reload_pref)
            self.reload_after.setToolTip("")
        else:
            # Nothing is written, so there is nothing to reload -- say so by clearing it, not
            # just grey out a tick that would never happen.
            self.reload_after.setEnabled(False)
            self.reload_after.setChecked(False)
            self.reload_after.setToolTip(
                "Nothing is being written, so there is nothing to reload.")

    def _update_mode(self):
        self.mode_widget.setVisible(os.path.exists(self.path_edit.text().strip()))

    def _browse_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save cells.csv", self.path_edit.text(),
            "CSV files (*.csv);;All files (*)")
        if path:
            self.path_edit.setText(path)

    def _browse_xml(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PhysiCell Config", self.new_path_edit.text(),
            "XML files (*.xml);;All files (*)")
        if path:
            self.new_path_edit.setText(path)

    # ------------------------------------------------------------------
    def destination(self):
        if not self.ctx["requests"]:
            return DEST_SKIP
        if self.merge_rb.isChecked():
            return DEST_MERGE
        if self.new_file_rb.isChecked():
            return DEST_NEW_FILE
        return DEST_SKIP

    def accept(self):
        """Refuse a Save the flow could not act on, rather than let it close and do nothing.

        Both paths are typed by hand, so both can be blank. Caught here because by the time
        the flow reads them the .csv may already be on disk, and backing out at that point
        would mean a file written and no word about why nothing else was.
        """
        missing = None
        if not self.csv_path():
            missing = ("a file to write the cell positions to", self.path_edit)
        elif self.new_file_rb.isChecked() and not self.new_file_path():
            missing = ("a path for the new config file", self.new_path_edit)
        if missing is None:
            return super().accept()

        QMessageBox.warning(self.parent() or self, "BIWT - Save Results",
                            "Enter %s." % missing[0])
        missing[1].setFocus()

    def csv_path(self):
        return self.path_edit.text().strip()

    def append_mode(self):
        return self.append_rb.isChecked()

    def wants_ics_pointed(self):
        return self.point_ics.isChecked()

    def new_file_path(self):
        return self.new_path_edit.text().strip()

    def wants_domain(self):
        return self.adopt_domain is not None and self.adopt_domain.isChecked()

    def wants_reload(self):
        return self.reload_after.isChecked()


class BiwtCompletionFlow:
    """Drives everything between BIWT finishing and Studio showing the result."""

    def __init__(self, ics_tab):
        self.ics = ics_tab
        self.xml_creator = ics_tab.xml_creator

    # ------------------------------------------------------------------
    def run(self, result):
        if result is None:
            return  # BIWT calls back with None when the user cancels.

        requests = bridge.extract_cell_defs(result)
        self._add_requests_for_csv_types(result, requests)
        self._resolve(requests, self.xml_creator.xml_root.find(".//cell_definitions"))
        context = self._build_context(result, requests)
        dialog = BiwtSaveDialog(self.ics, context)
        if dialog.exec_() != QDialog.Accepted:
            return

        csv_path = dialog.csv_path()
        if not csv_path:
            return

        self._strip_csv_type_names(result)
        if not self._save_csv(result, csv_path, dialog.append_mode()):
            return

        folder, filename = os.path.split(csv_path)
        self.ics.csv_folder.setText(folder or ".")
        self.ics.output_file.setText(filename)

        destination = dialog.destination()
        if destination == DEST_SKIP:
            # Nothing else is touched -- with no cell definitions to add, the model the
            # user has open is left exactly as it was.
            self._receipt(csv_path, result, None, None, [], [], [], context)
            return

        chosen, replaced = self._chosen_cell_defs(context["rows"], merging=(destination == DEST_MERGE))
        if not chosen:
            self._receipt(csv_path, result, None, None, [], [], [], context)
            return

        if destination == DEST_MERGE:
            self._merge(dialog, result, chosen, replaced, csv_path, context)
        else:
            self._write_new_file(dialog, result, chosen, csv_path, context)

    # ------------------------------------------------------------------
    def _strip_csv_type_names(self, result):
        """Trim whitespace off the .csv's cell type names, as the config's are trimmed."""
        coordinates = getattr(result, "coordinates", None)
        if coordinates is None or "type" not in getattr(coordinates, "columns", []):
            return
        result.coordinates = coordinates.assign(
            type=coordinates["type"].astype(str).str.strip())

    def _add_requests_for_csv_types(self, result, requests):
        """Add a request for every cell type the .csv places that has no definition coming.

        A type left at "(none)" is simply absent from BIWT's mapping. Where the model already
        has that type, absence is the useful answer -- keep the definition Studio holds. Where
        it does not, the .csv would place cells that nothing defines, which PhysiCell refuses
        and the ICs tab reports only as an opaque "Invalid cell type name".
        """
        try:
            existing = list(self.xml_creator.celldef_tab.param_d.keys())
        except AttributeError:
            existing = []
        known = list(requests) + existing
        for name in _csv_types_without_definitions(result, known):
            requests[name] = bridge.request_for_csv_type(name)
        return requests

    def _resolve(self, requests, cell_definitions_elm):
        """Give every request an element, then fill in any phenotype section it lacks."""
        nanohub = getattr(self.xml_creator, "nanohub_flag", False)
        data_dir = getattr(self.xml_creator, "absolute_data_dir", None)
        bridge.resolve_cell_defs(requests, cell_definitions_elm, nanohub, data_dir)
        bridge.repair_cell_defs(requests, nanohub_flag=nanohub, data_dir=data_dir)
        return requests

    def _build_context(self, result, requests):
        xml_root = self.xml_creator.xml_root
        celldef_tab = self.xml_creator.celldef_tab
        existing_names = list(celldef_tab.param_d.keys())

        # Exact name only. Studio does no matching of its own: what the user called a cell type
        # in BIWT is what gets built, and if they meant one of this model's types they had its
        # own name to pick at the parameters step.
        matched, _added = bridge.classify_names(list(requests), existing_names)
        rows = [TypeRow(request, request.name in matched) for request in requests.values()]

        model_subs = bridge.model_substrates(xml_root)
        referenced = bridge.collect_referenced_substrates(requests)
        to_add = [s for s in referenced if s not in model_subs]
        # What "Write a new config file" would produce, from the same function that writes it.
        new_file_subs, new_file_extra = bridge.new_file_substrates(requests)
        # A cell type taken from this model names every substrate this model has, so choosing
        # one carries the lot into a new config. Surprising enough to explain, and it needs a
        # cell type to point at as the reason.
        carried_substrates = [s for s in new_file_extra if s in model_subs]
        carried_because = next((r.name for r in rows if r.request.from_host()), "")

        # What happens to the rules is entirely a question of destination. A merge keeps this
        # model's <cell_rules>, and only adds and replaces cell types, so anything the ruleset
        # names is still there afterwards -- a finding means the ruleset was already out of
        # step. A new file takes its <cell_rules> from Studio's defaults like every other
        # section, so the ruleset does not come across at all and its cell types are beside
        # the point; what matters is how much is being left behind.
        rules_csv = bridge.rules_csv_path(xml_root)
        merged_roster = list(existing_names) + [r.name for r in rows if r.name not in matched]
        rules_findings = bridge.scan_rules_for_missing_types(rules_csv, merged_roster)
        model_rule_count = bridge.count_rules(rules_csv)

        # Two reasons a cell type ends up on Studio's default phenotype, reported separately
        # because only one of them is the user's doing.
        no_template = sorted(r.name for r in rows
                             if not r.request.chose_template()
                             and r.request.origin == bridge.ORIGIN_DEFAULT)
        unusable = sorted(r.name for r in rows
                          if r.request.chose_template()
                          and r.request.origin == bridge.ORIGIN_DEFAULT)

        notes = []
        if unusable:
            notes.append(
                "! The template chosen for %s could not be used, so %s built from Studio's "
                "generic default phenotype instead. The rows above say why."
                % (", ".join(unusable), "it was" if len(unusable) == 1 else "they were"))
        if no_template:
            notes.append(
                "! No template was chosen for: %s. The .csv places cells of these types so "
                "they will be created with Studio's generic default phenotype."
                % ", ".join(no_template))
        # Only the cell types that actually arrive without secretion values. A run where every
        # type came from this model's own definitions changes no secretion at all, and saying
        # otherwise sends the user looking for something that is not there.
        needs_setup = sorted(r.name for r in rows if not r.brings_own_substrate_values())
        # Neither this nor the rules warning is in the notes list: both say something
        # different per destination, so the dialog carries them in labels of their own.

        foreign = sorted({
            request.source for request in requests.values()
            if request.source and not request.from_host()
            and not bridge.is_bundled_library(request.source)})
        if foreign:
            notes.append(
                "These phenotypes came from a template library other than the one Studio "
                "ships: %s" % ", ".join(foreign))

        # Both numbers off the .csv, which is what "placed" means. len(requests) is the
        # number of cell definitions Studio will build, and the two differ whenever a type is
        # defined but has no cells, or has cells and a definition the model already holds.
        count, kinds = 0, 0
        try:
            count = len(result.coordinates)
            kinds = len({str(n).strip() for n in result.coordinates["type"].unique()
                         if str(n).strip()})
        except Exception:
            pass
        headline = "BIWT placed %s cells in %d cell type%s." % (
            format(count, ","), kinds, "" if kinds == 1 else "s")
        if not count:
            headline = "BIWT placed no cells."

        config_path = os.path.abspath(self.xml_creator.current_xml_file)
        return {
            "headline": headline,
            "csv_path": self._default_csv_path(),
            "config_path": config_path,
            "new_file_default": os.path.join(
                os.path.dirname(config_path), "PhysiCell_settings_biwt.xml"),
            "requests": requests,
            "rows": rows,
            "notes": notes,
            "substrates_to_add": to_add,
            "new_file_substrates": new_file_subs,
            "model_substrates": model_subs,
            "needs_substrate_setup": needs_setup,
            "carried_substrates": carried_substrates,
            "carried_because": carried_because,
            "rules_findings": rules_findings,
            "model_rule_count": model_rule_count,
            "no_template": no_template,
            "unusable_template": unusable,
            **self._domain_context(result),
        }

    def _default_csv_path(self):
        folder = self.ics.csv_folder.text().strip() or "config"
        name = self.ics.output_file.text().strip() or "cells.csv"
        return os.path.join(folder, name)

    def _domain_context(self, result):
        domain = getattr(result, "domain_used", None)
        config_tab = self.xml_creator.config_tab
        if domain is None:
            return {"domain_rows": [], "domain_differs": False, "dimensionality_flip": ""}

        def current(widget, fallback=0.0):
            try:
                return float(widget.text())
            except (ValueError, AttributeError):
                return fallback

        now = (current(config_tab.xmin), current(config_tab.xmax),
               current(config_tab.ymin), current(config_tab.ymax),
               current(config_tab.zmin), current(config_tab.zmax))
        theirs = (float(domain.xmin), float(domain.xmax),
                  float(domain.ymin), float(domain.ymax),
                  float(domain.zmin), float(domain.zmax))

        # Pairs in the Config tab's order: x, y, z.
        fmt = lambda d: "[%g, %g] x [%g, %g] x [%g, %g]" % d
        label = _domain_source_label(getattr(domain, "source", ""))
        rows = [("current:", fmt(now)),
                ("BIWT:", fmt(theirs) + ("   (%s)" % label if label else ""))]

        differs = any(abs(a - b) > 1e-9 for a, b in zip(now, theirs))

        try:
            dz = float(config_tab.zdel.text())
        except (ValueError, AttributeError):
            dz = 20.0
        was_2d = bridge.is_2d(now[4], now[5], dz)
        becomes_2d = bridge.is_2d(theirs[4], theirs[5], dz)
        flip = ""
        if was_2d != becomes_2d:
            flip = "2D" if becomes_2d else "3D"
            if flip == "3D" and not getattr(self.xml_creator, "model3D_flag", False):
                flip = ("3D. Studio is running in 2D mode, so the ICs plot will ignore z "
                        "and cell motility stays 2D - restart with --3D to plot in 3D")
        return {"domain_rows": rows, "domain_differs": differs, "dimensionality_flip": flip}

    # ------------------------------------------------------------------
    def _chosen_cell_defs(self, rows, merging):
        """{name: ExtractedCellDef}, plus the names whose definitions are being replaced."""
        chosen = {row.name: row.request for row in rows}
        replaced = {row.name for row in rows if merging and row.replaces}
        return chosen, replaced

    def _save_csv(self, result, out_path, append):
        out_dir = os.path.dirname(out_path)
        try:
            if out_dir and not os.path.isdir(out_dir):
                os.makedirs(out_dir, exist_ok=True)

            if os.path.exists(out_path) and append:
                import pandas as _pd
                new_rows = result.coordinates[["x", "y", "z", "type"]]

                # A Studio cells CSV starts with x,y,z,type. Let pandas parse the header
                # (nrows=0 reads columns only) and refuse anything else rather than
                # trying to reshape it: appending to a file whose columns are ordered
                # differently would silently write each value into the wrong column.
                existing_cols = list(_pd.read_csv(out_path, nrows=0).columns)
                if existing_cols[:4] != ["x", "y", "z", "type"]:
                    raise ValueError(
                        "Cannot append: this file's first four columns are "
                        "%s, but a PhysiCell cells CSV must start with "
                        "['x', 'y', 'z', 'type']. Pick another file, or overwrite it."
                        % (existing_cols[:4],))

                if len(existing_cols) == 4:
                    # Exactly the columns we write: append in place, no rewrite.
                    new_rows.to_csv(out_path, mode="a", header=False, index=False)
                else:
                    # Extra columns after x,y,z,type (e.g. custom data). Appending only
                    # four fields would leave a ragged row PhysiCell may not parse, so
                    # align by name and rewrite, leaving the extras blank for new cells.
                    existing = _pd.read_csv(out_path)
                    _pd.concat([existing, new_rows], ignore_index=True).to_csv(out_path, index=False)
            else:
                result.to_csv(out_path)
        except Exception as e:
            # Deliberately broad: besides OSError, the append path can raise KeyError
            # if the result lacks the x/y/z/type columns, and a malformed existing CSV
            # raises from pandas. None of that should take the UI down mid-save.
            QMessageBox.critical(
                self.ics,
                "BIWT - Could not save cells CSV",
                "Failed to write '%s':\n\n%s: %s" % (out_path, type(e).__name__, e),
            )
            return False
        return True

    # ------------------------------------------------------------------
    def _merge(self, dialog, result, chosen, replaced, csv_path, context):
        xml_creator = self.xml_creator
        config_path = xml_creator.current_xml_file

        ok, reason = _is_writable(config_path)
        if not ok:
            QMessageBox.critical(
                self.ics, "BIWT - Cannot merge",
                "Studio cannot write to %s.\n\n%s\n\nNothing was changed. Use "
                '"Write a new config file" instead, or fix the file\'s permissions.'
                % (os.path.abspath(config_path), reason))
            return

        # Before anything is touched. check_valid_cell_defs() offers Cancel, and cancelling
        # after the substrates went in would leave them in a model this says nothing about.
        # It reads param_d for duplicate and non-contiguous IDs, so it does not care that the
        # new substrates are not in yet.
        if not xml_creator.celldef_tab.check_valid_cell_defs():
            # Cancelled at the ID check, which explains itself. The .csv is already written,
            # though, so end on the same receipt the "keep the .csv only" destination gets
            # rather than on nothing at all.
            self._receipt(csv_path, result, None, None, [], [], [], context)
            return

        # Add substrates first: microenv_tab fans out to celldef_tab.add_new_substrate(),
        # which seeds secretion and chemotactic sensitivity on *every* cell def already in
        # the model. Doing it after the flush would leave those cell defs without the new
        # substrate, and cell_def_tab.fill_xml() raises on exactly that.
        added_substrates = []
        for name in context["substrates_to_add"]:
            try:
                xml_creator.microenv_tab.new_substrate_named(name)
                added_substrates.append(name)
            except Exception as e:
                QMessageBox.critical(
                    self.ics, "BIWT - Cannot merge",
                    "Could not add the substrate '%s' to the model:\n\n%s: %s\n\n"
                    "Nothing was written." % (name, type(e).__name__, e))
                return

        self._apply_widgets(dialog, result, csv_path)

        if not xml_creator.update_xml_from_gui():
            # Past the point where backing out is free: the substrates and the widget values
            # are already in the model. Nothing is written to disk, but saying nothing would
            # leave the user with changes they did not make and no idea where they came from.
            QMessageBox.warning(
                self.ics, "BIWT - Merge stopped",
                "Studio could not update the model from the tabs, so nothing was written to "
                "%s.\n\nThe model in front of you already has %s. Undo them by re-opening the "
                "file without saving."
                % (os.path.abspath(config_path),
                   " and ".join(filter(None, [
                       "the substrates %s" % ", ".join(added_substrates) if added_substrates else "",
                       "the values BIWT proposed"]))))
            return

        xml_root = xml_creator.xml_root
        # Re-copy the host-sourced ones now the flush has written the user's pending edits,
        # then fill anything the fresh copy lacks.
        container = xml_root.find(".//cell_definitions")
        bridge.recopy_host_definitions(chosen, container)
        self._resolve(chosen, container)

        substrates = bridge.model_substrates(xml_root)
        existing = {cd.attrib.get("name"): cd
                    for cd in xml_root.findall(".//cell_definitions/cell_definition")}
        roster = [name for name in bridge.model_cell_type_names(xml_root)]
        for name in chosen:
            if name not in roster:
                roster.append(name)

        custom_src = self._custom_data_source(existing)

        reports = []
        for name, request in chosen.items():
            request.element.attrib["name"] = name
            reports.append(bridge.reconcile_cell_def(
                request.element, substrates, existing.get(name), roster, custom_src))

        try:
            backup = backup_config(config_path)
        except OSError as e:
            QMessageBox.critical(
                self.ics, "BIWT - Cannot merge",
                "Could not back up %s before overwriting it:\n\n%s: %s\n\nNothing was "
                "written." % (config_path, type(e).__name__, e))
            return

        elements = {name: request.element for name, request in chosen.items()}
        container = bridge.inject_cell_defs(xml_root, elements, replaced)
        if container is not None:
            # Now that the final roster is known, give every definition -- not just the ones
            # that arrived -- a row for each cell type in it.
            bridge.reconcile_cell_type_references(
                container, bridge.model_cell_type_names(xml_root))
        if container is None:
            QMessageBox.critical(
                self.ics, "BIWT - Cannot merge",
                "%s has no <cell_definitions> section, so there is nowhere to put these "
                "cell types.\n\nNothing was written." % os.path.abspath(config_path))
            return

        try:
            xml_creator.tree.write(config_path)
            pretty_print(config_path, config_path)
        except OSError as e:
            QMessageBox.critical(
                self.ics, "BIWT - Could not save config XML",
                "Failed to write '%s':\n\n%s: %s\n\nYour model now holds the merged cell "
                "types in memory but they are not saved. A backup of the original is at "
                "%s." % (config_path, type(e).__name__, e, backup))
            return

        self._reload(config_path)
        # A cell type copied from its own definition is still injected -- same content, same
        # slot -- but it is not something that happened to the model, so it is not reported
        # as one.
        unchanged = {row.name for row in context["rows"] if row.unchanged()}
        self._receipt(csv_path, result, config_path, backup,
                      sorted(n for n in replaced if n not in unchanged),
                      [n for n in chosen if n not in replaced],
                      added_substrates, context, reports,
                      rules_findings=context["rules_findings"])

    def _write_new_file(self, dialog, result, chosen, csv_path, context):
        path = dialog.new_file_path()
        if not path:
            return
        ok, reason = _is_writable(path)
        if not ok:
            QMessageBox.critical(
                self.ics, "BIWT - Cannot write config",
                "Studio cannot write to %s.\n\n%s\n\nNothing was changed."
                % (os.path.abspath(path), reason))
            return

        # "Use the host's definition" still means this model's, even when writing elsewhere --
        # and it means as the user has it now, not as it was last saved. Cell Types edits live
        # in celldef_tab.param_d until a flush writes them into the tree, so without this the
        # copy would silently be the stale one. The flush touches only the tree in memory; the
        # file this model came from is not written.
        xml_creator = self.xml_creator
        if not xml_creator.update_xml_from_gui():
            QMessageBox.critical(
                self.ics, "BIWT - Cannot write config",
                "Studio could not read the current state of the model's tabs, so the cell "
                "definitions it would copy cannot be trusted.\n\nNothing was written.")
            return
        container = xml_creator.xml_root.find(".//cell_definitions")
        bridge.recopy_host_definitions(chosen, container)
        self._resolve(chosen, container)

        substrates, extra = bridge.new_file_substrates(chosen)
        roster = list(chosen)

        reports = []
        for name, request in chosen.items():
            request.element.attrib["name"] = name
            reports.append(
                bridge.reconcile_cell_def(request.element, substrates, None, roster, None))

        elements = {name: request.element for name, request in chosen.items()}
        bridge.assign_names_and_ids(elements, start_id=0)

        domain = getattr(result, "domain_used", None) if dialog.wants_domain() else None
        config_tab = self.xml_creator.config_tab
        deltas = []
        for widget in (config_tab.xdel, config_tab.ydel, config_tab.zdel):
            try:
                deltas.append(float(widget.text()))
            except (ValueError, AttributeError):
                deltas.append(None)

        # The same checkbox the merge path honours, so it means one thing wherever it is
        # ticked: the config being written loads these cells at startup. Left None, the new
        # file keeps the defaults' disabled <cell_positions>.
        csv_folder = csv_file = None
        if dialog.wants_ics_pointed():
            csv_folder, csv_file = os.path.split(csv_path)
            csv_folder = csv_folder or "./config"
        tree = bridge.build_new_document(
            elements, domain, deltas, extra, csv_folder, csv_file)

        try:
            tree.write(path)
            pretty_print(path, path)
        except OSError as e:
            QMessageBox.critical(
                self.ics, "BIWT - Could not save config XML",
                "Failed to write '%s':\n\n%s: %s" % (path, type(e).__name__, e))
            return

        if dialog.wants_reload():
            self._reload(path)
        # The whole list, not just `extra`: every substrate in a new file is new to it, and
        # which ones came across is the thing the user cannot see from the destination row.
        self._receipt(csv_path, result, path, None, [], list(chosen), substrates,
                      context, reports, new_file=True, reloaded=dialog.wants_reload())

    # ------------------------------------------------------------------
    def _apply_widgets(self, dialog, result, csv_path):
        """Push the domain and the .csv path into the Config tab, before the flush.

        config_tab.fill_xml() is what carries these into the XML, and it derives use_2D
        from the z extent itself -- so setting the widgets and letting it run is both less
        code and the only way the two stay consistent.
        """
        config_tab = self.xml_creator.config_tab

        if dialog.wants_domain():
            domain = getattr(result, "domain_used", None)
            if domain is not None:
                for widget, value in (
                    (config_tab.xmin, domain.xmin), (config_tab.xmax, domain.xmax),
                    (config_tab.ymin, domain.ymin), (config_tab.ymax, domain.ymax),
                    (config_tab.zmin, domain.zmin), (config_tab.zmax, domain.zmax),
                ):
                    widget.setText(str(value))

        if dialog.wants_ics_pointed():
            # fill_xml() returns early when <initial_conditions> is missing and dereferences
            # <cell_positions> without checking, so make sure both are there first.
            self._ensure_initial_conditions()
            folder, filename = os.path.split(csv_path)
            config_tab.csv_folder.setText(folder or "./config")
            config_tab.csv_file.setText(filename)
            config_tab.cells_csv.setChecked(True)

    def _ensure_initial_conditions(self):
        xml_root = self.xml_creator.xml_root
        if xml_root.find(".//initial_conditions//cell_positions") is not None:
            return
        initial = xml_root.find(".//initial_conditions")
        if initial is None:
            initial = ET.fromstring(
                "<initial_conditions>%s</initial_conditions>"
                % pcdefaults.XML_DEFAULT_SECTIONS["initial_conditions"].strip())
            xml_root.append(initial)
        elif initial.find("cell_positions") is None:
            template = ET.fromstring(
                "<initial_conditions>%s</initial_conditions>"
                % pcdefaults.XML_DEFAULT_SECTIONS["initial_conditions"].strip())
            initial.append(template.find("cell_positions"))

    def _custom_data_source(self, existing):
        """A <custom_data> to give new cell types, so the shared table stays consistent."""
        if not existing:
            return None
        preferred = existing.get("default")
        if preferred is None:
            preferred = next(iter(existing.values()))
        return preferred.find("custom_data")

    def _reload(self, path):
        """Point every one of Studio's ideas of "the open file" at *path*, then reload.

        current_xml_file is what File > Save writes and config_file is what the reload
        parses; set only the latter and Save overwrites the file that was open before.
        """
        xml_creator = self.xml_creator
        xml_creator.current_xml_file = path
        xml_creator.config_file = path
        xml_creator.celldef_tab.config_path = path
        if getattr(xml_creator, "studio_flag", False):
            xml_creator.run_tab.config_file = path
            xml_creator.run_tab.config_xml_name.setText(path)
        xml_creator.show_sample_model()
        self.ics.tab_widget.setCurrentIndex(self.ics.base_tab_id)
        # show_sample_model() -> reset_xml_root() -> ics_tab.fill_gui() has already
        # re-pointed the BIWT input at the reloaded model.

    def _cell_type_trail(self, result):
        """Lines describing labels BIWT dropped or merged, or [] if nothing to say."""
        mapping = getattr(result, "cell_type_map", None)
        if not isinstance(mapping, dict) or not mapping:
            return []

        deleted = sorted(original for original, final in mapping.items() if final is None)
        merged = {}
        for original, final in mapping.items():
            if final is not None:
                merged.setdefault(final, []).append(original)

        lines = []
        if deleted:
            lines.append("Dropped in BIWT: %s." % ", ".join(deleted))
        for final, originals in sorted(merged.items()):
            if len(originals) > 1:
                lines.append("Merged into %s: %s." % (final, ", ".join(sorted(originals))))
        return lines

    def _receipt(self, csv_path, result, config_path, backup, replaced, added,
                 substrates, context, reports=(), new_file=False, rules_findings=(),
                 reloaded=True):
        # Built as rich text rather than indented plain text. A message box is narrow, and the
        # long items here -- an absolute path, a list of fifteen cell types -- always wrap;
        # with plain text the continuation returns to the left margin and the indentation
        # stops meaning anything. List items keep a hanging indent when they wrap.
        esc = _escape
        csv_item = esc(csv_path)
        try:
            csv_item += " &mdash; %s cells" % format(len(result.coordinates), ",")
        except Exception:
            pass

        html = ["<b>Wrote</b>", "<ul>", "<li>%s</li>" % csv_item]

        if config_path:
            folder, filename = os.path.split(os.path.abspath(config_path))
            detail = []
            if replaced:
                detail.append("replaced: %s" % esc(", ".join(replaced)))
            if added:
                detail.append("added: %s" % esc(", ".join(added)))
            # Name the sections, not just the cell types: "filled in" means Studio invented
            # parameters, and which ones decides whether that matters.
            for row in context["rows"]:
                if row.request.filled:
                    detail.append("%s: filled in %s" % (
                        esc(row.name),
                        esc(", ".join(p.rpartition("/")[2] for p in row.request.filled))))
            if substrates:
                detail.append("%s: %s" % (
                    "substrates" if new_file else "new substrates",
                    esc(", ".join(substrates))))
            if not (replaced or added or substrates):
                detail.append("no cell definitions changed")
            if backup:
                detail.append("backup: %s" % esc(os.path.basename(backup)))

            html.append("<li>%s<br><span style='color:gray;'>in %s</span>%s</li>" % (
                esc(filename), esc(folder),
                ("<ul>%s</ul>" % "".join("<li>%s</li>" % d for d in detail)) if detail else ""))
        html.append("</ul>")

        if not config_path:
            html.append("<p>The model was left unchanged.</p>")

        # Which substrates, not just which cell types. A type carrying values for four of five
        # substrates is not one whose "secretion and uptake are 0", and naming only the type
        # sends the user through every row looking for the gap. Types that came out with the
        # same gap share a line.
        zeroed = {}
        for report in reports:
            if report.substrates_zeroed:
                zeroed.setdefault(tuple(report.substrates_zeroed), []).append(report.name)
        if config_path and zeroed:
            groups = sorted((sorted(names), subs) for subs, names in zeroed.items())
            html.append("<p><b>Next</b><br>Secretion and uptake are 0 for %s. "
                        "Set them in Cell Types &gt; Secretion.</p>"
                        % "; ".join("%s: %s" % (esc(", ".join(names)), esc(", ".join(subs)))
                                    for names, subs in groups))

        # Every note below describes a cell definition. When no config was written there are
        # none, so saying any of this would contradict "the model was left unchanged".
        notes = []
        if config_path:
            # A new file's microenvironment is built from Studio's defaults, so a substrate
            # from the open model appearing in it needs explaining -- and so does why the
            # quiet ones were not left behind.
            if new_file and context["carried_substrates"]:
                notes.append(
                    "The currently loaded substrates were copied into the new config: %s. "
                    "That is because %s was taken from this model and names them."
                    % (esc(", ".join(context["carried_substrates"])),
                       esc(context["carried_because"])))
            if context["unusable_template"]:
                notes.append(
                    "The template chosen for %s could not be used, so Studio's generic default "
                    "phenotype was used instead. Set %s up in Cell Types."
                    % (esc(", ".join(context["unusable_template"])),
                       "it" if len(context["unusable_template"]) == 1 else "them"))
            if context["no_template"]:
                notes.append(
                    "%s had no template, so %s created with Studio's generic default phenotype "
                    "rather than anything drawn from this model. Set them up in Cell Types."
                    % (esc(", ".join(context["no_template"])),
                       "was" if len(context["no_template"]) == 1 else "were"))
            if new_file and context["model_rule_count"]:
                notes.append("The new config has no rules - the %d in this model stayed with it."
                             % context["model_rule_count"])
            if rules_findings:
                names = sorted({n for _r, _c, n in rules_findings})
                notes.append("The rules file still refers to %s." % esc(", ".join(names)))
            # cell_type_map is BIWT's audit trail from input cluster to output cell type. Only
            # worth showing where it says something the cell type list does not: a label that
            # was dropped, or several that were merged into one.
            notes.extend(esc(line) for line in self._cell_type_trail(result))
        if notes:
            html.append("<p><b>Note</b></p><ul>%s</ul>"
                        % "".join("<li>%s</li>" % n for n in notes))

        if new_file and not reloaded and notes:
            notes.insert(0, "Studio still has the previous model open - open %s to make any of "
                            "the changes below." % esc(os.path.basename(config_path)))

        version = _biwt_version()
        if version:
            html.append("<p style='color:gray;'>BIWT %s</p>" % esc(version))

        box = QMessageBox(self.ics)
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle("BIWT - Done")
        box.setTextFormat(QtCore.Qt.RichText)
        # The body goes in the informative text: a message box renders setText() as its
        # heading, in bold, which is unreadable for anything this long.
        box.setText("BIWT finished.")
        box.setInformativeText("".join(html))
        box.setStandardButtons(QMessageBox.Ok)

        # A message box is ~400px by default, which wraps a list of cell types into a column.
        # An invisible spacer on its grid is the supported way to widen one -- it has no
        # sizeHint of its own to set.
        layout = box.layout()
        layout.addItem(QSpacerItem(620, 0, QSizePolicy.Minimum, QSizePolicy.Expanding),
                       layout.rowCount(), 0, 1, layout.columnCount())
        box.exec()
