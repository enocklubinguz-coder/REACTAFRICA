import os
import pandas as pd
import plotly.express as px
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Multi-Facility Antibiotic Stewardship Dashboard", layout="wide"
)

# --- CUSTOM CSS FOR METRIC TILES ---
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 12px;
    }
    .metric-title {
        color: #495057;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #1e293b;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 4px;
        word-break: break-word;
    }
    .metric-sub {
        color: #059669;
        font-size: 12px;
        font-weight: 600;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- DIRECT DATA LOADING & PATIENT-LEVEL AGGREGATION ---
DATA_PATH = r'C:\Users\LUBINGU\PycharmProjects\LWANSASE\cdata\ANTIBIOTICS_WITH_DIAGNOSIS.csv'


@st.cache_data
def load_and_aggregate_patient_data(file_path):
  if not os.path.exists(file_path):
    return None, None

  df_raw = pd.read_csv(file_path)

  # Group strictly by FILE NUMBER (1 row per patient)
  df_patients = (
      df_raw.groupby("FILE NUMBER")
      .agg({
          "FACILITY": "first",
          "PATIENT GENDER": "first",
          "AGE": "first",
          "PATIENT HAS MALARIA": "first",
          "PATIENT HAS TUBERCULOSIS": "first",
          "PATIENT HIV STATUS": "first",
          "DIAGNOSIS": "first",
          "WORKING DIAGNOSIS": "first",
          "DEFINITIVE DIAGNOSIS": "first",
          "NUMBER OF ANTIBIOTICS": "first",
          # Collect multi-value antibiotics and cultures as lists
          "ANTIBIOTIC": lambda x: [
              item for item in x.dropna().unique() if str(item).strip() != ""
          ],
          "CULTURE SAMPLE": lambda x: [
              item for item in x.dropna().unique() if str(item).strip() != ""
          ],
          "CULTURE SAMPLE TAKEN": "first",
          "DEESCALATION CHANGE OF TREATMENT DONE": "first",
          "TREATMENT TYPE": "first",
      })
      .reset_index()
  )

  # Derived patient-level metrics
  df_patients["ANTIBIOTIC_COUNT"] = df_patients["ANTIBIOTIC"].apply(len)
  df_patients["CULTURE_COUNT"] = df_patients["CULTURE SAMPLE"].apply(len)

  return df_raw, df_patients


# Load data
df_raw, df_patients = load_and_aggregate_patient_data(DATA_PATH)

# --- HEADER SECTION ---
st.title("💊 Multi-Facility Clinical & Antibiotic Stewardship Dashboard")
st.markdown(
    "Data consolidated by **`FILE NUMBER`** (1 Patient = 1 Record with multiple"
    " cultures and antibiotics aggregated)."
)

# --- TOP FACILITY TABS ---
tab_nakuru, tab_uth, tab_levy, tab_aar = st.tabs([
    "🇰🇪 Nakuru (Kenya)",
    "🇿🇲 UTH (Zambia)",
    "🇿🇲 Levy (Zambia)",
    "🇰🇪 AAR (Kenya)",
])

facilities_map = {
    "Nakuru": (
        "Nakuru Level 5 Hospital",
        "Kenya",
        "Nakuru County Referral Hospital",
        tab_nakuru,
    ),
    "UTH": (
        "University Teaching Hospital",
        "Zambia",
        "University Teaching Hospital",
        tab_uth,
    ),
    "Levy": (
        "Levy Mwanawasa Hospital",
        "Zambia",
        "Levy Mwanawasa Hospital",
        tab_levy,
    ),
    "AAR": ("AAR Hospital", "Kenya", "AAR Hospital", tab_aar),
}


# Helper tile renderer
def render_tile(title, value, subtext=""):
  st.markdown(
      f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{subtext}</div>
        </div>
    """,
      unsafe_allow_html=True,
  )


# Dashboard Render Function
def render_facility_dashboard(
    facility_code, full_name, country, facility_match, tab
):
  with tab:
    # --- TOP BANNER ---
    b1, b2, b3 = st.columns(3)
    with b1:
      st.info(f"**🏥 Facility:** {full_name}")
    with b2:
      st.warning(f"**🌍 Country:** {country}")
    with b3:
      st.success("**📌 Phase:** ENDLINE 2026")

    # Filter patient dataframe
    if df_patients is not None and "FACILITY" in df_patients.columns:
      pts = df_patients[
          df_patients["FACILITY"]
          .astype(str)
          .str.contains(facility_code, case=False)
          | df_patients["FACILITY"]
          .astype(str)
          .str.contains(facility_match, case=False)
      ].copy()
    else:
      pts = pd.DataFrame()

    total_patients = len(pts)

    if total_patients == 0:
      st.warning(
          f"No patient records found for **{full_name}** in dataset."
      )
      return

    # --- KEY PERFORMANCE INDICATORS ---
    st.header("📊 Key Performance Indicators (Patient Base)")

    # Row 1: Overview
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    with r1_c1:
      render_tile(
          "Total Patients (Files)",
          f"{total_patients:,}",
          "Unique FILE NUMBER Records",
      )

    with r1_c2:
      gender_counts = pts["PATIENT GENDER"].value_counts()
      gender_str = " • ".join([
          f"{k}: {v} ({(v/total_patients)*100:.1f}%)"
          for k, v in gender_counts.items()
      ])
      render_tile(
          "Gender Breakdown",
          f"{len(pts['PATIENT GENDER'].dropna()):,}",
          gender_str,
      )

    with r1_c3:
      total_abx_courses = pts["ANTIBIOTIC_COUNT"].sum()
      render_tile(
          "Total Antibiotics Prescribed",
          f"{total_abx_courses:,}",
          f"Avg {(total_abx_courses/total_patients):.2f} / patient",
      )

    # Row 2: Compliance & Risk
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1:
      pts_3plus = (pts["ANTIBIOTIC_COUNT"] >= 3).sum()
      pct_3plus = (pts_3plus / total_patients) * 100
      render_tile(
          "Patients on ≥3 Antibiotics",
          f"{pts_3plus:,}",
          f"{pct_3plus:.1f}% of patients",
      )

    with r2_c2:
      pts_with_cultures = (pts["CULTURE_COUNT"] > 0).sum()
      total_cultures = pts["CULTURE_COUNT"].sum()
      pct_cultures = (pts_with_cultures / total_patients) * 100
      render_tile(
          "Patients with Cultures",
          f"{pts_with_cultures:,}",
          f"{total_cultures} Total Samples ({pct_cultures:.1f}%)",
      )

    with r2_c3:
      deescalated = (
          pts["DEESCALATION CHANGE OF TREATMENT DONE"]
          .astype(str)
          .str.strip()
          .str.lower()
          .isin(["yes", "1", "true"])
          .sum()
      )
      pct_deesc = (deescalated / total_patients) * 100
      render_tile(
          "De-escalated Cases", f"{deescalated:,}", f"{pct_deesc:.1f}% compliance"
      )

    # Row 3: Common Frequencies
    r3_c1, r3_c2, r3_c3 = st.columns(3)
    with r3_c1:
      all_abx = [abx for sublist in pts["ANTIBIOTIC"] for abx in sublist]
      if all_abx:
        top_abx = pd.Series(all_abx).value_counts().index[0]
        top_abx_cnt = pd.Series(all_abx).value_counts().iloc[0]
        render_tile(
            "Common Antibiotic",
            str(top_abx),
            f"{top_abx_cnt:,} patient prescriptions",
        )
      else:
        render_tile("Common Antibiotic", "N/A", "None recorded")

    with r3_c2:
      all_cultures = [c for sublist in pts["CULTURE SAMPLE"] for c in sublist]
      if all_cultures:
        top_culture = pd.Series(all_cultures).value_counts().index[0]
        top_culture_cnt = pd.Series(all_cultures).value_counts().iloc[0]
        render_tile(
            "Common Specimen",
            str(top_culture),
            f"{top_culture_cnt:,} patient samples",
        )
      else:
        render_tile("Common Specimen", "N/A", "None recorded")

    with r3_c3:
      top_diag = pts["DIAGNOSIS"].value_counts().index[0]
      diag_cnt = pts["DIAGNOSIS"].value_counts().iloc[0]
      render_tile(
          "Common Diagnosis", str(top_diag), f"{diag_cnt:,} patient diagnoses"
      )

    st.markdown("---")

    # --- VISUAL ANALYTICS ---
    st.header("📈 Visual Analytics (Patient-Level)")

    c1, c2 = st.columns(2)
    with c1:
      all_abx = [abx for sublist in pts["ANTIBIOTIC"] for abx in sublist]
      if all_abx:
        t10_abx = pd.Series(all_abx).value_counts().head(10).reset_index()
        t10_abx.columns = ["Antibiotic", "Patients"]
        fig = px.bar(
            t10_abx,
            x="Patients",
            y="Antibiotic",
            orientation="h",
            title="Top Antibiotics Prescribed (Patient Count)",
            text="Patients",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(
            fig, use_container_width=True, key=f"top_abx_{facility_code}"
        )

    with c2:
      abx_dist = pts["ANTIBIOTIC_COUNT"].value_counts().reset_index()
      abx_dist.columns = ["Antibiotics Per Patient", "Patients"]
      fig = px.pie(
          abx_dist,
          values="Patients",
          names="Antibiotics Per Patient",
          title="Patient Distribution by Antibiotic Count",
          hole=0.4,
      )
      st.plotly_chart(
          fig, use_container_width=True, key=f"abx_dist_{facility_code}"
      )

    c3, c4 = st.columns(2)
    with c3:
      t_diag = pts["DIAGNOSIS"].value_counts().head(10).reset_index()
      t_diag.columns = ["Diagnosis", "Patients"]
      fig = px.bar(
          t_diag,
          x="Diagnosis",
          y="Patients",
          title="Top 10 Diagnoses (1 Per Patient)",
          text="Patients",
          color="Patients",
      )
      st.plotly_chart(
          fig, use_container_width=True, key=f"top_diag_{facility_code}"
      )

    with c4:
      all_cultures = [c for sublist in pts["CULTURE SAMPLE"] for c in sublist]
      if all_cultures:
        spec_counts = pd.Series(all_cultures).value_counts().reset_index()
        spec_counts.columns = ["Specimen Type", "Count"]
        fig = px.bar(
            spec_counts,
            x="Specimen Type",
            y="Count",
            title="Culture Specimens Taken Across Patients",
            text="Count",
        )
        st.plotly_chart(
            fig, use_container_width=True, key=f"specimen_{facility_code}"
        )

    st.markdown("---")

    # --- CO-MORBIDITIES SECTION ---
    st.header("🦠 Co-morbidities Breakdown (Base: Unique Patients)")
    col_tb, col_malaria, col_hiv = st.columns(3)

    with col_tb:
      tb_counts = (
          pts["PATIENT HAS TUBERCULOSIS"]
          .fillna("Unknown")
          .astype(str)
          .str.strip()
          .str.capitalize()
          .value_counts()
          .reset_index()
      )
      tb_counts.columns = ["Status", "Patients"]
      fig_tb = px.bar(
          tb_counts,
          x="Status",
          y="Patients",
          title="TB Status Breakdown",
          text="Patients",
          color="Status",
          color_discrete_map={
              "Yes": "#dc2626",
              "No": "#2563eb",
              "Unknown": "#6b7280",
          },
      )
      st.plotly_chart(
          fig_tb, use_container_width=True, key=f"tb_chart_{facility_code}"
      )

    with col_malaria:
      mal_counts = (
          pts["PATIENT HAS MALARIA"]
          .fillna("Unknown")
          .astype(str)
          .str.strip()
          .str.capitalize()
          .value_counts()
          .reset_index()
      )
      mal_counts.columns = ["Status", "Patients"]
      fig_malaria = px.bar(
          mal_counts,
          x="Status",
          y="Patients",
          title="Malaria Status Breakdown",
          text="Patients",
          color="Status",
          color_discrete_map={
              "Yes": "#d97706",
              "No": "#2563eb",
              "Unknown": "#6b7280",
          },
      )
      st.plotly_chart(
          fig_malaria,
          use_container_width=True,
          key=f"malaria_chart_{facility_code}",
      )

    with col_hiv:
      hiv_counts = (
          pts["PATIENT HIV STATUS"]
          .fillna("Unknown")
          .astype(str)
          .str.strip()
          .str.capitalize()
          .value_counts()
          .reset_index()
      )
      hiv_counts.columns = ["Status", "Patients"]
      fig_hiv = px.bar(
          hiv_counts,
          x="Status",
          y="Patients",
          title="HIV Status Breakdown",
          text="Patients",
          color="Status",
          color_discrete_map={
              "Positive": "#ef4444",
              "Negative": "#10b981",
              "Unknown": "#6b7280",
              "None": "#6b7280",
          },
      )
      st.plotly_chart(
          fig_hiv, use_container_width=True, key=f"hiv_chart_{facility_code}"
      )


# Render facility tabs
for code, (name, country, match_str, tab_obj) in facilities_map.items():
  render_facility_dashboard(code, name, country, match_str, tab_obj)