### Import packages ###
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilenames
import numpy as np
import pandas as pd
import re

### Temp packages ###
from math import pi

### Import debugging ###
import sys
import time

### Import functions ###
import load
import save
import filt
import plot_data

### Indexing ###
ixs=pd.IndexSlice

### File processing ###

raw_cols = ['Test_Time(s)','Cycle_Index','Step_Index','Current(A)',
            'Voltage(V)','Charge_Capacity(Ah)','Discharge_Capacity(Ah)']
col_rename = ['time','cycle','step','I','E','Qp','Qn']

### Options ###

cv_cut = 1.1 #(minimum ratio between CC current vs CV current)
calc_avg = True
param_volt_output = [True, True, True, True] # mAh, mass, areal, volume
param_volt_plot = ['mAh']
param_cap_output = [True, True, True, True] # mAh, mass, areal, volume
param_cap_plot = ['mAh']

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Script ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

print('--------------------- Import files ---------------------')

# Open dialog to select folder call import functions
root = Tk()
root.attributes("-topmost", True)
root.withdraw()  # stops root window from appearing
data_folder = askdirectory(title="Choose data folder")  # "Open" dialog box and return the selected path
data_paths = list(Path(data_folder).glob('*.csv'))
data_folder = Path(data_paths[0]).parent

# Identify cell_info csv and remove from data file list
for index, fpath in enumerate(data_paths):
    if fpath.stem == 'cell_info':
        info_file = fpath
        info_index = index

del data_paths[info_index]

# Read cell_info.csv into dataframe
cell_info = pd.read_csv(info_file)
print(cell_info)

# --------------------------- Data filtering ---------------------------
print('--------------------- Data filtering ---------------------')

lst_df = []
lst_df_cap_tmp = []
c = 0
for fpath in data_paths:
    # Read raw data into dataframe, rename columns and set cycle and step as index
    df = pd.read_csv(fpath,usecols=raw_cols)[raw_cols]
    df.columns = col_rename
    df.set_index(['cycle','step'],inplace=True)

    # Convert Ah to mAh
    df.Qp = df.Qp * 1000
    df.Qn = df.Qn * 1000

    # Print data
    print('{} - Returned dataframe: {}'.format(c, df.shape))
    c = c+1

    # List of df multindex
    df_idx = df.index.unique()

    # Find last capacity value in each step
    qp_filt = df.groupby(['cycle', 'step'])['Qp'].first()
    qn_filt = df.groupby(['cycle', 'step'])['Qn'].first()

    # Subtract step(n-1) capacity from step(n) capacity starting with last step
    for nidx, midx in reversed(list(enumerate(df_idx))):
        df.loc[df_idx[nidx]]['Qp'] = df.loc[df_idx[nidx]]['Qp'] - list(qp_filt)[nidx]
        df.loc[df_idx[nidx]]['Qn'] = df.loc[df_idx[nidx]]['Qn'] - list(qn_filt)[nidx]

    df_cap = df.groupby(['cycle', 'step'])['I','Qp','Qn'].last()

    # Labelling of constant current steps
    df.loc[df_cap.index[df_cap['I'] == 0].tolist(), 'step_type'] = 'rest'
    df.loc[df_cap.index[df_cap['Qp'] > 0].tolist(), 'step_type'] = 'pos'
    df.loc[df_cap.index[df_cap['Qn'] > 0].tolist(), 'step_type'] = 'neg'

    # Labelling of constant voltage steps - positive current
    cap_filt = df_cap[df_cap['Qp'] > 0].index
    first = df.loc[cap_filt].groupby(['cycle', 'step'])['I'].first()
    last = df.loc[cap_filt].groupby(['cycle', 'step'])['I'].last()
    cv_filt = first/last
    if len(cv_filt.index[cv_filt > cv_cut].tolist()) != 0:
        df.loc[cv_filt.index[cv_filt > cv_cut].tolist(), 'step_type'] = 'posCV'

    # Labelling of constant voltage steps - negative current
    cap_filt = df_cap[df_cap['Qn'] > 0].index
    first = df.loc[cap_filt].groupby(['cycle', 'step'])['I'].first()
    last = df.loc[cap_filt].groupby(['cycle', 'step'])['I'].last()
    cv_filt = first/last
    if len(cv_filt.index[cv_filt > cv_cut].tolist()) != 0:
        df.loc[cv_filt.index[cv_filt > cv_cut].tolist(), 'step_type'] = 'negCV'

    # Make step_type an index for df
    df.set_index(['step_type'], inplace=True, append=True)

    # Update df_cap with new step_type index
    df_cap = df.groupby(['cycle', 'step','step_type'])['I','Qp','Qn'].last()
    #print(df_cap.tail())

    # Create data_frame of total capacity per cycle
    #df_cap_total = df_cap.groupby(['cycle'])['Qp','Qn'].sum()
    #print(df_cap_total.head())

    lst_df.append(df)
    lst_df_cap_tmp.append(df_cap)

# Organises dfs into list of lists based on set number in cell_info.csv
n_sets = len(cell_info['set'].unique())
lsts_df_cap = [[] for i in range(n_sets)]
level = 0
prev_cell_set = cell_info['set'][0]
for idx in range(len(cell_info)):
    cell_set = cell_info['set'][idx]
    if cell_set != prev_cell_set:
        level = level + 1
    lsts_df_cap[level].append(lst_df_cap_tmp[idx])
    prev_cell_set = cell_info['set'][idx]

# Calculates mean and std of cells in the same set and reduces list of lists to flat list
lst_df_cap = []
avg_idx = []
for idx, lst in enumerate(lsts_df_cap):
    if len(lst) > 1:
        df_temp = pd.concat(lsts_df_cap[idx])
        df_mean = df_temp.groupby(['cycle', 'step','step_type'])['I','Qp','Qn'].mean()
        df_std = df_temp.groupby(['cycle', 'step','step_type'])['Qp','Qn'].std()
        df_std.columns = ['Qp_std','Qn_std']
        df_avg = pd.concat([df_mean, df_std], axis=1)
        lst_df_cap.append(df_avg)
        avg_idx.append(True)
    else:
        lsts_df_cap[idx] = lsts_df_cap[idx][0].reindex(columns = ['I','Qp','Qn','Qp_std','Qn_std'])
        lst_df_cap.append(lsts_df_cap[idx])
        avg_idx.append(False)

print(lst_df_cap)

### List of useful variables ###
# lst_df            -- full voltage profile data with capacity per cycle
# lst_df_cap_temp   -- capacity per step for each individual file
# lst_df_cap        -- capacity per step with mean and std calculated