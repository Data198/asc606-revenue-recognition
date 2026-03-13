"""Plotly chart builders for ASC 606 visualizations."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

COLORS = {
    "primary": "#1E3A5F",
    "secondary": "#3D6B99",
    "accent": "#5BA4E6",
    "light": "#8BC4F0",
    "success": "#28a745",
    "danger": "#dc3545",
}


def revenue_waterfall_chart(schedule_df, title="Revenue Recognition Schedule"):
    """Stacked bar chart showing revenue recognition over time by obligation."""
    if schedule_df.empty:
        return go.Figure()

    pivot = schedule_df.pivot_table(
        index="period", columns="obligation", values="amount", aggfunc="sum", fill_value=0
    ).reset_index()

    fig = go.Figure()
    colors = [COLORS["primary"], COLORS["secondary"], COLORS["accent"], COLORS["light"]]
    for i, col in enumerate([c for c in pivot.columns if c != "period"]):
        fig.add_trace(go.Bar(
            x=pivot["period"], y=pivot[col], name=col,
            marker_color=colors[i % len(colors)],
        ))

    fig.update_layout(
        title=title, barmode="stack",
        xaxis_title="Period", yaxis_title="Revenue (USD)",
        yaxis_tickprefix="$", yaxis_tickformat=",",
        plot_bgcolor="rgba(0,0,0,0)", height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def cumulative_recognition_chart(schedule_df, total_price, title="Cumulative Revenue Recognition"):
    """Line chart showing cumulative revenue vs total transaction price."""
    if schedule_df.empty:
        return go.Figure()

    cumulative = schedule_df.groupby("period")["amount"].sum().cumsum().reset_index()
    cumulative.columns = ["period", "cumulative"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cumulative["period"], y=cumulative["cumulative"],
        mode="lines+markers", name="Recognized Revenue",
        line=dict(color=COLORS["primary"], width=2.5),
        fill="tozeroy", fillcolor="rgba(30, 58, 95, 0.1)",
    ))
    fig.add_hline(y=total_price, line_dash="dash", line_color=COLORS["danger"],
                  annotation_text=f"Total Transaction Price: ${total_price:,.0f}")

    fig.update_layout(
        title=title,
        xaxis_title="Period", yaxis_title="Revenue (USD)",
        yaxis_tickprefix="$", yaxis_tickformat=",",
        plot_bgcolor="rgba(0,0,0,0)", height=400,
    )
    return fig


def deferred_revenue_chart(schedule_df, total_price, title="Deferred Revenue Balance"):
    """Area chart showing deferred revenue declining over time."""
    if schedule_df.empty:
        return go.Figure()

    cumulative = schedule_df.groupby("period")["amount"].sum().cumsum().reset_index()
    cumulative.columns = ["period", "cumulative"]
    cumulative["deferred"] = total_price - cumulative["cumulative"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cumulative["period"], y=cumulative["deferred"],
        mode="lines+markers", name="Deferred Revenue",
        line=dict(color=COLORS["accent"], width=2.5),
        fill="tozeroy", fillcolor="rgba(91, 164, 230, 0.1)",
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Period", yaxis_title="Deferred Revenue (USD)",
        yaxis_tickprefix="$", yaxis_tickformat=",",
        plot_bgcolor="rgba(0,0,0,0)", height=400,
    )
    return fig


def ssp_allocation_pie(allocations, title="Transaction Price Allocation"):
    """Pie chart of SSP allocation by obligation."""
    names = [a["obligation"] for a in allocations]
    values = [a["allocated_price"] for a in allocations]

    fig = px.pie(
        values=values, names=names, title=title, hole=0.4,
        color_discrete_sequence=[COLORS["primary"], COLORS["secondary"], COLORS["accent"], COLORS["light"]],
    )
    fig.update_layout(height=350)
    return fig


def principal_agent_gauge(score_pct, title="Principal vs. Agent Assessment"):
    """Gauge chart showing principal/agent score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score_pct,
        title={"text": title},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": COLORS["primary"]},
            "steps": [
                {"range": [0, 40], "color": "#ffcccc"},
                {"range": [40, 60], "color": "#fff3cd"},
                {"range": [60, 100], "color": "#d4edda"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": 60,
            },
        },
        number={"suffix": "%"},
    ))
    fig.update_layout(height=300)
    return fig
