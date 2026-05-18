import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context

# =========================
# VISUAL SYSTEM
# =========================

COLORS = {
    "ink": "#181716",
    "muted": "#6f6b64",
    "quiet": "#918b82",
    "line": "#ded8ce",
    "paper": "#f7f5f0",
    "surface": "#fffdfa",
    "accent": "#176b5c",
    "accent_dark": "#104d43",
    "accent_soft": "#e8f0ed",
}

FONT_STACK = 'Inter, "Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'

SMALL_COUNTRY_COORDS = {
    "AND": {"lat": 42.5063, "lon": 1.5218},
    "BHR": {"lat": 26.0667, "lon": 50.5577},
    "LIE": {"lat": 47.1660, "lon": 9.5554},
    "MCO": {"lat": 43.7384, "lon": 7.4246},
    "MLT": {"lat": 35.9375, "lon": 14.3754},
    "MDV": {"lat": 3.2028, "lon": 73.2207},
    "SMR": {"lat": 43.9424, "lon": 12.4578},
    "SGP": {"lat": 1.3521, "lon": 103.8198},
}


def fill_small_country_coords(frame):
    frame = frame.copy()
    for code, coords in SMALL_COUNTRY_COORDS.items():
        mask = frame["Country Code"].eq(code)
        frame.loc[mask & frame["lat"].isna(), "lat"] = coords["lat"]
        frame.loc[mask & frame["lon"].isna(), "lon"] = coords["lon"]
    return frame

APP_STYLE = {
    "fontFamily": FONT_STACK,
    "margin": "0",
    "padding": "0",
    "backgroundColor": COLORS["paper"],
    "color": COLORS["ink"],
}

SHELL_STYLE = {
    "display": "flex",
    "height": "100vh",
    "backgroundColor": COLORS["paper"],
}

SIDEBAR_STYLE = {
    "width": "340px",
    "padding": "22px",
    "borderRight": f'1px solid {COLORS["line"]}',
    "boxSizing": "border-box",
    "overflowY": "auto",
    "backgroundColor": COLORS["surface"],
}

MAIN_STYLE = {
    "flex": "1",
    "padding": "14px 22px",
    "boxSizing": "border-box",
    "backgroundColor": COLORS["paper"],
}

LABEL_STYLE = {
    "fontWeight": "800",
    "fontSize": "13px",
    "letterSpacing": "0.08em",
    "textTransform": "uppercase",
    "color": COLORS["accent_dark"],
}

BUTTON_STYLE = {
    "width": "100%",
    "padding": "11px 14px",
    "border": f'1px solid {COLORS["line"]}',
    "borderRadius": "999px",
    "backgroundColor": COLORS["accent_dark"],
    "color": "#fffdfa",
    "fontSize": "14px",
    "fontWeight": "800",
    "cursor": "pointer",
}

INFO_BOX_STYLE = {
    "fontSize": "14px",
    "fontWeight": "700",
    "lineHeight": "1.45",
    "marginTop": "18px",
    "marginBottom": "18px",
    "padding": "12px 14px",
    "backgroundColor": COLORS["accent_soft"],
    "borderRadius": "14px",
    "border": f'1px solid {COLORS["line"]}',
    "color": COLORS["accent_dark"],
}

TITLE_STYLE = {
    "textAlign": "center",
    "margin": "8px 0 4px 0",
    "fontSize": "clamp(22px, 3vw, 32px)",
    "fontWeight": "800",
    "letterSpacing": "0",
    "color": COLORS["ink"],
}

SUBTITLE_STYLE = {
    "textAlign": "center",
    "fontSize": "14px",
    "color": COLORS["muted"],
    "marginBottom": "8px",
}

SOURCE_STYLE = {
    "textAlign": "center",
    "fontSize": "12px",
    "color": COLORS["quiet"],
    "marginTop": "-8px",
    "marginBottom": "8px",
    "fontWeight": "600",
}

DASH_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
body {{
  margin: 0;
  background: {COLORS['paper']};
  color: {COLORS['ink']};
  font-family: {FONT_STACK};
}}
.dash-tabs .tab {{
  background: {COLORS['paper']} !important;
  border-color: {COLORS['line']} !important;
  color: {COLORS['muted']} !important;
  font-weight: 700;
}}
.dash-tabs .tab--selected {{
  background: {COLORS['surface']} !important;
  border-top: 3px solid {COLORS['accent']} !important;
  color: {COLORS['ink']} !important;
}}
.Select-control, .Select-menu-outer {{
  border-color: {COLORS['line']} !important;
  border-radius: 12px !important;
}}
.rc-slider-track {{ background-color: {COLORS['accent']} !important; }}
.rc-slider-handle {{
  border-color: {COLORS['accent']} !important;
  background-color: {COLORS['surface']} !important;
}}
@media (max-width: 760px) {{
  .dashboard-shell {{
    display: block !important;
    height: auto !important;
    min-height: 100vh;
  }}
  .dashboard-sidebar {{
    width: 100% !important;
    border-right: 0 !important;
    border-bottom: 1px solid {COLORS['line']} !important;
  }}
  .dashboard-main {{
    padding: 12px !important;
  }}
  .dashboard-graph {{
    height: 68vh !important;
    min-height: 520px;
  }}
}}
"""

# =========================
# LOAD DATA
# =========================

file_path = "P_Data_Extract_From_World_Development_Indicators.xlsx"

infant_data = pd.read_excel(file_path, sheet_name="Data", engine="openpyxl")

infant_indicators = {
    "Total": "SP.DYN.IMRT.IN",
    "Male": "SP.DYN.IMRT.MA.IN",
    "Female": "SP.DYN.IMRT.FE.IN"
}

infant_year_cols = [col for col in infant_data.columns if "[YR" in col]

infant_all_data = []

for name, code in infant_indicators.items():
    temp = infant_data[infant_data["Series Code"] == code].copy()
    temp = temp[["Country Name", "Country Code"] + infant_year_cols]

    temp = temp.melt(
        id_vars=["Country Name", "Country Code"],
        value_vars=infant_year_cols,
        var_name="year",
        value_name="infant_mortality"
    )

    temp["year"] = temp["year"].str.extract(r"(\d{4})").astype(int)

    temp["infant_mortality"] = pd.to_numeric(
        temp["infant_mortality"].replace("..", pd.NA),
        errors="coerce"
    )

    temp = temp.dropna(subset=["infant_mortality"])

    temp["indicator"] = name
    temp["color_value"] = temp["infant_mortality"].clip(upper=150)
    temp["display_rate"] = temp["infant_mortality"].round(1)

    infant_all_data.append(temp)

infant_df = pd.concat(infant_all_data, ignore_index=True)
infant_df = infant_df[(infant_df["year"] >= 1960) & (infant_df["year"] <= 2024)].copy()

# =========================
# COUNTRY CENTROIDS
# =========================

infant_world_url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
infant_world = gpd.read_file(infant_world_url)

infant_world["centroid"] = infant_world.geometry.representative_point()
infant_world["lon"] = infant_world["centroid"].x
infant_world["lat"] = infant_world["centroid"].y

infant_centroids = infant_world[["ADM0_A3", "lat", "lon"]].rename(
    columns={"ADM0_A3": "Country Code"}
)

infant_df = infant_df.merge(infant_centroids, on="Country Code", how="left")
infant_df = fill_small_country_coords(infant_df)

infant_country_lookup = (
    infant_df[infant_df["lat"].notna()][["Country Name", "Country Code"]]
    .dropna()
    .drop_duplicates()
    .sort_values("Country Name")
)

infant_country_options = [
    {
        "label": f"{row['Country Name']} ({row['Country Code']})",
        "value": row["Country Name"],
        "search": f"{row['Country Name']} {row['Country Code']}"
    }
    for _, row in infant_country_lookup.iterrows()
]

infant_country_list_text = ", ".join(
    f"{row['Country Name']} ({row['Country Code']})"
    for _, row in infant_country_lookup.iterrows()
)

# =========================
# COLOR SCALE
# =========================

infant_color_scale = [
    [0.0, "#f4efe6"],
    [0.18, "#d9e7df"],
    [0.36, "#9ec9bb"],
    [0.56, "#4f9d8a"],
    [0.74, "#176b5c"],
    [0.9, "#8f4f43"],
    [1.0, "#5f2f2a"]
]

# =========================
# LOAD DATA
# =========================

file_path = "P_Data_Extract_From_World_Development_Indicators.xlsx"

transition_data = pd.read_excel(file_path, sheet_name="Data", engine="openpyxl")

transition_codes = {
    "total_mortality": "SP.DYN.IMRT.IN",
    "male_mortality": "SP.DYN.IMRT.MA.IN",
    "female_mortality": "SP.DYN.IMRT.FE.IN"
}

transition_year_cols = [col for col in transition_data.columns if "[YR" in col]


def clean_indicator(series_code, value_name):
    temp = transition_data[transition_data["Series Code"] == series_code].copy()
    temp = temp[["Country Name", "Country Code"] + transition_year_cols]

    temp = temp.melt(
        id_vars=["Country Name", "Country Code"],
        value_vars=transition_year_cols,
        var_name="year",
        value_name=value_name
    )

    temp["year"] = temp["year"].str.extract(r"(\d{4})").astype(int)

    temp[value_name] = pd.to_numeric(
        temp[value_name].replace("..", pd.NA),
        errors="coerce"
    )

    return temp


transition_total = clean_indicator(transition_codes["total_mortality"], "total_mortality")
transition_male = clean_indicator(transition_codes["male_mortality"], "male_mortality")
transition_female = clean_indicator(transition_codes["female_mortality"], "female_mortality")

transition_df = transition_total.merge(
    transition_male,
    on=["Country Name", "Country Code", "year"],
    how="inner"
)

transition_df = transition_df.merge(
    transition_female,
    on=["Country Name", "Country Code", "year"],
    how="inner"
)

transition_df = transition_df.dropna(
    subset=["total_mortality", "male_mortality", "female_mortality"]
)

transition_df = transition_df[
    (transition_df["year"] >= 1960) &
    (transition_df["year"] <= 2024)
].copy()

transition_df["mortality_gap"] = transition_df["male_mortality"] - transition_df["female_mortality"]

transition_df["total_mortality"] = transition_df["total_mortality"].round(1)
transition_df["male_mortality"] = transition_df["male_mortality"].round(1)
transition_df["female_mortality"] = transition_df["female_mortality"].round(1)
transition_df["mortality_gap"] = transition_df["mortality_gap"].round(2)

# =========================
# ADD REGIONS
# =========================

transition_world_url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
transition_world = gpd.read_file(transition_world_url)

transition_regions = transition_world[["ADM0_A3", "CONTINENT"]].rename(
    columns={
        "ADM0_A3": "Country Code",
        "CONTINENT": "region"
    }
)

transition_df = transition_df.merge(transition_regions, on="Country Code", how="left")
transition_df["region"] = transition_df["region"].fillna("Other")

# =========================
# OPTIONS
# =========================

transition_valid_regions = sorted(
    region for region in transition_df["region"].dropna().unique()
    if region not in ["Antarctica", "Seven seas (open ocean)"]
)

transition_region_options = [{"label": "All Regions", "value": "All"}] + [
    {"label": region, "value": region}
    for region in transition_valid_regions
]

transition_country_options = [
    {"label": country, "value": country}
    for country in sorted(transition_df["Country Name"].dropna().unique())
]

transition_region_colors = {
    "Africa": "#9f5f4f",
    "Asia": "#176b5c",
    "Europe": "#4d7188",
    "North America": "#7c6a93",
    "South America": "#aa7d2a",
    "Oceania": "#4f9d8a",
    "Other": "#918b82"
}

transition_label_positions = [
    "top center",
    "bottom center",
    "middle right",
    "middle left"
]

# =========================
# DASH APP
# =========================

app = Dash(__name__)
server = app.server
app.index_string = """
<!DOCTYPE html>
<html>
  <head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>
    {DASH_CSS}
    </style>
  </head>
  <body>
    {%app_entry%}
    <footer>
      {%config%}
      {%scripts%}
      {%renderer%}
    </footer>
  </body>
</html>
""".replace("{DASH_CSS}", DASH_CSS)

infant_layout = html.Div(
    style=APP_STYLE,
    children=[
        html.Div(
            className="dashboard-shell", style=SHELL_STYLE,
            children=[
                # =========================
                # LEFT SIDEBAR
                # =========================

                html.Div(
                    className="dashboard-sidebar", style=SIDEBAR_STYLE,
                    children=[
                        html.Label(
                            "Indicators",
                            style=LABEL_STYLE
                        ),

                        dcc.Checklist(
                            id="infant-indicator-checklist",
                            options=[
                                {"label": " Total", "value": "Total"},
                                {"label": " Male", "value": "Male"},
                                {"label": " Female", "value": "Female"}
                            ],
                            value=["Total"],
                            style={
                                "marginTop": "8px",
                                "lineHeight": "1.8",
                                "fontSize": "15px"
                            }
                        ),

                        html.Div(style={"height": "18px"}),

                        html.Label(
                            "Search Country",
                            style=LABEL_STYLE
                        ),

                        dcc.Dropdown(
                            id="infant-country-search",
                            options=infant_country_options,
                            placeholder="Type country or code, e.g. Singapore or SGP...",
                            clearable=True,
                            searchable=True,
                            optionHeight=42,
                            style={"marginTop": "6px"}
                        ),

                        html.Details(
                            style={
                                "marginTop": "10px",
                                "fontSize": "12px",
                                "color": COLORS["muted"],
                                "lineHeight": "1.45"
                            },
                            children=[
                                html.Summary(
                                    f"Show available countries ({len(infant_country_options)})",
                                    style={
                                        "cursor": "pointer",
                                        "fontWeight": "800",
                                        "color": COLORS["accent_dark"]
                                    }
                                ),
                                html.Div(
                                    infant_country_list_text,
                                    style={
                                        "maxHeight": "150px",
                                        "overflowY": "auto",
                                        "marginTop": "8px",
                                        "padding": "10px",
                                        "border": f'1px solid {COLORS["line"]}',
                                        "borderRadius": "12px",
                                        "backgroundColor": COLORS["paper"]
                                    }
                                )
                            ]
                        ),

                        html.Div(
                            id="infant-country-info",
                            style=INFO_BOX_STYLE
                        ),

                        html.Hr(
                            style={
                                "border": "none",
                                "borderTop": "1px solid #ded8ce",
                                "margin": "18px 0"
                            }
                        ),

                        html.Label(
                            "Year",
                            style=LABEL_STYLE
                        ),

                        html.Div(
                            style={
                                "display": "flex",
                                "justifyContent": "center",
                                "marginTop": "12px"
                            },
                            children=[
                                dcc.Slider(
                                    id="infant-year-slider",
                                    min=1960,
                                    max=2024,
                                    step=1,
                                    value=2024,
                                    marks={
                                        1960: "1960",
                                        1980: "1980",
                                        2000: "2000",
                                        2024: "2024"
                                    },
                                    tooltip={
                                        "placement": "bottom",
                                        "always_visible": True
                                    },
                                    vertical=True,
                                    verticalHeight=300
                                )
                            ]
                        ),

                        html.Button(
                            "Play / Pause",
                            id="infant-play-button",
                            n_clicks=0,
                            style={**BUTTON_STYLE, "marginTop": "20px"}
                        )
                    ]
                ),

                # =========================
                # MAP AREA
                # =========================

                html.Div(
                    className="dashboard-main", style=MAIN_STYLE,
                    children=[
                        html.H1(
                            "Global Infant Mortality Trends by Year and Sex",
                            style=TITLE_STYLE
                        ),

                        dcc.Interval(
                            id="infant-interval",
                            interval=700,
                            n_intervals=0,
                            disabled=True
                        ),

                        dcc.Graph(
                            id="infant-map-graph",
                            className="dashboard-graph",
                            style={"height": "calc(100vh - 112px)"},
                            config={"responsive": True, "displayModeBar": False}
                        ),

                        html.Div(
                            "Source: World Bank, World Development Indicators",
                            style=SOURCE_STYLE
                        )
                    ]
                )
            ]
        )
    ]
)

transition_layout = html.Div(
    style=APP_STYLE,
    children=[
        html.Div(
            className="dashboard-shell", style=SHELL_STYLE,
            children=[
                # =========================
                # SIDEBAR
                # =========================

                html.Div(
                    className="dashboard-sidebar", style=SIDEBAR_STYLE,
                    children=[
                        html.Label("Regions", style=LABEL_STYLE),

                        dcc.Dropdown(
                            id="transition-region-dropdown",
                            options=transition_region_options,
                            value=["All"],
                            multi=True,
                            clearable=True,
                            searchable=True,
                            style={"marginTop": "6px"}
                        ),

                        html.Br(),

                        html.Label("Highlight Countries", style=LABEL_STYLE),

                        dcc.Dropdown(
                            id="transition-country-dropdown",
                            options=transition_country_options,
                            value=[
                                "Korea, Rep.",
                                "Japan",
                                "United States",
                                "Brazil",
                                "India",
                                "Nigeria"
                            ],
                            multi=True,
                            searchable=True,
                            clearable=True,
                            placeholder="Search countries...",
                            style={"marginTop": "6px"}
                        ),

                        html.Br(),

                        html.Label("Year", style=LABEL_STYLE),

                        dcc.Slider(
                            id="transition-year-slider",
                            min=1960,
                            max=2024,
                            step=1,
                            value=2024,
                            marks={
                                1960: "1960",
                                1980: "1980",
                                2000: "2000",
                                2024: "2024"
                            },
                            tooltip={
                                "placement": "bottom",
                                "always_visible": True
                            }
                        ),

                        html.Br(),

                        html.Button(
                            "Play / Pause",
                            id="transition-play-button",
                            n_clicks=0,
                            style=BUTTON_STYLE
                        ),

                        html.Hr(),

                        html.Div(
                            "Region selection controls the background points. Clear Regions to show highlighted countries only; selected country trails always remain visible.",
                            style={"fontSize": "14px", "lineHeight": "1.45", "color": COLORS["muted"]}
                        )
                    ]
                ),

                # =========================
                # MAIN AREA
                # =========================

                html.Div(
                    className="dashboard-main", style=MAIN_STYLE,
                    children=[
                        html.H1(
                            "Global Health Transition and Sex-Based Infant Mortality Inequality",
                            style=TITLE_STYLE
                        ),

                        html.Div(
                            "How does sex disparity behave as infant mortality changes?",
                            style=SUBTITLE_STYLE
                        ),

                        dcc.Interval(
                            id="transition-interval",
                            interval=650,
                            n_intervals=0,
                            disabled=True
                        ),

                        dcc.Graph(
                            id="transition-graph",
                            className="dashboard-graph",
                            style={"height": "calc(100vh - 132px)"},
                            config={"responsive": True, "displayModeBar": False}
                        ),

                        html.Div(
                            "Source: World Bank, World Development Indicators",
                            style=SOURCE_STYLE
                        )
                    ]
                )
            ]
        )
    ]
)

app.layout = html.Div(
    style=APP_STYLE,
    children=[
        dcc.Tabs(
            id="main-tabs",
            className="dash-tabs",
            value="infant-mortality-map",
            children=[
                dcc.Tab(
                    label="Infant Mortality Map",
                    value="infant-mortality-map",
                    children=infant_layout
                ),
                dcc.Tab(
                    label="Health Transition Scatter",
                    value="health-transition-scatter",
                    children=transition_layout
                )
            ]
        )
    ]
)

# =========================
# AVAILABLE YEARS
# =========================

def available_years_for_country(country, selected_indicators):
    if not country:
        return list(range(1960, 2025))

    temp = infant_df[infant_df["Country Name"] == country].copy()

    if selected_indicators:
        temp = temp[temp["indicator"].isin(selected_indicators)]

    years = sorted(temp["year"].unique())

    if not years:
        return list(range(1960, 2025))

    return years

# =========================
# PLAY / PAUSE
# =========================

@app.callback(
    Output("infant-interval", "disabled"),
    Input("infant-play-button", "n_clicks"),
    State("infant-interval", "disabled")
)
def toggle_infant_animation(n_clicks, disabled):
    if n_clicks == 0:
        return True

    return not disabled

# =========================
# AUTO YEAR CONTROL
# =========================

@app.callback(
    Output("infant-year-slider", "value"),
    Input("infant-interval", "n_intervals"),
    Input("infant-country-search", "value"),
    Input("infant-indicator-checklist", "value"),
    State("infant-year-slider", "value")
)
def update_infant_year_slider(
    n_intervals,
    selected_country,
    selected_indicators,
    current_year
):
    trigger = callback_context.triggered[0]["prop_id"].split(".")[0]

    if not selected_indicators:
        selected_indicators = ["Total"]

    years = available_years_for_country(
        selected_country,
        selected_indicators
    )

    if trigger in ["infant-country-search", "infant-indicator-checklist"]:
        return min(years)

    if trigger == "infant-interval":
        future_years = [
            year for year in years
            if year > current_year
        ]

        if future_years:
            return min(future_years)

        return min(years)

    return current_year

# =========================
# MAIN MAP UPDATE
# =========================

@app.callback(
    Output("infant-map-graph", "figure"),
    Output("infant-country-info", "children"),
    Input("infant-indicator-checklist", "value"),
    Input("infant-year-slider", "value"),
    Input("infant-country-search", "value")
)
def update_infant_map(
    selected_indicators,
    selected_year,
    selected_country
):

    if not selected_indicators:
        selected_indicators = ["Total"]

    year_data = infant_df[
        (infant_df["year"] == selected_year) &
        (infant_df["indicator"].isin(selected_indicators))
    ].copy()

    # =========================
    # SINGLE MAP OR FACET MAPS
    # =========================

    if len(selected_indicators) == 1:
        selected_indicator = selected_indicators[0]

        fig = px.choropleth(
            year_data,
            locations="Country Code",
            color="color_value",
            hover_name="Country Name",
            color_continuous_scale=infant_color_scale,
            range_color=(0, 150),
            projection="natural earth",
            hover_data={
                "Country Code": False,
                "indicator": True,
                "year": True,
                "display_rate": True,
                "color_value": False,
                "lat": False,
                "lon": False
            }
        )

        fig.update_layout(
            title=f"{selected_indicator} Infant Mortality Rate ({selected_year})",
            title_x=0.5,
            height=750
        )

    else:
        fig = px.choropleth(
            year_data,
            locations="Country Code",
            color="color_value",
            hover_name="Country Name",
            facet_col="indicator",
            color_continuous_scale=infant_color_scale,
            range_color=(0, 150),
            projection="natural earth",
            hover_data={
                "Country Code": False,
                "indicator": True,
                "year": True,
                "display_rate": True,
                "color_value": False,
                "lat": False,
                "lon": False
            }
        )

        fig.update_layout(
            title=f"Infant Mortality Comparison ({selected_year})",
            title_x=0.5,
            height=750
        )

    # =========================
    # COUNTRY INFO BOX
    # =========================

    country_info = "Search a country to highlight and zoom."

    selected_lat = None
    selected_lon = None

    if selected_country:
        selected_rows = year_data[
            year_data["Country Name"] == selected_country
        ].copy()

        if not selected_rows.empty:
            display_rows = selected_rows.sort_values("indicator")

            country_info = [
                html.Div(f"{selected_country} ({selected_year})")
            ]

            for _, row in display_rows.iterrows():
                country_info.append(
                    html.Div(
                        f"{row['indicator']}: {row['display_rate']} deaths per 1,000"
                    )
                )

            marker_row = display_rows.iloc[0]

            selected_lat = marker_row["lat"]
            selected_lon = marker_row["lon"]

            fig.add_trace(
                go.Scattergeo(
                    lon=[selected_lon],
                    lat=[selected_lat],
                    mode="markers",
                    marker=dict(
                        size=22,
                        color=COLORS["surface"],
                        line=dict(width=3, color=COLORS["ink"]),
                        symbol="circle"
                    ),
                    hoverinfo="skip",
                    name="Selected country halo",
                    showlegend=False
                )
            )

            fig.add_trace(
                go.Scattergeo(
                    lon=[selected_lon],
                    lat=[selected_lat],
                    mode="text",
                    text=[selected_country],
                    textposition="middle right",
                    textfont=dict(
                        size=18,
                        color=COLORS["ink"],
                        family=FONT_STACK
                    ),
                    hoverinfo="skip",
                    showlegend=False
                )
            )

            fig.add_trace(
                go.Scattergeo(
                    lon=[selected_lon],
                    lat=[selected_lat],
                    mode="markers+text",
                    text=[selected_country],
                    textposition="middle right",
                    textfont=dict(
                        size=14,
                        color=COLORS["surface"],
                        family=FONT_STACK
                    ),
                    marker=dict(
                        size=11,
                        color=COLORS["accent"],
                        line=dict(
                            width=2,
                            color=COLORS["surface"]
                        ),
                        symbol="circle"
                    ),
                    name="Searched country",
                    showlegend=False
                )
            )

    # =========================
    # COLORBAR
    # =========================

    existing_annotations = list(fig.layout.annotations) if fig.layout.annotations else []

    existing_annotations.append(
        dict(
            text="Deaths per 1,000 live births",
            x=1.08,
            y=0.93,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
    )

    fig.update_layout(
        coloraxis_colorbar=dict(
            title="",
            tickvals=[
                0, 15, 30, 45, 60,
                75, 90, 105, 120,
                135, 150
            ],
            ticktext=[
                "0", "15", "30", "45", "60",
                "75", "90", "105", "120",
                "135", "150+"
            ],
            y=0.42,
            len=0.78,
            thickness=58
        ),
        annotations=existing_annotations,
        font=dict(family=FONT_STACK, color=COLORS["ink"]),
        margin=dict(
            l=10,
            r=110,
            t=70,
            b=10
        )
    )

    # =========================
    # MAP STYLE / ZOOM
    # =========================

    if selected_country and selected_lat is not None and selected_lon is not None:
        fig.update_geos(
            center=dict(lat=selected_lat, lon=selected_lon),
            projection_scale=3.5,
            showframe=False,
            showcoastlines=True,
            coastlinecolor=COLORS["muted"],
            showcountries=True,
            countrycolor=COLORS["line"],
            showland=True,
            landcolor="#ece7de"
        )
    else:
        fig.update_geos(
            center=dict(lat=10, lon=0),
            projection_scale=1,
            showframe=False,
            showcoastlines=True,
            coastlinecolor=COLORS["muted"],
            showcountries=True,
            countrycolor=COLORS["line"],
            showland=True,
            landcolor="#ece7de"
        )

    return fig, country_info

# =========================
# CALLBACKS
# =========================

@app.callback(
    Output("transition-interval", "disabled"),
    Input("transition-play-button", "n_clicks"),
    State("transition-interval", "disabled")
)
def toggle_transition_play(n_clicks, disabled):
    if n_clicks == 0:
        return True

    return not disabled


@app.callback(
    Output("transition-year-slider", "value"),
    Input("transition-interval", "n_intervals"),
    State("transition-year-slider", "value")
)
def animate_transition_year(n_intervals, current_year):
    if current_year >= 2024:
        return 1960

    return current_year + 1


@app.callback(
    Output("transition-graph", "figure"),
    Input("transition-region-dropdown", "value"),
    Input("transition-country-dropdown", "value"),
    Input("transition-year-slider", "value")
)
def update_transition_graph(selected_regions, selected_countries, selected_year):

    if selected_countries is None:
        selected_countries = []

    if selected_regions is None:
        selected_regions = []

    # Region selection controls only the background cloud.
    # Clearing regions intentionally hides background countries while keeping
    # highlighted country trails visible.
    if not selected_regions:
        background_data = transition_df.iloc[0:0].copy()
    else:
        background_data = transition_df.copy()

        if "All" not in selected_regions:
            background_data = background_data[
                background_data["region"].isin(selected_regions)
            ]

    current_data = background_data[
        background_data["year"] == selected_year
    ].copy()

    fig = go.Figure()

    # =========================
    # BACKGROUND REGION POINTS
    # =========================

    for region in sorted(current_data["region"].dropna().unique()):

        region_data = current_data[
            (current_data["region"] == region) &
            (~current_data["Country Name"].isin(selected_countries))
        ]

        if region_data.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=region_data["total_mortality"],
                y=region_data["mortality_gap"],
                mode="markers",
                name=region,
                marker=dict(
                    size=region_data["total_mortality"].clip(lower=5, upper=150) / 4,
                    color=transition_region_colors.get(region, "#918b82"),
                    opacity=0.35,
                    line=dict(width=0.5, color=COLORS["surface"])
                ),
                text=region_data["Country Name"],
                customdata=region_data[
                    ["male_mortality", "female_mortality", "region"]
                ],
                hovertemplate=
                    "<b>%{text}</b><br>" +
                    "Region: %{customdata[2]}<br>" +
                    "Total mortality: %{x}<br>" +
                    "Male − Female gap: %{y}<br>" +
                    "Male mortality: %{customdata[0]}<br>" +
                    "Female mortality: %{customdata[1]}<extra></extra>"
            )
        )

    # =========================
    # SELECTED COUNTRY TRAILS
    # =========================

    for i, country in enumerate(selected_countries):

        country_data = transition_df[
            (transition_df["Country Name"] == country) &
            (transition_df["year"] <= selected_year)
        ].copy()

        current_country = transition_df[
            (transition_df["Country Name"] == country) &
            (transition_df["year"] == selected_year)
        ].copy()

        if country_data.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=country_data["total_mortality"],
                y=country_data["mortality_gap"],
                mode="lines",
                name=f"{country} trail",
                line=dict(
                    width=2,
                    color=COLORS["muted"]
                ),
                opacity=0.35,
                hoverinfo="skip",
                showlegend=False
            )
        )

        if not current_country.empty:
            region = current_country["region"].iloc[0]
            label_position = transition_label_positions[i % len(transition_label_positions)]

            fig.add_trace(
                go.Scatter(
                    x=current_country["total_mortality"],
                    y=current_country["mortality_gap"],
                    mode="markers+text",
                    name=country,
                    text=[country],
                    textposition=label_position,
                    textfont=dict(
                        size=13,
                        color=COLORS["ink"],
                        family=FONT_STACK
                    ),
                    marker=dict(
                        size=18,
                        color=transition_region_colors.get(region, "#181716"),
                        opacity=0.95,
                        line=dict(width=2, color=COLORS["ink"])
                    ),
                    customdata=current_country[
                        ["male_mortality", "female_mortality", "region"]
                    ],
                    hovertemplate=
                        "<b>%{text}</b><br>" +
                        "Region: %{customdata[2]}<br>" +
                        "Total mortality: %{x}<br>" +
                        "Male − Female gap: %{y}<br>" +
                        "Male mortality: %{customdata[0]}<br>" +
                        "Female mortality: %{customdata[1]}<extra></extra>"
                )
            )

    # =========================
    # STYLE
    # =========================

    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color=COLORS["quiet"],
        line_width=1
    )

    fig.update_layout(
        title=f"Health Transition Scatter ({selected_year})",
        title_x=0.5,
        height=720,
        plot_bgcolor=COLORS["surface"],
        paper_bgcolor=COLORS["surface"],

        xaxis=dict(
            title="Total infant mortality (per 1,000 live births)",
            range=[0, 230],
            gridcolor=COLORS["line"],
            zeroline=False
        ),

        yaxis=dict(
            title="Male - Female mortality gap",
            range=[-10, 32],
            gridcolor=COLORS["line"],
            zeroline=True,
            zerolinecolor=COLORS["quiet"]
        ),

        legend=dict(
            title="Region / Highlighted Countries",
            orientation="h",
            x=0,
            y=-0.24,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255,253,250,0)",
            font=dict(size=11)
        ),

        font=dict(family=FONT_STACK, color=COLORS["ink"]),
        margin=dict(l=64, r=24, t=70, b=148)
    )

    return fig

# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    app.run(debug=False)

