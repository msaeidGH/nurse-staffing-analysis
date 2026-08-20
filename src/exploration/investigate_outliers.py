import pandas as pd

df = pd.read_parquet("data/processed/pbj_q2_2024_cleaned.parquet")

# Investigate the zero-ratio facility — look at raw daily data, not the aggregate
white_river = df[df["PROVNAME"] == "WHITE RIVER HEALTHCARE"]
print("--- White River Healthcare, daily detail ---")
print(white_river[["WorkDate", "MDScensus", "Hrs_RN", "Hrs_LPN", "Hrs_CNA",
                    "Hrs_RNDON", "Hrs_RNadmin", "Hrs_LPNadmin", "Hrs_MedAide"]].head(10))

# Find the facility-month with the extreme max ratio (217)
fm = pd.read_parquet("data/processed/facility_month_summary.parquet")
extreme = fm.nlargest(3, "Nurse_to_Patient_Ratio")
print("\n--- Extreme high-ratio facilities ---")
print(extreme[["PROVNAME", "STATE", "Month", "Nurse_to_Patient_Ratio",
                "Total_Direct_Care_Hours", "Census_Sum_ExclZero", "Avg_MDScensus"]])

# Check that specific facility's daily census — a tiny denominator would explain a huge ratio
extreme_provnum = extreme.iloc[0]["PROVNAME"]
print(f"\n--- Daily detail for {extreme_provnum} ---")
print(df[df["PROVNAME"] == extreme_provnum][
    ["WorkDate", "MDScensus", "Hrs_RN", "Hrs_LPN", "Hrs_CNA"]].head(10))