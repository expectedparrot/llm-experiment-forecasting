#!/usr/bin/env python3
"""Export model answers from an EDSL Results file to the vendored CSV schema."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from edsl import Results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path, help="EDSL Results package (.ep or JSON).")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "one_shot_forecasts.csv",
    )
    args = parser.parse_args()

    raw = Results.load(str(args.results)).to_pandas()
    forecasts = raw[
        ["scenario.scenario_id", "model.model", "answer.predicted_effect"]
    ].rename(
        columns={
            "scenario.scenario_id": "scenario_id",
            "model.model": "model",
            "answer.predicted_effect": "one_shot_effect",
        }
    )
    forecasts["one_shot_effect"] = pd.to_numeric(
        forecasts.one_shot_effect, errors="raise"
    )
    if len(forecasts) != 469 * 3:
        raise ValueError(f"Expected 1,407 model/case rows, found {len(forecasts)}.")
    if forecasts.duplicated(["scenario_id", "model"]).any():
        raise ValueError("Duplicate scenario/model forecast rows found.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    forecasts.to_csv(args.output, index=False)
    print(f"Exported {len(forecasts)} forecasts to {args.output}.")


if __name__ == "__main__":
    main()
