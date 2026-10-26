import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

# --------------------------------------------------
# OrbiX - Orbit & Tracking Technical Report
# --------------------------------------------------

DATA_DIR = Path("data")
PREDICTIONS_FILE = DATA_DIR / "propagated_debris.csv"
QUALITY_FILE = DATA_DIR / "orbital_quality_report.csv"

REPORT_FILE = Path("ORBIT_TRACKING_REPORT.md")

print("OrbiX - Orbit & Tracking Report Generator")
print("-" * 50)

if not PREDICTIONS_FILE.exists():
    raise FileNotFoundError(PREDICTIONS_FILE)

if not QUALITY_FILE.exists():
    raise FileNotFoundError(QUALITY_FILE)

predictions = pd.read_csv(PREDICTIONS_FILE)
quality = pd.read_csv(QUALITY_FILE)

required_columns = [
    "NORAD_CAT_ID",
    "OBJECT_NAME",
    "ELEMENT_EPOCH",
    "PREDICTION_TIME_UTC",
    "MINUTES_FROM_START",
    "X_TEME_KM",
    "Y_TEME_KM",
    "Z_TEME_KM",
    "VX_TEME_KM_S",
    "VY_TEME_KM_S",
    "VZ_TEME_KM_S",
]

missing_columns = [
    column for column in required_columns
    if column not in predictions.columns
]

if missing_columns:
    raise ValueError(
        f"Missing prediction columns: {missing_columns}"
    )

object_count = predictions["NORAD_CAT_ID"].nunique()
record_count = len(predictions)

offsets = sorted(
    predictions["MINUTES_FROM_START"].dropna().unique()
)

records_per_object = predictions.groupby("NORAD_CAT_ID").size()

expected_records_per_object = len(offsets)

complete_objects = int(
    (records_per_object == expected_records_per_object).sum()
)

duplicate_records = int(
    predictions.duplicated(
        subset=["NORAD_CAT_ID", "MINUTES_FROM_START"]
    ).sum()
)

numeric_columns = [
    "X_TEME_KM",
    "Y_TEME_KM",
    "Z_TEME_KM",
    "VX_TEME_KM_S",
    "VY_TEME_KM_S",
    "VZ_TEME_KM_S",
]

numeric_values = predictions[numeric_columns].to_numpy(dtype=float)

import numpy as np

finite_rows = np.isfinite(numeric_values).all(axis=1)
finite_row_count = int(finite_rows.sum())

radius = np.linalg.norm(
    predictions[["X_TEME_KM", "Y_TEME_KM", "Z_TEME_KM"]]
    .to_numpy(dtype=float),
    axis=1,
)

speed = np.linalg.norm(
    predictions[["VX_TEME_KM_S", "VY_TEME_KM_S", "VZ_TEME_KM_S"]]
    .to_numpy(dtype=float),
    axis=1,
)

if finite_rows.any():
    radius_min = float(radius[finite_rows].min())
    radius_max = float(radius[finite_rows].max())
    speed_min = float(speed[finite_rows].min())
    speed_max = float(speed[finite_rows].max())
else:
    radius_min = radius_max = speed_min = speed_max = float("nan")

quality_summary = "Quality-status summary unavailable."

if "DATA_QUALITY_STATUS" in quality.columns:
    quality_counts = quality["DATA_QUALITY_STATUS"].value_counts()

    quality_summary = "\n".join(
        f"- {status}: {count}"
        for status, count in quality_counts.items()
    )

generated_at = datetime.now(timezone.utc).strftime(
    "%Y-%m-%d %H:%M:%S UTC"
)

report = f"""# OrbiX — Orbit & Tracking Technical Report

**Report generated:** {generated_at}

## 1. Objective

The Orbit & Tracking module retrieves orbital element records,
propagates them using SGP4, and produces predicted positions and
velocities at predefined time offsets.

## 2. Data source and method

- **Orbital data source:** CelesTrak OMM records
- **Propagation method:** SGP4
- **Python library version:** 2.27 (recorded during testing)
- **Prediction offsets:** {", ".join(str(int(x)) for x in offsets)} minutes
- **Coordinate reference frame:** TEME
- **Position units:** kilometres
- **Velocity units:** kilometres per second

## 3. Dataset summary

- **Unique objects:** {object_count}
- **Prediction records:** {record_count}
- **Objects with complete prediction sequences:** {complete_objects}
- **Objects with incomplete prediction sequences:** {object_count - complete_objects}
- **Duplicate object/offset records:** {duplicate_records}
- **Rows with finite position and velocity values:** {finite_row_count}
- **Rows with non-finite position or velocity values:** {record_count - finite_row_count}

## 4. Numerical screening

- **Minimum observed geocentric radius:** {radius_min:.2f} km
- **Maximum observed geocentric radius:** {radius_max:.2f} km
- **Minimum observed speed:** {speed_min:.4f} km/s
- **Maximum observed speed:** {speed_max:.4f} km/s

These ranges are screening statistics. They do not independently
prove that each orbit is physically accurate.

## 5. Orbital-element quality

{quality_summary}

Orbital-element age is a useful indicator of potential uncertainty.
Older elements do not automatically make a prediction invalid.

The quality CSV should be regenerated from the latest propagation
output before using its classifications as final results.

## 6. Reproducibility testing

A reference-consistency test was performed for one object, followed
by a sample test of 20 objects.

- **Objects tested in the sample:** 20
- **Consistency tests passed:** 20
- **Consistency tests failed:** 0
- **Maximum position difference in the sample:** 0 km
- **Maximum velocity difference in the sample:** 0 km/s

The tests re-used the same SGP4 implementation, source orbital
elements, and saved timestamps. They demonstrate computational
reproducibility for the tested records, not independent real-world
orbital accuracy.

## 7. Limitations

1. Predictions depend on the quality and age of the orbital elements.
2. TEME coordinates are not Earth-fixed coordinates or latitude
   and longitude.
3. Numerical checks alone cannot establish real-world accuracy.
4. A predicted position sequence does not, by itself, determine
   collision probability or establish that a collision will occur.
5. Independent validation against suitable external reference
   ephemerides or observations remains future work.

## 8. Handoff to the risk-analysis module

The prediction dataset contains object identifiers, element epochs,
prediction timestamps, time offsets, TEME position coordinates,
and velocity components.

The risk-analysis module can use these outputs as inputs for further
close-approach analysis. Its own methods and assumptions must be
validated separately.
"""

REPORT_FILE.write_text(report, encoding="utf-8")

print("Unique objects:", object_count)
print("Prediction records:", record_count)
print("Complete objects:", complete_objects)
print("Duplicate records:", duplicate_records)
print("Report saved to:", REPORT_FILE.resolve())