import pandas as pd

# Specify dtypes up front — this is what keeps memory sane on 1.3M rows.
# WorkDate stays as string here on purpose; we convert it explicitly next step,
# not silently via parse_dates, so the conversion is visible and checkable.
dtypes = {
    "PROVNUM": "string",
    "PROVNAME": "string",
    "CITY": "string",
    "STATE": "string",
    "COUNTY_NAME": "string",
    "COUNTY_FIPS": "string",
    "CY_Qtr": "string",
    "WorkDate": "string",
    "MDScensus": "float32",
}
# All the Hrs_* columns are numeric — fill in float32 for the rest
hrs_cols = [c for c in pd.read_csv("data/raw/PBJ_Daily_Nurse_Staffing_Q2_2024.csv", nrows=0).columns
            if c.startswith("Hrs_")]
for c in hrs_cols:
    dtypes[c] = "float32"

df = pd.read_csv("data/raw/PBJ_Daily_Nurse_Staffing_Q2_2024.csv", dtype=dtypes, engine="pyarrow", encoding="cp1252")

print("Shape:", df.shape)
print("\nColumn dtypes:\n", df.dtypes)
print("\nMemory usage (MB):", df.memory_usage(deep=True).sum() / 1e6)

print("\n--- Facility-level ---")
print("Unique facilities (PROVNUM):", df["PROVNUM"].nunique())
print("Unique states:", df["STATE"].nunique())
print("Date range:", df["WorkDate"].min(), "to", df["WorkDate"].max())

print("\n--- Missing values (top 15) ---")
print(df.isna().sum().sort_values(ascending=False).head(15))

print("\n--- Duplicate rows ---")
print("Exact duplicate rows:", df.duplicated().sum())
print("Duplicate PROVNUM+WorkDate pairs:", df.duplicated(subset=["PROVNUM", "WorkDate"]).sum())

print("\n--- MDScensus sanity check ---")
print(df["MDScensus"].describe())
print("Rows with census = 0:", (df["MDScensus"] == 0).sum())

print("\n--- Reporting completeness ---")
# Each facility should report once per day in the quarter (91 days for Q2 2024).
counts = df.groupby("PROVNUM")["WorkDate"].count()
print(counts.describe())

# Add to your script, after the census check
print("\n--- Staffing hours outlier check ---")
for col in hrs_cols:
    print(f"{col}: min={df[col].min():.1f}, max={df[col].max():.1f}, "
          f"99th pct={df[col].quantile(0.99):.1f}, negative values={(df[col] < 0).sum()}")


# Find the problem row(s)
suspect = df[df["Hrs_LPN"] > 1000].sort_values("Hrs_LPN", ascending=False)
print(suspect[["PROVNUM", "PROVNAME", "STATE", "WorkDate", "MDScensus",
               "Hrs_LPN", "Hrs_LPN_emp", "Hrs_LPN_ctr"]].head(10))
print("\nRows with Hrs_LPN > 1000:", (df["Hrs_LPN"] > 1000).sum())

# Flag and correct the known bad data point (documented data quality issue)
bad_row_mask = (df["PROVNUM"] == "145446") & (df["WorkDate"] == "20240525")
print("Before fix:")
print(df.loc[bad_row_mask, ["Hrs_LPN", "Hrs_LPN_emp", "Hrs_LPN_ctr"]])

df.loc[bad_row_mask, "Hrs_LPN_ctr"] = pd.NA
df.loc[bad_row_mask, "Hrs_LPN"] = pd.NA  # recompute as emp + ctr once ctr is fixed, see below

print("\nAfter fix:")
print(df.loc[bad_row_mask, ["Hrs_LPN", "Hrs_LPN_emp", "Hrs_LPN_ctr"]])


