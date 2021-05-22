# ~/git/PhysiCell-model-builder/bin$ grep qlineed cell_def_tab.py |grep self >qlineedits.txt

"""
        self.apoptosis_death_rate = QLineEdit()
        self.apoptosis_death_rate.setValidator(QtGui.QDoubleValidator())
        self.apoptosis_death_rate.textChanged.connect(self.apop_death_rate_changed)

        self.secretion_net_export_rate.textChanged.connect(self.secretion_net_export_rate_changed


    def apop_phase0_changed(self, text):
        self.param_d[self.current_cell_def]["apop_phase0"] = text

"""
for loop in range(2):
  with open('qlineedits.txt') as f:
#   self.relative_maximum_adhesion_distance = QLineEdit()
    for line in f:
        # print(len(line),line)
        if (line[0] == '#'):
            continue
        iptr = line.index('=')
        objname = line[:iptr].strip()
        if '#' in objname:
            continue
        if loop==0:
            print(8*' ' + objname + ".textChanged.connect(" + objname + "_changed)")
        else:
            print(4*' ' + "def " + objname[5:] + "_changed(self, text):")
            print(8*' ' + "self.param_d[self.current_cell_def]['" + objname[5:] + "'] = text")
        # print('after =',line[iptr:])