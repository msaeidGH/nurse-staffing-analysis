
import pandas as pd

fm = pd.read_parquet("data/processed/facility_month_summary.parquet")

print("--- Top 5 facilities by Total_Nurse_Hours_All (any month) ---")
print(fm.nlargest(5, "Total_Nurse_Hours_All")[
    ["PROVNAME", "STATE", "Month", "Total_Nurse_Hours_All", "Avg_MDScensus"]])

print("\n--- Lowest nurse-to-patient ratio (potential understaffing) ---")
print(fm.nsmallest(5, "Nurse_to_Patient_Ratio")[
    ["PROVNAME", "STATE", "Month", "Nurse_to_Patient_Ratio", "Avg_MDScensus", "Days_Reported"]])

print("\n--- Highest contract ratio ---")
print(fm.nlargest(5, "Contract_Ratio")[
    ["PROVNAME", "STATE", "Month", "Contract_Ratio", "Total_Nurse_Hours_All"]])

print("\n--- Nurse_to_Patient_Ratio distribution ---")
print(fm["Nurse_to_Patient_Ratio"].describe())