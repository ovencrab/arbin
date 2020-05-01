### Import packages ###
import pandas as pd
from pathlib import Path
import yaml
from math import floor
from more_itertools import pairwise

### Debugging ###
import sys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Functions ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def save(df, filt_string, data_paths, data_folder) :
    """Saves dataframe to a csv file per cell number

    Arguments:
        df {dataframe} -- dataframe to be saved
        filt_string {str} -- str to name folder and append to processed filenames
        data_paths {list} -- list of path objects to csv files
        data_folder {path obj} -- path object to data folder

    Returns:
        Exception error messages
    """
    try :
        if not data_folder.joinpath(filt_string).is_dir() :
                data_folder.joinpath(filt_string).mkdir(parents=True, exist_ok=True)
        try :
            for i, data in enumerate(df.groupby(level='cell')):
                data[1].to_csv(data_folder.joinpath(filt_string,'{}_{}_{}.csv'.format(data_paths[i].stem, filt_string, i+1)), encoding='utf-8')
        except :
            return print("Couldn't overwrite {} csv files".format(filt_string))
    except :
        return print("Couldn't create {} folder".format(filt_string))


def index(df, data_paths, data_folder, save_indexed) :
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
        df = df.drop(df_mean.index[df_mean == 0].tolist())
        print('2 - Dropped \'average current = 0\' rows.')
    else :
        print('2 - No initial rest step detected.')

    df_last = df.groupby(['cell', 'cycle_index', 'step_index'])['current'].last()

    # Find indexes where the current reduces to 0 label them as 'rest' steps (probably need some extra checks here)
    last_current_list = df_last.index[df_last == 0].tolist()
    if last_current_list :
        df.loc[df_last.index[df_last == 0].tolist(), 'new_index'] = 'rest'
        print('3 - Dropped indexes that have \'current = 0\' in any row.')
    else :
        print('3 - No indexes that have \'current = 0\' in any row detected.')

    # Group filtered data by the mean of each step_index and assign 'pos' or 'neg' labels to the new column 'new_index'
    df_mean = df.groupby(['cell', 'cycle_index', 'step_index'])['current'].mean()
    df_mean.drop(df_last.index[df_last == 0].tolist(), inplace=True)
    df.loc[df_mean.index[df_mean > 0].tolist(), 'new_index'] = 'pos'
    df.loc[df_mean.index[df_mean < 0].tolist(), 'new_index'] = 'neg'

    # Remove old step_index from df and reindex with 'new_index'
    df.reset_index(level='step_index',inplace=True,drop=True)
    df.set_index(['date_time', 'new_index'], inplace=True, append=True)
    df.index.names = ['cell', 'cycle_index', 'date_time', 'step_index']
    df.sort_index(inplace=True)

    if save_indexed == 1 :
        save(df, 'indexed', data_paths, data_folder)

    return df


def decimate(df, row_target, data_paths, data_folder, save_decimated) :
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

    # Save decimated data to csv files in */decimated folder
    if save_decimated == 1 :
        save(df, 'decimated', data_paths, data_folder)

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
    # Remove date_time as index
    df_new = df.reset_index()
    df_new.set_index(['cell', 'cycle_index', 'step_index'], inplace=True)
    df_new.sort_index(inplace=True)

    # Take the last capacity per step_index in the positive cumulative capacity column
    df_pos = df_new.groupby(['cell', 'cycle_index', 'step_index'])['charge_cumulative'].last()
    df_pos = df_pos.loc(axis=0)[pd.IndexSlice[: , :, 'pos']]
    df_pos.reset_index('step_index', drop=True, inplace=True)

    # Take the last capacity per step_index in the negative cumulative capacity column
    df_neg = df_new.groupby(['cell', 'cycle_index', 'step_index'])['discharge_cumulative'].last()
    df_neg = df_neg.loc(axis=0)[pd.IndexSlice[: , :, 'neg']]
    df_neg.reset_index('step_index', drop=True, inplace=True)

    # Combine positive and negative dataframes
    df_cap = pd.concat([df_pos,df_neg], ignore_index=True, axis=1)
    df_cap.columns = ['p_cap','n_cap']

    # Use pairwise function and generator expression to find the
    # capacity per cycle from cumulative capacities
    for n in range(n_cells) :
        i = 2
        for value in (y - x for (x, y) in pairwise(df_cap.loc[n+1]['p_cap'])) :
            df_cap.loc[(n+1, i), 'p_cap'] = value
            i = i + 1

        i=2
        for value in (y - x for (x, y) in pairwise(df_cap.loc[n+1]['n_cap'])) :
            df_cap.loc[(n+1, i), 'n_cap'] = value
            i = i + 1

    # Calculate mean and std from multiple cells and create '0' cell index
    # Append df_cap to averaged data
    if n_cells > 1 :
        df_avg = df_cap.groupby('cycle_index').mean()
        df_std = df_cap.groupby('cycle_index').std()
        df_std.columns = ['p_cap_std', 'n_cap_std']

        df_avg.insert(2, 'cell', 0)
        df_avg.reset_index(inplace = True)
        df_avg.set_index(['cell','cycle_index'], inplace = True)
        df_cap = df_avg.append(df_cap)

        df_std.insert(2, 'cell', 0)
        df_std.reset_index(inplace = True)
        df_std.set_index(['cell','cycle_index'], inplace = True)

        df_cap = pd.concat([df_cap, df_std], axis=1)

    # Create multi index in column axis referring to 'raw' capacity
    df_cap = pd.concat([df_cap], axis=1, keys=['raw'])
    df_cap.sort_index(inplace=True)

    return df_cap