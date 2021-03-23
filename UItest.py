import sys
from pathlib import Path
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui
from PyQt5.uic import loadUi

# Stream class allows writing of sys.stdout to QTextEdit field
class Stream(qtc.QObject):
    newText = qtc.pyqtSignal(str)

    def write(self, text):
        self.newText.emit(str(text))

# Main UI class
class MainWindow(qtw.QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()
        loadUi("mainGUI.ui",self)

        self.s_dict = {}

        sys.stdout = Stream(newText=self.onUpdateText)

        self.files_button.clicked.connect(self.browse_files)
        self.folder_button.clicked.connect(self.browse_folders)
        self.run_button.clicked.connect(self.process_data)

        self.lst_cB = [self.cB_textpaths,self.cB_filenames,self.cB_calc_avg,self.cB_sv_avg,self.cB_sv_step,self.cB_sv_indv]
        self.lst_dict_names = ['text_paths','filenames','avg_calc','sv_avg','sv_step','sv_indv']

        self.cB_textpaths.stateChanged.connect(lambda:self.check_state(self.cB_textpaths,'text_paths'))
        self.cB_filenames.stateChanged.connect(lambda:self.check_state(self.cB_filenames,'filenames'))
        self.cB_calc_avg.stateChanged.connect(lambda:self.check_state(self.cB_calc_avg,'avg_calc'))
        self.cB_sv_avg.stateChanged.connect(lambda:self.check_state(self.cB_sv_avg,'sv_avg'))
        self.cB_sv_step.stateChanged.connect(lambda:self.check_state(self.cB_sv_step,'sv_step'))
        self.cB_sv_indv.stateChanged.connect(lambda:self.check_state(self.cB_sv_indv,'sv_indv'))

    def onUpdateText(self, text):
        cursor = self.log.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()

    def __del__(self):
        sys.stdout = sys.__stdout__

    def show_selection(self,f_paths):
        self.log.clear()

        print("Data folder:")
        print("{}".format(f_paths[0].parent))

        print(" ")
        print("Files to import:")
        for i, path in enumerate(f_paths):
            print("{}: {}".format(i,path.name))

    def browse_files(self):
        f_dlg = qtw.QFileDialog()
        f_dlg.setFileMode(qtw.QFileDialog.ExistingFiles)
        filter = "Arbin data (*.csv *.xlsx)"
        self.f_paths_temp = f_dlg.getOpenFileNames(self, "Select files", "C\\Desktop", filter)[0]
        self.s_dict['f_paths'] = [Path(i) for i in self.f_paths_temp]
        self.s_dict['folder_select'] = False
        self.show_selection(self.s_dict['f_paths'])

    def browse_folders(self):
        f_dlg = qtw.QFileDialog()
        f_dlg.setFileMode(qtw.QFileDialog.ExistingFiles)
        self.raw_folder = f_dlg.getExistingDirectory(self, "Select folder", "C\\Desktop")
        self.raw_folder = Path(self.raw_folder)
        self.s_dict['f_paths'] = list(self.raw_folder.glob('*.csv')) + list(self.raw_folder.glob('*.xlsx'))
        self.s_dict['folder_select'] = True
        self.show_selection(self.s_dict['f_paths'])

    def check_state(self,b,str):
        if b.isChecked() == True:
            self.s_dict[str] = True
        else:
            self.s_dict[str] = False

    def process_data(self):
        for i, cB in enumerate(self.lst_cB):
            self.check_state(cB, self.lst_dict_names[i])

        if self.usr_avg_name.text() == "":
            self.s_dict['avg_name'] = "average_data"
        else:
            self.s_dict['avg_name'] = self.usr_avg_name.text()

        self.log.clear()

        self.show_selection(self.s_dict['f_paths'])

        print(" ")
        print("Settings:")
        print_dict = {k: v for k, v in self.s_dict.items() if k not in {'f_paths'}}
        for key in print_dict:
            print("{}: {}".format(key,print_dict[key]))


if __name__ == "__main__":
    app = qtw.QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())