# PhysiCell model builder: graphical user interface (GUI) for a PhysiCell model

VERSION: 2.1.0

A graphical user interface (GUI) application to make it easier to create and edit a PhysiCell (XML) model. 


## Usage
We recommend installing the [Anaconda Python distribution](https://www.anaconda.com/products/individual) to have the necessary Qt modules (used by the GUI). 
This Python distribution will also provide plotting modules that are used by the experimental Studio version of the GUI.

Download the latest release and run the following command in your Terminal (or Command Prompt) shell:
```
python bin/pmb.py  # run PhysiCell model builder
```

To run the experimental Studio version, use:
```
python bin/pmb.py --studio   # run PhysiCell model builder + "Studio" funtionality (alpha version)
```

## Release 2.1.0
* update data/interaction.xml to match PhysiCell v1.10
* provide normalize_each_gradient in motility | advanced_chemotaxis

## Release 2.0.0

This release captures most of the functionality provided in [PhysiCell 1.10.0](https://github.com/MathCancer/PhysiCell/releases/tag/1.10.0)

