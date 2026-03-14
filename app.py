import dash
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

server = app.server  # required for Plotly Cloud deployment

# ---------------------------------------------------------------------------
# Navbar
# ---------------------------------------------------------------------------

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Overview", href="/")),
        dbc.NavItem(dbc.NavLink("Peak Hours", href="/peak-hours")),
        dbc.NavItem(dbc.NavLink("Map", href="/map")),
    ],
    brand=html.Span(
        [
            html.Img(
                src="/assets/canada_leaf.png",
                height="30px",
                style={
                    "marginRight": "8px",
                    "borderRadius": "50%",
                    "background": "white",
                    "padding": "3px",
                },
            ),
            "Canada Food Pulse",
        ]
    ),
    brand_href="/",
    color="primary",
    dark=True,
    className="mb-0 shadow-sm cfp-navbar",
    fluid=True,
)

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

app.layout = html.Div(
    [
        navbar,
        # Global city filter — shared across all pages via dcc.Store
        dcc.Store(id="city-store", storage_type="session", data="Both"),
        # Page content rendered here by Dash Pages
        dash.page_container,
    ],
    className="app-wrapper",
)


if __name__ == "__main__":
    app.run(debug=True)
