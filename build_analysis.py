#!/usr/bin/env python3
"""Build analysis tables from vendored Hewitt archive data and stored forecasts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
MODELS = ["gpt-6-astra", "claude-fable-5", "gemini-4-argon"]


def main() -> None:
    targets = pd.read_csv(DATA / "archive_targets_and_twins.csv")
    scenarios = pd.read_csv(DATA / "one_shot_scenarios.csv")
    forecasts = pd.read_csv(DATA / "one_shot_forecasts.csv")

    if len(targets) != 469 or targets.study.nunique() != 70:
        raise ValueError(
            f"Expected the fixed common sample of 469 contrasts in 70 studies; "
            f"found {len(targets)} contrasts in {targets.study.nunique()} studies."
        )
    if targets.scenario_id.duplicated().any() or scenarios.scenario_id.duplicated().any():
        raise ValueError("Archive cases and prompts must have unique scenario IDs.")
    if forecasts.duplicated(["scenario_id", "model"]).any():
        raise ValueError("Forecasts must have one row per case and model.")
    if set(forecasts.model) != set(MODELS):
        raise ValueError(f"Unexpected one-shot model set: {sorted(forecasts.model.unique())}")
    if len(forecasts) != len(targets) * len(MODELS):
        raise ValueError(f"Expected {len(targets) * len(MODELS)} model forecasts, got {len(forecasts)}.")
    if set(forecasts.scenario_id) != set(targets.scenario_id):
        raise ValueError("Stored one-shot forecasts and archive outcome cases have different IDs.")

    keys = ["scenario_id", "study", "outcome_name", "condition_a", "condition_b"]
    cases = targets.merge(
        scenarios[["scenario_id", "prompt"]].rename(columns={"prompt": "one_shot_prompt"}),
        on="scenario_id", how="outer", validate="one_to_one", indicator=True,
    )
    if not (cases._merge == "both").all():
        raise ValueError("Archive outcomes and one-shot prompt cases do not match exactly.")
    cases = cases.drop(columns="_merge")
    forecast_wide = forecasts.pivot(index="scenario_id", columns="model", values="one_shot_effect")
    if forecast_wide.isna().any().any():
        raise ValueError("At least one stored model forecast is missing.")
    forecast_wide.columns = [f"one_shot_{column}" for column in forecast_wide.columns]
    cases = cases.merge(forecast_wide.reset_index(), on="scenario_id", validate="one_to_one")
    cases.to_csv(HERE / "analysis_cases.csv", index=False)

    scored_rows = []
    for model in MODELS:
        frame = cases[keys + ["truth_effect_b_minus_a", "archive_gpt4_effect_b_minus_a"]].copy()
        frame["model"] = model
        frame["one_shot_effect"] = cases[f"one_shot_{model}"]
        scored_rows.append(frame)
    scores = pd.concat(scored_rows, ignore_index=True)
    scores["archive_twin_error"] = (
        scores.archive_gpt4_effect_b_minus_a - scores.truth_effect_b_minus_a
    )
    scores.to_csv(HERE / "study_scores.csv", index=False)
    print(f"Prepared {len(cases)} contrasts across {cases.study.nunique()} experiments.")


if __name__ == "__main__":
    main()
