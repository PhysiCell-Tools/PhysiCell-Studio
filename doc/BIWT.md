# BIWT (BioInformatics WalkThrough)

BIWT is a standalone, pip-installable package that provides a guided wizard for importing
single-cell data into PhysiCell-compatible initial conditions. It is developed and
versioned separately from [PhysiCell Studio](https://github.com/PhysiCell-Tools/PhysiCell-Studio);
Studio consumes it when it is installed, and enables it via the `--biwt` flag.

BIWT's own documentation — user guide, Seurat / R setup, and troubleshooting — lives at
[drbergman-lab.github.io/biwt](https://drbergman-lab.github.io/biwt/). This page covers the
Studio-specific part: installing `biwt` alongside Studio's dependencies.

See also the [PhysiCell Studio Guide](https://github.com/PhysiCell-Tools/Studio-Guide) for
general Studio documentation.

## Installation

Install `biwt` into Studio's conda environment and launch Studio with `--biwt`:

```bash
conda env create -f environment.yml   # creates the "studio" environment
conda activate studio
pip install 'biwt>=0.6.0'             # no extras -- see the warning below
python bin/studio.py --biwt           # within the activated env
```

> **Install `biwt` without extras here.** This environment already has everything the
> extras would add: PyQt5 from pip, matplotlib and anndata from conda (see
> `environment.yml`). So `biwt[gui]`, `biwt[anndata]`, and `biwt[all]` buy nothing, and
> `biwt[gui]` can re-resolve PyQt5 to a different build than the one Studio is running on.
> (`biwt[seurat]` is the one exception: it is needed for `.rds` input — see below.)

If `biwt` is not installed, Studio falls back to the legacy built-in BIWT tab.

## Seurat / `.rds` import (optional)

Reading `.rds` / `.rda` / `.rdata` (Seurat / SingleCellExperiment) additionally needs a
working R with the `Seurat` and `SingleCellExperiment` R packages, reached through `rpy2`.
The whole R stack installs from conda as prebuilt binaries — fast, no source compile — into
the same `studio` environment you created above.

That setup is not specific to Studio, so it is maintained in BIWT's own documentation:

- **[Installing the R stack](https://drbergman-lab.github.io/biwt/getting-started/installation/#seurat-rds-import-optional)**
  — the conda recipe, including pinning `R_HOME` to the environment's own R.
- **[Troubleshooting](https://drbergman-lab.github.io/biwt/getting-started/troubleshooting/)**
  — the `substring` segfault, duplicate-OpenMP errors, missing `SeuratObject`, and the
  `anndata2ri` 2.0 `activate()` removal.

Two Studio-specific substitutions when following those pages: the environment they call
`<env>` is `studio`, and where they launch the host application, run
`python bin/studio.py --biwt`.



## Using BIWT

For what each wizard step does, see the
**[BIWT user guide](https://drbergman-lab.github.io/biwt/guide/)**.
