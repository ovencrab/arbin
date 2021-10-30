### Import packages ###
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilenames
import numpy as np
import pandas as pd
import yaml
import natsort
import re

### Temp packages ###
from math import pi

### Import debugging ###
import os
import sys
import time

### Import *.py files ###
from arbin_scripts import process

### Fixed variables ###
file_types = [('Arbin & cell_info files', ['*.csv','*.xlsx'])]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### User options ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

s_dict = {}
with open(r'arbin_settings.yml') as file:
    s_dict = yaml.load(file, Loader=yaml.FullLoader)

# Open dialog to select folder, search folder for csv and xlsx files, name output path
root = Tk()
root.attributes("-topmost", True)
root.withdraw()  # stops root window from appearing

if s_dict['folder_select']:
    s_dict['raw_dir'] = askdirectory(parent=root, title="Choose data folder")
    s_dict['raw_dir'] = Path(s_dict['raw_dir'])
    s_dict['f_paths'] = list(s_dict['raw_dir'].glob('*.csv')) + list(s_dict['raw_dir'].glob('*.xlsx'))

if not s_dict['folder_select']:
    f_paths_temp = askopenfilenames(parent=root, title='Choose data files',filetypes=file_types)
    s_dict['f_paths'] = [Path(i) for i in f_paths_temp]
    s_dict['raw_dir'] = s_dict['f_paths'][0].parent

process(s_dict)