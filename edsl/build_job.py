#!/usr/bin/env python3
"""Rebuild the EDSL survey job from the archived one-shot prompts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from edsl import QuestionNumerical, ScenarioList, Survey


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def build_job() -> dict:
    scenarios = pd.read_csv(ROOT / "data" / "one_shot_scenarios.csv")
    archived_job = json.loads((HERE / "jobs.json").read_text())
    survey = Survey(
        [
            QuestionNumerical(
                question_name="predicted_effect",
                question_text="{{ prompt }}",
                min_value=-1,
                max_value=1,
                include_comment=False,
            )
        ],
        name="Full archive one-shot treatment effect forecasts",
    )
    scenario_list = ScenarioList.from_list_of_dicts(
        scenarios.to_dict(orient="records")
    ).to_dict()["scenarios"]
    # The model records are kept exactly as they were serialized at forecast
    # time. That preserves provider-specific settings even if a later EDSL
    # installation no longer registers those historical model classes.
    return {
        "survey": survey.to_dict(),
        "agents": archived_job["agents"],
        "models": archived_job["models"],
        "scenarios": scenario_list,
        "edsl_version": archived_job["edsl_version"],
        "edsl_class_name": archived_job["edsl_class_name"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare the rebuilt EDSL job with the committed jobs.json.",
    )
    args = parser.parse_args()
    output = HERE / "jobs.json"
    job = build_job()
    if args.check:
        saved = json.loads(output.read_text())
        if job != saved:
            raise SystemExit(
                "Rebuilt job differs from edsl/jobs.json. Check the EDSL version "
                "and model defaults before replacing the archived job."
            )
        print("Rebuilt job matches edsl/jobs.json.")
    else:
        output.write_text(json.dumps(job, ensure_ascii=False) + "\n")
        print(f"Wrote {output} using 3 archived model configurations and 469 scenarios.")


if __name__ == "__main__":
    main()
