"""
Top Cuisines Page — horizontal bar chart ranked by reviews or avg stars.

Route: /cuisines
"""

import pathlib

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dcc, html

dash.register_page(__name__, path="/cuisines", name="Top Cuisines", order=1)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"
df_cuisine = pd.read_csv(DATA_DIR / "df_cuisine_stats.csv")

CITIES = ["Both", "Toronto", "Montreal"]
CITY_COLORS = {"Toronto": "#2c7be5", "Montreal": "#e5522c"}

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = html.Div([
    # Page header
    html.Div([
        html.H2("Top Cuisines"),
        html.P("Explore the most popular and highest-rated food categories across Canadian cities."),
    ], className="page-header"),

    # Filter bar
    html.Div([
        html.Label("City"),
        dcc.Dropdown(
            id="cuisines-city",
            options=[{"label": c, "value": c} for c in CITIES],
            value="Both",
            clearable=False,
            style={"minWidth": "160px"},
        ),
        html.Label("Rank by", style={"marginLeft": "1rem"}),
        dcc.RadioItems(
            id="cuisines-metric",
            options=[
                {"label": "  Total Reviews", "value": "total_reviews"},
                {"label": "  Avg Stars", "value": "avg_stars"},
                {"label": "  Business Count", "value": "business_count"},
            ],
            value="total_reviews",
            inline=True,
            inputStyle={"marginRight": "4px"},
            labelStyle={"marginRight": "16px", "fontSize": "0.88rem"},
        ),
        html.Label("Top N", style={"marginLeft": "1rem"}),
        dcc.Slider(
            id="cuisines-topn",
            min=5, max=30, step=5, value=15,
            marks={5: "5", 10: "10", 15: "15", 20: "20", 25: "25", 30: "30"},
            tooltip={"placement": "bottom"},
            className="ms-2",
        ),
    ], className="filter-bar"),

    # Main chart + comparison side-by-side
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div(id="main-cuisine-title", className="section-title"),
                dcc.Graph(id="cuisines-main-chart", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=8),
        dbc.Col([
            html.Div([
                html.Div("Toronto vs Montreal", className="section-title"),
                dcc.Graph(id="cuisines-compare-chart", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=4),
    ]),

    # Scatter: business count vs avg stars, sized by total reviews
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div("Cuisine Landscape: Volume vs Quality", className="section-title"),
                dcc.Graph(id="cuisines-bubble-chart", config={"displayModeBar": False}),
            ], className="chart-card"),
        ]),
    ]),
], className="page-content")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

METRIC_LABELS = {
    "total_reviews": "Total Reviews",
    "avg_stars": "Avg Star Rating",
    "business_count": "Number of Businesses",
}


def aggregate(city: str) -> pd.DataFrame:
    if city == "Both":
        return (
            df_cuisine
            .groupby("cuisine", as_index=False)
            .agg(
                avg_stars=("avg_stars", "mean"),
                total_reviews=("total_reviews", "sum"),
                business_count=("business_count", "sum"),
            )
            .round({"avg_stars": 2})
        )
    return df_cuisine[df_cuisine["city_clean"] == city].copy()


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("cuisines-main-chart", "figure"),
    Output("main-cuisine-title", "children"),
    Input("cuisines-city", "value"),
    Input("cuisines-metric", "value"),
    Input("cuisines-topn", "value"),
)
def update_main_chart(city, metric, top_n):
    df = aggregate(city)
    top = df.nlargest(top_n, metric).sort_values(metric)

    label = METRIC_LABELS[metric]
    title = f"Top {top_n} Cuisines by {label}"

    color = CITY_COLORS.get(city, "#2c7be5") if city != "Both" else "#2c7be5"

    fig = px.bar(
        top, x=metric, y="cuisine",
        orientation="h",
        color=metric,
        color_continuous_scale=["#d0e8ff", color],
        text=metric,
        labels={metric: label, "cuisine": ""},
        hover_data={"avg_stars": ":.2f", "total_reviews": ":,", "business_count": True},
    )
    fig.update_traces(
        texttemplate="%{x:,.0f}" if metric != "avg_stars" else "%{x:.2f}",
        textposition="outside",
    )
    fig.update_coloraxes(showscale=False)
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=80, t=10, b=10),
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
        yaxis=dict(tickfont=dict(size=11)),
        height=max(300, top_n * 28),
    )
    return fig, title


@callback(
    Output("cuisines-compare-chart", "figure"),
    Input("cuisines-metric", "value"),
    Input("cuisines-topn", "value"),
)
def update_compare_chart(metric, top_n):
    # Find the top N cuisines globally, then compare per city
    global_top = (
        df_cuisine.groupby("cuisine")[metric].sum()
        .nlargest(min(top_n, 15))
        .index.tolist()
    )

    df_filtered = df_cuisine[df_cuisine["cuisine"].isin(global_top)]

    fig = px.bar(
        df_filtered.sort_values(metric, ascending=True),
        x=metric, y="cuisine", color="city_clean",
        orientation="h",
        barmode="group",
        color_discrete_map=CITY_COLORS,
        labels={metric: METRIC_LABELS[metric], "cuisine": "", "city_clean": "City"},
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(title="", orientation="h", y=1.02, x=0),
        yaxis=dict(tickfont=dict(size=10)),
        height=max(300, min(top_n, 15) * 38),
    )
    return fig


@callback(
    Output("cuisines-bubble-chart", "figure"),
    Input("cuisines-city", "value"),
    Input("cuisines-topn", "value"),
)
def update_bubble(city, top_n):
    df = aggregate(city)
    top = df.nlargest(top_n, "total_reviews")

    color_col = "city_clean" if city == "Both" else "avg_stars"
    color_map = CITY_COLORS if city == "Both" else None

    fig = px.scatter(
        top,
        x="business_count",
        y="avg_stars",
        size="total_reviews",
        color=color_col,
        color_discrete_map=color_map,
        color_continuous_scale="Blues" if city != "Both" else None,
        text="cuisine",
        labels={
            "business_count": "Number of Businesses",
            "avg_stars": "Avg Star Rating",
            "total_reviews": "Total Reviews",
            "city_clean": "City",
        },
        hover_data={"total_reviews": ":,", "business_count": True, "avg_stars": ":.2f"},
        size_max=60,
    )
    fig.update_traces(textposition="top center", textfont=dict(size=10))
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(title=""),
        height=420,
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0", range=[2.5, 5.2]),
    )
    return fig
