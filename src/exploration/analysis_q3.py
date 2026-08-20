import pandas as pd

facility_month = pd.read_parquet("data/processed/facility_month_summary.parquet")
state_month = pd.read_parquet("data/processed/state_month_summary.parquet")


print(state_month.groupby("STATE")["Total_Nurse_Hours_All"].mean().sort_values(ascending=False).head(10))

# Average total nurse hours PER FACILITY, per month, by state — normalizes out state size
per_facility = facility_month.groupby("STATE").agg(
    Avg_Hours_Per_Facility=("Total_Nurse_Hours_All", "mean"),
    Facility_Count=("PROVNUM", "nunique")
).sort_values("Avg_Hours_Per_Facility", ascending=False)

print(per_facility.head(10))
print("\n--- Lowest ---")
print(per_facility.tail(10))