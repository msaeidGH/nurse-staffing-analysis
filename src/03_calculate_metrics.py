'''
Step 5 — building the actual metrics from the requirements doc:

1- Nurse-to-Patient Ratio (using Total_Direct_Care_Hours, excluding the 320 zero-census rows)
2- Total Nurse Hours (grouped by facility / state / month, using Total_Nurse_Hours_All)
3- Contract vs Permanent Staff Ratio (Total_Contract_Hours / Total_Nurse_Hours_All)
4- Average Patient Census (by facility / state)
5- Hospitals — well, facilities — with Highest Staffing Hours (correcting the doc's wording again, since these are nursing homes, not hospitals)

'''

import pandas as pd

df = pd.read_parquet("data/processed/pbj_q2_2024_cleaned.parquet")
print("Loaded:", df.shape)

df["Month"] = df["WorkDate"].dt.to_period("M").astype(str)

# --- Facility-month aggregation ---
facility_month = df.groupby(["PROVNUM", "PROVNAME", "STATE", "Month"], observed=True).agg(
    Total_Nurse_Hours_All=("Total_Nurse_Hours_All", "sum"),
    Total_Direct_Care_Hours=("Total_Direct_Care_Hours", "sum"),
    Total_Contract_Hours=("Total_Contract_Hours", "sum"),
    Avg_MDScensus=("MDScensus", "mean"),
    Days_Reported=("WorkDate", "count"),
    Zero_Census_Days=("Zero_Census_Flag", "sum"),
).reset_index()

# Ratio metrics — computed AFTER aggregation, on summed totals, not averaged daily ratios.
# Averaging a ratio across days is mathematically wrong (it weights a 5-census day
# the same as a 100-census day); summing hours and census separately, then dividing
# once, weights each day correctly.
nonzero_census_totals = df[~df["Zero_Census_Flag"]].groupby(
    ["PROVNUM", "Month"], observed=True
)["MDScensus"].sum().rename("Census_Sum_ExclZero")

facility_month = facility_month.merge(
    nonzero_census_totals, on=["PROVNUM", "Month"], how="left"
)
facility_month["Nurse_to_Patient_Ratio"] = (
    facility_month["Total_Direct_Care_Hours"] / facility_month["Census_Sum_ExclZero"]
)
facility_month["Contract_Ratio"] = (
    facility_month["Total_Contract_Hours"] / facility_month["Total_Nurse_Hours_All"]
)

# --- State-month aggregation ---
state_month = df.groupby(["STATE", "Month"], observed=True).agg(
    Total_Nurse_Hours_All=("Total_Nurse_Hours_All", "sum"),
    Total_Direct_Care_Hours=("Total_Direct_Care_Hours", "sum"),
    Total_Contract_Hours=("Total_Contract_Hours", "sum"),
    Avg_MDScensus=("MDScensus", "mean"),
    Facility_Count=("PROVNUM", "nunique"),
).reset_index()

state_nonzero_census = df[~df["Zero_Census_Flag"]].groupby(
    ["STATE", "Month"], observed=True
)["MDScensus"].sum().rename("Census_Sum_ExclZero")

state_month = state_month.merge(state_nonzero_census, on=["STATE", "Month"], how="left")
state_month["Nurse_to_Patient_Ratio"] = (
    state_month["Total_Direct_Care_Hours"] / state_month["Census_Sum_ExclZero"]
)
state_month["Contract_Ratio"] = (
    state_month["Total_Contract_Hours"] / state_month["Total_Nurse_Hours_All"]
)

state_month.to_parquet("data/processed/state_month_summary.parquet", index=False)
print("State-month table:", state_month.shape)


# --- Flag facilities where the ratio metric isn't meaningful ---
MIN_CENSUS_THRESHOLD = 10

facility_month["Low_Census_Flag"] = facility_month["Avg_MDScensus"] < MIN_CENSUS_THRESHOLD
facility_month["Zero_Direct_Care_Flag"] = (
    (facility_month["Total_Direct_Care_Hours"] == 0) &
    (facility_month["Total_Nurse_Hours_All"] > 0)
)

print(f"Facility-months below census threshold ({MIN_CENSUS_THRESHOLD}): "
      f"{facility_month['Low_Census_Flag'].sum()}")
print(f"Facility-months with zero direct-care hours but nonzero total hours: "
      f"{facility_month['Zero_Direct_Care_Flag'].sum()}")

facility_month.to_parquet("data/processed/facility_month_summary.parquet", index=False)

