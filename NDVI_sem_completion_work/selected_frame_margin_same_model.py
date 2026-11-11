"""Original fixed SEM diagnostic for the root-selected frame-margin sources.

Source selection precedes SEM and is not performed by this code. All 39 inside
and outside zonal means are separately standardized with sample SD (n-1=38).
Original GIS/SAV/XLSX/AMW files are read-only. This is not native Amos output.
"""

import csv
import json
import math
from pathlib import Path
import random

import check_composite_ml as engine
from check_composite_ml import ROOT, sem, ReducedObjective, original_to_reduced, reduced_to_original, minimize

SOURCES = {9: "NDVI_nagoya.tif", 18: "NDVI_nara.tif",
           28: "NDVI_nara.tif", 32: "NDVI_fukushima_up.tif"}
OUT = Path(__file__).resolve().parent


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def write_csv(path, header, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def load_selected_data():
    scan = json.loads((ROOT / "NDVI_mean_work/regional_mean_source_scan.json").read_text(encoding="utf-8"))
    means = []
    for park in scan["parks"]:
        pid = park["ParkID"]
        if pid in SOURCES:
            candidates = [c for c in park["candidates"] if c["source_raster"] == SOURCES[pid]]
            assert len(candidates) == 1
            chosen = candidates[0]
        else:
            chosen = park["selected"]
            assert chosen is not None
        assert chosen["full_extent"]
        assert all(chosen[s]["valid_n"] > 0 and chosen[s]["out_of_range_n"] == 0
                   for s in ("inside", "outside"))
        means.append({"ParkID": pid, "source_raster": chosen["source_raster"],
                      "inside_mean": chosen["inside"]["mean"],
                      "outside_mean": chosen["outside"]["mean"],
                      "inside_valid_n": chosen["inside"]["valid_n"],
                      "outside_valid_n": chosen["outside"]["valid_n"]})
    assert [row["ParkID"] for row in means] == list(range(1, 40))
    standardization = {}
    for side in ("inside", "outside"):
        values = [row[side + "_mean"] for row in means]
        average = math.fsum(values) / 39
        sample_sd = math.sqrt(math.fsum((v - average) ** 2 for v in values) / 38)
        for row, value in zip(means, values):
            row["z_" + side] = (value - average) / sample_sd
        zs = [row["z_" + side] for row in means]
        standardization[side] = {"mean_of_39_zonal_means": average, "sample_SD": sample_sd,
                                 "SD_denominator": 38,
                                 "mean_of_Z": math.fsum(zs) / 39,
                                 "sample_SD_of_Z": math.sqrt(math.fsum(z * z for z in zs) / 38)}
        assert abs(standardization[side]["mean_of_Z"]) < 1e-14
        assert abs(standardization[side]["sample_SD_of_Z"] - 1) < 1e-14
    original = sem.load_original()
    rows = [row[:] for row in original]
    for row, ndvi in zip(rows, means):
        row[5] = ndvi["z_outside"]
        row[6] = ndvi["z_inside"]
    assert all(row[i] == old[i] for row, old in zip(rows, original)
               for i in range(16) if i not in (5, 6))
    return rows, means, standardization


def observed_hessian_information(original_raw, sample, step_relative):
    objective = sem.Objective(sample)
    x = [v / s for v, s in zip(original_raw, sem.SCALES)]
    hessian_columns = []
    for k in range(36):
        step = step_relative * max(1, abs(x[k]))
        plus, minus = x[:], x[:]
        plus[k] += step
        minus[k] -= step
        gp, gm = objective.evaluate(plus)[1], objective.evaluate(minus)[1]
        if gp is None or gm is None:
            raise ValueError("Hessian perturbation covariance not SPD")
        hessian_columns.append([(a - b) / (2 * step) for a, b in zip(gp, gm)])
    unsym = [[hessian_columns[j][i] for j in range(36)] for i in range(36)]
    asymmetry = max(abs(unsym[i][j] - unsym[j][i]) for i in range(36) for j in range(36))
    hessian = [[19 * (unsym[i][j] + unsym[j][i]) / 2 for j in range(36)] for i in range(36)]
    inverse, _ = sem.inverse_spd(hessian)
    ses = [sem.SCALES[k] * math.sqrt(inverse[k][k]) for k in range(36)]
    return {"method": "Observed negative-log-likelihood Hessian, multiplier38/2",
            "relative_step": step_relative, "maximum_scaled_F_Hessian_asymmetry": asymmetry,
            "positive_definite": True, "SE_raw_parameters": ses,
            "hessian_scaled_parameters": hessian}


def main():
    rows, means, standardization = load_selected_data()
    sample = sem.covariance(rows, 39)
    old_record = json.loads((ROOT / "NDVI_sem_sensitivity_work/independent_ml_baseline_checks.json").read_text(encoding="utf-8"))
    baseline = next(r for r in old_record["models"] if r["covariance_divisor"] == 39)
    initial = original_to_reduced(baseline["raw_parameters"])
    initial_objective = ReducedObjective(sample)
    initial_gradient_check = engine.gradient_check(initial_objective, initial)
    assert initial_gradient_check["maximum_relative_gradient_error"] < 1e-6
    rng = random.Random(20261112)
    attempts = []
    for start in range(3):
        guess = initial[:]
        if start:
            for k in range(16):
                scale = .15 if k == 9 else sem.SCALES[k]
                guess[k] += .15 * scale * rng.uniform(-1, 1)
            for k in range(16, 21):
                guess[k] *= rng.uniform(.85, 1.15)
        objective = ReducedObjective(sample)
        fit = minimize(objective, guess, maximum=1000)
        fit["start"] = start
        attempts.append(fit)
        print(json.dumps({"selected_source_start": start, "F": fit["F_ml"],
                          "termination": fit["termination"],
                          "Var_EQ": fit["raw_parameters_reduced"][17]}), flush=True)
    best = min(attempts, key=lambda r: r["F_ml"])
    original_raw = reduced_to_original(best["raw_parameters_reduced"])
    assert original_raw is not None
    scaled = [v / s for v, s in zip(original_raw, sem.SCALES)]
    sigma_original = sem.components(scaled)[6]
    sigma_reduced = engine.reduced_sigma(best["raw_parameters_reduced"])[0]
    covariance_error = max(abs(sigma_original[i][j] - sigma_reduced[i][j])
                           for i in range(16) for j in range(16))
    assert covariance_error < 1e-10
    original_objective = sem.Objective(sample)
    actual_f, original_gradient = original_objective.evaluate(scaled)
    assert abs(actual_f - best["F_ml"]) < 1e-10
    final_gradient_check = engine.gradient_check(ReducedObjective(sample), best["raw_parameters_reduced"])
    assert final_gradient_check["maximum_relative_gradient_error"] < 1e-6
    fit_original = {"raw_parameters": original_raw, "scaled_parameters": scaled,
                    "F_ml": actual_f, "max_abs_scaled_gradient": max(map(abs, original_gradient)),
                    "iterations": best["iterations"], "termination": best["termination"]}
    summary = sem.fit_summary(fit_original, sample, 38)
    summary["covariance_divisor"] = 39
    information = {"SE_inference_valid_for_manuscript": False,
                   "reason": "Model admissibility must be checked independently of a positive Hessian"}
    expected_ses, observed_ses = [None] * 36, [None] * 36
    try:
        observed1 = observed_hessian_information(original_raw, sample, 1e-5)
        observed2 = observed_hessian_information(original_raw, sample, 2e-6)
        relative_SE_difference = max(abs(a - b) / max(abs(a), abs(b), 1e-12)
                                     for a, b in zip(observed1["SE_raw_parameters"], observed2["SE_raw_parameters"]))
        assert relative_SE_difference < 1e-4
        expected = sem.expected_information(fit_original, sample, 38)
        expected_ses = [r["SE"] for r in expected["free_parameters"]]
        observed_ses = observed2["SE_raw_parameters"]
        information.update({"observed_Hessian_positive_definite": True,
                            "expected_information_positive_definite": True,
                            "maximum_observed_Hessian_SE_relative_step_difference": relative_SE_difference,
                            "expected_normal_information": expected,
                            "observed_Hessian_step_checks": [observed1, observed2]})
    except (ValueError, AssertionError, OverflowError) as error:
        information.update({"SE_not_reported": True, "curvature_check_error": str(error)})
    model = json.loads((ROOT / "NDVI_sem_sensitivity_work/sem_model_specification.json").read_text(encoding="utf-8"))
    index_map = {(sem.LATENTS[source], sem.LATENTS[target]): k
                 for k, (target, source) in enumerate(sem.STRUCTURAL)}
    index_map.update({(sem.LATENTS[source], f"O{target + 1:02d}"): k
                      for k, (target, source) in enumerate(sem.MEASUREMENT, 4)})
    regression_rows = []
    for r in model["regressions"]:
        key = (r["from"], r["to"])
        k = index_map.get(key)
        estimate = r["B"] if r["fixed"] else original_raw[k]
        regression_rows.append([r["from"], r["to"], r.get("parameter"), estimate,
                                None if r["fixed"] else expected_ses[k],
                                None if r["fixed"] else observed_ses[k],
                                r["fixed"], "DIAGNOSTIC_INADMISSIBLE_MODEL"
                                if not summary["solution_admissible_nonnegative_variances"] else "DIAGNOSTIC_NOT_AMOS"])
    variance_rows = []
    q = sem.components(scaled)[3]
    theta = sem.components(scaled)[4]
    for i, label in enumerate(["SN", "UA", "EQ", "dENV", "dBAL", "dUSR"]):
        k = None if i == 0 else 15 + i
        variance_rows.append([label, "latent_exogenous" if i < 3 else "latent_disturbance", q[i],
                              None if k is None else expected_ses[k],
                              None if k is None else observed_ses[k], i == 0,
                              "NEGATIVE_INADMISSIBLE" if q[i] < 0 else "NONNEGATIVE"])
    for i, observed in enumerate(model["observed"]):
        k = None if i == 4 else 21 + sem.FREE_THETA.index(i)
        variance_rows.append([observed["error"], observed["sav"], theta[i],
                              None if k is None else expected_ses[k],
                              None if k is None else observed_ses[k], i == 4,
                              "NEGATIVE_INADMISSIBLE" if theta[i] < 0 else "NONNEGATIVE"])
    mean_headers = ["ParkID", "source_raster", "inside_mean", "outside_mean",
                    "inside_valid_n", "outside_valid_n", "z_inside", "z_outside"]
    write_csv(OUT / "selected_frame_margin_ndvi_means_and_z.csv", mean_headers,
              [[r[field] for field in mean_headers] for r in means])
    write_csv(OUT / "selected_frame_margin_same_model_regressions.csv",
              ["from", "to", "original_parameter", "B", "SE_expected_normal_diagnostic",
               "SE_observed_Hessian_diagnostic", "fixed", "status"], regression_rows)
    write_csv(OUT / "selected_frame_margin_same_model_variances.csv",
              ["parameter", "target_or_kind", "variance", "SE_expected_normal_diagnostic",
               "SE_observed_Hessian_diagnostic", "fixed", "admissibility"], variance_rows)
    indices = summary["fit_indices"]
    write_csv(OUT / "selected_frame_margin_same_model_fit_indices.csv", list(indices) + ["status"],
              [[indices[k] for k in indices] + ["DIAGNOSTIC_INADMISSIBLE_MODEL"
                if not summary["solution_admissible_nonnegative_variances"] else "DIAGNOSTIC_NOT_AMOS"]])
    write_json(OUT / "selected_frame_margin_same_model_fit.json",
               {"dataset_source_choice": "Root-selected TIFF frame-margin rule, selected before SEM",
                "four_selected_sources": SOURCES, "not_composite": True,
                "no_other_park_mean_imputation": True, "original_14_variables_unchanged": True,
                "independent_not_native_Amos": True, "original_model_constraints_unchanged": True,
                "standardization": standardization, "cases": 39,
                "means_and_Z": means, "observed_order": sem.OBSERVED,
                "input_matrix_original_model_order": rows, "sample_covariance_divisor39": sample,
                "starts": attempts, "multistart_F_range": max(f["F_ml"] for f in attempts) - min(f["F_ml"] for f in attempts),
                "fit_diagnostic_not_publication_result": summary,
                "manuscript_reportable_solution": summary["solution_admissible_nonnegative_variances"]
                    and best["termination"] == "gradient_converged",
                "formal_standardized_result_figure_generated": False})
    write_json(OUT / "selected_frame_margin_same_model_QA.json",
               {"initial_gradient_check": initial_gradient_check,
                "final_reduced_gradient_check": final_gradient_check,
                "original_coordinate_scaled_gradient_maximum": max(map(abs, original_gradient)),
                "original_reduced_covariance_maximum_error": covariance_error,
                "original_reduced_F_difference": actual_f - best["F_ml"],
                "positive_definite_model_covariance": True,
                "information_and_Hessian_checks": information,
                "negative_variance_parameters": summary["negative_variance_parameters"],
                "original_inputs_modified": False})
    print(json.dumps({"selected_sources": SOURCES, "F": actual_f,
                      "multistart_F_range": max(f["F_ml"] for f in attempts) - min(f["F_ml"] for f in attempts),
                      "negative_variances": summary["negative_variance_parameters"],
                      "original_scaled_gradient": max(map(abs, original_gradient)),
                      "Hessian_positive_and_SE_checked": information.get("observed_Hessian_positive_definite", False)},
                     ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
