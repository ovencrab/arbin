### Import packages ###
import pandas as pd
from pathlib import Path
import yaml

### Debugging ###
import sys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Functions ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def single(df, output_folder, c, str_name, str_pass, str_fail) :
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