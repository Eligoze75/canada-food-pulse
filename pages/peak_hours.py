"""
Peak Hours Page — weekday × hour heatmap + busiest day bar chart.

Route: /peak-hours
"""

import pathlib

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Input, Output, callback, dcc, html

dash.register_page(__name__, path="/peak-hours", name="Peak Hours", order=1)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"

# Load only the columns needed for peak analysis (104k rows, 5 cols — fast)
df_src = pd.read_csv(
    DATA_DIR / "yelp_business_data_cleaned.csv",
    usecols=["categories", "city_clean", "weekday", "peak_hour", "total_checkins"],
    low_memory=False,
)
df_src = df_src.dropna(subset=["weekday", "peak_hour"])

WEEKDAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CITIES = ["Both", "Toronto", "Montreal"]
CITY_COLORS = {"Toronto": "#2c7be5", "Montreal": "#e5522c"}

SEGMENT_OPTIONS = [
    {"label": "All Food & Drink",   "value": "all"},
    {"label": "Restaurants",        "value": "Restaurants"},
    {"label": "Cafes & Coffee",     "value": "Cafes"},
    {"label": "Bars",               "value": "Bars"},
    {"label": "Fast Food",          "value": "Fast Food"},
    {"label": "Bakeries",           "value": "Bakeries"},
    {"label": "Breakfast & Brunch", "value": "Breakfast & Brunch"},
]


def hour_to_int(h: str) -> int:
    try:
        return int(str(h).split(":")[0])
    except Exception:
        return -1


def fmt_hour(h: int) -> str:
    if h == 0:      return "12am"
    elif h < 12:    return f"{h}am"
    elif h == 12:   return "12pm"
    else:           return f"{h - 12}pm"


HOUR_LABELS = {i: fmt_hour(i) for i in range(24)}

df_src["hour_int"] = df_src["peak_hour"].apply(hour_to_int)

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = html.Div([
    html.Div([
        html.H2("Peak Hours"),
        html.P("City-wide traffic patterns — when are restaurants and cafes busiest?"),
    ], className="page-header"),

    html.Div([
        html.Label("City"),
        dcc.Dropdown(
            id="peaks-city",
            options=[{"label": c, "value": c} for c in CITIES],
            value="Both",
            clearable=False,
            style={"minWidth": "160px"},
        ),
        html.Label("Segment", style={"marginLeft": "1rem"}),
        dcc.Dropdown(
            id="peaks-segment",
            options=SEGMENT_OPTIONS,
            value="all",
            clearable=False,
            style={"minWidth": "200px"},
        ),
    ], className="filter-bar"),

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
], className="page-content")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def filter_src(city: str, segment: str) -> pd.DataFrame:
    df = df_src
    if city != "Both":
        df = df[df["city_clean"] == city]
    if segment != "all":
        df = df[df["categories"].fillna("").str.contains(segment, case=False)]
    return df


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("peaks-heatmap", "figure"),
    Output("peaks-heatmap-title", "children"),
    Input("peaks-city", "value"),
    Input("peaks-segment", "value"),
)
def update_heatmap(city, segment):
    df = filter_src(city, segment)

    pivot = (
        df.groupby(["weekday", "hour_int"])["total_checkins"]
        .sum()
        .unstack(fill_value=0)
        .reindex(WEEKDAY_ORDER)
    )
    hour_cols = sorted(pivot.columns)
    pivot = pivot[hour_cols]
    pivot.columns = [HOUR_LABELS.get(c, str(c)) for c in pivot.columns]

    seg_label = next((o["label"] for o in SEGMENT_OPTIONS if o["value"] == segment), segment)
    title = f"Traffic by Hour & Weekday — {city}"
    if segment != "all":
        title += f" · {seg_label}"

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="YlOrRd",
        hoverongaps=False,
        hovertemplate="<b>%{y} %{x}</b><br>Check-ins: %{z:,}<extra></extra>",
        colorbar=dict(title="Check-ins", thickness=14, len=0.8),
    ))
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title="Hour of Day", tickangle=-45, tickfont=dict(size=10)),
        yaxis=dict(title="", tickfont=dict(size=11)),
        height=340,
    )
    return fig, title


@callback(
    Output("peaks-by-day", "figure"),
    Input("peaks-city", "value"),
    Input("peaks-segment", "value"),
)
def update_by_day(city, segment):
    df = filter_src(city, segment)

    daily = (
        df.groupby("weekday")["total_checkins"]
        .sum()
        .reindex(WEEKDAY_ORDER)
        .reset_index()
    )
    color = CITY_COLORS.get(city, "#2c7be5") if city != "Both" else "#D52B1E"

    fig = px.bar(
        daily, x="weekday", y="total_checkins",
        color="total_checkins",
        color_continuous_scale=["#fdd5d2", color],
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
        margin=dict(l=10, r=10, t=10, b=30),
        xaxis=dict(categoryorder="array", categoryarray=WEEKDAY_ORDER),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0", title=""),
        height=340,
    )
    return fig
