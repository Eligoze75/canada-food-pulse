"""
Map Page — interactive scatter_mapbox of business locations.

Route: /map
"""

import pathlib

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dcc, html

dash.register_page(__name__, path="/map", name="Map", order=4)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"
df_biz = pd.read_csv(DATA_DIR / "df_businesses.csv", low_memory=False)
df_biz["name"] = df_biz["name"].str.strip('"')
df_biz["address"] = df_biz["address"].str.strip('"')
df_biz = df_biz.dropna(subset=["latitude", "longitude"])

# Primary cuisine per business (first food-relevant category)
FOOD_KEYS = {
    "Restaurants", "Cafes", "Coffee & Tea", "Bars", "Bakeries",
    "Fast Food", "Pizza", "Sushi Bars", "Burgers", "Sandwiches",
    "Breakfast & Brunch", "Food", "Nightlife", "Pubs",
}

def primary_cuisine(cats: str) -> str:
    if not isinstance(cats, str):
        return "Other"
    for c in cats.split(";"):
        c = c.strip()
        if c in FOOD_KEYS:
            return c
    parts = cats.split(";")
    return parts[0].strip() if parts else "Other"

df_biz["primary_cuisine"] = df_biz["categories"].apply(primary_cuisine)

CITIES = ["Both", "Toronto", "Montreal"]
CITY_COLORS = {"Toronto": "#2c7be5", "Montreal": "#e5522c"}

# City center coordinates for auto-zoom
CITY_CENTERS = {
    "Toronto": {"lat": 43.6532, "lon": -79.3832, "zoom": 11},
    "Montreal": {"lat": 45.5017, "lon": -73.5673, "zoom": 11},
    "Both": {"lat": 44.5, "lon": -76.5, "zoom": 5},
}

# Segment options
SEGMENT_OPTIONS = [
    {"label": "All Food & Drink", "value": "all"},
    {"label": "Restaurants", "value": "Restaurants"},
    {"label": "Cafes & Coffee", "value": "Cafes"},
    {"label": "Bars", "value": "Bars"},
    {"label": "Fast Food", "value": "Fast Food"},
    {"label": "Bakeries", "value": "Bakeries"},
    {"label": "Breakfast & Brunch", "value": "Breakfast & Brunch"},
]

COLOR_OPTIONS = [
    {"label": "Star Rating", "value": "stars"},
    {"label": "Review Count", "value": "review_count"},
    {"label": "City", "value": "city_clean"},
    {"label": "Open/Closed", "value": "is_open_label"},
]

df_biz["is_open_label"] = df_biz["is_open"].map({1: "Open", 0: "Closed"})

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = html.Div([
    html.Div([
        html.H2("Business Map"),
        html.P("Explore the geographic distribution of restaurants, cafes, and bars across Toronto and Montreal."),
    ], className="page-header"),

    html.Div([
        html.Label("City"),
        dcc.Dropdown(
            id="map-city",
            options=[{"label": c, "value": c} for c in CITIES],
            value="Both",
            clearable=False,
            style={"minWidth": "150px"},
        ),
        html.Label("Segment", style={"marginLeft": "1rem"}),
        dcc.Dropdown(
            id="map-segment",
            options=SEGMENT_OPTIONS,
            value="Restaurants",
            clearable=False,
            style={"minWidth": "200px"},
        ),
        html.Label("Colour by", style={"marginLeft": "1rem"}),
        dcc.Dropdown(
            id="map-color",
            options=COLOR_OPTIONS,
            value="stars",
            clearable=False,
            style={"minWidth": "160px"},
        ),
        html.Label("Min Reviews", style={"marginLeft": "1rem"}),
        dcc.Slider(
            id="map-min-reviews",
            min=0, max=200, step=10, value=10,
            marks={0: "0", 50: "50", 100: "100", 200: "200"},
            tooltip={"placement": "bottom"},
        ),
    ], className="filter-bar"),

    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div(id="map-title", className="section-title"),
                dcc.Graph(id="main-map", config={"scrollZoom": True, "displayModeBar": True}),
            ], className="chart-card map-container"),
        ], md=8),
        dbc.Col([
            html.Div([
                html.Div("Distribution by Star Rating", className="section-title"),
                dcc.Graph(id="map-stars-hist", config={"displayModeBar": False}),
            ], className="chart-card"),
            html.Div([
                html.Div("Top Neighbourhoods", className="section-title"),
                dcc.Graph(id="map-neighbourhood-chart", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=4),
    ]),
], className="page-content")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def filter_map_data(city: str, segment: str, min_reviews: int) -> pd.DataFrame:
    df = df_biz.copy()
    if city != "Both":
        df = df[df["city_clean"] == city]
    if segment != "all":
        df = df[df["categories"].fillna("").str.contains(segment, case=False)]
    df = df[df["review_count"] >= min_reviews]
    return df


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("main-map", "figure"),
    Output("map-title", "children"),
    Input("map-city", "value"),
    Input("map-segment", "value"),
    Input("map-color", "value"),
    Input("map-min-reviews", "value"),
)
def update_map(city, segment, color_col, min_reviews):
    df = filter_map_data(city, segment, min_reviews)

    center = CITY_CENTERS[city]
    seg_label = next((o["label"] for o in SEGMENT_OPTIONS if o["value"] == segment), segment)
    title = f"{seg_label} in {city} ({len(df):,} locations)"

    is_discrete = color_col in ("city_clean", "is_open_label")

    if is_discrete:
        color_map = (
            CITY_COLORS if color_col == "city_clean"
            else {"Open": "#1cc88a", "Closed": "#e74a3b"}
        )
        fig = px.scatter_mapbox(
            df,
            lat="latitude", lon="longitude",
            color=color_col,
            color_discrete_map=color_map,
            hover_name="name",
            hover_data={
                "stars": ":.1f",
                "review_count": ":,",
                "address": True,
                "primary_cuisine": True,
                "latitude": False,
                "longitude": False,
            },
            zoom=center["zoom"],
            center={"lat": center["lat"], "lon": center["lon"]},
            opacity=0.7,
            size_max=8,
        )
    else:
        fig = px.scatter_mapbox(
            df,
            lat="latitude", lon="longitude",
            color=color_col,
            color_continuous_scale="RdYlGn" if color_col == "stars" else "Blues",
            range_color=(1, 5) if color_col == "stars" else None,
            size="review_count",
            size_max=18,
            hover_name="name",
            hover_data={
                "stars": ":.1f",
                "review_count": ":,",
                "address": True,
                "primary_cuisine": True,
                "latitude": False,
                "longitude": False,
            },
            zoom=center["zoom"],
            center={"lat": center["lat"], "lon": center["lon"]},
            opacity=0.75,
            labels={
                "stars": "Stars",
                "review_count": "Reviews",
                "city_clean": "City",
                "is_open_label": "Status",
            },
        )

    fig.update_layout(
        mapbox_style="open-street-map",
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(title=""),
        height=580,
        coloraxis_colorbar=dict(thickness=12, title=""),
    )
    return fig, title


@callback(
    Output("map-stars-hist", "figure"),
    Input("map-city", "value"),
    Input("map-segment", "value"),
    Input("map-min-reviews", "value"),
)
def update_stars_hist(city, segment, min_reviews):
    df = filter_map_data(city, segment, min_reviews)

    if city == "Both":
        fig = px.histogram(
            df, x="stars", color="city_clean",
            barmode="overlay",
            nbins=9,
            color_discrete_map=CITY_COLORS,
            labels={"stars": "Stars", "city_clean": "City"},
            opacity=0.75,
        )
    else:
        color = CITY_COLORS.get(city, "#2c7be5")
        fig = px.histogram(
            df, x="stars", nbins=9,
            color_discrete_sequence=[color],
            labels={"stars": "Stars"},
        )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=5, b=10),
        legend=dict(title=""),
        bargap=0.05,
        height=200,
        showlegend=city == "Both",
        xaxis=dict(dtick=0.5),
    )
    return fig


@callback(
    Output("map-neighbourhood-chart", "figure"),
    Input("map-city", "value"),
    Input("map-segment", "value"),
    Input("map-min-reviews", "value"),
)
def update_neighbourhood(city, segment, min_reviews):
    df = filter_map_data(city, segment, min_reviews)
    df_n = df.dropna(subset=["neighborhood"])

    top = (
        df_n.groupby(["city_clean", "neighborhood"])
        .size()
        .reset_index(name="count")
        .nlargest(12, "count")
        .sort_values("count")
    )

    color_col = "city_clean" if city == "Both" else "count"
    color_map = CITY_COLORS if city == "Both" else None

    fig = px.bar(
        top, x="count", y="neighborhood",
        orientation="h",
        color=color_col,
        color_discrete_map=color_map,
        color_continuous_scale="Blues" if city != "Both" else None,
        labels={"count": "Businesses", "neighborhood": "", "city_clean": "City"},
    )
    fig.update_coloraxes(showscale=False)
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=5, b=10),
        legend=dict(title="", orientation="h", y=1.05),
        yaxis=dict(tickfont=dict(size=10)),
        height=260,
    )
    return fig
