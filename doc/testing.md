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


