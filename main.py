### Import packages ###
from tkinter import Tk
from tkinter.filedialog import askopenfilenames, askdirectory
from pathlib import Path
import yaml
import pandas as pd
import os
import shutil

### Plotting ###

import matplotlib
import cufflinks as cf #conda install -c conda-forge cufflinks-py
import plotly
import plotly.offline as py
import plotly.graph_objs as go

import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style="darkgrid")

### Debugging ###
import time
import sys

### Import functions ###
import load
import filt

### Options ###

# Folder or file import
folder_select = 0

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
    cell_info = load.yml(data_folder)

    # Create dataframes from xlsx or csv files, and convert xlsx files to csv
    tic = time.perf_counter()
    df, n_cells = load.csv(data_path, cell_info)
    toc = time.perf_counter()
    print(f"Imported files in {toc - tic:0.1f}s")
else:
    # Open dialog box to select folder
    Tk().withdraw()  # stops root window from appearing
    data_folder = askdirectory(title="Choose data folder")  # "Open" dialog box and return the selected path

    # Finds the .yaml file in data_folder and creates a dictionary from the information
    cell_info = load.yml(data_folder)

    # Create dataframes from csv files, and convert xlsx files to csv
    tic = time.perf_counter()
    data_path = list(Path(data_folder).glob('*.csv'))
    df, n_cells = load.csv(data_path, cell_info)
    toc = time.perf_counter()
    print(f"Imported files in {toc - tic:0.1f}s")

# Print data
print('--------------------------------------')
print("Returned data:")
print('--------------------------------------')
[print(key, ': ', value) for key, value in cell_info.items()]
print('Dataframe size: {}'.format(df.size))

#------------------------
# Data filtering

print('--------------------------------------')
print('Data filtering')
print('--------------------------------------')

tic = time.perf_counter()

df = filt.index(df)

toc = time.perf_counter()
print(f"4 - Created new index in {toc - tic:0.1f}s")

#------------------------
# Downsampling

print('--------------------------------------')
print('Downsampling data')
print('--------------------------------------')

tic = time.perf_counter()

df_downsampled, counter = filt.downsample(df)

toc = time.perf_counter()
t = f'{toc - tic:0.1f}'
print('{} - Reduced number of rows from {} to {} in {}s'.format(counter, df.shape[0], df_downsampled.shape[0],t))

#------------------------
# Plotting test

print('--------------------------------------')
print('Plot data')
print('--------------------------------------')

df_slice = df_downsampled.loc[(1, 11)]

g = sns.relplot(x="test_time", y="voltage", kind="line", data=df_slice)
g.fig.autofmt_xdate()
plt.show()

print('Plotted')

sys.exit()