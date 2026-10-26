import json
from pathlib import Path

import numpy as np
import pandas as pd

from sgp4.api import Satrec, jday
from sgp4.omm import initialize

# --------------------------------------------------
# OrbiX - Multi-Object SGP4 Consistency Test
# --------------------------------------------------

DATA_DIR = Path("data")
OMM_FILE = DATA_DIR / "debris_omm.json"
PREDICTIONS_FILE = DATA_DIR / "propagated_debris.csv"

SAMPLE_SIZE = 20

POSITION_COLUMNS = [
    "X_TEME_KM",
    "Y_TEME_KM",
    "Z_TEME_KM",
]

VELOCITY_COLUMNS = [
    "VX_TEME_KM_S",
    "VY_TEME_KM_S",
    "VZ_TEME_KM_S",
]

print("OrbiX - Multi-Object SGP4 Consistency Test")
print("-" * 50)

# Load source orbital elements
with OMM_FILE.open("r", encoding="utf-8") as file:
    orbital_records = json.load(file)

# Load saved predictions
predictions = pd.read_csv(PREDICTIONS_FILE)

# Use a reproducible sample of available object IDs
available_ids = predictions["NORAD_CAT_ID"].drop_duplicates()

sample_ids = available_ids.head(SAMPLE_SIZE).tolist()

passed = 0
failed = 0

maximum_position_difference = 0.0
maximum_velocity_difference = 0.0

for object_id in sample_ids:

    matching_records = [
        record
        for record in orbital_records
        if str(record.get("NORAD_CAT_ID")) == str(object_id)
    ]

    if not matching_records:
        print(f"FAIL | NORAD ID {object_id}: source record missing")
        failed += 1
        continue

    record = matching_records[0]

    # Use the first saved prediction for this object
    rows = predictions[
        predictions["NORAD_CAT_ID"].astype(str) == str(object_id)
    ]

    if rows.empty:
        print(f"FAIL | NORAD ID {object_id}: prediction missing")
        failed += 1
        continue

    saved = rows.iloc[0]

    try:
        # Reinitialize SGP4 from the source orbital record
        satellite = Satrec()
        initialize(satellite, record)

        # Use the exact saved UTC timestamp
        prediction_time = pd.to_datetime(
            saved["PREDICTION_TIME_UTC"],
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
            print(
                f"FAIL | NORAD ID {object_id}: "
                f"SGP4 error {error_code}"
            )
            failed += 1
            continue

        reference_position = np.asarray(position, dtype=float)
        reference_velocity = np.asarray(velocity, dtype=float)

        saved_position = saved[POSITION_COLUMNS].to_numpy(dtype=float)
        saved_velocity = saved[VELOCITY_COLUMNS].to_numpy(dtype=float)

        position_difference = float(
            np.max(np.abs(reference_position - saved_position))
        )

        velocity_difference = float(
            np.max(np.abs(reference_velocity - saved_velocity))
        )

        maximum_position_difference = max(
            maximum_position_difference,
            position_difference,
        )

        maximum_velocity_difference = max(
            maximum_velocity_difference,
            velocity_difference,
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

        if position_match and velocity_match:
            passed += 1
            print(
                f"PASS | NORAD ID {object_id} | "
                f"Position difference: {position_difference:.3e} km | "
                f"Velocity difference: {velocity_difference:.3e} km/s"
            )
        else:
            failed += 1
            print(
                f"FAIL | NORAD ID {object_id} | "
                f"Position difference: {position_difference:.3e} km | "
                f"Velocity difference: {velocity_difference:.3e} km/s"
            )

    except Exception as error:
        failed += 1
        print(f"FAIL | NORAD ID {object_id}: {error}")

print("\nTest Summary")
print("-" * 50)
print("Objects tested:", len(sample_ids))
print("Passed:", passed)
print("Failed:", failed)

print(
    "Maximum position difference (km):",
    f"{maximum_position_difference:.12g}",
)

print(
    "Maximum velocity difference (km/s):",
    f"{maximum_velocity_difference:.12g}",
)

if failed == 0 and passed == len(sample_ids):
    print("\nRESULT: PASS")
else:
    print("\nRESULT: REVIEW REQUIRED")