# PhysiCell model builder/Studio: graphical user interface (GUI) for a PhysiCell model


A graphical user interface (GUI) application to make it easier to create and edit a PhysiCell (XML) model, run a simulation, and visualize results. 


## Usage
We recommend installing the [Anaconda Python distribution](https://www.anaconda.com/products/individual) to have the necessary Python modules (used by the GUI, data parsing, visualization). 

Download the latest release and run the following command in your Terminal (or Command Prompt) shell:
```
python bin/pmb.py  # run PhysiCell model builder
```

To run the Studio version, use:
```
python bin/pmb.py --studio   # run PhysiCell model builder + "Studio" functionality
```

To also specify the name of an executable, use "-e" argument, e.g.:
```
python bin/pmb.py --studio -e template 
```

To also specify the name of a configuration file (to populate the GUI), use "-c" argument, e.g.:
* it must be a "flattened" one (see NOTE below)
```
python bin/pmb.py --studio -e template -c config/PhysiCell_settings.xml
```

To specify 3D visualization , use "-3" argument.

To see all possible arguments:
```
python bin/pmb.py --help
```

NOTE: a model's configuration file (.xml) needs to have a "flattened" format, as opposed to the traditional "hierarchical" format, for the cell_definitions. That is to say, each cell_definition needs to explicitly provide *all* parameters, not just those that differ from a parent cell_definition. All of the config files in the `/data` directory have the flattened format.
