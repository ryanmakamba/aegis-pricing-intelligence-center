from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data import generate_portfolio
from pricing import add_pricing_metrics, portfolio_summary, run_scenario, segment_summary


st.set_page_config(
    page_title="Aegis Pricing Intelligence Center",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#10233f"
SLATE = "#52677f"
TEAL = "#408b8e"
COPPER = "#b75f3f"
GOLD = "#c5913c"
OFF_WHITE = "#f5f2eb"

st.markdown(
    f"""
    <style>
    .stApp {{ background: {OFF_WHITE}; color: {NAVY}; }}
    [data-testid="stSidebar"] {{ background: #ebe7de; border-right: 1px solid #d7d0c3; }}
    [data-testid="stMetric"] {{
        background: rgba(255,255,255,.70); border: 1px solid #d8d2c7;
        border-radius: 14px; padding: 16px 18px; min-height: 122px;
    }}
    [data-testid="stMetricLabel"] {{ color: {SLATE}; }}
    [data-testid="stMetricValue"] {{ color: {NAVY}; font-family: Georgia, serif; }}
    h1, h2, h3 {{ color: {NAVY}; }}
    h1 {{ font-family: Georgia, serif; letter-spacing: -1px; }}
    .eyebrow {{ color: {COPPER}; font-size: .77rem; font-weight: 800; letter-spacing: .18em; text-transform: uppercase; }}
    .hero {{ background: {NAVY}; padding: 28px 30px; border-radius: 18px; color: white; margin-bottom: 22px; }}
    .hero h1 {{ color: white; margin: 4px 0 6px; font-size: 2.35rem; }}
    .hero p {{ color: #dbe4ee; margin: 0; max-width: 800px; }}
    .callout {{ background: #fffaf1; border-left: 4px solid {GOLD}; padding: 14px 18px; border-radius: 8px; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 12px; }}
    .stTabs [data-baseweb="tab"] {{ background: transparent; color: {SLATE}; font-weight: 700; }}
    .stTabs [aria-selected="true"] {{ color: {NAVY}; border-bottom-color: {COPPER}; }}
    footer {{ visibility: hidden; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    return add_pricing_metrics(generate_portfolio())


def money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:,.1f}K"
    return f"${value:,.0f}"


def chart_layout(fig, height=390):
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=55, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.45)",
        font=dict(color=NAVY, family="Arial"),
        legend_title_text="",
    )
    return fig


df = load_data()

with st.sidebar:
    st.markdown("### AEGIS")
    st.caption("Pricing Intelligence Center")
    st.divider()
    selected_lines = st.multiselect(
        "Lines of business",
        sorted(df["line_of_business"].unique()),
        default=sorted(df["line_of_business"].unique()),
    )
    selected_states = st.multiselect(
        "States",
        sorted(df["state"].unique()),
        default=sorted(df["state"].unique()),
    )
    selected_years = st.multiselect(
        "Policy years",
        sorted(df["policy_year"].unique()),
        default=sorted(df["policy_year"].unique()),
    )
    target_lr_pct = st.slider("Target loss ratio", 50, 80, 65, 1)
    target_lr = target_lr_pct / 100
    st.divider()
    st.caption("Demonstration portfolio · Synthetic data")

filtered = df[
    df["line_of_business"].isin(selected_lines)
    & df["state"].isin(selected_states)
    & df["policy_year"].isin(selected_years)
]

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow" style="color:#d9a66c">Property &amp; Casualty Pricing</div>
      <h1>Aegis Pricing Intelligence Center</h1>
      <p>Portfolio adequacy, frequency and severity diagnostics, and transparent rate indications for defensible pricing decisions.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if filtered.empty:
    st.warning("Select at least one value from each filter to display the portfolio analysis.")
    st.stop()

summary = portfolio_summary(filtered, target_lr)

tabs = st.tabs(["Executive View", "Portfolio Segmentation", "Frequency & Severity", "Scenario Lab", "Data & Methodology"])

with tabs[0]:
    a, b, c, d, e = st.columns(5)
    a.metric("Earned Premium", money(summary["premium"]))
    b.metric("Incurred Loss", money(summary["losses"]))
    c.metric("Loss Ratio", f"{summary['loss_ratio']:.1%}", f"{summary['loss_ratio']-target_lr:+.1%} vs target", delta_color="inverse")
    d.metric("Combined Ratio", f"{summary['combined_ratio']:.1%}", "Profitable" if summary["combined_ratio"] < 1 else "Above 100%", delta_color="normal" if summary["combined_ratio"] < 1 else "inverse")
    e.metric("Indicated Rate Change", f"{summary['indicated_change']:+.1%}")

    left, right = st.columns([1.45, 1])
    with left:
        trend = segment_summary(filtered, "policy_year", target_lr)
        fig = go.Figure()
        fig.add_bar(x=trend["policy_year"], y=trend["earned_premium"], name="Earned Premium", marker_color=SLATE, yaxis="y")
        fig.add_scatter(x=trend["policy_year"], y=trend["loss_ratio"], name="Loss Ratio", mode="lines+markers", line=dict(color=COPPER, width=3), yaxis="y2")
        fig.update_layout(
            title="Premium and Loss-Ratio Trend",
            yaxis=dict(title="Earned premium", tickprefix="$", tickformat="~s"),
            yaxis2=dict(title="Loss ratio", overlaying="y", side="right", tickformat=".0%", range=[0, max(1, trend["loss_ratio"].max() * 1.2)]),
        )
        st.plotly_chart(chart_layout(fig), use_container_width=True)
    with right:
        lob = segment_summary(filtered, "line_of_business", target_lr)
        fig = px.bar(
            lob.sort_values("loss_ratio"), x="loss_ratio", y="line_of_business", orientation="h",
            color="loss_ratio", color_continuous_scale=[[0, TEAL], [.65, GOLD], [1, COPPER]],
            title="Loss Ratio by Line of Business", text_auto=".1%",
        )
        fig.add_vline(x=target_lr, line_dash="dash", line_color=NAVY, annotation_text="Target")
        fig.update_xaxes(tickformat=".0%", title="Loss ratio")
        fig.update_yaxes(title="")
        st.plotly_chart(chart_layout(fig), use_container_width=True)

    action = lob.iloc[0]
    st.markdown(
        f"<div class='callout'><strong>Pricing signal:</strong> {action['line_of_business']} has the highest selected loss ratio at "
        f"<strong>{action['loss_ratio']:.1%}</strong>, producing an indicated rate action of "
        f"<strong>{action['indicated_rate_change']:+.1%}</strong> against the {target_lr:.0%} target.</div>",
        unsafe_allow_html=True,
    )

with tabs[1]:
    dimension_labels = {
        "Line of business": "line_of_business",
        "Risk tier": "risk_tier",
        "State": "state",
        "Distribution channel": "distribution_channel",
    }
    label = st.selectbox("Analyze portfolio by", list(dimension_labels))
    dimension = dimension_labels[label]
    segments = segment_summary(filtered, dimension, target_lr)
    left, right = st.columns([1.3, 1])
    with left:
        fig = px.scatter(
            segments,
            x="earned_premium",
            y="loss_ratio",
            size="incurred_loss",
            color="pricing_action",
            hover_name=dimension,
            color_discrete_map={"Increase": COPPER, "Maintain": GOLD, "Review for growth": TEAL},
            title=f"Pricing Position by {label}",
        )
        fig.add_hline(y=target_lr, line_dash="dash", line_color=NAVY, annotation_text="Target")
        fig.update_xaxes(tickprefix="$", tickformat="~s")
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(chart_layout(fig, 440), use_container_width=True)
    with right:
        display = segments[[dimension, "earned_premium", "incurred_loss", "loss_ratio", "indicated_rate_change", "pricing_action"]].copy()
        st.dataframe(
            display,
            hide_index=True,
            use_container_width=True,
            column_config={
                dimension: st.column_config.TextColumn(label),
                "earned_premium": st.column_config.NumberColumn("Earned Premium", format="$%.0f"),
                "incurred_loss": st.column_config.NumberColumn("Incurred Loss", format="$%.0f"),
                "loss_ratio": st.column_config.NumberColumn("Loss Ratio", format="%.1%%"),
                "indicated_rate_change": st.column_config.NumberColumn("Indicated Change", format="%.1%%"),
                "pricing_action": "Pricing Action",
            },
            height=440,
        )

with tabs[2]:
    a, b, c = st.columns(3)
    a.metric("Claim Frequency", f"{summary['frequency']:.2%}", help="Claim count divided by earned exposure")
    b.metric("Average Severity", money(summary["severity"]), help="Incurred loss divided by claim count")
    c.metric("Reported Claims", f"{summary['claims']:,}")
    dimension = st.selectbox("Compare by", ["line_of_business", "risk_tier", "state"], format_func=lambda x: x.replace("_", " ").title(), key="freq_dimension")
    freq = segment_summary(filtered, dimension, target_lr)
    left, right = st.columns(2)
    fig = px.bar(freq, x=dimension, y="frequency", color=dimension, title="Claim Frequency", text_auto=".2%", color_discrete_sequence=[NAVY, SLATE, TEAL, GOLD, COPPER])
    fig.update_yaxes(tickformat=".1%")
    fig.update_xaxes(title="")
    left.plotly_chart(chart_layout(fig), use_container_width=True)
    fig = px.bar(freq, x=dimension, y="severity", color=dimension, title="Average Claim Severity", text_auto="$.3s", color_discrete_sequence=[NAVY, SLATE, TEAL, GOLD, COPPER])
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    fig.update_xaxes(title="")
    right.plotly_chart(chart_layout(fig), use_container_width=True)

with tabs[3]:
    st.subheader("Forward Pricing Scenario")
    st.caption("Adjust the assumptions to test how trend and pricing actions affect the selected portfolio.")
    c1, c2, c3, c4 = st.columns(4)
    severity_trend = c1.slider("Severity trend", -10, 30, 8, 1) / 100
    frequency_trend = c2.slider("Frequency trend", -10, 20, 3, 1) / 100
    premium_change = c3.slider("Proposed premium change", -10, 30, 6, 1) / 100
    expense_ratio = c4.slider("Expense ratio", 15, 40, 27, 1) / 100
    scenario = run_scenario(filtered, severity_trend, frequency_trend, premium_change, expense_ratio, target_lr)
    a, b, c, d = st.columns(4)
    a.metric("Projected Premium", money(scenario["premium"]), f"{premium_change:+.1%}")
    b.metric("Projected Loss Ratio", f"{scenario['loss_ratio']:.1%}", f"{scenario['loss_ratio']-summary['loss_ratio']:+.1%}", delta_color="inverse")
    c.metric("Projected Combined Ratio", f"{scenario['combined_ratio']:.1%}")
    d.metric("Underwriting Result", money(scenario["underwriting_result"]))
    gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=scenario["loss_ratio"] * 100,
        number={"suffix": "%", "valueformat": ".1f"},
        delta={"reference": target_lr * 100, "increasing": {"color": COPPER}, "decreasing": {"color": TEAL}},
        title={"text": "Projected Loss Ratio vs Target"},
        gauge={
            "axis": {"range": [0, max(110, scenario["loss_ratio"] * 125)], "ticksuffix": "%"},
            "bar": {"color": NAVY},
            "steps": [
                {"range": [0, target_lr * 100], "color": "#dcebe5"},
                {"range": [target_lr * 100, 85], "color": "#f3e3bd"},
                {"range": [85, 120], "color": "#ecd0c5"},
            ],
            "threshold": {"line": {"color": COPPER, "width": 4}, "value": target_lr * 100},
        },
    ))
    st.plotly_chart(chart_layout(gauge, 360), use_container_width=True)

with tabs[4]:
    st.subheader("Data and Methodology")
    st.info("This application uses a reproducible synthetic portfolio. It contains no customer or proprietary insurer data.")
    st.markdown(
        """
        **Core calculations**

        - Claim frequency = reported claim count ÷ earned exposure
        - Claim severity = incurred losses ÷ reported claim count
        - Loss ratio = incurred losses ÷ earned premium
        - Combined ratio = loss ratio + expense ratio
        - Indicated rate change = current loss ratio ÷ target loss ratio − 1

        The model is intended to demonstrate insurance analytics, portfolio monitoring, and transparent pricing logic. It is not intended for production ratemaking or regulatory filing.
        """
    )
    export = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download selected portfolio data", export, "aegis_pricing_portfolio.csv", "text/csv")
    st.dataframe(filtered.head(250), use_container_width=True, hide_index=True)

st.markdown("<br><small>© 2026 Aegis Group by Ryan Makamba · Demonstration analytics platform</small>", unsafe_allow_html=True)

