# Testing scenarios

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
