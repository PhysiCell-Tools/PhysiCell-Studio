from PyQt5.QtWidgets import QMessageBox

def show_studio_warning_window(msg):
    msgBox = QMessageBox()
    msgBox.setIcon(QMessageBox.Information)
    msgBox.setText(msg)
    msgBox.setStandardButtons(QMessageBox.Ok)

    return msgBox.exec()

def style_sheet_template(widget_class):
    return f"""
            {widget_class.__name__}:disabled {{
                background-color: lightgray;
                color: black;
            }}
            {widget_class.__name__}:enabled {{
                background-color: white;
                color: black;
            }}
            """