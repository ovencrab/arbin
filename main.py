### Import packages ###
from tkinter import Tk
from tkinter.filedialog import askopenfilenames, askdirectory
from pathlib import Path
import yaml
import pandas as pd

### Import debugging ###
import time
import sys

### Import functions ###
import load
import filt
import plot_data

### Options ###

# Folder or file import
folder_select = 0

# Data processing
user_decimate = 0
row_target = 500

# Outputs
save_indexed = 1
save_decimated = 0

# Plot config
user_cell = 1
user_cycle = 0 # 0 plots all cycles
user_x = 'test_time'
user_y = 'voltage'
user_y2 = 'current'

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Script ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Select files and call import functions
if folder_select == 0 :

    # Open dialog box to select files
    # Tk().withdraw()
    # filez = askopenfilenames(title='Choose a file', filetypes=(('.csv files', '*.csv'),))

    # Create list of files and extract folder path from first file path
    # filez = list(filez)
    # data_paths = [Path(data_path) for data_path in filez]
    # data_folder = Path(data_paths[0]).parent
    t_str = 'decimated'
    data_paths = [Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/{}/JE_LtS_rate_B1_12_Channel_12_{}_1.csv'.format(t_str, t_str),
                 Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/{}/JE_LtS_rate_B2_13_Channel_13_{}_2.csv'.format(t_str, t_str),
                 Path.home() / 'OneDrive - Nexus365/Oxford/0 Post doc/02 Data/Arbin/001 Test data/{}/JE_LtS_rate_B3_14_Channel_14_{}_3.csv'.format(t_str, t_str)]
    data_folder = Path(data_paths[0]).parent
else:
    # Open dialog box to select folder
    Tk().withdraw()  # stops root window from appearing
    data_folder = askdirectory(title="Choose data folder")  # "Open" dialog box and return the selected path
    data_paths = list(Path(data_folder).glob('*.csv'))

# Finds the .yaml file in data_folder and creates a dictionary from the information
try :
    cell_info = load.yml(data_folder)
except :
    try :
        cell_info = load.yml(data_folder.parent)
    except :
        raise Exception("Can't find *.yaml information file")

# Checks for decimated or previously indexed data
str_check = [data_path.as_posix() for data_path in data_paths]

deci_check = []
index_check = []
for i, data_name in enumerate(str_check) :
    deci_check.append('decimated' in data_name)
    index_check.append('indexed' in data_name)

# Load csv data
tic = time.perf_counter()
if not any(deci_check) and not any(index_check) :
    df, n_cells = load.csv_raw(data_paths, cell_info)
    decimated = 0
    filtered = 0
elif any(deci_check) :
    df, n_cells = load.csv_processed(data_paths, cell_info)
    decimated = 1
elif any(index_check) :
    df, n_cells = load.csv_processed(data_paths, cell_info)
    decimated = 0
    filtered = 1

toc = time.perf_counter()
print(f"Imported files in {toc - tic:0.1f}s")

# Print data
print('--------------------------------------')
print("Returned data:")
print('--------------------------------------')
[print(key, ': ', value) for key, value in cell_info.items()]
print('Dataframe size: {}'.format(df.size))

#------------------------
# Data filtering

if decimated == 0 :
    if filtered == 0 :
        print('--------------------------------------')
        print('Data filtering')
        print('--------------------------------------')

        tic = time.perf_counter()

        df = filt.index(df, data_paths, data_folder, save_indexed)

        toc = time.perf_counter()
        print(f"4 - Created new index in {toc - tic:0.1f}s")

    #------------------------
    # Downsampling

    if user_decimate == 1:
        print('--------------------------------------')
        print('Decimating data')
        print('--------------------------------------')

        tic = time.perf_counter()

        df_decimate, counter = filt.decimate(df, row_target, data_paths, data_folder, save_decimated)

        toc = time.perf_counter()
        t = f'{toc - tic:0.1f}'
        print('{} - Reduced number of rows from {} to {} in {}s'.format(counter, df.shape[0], df_decimate.shape[0],t))
        df = df_decimate

#------------------------
# Plotting test

print('--------------------------------------')
print('Plot data')
print('--------------------------------------')

tic = time.perf_counter()

fig = plot_data.profile(df, user_cell, user_cycle, user_x, user_y, user_y2)

fig.show()

toc = time.perf_counter()
print(f"Plot generated in {toc - tic:0.1f}s")

#------------------------
# End

sys.exit()