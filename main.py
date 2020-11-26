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

### Indexing ###
idx=pd.IndexSlice

### Options ###

# Folder or file import
folder_select = 1

# Outputs
save_indexed = 0
save_decimated = 0
#save_cycle_data = 1
save_volt_indv = [1,['mass']]
save_cyc_combined = 1
save_cyc_indv = [1,['mass']]
param_list = ['mAh','mass','volume','areal']

# Data processing
user_decimate = 0
row_target = 500
drop_list = ['test_time','charge_cumulative','discharge_cumulative',
            'charge_energy','discharge_energy','ACR','int_resistance','dv/dt']

# Plot config
user_plot_fprofile = 1
user_cell = 1
user_cycle = '1-2' # 0 plots all cycles # '2-5' to plot cycles 2 to 5
user_x = 'test_time'
user_y = 'voltage'
user_y2 = 'current'

user_plot_cycle = 0
user_cyc_x = 'cycle'
user_cyc_y = 'p_cap'
user_cap_param = 'mass'
user_cyc_y2 = 0

# Step list
step_list = [(1,21,5),
             (1,22,5)]

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
    root = Tk()
    root.attributes("-topmost", True)
    root.withdraw()  # stops root window from appearing
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
df_raw, n_cells, raw = load.csv(data_paths, cell_info)
toc = time.perf_counter()
print(f"Imported files in {toc - tic:0.1f}s")

# Print data
print('--------------------------------------')
print("Returned data:")
print('--------------------------------------')
[print(key, ': ', value) for key, value in cell_info.items()]
print('Dataframe size: {}'.format(df_raw.size))

#------------------------
# Data filtering
#------------------------

if raw :
    print('--------------------------------------')
    print('Data filtering')
    print('--------------------------------------')

    tic = time.perf_counter()
    # Call index function on raw dataframe
    df_indexed = filt.index(df_raw, step_list, 'yes')
    toc = time.perf_counter()
    print(f"4 - Created new index in {toc - tic:0.1f}s")

    # Save csv and yaml files
    if save_indexed == 1 :
        tic = time.perf_counter()

        message, success = save.multi(df_indexed, data_folder, data_paths, cell_info, 'indexed', 'normal', ['cell','date_time'], 'indexed')
        cell_info['filtered'] = 1
        save.yml(cell_info, 'indexed', data_folder, info_path)

        toc = time.perf_counter()

        if success == 1 :
            print(f"5 - Saved files to 'indexed' in {toc - tic:0.1f}s")
        else :
            print(message)

#------------------------
# Capacity calculations
#------------------------

print('--------------------------------------')
print('Calculating capacity and cycle data')
print('--------------------------------------')

tic = time.perf_counter()
# Call function to filter data into capacity per step index
df_cyc, df_processed = filt.cap(df_indexed, n_cells)

# Fill NaN and combined columns
df_cyc.fillna(0,inplace=True)
df_cyc2 = pd.DataFrame(columns=['current', 'cap', 'cap_std'])
df_cyc2['current'] = df_cyc['p_curr'] + df_cyc['n_curr']
df_cyc2['cap'] = df_cyc['p_cap'] + df_cyc['n_cap']
df_cyc2['cap_std'] = df_cyc['p_cap_std'] + df_cyc['n_cap_std']
df_cyc = df_cyc2

# Create pos and neg index column
df_cyc.loc[df_cyc.index[df_cyc['current']<0].tolist(), 'new_index'] = 'neg'
df_cyc.loc[df_cyc.index[df_cyc['current']>0].tolist(), 'new_index'] = 'pos'
df_cyc.set_index(['new_index'], inplace=True, append=True)
df_cyc.index.names = ['cell', 'step_index', 'step_type']

# Update cell_info with new average cell
cell_info['cell'].insert(0, 0)
cell_info['thickness'].insert(0, filt.f_mean(cell_info['thickness']))
cell_info['mass'].insert(0, filt.f_mean(cell_info['mass']))

toc = time.perf_counter()

print(f"1 - Subtractive capacity and cycle data generated in {toc - tic:0.1f}s")

# Save cycle data to csv files in */output folder
#if save_cycle_data == 1 :
#    tic = time.perf_counter()
#    message, success = save.single(df_cap, data_folder, data_paths, cell_info, 'output', 'cycle_data')
#    toc = time.perf_counter()
#    if success == 1 :
#        print(f"2 - Saved formatted cycle data to '*/output' in {toc - tic:0.1f}s")
#    else :
#        print(message)

print('--------------------------------------')
print('Convert voltage profiles to alternative formats')
print('--------------------------------------')

tic = time.perf_counter()

# Drop unused columns and create multi index in column axis referring to 'raw' capacity
df_volt = df_processed.drop(columns=drop_list)
df_volt.set_index(['date_time'], inplace=True, append=True)
df_volt.sort_index(inplace=True)

# Create list of dataframes of converted voltage vs capacity data and concat with raw dataframe
volt_cnvrt_list = []
for i, param in enumerate(param_list):
  data_cnvrt = filt.param_convert_volt(df_volt, cell_info, param, ['p_cap', 'n_cap'])
  volt_cnvrt_list.append(data_cnvrt)

df_volt_cnvrt = pd.concat(volt_cnvrt_list, axis=1)

# Create multiindex for raw data and universal columns (voltage, current)
universal_cols = ['step_time','voltage','current']
univ_volt = df_volt.loc[idx[:, :, :, :], universal_cols]
raw_volt = df_volt.loc[idx[:, :, :, :], ['p_cap','n_cap']]
df_volt = pd.concat([univ_volt, raw_volt], axis=1, keys=['univ','raw'])

# Concatenate universal columns and converted capacities
df_volt = pd.concat([df_volt, df_volt_cnvrt], axis=1)

toc = time.perf_counter()

print(f"1 - Converted voltage data to mAh, mass, areal and volume format in {toc - tic:0.1f}s")

# Save processed voltage profile data to csv files in */output folder
if save_volt_indv[0] == 1 :
    tic = time.perf_counter()

    for param in save_volt_indv[1]:
        message, success = save.multi(df_volt.loc[:, idx[['univ',param],:]], data_folder, data_paths, cell_info, 'output', 'voltage', ['cell','date_time'], 'voltage_'+param)

    toc = time.perf_counter()
    if success == 1 :
        print(f"2 - Saved converted voltage profile data to '*/output' in {toc - tic:0.1f}s")
    else :
        print(message)

print('--------------------------------------')
print('Convert cycle data to other formats')
print('--------------------------------------')

tic = time.perf_counter()
save_count = 1

# Create list of dataframes of converted cycle vs capacity data and concat into dataframe
cyc_cnvrt_list = []
for i, param in enumerate(param_list):
  data_cnvrt = filt.param_convert_cap(df_cyc, cell_info, param, ['cap','cap_std'])
  cyc_cnvrt_list.append(data_cnvrt)

# Set column index for original raw data
univ_cyc = df_cyc.loc[idx[:, :, :], 'current']
raw_cyc = df_cyc.loc[idx[:, :, :], ['cap','cap_std']]
df_cyc = pd.concat([univ_cyc, raw_cyc], axis=1, keys=['univ','raw'])

# Concatenate raw data with param data
df_cyc = pd.concat([df_cyc,pd.concat(cyc_cnvrt_list, axis=1)], axis=1)

# Reformat dataframe into suitable format for csv export
df_cyc_reformat = filt.reformat(df_cyc)

#df_cap_reformat.loc[idx[:],idx[:,param,:]]

toc = time.perf_counter()

print(f"{save_count} - Converted cycle data to mAh, mass, areal and volume format in {toc - tic:0.1f}s")
save_count = save_count + 1

if save_cyc_combined == 1 :
    tic = time.perf_counter()
    message, success = save.param_filter(df_cyc_reformat, data_folder, data_paths, cell_info, 'output', param_list)
    toc = time.perf_counter()
    if success == 1 :
        print(f"{save_count} - Saved formatted cycle data to '*/output' in {toc - tic:0.1f}s")
        save_count = save_count + 1
    else :
        print(message)

# Save processed voltage profile data to csv files in */output folder
if save_cyc_indv[0] == 1 :
    tic = time.perf_counter()

    for param in save_cyc_indv[1]:
        message, success = save.multi(df_cyc_reformat.loc[:, idx[:,['univ',param],:]], data_folder, data_paths, cell_info, 'output', 'reformat', ['cell','date_time'], 'cyc_'+param)

    toc = time.perf_counter()
    if success == 1 :
        print(f"{save_count} - Saved converted cycle data to '*/output' in {toc - tic:0.1f}s")
        save_count = save_count + 1
    else :
        print(message)

sys.exit()

#------------------------
# Plotting test
#------------------------

print('--------------------------------------')
print('Plot data')
print('--------------------------------------')

# Plot voltage/current profiles
if user_plot_fprofile == 1 :
    tic = time.perf_counter()
    fig = plot_data.fprofile(df_processed, user_cell, user_cycle, user_x, user_y, user_y2)
    fig.show()
    toc = time.perf_counter()
    print(f"Plot generated in {toc - tic:0.1f}s")

# Plot cycle data
if user_plot_cycle == 1 :
    tic = time.perf_counter()

    # Checks for the number of cells in the data frame and plots traces
    if len(df_cyc.index.get_level_values(0).unique()) == 1 :
        # Dataframe only contains 1 cell
        fig = go.Figure()
        cell_idx = df_cyc.index.get_level_values(0).unique().values[0]
        fig = plot_data.cycle_trace(df_cyc, fig, cell_idx, user_cap_param, user_cyc_y)
        plot_data.def_format(fig, cell_idx, n_cells)
    else :
        fig = go.Figure()
        for cell_idx in df_cyc.index.get_level_values(0).unique() :
            if cell_idx == 0 :
                # skip cell index of 0 as it is the mean
                continue
            else :
                # create trace for all other cell indexes
                fig = plot_data.cycle_trace(df_cyc, fig, cell_idx, user_cap_param, user_cyc_y)

        # Plot traces for each cell
        plot_data.def_format(fig, cell_idx, n_cells)

        # Plot trace of mean
        fig_avg = go.Figure()
        cell_idx = 0
        fig_avg = plot_data.cycle_trace(df_cyc.xs(0, level='cell', drop_level=False), fig_avg, cell_idx, user_cap_param, user_cyc_y)
        plot_data.def_format(fig_avg, cell_idx, n_cells)

    toc = time.perf_counter()
    print(f"Plots generated in {toc - tic:0.1f}s")

#Debug
#idx = pd.IndexSlice
#df_cyc.loc[idx[1, 1], idx['raw', 'p_curr']]
#df_cyc_reformat.loc[:, idx[:,'mAh', ('p_cap','p_cap_std')]]

