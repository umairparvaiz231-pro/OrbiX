import json
from pathlib import Path

import numpy as np
import pandas as pd
from sgp4.api import Satrec, jday
from sgp4.omm import initialize

DATA_DIR = Path("data")
OMM_FILE = DATA_DIR / "debris_omm.json"
PREDICTIONS_FILE = DATA_DIR / "propagated_debris.csv"

print("OrbiX - SGP4 Reference Consistency Test")
print("-" * 50)

with OMM_FILE.open("r", encoding="utf-8") as file:
    orbital_records = json.load(file)

predictions = pd.read_csv(PREDICTIONS_FILE)

# Select the first object with an available prediction.
record = None
prediction = None

for candidate in orbital_records:
    object_id = candidate.get("NORAD_CAT_ID")

    matches = predictions[
        predictions["NORAD_CAT_ID"] == object_id
    ]

    if not matches.empty:
        record = candidate
        prediction = matches.iloc[0]
        break

if record is None:
    raise RuntimeError("No matching orbital record found.")

# Reinitialize SGP4 independently from the saved OMM record.
satellite = Satrec()
initialize(satellite, record)

# Use the exact UTC timestamp stored in the CSV.
prediction_time = pd.to_datetime(
    prediction["PREDICTION_TIME_UTC"],
    utc=True,
)

jd, fr = jday(
    prediction_time.year,
    prediction_time.month,
    prediction_time.day,
    prediction_time.hour,
    prediction_time.minute,
    prediction_time.second
    + prediction_time.microsecond / 1_000_000,
)

error_code, position, velocity = satellite.sgp4(jd, fr)

if error_code != 0:
    raise RuntimeError(
        f"SGP4 returned error code {error_code}."
    )

reference_position = np.array(position, dtype=float)
reference_velocity = np.array(velocity, dtype=float)

saved_position = prediction[
    ["X_TEME_KM", "Y_TEME_KM", "Z_TEME_KM"]
].to_numpy(dtype=float)

saved_velocity = prediction[
    ["VX_TEME_KM_S", "VY_TEME_KM_S", "VZ_TEME_KM_S"]
].to_numpy(dtype=float)

position_difference = np.abs(
    reference_position - saved_position
)

velocity_difference = np.abs(
    reference_velocity - saved_velocity
)

print("NORAD ID:", record.get("NORAD_CAT_ID"))
print("Object:", record.get("OBJECT_NAME"))
print("Prediction time:", prediction_time.isoformat())

print("\nPosition comparison (km)")
print("Reference:", reference_position)
print("Saved CSV:", saved_position)
print("Absolute differences:", position_difference)
print(
    "Maximum position difference (km):",
    f"{position_difference.max():.12g}",
)

print("\nVelocity comparison (km/s)")
print("Reference:", reference_velocity)
print("Saved CSV:", saved_velocity)
print("Absolute differences:", velocity_difference)
print(
    "Maximum velocity difference (km/s):",
    f"{velocity_difference.max():.12g}",
)

position_match = np.allclose(
    reference_position,
    saved_position,
    rtol=1e-9,
    atol=1e-6,
)

velocity_match = np.allclose(
    reference_velocity,
    saved_velocity,
    rtol=1e-9,
    atol=1e-9,
)

print("\nRESULT")
print("Position consistency:", "PASS" if position_match else "FAIL")
print("Velocity consistency:", "PASS" if velocity_match else "FAIL")

if not (position_match and velocity_match):
    raise SystemExit(
        "Reference consistency test failed. Investigate the differences."
    )