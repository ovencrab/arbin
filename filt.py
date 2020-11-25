### Import packages ###
import pandas as pd
from pathlib import Path
import yaml
from math import floor, pi
from more_itertools import pairwise

### Debugging ###
import sys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Functions ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def index(df, step_list, auto_cycle) :
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

    # Find indexes where the current reduces to 0 label them as 'rest' steps (probably need some extra checks here)
    last_current_list = df_last.index[df_last == 0].tolist()
    if last_current_list :
        df.loc[last_current_list, 'temp_index'] = 'rest'
        df.loc[last_current_list, 'new_index'] = 'rest'
        print('3 - Marked indexes that have \'current = 0\' in any row as rest step.')
    else :
        print('3 - No indexes that have \'current = 0\' in any row detected.')

    # Group filtered data by the mean of each step_index and assign 'pos' or 'neg' labels to the new column 'new_index'
    df_mean = df.groupby(['cell', 'cycle_index', 'step_index'])['current'].mean()
    df_mean.drop(df_last.index[df_last == 0].tolist(), inplace=True)
    df.loc[df_mean.index[df_mean > 0].tolist(), 'temp_index'] = 1
    df.loc[df_mean.index[df_mean < 0].tolist(), 'temp_index'] = 2
    df.loc[df_mean.index[df_mean > 0].tolist(), 'new_index'] = 'pos'
    df.loc[df_mean.index[df_mean < 0].tolist(), 'new_index'] = 'neg'
    df.set_index(['temp_index'], inplace=True, append=True)

    # Filter for cycle index in case no change in cycle recorded in arbin routine
    test = df.index.unique().tolist()

    # Creates list to ensure constant voltage steps do not trigger cycle number increase
    lst = []
    for row,data in enumerate(test):
        if row == 0:
            lst.append(test[row][2])
        elif test[row-1][0] == test[row][0] and test[row-1][1] == test[row][1] and test[row-1][3] == test[row][3]:
            lst.append(test[row-1][2])
        else:
            lst.append(test[row][2])

    # Creates list to increase cycle number based on current changing sign twice, ignoring adjacent steps
    lst2 = []
    cycle_count = 1
    for row,data in enumerate(test):
        row_curr = test[row][3]
        if row == 0:
            lst2.append(cycle_count)
        elif test[row-1][0] != test[row][0]:
            cycle_count = 1
            lst2.append(cycle_count)
        elif row_curr == test[0][3] and lst[row] != lst[row-1] and test[row-1][0] == test[row][0]:
            cycle_count = cycle_count+1
            lst2.append(cycle_count)
        else:
            lst2.append(cycle_count)

    # Create new column in dataframe for auto generated cycle number
    for row,idx in enumerate(df.index.unique().tolist()):
        df.loc[idx, 'auto_index'] = lst2[row]

        for row2,tupe in enumerate(step_list):
            if set((idx[1],idx[2])).issubset(tupe):
                df.loc[idx, 'auto_index'] = step_list[row2][2]

    df['auto_index'] = df['auto_index'].astype(int)

    # Remove old step_index from df and reindex with 'new_index'
    df.reset_index(level='step_index',inplace=True,drop=True)
    df.reset_index(level='cycle_index',inplace=True,drop=True)
    df.reset_index(level='temp_index',inplace=True,drop=True)
    df.set_index(['auto_index','date_time', 'new_index'], inplace=True, append=True)
    df.index.names = ['cell', 'cycle_index', 'date_time', 'step_index']
    df.sort_index(inplace=True)

    return df


def decimate(df, row_target) :
    """Removes rows of data according to the floored ratio between row_target and the step length

    Arguments:
        df {dataframe} -- raw dataframe imported from csv files
        row_target {int} -- target number of rows left after decimation
        data_paths {list} -- list of path objects to csv files
        data_folder {path obj} -- path object to data folder
        save_decimated {int} -- if == 1, save decimated df, if == 0 don't

    Returns:
        dataframe -- dataframe with new index
    """
    df_plot = df
    df_plot.reset_index('date_time', inplace=True)
    df_plot.sort_index(inplace=True)

    # Create empty dataframe to store downsampled df
    my_index = pd.MultiIndex(levels=[[0],[1],[2]],
                             codes=[[],[],[]],
                             names=['cell','cycle_index','step_index'])
    df_decimate = pd.DataFrame(columns=df_plot.columns, index=my_index)

    # Find start and end of cell index, and the start of both cycle_index and step_index
    L0_start = df_plot.index.get_level_values(0)[1]
    L0_end = df_plot.index.get_level_values(0)[-1]
    L1_start = df_plot.index.get_level_values(1)[1]
    L2_start = df_plot.index.get_level_values(2)[1]

    # Loop over unique indexes and reduce any step_index to 500 rows if above 1000 rows.
    counter = 1
    for i in df_plot.index.unique() :
        df_temp = df_plot.loc[i]

        if len(df_temp) >= row_target*2 :
            downsampler = floor(len(df_temp)/row_target)
            df_decimate = df_decimate.append(df_temp.iloc[::downsampler])

            if df_decimate['voltage'].iloc[-1] != df_temp['voltage'].iloc[-1] :
                df_decimate = df_decimate.append(df_temp.iloc[-1])

            if L0_start <= i[0] <= L0_end and i[1] == L1_start and i[2] == L2_start :
                print('{} - Decimated cell {}...'.format(counter, i[0]))
                counter = counter + 1
        else :
            df_decimate = df_decimate.append(df_temp.iloc[::downsampler])

            if L0_start <= i[0] <= L0_end and i[1] == L1_start and i[2] == L2_start :
                print('{} - Left {}...'.format(counter, i))
                counter = counter + 1

    df_decimate.reset_index(inplace=True)
    df_decimate.set_index(['cell','cycle_index', 'date_time','step_index'], inplace=True)
    df_decimate.sort_index(inplace=True)

    return df_decimate, counter


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
    # Remove date_time as index
    df = df.reset_index()
    df.set_index(['cell', 'cycle_index', 'step_index'], inplace=True)
    df.sort_index(inplace=True)

    # Positive current (mean)
    df_p_curr = df.groupby(['cell', 'cycle_index', 'step_index'])['current'].mean()
    df_p_curr = df_p_curr.loc[idx[: , :, 'pos']]

    # Negative current (mean)
    df_n_curr = df.groupby(['cell', 'cycle_index', 'step_index'])['current'].mean()
    df_n_curr = df_n_curr.loc[idx[: , :, 'neg']]

    # Positive cumulative capacity (last)
    df_pos = df.groupby(['cell', 'cycle_index', 'step_index'])['charge_cumulative'].last()
    df_pos = df_pos.loc[idx[: , :, 'pos']]

    # Negative cumulative capacity (last)
    df_neg = df.groupby(['cell', 'cycle_index', 'step_index'])['discharge_cumulative'].last()
    df_neg = df_neg.loc[idx[: , :, 'neg']]

    # Combine positive and negative dataframes
    df_cap = pd.concat([df_p_curr, df_n_curr, df_pos, df_neg], ignore_index=True, axis=1)
    df_cap.columns = ['p_curr', 'n_curr', 'p_cap', 'n_cap']

    # Create columns for substractive capacity in full dataframe
    df['p_cap'] = df['charge_cumulative'].copy()
    df['n_cap'] = df['discharge_cumulative'].copy()

    # Use pairwise function and generator expression to find the capacity
    # per cycle from cumulative capacities. Use capacity per cycle to
    # generate substractive capacity voltage curve data in df
    for cell in df_cap.index.get_level_values(0).unique().values :
        for cyc_idx in df_cap.index.get_level_values(1).unique().values :
            if cyc_idx > 1 :
                df.loc[idx[cell , cyc_idx, :], 'p_cap'] = df.loc[idx[cell , cyc_idx, :], 'p_cap'] - df_cap.loc[idx[cell, cyc_idx-1], 'p_cap']
                df.loc[idx[cell , cyc_idx, :], 'n_cap'] = df.loc[idx[cell , cyc_idx, :], 'n_cap'] - df_cap.loc[idx[cell, cyc_idx-1], 'n_cap']

        i = 2
        for value in (y - x for (x, y) in pairwise(df_cap.loc[cell]['p_cap'])) :
            df_cap.loc[idx[cell , i], 'p_cap'] = value
            i = i + 1

        i = 2
        for value in (y - x for (x, y) in pairwise(df_cap.loc[cell]['n_cap'])) :
            df_cap.loc[idx[cell , i], 'n_cap'] = value
            i = i + 1

    # Calculate mean and std from multiple cells and create '0' cell index
    # Append df_cap to averaged data
    if n_cells > 1 :
        df_avg = df_cap.groupby('cycle_index').mean()
        df_std = df_cap.groupby('cycle_index').std()
        df_std = df_std[['p_cap','n_cap']]
        df_std.columns = ['p_cap_std', 'n_cap_std']

        df_avg.insert(2, 'cell', 0)
        df_avg.reset_index(inplace = True)
        df_avg.set_index(['cell','cycle_index'], inplace = True)
        df_cap = df_avg.append(df_cap)

        df_std.insert(2, 'cell', 0)
        df_std.reset_index(inplace = True)
        df_std.set_index(['cell','cycle_index'], inplace = True)

        df_cap = pd.concat([df_cap, df_std], axis=1)

    df = df.reset_index()
    df.set_index(['cell','cycle_index', 'date_time','step_index'], inplace=True)
    df.sort_index(inplace=True)

    return df_cap, df


def f_mean(lst) :
    """Returns average of a list

    Arguments:
        lst {list} -- list of ints

    Returns:
        int -- the average value
    """
    return sum(lst) / len(lst)


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

def param_convert(df, cell_info, param, col_slice) :
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
    df_copy = df.loc[idx[:, :, :, :], col_slice].copy()

    for cell in df_copy.index.get_level_values(0).unique().values :

        if col_slice == 'all' :
            data = df_copy.loc[idx[cell,:,:,:], :]
        else :
            data = df_copy.loc[idx[cell,:,:,:], col_slice]

        div = converter(param, cell_info, cell)
        df_copy.update((data*1000)/(div/1000))

    df_copy = pd.concat([df_copy], axis=1, keys=[param])

    return df_copy


def reformat(df_cap) :
    """Converts vertically concat data frame structure, i.e. cell and cycle index, to
       horizontal concat

    Arguments:
        df {dataframe} -- dataframe of cells, cycle number and capacity values/stds

    Returns:
        dataframe -- the converted dataframe
    """
    df_cap_reformat = pd.DataFrame()
    cells = df_cap.index.levels[0]
    for cell in cells :
        df_copy = df_cap.loc[cell]

        if cell > 0 :
            try:
                df_copy.drop(['p_cap_std', 'n_cap_std'], axis=1, level=1, inplace=True)
            except:
                pass

        df_copy = pd.concat([df_copy], keys=[cell], names=['cell'], axis=1)
        df_cap_reformat = pd.concat([df_cap_reformat, df_copy], axis=1)

    return df_cap_reformat