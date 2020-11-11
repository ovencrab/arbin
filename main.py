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
folder_select = 1

# Outputs
save_indexed = 0
save_decimated = 0
save_cycle_data = 1
save_processed = 1
save_cycle_data_converted = 1

# Data processing
user_decimate = 0
row_target = 500
drop_list = ['test_time','charge_cumulative','discharge_cumulative',
            'charge_energy','discharge_energy','ACR','int_resistance','dv/dt']

# Plot config
user_plot_fprofile = 0
user_cell = 1
user_cycle = '2-5' # 0 plots all cycles # '2-5' to plot cycles 2 to 5
user_x = 'test_time'
user_y = 'voltage'
user_y2 = 'current'

user_plot_cycle = 0
user_cyc_x = 'cycle'
user_cyc_y = 'n_cap'
user_cap_param = 'mass'
user_cyc_y2 = 0

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Script ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Select files and call import functions
if folder_select == 0 :
    t_str = 'decimated'
    data_paths = [Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data & Notes/02 Code analysis/Arbin/001 Test data/JE_LtS_rate_B1_12_Channel_12.csv',
                 Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data & Notes/02 Code analysis/Arbin/001 Test data/JE_LtS_rate_B2_13_Channel_13.csv',
                 Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data & Notes/02 Code analysis/Arbin/001 Test data/JE_LtS_rate_B3_14_Channel_14.csv']
    #data_paths = [Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/JE_LtS_rate_B1_12_Channel_12.csv',
    #              Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/JE_LtS_rate_B2_13_Channel_13.csv',
    #              Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/JE_LtS_rate_B3_14_Channel_14.csv']
    data_folder = Path(data_paths[0]).parent
else:
    # Open dialog box to select folder
    Tk().withdraw()  # stops root window from appearing
    data_folder = askdirectory(title="Choose data folder")  # "Open" dialog box and return the selected path
    data_paths = list(Path(data_folder).glob('*.csv'))
    data_folder = Path(data_paths[0]).parent

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

    # Save csv and yaml files
    if save_indexed == 1 :
        tic = time.perf_counter()

        message, success = save.multi(df, data_folder, data_paths, 'indexed', 'indexed')
        cell_info['filtered'] = 1
        save.yml(cell_info, 'indexed', data_folder, info_path)

        toc = time.perf_counter()

        if success == 1 :
            print(f"5 - Saved files to 'indexed' in {toc - tic:0.1f}s")
        else :
            print(message)

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

    # Save decimated data to csv files in */decimated folder
    if save_decimated == 1 :
        tic = time.perf_counter()

        message, success = save.multi(df, data_folder, data_paths, 'decimated', 'decimated')
        cell_info['decimated'] = 1
        save.yml(cell_info, 'decimated', data_folder, info_path)

        toc = time.perf_counter()
        t = f'{toc - tic:0.1f}'

        if success == 1 :
            print('{} - Saved files in {}s'.format(counter+1,t))
        else :
            print(message)


#------------------------
# Capacity calculations
#------------------------

print('--------------------------------------')
print('Calculating capacity and cycle data')
print('--------------------------------------')

tic = time.perf_counter()
# Call function to filter data into capacity per cycle
df_cap, df = filt.cap(df, n_cells)

# Update cell_info with new average cell
cell_info['cell'].insert(0, 0)
cell_info['thickness'].insert(0, filt.f_mean(cell_info['thickness']))
cell_info['mass'].insert(0, filt.f_mean(cell_info['mass']))

toc = time.perf_counter()

print(f"1 - Subtractive capacity and cycle data generated in {toc - tic:0.1f}s")

# Save cycle data to csv files in */output folder
if save_cycle_data == 1 :
    tic = time.perf_counter()
    message, success = save.single(df_cap, data_folder, data_paths, 'output', 'cycle_data')
    toc = time.perf_counter()
    if success == 1 :
        print(f"2 - Saved formatted cycle data to '*/output' in {toc - tic:0.1f}s")
    else :
        print(message)

# Save processed voltage profile data to csv files in */output folder
if save_processed == 1 :
    tic = time.perf_counter()
    df_export = df.drop(columns=drop_list)
    message, success = save.multi_processed(df_export, data_folder, data_paths, 'none', 'processed')
    toc = time.perf_counter()
    if success == 1 :
        print(f"3 - Saved processed voltage profile data to '*/output' in {toc - tic:0.1f}s")
    else :
        print(message)

print('--------------------------------------')
print('Convert capacity data to other formats')
print('--------------------------------------')

tic = time.perf_counter()

# Create multi index in column axis referring to 'raw' capacity
df_cap = pd.concat([df_cap], axis=1, keys=['raw'])
df_cap.sort_index(inplace=True)
df_cap = filt.cap_convert(df_cap, cell_info, 'mAh', ['p_cap', 'n_cap', 'p_cap_std', 'n_cap_std'])

# For each cell in data frame, convert mAh to mAh/g (cell = 0 is the mean)
df_cap_mass = filt.cap_convert(df_cap, cell_info, 'mass', ['p_cap', 'n_cap', 'p_cap_std', 'n_cap_std'])

# For each cell in data frame, convert mAh to mAh/cm3 (cell = 0 is the mean)
df_cap_vol = filt.cap_convert(df_cap, cell_info, 'volume', ['p_cap', 'n_cap', 'p_cap_std', 'n_cap_std'])

# For each cell in data frame, convert mAh to mAh/cm2 (cell = 0 is the mean)
df_cap_areal = filt.cap_convert(df_cap, cell_info, 'areal', ['p_cap', 'n_cap', 'p_cap_std', 'n_cap_std'])

# Concatenate raw, mass and vol cycle capacity dataframes
df_cap = pd.concat([df_cap, df_cap_mass,  df_cap_areal, df_cap_vol], axis=1)

toc = time.perf_counter()

print(f"1 - Converted cycle data to mass and volume format in {toc - tic:0.1f}s")

if save_cycle_data_converted == 1 :
    tic = time.perf_counter()
    message, success = save.single(df_cap, data_folder, data_paths, 'output', 'cycle_data_converted')
    toc = time.perf_counter()
    if success == 1 :
        print(f"2 - Saved formatted cycle data to '*/output' in {toc - tic:0.1f}s")
    else :
        print(message)

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

# Plot cycle data
if user_plot_cycle == 1 :
    tic = time.perf_counter()

    # Checks for the number of cells in the data frame and plots traces
    if len(df_cap.index.get_level_values(0).unique()) == 1 :
        # Dataframe only contains 1 cell
        fig = go.Figure()
        cell_idx = df_cap.index.get_level_values(0).unique().values[0]
        fig = plot_data.cycle_trace(df_cap, fig, cell_idx, user_cap_param, user_cyc_y)
        plot_data.def_format(fig, cell_idx, n_cells)
    else :
        fig = go.Figure()
        for cell_idx in df_cap.index.get_level_values(0).unique() :
            if cell_idx == 0 :
                # skip cell index of 0 as it is the mean
                continue
            else :
                # create trace for all other cell indexes
                fig = plot_data.cycle_trace(df_cap, fig, cell_idx, user_cap_param, user_cyc_y)

        # Plot traces for each cell
        plot_data.def_format(fig, cell_idx, n_cells)

        # Plot trace of mean
        fig_avg = go.Figure()
        cell_idx = 0
        fig_avg = plot_data.cycle_trace(df_cap.xs(0, level='cell', drop_level=False), fig_avg, cell_idx, user_cap_param, user_cyc_y)
        plot_data.def_format(fig_avg, cell_idx, n_cells)

    toc = time.perf_counter()
    print(f"Plots generated in {toc - tic:0.1f}s")

#Debug
#idx = pd.IndexSlice
#df_cap.loc[idx[1, 1], idx['raw', 'p_curr']]

