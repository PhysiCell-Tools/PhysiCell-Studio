import os
import glob
import zipfile
from PyQt5.QtWidgets import QMessageBox

try:
    from galaxy_ie_helpers import put
except:
    pass

#-----------------------------------------------------------------
# Helper functions for Galaxy
def save_project_galaxy(self):
    fname = "my_model.zip"
    file_str = "config/*.csv"
    file_str = os.path.join(os.getcwd(), file_str)
    print('-------- save_project_galaxy(): zip up all ',file_str)

    msgBox = QMessageBox()
    msgBox.setText(f"This will start a job that bundles your current model's config file, its cells and substrates ICs, and its rules, and creates and copies '{fname}' to the Galaxy History. You can download it from there once it completes.")
    msgBox.setIcon(QMessageBox.Information)
    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    returnValue = msgBox.exec()
    if returnValue == QMessageBox.Cancel:
        return

    try:
        with zipfile.ZipFile(fname, 'w') as myzip:
            # myzip.write(self.current_xml_file)
            myzip.write(self.current_xml_file, os.path.basename(self.current_xml_file))
            for f in glob.glob(file_str):
                myzip.write(f, os.path.basename(f))   # 2nd arg avoids full filename 
            # csv_files = glob.glob(file_str)
            # print("csv_files = ",csv_files)
            # for f in glob.glob(file_str):
                # myzip.write(f, os.path.basename(f))   # 2nd arg avoids full filename 
        put(fname)
        # print("dummy put...")
    except:
        self.show_error_message(f"Error: put({fname})")
    return


def load_project_galaxy_history(self):
    from galaxy_history import LoadProjectWindow
    self.project_historyUI = LoadProjectWindow()
    self.project_historyUI.xml_creator = self
    # hack to bring to foreground
    self.project_historyUI.hide()
    self.project_historyUI.show()

def get_galaxy_history(self):
    from galaxy_history import GalaxyHistoryWindow
    self.galaxy_historyUI = GalaxyHistoryWindow(self)
    # hack to bring to foreground
    self.galaxy_historyUI.hide()
    self.galaxy_historyUI.show()

def download_config_galaxy(self):
    # put("config/PhysiCell_settings.xml")
    #     put( args.filepath, file_type=args.filetype, history_id=args.history_id )
    # fname = "/opt/pcstudio/config/PhysiCell_settings.xml"
    fname = self.current_xml_file 
    msgBox = QMessageBox()
    msgBox.setText("This will start a job that copies your current model's config file to the Galaxy History. You can download it from there once it completes.")
    msgBox.setIcon(QMessageBox.Information)
    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    returnValue = msgBox.exec()
    if returnValue == QMessageBox.Cancel:
        return
    try:
        put(fname)
        # print("dummy put...")
    except:
        self.show_error_message(f"Error: put({fname})")
    return

def download_zipped_csv_galaxy(self):
    # fname = "/opt/pcstudio/all_csv.zip"
    msgBox = QMessageBox()
    msgBox.setText("This will start a job that copies a zip file of all output/*.csv to the Galaxy History. You can download it from there once it completes.")
    msgBox.setIcon(QMessageBox.Information)
    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    returnValue = msgBox.exec()
    if returnValue == QMessageBox.Cancel:
        return
    fname = "all_csv.zip"
    print("download_zipped_csv_galaxy():  cwd= ",os.getcwd())
    try:
        # file_str = "/opt/pcstudio/output/*.csv"
        file_str = "output/*.csv"
        file_str = os.path.join(os.getcwd(), file_str)
        print('-------- download_zipped_csv_galaxy(): zip up all ',file_str)
        # fname = "/opt/pcstudio/output/all_csv.zip"
        with zipfile.ZipFile(fname, 'w') as myzip:
            # csv_files = glob.glob(file_str)
            # print("csv_files = ",csv_files)
            for f in glob.glob(file_str):
                myzip.write(f, os.path.basename(f))   # 2nd arg avoids full filename 
    except:
        self.show_error_message(f"Error zipping all output/*.csv")
        return

    try:
        put(fname)
        # print("dummy put...")
    except:
        self.show_error_message(f"Error: put({fname})")

def download_all_zipped_galaxy(self):
    # fname = "/opt/pcstudio/all_output.zip"
    msgBox = QMessageBox()
    msgBox.setText("This will start a job that copies a zip file of all output/* to the Galaxy History. You can download it from there once it completes. If you have a lot of output files from your simulation, it may take a while to complete, but it runs in the background and will not affect your ability to continue using the Studio.")
    msgBox.setIcon(QMessageBox.Information)
    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    returnValue = msgBox.exec()
    if returnValue == QMessageBox.Cancel:
        return

    fname = "all_output.zip"
    print("download_all_zipped_galaxy():  cwd= ",os.getcwd())
    try:
        # file_str = "/opt/pcstudio/output/*.csv"
        file_str = "output/*"
        file_str = os.path.join(os.getcwd(), file_str)
        print('-------- download_all_zipped_galaxy(): zip up all ',file_str)
        # fname = "/opt/pcstudio/output/all_csv.zip"
        with zipfile.ZipFile(fname, 'w') as myzip:
            # all_files = glob.glob(file_str)
            # print("all_files = ",all_files)
            for f in glob.glob(file_str):
                myzip.write(f, os.path.basename(f))   # 2nd arg avoids full filename 
    except:
        self.show_error_message(f"Error zipping all output/*")
        return

    try:
        put(fname)
        # print("dummy put")
    except:
        self.show_error_message(f"Error: put({fname})")
