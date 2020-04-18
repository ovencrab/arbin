### Import packages ###
from tkinter import Tk
from tkinter.filedialog import askopenfilenames, askdirectory
from pathlib import Path
import yaml
import pandas as pd
import os
import shutil

### Debugging ###
import time
import sys

### Import functions ###
import load

### Options ###

# Folder or file import
folder_select = 0

# Excel files need converting - very slow, excel vba conversion recommended
# (see 'Excel add-in' folder
convert_excel = 0

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Script ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Select files and call import functions
if folder_select == 0 :

    # Open dialog box to select files
    #Tk().withdraw()
    #filez = askopenfilenames(title='Choose a file',
    #                         filetypes=((".csv files", "*.csv"),("Excel files", "*.xlsx *.xls"), ("All files", "*.*")))

    # Create list of files and extract folder path from first file path
    #data_path = list(filez)
    data_path = [Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/JE_LtS_rate_B1_12_Channel_12.csv',
                 Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/JE_LtS_rate_B2_13_Channel_13.csv',
                 Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/JE_LtS_rate_B3_14_Channel_14.csv']
    data_folder = Path(data_path[0]).parent

    # Finds the .yaml file in data_folder and creates a dictionary from the information
    info_path = list(data_folder.glob('*.yaml'))
    with open(str(info_path[0])) as file:
        cell_info = yaml.full_load(file)

    # Create dataframes from xlsx or csv files, and convert xlsx files to csv
    tic = time.perf_counter()
    if convert_excel == 1 :
        df, n_cells = load.xlsx(data_folder, data_path, cell_info)
    else:
        df, n_cells = load.csv(data_path, cell_info)
    
    toc = time.perf_counter()
    print(f"Imported files in {toc - tic:0.1f}s")
else:
    # Open dialog box to select folder
    Tk().withdraw()  # stops root window from appearing
    data_folder = askdirectory(title="Choose data folder")  # "Open" dialog box and return the selected path

    # Finds the .yaml file in data_folder and creates a dictionary from the information
    info_path = list(Path(data_folder).glob('*.yaml'))
    with open(str(info_path[0])) as file:
        cell_info = yaml.full_load(file)

    tic = time.perf_counter()
    # Create dataframes from xlsx and csv files, and convert xlsx files to csv
    if convert_excel == 1:
        data_path = list(Path(data_folder).glob('*.xlsx'))
        df, n_cells = load.xlsx(data_folder, data_path, cell_info)
    else:
        data_path = list(Path(data_folder).glob('*.csv'))
        df, n_cells = load.csv(data_path, cell_info)
    
    toc = time.perf_counter()
    print(f"Imported files in {toc - tic:0.1f}s")

# Print data
print("Returned data:")
[print(key, ': ', value) for key, value in cell_info.items()]
print(df)

# Data filtering

# Find mean current value of each step (i.e. rest, charge, discharge)
df_grouped = df.groupby(['cell', 'Cycle_Index', 'Step_Index'])['Current(A)'].mean()
print(df_grouped.loc[(1)])

# Drop rows of data that aren't a charge or discharge step
df_grouped_dropped = df_grouped.drop(index=3, level=2)
print(df_grouped_dropped.loc[(1)])

sys.exit()