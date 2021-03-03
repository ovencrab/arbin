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
        div = cell_info['mass']
    elif param == 'volume' :
        div = pi * ((cell_info['diameter'] / 2) ** 2) * cell_info['thickness'] * (10 ** -4)
        div = div * 1000 # Unit conversion allows same equation to convert to both mass, thickness and areal capacity
    elif param == 'areal' :
        div = pi * ((cell_info['diameter'] / 2) ** 2)
        div = div * 1000 # Unit conversion allows same equation to convert to both mass, thickness and areal capacity
    elif param == 'mAh' :
        div = 1000

    df_conv = df.copy()

    cols = df_conv.drop(drop_col,axis=1).columns

    df_conv.loc[idx[:,:,:],idx[cols]] = (df_conv.loc[idx[:,:,:],idx[cols]]*1000) / div

    return df_conv