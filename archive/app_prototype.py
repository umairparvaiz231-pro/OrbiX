from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# -------------------------------------------
# OrbiX: Space Debris Tracking Dashboard
# -------------------------------------------

st.set_page_config(
    page_title="OrbiX",
    page_icon="🛰️",
    layout="wide",
)
# -------------------------------------------
# OrbiX: Professional Space Theme
# -------------------------------------------

st.markdown("""
<style>

/* Main application background */
.stApp {
    background:
        radial-gradient(
            circle at 85% 0%,
            rgba(37, 99, 235, 0.16),
            transparent 32%
        ),
        linear-gradient(
            135deg,
            #060d19 0%,
            #0a1425 55%,
            #0b192b 100%
        );
    color: #e8f1ff;
}

/* Main content spacing */
.block-container {
    max-width: 1500px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Main title */
h1 {
    color: #f4f8ff !important;
    font-weight: 800 !important;
    letter-spacing: -1px;
}

h2, h3 {
    color: #dceaff !important;
    font-weight: 650 !important;
}

/* Secondary text */
[data-testid="stCaptionContainer"] {
    color: #91a7c4 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #091424 0%,
        #0d1c30 100%
    );
    border-right: 1px solid rgba(67, 180, 255, 0.22);
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #36d9f5 !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: linear-gradient(
        145deg,
        rgba(19, 36, 58, 0.98),
        rgba(12, 26, 44, 0.98)
    );
    border: 1px solid rgba(54, 217, 245, 0.22);
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 6px 22px rgba(0, 0, 0, 0.16);
    transition: border-color 0.2s ease;
}

[data-testid="stMetric"]:hover {
    border-color: rgba(54, 217, 245, 0.75);
}

[data-testid="stMetricLabel"] {
    color: #9aafca !important;
}

[data-testid="stMetricValue"] {
    color: #36d9f5 !important;
    font-weight: 750 !important;
}

/* Search input */
[data-testid="stTextInput"] input {
    background: #0c1a2b !important;
    color: #edf5ff !important;
    border: 1px solid #29435f !important;
    border-radius: 9px !important;
}

/* Dropdowns */
[data-testid="stSelectbox"] > div > div {
    background: #101e31;
    border-radius: 9px;
}

/* Buttons */
.stButton > button,
.stDownloadButton > button {
    background: linear-gradient(100deg, #087eaa, #315de0);
    color: white !important;
    border: 1px solid rgba(104, 211, 255, 0.45);
    border-radius: 9px;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: #36d9f5;
    box-shadow: 0 0 14px rgba(54, 217, 245, 0.2);
}

/* Data tables */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(91, 157, 230, 0.25);
    border-radius: 10px;
    overflow: hidden;
}

/* Alerts and dividers */
[data-testid="stAlert"] {
    border-radius: 10px;
}

hr {
    border-color: rgba(120, 165, 220, 0.2) !important;
}

/* Links */
a {
    color: #36d9f5 !important;
}

/* Mobile layout */
@media (max-width: 768px) {
    .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    h1 {
        font-size: 1.8rem !important;
    }
}

</style>
""", unsafe_allow_html=True)

DATA_DIR = Path("data")
PROPAGATION_FILE = DATA_DIR / "propagated_debris.csv"
QUALITY_FILE = DATA_DIR / "orbital_quality_report.csv"



st.title("🛰️ OrbiX")
st.caption("Space Debris Tracking & Analytics Dashboard")
st.markdown(
    "Explore SGP4-propagated positions, inspect debris objects, "
    "and review orbital element age."
)
st.info(
    "Scientific note: positions are estimates in the TEME reference "
    "frame, not direct observations or Earth-surface coordinates."
)

if not PROPAGATION_FILE.exists():
    st.error("Missing data/propagated_debris.csv. Run orbital_propagation.py first.")
    st.stop()

data = pd.read_csv(PROPAGATION_FILE)

required = [
    "NORAD_CAT_ID",
    "OBJECT_NAME",
    "ELEMENT_EPOCH",
    "PREDICTION_TIME_UTC",
    "MINUTES_FROM_START",
    "X_TEME_KM",
    "Y_TEME_KM",
    "Z_TEME_KM",
]

missing = [column for column in required if column not in data.columns]
if missing:
    st.error(f"Required columns are missing: {missing}")
    st.stop()

data["NORAD_CAT_ID"] = data["NORAD_CAT_ID"].astype(str)
data["MINUTES_FROM_START"] = pd.to_numeric(
    data["MINUTES_FROM_START"], errors="coerce"
)
for column in ["X_TEME_KM", "Y_TEME_KM", "Z_TEME_KM"]:
    data[column] = pd.to_numeric(data[column], errors="coerce")

data["ELEMENT_EPOCH"] = pd.to_datetime(
    data["ELEMENT_EPOCH"], utc=True, errors="coerce"
)
data["PREDICTION_TIME_UTC"] = pd.to_datetime(
    data["PREDICTION_TIME_UTC"], utc=True, errors="coerce"
)

data = data.dropna(
    subset=[
        "NORAD_CAT_ID",
        "PREDICTION_TIME_UTC",
        "X_TEME_KM",
        "Y_TEME_KM",
        "Z_TEME_KM",
    ]
)

if data.empty:
    st.error("No valid prediction records are available.")
    st.stop()

# Sidebar controls
st.sidebar.header("Explore Debris")

search = st.sidebar.text_input("Search by object name or NORAD ID")

filtered = data.copy()
if search.strip():
    query = search.strip().lower()
    filtered = filtered[
        filtered["OBJECT_NAME"].astype(str).str.lower().str.contains(
            query, regex=False, na=False
        )
        | filtered["NORAD_CAT_ID"].str.contains(
            query, regex=False, na=False
        )
    ]

if filtered.empty:
    st.warning("No debris objects match your search.")
    st.stop()

object_ids = sorted(filtered["NORAD_CAT_ID"].unique())

selected_id = st.sidebar.selectbox(
    "Select a debris object",
    object_ids,
    format_func=lambda object_id: (
        f"{object_id} — "
        f"{filtered.loc[filtered['NORAD_CAT_ID'] == object_id, 'OBJECT_NAME'].iloc[0]}"
    ),
)

selected = filtered[filtered["NORAD_CAT_ID"] == selected_id].copy()
selected = selected.sort_values("MINUTES_FROM_START")

# Summary cards
total_objects = data["NORAD_CAT_ID"].nunique()
total_positions = len(data)
latest_time = data["PREDICTION_TIME_UTC"].max()

st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background: linear-gradient(
            145deg,
            rgba(17, 35, 59, 0.95),
            rgba(10, 24, 42, 0.95)
        );
        border: 1px solid rgba(54, 217, 245, 0.22);
        padding: 18px 20px;
        border-radius: 14px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.16);
    }

    div[data-testid="stMetricLabel"] {
        color: #A8BEDA;
        font-size: 13px;
    }

    div[data-testid="stMetricValue"] {
        color: #F4F8FF;
        font-size: 30px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3 = st.columns(3)

m1.metric("Debris Objects", f"{total_objects:,}")
m2.metric("Position Records", f"{total_positions:,}")
m3.metric(
    "Objects Matching Search",
    f"{filtered['NORAD_CAT_ID'].nunique():,}",
)

st.divider()

st.subheader("Selected Object")

st.markdown(
    f"""
    <div style="
        background: linear-gradient(
            135deg,
            rgba(17, 35, 59, 0.96),
            rgba(10, 24, 42, 0.96)
        );
        border: 1px solid rgba(54, 217, 245, 0.25);
        border-radius: 16px;
        padding: 22px 24px;
        margin: 10px 0 20px 0;
    ">
        <div style="
            color: #36D9F5;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 2px;
            margin-bottom: 8px;
        ">TRACKED OBJECT</div>

        <div style="
            color: #F4F8FF;
            font-size: 25px;
            font-weight: 700;
            margin-bottom: 18px;
        ">{selected['OBJECT_NAME'].iloc[0]}</div>

        <div style="color: #A8BEDA; font-size: 14px; line-height: 2;">
            <b style="color: #DCEAFF;">NORAD Catalog ID:</b> {selected_id}<br>
            <b style="color: #DCEAFF;">Orbital Element Epoch (UTC):</b>
            {selected['ELEMENT_EPOCH'].iloc[0]}<br>
            <b style="color: #DCEAFF;">Latest Generated Prediction (UTC):</b>
            {latest_time}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
# Interactive 3D trajectory
st.subheader("Predicted Positions in 3D")

fig = go.Figure()

fig.add_trace(
    go.Scatter3d(
        x=selected["X_TEME_KM"],
        y=selected["Y_TEME_KM"],
        z=selected["Z_TEME_KM"],
        mode="lines+markers",
        name="Predicted positions",
        marker=dict(
            size=5,
            color=selected["MINUTES_FROM_START"],
                        colorscale=[
                [0.0, "#2563eb"],
                [0.5, "#06b6d4"],
                [1.0, "#67e8f9"],
            ],
            colorbar=dict(
                title=dict(text="Minutes", font=dict(color="#DCEAFF")),
                tickfont=dict(color="#DCEAFF"),
                bgcolor="#101e31",
                outlinecolor="#29435f",
            ),
        ),
        line=dict(width=4),
        customdata=selected[["PREDICTION_TIME_UTC"]].astype(str),
        hovertemplate=(
            "X: %{x:.2f} km<br>"
            "Y: %{y:.2f} km<br>"
            "Z: %{z:.2f} km<br>"
            "Time: %{customdata[0]}<extra></extra>"
        ),
    )
)

fig.update_layout(
    height=560,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#091525",
    font=dict(
        family="Arial, sans-serif",
        color="#DCEAFF",
        size=12,
    ),
    scene=dict(
        bgcolor="#091525",
        xaxis=dict(
            title="X TEME (km)",
            backgroundcolor="#091525",
            gridcolor="rgba(91,157,230,0.22)",
            zerolinecolor="rgba(54,217,245,0.45)",
            showbackground=True,
            color="#B8CAE3",
        ),
        yaxis=dict(
            title="Y TEME (km)",
            backgroundcolor="#091525",
            gridcolor="rgba(91,157,230,0.22)",
            zerolinecolor="rgba(54,217,245,0.45)",
            showbackground=True,
            color="#B8CAE3",
        ),
        zaxis=dict(
            title="Z TEME (km)",
            backgroundcolor="#091525",
            gridcolor="rgba(91,157,230,0.22)",
            zerolinecolor="rgba(54,217,245,0.45)",
            showbackground=True,
            color="#B8CAE3",
        ),
        aspectmode="data",
    ),
    margin=dict(l=0, r=0, t=25, b=0),
    legend=dict(
        bgcolor="rgba(10,20,37,0.75)",
        font=dict(color="#DCEAFF"),
    ),
)

st.plotly_chart(fig, use_container_width=True)

# Coordinate chart
st.subheader("Position Components Over Time")

coordinate_data = selected.melt(
    id_vars=["MINUTES_FROM_START"],
    value_vars=["X_TEME_KM", "Y_TEME_KM", "Z_TEME_KM"],
    var_name="Coordinate",
    value_name="Position (km)",
)

coordinate_fig = px.line(
    coordinate_data,
    x="MINUTES_FROM_START",
    y="Position (km)",
    color="Coordinate",
    markers=True,
    color_discrete_map={
        "X_TEME_KM": "#36D9F5",
        "Y_TEME_KM": "#5587FF",
        "Z_TEME_KM": "#B794F6",
    },
)
coordinate_fig.update_layout(
    height=380,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#091525",
    font=dict(
        family="Arial, sans-serif",
        color="#DCEAFF",
        size=12,
    ),
    xaxis=dict(
        title="Minutes from propagation start",
        gridcolor="rgba(91,157,230,0.18)",
        zerolinecolor="rgba(91,157,230,0.3)",
        linecolor="#29435f",
    ),
    yaxis=dict(
        title="Position (km)",
        gridcolor="rgba(91,157,230,0.18)",
        zerolinecolor="rgba(91,157,230,0.3)",
        linecolor="#29435f",
    ),
    legend=dict(
        title=dict(text="Coordinate"),
        bgcolor="rgba(10,20,37,0.75)",
        font=dict(color="#DCEAFF"),
    ),
    margin=dict(l=15, r=15, t=30, b=15),
)
st.plotly_chart(coordinate_fig, use_container_width=True)

# Prediction table
st.subheader("Position Records")

display_columns = [
    "NORAD_CAT_ID",
    "OBJECT_NAME",
    "PREDICTION_TIME_UTC",
    "MINUTES_FROM_START",
    "X_TEME_KM",
    "Y_TEME_KM",
    "Z_TEME_KM",
]

st.markdown(
    """
    <style>
    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(54, 217, 245, 0.22);
        border-radius: 12px;
        overflow: hidden;
    }

    div[data-testid="stDownloadButton"] button {
        background: linear-gradient(90deg, #087ca7, #2563eb);
        color: #ffffff;
        border: 1px solid rgba(54, 217, 245, 0.4);
        border-radius: 9px;
        padding: 10px 18px;
        font-weight: 600;
    }

    div[data-testid="stDownloadButton"] button:hover {
        border-color: #36D9F5;
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(54, 217, 245, 0.22);
        border-radius: 12px;
        overflow: hidden;
    }

    div[data-testid="stDownloadButton"] button {
        background: linear-gradient(90deg, #087ca7, #2563eb);
        color: #ffffff;
        border: 1px solid rgba(54, 217, 245, 0.4);
        border-radius: 9px;
        padding: 10px 18px;
        font-weight: 600;
    }

    div[data-testid="stDownloadButton"] button:hover {
        border-color: #36D9F5;
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.dataframe(
    selected[display_columns].reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    label="⬇️ Download Selected Object Predictions",
    data=selected[display_columns].to_csv(index=False),
    file_name=f"debris_{selected_id}_predictions.csv",
    mime="text/csv",
    use_container_width=True,
)

# Data quality panel
st.divider()
st.header("Orbital Data Quality")

if QUALITY_FILE.exists():
    quality = pd.read_csv(QUALITY_FILE)

    if {"NORAD_CAT_ID", "ELEMENT_AGE_HOURS", "DATA_QUALITY_STATUS"}.issubset(quality.columns):
        quality["NORAD_CAT_ID"] = quality["NORAD_CAT_ID"].astype(str)
        quality["ELEMENT_AGE_HOURS"] = pd.to_numeric(
            quality["ELEMENT_AGE_HOURS"], errors="coerce"
        )

        selected_quality = quality[
            quality["NORAD_CAT_ID"] == selected_id
        ]

        if not selected_quality.empty:
            row = selected_quality.iloc[0]
            q1, q2 = st.columns(2)
            q1.metric(
                "Element Age",
                f"{row['ELEMENT_AGE_HOURS']:.1f} hours"
                if pd.notna(row["ELEMENT_AGE_HOURS"])
                else "Unknown",
            )
            q2.metric("Age-Based Review Status", str(row["DATA_QUALITY_STATUS"]))

        counts = (
            quality["DATA_QUALITY_STATUS"]
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Objects")
        )

        quality_fig = px.bar(
            counts,
            x="Status",
            y="Objects",
            color="Status",
            title="Objects by orbital element age category",
        )
        st.plotly_chart(quality_fig, use_container_width=True)
    else:
        st.warning(
            "The quality report is missing expected columns. "
            "Run orbital_quality_report.py again."
        )
else:
    st.info(
        "The quality report is not available yet. "
        "Run: python orbital_quality_report.py"
    )

st.caption(
    "OrbiX prototype. The displayed trajectory represents sampled "
    "SGP4 predictions, not a complete orbital-period path. "
    "Element age is a screening indicator, not a direct measure of accuracy."
)