import pandas as pd
import numpy as np
from pathlib import Path

# --------------------------------------------------
# OrbiX - Orbital Prediction Validation
# --------------------------------------------------

DATA_FILE = Path("data/propagated_debris.csv")

TIME_OFFSETS = [0, 10, 20, 30, 40, 50, 60]

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

print("OrbiX - Orbital Prediction Validation")
print("-" * 45)

if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Prediction file not found: {DATA_FILE}"
    )

df = pd.read_csv(DATA_FILE)

required_columns = [
    "NORAD_CAT_ID",
    "OBJECT_NAME",
    "PREDICTION_TIME_UTC",
    "MINUTES_FROM_START",
    *POSITION_COLUMNS,
    *VELOCITY_COLUMNS,
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

# 1. Basic dataset information
print("\n1. DATASET SUMMARY")
print("Total prediction records:", len(df))

unique_objects = df["NORAD_CAT_ID"].nunique()
print("Unique objects:", unique_objects)

# 2. Check missing values
print("\n2. MISSING VALUES")
missing_count = int(df[required_columns].isna().sum().sum())
print("Missing required values:", missing_count)

# 3. Check infinite or invalid numerical values
print("\n3. NUMERICAL VALIDITY")

numeric_columns = POSITION_COLUMNS + VELOCITY_COLUMNS

numeric_data = df[numeric_columns].to_numpy(dtype=float)

finite_mask = np.isfinite(numeric_data).all(axis=1)

print("Rows with finite coordinates and velocities:",
      int(finite_mask.sum()))

print("Rows with invalid numerical values:",
      int((~finite_mask).sum()))

# 4. Check prediction intervals
print("\n4. PREDICTION INTERVALS")

actual_offsets = sorted(
    df["MINUTES_FROM_START"].dropna().unique().tolist()
)

print("Observed offsets:", actual_offsets)

print("Expected offsets:", TIME_OFFSETS)

# 5. Check records per object
print("\n5. RECORD COMPLETENESS")

records_per_object = df.groupby("NORAD_CAT_ID").size()

complete_objects = int(
    (records_per_object == len(TIME_OFFSETS)).sum()
)

incomplete_objects = int(
    (records_per_object != len(TIME_OFFSETS)).sum()
)

print("Objects with seven records:", complete_objects)
print("Objects with an unexpected record count:",
      incomplete_objects)

# Check for duplicate object/offset combinations
duplicate_count = int(
    df.duplicated(
        subset=["NORAD_CAT_ID", "MINUTES_FROM_START"]
    ).sum()
)

print("Duplicate object/offset records:", duplicate_count)

# 6. Calculate orbital radius and speed
print("\n6. POSITION AND VELOCITY MAGNITUDES")

positions = df[POSITION_COLUMNS].to_numpy(dtype=float)
velocities = df[VELOCITY_COLUMNS].to_numpy(dtype=float)

radius_km = np.linalg.norm(positions, axis=1)
speed_km_s = np.linalg.norm(velocities, axis=1)

valid_rows = finite_mask

if valid_rows.any():
    valid_radius = radius_km[valid_rows]
    valid_speed = speed_km_s[valid_rows]

    print(
        "Orbital radius range (km):",
        round(float(valid_radius.min()), 2),
        "to",
        round(float(valid_radius.max()), 2),
    )

    print(
        "Speed range (km/s):",
        round(float(valid_speed.min()), 4),
        "to",
        round(float(valid_speed.max()), 4),
    )

    # Earth mean radius is approximately 6371 km.
    # This is a screening check, not a complete orbit-validity test.
    below_earth_radius = int(
        (valid_radius < 6371).sum()
    )

    print(
        "Predicted positions inside mean Earth radius:",
        below_earth_radius,
    )

else:
    print("No rows have fully finite coordinates and velocities.")

# 7. Final summary
print("\n7. VALIDATION SUMMARY")
print("-" * 45)

print("Checks completed.")
print(
    "Review the results before deciding whether "
    "the predictions are scientifically acceptable."
)