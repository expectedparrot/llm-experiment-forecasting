#!/usr/bin/env python3
"""Evaluate equal and study-held-out weighted mixtures of frontier forecasts."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog


HERE = Path(__file__).resolve().parent
RUN = HERE
MODELS = ["gpt-6-astra", "claude-fable-5", "gemini-4-argon"]
KEYS = ["study", "outcome_name", "condition_a", "condition_b"]
BOOTSTRAPS = 10_000
SEED = 20261024


def fit_mae_weights(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Minimize training MAE subject to nonnegative weights summing to one."""
    n = len(y)
    objective = np.r_[np.zeros(x.shape[1]), np.ones(n)]
    # t >= y - Xw and t >= Xw - y, where t is absolute error.
    a_ub = np.vstack(
        [np.c_[-x, -np.eye(n)], np.c_[x, -np.eye(n)]]
    )
    b_ub = np.r_[-y, y]
    a_eq = np.array([[1.0] * x.shape[1] + [0.0] * n])
    result = linprog(
        objective,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=a_eq,
        b_eq=[1.0],
        bounds=[(0.0, 1.0)] * x.shape[1] + [(0.0, None)] * n,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(result.message)
    return result.x[: x.shape[1]]


def write_latex_tables(
    summary: list[dict],
    targets: pd.DataFrame,
    predictions: dict[str, np.ndarray],
    weighted_equal_ci: np.ndarray,
    fold_weights: np.ndarray,
) -> None:
    """Render the two numeric paper tables and prose macros from scored data."""
    by_method = {row["method"]: row for row in summary}
    rows = [
        ("Original GPT-4 respondent twins", "original_twins"),
        ("GPT-6 Astra, one-shot", "gpt-6-astra"),
        ("Claude Fable 5, one-shot", "claude-fable-5"),
        ("Gemini 4 Argon, one-shot", "gemini-4-argon"),
        ("Equal mean of one-shots", "equal_weight_mean"),
        ("Study-held-out weighted mean", "leave_one_study_out_weighted"),
    ]
    lines = [r"\begin{tabular}{lrrr}", r"\toprule", r"Forecast & MAE & RMSE & Sign accuracy \\", r"\midrule"]
    for label, method in rows:
        if method == "original_twins":
            frame = targets
            truth = frame.truth_effect_b_minus_a.to_numpy(float)
            pred = frame.archive_gpt4_effect_b_minus_a.to_numpy(float)
            mae = np.abs(pred - truth).mean()
            rmse = np.sqrt(np.mean((pred - truth) ** 2))
            sign = np.mean(np.sign(pred) == np.sign(truth))
        else:
            item = by_method[method]
            mae, rmse, sign = item["mae"], item["rmse"], item["sign_accuracy"]
        lines.append(f"{label} & {mae:.4f} & {rmse:.4f} & {sign:.3f} \\\\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (HERE / "main_results_table.tex").write_text("\n".join(lines) + "\n")

    cases = targets.copy()
    cases["equal_one_shot"] = predictions["equal_weight_mean"]
    cases["magnitude_group"] = pd.qcut(cases.truth_effect_b_minus_a.abs(), q=5, labels=False)
    grouped = cases.groupby("magnitude_group", sort=True, observed=True)
    bucket_labels = ["Smallest", "Second", "Middle", "Fourth", "Largest"]
    lines = [r"\begin{tabular}{lrrr}", r"\toprule",
             r"Observed $|\tau|$ fifth & $n$ & Equal one-shot MAE & Twin MAE \\", r"\midrule"]
    for i, (_, frame) in enumerate(grouped):
        truth = frame.truth_effect_b_minus_a.to_numpy(float)
        one = frame.equal_one_shot.to_numpy(float)
        twin = frame.archive_gpt4_effect_b_minus_a.to_numpy(float)
        lines.append(
            f"{bucket_labels[i]} & {len(frame)} & {np.abs(one-truth).mean():.4f} & "
            f"{np.abs(twin-truth).mean():.4f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (HERE / "magnitude_results_table.tex").write_text("\n".join(lines) + "\n")

    best_single = min(by_method[name]["mae"] for name in MODELS)
    equal = by_method["equal_weight_mean"]
    weighted = by_method["leave_one_study_out_weighted"]
    delta_ci = equal["mae_difference_vs_original_twins_ci95"]
    weight_ci = weighted_equal_ci
    twin_mae = np.abs(
        targets.archive_gpt4_effect_b_minus_a.to_numpy(float)
        - targets.truth_effect_b_minus_a.to_numpy(float)
    ).mean()
    macros = {
        "TwinsMAE": twin_mae,
        "BestSingleMAEMin": min(by_method[name]["mae"] for name in MODELS),
        "BestSingleMAEMax": max(by_method[name]["mae"] for name in MODELS),
        "MeanOneShotMAE": equal["mae"],
        "MeanOneShotGain": 0.073468 - equal["mae"],
        "MeanTwinDeltaLow": delta_ci[0],
        "MeanTwinDeltaHigh": delta_ci[1],
        "TwinSignAccuracyPct": 100 * np.mean(np.sign(targets.archive_gpt4_effect_b_minus_a) == np.sign(targets.truth_effect_b_minus_a)),
        "MeanOneShotSignAccuracyPct": 100 * equal["sign_accuracy"],
        "BestSingleGain": best_single - equal["mae"],
        "WeightedMAE": weighted["mae"],
        "EqualMAE": equal["mae"],
        "WeightedEqualLow": weight_ci[0],
        "WeightedEqualHigh": weight_ci[1],
        "AstraFoldWeight": float(fold_weights[:, 0].mean()),
        "ClaudeFoldWeight": float(fold_weights[:, 1].mean()),
        "GeminiFoldWeight": float(fold_weights[:, 2].mean()),
    }
    with (HERE / "analysis_macros.tex").open("w") as out:
        for name, value in macros.items():
            precision = 0 if name.endswith("Pct") else 4
            out.write(f"\\newcommand{{\\{name}}}{{{value:.{precision}f}}}\n")


def main() -> None:
    raw = pd.read_csv(RUN / "study_scores.csv")
    raw = raw[raw.model != "equal_weight_frontier_ensemble"].copy()
    wide = raw.pivot(index=KEYS, columns="model", values="one_shot_effect").reset_index()
    case_targets = raw.drop_duplicates(KEYS).copy()
    targets = case_targets.set_index(KEYS)
    wide_index = wide.set_index(KEYS).index
    targets = targets.loc[wide_index]
    x = wide[MODELS].to_numpy(float)
    y = targets.truth_effect_b_minus_a.to_numpy(float)
    original_error = targets.archive_twin_error.to_numpy(float)
    studies = wide.study.to_numpy()

    equal_prediction = x.mean(axis=1)
    weighted_prediction = np.empty(len(y))
    fold_weights = []
    for held_out in np.unique(studies):
        train = studies != held_out
        test = ~train
        weights = fit_mae_weights(x[train], y[train])
        fold_weights.append({"held_out_study": held_out, **dict(zip(MODELS, weights))})
        weighted_prediction[test] = x[test] @ weights
    pd.DataFrame(fold_weights).to_csv(HERE / "mixture_fold_weights.csv", index=False)

    predictions = {model: x[:, i] for i, model in enumerate(MODELS)}
    predictions["equal_weight_mean"] = equal_prediction
    predictions["leave_one_study_out_weighted"] = weighted_prediction
    summary = []
    method_errors = {}
    for name, pred in predictions.items():
        error = pred - y
        method_errors[name] = np.abs(error)
        summary.append(
            {
                "method": name,
                "contrasts": len(y),
                "studies": len(np.unique(studies)),
                "mae": float(np.abs(error).mean()),
                "rmse": float(np.sqrt(np.mean(error**2))),
                "sign_accuracy": float(np.mean(np.sign(pred) == np.sign(y))),
                "mae_difference_vs_original_twins": float(
                    np.abs(error).mean() - np.abs(original_error).mean()
                ),
            }
        )

    # Paired bootstrap, resampling whole studies and retaining all their contrasts.
    study_ids = np.unique(studies)
    indices = [np.flatnonzero(studies == study) for study in study_ids]
    rng = np.random.default_rng(SEED)
    draws = rng.integers(0, len(study_ids), size=(BOOTSTRAPS, len(study_ids)))
    equal_error = np.abs(equal_prediction - y)
    weighted_error = np.abs(weighted_prediction - y)
    bootstrap_deltas = {name: np.empty(BOOTSTRAPS) for name in predictions}
    for name, error in method_errors.items():
        delta = error - np.abs(original_error)
        for i, draw in enumerate(draws):
            ix = np.concatenate([indices[j] for j in draw])
            bootstrap_deltas[name][i] = delta[ix].mean()
    weighted_minus_equal = np.empty(BOOTSTRAPS)
    for i, draw in enumerate(draws):
        ix = np.concatenate([indices[j] for j in draw])
        weighted_minus_equal[i] = (weighted_error[ix] - equal_error[ix]).mean()
    ci = np.quantile(weighted_minus_equal, [0.025, 0.5, 0.975])
    for row in summary:
        row["mae_difference_vs_original_twins_ci95"] = [
            float(np.quantile(bootstrap_deltas[row["method"]], 0.025)),
            float(np.quantile(bootstrap_deltas[row["method"]], 0.975)),
        ]
    weights = np.asarray([[row[model] for model in MODELS] for row in fold_weights])
    output = {
        "weight_training": "For each held-out study, fit nonnegative weights summing to one by minimizing MAE on the other studies.",
        "bootstrap": f"Paired cluster bootstrap resampling {len(study_ids)} studies; seed {SEED}; {BOOTSTRAPS} draws.",
        "weighted_minus_equal_mae_bootstrap_95pct": [float(ci[0]), float(ci[2])],
        "weighted_minus_equal_mae_bootstrap_median": float(ci[1]),
        "mean_leave_one_study_out_weights": dict(zip(MODELS, weights.mean(axis=0).astype(float))),
        "results": summary,
    }
    (HERE / "mixture_results.json").write_text(json.dumps(output, indent=2) + "\n")
    write_latex_tables(summary, targets.reset_index(), predictions, ci[[0, 2]], weights)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
