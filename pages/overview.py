"""
Overview Page — KPI cards + rating distribution + city selector.

Route: /
"""

import pathlib

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

dash.register_page(__name__, path="/", name="Overview", order=0)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"
df_biz = pd.read_csv(DATA_DIR / "df_businesses.csv", low_memory=False)
df_cuisine = pd.read_csv(DATA_DIR / "df_cuisine_stats.csv")

CITIES = ["Both", "Toronto", "Montreal"]

CITY_COLORS = {"Toronto": "#2c7be5", "Montreal": "#e5522c"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def filter_by_city(df: pd.DataFrame, city: str) -> pd.DataFrame:
    if city == "Both":
        return df
    return df[df["city_clean"] == city]


def top_cuisine(df_c: pd.DataFrame) -> str:
    if df_c.empty:
        return "N/A"
    row = df_c.sort_values("total_reviews", ascending=False).iloc[0]
    return row["cuisine"]


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = html.Div([
    # Filter bar
    html.Div([
        html.Label("City"),
        dcc.Dropdown(
            id="overview-city",
            options=[{"label": c, "value": c} for c in CITIES],
            value="Both",
            clearable=False,
            style={"minWidth": "160px"},
        ),
    ], className="filter-bar"),

    # KPI row
    dbc.Row(id="kpi-row", className="g-3 mb-3"),

    # Charts row
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div("Rating Distribution", className="section-title"),
                dcc.Graph(id="rating-dist-chart", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=6),
        dbc.Col([
            html.Div([
                html.Div("Top 10 Cuisines by Total Reviews", className="section-title"),
                dcc.Graph(id="overview-top-cuisines-chart", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=6),
    ]),

    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div("Open vs Closed Businesses", className="section-title"),
                dcc.Graph(id="open-closed-chart", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=4),
        dbc.Col([
            html.Div([
                html.Div("Reviews vs Stars (sample)", className="section-title"),
                dcc.Graph(id="reviews-stars-chart", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=8),
    ]),
], className="page-content")


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("kpi-row", "children"),
    Input("overview-city", "value"),
)
def update_kpis(city):
    df = filter_by_city(df_biz, city)
    df_c = filter_by_city(df_cuisine, city) if city != "Both" else df_cuisine

    total_biz = len(df)
    avg_stars = df["stars"].mean()
    total_reviews = int(df["review_count"].sum())
    best_cuisine = top_cuisine(df_c)
    pct_open = df["is_open"].mean() * 100

    cards = [
        {
            "label": "Total Businesses",
            "value": f"{total_biz:,}",
            "sub": f"{city if city != 'Both' else 'Toronto + Montreal'}",
            "border": "#2c7be5",
        },
        {
            "label": "Avg Star Rating",
            "value": f"{avg_stars:.2f} ★",
            "sub": "across all businesses",
            "border": "#f6c23e",
        },
        {
            "label": "Total Reviews",
            "value": f"{total_reviews:,}",
            "sub": "cumulative",
            "border": "#1cc88a",
        },
        {
            "label": "Top Cuisine",
            "value": best_cuisine,
            "sub": "by total reviews",
            "border": "#e5522c",
        },
        {
            "label": "Currently Open",
            "value": f"{pct_open:.0f}%",
            "sub": f"{int(df['is_open'].sum()):,} of {total_biz:,}",
            "border": "#36b9cc",
        },
    ]

    return [
        dbc.Col(
            html.Div([
                html.Div(c["label"], className="kpi-label"),
                html.Div(c["value"], className="kpi-value"),
                html.Div(c["sub"], className="kpi-sub"),
            ], className="kpi-card", style={"borderLeftColor": c["border"]}),
            xs=12, sm=6, lg=True,
        )
        for c in cards
    ]


@callback(
    Output("rating-dist-chart", "figure"),
    Input("overview-city", "value"),
)
def update_rating_dist(city):
    df = filter_by_city(df_biz, city)

    if city == "Both":
        fig = px.histogram(
            df, x="stars", color="city_clean",
            barmode="overlay",
            nbins=9,
            color_discrete_map=CITY_COLORS,
            labels={"stars": "Star Rating", "city_clean": "City", "count": "# Businesses"},
            opacity=0.75,
        )
    else:
        fig = px.histogram(
            df, x="stars", nbins=9,
            color_discrete_sequence=[CITY_COLORS.get(city, "#2c7be5")],
            labels={"stars": "Star Rating", "count": "# Businesses"},
        )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(title=""),
        xaxis=dict(dtick=0.5),
        bargap=0.05,
        height=280,
    )
    return fig


@callback(
    Output("overview-top-cuisines-chart", "figure"),
    Input("overview-city", "value"),
)
def update_top_cuisines(city):
    df_c = filter_by_city(df_cuisine, city) if city != "Both" else df_cuisine
    top = (
        df_c.groupby("cuisine", as_index=False)
        .agg(total_reviews=("total_reviews", "sum"))
        .nlargest(10, "total_reviews")
        .sort_values("total_reviews")
    )

    fig = px.bar(
        top, x="total_reviews", y="cuisine",
        orientation="h",
        color="total_reviews",
        color_continuous_scale="Blues",
        labels={"total_reviews": "Total Reviews", "cuisine": ""},
    )
    fig.update_coloraxes(showscale=False)
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        height=280,
        yaxis=dict(tickfont=dict(size=11)),
    )
    return fig


@callback(
    Output("open-closed-chart", "figure"),
    Input("overview-city", "value"),
)
def update_open_closed(city):
    df = filter_by_city(df_biz, city)
    counts = df["is_open"].map({1: "Open", 0: "Closed"}).value_counts().reset_index()
    counts.columns = ["Status", "Count"]

    fig = px.pie(
        counts, names="Status", values="Count",
        color="Status",
        color_discrete_map={"Open": "#1cc88a", "Closed": "#e74a3b"},
        hole=0.45,
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
        height=280,
    )
    return fig


@callback(
    Output("reviews-stars-chart", "figure"),
    Input("overview-city", "value"),
)
def update_reviews_stars(city):
    df = filter_by_city(df_biz, city).copy()
    # Sample for performance
    df_sample = df.sample(min(2000, len(df)), random_state=42)
    df_sample["log_reviews"] = np.log1p(df_sample["review_count"])

    color_col = "city_clean" if city == "Both" else "stars"
    color_map = CITY_COLORS if city == "Both" else None

    fig = px.scatter(
        df_sample,
        x="log_reviews",
        y="stars",
        color=color_col,
        color_discrete_map=color_map,
        color_continuous_scale="Viridis" if city != "Both" else None,
        opacity=0.55,
        hover_data={"name": True, "review_count": True, "log_reviews": False},
        labels={
            "log_reviews": "log(Review Count + 1)",
            "stars": "Star Rating",
            "city_clean": "City",
        },
    )
    fig.update_traces(marker=dict(size=5))
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(title=""),
        height=280,
    )
    return fig
