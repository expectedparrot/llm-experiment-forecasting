SHELL := /bin/sh
PYTHON ?= python
R ?= Rscript
PDFLATEX ?= pdflatex
BIBTEX ?= bibtex

.PHONY: all analysis mixture plot paper verify edsl-job edsl-job-check clean

all: paper verify study_slope_grid.png

analysis: study_scores.csv

study_scores.csv: build_analysis.py data/archive_targets_and_twins.csv data/one_shot_scenarios.csv data/one_shot_forecasts.csv requirements.txt
	$(PYTHON) build_analysis.py

mixture: mixture_results.json main_results_table.tex magnitude_results_table.tex analysis_macros.tex

mixture_results.json main_results_table.tex magnitude_results_table.tex analysis_macros.tex: .mixture.stamp
	@test -f "$@" || { rm -f .mixture.stamp; $(MAKE) .mixture.stamp; }

.mixture.stamp: study_scores.csv score_one_shot_mixtures.py requirements.txt
	$(PYTHON) score_one_shot_mixtures.py
	touch .mixture.stamp

plot: study_slope_grid.pdf study_slope_grid.png

study_slope_grid.pdf: study_scores.csv make_study_grid.R
	$(R) make_study_grid.R

study_slope_grid.png: study_slope_grid.pdf
	@test -f "$@" || { rm -f "$<"; $(MAKE) "$<"; }

paper: note.pdf

note.pdf: note.tex refs.bib analysis_macros.tex main_results_table.tex magnitude_results_table.tex study_slope_grid.pdf
	$(PDFLATEX) -interaction=nonstopmode note.tex
	$(BIBTEX) note
	$(PDFLATEX) -interaction=nonstopmode note.tex
	$(PDFLATEX) -interaction=nonstopmode note.tex

verify: note.pdf
	! grep -E 'undefined|Citation .* undefined|LaTeX Error' note.log
	$(PYTHON) verify_build.py

edsl-job:
	$(PYTHON) edsl/build_job.py

edsl-job-check:
	$(PYTHON) edsl/build_job.py --check

clean:
	rm -f analysis_cases.csv study_scores.csv mixture_results.json mixture_fold_weights.csv
	rm -f main_results_table.tex magnitude_results_table.tex analysis_macros.tex
	rm -f .mixture.stamp
	rm -f study_grid_plot_data.csv study_slope_grid.pdf study_slope_grid.png
	rm -f note.aux note.bbl note.blg note.log note.out note.pdf
