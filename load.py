### Import packages ###
import pandas as pd
import os
from pathlib import Path
import shutil
import xlrd

### Debugging ###
import sys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Script ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def xlsx(data_folder, data_path, cell_info) :
    # Find length of file list
    n_cells = len(data_path)
    df = pd.DataFrame()

    for i in range (n_cells) :
        
        # Read in xlsx
        print("Reading file #",i+1," of ",n_cells,": ",data_path[i])
        data = pd.read_excel(data_path[i], sheet_name=1)
        
        # Output csv
        output = data_path[i].parent / (data_path[i].stem + '.csv')
        data.to_csv(output, encoding='utf-8',index = False, header=True)
        print("Saved file #",i+1," of ",n_cells,": ",output)
        
        # Create concatenated dataframe from all cells
        data.insert(0, 'cell', cell_info['cell'][i])
        df = df.append(data)
    
    # Set indexes based on cell number, step index and cycle index
    df.set_index(['cell', 'Cycle_Index', 'Step_Index'], inplace=True)
    df.sort_index(inplace=True)

    # Move raw xlsx data to subfolder
    new_directory = Path(data_folder) / 'raw/'
    # Create folder if it doesn't already exist
    if new_directory.exists ():
        print ("Folder already exists")
    else:
        new_directory.mkdir()
        print ("Created raw folder")
    # Move xlsx files
    for i in range (n_cells) :
        new_loc = new_directory / data_path[i].name
        # Copy files
        try:
            shutil.copy(data_path[i],new_loc)
            print("Copied file #",i+1," of ",n_cells,": ",new_loc.name)
            # Remove files if copy was successful
            try:
                os.remove(data_path[i])
                print("Removed old file #",i+1," of ",n_cells,": ",new_loc.name)
            except OSError as e:  ## if failed, report it back to the user ##
                print ("Error: %s - %s." % (e.filename, e.strerror))
        except IOError as e:
            print("Unable to copy file. %s" % e)
        
    return df, n_cells

def csv(data_path, cell_info) :
    # Find length of file list
    n_cells = len(data_path)
    df = pd.DataFrame()
    
    for i in range (n_cells) :
        
        # Read in csv
        print("Reading file #",i+1," of ",n_cells,": ",data_path[i])
        data = pd.read_csv(data_path[i])
        
        # Create concatenated dataframe from all cells
        data.insert(0, 'cell', cell_info['cell'][i])
        df = df.append(data)
    
    # Set indexes based on cell number, step index and cycle index
    df.set_index(['cell', 'Cycle_Index', 'Step_Index'], inplace=True)
    df.sort_index(inplace=True)

    return df, n_cells