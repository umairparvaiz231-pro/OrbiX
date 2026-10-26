import pandas as pd
from pathlib import Path

# ==========================================
# ORBITVISION - SPACE DEBRIS TRACKING SYSTEM
# Step 8: Dataset Validation
# ==========================================

file_path = Path("data/clean_space_debris copy.csv")

# Check if the file exists
if not file_path.exists():
    raise FileNotFoundError(f"Dataset not found: {file_path}")

# Load the dataset
debris_data = pd.read_csv(file_path)

print("\n========== ORBITVISION ==========")
print("SPACE DEBRIS TRACKING SYSTEM")
print("=================================\n")

# 1. Dataset size
print("1. DATASET INFORMATION")
print("Total debris records:", len(debris_data))
print("Total columns:", len(debris_data.columns))

# 2. Required orbital parameters
required_columns = [
    "OBJECT_NAME",
    "NORAD_CAT_ID",
    "EPOCH",
    "MEAN_MOTION",
    "ECCENTRICITY",
    "INCLINATION",
    "RA_OF_ASC_NODE",
    "ARG_OF_PERICENTER",
    "MEAN_ANOMALY"
]

print("\n2. REQUIRED COLUMN CHECK")

for column in required_columns:
    if column in debris_data.columns:
        print(f"{column}: Available")
    else:
        print(f"{column}: MISSING")

# 3. Missing values
print("\n3. MISSING VALUES")
print(debris_data[required_columns].isnull().sum())

# 4. Duplicate records
print("\n4. DUPLICATE RECORDS")
print("Duplicate rows:", debris_data.duplicated().sum())

# 5. Validate numeric orbital parameters
numeric_columns = [
    "MEAN_MOTION",
    "ECCENTRICITY",
    "INCLINATION",
    "RA_OF_ASC_NODE",
    "ARG_OF_PERICENTER",
    "MEAN_ANOMALY"
]

print("\n5. ORBITAL PARAMETER VALIDATION")

for column in numeric_columns:
    values = pd.to_numeric(debris_data[column], errors="coerce")
    invalid_count = values.isna().sum()
    print(f"{column}: {invalid_count} missing or non-numeric values")

# 6. Check basic orbital ranges
eccentricity = pd.to_numeric(
    debris_data["ECCENTRICITY"], errors="coerce"
)

mean_motion = pd.to_numeric(
    debris_data["MEAN_MOTION"], errors="coerce"
)

inclination = pd.to_numeric(
    debris_data["INCLINATION"], errors="coerce"
)

print("\n6. BASIC ORBITAL RANGE CHECKS")
print("Eccentricity outside [0, 1):",
      ((eccentricity < 0) | (eccentricity >= 1)).sum())

print("Mean motion <= 0:",
      (mean_motion <= 0).sum())

print("Inclination outside [0, 180]:",
      ((inclination < 0) | (inclination > 180)).sum())

print("\n========== VALIDATION COMPLETE ==========")
# ==========================================
# STEP 9: ORBITAL DATA SUMMARY
# ==========================================

print("\n========== ORBITAL DATA SUMMARY ==========")

# Display the first five debris objects
print("\nFirst five debris objects:")

print(
    debris_data[
        [
            "OBJECT_NAME",
            "NORAD_CAT_ID",
            "EPOCH",
            "MEAN_MOTION",
            "ECCENTRICITY",
            "INCLINATION",
        ]
    ].head()
)

# Check the observation epochs
debris_data["EPOCH"] = pd.to_datetime(
    debris_data["EPOCH"],
    errors="coerce",
    utc=True
)

print("\nEarliest epoch:", debris_data["EPOCH"].min())
print("Latest epoch:", debris_data["EPOCH"].max())

# Count objects with valid epochs
print(
    "Objects with invalid epochs:",
    debris_data["EPOCH"].isna().sum()
)

print("\n========== SUMMARY COMPLETE ==========")
