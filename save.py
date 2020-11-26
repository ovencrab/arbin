### Import packages ###
import pandas as pd
from pathlib import Path
import yaml

### Debugging ###
import sys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Functions ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def get_name(data_path):
    name = data_path.stem.split("_")
    name = name[0]+'_'+name[1]+'_'+name[2]+'_'+name[3]
    return name

def get_name_custom(data_path,cell_info,suffix):
    name = data_path.stem.split("_")
    name = cell_info['name']+'_'+name[2]+'_'+suffix
    return name

def multi(df, data_folder, data_paths, cell_info, filt_string, df_type, drop_levels, prefix) :
    """Saves dataframe to a csv file per cell number

    Arguments:
        df {dataframe} -- dataframe to be saved
        filt_string {str} -- name of new folder
        data_paths {list} -- list of path objects to csv files
        data_folder {path obj} -- path object to original data folder

    Returns:
        Exception error messages
    """
    idx = pd.IndexSlice

    try :
        if filt_string != 'none' :
            data_folder = data_folder.joinpath(filt_string)
            if not data_folder.is_dir() :
                    data_folder.mkdir(parents=True, exist_ok=True)
        try :
            if df_type == 'voltage':
                for i, data in enumerate(df.groupby(level='cell')) :
                    name = get_name(data_paths[i])
                    data[1].reset_index(level=drop_levels,drop=True).to_csv(data_folder.joinpath('{}_{}.csv'.format(prefix,name)), encoding='utf-8')
            elif df_type == 'reformat':
                for i, cell in enumerate(df.columns.levels[0]):
                    if cell == 0 :
                        name = get_name_custom(data_paths[0],cell_info,'avg')
                        df.loc[idx[:,:], idx[cell,:,:]].to_csv(data_folder.joinpath('{}_{}.csv'.format(prefix,name)), encoding='utf-8')
                    else :
                        name = get_name(data_paths[cell-1])
                        df.loc[idx[:,:], idx[cell,:,:]].to_csv(data_folder.joinpath('{}_{}.csv'.format(prefix,name)), encoding='utf-8')
        except :
            message = "ERROR: Couldn't create or overwrite {} csv files".format(filt_string)
            return message, 0
    except :
        message = "ERROR: Couldn't create {} folder".format(filt_string)
        return message, 0

    message = ""
    return message, 1

def param_filter(df, data_folder, data_paths, cell_info, filt_string, param_list) :
    """Saves dataframe to a csv file per cell number

    Arguments:
        df {dataframe} -- dataframe to be saved
        filt_string {str} -- name of new folder
        data_paths {list} -- list of path objects to csv files
        data_folder {path obj} -- path object to original data folder

    Returns:
        Exception error messages
    """
    idx=pd.IndexSlice
    try :
        if filt_string != 'none' :
            data_folder = data_folder.joinpath(filt_string)
            if not data_folder.is_dir() :
                    data_folder.mkdir(parents=True, exist_ok=True)
        try :
            for param in param_list :
                name = get_name_custom(data_paths[0],cell_info,param)
                df.loc[idx[:,:],idx[:,['univ',param],:]].to_csv(data_folder.joinpath('{}.csv'.format(name)), encoding='utf-8')
        except :
            message = "ERROR: Couldn't create or overwrite {} csv files".format(filt_string)
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
        return print("ERROR: Couldn't create or overwrite {} yaml file".format(filt_string))

def single(df, data_folder, data_paths, cell_info, filt_string, suffix) :
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
        if filt_string != 'existing' :
            data_folder = data_folder.joinpath(filt_string)
            if not data_folder.is_dir() :
                    data_folder.mkdir(parents=True, exist_ok=True)
        try :
            df.to_csv(data_folder.joinpath('{}_{}.csv'.format(cell_info['name'],
                                                            suffix)), encoding='utf-8')
        except :
            message = "ERROR: Couldn't create or overwrite {} csv files".format(filt_string)
            return message, 0
    except :
        message = "ERROR: Couldn't create {} folder".format(filt_string)
        return message, 0

    message = ""
    return message, 1