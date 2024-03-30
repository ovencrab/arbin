### Import packages ###
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilenames
import numpy as np
import pandas as pd

### Temp packages ###
from math import pi

### Fixed variables ###
file_types = [('Processed CSV files', ['*.csv'])]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### User options ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def import_data():
    # Open dialog to select folder, search folder for csv and xlsx files, name output path
    root = Tk()
    root.attributes("-topmost", True)
    root.withdraw()  # stops root window from appearing

    f_paths_temp = askopenfilenames(parent=root, title='Choose data files',filetypes=file_types)
    f_paths = [Path(i) for i in f_paths_temp]
    f_dir = f_paths[0].parent

    return f_paths, f_dir