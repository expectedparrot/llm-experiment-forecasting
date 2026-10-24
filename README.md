# Reproducing the note

From this directory, run:

    make

This rebuilds the analysis-ready case file, forecast scores, study-held-out
mixture analysis, generated LaTeX tables and numeric macros, the 70-panel
contrast plot, and note.pdf. It then checks the LaTeX log, citations, and PDF
page count. The build is offline after the tools below are installed because
the paper subset, exact one-shot prompts, and returned frontier-model forecasts
are included in data/.

Required tools are Python with the versions in requirements.txt, R with
ggplot2 3.5 or newer, ragg and png, GNU Make, and TeX Live (pdflatex and
BibTeX). Install the Python requirements with python -m pip install -r
requirements.txt. Set PYTHON, R, PDFLATEX, or BIBTEX on the make command line
to select other executable paths. Run make clean to remove generated files;
vendored inputs and source files remain.

The default build reuses the stored one-shot forecast outputs. Obtaining new
forecasts requires access to the model providers and constitutes a new model
run; it is intentionally separate from the reproducible analysis and paper
build.
