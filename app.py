import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context

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

infant_country_options = [
    {"label": country, "value": country}
    for country in sorted(infant_df["Country Name"].unique())
]

# =========================
# COLOR SCALE
# =========================

infant_color_scale = [
    [0.0, "#1a237e"],
    [0.12, "#1565c0"],
    [0.28, "#29b6f6"],
    [0.45, "#b3e5fc"],
    [0.58, "#fff176"],
    [0.72, "#ffb74d"],
    [0.86, "#ff7043"],
    [1.0, "#c62828"]
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
    "Africa": "#E76F51",
    "Asia": "#2A9D8F",
    "Europe": "#457B9D",
    "North America": "#8E44AD",
    "South America": "#F4A261",
    "Oceania": "#00A6D6",
    "Other": "#999999"
}

# =========================
# DASH APP
# =========================

app = Dash(__name__)
server = app.server

infant_layout = html.Div(
    style={"fontFamily": "Arial", "margin": "0", "padding": "0"},
    children=[
        html.Div(
            style={"display": "flex", "height": "100vh"},
            children=[
                # =========================
                # LEFT SIDEBAR
                # =========================

                html.Div(
                    style={
                        "width": "340px",
                        "padding": "20px 22px",
                        "borderRight": "1px solid #dddddd",
                        "boxSizing": "border-box",
                        "overflowY": "auto"
                    },
                    children=[
                        html.Label(
                            "Indicators",
                            style={"fontWeight": "bold", "fontSize": "17px"}
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
                            style={"fontWeight": "bold", "fontSize": "17px"}
                        ),

                        dcc.Dropdown(
                            id="infant-country-search",
                            options=infant_country_options,
                            placeholder="Type country...",
                            clearable=True,
                            searchable=True,
                            style={"marginTop": "6px"}
                        ),

                        html.Div(
                            id="infant-country-info",
                            style={
                                "fontSize": "15px",
                                "fontWeight": "bold",
                                "lineHeight": "1.45",
                                "marginTop": "18px",
                                "marginBottom": "18px",
                                "padding": "10px 12px",
                                "backgroundColor": "#f7f7f7",
                                "borderRadius": "8px",
                                "border": "1px solid #dddddd"
                            }
                        ),

                        html.Hr(
                            style={
                                "border": "none",
                                "borderTop": "1px solid #bbbbbb",
                                "margin": "18px 0"
                            }
                        ),

                        html.Label(
                            "Year",
                            style={"fontWeight": "bold", "fontSize": "17px"}
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
                            style={
                                "width": "100%",
                                "padding": "10px",
                                "marginTop": "20px",
                                "fontSize": "15px"
                            }
                        )
                    ]
                ),

                # =========================
                # MAP AREA
                # =========================

                html.Div(
                    style={
                        "flex": "1",
                        "padding": "0 10px",
                        "boxSizing": "border-box"
                    },
                    children=[
                        html.H1(
                            "Global Infant Mortality Trends by Year and Sex",
                            style={
                                "textAlign": "center",
                                "margin": "12px 0 5px 0",
                                "fontSize": "34px",
                                "fontWeight": "bold"
                            }
                        ),

                        dcc.Interval(
                            id="infant-interval",
                            interval=700,
                            n_intervals=0,
                            disabled=True
                        ),

                        dcc.Graph(
                            id="infant-map-graph",
                            style={"height": "calc(100vh - 95px)"}
                        ),

                        html.Div(
                            "Source: World Bank, World Development Indicators",
                            style={
                                "textAlign": "center",
                                "fontSize": "13px",
                                "color": "#666666",
                                "marginTop": "-8px",
                                "marginBottom": "8px"
                            }
                        )
                    ]
                )
            ]
        )
    ]
)

transition_layout = html.Div(
    style={"fontFamily": "Arial", "margin": "0", "padding": "0"},
    children=[
        html.Div(
            style={"display": "flex", "height": "100vh"},
            children=[
                # =========================
                # SIDEBAR
                # =========================

                html.Div(
                    style={
                        "width": "330px",
                        "padding": "20px",
                        "borderRight": "1px solid #dddddd",
                        "boxSizing": "border-box",
                        "overflowY": "auto"
                    },
                    children=[
                        html.Label("Regions", style={"fontWeight": "bold"}),

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

                        html.Label("Highlight Countries", style={"fontWeight": "bold"}),

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

                        html.Label("Year", style={"fontWeight": "bold"}),

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
                            style={
                                "width": "100%",
                                "padding": "10px",
                                "fontSize": "15px"
                            }
                        ),

                        html.Hr(),

                        html.Div(
                            "This chart shows how countries move as infant mortality declines and the transition_male–transition_female mortality gap changes.",
                            style={
                                "fontSize": "14px",
                                "lineHeight": "1.4",
                                "color": "#555555"
                            }
                        )
                    ]
                ),

                # =========================
                # MAIN AREA
                # =========================

                html.Div(
                    style={
                        "flex": "1",
                        "padding": "10px 20px",
                        "boxSizing": "border-box"
                    },
                    children=[
                        html.H1(
                            "Global Health Transition and Sex-Based Infant Mortality Inequality",
                            style={
                                "textAlign": "center",
                                "fontSize": "28px",
                                "margin": "10px 0 0 0"
                            }
                        ),

                        html.Div(
                            "How does sex disparity behave as infant mortality changes?",
                            style={
                                "textAlign": "center",
                                "fontSize": "15px",
                                "color": "#555555",
                                "marginBottom": "5px"
                            }
                        ),

                        dcc.Interval(
                            id="transition-interval",
                            interval=650,
                            n_intervals=0,
                            disabled=True
                        ),

                        dcc.Graph(
                            id="transition-graph",
                            style={"height": "calc(100vh - 115px)"}
                        ),

                        html.Div(
                            "Source: World Bank, World Development Indicators",
                            style={
                                "textAlign": "center",
                                "fontSize": "12px",
                                "color": "#666666",
                                "marginTop": "-8px"
                            }
                        )
                    ]
                )
            ]
        )
    ]
)

app.layout = html.Div(
    style={"fontFamily": "Arial", "margin": "0", "padding": "0"},
    children=[
        dcc.Tabs(
            id="main-tabs",
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
                    mode="markers+text",
                    text=[selected_country],
                    textposition="middle right",
                    textfont=dict(
                        size=14,
                        color="#111111",
                        family="Arial Black"
                    ),
                    marker=dict(
                        size=11,
                        color="#111111",
                        line=dict(
                            width=1.5,
                            color="white"
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
            coastlinecolor="#444444",
            showcountries=True,
            countrycolor="#444444",
            showland=True,
            landcolor="lightgray"
        )
    else:
        fig.update_geos(
            center=dict(lat=10, lon=0),
            projection_scale=1,
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#444444",
            showcountries=True,
            countrycolor="#444444",
            showland=True,
            landcolor="lightgray"
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

    # If no transition_regions selected, show an empty chart
    if not selected_regions:
        plot_data = transition_df.iloc[0:0].copy()
    else:
        plot_data = transition_df.copy()

        if "All" not in selected_regions:
            plot_data = plot_data[
                plot_data["region"].isin(selected_regions)
            ]

    current_data = plot_data[
        plot_data["year"] == selected_year
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
                    color=transition_region_colors.get(region, "#999999"),
                    opacity=0.35,
                    line=dict(width=0.5, color="white")
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

    for country in selected_countries:

        country_data = plot_data[
            (plot_data["Country Name"] == country) &
            (plot_data["year"] <= selected_year)
        ].copy()

        current_country = plot_data[
            (plot_data["Country Name"] == country) &
            (plot_data["year"] == selected_year)
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
                    color="#444444"
                ),
                opacity=0.35,
                hoverinfo="skip",
                showlegend=False
            )
        )

        if not current_country.empty:
            region = current_country["region"].iloc[0]

            fig.add_trace(
                go.Scatter(
                    x=current_country["total_mortality"],
                    y=current_country["mortality_gap"],
                    mode="markers+text",
                    name=country,
                    text=[country],
                    textposition="top center",
                    textfont=dict(
                        size=13,
                        color="#111111",
                        family="Arial Black"
                    ),
                    marker=dict(
                        size=18,
                        color=transition_region_colors.get(region, "#111111"),
                        opacity=0.95,
                        line=dict(width=2, color="black")
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
        line_color="#666666",
        line_width=1
    )

    fig.update_layout(
        title=f"Health Transition Scatter ({selected_year})",
        title_x=0.5,
        height=720,
        plot_bgcolor="white",
        paper_bgcolor="white",

        xaxis=dict(
            title="Total infant mortality, deaths per 1,000 live births",
            range=[0, 230],
            gridcolor="#e6e6e6",
            zeroline=False
        ),

        yaxis=dict(
            title="Male − Female infant mortality gap",
            range=[-10, 32],
            gridcolor="#e6e6e6",
            zeroline=True,
            zerolinecolor="#555555"
        ),

        legend=dict(
            title="Region / Highlighted Countries",
            x=1.02,
            y=1,
            bgcolor="rgba(255,255,255,0.85)"
        ),

        margin=dict(l=80, r=230, t=70, b=45)
    )

    return fig

# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    app.run(debug=False)

