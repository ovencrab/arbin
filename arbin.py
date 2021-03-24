### Import packages ###
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilenames
import numpy as np
import pandas as pd
import natsort
import re

### Temp packages ###
from math import pi

### Import debugging ###
import os
import sys
import time

# ### Manual run ###
# manual_run = True

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Functions ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def sort_paths(path_lst,raw_dir):
    """Sorts a list of pathlib paths based on filename

    Arguments:
        path_lst {list} -- list of pathlib paths

    Returns:
        The sorted list of pathlib paths
    """
    path_lst2=[]
    path_lst3=[]
    path_lst4=[]

    for i in path_lst:
        path_lst2.append(i.name)

    path_lst3 = natsort.natsorted(path_lst2, reverse=False)

    for i in path_lst3:
        path_lst4.append(Path(raw_dir, i))

    path_lst = path_lst4

    return path_lst


def check_paths(c,cell_info):
    """Checks 'cell_info.csv' for filepaths and checks for errors

    Arguments:
        cell_info {df} -- df of cell information

    Returns:
        data_paths {list} -- list of data filepaths
    """

    if not 'data_paths' in cell_info.columns:
        raise Exception("Error: 'text_paths' option is enabled without any data filepaths in 'cell_info.csv'")

    # Check for missing data filepaths in data_paths column
    empty_idx = cell_info[(cell_info['data_paths'].isnull())].index
    if len(empty_idx) > 0:
        print('{} - Missing {} of {} data paths in cell_info'.format(c,len(empty_idx),len(cell_info)))
        cell_info.drop(empty_idx, inplace=True)
        c=c+1

    # Check filepaths exist and add to data_paths if True
    path_exists_list=[]
    data_paths =[]
    for i,fpath in enumerate(cell_info['data_paths']):
        path_exists = Path(fpath).exists()
        path_exists_list.append(path_exists)
        if not path_exists:
            print("{} - Cell {} of 'cell_info.csv' contains non-existant filepath".format(c,i+1))
            c=c+1
        elif path_exists:
            data_paths.append(Path(fpath))

    # Remove cell_info rows that contain nonexistant filepath
    cell_info = cell_info[path_exists_list]
    cell_info.reset_index(drop=True, inplace=True)

    # Raise error if data_paths column is empty for every row
    if len(cell_info) == 0:
        raise Exception("Error: 's_dict['text_paths']' option is enabled without any data filepaths in 'cell_info.csv'")

    return c, data_paths, cell_info


def converter(df, param, cell_info, drop_col) :
    """Converts raw capacity values (or stds) to:
    1) Ah to mAh
    2) per g (param = 'mass')
    3) per cm2 (param = 'areal')
    4) per cm3 (param = 'volume')

    Arguments:
        df {dataframe} -- dataframe of cells, cycle number and capacity values/stds
        cell_info {dict} -- cell information
        param {str} -- passed to filt.converter function
        col_slice {str or list} -- column headers in level=1 to index by

    Returns:
        dataframe -- the converted dataframe
    """
    idx = pd.IndexSlice

    if param == 'mass' :
        div = cell_info['mass']/1000
    elif param == 'volume' :
        div = pi * ((cell_info['diameter'] / 2) ** 2) * cell_info['thickness'] * (10 ** -4)
        #div = div *1000 # Unit conversion allows same equation to convert to both mass, thickness and areal capacity
    elif param == 'areal' :
        div = pi * ((cell_info['diameter'] / 2) ** 2)
        #div = div *1000 # Unit conversion allows same equation to convert to both mass, thickness and areal capacity
    elif param == 'mAh' :
        div = 1

    df_conv = df.copy()

    cols = df_conv.drop(drop_col,axis=1).columns

    df_conv.loc[idx[:,:,:],idx[cols]] = (df_conv.loc[idx[:,:,:],idx[cols]]*1000) / div

    return df_conv


def save_csv(df, output_folder, c, str_name, str_pass, str_fail) :
    """Saves dataframe to a csv file

    Arguments:
        df {dataframe} -- dataframe to be saved
        output_folder {path obj} -- output folder path
        c        {int} -- counter variable for text outputs
        str_name {str} -- name of file in .format() format
        str_pass {str} -- success text in .format() format
        str_fail {str} -- error text in .format() format

    Returns:
        Message indicating success or failure
    """
    try :
        df.to_csv(output_folder.joinpath(str_name),encoding='utf-8')
        print(str_pass)
        c=c+1
    except:
        print(str_fail)
        c=c+1
        return c

    return c

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Script ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def process(s_dict):
    print('--------------------- Script initiated ----------------')
    print(' ')

    c=0
    
    ### File processing ###
    raw_cols = ['Test_Time(s)','Cycle_Index','Step_Index','Current(A)',
                'Voltage(V)','Charge_Capacity(Ah)','Discharge_Capacity(Ah)']
    col_rename = ['time','cycle','step','I','E','Qp','Qn']

    # Conversion settings - dynamic response to information in 'cell_info.csv'
    param_out_V = ['mAh','mass','areal','volume'] # ['mAh','mass','areal','volume']
    param_out_Q = ['mAh','mass','areal','volume'] #['mAh','mass','areal','volume']

    # Debug
    filepath_debug = True

    # Convert s_dict path and folder settings to local vars
    data_paths = s_dict['f_paths']
    output_folder = s_dict['raw_dir'].joinpath('output')

    # Identify 'cell_info.csv' filepath, import 'cell_info.csv' into df
    # and remove path from data_paths list
    got_info = False
    for index, fpath in enumerate(data_paths):
        if fpath.stem == 'cell_info':
            got_info = True
            cell_info = pd.read_csv(fpath)
            del data_paths[index]

    # Import data paths from 'cell_info.csv' if desired
    if s_dict['text_paths'] and not got_info:
        raise Exception("Error: 's_dict['text_paths']' option is enabled with missing cell_info file." +
                        " Disable 's_dict['text_paths']' option to select data files in a GUI" +
                        " or create a cell_info.csv file containing data filepaths")
    elif s_dict['text_paths'] and got_info:
        c, data_paths, cell_info = check_paths(c,cell_info)

    # If s_dict['text_paths'] is false, sort data_paths to catch issues...
    # with ordering of mixed filetype data sets
    if not s_dict['text_paths'] and got_info:
        data_paths = sort_paths(data_paths,s_dict['raw_dir'])

    # If s_dict['text_paths'] is false and 'cell_info.csv' is missing, create cell_info df from file names
    if not s_dict['text_paths'] and not got_info:
        cell_info = pd.DataFrame(columns=['name'])
        param_out_Q = ['mAh']
        got_info = False
        for i, fpath in enumerate(data_paths):
            cell_info.loc[i] = data_paths[i].stem

    if not len(data_paths) == len(cell_info):
        raise Exception("Number of imported data filepaths does not match 'cell_info.csv' rows"+
                        ", check folder for extra xlsx or csv files and check that 'cell_info.csv'"+
                        "contains a row for each data file.")

    # Put data filepaths into cell_info dataframe
    if not s_dict['text_paths']:
        cell_info['data_paths'] = data_paths

    if filepath_debug:
        print('--------------------- Data files ----------------------')
        fp_names = [i.name for i in data_paths]
        for i,fname in enumerate(fp_names):
            print("{}  {}".format(i,fname))

    print('--------------------- Cell information -----------------')
    if got_info:
        print_info = cell_info.loc[:, cell_info.columns != 'data_paths']
        print(print_info)
    else:
        print("0 - 'cell_info.csv' not found, proceeding with only mAh conversion.")
        param_out_V = ['mAh'] # ['mAh','mass','areal','volume']
        param_out_Q = ['mAh'] #['mAh','mass','areal','volume']

    print('--------------------- Information checks ---------------')

    c=0
    if got_info:
        # Check cell_info for empty name data and add from filename if found
        empty_idx = cell_info[(cell_info['name'].isnull())].index
        if len(empty_idx) > 0:
            for cell in empty_idx:
                cell_info['name'][cell] = data_paths[cell].stem
                print('{} - Cell name added from filename for cell index {}'.format(c,cell))
                c = c+1

        # Check columns exist for data conversion
        params = ['mass','thickness','diameter']
        if not 'mass' in cell_info.columns:
            param_out_Q.remove('mass')
            params.remove('mass')
            print("{} - Missing mass column in 'cell_info.csv' - mass conversion disabled".format(c))
            c=c+1
        if not 'thickness' in cell_info.columns:
            param_out_Q.remove('volume')
            params.remove('thickness')
            print("{} - Missing thickness column in 'cell_info.csv' - volume conversion disabled".format(c))
            c=c+1
        if not 'diameter' in cell_info.columns:
            param_out_Q.remove(['areal','volume'])
            params.remove('diameter')
            print("{} - Missing diameter column in 'cell_info.csv' - areal and volume conversion disabled".format(c))
            c=c+1

        # Check rows in cell_info contain data allowing conversions. If not, remove request for conversion.
        for param in params:
            empty_idx = cell_info[(cell_info[param].isnull())].index
            if len(empty_idx) > 0:
                if param == 'mass':
                    param_out_Q.remove('mass')
                    print('{} - Missing mass entry - mass conversion disabled'.format(c))
                    c=c+1
                elif param == 'thickness':
                    param_out_Q.remove('volume')
                    print('{} - Missing thickness entry - volume conversion disabled'.format(c))
                    c=c+1
                elif param == 'diameter':
                    param_out_Q.remove(['areal','volume'])
                    print('{} - Missing diameter entry - areal and volume conversion disabled'.format(c))
                    c=c+1

    if c == 0:
        print('{} - Cell information provided is complete for chosen outputs'.format(c))

    # --------------------------- Data filtering ---------------------------
    print('--------------------- Data filtering -------------------')

    lst_df = []
    lst_df_cap = []
    c = 0

    for fpath in data_paths:
        # Read raw data into dataframe, rename columns and set cycle and step as index
        if fpath.suffix == '.xlsx':
            xls = pd.ExcelFile(fpath,engine='openpyxl')
            data_sheet = [i for i, sht_name in enumerate(xls.sheet_names) if 'Channel' in sht_name]
            if len(data_sheet) == 1:
                df = xls.parse(data_sheet[0],usecols=raw_cols)[raw_cols]
                xls = None
            else:
                raise Exception("Multiple 'Channel' data sheets in xlsx file," +
                                " check xlsx file: {}".format(fpath))
        elif fpath.suffix == '.csv':
            df = pd.read_csv(fpath,usecols=raw_cols)[raw_cols]

        df.columns = col_rename
        df.set_index(['cycle','step'],inplace=True)

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

        df_cap = df.groupby(['cycle', 'step'])[['I','Qp','Qn']].last()

        # Labelling of constant current steps
        df.loc[df_cap.index[df_cap['I'] == 0].tolist(), 'step_type'] = 'rest'
        df.loc[df_cap.index[df_cap['Qp'] > 0].tolist(), 'step_type'] = 'pos'
        df.loc[df_cap.index[df_cap['Qn'] > 0].tolist(), 'step_type'] = 'neg'

        # Labelling of constant voltage steps - positive current
        cap_filt = df_cap[df_cap['Qp'] > 0].index
        first = df.loc[cap_filt].groupby(['cycle', 'step'])['I'].first()
        last = df.loc[cap_filt].groupby(['cycle', 'step'])['I'].last()
        cv_filt = first/last
        if len(cv_filt.index[cv_filt > s_dict['cv_cut']].tolist()) != 0:
            df.loc[cv_filt.index[cv_filt > s_dict['cv_cut']].tolist(), 'step_type'] = 'posCV'

        # Labelling of constant voltage steps - negative current
        cap_filt = df_cap[df_cap['Qn'] > 0].index
        first = df.loc[cap_filt].groupby(['cycle', 'step'])['I'].first()
        last = df.loc[cap_filt].groupby(['cycle', 'step'])['I'].last()
        cv_filt = first/last
        if len(cv_filt.index[cv_filt > s_dict['cv_cut']].tolist()) != 0:
            df.loc[cv_filt.index[cv_filt > s_dict['cv_cut']].tolist(), 'step_type'] = 'negCV'

        # Make step_type an index for df
        df.set_index(['step_type'], inplace=True, append=True)

        # Update df_cap with new step_type index
        df_cap = df.groupby(['cycle', 'step','step_type'])[['I','Qp','Qn']].last()
        #print(df_cap.tail())

        # Create data_frame of total capacity per cycle
        #df_cap_total = df_cap.groupby(['cycle'])['Qp','Qn'].sum()
        #print(df_cap_total.head())

        lst_df.append(df)
        lst_df_cap.append(df_cap)

    # Calculate average data
    if s_dict['avg_calc']:
        df_cap_temp = pd.concat(lst_df_cap)
        df_cap_avg = df_cap_temp.groupby(['cycle', 'step','step_type'])[['I','Qp','Qn']].mean()
        df_cap_std = df_cap_temp.groupby(['cycle', 'step','step_type'])[['Qp','Qn']].std()
        df_cap_std.columns = ['Qp_std', 'Qn_std']
        df_cap_avg = pd.concat([df_cap_avg, df_cap_std], axis=1)

        # Create average cell_info
        d = {'name': s_dict['avg_name']}
        new_row = pd.Series(data=d, index=['name'])
        new_df = cell_info.mean().to_frame()
        cell_info_avg = pd.concat([new_row,new_df]).T

        print('--------------------- Averaged data --------------------')
        print(cell_info_avg)
        print(df_cap_avg.groupby(['cycle'])[['Qp','Qn','Qp_std','Qn_std']].sum())

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
    if s_dict['sv_avg']:
        print('--------------------- Average export ------------------')

        c=0
        # Save averaged data. One file per param.
        df_param_list = []
        for p,param in enumerate(param_out_Q):
            df_conv = converter(df_cap_avg,param,cell_info_avg.loc[0],'I')

            if s_dict['sv_indv'] & s_dict['sv_avg'] & s_dict['sv_step']:
                c = save_csv(df_conv, output_folder, c,
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

        # Combine param data to single df
        if len(param_out_Q) > 1:
            df_param = pd.concat(df_param_list, axis=1)
        else:
            df_param = df_param_list[0]

        # Group combined df rows by cycle index and save
        c = save_csv(df_param.drop('I',axis=1).groupby(['cycle']).sum(), output_folder, c,
                    'avg_params_cycle_{}.csv'.format(cell_info_avg.loc[0]['name']),
                    "{} - Saved 'per cycle' combined conversion of '{}'".format(c,cell_info_avg.loc[0]['name']),
                    "{} - Error: Could not save 'per cycle' combined conversion of '{}'".format(c,cell_info_avg.loc[0]['name']))

        # Group combined df by step and save
        if s_dict['sv_step']:
            c = save_csv(df_param, output_folder, c,
                    'avg_params_{}.csv'.format(cell_info_avg.loc[0]['name']),
                    "{} - Saved combined conversion of '{}'".format(c,cell_info_avg.loc[0]['name']),
                    "{} - Error: Could not save combined conversion of '{}'".format(c,cell_info_avg.loc[0]['name']))


    # --------------------------- 'per cell' data ---------------------------
    if s_dict['sv_avg']:
        print("--------------------- Cell capacity export ------------")

    c=0
    # Save capacity conversions - converts all mAh columns to divider type (i.e. 'mass')
    for i, df_cap in enumerate(lst_df_cap):
        df_param_list = []
        for p,param in enumerate(param_out_Q):

            # Convert raw data by param
            df_conv = converter(df_cap,param,cell_info.loc[i],'I')

            # Save converted df to individual file
            if s_dict['sv_indv'] & s_dict['sv_step']:
                c = save_csv(df_conv, output_folder, c,
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

        # Combine param data to single df
        if len(param_out_Q) > 1:
            df_param = pd.concat(df_param_list, axis=1)
        else:
            df_param = df_param_list[0]

        # Group combined df rows by cycle index and save
        c = save_csv(df_param.drop('I',axis=1).groupby(['cycle']).sum(), output_folder, c,
                'params_cycle_{}.csv'.format(cell_info.loc[i]['name']),
                "{} - Saved per cycle combined conversion of '{}'".format(c,cell_info['name'][i]),
                "{} - Error: Could not save per cycle combined conversion of '{}'".format(c,cell_info['name'][i]))

        # Group combined df by step and save
        if s_dict['sv_step']:
            c = save_csv(df_param, output_folder, c,
                    'params_{}.csv'.format(cell_info.loc[i]['name']),
                    "{} - Saved combined conversion of '{}'".format(c,cell_info['name'][i]),
                    "{} - Error: Could not save combined conversion of '{}'".format(c,cell_info['name'][i]))

    print("--------------------- Cell voltage export -------------")

    c=0
    drop_cols = ['time','I','E']
    # Save capacity conversions - converts all mAh columns to divider type (i.e. 'mass')
    for i, df in enumerate(lst_df):
        df_param_list = []
        for p,param in enumerate(param_out_V):

            # Convert raw data by param
            df_conv = converter(df,param,cell_info.loc[i],drop_cols)

            # Save converted df to individual file
            if s_dict['sv_indv']:
                c = save_csv(df_conv, output_folder, c,
                        '{}_{}_{}.csv'.format('volt',param,cell_info.loc[i]['name']),
                        "{} - Saved {} conversion of '{}'".format(c,param,cell_info['name'][i]),
                        "{} - Error: Could not save '{}'".format(c,cell_info['name'][i]))

            # Create list of param converted dataframes per cell for concatenation. Append param to column names.
            if p == 0:
                df_param = df_conv.copy()
                df_param.columns = ['{}{}'.format(col, '' if col in drop_cols else '_{}'.format(param)) for col in df_param.columns]
            else:
                df_param = df_conv.copy().drop(drop_cols,axis=1).add_suffix('_'+param)

            df_param_list.append(df_param)

        # Combine param data to single df
        if len(param_out_V) > 1:
            df_param = pd.concat(df_param_list, axis=1)
        else:
            df_param = df_param_list[0]

        # Group combined df by step and save
        c = save_csv(df_param, output_folder, c,
                    '{}_params_{}.csv'.format('volt',cell_info.loc[i]['name']),
                    "{} - Saved combined conversion of '{}'".format(c,cell_info['name'][i]),
                    "{} - Error: Could not save combined conversion of '{}'".format(c,cell_info['name'][i]))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Non-gui file import ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# if manual_run:
#     s_dict = {}
#     s_dict['folder_select'] = True
#     s_dict['text_paths'] = False # Uses text paths from cell_info rather than files in the folder
#     s_dict['use_filenames'] = True
#     s_dict['cv_cut'] = 1.1 # (minimum ratio between CC current vs CV current)
#     s_dict['avg_calc'] = True
#     s_dict['avg_name'] = 'average_data'
#     s_dict['sv_indv'] = False # Save individual csv per conversion i.e. Cell 1 converted to mAh
#     s_dict['sv_step'] = False # Save csv per conversion i.e. Cell 1 converted to mAh
#     s_dict['sv_avg'] = True

#     # Open dialog to select folder, search folder for csv and xlsx files, name output path
#     root = Tk()
#     root.attributes("-topmost", True)
#     root.withdraw()  # stops root window from appearing

#     if s_dict['folder_select']:
#         s_dict['raw_dir'] = askdirectory(parent=root, title="Choose data folder")
#         s_dict['raw_dir'] = Path(s_dict['raw_dir'])
#         s_dict['f_paths'] = list(s_dict['raw_dir'].glob('*.csv')) + list(s_dict['raw_dir'].glob('*.xlsx'))

#     if not s_dict['folder_select']:
#         f_paths_temp = askopenfilenames(parent=root, title='Choose data files',filetypes=file_types)
#         s_dict['f_paths'] = [Path(i) for i in f_paths_temp]
#         s_dict['raw_dir'] = s_dict['f_paths'][0].parent

#     arbin_process(s_dict)

### List of useful variables ###
# lst_df        -- full voltage profile data
# lst_df_cap    -- capacity per step for each individual cell
# df_cap_avg    -- capacity per step with mean and std calculated

### List of useful filters ###
# df_cap.loc[idx[:, :, ['pos']],] -- selects positive constant current capacity steps
# df_cap.loc[idx[:, :, ['posCV']],] -- selects positive constant voltage capacity steps
# df_cap_avg.groupby(['cycle'])['Qp','Qn','Qp_std','Qn_std'].sum() -- capacity per cycle (average df as example)

