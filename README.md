# PhysiCell Studio

A graphical tool to create, execute, and visualize a multicellular model using PhysiCell.

## Usage
We recommend installing the [Anaconda Python distribution](https://www.anaconda.com/products/individual) to have the necessary Python modules (used by the GUI, data parsing, visualization). 

Download the latest release and run the following command in your Terminal (or Command Prompt) shell:
```
python bin/studio.py
```

To specify the name of an executable, use "-e" argument, e.g.:
```
python bin/studio.py -e project 
```

To specify the name of a configuration file (to populate the Studio), use "-c" argument, e.g.:
* it must be a "flattened" one (see NOTE below)
```
python bin/studio.py -e project -c config/PhysiCell_settings.xml
```

To specify 3D visualization , use "-3" argument.

To run a minimal Studio, without the Run and Plot tabs (in case your Python is missing the required modules), use:
```
python bin/studio.py --basic
```

To see all possible arguments:
```
python bin/studio.py --help
```

NOTE: a model's configuration file (.xml) needs to have a "flattened" format, as opposed to the traditional "hierarchical" format, for the cell_definitions. That is to say, each cell_definition needs to explicitly provide *all* parameters, not just those that differ from a parent cell_definition. All of the config files in the `/data` directory have the flattened format.
