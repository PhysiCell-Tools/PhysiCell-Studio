
## Release 2.9.4
* reposition New,Copy,Delete buttons on Microenv and Cell Types tabs
* better About info in Studio menu
* this release doc; cleanup README
* cleanup dirs to be less nanoHUB-template

## Release 2.9.3
* remove Rules for now
* add voxel and mechanics grid toggles to 2D View
* remove rules subtab code in Cell Types module

## Release 2.9.2
* logging for debugging (not just errors)
* sanity checks for vis3D with existing output
* fix crazy Config checkbox for csv (move to non-zeroth column)

## Release 2.9.1
* fix bugs related to not having ICs tab created in cell_def_tab.py (thanks Grant Maxey)
* switch to pcolormesh instead of contourf for 2D substrates
* View menu: allow Gouraud shading for pcolormesh
* logging for debugging
* full config path in title
* plot legend if already exists in output dir
* improved Rules tab: Load, Save, etc.

## Release 2.9.0
* fix bugs related to allowing for empty <custom_data> (thanks Issy Cowlishaw)
* fix show voxels (for 3D)
* vtk 3D viewer cmds
* fix cmap and min,max (3D)
* detect incomplete final .svg

## Release 2.8.6
* more cutting planes for 3D vis
* option to plot all voxels in 3D vis
* fix logic of Dirichlet boundaries toggles

## Release 2.8.5
* gracefully handle deprecated cycle "transition_rates" in config file
* fix bug related to specified output dir in 3D vis
* add some ABM benchmark data files

## Release 2.8.4
* awareness of where it's being run from and behaving appropriately
* use latest pyMCDS.py
* try to properly Cancel a Run (studio mode) on Windows
* check for bogus colormap ranges
* add couple checks for "old" config file syntax: missing virtual walls, missing death params

## Release 2.8.3
* fix undefined exec_file bug
* add nuclei checkbox/plotting for 2D
* various improvements to 3D plotting
* have ICs tab plot reset to match config_tab domain
* fix ICs bug for cells.csv for disk hex 
* populate_tree_cell_defs now updates various widget combobox entries 
* add a few config files and cells.csv for ABM benchmarks

## Release 2.8.2
* added command line arguments (see `--help`)
* several improvements for 3D plotting (using VTK); still missing color-by-celltype
* added some 3D models in /data

## Release 2.8.1
* ICs: Compute radius from celltype volume. Improve widgets layout.

## Release 2.8.0
* Provide a tab to create common setup_tissue patterns (cells.csv)

## Release 2.7.9
* bug fix for toggling Chemotaxis vs. Advanced Chemotaxis (Thanks Daniel Bergman!)

## Release 2.7.8
* update VERSION.txt
 
## Release 2.7.7
* Disable keyboard navigation through items in the QTreeWidget

## Release 2.7.6
* When we load a new model, part of the reset needs to reset cell_adhesion_affinity_celltype to None (thanks to Joel Eliason for catching and reporting this!)

## Release 2.7.5
* Fix bug on maintaining cell def state of mechanics cell adhesion affinity

## Release 2.7.4
* Provide at least minimal validation of the config file being loaded. It cannot use the legacy hierarchical syntax; it needs to provide explicit parameters for each <cell_definition>.

## Release 2.7.3
* When a cell type is deleted, also delete it in the dicts associated with mechanics:cell adhesion affinities and interactions:*

## Release 2.7.2
* Allow starting the PMB from anywhere

## Release 2.7.1
* fixes for the PhysiBoSS cell lines sample

## Release 2.7.0
* operate directly on a .xml file instead of a copy
* provide a /data/backup to keep copies of original sample models

## Release 2.6.0
Update of the PhysiBoSS intracellular interface.

Update of the XML structure:

* Added dropdowns for signals, behaviours, and nodes in mapping
* Automatic update of signals, behaviours according to
* Automatic update of maboss model nodes according to BND file

## Release 2.5.0
* handle `conserved` attribute on custom data (if true, daughter cells split quantity evenly)
* allow CSV vector of values for custom data; drop validation (of numeric value)
* resolve headache of default dark-mode on macOS/arm64 (from `conda install -c anaconda pyqt`)

## Release 2.4.1
* check for 3D model: (zmax-zmin)>dz ; set <domain><use_2D> accordingly
* bug fixes for Studio modules


## Release 2.4
* mostly improvements related to the Studio version, e.g.
* allow for Plotting from different output folders (rf. Config Basics)
* Warn user if SVG and full output intervals do not match
* Disable Run Simulation button when one starts
* Stop a running simulation if a new model is selected from File menu
* Provide a Legend tab to display the cell types' colors legend

## Release 2.3.1
* prevent Cell Types subtabs from scrolling away
* update VERSION and README :/

## Release 2.2.0
* provide get_pgms.sh bash script to get sample executables
* update pmb.py and run_tab.py to provide mostly-working Studio

## Release 2.1.0
* update data/interactions.xml to match PhysiCell v1.10
* provide normalize_each_gradient in motility | advanced_chemotaxis

## Release 2.0.0

This release captures most of the functionality provided in [PhysiCell 1.10.0](https://github.com/MathCancer/PhysiCell/releases/tag/1.10.0)
