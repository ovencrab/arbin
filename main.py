### Import packages ###
import sys
from pathlib import Path
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui
from PyQt5 import uic
import resources

### Import *.py functions ###
from arbin import process

# Stream class allows writing of sys.stdout to QTextEdit field
class Stream(qtc.QObject):
    newText = qtc.pyqtSignal(str)

    def write(self, text):
        self.newText.emit(str(text))

# Main UI class
class MainWindow(qtw.QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()
        fileh = qtc.QFile(':/ui/mainGUI.ui')
        fileh.open(qtc.QFile.ReadOnly)
        uic.loadUi(fileh, self)
        fileh.close()


        # Create settings dictionary
        self.s_dict = {}

        # Re-route standard python prints and errors using Stream and onUpdateText function
        sys.stdout = Stream(newText=self.onUpdateText)
        sys.stderr = Stream(newText=self.onUpdateText)

        # Clickable buttons
        self.files_button.clicked.connect(self.browse_files)
        self.folder_button.clicked.connect(self.browse_folders)
        self.run_button.clicked.connect(self.process_data)
        self.close_button.clicked.connect(lambda:self.close())

        # Create list of checkboxes and complementary dictionary key names
        self.lst_cB = [self.cB_textpaths,self.cB_filenames,self.cB_calc_avg,self.cB_sv_avg,self.cB_sv_step,self.cB_sv_indv]
        self.lst_dict_names = ['text_paths','use_filenames','avg_calc','sv_avg','sv_step','sv_indv']

    # Print python prints and errors to log (QTextEdit)
    def onUpdateText(self, text):
        cursor = self.log.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()

    def __del__(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    # Prints files and folders selected by the user to the log
    def show_selection(self,f_paths):
        self.log.clear()

        print("Data folder:")
        print("{}".format(f_paths[0].parent))

        print(" ")
        print("Files to import:")
        for i, path in enumerate(f_paths):
            print("{}: {}".format(i,path.name))

    # Allows user to select files by dialog
    def browse_files(self):
        self.log.clear()
        f_dlg = qtw.QFileDialog()
        f_dlg.setFileMode(qtw.QFileDialog.ExistingFiles)
        filter = "Arbin data (*.csv *.xlsx)"
        self.f_paths_temp = f_dlg.getOpenFileNames(self, "Select files", "C\\Desktop", filter)[0]
        if self.f_paths_temp:
            self.s_dict['f_paths'] = [Path(i) for i in self.f_paths_temp]
            self.s_dict['raw_dir'] = self.s_dict['f_paths'][0].parent
            self.s_dict['folder_select'] = False
            self.show_selection(self.s_dict['f_paths'])
        else:
            print('No files selected')

    # Allows user to select a folder by dialog
    def browse_folders(self):
        self.log.clear()
        f_dlg = qtw.QFileDialog()
        f_dlg.setFileMode(qtw.QFileDialog.ExistingFiles)
        self.s_dict['raw_dir'] = f_dlg.getExistingDirectory(self, "Select folder", "C\\Desktop")
        if self.s_dict['raw_dir']:
            self.s_dict['raw_dir'] = Path(self.s_dict['raw_dir'])
            self.s_dict['f_paths'] = list(self.s_dict['raw_dir'].glob('*.csv')) + list(self.s_dict['raw_dir'].glob('*.xlsx'))
            self.s_dict['folder_select'] = True
            self.show_selection(self.s_dict['f_paths'])
        else:
            print('No folder selected')

    # Checks checkbox state and adds key (lst_dict_names) - value (bool) pair to settings dictionary
    def check_state(self,b,str):
        if b.isChecked() == True:
            self.s_dict[str] = True
        else:
            self.s_dict[str] = False

    # When run button is clicked, print settings info and run script
    def process_data(self):
        # Build settings dictionary
        for i, cB in enumerate(self.lst_cB):
            self.check_state(cB, self.lst_dict_names[i])

        # Check value of CV filter ratio text field
        if self.cv_filter_edit.text() == "":
            self.s_dict['cv_cut'] = 1.1
        else:
            self.s_dict['cv_cut'] = self.cv_filter_edit.text()

        # Check value of 'Average name' text field
        if self.avg_name_edit.text() == "":
            self.s_dict['avg_name'] = "average_data"
        else:
            self.s_dict['avg_name'] = self.avg_name_edit.text()

        # Clear log
        self.log.clear()

        # Print folder and filenames
        self.show_selection(self.s_dict['f_paths'])

        # Print settings dictionary
        print(" ")
        print("Settings:")
        print_dict = {k: v for k, v in self.s_dict.items() if k not in {'f_paths','raw_dir'}}
        for key in print_dict:
            print("{}: {}".format(key,print_dict[key]))

        print(" ")
        process(self.s_dict)


if __name__ == "__main__":
    app = qtw.QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())