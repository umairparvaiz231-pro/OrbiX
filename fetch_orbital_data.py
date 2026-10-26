import time
import pandas as pd
import requests
from pathlib import Path

# File locations
DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "clean_space_debris copy.csv"
OUTPUT_FILE = DATA_DIR / "debris_omm.json"

print("OrbitVision - Orbital Data Retrieval")
print("-" * 40)

# Check whether the input file exists
if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Dataset not found: {INPUT_FILE}")

# Read the cleaned dataset
debris_data = pd.read_csv(INPUT_FILE)

# Extract unique NORAD catalog numbers
norad_ids = (
    pd.to_numeric(
        debris_data["NORAD_CAT_ID"],
        errors="coerce"
    )
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

print("Debris objects in dataset:", len(norad_ids))

# CelesTrak supports one CATNR per request.
# Retrieve objects individually and save successful results.
url = "https://celestrak.org/NORAD/elements/gp.php"

session = requests.Session()
records = []
failed_ids = []

for index, norad_id in enumerate(norad_ids, start=1):
    try:
        response = session.get(
            url,
            params={
                "CATNR": norad_id,
                "FORMAT": "JSON"
            },
            timeout=30
        )

        if response.status_code == 404:
            failed_ids.append(norad_id)
            print(
                f"[{index}/{len(norad_ids)}] "
                f"No current orbital data: {norad_id}"
            )
            continue

        response.raise_for_status()
        result = response.json()

        if isinstance(result, dict):
            result = [result]

        matching_records = [
            item for item in result
            if str(item.get("NORAD_CAT_ID", "")) == str(norad_id)
        ]

        if matching_records:
            records.extend(matching_records)
            print(
                f"[{index}/{len(norad_ids)}] "
                f"Retrieved: {norad_id}"
            )
        else:
            failed_ids.append(norad_id)
            print(
                f"[{index}/{len(norad_ids)}] "
                f"No matching record: {norad_id}"
            )

        # Be considerate of the data provider.
        time.sleep(0.5)

    except requests.RequestException as error:
        print(f"\nRequest failed for NORAD {norad_id}: {error}")
        print("Stopping to avoid repeated requests.")
        break

    except ValueError as error:
        print(f"\nInvalid JSON for NORAD {norad_id}: {error}")
        print("Stopping to inspect the response.")
        break

# Save any records retrieved successfully
if records:
    pd.DataFrame(records).drop_duplicates(
        subset=["NORAD_CAT_ID"]
    ).to_json(
        OUTPUT_FILE,
        orient="records",
        indent=2
    )

    print("\nRetrieval summary")
    print("-" * 40)
    print("Records saved:", len(records))
    print("Output file:", OUTPUT_FILE.resolve())
    print("IDs without retrieved data:", len(failed_ids))
else:
    print("\nNo orbital records were retrieved.")
    print("No JSON output file was created.")