# Reproduction and verification

## Data and analysis

- make rebuilds the analysis and paper from files in data/. The 469-case Hewitt archive subset includes observed outcomes and original GPT-4 respondent-twin estimates. The exact one-shot prompts and the stored responses from GPT-6 Astra, Claude Fable 5, and Gemini 4 Argon are also vendored. See data/README.md for provenance.
- build_analysis.py validates matching case IDs and creates analysis_cases.csv and study_scores.csv.
- score_one_shot_mixtures.py calculates per-model scores, equal means, leave-one-study-out MAE-optimal weights, study-cluster bootstrap intervals, and the LaTeX tables/macros. It uses 10,000 bootstrap draws with seed 20261024.
- make_study_grid.R regenerates the all-contrast faceted slope graph using ggplot2. Each of 70 panels has a free vertical scale; the 469 contrasts are ranked and evenly spaced horizontally within study, and the lower-MAE path is emphasized.
- The numerical result tables and prose macros are generated from the vendored forecast/outcome data, avoiding hand-copied summary statistics.

## Reproduction results

- Original GPT-4 twins: MAE 0.073468, RMSE 0.107139, sign accuracy 0.690832.
- Individual one-shot MAEs: 0.056037 (GPT-6 Astra), 0.055607 (Claude Fable 5), 0.055128 (Gemini 4 Argon). The equal one-shot mean has MAE 0.053220; study-held-out weights have MAE 0.053507.
- Equal-mean one-shot MAE across ascending fifths of observed absolute effect: 0.034519, 0.032819, 0.047582, 0.064966, and 0.086154. Corresponding twin MAEs: 0.037249, 0.044042, 0.071745, 0.094197, and 0.120090.
- Mean leave-one-study-out weights are 0.181 (GPT-6 Astra), 0.339 (Claude Fable 5), and 0.480 (Gemini 4 Argon). The 95% cluster-bootstrap interval for weighted-minus-equal MAE is [-0.000362, 0.001039].

## Bibliography verification

- Argyle et al. (2023), “Out of One, Many: Using Language Models to Simulate Human Samples.” DOI: <https://doi.org/10.1017/PAN.2023.2>. **High confidence:** Cambridge metadata confirms the publication and DOI.
- Aher, Arriaga, and Kalai (2023), “Using Large Language Models to Simulate Multiple Humans and Replicate Human Subject Studies.” URL: <https://proceedings.mlr.press/v202/aher23a.html>. **High confidence:** official PMLR record.
- Ashokkumar et al. (2026), “Large Language Models Can Predict the Results of Social Science Experiments.” DOI: <https://doi.org/10.1038/s41586-026-10742-x>. **High confidence:** Nature and PubMed metadata.
- Cao et al. (2025), “Specializing Large Language Models to Simulate Survey Response Distributions for Global Populations.” DOI: <https://doi.org/10.18653/v1/2025.naacl-long.162>. **High confidence:** official ACL Anthology record.
- Horton (2023), “Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?” DOI: <https://doi.org/10.3386/w31122>. **High confidence:** NBER working-paper record.

## Build checks

- Full make build: passed.
- LaTeX/BibTeX build: passed; no undefined citations or LaTeX errors.
- Citation-key and bibliography-entry check: passed (5 cited references, no unused entries).
- PDF page count from the final TeX log: 6.
