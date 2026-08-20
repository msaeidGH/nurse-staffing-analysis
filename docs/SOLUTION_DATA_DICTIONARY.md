# Solution Data Dictionary

This document explains the columns **created by this project's pipeline** — derived metrics, flags, and aggregation keys that do not exist in the original CMS source file. For the original raw columns (`Hrs_RN`, `MDScensus`, `PROVNUM`, etc.), see `docs/NH_Data_Dictionary.pdf`, published by CMS.

There are three output files. Each is documented separately below.

---

## 1. `data/processed/pbj_q2_2024_cleaned.parquet`

Row grain: one row per facility per day (same grain as the raw CMS file). Produced by `src/02_clean_data.py`.

| Column | Type | Description | How it's calculated |
|---|---|---|---|
| `WorkDate` | datetime | Calendar date of the record | Converted from the raw `YYYYMMDD` string format |
| `Total_Nurse_Hours_All` | float | Full nursing payroll hours for the facility that day, across every nursing role | Sum of `Hrs_RNDON + Hrs_RNadmin + Hrs_RN + Hrs_LPNadmin + Hrs_LPN + Hrs_CNA + Hrs_NAtrn + Hrs_MedAide` |
| `Total_Direct_Care_Hours` | float | Hours spent on direct resident care only — excludes management/admin/training roles | Sum of `Hrs_RN + Hrs_LPN + Hrs_CNA` |
| `Total_Contract_Hours` | float | Hours worked by contracted/agency staff, across all roles | Sum of every `*_ctr` column |
| `Zero_Census_Flag` | boolean | True if the facility reported 0 residents that day | `MDScensus == 0` |

**Known data correction applied:** one row (facility 145446, Marigold Rehabilitation HCC, IL, 2024-05-25) had an implausible `Hrs_LPN_ctr` value (13,801.5 hours in a single day). That value and the dependent `Hrs_LPN` total were set to null for this row only; all other columns for that row are unaffected. See README Methodology section for full reasoning.

---

## 2. `data/processed/facility_month_summary.parquet`

Row grain: one row per facility per month (April/May/June 2024). Produced by `src/03_calculate_metrics.py`.

| Column | Type | Description | How it's calculated |
|---|---|---|---|
| `Month` | string | Calendar month, format `YYYY-MM` | Derived from `WorkDate` |
| `Total_Nurse_Hours_All` | float | Total nursing hours (all roles) for this facility, this month | Sum across all days in the month |
| `Total_Direct_Care_Hours` | float | Total direct-care hours (RN+LPN+CNA) for this facility, this month | Sum across all days in the month |
| `Total_Contract_Hours` | float | Total contract/agency hours for this facility, this month | Sum across all days in the month |
| `Avg_MDScensus` | float | Average daily resident count for the month | Mean of daily `MDScensus` |
| `Days_Reported` | int | Number of days in the month this facility has a record for | Count of rows |
| `Zero_Census_Days` | int | Number of days that month with 0 residents reported | Sum of `Zero_Census_Flag` |
| `Census_Sum_ExclZero` | float | Sum of daily census, excluding zero-census days | Used only as the denominator for the ratio below — not a metric on its own |
| `Nurse_to_Patient_Ratio` | float | Direct-care hours provided per resident, for the month | `Total_Direct_Care_Hours / Census_Sum_ExclZero`. Computed on monthly totals, not averaged from daily ratios — this weights each day by its actual patient volume rather than treating a 5-patient day the same as a 100-patient day. |
| `Contract_Ratio` | float | Share of total nursing hours worked by contract/agency staff | `Total_Contract_Hours / Total_Nurse_Hours_All`. Ranges 0 (no contract reliance) to 1 (fully contract-staffed). |
| `Low_Census_Flag` | boolean | True if this facility-month's ratio is statistically unreliable due to a tiny resident count | `Avg_MDScensus < 10` |
| `Zero_Direct_Care_Flag` | boolean | True if the facility reported zero RN/LPN/CNA hours all month despite having real total nursing hours (staffed through admin/DON roles instead — see README) | `Total_Direct_Care_Hours == 0` and `Total_Nurse_Hours_All > 0` |

**Usage note:** for any ranking or average involving `Nurse_to_Patient_Ratio`, filter out rows where `Low_Census_Flag` or `Zero_Direct_Care_Flag` is True. The dashboard does this automatically (see `dashboard/app.py`, the `reliable` DataFrame); a raw query against this file will not.

---

## 3. `data/processed/state_month_summary.parquet`

Row grain: one row per state/territory per month. Same column definitions as the facility-month table above, aggregated to the state level instead of facility level, plus:

| Column | Type | Description |
|---|---|---|
| `Facility_Count` | int | Number of distinct facilities in this state that month (`PROVNUM` nunique) |

**Usage note:** this table has no reliability flags of its own — it's built from all facilities, including ones flagged at the facility level. For a ratio ranking that excludes known-unreliable facility-months (as used for the "lowest ratio" finding in the README), aggregate from the *filtered* facility-month table instead — see `src/exploration/analysis_q4.py` for the exact approach used.

---

*Generated for the Nurse Staffing Analysis project. For raw source columns, see `docs/NH_Data_Dictionary.pdf` (CMS-published). For the reasoning behind each derived metric, see the Methodology & Key Decisions section of the main README.*
