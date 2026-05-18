import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context

# =========================
# LOAD DATA
# =========================

file_path = "P_Data_Extract_From_World_Development_Indicators.xlsx"

data = pd.read_excel(file_path, sheet_name="Data", engine="openpyxl")

indicators = {
    "Total": "SP.DYN.IMRT.IN",
    "Male": "SP.DYN.IMRT.MA.IN",
    "Female": "SP.DYN.IMRT.FE.IN"
}

year_cols = [col for col in data.columns if "[YR" in col]

all_data = []

for name, code in indicators.items():
    temp = data[data["Series Code"] == code].copy()
    temp = temp[["Country Name", "Country Code"] + year_cols]

    temp = temp.melt(
        id_vars=["Country Name", "Country Code"],
        value_vars=year_cols,
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

    all_data.append(temp)

df = pd.concat(all_data, ignore_index=True)
df = df[(df["year"] >= 1960) & (df["year"] <= 2024)].copy()

# =========================
# COUNTRY CENTROIDS
# =========================

world_url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
world = gpd.read_file(world_url)

world["centroid"] = world.geometry.representative_point()
world["lon"] = world["centroid"].x
world["lat"] = world["centroid"].y

centroids = world[["ADM0_A3", "lat", "lon"]].rename(
    columns={"ADM0_A3": "Country Code"}
)

df = df.merge(centroids, on="Country Code", how="left")

country_options = [
    {"label": country, "value": country}
    for country in sorted(df["Country Name"].unique())
]

# =========================
# COLOR SCALE
# =========================

color_scale = [
    [0.0, "#f4efe6"],
    [0.18, "#d9e7df"],
    [0.36, "#9ec9bb"],
    [0.56, "#4f9d8a"],
    [0.74, "#176b5c"],
    [0.9, "#8f4f43"],
    [1.0, "#5f2f2a"]
]

# =========================
# DASH APP
# =========================

app = Dash(__name__)

app.layout = html.Div(
    style={"fontFamily": "Inter, Arial, sans-serif", "margin": "0", "padding": "0", "backgroundColor": "#f7f5f0", "color": "#181716"},
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
                        "borderRight": "1px solid #ded8ce",
                        "boxSizing": "border-box",
                        "overflowY": "auto"
                    },
                    children=[
                        html.Label(
                            "Indicators",
                            style={"fontWeight": "bold", "fontSize": "17px"}
                        ),

                        dcc.Checklist(
                            id="indicator-checklist",
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
                            id="country-search",
                            options=country_options,
                            placeholder="Type country...",
                            clearable=True,
                            searchable=True,
                            style={"marginTop": "6px"}
                        ),

                        html.Div(
                            id="country-info",
                            style={
                                "fontSize": "15px",
                                "fontWeight": "bold",
                                "lineHeight": "1.45",
                                "marginTop": "18px",
                                "marginBottom": "18px",
                                "padding": "10px 12px",
                                "backgroundColor": "#e8f0ed",
                                "borderRadius": "8px",
                                "border": "1px solid #ded8ce"
                            }
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
                                    id="year-slider",
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
                            id="play-button",
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
                            id="interval",
                            interval=700,
                            n_intervals=0,
                            disabled=True
                        ),

                        dcc.Graph(
                            id="map-graph",
                            style={"height": "calc(100vh - 95px)"}
                        ),

                        html.Div(
                            "Source: World Bank, World Development Indicators",
                            style={
                                "textAlign": "center",
                                "fontSize": "13px",
                                "color": "#918b82",
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

# =========================
# AVAILABLE YEARS
# =========================

def available_years_for_country(country, selected_indicators):
    if not country:
        return list(range(1960, 2025))

    temp = df[df["Country Name"] == country].copy()

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
    Output("interval", "disabled"),
    Input("play-button", "n_clicks"),
    State("interval", "disabled")
)
def toggle_animation(n_clicks, disabled):
    if n_clicks == 0:
        return True

    return not disabled

# =========================
# AUTO YEAR CONTROL
# =========================

@app.callback(
    Output("year-slider", "value"),
    Input("interval", "n_intervals"),
    Input("country-search", "value"),
    Input("indicator-checklist", "value"),
    State("year-slider", "value")
)
def update_year_slider(
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

    if trigger in ["country-search", "indicator-checklist"]:
        return min(years)

    if trigger == "interval":
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
    Output("map-graph", "figure"),
    Output("country-info", "children"),
    Input("indicator-checklist", "value"),
    Input("year-slider", "value"),
    Input("country-search", "value")
)
def update_map(
    selected_indicators,
    selected_year,
    selected_country
):

    if not selected_indicators:
        selected_indicators = ["Total"]

    year_data = df[
        (df["year"] == selected_year) &
        (df["indicator"].isin(selected_indicators))
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
            color_continuous_scale=color_scale,
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
            height=750,
            paper_bgcolor="#fffdfa",
            font=dict(family="Inter, Arial, sans-serif", color="#181716")
        )

    else:
        fig = px.choropleth(
            year_data,
            locations="Country Code",
            color="color_value",
            hover_name="Country Name",
            facet_col="indicator",
            color_continuous_scale=color_scale,
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
            height=750,
            paper_bgcolor="#fffdfa",
            font=dict(family="Inter, Arial, sans-serif", color="#181716")
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
                        color="#181716",
                        family="Inter, Arial, sans-serif"
                    ),
                    marker=dict(
                        size=11,
                        color="#181716",
                        line=dict(
                            width=1.5,
                            color="#fffdfa"
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
            coastlinecolor="#6f6b64",
            showcountries=True,
            countrycolor="#ded8ce",
            showland=True,
            landcolor="#ece7de"
        )
    else:
        fig.update_geos(
            center=dict(lat=10, lon=0),
            projection_scale=1,
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#6f6b64",
            showcountries=True,
            countrycolor="#ded8ce",
            showland=True,
            landcolor="#ece7de"
        )

    return fig, country_info

# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    app.run(debug=False)