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
print("Returned data:")
[print(key, ': ', value) for key, value in cell_info.items()]
print(df)

#------------------------
# Data filtering

# Find mean current value of each step (i.e. rest, charge, discharge)
df_grouped = df.groupby(['cell', 'cycle_index', 'step_index'])['current'].mean()
print('Created dataframe of mean current values per step_index.')
#print(df_grouped.head())

# Find indexes which have an average current of 0 and drop them (as they should be the initial rest steps)
df = df.drop(df_grouped.index[df_grouped == 0].tolist())
df_avg_zero = df_grouped.drop(df_grouped.index[df_grouped == 0].tolist())
print('Dropped \'average current = 0\' rows.')
#print(df_avg_zero.head())

# Find indexes where the current reduces to 0 and drop them (rest steps after charge or discharge)
df_filt = df_avg_zero.drop(df.index[df['current'] == 0].tolist())
df = df.drop(df.index[df['current'] == 0].tolist())
print('Dropped rows that have \'current = 0\' in any row.')
#print(df_filt.head())

df.set_index('test_time', append = True, inplace = True)

df['new_index'] = ''
for i in df_filt.index.values :
    if df.loc[i, 'current'].mean() > 0 :
        df.loc[i, 'new_index'] = 'pos'
    else :
        df.loc[i, 'new_index'] = 'neg'
        
df.reset_index(inplace=True)
df.drop(columns='step_index', inplace=True)
df.set_index(['cell', 'cycle_index', 'new_index', 'date_time'], inplace=True)
df.index.names = ['cell', 'cycle_index', 'step_index', 'date_time']
#df.sort_index(inplace=True)
df.index.sortlevel(level='date_time')

print(df)

#------------------------
# Plotting test

print('--------------------------------------')
print('Plot data')
#df_one_step = df.loc[(1, 1):(1,last_cycle), 'test_time', 'voltage']
df_plot = df.xs(1, level='cell')[['test_time','voltage']]
#df_plot = df_plot[['test_time','voltage']]

df_plot.reset_index(level='date_time', inplace=True)
df_plot_sampled = pd.DataFrame(columns=df_plot.columns, index=df_plot.index)
df_plot.sort_index()
print(len(df_plot.index))

for i in df_plot.index.unique() :
    df_temp = df_plot.loc[i]
    if len(df_temp) > 2000 :
        downsampler = floor(len(df_temp)/1000)
        df_plot_sampled.append(df_temp.iloc[::downsampler])
        print('Downsampled {}'.format(i))
    else :
        print('Left {}'.format(i))
    #df_plot_sampled.append(df_temp.iloc[-1])
    
print(df_plot_sampled)

sys.exit()

df_plot_sampled.set_index('date_time', append=True, inplace=True)
df_plot_sampled.index.sortlevel(level='date_time')

g = sns.relplot(x="test_time", y="voltage", kind="line", data=df_plot_sampled)
g.fig.autofmt_xdate()
plt.show()

sys.exit()