"""Multistart same-model check and explicitly labelled nonnegative diagnostics.

The positive-variance analysis adds bounds solely as a diagnostic. It must not
be substituted for the source Amos model's unrestricted-variance estimates.
"""

import json
import math
from pathlib import Path
import random

import check_composite_ml as check
from check_composite_ml import ROOT, ReducedObjective, original_to_reduced, reduced_to_original, minimize, sem


class PositiveVarianceObjective:
    def __init__(self, sample):
        self.original = sem.Objective(sample)
        self.scales = [1.0] * 36

    def original_raw(self, x):
        return [x[i] * sem.SCALES[i] if i < 16 else math.exp(x[i]) * sem.SCALES[i]
                for i in range(36)]

    def transform(self, raw):
        assert all(v > 0 for v in raw[16:])
        return [raw[i] / sem.SCALES[i] if i < 16 else math.log(raw[i] / sem.SCALES[i])
                for i in range(36)]

    def evaluate(self, x, gradient=True):
        try:
            scaled = [x[i] if i < 16 else math.exp(x[i]) for i in range(36)]
            f, g = self.original.evaluate(scaled, gradient)
            if not gradient or g is None:
                return f, None
            return f, [g[i] if i < 16 else g[i] * scaled[i] for i in range(36)]
        except (OverflowError, ZeroDivisionError):
            return math.inf, None


def summarize_reduced_fit(fit, sample):
    raw = reduced_to_original(fit["raw_parameters_reduced"])
    sigma = check.reduced_sigma(fit["raw_parameters_reduced"])[0]
    if raw is None:
        return {"termination": fit["termination"], "F": fit["F_ml"],
                "gradient": fit["maximum_scaled_gradient"], "finite_original_parameters": False}
    scaled = [v / s for v, s in zip(raw, sem.SCALES)]
    original_sigma = sem.components(scaled)[6]
    components = sem.components(scaled)
    negatives = [{"parameter": label, "value": raw[i]}
                 for i, label in enumerate(sem.PARAMETER_LABELS) if i >= 16 and raw[i] < 0]
    original_score = sem.Objective(sample).evaluate(scaled)
    return {"termination": fit["termination"], "iterations": fit["iterations"],
            "F": fit["F_ml"], "gradient": fit["maximum_scaled_gradient"],
            "finite_original_parameters": True, "Var_EQ": raw[17],
            "original_parameter_score_maximum": max(map(abs, original_score[1])),
            "same_model_sigma_error": max(abs(sigma[i][j] - original_sigma[i][j])
                                          for i in range(16) for j in range(16)),
            "negative_variances": negatives, "raw_original_parameters": raw}


def main():
    rows, _ = check.load_diagnostic_data()
    sample = sem.covariance(rows, 39)
    old = json.loads((ROOT / "NDVI_sem_sensitivity_work/independent_ml_baseline_checks.json").read_text(encoding="utf-8"))
    base = next(r for r in old["models"] if r["covariance_divisor"] == 39)
    reduced_initial = original_to_reduced(base["raw_parameters"])
    rng = random.Random(20261111)
    multistart = []
    for attempt in range(4):
        initial = reduced_initial[:]
        if attempt:
            for k in range(16):
                scale = .15 if k == 9 else sem.SCALES[k]
                initial[k] += .15 * scale * rng.uniform(-1, 1)
            for k in range(16, 21):
                initial[k] *= rng.uniform(.85, 1.15)
        objective = ReducedObjective(sample)
        fit = minimize(objective, initial, maximum=600)
        summary = summarize_reduced_fit(fit, sample)
        summary["start"] = attempt
        multistart.append(summary)
        print(json.dumps({"same_model_start": attempt, "F": summary["F"],
                          "termination": summary["termination"], "Var_EQ": summary.get("Var_EQ")}), flush=True)
    positive = []
    for attempt in range(3):
        objective = PositiveVarianceObjective(sample)
        initial = objective.transform(base["raw_parameters"])
        if attempt:
            for k in range(36):
                initial[k] += .1 * rng.uniform(-1, 1)
        fit = minimize(objective, initial, maximum=1000)
        original_raw = objective.original_raw(fit["raw_parameters_reduced"])
        scaled = [v / s for v, s in zip(original_raw, sem.SCALES)]
        f, gradient = sem.Objective(sample).evaluate(scaled)
        raw_score = [gradient[i] / sem.SCALES[i] for i in range(36)]
        active = [i for i in range(16, 36) if original_raw[i] < 1e-8 * sem.SCALES[i]]
        inactive = [i for i in range(36) if i not in active]
        kkt = {"inactive_score_maximum_scaled": max(abs(gradient[i]) for i in inactive),
               "active_bounds_raw_scores": [{"parameter": sem.PARAMETER_LABELS[i],
                                             "variance": original_raw[i], "raw_score": raw_score[i]}
                                            for i in active],
               "all_active_scores_nonnegative_with_tolerance": all(raw_score[i] >= -1e-6 for i in active)}
        record = {"start": attempt, "termination": fit["termination"],
                  "iterations": fit["iterations"], "F": f,
                  "log_coordinate_gradient": fit["maximum_scaled_gradient"],
                  "raw_parameters": original_raw, "boundary_KKT": kkt,
                  "extra_nonnegative_variance_bounds_added": True,
                  "not_source_Amos_unrestricted_solution": True}
        positive.append(record)
        print(json.dumps({"positive_variance_diagnostic_start": attempt, "F": f,
                          "termination": fit["termination"], "active_variance_bounds": len(active),
                          "inactive_score_maximum": kkt["inactive_score_maximum_scaled"]}), flush=True)
    result = {"independent_not_Amos_output": True, "no_original_input_modified": True,
              "equal_weight_four_park_composite_is_provisional_source_assumption": True,
              "same_model_multistart": multistart,
              "same_model_multistart_F_range": max(r["F"] for r in multistart) - min(r["F"] for r in multistart),
              "positive_variance_boundary_diagnostics": positive,
              "positive_bounds_not_present_in_original_model": True}
    (Path(__file__).resolve().parent / "composite_multistart_and_boundary_diagnostics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"same_model_F_range": result["same_model_multistart_F_range"],
                      "all_same_model_EQ_negative": all(r.get("Var_EQ", 1) < 0 for r in multistart),
                      "positive_diagnostic_F_values": [r["F"] for r in positive]}), flush=True)


if __name__ == "__main__":
    main()
