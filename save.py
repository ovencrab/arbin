### Import packages ###
import pandas as pd
from pathlib import Path
import yaml

### Debugging ###
import sys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Functions ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def multi(df, data_folder, data_paths, filt_string, suffix) :
    """Saves dataframe to a csv file per cell number

    Arguments:
        df {dataframe} -- dataframe to be saved
        filt_string {str} -- name of new folder
        data_paths {list} -- list of path objects to csv files
        data_folder {path obj} -- path object to original data folder

    Returns:
        Exception error messages
    """
    try :
        if not data_folder.joinpath(filt_string).is_dir() :
                data_folder.joinpath(filt_string).mkdir(parents=True, exist_ok=True)
        try :
            for i, data in enumerate(df.groupby(level='cell')):
                data[1].reset_index(level=['cell','date_time'],drop=True).to_csv(data_folder.joinpath(filt_string,'{}_{}_{}.csv'.format(data_paths[i].stem,
                                                                                    suffix,
                                                                                    i+1)), encoding='utf-8')
        except :
            message = "ERROR: Couldn't overwrite {} csv files".format(filt_string)
            return message, 0
    except :
        message = "ERROR: Couldn't create {} folder".format(filt_string)
        return message, 0

    message = ""
    return message, 1


def yml(cell_info, filt_string, data_folder, info_path) :
    """Saves yaml file to directory

    Arguments:
        cell_info {dict} -- dictionary to be saved
        filt_string {str} -- name of new folder
        data_folder {path obj} -- path object to original data folder

    Returns:
        Exception error messages on error
    """
    try :
        file = data_folder.joinpath(filt_string,info_path[0].name)
        with open(file, 'w') as yaml_file :
            yaml.dump(cell_info, yaml_file, default_flow_style=False)
    except :
        return print("ERROR: Couldn't overwrite {} yaml file".format(filt_string))

def single(df, data_folder, data_paths, filt_string, suffix) :
    """Saves dataframe to a csv file

    Arguments:
        df {dataframe} -- dataframe to be saved
        filt_string {str} -- name of new folder
        data_paths {list} -- list of path objects to csv files
        data_folder {path obj} -- path object to original data folder

    Returns:
        Exception error messages
    """
    try :
        if not data_folder.joinpath(filt_string).is_dir() :
                data_folder.joinpath(filt_string).mkdir(parents=True, exist_ok=True)
        try :
            df.to_csv(data_folder.joinpath(filt_string,'{}_{}.csv'.format(data_paths[0].stem,
                                                                                      suffix)), encoding='utf-8')
        except :
            return print("Couldn't overwrite {} csv files".format(filt_string))
    except :
        return print("Couldn't create {} folder".format(filt_string))