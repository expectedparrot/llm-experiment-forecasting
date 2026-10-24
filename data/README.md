# Vendored analysis data

These files are the complete, analysis-ready inputs required to rebuild this
note. The file archive_targets_and_twins.csv contains the 469 human contrasts and
original GPT-4 respondent-twin estimates used here, drawn from the archive
published by Ashokkumar, Hewitt, Ghezae, and Willer (2026). The paper is
[doi:10.1038/s41586-026-10742-x](https://doi.org/10.1038/s41586-026-10742-x).
The selected rows needed for this analysis are vendored here; the full source
archive is not required to rebuild the note.

The file one_shot_scenarios.csv stores the exact direct-forecast prompts and
contrast identifiers used for this comparison. The file one_shot_forecasts.csv
stores the completed forecasts returned by GPT-6 Astra, Claude Fable 5, and
Gemini 4 Argon. The forecasts are vendored so that make rebuilds the analysis
without API credentials, model availability, or additional inference cost.
Re-running the frontier models is a new data collection, not part of the
deterministic build.

The source tables are reduced to the rows and fields needed for the comparison;
no participant-level response records are included here. build_analysis.py
checks that archive cases, prompts, and forecast rows match exactly before
creating the analysis tables.
