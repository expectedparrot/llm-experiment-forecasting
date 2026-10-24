# EDSL forecast job

This directory contains the EDSL job definition used to collect the three
one-shot forecast series. The exact serialized job is jobs.json; it contains
469 scenarios and 1,407 model/scenario interviews. The prompts are also
archived in ../data/one_shot_scenarios.csv. The original EDSL results package
is results.ep; its predictions are archived in ../data/one_shot_forecasts.csv.

## Rebuild and check the job

Install the optional dependencies with python -m pip install -r
edsl/requirements.txt, then run from the repository root:

    make edsl-job-check

To serialize a fresh copy of the job from the archived prompts and preserved
model configurations, run:

    python edsl/build_job.py

The check compares the reconstructed survey and scenario records with the
committed job. EDSL serialization can change between versions, so keep the
recorded EDSL version when checking or rebuilding it.

## Run new inference

New model calls are separate from make and can incur provider charges. With
Expected Parrot's EDSL command-line runner and provider access configured, run
a new inference job to a new file so the archived results.ep is preserved:

    ep run --jobs edsl/jobs.json --background --wait --task-timeout 1800 --remote_inference_results_visibility private --output edsl/new_results.ep

Export completed answers in the CSV format used by the analysis with:

python edsl/export_forecasts.py edsl/new_results.ep --output edsl/new_forecasts.csv

After reviewing the new predictions, copy the selected CSV to
data/one_shot_forecasts.csv and rerun make to update the tables, figure, and
paper. To re-export the original stored results without new inference, run
python edsl/export_forecasts.py edsl/results.ep --output edsl/reexported_forecasts.csv.
