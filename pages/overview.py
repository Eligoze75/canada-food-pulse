import pathlib
import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dcc, html

dash.register_page(__name__, path="/", name="Overview", order=0)
DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"
df_biz = pd.read_csv(DATA_DIR / "df_businesses.csv", low_memory=False)

CITIES = ["Both", "Toronto", "Montreal"]
CITY_COLORS = {"Toronto": "#2c7be5", "Montreal": "#e5522c"}

SEGMENT_OPTIONS = [
    {"label": "All Food & Drink", "value": "all"},
    {"label": "Restaurants", "value": "Restaurants"},
    {"label": "Cafes & Coffee", "value": "Cafes"},
    {"label": "Bars", "value": "Bars"},
    {"label": "Fast Food", "value": "Fast Food"},
    {"label": "Bakeries", "value": "Bakeries"},
    {"label": "Breakfast & Brunch", "value": "Breakfast & Brunch"},
]

METRIC_OPTIONS = [
    {"label": "  Popularity", "value": "total_reviews"},
    {"label": "  Rating", "value": "avg_stars"},
    {"label": "  Number of Businesses", "value": "business_count"},
]

METRIC_LABELS = {
    "total_reviews": "Popularity (Total Reviews)",
    "avg_stars": "Rating (Avg Stars)",
    "business_count": "Number of Businesses",
}

CUISINE_CATEGORIES = {
    "Italian",
    "Chinese",
    "Mexican",
    "Japanese",
    "Thai",
    "Indian",
    "French",
    "Greek",
    "Mediterranean",
    "Vietnamese",
    "Korean",
    "American (Traditional)",
    "American (New)",
    "Middle Eastern",
    "Lebanese",
    "African",
    "Caribbean",
    "Latin American",
    "Spanish",
    "Pakistani",
    "Sri Lankan",
    "Filipino",
    "Himalayan/Nepalese",
    "Persian/Iranian",
    "Turkish",
    "Ethiopian",
    "Taiwanese",
    "Cantonese",
    "Szechuan",
    "Hong Kong Style Cafe",
    "Seafood",
    "Steakhouses",
    "Sushi Bars",
    "Burgers",
    "Sandwiches",
    "Pizza",
    "Bakeries",
    "Breakfast & Brunch",
    "Diners",
    "Delis",
    "Tapas Bars",
    "Tapas/Small Plates",
    "Noodles",
    "Ramen",
    "Hot Pot",
    "Dim Sum",
    "Chicken Wings",
    "Barbeque",
    "Soup",
    "Waffles",
    "Poutineries",
    "Creperies",
    "Fondue",
    "Soul Food",
    "Comfort Food",
}


def filter_biz(city: str, segment: str) -> pd.DataFrame:
    df = df_biz
    if city != "Both":
        df = df[df["city_clean"] == city]
    if segment != "all":
        df = df[df["categories"].fillna("").str.contains(segment, case=False)]
    return df


def compute_cuisine_stats(city: str, segment: str) -> pd.DataFrame:
    df = filter_biz(city, segment)
    df_exp = df[["business_id", "stars", "review_count", "categories"]].copy()
    df_exp["cuisine"] = df_exp["categories"].str.split(";")
    df_exp = df_exp.explode("cuisine")
    df_exp["cuisine"] = df_exp["cuisine"].str.strip()
    df_exp = df_exp[df_exp["cuisine"].isin(CUISINE_CATEGORIES)]
    if df_exp.empty:
        return pd.DataFrame(
            columns=["cuisine", "avg_stars", "total_reviews", "business_count"]
        )
    return (
        df_exp.groupby("cuisine", as_index=False)
        .agg(
            avg_stars=("stars", "mean"),
            total_reviews=("review_count", "sum"),
            business_count=("business_id", "nunique"),
        )
        .round({"avg_stars": 2})
    )


layout = html.Div(
    [
        html.Div(
            [
                html.Label("City"),
                dcc.Dropdown(
                    id="overview-city",
                    options=[{"label": c, "value": c} for c in CITIES],
                    value="Both",
                    clearable=False,
                    style={"minWidth": "160px"},
                ),
                html.Label("Segment", style={"marginLeft": "1rem"}),
                dcc.Dropdown(
                    id="overview-segment",
                    options=SEGMENT_OPTIONS,
                    value="all",
                    clearable=False,
                    style={"minWidth": "200px"},
                ),
            ],
            className="filter-bar",
        ),
        dbc.Row(id="kpi-row", className="g-3 mb-3"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div(
                                    "Rating Distribution", className="section-title"
                                ),
                                dcc.Graph(
                                    id="rating-dist-chart",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="chart-card",
                        ),
                    ],
                    md=5,
                ),
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Span(
                                            id="cuisine-chart-title",
                                            className="section-title",
                                            style={
                                                "display": "inline-block",
                                                "marginBottom": 0,
                                            },
                                        ),
                                        dcc.RadioItems(
                                            id="cuisine-metric",
                                            options=METRIC_OPTIONS,
                                            value="total_reviews",
                                            inline=True,
                                            inputStyle={"marginRight": "4px"},
                                            labelStyle={
                                                "marginRight": "14px",
                                                "fontSize": "0.82rem",
                                                "cursor": "pointer",
                                            },
                                            style={
                                                "display": "inline-block",
                                                "marginLeft": "auto",
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "space-between",
                                        "marginBottom": "0.75rem",
                                        "borderBottom": "1px solid #eaf0f9",
                                        "paddingBottom": "0.5rem",
                                    },
                                ),
                                dcc.Graph(
                                    id="top-cuisines-chart",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="chart-card",
                        ),
                    ],
                    md=7,
                ),
            ],
            className="mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div(
                                    "Cuisine Landscape: Volume vs Quality",
                                    className="section-title",
                                ),
                                dcc.Graph(
                                    id="cuisine-bubble-chart",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="chart-card",
                        ),
                    ]
                ),
            ]
        ),
    ],
    className="page-content",
)


@callback(
    Output("kpi-row", "children"),
    Input("overview-city", "value"),
    Input("overview-segment", "value"),
)
def update_kpis(city, segment):
    df = filter_biz(city, segment)
    df_c = compute_cuisine_stats(city, segment)

    total_biz = len(df)
    avg_stars = df["stars"].mean() if total_biz > 0 else 0

    top_cuisine = (
        df_c.sort_values("total_reviews", ascending=False).iloc[0]["cuisine"]
        if not df_c.empty
        else "N/A"
    )
    df_rated = df_c[df_c["business_count"] >= 3]
    if not df_rated.empty:
        row = df_rated.sort_values("avg_stars", ascending=False).iloc[0]
        rated_cuisine, rated_stars = row["cuisine"], f"{row['avg_stars']:.2f} ★ avg"
    else:
        rated_cuisine, rated_stars = "N/A", ""

    cards = [
        {
            "label": "Total Businesses",
            "value": f"{total_biz:,}",
            "sub": city if city != "Both" else "Toronto + Montreal",
            "border": "#2c7be5",
        },
        {
            "label": "Avg Star Rating",
            "value": f"{avg_stars:.2f} ★",
            "sub": "across filtered businesses",
            "border": "#f6c23e",
        },
        {
            "label": "Most Popular Cuisine",
            "value": top_cuisine,
            "sub": "by total reviews",
            "border": "#1cc88a",
        },
        {
            "label": "Best Rated Cuisine",
            "value": rated_cuisine,
            "sub": rated_stars,
            "border": "#D52B1E",
        },
    ]

    return [
        dbc.Col(
            html.Div(
                [
                    html.Div(c["label"], className="kpi-label"),
                    html.Div(c["value"], className="kpi-value"),
                    html.Div(c["sub"], className="kpi-sub"),
                ],
                className="kpi-card",
                style={"borderLeftColor": c["border"]},
            ),
            xs=12,
            sm=6,
            lg=True,
        )
        for c in cards
    ]


@callback(
    Output("rating-dist-chart", "figure"),
    Input("overview-city", "value"),
    Input("overview-segment", "value"),
)
def update_rating_dist(city, segment):
    df = filter_biz(city, segment)

    if city == "Both":
        fig = px.histogram(
            df,
            x="stars",
            color="city_clean",
            barmode="overlay",
            nbins=9,
            color_discrete_map=CITY_COLORS,
            labels={
                "stars": "Star Rating",
                "city_clean": "City",
                "count": "# Businesses",
            },
            opacity=0.75,
        )
    else:
        fig = px.histogram(
            df,
            x="stars",
            nbins=9,
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
        height=300,
    )
    return fig


@callback(
    Output("top-cuisines-chart", "figure"),
    Output("cuisine-chart-title", "children"),
    Input("overview-city", "value"),
    Input("overview-segment", "value"),
    Input("cuisine-metric", "value"),
)
def update_top_cuisines(city, segment, metric):
    df_c = compute_cuisine_stats(city, segment)
    top10 = df_c.nlargest(10, metric).sort_values(metric)

    label = METRIC_LABELS[metric]
    title = f"Top 10 Cuisines by {label}"
    color = CITY_COLORS.get(city, "#2c7be5") if city != "Both" else "#2c7be5"
    fmt = "%{x:,.0f}" if metric != "avg_stars" else "%{x:.2f}"

    fig = px.bar(
        top10,
        x=metric,
        y="cuisine",
        orientation="h",
        color=metric,
        color_continuous_scale=["#d0e8ff", color],
        text=metric,
        labels={metric: label, "cuisine": ""},
        hover_data={"avg_stars": ":.2f", "total_reviews": ":,", "business_count": True},
    )
    fig.update_traces(texttemplate=fmt, textposition="outside")
    fig.update_coloraxes(showscale=False)
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=80, t=10, b=10),
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
        yaxis=dict(tickfont=dict(size=11)),
        height=300,
    )
    return fig, title


@callback(
    Output("cuisine-bubble-chart", "figure"),
    Input("overview-city", "value"),
    Input("overview-segment", "value"),
    Input("cuisine-metric", "value"),
)
def update_cuisine_bubble(city, segment, metric):
    df_c = compute_cuisine_stats(city, segment)
    top = df_c.nlargest(20, "total_reviews")

    fig = px.scatter(
        top,
        x="business_count",
        y="avg_stars",
        size="total_reviews",
        color="avg_stars",
        color_continuous_scale="RdYlGn",
        range_color=(3.0, 4.5),
        text="cuisine",
        size_max=55,
        labels={
            "business_count": "Number of Businesses",
            "avg_stars": "Avg Star Rating",
            "total_reviews": "Total Reviews",
        },
        hover_data={"total_reviews": ":,", "business_count": True, "avg_stars": ":.2f"},
    )
    fig.update_traces(
        textposition="top center",
        textfont=dict(size=9),
        marker=dict(opacity=0.75, line=dict(width=0.5, color="white")),
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_colorbar=dict(title="Avg ★", thickness=12, len=0.7),
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0", range=[2.8, 5.2]),
        height=380,
    )
    return fig
