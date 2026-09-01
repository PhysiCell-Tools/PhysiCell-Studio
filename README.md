# PhysiCell Studio

[![cancer_immune model regression test](https://github.com/PhysiCell-Tools/PhysiCell-Studio/actions/workflows/cancer-immune-test.yml/badge.svg)](https://github.com/PhysiCell-Tools/PhysiCell-Studio/actions/workflows/cancer-immune-test.yml)

A graphical tool to create, execute, and visualize a multicellular model using PhysiCell.

See the [PhysiCell Studio Guide](https://github.com/PhysiCell-Tools/Studio-Guide/blob/main/README.md) for full documentation.

## BIWT (BioInformatics WalkThrough)

BIWT is a standalone, pip-installable package that adds a guided wizard for importing
single-cell data (`.csv`, `.h5ad`, and Seurat `.rds`) into PhysiCell initial conditions,
enabled with `python bin/studio.py --biwt`. See [doc/BIWT.md](doc/BIWT.md) for installing it
alongside Studio's dependencies, and the
[BIWT documentation](https://drbergman-lab.github.io/biwt/) for the user guide, Seurat / R
setup, and troubleshooting.

# License

Except when noted otherwise, the entirety of this repository is licensed under a GPL v3 License ([LICENSE](./LICENSE)). This
is due to the use and licensing of PyQt5 (rf. https://pypi.org/project/PyQt5/).

Files matched by the following glob patterns are licensed under [BSD-3-Clause](LICENSE-BSD-3-Clause.txt):

* *.xml
* *.yml
* *.csv
* pyMCDS*.py
* .gitignore
