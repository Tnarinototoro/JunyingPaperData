"""Independent covariance-only ML reconstruction of the supplied fixed SEM.

This is NOT IBM SPSS Amos output. The original-data reconstruction must pass
comparison with the supplied Amos estimates before scenario fits are used.
No input, original model, or manuscript is modified. Free variances are not
silently bounded to zero; inadmissible solutions must be explicitly reported.
"""

import argparse
import csv
import json
import math
from pathlib import Path
import random
import sys
import time


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.paper15_work'))
from read_numeric_sav import decode_numeric_matrix

OBSERVED = ['S3_1', 'S3_2', 'S7', 'S8_1', 'S8_2',
            'Z外部NDVI平均値', 'Z内部NDVI平均値', 'S2_1', 'S6', 'S2_3',
            'S2_2', 'S5_1', 'S5_2', 'S4_1', 'S4_2', 'S9']
LATENTS = ['SN', 'UA', 'EQ', 'ENV', 'BAL', 'USR']
# Structural coefficient order: target latent, independent source column.
STRUCTURAL = [(3, 0), (3, 2), (4, 0), (5, 0)]
STRUCTURAL_LABELS = ['SN -> ENV', 'EQ -> ENV', 'SN -> BAL', 'SN -> USR']
MEASUREMENT = [(0, 0), (1, 0), (2, 0), (2, 1), (5, 1), (5, 2),
               (9, 3), (10, 3), (10, 4), (13, 5), (13, 1), (15, 5)]
FIXED_MEASUREMENT = [(3, 1), (4, 1), (6, 2), (7, 3), (8, 3),
                     (11, 4), (12, 4), (14, 5)]
BASE_REGRESSIONS = [.136, -.587, .218, -.124, .137, .073, .074,
                    .327, .555, 2.893, .570, .586, .409, .514, -.455, .058]
BASE_Q = [1.0, .578, .020, .001, .046, .456]
BASE_THETA = [.015, .014, .053, .241, .120, .654, .929,
              .022, .061, .153, .017, .567, .165, .356, .257, .029]
FREE_THETA = [i for i in range(16) if i != 4]
PARAMETER_LABELS = (STRUCTURAL_LABELS
    + [f'{LATENTS[s]} -> O{r + 1:02d}' for r, s in MEASUREMENT]
    + ['variance ' + label for label in ['UA', 'EQ', 'dENV', 'dBAL', 'dUSR']]
    + [f'error variance O{i + 1:02d}' for i in FREE_THETA])
BASE_RAW = BASE_REGRESSIONS + BASE_Q[1:] + [BASE_THETA[i] for i in FREE_THETA]
SCALES = ([max(.15, abs(v)) for v in BASE_REGRESSIONS]
          + [max(.03, v) for v in BASE_Q[1:]]
          + [max(.03, BASE_THETA[i]) for i in FREE_THETA])
assert len(BASE_RAW) == len(SCALES) == len(PARAMETER_LABELS) == 36


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b))


def matmul(a, b):
    bt = list(zip(*b))
    return [[dot(row, col) for col in bt] for row in a]


def inverse_spd(matrix):
    n = len(matrix)
    lower = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            value = matrix[i][j] - math.fsum(lower[i][k] * lower[j][k] for k in range(j))
            if i == j:
                if value <= 1e-14 or not math.isfinite(value):
                    raise ValueError('Covariance is not positive definite')
                lower[i][j] = math.sqrt(value)
            else:
                lower[i][j] = value / lower[j][j]
    invlower = [[0.0] * n for _ in range(n)]
    for col in range(n):
        for i in range(n):
            numerator = (1.0 if i == col else 0.0) - math.fsum(
                lower[i][k] * invlower[k][col] for k in range(i))
            invlower[i][col] = numerator / lower[i][i]
    inverse = matmul(list(map(list, zip(*invlower))), invlower)
    logdet = 2 * math.fsum(math.log(lower[i][i]) for i in range(n))
    return inverse, logdet


def covariance(rows, denominator):
    p = len(rows[0])
    means = [math.fsum(row[i] for row in rows) / len(rows) for i in range(p)]
    return [[math.fsum((row[i] - means[i]) * (row[j] - means[j]) for row in rows)
             / denominator for j in range(p)] for i in range(p)]


def components(scaled):
    raw = [s * v for s, v in zip(SCALES, scaled)]
    transform = [[float(i == j) for j in range(6)] for i in range(6)]
    for value, (target, source) in zip(raw[:4], STRUCTURAL):
        transform[target][source] = value
    transform[4][2] = 1.0  # EQ -> BAL is fixed, not estimated.
    loadings = [[0.0] * 6 for _ in range(16)]
    for target, source in FIXED_MEASUREMENT:
        loadings[target][source] = 1.0
    for value, (target, source) in zip(raw[4:16], MEASUREMENT):
        loadings[target][source] = value
    q = [1.0] + raw[16:21]
    theta = [0.0] * 16
    theta[4] = .120
    for value, target in zip(raw[21:], FREE_THETA):
        theta[target] = value
    propagated = matmul(loadings, transform)
    sigma = [[math.fsum(propagated[i][k] * q[k] * propagated[j][k] for k in range(6))
              + (theta[i] if i == j else 0.0) for j in range(16)] for i in range(16)]
    latent_cov = [[math.fsum(transform[i][k] * q[k] * transform[j][k] for k in range(6))
                   for j in range(6)] for i in range(6)]
    return raw, transform, loadings, q, theta, propagated, sigma, latent_cov


class Objective:
    def __init__(self, sample_covariance):
        self.sample = sample_covariance
        _, self.logdet_sample = inverse_spd(self.sample)
        self.evaluations = 0

    def evaluate(self, scaled, gradient=True):
        self.evaluations += 1
        try:
            raw, transform, loadings, q, theta, propagated, sigma, latent_cov = components(scaled)
            inv, logdet = inverse_spd(sigma)
        except (ValueError, OverflowError, ZeroDivisionError):
            return math.inf, None
        value = logdet + math.fsum(self.sample[i][j] * inv[i][j]
                                  for i in range(16) for j in range(16)) - self.logdet_sample - 16
        if not gradient:
            return value, None
        inv_s_inv = matmul(matmul(inv, self.sample), inv)
        h = [[inv[i][j] - inv_s_inv[i][j] for j in range(16)] for i in range(16)]
        h_propagated = matmul(h, propagated)
        dg = [[2 * h_propagated[i][k] * q[k] for k in range(6)] for i in range(16)]
        derivatives = [math.fsum(dg[i][source] * loadings[i][target] for i in range(16))
                       for target, source in STRUCTURAL]
        derivatives += [dot(dg[target], transform[source]) for target, source in MEASUREMENT]
        derivatives += [math.fsum(h_propagated[i][k] * propagated[i][k] for i in range(16))
                        for k in range(1, 6)]
        derivatives += [h[i][i] for i in FREE_THETA]
        return value, [d * s for d, s in zip(derivatives, SCALES)]


def gradient_check(objective, scaled):
    _, gradient = objective.evaluate(scaled)
    errors = []
    for i in range(36):
        step = 1e-5 * max(1, abs(scaled[i]))
        plus, minus = scaled[:], scaled[:]
        plus[i] += step
        minus[i] -= step
        fp = objective.evaluate(plus, gradient=False)[0]
        fm = objective.evaluate(minus, gradient=False)[0]
        numeric = (fp - fm) / (2 * step)
        errors.append(abs(numeric - gradient[i]) / max(1, abs(numeric), abs(gradient[i])))
    return {'maximum_relative_gradient_difference': max(errors),
            'all_36_parameters_checked': True, 'step_relative': 1e-5}


def minimize(objective, initial_raw, max_iterations=1000):
    x = [value / scale for value, scale in zip(initial_raw, SCALES)]
    f, g = objective.evaluate(x)
    if not math.isfinite(f):
        raise ValueError('Starting model covariance is not positive definite')
    inverse_hessian = [[float(i == j) for j in range(36)] for i in range(36)]
    iterations = 0
    status = 'iteration_limit'
    for iteration in range(max_iterations):
        iterations = iteration
        gmax = max(abs(v) for v in g)
        if gmax < 3e-7:
            status = 'gradient_converged'
            break
        direction = [-dot(row, g) for row in inverse_hessian]
        slope = dot(direction, g)
        if not math.isfinite(slope) or slope >= -1e-16:
            inverse_hessian = [[float(i == j) for j in range(36)] for i in range(36)]
            direction = [-v for v in g]
            slope = -dot(g, g)
        step = 1.0
        accepted = False
        for _ in range(45):
            trial = [a + step * b for a, b in zip(x, direction)]
            trial_f = objective.evaluate(trial, gradient=False)[0]
            if math.isfinite(trial_f) and trial_f <= f + 1e-4 * step * slope:
                accepted = True
                break
            step *= .5
        if not accepted:
            status = 'line_search_stopped'
            break
        new_f, new_g = objective.evaluate(trial)
        s = [a - b for a, b in zip(trial, x)]
        y = [a - b for a, b in zip(new_g, g)]
        sy = dot(s, y)
        if sy > 1e-14 * max(1, math.sqrt(dot(s, s) * dot(y, y))):
            hy = [dot(row, y) for row in inverse_hessian]
            rho = 1 / sy
            factor = (1 + dot(y, hy) * rho) * rho
            inverse_hessian = [[inverse_hessian[i][j] + factor * s[i] * s[j]
                                - rho * (hy[i] * s[j] + s[i] * hy[j])
                                for j in range(36)] for i in range(36)]
        x, f, g = trial, new_f, new_g
        if iteration % 100 == 0:
            print(json.dumps({'iteration': iteration, 'F_ml': f,
                              'max_abs_scaled_gradient': max(abs(v) for v in g)}), flush=True)
    return {'raw_parameters': [s * v for s, v in zip(SCALES, x)],
            'scaled_parameters': x, 'F_ml': f, 'max_abs_scaled_gradient': max(abs(v) for v in g),
            'iterations': iterations, 'termination': status,
            'function_evaluations': objective.evaluations}


def fit_summary(fit, sample, multiplier, n=39):
    raw, transform, loadings, q, theta, propagated, sigma, latent_cov = components(fit['scaled_parameters'])
    inv, _ = inverse_spd(sigma)
    _, sample_logdet = inverse_spd(sample)
    null_f = math.fsum(math.log(sample[i][i]) for i in range(16)) - sample_logdet
    chi, null_chi = multiplier * fit['F_ml'], multiplier * null_f
    delta, null_delta = max(0, chi - 100), max(0, null_chi - 120)
    weighted_sample = matmul(inv, sample)
    numerator = math.fsum((weighted_sample[i][j] - (1.0 if i == j else 0.0))
                          * (weighted_sample[j][i] - (1.0 if j == i else 0.0))
                          for i in range(16) for j in range(16))
    denominator = math.fsum(weighted_sample[i][j] * weighted_sample[j][i]
                            for i in range(16) for j in range(16))
    gfi = 1 - numerator / denominator
    paths = []
    for value, (target, source), label in zip(raw[:4], STRUCTURAL, STRUCTURAL_LABELS):
        source_var, target_var = latent_cov[source][source], latent_cov[target][target]
        beta = value * math.sqrt(source_var / target_var) if source_var > 0 and target_var > 0 else None
        paths.append({'path': label, 'B': value, 'beta': beta, 'fixed': False})
    paths.append({'path': 'EQ -> BAL', 'B': 1.0,
                  'beta': math.sqrt(latent_cov[2][2] / latent_cov[4][4])
                  if latent_cov[2][2] > 0 and latent_cov[4][4] > 0 else None, 'fixed': True})
    direct = raw[14]
    paths.append({'path': 'UA -> O14', 'B': direct,
                  'beta': direct * math.sqrt(latent_cov[1][1] / sigma[13][13])
                  if latent_cov[1][1] > 0 else None, 'fixed': False})
    measurement_paths = []
    for target in range(16):
        for source in range(6):
            if not loadings[target][source]:
                continue
            beta = (loadings[target][source] * math.sqrt(latent_cov[source][source] / sigma[target][target])
                    if latent_cov[source][source] > 0 else None)
            measurement_paths.append({'path': f'{LATENTS[source]} -> O{target + 1:02d}',
                                      'B': loadings[target][source], 'beta': beta,
                                      'fixed': (target, source) in FIXED_MEASUREMENT})
    negative = ([{'parameter': ['SN', 'UA', 'EQ', 'dENV', 'dBAL', 'dUSR'][i], 'value': v}
                 for i, v in enumerate(q) if v < 0]
                + [{'parameter': f'error O{i + 1:02d}', 'value': v}
                   for i, v in enumerate(theta) if v < 0])
    return {**fit, 'covariance_divisor': None, 'likelihood_multiplier': multiplier,
            'independent_implementation_not_Amos_output': True,
            'fit_indices': {'chi_square': chi, 'df': 100, 'chi_square_div_df': chi / 100,
                           'GFI': gfi, 'AGFI': 1 - 1.36 * (1 - gfi),
                           'CFI': 1 - delta / max(delta, null_delta) if max(delta, null_delta) else 1,
                           'TLI': ((null_chi / 120) - (chi / 100)) / ((null_chi / 120) - 1),
                           'RMR': math.sqrt(math.fsum((sample[i][j] - sigma[i][j]) ** 2
                                                     for i in range(16) for j in range(i + 1)) / 136),
                           'RMSEA': math.sqrt(max((chi - 100) / (100 * (n - 1)), 0)),
                           'independence_chi_square': null_chi, 'independence_df': 120},
            'main_paths': paths, 'measurement_paths': measurement_paths,
            'latent_variances': {label: latent_cov[i][i] for i, label in enumerate(LATENTS)},
            'R_squared': {label: 1 - q[i] / latent_cov[i][i]
                          for i, label in enumerate(LATENTS) if i >= 3 and latent_cov[i][i] > 0},
            'negative_variance_parameters': negative,
            'solution_admissible_nonnegative_variances': not negative}


def expected_information(fit, sample, multiplier):
    """Normal-theory expected information; not robust or bootstrap inference."""
    x = fit['scaled_parameters']
    sigma = components(x)[6]
    inv, _ = inverse_spd(sigma)
    derivatives = []
    for k in range(36):
        step = 1e-5 * max(1, abs(x[k]))
        plus, minus = x[:], x[:]
        plus[k] += step
        minus[k] -= step
        upper, lower = components(plus)[6], components(minus)[6]
        derivatives.append([[(upper[i][j] - lower[i][j]) / (2 * step)
                              for j in range(16)] for i in range(16)])
    weighted = [matmul(inv, derivative) for derivative in derivatives]
    information = [[multiplier / 2 * math.fsum(weighted[k][i][j] * weighted[l][j][i]
                                              for i in range(16) for j in range(16))
                    for l in range(36)] for k in range(36)]
    inverse_info, _ = inverse_spd(information)
    result = []
    for k, label in enumerate(PARAMETER_LABELS):
        se = SCALES[k] * math.sqrt(inverse_info[k][k])
        estimate = fit['raw_parameters'][k]
        critical_ratio = estimate / se
        result.append({'parameter': label, 'estimate': estimate, 'SE': se,
                       'CR': critical_ratio, 'p_two_sided_normal': math.erfc(abs(critical_ratio) / math.sqrt(2))})
    return {'method': 'Normal-theory expected information with likelihood multiplier validated against original output',
            'not_robust_or_bootstrap': True, 'free_parameters': result}


def load_original():
    matrix = decode_numeric_matrix(ROOT / '最终用于sem的匿名39✖16输入矩阵.sav')
    columns = {variable['name']: i for i, variable in enumerate(matrix['variables'])}
    assert [int(row[columns['ParkID']]) for row in matrix['rows']] == list(range(1, 40))
    rows = [[row[columns[name]] for name in OBSERVED] for row in matrix['rows']]
    assert len(rows) == 39 and all(len(row) == 16 and all(v is not None for v in row) for row in rows)
    return rows


def baseline():
    rows = load_original()
    all_results = []
    for divisor in (38, 39):
        sample = covariance(rows, divisor)
        objective = Objective(sample)
        initial = [v / s for v, s in zip(BASE_RAW, SCALES)]
        check = gradient_check(objective, initial)
        assert check['maximum_relative_gradient_difference'] < 1e-6
        print(json.dumps({'baseline_covariance_divisor': divisor, 'gradient_check': check}), flush=True)
        fit = minimize(objective, BASE_RAW)
        result = fit_summary(fit, sample, 38)
        result['covariance_divisor'] = divisor
        result['gradient_check'] = check
        result['chi_square_with_multiplier_39'] = 39 * result['F_ml']
        all_results.append(result)
        print(json.dumps({'baseline_covariance_divisor': divisor,
                          'fit_indices': result['fit_indices'],
                          'max_abs_scaled_gradient': result['max_abs_scaled_gradient'],
                          'main_paths': result['main_paths']}), flush=True)
    out = Path(__file__).resolve().parent / 'independent_ml_baseline_checks.json'
    out.write_text(json.dumps({'reported_Amos_baseline': {'chi_square': 119.555, 'df': 100,
                                                        'GFI': .749, 'CFI': .854, 'TLI': .825},
                              'models': all_results}, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    return all_results


def scenarios():
    work = Path(__file__).resolve().parent
    baseline_record = json.loads((work / 'independent_ml_baseline_checks.json').read_text(encoding='utf-8'))
    old_fit = next(model for model in baseline_record['models'] if model['covariance_divisor'] == 39)
    assert abs(old_fit['fit_indices']['chi_square'] - 119.555) < .0005
    assert old_fit['max_abs_scaled_gradient'] < 1e-6
    original_rows = load_original()
    sample_old = covariance(original_rows, 39)
    old_information = expected_information(old_fit, sample_old, 38)
    (work / 'independent_ml_baseline_information.json').write_text(
        json.dumps(old_information, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    with (work / 'qc_four_ndvi_values.csv').open(encoding='utf-8-sig', newline='') as stream:
        ndvi_rows = list(csv.DictReader(stream))
    all_results = []
    for scenario_number in range(1, 5):
        chosen = [row for row in ndvi_rows if int(row['scenario']) == scenario_number]
        assert [int(row['ParkID']) for row in chosen] == list(range(1, 40))
        rows = [row[:] for row in original_rows]
        for row, ndvi in zip(rows, chosen):
            row[5] = float(ndvi['z_outside_area_mean'])
            row[6] = float(ndvi['z_inside_area_mean'])
        assert all(row[i] == old[i] for row, old in zip(rows, original_rows)
                   for i in range(16) if i not in (5, 6))
        sample = covariance(rows, 39)
        attempts = []
        rng = random.Random(20261111)
        initial_guesses = [old_fit['raw_parameters']]
        for _ in range(2):
            guess = [value + .2 * scale * rng.uniform(-1, 1)
                     for value, scale in zip(old_fit['raw_parameters'][:16], SCALES[:16])]
            guess += [value * rng.uniform(.8, 1.2) for value in old_fit['raw_parameters'][16:]]
            initial_guesses.append(guess)
        for attempt, initial in enumerate(initial_guesses):
            print(json.dumps({'scenario': scenario_number, 'start': attempt}), flush=True)
            objective = Objective(sample)
            fit = minimize(objective, initial, max_iterations=1000)
            fit['start'] = attempt
            attempts.append(fit)
        best = min(attempts, key=lambda result: result['F_ml'])
        summary = fit_summary(best, sample, 38)
        summary['covariance_divisor'] = 39
        summary['scenario'] = scenario_number
        summary['ParkID_9_18_28_source'] = next(row['source_raster'] for row in chosen if int(row['ParkID']) == 9)
        summary['ParkID_32_source'] = next(row['source_raster'] for row in chosen if int(row['ParkID']) == 32)
        summary['starts'] = [{'start': result['start'], 'F_ml': result['F_ml'],
                             'iterations': result['iterations'], 'termination': result['termination'],
                             'max_abs_scaled_gradient': result['max_abs_scaled_gradient']}
                            for result in attempts]
        summary['multistart_F_range'] = max(result['F_ml'] for result in attempts) - min(result['F_ml'] for result in attempts)
        summary['expected_information'] = expected_information(best, sample, 38)
        summary['source_selected_as_primary'] = False
        summary['original_14_other_indicators_unchanged'] = True
        all_results.append(summary)
        print(json.dumps({'scenario': scenario_number, 'fit_indices': summary['fit_indices'],
                          'main_paths': summary['main_paths'],
                          'negative_variances': summary['negative_variance_parameters'],
                          'multistart_F_range': summary['multistart_F_range']}), flush=True)
    (work / 'independent_ml_four_scenarios.json').write_text(
        json.dumps({'scope': 'Four NDVI source-combination sensitivity analyses; no primary imagery selection',
                    'original_model_and_data_files_modified': False,
                    'baseline_reproduced_to_reported_precision': True,
                    'independent_implementation_not_Amos_output': True,
                    'covariance_divisor': 39, 'likelihood_multiplier': 38,
                    'parameter_count': 36, 'df': 100,
                    'models': all_results}, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    return all_results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--scenarios', action='store_true')
    args = parser.parse_args()
    if args.scenarios:
        scenarios()
    else:
        baseline()
