"""
Top Businesses Page — top 10 restaurants/cafes with cuisine filter.

Route: /top-businesses
"""

import pathlib

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dash_table, dcc, html

dash.register_page(__name__, path="/top-businesses", name="Top Businesses", order=2)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"
df_biz = pd.read_csv(DATA_DIR / "df_businesses.csv", low_memory=False)
df_biz["name"] = df_biz["name"].str.strip('"')
df_biz["address"] = df_biz["address"].str.strip('"')

# Composite score: balances stars with review volume
df_biz["score"] = df_biz["stars"] * np.log1p(df_biz["review_count"])

CITIES = ["Both", "Toronto", "Montreal"]
CITY_COLORS = {"Toronto": "#2c7be5", "Montreal": "#e5522c"}

# Build category filter options from the data
ALL_CATS = (
    df_biz["categories"]
    .dropna()
    .str.split(";")
    .explode()
    .str.strip()
    .value_counts()
    .head(60)
    .index.tolist()
)
# Focus on food-relevant top-level categories for the dropdown
SEGMENT_OPTIONS = [
    {"label": "All Food & Drink", "value": "all"},
    {"label": "Restaurants", "value": "Restaurants"},
    {"label": "Cafes & Coffee", "value": "Cafes"},
    {"label": "Bars & Nightlife", "value": "Bars"},
    {"label": "Bakeries", "value": "Bakeries"},
    {"label": "Fast Food", "value": "Fast Food"},
    {"label": "Breakfast & Brunch", "value": "Breakfast & Brunch"},
]

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = html.Div([
    html.Div([
        html.H2("Top Businesses"),
        html.P("Discover the highest-rated restaurants, cafes, and bars — ranked by a composite score of stars and review volume."),
    ], className="page-header"),

    html.Div([
        html.Label("City"),
        dcc.Dropdown(
            id="top-biz-city",
            options=[{"label": c, "value": c} for c in CITIES],
            value="Both",
            clearable=False,
            style={"minWidth": "160px"},
        ),
        html.Label("Segment", style={"marginLeft": "1rem"}),
        dcc.Dropdown(
            id="top-biz-segment",
            options=SEGMENT_OPTIONS,
            value="Restaurants",
            clearable=False,
            style={"minWidth": "200px"},
        ),
        html.Label("Rank by", style={"marginLeft": "1rem"}),
        dcc.RadioItems(
            id="top-biz-metric",
            options=[
                {"label": "  Composite Score", "value": "score"},
                {"label": "  Avg Stars", "value": "stars"},
                {"label": "  Review Count", "value": "review_count"},
            ],
            value="score",
            inline=True,
            inputStyle={"marginRight": "4px"},
            labelStyle={"marginRight": "16px", "fontSize": "0.88rem"},
        ),
    ], className="filter-bar"),

    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div(id="top-biz-chart-title", className="section-title"),
                dcc.Graph(id="top-biz-chart", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=7),
        dbc.Col([
            html.Div([
                html.Div("Toronto vs Montreal — Head to Head", className="section-title"),
                dcc.Graph(id="top-biz-city-compare", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=5),
    ]),

    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div("Business Details", className="section-title"),
                html.Div(id="top-biz-table-wrapper"),
            ], className="chart-card"),
        ]),
    ]),
], className="page-content")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

METRIC_LABELS = {
    "score": "Composite Score (stars × log reviews)",
    "stars": "Avg Stars",
    "review_count": "Review Count",
}


def filter_data(city: str, segment: str) -> pd.DataFrame:
    df = df_biz.copy()
    if city != "Both":
        df = df[df["city_clean"] == city]
    if segment != "all":
        df = df[df["categories"].fillna("").str.contains(segment, case=False)]
    return df


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("top-biz-chart", "figure"),
    Output("top-biz-chart-title", "children"),
    Input("top-biz-city", "value"),
    Input("top-biz-segment", "value"),
    Input("top-biz-metric", "value"),
)
def update_top_chart(city, segment, metric):
    df = filter_data(city, segment)
    top10 = df.nlargest(10, metric).sort_values(metric)

    label = METRIC_LABELS[metric]
    seg_label = next((o["label"] for o in SEGMENT_OPTIONS if o["value"] == segment), segment)
    title = f"Top 10 {seg_label} — by {label}"

    color_col = "city_clean" if city == "Both" else metric
    color_map = CITY_COLORS if city == "Both" else None

    fig = px.bar(
        top10,
        x=metric,
        y="name",
        orientation="h",
        color=color_col,
        color_discrete_map=color_map,
        color_continuous_scale="Blues" if city != "Both" else None,
        text=metric,
        hover_data={
            "stars": ":.1f",
            "review_count": ":,",
            "score": ":.2f",
            "address": True,
            "city_clean": True,
        },
        labels={metric: label, "name": "", "city_clean": "City"},
    )
    fmt = ":.2f" if metric == "score" else (":.1f" if metric == "stars" else ":,")
    fig.update_traces(texttemplate=f"%{{x{fmt}}}", textposition="outside")
    fig.update_coloraxes(showscale=False)
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=90, t=10, b=10),
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
        yaxis=dict(tickfont=dict(size=11)),
        legend=dict(title=""),
        height=380,
    )
    return fig, title


@callback(
    Output("top-biz-city-compare", "figure"),
    Input("top-biz-segment", "value"),
    Input("top-biz-metric", "value"),
)
def update_city_compare(segment, metric):
    """Box plot comparing distribution of the metric between the two cities."""
    df_t = filter_data("Toronto", segment)
    df_m = filter_data("Montreal", segment)

    fig = go.Figure()
    for city, df_c, color in [
        ("Toronto", df_t, CITY_COLORS["Toronto"]),
        ("Montreal", df_m, CITY_COLORS["Montreal"]),
    ]:
        fig.add_trace(go.Box(
            y=df_c[metric],
            name=city,
            marker_color=color,
            boxmean="sd",
        ))

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(
            title=METRIC_LABELS[metric],
            showgrid=True,
            gridcolor="#f0f0f0",
        ),
        legend=dict(title=""),
        height=380,
    )
    return fig


@callback(
    Output("top-biz-table-wrapper", "children"),
    Input("top-biz-city", "value"),
    Input("top-biz-segment", "value"),
    Input("top-biz-metric", "value"),
)
def update_table(city, segment, metric):
    df = filter_data(city, segment)
    top20 = (
        df.nlargest(20, metric)
        [["name", "city_clean", "stars", "review_count", "score", "address", "neighborhood", "is_open"]]
        .copy()
    )
    top20["score"] = top20["score"].round(2)
    top20["is_open"] = top20["is_open"].map({1: "Yes", 0: "No"})
    top20.columns = ["Name", "City", "Stars", "Reviews", "Score", "Address", "Neighbourhood", "Open"]

    return dash_table.DataTable(
        data=top20.to_dict("records"),
        columns=[{"name": c, "id": c} for c in top20.columns],
        sort_action="native",
        page_size=10,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": "#f4f6f9",
            "fontWeight": "600",
            "fontSize": "0.82rem",
            "border": "none",
            "borderBottom": "2px solid #e0e0e0",
        },
        style_cell={
            "fontFamily": "Inter, Segoe UI, sans-serif",
            "fontSize": "0.83rem",
            "padding": "8px 12px",
            "border": "none",
            "borderBottom": "1px solid #f0f0f0",
            "textAlign": "left",
            "maxWidth": "200px",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#fafbfd"},
            {
                "if": {"filter_query": '{Open} = "Yes"', "column_id": "Open"},
                "color": "#1cc88a",
                "fontWeight": "600",
            },
            {
                "if": {"filter_query": '{Open} = "No"', "column_id": "Open"},
                "color": "#e74a3b",
            },
        ],
    )
