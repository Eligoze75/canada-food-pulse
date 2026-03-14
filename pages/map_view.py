import pathlib
import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dcc, html

dash.register_page(__name__, path="/map", name="Map", order=2)

DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"
df_biz = pd.read_csv(DATA_DIR / "df_businesses.csv", low_memory=False)
df_biz["name"] = df_biz["name"].str.strip('"')
df_biz = df_biz.dropna(subset=["latitude", "longitude"])

CITIES = ["Both", "Toronto", "Montreal"]
CITY_COLORS = {"Toronto": "#2c7be5", "Montreal": "#e5522c"}

CITY_CENTERS = {
    "Toronto": {"lat": 43.6532, "lon": -79.3832, "zoom": 11},
    "Montreal": {"lat": 45.5017, "lon": -73.5673, "zoom": 11},
    "Both": {"lat": 44.57, "lon": -77.3, "zoom": 5},
}

SEGMENT_OPTIONS = [
    {"label": "All Food & Drink", "value": "all"},
    {"label": "Restaurants", "value": "Restaurants"},
    {"label": "Cafes & Coffee", "value": "Cafes"},
    {"label": "Bars", "value": "Bars"},
    {"label": "Fast Food", "value": "Fast Food"},
    {"label": "Bakeries", "value": "Bakeries"},
    {"label": "Breakfast & Brunch", "value": "Breakfast & Brunch"},
]

layout = html.Div(
    [
        html.Div(
            [
                html.H2("Business Map"),
                html.P(
                    "Hotspots of food & drink across Toronto and Montreal — density reflects concentration of businesses."
                ),
            ],
            className="page-header",
        ),
        html.Div(
            [
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
                    value="all",
                    clearable=False,
                    style={"minWidth": "200px"},
                ),
                html.Label("Min Reviews", style={"marginLeft": "1rem"}),
                dcc.Slider(
                    id="map-min-reviews",
                    min=0,
                    max=200,
                    step=10,
                    value=0,
                    marks={0: "0", 50: "50", 100: "100", 200: "200"},
                    tooltip={"placement": "bottom"},
                ),
            ],
            className="filter-bar",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div(id="map-title", className="section-title"),
                                dcc.Graph(
                                    id="main-map",
                                    config={"scrollZoom": True, "displayModeBar": True},
                                ),
                            ],
                            className="chart-card map-container",
                        ),
                    ],
                    md=8,
                ),
                dbc.Col(
                    [
                        html.Div(id="neighbourhood-kpis"),
                    ],
                    md=4,
                ),
            ]
        ),
    ],
    className="page-content",
)


def filter_map_data(city: str, segment: str, min_reviews: int) -> pd.DataFrame:
    df = df_biz.copy()
    if city != "Both":
        df = df[df["city_clean"] == city]
    if segment != "all":
        df = df[df["categories"].fillna("").str.contains(segment, case=False)]
    return df[df["review_count"] >= min_reviews]


def neighbourhood_kpi_cards(df: pd.DataFrame) -> list:
    """Return three stacked chart-cards: best rated, most variety, most places."""
    df_n = df.dropna(subset=["neighborhood"])

    # --- Most places (top 3) ---
    most_places = (
        df_n.groupby("neighborhood").size().nlargest(3).reset_index(name="count")
    )

    # --- Best rated (top 3, min 3 businesses) ---
    best_rated = (
        df_n.groupby("neighborhood")
        .filter(lambda g: len(g) >= 3)
        .groupby("neighborhood")["stars"]
        .mean()
        .nlargest(3)
        .reset_index()
    )
    best_rated["stars"] = best_rated["stars"].round(2)

    # --- Most variety: distinct cuisine tags per neighbourhood ---
    df_exp = df_n.copy()
    df_exp["cuisine"] = df_n["categories"].fillna("").str.split(";")
    df_exp = df_exp.explode("cuisine")
    df_exp["cuisine"] = df_exp["cuisine"].str.strip()
    most_variety = (
        df_exp[df_exp["cuisine"] != ""]
        .groupby("neighborhood")["cuisine"]
        .nunique()
        .nlargest(3)
        .reset_index(name="cuisines")
    )

    medals = ["🥇", "🥈", "🥉"]

    def kpi_card(title: str, rows: list) -> html.Div:
        return html.Div(
            [
                html.Div(title, className="section-title"),
                *[
                    html.Div(
                        [
                            html.Span(
                                f"{medals[i]}  {name}",
                                style={"fontWeight": "600", "fontSize": "0.85rem"},
                            ),
                            html.Span(
                                value,
                                style={
                                    "float": "right",
                                    "color": "#6c757d",
                                    "fontSize": "0.83rem",
                                },
                            ),
                        ],
                        style={"padding": "5px 0", "borderBottom": "1px solid #f0f0f0"},
                    )
                    for i, (name, value) in enumerate(rows)
                ],
            ],
            className="chart-card",
            style={"marginBottom": "1rem"},
        )

    places_rows = [
        (r["neighborhood"], f"{r['count']:,} places") for _, r in most_places.iterrows()
    ]
    rated_rows = [
        (r["neighborhood"], f"{r['stars']:.2f} ★") for _, r in best_rated.iterrows()
    ]
    variety_rows = [
        (r["neighborhood"], f"{r['cuisines']} cuisines")
        for _, r in most_variety.iterrows()
    ]

    return [
        kpi_card("Most Places", places_rows),
        kpi_card("Best Rated", rated_rows),
        kpi_card("Most Variety", variety_rows),
    ]


@callback(
    Output("main-map", "figure"),
    Output("map-title", "children"),
    Input("map-city", "value"),
    Input("map-segment", "value"),
    Input("map-min-reviews", "value"),
)
def update_map(city, segment, min_reviews):
    df = filter_map_data(city, segment, min_reviews)
    center = CITY_CENTERS[city]
    seg_label = next(
        (o["label"] for o in SEGMENT_OPTIONS if o["value"] == segment), segment
    )
    title = f"{seg_label} hotspots — {city} ({len(df):,} locations)"

    fig = px.density_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        z="review_count",
        radius=14,
        zoom=center["zoom"],
        center={"lat": center["lat"], "lon": center["lon"]},
        color_continuous_scale="YlOrRd",
        labels={"z": "Review weight"},
    )
    fig.update_layout(
        mapbox_style="open-street-map",
        margin=dict(l=0, r=0, t=0, b=0),
        height=580,
        coloraxis_colorbar=dict(title="Density", thickness=12, len=0.6),
    )
    return fig, title


@callback(
    Output("neighbourhood-kpis", "children"),
    Input("map-city", "value"),
    Input("map-segment", "value"),
    Input("map-min-reviews", "value"),
)
def update_neighbourhood_kpis(city, segment, min_reviews):
    df = filter_map_data(city, segment, min_reviews)
    return neighbourhood_kpi_cards(df)
