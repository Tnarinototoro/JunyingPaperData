"""Read-only independent diagnostics for four incomplete ML sensitivity runs.

No new optimization, source selection, or input/model editing is performed.
Retained iterates are diagnostic points, not publishable SEM estimates.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

import sem_covariance_ml as ml
from qa_baseline_reproduction import ram_sigma, ram_objective, multiply, raw_lookup


REPORTED_REGRESSION_INFERENCE = {
    'SN -> O02': (.024,3.059), 'SN -> O01':(.032,4.338), 'UA -> O03':(.057,5.719),
    'ENV -> O11':(.310,1.889), 'USR -> O14':(.559,.919), 'EQ -> ENV':(.664,-.885),
    'EQ -> O06':(3.349,.864), 'ENV -> O10':(.467,1.220), 'USR -> O16':(.071,.815),
    'SN -> ENV':(.037,3.709), 'SN -> BAL':(.092,2.376), 'UA -> O14':(.146,-3.124),
    'BAL -> O11':(.191,2.140), 'SN -> O03':(.046,1.617), 'UA -> O06':(.200,2.769),
    'SN -> USR':(.151,-.820),
}
REPORTED_VARIANCE_INFERENCE = {
    'variance UA':(.151,3.824), 'variance EQ':(.031,.634), 'variance dENV':(.012,.049),
    'variance dBAL':(.051,.899), 'variance dUSR':(.519,.879),
    'error variance O01':(.006,2.461), 'error variance O02':(.004,3.903),
    'error variance O03':(.014,3.698), 'error variance O04':(.073,3.285),
    'error variance O07':(.216,4.291), 'error variance O06':(.265,2.463),
    'error variance O14':(.157,2.261), 'error variance O15':(.505,.509),
    'error variance O08':(.008,2.604), 'error variance O11':(.008,1.968),
    'error variance O12':(.140,4.050), 'error variance O13':(.057,2.869),
    'error variance O09':(.016,3.866), 'error variance O10':(.036,4.282),
    'error variance O16':(.007,4.191),
}


def independent_ram_gradient(spec,scaled,sample):
    """Differentiate generic source-graph RAM, not Lambda/transform components."""
    raw=[x*s for x,s in zip(scaled,ml.SCALES)]
    labels=ml.LATENTS+[row['alias'] for row in spec['observed']]
    index={name:i for i,name in enumerate(labels)}
    size=len(labels)
    lookup=raw_lookup(raw)
    a=[[0.0]*size for _ in range(size)]
    for edge in spec['regressions']:
        key=edge['from']+' -> '+edge['to']
        a[index[edge['to']]][index[edge['from']]]=edge['B'] if edge['fixed'] else lookup[key]
    a2=multiply(a,a)
    transfer=[[float(i==j)+a[i][j]+a2[i][j] for j in range(size)] for i in range(size)]
    observed=transfer[6:]
    disturbance=[1.0,lookup['variance UA'],lookup['variance EQ'],lookup['variance dENV'],
                 lookup['variance dBAL'],lookup['variance dUSR']]
    for row in spec['observed']:
        disturbance.append(row.get('fixed_error_variance',lookup.get('error variance '+row['alias'])))
    sigma=ram_sigma(spec,raw)
    inverse,_=ml.inverse_spd(sigma)
    product=multiply(multiply(inverse,sample),inverse)
    h=[[inverse[i][j]-product[i][j] for j in range(16)] for i in range(16)]
    hm=multiply(h,observed)
    gradients=[]
    for label,scale in zip(ml.PARAMETER_LABELS,ml.SCALES):
        if ' -> ' in label:
            source,target=label.split(' -> ')
            si,ti=index[source],index[target]
            dm=[[0.0]*size for _ in range(size)]
            # dM=dA + A*dA + dA*A; dA has a single nonzero coefficient.
            dm[ti][si]+=scale
            for i in range(size):
                dm[i][si]+=a[i][ti]*scale
            for j in range(size):
                dm[ti][j]+=scale*a[si][j]
            gradients.append(2*math.fsum(hm[i][k]*disturbance[k]*dm[i+6][k]
                                         for i in range(16) for k in range(size)))
        else:
            if label.startswith('error variance '):
                di=index[label.removeprefix('error variance ')]
            else:
                name=label.removeprefix('variance ')
                di=index[{'dENV':'ENV','dBAL':'BAL','dUSR':'USR'}.get(name,name)]
            gradients.append(scale*math.fsum(hm[i][di]*observed[i][di] for i in range(16)))
    return gradients


def audit():
    work = Path(__file__).resolve().parent
    root = work.parent
    sav = root / '最终用于sem的匿名39✖16输入矩阵.sav'
    sav_before = hashlib.sha256(sav.read_bytes()).hexdigest()
    spec = json.loads((work/'sem_model_specification.json').read_text(encoding='utf-8'))
    runs = json.loads((work/'independent_ml_four_scenarios.json').read_text(encoding='utf-8'))
    information = json.loads((work/'independent_ml_baseline_information.json').read_text(encoding='utf-8'))
    originals = ml.decode_numeric_matrix(sav)
    indexes = {row['name']:i for i,row in enumerate(originals['variables'])}
    assert [int(row[indexes['ParkID']]) for row in originals['rows']] == list(range(1,40))
    names = [row['sav'] for row in spec['observed']]
    assert names == ml.OBSERVED
    original = [[row[indexes[name]] for name in names] for row in originals['rows']]
    assert original == ml.load_original()
    original_sample = ml.covariance(original,39)
    with (work/'qc_four_ndvi_values.csv').open(encoding='utf-8-sig',newline='') as stream:
        values = list(csv.DictReader(stream))
    extraction = json.loads((root/'NDVI_区域平均值_20261111_核对版/GIS/pixel_extractions.json').read_text(encoding='utf-8'))
    by_source = {(row['ParkID'],row['source_raster']):row for row in extraction}
    desired = {1:('NDVI_nagoya.tif','NDVI_fukushima.tif'),2:('NDVI_nagoya.tif','NDVI_fukushima_up.tif'),
               3:('NDVI_nara.tif','NDVI_fukushima.tif'),4:('NDVI_nara.tif','NDVI_fukushima_up.tif')}
    diagnostics = []
    assert len(runs['models']) == 4
    for run in runs['models']:
        number = run['scenario']
        csv_rows = [row for row in values if int(row['scenario']) == number]
        assert [int(row['ParkID']) for row in csv_rows] == list(range(1,40))
        assert (run['ParkID_9_18_28_source'],run['ParkID_32_source']) == desired[number]
        rows = [row[:] for row in original]
        for i,row in enumerate(csv_rows):
            source = by_source[(i+1,row['source_raster'])]
            assert float(row['ndvi_inside_area_mean']) == source['inside']['mean']
            assert float(row['ndvi_outside_area_mean']) == source['outside']['mean']
            if i+1 in (9,18,28):
                assert row['source_raster'] == desired[number][0]
            elif i+1 == 32:
                assert row['source_raster'] == desired[number][1]
            rows[i][names.index('Z内部NDVI平均値')] = float(row['z_inside_area_mean'])
            rows[i][names.index('Z外部NDVI平均値')] = float(row['z_outside_area_mean'])
        for raw_key,z_key in [('ndvi_inside_area_mean','z_inside_area_mean'),('ndvi_outside_area_mean','z_outside_area_mean')]:
            raw_values = [float(row[raw_key]) for row in csv_rows]
            mean = math.fsum(raw_values)/39
            sd = math.sqrt(math.fsum((value-mean)**2 for value in raw_values)/38)
            assert all(abs(float(row[z_key])-(value-mean)/sd) < 1e-14 for row,value in zip(csv_rows,raw_values))
        other = [i for i in range(16) if i not in (5,6)]
        assert all(row[i] == old[i] for row,old in zip(rows,original) for i in other)
        sample = ml.covariance(rows,39)
        assert all(sample[i][j] == original_sample[i][j] for i in other for j in other)
        sigma = ml.components(run['scaled_parameters'])[6]
        independent = ram_sigma(spec,run['raw_parameters'])
        sigma_difference = max(abs(sigma[i][j]-independent[i][j]) for i in range(16) for j in range(16))
        assert sigma_difference < 1e-10
        objective = ml.Objective(sample)
        value,gradient = objective.evaluate(run['scaled_parameters'])
        _,logdet = ml.inverse_spd(sample)
        direct = ram_objective(spec,run['scaled_parameters'],sample,logdet)
        assert abs(value-run['F_ml']) < 1e-10 and abs(value-direct) < 1e-10
        gradient_tests = []
        for relative_step in (1e-5,1e-6,1e-7,1e-8):
            errors = []
            for i in range(36):
                step = relative_step*max(1,abs(run['scaled_parameters'][i]))
                plus,minus = run['scaled_parameters'][:],run['scaled_parameters'][:]
                plus[i]+=step
                minus[i]-=step
                numeric = (ram_objective(spec,plus,sample,logdet)-ram_objective(spec,minus,sample,logdet))/(2*step)
                errors.append(abs(numeric-gradient[i])/max(1,abs(numeric),abs(gradient[i])))
            gradient_tests.append({'relative_step':relative_step,'maximum_relative_difference':max(errors)})
        best_gradient_error = min(row['maximum_relative_difference'] for row in gradient_tests)
        print(json.dumps({'scenario_gradient_diagnostic':number,'finite_difference_steps':gradient_tests}),flush=True)
        ram_gradient=independent_ram_gradient(spec,run['scaled_parameters'],sample)
        analytic_gradient_error=max(abs(left-right)/max(1,abs(left),abs(right))
                                    for left,right in zip(gradient,ram_gradient))
        assert analytic_gradient_error < 1e-8
        q,theta = ml.components(run['scaled_parameters'])[3:5]
        assert theta[5] < 0
        assert run['negative_variance_parameters'] == [{'parameter':'error O06','value':theta[5]}]
        assert not run['solution_admissible_nonnegative_variances']
        assert all(row['termination'] == 'iteration_limit' for row in run['starts'])
        assert len(run['starts']) == 3 and run['termination'] == 'iteration_limit'
        diagnostics.append({'scenario':number,'source_pair':desired[number],
                            'data_cases':39,'two_NDVI_positions':{'inside':6,'outside':5},
                            'other_14_variables_exactly_preserved':True,'non_NDVI_sample_covariance_block_unchanged':True,
                            'NDVI_values_and_sample_SD_z_checked':True,
                            'maximum_RAM_sigma_difference':sigma_difference,
                            'recorded_F_reproduced_difference':abs(value-run['F_ml']),
                            'direct_RAM_F_difference':abs(value-direct),
                            'gradient_checks':gradient_tests,'best_gradient_difference':best_gradient_error,
                            'independent_RAM_analytic_gradient_relative_difference':analytic_gradient_error,
                            'independent_RAM_analytic_gradient_matches':True,
                            'finite_difference_note':'Extreme unconverged coefficient/variance values cause high curvature and cancellation; central-difference error depends strongly on step. Generic analytic RAM derivatives supply the decisive formula check.',
                            'retained_point_positive_definite_Sigma':True,
                            'retained_point_e16_variance':theta[5],
                            'all_three_starts_reached_iteration_limit':True,
                            'max_abs_scaled_gradient':run['max_abs_scaled_gradient'],
                            'formal_converged_SEM_result':False,'source_selected':False})
    inference = []
    expected = {**REPORTED_REGRESSION_INFERENCE,**REPORTED_VARIANCE_INFERENCE}
    actual = {row['parameter']:row for row in information['free_parameters']}
    assert set(actual) == set(expected) and len(actual) == 36
    for name,(old_se,old_cr) in expected.items():
        row=actual[name]
        inference.append({'parameter':name,'original_displayed_SE':old_se,'reconstructed_SE':row['SE'],
                          'SE_matches_three_decimals':f'{old_se:.3f}' == f"{row['SE']:.3f}",
                          'original_displayed_CR':old_cr,'reconstructed_CR':row['CR'],
                          'CR_matches_three_decimals':f'{old_cr:.3f}' == f"{row['CR']:.3f}"})
    assert all(row['SE_matches_three_decimals'] and row['CR_matches_three_decimals'] for row in inference)
    sav_after=hashlib.sha256(sav.read_bytes()).hexdigest()
    assert sav_before == sav_after
    report={'scope':'Read-only independent diagnostics of four incomplete sensitivity runs; not an Amos execution',
            'no_new_optimization_performed':True,'original_sav_sha256_unchanged':sav_after,
            'scenario_diagnostics':diagnostics,'all_four_NDVI_replacements_verified':True,
            'all_14_other_variables_preserved':True,
            'baseline_expected_information_formula':'I_kl=(38/2)*tr(Sigma^-1 dSigma_k Sigma^-1 dSigma_l) in scaled coordinates, SE converted back to raw parameter scale',
            'baseline_all_36_SE_CR_match_original_displayed_output':True,'baseline_inference_comparisons':inference,
            'only_supported_diagnostic_statement':'This independent implementation, with these starts and iteration limit, did not obtain a converged solution with nonnegative variance estimates for any of the four source combinations.',
            'unsupported_claims':['Amos necessarily fails on the same data','No admissible solution exists anywhere in parameter space','One source combination can be selected by closest displayed iterate to old SEM'],
            'iterative_beta_p_fit_not_final_SEM_estimates':True,'imagery_source_selected':False}
    (work/'qa_four_scenario_diagnostics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'diagnostic_scenarios':len(diagnostics),'all_inputs_preserved':True,
                      'baseline_36_SE_CR_match':True,'best_gradient_differences':[row['best_gradient_difference'] for row in diagnostics]},ensure_ascii=True))
    return report


if __name__=='__main__':
    audit()
