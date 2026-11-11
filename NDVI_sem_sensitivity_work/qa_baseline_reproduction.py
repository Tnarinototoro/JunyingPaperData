"""Independent source-specification parity checks for the reconstructed baseline.

Does not estimate SEM, modify inputs, choose imagery, or claim native Amos output.
Builds the 22-variable RAM covariance directly from the audited source graph,
and checks all displayed original path/variance values and numerical gradients.
"""
import json
import math
from pathlib import Path

import sem_covariance_ml as ml


def multiply(a, b):
    return [[math.fsum(a[i][k] * b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]


def raw_lookup(raw):
    return dict(zip(ml.PARAMETER_LABELS, raw))


def ram_sigma(spec, raw):
    labels = ml.LATENTS + [row['alias'] for row in spec['observed']]
    index = {name: i for i, name in enumerate(labels)}
    look = raw_lookup(raw)
    size = len(labels)
    a = [[0.0] * size for _ in range(size)]
    for edge in spec['regressions']:
        key = edge['from'] + ' -> ' + edge['to']
        a[index[edge['to']]][index[edge['from']]] = edge['B'] if edge['fixed'] else look[key]
    a2 = multiply(a, a)
    a3 = multiply(a2, a)
    assert max(abs(v) for row in a3 for v in row) == 0
    # The actual graph has maximum two-arrow paths, so (I-A)^-1 = I+A+A^2.
    transfer = [[float(i == j) + a[i][j] + a2[i][j] for j in range(size)] for i in range(size)]
    disturbances = [1.0, look['variance UA'], look['variance EQ'], look['variance dENV'],
                    look['variance dBAL'], look['variance dUSR']]
    for row in spec['observed']:
        disturbances.append(row.get('fixed_error_variance', look.get('error variance ' + row['alias'])))
    assert len(disturbances) == size == 22
    return [[math.fsum(transfer[i+6][k] * disturbances[k] * transfer[j+6][k] for k in range(size))
             for j in range(16)] for i in range(16)]


def ram_objective(spec, scaled, sample, logdet_sample):
    raw = [x * s for x, s in zip(scaled, ml.SCALES)]
    sigma = ram_sigma(spec, raw)
    inverse, logdet = ml.inverse_spd(sigma)
    return logdet + math.fsum(sample[i][j] * inverse[i][j] for i in range(16) for j in range(16)) - logdet_sample - 16


def audit():
    work = Path(__file__).resolve().parent
    spec = json.loads((work / 'sem_model_specification.json').read_text(encoding='utf-8'))
    fit = next(row for row in json.loads((work / 'independent_ml_baseline_checks.json').read_text(encoding='utf-8'))['models']
               if row['covariance_divisor'] == 39)
    reported_paths = {edge['from'] + ' -> ' + edge['to']: edge for edge in spec['regressions']}
    actual_paths = {row['path']: row for row in fit['measurement_paths'] + fit['main_paths']}
    assert set(actual_paths) == set(reported_paths) and len(actual_paths) == 25
    comparisons = []
    for name, expected in reported_paths.items():
        actual = actual_paths[name]
        old_b = expected['B'] if expected['fixed'] else expected['reported_B']
        comparisons.append({'path': name, 'fixed': expected['fixed'],
                            'original_displayed_B': old_b, 'reconstructed_B': actual['B'],
                            'B_matches_three_decimals': f"{old_b:.3f}" == f"{actual['B']:.3f}",
                            'original_displayed_beta': expected['reported_beta'], 'reconstructed_beta': actual['beta'],
                            'beta_matches_three_decimals': f"{expected['reported_beta']:.3f}" == f"{actual['beta']:.3f}",
                            'fixed_status_matches': actual['fixed'] == expected['fixed']})
    raw, transform, loads, q, theta, propagated, sigma, latent_cov = ml.components(fit['scaled_parameters'])
    variances = []
    for i, label in enumerate(['SN', 'UA', 'EQ', 'd1', 'd2', 'd3']):
        source = spec['latent_disturbance_variances'][i]
        old = source['value'] if source['fixed'] else source['reported_value']
        variances.append({'parameter': label, 'fixed': source['fixed'], 'original_displayed':old,
                          'reconstructed':q[i], 'matches_three_decimals':f'{old:.3f}' == f'{q[i]:.3f}'})
    for i, row in enumerate(spec['observed']):
        old = row.get('fixed_error_variance', row.get('reported_error_variance'))
        variances.append({'parameter':row['error'], 'target':row['alias'],
                          'fixed':'fixed_error_variance' in row, 'original_displayed':old,
                          'reconstructed':theta[i], 'matches_three_decimals':f'{old:.3f}' == f'{theta[i]:.3f}'})
    direct_sigma = ram_sigma(spec, raw)
    covariance_difference = max(abs(sigma[i][j] - direct_sigma[i][j]) for i in range(16) for j in range(16))
    assert covariance_difference < 1e-13
    sample = ml.covariance(ml.load_original(), 39)
    objective = ml.Objective(sample)
    _, logdet_sample = ml.inverse_spd(sample)
    gradient_reports = []
    for name, scaled in [('displayed_original_initial_point', [r / s for r, s in zip(ml.BASE_RAW, ml.SCALES)]),
                         ('reconstructed_baseline_optimum', fit['scaled_parameters'])]:
        value, analytic = objective.evaluate(scaled)
        direct_value = ram_objective(spec, scaled, sample, logdet_sample)
        diffs = []
        for i in range(36):
            step = 1e-5 * max(1, abs(scaled[i]))
            plus, minus = scaled[:], scaled[:]
            plus[i] += step
            minus[i] -= step
            numeric = (ram_objective(spec, plus, sample, logdet_sample) - ram_objective(spec, minus, sample, logdet_sample)) / (2 * step)
            diffs.append(abs(numeric - analytic[i]) / max(1, abs(numeric), abs(analytic[i])))
        gradient_reports.append({'point':name, 'all_36_free_parameters_checked':True,
                                 'maximum_relative_gradient_difference':max(diffs),
                                 'direct_RAM_objective_difference':abs(value-direct_value), 'step_relative':1e-5})
        assert max(diffs) < 1e-6 and abs(value-direct_value) < 1e-12
    fit_comparisons = []
    for actual_name, old_name in [('chi_square','chisq'),('GFI','GFI'),('AGFI','AGFI'),('CFI','CFI'),
                                  ('TLI','TLI'),('RMR','RMR'),('RMSEA','RMSEA')]:
        old, actual = spec['reported_fit'][old_name], fit['fit_indices'][actual_name]
        fit_comparisons.append({'indicator':actual_name, 'original_displayed':old, 'reconstructed':actual,
                                'matches_three_decimals':f'{old:.3f}' == f'{actual:.3f}'})
    r2 = [{'latent':label, 'original_displayed':old, 'reconstructed':fit['R_squared'][label],
           'matches_three_decimals':f'{old:.3f}' == f"{fit['R_squared'][label]:.3f}"}
          for label, old in spec['reported_latent_R2'].items()]
    report = {'scope':'Source-graph/independent-implementation parity QA; not native Amos execution or imagery selection',
              'original_inputs_modified':False, 'scenario_models_estimated_by_this_QA':False,
              'all_25_paths_checked':True, 'path_comparisons':comparisons,
              'all_22_variances_checked':True, 'variance_comparisons':variances,
              'nine_fixed_regressions_match':sum(row['fixed'] for row in comparisons) == 9 and all(row['fixed_status_matches'] for row in comparisons),
              'two_fixed_variances_match':sum(row['fixed'] for row in variances) == 2,
              'covariance_constraints':'All exogenous/disturbance/error covariances zero as in source graph',
              'covariance_expression':'Independent 22-variable RAM (I+A+A^2) D (I+A+A^2)^T observed block matches root Lambda-T expression',
              'maximum_covariance_difference':covariance_difference,
              'gradient_checks_against_independent_RAM_objective':gradient_reports,
              'covariance_divisor_verified_by_original_output':39,
              'fit_multiplier_verified_by_original_output':38,
              'fit_comparisons':fit_comparisons, 'latent_R2_comparisons':r2,
              'all_displayed_paths_match':all(row['B_matches_three_decimals'] and row['beta_matches_three_decimals'] and row['fixed_status_matches'] for row in comparisons),
              'all_displayed_variances_match':all(row['matches_three_decimals'] for row in variances),
              'all_displayed_fit_indices_match':all(row['matches_three_decimals'] for row in fit_comparisons),
              'all_displayed_R2_match':all(row['matches_three_decimals'] for row in r2),
              'baseline_solution_nonnegative_variances':fit['solution_admissible_nonnegative_variances'],
              'note':'This validates numerical baseline correspondence under the given fixed model, not substantive validity or universal optimizer convergence.'}
    (work/'qa_baseline_reproduction.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key:value for key,value in report.items() if key.startswith('all_') or key.startswith('maximum_') or key.endswith('_match')}, ensure_ascii=True))
    return report


if __name__ == '__main__':
    audit()
