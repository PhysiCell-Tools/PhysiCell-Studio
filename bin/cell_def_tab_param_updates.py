from PyQt5.QtGui import QValidator

class CellDefParamUpdates:
    def __init__(self, parent=None):
        self.parent = parent

        self.diffusion_dt = parent.xml_creator.config_tab.diffusion_dt
        self.mechanics_dt = parent.xml_creator.config_tab.mechanics_dt
        self.phenotype_dt = parent.xml_creator.config_tab.phenotype_dt

        parent.cell_def_param_changed = self.cell_def_param_changed
        parent.cell_def_mechano_rate_changed = self.cell_def_mechano_rate_changed
        parent.cell_def_mechano_duration_changed = self.cell_def_mechano_duration_changed
        parent.cell_def_pheno_rate_changed = self.cell_def_pheno_rate_changed
        parent.cell_def_pheno_duration_changed = self.cell_def_pheno_duration_changed
        parent.cell_def_fixed_clicked = self.cell_def_fixed_clicked
        parent.check_rate_too_fast = self.check_rate_too_fast
        parent.is_dt_set = self.is_dt_set

    def get_current_celldef(self):
        return self.parent.get_current_celldef()
        
    # functions to update cell_def parameters and issue warnings if they are unecessarily fast
    def cell_def_param_changed(self, text, check=True, name=None):
        if name==None:
            name = self.parent.sender().objectName()
        if check:
            if name not in self.parent.param_d[self.get_current_celldef()].keys():
                print(f'cell_def_param_changed: {name} not in {self.parent.param_d[self.get_current_celldef()].keys()}')
                raise KeyError(f'cell_def_param_changed: {name} not in {self.parent.param_d[self.get_current_celldef()].keys()}')
        self.parent.param_d[self.get_current_celldef()][name] = text

    # we could use lambda functions to accomplish most/all of this. but this keeps the initialization of the widgets simpler
    def cell_def_mechano_rate_changed(self, text):
        self.cell_def_mechano_changed(text, self.check_rate_too_fast)

    def cell_def_mechano_duration_changed(self, text):
        self.cell_def_mechano_changed(text, self.check_duration_too_fast)
        
    def cell_def_mechano_changed(self, text, fn):
        self.cell_def_rate_changed(text, fn, "mechanics_dt")

    def cell_def_pheno_rate_changed(self, text):
        self.cell_def_pheno_changed(text, self.check_rate_too_fast)

    def cell_def_pheno_duration_changed(self, text):
        self.cell_def_pheno_changed(text, self.check_duration_too_fast)

    def cell_def_pheno_changed(self, text, fn):
        self.cell_def_rate_changed(text, fn, "phenotype_dt")

    def cell_def_rate_changed(self, text, fn, time_step):
        name = self.parent.sender().objectName()
        label = getattr(self.parent, f"{name}_warning_label")
        fn(text, label, time_step=time_step)
        self.cell_def_param_changed(text, check=False, name=name)
        
    def cell_def_fixed_clicked(self, bval):
        name = self.parent.sender().objectName()
        fixed_rate_name = f"{name}_trate"
        fixed_duration_name = f"{name}_duration"
        self.parent.param_d[self.get_current_celldef()][fixed_rate_name] = bval
        self.parent.param_d[self.get_current_celldef()][fixed_duration_name] = bval
        getattr(self.parent, fixed_rate_name).setChecked(bval)   # sync rate and duration
        getattr(self.parent, fixed_duration_name).setChecked(bval)   # sync rate and duration

    def check_rate_too_fast(self, text, label, time_step="mechanics_dt"):
        self.check_too_fast(text, label, time_step)

    def check_duration_too_fast(self, text, label, time_step="mechanics_dt"):
        self.check_too_fast(text, label, time_step, is_duration=True)

    def check_too_fast(self, text, label, time_step, is_duration=False):
        if self.parent.sender().validator().validate(text,0)[0]==QValidator.Intermediate:
            return

        if time_step == "diffusion_dt":
            dt_text = self.diffusion_dt.text()
        elif time_step == "mechanics_dt":
            dt_text = self.mechanics_dt.text()
        elif time_step == "phenotype_dt":
            dt_text = self.phenotype_dt.text()

        if self.is_dt_set(label, time_step, dt_text) == False:
            return

        rate = float(text)
        if is_duration:
            if rate==0:
                label.hide_icon()
                return # if duration is set to 0, then they already know it is going to happen instantaneously
            rate = 1/rate
        dt = float(dt_text)
        max_val = dt if is_duration else 1/dt # help the user with the max value depending on if it's a rate or duration
        prob = rate * dt
        if prob > 1:
            label.show_icon()
            phrase = f"duration < {time_step}" if is_duration else f"rate > 1/{time_step}"
            label.setHoverText(f"WARNING: A {phrase} is instantaneous. May as well set to {max_val}.")
        else:
            label.hide_icon()

    def is_dt_set(self, label, time_step, dt_text):
        if dt_text != "" and float(dt_text) != 0:
            return True
        label.show_icon()
        label.setHoverText(f"WARNING: Current {time_step} is 0 (or unset). Make sure to set that value > 0.")
        return False