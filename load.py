### Import packages ###
import pandas as pd
import os
from pathlib import Path
import shutil
import yaml

### Debugging ###
import sys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Functions ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def yml(data_folder) :
    """Takes selected data directory and imports the .yaml cell information as a dictionary

    Arguments:
        data_folder {path} -- Selected directory path

    Returns:
        dictionary -- Cell information including material, mass, thickness etc.
    """
    # List yaml files, open first one (should only be one) and import into dictionary
    info_path = list(data_folder.glob('*.yaml'))
    with open(str(info_path[0])) as file :
        cell_info = yaml.full_load(file)

    return cell_info, info_path

def csv(data_paths, cell_info) :
    """Takes path to csv files and returns a multi-index dataframe and # of cells variable.

    Arguments:
        data_path {list} -- Strings pointing to selected csv data files
        cell_info {dictionary} -- Cell information including material, mass, thickness etc.

    Returns:
        dataframe -- A multi-index dataframe of arbin cell cycle data (Index: cell number (cell), cycle index (Cycle_Index) and step index (Step_Index)
        integer -- Number of cells in data set
    """
    # Find length of file list
    n_cells = len(data_paths)
    df = pd.DataFrame()

    for i in range (n_cells) :

        # Read in csv
        print("Reading file #",i+1," of ",n_cells,": ",data_paths[i])
        data = pd.read_csv(data_paths[i]) # Perhaps add dtypes to improve peformance

        if data.columns[0] == 'Date_Time' :
            # Create concatenated dataframe from all cells
            data.insert(0, 'cell', cell_info['cell'][i])
            raw = True
        else :
            raw = False

        df = df.append(data)

    if raw :
        # Change column headers to correct format and set indexes based on cell number, step index and cycle index
        df.columns = ['cell',
                    'date_time',
                    'test_time',
                    'step_time',
                    'step_index',
                    'cycle_index',
                    'voltage',
                    'current',
                    'charge_cumulative',
                    'discharge_cumulative',
                    'charge_energy',
                    'discharge_energy',
                    'ACR',
                    'int_resistance',
                    'dv/dt']
        df.set_index(['cell', 'cycle_index', 'step_index'], inplace=True)
        df.sort_index(inplace=True)
    else :
        df.set_index(['cell', 'cycle_index', 'date_time', 'step_index'], inplace=True)
        df.sort_index(inplace=True)

    return df, n_cells, raw