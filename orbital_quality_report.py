import pandas as pd
from pathlib import Path

# OrbitVision - Orbital Data Quality Report

INPUT_FILE = Path("data/propagated_debris.csv")
OUTPUT_FILE = Path("data/orbital_quality_report.csv")

print("OrbitVision - Orbital Data Quality Report")
print("-" * 45)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"File not found: {INPUT_FILE}"
    )

data = pd.read_csv(INPUT_FILE)

# Convert timestamps to UTC
data["ELEMENT_EPOCH"] = pd.to_datetime(
    data["ELEMENT_EPOCH"],
    utc=True,
    errors="coerce"
)

data["PREDICTION_TIME_UTC"] = pd.to_datetime(
    data["PREDICTION_TIME_UTC"],
    utc=True,
    errors="coerce"
)

# Calculate age of the orbital elements
data["ELEMENT_AGE_HOURS"] = (
    data["PREDICTION_TIME_UTC"] - data["ELEMENT_EPOCH"]
).dt.total_seconds() / 3600

# Keep the first prediction for each object
objects = (
    data.sort_values("MINUTES_FROM_START")
    .drop_duplicates(subset="NORAD_CAT_ID")
    .copy()
)

# Assign age-based review categories.
# These are project screening thresholds, not guarantees of accuracy.
def classify_age(hours):
    if pd.isna(hours):
        return "Unknown"
    elif hours < 24:
        return "Recent"
    elif hours < 72:
        return "Review Recommended"
    else:
        return "Stale - Review Required"

objects["DATA_QUALITY_STATUS"] = (
    objects["ELEMENT_AGE_HOURS"].apply(classify_age)
)

# Save one report row per debris object
objects.to_csv(OUTPUT_FILE, index=False)

print("Unique objects assessed:", len(objects))
print("\nOrbital element age categories:")
print(
    objects["DATA_QUALITY_STATUS"]
    .value_counts()
    .to_string()
)

print("\nMedian element age (hours):",
      round(objects["ELEMENT_AGE_HOURS"].median(), 2))

print("Maximum element age (hours):",
      round(objects["ELEMENT_AGE_HOURS"].max(), 2))

print("\nReport saved to:", OUTPUT_FILE.resolve())