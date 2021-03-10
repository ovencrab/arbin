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
import filt
import save

### Indexing ###
idx=pd.IndexSlice

### File processing ###

raw_cols = ['Test_Time(s)','Cycle_Index','Step_Index','Current(A)',
            'Voltage(V)','Charge_Capacity(Ah)','Discharge_Capacity(Ah)']
col_rename = ['time','cycle','step','I','E','Qp','Qn']

### Options ###

xlsx = True # Takes longer to read than csv files
cell_rename = True
cv_cut = 1.1 # (minimum ratio between CC current vs CV current)
avg_calc = True
avg_name = 'JE_210128_WP0_form'
param_output_cap = ['mAh','mass','areal','volume'] # mAh, mass, areal, volume

save_indv = False
save_average = True

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Script ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

print('--------------------- Import files ---------------------')

c=0
# Open dialog to select folder call import functions
root = Tk()
root.attributes("-topmost", True)
root.withdraw()  # stops root window from appearing
raw_folder = askdirectory(title="Choose data folder")  # "Open" dialog box and return the selected path
data_paths = list(Path(raw_folder).glob('*.csv'))
raw_folder = Path(data_paths[0]).parent
output_folder = raw_folder.joinpath('output')

# Identify cell_info csv and remove from data file list
for index, fpath in enumerate(data_paths):
    if fpath.stem == 'cell_info':
        info_file = fpath
        info_index = index

# Remove cell_info file path from data_paths and read cell_info into df
if 'info_index' in locals():
    del data_paths[info_index]
    cell_info = pd.read_csv(info_file)
    missing_info = False
else:
    cell_info = pd.DataFrame(columns=['name'])
    param_output_cap = ['mAh']
    missing_info = True
    print("{} - Disabled capacity conversions due to missing 'cell_info.csv' file".format(c))
    c=c+1
    for i, fpath in enumerate(data_paths):
        cell_info.loc[i] = data_paths[i].stem

if xlsx:
    data_paths = list(Path(raw_folder).glob('*.xlsx'))

print('{} - Imported {} data paths and {} rows of cell information'.format(c,len(data_paths),len(cell_info)))

print('--------------------- Cell information -----------------')

# Read cell_info.csv into dataframe
print(cell_info)

print('--------------------- Information checks ---------------')

c=0
if not missing_info:
    # Check cell_info for empty name data and add from filename if found
    empty_idx = cell_info[ (cell_info['name'].isnull()) | (cell_info['name']=='') ].index
    if empty_idx > 0:
        for cell in empty_idx:
            cell_info['name'][cell] = data_paths[cell].stem
            print('{} - Name added for cell index {}'.format(c,cell))
            c = c+1

    # Check columns exist for data conversion
    columns = ['mass','thickness','diameter']
    if not 'mass' in cell_info.columns:
        param_output_cap.remove('mass')
        columns.remove('mass')
        print('{} - Missing mass column - mass conversion disabled'.format(c))
        c=c+1
    if not 'thickness' in cell_info.columns:
        param_output_cap.remove('volume')
        columns.remove('thickness')
        print('{} - Missing thickness column - volume conversion disabled'.format(c))
        c=c+1
    if not 'diameter' in cell_info.columns:
        param_output_cap.remove(['areal','volume'])
        columns.remove('diameter')
        print('{} - Missing diameter column - areal and volume conversion disabled'.format(c))
        c=c+1

    # Check rows in cell_info contain data allowing conversions. If not, remove request for conversion.
    for column in columns:
        empty_idx = cell_info[ (cell_info[column].isnull()) | (cell_info[column]=='') ].index
        if len(empty_idx) > 0:
            if column == 'mass':
                param_output_cap.remove('mass')
                print('{} - Missing mass entry - mass conversion disabled'.format(c))
                c=c+1
            elif column == 'thickness':
                param_output_cap.remove('volume')
                print('{} - Missing thickness entry - volume conversion disabled'.format(c))
                c=c+1
            elif column == 'diameter':
                param_output_cap.remove('areal')
                param_output_cap.remove('volume')
                print('{} - Missing diameter entry - areal and volume conversion disabled'.format(c))
                c=c+1

if c == 0:
    print('{} - Cell information is good'.format(c))

# --------------------------- Data filtering ---------------------------
print('--------------------- Data filtering -------------------')

lst_df = []
lst_df_cap = []
c = 0
for fpath in data_paths:
    # Read raw data into dataframe, rename columns and set cycle and step as index
    if xlsx:
        xls = pd.ExcelFile(fpath,engine='openpyxl')
        data_sheet = [i for i, sht_name in enumerate(xls.sheet_names) if 'Channel' in sht_name]
        if len(data_sheet) == 1:
            data_sheet = data_sheet[0]
            df = xls.parse(data_sheet,usecols=raw_cols)[raw_cols]
        else:
            print("Multiple 'Channel' data sheets in xlsx file, check xlsx file:")
            sys.exit("{}".format(fpath))
    else:
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
    lst_df_cap.append(df_cap)

# Calculate average data
if avg_calc:
    df_cap_temp = pd.concat(lst_df_cap)
    df_cap_avg = df_cap_temp.groupby(['cycle', 'step','step_type'])['I','Qp','Qn'].mean()
    df_cap_std = df_cap_temp.groupby(['cycle', 'step','step_type'])['Qp','Qn'].std()
    df_cap_std.columns = ['Qp_std', 'Qn_std']
    df_cap_avg = pd.concat([df_cap_avg, df_cap_std], axis=1)

    # Create average cell_info
    d = {'name': avg_name}
    new_row = pd.Series(data=d, index=['name'])
    new_df = cell_info.mean().to_frame()
    cell_info_avg = pd.concat([new_row,new_df]).T

    print('--------------------- Averaged data --------------------')
    print(cell_info_avg)
    print(df_cap_avg.groupby(['cycle'])['Qp','Qn','Qp_std','Qn_std'].sum())

# --------------------------- File output ---------------------------
print('--------------------- File output ----------------------')

c=0
# Create output folder
if not output_folder.is_dir() :
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
        print("{} - Created output folder".format(c))
        c=c+1
    except:
        print("{} - ERROR: Couldn't create output folder".format(c))
        c=c+1
else:
    print("{} - Output folder already exists, trying to save files:".format(c))
    c=c+1

# --------------------------- Averaged data ---------------------------
if save_average:
    print('--------------------- Averaged data -------------------')

    c=0
    # Save averaged data. One file per param.
    df_param_list = []
    for p,param in enumerate(param_output_cap):
        df_conv = filt.converter(df_cap_avg,param,cell_info_avg.loc[0],'I')

        if save_indv & save_average:
            c = save.single(df_conv, output_folder, c,
                            'avg_{}_{}.csv'.format(param,cell_info_avg.loc[0]['name']),
                            "{} - Saved {} conversion of '{}'".format(c,param,cell_info_avg.loc[0]['name']),
                            "{} - Error: Could not save '{}'".format(c,cell_info_avg.loc[0]['name']))

        # Create list of param converted dataframes for concatenation. Append param to column names.
        if p == 0:
            df_param = df_conv.copy()
            df_param.columns = ['{}{}'.format(col, '' if col in 'I' else '_{}'.format(param)) for col in df_param.columns]
        else:
            df_param = df_conv.copy().drop('I',axis=1).add_suffix('_'+param)

        df_param_list.append(df_param)

    # Output concatenated df of data frames converted by param and per cycle data. If only one param, only output per cycle data.
    if len(param_output_cap) > 1:
        df_param = pd.concat(df_param_list, axis=1)

        c = save.single(df_param, output_folder, c,
                        'avg_params_{}.csv'.format(cell_info_avg.loc[0]['name']),
                        "{} - Saved combined conversion of '{}'".format(c,cell_info_avg.loc[0]['name']),
                        "{} - Error: Could not save combined conversion of '{}'".format(c,cell_info_avg.loc[0]['name']))

        c = save.single(df_param.drop('I',axis=1).groupby(['cycle']).sum(), output_folder, c,
                        'avg_params_cycle_{}.csv'.format(cell_info_avg.loc[0]['name']),
                        "{} - Saved per cycle combined conversion of '{}'".format(c,cell_info_avg.loc[0]['name']),
                        "{} - Error: Could not save per cycle combined conversion of '{}'".format(c,cell_info_avg.loc[0]['name']))
    else:
        c = save.single(df_param.drop('I',axis=1).groupby(['cycle']).sum(), output_folder, c,
                        'avg_params_cycle_{}.csv'.format(cell_info_avg.loc[0]['name']),
                        "{} - Saved per cycle {} conversion of '{}'".format(c,param,cell_info_avg.loc[0]['name']),
                        "{} - Error: Could not save per cycle {} conversion of '{}'".format(c,param,cell_info_avg.loc[0]['name']))

# --------------------------- 'per cell' data ---------------------------
if save_average:
    print("--------------------- 'per cell' data -------------------")

c=0
# Save capacity conversions - converts all mAh columns to divider type (i.e. 'mass')
for i, df_cap in enumerate(lst_df_cap):
    df_param_list = []
    for p,param in enumerate(param_output_cap):
        df_conv = filt.converter(df_cap,param,cell_info.loc[i],'I')

        if save_indv:
            c = save.single(df_conv, output_folder, c,
                            '{}_{}.csv'.format(param,cell_info.loc[i]['name']),
                            "{} - Saved {} conversion of '{}'".format(c,param,cell_info['name'][i]),
                            "{} - Error: Could not save '{}'".format(c,cell_info['name'][i]))

        # Create list of param converted dataframes per cell for concatenation. Append param to column names.
        if p == 0:
            df_param = df_conv.copy()
            df_param.columns = ['{}{}'.format(col, '' if col in 'I' else '_{}'.format(param)) for col in df_param.columns]
        else:
            df_param = df_conv.copy().drop('I',axis=1).add_suffix('_'+param)

        df_param_list.append(df_param)

    # Save combined param data to single file
    if len(param_output_cap) > 1:
        df_param = pd.concat(df_param_list, axis=1)

        c = save.single(df_param, output_folder, c,
                        'params_{}.csv'.format(cell_info.loc[i]['name']),
                        "{} - Saved combined conversion of '{}'".format(c,cell_info['name'][i]),
                        "{} - Error: Could not save combined conversion of '{}'".format(c,cell_info['name'][i]))

        c = save.single(df_param.drop('I',axis=1).groupby(['cycle']).sum(), output_folder, c,
                        'params_cycle_{}.csv'.format(cell_info.loc[i]['name']),
                        "{} - Saved per cycle combined conversion of '{}'".format(c,cell_info['name'][i]),
                        "{} - Error: Could not save per cycle combined conversion of '{}'".format(c,cell_info['name'][i]))
    else:
        c = save.single(df_param.drop('I',axis=1).groupby(['cycle']).sum(), output_folder, c,
                        'params_cycle_{}.csv'.format(cell_info.loc[i]['name']),
                        "{} - Saved per cycle combined conversion of '{}'".format(c,cell_info['name'][i]),
                        "{} - Error: Could not save per cycle combined conversion of '{}'".format(c,cell_info['name'][i]))

### List of useful variables ###
# lst_df        -- full voltage profile data with capacity per cycle
# lst_df_cap    -- capacity per step for each individual file
# df_cap_avg    -- capacity per step with mean and std calculated

### List of useful filters ###
# df_cap.loc[idx[:, :, ['pos']],] -- selects positive constant current capacity steps
# df_cap.loc[idx[:, :, ['posCV']],] -- selects positive constant voltage capacity steps
# df_cap_avg.groupby(['cycle'])['Qp','Qn','Qp_std','Qn_std'].sum() -- full capacity per cycle

