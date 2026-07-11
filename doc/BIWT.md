# BIWT (BioInformatics WalkThrough)

BIWT is a standalone, pip-installable package that provides a guided wizard for importing
single-cell data into PhysiCell-compatible initial conditions. It is developed and
versioned separately from [PhysiCell Studio](https://github.com/PhysiCell-Tools/PhysiCell-Studio);
Studio consumes it when it is installed, and enables it via the `--biwt` flag.

See also the [PhysiCell Studio Guide](https://github.com/PhysiCell-Tools/Studio-Guide) for
general Studio documentation.

## Installation

Install `biwt` into Studio's conda environment and launch Studio with `--biwt`:

```bash
conda env create -f environment.yml   # creates the "studio" environment
conda activate studio
pip install biwt                       # GUI, .csv, and .h5ad come via the conda env
python3 bin/studio.py --biwt
```

If `biwt` is not installed, Studio falls back to the legacy built-in BIWT tab.

## Seurat / `.rds` import (optional)

Reading `.rds` / `.rda` / `.rdata` (Seurat / SingleCellExperiment) additionally needs a
working R with the `Seurat` and `SingleCellExperiment` R packages, reached through `rpy2`.
The whole R stack — the R interpreter, both R packages, and `rpy2` — installs from conda as
**prebuilt binaries**, so it is fast (no source compile) and lands in the environment's own
R, with no dependency on a system-wide R install.

Add it to the environment you already created for Studio:

```bash
# 1. Activate your existing Studio environment
conda activate studio

# 2. Add the R stack from conda (prebuilt binaries; r-seurat pulls r-seuratobject)
conda install -c conda-forge -c bioconda r-base rpy2 r-seurat bioconductor-singlecellexperiment

# 3. Install BIWT with the Seurat extra (adds anndata2ri<2; rpy2 already satisfied by conda)
pip install "biwt[seurat]"

# 4. Point rpy2 at this environment's R (conda re-applies it on every activation)
conda env config vars set R_HOME="$CONDA_PREFIX/lib/R"
conda deactivate && conda activate studio
```

Then launch as usual with `python3 bin/studio.py --biwt`.

> **Why step 4 matters:** `rpy2` chooses its R from `R_HOME`, falling back to the first `R`
> on `PATH` when it is unset. On macOS a different R installation may sit earlier on `PATH`
> (for example, one reachable by a symlink in `/usr/local/bin`), so without `R_HOME` set
> `rpy2` can load that other R (which lacks Seurat) and segfault. Setting `R_HOME` via
> `conda env config vars` pins it to this
> environment's own R — scoped to the environment, re-applied on every activation, with no
> global PATH changes.

> **Order matters:** install the conda R stack (step 2) *before* `pip install biwt[seurat]`
> (step 3). `anndata2ri` depends on `rpy2`, but neither pulls in R itself (`r-base` is not a
> pip package). If `rpy2` is left to pip, it links against whatever R it finds — the system
> R — reproducing the segfault below. Installing it from conda first gives an `rpy2` that is
> ABI-matched to conda's R.

> **Fallback (slow):** if the conda `r-seurat` / `bioconductor-singlecellexperiment`
> binaries are unavailable for your platform, install just `r-base rpy2` from conda (step 2)
> and get the R packages from CRAN/Bioconductor instead — this compiles from source and can
> take a long time:
> ```bash
> R -e 'install.packages("Seurat", repos="https://cloud.r-project.org")'
> R -e 'if (!requireNamespace("BiocManager", quietly=TRUE)) install.packages("BiocManager", repos="https://cloud.r-project.org"); BiocManager::install("SingleCellExperiment", update=FALSE, ask=FALSE)'
> ```

## Troubleshooting Seurat / `.rds` import

**A common root cause is `rpy2` using the wrong R.** `rpy2` picks its R from
`$R_HOME`, and only falls back to the first `R` on `$PATH` when that is unset. On macOS
another R installation is often reachable earlier on `PATH` (for example, by a symlink in
`/usr/local/bin`), so if the active conda environment has no R of its own — or `R_HOME` is
unset — `rpy2` can silently bind to that system R instead of the conda R. Mixing conda-Python
with a non-conda R is what produces the segfault and OpenMP errors below. Setting `R_HOME` to
the environment's own R resolves the majority of these problems at once.

### Quick diagnostics

```bash
# Which R will rpy2 actually use? Should print a path INSIDE the active env.
python -c "import rpy2.situation as s; print(s.get_r_home())"
python -m rpy2.situation                     # fuller rpy2/R report

# Which executables resolve, and in what order?
which python                                 # expect the conda env's python
which R; type -a R                           # watch for a system R, e.g. /usr/local/bin/R
echo "$PATH"

# Confirm the active environment
echo "$CONDA_PREFIX"; echo "$CONDA_SHLVL"
conda env config vars list                   # is R_HOME pinned for this env?

# Which OpenMP libraries get loaded at launch?
DYLD_PRINT_LIBRARIES=1 python ./bin/studio.py --biwt 2>&1 | grep -i libomp
```

### 1. conda cannot solve `anndata2ri`

- **Symptom:** `nothing provides get_version needed by anndata2ri-1.3.2`
- **Cause:** `conda-forge` (and/or `bioconda`) was not enabled, so conda could not resolve a
  transitive dependency of the `anndata2ri` conda package.
- **Fix:** Prefer installing `anndata2ri` via **pip** (`pip install "biwt[seurat]"` pulls a
  correctly pinned `anndata2ri<2`). If you must use conda, enable both channels with strict
  priority: `conda install -c conda-forge -c bioconda anndata2ri`.

### 2. `rpy2` binds to the wrong R

- **Symptom:** `python -m rpy2.situation` reports
  `Calling 'R RHOME': /Library/Frameworks/R.framework/Resources` even though `r-base` is
  installed in the conda environment; and/or `which R` → `/usr/local/bin/R`.
- **Cause:** `R_HOME` is unset, so `rpy2` resolves `R` from `PATH`, where a system R (e.g.
  `/usr/local/bin/R`) is found before (or instead of) the conda R.
- **Fix:** Pin `R_HOME` to the environment's R — scoped to the env, re-applied on every
  activation, no global PATH edits:
  ```bash
  conda env config vars set R_HOME="$CONDA_PREFIX/lib/R"
  conda deactivate && conda activate <env>
  ```
  Verify with the first diagnostic command — it should now print a path inside the env.

### 3. `substring` error then segmentation fault

- **Symptom:** `Error in substring(x, m + 1L) : invalid substring arguments` immediately
  followed by `Segmentation fault`, crashing Studio.
- **Cause:** `rpy2` embedded a **different R than it was built against** — typically conda's
  `rpy2` loading a system R (see #2). The ABI mismatch corrupts R initialization, surfacing
  as the `substring` error and then a segfault. (The OpenMP clash in #4 is a related symptom
  of the same conda-Python + non-conda-R mixing.)
- **Fix:** Make `rpy2` use the matching conda R by setting `R_HOME` (#2). Also install
  `r-base` **and** `rpy2` from conda *before* `pip install "biwt[seurat]"`, so `rpy2` is the
  conda build that is ABI-matched to conda's R — never let pip compile `rpy2` against the
  system R.

### 4. Duplicate OpenMP runtime

- **Symptom:** `OMP: Error #15: Initializing libomp.dylib, but found libomp.dylib already
  initialized.`
- **Cause:** Two OpenMP runtimes in one process — conda-Python's `libomp.dylib` plus the one
  the embedded non-conda R links against.
- **Fix:** Use a single R stack. With `rpy2` pointed at the **conda** R (#2), the embedded R
  shares conda's `libomp` and the clash disappears. Avoid embedding a non-conda R inside a
  conda-Python process. (`KMP_DUPLICATE_LIB_OK=TRUE` silences the message but is a last
  resort — it can mask crashes or produce wrong results; fix the R mismatch instead.)

### 5. Missing Seurat R packages

- **Symptom:** `Failed to read '<file>.rds' as R object: ... unable to load required package
  'SeuratObject'`
- **Cause:** The R that `rpy2` uses does not have the Seurat R packages installed. Reading a
  Seurat `.rds` needs `SeuratObject` just to reconstruct the object's classes, plus `Seurat`
  and `SingleCellExperiment` for the conversion to AnnData.
- **Fix:** Install the R packages into the *same* R `rpy2` uses (confirm with the first
  diagnostic first). Prefer conda's prebuilt binaries:
  ```bash
  conda install -c conda-forge -c bioconda r-seurat bioconductor-singlecellexperiment
  ```
  If those binaries aren't available for your platform, fall back to CRAN/Bioconductor
  (compiles from source, slow):
  ```bash
  R -e 'install.packages("Seurat", repos="https://cloud.r-project.org")'
  R -e 'if (!requireNamespace("BiocManager", quietly=TRUE)) install.packages("BiocManager", repos="https://cloud.r-project.org"); BiocManager::install("SingleCellExperiment", update=FALSE, ask=FALSE)'
  ```

### 6. `anndata2ri` has no `activate()`

- **Symptom:** `module 'anndata2ri' has no attribute 'activate'` (or `anndata2ri activation
  failed: ...`) when loading an `.rds`/`.rda`.
- **Cause:** `anndata2ri` **2.0+** is installed. The `activate()` API BIWT uses exists
  throughout the `1.x` line but was removed in the 2.0 rewrite; BIWT requires
  `anndata2ri < 2`. This usually happens when 2.0 gets pulled in by an unpinned
  `conda install anndata2ri` over BIWT's requirement.
- **Fix:** Pin to the 1.x line: `pip install "anndata2ri<2"`. Installing via
  `pip install "biwt[seurat]"` already enforces this — just don't override it with a newer
  conda build.

## Root-cause summary

1. **Wrong R (the big one).** `R_HOME` unset → `rpy2` uses a system R (e.g.
   `/usr/local/bin/R`) from `PATH` instead of the conda R. Causes #2, #3, and #4. Fixed by
   pinning `R_HOME`.
2. **pip-built `rpy2`.** Letting pip compile `rpy2` links it against the system R. Install
   `r-base` + `rpy2` from conda first so they are ABI-matched.
3. **Channel / version hygiene.** Missing `conda-forge`/`bioconda` (#1) and unpinned
   `anndata2ri` 2.0 (#6). Prefer `pip install "biwt[seurat]"`, which pins dependencies.
