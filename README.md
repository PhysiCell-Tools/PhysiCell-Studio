# PhysiCell Studio

A graphical tool to create, execute, and visualize a multicellular model using PhysiCell.

https://github.com/PhysiCell-Tools/Studio-Guide/blob/main/README.md

## BIWT (BioInformatics WalkThrough)

BIWT is a standalone pip-installable package that provides a guided wizard for importing single-cell bioinformatics data (.h5ad, .rds, .rda, .rdata, .csv) into PhysiCell-compatible initial conditions.

### Installation

Create the Studio conda environment (which provides PyQt5, matplotlib, and anndata), then install biwt into it:

```bash
conda env create -f environment.yml
conda activate studio-conda-env
pip install biwt
```

For development (editable install from a local clone):

```bash
pip install -e /path/to/biwt/
```

> **Note:** Do not use `pip install biwt[gui]` in a conda environment — the `gui` extra pulls in pip's PyQt5, which conflicts with conda's PyQt5 and breaks Studio.

Enable in Studio with:

```bash
python3 bin/studio.py --biwt
```

If the package is not installed, Studio falls back to the legacy BIWT tab.

# License

Except when noted otherwise, the entirety of this repository is licensed under a GPL v3 License ([LICENSE](./LICENSE)). This
is due to the use and licensing of PyQt5 (rf. https://pypi.org/project/PyQt5/).

Files matched by the following glob patterns are licensed under [BSD-3-Clause](LICENSE-BSD-3-Clause.txt):

* *.xml
* *.yml
* *.csv
* pyMCDS*.py
* .gitignore
