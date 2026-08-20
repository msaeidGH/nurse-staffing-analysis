import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Nursing Home Staffing Dashboard — Q2 2024", layout="wide")

@st.cache_data
def load_data():
    fm = pd.read_parquet("data/processed/facility_month_summary.parquet")
    sm = pd.read_parquet("data/processed/state_month_summary.parquet")
    return fm, sm

facility_month, state_month = load_data()

# Reliable subset for ratio-based views (excludes low-census / zero-direct-care edge cases)
reliable = facility_month[
    ~facility_month["Low_Census_Flag"] & ~facility_month["Zero_Direct_Care_Flag"]
]

page = st.sidebar.radio("Navigate", ["National Overview", "Facility Lookup", "Staffing vs. Census"])

st.sidebar.markdown("---")
st.sidebar.caption(
    "Source: CMS Payroll-Based Journal (PBJ), Q2 2024. "
    "163 facility-months excluded from ratio metrics due to low census (<10); "
    "8 flagged for reporting-pattern anomalies. See README for methodology."
)

# ---------------- PAGE 1: NATIONAL OVERVIEW ----------------
if page == "National Overview":
    st.title("Nursing Home Staffing — National Overview (Q2 2024)")

    col1, col2, col3 = st.columns(3)
    col1.metric("Facilities", f"{facility_month['PROVNUM'].nunique():,}")
    col2.metric("States/Territories", f"{state_month['STATE'].nunique()}")
    col3.metric("Avg Nurse-to-Patient Ratio", f"{reliable['Nurse_to_Patient_Ratio'].mean():.2f}")

    st.subheader("Average Nurse-to-Patient Ratio by State")
    state_avg = state_month.groupby("STATE")["Nurse_to_Patient_Ratio"].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(12, 6))
    state_avg.plot(kind="bar", ax=ax)
    ax.set_ylabel("Direct Care Hours per Patient")
    st.pyplot(fig)

    st.subheader("Contract Staff Reliance by State")
    contract_avg = state_month.groupby("STATE")["Contract_Ratio"].mean().sort_values(ascending=False)
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    contract_avg.plot(kind="bar", ax=ax2, color="orange")
    ax2.set_ylabel("Contract Hours / Total Hours")
    st.pyplot(fig2)

    st.subheader("Average Nurse Hours per Facility by State")
    per_facility_state = facility_month[facility_month["STATE"] != "PR"].groupby("STATE").agg(
        Avg_Hours_Per_Facility=("Total_Nurse_Hours_All", "mean"),
        Facility_Count=("PROVNUM", "nunique")
    ).sort_values("Avg_Hours_Per_Facility", ascending=False)
    fig3, ax3 = plt.subplots(figsize=(12, 6))
    per_facility_state["Avg_Hours_Per_Facility"].plot(kind="bar", ax=ax3, color="green")
    ax3.set_ylabel("Avg Nurse Hours per Facility (monthly)")
    st.pyplot(fig3)
    st.caption("Puerto Rico excluded (only 6 facilities — sample too small to be reliable).")

# ---------------- PAGE 2: FACILITY LOOKUP ----------------
elif page == "Facility Lookup":
    st.title("Facility Lookup")

    search = st.text_input("Search facility name (partial match ok)")
    state_filter = st.selectbox("Or filter by state", ["All"] + sorted(facility_month["STATE"].unique().tolist()))

    filtered = facility_month.copy()
    if search:
        filtered = filtered[filtered["PROVNAME"].str.contains(search, case=False, na=False)]
    if state_filter != "All":
        filtered = filtered[filtered["STATE"] == state_filter]

    st.write(f"{filtered['PROVNUM'].nunique()} matching facilities")
    st.dataframe(
        filtered[["PROVNAME", "STATE", "Month", "Avg_MDScensus",
                  "Total_Nurse_Hours_All", "Nurse_to_Patient_Ratio", "Contract_Ratio",
                  "Low_Census_Flag", "Zero_Direct_Care_Flag"]]
        .sort_values(["PROVNAME", "Month"])
    )

    if search and filtered["PROVNUM"].nunique() == 1:
        st.subheader(f"Trend: {filtered['PROVNAME'].iloc[0]}")
        trend = filtered.sort_values("Month")
        fig, ax = plt.subplots()
        ax.plot(trend["Month"], trend["Nurse_to_Patient_Ratio"], marker="o")
        ax.set_ylabel("Nurse-to-Patient Ratio")
        st.pyplot(fig)

# ---------------- PAGE 3: STAFFING VS CENSUS ----------------
else:
    st.title("Staffing Levels vs. Patient Census")
    st.caption("Each point is one facility-month. Color indicates contract staff reliance.")

    fig, ax = plt.subplots(figsize=(10, 7))
    scatter = ax.scatter(
        reliable["Avg_MDScensus"], reliable["Total_Nurse_Hours_All"],
        c=reliable["Contract_Ratio"], cmap="viridis", alpha=0.5, s=15
    )
    ax.set_xlabel("Average Daily Census")
    ax.set_ylabel("Total Nurse Hours (month)")
    plt.colorbar(scatter, label="Contract Ratio")
    st.pyplot(fig)

    corr = reliable[["Avg_MDScensus", "Total_Nurse_Hours_All"]].corr().iloc[0, 1]
    st.metric("Correlation (census vs. total hours)", f"{corr:.3f}")