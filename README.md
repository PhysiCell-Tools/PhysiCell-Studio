# PhysiCell-model-builder
GUI application to build a PhysiCell model

## NOTE: this repo is a work in progress. Feel free to explore the code, however, it is not yet a fully functional application. Please check back later for updates.

We are currently exploring two approaches to building a Qt application that will allow a user to build a PhysiCell model (a .xml file). One approach uses Qt Creator and the C++ API. The other approach uses the Python API for Qt (either PyQt5 or PySide6). 

## Directions for contributors: fork the repo, make edits to the dev branch, and submit Pull requests to dev.


To run the Python version (the preferred version for now as it's more feature complete):

We recommend installing the [Anaconda Python distribution](https://www.anaconda.com/products/individual) to have the necessary Qt modules and, later, plotting modules.
```
Download the latest release, then run this python script from the root folder in your Terminal/Command Prompt:

.../PhysiCell-model-builder-0.1$ python bin/gui4xml.py
```
