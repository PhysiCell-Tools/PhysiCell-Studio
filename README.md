# PhysiCell-model-builder
GUI application to build a PhysiCell model

## NOTE: this repo is a work in progress. Feel free to explore to code, however, it is not yet a fully functional application. Please check back later for updates.

We are currently exploring two approaches to building a Qt application that will allow a user to build a PhysiCell model (a .xml file). One approach uses Qt Creator and the C++ API. The other approach uses Qt for Python (PySide6). We may eventually port the PySide6 to PyQt5 for reasons to be discussed later. Eventually, we will  settle on a single approach and provide a standalone package for download and execution on Windows, Linux, and macOS.

## Directions for contributors: fork the repo, make edits to the dev branch, and submit Pull requests to dev.

To compile and run the C++ version:
```
cd Qt_Cpp
qmake
make
```

To run the Python version:
```
pip install pyside6
cd Qt_Python/PySide6
python gui4xml.py
```
