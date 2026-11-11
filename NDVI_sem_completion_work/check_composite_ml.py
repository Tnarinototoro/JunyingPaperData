"""Independent same-model ML checks for provisional four-park composites.

The covariance reparameterization is algebraically equivalent to the original
model when Var(EQ) != 0. It exposes the non-finite-loading limit at Var(EQ)=0;
it never releases a fixed path, adds a covariance, or edits research inputs.
This is not IBM SPSS Amos output. Source choice belongs to the root agent.
"""

import csv
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "NDVI_sem_sensitivity_work"))
import sem_covariance_ml as sem

FREE_DIAG = sem.FREE_THETA


def load_diagnostic_data():
    scan = json.loads((ROOT / "NDVI_mean_work/regional_mean_source_scan.json").read_text(encoding="utf-8"))
    means = []
    for item in scan["parks"]:
        if item["selected"]:
            candidates = [item["selected"]]
        else:
            candidates = [c for c in item["candidates"] if c["full_extent"] and all(
                c[s]["valid_n"] > 0 and c[s]["out_of_range_n"] == 0 for s in ("inside", "outside"))]
            assert len(candidates) == 2
        means.append({"ParkID": item["ParkID"],
                      "inside_mean": math.fsum(c["inside"]["mean"] for c in candidates) / len(candidates),
                      "outside_mean": math.fsum(c["outside"]["mean"] for c in candidates) / len(candidates),
                      "sources": [c["source_raster"] for c in candidates]})
    assert [m["ParkID"] for m in means] == list(range(1, 40))
    for side in ("inside", "outside"):
        values = [m[side + "_mean"] for m in means]
        avg = math.fsum(values) / 39
        sd = math.sqrt(math.fsum((v - avg) ** 2 for v in values) / 38)
        for item, value in zip(means, values):
            item["z_" + side] = (value - avg) / sd
    rows = sem.load_original()
    for row, item in zip(rows, means):
        row[5] = item["z_outside"]
        row[6] = item["z_inside"]
    return rows, means


def reduced_sigma(raw):
    # raw[9] is h = loading(O06,EQ) * Var(EQ), not loading itself.
    transform = [[float(i == j) for j in range(6)] for i in range(6)]
    for value, (target, source) in zip(raw[:4], sem.STRUCTURAL):
        transform[target][source] = value
    transform[4][2] = 1.0
    loadings = [[0.0] * 6 for _ in range(16)]
    for target, source in sem.FIXED_MEASUREMENT:
        loadings[target][source] = 1.0
    for k, (target, source) in enumerate(sem.MEASUREMENT, 4):
        if k != 9:
            loadings[target][source] = raw[k]
    q = [1.0] + raw[16:21]
    g = sem.matmul(loadings, transform)
    h = raw[9]
    sigma = [[math.fsum(g[i][k] * q[k] * g[j][k] for k in range(6))
              + (h * g[j][2] if i == 5 else h * g[i][2] if j == 5 else 0.0)
              for j in range(16)] for i in range(16)]
    sigma[4][4] += .120
    for value, i in zip(raw[21:], FREE_DIAG):
        sigma[i][i] = value
    return sigma, transform, loadings, q, g


class ReducedObjective:
    def __init__(self, sample):
        self.sample = sample
        self.logdet_sample = sem.inverse_spd(sample)[1]
        self.evaluations = 0
        self.scales = sem.SCALES[:]
        self.scales[9] = .15
        self.scales[17] = .05
        for k, i in enumerate(FREE_DIAG, 21):
            self.scales[k] = max(.03, sample[i][i])

    def evaluate(self, scaled, gradient=True):
        self.evaluations += 1
        raw = [x * scale for x, scale in zip(scaled, self.scales)]
        try:
            sigma, transform, loadings, q, g = reduced_sigma(raw)
            inverse, logdet = sem.inverse_spd(sigma)
        except (ValueError, OverflowError, ZeroDivisionError):
            return math.inf, None
        f = logdet + math.fsum(self.sample[i][j] * inverse[i][j] for i in range(16)
                              for j in range(16)) - self.logdet_sample - 16
        if not gradient:
            return f, None
        isinv = sem.matmul(sem.matmul(inverse, self.sample), inverse)
        hessian_sigma = [[inverse[i][j] - isinv[i][j] for j in range(16)] for i in range(16)]
        diag_derivatives = [hessian_sigma[i][i] for i in FREE_DIAG]
        for i in FREE_DIAG:
            hessian_sigma[i][i] = 0.0
        hg = sem.matmul(hessian_sigma, g)
        k = [[q[j] * hg[i][j] + (raw[9] * hessian_sigma[i][5] if j == 2 else 0.0)
              for j in range(6)] for i in range(16)]
        derivatives = [2 * math.fsum(k[i][source] * loadings[i][target] for i in range(16))
                       for target, source in sem.STRUCTURAL]
        derivatives.extend(2 * sem.dot(k[target], transform[source])
                           if index != 9 else 2 * hg[5][2]
                           for index, (target, source) in enumerate(sem.MEASUREMENT, 4))
        derivatives.extend(math.fsum(hg[i][j] * g[i][j] for i in range(16)) for j in range(1, 6))
        derivatives.extend(diag_derivatives)
        assert len(derivatives) == 36
        return f, [derivative * scale for derivative, scale in zip(derivatives, self.scales)]


def original_to_reduced(original):
    sigma = sem.components([v / s for v, s in zip(original, sem.SCALES)])[6]
    raw = original[:]
    raw[9] *= raw[17]
    raw[21:] = [sigma[i][i] for i in FREE_DIAG]
    return raw


def reduced_to_original(reduced):
    if abs(reduced[17]) < 1e-12:
        return None
    raw = reduced[:]
    raw[9] /= raw[17]
    trial = raw[:]
    trial[21:] = [0.0] * len(FREE_DIAG)
    covariance_no_theta = sem.components([v / s for v, s in zip(trial, sem.SCALES)])[6]
    raw[21:] = [reduced[21 + k] - covariance_no_theta[i][i] for k, i in enumerate(FREE_DIAG)]
    return raw


def gradient_check(objective, raw):
    scaled = [v / s for v, s in zip(raw, objective.scales)]
    f, gradient = objective.evaluate(scaled)
    errors = []
    for k in range(36):
        step = 1e-6 * max(1, abs(scaled[k]))
        plus, minus = scaled[:], scaled[:]
        plus[k] += step
        minus[k] -= step
        difference = (objective.evaluate(plus, False)[0] - objective.evaluate(minus, False)[0]) / (2 * step)
        errors.append(abs(difference - gradient[k]) / max(1, abs(difference), abs(gradient[k])))
    return {"F": f, "maximum_relative_gradient_error": max(errors)}


def minimize(objective, initial, maximum=2000):
    x = [v / s for v, s in zip(initial, objective.scales)]
    f, gradient = objective.evaluate(x)
    if not math.isfinite(f):
        raise ValueError("Reduced starting covariance not positive definite")
    ih = [[float(i == j) for j in range(36)] for i in range(36)]
    status = "iteration_limit"
    trace = []
    start = time.perf_counter()
    for iteration in range(maximum):
        gmax = max(map(abs, gradient))
        if gmax < 3e-7:
            status = "gradient_converged"
            break
        direction = [-sem.dot(row, gradient) for row in ih]
        slope = sem.dot(direction, gradient)
        if not math.isfinite(slope) or slope >= -1e-16:
            ih = [[float(i == j) for j in range(36)] for i in range(36)]
            direction = [-v for v in gradient]
            slope = -sem.dot(gradient, gradient)
        step = 1.0
        accepted = False
        for _ in range(50):
            trial = [a + step * b for a, b in zip(x, direction)]
            trial_f = objective.evaluate(trial, False)[0]
            if math.isfinite(trial_f) and trial_f <= f + 1e-4 * step * slope:
                accepted = True
                break
            step *= .5
        if not accepted:
            status = "line_search_stopped"
            break
        nf, ng = objective.evaluate(trial)
        s = [a - b for a, b in zip(trial, x)]
        y = [a - b for a, b in zip(ng, gradient)]
        sy = sem.dot(s, y)
        if sy > 1e-14 * max(1, math.sqrt(sem.dot(s, s) * sem.dot(y, y))):
            hy = [sem.dot(row, y) for row in ih]
            rho = 1 / sy
            factor = (1 + sem.dot(y, hy) * rho) * rho
            ih = [[ih[i][j] + factor * s[i] * s[j] - rho * (hy[i] * s[j] + s[i] * hy[j])
                   for j in range(36)] for i in range(36)]
        x, f, gradient = trial, nf, ng
        if iteration % 100 == 0:
            trace.append({"iteration": iteration, "F": f, "max_scaled_gradient": max(map(abs, gradient))})
            print(json.dumps(trace[-1]), flush=True)
    return {"raw_parameters_reduced": [v * scale for v, scale in zip(x, objective.scales)],
            "F_ml": f, "iterations": iteration, "termination": status,
            "maximum_scaled_gradient": max(map(abs, gradient)), "trace": trace,
            "elapsed_seconds": time.perf_counter() - start}


def main():
    out = Path(__file__).resolve().parent
    rows, means = load_diagnostic_data()
    sample = sem.covariance(rows, 39)
    old_record = json.loads((ROOT / "NDVI_sem_sensitivity_work/independent_ml_baseline_checks.json").read_text(encoding="utf-8"))
    old_fit = next(fit for fit in old_record["models"] if fit["covariance_divisor"] == 39)
    initial = original_to_reduced(old_fit["raw_parameters"])
    objective = ReducedObjective(sample)
    gradient = gradient_check(objective, initial)
    assert gradient["maximum_relative_gradient_error"] < 1e-6
    original_sigma = sem.components(old_fit["scaled_parameters"])[6]
    reduced_cov = reduced_sigma(initial)[0]
    equivalence_error = max(abs(original_sigma[i][j] - reduced_cov[i][j]) for i in range(16) for j in range(16))
    assert equivalence_error < 1e-12
    original_objective = sem.Objective(sample)
    f_original = original_objective.evaluate(old_fit["scaled_parameters"])[0]
    assert abs(f_original - gradient["F"]) < 1e-12
    fit = minimize(objective, initial)
    original = reduced_to_original(fit["raw_parameters_reduced"])
    if original is not None:
        scaled = [v / s for v, s in zip(original, sem.SCALES)]
        sigma_o = sem.components(scaled)[6]
        sigma_r = reduced_sigma(fit["raw_parameters_reduced"])[0]
        original_check = sem.Objective(sample).evaluate(scaled)
        fit["same_model_original_F_difference"] = original_check[0] - fit["F_ml"]
        fit["same_model_sigma_max_difference"] = max(abs(sigma_o[i][j] - sigma_r[i][j]) for i in range(16) for j in range(16))
        fit["original_parameterization_max_scaled_gradient"] = max(map(abs, original_check[1]))
        original_fit = {"raw_parameters": original, "scaled_parameters": scaled,
                        "F_ml": fit["F_ml"], "max_abs_scaled_gradient": fit["maximum_scaled_gradient"],
                        "iterations": fit["iterations"], "termination": fit["termination"]}
        fit["original_model_diagnostics"] = sem.fit_summary(original_fit, sample, 38)
    fit["gradient_check_at_final_reduced"] = gradient_check(objective, fit["raw_parameters_reduced"])
    result = {"purpose": "Provisional equal-weight two-source four-park NDVI ML diagnostic; not a final source choice",
              "source_grid_mask_equality_to_be_confirmed_by_root": True,
              "independent_not_Amos_output": True,
              "no_model_constraints_released": True, "original_files_modified": False,
              "gradient_check_initial": gradient, "original_covariance_equivalence_max_error": equivalence_error,
              "observed_count": 16, "cases": 39, "covariance_divisor": 39, "likelihood_multiplier": 38,
              "means_and_z_for_check": means, "fit": fit}
    (out / "composite_same_model_ml_diagnostic.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    brief = {"termination": fit["termination"], "iterations": fit["iterations"], "F": fit["F_ml"],
             "gradient": fit["maximum_scaled_gradient"],
             "Var_EQ_reduced": fit["raw_parameters_reduced"][17],
             "negative_variances": fit.get("original_model_diagnostics", {}).get("negative_variance_parameters"),
             "same_model_sigma_error": fit.get("same_model_sigma_max_difference")}
    print(json.dumps(brief, ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
