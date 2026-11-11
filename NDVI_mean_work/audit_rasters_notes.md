# Source raster audit (headers only)

The Python standard-library script `audit_rasters_stdlib.py` reads TIFF/GeoTIFF
headers and selected tag values, plus existing PAM `.aux.xml` metadata. It does
not load image arrays, calculate park means, modify source files, resample,
mosaic, choose overlapping rasters, or choose acquisition dates.

The machine-readable results are `audit_rasters_stdlib.json` and
`audit_rasters_stdlib.tsv`. Twenty-four TIFF files were audited with no parsing
errors: ten labelled NDVI, ten labelled NDBI, and four Hokka variants.

## Ten NDVI-labelled rasters

| Filename | Width | Height | Projected EPSG |
| --- | ---: | ---: | ---: |
| NDVI_fukushima.tif | 7731 | 7851 | 32654 |
| NDVI_fukushima_up.tif | 7811 | 7921 | 32654 |
| NDVI_hokka_test.tif | 7701 | 7821 | 32654 |
| NDVI_island.tif | 7661 | 7801 | 32652 |
| NDVI_kyoto.tif | 7761 | 7901 | 32653 |
| NDVI_nagoya.tif | 7611 | 7741 | 32653 |
| NDVI_nara.tif | 7681 | 7811 | 32653 |
| NDVI_tokyo.tif | 7741 | 7871 | 32654 |
| NDVI_tokyo_down.tif | 7831 | 7961 | 32654 |
| NDVI_west.tif | 7621 | 7761 | 32652 |

All ten are single-band Float32, little-endian classic TIFF, uncompressed
(Compression tag = 1), with 30 by 30 m pixel spacing and PixelIsArea metadata.
The recorded NoData text is `-3.4028234663852886e+38`. There is no explicit
GDAL band scale/offset metadata; the semantic defaults are scale 1 and offset 0.
This is not evidence of an upstream satellite-product scaling procedure.

All use one row per strip. Most strip offsets are not sequential in raster row
order, so a single image base offset with a row stride is unsafe. Read exact
StripOffsets (tag 273) and StripByteCounts (tag 279) for each row. The helper
`read_ifd(Path(...))` returns these arrays without reading pixel values.

Whole-raster bounding extents and geotransforms are in the JSON/TSV. They are
not park locations or valid-pixel footprints. The `stored_statistics` fields
are copied existing header/PAM statistics, marked approximate; they are not
recomputed extrema/means and cannot substitute for park-level zonal means.

## NDBI and Hokka cautions

- NDBI files have their own index values and are not substitutes for NDVI,
  even where the dimensions, georeferencing, or strip offsets match.
- `Hokka.tif` declares a geographic CRS (EPSG 9055, WGS 84 G1150, degrees),
  but its coordinate magnitudes and 30-unit grid are projected-looking. This
  metadata conflict must not be resolved by silently relabelling the CRS.
- `Hokka_test.tif` declares UTM 54N and carries plausible approximate statistics;
  no equivalence to another file's pixel content was tested in this audit.
- `hokkaido.tif` has zero strip offsets and byte counts throughout; its PAM
  records 0 percent valid values. Do not interpret file-header bytes at offset
  zero as raster pixels.
- `hokkaido.tif` and `hokkaido_correct.tif` declare the user-defined
  `Asia_North_Albers_Equal_Area_Conic`, not UTM 54N. GeoKey value 32767 means
  user-defined, not an EPSG authority code.
- `hokkaido_correct.tif` has stored statistics containing negative/positive
  infinity and NaN. Its name alone is not evidence that it is corrected/usable.

## Provenance and time

No audited file supplied TIFF DateTime, ImageDescription, or Software tags,
or identifiable satellite product/acquisition/compositing-time metadata in
the examined GDAL metadata. The 30 m grid alone cannot identify the sensor.
Filesystem modification dates are in November 2026 and describe file
modification/upload, not imagery acquisition. Existing approximate statistics
also do not establish cloud, shadow, water, or invalid-pixel processing.

Further raster-source/date validation and polygon coverage/valid-pixel checks
are separate from this header audit. No park names, addresses, or park identity
keys are included in this report.
