import pandas as pd

facility_month = pd.read_parquet("data/processed/facility_month_summary.parquet")
state_month = pd.read_parquet("data/processed/state_month_summary.parquet")

reliable = facility_month[
    ~facility_month["Low_Census_Flag"] & ~facility_month["Zero_Direct_Care_Flag"]
]

state_reliable = reliable.groupby("STATE")["Nurse_to_Patient_Ratio"].mean().sort_values()
print(state_reliable.head(10))

mo_flagged = facility_month[facility_month["STATE"] == "MO"]
print(f"\nMissouri facility-months: {len(mo_flagged)}")
print(f"Missouri flagged (low census or zero direct care): "
      f"{(mo_flagged['Low_Census_Flag'] | mo_flagged['Zero_Direct_Care_Flag']).sum()}")

