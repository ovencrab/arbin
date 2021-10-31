# Arbin Data Processor

This code automatically manipulates and converts raw data from arbin cyclers to a more useful format for analysis and visualisation. An Excel VBA add-in is included which converts a folder of arbin *.xlsx* or *.xls* files to *.csv* files.

## Requirements

- Python 3.9.2

## Installation

1. Clone the repository using git, or just download as a zip.

~~~
git clone https://github.com/ovencrab/arbin
~~~

2. Make sure your python environment has the required packages installed (*requirements.txt* is included for virtualenv and *environment.yml* is included for conda)

3. Run *arbin_main.py* using Python 3.9.2 for the GUI version of Arbin Data Processor, or *arbin_manual.py* for the terminal version.

## Usage

Arbin Data Processor can be used in several workflows. Data files for processing can be selected individually, or by folder. By default the script converts the capacity data from Ah to mAh and calculates capacity per charge and discharge cycle. If requested by the user, the script can differentiate and label constant current and constant voltage steps for analysis. Output data is saved in a subfolder named */output*.

![ArbinGUI](/assets/GUI.png)

### Additional calculations

To convert the capacity data to *mAh/g*, *mAh/cm<sup>2</sup>* and *mAh/cm<sup>3</sup>*, an extra *.csv* file can be user generated and named *cell_info.csv* in the same folder as the arbin data files. If the user chooses to use the *'Select files...'* option, the *cell_info.csv* should be selected in addition to the data files.

It may include the columns as shown in the table below:

| name   | mass | thickness | diameter |
|--------|------|-----------|----------|
| cell_1 | 30.2 | 83        | 1.48     |
| cell_2 | 30.2 | 82        | 1.48     |
| cell_2 | 30.2 | 84        | 1.48     |

Where the units of mass are in *mg*, thickness in *&mu;m* and diameter in *cm*.

Note: only diameter rather than area is supported currently.

## Excel Add-In

Although Arbin Data Processor will function while using *.xlsx* or *.xls* files, importing these file types within a python script can take a long time. Converting the *.xlsx* files to *.csv* with the included add-in is recommended.

### Installation

1. Click the **File** tab, click **Options**, and then click the **Add-Ins** category.
2. In the **Manage** box, click **Excel Add-ins**, and then click **Go**. The Add-Ins dialog box appears.
3. Click **Browse** (in the Add-Ins dialog box) to locate the add-in on your computer, and then click **OK**.

### Usage

Ensure the *.xlsx* or *.xls* files are stored in a folder only containing arbin cycling data, otherwise conversion might fail.

1. Open Excel, go to the **Add-Ins** tab and click **SaveAsCsv**, a folder dialog will open.
2. Select the folder which contains the *.xlsx* or *.xls* files.
3. The add-in will convert the files.
