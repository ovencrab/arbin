### Import packages ###
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilenames
import numpy as np
import pandas as pd
import yaml
import re

### Temp packages ###
from math import pi

### Import debugging ###
import sys
import time

import plotly.graph_objects as go
from plotly.subplots import make_subplots

### Import functions ###
import load
import save
import filt
import plot_data

### Options ###

# Folder or file import
folder_select = 0

# Outputs
save_indexed = 0
save_decimated = 0

# Data processing
user_decimate = 0
row_target = 500

# Plot config
user_plot_fprofile = 0
user_cell = 1
user_cycle = '2-5' # 0 plots all cycles
user_x = 'test_time'
user_y = 'voltage'
user_y2 = 'current'

user_plot_cycle = 1
user_cyc_x = 'cycle'
user_cyc_y = 'n_cap'
user_cap_type = 'mass'
user_cyc_y2 = 0

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Script ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Select files and call import functions
if folder_select == 0 :

    # # Open dialog box to select files
    # Tk().withdraw()
    # filez = askopenfilenames(title='Choose a file', filetypes=(('.csv files', '*.csv'),))

    # # Create list of files and extract folder path from first file path
    # filez = list(filez)
    # data_paths = [Path(data_path) for data_path in filez]
    # data_folder = Path(data_paths[0]).parent

    t_str = 'decimated'
    data_paths = [Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/{}/JE_LtS_rate_B1_12_Channel_12_{}_1.csv'.format(t_str, t_str),
                 Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/{}/JE_LtS_rate_B2_13_Channel_13_{}_2.csv'.format(t_str, t_str),
                 Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/{}/JE_LtS_rate_B3_14_Channel_14_{}_3.csv'.format(t_str, t_str)]
    # data_paths = [Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/JE_LtS_rate_B1_12_Channel_12.csv',
    #              Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/JE_LtS_rate_B2_13_Channel_13.csv',
    #              Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/JE_LtS_rate_B3_14_Channel_14.csv']
    data_folder = Path(data_paths[0]).parent
else:
    # Open dialog box to select folder
    Tk().withdraw()  # stops root window from appearing
    data_folder = askdirectory(title="Choose data folder")  # "Open" dialog box and return the selected path
    data_paths = list(Path(data_folder).glob('*.csv'))

# Finds the .yaml file in data_folder (or the parent directory) and
# creates a dictionary from the information
try :
    cell_info, info_path = load.yml(data_folder)
except :
    try :
        cell_info, info_path = load.yml(data_folder.parent)
    except :
        raise Exception("Can't find *.yaml information file")

# Load csv data
tic = time.perf_counter()
df, n_cells, raw = load.csv(data_paths, cell_info)
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
#------------------------

if raw :
    print('--------------------------------------')
    print('Data filtering')
    print('--------------------------------------')

    tic = time.perf_counter()
    # Call index function on raw dataframe
    df = filt.index(df)
    toc = time.perf_counter()
    print(f"4 - Created new index in {toc - tic:0.1f}s")

    tic = time.perf_counter()
    # Save csv and yaml files
    if save_indexed == 1 :
        save.multi(df, 'indexed', data_folder, data_paths)
        cell_info['filtered'] = 1
        save.yml(cell_info, 'indexed', data_folder, info_path)
    toc = time.perf_counter()
    print(f"5 - Saved files to 'indexed' in {toc - tic:0.1f}s")

#------------------------
# Downsampling
#------------------------

if user_decimate == 1 :
    print('--------------------------------------')
    print('Decimating data')
    print('--------------------------------------')

    tic = time.perf_counter()
    # Call decimate function on dataframe
    df_decimate, counter = filt.decimate(df, row_target)
    toc = time.perf_counter()
    t = f'{toc - tic:0.1f}'
    print('{} - Reduced number of rows from {} to {} in {}s'.format(counter, df.shape[0], df_decimate.shape[0],t))
    df = df_decimate

    tic = time.perf_counter()
    # Save decimated data to csv files in */decimated folder
    if save_decimated == 1 :
        save.multi(df, 'decimated', data_folder, data_paths)
        cell_info['decimated'] = 1
        save.yml(cell_info, 'decimated', data_folder, info_path)
    toc = time.perf_counter()
    t = f'{toc - tic:0.1f}'
    print('{} - Saved files in {}s'.format(counter+1,t))

#------------------------
# Capacity calculations
#------------------------

print('--------------------------------------')
print('Cycle data')
print('--------------------------------------')

tic = time.perf_counter()
# Call function to filter data into capacity per cycle
df_cap = filt.cap(df, n_cells)
toc = time.perf_counter()
print(f"Cycle data generated in {toc - tic:0.1f}s")

#------------------------
# Plotting test
#------------------------

print('--------------------------------------')
print('Plot data')
print('--------------------------------------')

# Plot voltage/current profiles
if user_plot_fprofile == 1 :
    tic = time.perf_counter()
    fig = plot_data.fprofile(df, user_cell, user_cycle, user_x, user_y, user_y2)
    fig.show()
    toc = time.perf_counter()
    print(f"Plot generated in {toc - tic:0.1f}s")

# Convert raw capacity to mAh/g
df_cap_mass = df_cap.copy()

for cell in df_cap_mass.index.get_level_values(0).unique().values :
    data = df_cap_mass.xs(cell, level=0, axis=0, drop_level=False)
    if cell == 0 :
        df_cap_mass.update((data*1000)/(filt.f_mean(cell_info['mass'])/1000))
    else :
        df_cap_mass.update((data*1000)/(cell_info['mass'][cell-1]/1000))

df_cap_mass.columns.set_levels(['mass'],level=0,inplace=True)

df_cap_vol = df_cap.copy()

# For each cell in data frame, convert Ah to mAh/g (cell = 0 is the mean)
for cell in df_cap_vol.index.get_level_values(0).unique().values :
    data = df_cap_vol.xs(cell, level=0, axis=0, drop_level=False)
    if cell == 0 :
        volume = pi * ((cell_info['diameter'] / 20) ** 2) * filt.f_mean(cell_info['thickness']) * (10 ** -4)
        df_cap_vol.update((data*1000)/volume)
    else :
        volume = pi * ((cell_info['diameter'] / 20) ** 2) * cell_info['thickness'][cell-1] * (10 ** -4)
        df_cap_vol.update((data*1000)/volume)

# Rename raw column index to mass
df_cap_vol.columns.set_levels(['vol'],level=0,inplace=True)

df_cap = pd.concat([df_cap, df_cap_mass, df_cap_vol], axis=1)

# Plot cycle data
if user_plot_cycle == 1 :
    tic = time.perf_counter()

    # Checks for the number of cells in the data frame and plots traces
    if len(df_cap.index.get_level_values(0).unique()) == 1 :
        # Dataframe only contains 1 cell
        fig = go.Figure()
        n = df_cap.index.get_level_values(0).unique().values[0]
        fig = plot_data.cycle_trace(df_cap, fig, n, user_cap_type, user_cyc_y)
        plot_data.def_format(fig, n, n_cells)
    else :
        fig = go.Figure()
        for n in df_cap.index.get_level_values(0).unique() :
            if n == 0 :
                # skip cell index of 0 as it is the mean
                continue
            else :
                # create trace for all other cell indexes
                fig = plot_data.cycle_trace(df_cap, fig, n, user_cap_type, user_cyc_y)

        # Plot traces for each cell
        plot_data.def_format(fig, n, n_cells)

        # Plot trace of mean
        fig_avg = go.Figure()
        n = 0
        fig_avg = plot_data.cycle_trace(df_cap.xs(0, level='cell', drop_level=False), fig_avg, n, user_cap_type, user_cyc_y)
        plot_data.def_format(fig_avg, n, n_cells)

    toc = time.perf_counter()
    print(f"Plot generated in {toc - tic:0.1f}s")

