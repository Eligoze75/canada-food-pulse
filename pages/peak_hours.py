"""
Peak Hours Page — weekday × hour heatmap of check-in traffic.

Route: /peak-hours
"""

import pathlib

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

dash.register_page(__name__, path="/peak-hours", name="Peak Hours", order=3)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"
df_heat = pd.read_csv(DATA_DIR / "df_peak_heatmap.csv")
df_biz = pd.read_csv(DATA_DIR / "df_businesses.csv", low_memory=False)
df_biz["name"] = df_biz["name"].str.strip('"')

WEEKDAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CITIES = ["Toronto", "Montreal"]
CITY_COLORS = {"Toronto": "#2c7be5", "Montreal": "#e5522c"}

# Pre-build business options (sorted by name) for the drill-down dropdown
# Merge peak data onto businesses so we know which have check-in data
biz_with_checkins = (
    df_biz[df_biz["total_checkins_all"] > 0]
    .sort_values("name")[["business_id", "name", "city_clean"]]
    .dropna(subset=["name"])
)

# Parse hour strings to integer for sorting (e.g. "9:00" → 9)
def hour_to_int(h: str) -> int:
    try:
        return int(str(h).split(":")[0])
    except Exception:
        return -1

df_heat["hour_int"] = df_heat["peak_hour"].apply(hour_to_int)
df_heat = df_heat.sort_values(["city_clean", "weekday", "hour_int"])

# Hour labels for display (0:00 → "12am", 12:00 → "12pm", etc.)
def fmt_hour(h: int) -> str:
    if h == 0:
        return "12am"
    elif h < 12:
        return f"{h}am"
    elif h == 12:
        return "12pm"
    else:
        return f"{h - 12}pm"

HOUR_LABELS = {i: fmt_hour(i) for i in range(24)}

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = html.Div([
    html.Div([
        html.H2("Peak Hours"),
        html.P("Understand when businesses are busiest — city-wide traffic patterns by day and hour."),
    ], className="page-header"),

    html.Div([
        html.Label("City"),
        dcc.Dropdown(
            id="peaks-city",
            options=[{"label": c, "value": c} for c in CITIES],
            value="Toronto",
            clearable=False,
            style={"minWidth": "160px"},
        ),
        html.Label("Drill-down to a specific business (optional)", style={"marginLeft": "1.5rem"}),
        dcc.Dropdown(
            id="peaks-business",
            options=[],
            value=None,
            clearable=True,
            placeholder="All businesses (city-wide)",
            style={"minWidth": "320px"},
        ),
    ], className="filter-bar"),

    # Main heatmap
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div(id="peaks-heatmap-title", className="section-title"),
                dcc.Graph(id="peaks-heatmap", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=8),
        dbc.Col([
            html.Div([
                html.Div("Busiest Day of the Week", className="section-title"),
                dcc.Graph(id="peaks-by-day", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=4),
    ]),

    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div("Hourly Traffic — Toronto vs Montreal", className="section-title"),
                dcc.Graph(id="peaks-hourly-compare", config={"displayModeBar": False}),
            ], className="chart-card"),
        ]),
    ]),
], className="page-content")


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("peaks-business", "options"),
    Input("peaks-city", "value"),
)
def update_business_options(city):
    df = biz_with_checkins[biz_with_checkins["city_clean"] == city]
    return [{"label": row["name"], "value": row["business_id"]} for _, row in df.iterrows()]


@callback(
    Output("peaks-heatmap", "figure"),
    Output("peaks-heatmap-title", "children"),
    Input("peaks-city", "value"),
    Input("peaks-business", "value"),
)
def update_heatmap(city, business_id):
    if business_id:
        # Business-level: use the cleaned source data
        from pathlib import Path
        src = Path(__file__).parent.parent / "data" / "processed" / "yelp_business_data_cleaned.csv"
        df_src = pd.read_csv(src, low_memory=False)
        df_biz_peaks = df_src[df_src["business_id"] == business_id].dropna(subset=["weekday", "peak_hour"])
        df_plot = (
            df_biz_peaks.groupby(["weekday", "peak_hour"], as_index=False)
            .agg(total_checkins=("total_checkins", "sum"))
        )
        biz_name = df_biz[df_biz["business_id"] == business_id]["name"].iloc[0]
        title = f"Peak Hours — {biz_name}"
    else:
        df_plot = df_heat[df_heat["city_clean"] == city].copy()
        title = f"Peak Hours — {city} (all businesses)"

    df_plot["hour_int"] = df_plot["peak_hour"].apply(hour_to_int)
    df_plot["hour_label"] = df_plot["hour_int"].map(HOUR_LABELS)
    df_plot["weekday"] = pd.Categorical(df_plot["weekday"], categories=WEEKDAY_ORDER, ordered=True)

    pivot = (
        df_plot.pivot_table(
            index="weekday",
            columns="hour_int",
            values="total_checkins",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(WEEKDAY_ORDER)
    )
    pivot.columns = [HOUR_LABELS.get(c, str(c)) for c in pivot.columns]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="YlOrRd",
        hoverongaps=False,
        hovertemplate="<b>%{y} %{x}</b><br>Check-ins: %{z:,}<extra></extra>",
        colorbar=dict(title="Check-ins", thickness=14),
    ))
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title="Hour of Day", tickangle=-45, tickfont=dict(size=10)),
        yaxis=dict(title=""),
        height=320,
    )
    return fig, title


@callback(
    Output("peaks-by-day", "figure"),
    Input("peaks-city", "value"),
    Input("peaks-business", "value"),
)
def update_by_day(city, business_id):
    if business_id:
        from pathlib import Path
        src = Path(__file__).parent.parent / "data" / "processed" / "yelp_business_data_cleaned.csv"
        df_src = pd.read_csv(src, low_memory=False)
        df_plot = df_src[df_src["business_id"] == business_id].dropna(subset=["weekday"])
    else:
        df_plot = df_heat[df_heat["city_clean"] == city]

    daily = (
        df_plot.groupby("weekday")["total_checkins"]
        .sum()
        .reindex(WEEKDAY_ORDER)
        .reset_index()
    )
    color = CITY_COLORS.get(city, "#2c7be5")

    fig = px.bar(
        daily, x="weekday", y="total_checkins",
        color="total_checkins",
        color_continuous_scale=["#d0e8ff", color],
        labels={"weekday": "", "total_checkins": "Check-ins"},
        text="total_checkins",
    )
    fig.update_traces(
        texttemplate="%{y:,.0f}",
        textposition="outside",
        textfont=dict(size=10),
    )
    fig.update_coloraxes(showscale=False)
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(categoryorder="array", categoryarray=WEEKDAY_ORDER),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0", title=""),
        height=320,
    )
    return fig


@callback(
    Output("peaks-hourly-compare", "figure"),
    Input("peaks-city", "value"),
)
def update_hourly_compare(_city):
    """Line chart comparing hourly traffic for Toronto vs Montreal."""
    hourly = (
        df_heat.groupby(["city_clean", "hour_int"])["total_checkins"]
        .sum()
        .reset_index()
    )
    hourly["hour_label"] = hourly["hour_int"].map(HOUR_LABELS)
    hourly = hourly.sort_values("hour_int")

    fig = px.line(
        hourly, x="hour_label", y="total_checkins",
        color="city_clean",
        color_discrete_map=CITY_COLORS,
        markers=True,
        labels={"hour_label": "Hour of Day", "total_checkins": "Total Check-ins", "city_clean": "City"},
    )
    fig.update_traces(line=dict(width=2.5), marker=dict(size=6))
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(title=""),
        xaxis=dict(
            categoryorder="array",
            categoryarray=[HOUR_LABELS[i] for i in range(24)],
        ),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
        height=300,
    )
    return fig
