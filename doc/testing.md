# Testing scenarios

# Use cases for running the Studio
Have two Terminal (Command Prompt) windows open. Let's call them T1 and T2. 
* T1 has the latest PhysiCell release where you have compiled a sample model, e.g., the `template` model.
* T2 has the latest PhysiCell Model Builder/Studio release.

## Run the Studio from the PhysiCell folder, from the command line:
* (use backward slashes `\` on Windows)
* `python <path-to-Studio>/bin/pmb.py --studio -e <executable-model> -c <config-file>`

## Run the Studio from its folder (or from the Studio binary package installation)
* `python bin/pmb.py --studio`

## Use the Studio to visualize pre-computed results in any folder

* Assume 2D data: View menu -> "Select output dir", select a folder other than the default output from the current model's config file. Do the Plot and Legend tabs get updated correctly? Then View -> "Select output dir" to switch back to the model's output folder and check Plot & Legend tabs again.

---
# Default parameters
 
 PhysiCell (C++) provides many default values for model parameters. We try to use these same default values in the Studio. For example, when a "New" cell type is created, we try to populate its phenotype subtabs with meaningful default parameters. Unfortunately, there's no easy way to automatically copy/use the default values in the C++ code into the Studio. Therefore, we need to manually check all these values. 
 Moreover, because the Studio offers interactivity when editing a model (as opposed to a static .xml config file), we need to make it clear to the user what is happening when certain actions occur. 
 For example, a cell cycle can have *either*  "phase_transition_rates" or "phase_durations" (which offer different ways to specify the same information). 
 But this raises a question for the Studio: when a user edits, say, a parameter for the phase_transition_rates, should the Studio automatically edit the associated phase_durations
 parameter? This is just one of many such examples of trying to do "the right thing" for the user/model.

 Another thing to manually test is for parameters that may have become deprecated in C++, but not yet in the Studio.

---
# Testing workflows

## General for Model Builder (just GUI and .xml)

* Edit parameters in various tabs/subtabs. If the model has
multiple Microenvironment substrates and/or multiple Cell Types, try editing those as well.
Use the menu "File -> Save as" to a (new) model config file.
Inspect this file to see if it correctly saved your edits. Ideally, you could keep the file open
in a IDE and watch it update live as you save new edits.

* During a single session of using the Studio, load different models containing different numbers of 
 substrates and/or cell types. Do the various dropdown boxes that contain substrates or cell types get updated correctly?

## Cell Types | Custom Data

A custom variable (`Name` column) can have unique `Value` and `Conserve` values across different cell types, however
its `Units` and `Description` will be the same across cell types.

* Make edits to existing parameters. Save results, inspect .xml.
* Confirm that changing the name of a variable (in `Name` column), also changes its name in other cell types.
* Confirm that changing its Units or Description also gets changed in other cell types.
* Confirm that changing a Value or Conserve flag for a variable does NOT get copied over to other cell types.
* Select a row, click the "Delete Row" button. Save results, inspect .xml.
* Use keyboard to remove (delete) just a variable name. Confirm it is also removed from all other cell types and that when you Save results, it is not saved in the .xml.
* Try entering a non-numeric string as a Value. Should not be allowed/possible.
* Try entering a non-valid Name string, e.g., contains spaces, special chars, or starts with a number. Should not be allowed/possible.

---
## General for Studio (includes ICs,Run,Plot,Legend tabs)

* For now, you will need to download PhysiCell and build a model - one of the sample models, for example.
* See the scenarios at the top of this document.