### Import packages ###
import pandas as pd
from pathlib import Path
import yaml
from math import floor, pi, isnan
from more_itertools import pairwise

### Debugging ###
import sys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Functions ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def index(df, auto_cycle) :
    """Removes rest steps from data, changes step_index to 'pos' and 'neg' current labels and
       creates a multi-index based on cell, cycle_index, step_index and date_time

    Arguments:
        df {dataframe} -- raw dataframe imported from csv files
        data_paths {list} -- list of path objects to csv files
        data_folder {path obj} -- path object to data folder
        save_indexed {int} -- if == 1, save decimated df, if == 0 don't

    Returns:
        dataframe -- dataframe with new index
    """
    idx=pd.IndexSlice

    # Find mean current value of each step (i.e. rest, charge, discharge)
    df_mean = df.groupby(['cell', 'cycle_index', 'step_index'])['current'].mean()
    print('1 - Created dataframe of mean current values per step_index.')

    # Find indexes which have an average current of 0 and drop them (as they should be the initial rest steps)
    mean_zero_list = df_mean.index[df_mean == 0].tolist()
    if mean_zero_list :
        df.drop(df_mean.index[df_mean == 0].tolist(), inplace=True)
        print('2 - Dropped \'average current = 0\' rows.')
    else :
        print('2 - No initial rest step detected.')

    df_last = df.groupby(['cell', 'cycle_index', 'step_index'])['current'].last()

    # Find indexes where the current reduces to 0 label them as 'rest' steps (might need extra checks here)
    last_current_list = df_last.index[df_last == 0].tolist()
    if last_current_list :
        df.loc[last_current_list, 'new_index'] = 'rest'
        print('3 - Marked indexes that have \'current = 0\' in any row as rest step.')
    else :
        print('3 - No indexes that have \'current = 0\' in any row detected.')

    # Group filtered data by the mean of each step_index and assign 'pos' or 'neg' labels to the new column 'new_index'
    df_mean = df.groupby(['cell', 'cycle_index', 'step_index'])['current'].mean()
    df_mean.drop(df_last.index[df_last == 0].tolist(), inplace=True)
    df.loc[df_mean.index[df_mean > 0].tolist(), 'new_index'] = 'pos'
    df.loc[df_mean.index[df_mean < 0].tolist(), 'new_index'] = 'neg'
    df.set_index(['new_index'], inplace=True, append=True)

    # Create new step index for each unique cycle and step number combination
    new_step_index = []
    for cell in df.index.get_level_values(0).unique():
        lvl_idx = df.loc[idx[cell,:,:,:],:].index.unique().tolist()
        new_step_index = new_step_index + list(range(1,len(lvl_idx)+1))

    # Create new column in dataframe for unique step number
    for row,idx in enumerate(df.index.unique().tolist()):
        df.loc[idx, 'auto_index'] = new_step_index[row]

    df['auto_index'] = df['auto_index'].astype(int)

    # Remove old step_index from df and reindex with 'new_index'
    df.reset_index(level='step_index',inplace=True,drop=True)
    df.reset_index(level='cycle_index',inplace=True,drop=True)
    df.reset_index(level='new_index',inplace=True,drop=False)
    df.set_index(['auto_index', 'new_index'], inplace=True, append=True)
    df.index.names = ['cell', 'step_index', 'step_type']
    df.sort_index(inplace=True)

    return df

def cap(df, n_cells) :
    """Takes dataframes after filt.index or filt.decimate processing and
    finds the capacity from positive and negative currents

    Arguments:
        df {dataframe} -- pre-processed dataframe
        n_cells {int} -- number of cells

    Returns:
        dataframe -- dataframe of capacity values
    """
    idx = pd.IndexSlice

    # Positive current (mean)
    df_p_curr = df.groupby(['cell', 'step_index', 'step_type'])['current'].mean()
    df_p_curr = df_p_curr.loc[idx[:,:,'pos']]

    # Negative current (mean)
    df_n_curr = df.groupby(['cell', 'step_index', 'step_type'])['current'].mean()
    df_n_curr = df_n_curr.loc[idx[:,:,'neg']]

    # Positive cumulative capacity (last)
    df_pos = df.groupby(['cell', 'step_index', 'step_type'])['charge_cumulative'].last()
    df_pos = df_pos.loc[idx[:,:,'pos']]

    # Negative cumulative capacity (last)
    df_neg = df.groupby(['cell', 'step_index', 'step_type'])['discharge_cumulative'].last()
    df_neg = df_neg.loc[idx[:,:,'neg']]

    # Create columns for substractive capacity in full dataframe
    df['p_cap'] = df['charge_cumulative'].copy()
    df['n_cap'] = df['discharge_cumulative'].copy()

    # Use pairwise function and generator expression to find the capacity
    # per step from cumulative capacities. Use capacity per step to
    # generate substractive capacity voltage curve data in df
    df, df_pos = sub_cap(df, df_pos, 'p_cap')
    df, df_neg = sub_cap(df, df_neg, 'n_cap')

    # Combine positive and negative dataframes
    df_cap = pd.concat([df_p_curr, df_n_curr, df_pos, df_neg], ignore_index=True, axis=1)
    df_cap.columns = ['p_curr', 'n_curr', 'p_cap', 'n_cap']

    # Calculate mean and std from multiple cells and create '0' cell index
    # Append df_cap to averaged data
    if n_cells > 1 :
        df_avg = df_cap.groupby('step_index').mean()
        df_std = df_cap.groupby('step_index').std()
        df_std = df_std[['p_cap','n_cap']]
        df_std.columns = ['p_cap_std', 'n_cap_std']

        df_avg.insert(2, 'cell', 0)
        df_avg.reset_index(inplace = True)
        df_avg.set_index(['cell','step_index'], inplace = True)
        df_cap = df_avg.append(df_cap)

        df_std.insert(2, 'cell', 0)
        df_std.reset_index(inplace = True)
        df_std.set_index(['cell','step_index'], inplace = True)

        df_cap = pd.concat([df_cap, df_std], axis=1)

    return df_cap, df

def sub_cap(df, df_grpd, col):
    """Generates subtractive capacity per cycle for both voltage data (df) and
    step data (df_grpd)

    Args:
        df (dataframe): voltage dataframe
        df_grpd (dataframe): dataframe of grouped cumulative capacity data for pos or neg current
        col (str): column in df for generated subtractive capacity data

    Returns:
        df (dataframe): voltage dataframe with subtractive capacity data per step
        df_grpd (dataframe): dataframe of grouped subtractive capacity
    """
    idx = pd.IndexSlice

    for cell in df.index.get_level_values(0).unique().values:

        p_step_init = df_grpd.index.get_level_values(1)[0]

        range_list=[]
        if len(df.index.get_level_values(0).unique().values) > 1:
            steps = df_grpd.loc[idx[cell,:]].index.get_level_values(1)
        else:
            steps = df_grpd.loc[idx[cell,:]].index.get_level_values(0)

        for i,x in enumerate(steps):
            if i == 0:
                lst = list(range(x+1))
            else:
                lst = list(range(steps[i-1]+1,x+1))

            range_list.append(lst)

        for step_idx in df.index.get_level_values(1).unique().values:
            if step_idx > p_step_init:
                for row,tupe in enumerate(range_list):
                    if step_idx in tupe:
                        i = row

                prev_cap = df_grpd.loc[idx[cell,range_list[i-1][-1]]]
                df.loc[idx[cell , step_idx, :], col] = df.loc[idx[cell , step_idx, :], col] - prev_cap

        i = 1
        for value in (y - x for (x, y) in pairwise(df_grpd.loc[idx[cell,:,:]])) :
            df_grpd.loc[idx[cell,range_list[i][-1]]] = value
            i = i + 1

    return df, df_grpd


def f_mean(lst) :
    """Returns average of a list

    Arguments:
        lst {list} -- list of ints

    Returns:
        int -- the average value
    """
    return sum(lst) / len(lst)


def param_convert_volt(df, cell_info, param, col_slice) :
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

    if col_slice == 'all' :
        df_copy = df.loc[idx[:, :, :, :], :].copy()
    else:
        df_copy = df.loc[idx[:, :, :, :], col_slice].copy()

    for cell in df_copy.index.get_level_values(0).unique().values :
        data = df_copy.xs(cell, level=0, drop_level=False)
        data.reindex()
        div = converter(param, cell_info, cell)
        df_copy.update((data*1000)/(div/1000))

    df_copy = pd.concat([df_copy], axis=1, keys=[param])

    return df_copy

def converter(df, param, cell_info, drop_cols) :
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
    df_t = df.drop(drop_cols,axis=1)

    if param == 'mass' :
        div = cell_info['mass']
    elif param == 'volume' :
        div = pi * ((cell_info['diameter'] / 2) ** 2) * cell_info['thickness'] * (10 ** -4)
        div = div * 1000 # Unit conversion allows same equation to convert to both mass, thickness and areal capacity
    elif param == 'areal' :
        div = pi * ((cell_info['diameter'] / 2) ** 2)
        div = div * 1000 # Unit conversion allows same equation to convert to both mass, thickness and areal capacity
    elif param == 'mAh' :
        div = 1000

    df_copy = (df_t*1000)/(div)

    return df_copy

def converter(param, cell_info, cell) :
    """Returns a parameter value (i.e. 'mass' or 'volume') for a cell
    or the average of the cells

    Arguments:
        param {str} -- decides conversion equation to use
        cell_info {dict} -- cell information
        cell {int} -- cell number (if 0, the equation uses the f_mean function value)

    Returns:
        int -- returns the calculated value
    """
    if param == 'mass' :
        div = cell_info['mass'][cell]
    elif param == 'volume' :
        div = pi * ((cell_info['diameter'] / 20) ** 2) * cell_info['thickness'][cell] * (10 ** -4)
        div = div * 1000 # Unit conversion allows same equation to convert to both mass, thickness and areal capacity
    elif param == 'areal' :
        div = pi * ((cell_info['diameter'] / 20) ** 2)
        div = div * 1000 # Unit conversion allows same equation to convert to both mass, thickness and areal capacity
    elif param == 'mAh' :
        div = 1000
    return div


def reformat(df_cap) :
    """Converts vertically concat data frame structure, i.e. cell and cycle index, to
       horizontal concat

    Arguments:
        df {dataframe} -- dataframe of cells, cycle number and capacity values/stds

    Returns:
        dataframe -- the converted dataframe
    """
    df_cap_reformat = pd.DataFrame()

    for cell in df_cap.index.levels[0]:
        df_copy = df_cap.loc[cell]

        if cell > 0 :
            try:
                df_copy.drop(['cap_std'], axis=1, level=1, inplace=True)
            except:
                pass

        df_copy = pd.concat([df_copy], keys=[cell], names=['cell'], axis=1)
        df_cap_reformat = pd.concat([df_cap_reformat, df_copy], axis=1)

    return df_cap_reformat