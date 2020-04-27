### Import packages ###
import pandas as pd
import os
from pathlib import Path
import shutil
import yaml
from math import floor

### Debugging ###
import sys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Functions ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def index(df):
    """Removes rest steps from data, changes step_index to 'pos' and 'neg' current labels and
       creates a multi-index based on cell, cycle_index, step_index and date_time

    Arguments:
        df {dataframe} -- raw dataframe imported from csv files

    Returns:
        dataframe -- dataframe with new index
    """

    # Find mean current value of each step (i.e. rest, charge, discharge)
    df_grouped = df.groupby(['cell', 'cycle_index', 'step_index'])['current'].mean()
    print('1 - Created dataframe of mean current values per step_index.')

    # Find indexes which have an average current of 0 and drop them (as they should be the initial rest steps)
    mean_zero_list = df_grouped.index[df_grouped == 0].tolist()
    if mean_zero_list :
        df = df.drop(df_grouped.index[df_grouped == 0].tolist())
        print('2 - Dropped \'average current = 0\' rows.')
    else :
        print('2 - No initial rest step detected.')

    # Find indexes where the current reduces to 0 and drop them (rest steps after charge or discharge)
    any_zero_list = df.index[df['current'] == 0].tolist()
    if any_zero_list :
        df.loc[df.index[df['current'] == 0].tolist(), 'new_index'] = 'rest'
        print('3 - Dropped indexes that have \'current = 0\' in any row.')
    else :
        print('3 - No indexes that have \'current = 0\' in any row detected.')

    # Group new data by the mean of each step_index and assign 'pos' or 'neg' labels to the new column 'new_index'
    df_grouped = df.groupby(['cell', 'cycle_index', 'step_index'])['current'].mean()
    df.loc[df_grouped.index[df_grouped > 0].tolist(), 'new_index'] = 'pos'
    df.loc[df_grouped.index[df_grouped < 0].tolist(), 'new_index'] = 'neg'

    # Remove old step_index and reindex with 'new_index' and 'date_time'
    df.reset_index(level='step_index',inplace=True,drop=True)
    df.set_index(['new_index', 'date_time'], inplace=True, append=True)
    df.index.names = ['cell', 'cycle_index', 'step_index', 'date_time']
    df.sort_index(inplace=True)

    return df

def downsample(df):
    df_plot = df

    df_plot.reset_index(level='date_time', inplace=True)
    df_plot.sort_index(inplace=True)
    my_index = pd.MultiIndex(levels=[[0],[1],[2]], codes=[[],[],[]], names=['cell','cycle_index','step_index'])
    df_downsampled = pd.DataFrame(columns=df_plot.columns, index=my_index)

    L0_start = df_plot.index.get_level_values(0)[1]
    L0_end = df_plot.index.get_level_values(0)[-1]
    L1_start = df_plot.index.get_level_values(1)[1]
    L2_start = df_plot.index.get_level_values(2)[1]

    counter = 1
    for i in df_plot.index.unique() :
        df_temp = df_plot.loc[i]

        if len(df_temp) > 1000 :
            downsampler = floor(len(df_temp)/500)
            df_downsampled = df_downsampled.append(df_temp.iloc[::downsampler])

            if df_downsampled['voltage'].iloc[-1] != df_temp['voltage'].iloc[-1] :
                df_downsampled = df_downsampled.append(df_temp.iloc[-1])

            if L0_start <= i[0] <= L0_end and i[1] == L1_start and i[2] == L2_start :
                print('{} - Downsampled {}...'.format(counter, i))
                counter = counter + 1

        else :
            df_downsampled = df_downsampled.append(df_temp.iloc[::downsampler])

            if L0_start <= i[0] <= L0_end and i[1] == L1_start and i[2] == L2_start :
                print('{} - Left {}...'.format(counter, i))
                counter = counter + 1

    df_downsampled.reset_index(inplace=True)
    df_downsampled.set_index(['cell','cycle_index', 'date_time','step_index'], inplace=True)
    df_downsampled.sort_index(inplace=True)

    #df_downsampled.set_index('date_time', append=True, inplace=True)
    #df_downsampled.sort_index(inplace=True)

    return df_downsampled, counter