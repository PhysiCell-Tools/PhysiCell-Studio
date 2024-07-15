from PyQt5.QtWidgets import QMessageBox

def show_warning(msg):
    msgBox = QMessageBox()
    msgBox.setIcon(QMessageBox.Information)
    msgBox.setText(msg)
    msgBox.setStandardButtons(QMessageBox.Ok)

    return msgBox.exec()