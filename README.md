# PhysiCell-model-builder
GUI application to build a PhysiCell model

## NOTE: this repo is a work in progress. Feel free to explore the code, however, it is not yet a fully functional application. Please check back later for updates.

We are currently exploring two approaches to building a Qt application that will allow a user to build a PhysiCell model (a .xml file). One approach uses Qt Creator and the C++ API. The other approach uses the Python API for Qt (either PyQt5 or PySide6). 

## Directions for contributors: fork the repo, make edits to the dev branch, and submit Pull requests to dev.

To compile and run the C++ version:
```
cd src
qmake
make
# run the generated application
```

To run the Python version:
```
cd bin
python gui4xml.py
```
