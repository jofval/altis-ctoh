# Altimetric Times Series Software


## Installation


1. Install Anaconda python and follow instructions :
    https://www.anaconda.com/distribution

2. Download [AlTiS archive](https://gitlab.com/ctoh/altis/-/archive/main/altis-main.zip)

3. Open archive : altis-main.zip
    - Extract the AlTiS archive.

4. Create AlTiS python environment
    - Start anaconda-navigator
    - Go to "environments" section
    - Select "base" environment to activate it
    - Click on the arrow to open terminal.
    - As function of your OS, type this command line:
        - For Win64 OS : `conda env create ctoh_legos/altis_win`
        - For Linux OS : `conda env create ctoh_legos/altis_linux`

5. Activate the Altis environment
    - Click the new environment "altis" to activate it. It is called
altis_win or altis_linux as function of previous point 4-.

6. Install cartopy features
    - Under anaconda-navigator section "environments"
    - Select "altis" environment to activate it
    - Click on the arrow to open terminal.
    - Go into the directory altis created just before
        `cd <directory_path>/altis-main`
    - Check if the feature_download.py file exist
    - Type this command line:
        * Coastline feature :
            `python feature_download.py gshhs`
        * Rivers and Lakes features :
            `python feature_download.py physical`

7. Install AlTiS
    - Under anaconda-navigator section "environments"
    - Select "altis" environment to activate it
    - Click on the arrow to open terminal.
    - Go into the directory altis created just before :
        `cd <directory_path>/altis-main`
    - Type this command line:
        `python setup.py install`

AlTiS is installed.

## Start Altis

Open terminal (or select Anaconda Powershell Prompt under Window OS Menu)

Activate AlTiS python environment. As function of your OS, type this command line:

- For Win64 OS > `conda activate altis_win`
- For Linux OS > `conda activate altis_linux`

Start AlTiS, type this command line:
- `altis_gui`




