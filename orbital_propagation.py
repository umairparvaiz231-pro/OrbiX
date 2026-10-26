import json
import csv
from pathlib import Path
from datetime import datetime, timedelta, timezone

from sgp4.api import Satrec, jday, SGP4_ERRORS
from sgp4.omm import initialize

# --------------------------------------------------
# OrbiX - Orbital Propagation
# --------------------------------------------------

DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "debris_omm.json"
OUTPUT_FILE = DATA_DIR / "propagated_debris.csv"

# Predict positions at these offsets from the current UTC time
TIME_OFFSETS_MINUTES = [0, 10, 20, 30, 40, 50, 60]

print("OrbiX - Orbital Propagation")
print("-" * 50)

# --------------------------------------------------
# 1. Load orbital records
# --------------------------------------------------

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Orbital data not found: {INPUT_FILE.resolve()}"
    )

with INPUT_FILE.open("r", encoding="utf-8") as file:
    orbital_records = json.load(file)

if not isinstance(orbital_records, list):
    raise ValueError(
        "Expected debris_omm.json to contain a list of orbital records."
    )

print("Orbital records loaded:", len(orbital_records))

# Use one UTC start time for the complete propagation run
start_time = datetime.now(timezone.utc)

# --------------------------------------------------
# 2. Initialize tracking results and error counters
# --------------------------------------------------

results = []

failed_objects = 0
failed_predictions = 0
sgp4_error_counts = {}

# Track objects that produced at least one successful prediction
successful_object_ids = set()

# --------------------------------------------------
# 3. Propagate each object's orbit
# --------------------------------------------------

for record in orbital_records:

    object_id = record.get("NORAD_CAT_ID")
    object_name = record.get("OBJECT_NAME", "Unknown")

    try:
        # Initialize SGP4 using the object's OMM record
        satellite = Satrec()
        initialize(satellite, record)

        object_had_exception = False

        for offset in TIME_OFFSETS_MINUTES:

            prediction_time = start_time + timedelta(
                minutes=offset
            )

            # Convert UTC prediction time to Julian date
            year = prediction_time.year
            month = prediction_time.month
            day = prediction_time.day

            hour = prediction_time.hour
            minute = prediction_time.minute

            second = (
                prediction_time.second
                + prediction_time.microsecond / 1_000_000
            )

            jd, fr = jday(
                year,
                month,
                day,
                hour,
                minute,
                second,
            )

            # Propagate orbit using SGP4
            error_code, position, velocity = satellite.sgp4(
                jd, fr
            )

            # Report unsuccessful propagation attempts
            if error_code != 0:

                failed_predictions += 1

                error_message = SGP4_ERRORS.get(
                    error_code,
                    "Unknown SGP4 error",
                )

                sgp4_error_counts[error_code] = (
                    sgp4_error_counts.get(error_code, 0) + 1
                )

                print(
                    f"SGP4 prediction failed | "
                    f"NORAD ID: {object_id} | "
                    f"Object: {object_name} | "
                    f"Offset: {offset} minutes | "
                    f"Error {error_code}: {error_message}"
                )

                continue

            # Reject non-finite numerical results
            numerical_values = list(position) + list(velocity)

            if not all(
                isinstance(value, (int, float))
                and __import__("math").isfinite(value)
                for value in numerical_values
            ):
                failed_predictions += 1

                print(
                    f"Invalid numerical result | "
                    f"NORAD ID: {object_id} | "
                    f"Offset: {offset} minutes"
                )

                continue

            # Save successful position and velocity prediction
            results.append({
                "NORAD_CAT_ID": object_id,
                "OBJECT_NAME": object_name,
                "ELEMENT_EPOCH": record.get("EPOCH"),
                "PREDICTION_TIME_UTC": prediction_time.isoformat(),
                "MINUTES_FROM_START": offset,
                "X_TEME_KM": position[0],
                "Y_TEME_KM": position[1],
                "Z_TEME_KM": position[2],
                "VX_TEME_KM_S": velocity[0],
                "VY_TEME_KM_S": velocity[1],
                "VZ_TEME_KM_S": velocity[2],
            })

            successful_object_ids.add(object_id)

    except Exception as error:

        failed_objects += 1

        print(
            f"Object processing failed | "
            f"NORAD ID: {object_id} | "
            f"Object: {object_name} | "
            f"Error: {error}"
        )

# --------------------------------------------------
# 4. Save successful predictions to CSV
# --------------------------------------------------

FIELDNAMES = [
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

if results:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        writer.writeheader()
        writer.writerows(results)

else:
    print(
        "\nWARNING: No successful predictions were generated. "
        "The output CSV was not overwritten."
    )

# --------------------------------------------------
# 5. Check prediction completeness
# --------------------------------------------------

expected_predictions = (
    len(orbital_records) * len(TIME_OFFSETS_MINUTES)
)

actual_predictions = len(results)

records_per_object = {}

for row in results:
    object_id = row["NORAD_CAT_ID"]

    records_per_object[object_id] = (
        records_per_object.get(object_id, 0) + 1
    )

incomplete_objects = sum(
    count != len(TIME_OFFSETS_MINUTES)
    for count in records_per_object.values()
)

# --------------------------------------------------
# 6. Display propagation summary
# --------------------------------------------------

print("\nPropagation Summary")
print("-" * 50)

print("Input orbital records:", len(orbital_records))
print(
    "Objects with at least one successful prediction:",
    len(successful_object_ids),
)
print("Objects with processing exceptions:", failed_objects)
print("Successful position predictions:", actual_predictions)
print("Failed prediction attempts:", failed_predictions)
print("Expected prediction records:", expected_predictions)
print("Objects with incomplete prediction sequences:", incomplete_objects)

if sgp4_error_counts:

    print("\nSGP4 Error Breakdown")

    for code, count in sorted(sgp4_error_counts.items()):

        print(
            f"Error {code}: "
            f"{SGP4_ERRORS.get(code, 'Unknown SGP4 error')} "
            f"({count} occurrences)"
        )

else:
    print("\nSGP4 errors: None reported")

if results:

    print("\nOutput file:", OUTPUT_FILE.resolve())
    print("CSV rows written:", actual_predictions)

    if actual_predictions == expected_predictions:
        print("Prediction count check: PASS")
    else:
        print("Prediction count check: REVIEW REQUIRED")

    print(
        "\nCoordinate reference frame: TEME"
        "\nPosition units: kilometres"
        "\nVelocity units: kilometres per second"
        "\nPropagation model: SGP4"
    )

    print(
        "\nNote: These are model-generated orbital estimates. "
        "Their accuracy depends on the orbital elements and "
        "their age. TEME coordinates are not Earth-fixed "
        "coordinates or latitude/longitude."
    )

else:
    print(
        "\nPropagation did not produce any successful predictions."
    )