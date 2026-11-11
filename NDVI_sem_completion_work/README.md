# New NDVI / original SEM diagnostic

## Latest selected-source analysis

The `selected_frame_margin_same_model_*` files are the latest analysis, not a
composite. The root selected 9=NDVI_nagoya, 18/28=NDVI_nara and
32=NDVI_fukushima_up by a source-frame margin rule before SEM; the remaining
35 use the sole usable supplied source. All 39 within/outside means were
separately standardized with sample SD, denominator 38. Original 14 other
observed variables are unchanged.

Three starts converge to the same finite original-model point:
F=3.67905256539465, Var(EQ)=-0.0943074249178; F range about 1.4e-14 and original
scaled score about 1.1e-7. This is still inadmissible. Both observed-Hessian
step checks and the expected-information matrix are positive definite; the
observed-Hessian SE relative step difference is below 2e-5. CSVs include
diagnostic free coefficients and SEs, all variances and fit indices, explicitly
marked as an inadmissible-model diagnostic. A positive Hessian does not make
negative latent variance substantively valid. No formal standardized result
figure is generated, and no native Amos execution is claimed.

`selected_frame_margin_ndvi_means_and_z.csv` contains the chosen raw regional
means and Z values for independent SAV/XLSX read-back validation. The JSON
records the complete 39x16 matrix in original model variable order.

## Earlier provisional composite diagnostics

These are independent standard-library calculations, not IBM SPSS Amos output.
The provisional four-park data use the equal-weight average of both candidate
regional means. Their use as a pixel-wise composite requires confirmation that
the two native grids and valid masks coincide. No original GIS, SAV, XLSX or
AMW input is edited by these scripts. Final source selection belongs to the
author/root workflow, not to these model fits.

## Original model, unchanged conditions

The stable reparameterization replaces each free observed error variance by its
free total marginal variance, and replaces the EQ loading on outside NDVI by
`h = loading * Var(EQ)`. For nonzero Var(EQ), this is exactly the same covariance
model and can be converted back to all original coefficients and variances.
All paths, cross-loadings, nine fixed coefficients, two fixed variances and zero
covariance conditions remain unchanged. The zero-EQ-variance limit with nonzero
h has no finite original loading and is not an admissible original estimate.

The converted original and reduced covariance matrices agree within 1.2e-16.
Initial and final gradient checks pass. Four independent starts converge to the
same finite stationary point: F=3.6888760616753, Var(EQ) approximately -0.11747056,
with a multistart F range below 8e-14. The original-coordinate scaled score is
below 2.5e-7. This is an **inadmissible solution**, not a publishable standardized
SEM: EQ standardized coefficients do not have real values when its variance is
negative. Do not replace missing standardized values with zero or draw a formal
Amos result figure from this output.

## Why changing the NDVI values matters

The unchanged fixed model imposes these covariance identities:

```
Cov(outside NDVI, inside NDVI)
 = Cov(outside NDVI, S5_1)
 = Cov(outside NDVI, S5_2)
 = h

Cov(inside NDVI, S5_1)
 = Cov(inside NDVI, S5_2)
 = Var(EQ)
```

They follow from EQ -> BAL = 1, EQ -> inside NDVI = 1, both BAL -> S5_1/S5_2
loadings = 1, and the zero exogenous/error covariances. The provisional corrected
sample covariances for the first three pairs are 0.77939, -0.11595 and 0.11858;
for the latter two pairs they are -0.15773 and 0.02045. These are not merely a
four-park missing-value problem. They show tension between the corrected NDVI
covariance structure and the original fixed model. Other sources or revised
boundaries require recomputation, not selection by which SEM fits best.

## Explicit nonnegative-variance diagnostic

Three additional runs impose nonnegative variance bounds via log coordinates.
They converge to F approximately 4.25015854443. The outside-NDVI error variance
e16 reaches its lower boundary (approximately 3e-11); other parameter scores
are small and the lower-bound KKT score is positive (about 0.25531). This bound
diagnostic is not the original AMW's unrestricted-variance estimate and must
not silently replace it. Boundary inference requires separate consideration.

## Files

- `composite_same_model_ml_diagnostic.json`: one strict-model fit, covariance
  equivalence and gradient checks, diagnostic means and Z values.
- `composite_multistart_and_boundary_diagnostics.json`: four strict-model
  starts and three explicitly bounded diagnostic runs.
- `check_composite_ml.py`, `additional_composite_diagnostics.py`: processing
  source code tied to the current Paper workspace, not Amos plugins.

Neither a valid final Amos figure nor a complete source-provenance determination
is claimed here. Amos/SPSS executables were not located in the checked standard
installation folders or uninstall registry; no installation was attempted.
