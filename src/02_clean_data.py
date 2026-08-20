'''
4. Data Cleaning

Perform the following cleaning steps:
• Handle missing values where appropriate
• Remove duplicate rowsc
• Ensure WorkDate is in datetime format
• Verify that staffing hours are numeric
• Check unrealistic staffing values (extreme outliers)
• Create derived columns for total nurse hours
'''

import pandas as pd

# --- Load with same settings as EDA ---
dtypes = {
    "PROVNUM": "category",
    "PROVNAME": "string",
    "CITY": "string",
    "STATE": "category",
    "COUNTY_NAME": "string",
    "COUNTY_FIPS": "string",
    "CY_Qtr": "string",
    "WorkDate": "string",
    "MDScensus": "float32",
}
hrs_cols = [c for c in pd.read_csv(
    "data/raw/PBJ_Daily_Nurse_Staffing_Q2_2024.csv", nrows=0).columns if c.startswith("Hrs_")]
for c in hrs_cols:
    dtypes[c] = "float32"

df = pd.read_csv(
    "data/raw/PBJ_Daily_Nurse_Staffing_Q2_2024.csv",
    dtype=dtypes, engine="pyarrow", encoding="cp1252"
)
print("Loaded:", df.shape)

# --- 1 & 2: confirm no missing values, no duplicates (should be 0, this proves it) ---
assert df.isna().sum().sum() == 0, "Unexpected missing values found"
assert df.duplicated().sum() == 0, "Unexpected exact duplicates found"
assert df.duplicated(subset=["PROVNUM", "WorkDate"]).sum() == 0, "Unexpected duplicate facility-day rows"
print("Missing values: 0 (confirmed) | Duplicates: 0 (confirmed)")

# --- 3: WorkDate to real datetime ---
df["WorkDate"] = pd.to_datetime(df["WorkDate"], format="%Y%m%d")
print("WorkDate dtype now:", df["WorkDate"].dtype)

# --- 4: staffing hours numeric — already guaranteed by dtype at load; confirm ---
assert all(df[c].dtype == "float32" for c in hrs_cols), "Non-numeric staffing column found"

# --- 5: apply the known outlier correction (documented data quality fix) ---
bad_row_mask = (df["PROVNUM"] == "145446") & (df["WorkDate"] == pd.Timestamp("2024-05-25"))
n_flagged = bad_row_mask.sum()
print(f"Applying known data quality fix to {n_flagged} row(s): Marigold Rehabilitation HCC, 2024-05-25")
df.loc[bad_row_mask, "Hrs_LPN_ctr"] = pd.NA
df.loc[bad_row_mask, "Hrs_LPN"] = pd.NA

# --- 6: derived columns ---
all_hours_cols = ["Hrs_RNDON", "Hrs_RNadmin", "Hrs_RN", "Hrs_LPNadmin", "Hrs_LPN",
                   "Hrs_CNA", "Hrs_NAtrn", "Hrs_MedAide"]
df["Total_Nurse_Hours_All"] = df[all_hours_cols].sum(axis=1, skipna=True)

direct_care_cols = ["Hrs_RN", "Hrs_LPN", "Hrs_CNA"]
df["Total_Direct_Care_Hours"] = df[direct_care_cols].sum(axis=1, skipna=True)

contract_cols = [c for c in hrs_cols if c.endswith("_ctr")]
df["Total_Contract_Hours"] = df[contract_cols].sum(axis=1, skipna=True)

# --- flag (don't drop) zero-census rows, for use in ratio calc later ---
df["Zero_Census_Flag"] = df["MDScensus"] == 0
print("Zero-census rows flagged:", df["Zero_Census_Flag"].sum())

# --- save cleaned output ---
df.to_parquet("data/processed/pbj_q2_2024_cleaned.parquet", index=False)
print("Saved cleaned data:", df.shape)