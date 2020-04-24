### Import packages ###
from tkinter import Tk
from tkinter.filedialog import askopenfilenames, askdirectory
from pathlib import Path
import yaml
import pandas as pd
import os
import shutil
from math import floor

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

# Find mean current value of each step (i.e. rest, charge, discharge)
df_grouped = df.groupby(['cell', 'cycle_index', 'step_index'])['current'].mean()
print('1 - Created dataframe of mean current values per step_index.')

# Find indexes which have an average current of 0 and drop them (as they should be the initial rest steps)
df = df.drop(df_grouped.index[df_grouped == 0].tolist())
df_avg_zero = df_grouped.drop(df_grouped.index[df_grouped == 0].tolist())
print('2 - Dropped \'average current = 0\' rows.')
#print(df_avg_zero.head())

# Find indexes where the current reduces to 0 and drop them (rest steps after charge or discharge)
df_filt = df_avg_zero.drop(df.index[df['current'] == 0].tolist())
df = df.drop(df.index[df['current'] == 0].tolist())
print('3 - Dropped indexes that have \'current = 0\' in any row.')

tic = time.perf_counter()

df_grouped = df.groupby(['cell', 'cycle_index', 'step_index'])['current'].mean()

df.loc[df_grouped.index[df_grouped > 0].tolist(), 'new_index'] = 'pos'
df.loc[df_grouped.index[df_grouped < 0].tolist(), 'new_index'] = 'neg'

df.reset_index(level='step_index',inplace=True,drop=True)
df.set_index(['new_index', 'date_time'], inplace=True, append=True)
df.index.names = ['cell', 'cycle_index', 'step_index', 'date_time']
df.index.sortlevel(level='date_time')

toc = time.perf_counter()
print(f"4 - Created new index in {toc - tic:0.1f}s")

#------------------------
# Downsampling

print('--------------------------------------')
print('Downsampling data')
print('--------------------------------------')

df_plot = df[['test_time','voltage']]

df_plot.reset_index(level='date_time', inplace=True)
df_plot.sort_index()
my_index = pd.MultiIndex(levels=[[0],[1],[2]], codes=[[],[],[]], names=['cell','cycle_index','step_index'])
df_downsampled = pd.DataFrame(columns=df_plot.columns, index=my_index)

L0_start = df_plot.index.get_level_values(0)[1]
L0_end = df_plot.index.get_level_values(0)[-1]
L1_start = df_plot.index.get_level_values(1)[1]
L2_start = df_plot.index.get_level_values(2)[1]

counter = 1
for i in df_plot.index.unique() :
    df_temp = df_plot.loc[i]

    if len(df_temp) > 1000 :
        downsampler = floor(len(df_temp)/500)
        df_downsampled = df_downsampled.append(df_temp.iloc[::downsampler])

        if df_downsampled['voltage'].iloc[-1] != df_temp['voltage'].iloc[-1] :
            df_downsampled = df_downsampled.append(df_temp.iloc[-1])

        if L0_start <= i[0] <= L0_end and i[1] == L1_start and i[2] == L2_start :
            print('{} - Downsampled {}...'.format(counter, i))
            counter = counter + 1

    else :
        df_downsampled = df_downsampled.append(df_temp.iloc[::downsampler])

        if L0_start <= i[0] <= L0_end and i[1] == L1_start and i[2] == L2_start :
            print('{} - Left {}...'.format(counter, i))
            counter = counter + 1

df_downsampled.set_index('date_time', append=True, inplace=True)
df_downsampled.index.sortlevel(level='date_time')

print('{} - Reduced number of rows from {} to {}'.format(counter, df.shape[0], df_downsampled.shape[0]))

#------------------------
# Plotting test

print('--------------------------------------')
print('Plot data')
print('--------------------------------------')

df_slice = df_downsampled.loc[(1, 1)]

g = sns.relplot(x="test_time", y="voltage", kind="line", data=df_slice)
g.fig.autofmt_xdate()
plt.show()

print('Plotted')

sys.exit()