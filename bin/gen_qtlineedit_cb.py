# This script reads a Qt Python module, looks for a "QLineEdit()" object, and insert a callback method
# connection for when a user changes the text in the widget, e.g.:

#         self.apoptosis_death_rate = QLineEdit()
#         self.apoptosis_death_rate.textChanged.connect(self.apop_death_rate_changed)  # <----- insert this line
#         self.apoptosis_death_rate.setValidator(QtGui.QDoubleValidator())
# 
# Author: Randy Heiland

k=0
sed_file = open("sed_cmds.sh", "w")
# with open('qlineedits.txt') as f:
with open('tmp.py') as f:
#   self.relative_maximum_adhesion_distance = QLineEdit()
    for line in f:
        # print(len(line),line)
        if 'QLineEdit()' in line:
            if '#' in line or 'self' not in line:
                continue
            print(line,end="")
            iptr = line.index('=')
            objname = line[:iptr].strip()
            line2 = line.strip()
            print(line2,end="")

            if (k % 2) == 0:
                cmd = 'gsed -e "/' + line2 + '/a \\\        ' + objname + '.textChanged.connect(' + objname + '_changed)" <foo.py >bar.py'
            else:
                cmd = 'gsed -e "/' + line2 + '/a \\\        ' + objname + '.textChanged.connect(' + objname + '_changed)" <bar.py >foo.py'
            sed_file.write(cmd+'\n')

            k += 1
            # if k > 10:
            #     break

# gsed -e "/self.cycle_trate00 = QLineEdit()/a \\        self.cycle_trate00.textChanged.connect(self.cycle_trate00_changed)" <foo.txt

        # if loop==0:
        #     print(8*' ' + objname + ".textChanged.connect(" + objname + "_changed)")
        # else:
        #     print(4*' ' + "def " + objname[5:] + "_changed(self, text):")
        #     print(8*' ' + "self.param_d[self.current_cell_def]['" + objname[5:] + "'] = text")
# new_file.close()