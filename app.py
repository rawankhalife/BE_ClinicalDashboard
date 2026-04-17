import json
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="VR Biofeedback Dashboard",
    layout="wide",
    page_icon="🧠"
)

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# ---------- Styling ----------
st.markdown("""
<style>
    .main {
        background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
    }

    .hero-card {
        background: rgba(255,255,255,0.92);
        padding: 2.2rem;
        border-radius: 24px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.07);
        border: 1px solid rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }

    .info-text {
        color: #5f6b7a;
        font-size: 0.98rem;
    }

    .upload-panel {
        background: rgba(255,255,255,0.92);
        padding: 1.6rem;
        border-radius: 24px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.07);
        border: 1px solid rgba(0,0,0,0.05);
    }

    .section-gap {
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def prepare_df(df):
    if df.empty:
        return df
    df = df.copy()

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
    if "bpm" in df.columns:
        df["bpm"] = pd.to_numeric(df["bpm"], errors="coerce")
    if "gsr" in df.columns:
        df["gsr"] = df["gsr"].fillna("NA").astype(str)

    return df


def load_json(uploaded_file):
    try:
        uploaded_file.seek(0)
        return json.load(uploaded_file)
    except Exception:
        return None


def reset_uploader():
    st.session_state.uploader_key += 1
    st.rerun()


# ---------- Landing ----------
left, right = st.columns([1.25, 1], vertical_alignment="center")

with left:
    st.markdown("""
    <div class="hero-card">
        <h1 style="margin-bottom:0.5rem;">VR Biofeedback Dashboard</h1>
        <p class="info-text" style="margin-top:0;">
            Review patient session data from a single uploaded JSON file.
        </p>
        <hr style="margin:1rem 0 1.2rem 0; border:none; border-top:1px solid #e8edf5;">
        <p style="margin-bottom:0.8rem;">This dashboard helps you inspect:</p>
        <ul style="line-height:1.9;">
            <li>Baseline physiological signals</li>
            <li>Exposure-phase heart rate trends</li>
            <li>GSR state distribution</li>
            <li>Session events and progression</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with right:
    st.markdown('<div class="upload-panel">', unsafe_allow_html=True)
    st.subheader("Upload Session File")
    uploaded_file = st.file_uploader(
        "Choose a JSON session file",
        type=["json"],
        key=f"session_uploader_{st.session_state.uploader_key}",
        help="Upload one session JSON file to open the analysis dashboard."
    )
    st.caption("Accepted format: .json")
    st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file is None:
    st.info("Upload a session JSON file to open the analysis page.")
    st.stop()

data = load_json(uploaded_file)

if data is None:
    st.error("The uploaded file is not a valid JSON file.")
    st.stop()

baseline_df = pd.DataFrame(data.get("baselineMetrics", []))
exposure_df = pd.DataFrame(data.get("metrics", []))
events_df = pd.DataFrame(data.get("events", []))

if baseline_df.empty and exposure_df.empty:
    st.warning("No baseline or exposure data found in this file.")
    st.stop()

baseline_df = prepare_df(baseline_df)
exposure_df = prepare_df(exposure_df)

session_id = data.get("sessionId", "N/A")
raw_date = data.get("date", "N/A")
duration = round(float(data.get("durationSeconds", 0)), 2)

try:
    formatted_date = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y, %I:%M %p")
except Exception:
    formatted_date = raw_date

baseline_avg_bpm = round(baseline_df["bpm"].dropna().mean(), 1) if not baseline_df.empty and "bpm" in baseline_df.columns else "N/A"
exposure_avg_bpm = round(exposure_df["bpm"].dropna().mean(), 1) if not exposure_df.empty and "bpm" in exposure_df.columns else "N/A"
exposure_max_bpm = int(exposure_df["bpm"].dropna().max()) if not exposure_df.empty and "bpm" in exposure_df.columns and not exposure_df["bpm"].dropna().empty else "N/A"
exposure_min_bpm = int(exposure_df["bpm"].dropna().min()) if not exposure_df.empty and "bpm" in exposure_df.columns and not exposure_df["bpm"].dropna().empty else "N/A"

baseline_gsr = "N/A"
if not baseline_df.empty and "gsr" in baseline_df.columns:
    valid_baseline_gsr = baseline_df[baseline_df["gsr"].str.upper() != "NA"]["gsr"]
    if not valid_baseline_gsr.empty:
        baseline_gsr = valid_baseline_gsr.mode().iloc[0]

dominant_exposure_gsr = "N/A"
if not exposure_df.empty and "gsr" in exposure_df.columns:
    valid_exposure_gsr = exposure_df[exposure_df["gsr"].str.upper() != "NA"]["gsr"]
    if not valid_exposure_gsr.empty:
        dominant_exposure_gsr = valid_exposure_gsr.mode().iloc[0]

event_count = len(events_df)
baseline_samples = len(baseline_df)
exposure_samples = len(exposure_df)

st.markdown("---")

header_left, header_right = st.columns([3, 1])

with header_left:
    st.title("Patient Session Analysis")
    st.caption(f"Loaded file: {uploaded_file.name}")

with header_right:
    st.write("")
    st.write("")
    st.button("Upload Another File", on_click=reset_uploader, use_container_width=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Session ID", session_id)
c2.metric("Session Date", formatted_date)
c3.metric("Duration (sec)", duration)
c4.metric("Total Events", event_count)

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Baseline Summary")
    b1, b2 = st.columns(2)
    b1.metric("Baseline Avg BPM", baseline_avg_bpm)
    b2.metric("Baseline GSR", baseline_gsr)
    st.caption(f"Baseline samples recorded: {baseline_samples}")

with right:
    st.subheader("Exposure Summary")
    e1, e2, e3 = st.columns(3)
    e1.metric("Exposure Avg BPM", exposure_avg_bpm)
    e2.metric("Exposure Max BPM", exposure_max_bpm)
    e3.metric("Exposure Min BPM", exposure_min_bpm)
    st.caption(f"Dominant exposure GSR: {dominant_exposure_gsr} | Exposure samples recorded: {exposure_samples}")

st.divider()

st.subheader("Session Interpretation")

interpretation = "No exposure data available."
if not exposure_df.empty and baseline_avg_bpm != "N/A" and exposure_avg_bpm != "N/A":
    if exposure_max_bpm != "N/A" and exposure_max_bpm >= baseline_avg_bpm * 1.4:
        interpretation = "This session shows a strong stress response during exposure compared to baseline."
    elif exposure_avg_bpm >= baseline_avg_bpm * 1.2:
        interpretation = "This session shows an elevated physiological response during exposure."
    else:
        interpretation = "This session remained relatively close to baseline, indicating a stable response."

st.info(interpretation)

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Baseline Signals",
    "Exposure Signals",
    "GSR Summary",
    "Events",
    "Raw Tables"
])

with tab1:
    st.subheader("Baseline Heart Rate")
    if not baseline_df.empty and "bpm" in baseline_df.columns:
        fig = px.line(
            baseline_df,
            x="timestamp",
            y="bpm",
            title="Baseline BPM vs Time",
            markers=False
        )
        fig.update_layout(xaxis_title="Time (seconds)", yaxis_title="BPM")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No baseline BPM data available.")

with tab2:
    st.subheader("Exposure Heart Rate")
    if not exposure_df.empty and "bpm" in exposure_df.columns:
        fig = px.line(
            exposure_df,
            x="timestamp",
            y="bpm",
            color="systemState" if "systemState" in exposure_df.columns else None,
            title="Exposure BPM vs Time",
            markers=False
        )
        fig.update_layout(xaxis_title="Time (seconds)", yaxis_title="BPM")
        st.plotly_chart(fig, use_container_width=True)

        if "level" in exposure_df.columns:
            level_fig = px.scatter(
                exposure_df,
                x="timestamp",
                y="level",
                color="systemState" if "systemState" in exposure_df.columns else None,
                title="Exposure Level Progression"
            )
            level_fig.update_layout(xaxis_title="Time (seconds)", yaxis_title="Level")
            st.plotly_chart(level_fig, use_container_width=True)
    else:
        st.write("No exposure BPM data available.")

with tab3:
    st.subheader("GSR State Distribution")
    if not exposure_df.empty and "gsr" in exposure_df.columns:
        gsr_plot_df = exposure_df[exposure_df["gsr"].str.upper() != "NA"].copy()
        if not gsr_plot_df.empty:
            gsr_counts = gsr_plot_df["gsr"].value_counts().reset_index()
            gsr_counts.columns = ["GSR State", "Count"]

            fig = px.bar(
                gsr_counts,
                x="Count",
                y="GSR State",
                color="GSR State",
                text="Count",
                orientation="h",
                title="Exposure GSR Distribution"
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            max_count = gsr_counts["Count"].max()
            fig.update_layout(
                xaxis_title="Count",
                yaxis_title="GSR State",
                showlegend=False,
                xaxis=dict(range=[0, max_count * 1.2 if max_count > 0 else 1])
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No valid exposure GSR data available.")
    else:
        st.write("No GSR data available.")

with tab4:
    st.subheader("Session Events")
    if not events_df.empty:
        if "timestamp" in events_df.columns:
            events_df["timestamp"] = pd.to_numeric(events_df["timestamp"], errors="coerce").round(2)

        cols = [c for c in ["timestamp", "eventType", "details", "level", "path"] if c in events_df.columns]
        st.dataframe(events_df[cols], use_container_width=True, height=350)

        if "eventType" in events_df.columns:
            event_counts = events_df["eventType"].value_counts().reset_index()
            event_counts.columns = ["Event Type", "Count"]

            fig = px.bar(
                event_counts,
                x="Count",
                y="Event Type",
                orientation="h",
                text="Count",
                title="Event Frequency"
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No events found in this session file.")

with tab5:
    st.subheader("Raw Baseline Data")
    if not baseline_df.empty:
        baseline_show = baseline_df.copy()
        if "timestamp" in baseline_show.columns:
            baseline_show["timestamp"] = baseline_show["timestamp"].round(4)
        st.dataframe(baseline_show, use_container_width=True, height=250)
    else:
        st.write("No baseline table available.")

    st.subheader("Raw Exposure Data")
    if not exposure_df.empty:
        exposure_show = exposure_df.copy()
        if "timestamp" in exposure_show.columns:
            exposure_show["timestamp"] = exposure_show["timestamp"].round(4)
        st.dataframe(exposure_show, use_container_width=True, height=250)
    else:
        st.write("No exposure table available.")
