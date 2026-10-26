import json
import csv
from pathlib import Path
from datetime import datetime, timedelta, timezone

from sgp4.api import Satrec, jday
from sgp4.omm import initialize

# --------------------------------------------------
# OrbitVision - Orbital Propagation
# --------------------------------------------------

DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "debris_omm.json"
OUTPUT_FILE = DATA_DIR / "propagated_debris.csv"

# Forecast positions at these offsets from the current UTC time
TIME_OFFSETS_MINUTES = [0, 10, 20, 30, 40, 50, 60]

print("OrbitVision - Orbital Propagation")
print("-" * 45)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Orbital data not found: {INPUT_FILE}"
    )

with INPUT_FILE.open("r", encoding="utf-8") as file:
    orbital_records = json.load(file)

print("Orbital records loaded:", len(orbital_records))

# Use the current UTC time as the propagation start time
start_time = datetime.now(timezone.utc)

results = []
failed_objects = 0

for record in orbital_records:
    try:
        satellite = Satrec()
        initialize(satellite, record)

        for offset in TIME_OFFSETS_MINUTES:
            prediction_time = start_time + timedelta(
                minutes=offset
            )

            # Convert prediction time to Julian date
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
                year, month, day,
                hour, minute, second
            )

            # Propagate orbit using SGP4
            error_code, position, velocity = satellite.sgp4(
                jd, fr
            )

            if error_code != 0:
                continue

            results.append({
                "NORAD_CAT_ID": record.get("NORAD_CAT_ID"),
                "OBJECT_NAME": record.get("OBJECT_NAME"),
                "ELEMENT_EPOCH": record.get("EPOCH"),
                "PREDICTION_TIME_UTC": (
                    prediction_time.isoformat()
                ),
                "MINUTES_FROM_START": offset,
                "X_TEME_KM": position[0],
                "Y_TEME_KM": position[1],
                "Z_TEME_KM": position[2],
                "VX_TEME_KM_S": velocity[0],
                "VY_TEME_KM_S": velocity[1],
                "VZ_TEME_KM_S": velocity[2],
            })

    except Exception as error:
        failed_objects += 1
        print(
            "Could not propagate NORAD ID",
            record.get("NORAD_CAT_ID"),
            "-",
            error
        )

# Save results to CSV
if results:
    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys()
        )
        writer.writeheader()
        writer.writerows(results)

print("\nPropagation summary")
print("-" * 45)
print("Input orbital records:", len(orbital_records))
print("Successful position predictions:", len(results))
print("Objects with processing errors:", failed_objects)

if results:
    print("Output file:", OUTPUT_FILE.resolve())
    print("CSV rows:", len(results))
    print(
        "\nNote: Positions are in the TEME reference frame "
        "and are estimates from SGP4."
    )
else:
    print(
        "No positions were generated. Check the errors above."
    )