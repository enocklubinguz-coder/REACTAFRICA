import os
import re
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
        font-size: 22px;
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


# --- DATA AGGREGATION UTILITY ---
def process_and_aggregate_dataframe(df_raw):
    """Processes raw facility DataFrame and performs patient-level aggregation."""
    required_cols = ["FILE NUMBER"]
    for col in required_cols:
        if col not in df_raw.columns:
            st.error(f"Missing required column: `{col}` in uploaded file.")
            return None

    agg_dict = {
        "FACILITY": (
            "first"
            if "FACILITY" in df_raw.columns
            else lambda x: "Uploaded Facility"
        ),
        "PATIENT GENDER": (
            "first" if "PATIENT GENDER" in df_raw.columns else lambda x: "Unknown"
        ),
        "AGE": "first" if "AGE" in df_raw.columns else lambda x: None,
        "PATIENT HAS MALARIA": (
            "first"
            if "PATIENT HAS MALARIA" in df_raw.columns
            else lambda x: "Unknown"
        ),
        "PATIENT HAS TUBERCULOSIS": (
            "first"
            if "PATIENT HAS TUBERCULOSIS" in df_raw.columns
            else lambda x: "Unknown"
        ),
        "PATIENT HIV STATUS": (
            "first"
            if "PATIENT HIV STATUS" in df_raw.columns
            else lambda x: "Unknown"
        ),
        "DIAGNOSIS": (
            "first" if "DIAGNOSIS" in df_raw.columns else lambda x: "N/A"
        ),
        "NUMBER OF ANTIBIOTICS": (
            "first"
            if "NUMBER OF ANTIBIOTICS" in df_raw.columns
            else lambda x: 0
        ),
        "ANTIBIOTIC": (
            lambda x: [
                item for item in x.dropna().unique() if str(item).strip() != ""
            ]
            if "ANTIBIOTIC" in df_raw.columns
            else []
        ),
        "CULTURE SAMPLE": (
            lambda x: [
                item for item in x.dropna().unique() if str(item).strip() != ""
            ]
            if "CULTURE SAMPLE" in df_raw.columns
            else []
        ),
        "DEESCALATION CHANGE OF TREATMENT DONE": (
            "first"
            if "DEESCALATION CHANGE OF TREATMENT DONE" in df_raw.columns
            else lambda x: "No"
        ),
    }

    if "TREATMENT TYPE" in df_raw.columns:
        agg_dict["TREATMENT TYPE"] = "first"

    df_patients = df_raw.groupby("FILE NUMBER").agg(agg_dict).reset_index()

    # Derived patient-level metrics
    df_patients["ANTIBIOTIC_COUNT"] = df_patients["ANTIBIOTIC"].apply(len)
    df_patients["CULTURE_COUNT"] = df_patients["CULTURE SAMPLE"].apply(len)

    return df_patients


@st.cache_data
def load_default_data(file_path):
    """Loads default system data from local disk."""
    if not os.path.exists(file_path):
        return None, None
    df_raw = pd.read_csv(file_path)
    df_patients = process_and_aggregate_dataframe(df_raw)
    return df_raw, df_patients


# Default local dataset setup
DATA_PATH = r"C:\Users\LUBINGU\PycharmProjects\LWANSASE\cdata\ANTIBIOTICS_WITH_DIAGNOSIS.csv"
default_df_raw, default_df_patients = load_default_data(DATA_PATH)

# --- HEADER SECTION ---
st.markdown(
    """
    <h1 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem;">
        💊 <span style="color: #ef4444;">REACT AFRICA</span> | ASPIRE DASHBOARD
    </h1>
    """,
    unsafe_allow_html=True,
)
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


def extract_numeric(value):
    """Extracts first valid integer/float from text (e.g., '7 days' -> 7)."""
    if pd.isna(value):
        return None
    match = re.search(r"(\d+(\.\d+)?)", str(value))
    return float(match.group(1)) if match else None


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

        st.markdown("### 📁 Data Source")
        uploaded_file = st.file_uploader(
            f"Upload custom CSV or Excel dataset for **{full_name}**",
            type=["csv", "xlsx", "xls"],
            key=f"uploader_{facility_code}",
        )

        pts = pd.DataFrame()
        raw_fac_df = pd.DataFrame()

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    raw_fac_df = pd.read_csv(uploaded_file)
                else:
                    raw_fac_df = pd.read_excel(uploaded_file)

                pts = process_and_aggregate_dataframe(raw_fac_df)
                st.success(
                    f"Successfully loaded uploaded dataset for"
                    f" **{full_name}** ({len(pts):,} patient records)."
                )
            except Exception as e:
                st.error(f"Error reading uploaded file: {e}")
                return
        else:
            if (
                default_df_patients is not None
                and "FACILITY" in default_df_patients.columns
            ):
                pts = default_df_patients[
                    default_df_patients["FACILITY"]
                    .astype(str)
                    .str.contains(facility_code, case=False)
                    | default_df_patients["FACILITY"]
                    .astype(str)
                    .str.contains(facility_match, case=False)
                ].copy()

            if (
                default_df_raw is not None
                and "FACILITY" in default_df_raw.columns
            ):
                raw_fac_df = default_df_raw[
                    default_df_raw["FACILITY"]
                    .astype(str)
                    .str.contains(facility_code, case=False)
                    | default_df_raw["FACILITY"]
                    .astype(str)
                    .str.contains(facility_match, case=False)
                ].copy()

        total_patients = len(pts)

        if total_patients == 0:
            st.warning(
                f"No patient records available for **{full_name}**. Please"
                " upload a dataset above."
            )
            return

        # --- KEY PERFORMANCE INDICATORS ---
        st.header("📊 Key Performance Indicators (Patient Base)")

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
            avg_abx = (
                (total_abx_courses / total_patients)
                if total_patients > 0
                else 0
            )
            render_tile(
                "Total Antibiotics Prescribed",
                f"{total_abx_courses:,}",
                f"Avg {avg_abx:.2f} / patient",
            )

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
                "De-escalated Cases",
                f"{deescalated:,}",
                f"{pct_deesc:.1f}% compliance",
            )

        # --- SECOND TILE ROW: COMMON METRICS ---
        all_abx = [abx for sublist in pts["ANTIBIOTIC"] for abx in sublist]
        all_cultures = [c for sublist in pts["CULTURE SAMPLE"] for c in sublist]

        r3_c1, r3_c2, r3_c3 = st.columns(3)

        # 1. Most Common Antibiotic
        with r3_c1:
            if all_abx:
                top_abx_series = pd.Series(all_abx).value_counts()
                top_abx_name = top_abx_series.index[0]
                top_abx_count = top_abx_series.iloc[0]
                pct_abx = (top_abx_count / len(all_abx)) * 100
                render_tile(
                    "Most Common Antibiotic",
                    str(top_abx_name),
                    f"{top_abx_count:,} Prescriptions ({pct_abx:.1f}%)",
                )
            else:
                render_tile("Most Common Antibiotic", "N/A", "No Data Available")

        # 2. Most Common Specimen
        with r3_c2:
            if all_cultures:
                top_spec_series = pd.Series(all_cultures).value_counts()
                top_spec_name = top_spec_series.index[0]
                top_spec_count = top_spec_series.iloc[0]
                pct_spec = (top_spec_count / len(all_cultures)) * 100
                render_tile(
                    "Most Common Specimen",
                    str(top_spec_name),
                    f"{top_spec_count:,} Samples ({pct_spec:.1f}%)",
                )
            else:
                render_tile("Most Common Specimen", "N/A", "No Data Available")

        # 3. Most Common Syndrome
        with r3_c3:
            diag_series = pts["DIAGNOSIS"].dropna()
            diag_series = diag_series[diag_series.astype(str).str.strip() != "N/A"]
            if not diag_series.empty:
                top_diag_counts = diag_series.value_counts()
                top_diag_name = top_diag_counts.index[0]
                top_diag_count = top_diag_counts.iloc[0]
                pct_diag = (top_diag_count / total_patients) * 100
                render_tile(
                    "Most Common Syndrome",
                    str(top_diag_name),
                    f"{top_diag_count:,} Patients ({pct_diag:.1f}%)",
                )
            else:
                render_tile("Most Common Syndrome", "N/A", "No Data Available")

        st.markdown("---")

        # --- TOP 5 ANTIBIOTICS & TREATMENT TYPE SECTION ---
        st.header("🎯 Stewardship Priorities: Top 5 Antibiotics & Treatment Type")
        sec1_c1, sec1_c2 = st.columns(2)

        with sec1_c1:
            st.subheader("🥇 Top 5 Most Prescribed Antibiotics")
            if all_abx:
                top5_abx = (
                    pd.Series(all_abx).value_counts().head(5).reset_index()
                )
                top5_abx.columns = ["Antibiotic", "Prescription Count"]
                top5_abx["Percentage"] = (
                    top5_abx["Prescription Count"] / len(all_abx) * 100
                ).round(1)

                fig_top5 = px.bar(
                    top5_abx,
                    x="Prescription Count",
                    y="Antibiotic",
                    orientation="h",
                    title="Top 5 Antibiotics by Total Prescriptions",
                    text=top5_abx.apply(
                        lambda r: (
                            f"{int(r['Prescription Count']):,} ({r['Percentage']}%)"
                        ),
                        axis=1,
                    ),
                    color="Prescription Count",
                    color_continuous_scale="Viridis",
                )
                fig_top5.update_layout(
                    yaxis={"categoryorder": "total ascending"}
                )
                fig_top5.update_traces(textangle=0, textposition="outside")
                fig_top5.update_xaxes(tickangle=0)
                fig_top5.update_yaxes(tickangle=0)
                st.plotly_chart(
                    fig_top5,
                    use_container_width=True,
                    key=f"top5_abx_chart_{facility_code}",
                )
            else:
                st.info("No antibiotic data available to derive Top 5.")

        with sec1_c2:
            st.subheader("💉 Treatment Type Breakdown")
            if "TREATMENT TYPE" in raw_fac_df.columns:
                tx_series = (
                    raw_fac_df["TREATMENT TYPE"].dropna().astype(str).str.strip()
                )
                if not tx_series.empty:
                    tx_df = tx_series.value_counts().reset_index()
                    tx_df.columns = ["TREATMENT TYPE", "Count"]

                    fig_tx = px.pie(
                        tx_df,
                        values="Count",
                        names="TREATMENT TYPE",
                        title="Treatment Type Breakdown",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set2,
                    )
                    fig_tx.update_traces(textinfo="label+percent+value")
                    st.plotly_chart(
                        fig_tx,
                        use_container_width=True,
                        key=f"tx_type_chart_{facility_code}",
                    )
                else:
                    st.warning("Column **`TREATMENT TYPE`** is present but contains no data.")
            else:
                st.error("Missing required column **`TREATMENT TYPE`** in the dataset.")

        st.markdown("---")

        # --- VISUAL ANALYTICS ---
        st.header("📈 Visual Analytics (Patient-Level)")

        c1, c2 = st.columns(2)
        with c1:
            if all_abx:
                t10_abx = (
                    pd.Series(all_abx).value_counts().head(10).reset_index()
                )
                t10_abx.columns = ["Antibiotic", "Patients"]
                fig = px.bar(
                    t10_abx,
                    x="Patients",
                    y="Antibiotic",
                    orientation="h",
                    title="Top 10 Antibiotics Prescribed (Patient Count)",
                    text="Patients",
                )
                fig.update_layout(yaxis={"categoryorder": "total ascending"})
                fig.update_traces(textangle=0, textposition="outside")
                fig.update_xaxes(tickangle=0)
                fig.update_yaxes(tickangle=0)
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key=f"top_abx_{facility_code}",
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
            fig.update_traces(textinfo="value+percent")
            st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"abx_dist_{facility_code}",
            )

        c3, c4 = st.columns(2)
        with c3:
            if not pts["DIAGNOSIS"].dropna().empty:
                t_diag = pts["DIAGNOSIS"].value_counts().head(10).reset_index()
                t_diag.columns = ["Syndrome", "Patients"]
                fig = px.bar(
                    t_diag,
                    x="Syndrome",
                    y="Patients",
                    title="Top 10 Syndromes (1 Per Patient)",
                    text="Patients",
                    color="Patients",
                )
                fig.update_traces(textangle=0, textposition="outside")
                fig.update_xaxes(tickangle=0)
                fig.update_yaxes(tickangle=0)
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key=f"top_diag_{facility_code}",
                )

        with c4:
            if all_cultures:
                spec_counts = (
                    pd.Series(all_cultures).value_counts().reset_index()
                )
                spec_counts.columns = ["Specimen Type", "Count"]
                fig = px.bar(
                    spec_counts,
                    x="Specimen Type",
                    y="Count",
                    title="Culture Specimens Taken Across Patients",
                    text="Count",
                )
                fig.update_traces(textangle=0, textposition="outside")
                fig.update_xaxes(tickangle=0)
                fig.update_yaxes(tickangle=0)
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key=f"specimen_{facility_code}",
                )

        # --- DURATION OF TOP 10 ANTIBIOTICS CHART ---
        st.markdown("---")
        st.subheader("⏱️ Average Duration of Treatment (Top 10 Antibiotics)")

        if not raw_fac_df.empty and "ANTIBIOTIC" in raw_fac_df.columns:
            if "DURATION" in raw_fac_df.columns:
                top10_names = (
                    pd.Series(all_abx).value_counts().head(10).index.tolist()
                    if all_abx
                    else []
                )

                df_dur = raw_fac_df[
                    raw_fac_df["ANTIBIOTIC"].isin(top10_names)
                ].copy()

                df_dur["CLEAN_DURATION"] = df_dur["DURATION"].apply(
                    extract_numeric
                )
                df_dur = df_dur.dropna(subset=["CLEAN_DURATION"])

                if not df_dur.empty:
                    duration_stats = (
                        df_dur.groupby("ANTIBIOTIC")["CLEAN_DURATION"]
                        .mean()
                        .reset_index()
                    )
                    duration_stats.columns = ["Antibiotic", "Avg_Days"]
                    duration_stats["Avg_Days"] = duration_stats[
                        "Avg_Days"
                    ].round(1)
                    duration_stats = duration_stats.sort_values(
                        by="Avg_Days", ascending=False
                    )

                    fig_dur = px.bar(
                        duration_stats,
                        x="Antibiotic",
                        y="Avg_Days",
                        title="Average Duration (Days) based on 'DURATION'",
                        text="Avg_Days",
                        color="Avg_Days",
                        color_continuous_scale="Teal",
                        labels={"Avg_Days": "Mean Days"},
                    )
                    fig_dur.update_traces(
                        textangle=0,
                        textposition="outside",
                        texttemplate="%{text} d",
                    )
                    fig_dur.update_xaxes(tickangle=0)
                    fig_dur.update_yaxes(tickangle=0)
                    st.plotly_chart(
                        fig_dur,
                        use_container_width=True,
                        key=f"dur_chart_{facility_code}",
                    )
                else:
                    st.warning(
                        "No valid numeric duration values found in column"
                        " **`DURATION`**."
                    )
            else:
                st.error("Missing required column **`DURATION`** in dataset.")
        else:
            st.info("No raw dataset available to compute treatment durations.")

        # --- METRONIDAZOLE BY SYNDROME CHART ---
        st.markdown("---")
        st.subheader("💊 Metronidazole Usage Across Top 5 Syndromes")

        metro_pts = pts[
            pts["ANTIBIOTIC"].apply(
                lambda abx_list: any(
                    "metronidaz" in str(a).lower()
                    for a in abx_list
                    if isinstance(abx_list, list)
                )
            )
        ]

        if not metro_pts.empty and not metro_pts["DIAGNOSIS"].dropna().empty:
            metro_diag = (
                metro_pts["DIAGNOSIS"].value_counts().head(5).reset_index()
            )
            metro_diag.columns = ["Syndrome", "Patients"]
            fig_metro = px.bar(
                metro_diag,
                x="Syndrome",
                y="Patients",
                title=(
                    "Metronidazole Prescriptions across Top 5 Syndromes"
                    " (Patient Base)"
                ),
                text="Patients",
                color="Patients",
                color_continuous_scale="Viridis",
            )
            fig_metro.update_traces(textangle=0, textposition="outside")
            fig_metro.update_xaxes(tickangle=0)
            fig_metro.update_yaxes(tickangle=0)
            st.plotly_chart(
                fig_metro,
                use_container_width=True,
                key=f"metro_diag_{facility_code}",
            )
        else:
            st.info(
                f"No Metronidazole prescriptions found in records for"
                f" **{full_name}**."
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
            fig_tb.update_traces(textangle=0, textposition="outside")
            fig_tb.update_xaxes(tickangle=0)
            fig_tb.update_yaxes(tickangle=0)
            st.plotly_chart(
                fig_tb,
                use_container_width=True,
                key=f"tb_chart_{facility_code}",
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
            fig_malaria.update_traces(textangle=0, textposition="outside")
            fig_malaria.update_xaxes(tickangle=0)
            fig_malaria.update_yaxes(tickangle=0)
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
            fig_hiv.update_traces(textangle=0, textposition="outside")
            fig_hiv.update_xaxes(tickangle=0)
            fig_hiv.update_yaxes(tickangle=0)
            st.plotly_chart(
                fig_hiv,
                use_container_width=True,
                key=f"hiv_chart_{facility_code}",
            )


# Render facility tabs
for code, (name, country, match_str, tab_obj) in facilities_map.items():
    render_facility_dashboard(code, name, country, match_str, tab_obj)